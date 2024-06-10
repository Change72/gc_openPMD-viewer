'''
source csv:
query_seq,target_percentage,select_set,test_type,test_name,index_type,storage,secondary,direct_block_read,read_groups,query_index_time_elapsed,remove_duplication_time_elapsed,sort_block_metadata_time_elapsed,find_optimal_read_solution_time_elapsed,generate_select_array_time_elapsed,get_target_data_time_elapsed,get_support_data_time_elapsed,data_calculation_time_elapsed,data_apply_select_time_elapsed,apply_particle_level_select_array_time_elapsed,total_time_elapsed,query_result_size,current_percentage,iteration,species,expand_set,envelope,data_size
0,0.01%,"('ux',)",1,Original,,,,,False,,,,,,118.22624921798706,7.334915637969971,11.795854330062866,1.9846346378326416,0.2186124324798584,139.83869791030884,,9.9e-05,9000,hydrogen,{'ux'},"{'ux': [0.0032448082260353095, 0.0032476844604416716]}",92466
1,0.01%,"('ux',)",1,Original,,,,,False,,,,,,112.6421148777008,7.391603708267212,11.850954055786133,1.996948480606079,0.22235894203186035,134.38244247436523,,0.000101,9000,hydrogen,{'ux'},"{'ux': [-0.0006646213925663649, -0.0006618219265703626]}",93552
2,0.01%,"('ux',)",1,Original,,,,,False,,,,,,112.42552304267883,7.430102825164795,12.007975339889526,2.062933921813965,0.21687674522399902,134.41904187202454,,0.0001,9000,hydrogen,{'ux'},"{'ux': [0.0012912866594012207, 0.0012937265437561415]}",93295
3,0.01%,"('ux',)",1,Original,,,,,False,,,,,,116.99430227279663,7.44066309928894,11.97099757194519,2.029893159866333,0.22768211364746094,138.943749666214,,0.000101,9000,hydrogen,{'ux'},"{'ux': [-0.0021310071960015504, -0.0021276786126757197]}",93607

output csv:
target_percentage,current_percentage,iteration,species,select_set,expand_set,envelope
0.0001,0.0001009775184097,500,electrons,"('ux',)",['ux'],"{'ux': [-0.0009535118682907291, -0.000952485969597308]}"
0.0001,9.967333615809548e-05,500,electrons,"('ux',)",['ux'],"{'ux': [-1.4461087910478131e-06, -1.419777591066521e-06]}"
0.0001,0.0001007843062243,500,electrons,"('ux',)",['ux'],"{'ux': [2.088437676840042e-05, 2.0971842571867772e-05]}"
0.0001,0.0001006635486084,500,electrons,"('ux',)",['ux'],"{'ux': [0.0011636304916018702, 0.001165019165892714]}"
'''

import pandas as pd
import numpy as np
import os

def select_n_from_results(source_csv, output_csv):
    df = pd.read_csv(source_csv)
    df = df[['target_percentage', 'current_percentage', 'iteration', 'species', 'select_set', 'expand_set', 'envelope']]
    df['target_percentage'] = df['target_percentage'].apply(lambda x: float(x.replace('%', '')) * 0.01)
    df.to_csv(output_csv, index=False)

import argparse

parser = argparse.ArgumentParser(description='Benchmark Select N Script')
parser.add_argument('--source_csv', type=str, help='source csv file path', default="results/10g_iteration_500/benchmark_result_00001_to_01.csv")
parser.add_argument('--output_csv', type=str, help='output csv file path', default="results/10g_iteration_500/selected_100_queries.csv")

source_csv = parser.parse_args().source_csv
output_csv = parser.parse_args().output_csv

select_n_from_results(source_csv, output_csv)