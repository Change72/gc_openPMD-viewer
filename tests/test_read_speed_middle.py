import os
import sys

sys.path.insert(0, os.getcwd())

from openpmd_viewer import OpenPMDTimeSeries

bp_file_path = '/nvme/gc/middle/data_b13206/'
geos_index_path = "/data/gc/rocksdb-index/GEOSIndex/cmake-build-debug/bp09000"

species = "hydrogen"
iteration = 9000

geos_ts = OpenPMDTimeSeries(bp_file_path, backend='openpmd-api', geos_index=True, geos_index_type="minmax",
                                 geos_index_storage_backend="file", geos_index_save_path=geos_index_path)

x_in_envelope = geos_ts.get_particle(['ux'], species=species, iteration=iteration, geos_index_read_groups=True, select={'ux': [0.0031552064001916886, 0.0031580667993416738]})

print(len(x_in_envelope[0]))