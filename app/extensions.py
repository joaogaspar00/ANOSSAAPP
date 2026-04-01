"""
extensions.py — Flask extensions

Instantiated here (without app) so blueprints can import them without
creating circular imports. The app factory (app/__init__.py) calls init_app().
"""
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from flask_wtf import CSRFProtect
from flask_migrate import Migrate

db = SQLAlchemy()
login_manager = LoginManager()
bcrypt = Bcrypt()
csrf = CSRFProtect()
migrate = Migrate()

# Redirect unauthenticated users to the login page
login_manager.login_view = "auth.login"
login_manager.login_message = "Log ind for at fortsætte."
login_manager.login_message_category = "info"
