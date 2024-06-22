#-------------------------------------------------------------------------------------------------------#
# Copyright (c) 2023 by <Company/Name>                                                                  #
#                                                                                                       #
# Licensed under the MIT License                                                                        #
#                                                                                                       #
#-------------------------------------------------------------------------------------------------------#
"""

routes.py
Description:
Defines the HTTP routes/endpoints for your Flask application. Routes direct requests to specific view functions which handle the request and return responses.

Content Overview:
Endpoint Definitions: Maps URLs to view functions.
Route Handling: Processes GET, POST, and other HTTP methods.

"""
from flask import render_template, jsonify, request
from . import app
from .views import reminder_view, index_view, get_events_view, save_event_view, trigger_initial_call_view, trigger_reminder_call_view, voice_view, gather_view, gather2_view, gather3_view, status_view

@app.route('/')
def index():
    return index_view()

@app.route('/get_events', methods=['GET'])
def get_events():
    return get_events_view()

@app.route('/save_event', methods=['POST'])
def save_event():
    return save_event_view()

@app.route('/trigger_initial_call', methods=['POST'])
def trigger_initial_call():
    return trigger_initial_call_view()

@app.route('/trigger_reminder_call', methods=['POST'])
def trigger_reminder_call():
    return trigger_reminder_call_view()

@app.route("/voice", methods=['GET', 'POST'])
def voice():
    return voice_view()

@app.route("/gather", methods=['GET', 'POST'])
def gather():
    return gather_view()

@app.route("/gather2", methods=['GET', 'POST'])
def gather2():
    return gather2_view()

@app.route("/gather3", methods=['GET', 'POST'])
def gather3():
    return gather3_view()

@app.route("/status", methods=['POST'])
def status():
    return status_view()

@app.route("/reminder", methods=['GET', 'POST'])
def reminder():
    return reminder_view()