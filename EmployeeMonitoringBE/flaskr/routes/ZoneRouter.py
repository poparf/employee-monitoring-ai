from flask import Blueprint, current_app as app, request
from flaskr.middlewares.PermissionMiddleware import permission_required
from werkzeug.utils import secure_filename
from flaskr.db import get_tenant_db
from flaskr.entities.Zone import Zone

bp = Blueprint("zone", __name__, "/zone")


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

@bp.route("/", methods="POST")
@permission_required("CREATE_ZONE")
def create_zone(current_user):
    try:
        if "name" not in request.form:
            return {"message": "Name of the zone is required"}, 400
        if "mask" not in request.files:
            return {"message": "Mask image is required"}, 400
        if "video_camera_id" not in request.form:
            return {"message": "Video camera id is required"}, 400
        if not allowed_file(request.files["mask"].filename):
            return {"message": "Invalid file"}, 400
        
        name = request.form.get("name")
        mask = request.files["mask"]
        video_camera_id = request.form.get("video_camera_id")

        zone = db.query(Zone).filter_by(name=name).first()
        if zone:
            return {"message": "Zone with that name already exists"}, 400
        zone = Zone(
            name=name,
            mask=f"{app.config['MASK_ZONES_PATH']}/{mask.filename}.png",
            video_camera_id=video_camera_id
        )

        filename = secure_filename(mask.filename)
        mask.save(f"{app.config['MASK_ZONES_PATH']}/{filename}.png")
        db = get_tenant_db()
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