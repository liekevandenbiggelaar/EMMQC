"""
This file contains the class of the subgroup.
"""

import eqc.candidates as ca

class Subgroup():
    """
    This class contains all information that needs to be known for a Subgroup.
    
    INPUT
    - model (str)           : what type of model class is tested, e.g. failing rate, scoring, ...
    - description (list)    : the description of the subgroup.
    - indices (list)        : the list of indices of the records included in the subgroup.
    - quality (float)       : the quality score of the subgroup.
    - values (list[float])  : a list of all model values for each record.
    """
    
    def __init__(self, model_params: dict, description: ca.Description, indices: list, metrics: dict):

        self._model_params = model_params
        self._rank = None #added later if it is included in the top-k.
        self._description = description
        
        self._indices = indices
        self._FIs = {} #the frequent itemsets still at play for the records in this subgroup

        self._metrics = metrics
        if len(metrics.keys()) == 0:
            self._size = None
            self._quality = None
        else:
            self._size = metrics['exercise_count'] #size of the subgroup
            self._quality = metrics['subgroup_quality']

    def __str__(self):
        conds = self._description._conditions

        summ_conds = " & ".join([cond.__str__() for cond in conds])

        return f"Records with {summ_conds} have a quality score of {self._quality}."

    def add_FIs(self, FPs):
        for key, val in FPs.items():
            self._FIs[key] = val
    
    # Print the containments of the subgroup
    def print_model(self):
        return f"The model is {self._model_params['model']} with, if necessary, beta {self._model_params['beta']}."
    
    def print_rank(self):
        return f"The rank is {self._rank}."
    
    def print_description(self):
        #return f"The subgroup description is {self._description}." 
        return self._description

    def print_quality(self):
        return f"The quality of the subgroup compared to population is {self._quality}."
    
    def print_indices(self):
        return f"The indices of the records in the subgroups are {self._indices}."
    
    def print_size(self):
        return f"The subgroup size is {self._size}."
    
    def print_metrics(self):
        #return f"The metrics in the subgroup are {self._metrics}."
        return self._metrics
