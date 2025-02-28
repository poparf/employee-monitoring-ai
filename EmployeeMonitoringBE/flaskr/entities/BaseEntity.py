from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Entity(DeclarativeBase):
    __abstract__ = True
