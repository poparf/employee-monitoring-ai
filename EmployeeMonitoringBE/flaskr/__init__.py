import os
from flask import Flask

def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)

    # Aici setezi env variables
    app.config.from_mapping(
        DATABASE_URL = "postgresql://postgres:Seneca123@localhost:5432/emonitoringdb",
        JWT_SECRET="ROBERTPOPA",
        SECRET_KEY="dev"
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