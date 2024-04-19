import os
import time
import argparse

import sys
sys.path.insert(0, os.getcwd())

import pandas as pd
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
):

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
    print(f"Total Time: {end - start}, data size: {result[0].size}")
    print()
    return end - start


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Batch Benchmark Generator Script')
    parser.add_argument('--bpfile', type=str, help='bp file path')
    parser.add_argument('--index', type=str, help='geoindex path (rtree)')
    parser.add_argument('--iteration', type=str, help='iteration number', default=10000)
    parser.add_argument('--species', type=str, help='species', default='electrons')
    parser.add_argument('--query_seq', type=str, help='query sequence', default='0')
    parser.add_argument('--test_type', type=str, help='test type', default='0')
    parser.add_argument('--query_path', type=str, help='query path', default='results/10g_iteration_500/benchmark_result_00001_to_01.csv')

    args = parser.parse_args()
    bp_file_path = args.bpfile
    index_path = args.index
    iteration = int(args.iteration)
    species = args.species
    query_seq = args.query_seq
    test_type = args.test_type
    query_path = args.query_path

    if not bp_file_path or not index_path:
        raise ValueError("bpfile and index are required")

    df = pd.read_csv(query_path, header=[0])

    # int(query_seq), "envelope"
    line = df.iloc[int(query_seq)]
    print(line)
    target_envelope = eval(line["envelope"])
    target_percentage = line["target_percentage"]

    print("===============================================")
    print(f"Query seq: {query_seq}, Target percentage: {target_percentage}, envelope: {target_envelope}")

    if test_type == "1":
        print("Test type 1: Original openPMD-viewer method")

        single_query_test(
            bp_file_path=bp_file_path,

            target_array=list(target_envelope.keys()),
            species=species,
            iteration=iteration,
            select_envelope=target_envelope,
        )

    elif test_type == "2":
        print("Test type 2: GeoIndex, Index type: Min-Max, Storage: File, Secondary: None, Direct Block Read: True")

        single_query_test(
            bp_file_path=bp_file_path,
            geos_index=True,
            geos_index_type="minmax",
            geos_index_storage_backend="file",
            geos_index_save_path=index_path,
            geos_index_secondary_type="none",

            target_array=list(target_envelope.keys()),
            species=species,
            iteration=iteration,
            select_envelope=target_envelope,

            geos_index_use_secondary=False,
            geos_index_direct_block_read=True,
            geos_index_read_groups=False,
        )

    elif test_type == "3":
        print("Test type 3: GeoIndex, Index type: Rtree, Storage: File, Secondary: None, Direct Block Read: True")

        single_query_test(
            bp_file_path=bp_file_path,
            geos_index=True,
            geos_index_type="rtree",
            geos_index_storage_backend="file",
            geos_index_save_path=index_path,
            geos_index_secondary_type="none",

            target_array=list(target_envelope.keys()),
            species=species,
            iteration=iteration,
            select_envelope=target_envelope,

            geos_index_use_secondary=False,
            geos_index_direct_block_read=True,
            geos_index_read_groups=False,
        )

    elif test_type == "4":
        print("Test type 4: GeoIndex, Index type: Min-Max, Storage: File, Secondary: None, Direct Block Read: False, Read Groups: True")

        single_query_test(
            bp_file_path=bp_file_path,
            geos_index=True,
            geos_index_type="minmax",
            geos_index_storage_backend="file",
            geos_index_save_path=index_path,
            geos_index_secondary_type="none",

            target_array=list(target_envelope.keys()),
            species=species,
            iteration=iteration,
            select_envelope=target_envelope,

            geos_index_use_secondary=False,
            geos_index_direct_block_read=False,
            geos_index_read_groups=True,
        )

    elif test_type == "5":
        print("Test type 5: GeoIndex, Index type: Rtree, Storage: File, Secondary: None, Direct Block Read: False, Read Groups: True")

        single_query_test(
            bp_file_path=bp_file_path,
            geos_index=True,
            geos_index_type="rtree",
            geos_index_storage_backend="file",
            geos_index_save_path=index_path,
            geos_index_secondary_type="none",

            target_array=list(target_envelope.keys()),
            species=species,
            iteration=iteration,
            select_envelope=target_envelope,

            geos_index_use_secondary=False,
            geos_index_direct_block_read=False,
            geos_index_read_groups=True,
        )

    elif test_type == "6":
        print("Test type 6: GeoIndex, Index type: Min-Max, Storage: File, Secondary: Min-Max, Direct Block Read: False, Read Groups: False")

        single_query_test(
            bp_file_path=bp_file_path,
            geos_index=True,
            geos_index_type="minmax",
            geos_index_storage_backend="file",
            geos_index_save_path=index_path,
            geos_index_secondary_type="minmax",

            target_array=list(target_envelope.keys()),
            species=species,
            iteration=iteration,
            select_envelope=target_envelope,

            geos_index_use_secondary=True,
            geos_index_direct_block_read=False,
            geos_index_read_groups=False,
        )

    elif test_type == "7":
        print("Test type 7: GeoIndex, Index type: Rtree, Storage: File, Secondary: Min-Max, Direct Block Read: False, Read Groups: False")

        single_query_test(
            bp_file_path=bp_file_path,
            geos_index=True,
            geos_index_type="rtree",
            geos_index_storage_backend="file",
            geos_index_save_path=index_path,
            geos_index_secondary_type="minmax",

            target_array=list(target_envelope.keys()),
            species=species,
            iteration=iteration,
            select_envelope=target_envelope,

            geos_index_use_secondary=True,
            geos_index_direct_block_read=False,
            geos_index_read_groups=False,
        )

    elif test_type == "8":
        print("Test type 8: GeoIndex, Index type: Min-Max, Storage: File, Secondary: Min-Max, Direct Block Read: False, Read Groups: True")

        single_query_test(
            bp_file_path=bp_file_path,
            geos_index=True,
            geos_index_type="minmax",
            geos_index_storage_backend="file",
            geos_index_save_path=index_path,
            geos_index_secondary_type="minmax",

            target_array=list(target_envelope.keys()),
            species=species,
            iteration=iteration,
            select_envelope=target_envelope,

            geos_index_use_secondary=True,
            geos_index_direct_block_read=False,
            geos_index_read_groups=True,
        )

    elif test_type == "9":
        print("Test type 9: GeoIndex, Index type: Rtree, Storage: File, Secondary: Min-Max, Direct Block Read: False, Read Groups: True")

        single_query_test(
            bp_file_path=bp_file_path,
            geos_index=True,
            geos_index_type="rtree",
            geos_index_storage_backend="file",
            geos_index_save_path=index_path,
            geos_index_secondary_type="minmax",

            target_array=list(target_envelope.keys()),
            species=species,
            iteration=iteration,
            select_envelope=target_envelope,

            geos_index_use_secondary=True,
            geos_index_direct_block_read=False,
            geos_index_read_groups=True,
        )
    
    elif test_type == "10":
        print("Test type 10: GeoIndex, Index type: Min-Max, Storage: File, Secondary: Min-Max, Direct Block Read: True, Read Groups: False")

        single_query_test(
            bp_file_path=bp_file_path,
            geos_index=True,
            geos_index_type="minmax",
            geos_index_storage_backend="file",
            geos_index_save_path=index_path,
            geos_index_secondary_type="minmax",

            target_array=list(target_envelope.keys()),
            species=species,
            iteration=iteration,
            select_envelope=target_envelope,

            geos_index_use_secondary=True,
            geos_index_direct_block_read=True,
            geos_index_read_groups=False,
        )

    elif test_type == "11":
        print("Test type 11: GeoIndex, Index type: Rtree, Storage: File, Secondary: Min-Max, Direct Block Read: True, Read Groups: False")

        single_query_test(
            bp_file_path=bp_file_path,
            geos_index=True,
            geos_index_type="rtree",
            geos_index_storage_backend="file",
            geos_index_save_path=index_path,
            geos_index_secondary_type="minmax",

            target_array=list(target_envelope.keys()),
            species=species,
            iteration=iteration,
            select_envelope=target_envelope,

            geos_index_use_secondary=True,
            geos_index_direct_block_read=True,
            geos_index_read_groups=False,
        )

    elif test_type == "12":
        print("Test type 12: GeoIndex, Index type: Min-Max, Storage: RocksDB, Secondary: None, Direct Block Read: True")

        single_query_test(
            bp_file_path=bp_file_path,
            geos_index=True,
            geos_index_type="minmax",
            geos_index_storage_backend="rocksdb",
            geos_index_save_path=index_path,
            geos_index_secondary_type="none",

            target_array=list(target_envelope.keys()),
            species=species,
            iteration=iteration,
            select_envelope=target_envelope,

            geos_index_use_secondary=False,
            geos_index_direct_block_read=True,
            geos_index_read_groups=False,
        )

    elif test_type == "13":
        print("Test type 13: GeoIndex, Index type: Rtree, Storage: RocksDB, Secondary: None, Direct Block Read: True")

        single_query_test(
            bp_file_path=bp_file_path,
            geos_index=True,
            geos_index_type="rtree",
            geos_index_storage_backend="rocksdb",
            geos_index_save_path=index_path,
            geos_index_secondary_type="none",

            target_array=list(target_envelope.keys()),
            species=species,
            iteration=iteration,
            select_envelope=target_envelope,

            geos_index_use_secondary=False,
            geos_index_direct_block_read=True,
            geos_index_read_groups=False,
        )
    
    elif test_type == "14":
        print("Test type 14: GeoIndex, Index type: Min-Max, Storage: RocksDB, Secondary: None, Direct Block Read: False, Read Groups: True")

        single_query_test(
            bp_file_path=bp_file_path,
            geos_index=True,
            geos_index_type="minmax",
            geos_index_storage_backend="rocksdb",
            geos_index_save_path=index_path,
            geos_index_secondary_type="none",

            target_array=list(target_envelope.keys()),
            species=species,
            iteration=iteration,
            select_envelope=target_envelope,

            geos_index_use_secondary=False,
            geos_index_direct_block_read=False,
            geos_index_read_groups=True,
        )
    
    elif test_type == "15":
        print("Test type 15: GeoIndex, Index type: Rtree, Storage: RocksDB, Secondary: None, Direct Block Read: False, Read Groups: True")

        single_query_test(
            bp_file_path=bp_file_path,
            geos_index=True,
            geos_index_type="rtree",
            geos_index_storage_backend="rocksdb",
            geos_index_save_path=index_path,
            geos_index_secondary_type="none",

            target_array=list(target_envelope.keys()),
            species=species,
            iteration=iteration,
            select_envelope=target_envelope,

            geos_index_use_secondary=False,
            geos_index_direct_block_read=False,
            geos_index_read_groups=True,
        )

    elif test_type == "16":
        print("Test type 16: GeoIndex, Index type: Min-Max, Storage: RocksDB, Secondary: Min-Max, Direct Block Read: False, Read Groups: False")

        single_query_test(
            bp_file_path=bp_file_path,
            geos_index=True,
            geos_index_type="minmax",
            geos_index_storage_backend="rocksdb",
            geos_index_save_path=index_path,
            geos_index_secondary_type="minmax",

            target_array=list(target_envelope.keys()),
            species=species,
            iteration=iteration,
            select_envelope=target_envelope,

            geos_index_use_secondary=True,
            geos_index_direct_block_read=False,
            geos_index_read_groups=False,
        )

    elif test_type == "17":
        print("Test type 17: GeoIndex, Index type: Rtree, Storage: RocksDB, Secondary: Min-Max, Direct Block Read: False, Read Groups: False")

        single_query_test(
            bp_file_path=bp_file_path,
            geos_index=True,
            geos_index_type="rtree",
            geos_index_storage_backend="rocksdb",
            geos_index_save_path=index_path,
            geos_index_secondary_type="minmax",

            target_array=list(target_envelope.keys()),
            species=species,
            iteration=iteration,
            select_envelope=target_envelope,

            geos_index_use_secondary=True,
            geos_index_direct_block_read=False,
            geos_index_read_groups=False,
        )

    elif test_type == "18":
        print("Test type 18: GeoIndex, Index type: Min-Max, Storage: RocksDB, Secondary: Min-Max, Direct Block Read: False, Read Groups: True")

        single_query_test(
            bp_file_path=bp_file_path,
            geos_index=True,
            geos_index_type="minmax",
            geos_index_storage_backend="rocksdb",
            geos_index_save_path=index_path,
            geos_index_secondary_type="minmax",

            target_array=list(target_envelope.keys()),
            species=species,
            iteration=iteration,
            select_envelope=target_envelope,

            geos_index_use_secondary=True,
            geos_index_direct_block_read=False,
            geos_index_read_groups=True,
        )

    elif test_type == "19":
        print("Test type 19: GeoIndex, Index type: Rtree, Storage: RocksDB, Secondary: Min-Max, Direct Block Read: False, Read Groups: True")

        single_query_test(
            bp_file_path=bp_file_path,
            geos_index=True,
            geos_index_type="rtree",
            geos_index_storage_backend="rocksdb",
            geos_index_save_path=index_path,
            geos_index_secondary_type="minmax",

            target_array=list(target_envelope.keys()),
            species=species,
            iteration=iteration,
            select_envelope=target_envelope,

            geos_index_use_secondary=True,
            geos_index_direct_block_read=False,
            geos_index_read_groups=True,
        )

    elif test_type == "20":
        print("Test type 20: GeoIndex, Index type: Min-Max, Storage: RocksDB, Secondary: Min-Max, Direct Block Read: True, Read Groups: False")

        single_query_test(
            bp_file_path=bp_file_path,
            geos_index=True,
            geos_index_type="minmax",
            geos_index_storage_backend="rocksdb",
            geos_index_save_path=index_path,
            geos_index_secondary_type="minmax",

            target_array=list(target_envelope.keys()),
            species=species,
            iteration=iteration,
            select_envelope=target_envelope,

            geos_index_use_secondary=True,
            geos_index_direct_block_read=True,
            geos_index_read_groups=False,
        )

    elif test_type == "21":
        print("Test type 21: GeoIndex, Index type: Rtree, Storage: RocksDB, Secondary: Min-Max, Direct Block Read: True, Read Groups: False")

        single_query_test(
            bp_file_path=bp_file_path,
            geos_index=True,
            geos_index_type="rtree",
            geos_index_storage_backend="rocksdb",
            geos_index_save_path=index_path,
            geos_index_secondary_type="minmax",

            target_array=list(target_envelope.keys()),
            species=species,
            iteration=iteration,
            select_envelope=target_envelope,

            geos_index_use_secondary=True,
            geos_index_direct_block_read=True,
            geos_index_read_groups=False,
        )