""" 
This file has the code to make the split of descriptors and targets, and gathers the dtypes of all attributes.
"""
import numpy as np

import refinements as rf

def split_spaces(data=None, descriptors=[], targets=[], ids=[]):
    """
    The original database gets split into the descriptive and target space, discarding all other columns that are not mentioned.

    INPUT
    - descriptors (list): names of the columns that are included in the descriptive space.
    - targets (list)    : names of the columns that are included in the target space.
    - ids (list)        : names of the columns that are included as an ID of sorts.
    - skips (list)      : names of the columns that will be skipped.

    OUTPUT
    - descriptive_space : dataframe of the descriptors, including the IDs.
    - target_space      : dataframe of the targets, including the IDs.
    - descriptor_types  : dictionary of the data types of the descriptors.
    - attributes        : dictionary containing information on the attribute splits, skips/ids/descriptors/targets.
    """

    # we split of the data into two spaces
    descriptive_space = data[ids + descriptors]
    target_space = data[ids + targets]

    # all other attributes will be skipped
    skipped = list( set(data.columns) - set(descriptors) - set(targets) - set(ids))

    # get all data types of the descriptive attributes, necessary for refinement
    descriptor_types = manual_attribute_types()
    #descriptor_types = get_attribute_types(descriptive_space, ids)

    # store relevant information on attribute placements
    attributes = {'descriptive_attributes': descriptors, 'target_attributes': targets, 'id_attributes': ids, 'skip_attributes': skipped}

    return descriptive_space, target_space, attributes, descriptor_types

def manual_attribute_types():

    dtypes = {'categorical': ['itemType'], 
              'boolean': ['interactionType'], 
              'numerical': [], 
              'ordinal': ['marksTotal', 'marksTotal_interaction', 'usedAttempts', 'marksPenalty', 'hintsRequested', 'mathErrors'],
              'collection': ['skills', 'positive_skills', 'negative_skills'],
              'sequence': ['event_types', 'event_evaluations'],
              'subsequence': ['stepTypes']}

    return dtypes

def DEPRECATED_get_attribute_types(data=None, ids=[]):
    """ 
    The columns in the data are categorized into four data types: numerical, boolean, categorical. We assume that all attributes are within these three types.
    Other attribute types such as lists, dicts, tuples, etc. should be removed as a skip attribute.

    INPUT
    - data       : any dataframe that you want the data types from.
    - ids (list) : the attributes that are indices and should not be conditioned.

    OUTPUT
    - dtypes (dict) : a dictionary that contains the attributes sorted per category for the input dataframe. 
    """

    # initialize
    dtypes = {'categorical': [], 'boolean': [], 'numerical': [], 'collection': []}

    # check each column in the data space
    for col in data.columns:

        # we do not want the types of the IDs
        if col in ids:
            continue
        
        # check if the column has a boolean data type
        elif data[col].dtype == 'bool': #only two options
            dtypes['boolean'].append(col)
        
        # check if the column has a numerical data type
        elif np.issubdtype(data[col].dtype, np.number):
            dtypes['numerical'].append(col)
        
        # otherwise it is a categorical value or invalid one
        elif isinstance(data[col].dropna().iloc[0], str) and len(data[col].dropna().unique()) > 2:
            dtypes['categorical'].append(col)
        
        elif isinstance(data[col].dropna().iloc[0], list): # lists are unordered
            dtypes['collection'].append(col)

        elif isinstance(data[col].dropna().iloc[0], tuple): # tuples are ordered
            dtypes['sequence'].append(col)
        
        else:
            continue

    return dtypes


def get_candidates_per_attribute(descriptive_space=None, dtypes=None, numerical_bins=None, collection_limit=None, description_keys=[]):
    """
    This performs the refinement on all attributes in the type dictionary. It returns a dictionary with the possible conditions stored per attribute.
    
    INPUT
    - descriptive_space     : the database of the descriptor space of the selected subgroup.
    - dtypes (dict)         : a dictionary that contains the attributes sorted per category for the input dataframe.
    - numerical_bins (int)  : the number of bins that the numerical attributes need to be divided into.
    - collection_limit (int): the maximum number of options in the collection refinement lists.

    OUTPUT
    - candidates_per_attribute (dict) : a dictionary with all candidate conditions stored per attribute.
    - candidates (list)               : a list of all candidate conditions
    """

    # initialize
    candidates_per_attribute = {}
    candidates = []

    # go over all numerical attributes
    for att in dtypes['numerical']:

        conditions = rf.numerical_refinement(descriptive_space, att, numerical_bins)
        candidates += conditions
        att_list = []

        for cond in conditions:
            att_list.append(cond[att])

        candidates_per_attribute[att] = att_list  

    # go over all boolean attributes
    for att in dtypes['boolean']:

        conditions = rf.boolean_refinement(descriptive_space, att)
        candidates += conditions
        att_list = []

        for cond in conditions:
            att_list.append(cond[att])

        candidates_per_attribute[att] = att_list  

    # go over all categorical attributes
    for att in dtypes['categorical']:

        conditions = rf.categorical_refinement(descriptive_space, att)
        candidates += conditions
        att_list = []

        for cond in conditions:
            att_list.append(cond[att])

        candidates_per_attribute[att] = att_list 

    # go over all collection attributes
    for att in dtypes['collection'] or att in dtypes['sequence'] or att in dtypes['subsequence']:

        conditions = rf.collection_refinement(descriptive_space, att, limit=collection_limit)
        candidates += conditions
        att_list = []

        for cond in conditions:
            att_list.append(cond[att])

        candidates_per_attribute[att] = att_list  

    return candidates_per_attribute, candidates

def add_condition(description=None, candidates=None):
    """
    Take from the dictionary, we will not further refine numericals because this risks the numerical ranges to get too large, especially with fewer instances as here.
    If the condition does not change anything, do not add it. But this is in the subgroup selection and redundancy reduction phase.
    """

    new_candidates = []

    for cand in candidates:
        candidate_attribute = list(cand.keys())[0]
        description_copy = description.copy()

        description_copy[candidate_attribute] = cand[candidate_attribute] #replaces if candidate attribute already in description, otherwise adds.
        new_candidates.append(description_copy)

    return new_candidates


def global_add_condition(description=None, starting_candidates=None):
    """
    Take from the dictionary, we will not further refine numericals because this risks the numerical ranges to get too large, especially with fewer instances as here.
    If the condition does not change anything, do not add it. But this is in the subgroup selection and redundancy reduction phase.
    """

    # Get all attributes already covered in the description
    attributes = list(description.keys())

    # Select only the starting descriptions of other attributes than those already included in the input description
    other_descriptions = [starting_candidates[i] for i in range(len(starting_candidates)) if not set(attributes).issubset(set(list(starting_candidates[i].keys()))) ]

    # Combine these descriptions with the existing one to make new candidates
    new_candidates = [description | new for new in other_descriptions]

    return new_candidates