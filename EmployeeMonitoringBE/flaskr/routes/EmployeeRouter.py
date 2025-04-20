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
        db = get_tenant_db()
        profile_picture = request.files.get("profile-picture") # Use .get()
        firstName = request.form.get("firstName")
        lastName = request.form.get("lastName")
        phoneNumber = request.form.get("phoneNumber")
        role = request.form.get("role")
        department = request.form.get("department")

        # Check for null
        if not firstName: return jsonify({"message": "First name is required"}), 400
        if not lastName: return jsonify({"message": "Last name is required"}), 400
        if not phoneNumber: return jsonify({"message": "Phone number is required"}), 400
        if not role: return jsonify({"message": "Role is required"}), 400
        if not department: return jsonify({"message": "Department is required"}), 400
        if not profile_picture: return jsonify({"message": "Profile picture is required"}), 400

        # Create employee first to get ID
        employee = Employee(
            firstName=firstName,
            lastName=lastName,
            phoneNumber=phoneNumber,
            role=role,
            department=department
        )
        db.add(employee)
        db.flush() # Assigns ID to employee object

        # Now save picture and encode face using the ID
        profile_picture_filename = f"{employee.id}.png"
        profile_picture_path = os.path.join(app.config["PROFILE_PICTURES_PATH"], profile_picture_filename)

        # Ensure directory exists
        os.makedirs(app.config["PROFILE_PICTURES_PATH"], exist_ok=True)

        profile_picture.save(profile_picture_path)
        encoded_face = face_recognition_impl.encode_picture(profile_picture_path)

        byte_io = io.BytesIO()
        np.save(byte_io, encoded_face)

        # Update employee with picture path and encoding
        employee.profilePicture = profile_picture_path
        employee.encodedFace = byte_io.getvalue()

        db.commit() # Commit all changes

        return {"message": "Employee created successfully. Face encoded successfully.",
                "employee": {
                    "id": employee.id,
                    "firstName": employee.firstName,
                    "lastName": employee.lastName,
                    "phoneNumber": employee.phoneNumber,
                    "role": employee.role,
                    "department": employee.department
                }}, 201

    except Exception as e:
        db.rollback() # Rollback in case of error after flush
        print(e)
        # Attempt to clean up saved file if creation failed after saving
        if 'profile_picture_path' in locals() and os.path.exists(profile_picture_path):
             try:
                 os.remove(profile_picture_path)
             except OSError as rm_err:
                 print(f"Error removing file during cleanup: {rm_err}")
        return jsonify({"message": "Something went wrong"}), 500

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

# Update employee by ID
@bp.route("/<int:employee_id>", methods=["PUT"])
@permission_required("CREATE_EMPLOYEE") # Assuming EDIT_EMPLOYEE permission exists
def update_employee(current_user, employee_id):
    try:
        db = get_tenant_db()
        employee = db.query(Employee).filter_by(id=employee_id).first()

        if not employee:
            return jsonify({"message": "Employee not found"}), 404

        # Get data from form
        firstName = request.form.get("firstName")
        lastName = request.form.get("lastName")
        phoneNumber = request.form.get("phoneNumber")
        role = request.form.get("role")
        department = request.form.get("department")
        profile_picture = request.files.get("profile-picture")

        # Update fields if provided
        if firstName: employee.firstName = firstName
        if lastName: employee.lastName = lastName
        if phoneNumber: employee.phoneNumber = phoneNumber
        if role: employee.role = role
        if department: employee.department = department

        # Handle profile picture update
        if profile_picture:
            profile_picture_filename = f"{employee.id}.png"
            profile_picture_path = os.path.join(app.config["PROFILE_PICTURES_PATH"], profile_picture_filename)

            # Ensure directory exists
            os.makedirs(app.config["PROFILE_PICTURES_PATH"], exist_ok=True)

            # Save new picture (overwrites old one if exists)
            profile_picture.save(profile_picture_path)

            # Re-encode face
            try:
                encoded_face = face_recognition_impl.encode_picture(profile_picture_path)
                byte_io = io.BytesIO()
                np.save(byte_io, encoded_face)
                employee.encodedFace = byte_io.getvalue()
                employee.profilePicture = profile_picture_path # Update path just in case
            except Exception as encode_err:
                # Handle case where encoding might fail (e.g., no face found)
                # Decide if you want to rollback the picture save or just log error
                print(f"Error encoding new profile picture: {encode_err}")
                # Optionally return an error or continue without updating encoding
                # return jsonify({"message": "Failed to process new profile picture."}), 400


        db.commit()

        return jsonify({
            "message": "Employee updated successfully",
            "employee": {
                "id": employee.id,
                "firstName": employee.firstName,
                "lastName": employee.lastName,
                "phoneNumber": employee.phoneNumber,
                "role": employee.role,
                "department": employee.department
            }
        }), 200

    except Exception as e:
        db.rollback()
        print(e)
        return jsonify({"message": "Something went wrong during update"}), 500

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

