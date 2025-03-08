from flask import Blueprint, request
from flaskr.db import get_tenant_db
from flaskr.entities import PPE

pperouter = Blueprint("pperouter", __name__, url_prefix="/ppe")

@pperouter.route('/', methods=['GET'])
def get_ppe():
    try:
        db = get_tenant_db()
        db.query(PPE).all()
        return {"ppe": [ppe.to_dict() for ppe in ppe]}
    except Exception as e:
        return {"message": "Something went wrong"}, 500

@pperouter.route("/<ppe_id>", methods=["GET"])
def get_ppe_by_id(ppe_id):
    try:
        db = get_tenant_db()
        ppe = db.query(PPE).filter_by(id=ppe_id).first()
        if ppe == None:
            return {"message": "PPE not found"}, 404
        return ppe.to_dict()
    except Exception as e:
        return {"message": "Something went wrong"}, 500