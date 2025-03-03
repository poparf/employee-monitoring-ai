from flask import current_app as app
from flask import Blueprint
from flaskr.middlewares.AuthMiddleware import auth_required

bp = Blueprint("video-cameras", __name__, url_prefix="/video-cameras")

@bp.route("/", methods=["GET"])
@auth_required
def hello_camera(current_user):
    return "Hello from camera!"