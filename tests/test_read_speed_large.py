import os
import sys

sys.path.insert(0, os.getcwd())

import time
from openpmd_viewer import OpenPMDTimeSeries

bp_file_path = '/nvme/gc/openPMD/'
geos_index_path = "/data/gc/rocksdb-index/GEOSIndex/build-with-blosc/bp10000"

species = "hydrogen"
iteration = 10000

geos_ts = OpenPMDTimeSeries(bp_file_path, backend='openpmd-api', geos_index=True, geos_index_type="minmax",
                                 geos_index_storage_backend="file", geos_index_save_path=geos_index_path)
start = time.time()
result_2 = geos_ts.get_particle(['ux'], species=species, iteration=iteration, geos_index_read_groups=True, skip_offset=True, select={'ux': [-0.0019551650236630095, -0.0019533063791186537]})
end = time.time()
print("Total time elapsed: ", end - start)

start = time.time()
result_1 = geos_ts.get_particle(['ux'], species=species, iteration=iteration, geos_index_read_groups=True, select={'ux': [-0.0019551650236630095, -0.0019533063791186537]})
end = time.time()
print("Total time elapsed: ", end - start)

import numpy as np
print(len(result_1[0]), len(result_2[0]))
print(np.array_equal(result_1[0], result_2[0]))