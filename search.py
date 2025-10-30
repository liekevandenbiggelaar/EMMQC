"""
This file has the beam search strategy.
"""

import candidates as ca
import priority_queue as pq
import subgroup_selection as ss
import subgroups as sub
import quality_measure as qm
import redundancy as rd


def beam_search(data=None, descriptors=None, targets=None, ids=None, refinement_params={}, beam_params={}, constraint_params={}, model_params={}):
    """
    k : top-k subgroups extracted.
    d : maximum depth of the beam.
    w : maximum width of a level in the beam.
    model : [finish_rate, average_marks_ratio]

    refinement_params (dict): [{numerical_bins: ..., collection_limit: ...}]
    beam_params (dict)      : [{k: ..., d: ..., w: ...}]
    constraint_params (dict): [{minimum_size: ...}]
    model_params (dict): [{model: ..., beta: ..., weighted: ...}]
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
                                                                                     numerical_bins=refinement_params['numerical_bins'], collection_limit=refinement_params['collection_limit'])
    candidate_queue = starting_candidates 

    # 3. Get the population quality
    population_finished_counts, _ = qm.finished_rates(target_space=target_space)

    # 4. Initialize the result set and the candidate queue
    result_set = pq.PriorityQueue(queue = [], max_length = beam_params['k'])

    # 5. For each level in until the maximum depth is reached, do:
    for level in range(1, beam_params['d'] + 1):
        print(f"start on level {level}")
        

    # 6.    Initialize the beam queue
        beam_queue = pq.PriorityQueue(queue = [], max_length = beam_params['w'])
        candidates_satisfied = []

    # 7.    For each description in the candidate queue, do:
        for description in candidate_queue:
            

            if not( rd.similar_description(sg_description=description, candidates_satisfied=candidates_satisfied) ):
    # 8.        Get the subgroup: indices, quality -> store as Subgroup Class if conditions hold
                indices, subgroup_descriptors = ss.check_record_inclusion(descriptive_space=descriptive_space, dtypes=descriptor_types, candidate=description)
                if len(indices) == 0:
                    continue #no valid subgroup

                unique_sessions = subgroup_descriptors['sessionID'].unique()

                # It should be sufficiently long and the descriptions should not exist in the beam queue in any form.
                if len(unique_sessions) > constraint_params['minimum_size']:
                   
                    subgroup_targets = target_space.iloc[indices]
                    subgroup_metrics = qm.subgroup_quality(subgroup_targets=subgroup_targets, params=model_params, population_dct=population_finished_counts) #already compared to population
                    selected_subgroup = sub.Subgroup(model_params=model_params, description=description, indices=indices, metrics=subgroup_metrics)

        # 9.        Insert the subgroup in the beam queue if all constraints are met and into the result set.
                    beam_queue.insert_subgroup(selected_subgroup)
                    result_set.insert_subgroup(selected_subgroup)
                    candidates_satisfied.append(selected_subgroup)

                    #print(f"{selected_subgroup} is added to the beam is now added to {beam_queue}")

        # 10.   Get the new candidate queue, by refining all descriptions in the beam queue
        candidate_queue = []
        for subgroup_description in beam_queue.get_descriptions():
            new_conditions = ca.add_condition(description=subgroup_description, starting_candidates=starting_candidates)
            candidate_queue += new_conditions
        
        print(f"Last beam was {beam_queue}")
        
    # 11. Return the result queue
    return result_set