"""
This file has the beam search strategy.
"""

import candidates as ca
import priority_queue as pq
import subgroup_selection as ss
import subgroups as sub
import quality_measure as qm


def beam_search(data=None, descriptors=None, targets=None, ids=None, numerical_bins=None, collection_limit=None, k=None, max_depth=None, beam_width=None, model=None, minimum_size=None):
    """
    k : top-k subgroups extracted.
    d : maximum depth of the beam.
    w : maximum width of a level in the beam.
    model : [finish_rate, average_marks_ratio]
    """

    # 1. Get the data ready -> Preprocessing and Split
    # 2. Get the starting candidate descriptions and candidate queue
    # 3. Get the population quality
    # 4. Initialize the result set
    # 5. For each level in until the maximum depth is reached, do:
    # 6.    Initialize the beam queue
    # 7.    For each description in the candidate queue, do:
    # 8.        Get the subgroup: indices, quality -> store as Subgroup Class
    # 9.        Check the validity and redundancy of the subgroup. -> Now only size matter.
    # 10.        Insert the subgroup in the beam queue and into the result set.
    # 11.   Get the new candidate queue, by refining all descriptions in the beam queue
    # 12. Return the result queue


    # 1. Get the data ready -> Preprocessing and Split
    descriptive_space, target_space, attributes, descriptor_types = ca.split_spaces(data=data, descriptors=descriptors, targets=targets, ids=ids)

    # 2. Get the starting candidate descriptions
    candidates_per_attribute, starting_candidates  = ca.get_candidates_per_attribute(descriptive_space=descriptive_space,  dtypes=descriptor_types, 
                                                                                     numerical_bins=numerical_bins, collection_limit=collection_limit)
    candidate_queue = starting_candidates 

    # 3. Get the population quality
    population_quality = qm.model_function(target_space=target_space, model=model)
    population_size = len(target_space)

    # 4. Initialize the result set and the candidate queue
    result_set = pq.PriorityQueue(queue = [], max_length = k)

    # 5. For each level in until the maximum depth is reached, do:
    for level in range(1, max_depth + 1):
        print(f"start on level {level}")

    # 6.    Initialize the beam queue
        beam_queue = pq.PriorityQueue(queue = [], max_length = beam_width)

    # 7.    For each description in the candidate queue, do:
        for description in candidate_queue:

    # 8.        Get the subgroup: indices, quality -> store as Subgroup Class if conditions hold
            indices, subgroup_descriptors = ss.check_record_inclusion(descriptive_space=descriptive_space, dtypes=descriptor_types, candidate=description)
            if len(indices) > minimum_size:
                quality = qm.compute_quality_measure(subgroup_indices=indices, target_space=target_space, model=model, population_quality=population_quality, population_size=population_size)
                selected_subgroup = sub.Subgroup(model=model, description=description, indices=indices, quality=quality)

    # 9.        Insert the subgroup in the beam queue and into the result set.
            beam_queue.insert_subgroup(selected_subgroup)
            result_set.insert_subgroup(selected_subgroup)

    # 10.   Get the new candidate queue, by refining all descriptions in the beam queue
        candidate_queue = []
        for subgroup_description in beam_queue.get_descriptions():
            new_conditions = ca.add_condition(description=subgroup_description, starting_candidates=starting_candidates)
            candidate_queue += new_conditions
        
    # 11. Return the result queue
    return result_set