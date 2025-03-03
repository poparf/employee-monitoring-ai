import uuid
from sqlalchemy import ForeignKey
from flaskr.entities.BaseEntity import  Mapped, mapped_column
from flaskr.entities.auth_db.AuthBaseEntity import AuthBaseEntity

class RolePermission(AuthBaseEntity):
    __tablename__ = "role_permission"

    role_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("roles.id"), primary_key=True)
    permission_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("permissions.id"), primary_key=True)
