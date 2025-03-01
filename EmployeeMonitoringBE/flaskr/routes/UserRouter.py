from flask import Blueprint, request, jsonify
from flaskr.db import get_db
from flaskr.entities.User import User
from flaskr.auth import check_password, hash_password
import re

bp = Blueprint("users", __name__, url_prefix="/users")

@bp.route("/register", methods=["POST"])
def register():
    data = request.get_json()

    # Validate data existance
    if data == None:
        return jsonify({"message": "No data provided"}), 400
    
    if email not in data:
        return jsonify({"message": "Email is required"}), 400
    
    if password not in data:
        return jsonify({"message": "Password is required"}), 400
    
    if phoneNumber not in data:
        return jsonify({"message": "Phone number is required"}), 400


    # Validate email
    email = data.get("email")    
    if re.match( r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email) == None:
        return jsonify({"message": "Invalid email format"}), 400

    # Validate password
    password = data.get("password")
    if len(password) < 8:
        return jsonify({"message": "Password must be at least 8 characters long"}), 400

    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return jsonify({"message": "Password must contain at least one special character"}), 400

    if not re.search(r"\d", password):
        return jsonify({"message": "Password must contain at least one number"}), 400

    # Validate phone number
    phoneNumber = data.get("phoneNumber")
    if not re.search(r"^[0-9]{10}$", phoneNumber): # Only romanian
        return jsonify({"message": "Invalid phone number"}), 400

    # TODO: Add email verification


    db = get_db()
    hashedPassword = hash_password(password)
    user = User(email=email, password=hashedPassword, phoneNumber=phoneNumber)
    db.add(user)
    db.commit()
    return jsonify({"message": "User created sucessfuly.","user": {"id": user.id, "email": user.email}}), 201

@bp.route("/login", methods=["POST"]):
def login():
    data = request.get_json()

    # Validate data existance
    if data == None:
        return jsonify({"message": "No data provided"}), 400
    
    if email not in data:
        return jsonify({"message": "Email is required"}), 400
    
    if password not in data:
        return jsonify({"message": "Password is required"}), 400

    email = data.get("email")
    password = data.get("password")

    db = get_db()
    user = db.query(User).filter_by(email=email).first()

    if user == None and not check_password(password, user.password):
        return jsonify({"message": "Invalid email or password."}), 400

    return jsonify({"message": "Login successful", "user": {"id": user.id, "email": user.email}}), 200