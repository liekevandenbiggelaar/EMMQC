import numpy as np
import pandas as pd

def process_one_subgroup(result_set=None, sg=None, out=None, columns=None):

    #print(len(result_set._queue))
    #i = 1
    #for sub in result_set._queue:
        #print(sub)
        #print(type(sub))
        #print(f"#{i}: {sub.print_description()}: {sub.print_metrics()['subgroup_quality']}")
        #i += 1

    top1 = result_set._queue[sg]
    top1_description = top1.print_description()
    top1_metrics = top1.print_metrics()
    #print(top1_metrics)
    results_params = [sg+1, top1_description, np.round(top1_metrics['subgroup_quality'],2),
                      np.round(top1_metrics['precision'],2),np.round(top1_metrics['recall'],2),np.round(top1_metrics['F_beta'],2),
                      np.round(top1_metrics['goodness_weights'],2), 
                      np.round(top1_metrics['exercise_count'],2), np.round(top1_metrics['session_count'],2)]
    
    results_columns = ['subgroup', 'desc', 'quality', 'found_precision', 'found_recall', 'found_fscore', 
                       'goodness_weights', 'exercise_count', 'session_count']

    # from list to pd dataframe with column names
    result_row = pd.DataFrame([out+results_params], columns=columns+results_columns)

    #result_experiment = pd.concat([result_experiment, pd.DataFrame([out], columns=columns)], ignore_index=True)

    return result_row

def process_multiple_subgroups(result_set=None, sg=None, out=None, columns=None, focus_on_top=None):
                
    # focus on top-5 subgroups
    # make new result row for every subgroup

    #print(len(result_set._queue))
    rows = []
    for i in np.arange(1,focus_on_top+1):
        one_row = process_one_subgroup(result_set=result_set, sg=i-1, out=out, columns=columns)
        rows.append(one_row)
                 
    result_rows = pd.concat(rows)

    return result_rows