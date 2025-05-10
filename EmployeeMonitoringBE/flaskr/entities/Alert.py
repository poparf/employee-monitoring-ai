from flaskr.entities.BaseEntity import Entity, mapped_column, Mapped
from enum import Enum
from datetime import datetime
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey

class AlertType(Enum):
    PERSON_DETECTED = "person_detected"
    UNAUTHORIZED_PERSON_DETECTED = "unauthorized_person_detected"
    NO_HELMET_DETECTED = "no_helmet_detected"
    NO_MASK_DETECTED = "no_mask_detected"
    NO_VEST_DETECTED = "no_vest_detected"
    NO_GLOVES_DETECTED = "no_gloves_detected"
    FACE_DETECTED = "face_detected"

class AlertLevel(Enum):
        LOW = "low"
        MEDIUM = "medium"
        HIGH = "high"

class AlertStatus(Enum):
    ACTIVE = "active"
    RESOLVED = "resolved"

class Alert(Entity):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(primary_key=True)
    type: Mapped[AlertType] = mapped_column()
    level: Mapped[AlertLevel] = mapped_column()
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now)

    screenshot: Mapped[str] = mapped_column(nullable=True)
    status: Mapped[AlertStatus] = mapped_column()
    explanation: Mapped[str] = mapped_column()
    resolved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"), nullable=True)
    zone_id: Mapped[int] = mapped_column(ForeignKey("zones.id"), nullable=True)
    camera_id: Mapped[int] = mapped_column(ForeignKey("video_cameras.id"), nullable=True)
    alert_rule_id: Mapped[int] = mapped_column(ForeignKey("alert_rules.id"), nullable=True)

    def to_dict(self):
        """Converts the Alert object to a JSON-serializable dictionary."""
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            if isinstance(value, Enum):
                # Convert Enum members to their string values
                result[column.name] = value.value
            elif isinstance(value, datetime):
                # Convert datetime objects to ISO 8601 string format
                # Handle potential None values for nullable datetime fields like resolved_at
                result[column.name] = value.isoformat() if value else None
            else:
                # Keep other types as they are (assuming they are serializable)
                result[column.name] = value
        return result