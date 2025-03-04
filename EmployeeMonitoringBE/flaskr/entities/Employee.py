from flaskr.entities.BaseEntity import Entity, mapped_column, Mapped
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
    
    encodedFace: Mapped[str] = mapped_column()
    profilePicture: Mapped[str] = mapped_column() # this wil represent the path to the image

    detection_list: Mapped[List["PersonDetected"]] = relationship("PersonDetected", back_populates="employee")
    alerts: Mapped[List["Alert"]] = relationship("Alert", back_populates="employee") 
    allowed_lists: Mapped[List["AllowedList"]] = relationship("AllowedList", back_populates="employee")