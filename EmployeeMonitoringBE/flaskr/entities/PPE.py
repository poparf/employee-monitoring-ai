# Personal Protective Equipment (PPE) entity
from flaskr.entities.BaseEntity import Entity, mapped_column, Mapped

class PPE(Entity):
    __tablename__ = "ppes"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column()
