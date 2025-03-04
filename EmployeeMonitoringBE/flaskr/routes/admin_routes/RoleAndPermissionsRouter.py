from flask import Blueprint, request, jsonify
from flaskr.db import get_users_db
from flaskr.entities.auth_db.Role import Role
from flaskr.entities.auth_db.Permission import Permission
from flaskr.entities.auth_db.RolePermission import RolePermission
from flaskr.middlewares.RoleMiddleware import role_required
from flaskr.middlewares.AuthMiddleware import auth_required
bp = Blueprint("admin", __name__, url_prefix="/admin")

@bp.route("/roles", methods=["POST"])
@auth_required
@role_required("admin")
def create_role():
    try:
        """
        Request body:
        {
            "role": "name",
            "permissions": ["permission1", "permission2"]
        }
        """
        data = request.get_json()
        db = get_users_db()
        role = Role(name=data["role"])
        db.add(role)

        permissions_created = []
        for name in data["permissions"]:
            permission = Permission(name=name)
            db.add(permission)
            permissions_created.add(permission)
        
        db.flush()
        for permission in permissions_created:
            role_permission = RolePermission(role_id=role.id, permission_id=permission.id)
            db.add(role_permission)
        
        db.commit()
        return {"message": "Role created successfully"}, 201
    except Exception as e:
        print(e)
        return {"message": "An error occured"}, 500 