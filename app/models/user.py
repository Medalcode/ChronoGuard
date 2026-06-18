import uuid

from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.db.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )

    email = Column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )

    password_hash = Column(
        String(255),
        nullable=False,
    )

    vault_salt = Column(
        String(64),
        nullable=False,
        unique=True,
    )

    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
    )

    failed_login_attempts = Column(
        Integer,
        default=0,
        nullable=False,
        server_default="0",
    )

    locked_until = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at = Column(
        DateTime(timezone=True),
        onupdate=func.now(),
        nullable=False,
        server_default=func.now(),
    )

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email})>"
