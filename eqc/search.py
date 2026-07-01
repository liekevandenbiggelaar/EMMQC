"""
This file has the beam search strategy.
"""
import numpy as np
from datetime import datetime 

import eqc.candidates as ca
import eqc.priority_queue as pq
import eqc.subgroup_selection as ss
import eqc.subgroups as sub
import eqc.quality_measure as qm
import eqc.redundancy as rd
import eqc.fpgrowth as fp


def beam_search(data=None, descriptors=None, targets=None, ids=None, refinement_params={}, beam_params={}, constraint_params={}, model_params={}, synth=False):
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

    start_time = datetime.now()
    if not(synth):
        print(f"Search started at {start_time.now()}")

    # 1. Get the data ready -> Preprocessing and Split
    descriptive_space, target_space, attributes, descriptor_types = ca.split_spaces(data=data, descriptors=descriptors, targets=targets, ids=ids, dtypes=beam_params['dtypes'])

    # 2. Get the starting candidate descriptions
    starting_candidates   = ca.get_candidates_per_attribute(descriptive_space=descriptive_space,  dtypes=descriptor_types, refinement_params=refinement_params)
    candidate_queue = starting_candidates 

    # 3. Get the population quality
    target_level_str = model_params['target_level'] + 'ID'
    subgroup_level_str = model_params['subgroup_level'] + 'ID'

    # 3. Get the population quality
    population_finished_counts, _ = qm.finished_rates(target_space=target_space, target_level_str=target_level_str, subgroup_level_str=subgroup_level_str)

    # 4. Initialize the result set and the candidate queue
    result_set = pq.PriorityQueue(queue = [], max_length = beam_params['k'])

    # 5. For each level in until the maximum depth is reached, do:
    for level in range(1, beam_params['d'] + 1):
        if not(synth):
            print(f"start on level {level} after {datetime.now() - start_time}")
        

    # 6.    Initialize the beam queue
        beam_queue = pq.PriorityQueue(queue = [], max_length = beam_params['w'])
        candidates_satisfied = []

    # 7.    For each description in the candidate queue, do:
        #print(candidate_queue)
        for description in candidate_queue:
            

            if not( rd.similar_description(sg_description=description, candidates_satisfied=candidates_satisfied) ):
    # 8.        Get the subgroup: indices, quality -> store as Subgroup Class if conditions hold
                indices, subgroup_descriptors = ss.check_record_inclusion(descriptive_space=descriptive_space, dtypes=descriptor_types, candidate=description)

                if subgroup_descriptors is None:
                    if not(synth):
                        for cond in description._conditions:
                            print(cond._descriptor, cond._value, cond._datatype)

                if len(indices) == 0:
                    continue #no valid subgroup

                unique_sessions = subgroup_descriptors['sessionID'].unique()

                # It should be sufficiently long and the descriptions should not exist in the beam queue in any form.
                if len(unique_sessions) > constraint_params['minimum_size']:
                   
                    subgroup_targets = target_space[ target_space['representative_index'].isin(indices)]

                    subgroup_metrics = qm.subgroup_quality(subgroup_targets=subgroup_targets, population_targets=target_space, model_params=model_params, population_dct=population_finished_counts) #already compared to population
                    selected_subgroup = sub.Subgroup(model_params=model_params, description=description, indices=indices, metrics=subgroup_metrics)

        # 9.        Insert the subgroup in the beam queue if all constraints are met and into the result set.
                    beam_queue.insert_subgroup(selected_subgroup, improvement_rate=constraint_params['improvement_rate'])
                    result_set.insert_subgroup(selected_subgroup, improvement_rate=constraint_params['improvement_rate'])
                    candidates_satisfied.append(selected_subgroup)

        # 10.   Get the new candidate queue, by refining all descriptions in the beam queue
        candidate_queue = []

        # print current descriptions
        # for descr in beam_queue._queue:
        #     print(descr)
        if level < beam_params['d']:
            for subgroup in beam_queue._queue:
                temp_subgroup_descriptors = descriptive_space[ descriptive_space['representative_index'].isin(subgroup._indices)] 

                # refine this condition further
                new_conditions = ca.get_candidates_per_attribute(descriptive_space=temp_subgroup_descriptors,  dtypes=descriptor_types, refinement_params=refinement_params, parent=subgroup)

                for new_cond in new_conditions:
                    new_candidate = ca.add_condition(old_description=subgroup._description, new_condition=new_cond._conditions[0]) # there is only one condition here.
                    candidate_queue.append(new_candidate)
        

        #print(f"Last beam was {beam_queue}")
    end_time = datetime.now()   
    runtime = end_time - start_time 
    if not(synth):
        print(f"This search took {end_time - start_time}")    
    # 11. Return the result queue
    return result_set, runtime



