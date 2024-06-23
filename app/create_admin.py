import os
from werkzeug.security import generate_password_hash
from app import app, db
from app.models import User

def create_admin_user():
    with app.app_context():
        email = input("Enter admin email: ")
        password = input("Enter admin password: ")
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        if not User.query.filter_by(email=email).first():
            admin_user = User(email=email, password=hashed_password, is_admin=True)
            db.session.add(admin_user)
            db.session.commit()
            print("Admin user created successfully")
        else:
            print("User already exists")


