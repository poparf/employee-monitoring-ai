from functools import wraps
from flaskr.entities.auth_db.Role import Role
from flaskr.db import get_users_db
from flaskr.middlewares.AuthMiddleware import auth_required

def permission_required(permission_name):
    def decorator(f):
        @auth_required
        @wraps(f)
        def decorated_function(current_user, *args, **kwargs):
            db = get_users_db()
            role_names = [role.name for role in current_user.roles]
            roles = db.query(Role).filter(Role.name.in_(role_names)).all()
            for role in roles:
                for permission in role.permissions:
                    if permission.name == permission_name:
                        return f(current_user, *args, **kwargs)
            return {
                "message": "Unauthorized"
            }, 401

        return decorated_function
    return decorator
