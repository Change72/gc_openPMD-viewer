import numpy as np
import time

from numba import njit

# Create a large ndarray
large_array = np.arange(1000000)  # 1 million elements

# Define the ranges to extract
ranges = [(0, 3), (6, 8), (12, 15), (100, 105), (1000, 1010), (10000, 10020), (100000, 100050)]

# Method 1: Using np.hstack
start_time = time.time()
slices = [large_array[start:end+1] for start, end in ranges]
new_array_hstack = np.hstack(slices)
time_hstack = time.time() - start_time

# Method 2: Using an array mask
start_time = time.time()
mask = np.zeros_like(large_array, dtype=bool)
for start, end in ranges:
    mask[start:end+1] = True
new_array_mask = large_array[mask]
time_mask = time.time() - start_time

# Method 3: Preallocating and Direct Filling
start_time = time.time()
total_length = sum(end - start + 1 for start, end in ranges)
new_array_prealloc = np.empty(total_length, dtype=large_array.dtype)

current_position = 0
for start, end in ranges:
    length = end - start + 1
    new_array_prealloc[current_position:current_position + length] = large_array[start:end + 1]
    current_position += length

time_prealloc = time.time() - start_time

# Ensure all methods produce the same result
assert np.array_equal(new_array_hstack, new_array_mask)
assert np.array_equal(new_array_hstack, new_array_prealloc)

print(f"Time using np.hstack: {time_hstack:.6f} seconds")
print(f"Time using array mask: {time_mask:.6f} seconds")
print(f"Time using preallocation: {time_prealloc:.6f} seconds")


# Create a large ndarray
large_array = np.arange(1000000)  # 1 million elements

# Define the ranges to extract
ranges = [(0, 3), (6, 8), (12, 15), (100, 105), (1000, 1010), (10000, 10020), (100000, 100050)]

# Function to calculate total length
@njit
def calculate_total_length(ranges):
    total_length = 0
    for start, end in ranges:
        total_length += (end - start + 1)
    return total_length

# Numba JIT-compiled function to extract ranges
@njit
def extract_ranges_jit(array, ranges):
    total_length = calculate_total_length(ranges)
    result = np.empty(total_length, dtype=array.dtype)

    current_position = 0
    for start, end in ranges:
        length = end - start + 1
        result[current_position:current_position + length] = array[start:end + 1]
        current_position += length

    return result

# Measure the time of the Numba-optimized function
start_time = time.time()
new_array_jit = extract_ranges_jit(large_array, ranges)
time_jit = time.time() - start_time

# Method: Preallocating and Direct Filling
start_time = time.time()
total_length = sum(end - start + 1 for start, end in ranges)
new_array_prealloc = np.empty(total_length, dtype=large_array.dtype)

current_position = 0
for start, end in ranges:
    length = end - start + 1
    new_array_prealloc[current_position:current_position + length] = large_array[start:end + 1]
    current_position += length

time_prealloc = time.time() - start_time

# Ensure both methods produce the same result
assert np.array_equal(new_array_jit, new_array_prealloc)

print(f"Time using preallocation: {time_prealloc:.6f} seconds")
print(f"Time using Numba JIT: {time_jit:.6f} seconds")
print("New array from specified slices (using Numba JIT):")
print(new_array_jit)