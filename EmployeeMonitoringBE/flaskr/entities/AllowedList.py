from flaskr.entities.BaseEntity import Entity, mapped_column, Mapped
from enum import Enum
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship

class AllowedListStatus(Enum):
    allowed = "allowed"
    not_allowed = "not_allowed"

class AllowedList(Entity):
    __tablename__ = "allowed_lists"

    id: Mapped[int] = mapped_column(primary_key=True)
    status: Mapped[AllowedListStatus] = mapped_column()
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"))
    zone_id: Mapped[int] = mapped_column(ForeignKey("zones.id"))

    employee = relationship("Employee", back_populates="allowed_lists")
    zone = relationship("Zone", back_populates="allowed_lists")