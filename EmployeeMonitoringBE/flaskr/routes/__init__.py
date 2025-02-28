from .UserRouter import bp as users_bp

def register_blueprints(app):
    app.register_blueprint(users_bp)