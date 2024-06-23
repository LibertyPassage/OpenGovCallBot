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
from flask_sqlalchemy import SQLAlchemy


#from app.db_connect import get_db_connection

from .config import account_sid, auth_token, connect_str, container_name,config

app = Flask(__name__)
# Configuration
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# Initialize the database
db = SQLAlchemy(app)
# Import the routes and models
from app import routes, models
with app.app_context():
    db.create_all()

logging.basicConfig(level=logging.DEBUG)


#from . import routes  # Import routes here to avoid circular imports