import os
import time
import sys
sys.path.insert(0, os.getcwd())

import geosindex

import matplotlib.pyplot as plt
import numpy as np

from openpmd_viewer import OpenPMDTimeSeries

# 1. Original

bp_file_path = os.environ.get('PSCRATCH')
print(bp_file_path)

ts = OpenPMDTimeSeries(bp_file_path, backend='openpmd-api')

start = time.time()
z_all = ts.get_particle(['z'], species='electrons', iteration=10000)
end = time.time()
print("1. Z without select. Time elapsed: ", end - start, "length: ", len(z_all[0]))


# z_selected_original, uz_selected_original = ts.get_particle( ['z', 'uz'], species='electrons',
#                             iteration=300, select={'x':[5e-6, 10e-6], 'y':[5e-6, 10e-6], 'z':[15e-6, 30e-6], 'ux':[0.0, 0.01], 'uy':[0.0, 0.01], 'uz':[0.0, 0.01]})
z_selected_original, uz_selected_original = ts.get_particle( ['z', 'uz'], species='electrons',
                            iteration=10000, select={'x':[0, 2]},
)

end = time.time()
print("2. Z and uz with select x. Time elapsed: ", end - start, "length: ", len(z_selected_original))

