"""
This file contains the class of the subgroup.
"""

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
    
    def __init__(self, model: str, description: str, indices: list, quality: float, values: list[float]):

        self._model = model
        self._rank = None #added later if it is included in the top-k.
        self._description = description
        self._indices = indices
        self._size = len(indices) #size of the subgroup
        self._quality = quality
        self._values = values

    def __str__(self):
        return f"This subgroup of size {self._size} has description {self._description} and a quality score of {self._quality}."
    
    def insert_condition(self, condition):  
        return None
    
    def remove_condition(self, condition):
        return None
    
    def modify_description(self, new_description: str):
        self._description = new_description
    
    def modify_indices(self, new_indices: list):
        self._indices = new_indices
        self._size = len(new_indices)
    
    def modify_values(self, new_values: list):
        self._values = new_values
    
    def modify_quality(self, new_quality: float):
        self._quality = new_quality
    
    def insert_rank(self, rank):
        self._rank = rank
    
    # Print the containments of the subgroup
    def print_model(self):
        return f"The model is {self._model}."
    
    def print_rank(self):
        return f"The rank is {self._rank}."
    
    def print_description(self):
        return f"The subgroup description is {self._description}." 
    
    def print_quality(self):
        return f"The quality of the subgroup is {self._quality}."
    
    def print_indices(self):
        return f"The indices of the records in the subgroups are {self._indices}."
    
    def print_size(self):
        return f"The subgroup size is {self._size}."
    
    def print_values(self):
        return f"The values of quality in the subgroup are {self._values}."
