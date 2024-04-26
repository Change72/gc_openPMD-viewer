import re
import argparse
import matplotlib.pyplot as plt

parser = argparse.ArgumentParser(description='Batch Benchmark Generator Script')
parser.add_argument('--log_file_path', type=str, help='log file path')

args = parser.parse_args()
log_file_path = args.log_file_path

# Initialize lists to store data
block_nums = []
counts = []
times = []

# Read the log file and extract data
with open(log_file_path, 'r') as log_file:
    for line in log_file:
        if 'chunk' in line:
            # chunk: 4 read in 0.13641095161437988 s start: 23981034 end: 34138208
            block_num = int(re.search('chunk: (\d+)', line).group(1))
            time = float(re.search('(\d+\.\d+) s', line).group(1))
            start = int(re.search('start: (\d+)', line).group(1))
            end = int(re.search('end: (\d+)', line).group(1))
            count = end - start
            # print('block_num:', block_num, 'count:', count, 'time:', time) 

            block_nums.append(block_num)
            counts.append(count)
            times.append(time)

# remove the last element from the lists
# block_nums.pop()
# counts.pop()
# times.pop()

# Create two subplots
plt.figure(figsize=(18, 6))

# Plot 1: blockNum - Count
plt.subplot(1, 3, 1)
plt.scatter(block_nums, counts, marker='o', linestyle='-', color='b')
plt.title('blockSeq - Count')
plt.xlabel('blockSeq')
plt.ylabel('Count')

# Plot 2: blockNum - time
plt.subplot(1, 3, 2)
plt.scatter(block_nums, times, marker='o', linestyle='-', color='r')
plt.title('blockSeq - Time')
plt.xlabel('blockSeq')
plt.ylabel('Time (seconds)')

# Plot 3: Count - time
plt.subplot(1, 3, 3)
plt.scatter(counts, times, marker='o', linestyle='-', color='g')
plt.title('Count - Time')
plt.xlabel('Count')
plt.ylabel('Time (seconds)')

# Save the blockNum - Time plot as an image
plt.savefig(log_file_path.replace('.log', '.png').replace('log/', 'output/'))

# Close the plots
plt.close()