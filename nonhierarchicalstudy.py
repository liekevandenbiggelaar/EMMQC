import pandas as pd
import numpy as np

import eqc.search_storing_non as store_bs_non
import eqc.preprocessing as pp


#open data
print(f"Start with data cleaning")
df = pd.read_csv("data/digitallearningmath.csv")


# experimental setup
DESCRIPTORS = [ 'interactionType', 'primarySubject', 'secondarySubject', 'stepTypes', 
                    'skills', 'positive_skills', 'negative_skills', 'event_evaluations', 
                    'context_hint', 'hintsRequested_cat', 'try_count']

TARGETS = ['finished'] # all to do with performance

IDS = ['exerciseID', 'sessionID', 'questionID', 'interactionID', 'representative_index', 'studentName']

REFINEMENT_PARAMS = {
                        'numerical_bins': 5,
                        'minimal_support_collections': 0.05, 'maximum_support_collections': 0.95, 
                        'maximum_itemsets': None, 'closed_itemsets': True
                        }

BEAM_PARAMS = {'k': 50, 'd': 3, 'w': 25, 'dtypes': {'nominal': ['interactionType', 'primarySubject', 'secondarySubject', "hintsRequested_cat", 'try_count'], 
                                                    'boolean': ['context_hint'], 
                                                    'numerical': [], 
                                                    'ordinal': [], 
                                                    'collection': ['skills', 'positive_skills', 'negative_skills', 'event_evaluations', 'stepTypes']}} 

CONSTRAINT_PARAMS = {'minimum_size': 25, 'improvement_rate': 0.1}

MODEL_PARAMS = {'model': 'F_beta', 'beta': 1, 'weighted': False, 'inner entropy levels': [], 'outer entropy levels': [],
                    'subgroup_level': 'session', 'target_level': 'interaction', 'apply_averaging': True, 'apply_entropy': True}

descriptor_dtypes = BEAM_PARAMS['dtypes']
collection_attributes = descriptor_dtypes['collection']
new_columns = []
df_one = df.copy()

for var in collection_attributes:
    vardf = pd.get_dummies(df_one[var].apply(pd.Series).stack(), prefix=var).groupby(level=0).sum()
    df_one = pd.concat([df_one.reset_index(drop=True), vardf], axis=1)
    df_one = df_one.drop(var, axis=1)
    DESCRIPTORS.remove(var)
    new_columns = new_columns + vardf.columns.tolist()
df_one.fillna(0, inplace=True)

df_clean = pp.clean_data_algebrakit(unfilterd_data=df_one, filter_type="remove_interaction")

# change names 
DESCRIPTORS = DESCRIPTORS + new_columns
descriptor_dtypes['boolean'] = descriptor_dtypes['boolean'] + new_columns
descriptor_dtypes['collection'] = []
BEAM_PARAMS['dtypes'] = descriptor_dtypes

# execute beam search
result_set_st, _ = store_bs_non.beam_search(data=df_clean, descriptors=DESCRIPTORS, targets=TARGETS, ids=IDS, 
                                refinement_params=REFINEMENT_PARAMS, beam_params=BEAM_PARAMS,
                                constraint_params=CONSTRAINT_PARAMS, model_params=MODEL_PARAMS)
    
df = pd.DataFrame()

df['rank'] = [i._rank for i in result_set_st._queue ]
df['description'] = [i._description for i in result_set_st._queue]
df['n'] = [i._metrics['total_records'] for i in result_set_st._queue]
df['n_exercises'] = [i._metrics['total_exercises'] for i in result_set_st._queue]
df['n_sessions'] = [i._metrics['total_sessions'] for i in result_set_st._queue]
df['indices'] = [i._indices for i in result_set_st._queue]

df.to_csv("results_nonhierarchical.csv")
