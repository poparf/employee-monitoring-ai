from flask import current_app, Blueprint, request, Response, g
from flaskr.db import get_tenant_db, get_users_db
from flaskr.middlewares.PermissionMiddleware import permission_required
from flaskr.entities.VideoCamera import VideoCamera
from flaskr.entities.auth_db.User import User
from flaskr.entities.Employee import Employee
from flaskr.entities.Alert import Alert, AlertType, AlertLevel, AlertStatus
from flaskr.entities.alert_system.AlertRule import AlertRule
import jwt
import cv2 as cv
import numpy as np
import face_recognition
import io
from threading import Thread, Lock
import time
import dlib
from ultralytics import YOLO
from flaskr.services.rule_system.RuleInference import RuleInference
from flaskr.services.alert_manager.AlertManager import AlertManager
from flaskr.entities.Zone import Zone 
from sqlalchemy.orm import joinedload
import os
from collections import defaultdict
from flaskr.entities.alert_system.RuleCameraLink import RuleCameraLink
from flaskr.entities.alert_system.RuleZoneLink import RuleZoneLink
from datetime import datetime
#from flask_socketio import send

bp = Blueprint("video-cameras", __name__, url_prefix="/video-cameras")

active_cameras = {}  # camera_name: {"frame": bytes, "clients": count, "running": bool, "filters": [], thread: Thread}
camera_locks = {}    # camera_name: Lock

detected_objects = {}

def clear_detected_objects():
    for camera_name in detected_objects:
        for object_name in detected_objects[camera_name]:
            if detected_objects[camera_name][object_name]["timestamp"] < time.time() - 60:
                detected_objects[camera_name].pop(object_name, None)

def raise_person_detected_alert(camera_name, name, frame, app_instance, tenant_id):
    with app_instance.app_context():
        g.tenant_id = tenant_id
        
        # Raise alert
        employee_id = None
        
        if name != "Unknown":
            level = AlertLevel.LOW
            # get employee id
            db = get_tenant_db()
            name_splitted = name.split(" ")
            firstName = name_splitted[0]
            lastName = name_splitted[1]
            
            employee = db.query(Employee).filter_by(firstName=firstName, lastName=lastName).first()
            if employee:
                employee_id = employee.id
        else:
            level = AlertLevel.HIGH
        print(employee_id)
        # Save matLike frame as jpeg
        success, jpeg_frame = cv.imencode('.jpg', frame)
        screenshot_path = None
        if not success:
            print(f"Failed to encode frame for camera: {camera_name}")
        else:
            # Create directory path if needed
            alerts_path = current_app.config.get('ALERTS_SCREENSHOTS_PATH', 'flaskr/static/alert_screenshots')
            os.makedirs(alerts_path, exist_ok=True)
            
            # Generate organized filename including timestamp
            timestamp = int(time.time())
            date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{camera_name}_{date_str}.jpg"
            
            # Save the file in the proper directory
            full_screenshot_path = os.path.join(alerts_path, filename)
            with open(full_screenshot_path, "wb") as f:
                f.write(jpeg_frame.tobytes())
                
            # Store the relative path for serving via static routes
            screenshot_path = f"alert_screenshots/{filename}"
            
            print(f"Saved face detection screenshot at: {full_screenshot_path}")
            
        alert = Alert(type=AlertType.FACE_DETECTED, level=level, \
            screenshot=screenshot_path, status=AlertStatus.ACTIVE,\
                explanation=f"Face detected: {name}", employee_id=employee_id, 
                # Include the camera ID in the alert
                camera_id=db.query(VideoCamera).filter_by(name=camera_name).first().id if camera_name else None,
                zone_id=None)
        db.add(alert)
        db.commit()

def is_valid_port(port):
    return 0 <= int(port) <= 65535

def validate_token(token):
        try:
            data = jwt.decode(token, current_app.config["JWT_SECRET"], algorithms=["HS256"])
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
                          known_face_encodings,
                          known_face_names,
                          app_instance,
                          tenant_id):
    with app_instance.app_context():
        g.tenant_id = tenant_id
        print(f"Starting stream processing for {camera_name} in tenant {tenant_id}")

        db = get_tenant_db()
        camera = db.query(VideoCamera).filter_by(name=camera_name).first()
        if not camera:
            print(f"ERROR: Camera '{camera_name}' not found in tenant DB.")
            return
        camera_id = camera.id

        rules = db.query(AlertRule).options(
                joinedload(AlertRule.camera_links),
                joinedload(AlertRule.zone_links)
            ).filter(
                (AlertRule.camera_links.any(RuleCameraLink.camera_id == camera_id)) |
                (AlertRule.zone_links.any(RuleZoneLink.zone_id.in_(
                    db.query(Zone.id).filter(Zone.video_camera_id == camera_id)
                )))
            ).all()

        print(f"Found {len(rules)} rules relevant to camera {camera_name} (ID: {camera_id})")

        rule_inference = RuleInference(rules=rules)
        alert_manager = AlertManager(app_instance, tenant_id)

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

        #cap = cv.VideoCapture(rtsp_url)
        cap = cv.VideoCapture(0)
        cap.set(cv.CAP_PROP_BUFFERSIZE, 2)
        active_cameras[camera_name]["cap"] = cap
        if not cap.isOpened():
            print(f"Could not open stream for camera: {camera_name}")
            with camera_locks[camera_name]:
                active_cameras[camera_name]["running"] = False
            return

        object_dwell_times_local = defaultdict(dict)
        last_cleanup_time = time.time()
        cleanup_interval = 30

        while active_cameras[camera_name]["running"]:
            with camera_locks[camera_name]:
                if active_cameras[camera_name]["clients"] <= 0:
                    active_cameras[camera_name]["running"] = False
                    print(f"No more clients for camera {camera_name}, stopping stream")
                    break

            success, frame = cap.read()
            if not success:
                print(f"Failed to read frame for camera: {camera_name}. Retrying...")
                time.sleep(0.5)
                continue

            current_time = time.time()
            current_frame_ids = set()

            try:
                if "face_recognition" in filters and known_face_encodings:
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
                        if camera_name not in detected_objects:
                            detected_objects[camera_name] = {}
                            if "face_recognition" not in detected_objects[camera_name]:
                                detected_objects[camera_name]["face_recognition"] = {}
                            if name not in detected_objects[camera_name]["face_recognition"]:
                                detected_objects[camera_name]["face_recognition"][name] = {
                                    "first_seen": time.time(),
                                    "last_seen": time.time(),
                                    "dwell_time": 0                                   
                                }
                            else:
                                detected_objects[camera_name]["face_recognition"][name]["last_seen"] = time.time()
                                detected_objects[camera_name]["face_recognition"][name]["dwell_time"] = time.time() - detected_objects[camera_name]["face_recognition"][name]["first_seen"]
                                
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

            if model is not None:
                try:
                    class_indices = []
                    for idx, name in yolo_labels.items():
                        if name in yolo_active_filters:
                            class_indices.append(idx)

                    results = model.track(frame, conf=0.5, iou=0.5, classes=class_indices, persist=True, tracker="bytetrack.yaml")
                    
                    for result in results:
                        boxes = result.boxes
                        for box in boxes:
                            box_id = str(box.id.item())
                            current_frame_ids.add(box_id)
                            x1, y1, x2, y2 = map(int, box.xyxy[0])
                            conf = box.conf[0]
                            cls = int(box.cls[0])
                            label = f"{yolo_labels[cls]} {conf:.2f}"
                            cv.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                            cv.putText(frame, "#" + box_id + " " + label, (x1, y1 - 10), cv.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
                            
                            if camera_name not in detected_objects:
                                detected_objects[camera_name] = {}
                                if box_id not in detected_objects[camera_name]:
                                    detected_objects[camera_name][box_id] = {
                                        "timestamp": time.time(),
                                        "name": yolo_labels[cls],
                                        "first_seen": current_time,
                                        "last_seen": current_time,
                                        "dwell_time": 0,
                                    }
                                else:
                                    detected_objects[camera_name][box_id]["last_seen"] = current_time
                                    detected_objects[camera_name][box_id]["dwell_time"] = current_time - detected_objects[camera_name][box_id]["first_seen"]
                except Exception as e:
                    print(f"Error in YOLO detection: {e}")

            # Create a proper frame context with all required fields before inference
            frame_context = {
                "timestamp": current_time,
                "camera_id": camera_id,
                "detected_objects": {},  # Will be populated with object counts
                "detected_persons": [],  # Will store recognized person IDs
                "dwell_times": {},       # For tracking how long objects have been present
                "zones_entered": {},     # For zone detection
                "ppe_status": {}         # For PPE compliance tracking
            }
            
            # Add face recognition data to frame context if applicable
            if "face_recognition" in filters and camera_name in detected_objects and "face_recognition" in detected_objects[camera_name]:
                recognized_persons = []
                for name, data in detected_objects[camera_name]["face_recognition"].items():
                    if name != "Unknown":
                        # If we have a known person, add their ID to detected_persons
                        # This is a simplified approach - you might need to look up actual employee IDs
                        name_parts = name.split(" ")
                        if len(name_parts) >= 2:
                            first_name, last_name = name_parts[0], name_parts[1]
                            employee = db.query(Employee).filter_by(firstName=first_name, lastName=last_name).first()
                            if employee:
                                recognized_persons.append(employee.id)
                frame_context["detected_persons"] = recognized_persons
            
            # Process detected objects from YOLO
            if camera_name in detected_objects:
                object_counts = {}
                for box_id, obj_data in detected_objects[camera_name].items():
                    if box_id != "face_recognition":  # Skip the face recognition entry
                        obj_name = obj_data.get("name")
                        if obj_name:
                            # Count objects by type
                            object_counts[obj_name] = object_counts.get(obj_name, 0) + 1
                            # Add to dwell times
                            frame_context["dwell_times"][box_id] = {
                                "class_name": obj_name,
                                "dwell_time": obj_data.get("dwell_time", 0)
                            }
                frame_context["detected_objects"] = object_counts
            
            # IMPORTANT: Direct population of detected objects from YOLO results
            # This ensures that even newly detected objects in the current frame are included
            if model is not None and results:
                # Get detection counts directly from the current frame
                for result in results:
                    for box in result.boxes:
                        cls = int(box.cls[0])
                        cls_name = yolo_labels[cls]
                        # Add or increment the count for this object type
                        frame_context["detected_objects"][cls_name] = frame_context["detected_objects"].get(cls_name, 0) + 1
                
                print(f"Current frame detections: {frame_context['detected_objects']}")
            
            # Set the enriched frame context for inference
            alerts = rule_inference.infer(frame_context)
    
            for alert in alerts:
                res = alert_manager.process_alert(alert, frame)
                if res:
                    # signal the alert to the frontend
                    pass
                    
            if current_time - last_cleanup_time > cleanup_interval:
                disappeared_ids = []
                for box_id, data in object_dwell_times_local.items():
                    if box_id not in current_frame_ids:
                        disappeared_ids.append(box_id)
                for box_id in disappeared_ids:
                    del object_dwell_times_local[box_id]
                last_cleanup_time = current_time

            success_encode, jpeg_frame = cv.imencode('.jpg', frame)
            if not success_encode:
                print(f"Failed to encode frame for camera: {camera_name}")
                continue
            frame_bytes = jpeg_frame.tobytes()
            with camera_locks[camera_name]:
                if active_cameras.get(camera_name, {}).get("running"):
                     active_cameras[camera_name]["frame"] = frame_bytes

        cap.release()
        print(f"Camera stream processing stopped for {camera_name}")
        with camera_locks.get(camera_name, Lock()):
            if camera_name in active_cameras:
                active_cameras[camera_name]["running"] = False
                active_cameras[camera_name]["cap"] = None

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
    
        if active_cameras[camera_name]["running"] and active_cameras[camera_name]["filters"] != activated_filters:
            print(f"Restarting camera stream for {camera_name} due to filter change")
            
            if active_cameras[camera_name]["cap"]:
                active_cameras[camera_name]["cap"].release()
            active_cameras[camera_name]["running"] = False
            active_cameras[camera_name]["frame"] = None

            old_thread = active_cameras[camera_name]["thread"]
            if old_thread is not None and old_thread.is_alive():
                print(f"Waiting for old stream thread for {camera_name} to finish...")
                old_thread.join(timeout=1)
                print("Old stream thread finished")

        active_cameras[camera_name]["filters"] = activated_filters

        if not active_cameras[camera_name]["running"]:
            active_cameras[camera_name]["running"] = True
            app_instance = current_app._get_current_object()
            tenant_id_from_request = g.tenant_id
            process_thread = Thread(target=process_camera_frames,
                                    args=(camera_name, rtsp_url, activated_filters,
                                          known_face_encodings, known_face_names,
                                          app_instance, tenant_id_from_request))
            process_thread.daemon = True
            active_cameras[camera_name]["thread"] = process_thread
            process_thread.start()
    
    def generate_frames_for_client():
        try:
            while True:
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
                
                time.sleep(0.066)
        finally:
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
@permission_required("CREATE_VIDEO_CAMERA")
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
        current_app.logger.error(e)
        return {"message": "Internal server error"}, 500

@bp.route('/<camera_name>/stream', methods=['OPTIONS'])
@permission_required("READ_VIDEO_STREAM")
def handle_options(current_user, camera_name):
    response = current_app.make_default_options_response()
    response.headers.add('Access-Control-Allow-Headers', 'Authorization, Content-Type')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    return response