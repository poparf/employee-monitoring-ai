from flask import Flask
from dotenv import load_dotenv
import os

def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    
    load_dotenv()
    app.config.from_mapping(
        DATABASE_URL = os.getenv("DATABASE_URL"),
        SECRET_KEY = os.getenv("SECRET_KEY"),
        JWT_SECRET = os.getenv("JWT_SECRET")
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    from flaskr.db import init_app
    init_app(app)

    # Register routes
    from flaskr.routes import register_blueprints
    register_blueprints(app)

    return app