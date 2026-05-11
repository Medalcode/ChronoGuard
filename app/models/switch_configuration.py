from sqlalchemy import Column, Integer, DateTime, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
from app.db.database import Base


class SwitchConfiguration(Base):
    """
    Modelo para la configuración del "Dead Man's Switch" de cada usuario.

    Campos:
    - user_id: Referencia al usuario propietario
    - ping_interval_days: Cada cuántos días se envía el ping de "¿Estás bien?"
    - trigger_after_days: Cuántos días de silencio para activar el protocolo de sucesión
    - last_active_at: Última vez que el usuario confirmó estar vivo
    - status: Estado del switch (ACTIVE, WARNING, TRIGGERED)
    """

    __tablename__ = "switch_configurations"

    # ============ Identificador Único ============
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        comment="Identificador único de la configuración",
    )

    # ============ Relación con Usuario ============
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
        comment="Referencia única al usuario propietario",
    )

    # ============ Configuración de Tiempo ============
    ping_interval_days = Column(
        Integer,
        default=7,
        nullable=False,
        comment="Número de días entre intentos de contacto automático",
    )

    trigger_after_days = Column(
        Integer,
        default=30,
        nullable=False,
        comment="Número de días de inactividad para ejecutar el protocolo de sucesión",
    )

    # ============ Monitoreo de Actividad ============
    last_active_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Timestamp de la última actividad confirmada del usuario",
    )

    # ============ Estado del Sistema ============
    status = Column(
        String(20),
        default="ACTIVE",
        nullable=False,
        comment="Estado del switch: ACTIVE, WARNING, TRIGGERED",
    )

    # ============ Auditoría ============
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Fecha de creación de la configuración",
    )

    updated_at = Column(
        DateTime(timezone=True),
        onupdate=func.now(),
        nullable=False,
        server_default=func.now(),
        comment="Fecha de última actualización",
    )

    def __repr__(self):
        return f"<SwitchConfiguration(user_id={self.user_id}, status={self.status})>"
