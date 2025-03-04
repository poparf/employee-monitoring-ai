from .UserRouter import bp as users_bp
from .VideoCameraRouter import bp as video_cameras_bp
from .EmployeeRouter import bp as employees_bp
from .TenantRouter import bp as tenants_bp

def register_blueprints(app):
    app.register_blueprint(users_bp)
    app.register_blueprint(video_cameras_bp)
    app.register_blueprint(employees_bp)
    app.register_blueprint(tenants_bp)