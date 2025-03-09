from sqlalchemy import create_engine
from flaskr.entities.auth_db.AuthBaseEntity import AuthBaseEntity
from flaskr.entities.BaseEntity import Entity
from flask import current_app, g
from sqlalchemy_utils import database_exists, create_database
import threading
from sqlalchemy.orm import Session, sessionmaker, configure_mappers

# Registry stores engines and session factories
engine_registry = {}
session_factory_registry = {}
registry_lock = threading.Lock()


class RoutingSession(Session):
    def get_bind(self, mapper=None, clause=None):
        if mapper and issubclass(mapper.class_, AuthBaseEntity):
            return engine_registry["users"]
        elif mapper and issubclass(mapper.class_, Entity):
            tenant_id = g.get('tenant_id')
            if tenant_id and tenant_id in engine_registry:
                return engine_registry[tenant_id]
        else:
            print("Daca s-a ajuns aici s-a terminat...")
            return None
        
def setup_users_db(app):
    """Initialize central users database"""
    user_db_url = app.config['USERS_DATABASE_URL']
    engine = create_engine(user_db_url)
    
    if not database_exists(engine.url):
        create_database(engine.url)
    
    
    #print("dropping auth db")
    #AuthBaseEntity.metadata.drop_all(bind=engine)
    AuthBaseEntity.metadata.create_all(bind=engine)
    
    with registry_lock:
        engine_registry['users'] = engine
        session_factory_registry['users'] = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=engine,
            class_=RoutingSession
        )

def setup_tenant_db(tenant_id):
    """Dynamically create tenant database and session factory"""
    app = current_app
    base_url = app.config['GENERAL_DATABASE_URL']
    db_url = f"{base_url}/{tenant_id}"
    print(db_url)
    engine = create_engine(db_url)
    
    if not database_exists(engine.url):
        create_database(engine.url)
        print("Created database:", engine.url)
    #Create tables for tenant-specific schema
    Entity.metadata.bind = engine
    Entity.metadata.create_all(bind=engine)
    configure_mappers()
    with registry_lock:
        engine_registry[tenant_id] = engine
        session_factory_registry[tenant_id] = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=engine,
            class_=RoutingSession
        )
    app.logger.info("Tenant database created: %s", tenant_id)
    app.logger.info("Session registry: ", session_factory_registry)

def get_users_db() -> RoutingSession:
    """Get central users database session"""
    if 'users_db_session' not in g:
        g.users_db_session = session_factory_registry['users']()
    print("Get_users_db() -> session_registry: ", session_factory_registry)

    return g.users_db_session

def get_tenant_db() -> RoutingSession:
    """Get appropriate database session based on current tenant"""
    if 'tenant_db_session' not in g:
        tenant_id = g.get('tenant_id')            
        if tenant_id not in session_factory_registry:
            setup_tenant_db(tenant_id)
        
        g.tenant_db_session = session_factory_registry[tenant_id]()

    return g.tenant_db_session

def close_session(e=None):
    """Close database session at end of request"""
    session = g.pop('db_session', None)
    if session is not None:
        session.close()

def init_app(app):
    app.teardown_appcontext(close_session)
    setup_users_db(app)