from flask import current_app as app, Blueprint, request, Response, g
from flaskr.db import get_tenant_db, get_users_db
from flaskr.middlewares.PermissionMiddleware import permission_required
from flaskr.entities.VideoCamera import VideoCamera
from flaskr.entities.auth_db.User import User
from flaskr.entities.Employee import Employee
import jwt
import cv2 as cv
import numpy as np
import face_recognition
import io
from threading import Thread, Lock
import time
import dlib
from ultralytics import YOLO

bp = Blueprint("video-cameras", __name__, url_prefix="/video-cameras")

active_cameras = {}  # camera_name: {"frame": bytes, "clients": count, "running": bool, "filters": [], thread: Thread}
camera_locks = {}    # camera_name: Lock


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
            print(logged_user)
            if logged_user == None:
                print("Invalid token")
                return {
                    "message": "Invalid token",
                }, 401
        except Exception as e:
            print(e)
            return {
                "message": "Something went wrong",
            }, 500
        
        # Set the tenant database such that it will query that specific one
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

def process_camera_frames(camera_name, rtsp_url,
                          filters,
                            known_face_encodings=[],
                            known_face_names=[]):
    print(f"Starting stream processing for {camera_name}")
    cuda_available = dlib.DLIB_USE_CUDA
    print(f"CUDA available: {cuda_available}")
    
    
    # --- Load the YOLO model ---
    model = None
    yolo_active_filters = [f for f in filters if f != "face_recognition"]
    if len(yolo_active_filters) != 0:
        model_path = "flaskr/ML/PPE_model/my_model.pt"
        try:
            model = YOLO(model_path, task='detect')
            print(f"YOLO model loaded successfully from {model_path}")
            yolo_labels = model.names
            print("YOLO labels:", yolo_labels)
        except Exception as e:
            print(f"Error loading YOLO model: {e}")
    # -------------------------

    cap = cv.VideoCapture(rtsp_url)
    #cap = cv.VideoCapture(0)
    # Reduced buffer size: solution 1
    cap.set(cv.CAP_PROP_BUFFERSIZE, 2)
    active_cameras[camera_name]["cap"] = cap
    if not cap.isOpened():
        print(f"Could not open stream for camera: {camera_name}")
        with camera_locks[camera_name]:
            active_cameras[camera_name]["running"] = False
        return
    
    #process_this_frame = True


    while active_cameras[camera_name]["running"]:
        with camera_locks[camera_name]:
            if active_cameras[camera_name]["clients"] <= 0:
                active_cameras[camera_name]["running"] = False
                print(f"No more clients for camera {camera_name}, stopping stream")
                break
        
        success, frame = cap.read()
        if not success:
            break

        #if process_this_frame:
        try:
            if "face_recognition" in filters and known_face_encodings:
                print("detecting faces")
                small_frame = cv.resize(frame, (0, 0), fx=0.25, fy=0.25)
                rgb_small_frame = np.ascontiguousarray(small_frame[:, :, ::-1])
                face_locations = face_recognition.face_locations(rgb_small_frame, model="cnn")
                face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)
                
                face_names = []
                for face_encoding in face_encodings:
                    matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
                    name = "Unknown"
                    
                    if len(known_face_encodings) > 0:
                        face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
                        best_match_index = np.argmin(face_distances)
                        if matches[best_match_index]:
                            name = known_face_names[best_match_index]
                    face_names.append(name)
                    print("Face names: ", face_names)
                
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
            print(f"Error in face recognition: {e}")
        
        # activate YOLO for every filter that is present in filters except face_recognition
        if model is not None:
            try:
                # Yolo active filters are strings, we need to convert into indices
                class_indices = []
                for idx, name in yolo_labels.items():
                    if name in yolo_active_filters:
                        class_indices.append(idx)

                results = model.predict(frame, conf=0.5, iou=0.5, classes=class_indices)
                for result in results:
                    boxes = result.boxes
                    for box in boxes:
                        x1, y1, x2, y2 = map(int, box.xyxy[0])
                        conf = box.conf[0]
                        cls = int(box.cls[0])
                        label = f"{yolo_labels[cls]} {conf:.2f}"
                        cv.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                        cv.putText(frame, label, (x1, y1 - 10), cv.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
            except Exception as e:
                print(f"Error in YOLO detection: {e}")
        #process_this_frame = not process_this_frame

        success, jpeg_frame = cv.imencode('.jpg', frame)
        if not success:
            print(f"Failed to encode frame for camera: {camera_name}")
            continue

        frame_bytes = jpeg_frame.tobytes()
        with camera_locks[camera_name]:
            active_cameras[camera_name]["frame"] = frame_bytes

        cv.waitKey(1)
        
    cap.release()
    print(f"Camera stream for {camera_name} has stopped")

@bp.route("/", methods=["GET"])
@permission_required("READ_VIDEO_CAMERA")
def get_cameras_list(current_user):
    db = get_tenant_db()
    cameras = db.query(VideoCamera).all()
    cameras_list = []
    for camera in cameras:
        if camera.name not in active_cameras:
            status = "inactive"
        else:
            status = "active" if active_cameras[camera.name]["running"] else "inactive"

        camera_info = {
            "id": camera.id,
            "ip": camera.ip,
            "port": camera.port,
            "username": camera.username,
            "password": camera.password,
            "name": camera.name,
            "location": camera.location,
            "status": status,
              "filters": active_cameras[camera.name]["filters"] if camera.name in active_cameras else {
            "face_recognition": False,
            }
        }
        cameras_list.append(camera_info)

    return {"cameras": cameras_list}, 200

@bp.route("/<int:camera_id>", methods=["GET"])
@permission_required("READ_VIDEO_CAMERA")
def get_camera_by_id(current_user, camera_id):
    db = get_tenant_db()
    camera = db.query(VideoCamera).filter_by(id=camera_id).first()
    if not camera:
        return {"message": "Camera not found"}, 404

    if camera.name not in active_cameras:
        status = "inactive"
    else:
        status = "active" if active_cameras[camera.name]["running"] else "inactive"

    camera_info = {
        "id": camera.id,
        "ip": camera.ip,
        "port": camera.port,
        "username": camera.username,
        "password": camera.password,
        "name": camera.name,
        "location": camera.location,
        "status": status,
        "filters": active_cameras[camera.name]["filters"] if camera.name in active_cameras else {
            "face_recognition": False,
        }
    }
    return {"camera": camera_info}, 200

@bp.route("/<string:camera_name>/stream", methods=["GET"])
def get_camera(camera_name):
    res, code = validate_token(request.args.get("token"))
    if code != 200:
        return res, code
    current_user = res

    valid_filters = [
        "Excavator", "Gloves", "Hardhat", "Ladder", "Mask", "NO-Hardhat", "NO-Mask", "NO-Safety Vest",
        "Person", "SUV", "Safety Cone", "Safety Vest", "bus", "dump truck", "fire hydrant", "machinery",
        "mini-van", "sedan", "semi", "trailer", "truck", "truck and trailer", "van", "vehicle", "wheel loader","face_recognition"
    ]
    activated_filters = []
    for arg in request.args:
        if arg in valid_filters:
            if request.args.get(arg).lower() == "true":
                activated_filters.append(arg)

    db = get_tenant_db()
    camera = db.query(VideoCamera).filter_by(name=camera_name).first()
    if not camera:
        return {"message": "Camera not found"}, 404
    
    known_face_encodings = []
    known_face_names = []
    if "face_recognition" in activated_filters:
        try:
            employees = db.query(Employee).all()
            known_face_encodings = [np.load(io.BytesIO(employee.encodedFace)) for employee in employees if hasattr(employee, 'encodedFace') and employee.encodedFace]
            known_face_names = [f"{employee.firstName} {employee.lastName}" for employee in employees if hasattr(employee, 'encodedFace') and employee.encodedFace]
            print(f"Loaded {len(known_face_encodings)} face encodings for recognition")
        except Exception as e:
            print(f"Error loading face data: {e}")
            return {"message": "Internal server error"}, 500


    # Here the RTSP stream should be read and returned
    #rtsp_url = f"rtsp://{camera.username}:{camera.password}@{camera.ip}:{camera.port}/stream2"
    rtsp_url = 0
    if camera_name not in active_cameras:
        active_cameras[camera_name] = {
            "frame": None,
            "clients": 0,
            "running": False,
            "filters": activated_filters,
            "thread": None,
            "cap": None
        }
        camera_locks[camera_name] = Lock()

    with camera_locks[camera_name]:
        active_cameras[camera_name]["clients"] += 1
        clients = active_cameras[camera_name]["clients"]
        print(f"New client connected to camera {camera_name}. Total clients: {clients}")
    
        # Check if the camera is already running and if it has any filters activated
        # if the camera is running and filters have changed
        if active_cameras[camera_name]["running"] and active_cameras[camera_name]["filters"] != activated_filters:
            print(f"Restarting camera stream for {camera_name} due to filter change")
            
            if active_cameras[camera_name]["cap"]:
                active_cameras[camera_name]["cap"].release()
            active_cameras[camera_name]["running"] = False
            active_cameras[camera_name]["frame"] = None

            print("Am ajuns aici")
            old_thread = active_cameras[camera_name]["thread"]
            if old_thread is not None and old_thread.is_alive():
                print(f"Waiting for old stream thread for {camera_name} to finish...")
                old_thread.join(timeout=1)
                print("Old stream thread finished")

        active_cameras[camera_name]["filters"] = activated_filters

        if not active_cameras[camera_name]["running"]:
            active_cameras[camera_name]["running"] = True
            process_thread = Thread(target=process_camera_frames,
                                    args=(camera_name, rtsp_url, activated_filters,
                                          known_face_encodings, known_face_names))
            process_thread.daemon = True
            active_cameras[camera_name]["thread"] = process_thread
            process_thread.start()
    
    def generate_frames_for_client():
        try:
            while True:
                # Check if camera is still running and get current frame
                with camera_locks[camera_name]:
                    if not camera_name in active_cameras or not active_cameras[camera_name]["running"]:
                        break
                    
                    frame = active_cameras[camera_name]["frame"]
                
                if frame is not None:
                    yield (b'--frame\r\n'
                          b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')
                else:
                    time.sleep(0.1)
                    continue
                
                time.sleep(0.066) # ~ 15 fps
        finally:
            # Decrement client count when this client disconnects
            if camera_name in active_cameras and camera_name in camera_locks:
                with camera_locks[camera_name]:
                    active_cameras[camera_name]["clients"] -= 1
                    remaining = active_cameras[camera_name]["clients"]
                    print(f"Client disconnected from camera {camera_name}. Remaining clients: {remaining}")
                
    return Response(generate_frames_for_client(), mimetype='multipart/x-mixed-replace; boundary=frame', headers={
        'Access-Control-Allow-Origin': 'http://127.0.0.1:5500',
        'Access-Control-Allow-Credentials': 'true'
    })

@bp.route("/<int:camera_id>", methods=["DELETE"])
@permission_required("CREATE_VIDEO_CAMERA") #TODO: Add new permission
def delete_camera(current_user, camera_id):
    try:
        db = get_tenant_db()
        if not camera_id:
            return {"message": "No camera ID provided"}, 400
        
        camera = db.query(VideoCamera).filter_by(id=camera_id).first()
        if not camera:
            return {"message": "Camera not found"}, 404
        
        if camera.name in active_cameras:
            with camera_locks[camera.name]:
                active_cameras[camera.name]["running"] = False
                if active_cameras[camera.name]["cap"]:
                    active_cameras[camera.name]["cap"].release()
                active_cameras.pop(camera.name, None)
            camera_locks.pop(camera.name, None)

        db.delete(camera)
        db.commit()
        return {"message": "Camera deleted successfully"}, 200
        
    except Exception as e:
        app.logger.error(e)
        return {"message": "Internal server error"}, 500

@bp.route('/<camera_name>/stream', methods=['OPTIONS'])
@permission_required("READ_VIDEO_STREAM")
def handle_options(current_user, camera_name):
    response = app.make_default_options_response()
    response.headers.add('Access-Control-Allow-Headers', 'Authorization, Content-Type')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    return response