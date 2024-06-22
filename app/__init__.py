#-------------------------------------------------------------------------------------------------------#
# Copyright (c) 2023 by <Company/Name>                                                                  #
#                                                                                                       #
# Licensed under the MIT License                                                                        #
#                                                                                                       #
#-------------------------------------------------------------------------------------------------------#
"""
__init__.py
Description:
The __init__.py file is crucial for making Python treat a directory as a package. This file is executed when the package is imported and typically contains initialization code for the package.

Content Overview:
Application Factory: Creates and configures the Flask application.
Blueprints: Registers Blueprints which organize routes and views.
Configuration Loading: Loads configuration settings from config.py.
Database Initialization: Sets up the database connection.

"""
from flask import Flask
import logging
from twilio.rest import Client
from azure.storage.blob import BlobServiceClient
from .config import account_sid, auth_token, connect_str, container_name

app = Flask(__name__)
logging.basicConfig(level=logging.DEBUG)
client = Client(account_sid, auth_token)
blob_service_client = BlobServiceClient.from_connection_string(connect_str)

from . import routes  # Import routes here to avoid circular imports