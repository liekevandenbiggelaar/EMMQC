import numpy as np
import pandas as pd
import random as r

def sample_item_descriptors(covs=None, params=None):

    covs_ext = covs.copy()
    nr_item_descriptors=params[5]
    nr_items=params[6]
    p=params[2]

    for itemdesc in np.arange(1,nr_item_descriptors+1):
        covs_ext['it' + str(itemdesc)] = sample_items(nr_items=nr_items, n=covs.shape[0], p=p)

    item_descriptor_names = ['it' + str(k) for k in np.arange(1,nr_item_descriptors+1)]

    return covs_ext, item_descriptor_names

def sample_items(nr_items=None, n=None, p=None):

    all_items = list('abcdefghijklmnopqrstuvwxyz')[0:nr_items]
    covs_temp = pd.DataFrame()
    for itemid in np.arange(1,nr_items+1):
        item = all_items[itemid-1]
        if itemid < 3:
            covs_temp[item] = np.random.binomial(n=1, p=p, size=n)
        else:
            random_prob = np.random.uniform(0.2, 0.8)
            covs_temp[item] = np.random.binomial(n=1, p=random_prob, size=n)
    
    # change binary covs_ext into tuples of items, for each row
    item_tuples = []
    for idx in range(n):
        selected_items = [all_items[i] for i in range(nr_items) if covs_temp.iloc[idx, i] == 1]
        item_tuples.append(tuple(selected_items))
    
    return item_tuples

def find_mask(dataset=None, true_description=None):

    # extract tuple from true description
    true_tuple = list(true_description.values())[0]

    # find rows in dataset where the item descriptor column contains at least the true tuple
    mask = dataset.apply(lambda row: set(true_tuple).issubset(set(row.iloc[dataset.columns.get_loc(list(true_description.keys())[0])])), axis=1)

    return mask