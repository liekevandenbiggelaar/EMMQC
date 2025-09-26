"""
This file has the functions to transform the descriptions into the corresponding subgroup of records.
"""

def get_subgroup_target_space(target_space=None, indices=None):

    subgroup_targets = target_space.iloc[indices]

    return subgroup_targets


def check_record_inclusion(descriptive_space=None, dtypes=None, candidate=None):
    """
    Get the indices of the records that correspond to the conditions set in the candidate description.
    """

    new_space = descriptive_space # in condition iteration, do include all again to save time.

    for attribute in candidate.keys():
        condition = candidate[attribute]
        attr_type = [key for key, val in dtypes.items() if attribute in val][0]

        
        if attr_type == 'numerical':
            new_space = get_indices_numerical(new_space, attribute, condition)
        
        elif attr_type == 'boolean':
            new_space = get_indices_boolean(new_space, attribute, condition)

        elif attr_type == 'categorical':
            new_space = get_indices_categorical(new_space, attribute, condition)

        elif attr_type == 'collection':
            new_space = get_indices_collection(new_space, attribute, condition)
        
        elif attr_type == 'sequence':
            new_space = get_indices_sequence(new_space, attribute, condition)
        
        else:
            return "ERROR -- Invalid attribute type."

    indices = list(new_space.index) # Keep updating each iteration.

    return indices, new_space


def get_indices_numerical(descriptive_space=None, attribute=None, condition=None):
    """
    Retrieve the indices of the records that are included in the range that is set in the condition.
    """

    minimum = float(condition[0])
    maximum = float(condition[1])

    new_space = descriptive_space[ (descriptive_space[attribute] >= minimum) & (descriptive_space[attribute] <= maximum) ]

    return new_space


def get_indices_boolean(descriptive_space=None, attribute=None, condition=None):
    """
    Retrieve the indices of the records that are either True or False depending on the condition.
    """

    val = condition[0]
    new_space = descriptive_space[ descriptive_space[attribute] == val ]
        
    return new_space


def get_indices_categorical(descriptive_space=None, attribute=None, condition=None):
    """
    Retrieve the indices of the records that either do or do not mention this category depending on the condition.
    """

    sign = condition[0]
    val = condition[1]

    if sign == 0: # has not
        new_space = descriptive_space[ descriptive_space[attribute] != val ]

    elif sign == 1: # has
        new_space = descriptive_space[ descriptive_space[attribute] == val ]
        
    return new_space


def get_indices_collection(descriptive_space=None, attribute=None, condition=None):
    """
    Retrieve the indices of the records that have the list of categories in the condition in their data, order is irrelevant.
    """

    selection = set(condition)

    #check if the categories in the condition are all in the records' attribute list.
    new_space = descriptive_space[ descriptive_space[attribute].apply(lambda x: isinstance(x, (list, set)) and set(selection).issubset(set(x))) ] 
        
    return new_space

def get_indices_sequence(descriptive_space=None, attribute=None, condition=None): # not yet included, later if we use event and make it into a list.
    """
    Retrieve the indices of the records that have the sequence of categories in the condition in their data, order is relevant.
    """

    # ===== NEEDS TO BE CHECKED STILL!
    def issubsequence(selection, candidate):
        iteration = iter(candidate)
        return all(item in iteration for item in selection)
    
    selection = set(condition)

    #check if the categories in the condition are all in the records' attribute list in that order.
    new_space = descriptive_space[ descriptive_space[attribute].apply(lambda x: isinstance(x, (list, set)) and issubsequence(selection, x)) ] 
        
    return new_space

def get_indices_text(descriptive_space=None, attribute=None, condition=None): # tbd future
    return None