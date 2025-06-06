# Personal Protective Equipment (PPE) entity
from flaskr.entities.BaseEntity import Entity, mapped_column, Mapped
from sqlalchemy.orm import relationship
from typing import List

class PPE(Entity):
    __tablename__ = "ppes"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column()

    ppe_recognitions: Mapped[List["PPERecognition"]] = relationship()

    def to_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}