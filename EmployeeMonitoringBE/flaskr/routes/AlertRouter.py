from flask import Blueprint, request
from flaskr.entities.Alert import Alert, AlertType, AlertLevel, AlertStatus
from flaskr.db import get_tenant_db
from flaskr.middlewares.PermissionMiddleware import permission_required

bp = Blueprint("alerts", __name__, url_prefix="/alerts")


# Creation of alerts are done only on the backend side
# so no need for a POST route


@bp.route("/", methods=["GET"])
@permission_required("GET_ALERTS")
def get_alerts():
    # TODO: Pagination/filtering
    query_params = request.args
    db = get_tenant_db()
    alerts = db.query(Alert).all()
    return {"alerts": [alert.to_dict() for alert in alerts]}
