import numpy as np
import random
import pandas as pd
from joblib import Parallel, delayed

import search_storing as bs_store



def get_distribution_params(dataset=None, descriptors=None, targets=None, ids=None, 
                            refinement_params=None, beam_params=None,
                            constraint_params=None, model_params=None, m=0):
    
    best_m_qms = get_m_false_discoveries(dataset=dataset, descriptors=descriptors, targets=targets, ids=ids, 
                            refinement_params=refinement_params, beam_params=beam_params,
                            constraint_params=constraint_params, model_params=model_params, m=m)
    
    # Get distribution params
    mu = np.mean(best_m_qms)
    std = np.std(best_m_qms)
    
    # Get p-values
    p90 = mu + 1.645 * std
    p95 = mu +  1.96 * std
    p99 = mu +  2.58 * std
    
    dfd_params = {'m': m, 
                  'qms': best_m_qms, 'mu': mu, 'std': std, 
                  'p90': p90, 'p95': p95, 'p99': p99}

    return dfd_params
    

def get_m_false_discoveries(dataset=None, descriptors=None, targets=None, ids=None, 
                            refinement_params=None, beam_params=None,
                            constraint_params=None, model_params=None, m=0):
    
    # Perform process in parallel to increase time efficiency
    best_m_qms = Parallel(n_jobs=3)(delayed(get_false_discovery)(dataset=dataset, descriptors=descriptors, targets=targets, ids=ids, 
                            refinement_params=refinement_params, beam_params=beam_params,
                            constraint_params=constraint_params, model_params=model_params) for i in range(m))
    
    return best_m_qms


#########################
# This should be altered to shuffle your descriptors.



def shuffle_descriptors(dataset=None, descriptors=None, targets=None, indexes=None):
    
    # Isolate the PID from the descriptors
    randomized_dataset = dataset.copy()

    df_descriptors = randomized_dataset[descriptors]
    df_targets_index = randomized_dataset[indexes + targets]
    
    # Shuffle the rows of the descriptors
    shuffled_descriptors = df_descriptors.sample(frac = 1, random_state=1).reset_index()
    shuffled_descriptors = shuffled_descriptors.drop('index', axis=1)
    
    # Combine the original PID with  the now shuffled descriptors
    df_shuffled = pd.concat([df_targets_index, shuffled_descriptors], axis=1)
    
    return df_shuffled


def get_false_discovery(dataset=None, descriptors=None, targets=None, ids=None, 
                            refinement_params=None, beam_params=None,
                            constraint_params=None, model_params=None):
    
    # Shuffle the descriptors to remove any correlation between the descriptors and targets
    df_shuffled = shuffle_descriptors(dataset=dataset, descriptors=descriptors, targets=targets, indexes=ids)
    
    # Perform beam search on the shuffled dataset
    result_set = bs_store.beam_search(data=df_shuffled, descriptors=descriptors, targets=targets, ids=ids, 
                            refinement_params=refinement_params, beam_params=beam_params,
                            constraint_params=constraint_params, model_params=model_params)
    
    best_qm = result_set._queue[0]._metrics['subgroup_quality']# Get the QM of the top-1 subgroup
    
    return best_qm