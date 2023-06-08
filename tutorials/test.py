import os

# def download_if_absent( dataset_name ):
#     "Function that downloads and decompress a chosen dataset"
#     if os.path.exists( dataset_name ) is False:
#         import wget, tarfile
#         tar_name = "%s.tar.gz" %dataset_name
#         url = "https://github.com/openPMD/openPMD-example-datasets/raw/draft/%s" %tar_name
#         wget.download( url, tar_name )
#         with tarfile.open( tar_name ) as tar_file:
#             tar_file.extractall()
#         os.remove( tar_name )
#
# download_if_absent( 'example-2d' )


import geosindex
# built_object = geosindex.BuildGEOSIndex(
#     "/data/gc/rocksdb-index/WarpX/build/bin/diags/diag2/openpmd.bp",
#     ["position", "momentum"],
#     "/data/gc/rocksdb-index/WarpX/build/bin/diags/diag2/rocksdb_small_bf",  # rocksdb save path, by defaults is {bpFilePath}/rocksdb. In this case, e.g. "/data/gc/rocksdb-index/WarpX/build/bin/diags/diag2/rocksdb"
#     "electrons",
#     10,
#     5,
#     400
# )
# built_object.buildFirstSTRtree3d()


# %matplotlib inline
import matplotlib.pyplot as plt
import numpy as np

from openpmd_viewer import OpenPMDTimeSeries
# ts = OpenPMDTimeSeries('./example-2d/hdf5/', backend='h5py')
# ts = OpenPMDTimeSeries('./example-2d/hdf5/')

# Plot the blue phase space with all the electrons
# ts.get_particle( ['z', 'uz'], species='electrons', iteration=300, plot=True, vmax=1e12 )

from openpmd_viewer import OpenPMDTimeSeries
ts = OpenPMDTimeSeries("/data/gc/rocksdb-index/WarpX/build/bin/diags/diag1/")
ts.get_particle( ['z', 'uz'], species='electrons', iteration=300, plot=True, vmax=1e6 )
z_selected, uz_selected = ts.get_particle( ['z', 'uz'], species='electrons',
                            iteration=300, select={'z':[22e-6, 40e-6]} )
plt.plot(z_selected, uz_selected, 'g.')
print(len(z_selected))

ts = OpenPMDTimeSeries("/data/gc/rocksdb-index/WarpX/build/bin/diags/diag1/", backend='openpmd-api')

# ts = OpenPMDTimeSeries("/data/gc/rocksdb-index/WarpX/build/bin/diags/diag1/", backend='openpmd-api', geos_index=True,
#                        rocksdb_path="/data/gc/rocksdb-index/WarpX/build/bin/diags/diag1/rocksdb")

# ts.get_particle( ['z', 'uz'], species='electrons', iteration=300, plot=True, vmax=1e6 )
# ts.get_particle( ['z', 'uz'], species='electrons', iteration=300, plot=True, vmax=1e12 )
#
# # Select only particles that have uz between 0.05 and 0.2
# # and plot them as green dots, on top of the phase space
# z_selected, uz_selected = ts.get_particle( ['z', 'uz'], species='electrons',
                            # iteration=400, select={'x':[-0.06996e-25, -0.06996e-24], 'y':[-0.06996e-5, 0.06996e-5], 'z':[4.996e-05, 7.996e-02], 'uz':[7.996e-25, 0.0010]} )
# z_selected, uz_selected = ts.get_particle( ['z', 'uz'], species='electrons',
#                             iteration=300, select={'x':[-6.996e-7, 6.996e-7], 'y':[-0.06996e-7, 0.06996e-7], 'z':[22e-6,40e-6]} )
z_selected, uz_selected = ts.get_particle( ['z', 'uz'], species='electrons',
                            iteration=300, select={'z':[22e-6, 40e-6]} )
# z_selected, uz_selected = ts.get_particle( ['z', 'uz'], species='electrons',
#                             iteration=300, select={'uz':[7.996e-25, 0.0010]} )
# plt.plot(z_selected, uz_selected, 'g.')
# print()


from openpmd_viewer import ParticleTracker
# Select particles to be tracked, at iteration 300
pt = ParticleTracker( ts, iteration=300, select={'z':[22e-6,40e-6]}, species='electrons' )
plot_iteration = 400

# Plot the blue phase space with all the electrons
ts.get_particle( ['z', 'uz'], species='electrons', iteration=plot_iteration, plot=True, vmax=1e6 );

# Plot the tracked particles as red dots, on top of the phase space
z_selected, uz_selected = ts.get_particle( ['z', 'uz'], species='electrons', iteration=plot_iteration, select=pt )
plt.plot(z_selected, uz_selected, 'r.')