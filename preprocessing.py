import json
import os
import re
import ast
import pandas as pd
import numpy as np

def transform_jsons(data_path='Data/private_data/sessionInfo'):
    library_dict = open_library(data_path)
    df_library = exercise_dataframe(library_dict)

    #df_library = additional_columns(df_library)

    df_library.to_csv("algebrakit_firstbatch_2.csv", index=False)
    
# ================== OPEN ALL FILES AS ONE DICTIONARY =================== #
def open_file(eID: str, sID: str, data_path = 'Data/private_data/sessionInfo'):
    """ 
    Opens the JSON file of one session of an exercise.

    INPUT PARAMETERS
    * eID: Unique Exercise ID in string format.
    * sID: Unique Session ID in string format.
    * data_path: Directory path where the data is stored.

    OUTPUT PARAMETERS
    * data: the opened JSON file in str-dict format.
    """

    with open(f'{data_path}/{eID}/{sID}.json', 'r') as file:
        data = json.load(file)

    return data


def open_exercise_sessions(eID: str, data_path = 'Data/private_data/sessionInfo'):
    """
    Opens the JSON files of all sessions for one exercise. 
    
    INPUT PARAMETERS
    * eID: Unique Exercise ID in string format. 
    * data_path: Directory path where the data is stored.
    
    OUTPUT PARAMETERS
    * exercise_dict: Dictionary with the data of a session stored per session key.
    """
    exercise_dict = {}

    sessions = os.listdir(f'{data_path}/{eID}')
    sessions = [sID.replace(".json", "") for sID in sessions] # removing .json

    for sID in sessions:
        data_sID = open_file(eID, sID, data_path)
        exercise_dict[sID] = data_sID

    return exercise_dict


def open_library(data_path = 'Data/private_data/sessionInfo'):
    """
    Opens the JSON files of all sessions of all exercises (library) and stores them into one long dictionary.
    
    INPUT PARAMETERS
    * data_path: Directory path where the data is stored.
    
    OUTPUT PARAMETERS
    * library_dict: Dictionary with the data of all sessions stored per session per exercise.
    """
    library_dict = {}

    exercises = os.listdir(f'{data_path}')

    for eID in exercises:
        exercise_dict = open_exercise_sessions(eID, data_path)
        library_dict[eID] = exercise_dict

    return library_dict


# ================== DATA AGGREGATIONS AND PREPROCESSING =================== #
def aggregate_tagDescriptions(data):

    # Explode and Aggregate Tag Descriptions
    # Always check if it is actually a dictionary
    data['skills'] = data['tagDescriptions'].apply(lambda d: list(d.keys())
                                                   if isinstance(d, dict) else [])
    
    data['stepTypes'] = data['tagDescriptions'].apply(lambda d: [v.get('stepType') for v in d.values()] 
                                                      if isinstance(d, dict) else [])
    data.drop('tagDescriptions', axis=1, inplace=True)

    return data


def aggregate_scoring(data):
    # Explode and Aggregate Scoring
    # Always check if it is actually a dictionary
    data['finished'] = data['scoring'].apply(lambda d: d['finished']
                                             if isinstance(d, dict) else [])
    
    data['marksEarned'] = data['scoring'].apply(lambda d: d['marksEarned']
                                                if isinstance(d, dict) else [])
    
    data['marksTotal'] = data['scoring'].apply(lambda d: d['marksTotal']
                                               if isinstance(d, dict) else [])
    data.drop('scoring', axis=1, inplace=True)

    return data


# ================== STORE DICTIONARY IN APPROPRIATE DATA FRAME =================== #
def exercise_dataframe(library_dict):
    """
    A dataframe with all sessions of one exercise and all questions of that session and all interactions of that question and all events of that interaction included.
    """

    unique_exercises = list(library_dict.keys())

    all_exercises = []
    for ex in unique_exercises:
        session = pd.DataFrame.from_dict(library_dict[ex]).T.reset_index().rename(columns={'index': 'sessionID'})
        session['exerciseID'] = len(session) * [ex]
        session = session[['exerciseID'] + [c for c in session.columns if c != 'exerciseID']]

        # Attributes without further levels
        session = aggregate_tagDescriptions(session)
        session = aggregate_scoring(session)

        # Attributes with further levels
        session = question_dataframe(session)

        all_exercises.append(session)
    
    data = pd.concat(all_exercises)
    data = data.reset_index(drop=True)

    return data


def question_dataframe(data):
    """
    A dataframe with all questions of a session and all interactions of that question and all events of that interaction included.
    """

    questions = data['elements']

    all_sessions = []
    for i in range(len(data)): # over all sessions
        all_questions = []
        for question in data.iloc[i]['elements']:
            dats = pd.DataFrame.from_dict(question).rename(columns={'id': 'questionID', 'type': 'questionType'})
            dats['sessionID'] = len(dats) * [data.iloc[i]['sessionID']]
            
            all_questions.append(dats)
    
        questions = pd.concat(all_questions)
        all_sessions.append(questions)

    # Combine all questions into one database
    session = pd.concat(all_sessions)
    session = session[['sessionID'] + [c for c in session.columns if c != 'sessionID']]

    # Merge everything with the existing database for each session
    session = pd.merge(data, session, on="sessionID", how='outer')
    session.drop('elements', axis=1, inplace=True)

    # Aggregate all items for the same question: now they are in different rows but we want them in the same one.
    org_columns = session.columns
    session = session.groupby(['sessionID', 'questionID'], sort=False, as_index=False).agg({'items': list, **{c: 'first' for c in session.columns if c not in ['sessionID', 'questionID', 'items']}})
    session = session[[c for c in org_columns]] # get original column order back

    # Into next hierarchical level
    session = interaction_dataframe(session)

    return session


def interaction_dataframe(data):

    # in session (data) we have two lines with Q1, and thus we add it twice here. We should add those dicts together
    
    
    all_items = []
    for i in range(len(data)): # go over all questions
        esq_data = data.iloc[i] # get the exercise, session, question row

        content = ''

        # Go over all available interactions for this unique ESQ-combination
        for j in range(len(esq_data['items'])):
            
            # We want to skip all text interaction -> only contains content that we include already now.
            if esq_data['items'][j]['itemType'] == 'TEXT':
                content = esq_data['items'][j]['content']
                continue

            item = pd.DataFrame.from_dict([esq_data['items'][j]]).rename(columns={'id': 'interactionID'}) # we just keep TEXT, but they get NaNs
            item['questionID'] = len(item) * [data.iloc[i]['questionID']]
            item['sessionID'] = len(item) * [data.iloc[i]['sessionID']]
            item['content'] = content
            content = '' # Only content for immediately successive interactions


            # Attributes with further levels, but in need of aggregation to get on the same level as interaction
            all_items.append(item)
    
    items = pd.concat(all_items)
    items = pd.merge(data, items, on=['sessionID', 'questionID'], how='outer')
    items['content'] = [s.replace('$', '') for s in items['content']]
    items['solution'] = [s.replace('$', '') for s in items['solution']]
    items.drop(['items', 'derivation'], axis=1, inplace=True) #derivation is too complex
    

    # Cleaning the strings
    items_events = aggregate_results(items)
    

    return items_events

def aggregate_results(df):
    event_type_list, event_eval_list = [], []
    pos_tags_all, neg_tags_all = [], []

    for i in range(len(df)):
        inter = df['result'].iloc[i]

        # Events of students
        events = inter['events']
        et, ee = [], [] # event type and evaluation

        for ev in events:
            et.append(ev['event'])

            if 'inputStatus' in ev.keys():
                ee.append(ev['inputStatus'])
            elif ev['event'] == 'EVALUATE':
                ee.append(ev['exerciseStatus'])
            else:
                ee.append(ev['event']) 
        
        event_eval_list.append(ee)
        event_type_list.append(et) 
        
        # Skills tackled by students
        tags = inter['tags']
        pos, neg = [], []

        for t in tags:
            if t['weight'] > 0:
                pos.append(t['id'])
            elif t['weight'] < 0:
                neg.append(t['id'])
            
        pos_tags_all.append(pos)
        neg_tags_all.append(neg)



    df['event_types'] = event_type_list
    df['event_evaluations'] = event_eval_list 
    df['positive_skills'] = pos_tags_all
    df['negative_skills'] = neg_tags_all

    #Simple, non-list, attributes
    df['result_status'] = [ df['result'].iloc[i]['status'] for i in range(len(df)) ]
    df['result_progress'] = [ df['result'].iloc[i]['progress'] for i in range(len(df)) ] 
    df['marksEarned_interaction'] = [ df['result'].iloc[i]['scoring']['marksEarned'] for i in range(len(df)) ] 
    df['marksTotal_interaction'] = [ df['result'].iloc[i]['scoring']['marksTotal'] for i in range(len(df)) ] 
    df['finished_interaction'] = [ df['result'].iloc[i]['scoring']['finished'] for i in range(len(df)) ] 
    df['maxAttempts'] = [ df['result'].iloc[i]['scoring']['maxAttempts'] if 'maxAttempts' in df['result'].iloc[i]['scoring'].keys() else np.nan for i in range(len(df)) ] 
    df['usedAttempts'] = [ df['result'].iloc[i]['scoring']['usedAttempts'] if 'usedAttempts' in df['result'].iloc[i]['scoring'].keys() else np.nan for i in range(len(df)) ] 
    df['failed'] = [ df['result'].iloc[i]['scoring']['failed'] if 'failed' in df['result'].iloc[i]['scoring'].keys() else np.nan for i in range(len(df)) ] 
    df['marksPenalty'] = [ df['result'].iloc[i]['scoring']['penalties']['marksPenalty'] for i in range(len(df)) ] 
    df['hintsRequested'] = [ df['result'].iloc[i]['scoring']['penalties']['hintsRequested'] for i in range(len(df)) ] 
    df['mathErrors'] = [ df['result'].iloc[i]['scoring']['penalties']['mathErrors'] for i in range(len(df)) ] 

    df.drop('result', axis=1, inplace=True)

    return df