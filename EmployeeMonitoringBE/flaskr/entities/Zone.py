from flaskr.entities.BaseEntity import Entity, mapped_column, Mapped
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from typing import List
from sqlalchemy.orm import relationship

class Zone(Entity):
    __tablename__ = "zones"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column()
    # Path to the mask image
    mask: Mapped[str] = mapped_column()

    video_camera_id: Mapped[int] = mapped_column(ForeignKey("video_cameras.id"))
    blacklist: Mapped[List["Blacklist"]] = relationship()

