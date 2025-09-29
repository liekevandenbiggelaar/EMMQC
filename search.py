"""
This file has the beam search strategy.
"""

import candidates as ca
import priority_queue as pq
import subgroup_selection as ss
import subgroups as sub


def beam_search(data=None, descriptors=None, targets=None, ids=None, numerical_bins=None, collection_limit=None, k=None, d=None, w=None):
    """
    k : top-k subgroups extracted.
    d : maximum depth of the beam.
    w : maximum width of a level in the beam.
    """

    # Split the data
    descriptive_space, target_space, attributes, descriptor_types = ca.split_spaces(data=data, 
                                                                                    descriptors=descriptors, 
                                                                                    targets=targets, 
                                                                                    ids=ids)

    # Get the starting candidates
    candidates_per_attribute, starting_candidates  = ca.get_candidates_per_attribute(descriptive_space=descriptive_space, 
                                                                                     dtypes=descriptor_types, 
                                                                                     numerical_bins=numerical_bins, 
                                                                                     collection_limit=collection_limit)

    # Get quality measure of entire population


    # Set initial priority queue for the end result
    result_set = pq.PriorityQueue(queue=[], max_length=k)

    # Start with the starting candidates, but keep those for further refinements.
    candidate_queue = starting_candidates 

    # Go over each level of the beam
    for level in range(1, d+1):

        beam = pq.PriorityQueue(queue=[], max_length=w)

        for description in candidate_queue:
            return None


    return None