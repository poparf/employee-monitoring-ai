from flaskr.entities.BaseEntity import Entity, mapped_column, Mapped
from sqlalchemy import ForeignKey
from enum import Enum

class PPEStatus(Enum):
    present = "present"
    not_present = "not_present"

class PPERecognition(Entity):
    __tablename__ = "ppe_recognitions"

    id: Mapped[int] = mapped_column(primary_key=True)
    video_camera_id: Mapped[int] = mapped_column(ForeignKey("video_cameras.id"))
    person_detected_id: Mapped[int] = mapped_column(ForeignKey("persons_detected.id"))
    status: Mapped[PPEStatus] = mapped_column()