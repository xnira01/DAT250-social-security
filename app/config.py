"""Provides the configuration for the Social Insecurity application.

This file is used to set the configuration for the application.

Example:
    from flask import Flask
    from app.config import Config

    app = Flask(__name__)
    app.config.from_object(Config)

    # Use the configuration
    secret_key = app.config["SECRET_KEY"]
"""

import os


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or " Group2f91349b2d25fab62228eb7feaaa9dba9f4909b74c2f569e2cf37038ff78fc9e"  # TODO: Use this with wtforms
    SQLITE3_DATABASE_PATH = "sqlite3.db"  # Path relative to the Flask instance folder
    UPLOADS_FOLDER_PATH = "uploads"  # Path relative to the Flask instance folder
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}  # TODO: Might use this at some point, probably don't want people to upload any file type
    WTF_CSRF_ENABLED = False  # TODO: I should probably implement this wtforms feature, but it's not a priority
