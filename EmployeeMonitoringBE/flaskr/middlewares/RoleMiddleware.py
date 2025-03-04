import jwt
from functools import wraps
from flask import request, abort, g
from flask import current_app as app
from flaskr.db import get_db
from flaskr.entities.auth_db.User import User


def role_required(role_name):
    def decorator(f):
        @wraps(f)
        def decorated_function(current_user, *args, **kwargs):
            if role_name in current_user.roles:
                return f(current_user, *args, **kwargs)
            else:
                return {
                    "message": "Unauthorized"
                }, 401
        return decorated_function
    return decorator

