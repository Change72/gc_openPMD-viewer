import os
import time
import sys
sys.path.insert(0, os.getcwd())

import geosindex

import matplotlib.pyplot as plt
import numpy as np

from openpmd_viewer import OpenPMDTimeSeries

# 1. Original

# bp_file_path = os.environ.get('PSCRATCH')
bp_file_path = "/nvme/gc/"
index_path = "/data/gc/rocksdb-index/GEOSIndex/build-with-blosc/bp010000"

# bp_file_path = "/data/gc/rocksdb-index/WarpX/build/bin/diags/diag2"
# index_path = "/data/gc/rocksdb-index/GEOSIndex/cmake-build-debug/diag2"
print(bp_file_path)
# ts = OpenPMDTimeSeries(bp_file_path, backend='openpmd-api')

# start = time.time()
# z_all = ts.get_particle(['uz'], species='electrons', iteration=10000)
# end = time.time()
# print("1. Z without select. Time elapsed: ", end - start, "length: ", len(z_all[0]))

ts = OpenPMDTimeSeries(bp_file_path, backend='openpmd-api', geos_index=True, geos_index_type="rtree",
                            geos_index_storage_backend="file",
                            geos_index_save_path=index_path)

start = time.time()
z_selected_original = ts.get_particle( ['z'], species='electrons', iteration=10000, select={'z':[-np.inf, np.inf]}, geos_index_read_groups=True, skip_offset=True)
# z_selected_original = ts.get_particle( ['uz'], species='electrons', iteration=10000, select={'uz':[-np.inf, np.inf]}, geos_index_read_groups=True)
end = time.time()
print("2. Z with select z geos read group:[-np.inf, np.inf]. Time elapsed: ", end - start, "length: ", len(z_selected_original[0]))
