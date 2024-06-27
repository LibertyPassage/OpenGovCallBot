#-------------------------------------------------------------------------------------------------------#
# Copyright (c) 2023 by <Company/Name>                                                                  #
#                                                                                                       #
# Licensed under the MIT License                                                                        #
#                                                                                                       #
#-------------------------------------------------------------------------------------------------------#

"""
db_update.py
The db_update.py script automates the process of updating a MySQL database with call status information stored in Azure Blob Storage. 
This script retrieves data from a specified Azure Blob, processes the data, and updates the corresponding entries in the MySQL database

Content Overview:
Blob retrive:This script retrieves data from a specified Azure Blob, processes the data.
DB table updates: Updates the corresponding entries in the MySQL database

DB tables which are getting updated:

DEV tables to handle the buckets
1. table1 = `callbot_response_callback`;
2. table2 = `callbot_response_accepted`;
3. table3 = `callbot_response_accepted_pickupdrop`;
4. table4 = `callbot_response_parking_coupon`;
5. table5 = `callbot_response_invalidoptioninput`;
6. table6 = `callbot_response_noanswer`;
7. table7 = `callbot_reminder_status`;
8. table8 =  `callbot_response_callback_status`;

PROD tables to handle the buckets
1. table1="callbot_response_callback_PROD"
2. table2="callbot_response_accepted_PROD"
3. table3="callbot_response_accepted_pickupdrop_PROD"
4. table4="callbot_response_parking_coupon_PROD"
5. table5="callbot_response_invalidoptioninput_PROD"
6. table6="callbot_response_noanswer_PROD"
7. table7="callbot_reminder_status_PROD"
8. table8="callbot_response_callback_status_PROD";

"""

import pandas as pd
import logging
from azure.storage.blob import BlobServiceClient
import mysql.connector
from mysql.connector import errorcode
from io import StringIO
import warnings
from datetime import datetime
import sys
from .config import table1, table2, table3, table4, table5, table6, table7, table8, config, connect_str, container_name

# Suppress warnings
warnings.filterwarnings("ignore")

# Initialize the BlobServiceClient
blob_service_client = BlobServiceClient.from_connection_string(connect_str)

#-------------------------------------------------------------------------------------------------------
# Utility Functions
#-------------------------------------------------------------------------------------------------------

def get_current_csv_blob_name():
    """
    Generates the blob name for the current date's CSV file.
    """
    date_str = datetime.now().strftime('%d_%m_%Y')
    file_name = f'call_status_{date_str}.csv'
    return file_name

blob_name = get_current_csv_blob_name()

# Get database connection
def get_db_connection():
    """
    Establishes and returns a connection to the MySQL database.
    """
    try:
        return mysql.connector.connect(**config)
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("Error: Something is wrong with the user name or password")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print("Error: Database does not exist")
        else:
            print(f"Error: {err}")
        return None

conn = get_db_connection()

# Create table if it does not exist
def create_table_if_not_exists(conn, table_name):
    """
    Creates a table with the specified name if it does not already exist in the database.
    """
    cursor = conn.cursor()
    cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS {table_name} (
            callbackID INT AUTO_INCREMENT PRIMARY KEY,
            GUID VARCHAR(36),
            Timestamp DATETIME,
            Twilio_Number VARCHAR(50),
            Recipient_Number VARCHAR(50),
            Call_Status VARCHAR(50),
            Response TEXT,
            Attendee_Name VARCHAR(250),
            Event_Date DATETIME,
            Event_Name VARCHAR(500),
            Event_Venue VARCHAR(500),
            Call_Type VARCHAR(50),
            Event_ID INT,
            Event_Summary TEXT,
            Event_Time TIME
        )
    ''')
    conn.commit()
    cursor.close()

# Function to check if table exists
def check_table_exists(conn, table_name):
    """
    Checks if a table with the specified name exists in the database.
    """
    query = """
    SELECT COUNT(*)
    FROM information_schema.tables 
    WHERE table_schema = %s 
    AND table_name = %s
    """
    cursor = conn.cursor()
    cursor.execute(query, (config['database'], table_name))
    result = cursor.fetchone()[0]
    cursor.close()
    return result > 0

def get_db_df(conn,table_name,lst):
    """
    Retrieves a DataFrame from the database for the specified table, filtered by a list of GUIDs.
    """

    if check_table_exists(conn, table_name):
            # Write a query to fetch the data
            query= f"SELECT * FROM {table_name}"

            # Load data into a pandas DataFrame
            df = pd.read_sql(query, conn)
            # Display the DataFrame            
            column_values = df['GUID'].tolist()
            set1=set(lst)
            set2=set(column_values)
            if len(column_values)>0:
                diff=list(set1-set2)
            else:
                diff=list(set1)

            return(diff)
    else:
            return(lst)


def create_df(lst, df, string):
    """
    Creates a DataFrame by filtering the input DataFrame for the specified list of GUIDs and default response.
    """
    all_results = pd.DataFrame()
    for value in lst:
        Result = df.loc[(df['GUID'] == value) & (df['Attendee Name'].notna())].copy()
        Result['Response'].fillna(string, inplace=True)
        all_results = pd.concat([all_results, Result])
    all_results.reset_index(drop=True, inplace=True)
    return all_results

# Download CSV file from Azure Blob Storage
def download_blob_to_df():
    """
    Downloads the CSV file from Azure Blob Storage and processes it into multiple DataFrames.
    """
    blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)
    download_stream = blob_client.download_blob()
    csv_data = download_stream.content_as_text()
    
    df = pd.read_csv(StringIO(csv_data))
    
    if len(df) < 2:
        sys.exit()  # Exit if the DataFrame is empty or has insufficient data
    
    value_Callback = df.loc[df['Response'] == 'Request Callback', 'GUID'].values
    accepted_lst = get_db_df(conn, table_name=table1, lst=value_Callback)
    Result_Callback = create_df(lst=accepted_lst, df=df, string='Request Callback')
    
    value_accepted = df.loc[df['Response'] == 'Invite Accepted', 'GUID'].values
    accepted_lst = get_db_df(conn, table_name=table2, lst=value_accepted)
    Result_accepted = create_df(lst=accepted_lst, df=df, string='Invite Accepted')

    value_pickup_accepted = df.loc[df['Response'] == 'Pickup and Drop Accepted', 'GUID']
    accepted_lst = get_db_df(conn, table_name=table3, lst=value_pickup_accepted)
    Result_pickup_accepted = create_df(lst=accepted_lst, df=df, string='Pickup and Drop Accepted')
    
    value_pickup_declined = df.loc[df['Response'] == 'parking coupon', 'GUID'].values
    accepted_lst = get_db_df(conn, table_name=table4, lst=value_pickup_declined)
    Result_pickup_declinded = create_df(lst=accepted_lst, df=df, string='parking coupon')

    value_invalidoptioninput = df.loc[df['Response'] == 'Invalid option', 'GUID'].values
    accepted_lst = get_db_df(conn, table_name=table5, lst=value_invalidoptioninput)
    Result_invalidoptioninput = create_df(lst=accepted_lst, df=df, string='Invalid option')

    value_NoAnswer = df.loc[df['Call Status'].isin(['no-answer', 'busy']), 'GUID'].values
    accepted_lst = get_db_df(conn, table_name=table6, lst=value_NoAnswer)
    Result_NoAnswer = create_df(lst=accepted_lst, df=df, string='no-answer')

    value_reminder = df.loc[df['Call Type'] == 'reminder', 'GUID'].values
    accepted_lst = get_db_df(conn, table_name=table7, lst=value_reminder)
    Result_reminder = create_df(lst=accepted_lst, df=df, string='reminder')

    value_callback_status = df.loc[df['Call Type'] == 'callback', 'GUID'].values
    accepted_lst = get_db_df(conn, table_name=table8, lst=value_callback_status)
    Result_callback_status = create_df(lst=accepted_lst, df=df, string='callback')
    
    return {
        table1: Result_Callback,
        table2: Result_accepted,
        table3: Result_pickup_accepted,
        table4: Result_pickup_declinded,
        table5: Result_invalidoptioninput,
        table6: Result_NoAnswer,
        table7: Result_reminder,
        table8: Result_callback_status
    }

def delete_confirmed_attendees():
    try:
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT GUID FROM {table8}")
            GUID_callback_confirmed = set(cursor.fetchall())

            cursor.execute(f"SELECT GUID FROM {table2}")
            GUID_accepted = set(cursor.fetchall())
            
            common_elements = list(GUID_accepted.intersection(GUID_callback_confirmed))
            
            for element in common_elements:
                cursor.execute(f"DELETE FROM {table1} WHERE GUID = %s",element)
            
            cursor.close()
            conn.close()
    except Exception as e:
        logging.error(f'Error occurred: {str(e)}')

# Insert data into the table
def insert_data_to_table(conn, df, table_name):
    """
    Inserts the data from the DataFrame into the specified table in the database.
    """
    cursor = conn.cursor()
    insert_query = f'''
        INSERT INTO {table_name} (GUID, Event_ID, Timestamp, Twilio_Number, Recipient_Number, Call_Status, Response, Attendee_Name, Event_Date, Event_Name, Event_Summary, Event_Time, Event_Venue, Call_Type)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    '''
    data = [tuple(None if pd.isna(x) else x for x in row) for row in df.itertuples(index=False)]
    cursor.executemany(insert_query, data)
    conn.commit()
    cursor.close()
    # print("db data insertion is successfull")

def check_blob_exists(container_name, blob_name):
    """
    Checks if a blob with the specified name exists in the Azure Blob Storage container.
    """
    container_client = blob_service_client.get_container_client(container_name)
    blob_list = container_client.list_blobs()
    for blob in blob_list:
        if blob.name == blob_name:
            return True
    return False

#-------------------------------------------------------------------------------------------------------
# Main Function
#-------------------------------------------------------------------------------------------------------

def main():
    """
    Main function that checks for the existence of the blob and processes it if available.
    """
    blob_exists = check_blob_exists(container_name, blob_name)
    if blob_exists:
        submain()
    else:
        return "blob is not available"

def submain():
    """
    Sub-function that processes the downloaded blob data and updates the database.
    """
    dfs = download_blob_to_df()  # Download and process data into multiple DataFrames
    conn = get_db_connection()
    # print("Here in blob_update submain func")
    if conn:
        try:
            for table_name, df in dfs.items():
                create_table_if_not_exists(conn, table_name)  # Ensure the table exists
                insert_data_to_table(conn, df, table_name)  # Insert each DataFrame into its corresponding table
        finally:
            conn.close()
    else:
        print("Error: Could not establish a connection to the database")