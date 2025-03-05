from flaskr.entities.BaseEntity import Entity, mapped_column, Mapped
from enum import Enum
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship

class Blacklist(Entity):
    __tablename__ = "Blacklist"

    id: Mapped[int] = mapped_column(primary_key=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"))
    zone_id: Mapped[int] = mapped_column(ForeignKey("zones.id"))