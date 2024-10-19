import os
import sys

sys.path.insert(0, os.getcwd())

import time
import numpy as np
from openpmd_viewer import OpenPMDTimeSeries

bp_file_path = '/data/gc/small/diag2/'
geos_index_path = "/data/gc/GEOSIndex/build-with-blosc/bp0500"

species = "electrons"
iteration = 500

# ts = OpenPMDTimeSeries(bp_file_path, backend='openpmd-api')
# result_0 = ts.get_particle(['ux'], species=species, iteration=iteration,
#                 select={'ux': [5.282296854337066e-06, 1.1545774343591047e-05], 'uy': [0.00010659756255792407, 0.00021095902110522736], 'uz': [1.4626885514144121e-05, 2.9286875203982146e-05]})

geos_ts = OpenPMDTimeSeries(bp_file_path, backend='openpmd-api', geos_index=True, geos_index_type="minmax",
                                 geos_index_storage_backend="file", geos_index_save_path=geos_index_path)

start = time.time()
# result_1 = geos_ts.get_particle(['ux'], species=species, iteration=iteration, geos_index_read_groups=True, select={'ux': [5.282296854337066e-06, 1.1545774343591047e-05], 'uy': [0.00010659756255792407, 0.00021095902110522736], 'uz': [1.4626885514144121e-05, 2.9286875203982146e-05]})
result_1 = geos_ts.get_particle(['x', 'y', 'z'], species=species, iteration=iteration, select={'ux': [-0.015521840413987263, 0.015494418973768166], 'uy': [-0.6423767151717688, 0.643299871221191], 'uz': [-0.13076028422576122, 0.13098850287295552]})
# result_1 = geos_ts.get_particle(['x', 'y', 'z'], species=species, iteration=iteration, select={'ux': [-np.inf, np.inf], 'uy': [-np.inf, np.inf], 'uz': [-np.inf, np.inf]})

end = time.time()
print("Total time elapsed: ", end - start)

print("============================================")

# start = time.time()
# result_2 = geos_ts.get_particle(['ux'], species=species, iteration=iteration, geos_index_read_groups=True, skip_offset=True, select={'ux': [5.282296854337066e-06, 1.1545774343591047e-05], 'uy': [0.00010659756255792407, 0.00021095902110522736], 'uz': [1.4626885514144121e-05, 2.9286875203982146e-05]})
# end = time.time()
# print("Total time elapsed: ", end - start)
# print(len(result_0[0]), len(result_1[0]), len(result_2[0]))

# print(result_0[0][0], result_1[0][0], result_2[0][0])

# print(np.array_equal(result_0[0], result_1[0]))
# print(np.array_equal(result_0[0], result_2[0]))
# print(np.array_equal(result_1[0], result_2[0]))
