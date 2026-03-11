import pandas as pd
import numpy as np

import eqc.search_storing as store_bs
import eqc.preprocessing as pp


#open data
print(f"Start with data cleaning")
df = pd.read_csv("data/digitallearningmath.csv")
df_clean = pp.clean_data_algebrakit(unfilterd_data=df, filter_type="remove_interaction")

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

BEAM_PARAMS = {'k': 50, 'd': 3, 'w': 25, 'dtypes': None} 

CONSTRAINT_PARAMS = {'minimum_size': 25, 'improvement_rate': 0.1}

MODEL_PARAMS = {'model': 'F_beta', 'beta': 1, 'weighted': True, 'inner entropy levels': ['session'], 'outer entropy levels': ['interaction'],
                    'subgroup_level': 'session', 'target_level': 'interaction', 'apply_averaging': True, 'apply_entropy': True}


# execute beam search
result_set_st, _ = store_bs.beam_search(data=df_clean, descriptors=DESCRIPTORS, targets=TARGETS, ids=IDS, 
                                refinement_params=REFINEMENT_PARAMS, beam_params=BEAM_PARAMS,
                                constraint_params=CONSTRAINT_PARAMS, model_params=MODEL_PARAMS)
    
examined = 0
for sub in result_set_st._queue:
    examined += 1

    fail_rate_ex = round(np.mean(sub._metrics['goodness_weights']), 2)
    fail_rate_sg = round(np.mean(sub._metrics['fail rates']), 2)
    rel_impr = round( (fail_rate_sg - fail_rate_ex) / fail_rate_ex, 2)

    if rel_impr >= 0.75:
        print(f"#{examined}: {sub}")
        print(f" avg. recall = {np.mean(sub._metrics['recall'])}")
        print(f" avg. precision = {np.mean(sub._metrics['precision'])}")
        print(f" avg. F_beta = {round(np.mean(sub._metrics['F_beta']), 2)}")
        print(f" avg. goodness_weights = {round(np.mean(sub._metrics['goodness_weights']), 2)}")
        print(f" avg. fail rate = {round(np.mean(sub._metrics['fail rates']), 2)}")
        print(f" Relative improvement = {rel_impr}")
        print(f" sessions = {min(sub._metrics['session_counts']), max(sub._metrics['session_counts'])}")

        print(f" exercises = {sub._metrics['exercise_count']}")
        print(f" exercises = {sub._metrics['exercises']}")

        print(5 * "=========")
