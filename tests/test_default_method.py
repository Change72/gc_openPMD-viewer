import os
import time
import argparse

import sys
sys.path.insert(0, os.getcwd())

from openpmd_viewer import OpenPMDTimeSeries

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Batch Benchmark Generator Script')
    parser.add_argument('--bpfile', type=str, help='bp file path')
    parser.add_argument('--iteration', type=str, help='iteration number', default=10000)
    parser.add_argument('--species', type=str, help='species', default='electrons')
    parser.add_argument('--envelope', type=str, help='envelope')

    args = parser.parse_args()
    bp_file_path = args.bpfile
    iteration = int(args.iteration)
    species = args.species
    envelope = args.envelope

    target_envelope = None
    if envelope:
        target_envelope = eval(envelope)

    ts = OpenPMDTimeSeries(bp_file_path, backend='openpmd-api')

    start = time.time()
    result = ts.get_particle(var_list=(list(target_envelope.keys()) if target_envelope else ['x']), iteration=iteration, species=species, select=target_envelope)
    end = time.time()

    print(f"Total Time: {end - start}, data size: {result[0].size}")
    print()
