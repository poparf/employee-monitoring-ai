from flask import current_app as app, Blueprint, request, Response, g
from flaskr.db import get_tenant_db, get_users_db
from flaskr.middlewares.PermissionMiddleware import permission_required
from flaskr.entities.VideoCamera import VideoCamera
from flaskr.entities.auth_db.User import User
import re
from flaskr.entities.Employee import Employee
import jwt
import cv2 as cv
import numpy as np
import face_recognition
import io

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
            print("Decoding jwt")
            data = jwt.decode(token, app.config["JWT_SECRET"], algorithms=["HS256"])
            print("Decoded jwt")
            db = get_users_db()
            print("Querying user")
            logged_user = db.query(User).filter_by(id=data["user_id"]).first()
            print("Logged user: ", logged_user)
            if logged_user == None:
                return {
                    "message": "Invalid token",
                }, 401
        except Exception as e:
            print(e)
            return {
                "message": "Something went wrong",
            }, 500
        
        # Set the tenant database such that it will query that specific one
        print(logged_user)
        g.tenant_id = logged_user.tenant_id
        return logged_user, 200
        


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
        print(e)
        return {"message": "Internal server error"}, 500


# query parameters: face_recognition, person_detection, ppe_recognition
@bp.route("/<string:camera_name>/stream", methods=["GET"])
#@permission_required("READ_VIDEO_STREAM")
def get_camera(camera_name):
    print("Called get camera")
    res, code = validate_token(request.args.get("token"))
    if code == 400:
        return res, code
    current_user = res
    face_recognition_filter = request.args.get("face_recognition")
    person_detection_filter = request.args.get("person_detection")
    ppe_recognition_filter = request.args.get("ppe_recognition")

    db = get_tenant_db()
    camera = db.query(VideoCamera).filter_by(name=camera_name).first()
    if not camera:
        return {"message": "Camera not found"}, 404
    
    
    # Here the RTSP stream should be read and returned
    rtsp_url = f"rtsp://{camera.username}:{camera.password}@{camera.ip}:{camera.port}/stream2"
    cap = cv.VideoCapture(rtsp_url)
    if not cap.isOpened():
        return {"message": "Could not open stream"}, 500
    
    employees = db.query(Employee).all()
    known_face_encodings = [np.load(io.BytesIO(employee.encodedFace)) for employee in employees]
    known_face_names = [f"{employee.firstName} {employee.lastName}" for employee in employees]
    print("Known face encodings:", known_face_encodings)
    def generate_frames():
        process_this_frame = True
        while True:
            success, frame = cap.read()
            if not success:
                print("Failed to read frame")
                break
            # Now process the frame based on the query parameters
            # and then encode it into jpeg
            if process_this_frame:
                try:
                    if face_recognition_filter:
                        face_names = []
                        # Apply face recognition
                        small_frame = cv.resize(frame, (0, 0), fx=0.25, fy=0.25)
                        rgb_small_frame = np.ascontiguousarray(small_frame[:, :, ::-1])
                        face_locations = face_recognition.face_locations(rgb_small_frame)
                        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)
                        
                        for face_encoding in face_encodings:
                            matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
                            name = "Unknown"

                            face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
                            best_match_index = np.argmin(face_distances)
                            if matches[best_match_index]:
                                name = known_face_names[best_match_index]
                            face_names.append(name)
                        # Draw a box around the face
                        for (top, right, bottom, left), name in zip(face_locations, face_names):
                            top *= 4
                            right *= 4
                            bottom *= 4
                            left *= 4
                            cv.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)
                            cv.rectangle(frame, (left, bottom - 35), (right, bottom), (0, 0, 255), cv.FILLED)
                            font = cv.FONT_HERSHEY_DUPLEX
                            cv.putText(frame, name, (left + 6, bottom - 6), font, 1.0, (255, 255, 255), 1)
                except Exception as e:
                    print(e)
                    print("Failed to apply face recognition")
                    break
                if person_detection_filter:
                    # Apply person detection
                    pass

                if ppe_recognition_filter:
                    # Apply PPE recognition
                    pass
            process_this_frame = not process_this_frame

            ######################3
            success, jpeg_frame = cv.imencode('.jpg', frame)
            if not success:
                print("Failed to encode frame")
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