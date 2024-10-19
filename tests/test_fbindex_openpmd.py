import os
import sys
sys.path.insert(0, os.getcwd())
import time

import argparse

from openpmd_viewer import OpenPMDTimeSeries
from scipy import constants

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Batch Benchmark Generator Script')
    parser.add_argument('--bpfile', type=str, help='bp file path')
    parser.add_argument('--iteration', type=str, help='iteration number', default=10000)
    parser.add_argument('--species', type=str, help='species', default='electrons')
    parser.add_argument('--index_path', type=str, help='index path')
    parser.add_argument('--metadata_path', type=str, help='metadata path')
    parser.add_argument('--envelope', type=str, help='envelope')

    args = parser.parse_args()
    bp_file_path = args.bpfile
    iteration = int(args.iteration)
    species = args.species
    index_path = args.index_path
    metadata_path = args.metadata_path
    envelope = args.envelope

    start = time.time()
    ts = OpenPMDTimeSeries(bp_file_path, fastbit_index=True, geos_index_save_path=index_path, geos_index_storage_backend="adios2")


    result = ts.get_particle(var_list=['y'], iteration=iteration, species=species, select=eval(envelope), block_meta_path=metadata_path)
    print(len(result[0]))
    end = time.time()
    print(f"Total Time: {end - start}, data size: {result[0].size}")
