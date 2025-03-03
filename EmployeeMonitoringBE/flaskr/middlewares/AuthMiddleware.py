import jwt
from functools import wraps
from flask import request, abort
from flask import current_app as app
from flaskr.db import get_db
from flaskr.entities.User import User

def auth_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if "Authorization" in request.headers:
            token = request.headers["Authorization"].split(" ")[1]
        if not token:
            return {
                "message": "Token is missing",
            }, 401
        try:
            data = jwt.decode(token, app.config["JWT_SECRET"], algorithms=["HS256"])
            db = get_db()
            # Token data contains:
            # Request header
            # Request body:
            """
            "user": {
                "id": 1,
                "email": "robertflorianp037@gmail.com",
                # Extra roles: ["admin"]
            }
            """
            logged_user = db.query(User).filter_by(id=data["user"]["id"]).first()
            if logged_user == None:
                return {
                    "message": "Invalid token",
                }, 401
        except Exception as e:
            return {
                "message": "Something went wrong",
            }, 500

        return f(logged_user, *args, **kwargs)
    return decorated