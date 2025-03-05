from flask import Blueprint, request, jsonify
from flaskr.db import get_users_db
from flaskr.entities.auth_db.Tenant import Tenant
from flaskr.entities.auth_db.User import User
from flaskr.middlewares.PermissionMiddleware import permission_required
from flaskr.db import setup_tenant_db

bp = Blueprint("tenant", __name__, url_prefix="/tenant")

@bp.route("/", methods=["POST"])
@permission_required("CREATE_TENANT")
def create_tenant(current_user):
    try:
        data = request.get_json()
        db = get_users_db()

        if data == None:
            return jsonify({"message": "No data provided"}), 400
        if "name" not in data:
            return jsonify({"message": "Name is required"}), 400
        
        name = data.get("name")
        tenant = db.query(Tenant).filter_by(name=name).first()
        if tenant:
            return jsonify({"message": "Tenant already exists"}), 400
        
        tenant = Tenant(name=name)
        db.add(tenant)

        db.flush()

        setup_tenant_db(tenant.id)

        # Conectam user-ul de db de abia dupa ce am creat db-ul ( tenant_ul )
        # tinand cont ca putem crea un user fara tenant
        user = db.query(User).filter_by(id=current_user.id).first()
        if user.tenant_id != None:
            return {"message": "User already has a tenant"}, 400
        user.tenant_id = tenant.id
        db.merge(user)
        current_user.tenant_id = tenant.id
        db.commit()
        return jsonify({"message": "Tenant created", "tenant_id": tenant.id}), 201
    except Exception as e:
        print(e)
        return jsonify({"message": "Something went wrong"}), 500