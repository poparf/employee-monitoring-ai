from flaskr.entities.BaseEntity import Entity, mapped_column, Mapped
from typing import List
from sqlalchemy.orm import relationship

class User(Entity):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column()
    password: Mapped[str] = mapped_column()
    phoneNumber: Mapped[str] = mapped_column()
    is_verified: Mapped[bool] = mapped_column(default=False)

    email_codes: Mapped[List["EmailCodes"]] = relationship()

