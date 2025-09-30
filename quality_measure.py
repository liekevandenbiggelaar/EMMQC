"""
This file contains all code related to the quality measure.
"""

import numpy as np
import math

import subgroup_selection as ss
import model_class as mc

def entropy_function(subgroup_size=None, population_size=None):
    complement_size = population_size - subgroup_size
    
    # no subgroup so invaluable
    if subgroup_size == 0 or complement_size == 0:
        return 0
    
    prob_subgroup = subgroup_size / population_size
    prob_complement = complement_size / population_size
    
    entropy = -prob_subgroup * math.log(prob_subgroup) + prob_complement * math.log(prob_complement)
    
    return entropy


def model_function(target_space=None, model=None):

    if model == 'finish_rate':
        quality = mc.finish_rate(target_space) 

    elif model == 'average_marks_ratio':
        quality = mc.average_marks_ratio(target_space)
    
    else:
        return "== ERROR: Invalid Model Class"

    return quality


def compute_quality_measure(subgroup_indices=None, target_space=None, model=None, population_quality=None, population_size=None):
    """
    Model options: finish_rate, average_marks_rate
    """

    # Get needed values
    subgroup_size = len(subgroup_indices)
    subgroup_target_space = ss.get_subgroup_target_space(target_space, subgroup_indices)

    # Calculate both components
    entropy = entropy_function(subgroup_size, population_size)
    subgroup_quality = model_function(subgroup_target_space, model)

    # Total quality
    #model_quality = np.abs(population_quality - subgroup_quality)
    quality_measure = subgroup_quality

    return quality_measure




