import json
import os
import re
import ast
import pandas as pd
import numpy as np

# def transform_jsons(data_path='Data/private_data/sessionInfo'):
#     library_dict = open_library(data_path)
#     df_library = exercise_dataframe(library_dict)

#     #df_library = additional_columns(df_library)

#     df_library.to_csv("algebrakit_firstbatch_2.csv", index=False)

def prepare_data():

    def anonymize_names(df):
        mapping = {}

        i = 0
        for name in list(df['studentName'].unique()):
            if 'unknown' not in name:
                mapping[name] = 'student' + str(i)
                i += 1
            else:
                continue

        df['studentName'] = df['studentName'].replace(mapping)

        return df

    df = pd.read_csv('algebrakit_practice.csv')
    df = df.drop(['maxAttempts', 'usedAttempts', 'failed', 'solution'], axis=1)
    df = anonymize_names(df)
    df['representative_index'] = range(len(df))

    df_exnams = pd.read_excel("Data/public_algebrakit/Copy of AK-Practice - Exercises.xlsx", 'Exercise Names')
    df_exnams = df_exnams.rename({'Exercise ID                                                                                                             ': 'ExerciseID'}, axis=1)

    our_exs = set(df['exerciseID'].unique())
    their_exs = set(df_exnams['ExerciseID'].unique())
    overlaps = our_exs.intersection(their_exs)
    df_interesting = df_exnams[df_exnams['ExerciseID'].isin(our_exs)]

    df = clean_data_algebrakit(unfilterd_data=df, filter_type="remove_interaction")
    
    first_hint = []

    for row in range(len(df)):
        if list(df.iloc[row]['event_types'])[0] == 'HINT':
            first_hint.append(True)
        else:
            first_hint.append(False)

    df['context_hint'] = first_hint

    subs = []
    items = []

    for i in range(len(df)):
        exID = df.iloc[i]['exerciseID']
        df_inter = df_interesting[ df_interesting['ExerciseID'] == exID]
        
        subs.append(list(df_inter['Subject'])[0].replace("│   ", ""))
        items.append(list(df_inter['Item Name'])[0])

    df['primarySubject'] = subs
    df['secondarySubject'] = items



    df_onehot = df.copy()
    collection_attr = ['event_types', 'event_evaluations', 'stepTypes']

    for attr in collection_attr:

        df_attr = df_onehot[[attr]]

        # Step 2: One-hot encoding with empty list handling
        attr_onehot = pd.crosstab(df_attr[attr].explode().index,
                    df_attr[attr].explode()).add_prefix(f"{attr}_")
            
        # Ensure rows with empty lists are handled
        df_attr_onehot = df_attr.drop(attr, axis=1).join(attr_onehot, how='left').fillna(0).astype(int)

        #df_onehot = df_onehot.drop(attr, axis=1)
        df_onehot = pd.concat([df_onehot, df_attr_onehot], axis=1)

    df_onehot.to_csv("algebrakit_practice_anonymized.csv", index=False)

def open_file(eID: str, iID: str, sID: str, data_path = 'Data/public_algebrakit/sessionInfo'):
    """ 
    Opens the JSON file of one session of an exercise.

    INPUT PARAMETERS
    * eID: Unique Exercise ID in string format.
    * sID: Unique Session ID in string format.
    * data_path: Directory path where the data is stored.

    OUTPUT PARAMETERS
    * data: the opened JSON file in str-dict format.
    """

    with open(f'{data_path}/{eID}/{iID}/{sID}.json', 'r') as file:
        data = json.load(file)

    return data

def open_exercise_sessions(eID: str, data_path = 'Data/public_algebrakit/sessionInfo'):
    """
    Opens the JSON files of all sessions for one exercise. 
    
    INPUT PARAMETERS
    * eID: Unique Exercise ID in string format. 
    * data_path: Directory path where the data is stored.
    
    OUTPUT PARAMETERS
    * exercise_dict: Dictionary with the data of a session stored per session key.
    """
    exercise_dict = {}

    # eIDs = []
    # iIDs = []
    # sIDs = []

    interactions = os.listdir(f'{data_path}/{eID}')

    for iID in interactions:

        sessions = os.listdir(f'{data_path}/{eID}/{iID}')
        sessions = [sID.replace(".json", "") for sID in sessions]

        for sID in sessions:
            data_sID = open_file(eID, iID, sID, data_path)
            exercise_dict[sID] = data_sID
            # iIDs.append(iID)
            # sIDs.append(sID)
            # eIDs.append(eID)


    return exercise_dict #, eIDs, iIDs, sIDs   

def open_library(data_path = 'Data/public_algebrakit/sessionInfo'):
    """
    Opens the JSON files of all sessions of all exercises (library) and stores them into one long dictionary.
    
    INPUT PARAMETERS
    * data_path: Directory path where the data is stored.
    
    OUTPUT PARAMETERS
    * library_dict: Dictionary with the data of all sessions stored per session per exercise.
    """

    # df = pd.DataFrame()

    # eIDs = []
    # iIDs = []
    # sIDs = []

    library_dict = {}

    exercises = os.listdir(f'{data_path}')

    for eID in exercises:
        #exercise_dict, eIDs_temp, iIDs_temp, sIDs_temp = open_exercise_sessions_AKpractice(eID, data_path)
        exercise_dict = open_exercise_sessions(eID, data_path)
        library_dict[eID] = exercise_dict
    #     eIDs.extend(eIDs_temp)
    #     iIDs.extend(iIDs_temp)
    #     sIDs.extend(sIDs_temp)
    
    # print(len(eIDs), len(iIDs), len(sIDs))
    # print("start on dataframe")
    # df['exericseID'] = eIDs
    # df['interactionID'] = iIDs
    # df['sessionID'] = sIDs

    return library_dict #, df 

def transform_jsons(data_path='Data/public_algebrakit/sessionInfo'):
    library_dict = open_library(data_path)
    print(f"start with dataframe")
    df_library = exercise_dataframe(library_dict)

    print(f"get arrangements")
    students = []
    df_arrangements = pd.read_excel('Data/public_algebrakit/Copy of AK Practice - Arrangements.xlsx', 'Results')[['StudentName', 'SessionId']]

    print(f"Start with student name matching")
    unknown_counter = 0
    for i in range(len(df_library)):

        if i % 1000 == 0:
            print(f"we are at {i} / {len(df_library)}")

        sessionID = df_library.iloc[i]['sessionID']
        if sessionID in list(df_arrangements['SessionId']):
            name = list(df_arrangements[df_arrangements['SessionId'] == sessionID ]['StudentName'])[0]
        else:
            name = 'unknown' + str(unknown_counter)
            unknown_counter += 1
        
        students.append(name)
        
    df_library['studentName'] = students

    #df_library = additional_columns(df_library)

    df_library.to_csv("algebrakit_practice.csv", index=False)



def clean_data_algebrakit(unfilterd_data=None, filter_type=None):

    # transform strings of lists back into lists
    collection_attributes = ['skills', 'stepTypes', 'event_types', 'event_evaluations', 'positive_skills', 'negative_skills']

    for colatt in collection_attributes:
        unfilterd_data[colatt] = unfilterd_data[colatt].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)


    # if a student has not tried one exercise, remove student session from data.
    if filter_type == "remove_session":
        invalid_sessions = []

        for i in range(len(unfilterd_data)):
            
            if len( unfilterd_data.iloc[i]['event_types'] ) == 0:
                invalid_sessions.append( unfilterd_data.iloc[i]['sessionID'])


        filtered_data = unfilterd_data [~unfilterd_data['sessionID'].isin(invalid_sessions)] #omit all information on sessions that have at least one empty event flow (unserious students?)

        filtered_data = filtered_data.reset_index().drop(['index'], axis=1)
    
    # remove the interaction and If all other failed are False, then finished = True
    elif filter_type == "remove_interaction":

        df_clean_list = []

        for sesh in list( unfilterd_data['sessionID'].unique()):
            df_sesh = unfilterd_data[ unfilterd_data['sessionID'] == sesh ].copy()
            
            invalid_indices = df_sesh.index[df_sesh['event_types'].apply(lambda x: x == [])].tolist()
            
            if not(invalid_indices): #no action needed
                df_clean_list.append(df_sesh)
                continue

            df_sesh = df_sesh.drop(invalid_indices)
                
            if True in list(df_sesh['failed']):
                df_clean_list.append(df_sesh)
                continue #finished does not change
            else:
                df_sesh.loc[:, 'finished'] = True
                df_clean_list.append(df_sesh)
            
        filtered_data = pd.concat(df_clean_list, ignore_index=True)  

    else:
        return "invalid filter type"

    return filtered_data
    
# ================== OPEN ALL FILES AS ONE DICTIONARY =================== #
# def open_file(eID: str, sID: str, data_path = 'Data/private_data/sessionInfo'):
#     """ 
#     Opens the JSON file of one session of an exercise.

#     INPUT PARAMETERS
#     * eID: Unique Exercise ID in string format.
#     * sID: Unique Session ID in string format.
#     * data_path: Directory path where the data is stored.

#     OUTPUT PARAMETERS
#     * data: the opened JSON file in str-dict format.
#     """

#     with open(f'{data_path}/{eID}/{sID}.json', 'r') as file:
#         data = json.load(file)

#     return data


# def open_exercise_sessions(eID: str, data_path = 'Data/private_data/sessionInfo'):
#     """
#     Opens the JSON files of all sessions for one exercise. 
    
#     INPUT PARAMETERS
#     * eID: Unique Exercise ID in string format. 
#     * data_path: Directory path where the data is stored.
    
#     OUTPUT PARAMETERS
#     * exercise_dict: Dictionary with the data of a session stored per session key.
#     """
#     exercise_dict = {}

#     sessions = os.listdir(f'{data_path}/{eID}')
#     sessions = [sID.replace(".json", "") for sID in sessions] # removing .json

#     for sID in sessions:
#         data_sID = open_file(eID, sID, data_path)
#         exercise_dict[sID] = data_sID

#     return exercise_dict


# def open_library(data_path = 'Data/private_data/sessionInfo'):
#     """
#     Opens the JSON files of all sessions of all exercises (library) and stores them into one long dictionary.
    
#     INPUT PARAMETERS
#     * data_path: Directory path where the data is stored.
    
#     OUTPUT PARAMETERS
#     * library_dict: Dictionary with the data of all sessions stored per session per exercise.
#     """
#     library_dict = {}

#     exercises = os.listdir(f'{data_path}')

#     for eID in exercises:
#         exercise_dict = open_exercise_sessions(eID, data_path)
#         library_dict[eID] = exercise_dict

#     return library_dict


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
    eNR = 0
    for ex in unique_exercises:
        eNR += 1
        print(f"started on exercise {eNR} of {len(unique_exercises)}")
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
    # items['content'] = [s.replace('$', '') for s in items['content']]
    # if 'solution' not in items.keys():
    #     print(items)
    # items['solution'] = [s.replace('$', '') for s in items['solution']]
    items.drop(['items'], axis=1, inplace=True) #derivation is too complex
    if 'derivation' in items.columns:
        items.drop(['derivation'], axis=1, inplace=True) #derivation is too complex
    

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
            if 'weight' in t.keys():
                neg.append(t['id'])
            else:
                pos.append(t['id'])
            
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