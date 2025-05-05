from flask import Blueprint, request,jsonify, current_app as app
from flaskr.db import get_tenant_db
from flaskr.middlewares.PermissionMiddleware import permission_required
from sqlalchemy.exc import SQLAlchemyError
from flaskr.entities.alert_system.AlertRule import AlertRule, Priority
from flaskr.entities.alert_system.RuleCameraLink import RuleCameraLink
from flaskr.entities.alert_system.RuleZoneLink import RuleZoneLink
from flaskr.entities.VideoCamera import VideoCamera
from sqlalchemy.orm import joinedload

bp = Blueprint("alert-rules", __name__, url_prefix="/alert-rules")

"""
conditions_json: 
{
    "logic": "AND",
    "conditions": [
    {
        "object_name": "Excavator",
        "dwell_time": 10, 
        "min_count": 1, 
        "action": {
            "notification": "email",
            "message": "Excavator detected",
            "recipient": {
                "security": [1, 2, 3],
                "employees": [1 , 2, 3]
            }
        }
    },
    {
        "object_name": "face_recognition",
        "dwell_time": 10, 
        "employees": [1, 2, 3]  // at least one
        "action": {
            "notification": "sms",
            "message": "Excavator detected",
            "recipient": {
                "security": [1, 2, 3],
                "employees": [1 , 2, 3]
            }
        }
    }
    ]
}

"""

@bp.route("/", methods=["POST"])
@permission_required("CREATE_ALERT_RULES")
def create_alert_rule(current_user):
    """
    Create a new alert rule.
    Request Body:
        {
            "description": "string",
            "is_active": true, // optional, default is false
            "priority": 1, // 1 - low 2 - medium 3 - high
            "conditions_json": "{}",
            "location": { // At least one camera or one zone
                "cameras": [1, 2],
                "zones": []
            }
        }
    Returns:
        JSON response with the created alert rule or an error message.
    """
    data = request.get_json()
    db = get_tenant_db()
    
    try:
        # Convert priority string to correct enum value
        priority_str = data.get("priority")
        try:
            if isinstance(priority_str, int):
                # If priority is sent as numeric value (1, 2, 3)
                if priority_str == 1:
                    priority = Priority.LOW
                elif priority_str == 2:
                    priority = Priority.MEDIUM
                elif priority_str == 3:
                    priority = Priority.HIGH
                else:
                    priority = Priority.MEDIUM  # Default
            elif isinstance(priority_str, str):
                # If priority is sent as string ('low', 'medium', 'high')
                priority_upper = priority_str.upper()
                if priority_upper == 'LOW':
                    priority = Priority.LOW
                elif priority_upper == 'MEDIUM':
                    priority = Priority.MEDIUM
                elif priority_upper == 'HIGH':
                    priority = Priority.HIGH
                else:
                    priority = Priority.MEDIUM  # Default
            else:
                priority = Priority.MEDIUM  # Default if not specified or invalid
        except (ValueError, TypeError):
            priority = Priority.MEDIUM  # Default if conversion fails
            
        alert_rule = AlertRule(
            description=data.get("description"),
            is_active=data.get("is_active", False),
            priority=priority,
            conditions_json=data["conditions_json"],
        )
        location = data.get("location", {})
        for camera_id in location.get("cameras", []):
            rule_camera_link = RuleCameraLink(
                camera_id=camera_id
            )
            alert_rule.camera_links.append(rule_camera_link)

        for zone_id in location.get("zones", []):
            rule_zone_link = RuleZoneLink(
                zone_id=zone_id
            )
            alert_rule.zone_links.append(rule_zone_link)

        db.add(alert_rule)
        db.commit()

        return jsonify({"message": "Alert rule created successfully", "alert_rule_id": alert_rule.id}), 201

    except SQLAlchemyError as e:
        db.rollback()
        app.logger.error(f"Error creating alert rule: {str(e)}")
        return jsonify({"error": str(e)}), 500

@bp.route("/", methods=["GET"])
@permission_required("READ_ALERT_RULES")
def get_alert_rules(current_user):
    """
    Get all alert rules.
    Returns:
        JSON response with the list of alert rules.
    """
    db = get_tenant_db()

    try:
        alert_rules = db.query(AlertRule).all()
        return jsonify([alert_rule.to_dict() for alert_rule in alert_rules]), 200

    except SQLAlchemyError as e:
        app.logger.error(f"Error fetching alert rules: {str(e)}")
        return jsonify({"error": str(e)}), 500

@bp.route("/<int:rule_id>", methods=["PUT"])
@permission_required("UPDATE_ALERT_RULES")
def update_alert_rule(current_user, rule_id):
    """
    Update an existing alert rule. Can update description, priority, conditions, active status, and location links.
    Request Body: (Include fields to update)
        {
            "description": "string",
            "is_active": true,
            "priority": "high", // or "medium", "low"
            "conditions_json": "{}",
            "location": {
                "cameras": [1, 2], // Overwrites existing camera links
                "zones": [3]       // Overwrites existing zone links
            }
        }
    Returns:
        JSON response confirming update or error.
    """
    data = request.get_json()
    db = get_tenant_db()

    try:
        alert_rule = db.query(AlertRule).filter(AlertRule.id == rule_id).first()
        if not alert_rule:
            return jsonify({"error": "Alert rule not found"}), 404

        if "description" in data:
            alert_rule.description = data["description"]
        if "is_active" in data:
            alert_rule.is_active = data["is_active"]
        if "priority" in data:
            priority_str = data["priority"]
            try:
                if isinstance(priority_str, int):
                    # If priority is sent as numeric value (1, 2, 3)
                    if priority_str == 1:
                        priority = Priority.LOW
                    elif priority_str == 2:
                        priority = Priority.MEDIUM
                    elif priority_str == 3:
                        priority = Priority.HIGH
                    else:
                        priority = Priority.MEDIUM  # Default
                elif isinstance(priority_str, str):
                    # If priority is sent as string ('low', 'medium', 'high')
                    priority_upper = priority_str.upper()
                    if priority_upper == 'LOW':
                        priority = Priority.LOW
                    elif priority_upper == 'MEDIUM':
                        priority = Priority.MEDIUM
                    elif priority_upper == 'HIGH':
                        priority = Priority.HIGH
                    else:
                        priority = Priority.MEDIUM  # Default
                else:
                    priority = Priority.MEDIUM  # Default if not specified or invalid
                
                alert_rule.priority = priority
            except (ValueError, TypeError):
                # Keep existing priority if conversion fails
                pass
        if "conditions_json" in data:
            alert_rule.conditions_json = data["conditions_json"]

        if "location" in data:
            location = data["location"]
            alert_rule.camera_links.clear()
            alert_rule.zone_links.clear()
            for camera_id in location.get("cameras", []):
                rule_camera_link = RuleCameraLink(camera_id=camera_id)
                alert_rule.camera_links.append(rule_camera_link)
            for zone_id in location.get("zones", []):
                rule_zone_link = RuleZoneLink(zone_id=zone_id)
                alert_rule.zone_links.append(rule_zone_link)

        db.commit()
        return jsonify({"message": "Alert rule updated successfully"}), 200

    except SQLAlchemyError as e:
        db.rollback()
        app.logger.error(f"Error updating alert rule {rule_id}: {str(e)}")
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        db.rollback()
        app.logger.error(f"Unexpected error updating alert rule {rule_id}: {str(e)}")
        return jsonify({"error": "An unexpected error occurred"}), 500

@bp.route("/<int:rule_id>", methods=["DELETE"])
@permission_required("DELETE_ALERT_RULES")
def delete_alert_rule(current_user, rule_id):
    """
    Delete an alert rule.
    Returns:
        JSON response confirming deletion or error.
    """
    db = get_tenant_db()
    try:
        alert_rule = db.query(AlertRule).filter(AlertRule.id == rule_id).first()
        if not alert_rule:
            return jsonify({"error": "Alert rule not found"}), 404

        db.delete(alert_rule)
        db.commit()
        return jsonify({"message": "Alert rule deleted successfully"}), 200

    except SQLAlchemyError as e:
        db.rollback()
        app.logger.error(f"Error deleting alert rule {rule_id}: {str(e)}")
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        db.rollback()
        app.logger.error(f"Unexpected error deleting alert rule {rule_id}: {str(e)}")
        return jsonify({"error": "An unexpected error occurred"}), 500

@bp.route("/camera/<int:camera_id>", methods=["GET"])
@permission_required("READ_ALERT_RULES")
def get_alert_rules_for_camera(current_user, camera_id):
    """
    Get all alert rules associated with a specific camera.
    Returns:
        JSON response with the list of alert rules.
    """
    db = get_tenant_db()
    try:
        camera = db.query(VideoCamera.id).filter(VideoCamera.id == camera_id).first()
        if not camera:
            return jsonify({"error": "Camera not found"}), 404

        alert_rules = db.query(AlertRule)\
            .join(RuleCameraLink)\
            .filter(RuleCameraLink.camera_id == camera_id)\
            .options(joinedload(AlertRule.camera_links), joinedload(AlertRule.zone_links))\
            .all()

        rules_list = [rule.to_dict() for rule in alert_rules]

        return jsonify(rules_list), 200

    except SQLAlchemyError as e:
        app.logger.error(f"Error fetching alert rules for camera {camera_id}: {str(e)}")
        return jsonify({"error": str(e)}), 500
    except AttributeError:
        app.logger.error(f"AlertRule entity likely missing a 'to_dict' method.")
        rules_list_manual = []
        for rule in alert_rules:
             rules_list_manual.append({
                 "id": rule.id,
                 "description": rule.description,
                 "is_active": rule.is_active,
                 "priority": rule.priority.value if rule.priority else None,
                 "conditions_json": rule.conditions_json,
                 "created_at": rule.created_at.isoformat() if rule.created_at else None,
             })
        return jsonify(rules_list_manual), 200

    except Exception as e:
        app.logger.error(f"Unexpected error fetching alert rules for camera {camera_id}: {str(e)}")
        return jsonify({"error": "An unexpected error occurred"}), 500
