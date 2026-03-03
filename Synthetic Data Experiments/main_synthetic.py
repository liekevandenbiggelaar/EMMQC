import numpy as np
import pandas as pd
import itertools as it

# in console: pip install xlsxwriter

import preprocessing as pp
import candidates as ca
import refinements as rf
import subgroup_selection as ss
import search as bs
import search_storing as store_bs
import dfd as dfd
import fpgrowth as fp

import generate_synthetic_data as gsd

def main(simulation_params=None, 
         nreps=None,    
         experiment_name=None):

    # create list of all simulation conditions
    parameter_set = list(it.product(simulation_params['N'],
                                    simulation_params['ncovs'], 
                                    simulation_params['p'],
                                    simulation_params['pop_fail_rate'],
                                    simulation_params['precision'],
                                    simulation_params['nr_item_descriptors'],
                                    simulation_params['nr_items'],
                                    simulation_params['true_description']))
    nexp = len(parameter_set)

    for exp in np.arange(1,nexp+1):   
        print('experiment', exp, 'of', nexp)
        params = parameter_set[exp-1]
        print('parameters:', params)

        # here you could do a parallelization over the nreps using joblib
        # for now I just do a for loop
        for rep in np.arange(1,nreps+1):
            print('rep', rep, 'of', nreps)
                 
            # generate dataset
            df, cov_names, covs, true_description, target_att_name, precision, recall, F1 = gsd.generate_dataset(params=params)
            print(df.head(20))
            dataset_metrics = [precision, recall, F1]

            # run beam search and save metrics such as runtime, quality value and whether true subgroup was in top-1 / top-10
            descriptors = cov_names
            print(descriptors)
            targets = [target_att_name] 
            ids = ['sID']        
            refinement_params = {
                     'numerical_bins': 2,
                     'minimal_support_collections': 0.1, 'maximum_support_collections': 0.9, 
                     'maximum_itemsets': 20, 'closed_itemsets': True
                     }
            beam_params = {'k': 25, 'd': 3, 'w': 20}
            constraint_params = {'minimum_size': 25}
            model_params = {'model': 'F_beta', 'beta': 1, 'weighted': True, 'entropy level': 'exercise'}    
            result_set = store_bs.beam_search(data=df, descriptors=descriptors, targets=targets, ids=ids, refinement_params=refinement_params, beam_params=beam_params, constraint_params=constraint_params, model_params=model_params)

            print(len(result_set._queue))

            results_params = [0,0,0]

            # make one long excel file with results for all parameter combinations
            out = list(params) + [rep] + dataset_metrics + results_params
            columns=['N', 'ncovs', 'p', 'pop_fail_rate', 'precision', 
                     'nr_item_descriptors', 'nr_items', 'true_description', 
                     'rep', 
                     'precision', 'recall', 'F1', 
                     'metric1', 'metric2', 'metric3']
            
            # from list to pd dataframe with column names
            if exp == 1 and rep == 1:
                result_experiment = pd.DataFrame([out], 
                                                 columns=columns)
            else:                
                result_experiment = pd.concat([result_experiment, pd.DataFrame([out], columns=columns)], ignore_index=True)

    # saving
    simulation_params_copy = simulation_params.copy()
    simulation_params_copy.pop('true_description', None)
    save_location = "Results/" + experiment_name + str(list(simulation_params_copy.values())) + ".xlsx"
    analysis_info = pd.DataFrame({'nreps':nreps}, index=[0])

    dfs = {'result_experiment':result_experiment,
           'analysis_info':analysis_info}
    
    writer = pd.ExcelWriter(save_location, engine='xlsxwriter')
    for sheet_name in dfs.keys():
        dfs[sheet_name].to_excel(writer, sheet_name=sheet_name, index=False)
    writer._save()        

if __name__ == '__main__':

    # in target space, I set finished = 0, unfinished = 1, and subgroup = 1, non-subgroup = 0
    # the precision, recall, subgroup size and pop fail rate heavily depend on each other
    # the data generating process is such that: we specify the pop fail rate + precision
    # depending on the size of the true subgroup, this means something for the recall
    # for now, we can control the size of the subgroup with the value for p 
    # because the true subgroup is based on 2 binary descriptors with probability p
    
    main(simulation_params={'N': [1000],
                            'ncovs': [5], # always 2 or more
                            'p': [0.5], # for too small p, subgroup may not exist for small N
                            'pop_fail_rate': [0.8],
                            'precision': [1],
                            'nr_item_descriptors': [0],
                            'nr_items': [0],
                            'true_description': [{'a1': 1, 'a2': 1}]},
         nreps=2,
         experiment_name="Exp1")

    '''
    # here, we create a true subgroup based on item descriptor 1, items a and b should be in the tuple
    # items a and b are sampled with probability p, to control subgroup size
    # the other items are sampled with varying probabilities 0.2-0.8 (prob for item the same per descriptor)
    # if item a and b have probability 0.5, this means items a,b will be halfway in the fp tree
    # it also means subgroup size is about 0.25

    main(simulation_params={'N': [100],
                            'ncovs': [5],
                            'p': [0.5], 
                            'pop_fail_rate': [0.8],
                            'precision': [0.6],
                            'nr_item_descriptors': [2,6],
                            'nr_items': [4,20], # always 2 or more
                            'true_description': [{'it1': ('a','b')}] # for item descriptors, we can specify the true description as a tuple of items that should be present in the item descriptor
                            },
         nreps=2,
         experiment_name="exp_with_item_descriptors")
    '''
    '''
    # here, we create a scenario with 2 exercises and 2 true subgroup descriptions
    # the dataset thus contains of 4 confusion matrices
    # I just code this directly; variables pop_fail_rate and true_description are not needed
    # the other variables can still be varied
    main(simulation_params={'N': [1000],
                            'ncovs': [10],
                            'p': [0.5], 
                            'pop_fail_rate': [None], # will hardcode 2 exercises with 0.4 and 0.6
                            'precision': [0.6], # same precision applied for every subgroup in every exercise, ideally compare different scenarios
                            'nr_item_descriptors': [2],
                            'nr_items': [5],
                            'true_description': [None]}, # one true description is a1:1, a2:1, the other true description is a1:0,a2:0,a3:1 (coded such that this subgroup is 1/8, the other 1/4 in size)
         nreps=1,
         experiment_name="exp_with_2_subgroups")
    '''