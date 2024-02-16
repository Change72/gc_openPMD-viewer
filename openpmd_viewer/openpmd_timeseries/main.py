"""
This file is part of the openPMD-viewer.

It defines the main OpenPMDTimeSeries class.

Copyright 2015-2016, openPMD-viewer contributors
Authors: Remi Lehe, Axel Huebl
License: 3-Clause-BSD-LBNL
"""
import geosindex
import numpy as np
from scipy import constants
from tqdm import tqdm

from .data_reader import DataReader, available_backends
from .interactive import InteractiveViewer
from .particle_tracker import ParticleTracker
from .plotter import Plotter
from .utilities import apply_selection, fit_bins_to_grid, try_array, \
    sanitize_slicing, combine_cylindrical_components


# Define a custom Exception
class OpenPMDException(Exception):
    "Exception raised for invalid use of the openPMD-viewer API"
    pass


class OpenPMDTimeSeries(InteractiveViewer):
    """
    Main class for the exploration of an openPMD timeseries

    For more details, see the docstring of the following methods:
    - get_field
    - get_particle
    - slider
    """

    def __init__(self, path_to_dir, check_all_files=True, backend=None, geos_index=False, rocksdb_path=None, 
    key_generation_function=None, UseMinMaxIndex=False, MinMaxIndexFileName=None):
        """
        Initialize an openPMD time series

        More precisely, scan the directory and extract the openPMD files,
        as well as some useful openPMD parameters

        Parameters
        ----------
        path_to_dir: string
            The path to the directory where the openPMD files are.

        check_all_files: bool, optional
            Check that all the files in the timeseries are consistent
            (i.e. that they contain the same fields and particles,
            with the same metadata)
            For fast access to the files, this can be changed to False.

        backend: string
            Backend to be used for data reading. Can be `openpmd-api`
            or `h5py`. If not provided will use `openpmd-api` if available
            and `h5py` otherwise.

        to build gc_geos_index, bpFileName should be like "/data/gc/rocksdb-index/WarpX/build/bin/diags/diag1/openpmd.bp"
            geosindex::BuildGEOSIndex buildGEOSIndex("/data/gc/rocksdb-index/WarpX/build/bin/diags/diag1/openpmd.bp");
            buildGEOSIndex.buildFirstSTRtree3d();
        the output database path by default is: std::filesystem::path(bpFileName).parent_path() + /rocksdb
            e.g. /data/gc/rocksdb-index/WarpX/build/bin/diags/diag1/rocksdb
        """
        # Check backend
        if backend is None:
            backend = available_backends[0] #Pick openpmd-api first if available
        elif backend not in available_backends:
            raise RuntimeError("Invalid backend requested: {0}\n"
                    "The available backends are: {1}"
                    .format(backend, available_backends) )
        self.backend = backend
        self.geos_index = geos_index
        if self.geos_index:
            self.query_geos_index = geosindex.QueryGEOSINDEX(rocksdb_path)
            pass

        self.UseMinMaxIndex = UseMinMaxIndex
        if self.UseMinMaxIndex:
            # initialize with MinMaxIndexFileName
            self.MinMaxIndex = geosindex.MinMaxQuery(MinMaxIndexFileName)
            pass

        if self.geos_index or self.UseMinMaxIndex:
            if key_generation_function:
                self.key_generation_function = key_generation_function
            else:
                self.key_generation_function = lambda iteration, species, type, dimension=None: f"/data/{iteration}/particles/{species}/{type}/" + (f"{dimension}" if dimension else "")
            pass

        # Initialize data reader
        self.data_reader = DataReader(backend)

        # Extract the iterations available in this timeseries
        self.iterations = self.data_reader.list_iterations(path_to_dir)

        # Check that there are files in this directory
        if len(self.iterations) == 0:
            print("Error: Found no valid files in the specified directory.\n"
                  "Please check that this is the path to the openPMD files.")
            return(None)

        # Go through the files of the series, extract the time
        # and a few parameters.
        N_iterations = len(self.iterations)
        self.t = np.zeros(N_iterations)

        # - Extract parameters from the first file
        t, params0 = self.data_reader.read_openPMD_params(self.iterations[0])
        self.t[0] = t
        self.extensions = params0['extensions']
        self.avail_fields = params0['avail_fields']
        if self.avail_fields is not None:
            self.fields_metadata = params0['fields_metadata']
            self.avail_geom = set( self.fields_metadata[field]['geometry']
                                for field in self.avail_fields )
        # Extract information of the particles
        self.avail_species = params0['avail_species']
        self.avail_record_components = \
            params0['avail_record_components']

        # - Extract the time for each file and, if requested, check
        #   that the other files have the same parameters
        for k in range(1, N_iterations):
            t, params = self.data_reader.read_openPMD_params(
                self.iterations[k], check_all_files)
            self.t[k] = t
            if check_all_files:
                for key in params0.keys():
                    if params != params0:
                        print("Warning: File %s has different openPMD "
                              "parameters than the rest of the time series."
                              % self.iterations[k])
                        break

        # - Set the current iteration and time
        self._current_i = 0
        self.current_iteration = self.iterations[0]
        self.current_t = self.t[0]
        # - Find the min and the max of the time
        self.tmin = self.t.min()
        self.tmax = self.t.max()

        # - Initialize a plotter object, which holds information about the time
        self.plotter = Plotter(self.t, self.iterations)

        # - gc read strategy
        self.max_level = 3
        self.max_read_length = 100000000
        self.sorted_blocks = None
        self.read_strategy = list()
        self.k = (3.7/3.4)*10e-8
        self.b = 0.06


    def result_to_tuple(self, result_obj):
        return result_obj.start, result_obj.end, None

    def find_optimal_strategy(self, start, end, current_level):
        """
        Finds the optimal strategy for reading a list of one-dimensional points.

        Args:
            start (int): The start index of the list.
            end (int): The end index of the list.
            current_level (int): The current level of the recursion.

        Returns:
            A tuple containing the optimal cost and the list of indices to cut the list at.
        """
        if current_level > self.max_level:
            self.read_strategy.append((start, end))
            return 

        # calculate the maximum gap between points
        max_gap = 0
        left_end = 0
        right_start = 0
        for i in range(start, end):
            gap = int(self.sorted_blocks[i+1][1].start) - int(self.sorted_blocks[i][1].end)
            if gap > max_gap:
                max_gap = gap
                left_end = i
                right_start = i+1

        # original_cost = (int(self.sorted_blocks[-1]) - int(self.sorted_blocks[0])) * k + b
        # new_cost = (int(self.sorted_blocks[left_end]) - int(self.sorted_blocks[0])) * k + b + (int(self.sorted_blocks[-1] - int(self.sorted_blocks[right_start]) * k + b
        # new_cost - original_cost = (int(self.sorted_blocks[left_end] - int(self.sorted_blocks[right_start]) * k + b
        temp1 = (int(self.sorted_blocks[left_end][1].start) - int(self.sorted_blocks[right_start][1].end)) * self.k + self.b
        temp2 = int(self.sorted_blocks[left_end][1].end) - int(self.sorted_blocks[start][1].start)
        temp3 = int(self.sorted_blocks[end][1].end) - int(self.sorted_blocks[right_start][1].start)
        if (int(self.sorted_blocks[left_end][1].start) - int(self.sorted_blocks[right_start][1].end)) * self.k + self.b < 0 \
                or int(self.sorted_blocks[left_end][1].end) - int(self.sorted_blocks[start][1].start) > self.max_read_length \
                or int(self.sorted_blocks[end][1].end) - int(self.sorted_blocks[right_start][1].start) > self.max_read_length:
            # if the cost of reading 2 times is less than the cost of reading once, then read twice
            self.find_optimal_strategy(start, left_end, current_level+1)
            self.find_optimal_strategy(right_start, end, current_level+1)
        else:
            self.read_strategy.append((start, end))
            return 

    def get_particle(self, var_list=None, species=None, t=None, iteration=None,
            select=None, plot=False, nbins=150,
            plot_range=[[None, None], [None, None]],
            use_field_mesh=True, direct_block_read=False, only_first_level=False, read_groups=False,
            simulate_adios=False, histogram_deposition='cic', **kw):
        """
        Extract a list of particle variables an openPMD file.

        Plot the histogram of the returned quantity.
        If two quantities are requested by the user, this plots
        a 2d histogram of these quantities.

        In the case of momenta, the result is returned as:
        - unitless momentum (i.e. gamma*beta) for particles with non-zero mass
        - in kg.m.s^-1 for particles with zero mass

        Parameters
        ----------
        var_list : list of string, optional
            A list of the particle variables to extract. If var_list is not
            provided, the available particle quantities are printed

        species: string
            A string indicating the name of the species
            This is optional if there is only one species

        t : float (in seconds), optional
            Time at which to obtain the data (if this does not correspond to
            an existing iteration, the closest existing iteration will be used)
            Either `t` or `iteration` should be given by the user.

        iteration : int
            The iteration at which to obtain the data
            Either `t` or `iteration` should be given by the user.

        select: dict or ParticleTracker object, optional
            - If `select` is a dictionary:
            then it lists a set of rules to select the particles, of the form
            'x' : [-4., 10.]   (Particles having x between -4 and 10 meters)
            'ux' : [-0.1, 0.1] (Particles having ux between -0.1 and 0.1 mc)
            'uz' : [5., None]  (Particles with uz above 5 mc)
            - If `select` is a ParticleTracker object:
            then it returns particles that have been selected at another
            iteration ; see the docstring of `ParticleTracker` for more info.

        plot : bool, optional
           Whether to plot the requested quantity
           Plotting support is only available when requesting one or two
           quantities (i.e. when var_list is of length 1 or 2)

        nbins : int, optional
           (Only used when `plot` is True)
           Number of bins for the histograms

        plot_range : list of lists
           A list containing 2 lists of 2 elements each
           Indicates the values between which to perform the histogram,
           along the 1st axis (first list) and 2nd axis (second list)
           Default: the range is automatically determined

        use_field_mesh: bool, optional
           (Only used when `plot` is True)
           Whether to use the information of the spatial mesh (whenever
           possible) in order to choose the parameters of the histograms.
           More precisely, when this is True:
           - The extent of the histogram (along any spatial dimension) is
             automatically chosen to be roughly the extent of the spatial mesh.
           - The number of bins (along any spatial dimension) is slightly
             modified (from the value `nbins` provided by the user) so that
             the spacing of the histogram is an integer multiple of the grid
             spacing. This avoids artifacts in the plot, whenever particles
             are regularly spaced in each cell of the spatial mesh.

        histogram_deposition : string
            Either `ngp` (Nearest Grid Point) or `cic` (Cloud-In-Cell)
            When plotting the particle histogram, this determines how
            particles affects neighboring bins.
            `cic` (which is the default) leads to smoother results than `ngp`.

        **kw : dict, otional
           Additional options to be passed to matplotlib's
           hist or hist2d.

        Returns
        -------
        A list of 1darray corresponding to the data requested in `var_list`
        (one 1darray per element of 'var_list', returned in the same order)
        """
        # Check that the species required are present
        if self.avail_species is None:
            raise OpenPMDException('No particle data in this time series')
        # If there is only one species, infer that the user asks for that one
        if species is None and len(self.avail_species) == 1:
            species = self.avail_species[0]
        if species not in self.avail_species:
            species_list = '\n - '.join(self.avail_species)
            raise OpenPMDException(
                "The argument `species` is missing or erroneous.\n"
                "The available species are: \n - %s\nPlease set the "
                "argument `species` accordingly." % species_list)

        # Check the list of variables
        valid_var_list = True
        if not isinstance(var_list, list):
            valid_var_list = False
        else:
            for quantity in var_list:
                if quantity not in self.avail_record_components[species]:
                    valid_var_list = False
        if not valid_var_list:
            quantity_list = '\n - '.join(
                self.avail_record_components[species])
            raise OpenPMDException(
                "The argument `var_list` is missing or erroneous.\n"
                "It should be a list of strings representing species record "
                "components.\n The available quantities for species '%s' are:"
                "\n - %s\nPlease set the argument `var_list` "
                "accordingly." % (species, quantity_list) )

        # Check the format of the particle selection
        if select is None or isinstance(select, ParticleTracker):
            pass
        elif isinstance(select, dict):
            # Dictionary: Check that all selection quantities are available
            valid_select_list = True
            for quantity in select.keys():
                if not (quantity in self.avail_record_components[species]):
                    valid_select_list = False
            if not valid_select_list:
                quantity_list = '\n - '.join(
                    self.avail_record_components[species])
                raise OpenPMDException(
                    "The argument `select` is erroneous.\n"
                    "It should be a dictionary whose keys represent particle "
                    "quantities.\n The available quantities are: "
                    "\n - %s\nPlease set the argument `select` "
                    "accordingly." % quantity_list)
        else:
            raise OpenPMDException("The argument `select` is erroneous.\n"
            "It should be either a dictionary or a ParticleTracker object.")

        # Find the output that corresponds to the requested time/iteration
        # (Modifies self._current_i, self.current_iteration and self.current_t)
        self._find_output(t, iteration)
        # Get the corresponding iteration
        iteration = self.iterations[self._current_i]

        # Extract the list of particle quantities
        data_list = []
        if (not self.geos_index and not self.UseMinMaxIndex) or not select:
            for quantity in var_list:
                data_list.append( self.data_reader.read_species_data(
                    iteration, species, quantity, self.extensions))
            # Apply selection if needed
            if isinstance( select, dict ):
                data_list = apply_selection( iteration, self.data_reader,
                    data_list, select, species, self.extensions)
            elif isinstance( select, ParticleTracker ):
                data_list = select.extract_tracked_particles( iteration,
                    self.data_reader, data_list, species, self.extensions )
            print(len(data_list[0]))
        else:
            # 1. [multiple columns] use geos_index to coarse selection return [a list of [key/block, start, count]]
            if isinstance( select, dict ):
                dict_record_comp = {'x': ['position', 'x'],
                    'y': ['position', 'y'],
                    'z': ['position', 'z'],
                    'ux': ['momentum', 'x'],
                    'uy': ['momentum', 'y'],
                    'uz': ['momentum', 'z'],
                    'w': ['weighting', None]}

                mass = 9.1093829099999999e-31
                momentum_constant = 1. / (mass * constants.c)

                if self.UseMinMaxIndex:
                    query_result = list()
                    for quantity in select.keys():
                        key = self.key_generation_function(iteration=iteration, species=species, type=dict_record_comp[quantity][0], dimension=dict_record_comp[quantity][1])
                        if dict_record_comp[quantity][0] == "momentum":
                            result = self.MinMaxIndex.queryMinMaxData(key, select[quantity][0]/momentum_constant, select[quantity][1]/momentum_constant)
                        else:
                            result = self.MinMaxIndex.queryMinMaxData(key, select[quantity][0], select[quantity][1])
                        query_result.append(result)

                    set1 = set(map(self.result_to_tuple, query_result[0]))
                    for i, result in enumerate(query_result):
                        if i == 0:
                            continue
                        set1 = set1.intersection(set(map(self.result_to_tuple, result)))
                    query_result[0] = list(set1)

                    if len(query_result[0]) == 0:
                        return list(), list()

                    # 2. read data based on query_result[0]
                    data_map = dict()
                    data_size = None
                    for quantity in set(var_list + list(select.keys())):
                        #todo optimize read data
                        data_map[quantity] = self.data_reader.read_species_data(iteration, species, quantity, self.extensions, query_result[0])
                        data_size = len(data_map[quantity])
                    print("Query by MinMaxIndex and read data size: ", data_size)
                    pass
                elif self.geos_index:
                    select_map = dict()
                    for quantity in select.keys():
                        if dict_record_comp[quantity][0] not in select_map.keys():
                            select_map[dict_record_comp[quantity][0]] = dict()
                            select_map[dict_record_comp[quantity][0]]["minx"] = -np.inf
                            select_map[dict_record_comp[quantity][0]]["maxx"] = np.inf
                            select_map[dict_record_comp[quantity][0]]["miny"] = -np.inf
                            select_map[dict_record_comp[quantity][0]]["maxy"] = np.inf
                            select_map[dict_record_comp[quantity][0]]["minz"] = -np.inf
                            select_map[dict_record_comp[quantity][0]]["maxz"] = np.inf

                        select_map[dict_record_comp[quantity][0]]["min" + dict_record_comp[quantity][1]] = select[quantity][0]
                        select_map[dict_record_comp[quantity][0]]["max" + dict_record_comp[quantity][1]] = select[quantity][1]
                        if dict_record_comp[quantity][0] == "momentum":
                            select_map[dict_record_comp[quantity][0]]["min" + dict_record_comp[quantity][1]] /= momentum_constant
                            select_map[dict_record_comp[quantity][0]]["max" + dict_record_comp[quantity][1]] /= momentum_constant



                    query_result = list()

                    if not direct_block_read and not only_first_level:
                        for i, select_type in enumerate(select_map.keys()):
                            key = self.key_generation_function(iteration=iteration, species=species, type=select_type)
                            # result = self.query_geos_index.queryByXYZ(key, -0.06996e-25, -0.06996e-24, -0.06996e-5, 0.06996e-5, 4.996e-05, 7.996e-02)
                            result = self.query_geos_index.queryByXYZ(key, select_map[select_type]["minx"],
                                                                      select_map[select_type]["maxx"],
                                                                      select_map[select_type]["miny"],
                                                                      select_map[select_type]["maxy"],
                                                                      select_map[select_type]["minz"],
                                                                      select_map[select_type]["maxz"])
                            query_result.append(result)

                        # mix query_result if select_map == 2
                        if len(select_map.keys()) == 2:
                            # todo try to optimize later
                            set1 = set(map(self.result_to_tuple, query_result[0]))
                            set2 = set(map(self.result_to_tuple, query_result[1]))

                            query_result[0] = list(set1.intersection(set2))
                        else:
                            query_result[0] = list(map(self.result_to_tuple, query_result[0]))

                        if len(query_result[0]) == 0:
                            return list(), list()

                        # 2. [multiple columns] read data [slice level]
                        # type 1: target_select_data, get_particle( ['z', 'uz']
                        # type 2: the data in select, select={'x':[-0.06996e-25, -0.06996e-24], 'y':[-0.06996e-5, 0.06996e-5], 'z':[4.996e-05, 7.996e-02]}
                        data_map = dict()
                        data_size = None
                        for quantity in set(var_list + list(select.keys())):
                            #todo optimize read data
                            data_map[quantity] = self.data_reader.read_species_data(iteration, species, quantity, self.extensions, query_result[0])
                            data_size = len(data_map[quantity])
                            print(data_size)

                    elif direct_block_read and only_first_level:
                        block_result_list = list()
                        for i, select_type in enumerate(select_map.keys()):
                            key = self.key_generation_function(iteration=iteration, species=species, type=select_type)
                            direct_block_result = self.query_geos_index.queryByOnlyBlockXYZ(key,
                                                                                            select_map[select_type]["minx"],
                                                                                            select_map[select_type]["maxx"],
                                                                                            select_map[select_type]["miny"],
                                                                                            select_map[select_type]["maxy"],
                                                                                            select_map[select_type]["minz"],
                                                                                            select_map[select_type]["maxz"])
                            block_result_list.append(direct_block_result)

                        if len(select_map.keys()) == 2:
                            for block_start in list(block_result_list[0].keys()):
                                if block_start not in block_result_list[1].keys():
                                    del block_result_list[0][block_start]

                        # plot particle number distribution
                        # particle_number = list()
                        # for block_ in block_result_list[0].values():
                        #     particle_number.append(block_.end - block_.start)
                        # plt.hist(particle_number)

                        if len(block_result_list[0]) == 0:
                            return list(), list()

                        self.sorted_blocks = sorted(block_result_list[0].items(), key=lambda x: int(x[0]))
                        if read_groups:
                            self.read_strategy = list()
                            self.find_optimal_strategy(0, len(self.sorted_blocks) - 1, 0)

                        data_map = dict()
                        data_size = None
                        for quantity in set(var_list + list(select.keys())):
                            # todo optimize read data
                            if read_groups:
                                data_map[quantity] = self.data_reader.read_species_data(iteration, species, quantity,
                                                                                        self.extensions, self.sorted_blocks, self.read_strategy)
                            else:
                                data_map[quantity] = self.data_reader.read_species_data(iteration, species, quantity, self.extensions, block_result_list[0])

                            data_size = len(data_map[quantity])
                        print(data_size)

                    elif direct_block_read:
                        block_result_list = list()
                        for i, select_type in enumerate(select_map.keys()):
                            key = self.key_generation_function(iteration=iteration, species=species, type=select_type)
                            direct_block_result = self.query_geos_index.queryByBlockXYZ(key,
                                                                                        select_map[select_type]["minx"],
                                                                                        select_map[select_type]["maxx"],
                                                                                        select_map[select_type]["miny"],
                                                                                        select_map[select_type]["maxy"],
                                                                                        select_map[select_type]["minz"],
                                                                                        select_map[select_type]["maxz"])
                            block_result_list.append(direct_block_result)

                        if len(select_map.keys()) == 2:
                            for block_start in list(block_result_list[0].keys()):
                                if block_start not in block_result_list[1].keys():
                                    del block_result_list[0][block_start]
                                    continue
                                for slice_start in list(block_result_list[0][block_start].q.keys()):
                                    if slice_start not in block_result_list[1][block_start].q.keys():
                                        del block_result_list[0][block_start].q[slice_start]

                        if len(block_result_list[0]) == 0:
                            return list(), list()

                        data_map = dict()
                        data_size = None
                        for quantity in set(var_list + list(select.keys())):
                            #todo optimize read data
                            data_map[quantity] = self.data_reader.read_species_data(iteration, species, quantity, self.extensions, block_result_list[0])
                            data_size = len(data_map[quantity])
                        print(data_size)


                select_array = np.ones(data_size, dtype='bool')
                for quantity in select.keys():
                    # Check lower bound
                    if select[quantity][0] is not None:
                        select_array = np.logical_and(
                            select_array,
                            data_map[quantity] > select[quantity][0])
                    # Check upper bound
                    if select[quantity][1] is not None:
                        select_array = np.logical_and(
                            select_array,
                            data_map[quantity] < select[quantity][1])
                # Use select_array to reduce each quantity
                data_list = list()
                for key in var_list:
                    if len(data_map[key]) > 1:  # Do not apply selection on scalar records
                        data_list.append(data_map[key][select_array])
                print(len(data_list[0]))

            else:
                # todo particle tracing
                pass
        print()
        # Plotting
        if plot and len(var_list) in [1, 2]:

            # Extract the weights, if they are available
            if 'w' in self.avail_record_components[species]:
                w = self.data_reader.read_species_data(
                    iteration, species, 'w', self.extensions)
                if isinstance( select, dict ):
                    w, = apply_selection( iteration, self.data_reader,
                        [w], select, species, self.extensions)
                elif isinstance( select, ParticleTracker ):
                    w, = select.extract_tracked_particles( iteration,
                        self.data_reader, [w], species, self.extensions )
            # Otherwise consider that all particles have a weight of 1
            else:
                w = np.ones_like(data_list[0])

            # Determine the size of the histogram bins
            # - First pick default values
            hist_range = [[None, None], [None, None]]
            for i_data in range(len(data_list)):
                data = data_list[i_data]

                # Check if the user specified a value
                if (plot_range[i_data][0] is not None) and \
                        (plot_range[i_data][1] is not None):
                    hist_range[i_data] = plot_range[i_data]
                # Else use min and max of data
                elif len(data) != 0:
                    hist_range[i_data] = [ data.min(), data.max() ]
                else:
                    hist_range[i_data] = [ -1., 1. ]

                # Avoid error when the min and max are equal
                if hist_range[i_data][0] == hist_range[i_data][1]:
                    if hist_range[i_data][0] == 0:
                        hist_range[i_data] = [ -1., 1. ]
                    else:
                        hist_range[i_data][0] *= 0.99
                        hist_range[i_data][1] *= 1.01

            hist_bins = [ nbins for i_data in range(len(data_list)) ]
            # - Then, if required by the user, modify this values by
            #   fitting them to the spatial grid
            if use_field_mesh and self.avail_fields is not None:
                # Extract the grid resolution
                grid_size_dict, grid_range_dict = \
                    self.data_reader.get_grid_parameters( iteration,
                        self.avail_fields, self.fields_metadata )
                # For each direction, modify the number of bins, so that
                # the resolution is a multiple of the grid resolution
                for i_var in range(len(var_list)):
                    var = var_list[i_var]
                    if var in grid_size_dict.keys():
                        # Check that the user indeed allowed this dimension
                        # to be determined automatically
                        if (plot_range[i_var][0] is None) or \
                                (plot_range[i_var][1] is None):
                            hist_bins[i_var], hist_range[i_var] = \
                                fit_bins_to_grid(hist_bins[i_var],
                                grid_size_dict[var], grid_range_dict[var] )

            # - In the case of only one quantity
            if len(data_list) == 1:
                # Do the plotting
                self.plotter.hist1d(data_list[0], w, var_list[0], species,
                        self._current_i, hist_bins[0], hist_range,
                        deposition=histogram_deposition, **kw)
            # - In the case of two quantities
            elif len(data_list) == 2:
                # Do the plotting
                self.plotter.hist2d(data_list[0], data_list[1], w,
                    var_list[0], var_list[1], species,
                    self._current_i, hist_bins, hist_range,
                    deposition=histogram_deposition, **kw)

        # Output the data
        return(data_list)

    def get_field(self, field=None, coord=None, t=None, iteration=None,
                  m='all', theta=0., slice_across=None,
                  slice_relative_position=None, plot=False,
                  plot_range=[[None, None], [None, None]], **kw):
        """
        Extract a given field from a file in the openPMD format.

        Parameters
        ----------

        field : string, optional
           Which field to extract

        coord : string, optional
           Which component of the field to extract

        m : int or str, optional
           Only used for thetaMode geometry
           Either 'all' (for the sum of all the modes)
           or an integer (for the selection of a particular mode)

        t : float (in seconds), optional
            Time at which to obtain the data (if this does not correspond to
            an existing iteration, the closest existing iteration will be used)
            Either `t` or `iteration` should be given by the user.

        iteration : int
            The iteration at which to obtain the data
            Either `t` or `iteration` should be given by the user.

        theta : float or None, optional
           Only used for thetaMode geometry
           The angle of the plane of observation, with respect to the x axis
           If `theta` is not None, then this function returns a 2D array
           corresponding to the plane of observation given by `theta` ;
           otherwise it returns a full 3D Cartesian array

        slice_across : str or list of str, optional
           Direction(s) across which the data should be sliced
           + In cartesian geometry, elements can be:
               - 1d: 'z'
               - 2d: 'x' and/or 'z'
               - 3d: 'x' and/or 'y' and/or 'z'
           + In cylindrical geometry, elements can be 'r' and/or 'z'
           Returned array is reduced by 1 dimension per slicing.
           If slicing is None, the full grid is returned.

        slice_relative_position : float or list of float, optional
           Number(s) between -1 and 1 that indicate where to slice the data,
           along the directions in `slice_across`
           -1 : lower edge of the simulation box
           0 : middle of the simulation box
           1 : upper edge of the simulation box
           Default: None, which results in slicing at 0 in all direction
           of `slice_across`.

        plot : bool, optional
           Whether to plot the requested quantity

        plot_range : list of lists
           A list containing 2 lists of 2 elements each
           Indicates the values between which to clip the plot,
           along the 1st axis (first list) and 2nd axis (second list)
           Default: plots the full extent of the simulation box

        **kw : dict, otional
           Additional options to be passed to matplotlib's imshow.

        Returns
        -------
        A tuple with
           F : a 2darray containing the required field
           info : a FieldMetaInformation object
           (see the corresponding docstring)
        """
        # Check that the field required is present
        if self.avail_fields is None:
            raise OpenPMDException('No field data in this time series')
        # Check the field type
        if field not in self.avail_fields:
            field_list = '\n - '.join(self.avail_fields)
            raise OpenPMDException(
                "The `field` argument is missing or erroneous.\n"
                "The available fields are: \n - %s\nPlease set the `field` "
                "argument accordingly." % field_list)
        # Check slicing
        slice_across, slice_relative_position = \
            sanitize_slicing(slice_across, slice_relative_position)
        if slice_across is not None:
            # Check that the elements are valid
            axis_labels = self.fields_metadata[field]['axis_labels']
            for axis in slice_across:
                if axis not in axis_labels:
                    axes_list = '\n - '.join(axis_labels)
                    raise OpenPMDException(
                    'The `slice_across` argument is erroneous: contains %s\n'
                    'The available axes are: \n - %s' % (axis, axes_list) )

        # Check the coordinate, for vector fields
        if self.fields_metadata[field]['type'] == 'vector':
            available_coord = ['x', 'y', 'z']
            if self.fields_metadata[field]['geometry'] == 'thetaMode':
                available_coord += ['r', 't']
            if coord not in available_coord:
                coord_list = '\n - '.join(available_coord)
                raise OpenPMDException(
                    "The field %s is a vector field, \nbut the `coord` "
                    "argument is missing or erroneous.\nThe available "
                    "coordinates are: \n - %s\nPlease set the `coord` "
                    "argument accordingly." % (field, coord_list))
        # Automatically set the coordinate to None, for scalar fields
        else:
            coord = None

        # Check the mode (for thetaMode)
        if self.fields_metadata[field]['geometry'] == "thetaMode":
            avail_circ_modes = self.fields_metadata[field]['avail_circ_modes']
            if str(m) not in avail_circ_modes:
                mode_list = '\n - '.join(avail_circ_modes)
                raise OpenPMDException(
                    "The requested mode '%s' is not available.\n"
                    "The available modes are: \n - %s" % (m, mode_list))

        # Find the output that corresponds to the requested time/iteration
        # (Modifies self._current_i, self.current_iteration and self.current_t)
        self._find_output(t, iteration)
        # Get the corresponding iteration
        iteration = self.iterations[self._current_i]

        # Find the proper path for vector or scalar fields
        if self.fields_metadata[field]['type'] == 'scalar':
            field_label = field
        elif self.fields_metadata[field]['type'] == 'vector':
            field_label = field + coord

        # Get the field data
        geometry = self.fields_metadata[field]['geometry']
        axis_labels = self.fields_metadata[field]['axis_labels']
        # - For cartesian
        if geometry in ["1dcartesian", "2dcartesian", "3dcartesian"]:
            F, info = self.data_reader.read_field_cartesian(
                iteration, field, coord, axis_labels,
                slice_relative_position, slice_across)
        # - For thetaMode
        elif geometry == "thetaMode":
            if (coord in ['x', 'y']) and \
                    (self.fields_metadata[field]['type'] == 'vector'):
                # For Cartesian components, combine r and t components
                Fr, info = self.data_reader.read_field_circ(
                    iteration, field, 'r', slice_relative_position,
                    slice_across, m, theta)
                Ft, info = self.data_reader.read_field_circ(
                    iteration, field, 't', slice_relative_position,
                    slice_across, m, theta)
                F = combine_cylindrical_components(Fr, Ft, theta, coord, info)
            else:
                # For cylindrical or scalar components, no special treatment
                F, info = self.data_reader.read_field_circ(iteration,
                    field, coord, slice_relative_position,
                    slice_across, m, theta)

        # Plot the resulting field
        # Deactivate plotting when there is no slice selection
        if plot:
            if F.ndim == 1:
                self.plotter.show_field_1d(F, info, field_label,
                self._current_i, plot_range=plot_range, **kw)
            elif F.ndim == 2:
                self.plotter.show_field_2d(F, info, slice_across, m,
                    field_label, geometry, self._current_i,
                    plot_range=plot_range, **kw)
            else:
                raise OpenPMDException('Cannot plot %d-dimensional data.\n'
                    'Use the argument `slice_across`, or set `plot=False`' % F.ndim)

        # Return the result
        return(F, info)

    def iterate( self, called_method, *args, **kwargs ):
        """
        Repeated calls the method `called_method` for every iteration of this
        timeseries, with the arguments `*args` and `*kwargs`.

        The result of these calls is returned as a list, or, whenever possible
        as an array, where the first axis corresponds to the iterations.

        If `called_method` returns a tuple/list, then `iterate` returns a
        tuple/list of lists (or arrays).

        Parameters
        ----------
        *args, **kwargs: arguments and keyword arguments
            Arguments that would normally be passed to `called_method` for
            a single iteration. Do not pass the argument `t` or `iteration`.
        """
        # Add the iteration key in the keyword aguments
        kwargs['iteration'] = self.iterations[0]

        # Check the shape of results
        result = called_method(*args, **kwargs)
        result_type = type( result )
        if result_type in [tuple, list]:
            returns_iterable = True
            iterable_length = len(result)
            accumulated_result = [ [element] for element in result ]
        else:
            returns_iterable = False
            accumulated_result = [ result ]

        # Call the method for all iterations
        for iteration in tqdm(self.iterations[1:]):
            kwargs['iteration'] = iteration
            result = called_method( *args, **kwargs )
            if returns_iterable:
                for i in range(iterable_length):
                    accumulated_result[i].append( result[i] )
            else:
                accumulated_result.append( result )

        # Try to stack the arrays
        if returns_iterable:
            for i in range(iterable_length):
                accumulated_result[i] = try_array( accumulated_result[i] )
            if result_type == tuple:
                return tuple(accumulated_result)
            elif result_type == list:
                return accumulated_result
        else:
            accumulated_result = try_array( accumulated_result )
            return accumulated_result

    def _find_output(self, t, iteration):
        """
        Find the output that correspond to the requested `t` or `iteration`
        Modify self._current_i accordingly.

        Parameter
        ---------
        t : float (in seconds)
            Time requested

        iteration : int
            Iteration requested
        """
        # Check the arguments
        if (t is not None) and (iteration is not None):
            raise OpenPMDException(
                "Please pass either a time (`t`) \nor an "
                "iteration (`iteration`), but not both.")
        # If a time is requested
        elif (t is not None):
            # Make sure the time requested does not exceed the allowed bounds
            if t < self.tmin:
                self._current_i = 0
            elif t > self.tmax:
                self._current_i = len(self.t) - 1
            # Find the closest existing iteration
            else:
                self._current_i = abs(self.t - t).argmin()
        # If an iteration is requested
        elif (iteration is not None):
            if (iteration in self.iterations):
                # Get the index that corresponds to this iteration
                self._current_i = abs(iteration - self.iterations).argmin()
            else:
                iter_list = '\n - '.join([str(it) for it in self.iterations])
                raise OpenPMDException(
                      "The requested iteration '%s' is not available.\nThe "
                      "available iterations are: \n - %s\n" % (iteration, iter_list))
        else:
            pass  # self._current_i retains its previous value

        # Register the value in the object
        self.current_t = self.t[self._current_i]
        self.current_iteration = self.iterations[self._current_i]
