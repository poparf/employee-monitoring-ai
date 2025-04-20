from flaskr.entities.BaseEntity import Entity, mapped_column, Mapped
from sqlalchemy import LargeBinary
from typing import List
from sqlalchemy.orm import relationship

class Employee(Entity):
    __tablename__ = "employees"

    id: Mapped[int] = mapped_column(primary_key=True)
    firstName: Mapped[str] = mapped_column()
    lastName: Mapped[str] = mapped_column()
    phoneNumber: Mapped[str] = mapped_column()
    role: Mapped[str] = mapped_column()
    department: Mapped[str] = mapped_column()
    
    encodedFace: Mapped[LargeBinary] = mapped_column(LargeBinary, nullable=True)
    profilePicture: Mapped[str] = mapped_column(nullable=True)

    detection_list: Mapped[List["PersonDetected"]] = relationship()
    alerts: Mapped[List["Alert"]] = relationship() 
    blacklist: Mapped[List["Blacklist"]] = relationship()