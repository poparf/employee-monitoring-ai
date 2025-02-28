from flask import Blueprint, request, jsonify
from flaskr.db import get_db
from flaskr.entities.User import User

bp = Blueprint("users", __name__, url_prefix="/users")

@bp.route("/", methods=["GET"])
def get_all_users():
    db = get_db()
    users = db.query(User).all()
    return jsonify([{"id": user.id, "username": user.username, "email": user.email} for user in users])

@bp.route("/<int:id>", methods=["GET"])
def get_user(id):
    db = get_db()
    user = db.query(User).filter(User.id == id).first()
    if user is None:
        return jsonify({"error": "User not found"}), 404
    return jsonify({"id": user.id, "username": user.username, "email": user.email})

# More routes for CRUD operations