#-------------------------------------------------------------------------------------------------------#
# Copyright (c) 2023 by <Company/Name>                                                                  #
#                                                                                                       #
# Licensed under the MIT License                                                                        #
#                                                                                                       #
#-------------------------------------------------------------------------------------------------------#
"""
Overview
The create_admin.py file is responsible for creating an administrative user for a Flask web application.
This script interacts with the Flask application and the database to securely create a new admin user if one does not already exist. It prompts for the admin's email and password,
hashes the password for security, and saves the new admin user to the database.

Content overview
Imports:
Imports necessary modules and components such as generate_password_hash from werkzeug.security,
app and db from the application package, and the User model.

"""

from app import db

# Temporary reference to the database instance. This isn't actively used here.
db_temp = db

# SQLAlchemy model representing a user in the database.
class User(db.Model):
    # Unique identifier for each user, auto-incremented integer.
    id = db.Column(db.Integer, primary_key=True)

    # Email address of the user. It must be unique and cannot be null.
    email = db.Column(db.String(150), unique=True, nullable=False)

    # Hashed password for the user. This cannot be null.
    password = db.Column(db.String(150), nullable=False)

    # Boolean flag to indicate if the user is an admin. Defaults to False.
    is_admin = db.Column(db.Boolean, default=False)
