import os
import sys

sys.path.insert(0, os.getcwd())

import time
from openpmd_viewer import OpenPMDTimeSeries
from scipy import constants

# bp_file_path = '/nvme/gc/middle/data_b13206/'
# geos_index_path = "/data/gc/rocksdb-index/GEOSIndex/cmake-build-debug/bp09000"
# bp_file_path = '/data/gc/middle_16/'
# geos_index_path = "/data/gc/GEOSIndex/build-with-blosc/bp09000"

bp_file_path = '/data/gc/middle_16/'
geos_index_path = "/data/gc/GEOSIndex/build-with-blosc/bp09000"


species = "hydrogen"
iteration = 9000

if species == "electrons":
    mass = 9.1093829099999999e-31
elif species == "hydrogen":
    mass = 1.6726219236900000e-27

momentum_constant = 1. / (mass * constants.c)

geos_ts = OpenPMDTimeSeries(bp_file_path, backend='openpmd-api', geos_index=True, geos_index_type="minmax",
                                 geos_index_storage_backend="file", geos_index_save_path=geos_index_path, 
                                geos_index_secondary_type="minmax"
                                 )
# target_select = {'uz': [2.35706e-21 * momentum_constant, 2.36506e-21 * momentum_constant]}
# target_select = {'uz': [2.35706e-21 * momentum_constant, 2.39606e-21 * momentum_constant]}
# target_select = {'uz': [2.35706e-21 * momentum_constant, 2.40606e-21 * momentum_constant]}
# 1%
# target_select = {'uz': [0, 0.005898306273075093]}
# 0.10%
# target_select = {'uz': [0, 0.005038306273075093]}
# 0.01%
target_select = {'uz': [0.004700587593000333, 0.004798306273075093]}
# target_select = {'uz': [0.009498306273075093, 0.009899306273075093]}
print(target_select)


start = time.time()
# x_in_envelope = geos_ts.get_particle(['ux'], species=species, iteration=iteration, geos_index_read_groups=True, select={'ux': [0, 1]})
x_in_envelope = geos_ts.get_particle(['uz'], species=species, iteration=iteration, geos_index_direct_block_read=True, select=target_select)

end = time.time()
print("Total Time elapsed: ", end - start)

start = time.time()
# x_in_envelope = geos_ts.get_particle(['ux'], species=species, iteration=iteration, geos_index_read_groups=True, select={'ux': [0, 1]})
x_in_envelope = geos_ts.get_particle(['uz'], species=species, iteration=iteration, geos_index_direct_block_read=True, select=target_select, geos_index_use_secondary=True)

end = time.time()
print("Total Time elapsed of 10M: ", end - start)


geos_index_path = "/data/gc/GEOSIndex/build-with-blosc/bp09000_1k"
geos_ts_1k = OpenPMDTimeSeries(bp_file_path, backend='openpmd-api', geos_index=True, geos_index_type="minmax",
                                 geos_index_storage_backend="file", geos_index_save_path=geos_index_path, 
                                geos_index_secondary_type="minmax"
                                 )

start = time.time()
# x_in_envelope = geos_ts.get_particle(['ux'], species=species, iteration=iteration, geos_index_read_groups=True, select={'ux': [0, 1]})
x_in_envelope = geos_ts_1k.get_particle(['uz'], species=species, iteration=iteration, geos_index_direct_block_read=True, select=target_select, geos_index_use_secondary=True)

end = time.time()
print("Total Time elapsed of 1K: ", end - start)

geos_index_path = "/data/gc/GEOSIndex/build-with-blosc/bp09000_100"
geos_ts_100 = OpenPMDTimeSeries(bp_file_path, backend='openpmd-api', geos_index=True, geos_index_type="minmax",
                                 geos_index_storage_backend="file", geos_index_save_path=geos_index_path, 
                                geos_index_secondary_type="minmax"
                                 )

start = time.time()
# x_in_envelope = geos_ts.get_particle(['ux'], species=species, iteration=iteration, geos_index_read_groups=True, select={'ux': [0, 1]})
x_in_envelope = geos_ts_100.get_particle(['uz'], species=species, iteration=iteration, geos_index_direct_block_read=True, select=target_select, geos_index_use_secondary=True)

end = time.time()
print("Total Time elapsed of 100: ", end - start)

# start = time.time()
# # x_in_envelope = geos_ts.get_particle(['ux'], species=species, iteration=iteration, geos_index_read_groups=True, select={'ux': [0, 1]})
# x_in_envelope = geos_ts.get_particle(['ux'], species=species, iteration=iteration, geos_index_read_groups=True, select=target_select, geos_index_use_secondary=True)

# end = time.time()
# print("Total Time elapsed: ", end - start)

print(len(x_in_envelope[0]))