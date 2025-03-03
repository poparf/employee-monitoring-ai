import uuid
from typing import List
from sqlalchemy import String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from flaskr.entities.BaseEntity import  mapped_column, Mapped
from flaskr.entities.auth_db.AuthBaseEntity import AuthBaseEntity


class Permission(AuthBaseEntity):
    __tablename__ = "permissions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)

    # Many-to-many relationship with Role
    roles: Mapped[List["Role"]] = relationship(secondary="role_permission", back_populates="permissions")
