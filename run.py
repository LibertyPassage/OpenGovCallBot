#-------------------------------------------------------------------------------------------------------#
# Copyright (c) 2023 by <Company/Name>                                                                  #
#                                                                                                       #
# Licensed under the MIT License                                                                        #
#                                                                                                       #
#-------------------------------------------------------------------------------------------------------#

"""
run.py
Description:
The entry point of the Flask application. This script starts the Flask development server and initializes the app.

Content Overview:
Application Initialization: Creates the app instance using the factory function.
Server Launch: Runs the Flask server, typically in development mode.

Summary
Each file in your project serves a specific purpose, from defining routes and views to handling database interactions and scheduling tasks. Here’s a brief summary:

__init__.py: Initializes the Flask app and configures settings.
routes.py: Defines HTTP routes and maps them to view functions.
views.py: Contains logic for handling requests and rendering responses.
utils.py: Provides utility functions for various tasks.
twilio_calls.py: Manages interactions with the Twilio API for phone calls.
blob_operations.py: Handles operations with Azure Blob Storage.
scheduler.py: Schedules and runs periodic tasks.
db.py: Manages database connections and operations.
config.py: Stores configuration settings for the app.
run.py: Launches the Flask application server.


"""

from app import app

if __name__ == '__main__':
    app.run(debug=True)
    # app.run(port=8000)


