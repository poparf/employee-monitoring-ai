from flask import Blueprint, request, current_app as app, send_file
from flaskr.db import get_tenant_db
from flaskr.entities import PPE
from flaskr.middlewares.PermissionMiddleware import auth_required
import os

pperouter = Blueprint("pperouter", __name__, url_prefix="/ppe")

@pperouter.route('/image', methods=["GET"])
@auth_required
def get_ppe_image(current_user):
    try:    
        db = get_tenant_db()
        ppe_name = request.args.get("text")
        app.logger.info(f"Received PPE name: {ppe_name}")
        
        if not ppe_name:
            app.logger.error("PPE name is required but was not provided")
            return {"message": "PPE name is required"}, 400
        
        # List all PPE names in DB for debugging
        all_ppe_names = [p.name for p in db.query(PPE).all()]
        app.logger.info(f"Available PPE names in database: {all_ppe_names}")
        
        ppe = db.query(PPE).filter_by(name=ppe_name).first()
        if ppe is None:
            app.logger.warning(f"PPE with name '{ppe_name}' not found in database")
            return {"message": f"PPE not found with name: {ppe_name}"}, 404
            
        app.logger.info(f"Found PPE: {ppe.name}, image path: {ppe.image}")
        
        if not ppe.image:
            app.logger.warning(f"PPE '{ppe_name}' exists but has no image path")
            return {"message": "PPE image not found"}, 404
        
        if not os.path.isfile(ppe.image):
            app.logger.error(f"PPE image file not found at path: {ppe.image}")
            return {"message": f"PPE image file not found: {ppe.image}"}, 404
        
        app.logger.info(f"Successfully serving image for PPE '{ppe_name}' from {ppe.image}")
        return send_file(ppe.image, mimetype='image/jpeg')
    except Exception as e:
        app.logger.error(f"Error getting PPE image: {str(e)}", exc_info=True)
        return {"message": "Something went wrong"}, 500

@pperouter.route('/', methods=['GET'])
@auth_required
def get_ppe(current_user):
    try:
        db = get_tenant_db()
        ppes = db.query(PPE).all()
        return {"ppe": [ppe.to_dict() for ppe in ppes]}
    except Exception as e:
        return {"message": "Something went wrong"}, 500

@pperouter.route("/<ppe_id>", methods=["GET"])
@auth_required
def get_ppe_by_id(current_user, ppe_id):
    try:
        db = get_tenant_db()
        ppe = db.query(PPE).filter_by(id=ppe_id).first()
        if ppe == None:
            return {"message": "PPE not found"}, 404
        return ppe.to_dict()
    except Exception as e:
        return {"message": "Something went wrong"}, 500