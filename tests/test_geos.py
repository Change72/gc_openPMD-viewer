import os
import time

import sys
sys.path.insert(0, os.getcwd())

import geosindex


# %matplotlib inline
import matplotlib.pyplot as plt
import numpy as np

from openpmd_viewer import OpenPMDTimeSeries


geos_ts = OpenPMDTimeSeries("/data/gc/middle/", backend='openpmd-api', geos_index=True, geos_index_type="rtree",
                 geos_index_storage_backend="file", geos_index_save_path="/data/gc/GEOSIndex/build-with-blosc/bp09000")

start = time.time()

print("direct block read")
# result = geos_ts.get_particle( ['y'], species='hydrogen',
#                             iteration=9000, select={'ux': [-0.027963249432878957, -0.027351281465401]},
#                             geos_index_use_secondary=False, geos_index_direct_block_read=True)

result = geos_ts.get_particle( ['y'], species='hydrogen',
                            iteration=9000, select={'x': [3.646344732214823e-07, 5.6552881947895036e-07]},
                            geos_index_use_secondary=False, geos_index_direct_block_read=True)

end = time.time()
print("Time elapsed: ", end - start)


start = time.time()

# print("direct block read with secondary index")
# result = geos_ts.get_particle( ['z', 'y', 'x'], species='hydrogen',
#                             iteration=10000, select={'x': [7.450558210356463e-06, 8.793662412174456e-06], 'y': [-3.0268816239146733e-06, -1.45683519311199e-06], 'z': [-1.1390350507475311e-05, -9.712457821046488e-06]},
#                             geos_index_use_secondary=True, geos_index_direct_block_read=True)

# end = time.time()
# print("Time elapsed: ", end - start)