import os
import sys
sys.path.insert(0, os.getcwd())

import libfbindex
from scipy import constants
import pandas as pd

fbidx = libfbindex.GeosFastBitQuery("/data/gc/fastbit-test/cmake-build-debug/f_middle_ind", "adios2")
# result = fbidx.queryFastbitData("/data/9000/particles/hydrogen/momentum/x", 0, 130, 15020314, -1e-21, -2e-22)

# read block meta info
block_meta_path = "/data/gc/GEOSIndex/build-with-blosc/bp09000.blockmeta"
iteration=9000
block_meta_df = pd.read_csv(block_meta_path, sep=',', header=None, names=['iteration', 'block_start', 'block_count'])
block_meta_df = block_meta_df[block_meta_df['iteration'] == iteration]
block_meta_df = block_meta_df.sort_values(by=['block_start'])
# remove duplicate
block_meta_df = block_meta_df.drop_duplicates(subset=['block_start'])
block_meta_df = block_meta_df.reset_index(drop=True)

# for idx, row in block_meta_df.iterrows():
#     print(row['block_start'], row['block_count'])

species = "hydrogen"

if species == "electrons":
    mass = 9.1093829099999999e-31
elif species == "hydrogen":
    mass = 1.6726219236900000e-27
momentum_constant = 1. / (mass * constants.c)


account = 0
for block_id, row in block_meta_df.iterrows():
    # print(f"block_id: {block_id}, block_start: {row['block_start']}, block_count: {row['block_count']}")
    # result = fbidx.queryFastbitData("/data/9000/particles/hydrogen/momentum/x", 0, block_id, row['block_count'], -0.027963249432878957 / momentum_constant, -0.027351281465401 / momentum_constant)
    result = fbidx.queryFastbitData("/data/9000/particles/hydrogen/position/x", 0, block_id, row['block_count'], 3.646344732214823e-07, 5.6552881947895036e-07)
    account += len(result)
print(account)
