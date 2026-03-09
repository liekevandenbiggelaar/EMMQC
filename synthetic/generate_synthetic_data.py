import numpy as np
import pandas as pd
import random as r
import itertools as it

import synthetic.generate_item_descriptors as gid
import synthetic.generate_multiple_exercises as gme

def generate_dataset(params=None):

    # if nr_exercises > 1, create data with multiple exercises
    if params[12] > 1:
        dataset, cov_names, covs, cov_names_types, true_description, target_att_name, array_with_pop_fail_rate = gme.multiple_exercises(params=params)
        #print(dataset.head(20))

    # otherwise just create 1 dataset with 1 subgroup
    else: 
        dataset, cov_names, covs, cov_names_types, true_description, target_att_name = dataset_for_one_exercise(params=params)
        array_with_pop_fail_rate = None
        dataset['exerciseID'] = 1
    
    dataset['representative_index'] = np.arange(1,len(dataset)+1)
    
    # calculate precision, recall and F1 for the true subgroup description
    TP, FP, FN, TN = calculate_confusion_matrix(df=dataset, true_description=true_description, target_att_name=target_att_name)
    #print(TP,FP,FN,TN)
    precision, recall, F1 = calculate_metrics(TP=TP, FP=FP, FN=FN, TN=TN)
    #print(precision, recall, F1)

    return dataset, cov_names, covs, cov_names_types, true_description, target_att_name, precision, recall, F1, array_with_pop_fail_rate

def dataset_for_one_exercise(params=None):

    # sample descriptive space
    covs, cov_names, cov_names_types = sample_covs(N=params[0], ncovs=params[1], p=params[2])
    
    # possibly sample item descriptors
    if params[5] > 0:
        covs, item_descriptor_names = gid.sample_item_descriptors(covs=covs, params=params)
        cov_names = cov_names + item_descriptor_names 
        cov_names_types['collection'] = item_descriptor_names
        #print(cov_names_types)

    # sample target space
    dataset = covs.copy()
    pop_fail_rate=params[3]
    #target_att_name = 'l' + str(1)
    target_att_name = 'finished'
    dataset[target_att_name] = create_target_values(pop_fail_rate=pop_fail_rate, size=params[0])

    # generate one true subgroup
    # true subgroup description given by experiment
    true_description = params[7]
    # determine mask
    mask = determine_mask(df=dataset, true_description=true_description)
    #print(np.sum(mask), "out of", len(mask), "records in the subgroup") # check how many records are in the subgroup
    #dataset['mask'] = mask

    # change target values for subgroup
    dataset = generate_one_true_subgroup(dataset=dataset, params=params, mask=mask, target_att_name=target_att_name)

    # add session ID
    dataset['sessionID'] = np.arange(1,len(dataset)+1)
        
    return dataset, cov_names, covs, cov_names_types, true_description, target_att_name

def generate_one_true_subgroup(dataset=None, params=None, mask=None, target_att_name=None):

    n = np.sum(mask)
    
    # extract subgroup values, number of 0s and 1s depends on desired precision
    precision=params[4]
    desired_nr_ones = int(n*precision)
    current_subgroup_values = dataset.loc[mask, target_att_name]
    current_subgroup_ones = np.sum(current_subgroup_values)
    required_ones = desired_nr_ones - current_subgroup_ones

    # we need to change some 0s into 1s in the subgroup
    # and do the reserve for the complement values, to maintain the same number of 1s and 0s in the entire dataset
    dataset = change_0s_and_1s(dataset=dataset, mask=mask, target_att_name=target_att_name, required_ones=required_ones)
    # count 0s and 1s for dataset target attribute
    #print(dataset[target_att_name].value_counts())

    return dataset
    
def change_0s_and_1s(dataset=None, mask=None, target_att_name=None, required_ones=None):
        
    df = dataset.copy()     
    if required_ones > 0:
        # we need to change some 0s to 1s in the subgroup
        zero_indices = df.loc[mask & (df[target_att_name] == 0)].index
        indices_to_change = r.sample(list(zero_indices), required_ones)
        df.loc[indices_to_change, target_att_name] = 1
        # we need to change some 1s to 0s in the complement
        complement_indices = df.loc[~mask & (df[target_att_name] == 1)].index
        if len(complement_indices) < required_ones:
            print("Warning: not enough records in the complement to change from 1 to 0, changing all of them")
            complement_indices_to_change = complement_indices
        else:
            complement_indices_to_change = r.sample(list(complement_indices), required_ones)
        df.loc[complement_indices_to_change, target_att_name] = 0
    elif required_ones < 0:
        # we need to change some 1s to 0s
        one_indices = df.loc[mask & (df[target_att_name] == 1)].index
        indices_to_change = r.sample(list(one_indices), abs(required_ones))
        df.loc[indices_to_change, target_att_name] = 0
        # we need to change some 0s to 1s in the complement
        complement_indices = df.loc[~mask & (df[target_att_name] == 0)].index
        if len(complement_indices) < abs(required_ones):
            print("Warning: not enough records in the complement to change from 0 to 1, changing all of them")
            complement_indices_to_change = complement_indices
        else:
            complement_indices_to_change = r.sample(list(complement_indices), abs(required_ones))   
        df.loc[complement_indices_to_change, target_att_name] = 1
    else:
        # we are already at the desired number of 1s, so we don't need to change anything
        pass

    return df

def determine_mask(df=None, true_description=None):

    dataset = df.copy()
    desc = true_description

    # is true description for binary or item descriptors?
    # determine all covariate names in the description, to select the right columns from the dataset
    if 'a' in list(desc.keys())[0]:
        mask = (dataset[list(desc.keys())] == pd.Series(desc)).all(axis=1)
    elif 'it' in list(desc.keys())[0]:
        mask = gid.find_mask(dataset=dataset, true_description=desc)
    
    if np.sum(mask) == 0:
        print("Warning: there are no records in the subgroup, possibly N is too small")

    return mask

def create_target_values(pop_fail_rate=None, size=None, precision=None):

    if pop_fail_rate is not None:
        # fail == 1
        target_values = np.random.binomial(n=1, p=pop_fail_rate, size=size) 
        return target_values
    
    else:
        # fail in the subgroup
        ntrue = int(size * precision)
        if ntrue == 0:
            ntrue = 1
        labels = np.concatenate([np.ones(ntrue), np.zeros(size-ntrue)])
        target_values = np.random.permutation(labels) # dit is een shuffle, niet een permutation!
        return target_values
    
def calculate_confusion_matrix(df=None, true_description=None, target_att_name=None):

    dftemp = df.copy()
    mask = determine_mask(df=dftemp, true_description=true_description)
    dftemp['mask'] = mask

    TP = np.sum((dftemp[target_att_name] == 1) & (dftemp['mask'] == True))
    FP = np.sum((dftemp[target_att_name] == 0) & (dftemp['mask'] == True))
    FN = np.sum((dftemp[target_att_name] == 1) & (dftemp['mask'] == False))
    TN = np.sum((dftemp[target_att_name] == 0) & (dftemp['mask'] == False))

    return TP, FP, FN, TN

def calculate_metrics(TP=None, FP=None, FN=None, TN=None):

    precision = TP / (TP + FP) if (TP + FP) > 0 else 0
    recall = TP / (TP + FN) if (TP + FN) > 0 else 0
    F1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

    return np.round(precision,2), np.round(recall,2), np.round(F1,2)

def sample_covs(N=None, ncovs=None, p=None):

    # sample covariates
    covs = pd.DataFrame()
    for cov in np.arange(1,ncovs+1):
        covs['a' + str(cov)] = np.random.binomial(n=1, p=p, size=N)

    cov_names = ['a' + str(k) for k in np.arange(1,ncovs+1)]

    cov_names_types = {'nominal': [], 
                       'boolean': cov_names, 
                       'numerical': [], 
                       'ordinal': [],
                       'collection': []}

    return covs, cov_names, cov_names_types