""" 
This file has the code to make the split of descriptors and targets, and gathers the dtypes of all attributes.
"""
import numpy as np

import refinements as rf


class Condition:

    def __init__(self, descriptor, value, datatype):

        self._descriptor = descriptor
        self._value = value
        self._datatype = datatype

        self._indices = None # only has a value for Collection datatype

    def add_indices(self, indices):

        if self._datatype == 'collection':
            self._indices = indices

        else:
            print("Descriptors of this datatype do not include indices.")

    def __str__(self):
        if self._datatype == 'boolean':
            summary = f"{self._descriptor.upper()} is {self._value}"
        
        elif self._datatype == 'numerical':
            summary = f"{self._descriptor.upper()} is between {self._value[0]} and {self._value[1]}"
        
        elif self._datatype == 'nominal':
            if self._value[0] == 0:
                summary = f"{self._descriptor.upper()} is not {self._value[1]}"     
            elif self._value[0] == 1:
                summary = f"{self._descriptor.upper()} is {self._value[1]}" 

        elif self._datatype ==  'ordinal':
            summary = f"{self._descriptor.upper()} is between {self._value[0]} and {self._value[-1]}"

        elif self._datatype == 'collection':
            summary = f"{self._descriptor.upper()} contains at least {self._value}"                  

        # elif self._datatype == 'sequence':
        #     summary = f"{self._descriptor.upper()} has {self._value} consecutively without interruptions"
        
        # elif self._datatype == 'subsequence':
        #     summary = f"{self._descriptor.upper()} has {self._value} consecutively with interruptions"

        return summary


class Description:

    def __init__(self, conditions, parent=None):

        self._conditions = conditions # list of conditions, initialize as empty
        self._descriptors = [cond._descriptor for cond in self._conditions] # list of descriptors in the conditions
        self._parent = parent

    def __str__(self):
        conds = self._conditions

        summ_conds = " & ".join([cond.__str__() for cond in conds])

        return f"Description: {summ_conds}."

    
    def get_condition(self, descriptor):
        """ Get the condition that has this descriptor. """

        if descriptor not in self._descriptors:
            return f"{descriptor} is not in this Description"

        else:
            for cond in self._conditions:
                if cond._descriptor == descriptor:
                    return cond._value
                else:
                    continue
    
    



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

    dtypes = {'nominal': ['interactionType', 'primarySubject', 'secondarySubject', "hintsRequested_cat", 'try_count'], 
              'boolean': ['context_hint'], 
              'numerical': [], 
              'ordinal': [], 
                            #[  'hintsRequested' ],
                        #   , 'event_types_EVALUATE', 'event_types_HINT',
                        #     'event_evaluations_CORRECT', 'event_evaluations_ERROR',
                        #     'event_evaluations_FALSE_EXPRESSION',
                        #     'event_evaluations_HINT', 'event_evaluations_NO_MATCH',
                        #     'event_evaluations_PARSE_ERROR', 'event_evaluations_TRUE_EXPRESSION',
                        #     'event_evaluations_UNKNOWN_STEP'],
 #                           ],
              'collection': ['skills', 'positive_skills', 'negative_skills', 'event_evaluations', 'stepTypes']}

    return dtypes

def get_candidates_per_attribute(descriptive_space=None, dtypes=None, refinement_params=None, parent=None, store=False):
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
    candidates = []

    # go over all numerical attributes
    for att in dtypes['numerical']:

        conditions = rf.numerical_refinement(subgroup=descriptive_space, attribute=att, bins=refinement_params['numerical_bins'], parent=parent)
        candidates += conditions
 

    # go over all boolean attributes
    for att in dtypes['boolean']:

        # make sure that there are still two options in this attribute. Otherwise, we skip this.
        if len(descriptive_space[att].unique()) > 1:
            conditions = rf.boolean_refinement(subgroup=descriptive_space, attribute=att, parent=parent)
            candidates += conditions
        
        # otherwise there are no unique new combination and we skip
        else:
            continue
    
    # go over all ordinal attributes
    for att in dtypes['ordinal']:

        conditions = rf.ordinal_refinement(subgroup=descriptive_space, attribute=att, parent=parent)
        candidates += conditions
 

    # go over all categorical attributes
    for att in dtypes['nominal']:

        conditions = rf.nominal_refinement(subgroup=descriptive_space, attribute=att, parent=parent)
        candidates += conditions


    # go over all collection attributes
    for att in dtypes['collection']:

        conditions = rf.collection_refinement(subgroup=descriptive_space, attribute=att, parent=parent, store=store,
                                              minimal_support=refinement_params['minimal_support_collections'], maximum_support=refinement_params['maximum_support_collections'], 
                                              maximum_itemsets=refinement_params['maximum_itemsets'], closed_itemsets=refinement_params['closed_itemsets'])
        candidates += conditions


    # # go over all sequence attributes
    # for att in dtypes['sequence']:
        
    #     conditions = rf.collection_refinement(subgroup=descriptive_space, attribute=att, maximum_length=refinement_params['maximum_length_collections'],
    #                                           minimal_support=refinement_params['minimal_support_collections'], maximum_support=refinement_params['maximum_support_collections'])
        
    #     #rf.sequence_refinement(subgroup=descriptive_space, attribute=att, maximum_length=refinement_params['maximum_length_sequence'],
    #     #                                      minimal_support=refinement_params['minimal_support_sequence'], maximum_support=refinement_params['maximum_support_sequence'])
        
    #     candidates += conditions


    # # go over all subsequence attributes
    # for att in dtypes['subsequence']:
        
    #     conditions = rf.collection_refinement(subgroup=descriptive_space, attribute=att, maximum_length=refinement_params['maximum_length_collections'],
    #                                           minimal_support=refinement_params['minimal_support_collections'], maximum_support=refinement_params['maximum_support_collections'])
        
    #     # rf.subsequence_refinement(subgroup=descriptive_space, attribute=att, maximum_length=refinement_params['maximum_length_subsequence'],
    #     #                                       minimal_support=refinement_params['minimal_support_subsequence'], maximum_support=refinement_params['maximum_support_subsequence'])
    #     candidates += conditions


    return candidates


def add_condition(old_description: Description, new_condition: Condition, parent=None):
    """
    Take from the dictionary, we will not further refine numericals because this risks the numerical ranges to get too large, especially with fewer instances as here.
    If the condition does not change anything, do not add it. But this is in the subgroup selection and redundancy reduction phase.
    """

    new_description_conditions = []


    for old_condition in old_description._conditions:

        # we do not want to include this old condition, because we refine it further in the new_condition
        if old_condition._descriptor == new_condition._descriptor:
            if new_condition._datatype == 'numerical' or new_condition._datatype == 'ordinal':
                new_description_conditions.append(new_condition)
            
            elif new_condition._datatype == 'boolean':
                new_description_conditions.append(old_condition) # keep the old one as this always holds (but it probably won't matter anyway because this should not be possible)

            # in the case of nominal attributes, we should allow both.
            elif new_condition._datatype == 'nominal':
                new_description_conditions.append(old_condition)
                new_description_conditions.append(new_condition)
            
            # aggregate these conditions as they always occur together and the indices are those of the new condition
            elif new_condition._datatype == 'collection':
                old_vals = old_condition._value
                new_vals = new_condition._value

                agg_vals = list(set(old_vals + new_vals))
                agg_cond = Condition(descriptor=new_condition._descriptor, value=agg_vals, datatype='collection')
                agg_cond.add_indices(indices=new_condition._indices)
                new_description_conditions.append(agg_cond)

        else:
            new_description_conditions.append(old_condition)
        
    if not( new_condition._descriptor in [c._descriptor for c in new_description_conditions] ):
        new_description_conditions.append(new_condition)
        
    new_description = Description(conditions=new_description_conditions, parent=parent)
    # if len(old_description._descriptors) >= 2:

    #     print(f"old descr: {old_description}")
    #     print(f"new cond: {new_condition}")
    #     print(f"new descr: {new_description}")
    
    return new_description


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




# ============= OLD ===============




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

