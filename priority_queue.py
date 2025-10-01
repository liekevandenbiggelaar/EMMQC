"""
This file has the priority queue class that is used in the beam search.
"""
import numpy as np

import subgroups as sub
import redundancy as re

class PriorityQueue():
    
    def __init__(self, queue: list[sub.Subgroup], max_length: int):
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
    
    def insert_subgroup(self, subgroup: sub.Subgroup):


        if self.redundancy_check(subgroup._description):
            # if there is redundancy, do not consider.
            self._queue = self._queue

        elif len(self._queue) < self._max_length:
            self._queue.append(subgroup)
            self._queue = sorted(self._queue, reverse=True, key = lambda i: i._quality)

        else:
            least_exceptional_in_queue = self._queue[-1]
            quality_least_in_queue = least_exceptional_in_queue._quality
            quality_candidate = subgroup._quality

            if quality_candidate > quality_least_in_queue: 
                # new candidate is more exceptional (higher difference with population)
                self._queue.pop(-1)
                self._queue.append(subgroup)
                self._queue = sorted(self._queue, reverse = True, key = lambda i: i._quality)
            else:
                self._queue = self._queue

    
    def compare_subgroups(self):
        return None
    
    def redundancy_check(self, candidate=None):

        return re.similarity_redundancy(description=candidate, list_of_descriptions=self.get_descriptions()) or re.generalization_redundancy()
    
    def get_descriptions(self):
        return [subgroup._description for subgroup in self._queue]
    
    def get_qualities(self):
        return [subgroup._quality for subgroup in self._queue]
    
    def get_indices(self):
        return [subgroup._indices for subgroup in self._queue]
    
    def get_sizes(self):
        return [subgroup._size for subgroup in self._queue]
    
    def get_values(self):
        return [subgroup._values for subgroup in self._queue]
