from flask import Blueprint, request, jsonify
from flaskr.entities.Alert import Alert, AlertType, AlertLevel, AlertStatus
from flaskr.db import get_tenant_db
from flaskr.middlewares.PermissionMiddleware import permission_required
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError

bp = Blueprint("alerts", __name__, url_prefix="/alerts")


# Creation of alerts are done only on the backend side
# so no need for a POST route


@bp.route("/", methods=["GET"])
@permission_required("GET_ALERTS")
def get_alerts(current_user):
    """
    Retrieves alerts, optionally filtering by status, level, zone, employee, and time range.
    Query Parameters:
        status (str): Filter by alert status (e.g., 'active', 'resolved').
        level (str): Filter by alert level (e.g., 'low', 'medium', 'high').
        zone_id (int): Filter by zone ID.
        employee_id (int): Filter by employee ID.
        start_time (str): Filter by start timestamp (ISO 8601 format, e.g., 'YYYY-MM-DDTHH:MM:SS').
        end_time (str): Filter by end timestamp (ISO 8601 format, e.g., 'YYYY-MM-DDTHH:MM:SS').
    Returns:
        JSON response with a list of alerts or an error message.
    """
    args = request.args
    db = get_tenant_db()
    try:
        query = db.query(Alert)

        if 'status' in args:
            try:
                status_enum = AlertStatus(args['status'].lower())
                query = query.filter(Alert.status == status_enum)
            except ValueError:
                return jsonify({"error": f"Invalid status value: {args['status']}"}), 400

        if 'level' in args:
            try:
                level_enum = AlertLevel(args['level'].lower())
                query = query.filter(Alert.level == level_enum)
            except ValueError:
                return jsonify({"error": f"Invalid level value: {args['level']}"}), 400

        if 'zone_id' in args:
            try:
                zone_id = int(args['zone_id'])
                query = query.filter(Alert.zone_id == zone_id)
            except ValueError:
                return jsonify({"error": f"Invalid zone_id value: {args['zone_id']}"}), 400

        if 'employee_id' in args:
            try:
                employee_id = int(args['employee_id'])
                query = query.filter(Alert.employee_id == employee_id)
            except ValueError:
                return jsonify({"error": f"Invalid employee_id value: {args['employee_id']}"}), 400

        if 'start_time' in args:
            try:
                # Assuming ISO 8601 format from query param
                start_time = datetime.fromisoformat(args['start_time'])
                query = query.filter(Alert.timestamp >= start_time)
            except ValueError:
                return jsonify({"error": f"Invalid start_time format: {args['start_time']}. Use ISO 8601."}), 400

        if 'end_time' in args:
            try:
                # Assuming ISO 8601 format from query param
                end_time = datetime.fromisoformat(args['end_time'])
                query = query.filter(Alert.timestamp <= end_time)
            except ValueError:
                return jsonify({"error": f"Invalid end_time format: {args['end_time']}. Use ISO 8601."}), 400

        # TODO: Add pagination later if needed
        alerts = query.all()
        return jsonify({"alerts": [alert.to_dict() for alert in alerts]}), 200

    except SQLAlchemyError as e:
        # Log the error e
        return jsonify({"error": "Database error occurred"}), 500
    except Exception as e:
        # Log the error e
        return jsonify({"error": "An unexpected error occurred"}), 500
