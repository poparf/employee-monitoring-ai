from flask import Blueprint, request, jsonify, current_app as app
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
        app.logger.error(f"Database error in retrieving alerts: {str(e)}")
        return jsonify({"error": "Database error occurred"}), 500
    except Exception as e:
        # Log the error e
        app.logger.error(f"Unexpected error in retrieving alerts: {str(e)}")
        return jsonify({"error": "An unexpected error occurred"}), 500


@bp.route("/<int:alert_id>", methods=["GET"])
@permission_required("GET_ALERTS")
def get_alert_by_id(current_user, alert_id):
    """
    Retrieves a single alert by ID with all its details, including screenshot path.
    
    Args:
        alert_id (int): The ID of the alert to retrieve.
        
    Returns:
        JSON response with the alert details or an error message.
    """
    db = get_tenant_db()
    try:
        alert = db.query(Alert).filter(Alert.id == alert_id).first()
        
        if not alert:
            return jsonify({"error": f"Alert with ID {alert_id} not found"}), 404
            
        alert_data = alert.to_dict()
        
        # Add the base URL for screenshots if a screenshot exists
        if alert.screenshot:
            # Create the full URL for the screenshot
            base_url = request.host_url.rstrip('/')
            if not alert.screenshot.startswith('http'):
                # If it's a relative path, create a full URL
                if alert.screenshot.startswith('/'):
                    alert_data['screenshot_url'] = f"{base_url}{alert.screenshot}"
                else:
                    alert_data['screenshot_url'] = f"{base_url}/static/{alert.screenshot}"
            else:
                # If it's already a full URL, use it as is
                alert_data['screenshot_url'] = alert.screenshot
        
        return jsonify({"alert": alert_data}), 200
        
    except SQLAlchemyError as e:
        app.logger.error(f"Database error retrieving alert {alert_id}: {str(e)}")
        return jsonify({"error": "Database error occurred"}), 500
    except Exception as e:
        app.logger.error(f"Unexpected error retrieving alert {alert_id}: {str(e)}")
        return jsonify({"error": "An unexpected error occurred"}), 500


@bp.route("/<int:alert_id>", methods=["PUT"])
@permission_required("GET_ALERTS")
def update_alert(current_user, alert_id):
    """
    Updates an existing alert with provided data.
    
    Request Body (all fields optional):
    {
        "status": "active" or "resolved",
        "explanation": "Updated explanation text",
        "level": "low", "medium", or "high",
        "resolved_at": "2025-05-05T10:00:00" (ISO format, required if status is "resolved")
    }
    
    Args:
        alert_id (int): The ID of the alert to update
        
    Returns:
        JSON response with success message or error
    """
    data = request.get_json()
    db = get_tenant_db()
    
    try:
        # Find the alert to update
        alert = db.query(Alert).filter(Alert.id == alert_id).first()
        
        if not alert:
            return jsonify({"error": f"Alert with ID {alert_id} not found"}), 404
        
        # Update alert fields if provided in the request
        if "status" in data:
            try:
                new_status = AlertStatus(data["status"].lower())
                
                # If changing to resolved, require resolved_at timestamp
                if new_status == AlertStatus.RESOLVED and alert.status != AlertStatus.RESOLVED:
                    # If resolved_at not provided in request, use current time
                    if "resolved_at" in data:
                        try:
                            resolved_at = datetime.fromisoformat(data["resolved_at"])
                        except ValueError:
                            return jsonify({"error": "Invalid resolved_at format. Use ISO 8601 (YYYY-MM-DDTHH:MM:SS)."}), 400
                    else:
                        resolved_at = datetime.now()
                        
                    alert.resolved_at = resolved_at
                
                alert.status = new_status
            except ValueError:
                return jsonify({"error": f"Invalid status value: {data['status']}. Allowed values: active, resolved"}), 400
        
        if "level" in data:
            try:
                alert.level = AlertLevel(data["level"].lower())
            except ValueError:
                return jsonify({"error": f"Invalid level value: {data['level']}. Allowed values: low, medium, high"}), 400
        
        if "explanation" in data:
            alert.explanation = data["explanation"]
        
        # Commit changes to the database
        db.commit()
        
        return jsonify({
            "message": "Alert updated successfully",
            "alert": alert.to_dict()
        }), 200
        
    except SQLAlchemyError as e:
        db.rollback()
        app.logger.error(f"Database error updating alert {alert_id}: {str(e)}")
        return jsonify({"error": "Database error occurred"}), 500
    except Exception as e:
        db.rollback()
        app.logger.error(f"Unexpected error updating alert {alert_id}: {str(e)}")
        return jsonify({"error": "An unexpected error occurred"}), 500
