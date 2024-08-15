import numpy as np
import time

# Define constants and arrays
constants = type('consts', (), {'c': 3.0})
size = 100000000  # Example size for performance testing
m = np.full((size,), 2.0)
data = np.full((size,), 1.0)

# Method 1: Vectorized approach
start_time = time.time()
data *= 1. / (m * constants.c)
vectorized_time = time.time() - start_time
# print(f"Vectorized data: {data[:10]}")  # Print first 10 elements to verify
print(f"Vectorized time: {vectorized_time:.6f} seconds")

# Reset data array
data = np.full((size,), 1.0)

# # Method 2: Loop approach
# start_time = time.time()
# for i in range(data.size):
#     data[i] *= 1. / (m[i] * constants.c)
# loop_time = time.time() - start_time
# # print(f"Loop data: {data[:10]}")  # Print first 10 elements to verify
# print(f"Loop time: {loop_time:.6f} seconds")
#
# # Reset data array
# data = np.full((size,), 1.0)

# Method 3: Chunking approach
chunk_size = 10000  # Example chunk size
start_time = time.time()
for start in range(0, data.size, chunk_size):
    end = min(start + chunk_size, data.size)
    data[start:end] *= 1. / (m[start:end] * constants.c)
chunking_time = time.time() - start_time
# print(f"Chunking data: {data[:10]}")  # Print first 10 elements to verify
print(f"Chunking time: {chunking_time:.6f} seconds")

# Reset data array
data = np.full((size,), 1.0)

# Method 4: Using temporary array
start_time = time.time()
temp = np.full_like(m, 1.0)  # Create a temporary array
m *= constants.c  # Compute intermediate values
temp /= m  # Compute final values
data *= temp  # Update data in place
temp_array_time = time.time() - start_time
# print(f"Temp array data: {data[:10]}")  # Print first 10 elements to verify
print(f"Temp array time: {temp_array_time:.6f} seconds")