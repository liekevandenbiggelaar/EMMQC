import numpy as np
import pandas as pd
import random as r
import string

import synthetic.generate_synthetic_data as gsd

def multiple_exercises(params=None):

    nr_exercises = params[12]  
    array_with_pop_fail_rate = np.linspace(0.2, 0.8, num=nr_exercises)

    for i in np.arange(1,nr_exercises+1):

        params_temp = list(params).copy()
        params_temp[0] = int(np.round(params_temp[0] / nr_exercises))
        params_temp[3] = array_with_pop_fail_rate[i-1]
        params_temp = tuple(params_temp)   
        #print(params_temp) 

        dataset, cov_names, covs, cov_names_types, true_description, target_att_name = gsd.dataset_for_one_exercise(params=params_temp)

        dataset['exerciseID'] = i
        dataset['e1'] = string.ascii_lowercase[i-1]

        if i == 1:            
            final_dataset = dataset.copy() 
        else:
            final_dataset = pd.concat([final_dataset, dataset.copy()], ignore_index=True)
    
    cov_names = cov_names + ['e1']
    cov_names_types['nominal'] = ['e1']
    #print(cov_names)
    #print(cov_names_types)
    
    return final_dataset, cov_names, covs, cov_names_types, true_description, target_att_name, array_with_pop_fail_rate