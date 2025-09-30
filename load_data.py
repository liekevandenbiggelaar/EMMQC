import json
import os
import re
import ast
from collections import Counter

import pandas as pd

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

def event_dataframes(event_dict: str, interactionID: str):
    """
    A dataframe with all events of one interaction.
    """

    event_columns_mapping = {'timestamp': 'eventID', 
                         'event': 'eventType', 
                         'tags': 'eventTags', 
                         'annotations': 'eventAnnotations', 
                         'exerciseStatus': 'exerciseStatusAfterEvent', 
                         'progress': 'progressAfterEvent',
                         'inputStatus': 'inputStatus'}
    

    df_event = pd.json_normalize(event_dict).rename(columns=event_columns_mapping)
    iIDs = len(df_event) * [interactionID]
    df_event['interactionID'] = iIDs
    df_event = df_event.iloc[:, [-1] + list(range(len(df_event.columns)-1))]
    
    return df_event


def interaction_dataframes(interaction_dict: str, questionID: str):
    """
    A dataframe with all interactions of one question and all events of that interaction included.
    """
    if type(interaction_dict) == dict:
        interaction_dict = [interaction_dict]

    interaction_columns_mapping = {'itemType': 'itemType',
                                   'content': 'itemContent',
                                   'id': 'interactionID',
                                   'interactionType': 'interactionType',
                                   'result': 'interactionResult',
                                   'solution': 'interactionSolution',
                                   'derivation': 'interactionDerivation'}

    # Create basis of the interaction dataframe
    df_interaction = pd.json_normalize(interaction_dict).rename(columns=interaction_columns_mapping) #flatten all contents of interactions
    df_interaction['questionID'] = len(df_interaction) * [questionID]
    df_interaction = df_interaction.iloc[:, [-1] + list(range(len(df_interaction.columns)-1))]

    # Append the event dataframe to the interactions
    for item in interaction_dict:
        
        if item['itemType'] == 'INTERACTION':
            events = item['result']['events']
            itemID = item['id']
            
            list_event_frames = []
            for event in events:
                one_item = event_dataframes(event, itemID)
                list_event_frames.append(one_item)
            
            if len(list_event_frames) >= 1 :
                df_event = pd.concat(list_event_frames, axis=0, ignore_index=True)
                df_interaction = pd.merge(df_interaction, df_event, on="interactionID", how='outer')
            
            else:
                df_interaction = df_interaction

    return df_interaction


def question_dataframes(questions, sessionID):
    """
    A dataframe with all questions of one session and all interactions of that question and all events of that interaction included.
    """

    question_columns_mapping = {'id': 'questionID',
                                   'type': 'questionType',
                                   'items': 'items'}

    # Create basis of the question dataframe
    df_question = pd.json_normalize(questions).rename(columns=question_columns_mapping).drop('items', axis=1) #flatten all contents of interactions
    df_question['sessionID'] = len(df_question) * [sessionID]
    df_question = df_question.iloc[:, [-1] + list(range(len(df_question.columns)-1))]
    
    list_question_frames = []
    # Append the interaction dataframe to the question
    for question in questions:
        interactions = question['items']
        questionID = question['id']

        one_question = interaction_dataframes(interactions, questionID)
        
        list_question_frames.append(one_question)

            
    df_interaction = pd.concat(list_question_frames, axis=0, ignore_index=True)

    
    # Join the interaction dataframe with the question dataframe
    df_question = pd.merge(df_question, df_interaction, on="questionID", how='outer')
        

    return df_question


def handle_skills(df_session):

    skill_frames = []
    for j in range(len(df_session)):
        session = df_session.iloc[j]
        df_skills = pd.DataFrame.from_dict(session['skills']).T.reset_index().rename(columns={'index': 'skillName'})
        df_skills['sessionID'] = len(df_skills) * [session['sessionID']]
        skill_frames.append(df_skills)
    
    df_skills = pd.concat(skill_frames).reset_index().drop(['index', 'descr'], axis=1)
    df_skills = df_skills.groupby(['sessionID']).agg(list).reset_index().rename(columns={'index': 'sessionID'})
    
    return df_skills


def session_dataframes(library_dict, exerciseID):
    """
    A dataframe with all sessions of one exercise and all questions of that session and all interactions of that question and all events of that interaction included.
    """

    question_columns_mapping = {'index': 'sessionID',
                                   'success': 'sessionSuccess',
                                   'creationTimeStamp': 'creationTimeStamp',
                                   'elements': 'elements',
                                   'tagDescriptions': 'skills',
                                   'scoring': 'scoring'}

    exercise = library_dict[exerciseID]
    sessions = exercise.keys()

    # Create basis of the question dataframe
    df_session = pd.DataFrame.from_dict(exercise, orient='index').reset_index().rename(columns=question_columns_mapping)

    # Flatten all scoring metrics
    all_scores = []

    for i in range(len(df_session)):
        scoring = df_session.iloc[i]['scoring']
        df_scoring = pd.json_normalize(scoring)
        df_scoring['sessionID'] = len(df_scoring) * [df_session.iloc[i]['sessionID']]

        all_scores.append(df_scoring)
    
    df_all_scores = pd.concat(all_scores)
    
    df_session = pd.merge(df_session, df_all_scores, on='sessionID', how='outer')

    df_skills = handle_skills(df_session)
    df_session = pd.merge(df_session, df_skills, on='sessionID', how='outer')

    df_session = df_session.drop(['elements', 'scoring', 'skills'], axis=1)

    
    df_session['exerciseID'] = len(df_session) * [exerciseID]
    df_session = df_session.iloc[:, [-1] + list(range(len(df_session.columns)-1))]
    

    list_session_frames = []
    errors = []
    # # Append the interaction dataframe to the question
    for session in sessions:

        questions = exercise[session]['elements']
        sessionID = session


        one_session = question_dataframes(questions, sessionID) 
        list_session_frames.append(one_session)
  
    df_question = pd.concat(list_session_frames, axis=0, ignore_index=True)

    
    # Join the interaction dataframe with the question dataframe
    df_session = pd.merge(df_session, df_question, on="sessionID", how='outer')
        
    
    return df_session


def exercise_dataframes(library_dict):
    """
    A dataframe with all sessions of one exercise and all questions of that session and all interactions of that question and all events of that interaction included.
    """

    exercises = library_dict.keys()

    all_exercise_frames = []
    for exercise in exercises:
        one_exercise = session_dataframes(library_dict, exercise)
        all_exercise_frames.append(one_exercise)

    df_exercises = pd.concat(all_exercise_frames)

    return df_exercises

def additional_columns(data=None):
    """
    Case-specific!
    """

    collection_attributes = ['skillName', 'skillsTodo', 'stepType']

    for colatt in collection_attributes:
        data[colatt] = data[colatt].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)

    # get ratios
    ## marksEarned and marksTotal
    data['marksRatio'] = data['marksEarned'] / data['marksTotal']

    # transform dictionaries
    def safe_eval(val):
        if pd.isna(val):
            return []
        try:
            # Always work with string
            s = str(val)

            # Normalize all variants of nan
            s = re.sub(r"\bnan\b", "None", s, flags=re.IGNORECASE)

            # Parse safely
            parsed = ast.literal_eval(s)

            # Function to flatten nested lists
            def flatten(lst):
                out = []
                for x in lst:
                    if isinstance(x, list):
                        out.extend(flatten(x))
                    elif x is not None:
                        out.append(x)
                return out

            if isinstance(parsed, list):
                return flatten(parsed)
            return parsed
        except Exception as e:
            print("Parse error:", e, "on", val)
            return []
    
    data["errors"] = data["errors"].apply(safe_eval)
    data["interactionDerivation"] = data["interactionDerivation"].apply(safe_eval)
    data["result.tags"] = data["result.tags"].apply(safe_eval)

    ## error Description and Types
    error_descs, error_types = [], []

    for i in range(len(data)):
        if len(data.iloc[i]['errors']) == 0:
            error_descs.append([])
            error_types.append([])
        else:
            row_desc, row_type = [], []
            for j in range(len(data['errors'].iloc[i])):
                row_desc.append( data['errors'].iloc[i][j]['id'] )
                row_type += data['errors'].iloc[i][j]['type']
        
            error_descs.append(row_desc)
            error_types.append(row_type)

    data['error_descriptions'] = error_descs
    data['error_types'] = error_types

    ## result tags: positive and negative
    posTag = []
    negTag = []

    for i in range(len(data)):
        if len(data.iloc[i]['result.tags']) == 0:
            posTag.append([])
            negTag.append([])
        else:
            rowPos, rowNeg = [], []
            for j in range(len(data['result.tags'].iloc[i])):
                if data['result.tags'].iloc[i][j]['weight'] == 100:
                    rowPos.append(data['result.tags'].iloc[i][j]['id'])
                elif data['result.tags'].iloc[i][j]['weight'] == -100:
                    rowNeg.append(data['result.tags'].iloc[i][j]['id'])

            posTag.append(rowPos)
            negTag.append(rowNeg)

    data['positiveResultTags'] = posTag
    data['negativeResultTags'] = negTag

    # get counts
    ## stepType
    counts = data["stepType"].apply(lambda x: Counter(x) if isinstance(x, list) else Counter())
    expanded = pd.DataFrame(list(counts)).fillna(0).astype(int)
    expanded = expanded.rename(columns=lambda c: f"step_{c}_count")
    data = pd.concat([data, expanded], axis=1)

    ## errorDescription
    counts = data["error_descriptions"].apply(lambda x: Counter(x) if isinstance(x, list) else Counter())
    expanded = pd.DataFrame(list(counts)).fillna(0).astype(int)
    expanded = expanded.rename(columns=lambda c: f"errorDesc_{c}_count")
    data = pd.concat([data, expanded], axis=1)

    ## errorType
    counts = data["error_types"].apply(lambda x: Counter(x) if isinstance(x, list) else Counter())
    expanded = pd.DataFrame(list(counts)).fillna(0).astype(int)
    expanded = expanded.rename(columns=lambda c: f"errorTypes_{c}_count")
    data = pd.concat([data, expanded], axis=1)

    ## derivation steps
    data['interactionStepsNeeded'] = data['interactionDerivation'].apply(lambda x: len(x))

    return data


def transform_jsons(data_path='Data/private_data/sessionInfo'):
    library_dict = open_library(data_path)
    df_library = exercise_dataframes(library_dict)

    #df_library = additional_columns(df_library)

    df_library.to_csv("algebrakit_firstbatch_2.csv", index=False)