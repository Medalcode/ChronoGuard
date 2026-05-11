from sqlalchemy import Boolean, Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
from app.db.database import Base


class User(Base):
    """
    Modelo de Usuario en PostgreSQL.

    Campos clave:
    - id: Identificador único (UUID)
    - email: Correo electrónico (único)
    - password_hash: Hash bcrypt solo para autenticación
    - vault_salt: Salt único para derivar la llave de cifrado en el cliente
    - is_active: Estado de la cuenta
    """

    __tablename__ = "users"

    # ============ Identificador Único ============
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        comment="Identificador único del usuario (UUID v4)",
    )

    # ============ Autenticación ============
    email = Column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
        comment="Correo electrónico único del usuario",
    )

    password_hash = Column(
        String(255),
        nullable=False,
        comment="Hash bcrypt de la contraseña maestra (no se puede descifrar)",
    )

    # ============ Cifrado en Cliente (Zero-Knowledge) ============
    vault_salt = Column(
        String(64),
        nullable=False,
        unique=True,
        comment="Salt único para derivar la llave AES-256 en el frontend",
    )

    # ============ Estado de Cuenta ============
    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
        comment="Indica si la cuenta está activa",
    )

    # ============ Auditoría Temporal ============
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Fecha de creación de la cuenta",
    )

    updated_at = Column(
        DateTime(timezone=True),
        onupdate=func.now(),
        nullable=False,
        server_default=func.now(),
        comment="Fecha de última actualización",
    )

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email})>"
