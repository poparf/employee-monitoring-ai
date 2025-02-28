from flaskr.entities.BaseEntity import Entity, mapped_column, Mapped
from datetime import datetime
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from typing import List

class PersonDetected(Entity):
    __tablename__ = "persons_detected"

    id: Mapped[int] = mapped_column(primary_key=True)
    detected_at: Mapped[datetime] = mapped_column(DateTime)

    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"))
    video_camera_id: Mapped[int] = mapped_column(ForeignKey("video_cameras.id"))

    ppe_recognitions: Mapped[List["PPERecognition"]] = relationship()