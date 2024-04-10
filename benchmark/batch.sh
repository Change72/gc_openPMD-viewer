#!/bin/bash

# Loop 1000 times
for ((i=1; i<=1000; i++)); do
    # Run the command with the given parameters
    nohup python3 -u benchmark/batch.py --bpfile "/data/gc/rocksdb-index/WarpX/build/bin/diags/diag2" --index "/data/gc/rocksdb-index/GEOSIndex/cmake-build-debug/diag2" --iteration 500 --threshold=0.01 --output_file "results/10g_iteration_500/benchmark_result_00001_to_01.csv" > "results/log/benchmark_result_$(printf '%05d' $i).log" 2>&1 &
    # if i / 20 == 0, Sleep for 3600 seconds
    if [ $((i % 20)) -eq 0 ]; then
        sleep 3600
    fi
done

