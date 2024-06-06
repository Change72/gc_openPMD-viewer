#!/bin/bash

# Check if a command-line argument is provided
if [ $# -eq 0 ]; then
    # Set default value
    bpfile="/data/gc/rocksdb-index/WarpX/build/bin/diags/diag2"
    index="/data/gc/rocksdb-index/GEOSIndex/cmake-build-debug/diag2"
    iteration=500
    species="electrons"
    total_particle_num=41405256
    output_file="results/10g_iteration_500/benchmark_result_00001_to_01.csv"
else
    # Use the value provided as a command-line argument
    bpfile=$1
    index=$2
    iteration=$3
    species=$4
    total_particle_num=$5
    output_file=$6
fi

# Loop 1000 times
for ((i=1; i<=10000; i++)); do
    # Run the command with the given parameters
    nohup python3 -u benchmark/batch.py \
        --bpfile $bpfile \
        --index $index \
        --iteration $iteration \
	    --species $species \
        --select_set "x,y;ux,uy;x,y,ux,uy;x,ux,uy,uz;x,y,ux,uy,uz" \
        --threshold 0.01 \
	    --percentage_range 0.0001,0.1,10 \
        --total_particle_num $total_particle_num \
        --limit_block_num 500 \
        --output_file $output_file \
        > "log/benchmark_result_$(printf '%05d' $i).log" \
        2>&1 &
    sleep 120
    # if i / 20 == 0, Sleep for 3600 seconds
    # if [ $((i % 2)) -eq 0 ]; then
    #     sleep 1800
    # fi
done

