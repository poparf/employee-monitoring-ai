from flaskr.entities.BaseEntity import Entity, mapped_column, Mapped
from enum import Enum
from sqlalchemy.orm import relationship
from typing import List

class VideoCamera(Entity):
    __tablename__ = "video_cameras"

    id: Mapped[int] = mapped_column(primary_key=True)
    ip: Mapped[str] = mapped_column()
    port: Mapped[str] = mapped_column()

    username: Mapped[str] = mapped_column()
    password: Mapped[str] = mapped_column()

    name: Mapped[str] = mapped_column()
    location: Mapped[str] = mapped_column()

    class CameraStatus(Enum):
        ACTIVE = "active"
        INACTIVE = "inactive"
        ERROR = "error"

    status: Mapped[CameraStatus] = mapped_column()

    persons_detected: Mapped[List["PersonDetected"]] = relationship()
    zones: Mapped[List["Zone"]] = relationship()
    rule_links: Mapped[List["RuleCameraLink"]] = relationship(
        "RuleCameraLink",
        back_populates="camera",
        cascade="all, delete-orphan"
    )