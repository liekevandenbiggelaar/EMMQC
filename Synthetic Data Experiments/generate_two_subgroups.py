import numpy as np
import pandas as pd
import random as r

import generate_synthetic_data as gsd

def two_exercises_with_2_subgroups(params=None):
        
    # change value in tuple
    params = list(params)
    params[3] = 0.4 # pop_fail_rate
    params[7] = {'a1': 1, 'a2': 1} # true description 1
    params = tuple(params)

    dataset1_temp, cov_names, covs, true_description, target_att_name = \
            gsd.dataset_for_one_exercise(params=params)
        
    # then create second subgroup
    # we keep the same descriptors, except we replace descriptor 3
    # calculate number where a1:0 and a2:0, this is complement of subgroup 1
    dataset1_temp['a' + str(3)] = 0
    mask0 = gsd.determine_mask(df=dataset1_temp, true_description={'a1': 0, 'a2': 0})
    
    # replace a3 with 1/0 only where mask == 1 (where a1 = 0 and a2 = 0)
    # the subgroup size is thus p*(1-p*p) = 0.125 when p = 0.5 
    dataset1_temp.loc[mask0 == 1, 'a' + str(3)] = np.random.binomial(n=1, p=params[2], size=np.sum(mask0))
    true_description={'a3': 1}
    mask1 = gsd.determine_mask(df=dataset1_temp, true_description=true_description)        
    dataset1_fixed = gsd.generate_one_true_subgroup(dataset=dataset1_temp, params=params, mask=mask1, target_att_name=target_att_name)
    
    # add indicator column
    dataset1_fixed['eID'] = 1
        
    # make second dataset with pop fail rate = 0.6
    params = list(params)
    params[3] = 0.6
    params[7] = {'a1': 1, 'a2': 1}
    params = tuple(params)
    dataset2_temp, cov_names2, covs2, true_description2, target_att_name2 = \
            gsd.dataset_for_one_exercise(params=params)
        
    # then create second subgroup
    dataset2_temp['a' + str(3)] = 0
    mask0 = gsd.determine_mask(df=dataset2_temp, true_description={'a1': 0, 'a2': 0})
    dataset2_temp.loc[mask0 == 1, 'a' + str(3)] = np.random.binomial(n=1, p=params[2], size=np.sum(mask0))
    true_description={'a3': 1}
    mask1 = gsd.determine_mask(df=dataset2_temp, true_description=true_description)        
    dataset2_fixed = gsd.generate_one_true_subgroup(dataset=dataset2_temp, params=params, mask=mask1, target_att_name=target_att_name)
    
    dataset2_fixed['eID'] = 2
        
    dataset = pd.concat([dataset1_fixed, dataset2_fixed], ignore_index=True)

    print(dataset.groupby(['eID'])[target_att_name].value_counts())
    print(dataset.groupby(['eID', 'a1', 'a2'])[target_att_name].value_counts())    
    print(dataset.groupby(['eID', 'a1', 'a2', 'a3'])[target_att_name].value_counts())

    return dataset, cov_names, covs, {'a1':1, 'a2':1}, target_att_name