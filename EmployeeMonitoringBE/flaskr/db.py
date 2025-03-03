from sqlalchemy import create_engine
from flaskr.entities.BaseEntity import Entity
from flaskr.entities.auth_db.User import User
from flaskr.entities.auth_db.Tenant import Tenant
from flaskr.entities.auth_db.RolePermission import RolePermission
from flaskr.entities.auth_db.Role import Role
from flaskr.entities.auth_db.Permission import Permission
from flaskr.entities.auth_db.EmailCodes import EmailCodes

from flaskr.entities.auth_db.AuthBaseEntity import AuthBaseEntity
from sqlalchemy.orm import sessionmaker
from flask import current_app, g
from sqlalchemy_utils import database_exists, create_database
import threading

# Registry stores engines and session factories
engine_registry = {}
session_factory_registry = {}
registry_lock = threading.Lock()


def setup_users_db(app):
    """Initialize central users database"""
    user_db_url = app.config['USERS_DATABASE_URL']
    engine = create_engine(user_db_url)
    
    if not database_exists(engine.url):
        create_database(engine.url)
    
    AuthBaseEntity.metadata.drop_all(bind=engine)
    AuthBaseEntity.metadata.create_all(bind=engine)
    
    with registry_lock:
        engine_registry['users'] = engine
        session_factory_registry['users'] = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=engine
        )

def setup_tenant_db(tenant_id):
    """Dynamically create tenant database and session factory"""
    app = current_app
    base_url = app.config['GENERAL_DATABASE_URL']
    db_url = f"{base_url}/{tenant_id}"
    
    engine = create_engine(db_url)
    
    if not database_exists(engine.url):
        create_database(engine.url)
    
    # Create tables for tenant-specific schema
    Entity.metadata.create_all(bind=engine)
    
    with registry_lock:
        engine_registry[tenant_id] = engine
        session_factory_registry[tenant_id] = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=engine
        )

def get_db():
    """Get appropriate database session based on current tenant"""
    if 'db_session' not in g:
        tenant_id = getattr(g, 'tenant_id', None)
        
        if not tenant_id:
            g.db_session = session_factory_registry['users']()
        else:
            if tenant_id not in session_factory_registry:
                setup_tenant_db(tenant_id)
            
            g.db_session = session_factory_registry[tenant_id]()
    
    return g.db_session

def close_session(e=None):
    """Close database session at end of request"""
    session = g.pop('db_session', None)
    if session is not None:
        session.close()

def init_app(app):
    app.teardown_appcontext(close_session)
    setup_users_db(app)