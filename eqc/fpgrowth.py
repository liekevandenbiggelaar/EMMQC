from collections import Counter, defaultdict
from itertools import combinations
import copy

def fpgrowth(subgroup=None, attribute_of_interest=None, closed=True):

    data = subgroup.copy()
    
    # 1. Compute the frequency pattern set.
    frequency_pattern_set = compute_frequency_pattern_set(data=data, attribute_of_interest=attribute_of_interest, minimal_support=1)

    # 2. Add the ordered-item-set into the database.
    ois = compute_ordered_item_sets(data=data, attribute_of_interest=attribute_of_interest, frequency_pattern_set=frequency_pattern_set)
    data['ordered_item_set'] = ois

    # 3. Build and fill the tree with the data
    fptree = FPTree()
    fptree.create_full_FPTree(data)

    # 4. Construct the Conditional Pattern Base
    cpb = compute_conditional_pattern_base(fptree, subgroup)

    # 5. Compute frequent patterns and filter them based on the conditions.
    frequent_itemsets = compute_frequent_patterns(cpb, minimal_support=1, maximum_support=len(data))

    # 6. Optionally, postprocess to only the closed itemsets
    if closed:
        closed_frequent_itemsets = compute_closed_patterns(frequent_itemsets)
        return closed_frequent_itemsets

    else:
        return frequent_itemsets

def prune_frequent_itemsets(FI=None, sg_indices=None, closed=True):

    FI_subgroup = copy.deepcopy(FI)
    ID_subgroup = set(sg_indices)

    for itemset in FI.keys():
        ID_i = set(FI[itemset]['indices'])
        ID_i_subgroup = ID_subgroup.intersection(ID_i)
        frequency_i_subgroup = len(ID_i_subgroup)

        # if the itemset is still true for one of the records
        # keep and decrease frequency and change indices
        if frequency_i_subgroup >= 1:
            FI_subgroup[itemset]['frequency'] = frequency_i_subgroup
            FI_subgroup[itemset]['indices'] = ID_i_subgroup
        
        # otherwise, it does not occur and we can remove it from the list.
        else:
            FI_subgroup.pop(itemset)
        
    # if we wanted only closed, this needs to be recomputed at this step.
    if closed:
        FI_subgroup = compute_closed_patterns(FI_subgroup)

    return FI_subgroup

# ================================
# Preprocessing before the FP-Tree

def compute_frequency_pattern_set(data=None, attribute_of_interest=None, minimal_support=None):
    """
    This computes the frequency pattern set of the population for a specific attribute (descriptor).

    INPUT
    * data                        : the transaction data, format: attribute of interest should contains lists.
    * attribute_of_interest (str) : the name of the descriptor that we are interested in.
    * minimal_support (int)       : the minimum number of times that a value (category) should occur in the data.

    OUTPUT
    * filtered_freq_dict (dict) : a dictionary with the unique categories and their frequencies, that exceed the minimal support.
    """

    nr_students = len(data)

    all_list = []
    for i in range(nr_students):
        all_list += data.iloc[i][attribute_of_interest]

    freq_dict = dict(Counter(all_list))
    # sort the dictionary
    sorted_freq_dict = dict(sorted(freq_dict.items(), key=lambda val: val[1], reverse=True))
    # remove all keys that do not pass the minimal support
    filtered_freq_dict = {key: val for key, val in sorted_freq_dict.items() if val >= minimal_support}

    return filtered_freq_dict


def compute_ordered_item_sets(data=None, attribute_of_interest=None, frequency_pattern_set=None):
    """
    This computes the ordered itemsets of each record in the data based on the frequency pattern set.

    INPUT
    * data                        : the transaction data, format: attribute of interest should contains lists.
    * attribute_of_interest (str) : the name of the descriptor that we are interested in.
    * frequency_pattern_set (dict): a dictionary that contains the categories and their frequency.

    OUTPUT
    * ordered_itemsets (list) : a list with the ordered itemsets per record.
    """

    nr_students = len(data)
    ordered_items = list(frequency_pattern_set.keys())

    ordered_item_sets = []
    for i in range(nr_students):
        row_ordered_items = []
        row = data.iloc[i][attribute_of_interest]

        for key in ordered_items:
            if key in row:
                row_ordered_items.append(key)

        ordered_item_sets.append(row_ordered_items)

    return ordered_item_sets

class Node:
    """
    This stores the category, frequency, indices about a single node in the FP-Tree.
    """

    def __init__(self, value, parent):
        self._value = value #the unique category in the node
        self._parent = parent #the Node that is the parent of this Node
        
        # Automatic initialization: always the same start.
        self._frequency = 0 #the frequency count
        self._indices = set() #the indices of the records that have been included in the _frequency count, no duplicates
        self._children = {} #a dictionary of the child _value (key) and the child Node (item)
        self._link = None #the last found previous node with the same _value
        self._next = None #the next found node with the same _value (if any, added later)

    def add_child(self, child):
        """
        This adds a child to the node. 

        INPUT
        * child (Node) : the child that occurs in relation to this one.
        """

        # Only add as a child if the child is not in the children list.
        # Otherwise we do nothing (if all is right, this could already be checked in the Tree.)
        if child._value not in self._children:
            self._children[child._value] = child

    def add_indices(self, index):
        """
        This adds the index of the current record to the list.

        INPUT
        * index (int) : index value to be added.
        """

        self._indices.add(index)

    def add_link(self, node):
        """
        This adds the information of a node with the same _value to keep track.
        """

        self._link = node
        node._next = self #add self to the node's next list.
    
    def increase_frequency(self):
        """
        This increases the frequency by one.
        """

        self._frequency += 1
    
    def alter_frequency(self, frequency):
        self._frequency = frequency
    
    def alter_indices(self, indices):
        self._indices = indices


class FPTree:

    def __init__(self):
        """ We start with an empty FP-tree. """
        self._root = Node("ROOT", None) #it has no parent
        self._firstinstances = {} #this is a dictionary with for every unique _value, it stores the first node that was found. 
    
    def __str__(self):
        return f"Our root has {len(self._root._children)} children"


    def add_collection(self, collection, index):
        """
        This adds the collection of a single record to the FP-Tree.

        INPUT
        * collection (list): a list with the _values of that records
        """

        current_node = self._root 
        # Iterate over all values in the collection of that record
        for val in collection: 

            # check if the value is already mentioned in the _root's children
            child_node = current_node._children.get(val)

            # if the value is not yet in the children, we have to create a new node
            if child_node == None:
                child_node = Node(value=val, parent=current_node)

                # add the new node (child) to the _children of the current node
                current_node.add_child(child_node) 

                # we check if the _value of the child node has already occurred somewhere in the tree
                if val in self._firstinstances.keys():
                    
                    # Get the first instance of the _value
                    instance_node = self._firstinstances[val]

                    # As long as we can form links between an instance of the value and another, keep going to the next link.
                    while instance_node._link != None:
                        instance_node = instance_node._link
                    
                    # Add the new child when there is no link anymore
                    instance_node._link = child_node

                # if it has not yet occurred, we add it to the instances as the first instance
                else:
                    self._firstinstances[val] = child_node
            
            # always add frequency, indices, and replace current node
            child_node.add_indices(index)
            child_node.increase_frequency() #always increases by 1

            current_node = child_node


    def create_full_FPTree(self, data_ordered_itemsets):
        """
        Go over the entire data and add in the FPTree.
        """

        for i in range(len(data_ordered_itemsets)):
            collection = data_ordered_itemsets.iloc[i]['ordered_item_set']
            index = data_ordered_itemsets.iloc[i]['representative_index']

            self.add_collection(collection=collection, index=index)


# =======================================
# Extracting information from the FP-Tree

def compute_conditional_pattern_base(fptree, subgroup):

    # start at the first instances in the FP-Tree
    FI = fptree._firstinstances
    subgroup_indices = set(subgroup['representative_index'])

    cpb = {}
    for val in FI.keys():

        # collect all patterns for this value
        val_patterns = []

        current_node = FI[val]

        # as long as our current node (i.e. parents) is not None
        while current_node is not None:
            all_indices = set(current_node._indices)
            fitting_indices = subgroup_indices.intersection(all_indices)
            val_collect = {}
            val_collect['frequency'] = len(fitting_indices)
            val_collect['indices'] = fitting_indices
            val_collect['pattern'] = []


            parent_node = current_node._parent

            # we want to find all parent, before the ROOT
            while parent_node._value != 'ROOT':
                val_collect['pattern'].append(parent_node._value)
                parent_node = parent_node._parent
            
            # if the pattern found is empty, hence the next parent is the root, we do not include it.
            if len(val_collect['pattern']) == 0:
                current_node = current_node._link
            
            else:
                # if found, we add it to the list and move on to the next link
                val_patterns.append(val_collect)
                current_node = current_node._link
        
        # only add if we have found actual patterns and itemsets.
        if len(val_patterns) != 0:
            cpb[val] = val_patterns

    return cpb

def compute_frequent_patterns(cpb, minimal_support=None, maximum_support=None):

    frequent_patterns = {}

    # For all unique categories in the collections
    for val in cpb.keys():
        
        # and for all conditional pattern bases found of that category
        for pb in cpb[val]:

            pattern = pb['pattern'].copy()
            
            # find all possible combinations to be made, and add the category to each combination
            all_combinations = []
            for i in range(len(pattern)):
                combis = combinations(pattern, i+1)

                if i == 0:
                    all_combinations += [[x[0], val] for x in combis]
                else:
                    all_combinations += [list(x) + [val] for x in combis]

            # now for each combination, check if we have already encountered it
            for combs in all_combinations:
                frozen_pattern = frozenset(combs)

                # if we have seen it, add the frequency of the current pattern base to that of the combination, and do the same with the indices
                if frozen_pattern in frequent_patterns.keys():
                    frequent_patterns[frozen_pattern]['frequency'] += pb['frequency']
                    frequent_patterns[frozen_pattern]['indices'] = frequent_patterns[frozen_pattern]['indices'].union(pb['indices'])
                
                # if we have not seen it, we make a new frequent pattern and initialize the frequency and indices with those of the current pattern base
                else:
                    frequent_patterns[frozen_pattern] = {'frequency': pb['frequency'],
                                                        'indices': pb['indices']}

    return frequent_patterns

def compute_closed_patterns(frequent_patterns):

    groups = defaultdict(list)

    for pattern, data in frequent_patterns.items():
        groups[frozenset(data['indices'])].append((pattern, data))

    closed_patterns = {}

    for group in groups.values():

        # only keep largest pattern per identical indices
        max_len = max(len(pattern) for pattern, _ in group)

        for pattern, data in group:
            if len(pattern) == max_len:
                closed_patterns[pattern] = data

    return closed_patterns