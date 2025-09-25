"""
This file has the priority queue class that is used in the beam search.
"""
import numpy as np

import subgroups as s

class PriorityQueue():
    
    def __init__(self, queue: list[s.Subgroup], max_length: int):
        self._queue = queue #Form [Subgroup(A), Subgroup(B), ...]
        self._max_length = max_length
        self._average_size = None #Get after summarizing
        self._average_quality = None #Get after summarizing
        self._length_queue = None #Get after summarizing

    def __str__(self):
        return f"The priority queue has {len(self._queue)} subgroups."

    def summarize_queue(self):
        self._average_size = np.mean(self.get_sizes())
        self._length_queue = len(self._queue)
        self._average_quality = np.mean(self.get_qualities())
        print(f"This queue has subgroups of average size {self._average_size} in a queue of length {self._length_queue} and an average quality of {self._average_quality}.")
    
    def insert_subgroup(self):
        return None
    
    def remove_subgroup(self):
        return None
    
    def compare_subgroups(self):
        return None
    
    def redundancy_check(self):
        return None
    
    def get_descriptions(self):
        return [subgroup._description for subgroup in self._queue]
    
    def get_qualities(self):
        return [subgroup._quality for subgroup in self._queue]
    
    def get_indices(self):
        return [subgroup._indices for subgroup in self._queue]
    
    def get_sizes(self):
        return [subgroup._size for subgroup in self._queue]
