"""
This file contains all code related to the quality measure.
"""

import numpy as np
import math

import subgroup_selection as ss
import model_class as mc

def subgroup_quality(subgroup_targets=None, params={}, population_dct={}):
    """
    This calculates the quality score of the entire subgroup (or population).

    INPUT
    * subgroup_targets  : [None] the dataframe with the target space of the records included in the subgroup.
    * params (dict)     : [{}]   a dictionary containing all model settings, including:
        * weighted (bool)       : [True] an option to remove weighting of more difficult exercises, automatically weighting is added.
        * function (str)        : [None] an option to select the wanted metric, choose from 'recall', 'precision', or 'F_beta'.
        * beta (int)            : [1] only important when function is F_beta. Automatically set to 1 for the F1 score.
    * population_dct (dict) : [{}] a dictionary with the finished and unfinished counts per exercise
    """

    # Start the loop and calculate the score for each unique exercise in the subgroup
    subgroup_dct, session_counts = finished_rates(target_space = subgroup_targets)

    # Initialize the exercise count and the total weighted quality

    metrics = { 'total_quality': 0,
                'exercise_qualities': [],
                'subgroup_quality': 0,

                'session_counts': session_counts,
                'exercise_count': 0,

                'goodness_weights': [],
                'recall': [],
                'precision': [],
                'F_beta': [],
                'beta': params['beta']}

    for eID in subgroup_dct.keys():
        pop_fail = population_dct[eID][False] #positive -> we want to capture these
        pop_pass = population_dct[eID][True]  #negative -> and leave these in the complement.

        sg_fail = subgroup_dct[eID][False] #negative  (TP)  -> we correctly captures these in the subgroup of "failed" exercises, and they actually failed.
        sg_pass = subgroup_dct[eID][True]  #positive  (FP)  -> we incorrectly captures these in the subgroup of "failed" exercises, and they actually passed.

        # initialize and fill a confusion matrix for the score computation
        confusion_matrix = {}
        confusion_matrix['TP'] = sg_fail
        confusion_matrix['FP'] = sg_pass
        confusion_matrix['TN'] = pop_pass - sg_pass # the passed exercises in the complement are the passed exercises in the population minus the ones in the subgroup
        confusion_matrix['FN'] = pop_fail - sg_fail # the failed exercises in the complement are the failed exercises in the population minus the ones in the subgroup
        
        # compute the weight based on the goodness of the exercise, worse exercises are better to capture. Only if weighted = True in the model parameters.
        if params['weighted']:
            goodness_weight = goodness_correction(population_dict=population_dct, eID=eID)

        else:
            goodness_weight = 1 #no weighting correction
        
        metrics['goodness_weights'].append(goodness_weight)
        
        # compute the quality score using the metrics
        pr = precision(confusion_matrix)
        re = recall(confusion_matrix)
        if pr == 0 or re == 0:
            fb = 0 #dividing by 0 is not possible
        else:
            fb = F_beta(confusion_matrix, beta=params['beta'])

        # store for post analysis
        metrics['recall'].append(re)
        metrics['precision'].append(pr)
        metrics['F_beta'].append(fb)

        exercise_quality = goodness_weight * metrics[params['model']][-1] # select last stored one

        # store for post analysis
        metrics['exercise_qualities'].append(exercise_quality)
        metrics['exercise_count'] += 1

        metrics['total_quality'] += exercise_quality # the higher the better

    metrics['subgroup_quality'] = (1 / metrics['exercise_count']) * metrics['total_quality']
    
    return metrics



def finished_rates(target_space=None):
    """
    Create a dictionary with all exercises as the keys. 
    Each key gets a new dictionary in the form of {"fail": x, "pass": y, "total": x + y}.
    Return this dictionary.
    """

    # Group the data on unique exercise and session pairs. 
    # As the "finished" parameter is recorded on the highest level (session), we can just take the last, first, anyone of them.
    target_grouped = target_space.copy()
    target_grouped = target_grouped.groupby(['exerciseID', 'sessionID']).last()

    # Get all unique exercises and get the finished counts for them
    exerciseIDs = list(target_grouped.index.levels[0].unique())
    finished_dct = {}
    sessions_count = []

    for ex in exerciseIDs:
        ex_dct = target_grouped.loc[ex]['finished'].value_counts().reindex([False, True], fill_value=0).to_dict()
        finished_dct[ex] = ex_dct
        nr_sessions = len(list(target_grouped.loc[ex].index.unique()))
        sessions_count.append(nr_sessions)

    return finished_dct, sessions_count

def goodness_correction(population_dict={}, eID=''):
    """
    Give extra weight to worse exercises to enforce capturing them.
    Basic: fail / total.

    INPUT
    * population_dict (dict): [{}] contains the count of passed and failed exercises for each exercise in the entire population
    * eID (str)             : [''] a string of the concerning exercise ID
    """

    failed = population_dict[eID][False]
    total = population_dict[eID][False] + population_dict[eID][True]

    return failed / total


def precision(confusion_matrix=None):
    """
    Measure how "correct" your model is. It wants to minimize the number of false positives.
    TP / (TP + FP)
    """

    TP = confusion_matrix['TP']
    FP = confusion_matrix['FP']

    return TP / (TP + FP)

def recall(confusion_matrix=None):
    """
    Measure if you have captured all positives. It minimized the number of false negatives.
    TP / (TP + FN)
    """

    TP = confusion_matrix['TP']
    FN = confusion_matrix['FN']

    return TP / (TP + FN)

def F_beta(confusion_matrix=None, beta=1):
    """
    Measures a trade-off between precision and recall.
    F_beta = (1 + beta^2) * (Precision * Recall)/(beta^2*Precision + Recall)
    beta = 1 gives the F1 score and precision and recall are equally important.
    beta > 1 means more weight to recall -> False Negatives (Unfinished exercises in Complement) are costly
    beta < 1 means more weight to precision -> False Positives (Finished exercises in Subgroup) are costly
    """

    return ( 1 + beta**2 ) * ( ( precision(confusion_matrix) * recall(confusion_matrix) ) / ( beta**2 * precision(confusion_matrix) + recall(confusion_matrix) ) )






# = = = = = = = DEPRECATED = = = = = = = #
def DEPR_entropy_function(subgroup_size=None, population_size=None):
    complement_size = population_size - subgroup_size
    
    # no subgroup so invaluable
    if subgroup_size == 0 or complement_size == 0:
        return 0
    
    prob_subgroup = subgroup_size / population_size
    prob_complement = complement_size / population_size
    
    entropy = -prob_subgroup * math.log(prob_subgroup) + prob_complement * math.log(prob_complement)
    
    return entropy


def DEPR_model_function(target_space=None, model=None):

    if model == 'finish_rate':
        quality, values = mc.finish_rate(target_space) 

    elif model == 'exercise_finish_rate':
        quality, values = mc.exercise_finish_rate(target_space) 

    elif model == 'average_marks_ratio':
        quality, values = mc.average_marks_ratio(target_space)
    
    else:
        return "== ERROR: Invalid Model Class"

    return quality, values


def DEPR_compute_quality_measure(subgroup_indices=None, target_space=None, model=None, population_quality=None, population_size=None):
    """
    Model options: finish_rate, average_marks_rate
    """

    # Get needed values
    subgroup_size = len(subgroup_indices)
    subgroup_target_space = ss.get_subgroup_target_space(target_space, subgroup_indices)

    # Calculate both components
    entropy = DEPR_entropy_function(subgroup_size, population_size)
    subgroup_quality, values = DEPR_model_function(subgroup_target_space, model)


    # Total quality
    model_quality = population_quality - subgroup_quality #*entropy

    return model_quality, values




