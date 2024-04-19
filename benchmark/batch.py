import os
import time
import argparse
import sys

sys.path.insert(0, os.getcwd())

from benchmark import BenchmarkGenerator
from openpmd_viewer import OpenPMDTimeSeries


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Batch Benchmark Generator Script')
    parser.add_argument('--bpfile', type=str, help='bp file path')
    parser.add_argument('--index', type=str, help='geoindex path (rtree)')
    parser.add_argument('--iteration', type=str, help='iteration number', default=10000)
    # select_set_list = [{'x', 'y', 'z'}, {'ux'}, {'ux', 'uy', 'uz'}, {'x', 'y', 'z', 'ux', 'uy', 'uz'}]
    parser.add_argument('--select_set', type=str, help='select set', default='x,y,z')
    # percentage_range=[0.0001, 0.1, 10]
    parser.add_argument('--percentage_range', type=str, help='percentage range (if len=3, (start, end, step), else [percentage list])', default='0.0001,0.1,10')
    parser.add_argument('--species', type=str, help='species', default='electrons')
    parser.add_argument('--total_particle_num', type=str, help="total particle number", default=0)
    parser.add_argument('--learning_rate', type=str, help="learning rate", default=0.99)
    parser.add_argument('--threshold', type=str, help="threshold", default=0.1)
    parser.add_argument('--output_file', type=str, help="output file path", default="benchmark_result.csv")

    args = parser.parse_args()
    bp_file_path = args.bpfile
    index_path = args.index
    iteration = int(args.iteration)
    select_set_list = [set(x.split(',')) for x in args.select_set.split(';')]
    percentage_range = [float(x) for x in args.percentage_range.split(',')]
    species = args.species
    total_particle_num = int(args.total_particle_num)
    learning_rate = float(args.learning_rate)
    threshold = float(args.threshold)
    output_file = args.output_file

    if not bp_file_path or not index_path:
        raise ValueError("bpfile and index are required")

    bg = BenchmarkGenerator(bp_file_path=bp_file_path, geos_index_path=index_path)
    # select_set_list = [{'x'}, {'x', 'y', 'z'}, {'ux'}, {'ux', 'uy', 'uz'}, {'x', 'y', 'z', 'ux', 'uy', 'uz'}]
    # [0.0001, 0.1, 10]

    for select_set in select_set_list:
        result = bg.generateRandomQuery(species=species, iteration=iteration, percentage_range=percentage_range,
                                        select_set=select_set, threshold=threshold, 
                                        learning_rate=learning_rate, total_particle_num=total_particle_num,
                                        output_file=output_file)



