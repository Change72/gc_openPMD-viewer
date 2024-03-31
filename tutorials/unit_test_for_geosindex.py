import os
import sys

sys.path.insert(0, os.getcwd())

from openpmd_viewer import OpenPMDTimeSeries

bp_file_path = '/pscratch/sd/c/cguo51/openPMD'
geos_index_path = "/pscratch/sd/c/cguo51/GEOSIndex/build/bp010000"

species = "electrons"
iteration = 10000

geos_ts = OpenPMDTimeSeries(bp_file_path, backend='openpmd-api', geos_index=True, geos_index_type="rtree",
                                 geos_index_storage_backend="file", geos_index_save_path=geos_index_path)

x_in_envelope = geos_ts.get_particle(['x'], species=species, iteration=iteration, geos_index_read_groups=True, select={'x':[7.500004278060827e-06, 8.999999217244436e-06]})

