#!/bin/bash

# This script is used to run the benchmark tests in batch mode.

# Check if a command-line argument is provided
if [ $# -eq 0 ]; then
    # Set default value
    bpfile="/nvme/gc/diag2"
    index="/data/gc/rocksdb-index/GEOSIndex/cmake-build-debug/diag2"
    iteration=500
    species="electrons"
    select_n=20
    result_dir="results/10g_iteration_500"
    test_type="1"
    percentage_num=4
    limit_memory_usage=""
    block_meta_path=""
else
    # Use the value provided as a command-line argument
    bpfile=$1
    index=$2
    iteration=$3
    species=$4
    select_n=$5
    result_dir=$6
    test_type=$7
    percentage_num=$8
    limit_memory_usage=$9
    block_meta_path=${10}
fi

# if not exist the result directory, Create: $result_dir + selected_n
output_dir="${result_dir}/selected_${select_n}"
if [ ! -d "${output_dir}" ]; then
    mkdir -p ${output_dir}
fi

# result_dir + select_n
benchmark_query_path="${result_dir}/selected_${select_n}_queries.csv"
# Convert the comma-separated string to an array
IFS=',' read -ra test_type_array <<< "$test_type"

# Function to display memory usage and log to file
function monitor_memory_usage_and_log() {
    local log_file=$1
    current_date_time=$(date +'%Y-%m-%d %H:%M:%S')
    echo "Current Date and time: $current_date_time" >> "$log_file"
    echo "Memory usage:" >> "$log_file"
    free -hm >> "$log_file"
}

# Function to monitor process status and memory usage
function monitor_process() {
    local pid=$1
    local log_file=$2

    # Loop until the process completes
    while kill -0 $pid 2>/dev/null; do
        # Display memory usage periodically and log to file
        monitor_memory_usage_and_log "$log_file"
        sleep 2  # Adjust sleep interval as needed
    done
}

# Loop select_n times
for j in "${test_type_array[@]}"; do
    for ((i=0; i<${select_n} * ${percentage_num} * 5; i++)); do
        echo 3 | sudo tee /proc/sys/vm/drop_caches

        # Run the command with the given parameters
        nohup python3 -u benchmark/batchTest.py \
            --bpfile $bpfile \
            --index $index \
            --iteration $iteration \
            --species $species \
            --query_seq $i \
            --test_type $j \
            --query_path $benchmark_query_path \
            --limit_memory_usage "$limit_memory_usage" \
            --block_meta_path "$block_meta_path" \
            > ${output_dir}/type_${j}_$(printf '%05d' $i).log 2>&1 &
        
        # Get the PID of the last background process
        pid=$!

        # Monitor the process (e.g., memory usage) in the background
        monitor_process $pid "${output_dir}/type_${j}_$(printf '%05d' $i).memlog"

    done
done
