"""
This file is part of the openPMD-viewer.

It defines a function that reads a species record component (data & meta)
from an openPMD file

Copyright 2020, openPMD-viewer contributors
Authors: Axel Huebl
License: 3-Clause-BSD-LBNL
"""

import numpy as np
from scipy import constants
from .utilities import get_data, chunk_to_slice


class QueryResult:
    def __init__(self):
        self.start = 0
        self.end = 0


class QueryBlockResult:
    def __init__(self):
        self.start = 0
        self.end = 0
        self.q = dict()


def read_species_data(series, iteration, species_name, component_name,
                      extensions):
    """
    Extract a given species' record_comp

    Parameters
    ----------
    series: openpmd_api.Series
        An open, readable openPMD-api series object

    iteration: integer
        Iteration from which parameters should be extracted

    species_name: string
        The name of the species to extract (in the openPMD file)

    component_name: string
        The record component to extract
        Either 'x', 'y', 'z', 'ux', 'uy', 'uz', or 'w'

    extensions: list of strings
        The extensions that the current OpenPMDTimeSeries complies with
    """
    it = series.iterations[iteration]

    # Translate the record component to the openPMD format
    dict_record_comp = {'x': ['position', 'x'],
                        'y': ['position', 'y'],
                        'z': ['position', 'z'],
                        'ux': ['momentum', 'x'],
                        'uy': ['momentum', 'y'],
                        'uz': ['momentum', 'z'],
                        'w': ['weighting', None]}
    
    if component_name in dict_record_comp:
        ompd_record_name, ompd_record_comp_name = \
            dict_record_comp[component_name]
    elif component_name.find('/') != -1:
        ompd_record_name, ompd_record_comp_name = \
            component_name.split('/')
    else:
        ompd_record_name = component_name
        ompd_record_comp_name = None

    # Extract the right dataset
    species = it.particles[species_name]
    record = species[ompd_record_name]
    if record.scalar:
        component = next(record.items())[1]
    else:
        component = record[ompd_record_comp_name]

    if ompd_record_name == 'id':
        output_type = np.uint64
    else:
        output_type = np.float64
    data = get_data( series, component, output_type=output_type )

    # For ED-PIC: if the data is weighted for a full macroparticle,
    # divide by the weight with the proper power
    # (Skip this if the current record component is the weight itself)
    if 'ED-PIC' in extensions and ompd_record_name != 'weighting':
        macro_weighted = record.get_attribute('macroWeighted')
        weighting_power = record.get_attribute('weightingPower')
        if (macro_weighted == 1) and (weighting_power != 0):
            w_component = next(species['weighting'].items())[1]
            w = get_data( w_component )
            data *= w ** (-weighting_power)

    # - Return positions, with an offset
    if component_name in ['x', 'y', 'z']:
        offset = get_data(series, species['positionOffset'][component_name])
        data += offset
    # - Return momentum in normalized units
    elif component_name in ['ux', 'uy', 'uz' ]:
        mass_component = next(species['mass'].items())[1]
        m = get_data(series, mass_component)
        # Normalize only if the particle mass is non-zero
        if np.all( m != 0 ):
            norm_factor = 1. / (m * constants.c)
            data *= norm_factor


    # Return the data
    return data

def tuple_to_slice(geos_results, read_strategy):
    # (result_obj.start, result_obj.end, None)
    if read_strategy:
        return tuple(map(lambda s: slice(s[1].start, s[1].end+1, None), geos_results))
    else:
        return tuple(map(lambda s: slice(s[0], s[1], s[2]), geos_results))


def gc_get_data(series, component, chunk_slices, output_type=None):
    raw_data_list = list()
    for chunk_slice in chunk_slices:
        x = component[chunk_slice]
        series.flush()
        raw_data_list.append(x)
    data = np.concatenate(raw_data_list)

    if (output_type is not None) and (data.dtype != output_type):
        data = data.astype( output_type )
    return data


def gc_get_data_block(series, component, blocks, output_type=None):
    raw_data_list = list()
    for block_info in blocks.values():
        block_index = slice(block_info.start, block_info.end + 1, None)
        x = component[block_index]
        series.flush()
        if not block_info.q:
            raw_data_list.append(x)
        else:
            for q_slice in block_info.q.values():
                raw_data_list.append(x[q_slice.start - block_info.start:q_slice.end+1 - block_info.start])
    data = np.concatenate(raw_data_list)

    if (output_type is not None) and (data.dtype != output_type):
        data = data.astype( output_type )
    return data


def gc_index_read_species_data(series, iteration, species_name, component_name,
                      extensions, geos_results, read_strategy=None):
    it = series.iterations[iteration]

    # Translate the record component to the openPMD format
    dict_record_comp = {'x': ['position', 'x'],
                        'y': ['position', 'y'],
                        'z': ['position', 'z'],
                        'ux': ['momentum', 'x'],
                        'uy': ['momentum', 'y'],
                        'uz': ['momentum', 'z'],
                        'w': ['weighting', None]}

    if component_name in dict_record_comp:
        ompd_record_name, ompd_record_comp_name = \
            dict_record_comp[component_name]
    elif component_name.find('/') != -1:
        ompd_record_name, ompd_record_comp_name = \
            component_name.split('/')
    else:
        ompd_record_name = component_name
        ompd_record_comp_name = None

    # Extract the right dataset
    species = it.particles[species_name]
    record = species[ompd_record_name]
    if record.scalar:
        component = next(record.items())[1]
    else:
        component = record[ompd_record_comp_name]

    if ompd_record_name == 'id':
        output_type = np.uint64
    else:
        output_type = np.float64

    if isinstance(geos_results, dict):
        if read_strategy:
            # something wrong with dict()
            geos_results_optimized = dict()
            for block_start, block_end in read_strategy:
                geos_results_optimized[block_start] = geos_results[block_start]
                geos_results_optimized[block_start].end = geos_results[block_end].end
                geos_results_optimized[block_start].q = dict()
                for i in range(block_start, block_end + 1):
                    geos_results_optimized[block_start].q[i] = geos_results[i]
            data = gc_get_data_block(series, component, geos_results_optimized, output_type)

        else:
            data = gc_get_data_block(series, component, geos_results, output_type)
        # - Return positions, with an offset
        if component_name in ['x', 'y', 'z']:
            offset = gc_get_data_block(series, species['positionOffset'][component_name], geos_results)
            if np.all(offset != 0):
                data += offset
        # - Return momentum in normalized units
        elif component_name in ['ux', 'uy', 'uz' ]:
            mass_component = next(species['mass'].items())[1]
            m = gc_get_data_block(series, mass_component, geos_results)
            # Normalize only if the particle mass is non-zero
            if np.all( m != 0 ):
                norm_factor = 1. / (m * constants.c)
                data *= norm_factor

    elif isinstance(geos_results, list):
        chunk_slices = tuple_to_slice(geos_results, read_strategy)
        if read_strategy:
            # something wrong with dict()
            geos_results_optimized = dict()
            for block_start, block_end in read_strategy:
                geos_results_optimized[block_start] = QueryBlockResult()
                geos_results_optimized[block_start].start = geos_results[block_start][1].start
                geos_results_optimized[block_start].end = geos_results[block_end][1].end
                geos_results_optimized[block_start].q = dict()
                for i in range(block_start, block_end + 1):
                    geos_results_optimized[block_start].q[i] = geos_results[i][1]
            data = gc_get_data_block(series, component, geos_results_optimized, output_type)
            # - Return positions, with an offset
            if component_name in ['x', 'y', 'z']:
                offset = gc_get_data_block(series, species['positionOffset'][component_name], geos_results_optimized)
                if np.all(offset != 0):
                    data += offset
            elif component_name in ['ux', 'uy', 'uz' ]:
                mass_component = next(species['mass'].items())[1]
                m = gc_get_data_block(series, mass_component, geos_results_optimized)
                # Normalize only if the particle mass is non-zero
                if np.all( m != 0 ):
                    norm_factor = 1. / (m * constants.c)
                    data *= norm_factor

        else:
            data = gc_get_data(series, component, chunk_slices, output_type)
            # - Return positions, with an offset
            if component_name in ['x', 'y', 'z']:
                offset = gc_get_data(series, species['positionOffset'][component_name], chunk_slices)
                if np.all(offset != 0):
                    data += offset
            # - Return momentum in normalized units
            elif component_name in ['ux', 'uy', 'uz' ]:
                mass_component = next(species['mass'].items())[1]
                m = gc_get_data(series, mass_component, chunk_slices)
                # Normalize only if the particle mass is non-zero
                if np.all( m != 0 ):
                    norm_factor = 1. / (m * constants.c)
                    data *= norm_factor

    return data