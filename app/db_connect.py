#-------------------------------------------------------------------------------------------------------#
# Copyright (c) 2023 by <Company/Name>                                                                  #
#                                                                                                       #
# Licensed under the MIT License                                                                        #
#                                                                                                       #
#-------------------------------------------------------------------------------------------------------#

"""

db_connect.py
Description:
Handles database connections and operations. This module abstracts database interactions, providing functions to connect to the database and perform CRUD operations.

Content Overview:
Database Connection: Functions to establish and manage database connections.
CRUD Operations: Functions to create, read, update, and delete database records.

"""



import mysql.connector
from mysql.connector import errorcode
from .config import config, registration_table

def get_db_connection():
    """
    Establishes and returns a connection to the MySQL database using the configuration provided.

    Returns:
    - conn (MySQLConnection or None): The MySQL database connection object if the connection is successful; 
      otherwise, returns None.

    This function attempts to connect to the MySQL database with the specified configuration. If the connection
    fails, it handles common errors by printing appropriate messages.

    Raises:
    - Logs any MySQL errors encountered during the connection attempt.
    """
    try:
        conn = mysql.connector.connect(**config)
        return conn
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("Error: Something is wrong with the user name or password")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print("Error: Database does not exist")
        else:
            print(f"Error: {err}")
        return None


def create_table_if_not_exists():
    """
    Creates the `callbot_event_registration` table in the MySQL database if it does not already exist.

    The table includes columns for event details such as event ID, name, location, summary, date, time,
    attendees, and the insertion timestamp.

    This function establishes a connection to the MySQL database and creates the table using SQL `CREATE TABLE IF NOT EXISTS`.
    If the connection cannot be established, an error message is printed.

    Raises:
    - Logs any SQL errors encountered during table creation.
    """
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS {registration_table} (
                eventID INT AUTO_INCREMENT PRIMARY KEY,
                eventName VARCHAR(250) NOT NULL UNIQUE,
                eventLocation VARCHAR(250) NOT NULL,
                eventSummary VARCHAR(500) NOT NULL,
                eventDate VARCHAR(50) NOT NULL,
                eventTime VARCHAR(50) NOT NULL,
                attendees TEXT NOT NULL,
                insert_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        cursor.close()
        conn.close()
    else:
        print("Error: Could not establish a connection to the database")