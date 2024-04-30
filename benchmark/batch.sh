#!/bin/bash

# Check if a command-line argument is provided
if [ $# -eq 0 ]; then
    # Set default value
    bpfile="/data/gc/rocksdb-index/WarpX/build/bin/diags/diag2"
    index="/data/gc/rocksdb-index/GEOSIndex/cmake-build-debug/diag2"
    iteration=500
else
    # Use the value provided as a command-line argument
    bpfile=$1
    index=$2
    iteration=$3
fi

# Loop 1000 times
for ((i=1; i<=10000; i++)); do
    # Run the command with the given parameters
    nohup python3 -u benchmark/batch.py \
        --bpfile $bpfile \
        --index $index \
        --iteration $iteration \
	    --species "hydrogen" \
        --select_set "x,y,z;ux,uy,uz;x,y,z,ux,uy,uz" \
        --threshold 0.01 \
	    --percentage_range 0.0001 \
        --total_particle_num 13122018434 \
        --output_file "results/500g_iteration_10000/benchmark_result_00001_to_01.csv" \
        > "log/benchmark_result_$(printf '%05d' $i).log" \
        2>&1 &
    sleep 3600
    # if i / 20 == 0, Sleep for 3600 seconds
    # if [ $((i % 2)) -eq 0 ]; then
    #     sleep 1800
    # fi
done

