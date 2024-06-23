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
from app import app
from app.views import home_view, login_view, signup_view, logout_view, admin_view, reminder_view, index_view, get_events_view, save_event_view, trigger_initial_call_view, trigger_reminder_call_view, voice_view, gather_view, gather2_view, gather3_view, status_view,create_admin_user_view,add_user_view, edit_user_view, delete_user_view
from app.utils import login_required

@app.route('/login', methods=['GET', 'POST'])
def login():
    return login_view()

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    return signup_view()

@app.route('/logout')
def logout():
    return logout_view()

@app.route('/admin')
@login_required
def admin():
    return admin_view()

@app.route('/')
@login_required
def index():
    return index_view()

@app.route('/get_events', methods=['GET'])
@login_required
def get_events():
    return get_events_view()

@app.route('/save_event', methods=['POST'])
@login_required
def save_event():
    return save_event_view()

@app.route('/trigger_initial_call', methods=['POST'])
# @login_required
def trigger_initial_call():
    return trigger_initial_call_view()

@app.route('/trigger_reminder_call', methods=['POST'])
# @login_required
def trigger_reminder_call():
    return trigger_reminder_call_view()

@app.route("/voice", methods=['GET', 'POST'])
# @login_required
def voice():
    return voice_view()

@app.route("/gather", methods=['GET', 'POST'])
# @login_required
def gather():
    return gather_view()

@app.route("/gather2", methods=['GET', 'POST'])
# @login_required
def gather2():
    return gather2_view()

@app.route("/gather3", methods=['GET', 'POST'])
# @login_required
def gather3():
    return gather3_view()

@app.route("/status", methods=['POST'])
# @login_required
def status():
    return status_view()

@app.route("/reminder", methods=['GET', 'POST'])
# @login_required
def reminder():
    return reminder_view()



@app.route('/create_admin_user', methods=['GET', 'POST'])
def create_admin_user():
    return create_admin_user_view()

@app.route('/add_user', methods=['POST'])
@login_required
def add_user():
    return add_user_view()

@app.route('/edit_user/<int:user_id>', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    return edit_user_view(user_id)

@app.route('/delete_user/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    return delete_user_view(user_id)