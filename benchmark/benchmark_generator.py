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

from memory_profiler import profile

def write_csv(filename, data):
    f = open(filename, 'a', newline='', encoding='utf-8')
    Writer = csv.writer(f)
    Writer.writerow(data)
    f.close()
    return

from scipy import constants
mass = 9.1093829099999999e-31
momentum_constant = 1. / (mass * constants.c)

class BenchmarkGenerator:
    def __init__(self, bp_file_path, geos_index_path):
        self.key_generation_function = lambda iteration, species, type, dimension=None: f"/data/{iteration}/particles/{species}/{type}/" + (f"{dimension}" if dimension else "")
        self.geos_ts = OpenPMDTimeSeries(bp_file_path, backend='openpmd-api', geos_index=True, geos_index_type="rtree",
                 geos_index_storage_backend="file", geos_index_save_path=geos_index_path)

    def selectRandomEnvelop(self, postion_key, random_select_from_max_n=1, include_momentum=False, factor=0.1):
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
            # random select one or multiple keys from the select_set
            expand_set = random.sample(select_set, random.randint(int(len(select_set) / 2), len(select_set)))
            random_expand_set = True

        for percentage in percentage_list:
            if random_expand_set:
                expand_set = random.sample(select_set, random.randint(int(len(select_set) / 2), len(select_set)))

            if {'ux', 'uy', 'uz'}.intersection(select_set):
                include_momentum = True
            else:
                include_momentum = False

            if len(select_set) == 6:
                factor = 100
            else:
                factor = 0.1

            init_envelope = self.selectRandomEnvelop(
                                postion_key=select_position_key,
                                random_select_from_max_n=random_select_from_max_n,
                                include_momentum=include_momentum,
                                factor=factor)

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
            while True:
                print(f"loop {i}: target_percentage: {percentage * 100}%, envelope: {envelope}")
                start = time.time()
                z_in_envelope = self.geos_ts.get_particle([target_key] if target_key else ['z'], species=species, iteration=iteration, geos_index_read_groups=True, select=envelope)

                current_percenage = float(len(z_in_envelope[0])) / z_all_length
                end = time.time()
                print("Time elapsed: ", end - start, f"current_percentage: {current_percenage * 100}%, envelope: {envelope}")
                print()
                del z_in_envelope
                print("===========================================================================")
                if last_percentage == current_percenage:
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
                    last_percentage = current_percenage

                diff_percentage = percentage - current_percenage

                if abs(diff_percentage) < threshold * percentage:
                    # result.append({
                    #     "code": 200,
                    #     "message": "query generated success",
                    #     "percentage": percentage,
                    #     "iteration": iteration,
                    #     "species": species,
                    #     "select_position_key": select_position_key,
                    #     "select_set": select_set,
                    #     "expand_set": expand_set,
                    #     "envelope": copy.deepcopy(envelope),
                    #     "inside_one_block": inside_one_block,
                    #     "diff_percentage": diff_percentage
                    # })

                    write_csv(output_file, [percentage, current_percenage, iteration, species, str(select_set), str(expand_set), envelope])
                    break

                for key in expand_set:
                    mid = (envelope[key][0] + envelope[key][1]) / 2
                    # random
                    # mid = random.uniform(envelope[key][0], envelope[key][1])
                    length = envelope[key][1] - envelope[key][0]
                    if diff_percentage > 0: # expand
                        new_length = length * (1 + diff_percentage * learning_rate + random.uniform(0, 0.1))
                    else: # shrink
                        new_length = length * (1 + diff_percentage * learning_rate - random.uniform(0, 0.1))
                    
                    envelope[key][0] = mid - new_length / 2
                    envelope[key][1] = mid + new_length / 2

                i += 1

            del envelope
            del init_envelope

        return result

