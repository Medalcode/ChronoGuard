from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
from app.db.database import Base


class AuditLog(Base):
    """
    Modelo para registrar todos los eventos importantes en ChronoGuard.

    Este registro es crítico para:
    - Trazabilidad legal (auditoría)
    - Debugging de problemas
    - Detección de accesos no autorizados
    - Cumplimiento normativo (LGPD, GDPR)

    Eventos registrados:
    - LOGIN: Usuario inicia sesión
    - PING_SENT: Sistema envía correo de "¿estás bien?"
    - PING_ACKNOWLEDGED: Usuario confirma estar vivo
    - ASSET_ACCESSED: Se accede a un activo
    - SWITCH_TRIGGERED: Se activa el protocolo de sucesión
    """

    __tablename__ = "audit_logs"

    # ============ Identificador Único ============
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        comment="Identificador único del evento",
    )

    # ============ Relación con Usuario ============
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,  # Puede ser nulo si el evento no está asociado a un usuario específico
        index=True,
        comment="Usuario asociado al evento (nullable para eventos de sistema)",
    )

    # ============ Descripción del Evento ============
    event_type = Column(
        String(50),
        nullable=False,
        index=True,
        comment="Tipo de evento: LOGIN, PING_SENT, PING_ACKNOWLEDGED, ASSET_ACCESSED, SWITCH_TRIGGERED",
    )

    description = Column(
        String(500),
        nullable=True,
        comment="Descripción adicional del evento",
    )

    # ============ Contexto de Red ============
    ip_address = Column(
        String(45),  # IPv6 puede tener hasta 45 caracteres
        nullable=True,
        comment="Dirección IP desde la cual se originó el evento",
    )

    # ============ Timestamp ============
    timestamp = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
        comment="Fecha y hora del evento",
    )

    def __repr__(self):
        return f"<AuditLog(event_type={self.event_type}, user_id={self.user_id}, timestamp={self.timestamp})>"
