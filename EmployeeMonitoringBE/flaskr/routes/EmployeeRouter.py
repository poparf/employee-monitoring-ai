from flask import Blueprint, request, jsonify
from flaskr.middlewares.AuthMiddleware import auth_required
from flaskr.db import get_db
from flaskr.entities.Employee import Employee
bp = Blueprint("employees", __name__, url_prefix="/employees")

# Create employees
"""
Columns:
firstName, lastName, phoneNumber, role, department
encodedFace str, profilePicture str(path)
"""
@bp.route("/", methods=["POST"])
@auth_required
def create_employee(current_user):
    try:
        data = request.get_json()
        response, code = validate_employee_data(data)
        if code == 400:
            return response, code

        db = get_db()
        employee = Employee(
            firstName=data.get("firstName"),
            lastName=data.get("lastName"),
            phoneNumber=data.get("phoneNumber"),
            role=data.get("role"),
            department=data.get("department")
        )
        

    except Exception as e:
        print(e)
        return jsonify({"message": "Something went wrong"}), 500

def validate_employee_data(data):
    if data == None:
        return jsonify({"message": "No data provided"}), 400
    if "firstName" not in data:
        return jsonify({"message": "First name is required"}), 400
    if "lastName" not in data:
        return jsonify({"message": "Last name is required"}), 400
    if "phoneNumber" not in data:
        return jsonify({"message": "Phone number is required"}), 400
    if "role" not in data:
        return jsonify({"message": "Role is required"}), 400
    if "department" not in data:
        return jsonify({"message": "Department is required"}), 400
    
    return None, 200

# Get all employees

