"""
This file has the code to do refinements on the descriptive attributes to make them into candidates.

The refinements are now done for one attribute, based on the data in the subgroup but independant of previous candidate conditions.
"""
import numpy as np
import pandas as pd
from itertools import combinations, permutations
from mlxtend.frequent_patterns import fpgrowth
from mlxtend.preprocessing import TransactionEncoder

import fpgrowth as fp
import candidates as ca

def numerical_refinement(subgroup=None, attribute=None, bins=None, parent=None):
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
    new_candidates = []

    while b <= bins :

        if b == bins:
            end_value = max_value
        else:
            end_value = float(start_value + bin_size)
        
        # Get condition
        range = (start_value, end_value)
        condition = ca.Condition(descriptor=attribute, value=range, datatype='numerical')
        description = ca.Description(conditions=[condition], parent=parent)
        new_candidates.append(description)

        # Get ready for next iteration
        start_value = end_value
        b += 1
    
    #print([cand.__str__() for cand in new_candidates])

    return new_candidates


def boolean_refinement(subgroup=None, attribute=None, parent=None):
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

    condition1 = ca.Condition(descriptor=attribute, value=bool1, datatype='boolean')
    condition2 = ca.Condition(descriptor=attribute, value=bool2, datatype='boolean')

    description1 = ca.Description(conditions=[condition1], parent=parent)
    description2 = ca.Description(conditions=[condition2], parent=parent)
        
    new_candidates = [description1, description2]

    return new_candidates

def ordinal_refinement(subgroup=None, attribute=None, parent=None):
    """
    Refinement of the ordinal attributes into two conditions per unique value.
    The condition will look like: attribute <= val and attribute > val

    INPUT
    - subgroup          : the subgroup (or entire population) that has the wanted information in the descriptor space.
    - attribute (str)   : the name of a ordinal-type attribute that needs to be refined.

    OUTPUT
    - candidates (list) : a list that has all possible conditions for that attribute
    """

    # 1. Get all unique values of the attribute in the subgroup
    unique_vals = list(subgroup[attribute].dropna().unique())

    # 2. Sort the unique values
    # In our use case, reverse=False because: 0 = Best, higher = Worse
    # Otherwise change to reverse=True
    sorted_unique = sorted(unique_vals, reverse=False)

    # 3. For each unique category, in order, add <= cat and > cat to the list of candidates
    new_candidates = []
    for cat in sorted_unique:
        cat_index = sorted_unique.index(cat)

        before = sorted_unique[:cat_index + 1]
        after = sorted_unique[cat_index + 1:]

        # only add if there is a value in the range
        if len(before) != 0:
            condition1 = ca.Condition(descriptor=attribute, value=before, datatype='ordinal')
            description1 = ca.Description(conditions=[condition1], parent=parent)
            new_candidates.append(description1)
            
        if len(after) != 0:
            condition2 = ca.Condition(descriptor=attribute, value=after, datatype='ordinal')
            description2 = ca.Description(conditions=[condition2], parent=parent)
            new_candidates.append(description2)
        
    return new_candidates


def nominal_refinement(subgroup=None, attribute=None, parent=None):
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
    
    new_candidates = []

    for cat in categories:
        condition1 = ca.Condition(descriptor=attribute, value=(1.0, cat), datatype='nominal') # means =
        condition2 = ca.Condition(descriptor=attribute, value=(0.0, cat), datatype='nominal') # means !=

        description1 = ca.Description(conditions=[condition1], parent=parent)
        description2 = ca.Description(conditions=[condition2], parent=parent)
        
        new_candidates = [description1, description2]

    return new_candidates



def collection_refinement(subgroup=None, attribute=None, minimal_support=0.01, maximum_support=1.0, maximum_itemsets=None, closed_itemsets=True, parent=None, store=False):
    """
    Refinement of the collection attributes into the containments.
    The condition will look like: eventTypes includes [GIVEUP, EVALUATE], order does not matter.
    It is based on Frequent Itemset Theory's FP-Growth: we extract frequent itemsets from the data's collections.
    It eliminates the most frequent and infrequent itemsets.

    INPUT: no restrictions is the basis
    - subgroup                      : the subgroup (or entire population) that has the wanted information in the descriptor space.
    - attribute (str)               : the name of a list-type attribute that needs to be refined.
    - minimal_support (0.01; float) : the minimal support that the itemset must have in the entire subgroup (or population). 
    - maximum_support (1.0; float)  : the maximum support that the itemset is allowed to have in the entire subgroup (or population)
    - maximum_length (int)          : a limit to the number of categories in the collection.
    - maximum_itemsets (int)        : the number of itemsets we want to include (or None if we want all)
    - closed_itemsets (bool)        : indicator if we want the closed itemset property to hold

    OUTPUT
    - candidates (list) : a list that has all possible conditions for that attribute, as many as there are unique combinations of the instances.
    """

    data = subgroup[['representative_index', attribute]]
    minsup = round( len(data) * minimal_support, 0)
    maxsup = round( len(data) * maximum_support, 0)

    # Gather a list of all collections

    # If we do store, extract the FIs from the parent node.
    if store:
        frequent_itemsets = parent._FIs[attribute]

    # Otherwise, redo FP-growth and extract new FIs
    else:
        frequent_itemsets = fp.fpgrowth(subgroup=data, attribute_of_interest=attribute, closed=closed_itemsets)

    # Lastly, only keep the conditions that satisfy the constraints: minimal support and maximum support
    # we don't want too frequent itemsets, but also not too unique ones, and not long, uninterpretable ones.

    for i in list(frequent_itemsets.keys()):
        # print(frequent_patterns[i]['frequency'], i)
        if frequent_itemsets[i]['frequency'] < minsup or frequent_itemsets[i]['frequency'] > maxsup:# or len(i) > maximum_length:
            frequent_itemsets.pop(i) #remove if it does not satisfy

    new_candidates = []
        
    if maximum_itemsets is not None:
        # Keep the top-... most frequent itemsets as descriptors.

        sorted_frequent_itemsets = sorted(frequent_itemsets.items(), key=lambda x: x[1]['frequency'], reverse=True)
        select_itemsets = min(len(sorted_frequent_itemsets), maximum_itemsets)

        selected_frequent_itemsets = dict(sorted_frequent_itemsets[:select_itemsets])

        for fi in selected_frequent_itemsets.keys():

            value = list(fi)
            indices = list(selected_frequent_itemsets[fi]['indices'])

            cond = ca.Condition(descriptor=attribute, value=value, datatype='collection')
            cond.add_indices(indices)

            description = ca.Description(conditions=[cond], parent=parent)

            # add condition to the list of candidates
            new_candidates.append(description)            

    # otherwise, we want to keep all found itemsets
    else:
        for fi in frequent_itemsets.keys():

            value = list(fi)
            indices = list(frequent_itemsets[fi]['indices'])

            cond = ca.Condition(descriptor=attribute, value=value, datatype='collection')
            cond.add_indices(indices)

            description = ca.Description(conditions=[cond], parent=parent)

            # add condition to the list of candidates
            new_candidates.append(description)     
    return new_candidates





# =========== DEPRECATED ============= #
def naive_collection_refinement(subgroup=None, attribute=None, minimal_support=0.0, maximum_support=1.0, maximum_length=None):
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
        condition = ca.Condition(descriptor=attribute, value=comb, datatype='collection')
        candidates.append(condition)

    return candidates





def sequence_refinement(subgroup=None, attribute=None, minimal_support=0.01, maximum_support=1.0, maximum_length=None): # I think the same as collection so no additional needed.
    """ Same as collection but does not have to be unique. """

    data_attribute = subgroup[attribute]
    uniques = list(data_attribute.explode().dropna().unique())

    options = []
    for u in uniques:
        options += maximum_length * [u]

    if len(options) <= 1:
        # No variation in the data so no candidate is returned
        return []

    if maximum_length == None:
        maximum_length = len(options) - 1 #Do not take into account the one with all options
        
    combs = []
    for i in range(maximum_length):
        combs += list(permutations(options, i+1))
    
    combs = list(set(combs)) # drop duplicates -> but it randomized I think!

    candidates = []
    for comb in combs:
        cond = ca.Condition(descriptor=attribute, value=comb, datatype='sequence')
        desc = ca.Description(conditions=[cond])
        candidates.append(desc)
    
    return candidates


def subsequence_refinement(subgroup=None, attribute=None, minimal_support=0.01, maximum_support=1.0, maximum_length=None): # I think the same as sequence so no additional needed.
    candidates = sequence_refinement(subgroup=subgroup, attribute=attribute, minimal_support=minimal_support, maximum_support=maximum_support, maximum_length=maximum_length) #improve later, basic version is still the same
    return candidates


def text_refinement(): #tbd future
    return None