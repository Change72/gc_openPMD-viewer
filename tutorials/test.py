import os
import time
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

import sys
sys.path.insert(0, os.getcwd())

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
# ts = OpenPMDTimeSeries("/data/gc/rocksdb-index/WarpX/build/bin/diags/diag1/")
# ts.get_particle( ['z', 'uz'], species='electrons', iteration=300, plot=True, vmax=1e6 )
# z_selected, uz_selected = ts.get_particle( ['z', 'uz'], species='electrons',
#                             iteration=300, select={'z':[22e-6, 40e-6]} )
# plt.plot(z_selected, uz_selected, 'g.')
# print(len(z_selected))


# 1. Original

# ts = OpenPMDTimeSeries("/data/gc/rocksdb-index/WarpX/build/bin/diags/diag2/", backend='openpmd-api')
# start = time.time()
#
# z_selected_minmax = ts.get_particle(['z'], species='electrons', iteration=300)
# end = time.time()
# print("Time elapsed: ", end - start)
#
#
# # z_selected_original, uz_selected_original = ts.get_particle( ['z', 'uz'], species='electrons',
# #                             iteration=300, select={'x':[5e-6, 10e-6], 'y':[5e-6, 10e-6], 'z':[15e-6, 30e-6], 'ux':[0.0, 0.01], 'uy':[0.0, 0.01], 'uz':[0.0, 0.01]})
# z_selected_original, uz_selected_original = ts.get_particle( ['z', 'uz'], species='electrons',
#                             iteration=300, select={'x':[0, 2]},
# )



# 2. MinMax-File direct block read

geos_ts = OpenPMDTimeSeries("/data/gc/rocksdb-index/WarpX/build/bin/diags/diag2/", backend='openpmd-api', geos_index=True, geos_index_type="minmax",
                 geos_index_storage_backend="file", geos_index_save_path="/data/gc/rocksdb-index/GEOSIndex/cmake-build-debug/diag2")

# timer 

start = time.time()

# z_selected_minmax, uz_selected_minmax = geos_ts.get_particle( ['z', 'uz'], species='electrons',
#                             iteration=300, select={'x':[5e-6, 10e-6], 'y':[5e-6, 10e-6], 'z':[15e-6, 30e-6], 'ux':[0.0, 0.01], 'uy':[0.0, 0.01], 'uz':[0.0, 0.01]})

# z_selected_minmax, uz_selected_minmax = geos_ts.get_particle( ['z', 'uz'], species='electrons',
#                             iteration=300, select={'z':[2.05e-6, 2.10e-6]}, geos_index_direct_block_read=True
#                                                 )

# get the total particle number
z_selected_minmax = geos_ts.get_particle(['z'], species='electrons', iteration=300, geos_index_read_groups=True, 
select={'z':[-np.inf, np.inf]})

end = time.time()
print("Time elapsed: ", end - start)


# 3. MinMax-File read groups

# geos_ts = OpenPMDTimeSeries("/data/gc/rocksdb-index/WarpX/build/bin/diags/diag2/", backend='openpmd-api', geos_index=True, geos_index_type="rtree",
#                  geos_index_storage_backend="rocksdb", geos_index_save_path="/data/gc/rocksdb-index/GEOSIndex/cmake-build-debug/diag2")

# timer 

start = time.time()

# z_selected_minmax, uz_selected_minmax = geos_ts.get_particle( ['z', 'uz'], species='electrons',
#                             iteration=300, select={'x':[5e-6, 10e-6], 'y':[5e-6, 10e-6], 'z':[15e-6, 30e-6], 'ux':[0.0, 0.01], 'uy':[0.0, 0.01], 'uz':[0.0, 0.01]}, geos_index_read_groups=True)

z_selected, uz_selected = geos_ts.get_particle( ['z', 'uz'], species='electrons',
                            iteration=300, select={'z':[2.05e-6, 2.10e-6]}, geos_index_read_groups=True)

end = time.time()
print("Time elapsed: ", end - start)



# 4. MinMax-File use secondary index

geos_ts = OpenPMDTimeSeries("/data/gc/rocksdb-index/WarpX/build/bin/diags/diag2/", backend='openpmd-api', geos_index=True, geos_index_type="minmax",
                 geos_index_storage_backend="file", geos_index_save_path="/data/gc/rocksdb-index/GEOSIndex/cmake-build-debug/diag2",
                 geos_index_secondary_type="minmax")

# timer

start = time.time()

# z_selected_minmax, uz_selected_minmax = geos_ts.get_particle( ['z', 'uz'], species='electrons',
#                             iteration=300, select={'x':[5e-6, 10e-6], 'y':[5e-6, 10e-6], 'z':[15e-6, 30e-6], 'ux':[0.0, 0.01], 'uy':[0.0, 0.01], 'uz':[0.0, 0.01]}, geos_index_read_groups=True)

print("secondary index direct read")
z_selected_secondary_direct, uz_selected_secondary_direct = geos_ts.get_particle( ['z', 'uz'], species='electrons',
                            iteration=300, select={'z':[2.05e-6, 2.10e-6]}, geos_index_use_secondary=True, geos_index_direct_block_read=False)

end = time.time()
print("Time elapsed: ", end - start)

# timer

start = time.time()

# z_selected_minmax, uz_selected_minmax = geos_ts.get_particle( ['z', 'uz'], species='electrons',
#                             iteration=300, select={'x':[5e-6, 10e-6], 'y':[5e-6, 10e-6], 'z':[15e-6, 30e-6], 'ux':[0.0, 0.01], 'uy':[0.0, 0.01], 'uz':[0.0, 0.01]}, geos_index_read_groups=True)

print("block read and use secondary index")
z_selected_secondary_block, uz_selected_secondary_block = geos_ts.get_particle( ['z', 'uz'], species='electrons',
                            iteration=300, select={'z':[2.05e-6, 2.10e-6]}, geos_index_use_secondary=True, geos_index_direct_block_read=True)

end = time.time()
print("Time elapsed: ", end - start)

# timer

start = time.time()

# z_selected_minmax, uz_selected_minmax = geos_ts.get_particle( ['z', 'uz'], species='electrons',
#                             iteration=300, select={'x':[5e-6, 10e-6], 'y':[5e-6, 10e-6], 'z':[15e-6, 30e-6], 'ux':[0.0, 0.01], 'uy':[0.0, 0.01], 'uz':[0.0, 0.01]}, geos_index_read_groups=True)

print("read optimized and use secondary index")
z_selected_secondary_group, uz_selected_secondary_group = geos_ts.get_particle( ['z', 'uz'], species='electrons',
                            iteration=300, select={'z':[2.05e-6, 2.10e-6]}, geos_index_use_secondary=True, geos_index_direct_block_read=False, geos_index_read_groups=True)

end = time.time()
print("Time elapsed: ", end - start)



# print(np.array_equal(np.sort(z_selected), np.sort(z_selected_original)))
# print(np.array_equal(np.sort(uz_selected), np.sort(uz_selected_original)))

print(np.array_equal(np.sort(z_selected), np.sort(z_selected_minmax)))
print(np.array_equal(np.sort(uz_selected), np.sort(uz_selected_minmax)))

print(np.array_equal(np.sort(z_selected), np.sort(z_selected_secondary_direct)))
print(np.array_equal(np.sort(uz_selected), np.sort(uz_selected_secondary_direct)))

print(np.array_equal(np.sort(z_selected), np.sort(z_selected_secondary_block)))
print(np.array_equal(np.sort(uz_selected), np.sort(uz_selected_secondary_block)))

print(np.array_equal(np.sort(z_selected), np.sort(z_selected_secondary_group)))
print(np.array_equal(np.sort(uz_selected), np.sort(uz_selected_secondary_group)))


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
# z_selected, uz_selected = ts.get_particle( ['z', 'uz'], species='electrons',
#                             iteration=300, select={'z':[22e-6, 40e-6], 'uz':[7.996e-25, 0.0010]})
# z_selected, uz_selected = ts.get_particle( ['z', 'uz'], species='electrons',
#                             iteration=300, select={'z':[22e-6, 40e-6], 'uz':[7.996e-25, 0.0010]}, direct_block_read=True )
# z_selected, uz_selected = ts.get_particle( ['z', 'uz'], species='electrons',
#                             iteration=300, select={'uz':[7.996e-25, 0.0010]} )
# plt.plot(z_selected, uz_selected, 'g.')
# print()



# geos_ts = OpenPMDTimeSeries("/data/gc/rocksdb-index/WarpX/build/bin/diags/diag2/", backend='openpmd-api', geos_index=True,
#                        rocksdb_path="/data/gc/rocksdb-index/WarpX/build/bin/diags/diag2/rocksdb")

# z_selected, uz_selected = geos_ts.get_particle( ['z', 'uz'], species='electrons',
#                             iteration=300, select={'z':[19e-6, 21e-6], 'uz':[0.7, 1.0]}, direct_block_read=True, only_first_level=True)
#
# %%time

# start = time.time()
# z_selected_gs_original, uz_selected_gs_original = geos_ts.get_particle( ['z', 'uz'], species='electrons',
#                             iteration=300, select={'x':[5e-6, 10e-6], 'y':[5e-6, 10e-6], 'z':[15e-6, 30e-6], 'ux':[0.0, 0.01], 'uy':[0.0, 0.01], 'uz':[0.0, 0.01]})
# end = time.time()
# print("Time elapsed: ", end - start)
#
# start = time.time()
# z_selected_direct, uz_selected_direct = geos_ts.get_particle( ['z', 'uz'], species='electrons',
#                             iteration=300, select={'x':[5e-6, 10e-6], 'y':[5e-6, 10e-6], 'z':[15e-6, 30e-6], 'ux':[0.0, 0.01], 'uy':[0.0, 0.01], 'uz':[0.0, 0.01]}, direct_block_read=True)
# end = time.time()
# print("Time elapsed: ", end - start)
#
# start = time.time()
# z_selected, uz_selected = geos_ts.get_particle( ['z', 'uz'], species='electrons',
#                             iteration=300, select={'x':[5e-6, 10e-6], 'y':[5e-6, 10e-6], 'z':[15e-6, 30e-6], 'ux':[0.0, 0.01], 'uy':[0.0, 0.01], 'uz':[0.0, 0.01]}, direct_block_read=True, only_first_level=True)
# end = time.time()
# print("Time elapsed: ", end - start)

start = time.time()
# z_selected_groups, uz_selected_groups = geos_ts.get_particle( ['z', 'uz'], species='electrons',
#                             iteration=300, select={'x':[5e-6, 10e-6], 'y':[5e-6, 10e-6], 'z':[15e-6, 30e-6], 'ux':[0.0, 0.001], 'uy':[0.0, 0.001], 'uz':[0.0, 0.001]}, direct_block_read=True, only_first_level=True, read_groups=True)

# z_selected, uz_selected = geos_ts.get_particle( ['z', 'uz'], species='electrons',
#                             iteration=300, select={'z':[2.05e-6, 2.10e-6]}, direct_block_read=True)
# z_selected, uz_selected = geos_ts.get_particle( ['z', 'uz'], species='electrons',
#                             iteration=300, select={'z':[2.05e-6, 2.10e-6]}, direct_block_read=True, only_first_level=True)

# z_selected, uz_selected = geos_ts.get_particle( ['z', 'uz'], species='electrons',
#                             iteration=300, select={'x':[5e-6, 10e-6], 'y':[-10e-6, -5e-6], 'z':[15e-6, 25e-6]},direct_block_read=True, only_first_level=True, read_groups=True)
#
# z_selected, uz_selected = geos_ts.get_particle( ['z', 'uz'], species='electrons',
#                             iteration=300, select={'z':[19e-6, 21e-6], 'uz':[0.7, 1.0]}, direct_block_read=True, only_first_level=True, read_groups=True)
# end = time.time()
# print("Time elapsed: ", end - start)

# print(np.array_equal(np.sort(z_selected), np.sort(z_selected_original)))
# print(np.array_equal(np.sort(uz_selected), np.sort(uz_selected_original)))
#
# print(np.array_equal(np.sort(z_selected), np.sort(z_selected_minmax)))
# print(np.array_equal(np.sort(uz_selected), np.sort(uz_selected_minmax)))
#
# print(np.array_equal(np.sort(z_selected), np.sort(z_selected_gs_original)))
# print(np.array_equal(np.sort(uz_selected), np.sort(uz_selected_gs_original)))
#
# print(np.array_equal(np.sort(z_selected), np.sort(z_selected_direct)))
# print(np.array_equal(np.sort(uz_selected), np.sort(uz_selected_direct)))
#
# # verify z_selected_groups and z_selected are the same
# print(np.array_equal(np.sort(z_selected), np.sort(z_selected_groups)))
# print(np.array_equal(np.sort(uz_selected), np.sort(uz_selected_groups)))
#
#
# temp1 = z_selected.sort()
# temp2 = z_selected_direct.sort()
# from openpmd_viewer import ParticleTracker
# Select particles to be tracked, at iteration 300
# pt = ParticleTracker( ts, iteration=300, select={'z':[22e-6,40e-6]}, species='electrons' )
# plot_iteration = 400
#
# # Plot the blue phase space with all the electrons
# ts.get_particle( ['z', 'uz'], species='electrons', iteration=plot_iteration, plot=True, vmax=1e6 );
#
# # Plot the tracked particles as red dots, on top of the phase space
# z_selected, uz_selected = ts.get_particle( ['z', 'uz'], species='electrons', iteration=plot_iteration, select=pt )
# plt.plot(z_selected, uz_selected, 'r.')
print()
