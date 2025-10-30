"""
This file contains code to reduce redundancies in the discovered subgroups.
"""
import numpy as np

import priority_queue as pq
import subgroups as sub


# ====== BEFORE COPMUTING THE QUALITY ======= #
def similar_description(sg_description=None, candidates_satisfied=None):

    check_similar_description = False

    # check for redundant descriptions (the exact same description but in another order)
    # the comparison has to be done with the candidate queue of the current iteration only
    # this queue is saved in cq_satisfied
    # in theory, a refinement at the current level can be similar to a desc from an earlier level
    # this can happen for numerical and ordinal attributes
    # changes are low that those descriptions will end up in the result list together
    for candidate in candidates_satisfied:

        if sg_description == candidate._description:

            check_similar_description = True
            break

    return check_similar_description





# ====== BEFORE ADDING TO THE PRIORITY QUEUE ======= #
def remove_redundant_descriptions(queue=None, subgroup=None):
    
    redundancy_found = False #Start with nothing, only change if something if found
    best_descr, idx_descr = None, None
    
    i = 0
        
    for candidate in queue: #We have already considered them candidate = sub.Subgroup
        if subgroup._quality == candidate._quality: # we can tweak this with a weight if we want.

            best_descr = compare_two_descs(old=candidate._description, new=subgroup._description)

            if best_descr != None:
                idx_descr = i
                redundancy_found = True
                
                return redundancy_found, best_descr, idx_descr  
              
        i += 1

    return redundancy_found, best_descr, idx_descr


def compare_two_descs(old=None, new=None):

    length_dif = len(new) - len(old)
    best_descr = None
    if np.abs(length_dif) > 1:
        best_descr = None

    # new_desc is smaller than old_desc
    # check if all items exist in old_desc
    # if so, the new_desc is a general description/subset of old_desc
    elif length_dif == -1:
        items_exist_in_old_desc = [item in list(old.items()) for item in list(new.items())]
        #print('items_exist_in_old_desc', items_exist_in_old_desc)
        if np.all(items_exist_in_old_desc):
            best_descr = 'new'

    # old_desc is smaller than new_desc
    # same procedure
    elif length_dif == 1:
        items_exist_in_new_desc = [item in list(new.items()) for item in list(old.items())]
        #print('items_exist_in_new_desc', items_exist_in_new_desc)
        if np.all(items_exist_in_new_desc):
            best_descr = 'old'

    # check difference
    # if two or more keys are different, both can be kept
    # if two or more literals are different, both can be kept
    # otherwise, take the more general description
    elif length_dif == 0:
        same_keys = [key not in list(old.keys()) for key in list(new.keys())]
        #print('same_keys', same_keys)
        if np.sum(same_keys) < 2:
            same_descs = [item not in list(old.items()) for item in list(new.items())]
            #print('same_descs', same_descs)
            if np.sum(same_descs) == 1:
                # we know the difference is in the key difference, we remove the latest one
                best_descr = 'old'
            elif np.sum(same_descs) == 0:
                # remove the more general description
                # bit complex to write, for convenience we remove the latest one
                best_descr = 'old'
            else: 
                best_descr = None

    else:
        print('some mistake, new subgroup is larger than old subgroup')
        best_descr = None

    #print('remove', remove)

    return best_descr