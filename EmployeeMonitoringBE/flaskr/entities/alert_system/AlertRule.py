from flaskr.entities.BaseEntity import Entity, mapped_column, Mapped
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import List
from sqlalchemy import DateTime
from flaskr.entities.alert_system.RuleCameraLink import RuleCameraLink
from flaskr.entities.alert_system.RuleZoneLink import RuleZoneLink

class AlertRule(Entity):
    __tablename__ = "alert_rules"

    id: Mapped[int] = mapped_column(primary_key=True)
    description: Mapped[str] = mapped_column(nullable=True)
    is_active: Mapped[bool] = mapped_column(default=False)
    priority: Mapped[int] = mapped_column()
    
    conditions_json: Mapped[str] = mapped_column(nullable=False)
    action_details_json: Mapped[str] = mapped_column(nullable=False)

    cooldown_seconds: Mapped[int] = mapped_column(default=30)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now())

    camera_links: Mapped[List["RuleCameraLink"]] = relationship(back_populates="alert_rule", cascade="all, delete-orphan")
    zone_links: Mapped[List["RuleZoneLink"]] = relationship(back_populates="alert_rule", cascade="all, delete-orphan")
