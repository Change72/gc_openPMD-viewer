import os
import time

import sys

sys.path.insert(0, os.getcwd())

from benchmark import BenchmarkGenerator
from openpmd_viewer import OpenPMDTimeSeries


def single_query_test(
        bp_file_path,
        geos_index=False,
        geos_index_type="minmax",
        geos_index_storage_backend="file",
        geos_index_save_path=None,
        geos_index_secondary_type="none",

        target_array=["x"],
        species="electrons",
        iteration=300,
        select_envelope=None,

        geos_index_use_secondary=False,
        geos_index_direct_block_read=True,
        geos_index_read_groups=False,

        query_test_message="",
):
    print(query_test_message)

    ts = OpenPMDTimeSeries(
        path_to_dir=bp_file_path,
        backend='openpmd-api',
        geos_index=geos_index,
        geos_index_type=geos_index_type,
        geos_index_storage_backend=geos_index_storage_backend,
        geos_index_save_path=geos_index_save_path,
        geos_index_secondary_type=geos_index_secondary_type,
    )

    start = time.time()

    result = ts.get_particle(
        var_list=target_array,
        iteration=iteration,
        species=species,
        select=select_envelope,
        geos_index_use_secondary=geos_index_use_secondary,
        geos_index_direct_block_read=geos_index_direct_block_read,
        geos_index_read_groups=geos_index_read_groups,
    )

    end = time.time()
    print(f"{query_test_message} Time: {end - start}, data size: {result[0][0].size}")
    return end - start


# main
def main():
    bp_file_path = '/pscratch/sd/c/cguo51/openPMD'
    geos_index_path = "/pscratch/sd/c/cguo51/GEOSIndex/build/bp010000"

    species = "electrons"
    iteration = 10000

    # generate random query
    bg = BenchmarkGenerator(bp_file_path=bp_file_path, geos_index_path=geos_index_path)

    result = bg.generateRandomQuery(species=species, iteration=iteration, percentage_range=[0.01, 0.1, 10],
                                    select_set={'x'}, expand_set={'x'}, threshold=0.1, repeat_num=3, learning_rate=0.99)

    target_array=["x"]
    query_time_dict = dict()

    for query in result:
        if query["code"] == 400:
            print("query failed, skip this query.")
            continue

        print()
        print("===============================================")
        print(f"current query: {query}")
        
        query_time_dict[query["percentage"]] = list()
        '''
        query_time_dict[query["percentage"]].append(single_query_test(
            bp_file_path=bp_file_path,
            geos_index=False,
            geos_index_type="minmax",
            geos_index_storage_backend="file",
            geos_index_save_path=geos_index_path,
            geos_index_secondary_type="none",

            target_array=target_array,
            species=species,
            iteration=iteration,
            select_envelope=query["envelope"],

            geos_index_use_secondary=False,
            geos_index_direct_block_read=True,
            geos_index_read_groups=False,

            query_test_message="1. Original openPMD-viewer query"
        ))
        '''
        query_time_dict[query["percentage"]].append(single_query_test(
            bp_file_path=bp_file_path,
            geos_index=True,
            geos_index_type="minmax",
            geos_index_storage_backend="file",
            geos_index_save_path=geos_index_path,
            geos_index_secondary_type="none",

            target_array=target_array,
            species=species,
            iteration=iteration,
            select_envelope=query["envelope"],

            geos_index_use_secondary=False,
            geos_index_direct_block_read=True,
            geos_index_read_groups=False,

            query_test_message="2. Min-Max only first level with direct block read"
        ))

        query_time_dict[query["percentage"]].append(single_query_test(
            bp_file_path=bp_file_path,
            geos_index=True,
            geos_index_type="minmax",
            geos_index_storage_backend="file",
            geos_index_save_path=geos_index_path,
            geos_index_secondary_type="none",

            target_array=target_array,
            species=species,
            iteration=iteration,
            select_envelope=query["envelope"],

            geos_index_use_secondary=False,
            geos_index_direct_block_read=False,
            geos_index_read_groups=True,

            query_test_message="3. Min-Max only first level with read groups"
        ))


        query_time_dict[query["percentage"]].append(single_query_test(
            bp_file_path=bp_file_path,
            geos_index=True,
            geos_index_type="minmax",
            geos_index_storage_backend="file",
            geos_index_save_path=geos_index_path,
            geos_index_secondary_type="minmax",

            target_array=target_array,
            species=species,
            iteration=iteration,
            select_envelope=query["envelope"],

            geos_index_use_secondary=True,
            geos_index_direct_block_read=False,
            geos_index_read_groups=False,

            query_test_message="4. Min-Max only first level with secondary index read"
        ))

        print()



if __name__ == "__main__":
    main()

