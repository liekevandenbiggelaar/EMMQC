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

import synthetic.generate_synthetic_data as gsd
import synthetic.process_output as po

def main(simulation_params=None, 
         refinement_params=None,
         beam_params=None,
         model_params=None,
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
                                    simulation_params['true_description'],
                                    simulation_params['weighted'],
                                    simulation_params['apply_averaging'],
                                    simulation_params['apply_entropy'],
                                    simulation_params['focus_on_top'],
                                    simulation_params['nr_exercises'],
                                    simulation_params['max_length'],
                                    simulation_params['apply_closed_itemsets'], 
                                    simulation_params['find_itemsets'],
                                    simulation_params['include_e1']))
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
            df, cov_names, covs, cov_names_types, true_description, target_att_name, precision, recall, F1, array_with_pop_fail_rate = gsd.generate_dataset(params=params)
            #print(df.head(20))
            #print(df['e1'].value_counts())
            dataset_metrics = [precision, recall, F1, array_with_pop_fail_rate]

            # run beam search and save metrics such as runtime, quality value and whether true subgroup was in top-1 / top-10
            descriptors = cov_names
            #print(descriptors)
            descriptor_dtypes = cov_names_types
            #print(descriptor_dtypes)
            targets = [target_att_name] 
            ids = ['exerciseID', 'sessionID', 'representative_index']        
            
            refinement_params = refinement_params
            refinement_params['maximum_itemsets'] = params[13]
            refinement_params['closed_itemsets'] = params[14]

            beam_params = beam_params
            constraint_params = {'minimum_size': 0.05*len(df)}
            model_params = model_params

            model_params['weighted'] = params[8]
            model_params['apply_averaging'] = params[9]
            model_params['apply_entropy'] = params[10]

            # check if descriptor 'e' should be available or not
            if not params[16]:
                if 'e1' in descriptors:
                    descriptors.remove('e1')
                    descriptor_dtypes['nominal'].remove('e1')
            
            if params[15] == 'RebuildFPTree':
                result_set, runtime = bs.beam_search(data=df, descriptors=descriptors, descriptor_dtypes=descriptor_dtypes,targets=targets, ids=ids, refinement_params=refinement_params, beam_params=beam_params, constraint_params=constraint_params, model_params=model_params)
            elif params[15] == 'OneFPTree':
                result_set, runtime = store_bs.beam_search(data=df, descriptors=descriptors, descriptor_dtypes=descriptor_dtypes,targets=targets, ids=ids, refinement_params=refinement_params, beam_params=beam_params, constraint_params=constraint_params, model_params=model_params)
            elif params[15] == 'OneHotEncoding':
                # change item descriptors to binary attributes
                collection_attributes = descriptor_dtypes['collection']
                new_columns = []
                for var in collection_attributes:
                    vardf = pd.get_dummies(df[var].apply(pd.Series).stack(), prefix=var).groupby(level=0).sum()
                    df = pd.concat([df.reset_index(drop=True), vardf], axis=1)
                    df = df.drop(var, axis=1)
                    descriptors.remove(var)
                    new_columns = new_columns + vardf.columns.tolist()
                df.fillna(0, inplace=True)
                # change names 
                descriptors = descriptors + new_columns
                descriptor_dtypes['boolean'] = descriptor_dtypes['boolean'] + new_columns
                descriptor_dtypes['collection'] = []
                result_set, runtime = bs.beam_search(data=df, descriptors=descriptors, descriptor_dtypes=descriptor_dtypes,targets=targets, ids=ids, refinement_params=refinement_params, beam_params=beam_params, constraint_params=constraint_params, model_params=model_params)

            out = list(params) + [rep] + dataset_metrics + [runtime]
            columns=['N', 'ncovs', 'p', 'pop_fail_rate', 'precision', 
                     'nr_item_descriptors', 'nr_items', 'true_description',
                     'weighted', 'apply_averaging', 'apply_entropy',
                     'focus_on_top', 'nr_exercises', 'max_length', 'apply_closed_itemsets',
                     'find_itemsets', 'include_e1',
                     'rep', 
                     'precision', 'recall', 'F1', 'array_with_pop_fail_rate', 
                     'runtime']
            
            if params[11] == 1:
                rows = po.process_one_subgroup(result_set=result_set, sg=0, out=out, columns=columns)
            else:
                rows = po.process_multiple_subgroups(result_set=result_set, sg=0, out=out, columns=columns, focus_on_top=params[11])


            if exp == 1 and rep == 1:
                result_experiment = rows
            else:
                result_experiment = pd.concat([result_experiment, rows], ignore_index=True)
                        
    # saving
    simulation_params_copy = simulation_params.copy()
    simulation_params_copy['nreps'] = [nreps]
    #simulation_params_copy.pop('true_description', None)
    save_location = "synthetic/results/" + experiment_name + ".xlsx"
    analysis_info = pd.DataFrame(list(simulation_params_copy.values()))

    dfs = {'result_experiment':result_experiment,
           'analysis_info':analysis_info}
    
    writer = pd.ExcelWriter(save_location, engine='xlsxwriter')
    for sheet_name in dfs.keys():
        dfs[sheet_name].to_excel(writer, sheet_name=sheet_name, index=False)
    writer._save()        

if __name__ == '__main__':

    '''
    # in target space, I set finished = 0, unfinished = 1, and subgroup = 1, non-subgroup = 0
    # the precision, recall, subgroup size and pop fail rate heavily depend on each other
    # the data generating process is such that: we specify the pop fail rate + precision
    # depending on the size of the true subgroup, this means something for the recall
    # for now, we can control the size of the subgroup with the value for p 
    # because the true subgroup is based on 2 binary descriptors with probability p
    main(simulation_params={'N': [1000],
                            'ncovs': [20], # always 2 or more
                            'p': [0.3,0.5,0.7], 
                            'pop_fail_rate': [0.4,0.6,0.8],
                            'precision': [0.4,0.6,0.8],
                            'nr_item_descriptors': [0],
                            'nr_items': [0],
                            'true_description': [{'a1': 1, 'a2': 1}],
                            'weighted': [False],
                            'apply_averaging': [False],
                            'apply_entropy': [False],
                            'focus_on_top': [3],
                            'nr_exercises': [1],
                            'max_length': [0],
                            'apply_closed_itemsets': [0],
                            'find_itemsets': ['OneFPTree'],
                            'include_e1': [0]},
         refinement_params = {
             'numerical_bins': 2,
             'minimal_support_collections': 0.1, 'maximum_support_collections': 0.9},
         beam_params = {'k': 10, 'd': 3, 'w': 10},         
         model_params = {'model': 'F_beta', 'beta': 1, 'entropy level': 'exercise'},
         nreps=1,
         experiment_name="Exp1")
    '''

    # here, we create a scenario with multiple exercises
    # the subgroup size varies, as well as exercise fail rate, and we see the effect of weighting
    main(simulation_params={'N': [1000],
                            'ncovs': [4],
                            'p': [0.3,0.5,0.7], 
                            'pop_fail_rate': [None],
                            'precision': [0.8],
                            'nr_item_descriptors': [0],
                            'nr_items': [0],
                            'true_description': [{'a1': 1, 'a2': 1}], # for second half of exercises: a3 and a4
                            'weighted': [True,False],
                            'apply_averaging': [True,False],
                            'apply_entropy': [False],
                            'focus_on_top': [1],
                            'nr_exercises': [2,5,10],
                            'max_length': [0],
                            'apply_closed_itemsets': [0],
                            'find_itemsets': ['OneFPTree'],
                            'include_e1': [True,False]},
         refinement_params = {
             'numerical_bins': 2,
             'minimal_support_collections': 0.1, 'maximum_support_collections': 0.9},
         beam_params = {'k': 10, 'd': 3, 'w': 10},         
         model_params = {'model': 'F_beta', 'beta': 1, 'entropy level': 'exercise'},
         nreps=1,
         experiment_name="Exp2")

    '''
    # here, we create a true subgroup based on item descriptor 1, items a and b should be in the tuple
    # items a and b are sampled with probability p, to control subgroup size
    # the other items are sampled with varying probabilities 0.2-0.8 (prob for item the same per descriptor)
    # if item a and b have probability 0.5, this means items a,b will be halfway in the fp tree
    # it also means subgroup size is about 0.25
    main(simulation_params={'N': [1000],
                            'ncovs': [10],
                            'p': [0.5], 
                            'pop_fail_rate': [0.4],
                            'precision': [0.8],
                            'nr_item_descriptors': [2,5,10],
                            'nr_items': [2,5,10], # always 2 or more
                            'true_description': [{'it1': ('a','b')}], # for item descriptors, we can specify the true description as a tuple of items that should be present in the item descriptor
                            'weighted': [False],
                            'apply_averaging': [False],
                            'apply_entropy': [False],
                            'focus_on_top': [3],
                            'nr_exercises': [1], 
                            'max_length': [2,5,10],
                            'apply_closed_itemsets': [False, True],
                            'find_itemsets': ['OneHotEncoding', 'RebuildFPTree', 'OneFPTree'],
                            'include_e1': [0]},
         refinement_params = {
             'numerical_bins': 2,
             'minimal_support_collections': 0.1, 'maximum_support_collections': 0.9},
         beam_params = {'k': 10, 'd': 3, 'w': 10},         
         model_params = {'model': 'F_beta', 'beta': 1, 'entropy level': 'exercise'},
         nreps=10,
         experiment_name="Exp3")
    '''