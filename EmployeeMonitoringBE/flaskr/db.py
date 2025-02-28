from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from flask import current_app, g

# Import entities
from flaskr.entities.BaseEntity import Entity
from flaskr.entities import Employee
from flaskr.entities import User
from flaskr.entities import VideoCamera
from flaskr.entities import Zone
from flaskr.entities import PPE
from flaskr.entities import PPERecognition
from flaskr.entities import PersonDetected
from flaskr.entities import Alert
from flaskr.entities import AllowedList


engine = None
SessionLocal = None

def setup_db(app):
    global engine, SessionLocal
    engine = create_engine(app.config['DATABASE_URL'])
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# g este un obiect care este unic pentru fieare request
# e folosit ca conexiunea sa fie deschisa doar o data
def get_db():
    if 'db' not in g:
        g.db = SessionLocal()
    return g.db

def close_db(e = None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    global engine
    Entity.metadata.create_all(bind=engine)

def init_app(app):
    setup_db(app)
    # Register database functions with the Flask app
    app.teardown_appcontext(close_db)
    
    # flask --app flaskr init-db
    # Create a CLI command to initialize the database
    @app.cli.command('init-db')
    def init_db_command():
        init_db()
        print('Initialized the database.')