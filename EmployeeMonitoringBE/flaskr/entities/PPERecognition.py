from flaskr.entities.BaseEntity import Entity, mapped_column, Mapped
from sqlalchemy import ForeignKey

class PPERecognition(Entity):
    __tablename__ = "ppe_recognitions"

    id: Mapped[int] = mapped_column(primary_key=True)
    person_detected_id: Mapped[int] = mapped_column(ForeignKey("persons_detected.id"))
    ppe_id: Mapped[int] = mapped_column(ForeignKey("ppes.id"))