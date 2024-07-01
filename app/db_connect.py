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
    Alters the table to add the `eventIndustry` column if it does not already exist.

    The table includes columns for event details such as event ID, name, location, summary, date, time,
    attendees, industry, and the insertion timestamp.

    This function establishes a connection to the MySQL database and creates/alters the table using SQL.
    If the connection cannot be established, an error message is printed.

    Raises:
    - Logs any SQL errors encountered during table creation.
    """
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS {registration_table} (
                eventID INT AUTO_INCREMENT PRIMARY KEY UNIQUE,
                eventName VARCHAR(500) NOT NULL,
                eventLocation VARCHAR(500) NOT NULL,
                eventSummary TEXT NOT NULL,
                eventDate VARCHAR(50) NOT NULL,
                eventTime VARCHAR(50) NOT NULL,
                eventIndustry VARCHAR(500) NOT NULL,
                attendees TEXT NOT NULL,
                insert_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()

        # Check if the column 'eventIndustry' exists
        # cursor.execute(f"SHOW COLUMNS FROM {registration_table} LIKE 'eventIndustry'")
        # result = cursor.fetchone()
        # if not result:
        #     cursor.execute(f"ALTER TABLE {registration_table} ADD COLUMN eventIndustry VARCHAR(500) NOT NULL")
        #     conn.commit()

        cursor.close()
        conn.close()
    else:
        print("Error: Could not establish a connection to the database")


def check_table_exists(cursor, table_name):
    """
    connects to db and find out the table name.
    returns: boolen to understand existance of the registration_table i.e. callbot_event_registration

    """
    cursor.execute("""
        SELECT COUNT(*)
        FROM information_schema.tables
        WHERE table_schema = %s
        AND table_name = %s
    """, (config['database'], table_name))
    return cursor.fetchall()[0] == 1

# logic to create the first table if not exist in connected db
conn = get_db_connection()
cursor = conn.cursor(dictionary=True)

if not check_table_exists(cursor, registration_table):
    create_table_if_not_exists()
else:
    print(f"Table {registration_table} already exists.")
