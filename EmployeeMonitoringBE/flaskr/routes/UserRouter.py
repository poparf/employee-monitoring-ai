from flask import Blueprint, request, jsonify, g
from flaskr.entities.auth_db.User import User
from flaskr.db import get_users_db
from flaskr.entities.auth_db.EmailCodes import EmailCodes
from flaskr.entities.auth_db.Role import Role
from flaskr.services.AuthService import check_password, hash_password
import re
from flaskr.services.EmailService import get_email_service
import flaskr.services.CodeGenerator as CodeGenerator
import jwt
from threading import Timer
from flask import current_app as app
from flaskr.middlewares.RoleMiddleware import role_required

bp = Blueprint("users", __name__, url_prefix="/users")


def validate_new_user_data(data):
    # Validate data existance
        if data == None:
            return jsonify({"message": "No data provided"}), 400
        
        if "email" not in data:
            return jsonify({"message": "Email is required"}), 400
        
        if "password" not in data:
            return jsonify({"message": "Password is required"}), 400
        
        if "phoneNumber" not in data:
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

        return None, 200

@bp.route("/register-security-guard", methods=["POST"])
@role_required("ADMIN")
def register_security_guard(current_user):
    try:
        data = request.get_json()
        message, code = validate_new_user_data(data)
        if code == 400:
            return message, code
        email = data["email"]
        password = data["password"]
        phoneNumber = data["phoneNumber"]

        db = get_users_db()
        user = db.query(User).filter_by(email=email).first()
        if user != None:
            return jsonify({"message": "Email already in use"}), 400
        
        hashedPassword = hash_password(password)
        user = User(email=email, password=hashedPassword, phoneNumber=phoneNumber, tenant_id=g.tenant_id)
        user.roles.append(db.query(Role).filter_by(name="SECURITY").first())
        db.add(user)
        db.flush()
        db.commit()
        return {"message": "User created successfully", "user": {
            "id": user.id,
            "email": user.email,
            "phoneNumber": user.phoneNumber,
            "tenant_id": user.tenant_id,
            "role": "SECURITY"
            }}, 201
    except Exception as e:
        app.logger.error(e)
        return jsonify({"message": "Something went wrong"}), 500

@bp.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    message, code = validate_new_user_data(data)
    if code == 400:
        return message, code
    email = data["email"]
    password = data["password"]
    phoneNumber = data["phoneNumber"]
    
    db = get_users_db()
    user = db.query(User).filter_by(email=email).first()
    if user != None:
        return jsonify({"message": "Email already in use"}), 400
    
    hashedPassword = hash_password(password)
    user = User(email=email, password=hashedPassword, phoneNumber=phoneNumber)
    user.roles.append(db.query(Role).filter_by(name="ADMIN").first())
    db.add(user)
    db.flush()  # Ensure the user ID is generated
    code = CodeGenerator.generate_email_verification_code()
    emailVerification = EmailCodes(user_id=user.id, code=code)
    db.add(emailVerification)
    db.commit()

    get_email_service().send_code_verification(email, code)
    Timer(60 * 5, delete_expired_timer_email_verification, [db, user, emailVerification]).start()
    return jsonify({"message": "Please verify your email in maximum 5 minutes.","user": {"id": user.id, "email": user.email}}), 201


def delete_expired_timer_email_verification(db, user, emailVerification):
    emailVerification = db.query(EmailCodes).filter_by(id=emailVerification.id).first()
    if emailVerification is not None:
        if user.is_verified == False:
            db.delete(user)
        db.delete(emailVerification)
        db.commit()

@bp.route("/verify-email", methods=["POST"])
def verify_email():
    data = request.get_json()

    # Validate data existance
    if data == None:
        return jsonify({"message": "No data provided"}), 400
    
    if "email" not in data:
        return jsonify({"message": "Email is required"}), 400
    
    if "code" not in data:
        return jsonify({"message": "Code is required"}), 400

    email = data.get("email")
    code = data.get("code")

    db = get_users_db()
    user = db.query(User).filter_by(email=email).first()
    if user == None:
        return jsonify({"message": "Invalid email or code. There is a possibility that the code expired."}), 400

    emailVerification = db.query(EmailCodes).filter_by(user_id=user.id, code=code).first()

    if emailVerification == None:
        return jsonify({"message": "Invalid email or code. There is a possibility that the code expired."}), 400

    user.is_verified = True

    db.delete(emailVerification)
    db.commit()
    return jsonify({"message": "Email verified"}), 200

@bp.route("/login", methods=["POST"])
def login():
    try:
        data = request.get_json()

        # Validate data existance
        if data == None:
            return jsonify({"message": "No data provided"}), 400
        
        if "email" not in data:
            return jsonify({"message": "Email is required"}), 400
        
        if "password" not in data:
            return jsonify({"message": "Password is required"}), 400

        email = data.get("email")
        password = data.get("password")

        db = get_users_db()
        user = db.query(User).filter_by(email=email).first()
        print("got to check password")
        if user == None or not check_password(password, user.password):
            return jsonify({"message": "Invalid email or password."}), 400
        print("Succeded check password")
        try:
            # TODO: Set token expiration and refresh
            token = jwt.encode({
                    "user_id": str(user.id),
                    "tenant_id": str(user.tenant_id),
                    "roles":[role.name for role in user.roles]
                },
                app.config["JWT_SECRET"],
                algorithm="HS256"
            )
            return jsonify({"token": token, "user": {
                "id": user.id,
                "email": user.email,
                "phoneNumber": user.phoneNumber,
                "tenant_id": user.tenant_id,
            }}), 200
        except Exception as e:
            app.logger.error(e)
            return jsonify({"message": "Something went wrong"}), 500
    except Exception as e:   
        app.logger.error(e)
        return jsonify({"message": "Something went wrong"}), 500