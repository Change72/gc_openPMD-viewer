import os
import sys
sys.path.insert(0, os.getcwd())

import geosindex
from openpmd_viewer import OpenPMDTimeSeries

import copy
import random
import numpy as np

from scipy import constants
mass = 9.1093829099999999e-31
momentum_constant = 1. / (mass * constants.c)

class BenchmarkGenerator:
    def __init__(self, bp_file_path, geos_index_path):
        self.key_generation_function = lambda iteration, species, type, dimension=None: f"/data/{iteration}/particles/{species}/{type}/" + (f"{dimension}" if dimension else "")
        self.geos_ts = OpenPMDTimeSeries(bp_file_path, backend='openpmd-api', geos_index=True, geos_index_type="rtree",
                 geos_index_storage_backend="file", geos_index_save_path=geos_index_path)

    def selectRandomEnvelop(self, postion_key, random_select_from_max_n=1, include_momentum=False):
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
        envelope['x'] = [metadata.minx, metadata.maxx]
        envelope['y'] = [metadata.miny, metadata.maxy]
        envelope['z'] = [metadata.minz, metadata.maxz]

        # max_envelope = dict()
        # max_envelope['x'] = [max_env.minx * 1.2, max_env.maxx * 1.2]
        # max_envelope['y'] = [max_env.miny * 1.2, max_env.maxy * 1.2]
        # max_envelope['z'] = [max_env.minz * 1.2, max_env.maxz * 1.2]

        if include_momentum:
            momentum_key = postion_key.replace("position", "momentum")
            momentum_result = self.geos_ts.query_geos_index.queryRTreeMetaData(momentum_key)
            max_momentum = self.geos_ts.query_geos_index.queryRTreeMetaDataRoot(momentum_key)

            # max_envelope['ux'] = [max_momentum.minx * momentum_constant, max_momentum.maxx * momentum_constant]
            # max_envelope['uy'] = [max_momentum.miny * momentum_constant, max_momentum.maxy * momentum_constant]
            # max_envelope['uz'] = [max_momentum.minz * momentum_constant, max_momentum.maxz * momentum_constant]

            # match the start and end
            for momentum_metadata in momentum_result:
                if momentum_metadata.start == metadata.start and momentum_metadata.end == metadata.end:
                    envelope['ux'] = [momentum_metadata.minx * momentum_constant, momentum_metadata.maxx * momentum_constant]
                    envelope['uy'] = [momentum_metadata.miny * momentum_constant, momentum_metadata.maxy * momentum_constant]
                    envelope['uz'] = [momentum_metadata.minz * momentum_constant, momentum_metadata.maxz * momentum_constant]
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
    def generateRandomQuery(self, species, iteration,
                            percentage_range, select_set, expand_set,
                            envelope=None, random_select_from_max_n=1, 
                            threshold=0.001, 
                            repeat_num=1, learning_rate=1.0):

        # get the total particle number
        z_all = self.geos_ts.get_particle(['z'], species=species, iteration=iteration, select={'z':[-np.inf, np.inf]}, geos_index_read_groups=True)

        select_position_key = self.key_generation_function(iteration, species, "position")

        result = list()
        # generate the percentage list
        percentage_list = list()
        start, end, step = percentage_range
        while start <= end:
            percentage_list.append(start)
            start *= step
        print(percentage_list)

        for percentage in percentage_list:
            for k in range(repeat_num):
                include_momentum = False
                init_envelope = self.selectRandomEnvelop(postion_key=select_position_key,
                                                         random_select_from_max_n=random_select_from_max_n,
                                                         include_momentum=include_momentum)
                envelope_keys = list(init_envelope.keys())
                for key in envelope_keys:
                    if key not in select_set:
                        # remove the key from the envelope
                        init_envelope.pop(key)

                i = 0
                inside_one_block = False
                envelope = copy.deepcopy(init_envelope)

                last_percentage = -1
                percentage_recursive_time = 0
                # offset = random.uniform(0, 1)
                while True:
                    z_in_envelope = self.geos_ts.get_particle(['z'], species=species, iteration=iteration, geos_index_read_groups=True, select=envelope)

                    current_percenage = float(len(z_in_envelope[0])) / len(z_all[0])

                    print(f"repeat_num {k}: loop {i}: target_percentage: {percentage * 100}%", f"current_percentage: {current_percenage * 100}%, envelope: {envelope}")
                    
                    if last_percentage == current_percenage:
                        percentage_recursive_time += 1
                        if percentage_recursive_time > 100:
                            result.append({
                                "code": 400,
                                "message": "query generated failed due to the percentage_recursive_time > 100",
                                "percentage": percentage,
                                "iteration": iteration,
                                "species": species,
                                "select_position_key": select_position_key,
                                "select_set": select_set,
                                "expand_set": expand_set,
                                "envelope": copy.deepcopy(envelope),
                                "inside_one_block": inside_one_block
                            })
                            print("query generated failed due to the percentage_recursive_time > 100")
                            break
                    else:
                        percentage_recursive_time = 0
                        last_percentage = current_percenage

                    # if current_percenage < percentage:
                    #     expand_flag = True
                    # else:
                    #     expand_flag = False
                    #     if i == 0:
                    #         inside_one_block = True

                    diff_percentage = percentage - current_percenage

                    if abs(diff_percentage) < threshold * percentage:
                        result.append({
                            "code": 200,
                            "message": "query generated success",
                            "percentage": percentage,
                            "iteration": iteration,
                            "species": species,
                            "select_position_key": select_position_key,
                            "select_set": select_set,
                            "expand_set": expand_set,
                            "envelope": copy.deepcopy(envelope),
                            "inside_one_block": inside_one_block,
                            "diff_percentage": diff_percentage
                        })
                        break

                    # TODO expand the envelope, for now, we just * 1.1 or * 0.9, it cannot change the +/- direction
                    # so tha maximum range can only include 50% of the total particle

                    # if expand_flag:
                    #     for key in expand_set:
                    #         if isinstance( expand_factor, list ):
                    #             envelope[key][0] *= expand_factor[0] if envelope[key][0] > 0 else expand_factor[1]
                    #             envelope[key][1] *= expand_factor[1] if envelope[key][1] > 0 else expand_factor[0]
                    #         elif isinstance( expand_factor, dict ):
                    #             envelope[key][0] *= expand_factor[key][0] if envelope[key][0] > 0 else expand_factor[key][1]
                    #             envelope[key][1] *= expand_factor[key][1] if envelope[key][1] > 0 else expand_factor[key][0]
                    # else:
                    #     for key in expand_set:
                    #         if isinstance( expand_factor, list ):
                    #             envelope[key][0] *= expand_factor[1] if envelope[key][0] > 0 else expand_factor[0]
                    #             envelope[key][1] *= expand_factor[0] if envelope[key][1] > 0 else expand_factor[1]
                    #         elif isinstance( expand_factor, dict ):
                    #             envelope[key][0] *= expand_factor[key][1] if envelope[key][0] > 0 else expand_factor[key][0]
                    #             envelope[key][1] *= expand_factor[key][0] if envelope[key][1] > 0 else expand_factor[key][1]
                    
                    # learning_rate *= learning_rate

                    for key in expand_set:
                        # mid = (envelope[key][0] + envelope[key][1]) / 2
                        # random
                        mid = random.uniform(envelope[key][0], envelope[key][1])
                        length = envelope[key][1] - envelope[key][0]
                        if diff_percentage > 0: # expand
                            new_length = length * (1 + diff_percentage * learning_rate + random.uniform(0, 0.1))
                        else: # shrink
                            new_length = length * (1 + diff_percentage * learning_rate - random.uniform(0, 0.1))
                        
                        envelope[key][0] = mid - new_length / 2
                        envelope[key][1] = mid + new_length / 2
                        #     envelope[key][0] *= expand_factor[0] if envelope[key][0] > 0 else expand_factor[1]
                        #     envelope[key][1] *= expand_factor[1] if envelope[key][1] > 0 else expand_factor[0]
                        # else: # shrink
                        #     envelope[key][0] *= expand_factor[1] if envelope[key][0] > 0 else expand_factor[0]
                        #     envelope[key][1] *= expand_factor[0] if envelope[key][1] > 0 else expand_factor[1]
                        # if envelope[key][0] > 0:
                        #     envelope[key][0] -= (diff_percentage + random.uniform(-0.1, 0.1)) * max_envelope[key][0] * learning_rate
                        # else:
                        #     envelope[key][0] += diff_percentage * max_envelope[key][0] * learning_rate

                        # if envelope[key][1] > 0:
                        #     envelope[key][1] += diff_percentage * max_envelope[key][1] * learning_rate
                        # else:
                        #     envelope[key][1] -= diff_percentage * max_envelope[key][1] * learning_rate

                    i += 1
        return result

