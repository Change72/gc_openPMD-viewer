import os
import sys

sys.path.insert(0, os.getcwd())

from openpmd_viewer import OpenPMDTimeSeries

bp_file_path = '/nvme/gc/diag2/'
geos_index_path = "/data/gc/rocksdb-index/GEOSIndex/cmake-build-debug/diag2"

species = "electrons"
iteration = 500

geos_ts = OpenPMDTimeSeries(bp_file_path, backend='openpmd-api', geos_index=True, geos_index_type="minmax",
                                 geos_index_storage_backend="file", geos_index_save_path=geos_index_path, geos_index_secondary_type="minmax")

x_in_envelope = geos_ts.get_particle(['ux','uy','uz'], species=species, iteration=iteration, geos_index_use_secondary=True, select={'ux': [5.282296854337066e-06, 1.1545774343591047e-05], 'uy': [0.00010659756255792407, 0.00021095902110522736], 'uz': [1.4626885514144121e-05, 2.9286875203982146e-05]})

print(len(x_in_envelope[0]))