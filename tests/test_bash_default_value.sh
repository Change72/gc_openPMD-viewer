#!/bin/bash

# This script is used to run the benchmark tests in batch mode.

# Check if a command-line argument is provided
if [ $# -eq 0 ]; then
    # Set default value
    bpfile=""
else
    # Use the value provided as a command-line argument
    bpfile=$1
fi

python3 -u tests/test_bash_default_value.py --bpfile "$bpfile"
