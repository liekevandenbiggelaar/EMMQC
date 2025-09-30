"""
This file contains all code related to the model class and fitting thereof.
"""

import numpy as np

def finish_rate(target_space=None):

    all_sessions = len(target_space)
    data_finished_sessions = target_space[target_space['finished'] == True]
    count_finished = len(data_finished_sessions)

    model_quality = count_finished / all_sessions

    return model_quality


def average_marks_ratio(target_space=None):

    marks_ratio = np.array(target_space['marksEarned']) / np.array(target_space['marksTotal'])
    model_quality = np.mean(marks_ratio)

    return model_quality



