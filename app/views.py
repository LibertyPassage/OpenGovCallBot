#-------------------------------------------------------------------------------------------------------#
# Copyright (c) 2023 by <Company/Name>                                                                  #
#                                                                                                       #
# Licensed under the MIT License                                                                        #
#                                                                                                       #
#-------------------------------------------------------------------------------------------------------#
"""

views.py
Description:
Contains the view functions that correspond to the routes defined in routes.py. Each view function handles the request, processes any necessary data, and returns an appropriate response.

Content Overview:
Request Handling: Processes data from HTTP requests.
Database Interaction: Queries or updates the database.
Response Generation: Returns HTML templates or JSON responses.

"""

import re
import logging
from flask import flash, redirect, request, Response, jsonify, render_template, session, url_for

from app.models import User
from .db_connect import get_db_connection, create_table_if_not_exists
from .twilio_calls import make_call,call_guid_map
from .utils import secure_filename, log_response
import pandas as pd
from .utils import get_current_csv_blob_name, log_response
from .blob_operations import write_csv_header, append_to_blob
from twilio.twiml.voice_response import VoiceResponse, Gather
from datetime import datetime
from .config import twilio_number, voice_change, registration_table
from .db_update import main
from werkzeug.security import generate_password_hash, check_password_hash
from app.models import User,db_temp
import logging

logging.basicConfig(level=logging.INFO)



# Set up logging
logging.basicConfig(level=logging.DEBUG)

# Initialize table flag
table_initialized = True

def index_view():
    """
    Renders the main HTML page and fetches events from the database.

    This function checks if the database table has been initialized and if not,
    it creates the table. It then fetches the list of events from the database 
    and passes them to the HTML template to be rendered.

    Returns:
        The rendered HTML template with the list of events.
    """
    global table_initialized
    if not table_initialized:
        create_table_if_not_exists()
        table_initialized = True

    # Fetch events from the database
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(f"SELECT eventID, eventName, eventLocation, eventDate FROM {registration_table}")
        events = cursor.fetchall()
        cursor.close()
        conn.close()
    else:
        events = []

    return render_template('callbotUI_V6.html', events=events)



def get_events_view():
    """
    API endpoint to get the list of events.

    This function fetches the list of events from the database and returns them 
    as a JSON response.

    Returns:
        JSON response containing the list of events.
    """
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(f"SELECT eventID, eventName, eventLocation, eventDate FROM {registration_table}")
        events = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify({"events": events})
        # return render_template('callbotUI_V6.html', events=events)
    else:
        return jsonify({"events": []})
        # return render_template('callbotUI_V6.html', events=events)


# @app.route('/save_event', methods=['POST'])
def save_event_view():
    """
    Saves event details into the database.

    This function saves the event details provided in the request form into the database.
    It performs input validation, checks for duplicate event names, and processes the 
    attendees file to extract attendee information.

    Returns:
        Renders the callbotUI_V6.html with appropriate status and messages.
    """
    try:
        event_name = request.form.get('eventName')
        event_location = request.form.get('eventLocation')
        event_summary = request.form.get('eventSummary')
        event_date = request.form.get('eventDate')
        event_time = request.form.get('eventTime')
        attendees_file = request.files.get('attendeesFile')

        # Replace commas with periods in event_summary
        if event_summary:
            event_summary = event_summary.replace(',', '.').replace("'", '')

        if event_location:
            event_location = event_location.replace("'", '')

        if event_name:
            event_name = event_name.replace("'", '')

        # Restrict commas in event_name and event_location
        if ',' in event_name:
            return jsonify(status='error', message='Event Name must not contain commas.')
        if ',' in event_location:
            return jsonify(status='error', message='Event Location must not contain commas.')

        # Input validation
        if not event_name:
            return jsonify(status='error', message='Event name is a mandatory field.')
        if not event_location:
            return jsonify(status='error', message='Event location is a mandatory field.')
        if not event_summary:
            return jsonify(status='error', message='Event summary is a mandatory field.')
        if not event_date:
            return jsonify(status='error', message='Event date is a mandatory field.')
        if not event_time:
            return jsonify(status='error', message='Event time is a mandatory field.')
        if not attendees_file:
            return jsonify(status='error', message='Attendees file is a mandatory field.')

        if len(event_name) > 500:
            return jsonify(status='error', message='Event Name must not exceed 250 characters.')
        if len(event_location) > 250:
            return jsonify(status='error', message='Event Location must not exceed 250 characters.')

        conn = get_db_connection()
        cursor = conn.cursor()

        # Check for duplicate event name
        cursor.execute("SELECT COUNT(*) FROM callbot_event_registration WHERE eventName = %s", (event_name,))
        if cursor.fetchone()[0] > 0:
            cursor.close()
            conn.close()
            return jsonify(status='error', message='Event Name already exists.')

        attendees = []
        if attendees_file:
            file_extension = secure_filename(attendees_file.filename).split('.')[-1].lower()
            logging.info(f'File extension: {file_extension}')
            if file_extension == 'xlsx':
                df = pd.read_excel(attendees_file, engine='openpyxl')
            elif file_extension == 'csv':
                df = pd.read_csv(attendees_file)
            else:
                return jsonify(status='error', message='Unsupported file format. Please upload a .csv or .xlsx file.')

            attendees = df.to_dict('records')

        attendees_data = ';'.join([f"{attendee['attendeeName']}:{attendee['attendeePhone']}" for attendee in attendees])
        # logging.info(f'Attendees data: {attendees_data}')

        cursor.execute(
            "INSERT INTO callbot_event_registration (eventName, eventLocation, eventSummary, eventDate, eventTime, attendees) VALUES (%s, %s, %s, %s, %s, %s)",
            (event_name, event_location, event_summary, event_date, event_time, attendees_data)
        )
        conn.commit()
        event_id = cursor.lastrowid

        cursor.close()
        conn.close()

        return jsonify(status='success', message='Event saved successfully', event_id=event_id)

    except KeyError as e:
        logging.error(f'Missing form field: {e.args[0]}')
        return jsonify(status='error', message=f'Missing form field: {e.args[0]}')
    except Exception as e:
        logging.error(f'Error occurred: {str(e)}')
        return jsonify(status='error', message='An error occurred while saving the event. Please try again.')
    
def is_valid_singapore_mobile(number):
    """
    Check if the given number is a valid Singapore mobile number.
    A valid Singapore mobile number starts with '65' followed by 8 digits.

    Args:
    number (str): The mobile number to validate.

    Returns:
    bool: True if the number is valid, False otherwise.
    """
    pattern = r'^65\d{8}$'
    return bool(re.match(pattern, str(number)))

# @app.route('/trigger_initial_call', methods=['POST'])
def trigger_initial_call_view():
    """
    Triggers the initial call to attendees of a specific event.

    This function retrieves event details and attendee information from the database using the event ID
    provided in the request. It then makes a call to each attendee with the event details using the 
    `make_call` function.

    Returns:
        JSON response with appropriate status and messages.
    """
    try:
        event_id = request.form['event_id']
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            
            # Retrieve event details from the database
            cursor.execute(f"SELECT * FROM {registration_table} WHERE eventID = %s", (event_id,))
            event = cursor.fetchone()

            if event:
                # Parse attendees from the event details
                attendees = event[6].split(';')
                attendees = [{'attendeeName': a.split(':')[0], 'attendeePhone': a.split(':')[1]} for a in attendees]

                event_details = {
                    'eventName': event[1],
                    'eventSummary': event[3],
                    'eventLocation': event[2],
                    'eventDate': event[4],
                    'eventTime': event[5],
                    'attendees': attendees,
                    'event_id': event_id
                }

                # Convert the attendees list to a DataFrame
                df_attendees = pd.DataFrame(attendees)

                # Loop over each attendee and make the call
                for idx, row in df_attendees.iterrows():
                    make_call(
                        attendee_phonenumber=row["attendeePhone"],
                        attendee_name=row["attendeeName"],
                        event_date=event_details.get('eventDate'),
                        event_name=event_details.get('eventName'),
                        event_summary=event_details.get('eventSummary'),
                        event_venue=event_details.get('eventLocation'),
                        eventTime=event_details.get('eventTime'),
                        call_type="initial",
                        event_id=event_details.get('event_id')
                    )

                cursor.close()
                conn.close()

                return jsonify(status='success', message='Initial call triggered successfully')
            else:
                cursor.close()
                conn.close()
                return jsonify(status='error', message='Event not found')
        else:
            return jsonify(status='error', message='Could not establish a connection to the database')
    except Exception as e:
        logging.error(f'Error occurred: {str(e)}')
        return jsonify(status='error', message='An error occurred while triggering the initial call. Please try again.')

# @app.route('/trigger_reminder_call', methods=['POST'])
from flask import request, jsonify
import pandas as pd
import logging

logging.basicConfig(level=logging.INFO)

def trigger_reminder_call_view():
    """
    Triggers reminder calls for attendees who have accepted the initial call invitation.

    This function retrieves the list of attendees who accepted the initial call invitation for a specific event
    from the database. It then makes a reminder call to each attendee with the event details using the 
    `make_call` function.

    Returns:
        JSON response indicating the status of the operation.
    """
    try:
        event_id = request.form['event_id']
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            
            # Retrieve attendees who accepted the initial call from the database
            cursor.execute("SELECT * FROM callbot_response_accepted WHERE Event_ID = %s", (event_id,))
            results = cursor.fetchall()
            column_names = [desc[0] for desc in cursor.description]  # Get column names from cursor description
            
            cursor.close()
            conn.close()
            
            if results:
                # Create DataFrame and clean it to remove duplicate recipient numbers
                df = pd.DataFrame(results, columns=column_names)
                df_cleaned = df.drop_duplicates(subset=['Recipient_Number'])
                df_cleaned['Event_Time'] = df_cleaned['Event_Time'].astype(str).apply(lambda x: x.split(" ")[-1])

                # Loop over each attendee and make the reminder call
                for idx, row in df_cleaned.iterrows():
                    make_call(
                        attendee_phonenumber=row["Recipient_Number"],
                        attendee_name=row["Attendee_Name"],
                        event_name=row["Event_Name"],
                        event_summary=row["Event_Summary"],
                        event_date=row["Event_Date"],
                        event_venue=row["Event_Venue"],
                        call_type='reminder',
                        event_id=row["Event_ID"],
                        eventTime=row["Event_Time"]
                    )
                
                return jsonify(status='success', message='Reminder call triggered successfully')
            else:
                return jsonify(status='error', message='No attendees found for this event')
        else:
            return jsonify(status='error', message='Could not establish a connection to the database')
    except Exception as e:
        logging.error(f'Error occurred: {str(e)}')
        return jsonify(status='error', message='An error occurred while triggering the reminder call. Please try again.')


def voice_view():
    """
    Handles the Twilio voice response for initial event invitations.

    This function processes the request from Twilio, gathers necessary event and attendee 
    information from query parameters, and initiates a Twilio voice response that provides 
    details about the event and prompts the attendee to accept the invitation or request a callback.

    Returns:
        str: The Twilio VoiceResponse object as a string.
    """
    try:
        attendee_name = request.args.get('name', 'Attendee')
        event_name = request.args.get('event', 'Event')
        event_summary = request.args.get('summary', 'Summary')
        event_date = request.args.get('date', 'the scheduled date')
        event_venue = request.args.get('venue', 'the designated venue')
        event_id = request.args.get('eventId', 'eventId')
        eventTime = request.args.get('eventTime', 'eventTime')
        attendee_phonenumber = request.args.get('attendee_phonenumber', 'attendee_phonenumber')
        first_name = attendee_name.split()[0]
        call_sid = request.values.get('CallSid')
        guid = call_guid_map.get(call_sid)
        resp = VoiceResponse()
        gather = Gather(action='/gather', num_digits=1)
        gather.say(
            f"Hello {first_name}, This is the Open GOV Bot calling on behalf of the organizing committee for an event. We are delighted to invite you to our upcoming event, {event_name}! Taking place on {event_date} at {eventTime} Malaysia Standard Time. This event promises to be an insightful experience held at {event_venue}. Here�s a brief overview: {event_summary}. We believe your presence will add immense value, and we would be honored to have you with us. To confirm your attendance, please press 1. If you need a callback for more details, press 2.",
            voice=voice_change
        )

        csv_blob_name = get_current_csv_blob_name()
        write_csv_header(csv_blob_name)
        data = f"{guid},{event_id},{datetime.now().strftime('%Y-%m-%d %H:%M:%S')},{twilio_number},{attendee_phonenumber},initiated,InVoice,,{event_date},{event_name},{event_summary},{eventTime},{event_venue},\n"
        append_to_blob(csv_blob_name, data)

        resp.append(gather)
        return str(resp)
    except Exception as e:
        logging.error(f"Error in /voice: {e}")
        return str(VoiceResponse().say("An application error occurred.", voice=voice_change))

def gather_view():
    """
    Handles the response from the call recipient and initiates further actions based on the response.

    This function processes the digit input from the call recipient, prompts further questions, and logs the
    responses to a CSV file. It offers options to accept the invitation or request a callback, and handles invalid inputs.

    Returns:
        str: The Twilio VoiceResponse object as a string.
    """
    attendee_name = request.args.get('name', 'Attendee')
    event_name = request.args.get('event', 'Event')
    event_summary = request.args.get('summary', 'Summary')
    event_date = request.args.get('date', 'the scheduled date')
    event_venue = request.args.get('venue', 'the designated venue')
    event_id = request.args.get('eventId', 'eventId')
    event_time = request.args.get('eventTime', 'eventTime')
    attendee_phonenumber = request.args.get('attendee_phonenumber', 'attendee_phonenumber')
    first_name = attendee_name.split()[0]

    try:
        digit = request.values.get('Digits')
        resp = VoiceResponse()
        call_sid = request.values.get('CallSid')
        guid = call_guid_map.get(call_sid)

        if digit == '1':
            gather = Gather(action='/gather2', num_digits=1)
            gather.say(
                "Thank you for accepting the invitation. Would you like to utilize our pickup and drop-off service for this event? If yes, press 1. If no, press 2.",
                voice=voice_change
            )
            resp.append(gather)

            csv_blob_name = get_current_csv_blob_name()
            write_csv_header(csv_blob_name)
            data = f"{guid},{event_id},{datetime.now().strftime('%Y-%m-%d %H:%M:%S')},{twilio_number},{attendee_phonenumber},initiated,Invite Accepted,,{event_date},{event_name},{event_summary},{event_time},{event_venue},\n"
            append_to_blob(csv_blob_name, data)

            log_response('Invite Accepted')
        elif digit == '2':
            resp.say(
                "You have requested a callback. We will reach out to you later. Thank you and Good day.",
                voice=voice_change
            )

            csv_blob_name = get_current_csv_blob_name()
            write_csv_header(csv_blob_name)
            data = f"{guid},{event_id},{datetime.now().strftime('%Y-%m-%d %H:%M:%S')},{twilio_number},{attendee_phonenumber},initiated,Request Callback,,{event_date},{event_name},{event_summary},{event_time},{event_venue},\n"
            append_to_blob(csv_blob_name, data)

            log_response('Request Callback')
        else:
            resp.say("You did not press a valid option.", voice=voice_change)

            csv_blob_name = get_current_csv_blob_name()
            write_csv_header(csv_blob_name)
            data = f"{guid},{event_id},{datetime.now().strftime('%Y-%m-%d %H:%M:%S')},{twilio_number},{attendee_phonenumber},initiated,Invalid option,,{event_date},{event_name},{event_summary},{event_time},{event_venue},\n"
            append_to_blob(csv_blob_name, data)

        return str(resp)
    except Exception as e:
        logging.error(f"Error in /gather: {e}")
        return str(VoiceResponse().say("An application error occurred.", voice=voice_change))


def gather2_view():
    """
    Handles the next response from the call recipient regarding pickup and drop-off service.

    This function processes the digit input to determine if the recipient wants to use the pickup and drop-off service,
    and prompts for further details if accepted. It logs the responses to a CSV file.

    Returns:
        str: The Twilio VoiceResponse object as a string.
    """
    attendee_name = request.args.get('name', 'Attendee')
    event_name = request.args.get('event', 'Event')
    event_summary = request.args.get('summary', 'Summary')
    event_date = request.args.get('date', 'the scheduled date')
    event_venue = request.args.get('venue', 'the designated venue')
    event_id = request.args.get('eventId', 'eventId')
    event_time = request.args.get('eventTime', 'eventTime')
    attendee_phonenumber = request.args.get('attendee_phonenumber', 'attendee_phonenumber')
    first_name = attendee_name.split()[0]

    try:
        digit = request.values.get('Digits')
        resp = VoiceResponse()
        call_sid = request.values.get('CallSid')
        guid = call_guid_map.get(call_sid)

        if digit == '1':
            gather = Gather(action='/gather3', num_digits=1)
            gather.say(
                "To arrange the pickup and drop-off service, please specify your preferred address. For office address, press 1. For home address, press 2.",
                voice=voice_change
            )
            resp.append(gather)

            csv_blob_name = get_current_csv_blob_name()
            write_csv_header(csv_blob_name)
            data = f"{guid},{event_id},{datetime.now().strftime('%Y-%m-%d %H:%M:%S')},{twilio_number},{attendee_phonenumber},initiated,Pickup and Drop Accepted,,{event_date},{event_name},{event_summary},{event_time},{event_venue},\n"
            append_to_blob(csv_blob_name, data)

            log_response('Pickup and Drop Accepted')
        elif digit == '2':
            resp.say(
                "You have declined the pickup and drop-off service. Thank you & Good day.",
                voice=voice_change
            )

            csv_blob_name = get_current_csv_blob_name()
            write_csv_header(csv_blob_name)
            data = f"{guid},{event_id},{datetime.now().strftime('%Y-%m-%d %H:%M:%S')},{twilio_number},{attendee_phonenumber},initiated,Pickup and Drop Declined,,{event_date},{event_name},{event_summary},{event_time},{event_venue},\n"
            append_to_blob(csv_blob_name, data)

            log_response('Pickup and Drop Declined')
        else:
            resp.say("You did not press a valid option.", voice=voice_change)

            csv_blob_name = get_current_csv_blob_name()
            write_csv_header(csv_blob_name)
            data = f"{guid},{event_id},{datetime.now().strftime('%Y-%m-%d %H:%M:%S')},{twilio_number},{attendee_phonenumber},initiated,Invalid option,,{event_date},{event_name},{event_summary},{event_time},{event_venue},\n"
            append_to_blob(csv_blob_name, data)

        return str(resp)
    except Exception as e:
        logging.error(f"Error in /gather2: {e}")
        return str(VoiceResponse().say("An application error occurred.", voice=voice_change))

def gather3_view():
    """
    Handles the final response from the call recipient regarding the preferred address for pickup and drop-off service.

    This function processes the digit input to confirm the preferred address for pickup and drop-off service,
    and logs the responses to a CSV file.

    Returns:
        str: The Twilio VoiceResponse object as a string.
    """
    attendee_name = request.args.get('name', 'Attendee')
    event_name = request.args.get('event', 'Event')
    event_summary = request.args.get('summary', 'Summary')
    event_date = request.args.get('date', 'the scheduled date')
    event_venue = request.args.get('venue', 'the designated venue')
    event_id = request.args.get('eventId', 'eventId')
    event_time = request.args.get('eventTime', 'eventTime')
    attendee_phonenumber = request.args.get('attendee_phonenumber', 'attendee_phonenumber')
    first_name = attendee_name.split()[0]

    try:
        digit = request.values.get('Digits')
        resp = VoiceResponse()
        call_sid = request.values.get('CallSid')
        guid = call_guid_map.get(call_sid)

        if digit == '1':
            resp.say(
                "You have chosen the office address for pickup and drop-off. Thank you & Good day.",
                voice=voice_change
            )

            csv_blob_name = get_current_csv_blob_name()
            write_csv_header(csv_blob_name)
            data = f"{guid},{event_id},{datetime.now().strftime('%Y-%m-%d %H:%M:%S')},{twilio_number},{attendee_phonenumber},initiated,Office Address,,{event_date},{event_name},{event_summary},{event_time},{event_venue},\n"
            append_to_blob(csv_blob_name, data)

            log_response('Office Address')
        elif digit == '2':
            resp.say(
                "You have chosen the home address for pickup and drop-off. Thank you & Good day.",
                voice=voice_change
            )

            csv_blob_name = get_current_csv_blob_name()
            write_csv_header(csv_blob_name)
            data = f"{guid},{event_id},{datetime.now().strftime('%Y-%m-%d %H:%M:%S')},{twilio_number},{attendee_phonenumber},initiated,Home Address,,{event_date},{event_name},{event_summary},{event_time},{event_venue},\n"
            append_to_blob(csv_blob_name, data)

            log_response('Home Address')
        else:
            resp.say("You did not press a valid option.", voice=voice_change)

            csv_blob_name = get_current_csv_blob_name()
            write_csv_header(csv_blob_name)
            data = f"{guid},{event_id},{datetime.now().strftime('%Y-%m-%d %H:%M:%S')},{twilio_number},{attendee_phonenumber},initiated,Invalid option,,{event_date},{event_name},{event_summary},{event_time},{event_venue},\n"
            append_to_blob(csv_blob_name, data)

        return str(resp)
    except Exception as e:
        logging.error(f"Error in /gather3: {e}")
        return str(VoiceResponse().say("An application error occurred.", voice=voice_change))

def status_view():
    """
    Handles POST requests to the /status endpoint to log and update the status of a call.

    Retrieves the call status and call SID from the request, logs this information, and maps the call SID 
    to a GUID. If the GUID is found, it logs the status update in a CSV file. If not, it returns a 404 response.
    In case of any errors during processing, it returns a 500 response.

    Returns:
        Response: HTTP response indicating the result of the operation.
    """
    try:
        # Retrieve call status and SID from the request
        call_status = request.values.get('CallStatus')  # Extract call status from the POST request
        call_sid = request.values.get('CallSid')  # Extract call SID from the POST request
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # Get the current timestamp

        # Log the received call status and SID
        logging.info(f"Call status: {call_status}, Call SID: {call_sid}")

        # Retrieve the GUID associated with the call SID
        guid = call_guid_map.get(call_sid)  # Lookup the GUID for the given call SID

        if not guid:
            # If GUID not found, log a warning and return a 404 response
            logging.warning(f"GUID not found for Call SID: {call_sid}")
            return Response(status=404, response="GUID not found.")

        # Prepare the CSV blob name and write the status update to the CSV file
        csv_blob_name = get_current_csv_blob_name()  # Get the name of the current CSV blob
        write_csv_header(csv_blob_name)  # Ensure the CSV header is written if necessary

        # Create a data string with GUID, timestamp, Twilio number, recipient number, and call status
        data = f"{guid},,{timestamp},{twilio_number},{request.values.get('To')},{call_status},\n"
        append_to_blob(csv_blob_name, data)  # Append the data string to the CSV blob

        if call_status == 'completed':
            main()
            logging.info(f"db updated successfully")

        # Return a 200 OK response indicating success
        return Response(status=200)
    except Exception as e:
        # Log any exceptions that occur and return a 500 Internal Server Error response
        logging.error(f"Error in /status: {e}")
        return Response(status=500)
    

def reminder_view():
        """
    Handles requests to send a voice reminder about an upcoming event to a specified attendee.

    Retrieves event and attendee details from the request parameters, constructs a voice message
    using Twilio's VoiceResponse, and logs the reminder details in a CSV file. If an error occurs,
    it logs the error and returns a voice response indicating an application error.

    Returns:
        str: Twilio VoiceResponse object as a string.
    """
        try:
            # Retrieve event and attendee details from the request
            attendee_name = request.args.get('name', 'Attendee')  # Attendee's name
            event_name = request.args.get('event', 'Event')  # Event name
            event_date = request.args.get('date', 'the scheduled date')  # Event date
            call_sid = request.values.get('CallSid')  # Call SID from the request
            event_time = request.args.get('eventTime', 'eventTime')  # Event time
            event_summary = request.args.get('summary', 'Summary')  # Event summary
            event_venue = request.args.get('venue', 'the designated venue')  # Event venue
            event_id = request.args.get('eventId', 'eventId')  # Event ID
            attendee_phonenumber = request.args.get('attendee_phonenumber', 'attendee_phonenumber')  # Attendee's phone number
    
            # Retrieve the GUID associated with the call SID
            guid = call_guid_map.get(call_sid)  # Lookup the GUID for the given call SID
            first_name = attendee_name.split()[0]  # Extract the first name of the attendee
    
            # Create a Twilio VoiceResponse for the reminder
            resp = VoiceResponse()
            resp.say(
                f"Hello {first_name}, as a valued registered participant, this is a reminder from the OpenGov call bot regarding the upcoming event, {event_name}. scheduled date {event_date} at {event_time} Malaysia Standard Time. To be held at {event_venue}. Thank you.",
                voice=voice_change
            )
    
            # Prepare the CSV blob name and write the reminder data to the CSV file
            csv_blob_name = get_current_csv_blob_name()  # Get the name of the current CSV blob
            write_csv_header(csv_blob_name)  # Ensure the CSV header is written if necessary
    
            # Create a data string with all event and attendee details
            data = (
                f"{guid},{event_id},{datetime.now().strftime('%Y-%m-%d %H:%M:%S')},{twilio_number},"
                f"{attendee_phonenumber},initiated,Reminder Completed,,{event_date},{event_name},"
                f"{event_summary},{event_time},{event_venue},\n"
            )
            append_to_blob(csv_blob_name, data)  # Append the data string to the CSV blob
    
            return str(resp)  # Return the Twilio VoiceResponse as a string
        except Exception as e:
            # Log any exceptions that occur and return a voice response indicating an error
            logging.error(f"Error in /reminder: {e}")
            return str(VoiceResponse().say("An application error occurred.", voice=voice_change))
    
#Login,signup and logout logic
def home_view():
    """
    View function for the home page.
    
    Renders the main user interface of the application.
    
    Returns:
        A rendered template of the 'callbotUI_V6.html' file.
    """
    return render_template('callbotUI_V6.html')

def login_view():
    """
    View function for the login page.
    
    Handles user authentication. If the request method is POST, it checks the
    user's credentials and logs them in if valid.
    
    Returns:
        - If GET: A rendered template of the 'login.html' file.
        - If POST: Redirects to the index page on successful login, or
          flashes an error message on failure.
    """
    if request.method == 'POST':
        # Retrieve email and password from the submitted form.
        email = request.form['email']
        password = request.form['password']
        
        # Query the database for the user by email.
        user = User.query.filter_by(email=email).first()
        
        # Verify the password and check if the user exists.
        if user and check_password_hash(user.password, password):
            # Store user information in the session.
            session['email'] = email
            session['is_admin'] = user.is_admin
            return redirect(url_for('index'))
        else:
            # Flash an error message for invalid credentials.
            flash('Invalid credentials. Please try again.', 'error')
    
    # Render the login page template.
    return render_template('login.html')

def signup_view():
    """
    View function for the signup page.
    
    Handles user registration. If the request method is POST, it creates a 
    new user if the email does not already exist.
    
    Returns:
        - If GET: A rendered template of the 'signup.html' file.
        - If POST: Redirects to the index page on successful registration, or
          flashes an error message if the user already exists.
    """
    if request.method == 'POST':
        # Retrieve email and password from the submitted form.
        email = request.form['email']
        password = request.form['password']
        
        # Check if the user already exists in the database.
        user = User.query.filter_by(email=email).first()
        if user:
            # Flash an error message if the user already exists.
            flash('User already exists. Please log in.', 'error')
        else:
            # Hash the password and create a new user.
            hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
            new_user = User(email=email, password=hashed_password)
            
            # Add the new user to the database and commit the transaction.
            db_temp.session.add(new_user)
            db_temp.session.commit()
            
            # Store user information in the session.
            session['email'] = email
            return redirect(url_for('index'))
    
    # Render the signup page template.
    return render_template('signup.html')

def logout_view():
    """
    View function for logging out.
    
    Removes user information from the session.
    
    Returns:
        A redirect to the login page.
    """
    # Remove 'email' from the session to log out the user.
    session.pop('email', None)
    return redirect(url_for('login'))

def admin_view():
    """
    View function for the admin page.
    
    Displays a list of all users.
    
    Returns:
        A rendered template of the 'admin.html' file with a list of users.
    """
    # Query the database for all users.
    users = User.query.all()
    return render_template('admin.html', users=users)

def create_admin_user_view():
    """
    View function for creating an admin user.
    
    Handles the creation of a new admin user. If the request method is POST,
    it creates an admin user if the email does not already exist.
    
    Returns:
        - If GET: A rendered template of the 'create_admin_user.html' file.
        - If POST: Redirects to the login page on successful creation, or
          flashes an error message if the user already exists.
    """
    if request.method == 'POST':
        # Retrieve email and password from the submitted form.
        email = request.form['email']
        password = request.form['password']
        
        # Check if the user already exists in the database.
        if not User.query.filter_by(email=email).first():
            # Hash the password and create a new admin user.
            hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
            admin_user = User(email=email, password=hashed_password, is_admin=True)
            
            # Add the new admin user to the database and commit the transaction.
            db_temp.session.add(admin_user)
            db_temp.session.commit()
            
            # Flash a success message and redirect to the login page.
            flash('Admin user created successfully', 'success')
            return redirect(url_for('login'))
        else:
            # Flash an error message if the user already exists.
            flash('User already exists', 'error')
    
    # Render the create admin user page template.
    return render_template('create_admin_user.html')

def add_user_view():
    """
    View function for adding a new user.
    
    Handles the addition of a new user. If the request method is POST,
    it creates a new user if the email does not already exist.
    
    Returns:
        A redirect to the admin page, either adding the user successfully
        or flashing an error message if the user already exists.
    """
    if request.method == 'POST':
        # Retrieve email, password, and admin status from the submitted form.
        email = request.form['email']
        password = request.form['password']
        is_admin = request.form.get('is_admin') == 'on'
        
        # Check if the user already exists in the database.
        user = User.query.filter_by(email=email).first()
        if user:
            # Flash an error message if the user already exists.
            flash('User already exists.', 'error')
        else:
            try:
                # Hash the password and create a new user.
                hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
                new_user = User(email=email, password=hashed_password, is_admin=is_admin)
                
                # Add the new user to the database and commit the transaction.
                db_temp.session.add(new_user)
                db_temp.session.commit()
                
                # Flash a success message and redirect to the admin page.
                flash('User added successfully', 'success')
                return redirect(url_for('admin'))
            except Exception as e:
                # Rollback the transaction in case of an error and flash the error message.
                db_temp.session.rollback()
                flash(f'Error: {str(e)}', 'error')
    
    # Redirect to the admin page.
    return redirect(url_for('admin'))

def edit_user_view(user_id):
    """
    View function for editing an existing user.
    
    Handles user updates. If the request method is POST, it updates the user's
    details based on the provided information.
    
    Args:
        user_id (int): The ID of the user to be edited.
        
    Returns:
        - If GET: A rendered template of the 'edit_user.html' file with the user data.
        - If POST: Redirects to the admin page on successful update, or flashes
          an error message in case of failure.
    """
    # Retrieve the user by ID.
    user = User.query.get(user_id)
    
    if request.method == 'POST':
        # Update user's email.
        user.email = request.form['email']
        
        # Update user's password if a new password is provided.
        if request.form['password']:
            user.password = generate_password_hash(request.form['password'], method='pbkdf2:sha256')
        
        # Update user's admin status.
        user.is_admin = request.form.get('is_admin') == 'on'
        
        try:
            # Commit the updates to the database.
            db_temp.session.commit()
            flash('User updated successfully', 'success')
            return redirect(url_for('admin'))
        except Exception as e:
            # Rollback the transaction in case of an error and flash the error message.
            db_temp.session.rollback()
            flash(f'Error: {str(e)}', 'error')
    
    # Render the edit user page template with the user data.
    return render_template('edit_user.html', user=user)

def delete_user_view(user_id):
    """
    View function for deleting an existing user.
    
    Handles user deletion. Deletes the user with the specified ID from the database.
    
    Args:
        user_id (int): The ID of the user to be deleted.
        
    Returns:
        A redirect to the admin page, either deleting the user successfully or
        flashing an error message in case of failure.
    """
    # Retrieve the user by ID.
    user = User.query.get(user_id)
    
    try:
        # Delete the user from the database and commit the transaction.
        db_temp.session.delete(user)
        db_temp.session.commit()
        flash('User deleted successfully', 'success')
    except Exception as e:
        # Rollback the transaction in case of an error and flash the error message.
        db_temp.session.rollback()
        flash(f'Error: {str(e)}', 'error')
    
    # Redirect to the admin page.
    return redirect(url_for('admin'))