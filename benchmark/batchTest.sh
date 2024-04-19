#!/bin/bash

# This script is used to run the benchmark tests in batch mode.

# Check if a command-line argument is provided
if [ $# -eq 0 ]; then
    # Set default value
    bpfile="/data/gc/rocksdb-index/WarpX/build/bin/diags/diag2"
    index="/data/gc/rocksdb-index/GEOSIndex/cmake-build-debug/diag2"
    select_n=1
    result_dir="results/10g_iteration_500"
    test_type="16,18,20"
else
    # Use the value provided as a command-line argument
    bpfile=$1
    index=$2
    select_n=$3
    result_dir=$4
    test_type=$5
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

# Loop select_n times
for j in "${test_type_array[@]}"; do
    for ((i=0; i<${select_n} * 20; i++)); do
        # Run the command with the given parameters
        python3 -u benchmark/batchTest.py \
            --bpfile $bpfile \
            --index $index \
            --iteration 500 \
            --query_seq $i \
            --test_type $j \
            --query_path $benchmark_query_path \
            > ${output_dir}/type_${j}_$(printf '%05d' $i).log

        echo 3 | sudo tee /proc/sys/vm/drop_caches
    done
done
