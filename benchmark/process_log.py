import os
import re
import argparse
import pandas as pd

def extract_data_from_log(log_file):
    """
    Extracts relevant information from a log file.
    """
    target_percentage = None
    current_percentage = None
    iteration = None
    species = None
    select_set = None
    expand_set = None
    query_seq = None
    envelope = None
    test_type = None
    test_name = None
    index_type = None
    storage = None
    secondary = None
    direct_block_read = None
    read_groups = None
    query_index_time_elapsed = None
    query_result_size = None
    remove_duplication_time_elapsed = None
    sort_block_metadata_time_elapsed = None
    find_optimal_read_solution_time_elapsed = None
    generate_select_array_time_elapsed = None
    get_target_data_time_elapsed = []
    get_support_data_time_elapsed = []
    data_calculation_time_elapsed = []
    data_apply_select_time_elapsed = []
    apply_particle_level_select_array_time_elapsed = []
    total_time_elapsed = None
    data_size = None

    with open(log_file, 'r') as file:
        lines = file.readlines()
        for line in lines:
            if 'target_percentage' in line:
                target_percentage = float(line.split()[1])

            elif 'current_percentage' in line:
                current_percentage = float(line.split()[1])

            elif 'iteration' in line:
                iteration = int(line.split()[1])

            elif 'species' in line:
                species = line.split()[1]

            elif 'select_set' in line:
                select_set = ''.join(line.split()[1:])

            elif 'expand_set' in line:
                expand_set = ''.join(line.split()[1:])

            elif 'Query seq' in line:
                # use regex to extract
                # Query seq: 1, Target percentage: 0.0001, envelope: {'ux': [3.21154209650796e-05, 6.509957656883304e-05], 'uy': [-0.0006029176508830782, -0.0002539190030947781], 'uz': [-0.0004867193636861238, -0.00021000904899415816]}
                regex_result = re.compile(r'Query seq: (\d+), Target percentage: (\d+\.\d+), envelope: ({.*})').findall(line)
                if regex_result:
                    query_seq = int(regex_result[0][0])
                    envelope = eval(regex_result[0][2])

            elif 'Test type' in line:
                # Test type 1: Original openPMD-viewer method
                # Test type 2: GeoIndex, Index type: Min-Max, Storage: File, Secondary: None, Direct Block Read: True
                # Test type 4: GeoIndex, Index type: Min-Max, Storage: File, Secondary: None, Direct Block Read: False, Read Groups: True")
                regex_result = re.compile(r'Test type (\d+): (.*?) ').findall(line)
                if regex_result:
                    test_type = int(regex_result[0][0])
                    test_name = (regex_result[0][1]).replace(',', '')

                regex_result = re.compile(r'Index type: (.*?), Storage: (.*?), Secondary: (.*?), Direct Block Read: (.*)').findall(line)
                if regex_result:
                    index_type = regex_result[0][0]
                    storage = regex_result[0][1]
                    secondary = regex_result[0][2]
                    direct_block_read = regex_result[0][3][:5].replace(',', '')
                
                regex_result = re.compile(r'Read Groups: (.*)').findall(line)
                read_groups = False
                if regex_result:
                    read_groups = regex_result[0]

            elif 'query index' in line:
                # query index: Time elapsed:  0.08427143096923828
                regex_result = re.compile(r'Time elapsed: (.*)').findall(line)
                if regex_result:
                    query_index_time_elapsed = float(regex_result[0])

            elif 'The size of the query result' in line:
                # The size of the query result:  2169
                regex_result = re.compile(r'The size of the query result: (.*)').findall(line)
                if regex_result:
                    query_result_size = int(regex_result[0])

            elif 'remove duplication' in line:
                # remove duplication. Time elapsed:  0.004973649978637695
                regex_result = re.compile(r'Time elapsed: (.*)').findall(line)
                if regex_result:
                    remove_duplication_time_elapsed = float(regex_result[0])

            elif 'sort block metadata by block start' in line:
                # sort block metadata by block start. Time elapsed:  0.0005142688751220703
                regex_result = re.compile(r'Time elapsed: (.*)').findall(line)
                if regex_result:
                    sort_block_metadata_time_elapsed = float(regex_result[0])

            elif 'find optimal read solution' in line:
                # find optimal read solution. Time elapsed:  0.02496027946472168
                regex_result = re.compile(r'Time elapsed: (.*)').findall(line)
                if regex_result:
                    find_optimal_read_solution_time_elapsed = float(regex_result[0])

            elif 'generate select array' in line:
                # generate select array. Time elapsed:  0.001024007797241211
                # Direct block read. generate select array. Time elapsed:  0.008704900741577148
                regex_result = re.compile(r'Time elapsed: (.*)').findall(line)
                if regex_result:
                    generate_select_array_time_elapsed = float(regex_result[0])

            elif 'get target data' in line:
                # get target data: x. Time elapsed:  24.65029001235962
                regex_result = re.compile(r'Time elapsed: (.*)').findall(line)
                if regex_result:
                    get_target_data_time_elapsed.append(float(regex_result[0]))

            elif 'read for' in line or 'for read' in line or 'get support data' in line:
                # get position offset for read x. Time elapsed:  0.16732120513916016
                # get mass read for ux. Time elapsed:  0.1673438549041748
                regex_result = re.compile(r'Time elapsed: (.*)').findall(line)
                if regex_result:
                    get_support_data_time_elapsed.append(float(regex_result[0]))

            elif ('data' in line and 'index select array' not in line and 'read data from disk' not in line and 'Total Time' not in line) or 'data apply support data' in line:
                # data *= norm_factor. Time elapsed:  0.26402854919433594
                # data += offset. Time elapsed:  0.04721331596374512
                regex_result = re.compile(r'Time elapsed: (.*)').findall(line)
                if regex_result:
                    data_calculation_time_elapsed.append(float(regex_result[0]))

            elif 'calculate particle level select array' in line:
                # data apply index select array. Time elapsed:  0.04328322410583496
                regex_result = re.compile(r'Time elapsed: (.*)').findall(line)
                if regex_result:
                    data_apply_select_time_elapsed.append(float(regex_result[0]))

            elif 'apply particle level select array' in line:
                # apply particle level select array. Time elapsed:  76.21706938743591
                regex_result = re.compile(r'Time elapsed: (.*)').findall(line)
                if regex_result:
                    apply_particle_level_select_array_time_elapsed.append(float(regex_result[0]))

            elif 'Total Time' in line:
                # Total Time: 149.23700332641602, data size: 4163
                regex_result = re.compile(r'Total Time: (.*?), data size: (\d*)').findall(line[:-1])
                if regex_result:
                    total_time_elapsed = float(regex_result[0][0])
                    data_size = int(regex_result[0][1])
    
    return {
        'query_seq': query_seq,
        'target_percentage': target_percentage,
        'select_set': select_set,
        'test_type': test_type,
        'test_name': test_name,
        'index_type': index_type,
        'storage': storage,
        'secondary': secondary,
        'direct_block_read': direct_block_read,
        'read_groups': read_groups,

        'query_index_time_elapsed': query_index_time_elapsed,
        'remove_duplication_time_elapsed': remove_duplication_time_elapsed,
        'sort_block_metadata_time_elapsed': sort_block_metadata_time_elapsed,
        'find_optimal_read_solution_time_elapsed': find_optimal_read_solution_time_elapsed,
        'generate_select_array_time_elapsed': generate_select_array_time_elapsed,
        'get_target_data_time_elapsed': sum(get_target_data_time_elapsed),
        'get_support_data_time_elapsed': sum(get_support_data_time_elapsed),
        'data_calculation_time_elapsed': sum(data_calculation_time_elapsed),
        'data_apply_select_time_elapsed': sum(data_apply_select_time_elapsed),
        'apply_particle_level_select_array_time_elapsed': sum(apply_particle_level_select_array_time_elapsed),
        'total_time_elapsed': total_time_elapsed,

        'query_result_size': query_result_size,
        'current_percentage': current_percentage,
        'iteration': iteration,
        'species': species,
        'expand_set': expand_set,
        'envelope': envelope,
        'data_size': data_size
    }


def process_folder(folder_path):
    """
    Processes all log files in the specified folder.
    """
    data = []
    for file_name in os.listdir(folder_path):
        if file_name.endswith('.log'):
            log_file = os.path.join(folder_path, file_name)
            data.append(extract_data_from_log(log_file))
    
    df = pd.DataFrame(data)
    return df

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Batch Benchmark Log Processor')
    parser.add_argument('--log_folder', type=str, help='Path to the folder containing log files', default='results/10g_iteration_500/selected_1')
    parser.add_argument('--output_file', type=str, help='Path to the output CSV file', default='results/10g_iteration_500/benchmark_result.csv')

    args = parser.parse_args()
    folder_path = args.log_folder
    output_file = args.output_file

    df = process_folder(folder_path)
    # sort by query_seq ascending, test_type ascending
    df = df.sort_values(by=['query_seq', 'test_type'])
    # turn target_percentage into a % string
    df['target_percentage'] = df['target_percentage'].apply(lambda x: f'{x:.2%}')
    df.to_csv(output_file, index=False)
    print(df)
