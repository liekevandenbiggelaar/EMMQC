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

    subgroup_descriptors = descriptive_space # in condition iteration, do include all again to save time.

    for condition in candidate._conditions:

        attr_type = condition._datatype

        if attr_type == 'numerical': 
            subgroup_descriptors = get_indices_numerical(subgroup_descriptors, condition)
        
        elif attr_type == 'boolean':
            subgroup_descriptors = get_indices_boolean(subgroup_descriptors, condition)
        
        elif attr_type == 'ordinal':
            subgroup_descriptors = get_indices_ordinal(subgroup_descriptors, condition)

        elif attr_type == 'nominal':
            subgroup_descriptors = get_indices_categorical(subgroup_descriptors, condition)

        elif attr_type == 'collection':
            subgroup_descriptors = get_indices_collection(subgroup_descriptors, condition)
        
        elif attr_type == 'sequence':
            subgroup_descriptors = get_indices_sequence(subgroup_descriptors, condition)

        elif attr_type == 'subsequence':
            subgroup_descriptors = get_indices_subsequence(subgroup_descriptors, condition)

        else:
            return "ERROR -- Invalid attribute."

    if subgroup_descriptors is None or len(subgroup_descriptors) == 0:
        indices = []
    else:
        indices = list(subgroup_descriptors['representative_index']) # Keep updating each iteration.

    return indices, subgroup_descriptors


def get_indices_numerical(descriptive_space=None, condition=None):
    """
    Retrieve the indices of the records that are included in the range that is set in the condition.
    """

    minimum = float(condition._value[0])
    maximum = float(condition._value[1])

    new_space = descriptive_space[ (descriptive_space[condition._descriptor] >= minimum) & (descriptive_space[condition._descriptor] <= maximum) ]

    return new_space


def get_indices_boolean(descriptive_space=None, condition=None):
    """
    Retrieve the indices of the records that are either True or False depending on the condition.
    """

    val = condition._value
    new_space = descriptive_space[ descriptive_space[condition._descriptor] == val ]
        
    return new_space


def get_indices_ordinal(descriptive_space=None, condition=None):

    val = condition._value
    new_space = descriptive_space[ descriptive_space[condition._descriptor].isin(val)]

    return new_space


def get_indices_categorical(descriptive_space=None, condition=None):
    """
    Retrieve the indices of the records that either do or do not mention this category depending on the condition.
    """

    sign = condition._value[0]
    val = condition._value[1]

    if sign == 0: # has not
        new_space = descriptive_space[ descriptive_space[condition._descriptor] != val ]

    elif sign == 1: # has
        #print('arrived here')
        #print(descriptive_space.head())
        #print(descriptive_space.shape)
        #print(len(descriptive_space['representative_index'].value_counts()))
        new_space = descriptive_space[ descriptive_space[condition._descriptor] == val ]
        #print(new_space.head())
        #print(new_space['e1'].value_counts())
        #print(len(new_space['representative_index'].value_counts()))
        #print(new_space.shape)
        
    return new_space


def get_indices_collection(descriptive_space=None, condition=None, naive=False):
    """
    Retrieve the indices of the records that have the list of categories in the condition in their data, order is irrelevant.
    """

    if naive:
        selection = condition._value

        #check if the categories in the condition are all in the records' attribute list.
        new_space = descriptive_space[ descriptive_space[condition._descriptor].apply(lambda x: isinstance(x, (list, set)) and set(selection).issubset(set(x))) ] 
    
    else:
        new_space = descriptive_space[ descriptive_space['representative_index'].isin(condition._indices)] 
        
    return new_space

def get_indices_sequence(descriptive_space=None, condition=None): # not yet included, later if we use event and make it into a list.
    """
    Retrieve the indices of the records that have the sequence of categories in the condition in their data, order is relevant.
    """

    selection = condition._value
    selected_records = []

    for i in range(len(descriptive_space)):
        rp_idx = descriptive_space.iloc[i]['representative_index']
        attr_collection = descriptive_space[condition._descriptor].iloc[rp_idx]
        #print(f" == collection of row {i} = {attr_collection}")
        #print(f" == we look for {selection}")

        if selection[0] in attr_collection and len(selection) > 1:

            indices = [idx for idx, val in enumerate(attr_collection) if val == selection[0]]
            #print(f"= = we find {selection[0]} at {indices}")

            for id in indices:
                #print(f"= = we look into {id}")
                
                j = 1
                maximum = len(selection)  # we already checked the first one
                select = True

                if len(selection)  > ( len(attr_collection) - id ):
                    #print(f"ERROR! TOO SHORT LENGTH OF {attr_collection} at {id} with {selection}")
                    select = False
                    continue

                while j < maximum: # go until all items are checked, or we find a mismatch
                    
                    if attr_collection[id + j] == selection[j]:
                        #print(f"= = = = we find value {j}, i.e. {selection[j]} of {selection} ")
                        #print(f"= = = = this is found at {id + j} of {attr_collection}, i.e. {attr_collection[id + j]}")
                        j += 1
                    
                    else:
                        #print(f"ERROR! NO MATCH")
                        select = False
                        j = maximum
                
                if select:
                    #print(f"SUCCESS! MATCH FOUND")
                    selected_records.append(rp_idx)
                    continue #no need to go over the other indices


            #print(f"ERROR! NO MATCH FOR FIRST VARIABLE")
        new_space = descriptive_space[ descriptive_space['representative_index'].isin(selected_records)]

        return new_space

def get_indices_subsequence(descriptive_space=None, condition=None):
    """
    Retrieve the indices of the records that have the sequence of categories in the condition in their data, order is relevant, but other values can come in between.
    """

    selection = condition._value
    selected_records = []

    for i in range(len(descriptive_space)):
        rp_idx = descriptive_space.iloc[i]['representative_index']
        attr_collection = descriptive_space[condition._descriptor].iloc[rp_idx]
        #print(f" == collection of row {i} = {attr_collection}")

        select = True
        min_idx = 0

        maximum = len(selection)
        j = 0
        after = attr_collection

        while j < maximum: # go until all items are checked, or we find a mismatch
                
            if selection[j] in after:
                
                idx = after.index(selection[j]) 
                #print(f" = = = = we find {j} of {selection}, i.e. {selection[j]}")
                #print(f" = = = = it is found at {idx} of {after}")
                after = after[idx + 1: ]

                #print(f" = = = = we continue with {after}")
                j += 1
                
            else:
                #print("ERROR! NO MATCH FOUND")
                select = False
                j = maximum

        if select:
            #print("SUCCESS! MATCH FOUND")
            selected_records.append(rp_idx)
        
        new_space = descriptive_space[ descriptive_space['representative_index'].isin(selected_records)]
                
    return new_space

def get_indices_text(descriptive_space=None, attribute=None, condition=None): # tbd future
    return None