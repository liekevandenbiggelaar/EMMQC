"""
This file has the code to do refinements on the descriptive attributes to make them into candidates.

The refinements are now done for one attribute, based on the data in the subgroup but independant of previous candidate conditions.
"""
import numpy as np
from itertools import combinations, permutations

def numerical_refinement(subgroup=None, attribute=None, bins=None):
    """
    Refinement of the numerical attributes into b bins. This is able to deal with NaN values.
    The condition will look like: marksEarned in (0.0, 1.0)

    INPUT
    - subgroup       : the subgroup (or entire population) that has the wanted information in the descriptor space.
    - attribute (str): the name of a numerical-type attribute that needs to be refined.
    - bins (int)     : the number of bins that the numerical candidate range should be partitioned into.

    OUTPUT
    - candidates (list) : a list that has all possible conditions for that attribute, in the numerical case as many as there are bins.
    """

    data_attribute = subgroup[attribute]
    min_value = min(data_attribute)
    max_value = max(data_attribute)

    # Get bin size
    length_range = max_value - min_value

    # if there are fewer values than bins, remove some bins to get nice ranges.
    if len(data_attribute.dropna().unique()) < bins - 1:
        bins = len(data_attribute.dropna().unique()) - 1
        if bins <= 1:
            # No variation in the data so no candidate is returned
            return []

    bin_size = length_range/bins

    # start at the minimum point
    start_value = min_value
    b = 1
    candidates = []

    while b <= bins :
        if b == bins:
            end_value = max_value
        else:
            end_value = float(start_value + bin_size)
        
        # Get condition
        range = (start_value, end_value)
        condition = {attribute: range}
        candidates.append(condition)

        # Get ready for next iteration
        start_value = end_value
        b += 1

    return candidates


def boolean_refinement(subgroup=None, attribute=None):
    """
    Refinement of the boolean attributes into the two option.
    The condition will look like: finished = True and finished = False

    INPUT
    - subgroup          : the subgroup (or entire population) that has the wanted information in the descriptor space.
    - attribute (str)   : the name of a boolean-type attribute that needs to be refined.

    OUTPUT
    - candidates (list) : a list that has all possible conditions for that attribute, in the boolean case two.
    """

    data_attribute = subgroup[attribute]

    if len(data_attribute.dropna().unique()) <= 1:
        # No variation in the data so no candidate is returned
        return []

    bool1 = data_attribute.dropna().unique()[0]
    bool2 = data_attribute.dropna().unique()[1]

    condition1 = {attribute: bool1}
    condition2 = {attribute: bool2}
        
    candidates = [condition1, condition2]

    return candidates


def categorical_refinement(subgroup=None, attribute=None):
    """
    Refinement of the categorical attributes into the options.
    The condition will look like: EventType.GIVEUP = 1 and EventType.GIVEUP = 0

    INPUT
    - subgroup          : the subgroup (or entire population) that has the wanted information in the descriptor space.
    - attribute (str)   : the name of a categorical-type attribute that needs to be refined.

    OUTPUT
    - candidates (list) : a list that has all possible conditions for that attribute, as many as there are unique instances.
    """

    data_attribute = subgroup[attribute]
    categories = list(data_attribute.dropna().unique())

    if len(categories) <= 1:
        # No variation in the data so no candidate is returned
        return []
    
    candidates = []

    for cat in categories:
        condition1 = {attribute: (1.0, cat)} # means =
        condition2 = {attribute: (0.0, cat)} # means !=

        candidates.append(condition1)
        candidates.append(condition2)

    return candidates

def collection_refinement(subgroup=None, attribute=None, limit=None):
    """
    Refinement of the collection attributes into the containments.
    The condition will look like: eventTypes includes [GIVEUP, EVALUATE], order does not matter.

    INPUT
    - subgroup          : the subgroup (or entire population) that has the wanted information in the descriptor space.
    - attribute (str)   : the name of a list-type attribute that needs to be refined.
    - limit (str)       : a limit to the number of categories in the collection.

    OUTPUT
    - candidates (list) : a list that has all possible conditions for that attribute, as many as there are unique combinations of the instances.
    """

    data_attribute = subgroup[attribute]
    options = list(data_attribute.explode().dropna().unique())

    if len(options) <= 1:
        # No variation in the data so no candidate is returned
        return []

    if limit == None:
        limit = len(options) - 1 #Do not take into account the one with all options
    
    combs = []
    for i in range(limit):
        combs += list(combinations(options, i+1))

    candidates = []
    for comb in combs:
        candidates.append({attribute: comb})

    return candidates

def sequence_refinement(subgroup=None, attribute=None, limit=None): # I think the same as collection so no additional needed.
    """ Same as collection but does not have to be unique. """

    data_attribute = subgroup[attribute]
    uniques = list(data_attribute.explode().dropna().unique())

    options = []
    for u in uniques:
        options += limit * [u]

    if len(options) <= 1:
        # No variation in the data so no candidate is returned
        return []

    if limit == None:
        limit = len(options) - 1 #Do not take into account the one with all options
        
    combs = []
    for i in range(limit):
        combs += list(permutations(options, i+1))
    
    combs = list(set(combs)) # drop duplicates -> but it randomized I think!

    candidates = []
    for comb in combs:
        candidates.append({attribute: comb})
    
    return candidates

def subsequence_refinement(subgroup=None, attribute=None, limit=None): # I think the same as collection so no additional needed.
    candidates = sequence_refinement(subgroup=subgroup, attribute=attribute, limit=limit) #improve later, basic version is still the same
    return candidates

def text_refinement(): #tbd future
    return None