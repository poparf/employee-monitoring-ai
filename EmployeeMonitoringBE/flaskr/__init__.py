from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv
import os


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    cors = CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)
    load_dotenv()
    app.config.from_mapping(
        DATABASE_URL = os.getenv("DATABASE_URL"),
        SECRET_KEY = os.getenv("SECRET_KEY"),
        JWT_SECRET = os.getenv("JWT_SECRET"),
        GENERAL_DATABASE_URL = os.getenv("GENERAL_DATABASE_URL"),
        USERS_DATABASE_URL = os.getenv("USERS_DATABASE_URL"),
        # Folder settings
        PROFILE_PICTURES_PATH = os.path.join(app.instance_path, 'assets/profile_pictures'),
        MASK_ZONES_PATH = os.path.join(app.instance_path, 'assets/mask_zones'),
        ALLOWED_EXTENSIONS = ['png', 'jpg', 'jpeg']
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

if __name__ == "__main__":
    create_app().run(debug=True, threaded=True)