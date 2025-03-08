from flask import current_app as app, Blueprint, request, Response, g
from flaskr.db import get_tenant_db, get_users_db
from flaskr.middlewares.PermissionMiddleware import permission_required
from flaskr.entities.VideoCamera import VideoCamera
from flaskr.entities.auth_db.User import User
from flask_cors import cross_origin
import re
import jwt
import cv2 as cv

bp = Blueprint("video-cameras", __name__, url_prefix="/video-cameras")

# def is_valid_ip(ip):
#     pattern = re.compile(
#         r"^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$"
#     )
#     return pattern.match(ip) is not None

def is_valid_port(port):
    return 0 <= int(port) <= 65535

def validate_token(token):
        try:
            data = jwt.decode(token, app.config["JWT_SECRET"], algorithms=["HS256"])
            db = get_users_db()
            logged_user = db.query(User).filter_by(id=data["user_id"]).first()
            if logged_user == None:
                return {
                    "message": "Invalid token",
                }, 401
        except Exception as e:
            return {
                "message": "Something went wrong",
            }, 500
        
        # Set the tenant database such that it will query that specific one
        g.tenant_id = logged_user.tenant_id
        


@bp.route("/", methods=["POST"])
@permission_required("CREATE_VIDEO_CAMERA")
def create_video_camera(current_user):
    try:
        data = request.get_json()
        if not data:
            return {"message": "No input data provided"}, 400

        required_fields = ["ip", "port", "username", "password", "name", "location"]
        for field in required_fields:
            if field not in data:
                return {"message": f"'{field}' is a required field"}, 400
        
        # if not is_valid_ip(data.get("ip")):
        #     return {"message": "Invalid IP address"}, 400

        if not is_valid_port(data.get("port")):
            return {"message": "Invalid port number"}, 400
        
        ip = data.get("ip")
        port = data.get("port")
        username = data.get("username")
        password = data.get("password")
        name = data.get("name")
        location = data.get("location")

        db = get_tenant_db()
        if db.query(VideoCamera).filter(VideoCamera.name == name).first():
            return {"message": "Camera with that name already exists"}, 400

        camera = VideoCamera(
            ip=ip,
            port=port,
            username=username,
            password=password,
            name=name,
            location=location,
            status=VideoCamera.CameraStatus.INACTIVE
        )

        db.add(camera)
        db.flush()
        db.commit()
        return {"message": "Camera created successfully", "camera": {
            "id": camera.id,
            "ip": camera.ip,
            "port": camera.port
        }}, 201
    except Exception as e:
        app.logger.error(e)
        return {"message": "Internal server error"}, 500


# query parameters: face_recognition, person_detection, ppe_recognition
@bp.route("/<string:camera_name>/stream", methods=["GET"])
@permission_required("READ_VIDEO_STREAM")
def get_camera(current_user, camera_name):
    db = get_tenant_db()
    camera = db.query(VideoCamera).filter_by(name=camera_name).first()
    if not camera:
        return {"message": "Camera not found"}, 404
    
    
    # Here the RTSP stream should be read and returned
    rtsp_url = f"rtsp://{camera.username}:{camera.password}@{camera.ip}:{camera.port}/stream2"
    # rtsp_url ="rtsp://robert037:emonitoringai037!@192.168.1.25:554/stream1"
    cap = cv.VideoCapture(rtsp_url)
    if not cap.isOpened():
        return {"message": "Could not open stream"}, 500
    
    def generate_frames():
        while True:
            success, frame = cap.read()
            if not success:
                app.logger.error("Failed to read frame")
                break
            success, jpeg_frame = cv.imencode('.jpg', frame)
            if not success:
                app.logger.error("Failed to encode frame")
                break
            frame_bytes = jpeg_frame.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n\r\n')
            cv.waitKey(33)  # 1000 ms / 30 fps = ~33 ms per frame

    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame', headers={
        'Access-Control-Allow-Origin': 'http://127.0.0.1:5500',
        'Access-Control-Allow-Credentials': 'true'
    })


@bp.route('/video-cameras/<camera_name>/stream', methods=['OPTIONS'])
@permission_required("READ_VIDEO_STREAM")
def handle_options(current_user, camera_name):
    response = app.make_default_options_response()
    response.headers.add('Access-Control-Allow-Headers', 'Authorization, Content-Type')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    return response