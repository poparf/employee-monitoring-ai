import uuid
from sqlalchemy import ForeignKey
from flaskr.entities.BaseEntity import  Mapped, mapped_column
from flaskr.entities.auth_db.AuthBaseEntity import AuthBaseEntity

class RoleUser(AuthBaseEntity):
    __tablename__ = "roles_users"
    role_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("roles.id"), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), primary_key=True)