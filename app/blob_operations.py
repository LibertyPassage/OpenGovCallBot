#-------------------------------------------------------------------------------------------------------#
# Copyright (c) 2023 by <Company/Name>                                                                  #
#                                                                                                       #
# Licensed under the MIT License                                                                        #
#                                                                                                       #
#-------------------------------------------------------------------------------------------------------#

"""
blob_operations.py
Description:
Provides functions to interact with Azure Blob Storage. This module handles file uploads, downloads, and other operations related to blob storage.

Content Overview:
Blob Upload/Download: Functions to upload files to and download files from Azure Blob Storage.
Blob Management: Additional functionality for managing blobs.

"""


from .config import container_name,blob_service_client
import logging
import threading

# Define CSV file path and lock
csv_lock = threading.Lock()

def write_csv_header(blob_name):
    """
    Writes a header row to a CSV file in Azure Blob Storage if the file does not already exist.

    Parameters:
    - blob_name (str): The name of the blob (file) in the Azure Blob Storage.

    This function checks if the specified CSV file exists in the Azure Blob Storage. If it does not exist,
    it writes a header row to the file. The header includes various fields related to event and call details.

    Locking is used to ensure thread safety when accessing the blob.

    Raises:
    - Logs any exceptions encountered during the process.
    """
    with csv_lock:
        try:
            blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)
            if not blob_client.exists():
                header = ['GUID','eventID', 'Timestamp', 'Twilio Number', 'Recipient Number', 'Call Status', 
                          'Response', 'Attendee Name', 'Event Date', 'Event Name','Event Summary','Event Time', 
                          'Event Venue', 'Call Type','event Industry','attendee EmailID']
                blob_client.upload_blob(','.join(header) + '\n', overwrite=True)
        except Exception as e:
            logging.error(f"Error writing CSV header: {e}")


def append_to_blob(blob_name, data):
    """
    Appends data to a blob in Azure Blob Storage. If the blob already contains data, the new data is appended.

    Parameters:
    - blob_name (str): The name of the blob (file) in the Azure Blob Storage.
    - data (str): The data to be appended to the blob.

    This function reads the existing content of the blob, appends the new data, and writes the updated content
    back to the blob. Thread safety is maintained using a lock.

    Raises:
    - Logs any exceptions encountered during the process.
    """
    with csv_lock:
        try:
            blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)
            existing_data = blob_client.download_blob().readall().decode('utf-8') if blob_client.exists() else ''
            updated_data = existing_data + data
            blob_client.upload_blob(updated_data, overwrite=True)
            logging.info(f"Data appended to Azure Blob Storage as {blob_name}.")
        except Exception as e:
            logging.error(f"Error appending to Azure Blob Storage: {e}")
