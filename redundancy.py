"""
This file contains code to reduce redundancies in the discovered subgroups.
"""

import priority_queue as pq


def similarity_redundancy(description=None, list_of_descriptions=None):
    """ 
    This means that the description {A=2, B=3} and {B=3, A=2} cannot both be included because they are the same.
    Check if the description in any form is already in the priority queue. Returns True if redundant or False
    """

    return description in list_of_descriptions

def generalization_redundancy():
    return False

def sufficient_subgroup_size():
    return None

def remove_candidate():
    return None
