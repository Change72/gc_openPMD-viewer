import os
import sys
sys.path.insert(0, os.getcwd())

import geosindex
from openpmd_viewer import OpenPMDTimeSeries

import copy
import random
import numpy as np
import csv
import time

# from memory_profiler import profile

def write_csv(filename, data):
    f = open(filename, 'a', newline='', encoding='utf-8')
    Writer = csv.writer(f)
    Writer.writerow(data)
    f.close()
    return

from scipy import constants

class BenchmarkGenerator:
    def __init__(self, bp_file_path, geos_index_path):
        self.key_generation_function = lambda iteration, species, type, dimension=None: f"/data/{iteration}/particles/{species}/{type}/" + (f"{dimension}" if dimension else "")
        self.geos_ts = OpenPMDTimeSeries(bp_file_path, backend='openpmd-api', geos_index=True, geos_index_type="rtree",
                 geos_index_storage_backend="file", geos_index_save_path=geos_index_path)

    def selectRandomEnvelop(self, species, postion_key, random_select_from_max_n=1, include_momentum=False, factor=1):
        metadata_result = self.geos_ts.query_geos_index.queryRTreeMetaData(postion_key)
        # max_env = self.geos_ts.query_geos_index.queryRTreeMetaDataRoot(postion_key)
        # build a map [length] -> metadata
        # length_map = {}
        # for metadata in metadata_result:
        #     length = metadata.end - metadata.start
        #     length_map[length] = metadata

        # select a random length from top n, reverse = true
        # top_n = sorted(length_map.keys(), reverse=True)[:random_select_from_max_n]
        # random_length = random.choice(top_n)
        # random_length = random.choice(list(length_map.keys()))

        # get the metadata
        # metadata = length_map[random_length]
        metadata = random.choice(metadata_result)

        envelope = dict()
        # assign the metadata to EntireEnvelope
        envelope['x'] = [metadata.minx * factor, metadata.maxx * factor]
        envelope['y'] = [metadata.miny * factor, metadata.maxy * factor]
        envelope['z'] = [metadata.minz * factor, metadata.maxz * factor]

        if include_momentum:
            if species == "electrons":
                mass = 9.1093829099999999e-31
            elif species == "hydrogen":
                mass = 1.6726219236900000e-27
            momentum_constant = 1. / (mass * constants.c)

            momentum_key = postion_key.replace("position", "momentum")
            momentum_result = self.geos_ts.query_geos_index.queryRTreeMetaData(momentum_key)
            max_momentum = self.geos_ts.query_geos_index.queryRTreeMetaDataRoot(momentum_key)

            # match the start and end
            for momentum_metadata in momentum_result:
                if momentum_metadata.start == metadata.start and momentum_metadata.end == metadata.end:
                    envelope['ux'] = [momentum_metadata.minx * momentum_constant * factor, momentum_metadata.maxx * momentum_constant * factor]
                    envelope['uy'] = [momentum_metadata.miny * momentum_constant * factor, momentum_metadata.maxy * momentum_constant * factor]
                    envelope['uz'] = [momentum_metadata.minz * momentum_constant * factor, momentum_metadata.maxz * momentum_constant * factor]
                    break

        return envelope


    '''
    generateRandomQuery
    species: species name
    iteration: iteration number
    percentage_range: [start, end, step]
    select_set: the set of the selected key
    expand_set: the set of the expanded key, subset of select_set
    envelope: the envelope of the selected particle
    random_select_from_max_n: the number of the random selected envelope
    threshold: the threshold of the percentage
    expand_factor: the factor of the envelope expand
    '''
    # @profile
    def generateRandomQuery(self, species, iteration,
                            percentage_range, select_set, expand_set=None,
                            envelope=None, random_select_from_max_n=1, 
                            threshold=0.001, 
                            learning_rate=1.0, 
                            total_particle_num=0,
                            output_file="benchmark_result.csv"):

        # get the total particle number
        if total_particle_num == 0:
            z_all = self.geos_ts.get_particle(['z'], species=species, iteration=iteration, select={'z':[-np.inf, np.inf]}, geos_index_read_groups=True)
            z_all_length = len(z_all[0])
            del z_all
        else:
            z_all_length = total_particle_num
        select_position_key = self.key_generation_function(iteration, species, "position")

        result = list()
        # generate the percentage list
        percentage_list = list()
        if len(percentage_range) != 3:
            percentage_list = percentage_range
        else:
            start, end, step = percentage_range
            while start <= end:
                percentage_list.append(start)
                start *= step
        print(percentage_list)

        random_expand_set = False
        if not expand_set:
            random_expand_set = True

        for percentage in percentage_list:
            if random_expand_set:
                if len(select_set) == 1:
                    expand_set = select_set
                else:
                    expand_set = random.sample(select_set, random.randint(int(len(select_set) / 2) + 1, len(select_set)))
            print(f"percentage: {percentage}, select_set: {select_set}, expand_set: {expand_set}")

            if {'ux', 'uy', 'uz'}.intersection(select_set):
                include_momentum = True
            else:
                include_momentum = False

            init_envelope = self.selectRandomEnvelop(
                                species=species,
                                postion_key=select_position_key,
                                random_select_from_max_n=random_select_from_max_n,
                                include_momentum=include_momentum,
                                )

            target_key = None
            envelope_keys = list(init_envelope.keys())
            for key in envelope_keys:
                if key not in select_set:
                    # remove the key from the envelope
                    init_envelope.pop(key)
                else:
                    target_key = key

            i = 0
            inside_one_block = False
            envelope = copy.deepcopy(init_envelope)

            last_percentage = -1
            percentage_recursive_time = 0
            # offset = random.uniform(0, 1)
            select_list = list(select_set)
            while True:
                print(f"loop {i}: target_percentage: {percentage * 100}%, envelope: {envelope}")
                start = time.time()
                select_envelope = copy.deepcopy(envelope)
                z_in_envelope = self.geos_ts.get_particle(select_list, species=species, iteration=iteration, geos_index_read_groups=True, select=select_envelope, skip_offset=True)
                del select_envelope
                
                current_percentage = float(len(z_in_envelope[0])) / z_all_length
                end = time.time()
                print("Time elapsed: ", end - start, f"current_percentage: {current_percentage * 100}%, envelope: {envelope}")
                print()
                print("===========================================================================")
                if last_percentage == current_percentage:
                    percentage_recursive_time += 1
                    if percentage_recursive_time > 100 or i > 1000:
                        # result.append({
                        #     "code": 400,
                        #     "message": "query generated failed due to the percentage_recursive_time > 100",
                        #     "percentage": percentage,
                        #     "iteration": iteration,
                        #     "species": species,
                        #     "select_position_key": select_position_key,
                        #     "select_set": select_set,
                        #     "expand_set": expand_set,
                        #     "envelope": copy.deepcopy(envelope),
                        #     "inside_one_block": inside_one_block
                        # })
                        print("query generated failed due to the percentage_recursive_time > 100")
                        break
                else:
                    percentage_recursive_time = 0
                    last_percentage = current_percentage

                diff_percentage = percentage - current_percentage

                if abs(diff_percentage) < threshold * percentage:
                    write_csv(output_file, [percentage, current_percentage, iteration, species, str(select_set), str(expand_set), envelope])
                    break

                i += 1
                if diff_percentage > 0:
                    for key in expand_set:
                        mid = (envelope[key][0] + envelope[key][1]) / 2
                        # random
                        # mid = random.uniform(envelope[key][0], envelope[key][1])
                        length = envelope[key][1] - envelope[key][0]
                        if current_percentage == 0.0:
                            new_length = length * 10
                        else:
                            new_length = length * (1 + diff_percentage * learning_rate + random.uniform(0, 0.1))
                        envelope[key][0] = mid - new_length / 2
                        envelope[key][1] = mid + new_length / 2
                    continue

                else:
                    boundary = copy.deepcopy(envelope)
                    k = 0
                    while True:
                        select_array = np.ones(len(z_in_envelope[0]), dtype='bool')

                        for key in expand_set:
                            if random.uniform(0, 1) > 0.8:
                                continue
                            # mid = (envelope[key][0] + envelope[key][1]) / 2
                            # random
                            random_middle = random.uniform(0.4, 0.6)  # Generate a random percentage between 40% and 60%
                            mid = envelope[key][0] + (envelope[key][1] - envelope[key][0]) * random_middle
                            # mid = random.uniform(envelope[key][0], envelope[key][1])
                            length = envelope[key][1] - envelope[key][0]
                            if diff_percentage > 0:
                                if current_percentage == 0.0:
                                    new_length = length * 3
                                else:
                                    new_length = length * (1 + diff_percentage * learning_rate + random.uniform(0, 0.1))
                            else:
                                new_length = length * (1 + diff_percentage * learning_rate - random.uniform(0, 0.1))
                                if new_length < 0:
                                    new_length = length * 0.9
                                new_length = max(new_length, length * 0.7)
                            envelope[key][0] = max(mid - new_length / 2, boundary[key][0])
                            envelope[key][1] = min(mid + new_length / 2, boundary[key][1])

                            # key index in select_list
                            key_index = select_list.index(key)

                            if key in ['ux', 'uy', 'uz']:
                                if species == "electrons":
                                    mass = 9.1093829099999999e-31
                                elif species == "hydrogen":
                                    mass = 1.6726219236900000e-27
                                momentum_constant = 1. / (mass * constants.c)

                                select_array = np.logical_and(
                                                select_array,
                                                z_in_envelope[key_index] > (envelope[key][0] / momentum_constant))

                                select_array = np.logical_and(
                                                select_array,
                                                z_in_envelope[key_index] < (envelope[key][1] / momentum_constant))
                            else:
                                select_array = np.logical_and(
                                                select_array,
                                                z_in_envelope[key_index] > envelope[key][0])

                                select_array = np.logical_and(
                                                select_array,
                                                z_in_envelope[key_index] < envelope[key][1])

                        z_new = [z_in_envelope[i][select_array] for i in range(len(z_in_envelope))]

                        current_percentage = float(len(z_new[0])) / z_all_length
                        diff_percentage = percentage - current_percentage

                        if current_percentage / percentage > 100:
                            z_in_envelope = z_new

                        print(f"loop {i}, k: {k}, current_percentage: {current_percentage * 100}%, length of z_in_envelope, {len(z_in_envelope[0])} envelope: {envelope}")

                        if abs(diff_percentage) < threshold * percentage:
                            write_csv(output_file, [percentage, current_percentage, iteration, species, str(select_set), str(expand_set), envelope])
                            break

                        k += 1
                        if k > 1000:
                            break

                del z_in_envelope
                break

            del envelope
            del init_envelope

        return result

