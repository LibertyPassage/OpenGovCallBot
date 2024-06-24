#-------------------------------------------------------------------------------------------------------#
# Copyright (c) 2023 by <Company/Name>                                                                  #
#                                                                                                       #
# Licensed under the MIT License                                                                        #
#                                                                                                       #
#-------------------------------------------------------------------------------------------------------#

"""
utils.py
Description:
Contains utility functions that are shared across various parts of the application. These functions typically perform tasks that are used by multiple other modules.

Content Overview:
Helper Functions: Common functions that provide reusable functionality.
Validation: Functions for data validation and formatting.
File Handling: Functions for file processing and conversion.
"""

from datetime import datetime
import threading
from werkzeug.utils import secure_filename
import logging
from flask import request
from .blob_operations import write_csv_header
from .twilio_calls import call_guid_map
import csv
from .config import twilio_number
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient
import io
from functools import wraps
from flask import session, redirect, url_for

# Define CSV file path and lock
csv_lock = threading.Lock()

# Azure Blob Storage configurations
AZURE_CONNECTION_STRING = 'your_connection_string'
AZURE_CONTAINER_NAME = 'your_container_name'


def login_required(f):
    """
    Decorator to ensure that a user is logged in before accessing a route.
    
    Args:
        f (function): The view function that requires login.
        
    Returns:
        function: A decorated function that checks for user login status.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        """
        Wrapper function that checks if the user is logged in.
        
        If the 'email' key is not in the session (i.e., the user is not logged in),
        it redirects the user to the login page. Otherwise, it proceeds with the 
        execution of the wrapped view function.
        
        Args:
            *args: Positional arguments passed to the view function.
            **kwargs: Keyword arguments passed to the view function.
        
        Returns:
            function: The result of the original view function if the user is logged in,
                      otherwise a redirect to the login page.
        """
        # Check if the user is logged in by verifying the presence of 'email' in the session.
        if 'email' not in session:
            # If the user is not logged in, redirect to the login page.
            return redirect(url_for('login'))
        
        # If the user is logged in, proceed with the execution of the original view function.
        return f(*args, **kwargs)
    
    # Return the wrapper function, effectively applying the decorator.
    return decorated_function

# blob / csv file name
def get_current_csv_blob_name():
    """
    Generates the blob name for the CSV file based on the current date.

    Returns:
    - str: The name of the CSV file, formatted as 'call_status_DD_MM_YYYY.csv', 
      where 'DD', 'MM', and 'YYYY' are the current day, month, and year respectively.

    This function creates a file name that includes the current date, ensuring that each day's data
    is stored in a separate CSV file in Azure Blob Storage.
    """
    date_str = datetime.now().strftime('%d_%m_%Y')
    file_name = f'call_status_{date_str}.csv'
    return file_name

def upload_blob(file_name, data):
    """
    Uploads the given data to Azure Blob Storage.

    Args:
        file_name (str): The name of the blob file.
        data (str): The data to be uploaded.

    Returns:
        None
    """
    try:
        blob_service_client = BlobServiceClient.from_connection_string(AZURE_CONNECTION_STRING)
        blob_client = blob_service_client.get_blob_client(container=AZURE_CONTAINER_NAME, blob=file_name)
        blob_client.upload_blob(data, blob_type="AppendBlob")
    except Exception as e:
        logging.error(f"Error uploading blob: {e}")

def log_response(response):
    """
    Logs the given response and appends it to a CSV file in Azure Blob Storage with relevant details.

    This function retrieves the call SID and event ID from the request, maps the call SID to a GUID,
    and logs the response details into a CSV file stored in Azure Blob Storage. It ensures thread-safe
    access to the CSV file using a lock. The logged details include the GUID, event ID, timestamp, Twilio
    number, recipient number, status, and the response message.

    Args:
        response (str): The response message to log.

    Returns:
        None
    """
    try:
        # Retrieve the current timestamp
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # Get the current timestamp
        
        # Retrieve call SID and event ID from the request
        call_sid = request.values.get('CallSid')  # Extract CallSid from the request
        event_id = request.values.get('eventId')  # Extract eventId from the request
        
        # Retrieve the GUID associated with the call SID
        guid = call_guid_map.get(call_sid)  # Lookup the GUID for the given CallSid
        
        # Get the current CSV file path and ensure the CSV header is written if necessary
        csv_file_name = get_current_csv_blob_name()  # Get the name of the current CSV blob
        # write_csv_header function needs to be modified to handle the header in blob storage

        # Create CSV content
        csv_content = io.StringIO()
        writer = csv.writer(csv_content)
        writer.writerow([
            guid, event_id, timestamp, twilio_number, request.values.get('To'), 'In Progress', response
        ])
        
        # Upload CSV content to Azure Blob Storage
        with csv_lock:  # Ensure thread-safe access to the CSV file
            upload_blob(csv_file_name, csv_content.getvalue())
        
        # Log the written CSV entry for auditing
        logging.info(
            f"Written to CSV: GUID: {guid}, Event ID: {event_id}, Timestamp: {timestamp}, "
            f"Twilio Number: {twilio_number}, To: {request.values.get('To')}, Status: 'In Progress', Response: {response}"
        )
    except Exception as e:
        logging.error(f"Error in log_response: {e}")
