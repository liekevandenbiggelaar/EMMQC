import json
import os
import re
import ast
import pandas as pd

def transform_jsons(data_path='Data/private_data/sessionInfo'):
    library_dict = open_library(data_path)
    df_library = exercise_dataframes(library_dict)

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
            dats = pd.DataFrame.from_dict(question).rename(columns={'id': 'questionID'})
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


    # Into next hierarchical level
    session = interaction_dataframe(session)

    return session


def interaction_dataframe(data):

    # in session (data) we have two lines with Q1, and thus we add it twice here. We should add those dicts together
    
    
    all_items = []
    for i in range(len(data)): # go over all interactions
        if data.iloc[i]['items']['itemType'] == 'TEXT':
            continue
        item = pd.DataFrame.from_dict([data.iloc[i]['items']]).rename(columns={'id': 'interactionID'}) # we just keep TEXT, but they get NaNs
        item['questionID'] = len(item) * [data.iloc[i]['questionID']]
        item['sessionID'] = len(item) * [data.iloc[i]['sessionID']]


        # Attributes with further levels, but in need of aggregation to get on the same level as interaction
        all_items.append(item)
    
    items = pd.concat(all_items)
    items = pd.merge(data, items, on=['sessionID', 'questionID'], how='outer')
    
    #items.drop('items', axis=1, inplace=True)
    #items.drop('derivation', axis=1, inplace=True) #way too complex with little information
    return items