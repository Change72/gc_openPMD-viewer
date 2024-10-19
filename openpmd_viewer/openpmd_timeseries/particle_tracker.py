"""
This file is part of the openPMD-viewer.

It defines the ParticleTracker class.

Copyright 2015-2016, openPMD-viewer contributors
Authors: Remi Lehe
License: 3-Clause-BSD-LBNL
"""
import numpy as np
from .numba_wrapper import jit

class ParticleTracker( object ):
    """
    Class that allows to select particles at a given iteration
    (by initializing an instance of this class) and then
    to return the same particles at another iteration (by passing
    this instance as the argument `select` of the method `get_particle`
    of an `OpenPMDTimeSeries`)

    Usage
    -----
    Here is a minimal example of how this class is used.
    In this example, all the particles in the simulation box at iteration 300
    are selected, and then the position of the same particles at iteration 400
    (or at least of those particles that remained in the simulation box at
    iteration 400) are returned.
    ```
    >>> ts = OpenPMDTimeSeries('./hdf5_directory/')
    >>> pt = ParticleTracker( ts, iteration=300 )
    >>> x, = ts.get_particle( ['x'], select=pt, iteration=400 )
    ```
    For more details on the API of ParticleTracker, see the docstring of
    the `__init__` method of this class.

    Note
    ----
    `ParticleTracker` requires the `id` of the particles
    to be stored in the openPMD files.
    """

    def __init__(self, ts, species=None, t=None,
                iteration=None, select=None, preserve_particle_index=False,
                use_geos_index=False,
                geos_index_use_secondary = False,
                geos_index_direct_block_read = True,
                geos_index_read_groups = False,
                skip_offset=False,
                limit_block_num=None,
                limit_memory_usage=None,
                block_meta_path=None,
                memory_usage_factor=1.0,
                ):
        """
        Initialize an instance of `ParticleTracker`: select particles at
        a given iteration, so that they can be retrieved at a later iteration.

        Parameters
        ----------
        ts: an OpenPMDTimeSeries object
            Contains the data on the particles

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

        select: dict or 1darray of int, optional
            Either None or a dictionary of rules
            to select the particles, of the form
            'x' : [-4., 10.]  (Particles having x between -4 and 10)
            'ux' : [-0.1, 0.1] (Particles having ux between -0.1 and 0.1 mc)
            'uz' : [5., None]  (Particles with uz above 5 mc).
            Can also be a 1d array of interegers corresponding to the
            selected particles `id`

        preserve_particle_index: bool, optional
            When retrieving particles at a several iterations,
            (for instance, with:
            ```
            >>> x1, = ts.get_particle( ['x'], select=pt, iteration=400 )
            >>> x2, = ts.get_particle( ['x'], select=pt, iteration=500 )
            ```
            it is sometimes important that the same individual particle has
            the same index in the array `x1` and `x2`.
            Using `preserve_particle_index=True` ensures that this is the case.
            However, this means that, for a particle that becomes absent at
            a later iteration, its index in the array has to be filled also.
            In this case, a NaN is returned at the index of this particle.
            When `preserve_particle_index=False`, no NaN is returned (the
            returned array is simply smaller when particles are absent) but
            then it is not garanteed that a given particle keeps the same index
        """

        # Extract or load the particle id and sort them
        if (type(select) is dict) or (select is None):
            self.selected_pid, = ts.get_particle(['id'], species=species,
                                    select=select, t=t, iteration=iteration,
                                    geos_index_use_secondary = geos_index_use_secondary,
                                    geos_index_direct_block_read = geos_index_direct_block_read,
                                    geos_index_read_groups = geos_index_read_groups,
                                    skip_offset=skip_offset,
                                    limit_block_num=limit_block_num,
                                    limit_memory_usage=limit_memory_usage,
                                    block_meta_path=block_meta_path,
                                    memory_usage_factor=memory_usage_factor
                                    )
        elif (type(select) is np.ndarray):
            self.selected_pid = select
        
        self.use_geos_index = use_geos_index
        self.ts = ts
        if not use_geos_index:
            self.selected_pid.sort()

        # Register a few metadata
        self.N_selected = len( self.selected_pid )
        self.species = species
        self.preserve_particle_index = preserve_particle_index


    def extract_tracked_particles( self, iteration, data_reader, data_list,
                                    species, extensions ):
        """
        Select the elements of each particle quantities in data_list,
        so as to only return those that correspond to the tracked particles

        Parameters
        ----------
        iteration: int
            The iteration at which to extract the particles

        data_reader: a DataReader object
            Used in order to extract the macroparticle IDs

        data_list: list of 1darrays
            A list of arrays with one element per macroparticle, that represent
            different particle quantities

        species: string
            Name of the species being requested

        extensions: list of strings
            The extensions that the current OpenPMDTimeSeries complies with

        Returns
        -------
        A list of 1darrays that correspond to data_list, but where only the
        particles that are tracked are kept. (NaNs may or may not be returned
        depending on whether `preserve_particle_index` was chosen at
        initialization)
        """
        # Extract the particle id, and get the extraction indices
        if not self.use_geos_index:
            pid = data_reader.read_species_data(iteration, species, 'id', extensions)
            selected_indices = self.get_extraction_indices( pid )

            # For each particle quantity, select only the tracked particles
            for i in range(len(data_list)):
                if len(data_list[i]) > 1:  # Do not apply selection on scalars
                    data_list[i] = self.extract_quantity(
                        data_list[i], selected_indices )

            return( data_list )
        else:
            key = self.ts.key_generation_function(iteration, species, "position")
            selected_block = self.ts.query_geos_index.queryRTreeTracingInteracted(key, self.selected_pid)
            print("len(selected_block):", len(selected_block))

            if len(selected_block) == 0:
                return [np.array([]) for _ in data_list]
            
            self.ts.read_strategy = list()
            self.ts.read_chunk_range = list()
            self.ts.sorted_blocks = sorted(selected_block.items(), key=lambda x: int(x[0]))

            self.ts.find_optimal_strategy(0, len(self.ts.sorted_blocks) - 1, 0)

            total_read_size = 0
            for block_start_index, block_end_index in self.ts.read_strategy:
                self.ts.read_chunk_range.append((self.ts.sorted_blocks[block_start_index][1].start, self.ts.sorted_blocks[block_end_index][1].end, None))
                total_read_size += self.ts.sorted_blocks[block_end_index][1].end - self.ts.sorted_blocks[block_start_index][1].start
            

            self.ts.read_chunk_range = sorted(self.ts.read_chunk_range, key=lambda x: x[0])
            print("read_chunk_range", self.ts.read_chunk_range)
            select_array = np.zeros(total_read_size, dtype='bool')
            
            id_list = self.ts.data_reader.read_species_data(iteration, species, 'id', self.ts.extensions, self.ts.read_chunk_range)
            print("len(id_list):", len(id_list))

            prev_offset = 0
            for block_start_index, block_end_index in self.ts.read_strategy:
                current_global_offset = self.ts.sorted_blocks[block_start_index][1].start
                for range_index in range(block_start_index, block_end_index + 1):
                    current_block = self.ts.sorted_blocks[range_index][1]
                    current_id_set = set(current_block.id_data)
                    
                    for i in range(current_block.end - current_block.start):
                        id_offset = current_block.start - current_global_offset + prev_offset + i
                        if current_id_set.__contains__(id_list[id_offset]):
                            select_array[id_offset] = True

                prev_offset += self.ts.sorted_blocks[block_end_index][1].end - self.ts.sorted_blocks[block_start_index][1].start
            # print("sum(select_array):", np.sum(select_array))
            var_list = data_list
            result_list = list()
            for quantity in var_list:
                result = self.ts.data_reader.read_species_data(iteration, species, quantity, self.ts.extensions, self.ts.read_chunk_range)
                result_list.append(result[select_array])
            
            return result_list

            

    def extract_quantity( self, q, selected_indices ):
        """
        Select the elements of the array `q`, so as to only return those
        that correspond to the tracked particles.

        Parameters
        ----------
        q: 1d array of floats or ints
            A particle quantity (one element per particle)

        selected_indices: 1d array of ints
            The indices (in array q) of the particles to be selected.
            If `preserve_particle_index` was selected to be True, this array
            contains -1 at the position of particles that are no longer present

        Returns
        -------
        selected_q: 1d array of floats or ints
            A particle quantity (one element per particles)
            where only the tracked particles are kept
        """
        # Extract the selected elements
        selected_q = q[ selected_indices ]

        # Handle the absent particles
        if self.preserve_particle_index:
            if q.dtype in [ np.float64, np.float32 ]:
                # Fill the position of absent particles by NaNs
                selected_q = np.where( selected_indices == -1,
                                        np.nan, selected_q)
            else:
                # The only non-float quantity in openPMD-viewer is particle id
                selected_q = self.selected_pid

        return( selected_q )

    def get_extraction_indices( self, pid ):
        """
        For each tracked particle (i.e. for each element of self.selected_pid)
        find the index of the same particle in the array `pid`

        Return these indices in an array, so that it can then be used to
        extract quantities (position, momentum, etc.) for the tracked particles

        Parameters
        ----------
        pid: 1darray of ints
            The id of each particle (one element per particle)

        Returns
        -------
        selected_indices: 1d array of ints
            The index of the tracked particles in the array `pid`
            If `preserve_particle_index` was selected to be True, this array
            contains -1 at the position of particles that are no longer present

        Note on the implementation
        --------------------------
        This could be implemented in brute force (i.e. for each element of
        `self.selected_pid`, search the entire array `pid` for the same
        element), but would be very costly.
        Instead, we sort the array `pid` (and keep track of the original
        pid, so as to be able to retrieve the indices) and use the fact
        that it is sorted in order to rapidly extract the elements
        that are also in `self.selected_pid` (which is also sorted)
        """
        # Sort the pid, and keep track of the original index
        # at which each pid was
        original_indices = pid.argsort().astype(np.int64)
        sorted_pid = pid[ original_indices ]

        # Extract only the indices for which sorted_pid is one of pid
        # in self.sselected_pid (i.e. which correpond to one
        # of the original particles)
        selected_indices = np.empty( self.N_selected, dtype=np.int64 )
        N_extracted = extract_indices(
            original_indices, selected_indices, sorted_pid,
            self.selected_pid, self.preserve_particle_index )

        # If there are less particles then self.N_selected
        # (i.e. not all the pid in self.selected_pid were in sorted_pid)
        if N_extracted < self.N_selected:
            if self.preserve_particle_index:
                # Finish filling the array with absent particles
                selected_indices[N_extracted:] = -1
            else:
                # Resize the array
                selected_indices = \
                    selected_indices[:N_extracted]

        return( selected_indices )

@jit
def extract_indices( original_indices, selected_indices,
                        pid, selected_pid, preserve_particle_index ):
    """
    Go through the sorted arrays `pid` and `selected_pid`, and record
    the indices (of the array `pid`) where they match, by storing them
    in the array `selected_indices` (this array is thus modified in-place)

    Return the number of elements that were filled in `selected_indices`
    """
    i = 0
    i_select = 0
    i_fill = 0
    N = len(pid)
    N_selected = len(selected_pid)

    # Go through both sorted arrays (pid and selected_pid) and match them.
    # i.e. whenever the same number appears in both arrays,
    # record the corresponding original index in selected_indices
    while i < N and i_select < N_selected:

        if pid[i] < selected_pid[i_select]:
            i += 1
        elif pid[i] == selected_pid[i_select]:
            selected_indices[i_fill] = original_indices[i]
            i_fill += 1
            i_select += 1
        elif pid[i] > selected_pid[i_select]:
            i_select += 1
            if preserve_particle_index:
                # Fill the index, to indicate that the particle is absent
                selected_indices[i_fill] = -1
                i_fill += 1

    return( i_fill )
