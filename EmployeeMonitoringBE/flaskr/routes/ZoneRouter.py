from flask import Blueprint, current_app as app, request
from flaskr.middlewares.PermissionMiddleware import permission_required
from werkzeug.utils import secure_filename
from flaskr.db import get_tenant_db
from flaskr.entities.Zone import Zone
from flaskr.routes.VideoCameraRouter import active_cameras, camera_locks
import cv2 as cv
import numpy as np

bp = Blueprint("zone", __name__, url_prefix="/zone")


"""
Context flow:
Users with required permission draw on a canvas
the zone that they want the detection to happen
That canvas is transformed in an image
Image is sent to the backend already masked
What does this mask mean?

Every pixel besides the ones drawn over by the user
are transformed in black ( this is done on the client
to save computation/time/resources from the server)

The endpoint receives as a multipart/form-data
name,
mask, ( image file (blob file))
video_camera_id, ( required to know on which videocamera
was the mask applied)

blacklist will be referenced later
"""

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config["ALLOWED_EXTENSIONS"]



@bp.route("/", methods=["POST"])
@permission_required("CREATE_ZONE")
def create_zone(current_user):
    try:
        db = get_tenant_db()
        data = request.get_json()
        if "zone_name" not in data:
            return {"message": "Zone name is required"}, 400
        if "camera_id" not in data:
            return {"message": "Video camera id is required"}, 400
        if "points" not in data:
            return {"message": "Points are required"}, 400
        if "camera_name" not in data:
            return {"message": "Camera name is required"}, 400

        zone_name = data.get("zone_name")
        camera_id = data.get("camera_id")
        camera_name = data.get("camera_name")
        points = data.get("points")
    
        with camera_locks[camera_name]:
            frame_bytes = active_cameras[camera_name]["frame"]
            
        if not frame_bytes:
            return {"message": "Camera is not active"}, 400
            
        # Decode the JPEG bytes back to numpy array
        nparr = np.frombuffer(frame_bytes, np.uint8)
        frame_snapshot = cv.imdecode(nparr, cv.IMREAD_COLOR)
        
        if frame_snapshot is None:
            return {"message": "Failed to decode camera frame"}, 400
        polygon = np.array([[p["x"], p["y"]] for p in points], dtype=np.int32)
        polygon = polygon.reshape((-1, 1, 2))
        mask = np.zeros_like(frame_snapshot)
        cv.fillPoly(mask, [polygon], (255, 255, 255))
        masked_frame = cv.bitwise_and(frame_snapshot, mask)
        success_encode, encoded_mask = cv.imencode('.jpg', masked_frame)
        filename = secure_filename(zone_name)
        filepath = f"{app.config['MASK_ZONES_PATH']}/{filename}.png"
        zone = db.query(Zone).filter_by(name=zone_name).first()
        if zone:
            return {"message": "Zone with that name already exists"}, 400
        zone = Zone(
            name=zone_name,
            mask=filepath,
            video_camera_id=camera_id
        )

        with open(filepath, "wb") as f:
            f.write(encoded_mask.tobytes())
        db.add(zone)
        db.flush()
        db.commit()
        return {"message": "Zone created sucessfuly.", "zone":{
            "id": zone.id,
            "name": zone.name,
            "video_camera_id": zone.video_camera_id
        }}
    except Exception as e:
        app.logger.error(e)
        return {"message": "Something went wrong"}, 500

@bp.route("/", methods=["DELETE"])
@permission_required("DELETE_ZONE")
def delete_zone(current_user):
    try:
        data = request.get_json()
        if "zone_id" not in data:
            return {"message": "Zone id is required"}, 400
        zone_id = data["zone_id"]
        db = get_tenant_db()
        # TODO: Afla ce face syncrohnize session
        db.query(Zone).filter_by(id=zone_id).delete(synchronize_session=False)
        db.commit()
        return {"message": "Zone deleted sucessfuly"}, 200
    except Exception as e:
        app.logger.error(e)
        return {"message": "Something went wrong"}, 500