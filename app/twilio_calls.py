#-------------------------------------------------------------------------------------------------------#
# Copyright (c) 2023 by <Company/Name>                                                                  #
#                                                                                                       #
# Licensed under the MIT License                                                                        #
#                                                                                                       #
#-------------------------------------------------------------------------------------------------------#

"""

twilio_calls.py
Description:
Handles interactions with the Twilio API for making phone calls. This module abstracts the complexity of the Twilio API and provides functions to make calls to attendees.

Content Overview:
API Integration: Functions to interact with Twilio's API.
Call Functionality: Initiates calls, handles responses, and logs results.

"""



from . import client, blob_service_client
# from .utils import get_current_csv_blob_name
from datetime import datetime
import urllib.parse
import logging
import uuid
from twilio.twiml.voice_response import VoiceResponse, Gather
from .config import account_sid, auth_token, connect_str, container_name,ngrok_url,twilio_number
# from .blob_operations import append_to_blob, write_csv_header
from .blob_operations import write_csv_header, append_to_blob

# Set up logging
logging.basicConfig(level=logging.DEBUG)

call_guid_map = {}


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




def make_call(attendee_phonenumber, attendee_name, event_name, event_summary, event_date, event_venue, call_type, event_id, eventTime):
    """
    Initiates a phone call using Twilio's API to notify an attendee about an event.

    This function generates a unique identifier for the call, constructs the appropriate URL 
    based on the call type (initial or reminder), and makes the call using Twilio's API. 
    It logs the call details to a CSV file and handles any exceptions that occur during the process.

    Args:
        attendee_phonenumber (str): The phone number of the attendee to call.
        attendee_name (str): The name of the attendee.
        event_name (str): The name of the event.
        event_summary (str): A brief summary of the event.
        event_date (str): The date of the event.
        event_venue (str): The venue of the event.
        call_type (str): The type of call (either 'initial' or 'reminder').
        event_id (str): The unique identifier for the event.
        eventTime (str): The time of the event.

    Returns:
        str: A message indicating the result of the call initiation.
    """
    try:
        guid = str(uuid.uuid4())  # Generate a new GUID for this call
        base_url = f'{ngrok_url}/'
        if call_type == 'initial':
            url = base_url + 'voice'
        elif call_type == 'reminder':
            url = base_url + 'reminder'
        else:
            return "Invalid call type."

        # Encode query parameters
        query_params = {
            'name': attendee_name,
            'event': event_name,
            'summary': event_summary,
            'date': event_date,
            'venue': event_venue,
            'eventId': event_id,
            'eventTime': eventTime,
            'attendee_phonenumber': attendee_phonenumber
        }
        encoded_params = urllib.parse.urlencode(query_params)
        full_url = f"{url}?{encoded_params}"
        print('full_url',full_url)
        status_callback_url = f'{base_url}/status'
        print('status_callback_url',status_callback_url)
        # Make the call
        call = client.calls.create(
            to=attendee_phonenumber,
            from_=twilio_number,
            url=full_url,
            status_callback=status_callback_url,
            status_callback_event=['initiated', 'ringing', 'answered', 'completed'],
            status_callback_method='POST',
            method='POST'
        )

        # Store the GUID in the dictionary
        call_guid_map[call.sid] = guid

        # Log the initial call to the CSV
        csv_blob_name = get_current_csv_blob_name()
        write_csv_header(csv_blob_name)
        data = f"{guid},{event_id},{datetime.now().strftime('%Y-%m-%d %H:%M:%S')},{twilio_number},{attendee_phonenumber},initiated,,{attendee_name},{event_date},{event_name},{event_summary},{eventTime},{event_venue},{call_type}\n"
        append_to_blob(csv_blob_name, data)

        # Run the blob update script (if needed)
        # subprocess.run(['python', 'blob_update.py'])

        return f"Call initiated. Call SID: {call.sid}"

    except Exception as e:
        logging.error(f"Error in make_call: {e}")
        return "An error occurred while making the call."