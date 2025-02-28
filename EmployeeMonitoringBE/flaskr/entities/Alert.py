from flaskr.entities.BaseEntity import Entity, mapped_column, Mapped
from enum import Enum
from datetime import datetime
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship

class AlertType(Enum):
    PERSON_DETECTED = "person_detected"
    UNAUTHORIZED_PERSON_DETECTED = "unauthorized_person_detected"
    NO_HELMET_DETECTED = "no_helmet_detected"
    NO_MASK_DETECTED = "no_mask_detected"
    NO_VEST_DETECTED = "no_vest_detected"
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

    screenshot: Mapped[str] = mapped_column()
    status: Mapped[AlertStatus] = mapped_column()
    explanation: Mapped[str] = mapped_column()
    resolved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"))
    zone_id: Mapped[int] = mapped_column(ForeignKey("zones.id"))