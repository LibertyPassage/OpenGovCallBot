#-------------------------------------------------------------------------------------------------------#
# Copyright (c) 2023 by <Company/Name>                                                                  #
#                                                                                                       #
# Licensed under the MIT License                                                                        #
#                                                                                                       #
#-------------------------------------------------------------------------------------------------------#

"""
The create_admin.py script is used to create an administrator user for a Flask web application.
This script is crucial for setting up initial access to administrative functions and ensures that a secure admin user can be created directly from the command line.

The script performs the following key tasks:

Accesses the Flask Application Context:

Utilizes app.app_context() to work within the Flask application context. This is necessary to access application-specific configurations and the database session.
Prompts for Admin Credentials:

Collects an email and password from the user via the command line. These credentials are used to create the new admin account.

"""



import os
from werkzeug.security import generate_password_hash
from app import app, db
from app.models import User

def create_admin_user():
    # Access the Flask application context to work with the app's configurations and database.
    with app.app_context():
        # Prompt the user to enter an email address for the admin user.
        email = input("Enter admin email: ")

        # Prompt the user to enter a password for the admin user.
        password = input("Enter admin password: ")

        # Generate a hashed version of the provided password for security purposes.
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

        # Check if a user with the provided email already exists in the database.
        if not User.query.filter_by(email=email).first():
            # If the user does not exist, create a new User instance with the provided email and hashed password.
            # Set the is_admin flag to True, indicating that this is an admin user.
            admin_user = User(email=email, password=hashed_password, is_admin=True)

            # Add the new admin user to the database session.
            db.session.add(admin_user)

            # Commit the changes to the database to save the new admin user.
            db.session.commit()

            # Inform the user that the admin account has been successfully created.
            print("Admin user created successfully")
        else:
            # Inform the user that a user with the provided email already exists.
            print("User already exists")


