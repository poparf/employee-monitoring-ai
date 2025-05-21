from flaskr.entities.BaseEntity import Entity, mapped_column, Mapped, relationship
from sqlalchemy import ForeignKey

class RuleCameraLink(Entity):
    __tablename__ = "rule_camera_links"

    id: Mapped[int] = mapped_column(primary_key=True)
    rule_id: Mapped[int] = mapped_column(ForeignKey("alert_rules.id"), nullable=False)
    camera_id: Mapped[int] = mapped_column(ForeignKey("video_cameras.id"), nullable=False)
        camera = relationship("VideoCamera", back_populates="rule_links")