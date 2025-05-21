import jwt
from functools import wraps
from flask import request, abort, g
from flask import current_app as app
from flaskr.db import get_users_db
from flaskr.entities.auth_db.User import User

def auth_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        try:
            token = None
            if "Authorization" in request.headers:
                token = request.headers["Authorization"].split(" ")[1]
            if not token:
                return {
                    "message": "Token is missing",
                }, 401
            try:
                data = jwt.decode(token, app.config["JWT_SECRET"], algorithms=["HS256"])
                db = get_users_db()
                logged_user = db.query(User).filter_by(id=data["user_id"]).first()
                if logged_user == None:
                    return {
                        "message": "Invalid token",
                    }, 401
                    
            except TimeoutError:
                return {
                    "message": "Timeout error.",
                }, 503 
            except Exception as e:
                return {
                    "message": "Something went wrong",
                    "error": e
                }, 500
            
            # Set the tenant database such that it will query that specific one
            g.tenant_id = logged_user.tenant_id
            
            return f(logged_user, *args, **kwargs)
        except TimeoutError:
                return {
                    "message": "Timeout error.",
                }, 503 
        except Exception as e:
            print(e)
            return {
                "message": "Something went wrong when checking token",
            }, 500
    return decorated