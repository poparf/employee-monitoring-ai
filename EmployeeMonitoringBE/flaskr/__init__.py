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
        PROFILE_PICTURES_PATH = os.path.join(app.root_path, 'static\\profile_pictures'),
        MASK_ZONES_PATH = os.path.join(app.root_path, 'static\\mask_zones'),
        ALLOWED_EXTENSIONS = ['png', 'jpg', 'jpeg']
    )

    from flaskr.db import init_app
    init_app(app)

    from flaskr.routes import register_blueprints
    register_blueprints(app)

    # from flaskr.init_auth_db import init_auth_db
    # with app.app_context():
        
    #     init_auth_db(app)


    return app

if __name__ == "__main__":
    create_app().run(debug=True, threaded=True)