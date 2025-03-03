from flask import Blueprint, request, jsonify
from flaskr.middlewares.AuthMiddleware import auth_required
from flaskr.db import get_db
from flaskr.entities.Employee import Employee
from flaskr.ML.face_recognition import face_recognition_impl 
import numpy as np
from PIL import Image
import os

bp = Blueprint("employees", __name__, url_prefix="/employees")

@bp.route("/", methods=["POST"])
#@auth_required
def create_employee():
    try:
        if "profile-picture" not in request.files:
            return jsonify({"message": "No file provided"}), 400
        profile_picture = request.files["profile-picture"]
        firstName = request.form.get("firstName")
        lastName = request.form.get("lastName")
        phoneNumber = request.form.get("phoneNumber")
        role = request.form.get("role")
        department = request.form.get("department")

        # Check for null
        if not firstName:
            return jsonify({"message": "First name is required"}), 400
        if not lastName:
            return jsonify({"message": "Last name is required"}), 400
        if not phoneNumber:
            return jsonify({"message": "Phone number is required"}), 400
        if not role:
            return jsonify({"message": "Role is required"}), 400
        if not department:
            return jsonify({"message": "Department is required"}), 400


        profile_picture.save(os.path.join("flaskr/static/profile_pictures", f"{firstName}_{lastName}.png"))
        encoded_face = face_recognition_impl.encode_picture(os.path.join("flaskr/static/profile_pictures", f"{firstName}_{lastName}.png"))
        
        db = get_db()
        employee = Employee(
            firstName = firstName,
            lastName = lastName,
            phoneNumber = phoneNumber,
            role = role,
            department = department,
            encodedFace = encoded_face.tostring(),
            profilePicture = f"static/profile_pictures/{firstName}_{lastName}.png"
        )# TODO: Take into account that people might have the same name
        db.add(employee)
        db.flush()
        db.commit()
        return {"message": "Employee created successfully. Face encoded sucessfuly.",
                "employee": {
                    "id": employee.id,
                    "firstName": employee.firstName,
                    "lastName": employee.lastName,
                    "phoneNumber": employee.phoneNumber,
                    "role": employee.role,
                    "department": employee.department
                }}, 201

    except Exception as e:
        print(e)
        return jsonify({"message": "Something went wrong"}), 500

# TODO: Pagination/sorting can be implemented 
# Get all employees
@bp.route("/", methods=["GET"])
#@auth_required
def get_all_employees():
    try:
        db = get_db()
        employees = db.query(Employee).all()
        return jsonify([{
            "id": employee.id,
            "firstName": employee.firstName,
            "lastName": employee.lastName,
            "phoneNumber": employee.phoneNumber,
            "role": employee.role,
            "department": employee.department
        } for employee in employees]), 200
    except Exception as e:
        print(e)
        return jsonify({"message": "Something went wrong"}), 500
    
