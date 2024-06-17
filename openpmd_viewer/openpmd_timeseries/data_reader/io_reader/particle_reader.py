"""
This file is part of the openPMD-viewer.

It defines a function that reads a species record component (data & meta)
from an openPMD file

Copyright 2020, openPMD-viewer contributors
Authors: Axel Huebl
License: 3-Clause-BSD-LBNL
"""
import time
import numpy as np
from scipy import constants
from .utilities import get_data


def read_species_data(series, iteration, species_name, component_name,
                      extensions, read_chunk_range=None, skip_offset=False):
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

    start = time.time()
    data = get_data_new( series, component, output_type=output_type, read_chunk_range=read_chunk_range)
    end = time.time()
    print(f"get target data: {component_name}. Time elapsed: ", end - start)

    if skip_offset:
        return data

    # For ED-PIC: if the data is weighted for a full macroparticle,
    # divide by the weight with the proper power
    # (Skip this if the current record component is the weight itself)
    if 'ED-PIC' in extensions and ompd_record_name != 'weighting':
        macro_weighted = record.get_attribute('macroWeighted')
        weighting_power = record.get_attribute('weightingPower')
        if (macro_weighted == 1) and (weighting_power != 0):
            w_component = next(species['weighting'].items())[1]
            w = get_data_new(series, w_component, read_chunk_range=read_chunk_range)
            data *= w ** (-weighting_power)

    # - Return positions, with an offset
    if component_name in ['x', 'y', 'z']:
        start = time.time()
        offset = get_data_new(series, species['positionOffset'][component_name], read_chunk_range=read_chunk_range)
        end = time.time()
        print(f"get position offset for read {component_name}. Time elapsed: ", end - start)

        start = time.time()
        data += offset
        end = time.time()
        print("data += offset. Time elapsed: ", end - start)
        del offset

    # - Return momentum in normalized units
    elif component_name in ['ux', 'uy', 'uz' ]:
        mass_component = next(species['mass'].items())[1]
        start = time.time()
        m = get_data_new(series, mass_component, read_chunk_range=read_chunk_range)
        end = time.time()
        print(f"get mass read for {component_name}. Time elapsed: ", end - start)

        start = time.time()
        # Normalize only if the particle mass is non-zero
        if np.all( m != 0 ):
            data *= 1. / (m * constants.c)
        end = time.time()
        print("data *= norm_factor. Time elapsed: ", end - start)
        del m

    # Return the data
    return data


def read_species_support_data(series, iteration, species_name, component_name,
                      extensions, read_chunk_range=None, skip_offset=False):
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

    # For ED-PIC: if the data is weighted for a full macroparticle,
    # divide by the weight with the proper power
    # (Skip this if the current record component is the weight itself)
    if 'ED-PIC' in extensions and ompd_record_name != 'weighting':
        macro_weighted = record.get_attribute('macroWeighted')
        weighting_power = record.get_attribute('weightingPower')
        if (macro_weighted == 1) and (weighting_power != 0):
            w_component = next(species['weighting'].items())[1]
            w = get_data_new(series, w_component, read_chunk_range=read_chunk_range)
            return w ** (-weighting_power)

    # - Return positions, with an offset
    if component_name in ['x', 'y', 'z']:
        start = time.time()
        offset = get_data_new(series, species['positionOffset'][component_name], read_chunk_range=read_chunk_range)
        end = time.time()
        print(f"get position offset for read {component_name}. Time elapsed: ", end - start)

        return offset

    # - Return momentum in normalized units
    elif component_name in ['ux', 'uy', 'uz' ]:
        mass_component = next(species['mass'].items())[1]
        start = time.time()
        m = get_data_new(series, mass_component, read_chunk_range=read_chunk_range)
        end = time.time()
        print(f"get mass read for {component_name}. Time elapsed: ", end - start)

        # Normalize only if the particle mass is non-zero
        return m

def tuple_to_slice(read_chunk_range):
    return tuple(map(lambda s: slice(s[0], s[1], s[2]), read_chunk_range))


def gc_get_data(series, component, chunk_slices, output_type=None):
    raw_data_list = list()
    for chunk_slice in chunk_slices:
        # start = time.time()
        x = component[chunk_slice]
        series.flush()
        raw_data_list.append(x)
        # end = time.time()
        # print(x.size, end - start)
    data = np.concatenate(raw_data_list)

    if (output_type is not None) and (data.dtype != output_type):
        data = data.astype( output_type )
    return data

def get_data_new(series, record_component, i_slice=None, pos_slice=None, output_type=None, read_chunk_range=None):
    if not read_chunk_range:
        return get_data(series, record_component, i_slice, pos_slice, output_type)
    else:
        chunk_slices = tuple_to_slice(read_chunk_range)
        return gc_get_data(series, record_component, chunk_slices, output_type)

