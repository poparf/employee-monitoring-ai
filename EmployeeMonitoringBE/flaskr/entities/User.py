from flaskr.entities.BaseEntity import Entity, mapped_column, Mapped

class User(Entity):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column()
    password: Mapped[str] = mapped_column()
    email: Mapped[str] = mapped_column()
    phoneNumber: Mapped[str] = mapped_column()

