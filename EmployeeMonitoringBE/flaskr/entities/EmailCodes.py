from flaskr.entities.BaseEntity import Entity, mapped_column, Mapped
from sqlalchemy import ForeignKey, DateTime
from datetime import datetime
from datetime import timedelta

class EmailCodes(Entity):
    __tablename__ = "email_codes"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now())
    expires_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now() + timedelta(minutes=5))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))