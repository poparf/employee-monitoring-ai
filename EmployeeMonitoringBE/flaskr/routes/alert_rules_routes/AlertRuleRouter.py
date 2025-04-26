from flask import Blueprint, request,jsonify, current_app as app
from flaskr.db import get_tenant_db
from flaskr.middlewares.PermissionMiddleware import permission_required
from sqlalchemy.exc import SQLAlchemyError
from flaskr.entities.alert_system.AlertRule import AlertRule
from flaskr.entities.alert_system.RuleCameraLink import RuleCameraLink
from flaskr.entities.alert_system.RuleZoneLink import RuleZoneLink

bp = Blueprint("alert-rules", __name__, url_prefix="/alert-rules")

@bp.route("/", methods=["POST"])
@permission_required("CREATE_ALERT_RULES")
def create_alert_rule(current_user):
    """
    Create a new alert rule.
    Request Body:
        {
            "description": "string",
            "is_active": true,
            "priority": 1,
            "conditions_json": "{}",
            "action_details_json": "{}",
            "cooldown_seconds": 30,
            "camera_links": [{"camera_id": 1}, {"camera_id": 2}],
            "zone_links": [{"zone_id": 1}, {"zone_id": 2}]
        }
    Returns:
        JSON response with the created alert rule or an error message.
    """
    data = request.get_json()
    db = get_tenant_db()

    try:
        # Create the alert rule
        alert_rule = AlertRule(
            description=data.get("description"),
            is_active=data.get("is_active", False),
            priority=data.get("priority"),
            conditions_json=data["conditions_json"],
            action_details_json=data["action_details_json"],
            cooldown_seconds=data.get("cooldown_seconds", 30)
        )

        # Add camera links
        for camera_link in data.get("camera_links", []):
            rule_camera_link = RuleCameraLink(
                camera_id=camera_link["camera_id"]
            )
            alert_rule.camera_links.append(rule_camera_link)

        # Add zone links
        for zone_link in data.get("zone_links", []):
            rule_zone_link = RuleZoneLink(
                zone_id=zone_link["zone_id"]
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
