import uuid
from typing import List
from sqlalchemy import String, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from flaskr.entities.auth_db.AuthBaseEntity import AuthBaseEntity
from flaskr.entities.auth_db.Tenant import Tenant
from flaskr.entities.auth_db.EmailCodes import EmailCodes
from flaskr.entities.auth_db.Role import Role
from flaskr.entities.auth_db.RoleUser import RoleUser

class User(AuthBaseEntity):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    password: Mapped[str] = mapped_column(String(100), nullable=False)
    phoneNumber: Mapped[str] = mapped_column(String(15), nullable=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id"), nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)

    # Relationships
    tenant: Mapped["Tenant"] = relationship(back_populates="users")
    email_codes: Mapped[List["EmailCodes"]] = relationship(back_populates="user")

    # Many-to-many relationship with Role
    roles: Mapped[List["Role"]] = relationship(secondary="roles_users")