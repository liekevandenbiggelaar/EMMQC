"""
This file contains all code related to the model class and fitting thereof.
"""

import numpy as np

def exercise_finish_rate(target_space=None):
    """
    Measure the successful finish rate of the exercises covered by the description, based on the unique sessions that are in the subgroup.
    """
    successrates = []
    for ex in list(target_space['exerciseID'].unique()):
        only_ex = target_space[ target_space['exerciseID'] == ex ]
        total = len(list(only_ex['sessionID'].unique()))

        finished = only_ex[ only_ex['finished'] == True ]

        partial = len(list(finished['sessionID'].unique()))
        rate = round(partial / total * 100, 2)
        successrates.append(rate)
    
    model_quality = np.mean(np.array(successrates))

    return model_quality, successrates

def finish_rate(target_space=None):

    all_sessions = len(target_space)
    data_finished_sessions = target_space[target_space['finished'] == True]
    count_finished = len(data_finished_sessions)

    model_quality = count_finished / all_sessions

    return model_quality, []


def average_marks_ratio(target_space=None):

    marks_ratio = np.array(target_space['marksEarned']) / np.array(target_space['marksTotal'])
    model_quality = np.mean(marks_ratio)

    return model_quality, []



