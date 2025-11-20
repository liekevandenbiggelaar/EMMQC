"""
This file contains code to reduce redundancies in the discovered subgroups.
"""
import numpy as np

import priority_queue as pq
import subgroups as sub


# ====== BEFORE COPMUTING THE QUALITY ======= #
def similar_description(sg_description=None, candidates_satisfied=None):

    for candidate in candidates_satisfied:
        candidate_same = True

        old_description = candidate._description
        old_descriptors = old_description._descriptors
        new_descriptors = sg_description._descriptors

        if new_descriptors != old_descriptors:
            candidate_same = False
        
        else: # descriptors are the same

            for cond in sg_description._conditions:
                attr = cond._descriptor
                value = cond._value

                old_value = old_description.get_condition(attr)

                if value == old_value:
                    candidate_same *= True
                    candidate_same = bool(candidate_same)

                else:
                    candidate_same *= False
                    candidate_same = bool(candidate_same)
                    break #it is different, so we can move onto a different candidate
        
        if candidate_same == True:
            return True

    return False





# ====== BEFORE ADDING TO THE PRIORITY QUEUE ======= #
def remove_redundant_descriptions(queue=None, subgroup=None):
    
    redundancy_found = False #Start with nothing, only change if something if found
    best_descr, idx_descr = None, None
    
    i = 0
        
    for candidate in queue: #We have already considered them candidate = sub.Subgroup
        if subgroup._quality == candidate._quality: # we can tweak this with a weight if we want.

            best_descr = compare_two_descs(old_description=candidate._description, new_description=subgroup._description)

            if best_descr != None:
                idx_descr = i
                redundancy_found = True
                
                return redundancy_found, best_descr, idx_descr  
              
        i += 1

    return redundancy_found, best_descr, idx_descr


def compare_two_descs(old_description=None, new_description=None):

    length_dif = len(new_description._conditions) - len(old_description._conditions)

    best_descr = None

    if np.abs(length_dif) > 1:
        best_descr = None

    # new_desc is smaller than old_desc
    # check if all items exist in old_desc
    # if so, the new_desc is a general description/subset of old_desc
    elif length_dif == -1:

        old_items = [(cond._descriptor, cond._value) for cond in old_description._conditions]
        new_items = [(cond._descriptor, cond._value) for cond in new_description._conditions]
        same_descs = [item not in old_items for item in new_items]    

        items_exist_in_old_desc = [item in old_items for item in new_items]
        if np.all(items_exist_in_old_desc):
            best_descr = 'new'    

        # items_exist_in_old_desc = []
        # new_conditions = new_description._condition
        # old_conditions = old_description._condition

        # for new_cond in new_conditions:

        #     condition_in_old = []
        #     for old_cond in old_conditions:
        #         if new_cond._descriptor == old_cond._descriptor and new_cond._value == old_cond._value:
        #             condition_in_old.append(True)
        #         else:
        #             condition_in_old.append(False)
            
        #     items_exist_in_old_desc.append(np.any(condition_in_old))

        # if np.all(items_exist_in_old_desc):
        #     best_descr = 'new'

    # old_desc is smaller than new_desc
    # same procedure
    elif length_dif == 1:

        old_items = [(cond._descriptor, cond._value) for cond in old_description._conditions]
        new_items = [(cond._descriptor, cond._value) for cond in new_description._conditions]
        same_descs = [item not in new_items for item in old_items]    

        items_exist_in_new_desc = [item in new_items for item in old_items]
        if np.all(items_exist_in_new_desc):
            best_descr = 'old'    

        # items_exist_in_new_desc = []
        # new_conditions = new_description._condition
        # old_conditions = old_description._condition

        # for old_cond in old_conditions:

        #     condition_in_new = []
        #     for new_cond in new_conditions:
        #         if old_cond._descriptor == new_cond._descriptor and old_cond._value == new_cond._value:
        #             condition_in_new.append(True)
        #         else:
        #             condition_in_new.append(False)
            
        #     items_exist_in_new_desc.append(np.any(condition_in_new))

        # if np.all(items_exist_in_new_desc):
        #     best_descr = 'old'

    # check difference
    # if two or more keys are different, both can be kept
    # if two or more literals are different, both can be kept
    # otherwise, take the more general description
    elif length_dif == 0:
        same_keys = [key not in old_description._descriptors for key in new_description._descriptors]
        #print('same_keys', same_keys)
        if np.sum(same_keys) < 2:
            old_items = [(cond._descriptor, cond._value) for cond in old_description._conditions]
            new_items = [(cond._descriptor, cond._value) for cond in new_description._conditions]
            same_descs = [item not in old_items for item in new_items]

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
        print(length_dif)
        print(new_description._conditions, old_description._conditions)
        best_descr = None

    #print('remove', remove)

    return best_descr