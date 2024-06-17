import os
import sys

sys.path.insert(0, os.getcwd())

from openpmd_viewer import OpenPMDTimeSeries

bp_file_path = '/nvme/gc/diag2/'
geos_index_path = "/data/gc/rocksdb-index/GEOSIndex/cmake-build-debug/diag2"

species = "electrons"
iteration = 500

# ts = OpenPMDTimeSeries(bp_file_path, backend='openpmd-api')
# result_0 = ts.get_particle(['ux'], species=species, iteration=iteration,
#                 select={'ux': [5.282296854337066e-06, 1.1545774343591047e-05], 'uy': [0.00010659756255792407, 0.00021095902110522736], 'uz': [1.4626885514144121e-05, 2.9286875203982146e-05]})

geos_ts = OpenPMDTimeSeries(bp_file_path, backend='openpmd-api', geos_index=True, geos_index_type="minmax",
                                 geos_index_storage_backend="file", geos_index_save_path=geos_index_path)


result_1 = geos_ts.get_particle(['ux'], species=species, iteration=iteration, geos_index_read_groups=True, select={'ux': [5.282296854337066e-06, 1.1545774343591047e-05], 'uy': [0.00010659756255792407, 0.00021095902110522736], 'uz': [1.4626885514144121e-05, 2.9286875203982146e-05]})

result_2 = geos_ts.get_particle(['ux'], species=species, iteration=iteration, geos_index_read_groups=True, skip_offset=True, select={'ux': [5.282296854337066e-06, 1.1545774343591047e-05], 'uy': [0.00010659756255792407, 0.00021095902110522736], 'uz': [1.4626885514144121e-05, 2.9286875203982146e-05]})

# print(len(result_0[0]), len(result_1[0]), len(result_2[0]))

# print(result_0[0][0], result_1[0][0], result_2[0][0])

import numpy as np
# print(np.array_equal(result_0[0], result_1[0]))
# print(np.array_equal(result_0[0], result_2[0]))
print(np.array_equal(result_1[0], result_2[0]))
