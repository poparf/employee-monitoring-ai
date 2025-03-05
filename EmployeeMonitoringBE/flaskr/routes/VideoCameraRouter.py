from flask import current_app as app
from flask import Blueprint
from flaskr.middlewares.PermissionMiddleware import permission_required

bp = Blueprint("video-cameras", __name__, url_prefix="/video-cameras")

@bp.route("/", methods=["GET"])
@permission_required("READ_VIDEO_STREAM")
def hello_camera(current_user):
    return "Hello from camera!"