from sqlalchemy.orm import DeclarativeBase

class AuthBaseEntity(DeclarativeBase):
     __abstract__ = True
