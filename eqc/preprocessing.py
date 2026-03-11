import pandas as pd
import ast

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