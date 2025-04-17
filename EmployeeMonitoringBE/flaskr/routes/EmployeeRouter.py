from flask import Blueprint, request, jsonify, current_app as app, send_file
from flaskr.middlewares.PermissionMiddleware import permission_required
from flaskr.middlewares.AuthMiddleware import auth_required
from flaskr.db import get_tenant_db
from flaskr.entities.Employee import Employee
from flaskr.ML.face_recognition import face_recognition_impl 
import numpy as np
import io
import os
bp = Blueprint("employees", __name__, url_prefix="/employees")

@bp.route("/", methods=["POST"])
@permission_required("CREATE_EMPLOYEE")
def create_employee(current_user):
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

        #profile_picture.save(os.path.join("flaskr/static/profile_pictures", f"{firstName}_{lastName}.png"))
        profile_picture.save(f"{app.config["PROFILE_PICTURES_PATH"]}\\{firstName}_{lastName}.png")
        encoded_face = face_recognition_impl.encode_picture(f"{app.config["PROFILE_PICTURES_PATH"]}\\{firstName}_{lastName}.png")
        db = get_tenant_db()

        byte_io = io.BytesIO()
        np.save(byte_io, encoded_face)
    

        employee = Employee(
            firstName = firstName,
            lastName = lastName,
            phoneNumber = phoneNumber,
            role = role,
            department = department,
            encodedFace = byte_io.getvalue(), # TODO: Maybe don't store the whole path of the profile picture
            profilePicture = f"{app.config["PROFILE_PICTURES_PATH"]}/{firstName}_{lastName}.png"
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
@permission_required("CREATE_EMPLOYEE")
def get_all_employees(current_user):
    try:
        db = get_tenant_db()
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

# Get employee by ID
@bp.route("/<int:employee_id>", methods=["GET"])
@permission_required("CREATE_EMPLOYEE")
def get_employee_by_id(current_user, employee_id):
    try:
        db = get_tenant_db()
        employee = db.query(Employee).filter_by(id=employee_id).first()
        
        if not employee:
            return jsonify({"message": "Employee not found"}), 404
            
        return jsonify({
            "id": employee.id,
            "firstName": employee.firstName,
            "lastName": employee.lastName,
            "phoneNumber": employee.phoneNumber,
            "role": employee.role,
            "department": employee.department,
            "profilePicture": employee.profilePicture
        }), 200
    except Exception as e:
        print(e)
        return jsonify({"message": "Something went wrong"}), 500

# Get employee profile picture
@bp.route("/<int:employee_id>/profile-picture", methods=["GET"])
@permission_required("CREATE_EMPLOYEE")
def get_employee_profile_picture(current_user, employee_id):
    try:
        db = get_tenant_db()
        employee = db.query(Employee).filter_by(id=employee_id).first()
        
        if not employee:
            return jsonify({"message": "Employee not found"}), 404
            
        if not employee.profilePicture or not os.path.exists(employee.profilePicture):
            return jsonify({"message": "Profile picture not found"}), 404
            
        # Return the image file directly
        return send_file(employee.profilePicture, mimetype='image/jpeg')
    except Exception as e:
        print(e)
        return jsonify({"message": "Something went wrong"}), 500

