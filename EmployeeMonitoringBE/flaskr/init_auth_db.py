from flaskr.db import get_users_db, setup_users_db

from flaskr.entities.auth_db.Role import Role
from flaskr.entities.auth_db.User import User
from flaskr.entities.auth_db.RolePermission import RolePermission
from flaskr.entities.auth_db.Permission import Permission
from flaskr.entities.auth_db.RoleUser import RoleUser
from flaskr.services.AuthService import hash_password
from flaskr.entities.auth_db.Tenant import Tenant

def init_auth_db(app):
    setup_users_db(app)
    print("Database initialized")
    db = get_users_db()
    admin_role = Role(name="ADMIN")
    db.add(admin_role)
    security_guard_role = Role(name="SECURITY")
    db.add(security_guard_role)

    manage_alerts_permission = Permission(name="MANAGE_ALERTS")
    db.add(manage_alerts_permission)
    read_alerts_permission = Permission(name="READ_ALERTS")
    db.add(read_alerts_permission)
    manage_alerts_rules_permission = Permission(name="MANAGE_ALERT_RULES")
    db.add(manage_alerts_rules_permission)
    read_alert_rule_permission = Permission(name="READ_ALERT_RULES")
    db.add(read_alert_rule_permission)

    get_alerts_permission = Permission(name="GET_ALERTS")
    db.add(get_alerts_permission)
    create_blacklist_permission = Permission(name="CREATE_BLACKLIST")
    db.add(create_blacklist_permission)
    delete_blacklist_permission = Permission(name="DELETE_BLACKLIST")
    db.add(delete_blacklist_permission)

    create_employee_permission = Permission(name="CREATE_EMPLOYEE")
    db.add(create_employee_permission)
    delete_employee_permission = Permission(name="DELETE_EMPLOYEE")
    db.add(delete_employee_permission)

    create_tenant_permission = Permission(name="CREATE_TENANT")
    db.add(create_tenant_permission)
    create_video_camera_permission = Permission(name="CREATE_VIDEO_CAMERA")
    db.add(create_video_camera_permission)
    read_video_camera_permission = Permission(name="READ_VIDEO_CAMERA")
    db.add(read_video_camera_permission)

    get_persons_detected = Permission(name="GET_PERSONS_DETECTED")
    db.add(get_persons_detected)

    read_video_stream = Permission(name="READ_VIDEO_STREAM")
    db.add(read_video_stream)

    create_zone_permission = Permission(name="CREATE_ZONE")
    db.add(create_zone_permission)
    delete_zone_permission = Permission(name="DELETE_ZONE")
    db.add(delete_zone_permission)

    db.flush()
    db.add(RolePermission(role_id=admin_role.id, permission_id=manage_alerts_permission.id))
    db.add(RolePermission(role_id=admin_role.id, permission_id=read_alerts_permission.id))
    db.add(RolePermission(role_id=admin_role.id, permission_id=manage_alerts_rules_permission.id))
    db.add(RolePermission(role_id=admin_role.id, permission_id=read_alert_rule_permission.id))
    db.add(RolePermission(role_id=admin_role.id, permission_id=get_alerts_permission.id))
    db.add(RolePermission(role_id=admin_role.id, permission_id=create_blacklist_permission.id))
    db.add(RolePermission(role_id=admin_role.id, permission_id=delete_blacklist_permission.id))
    db.add(RolePermission(role_id=admin_role.id, permission_id=create_employee_permission.id))
    db.add(RolePermission(role_id=admin_role.id, permission_id=delete_employee_permission.id))
    db.add(RolePermission(role_id=admin_role.id, permission_id=get_persons_detected.id))
    db.add(RolePermission(role_id=admin_role.id, permission_id=read_video_stream.id))
    db.add(RolePermission(role_id=admin_role.id, permission_id=create_zone_permission.id))
    db.add(RolePermission(role_id=admin_role.id, permission_id=delete_zone_permission.id))
    db.add(RolePermission(role_id=admin_role.id, permission_id=create_video_camera_permission.id))
    db.add(RolePermission(role_id=admin_role.id, permission_id=read_video_camera_permission.id))

    db.add(RolePermission(role_id=security_guard_role.id, permission_id=read_alert_rule_permission.id))
    db.add(RolePermission(role_id=security_guard_role.id, permission_id=read_alerts_permission.id))
    db.add(RolePermission(role_id=security_guard_role.id, permission_id=get_alerts_permission.id))
    db.add(RolePermission(role_id=security_guard_role.id, permission_id=get_persons_detected.id))
    db.add(RolePermission(role_id=security_guard_role.id, permission_id=read_video_stream.id))
    db.add(RolePermission(role_id=security_guard_role.id, permission_id=read_video_camera_permission.id))

    tenant = Tenant(name="ASE")
    db.add(tenant)
    db.flush()
    super_admin = User(email="robertflorianp037@gmail.com", password=hash_password("admin"), phoneNumber="0728922213", is_verified=True, tenant_id=tenant.id)
    super_admin.roles.append(admin_role)
    db.add(super_admin)
    db.commit()
    print("Done")