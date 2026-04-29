"""
Configuración del Scheduler - Dead Man's Switch

Este módulo configura APScheduler para ejecutar tareas en segundo plano.
En particular, monitorea la inactividad de los usuarios y ejecuta el protocolo
de sucesión cuando es necesario.
"""

from datetime import UTC, datetime

from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.models.audit_log import AuditLog
from app.models.switch_configuration import SwitchConfiguration


def evaluate_dead_mans_switches():
    """
    Función que se ejecuta periódicamente (ej. diariamente).

    Lógica:
    1. Consulta todas las configuraciones de switch
    2. Calcula días de inactividad para cada usuario
    3. Si está en rango de "ping", envía email de alerta
    4. Si superó el umbral, activa el protocolo de sucesión

    NOTA: En esta versión MVP, solo imprimimos en consola.
    En producción, esto enviaría correos reales vía SMTP.
    """
    db: Session = SessionLocal()

    try:
        print(f"\n[{datetime.now(UTC)}] Iniciando evaluación de Dead Man's Switches...")

        # Obtener todas las configuraciones de switch
        configs = db.query(SwitchConfiguration).all()

        if not configs:
            print("  ℹ️  No hay usuarios configurados aún")
            return

        for config in configs:
            days_inactive = (datetime.now(UTC) - config.last_active_at).days

            # ========== NIVEL 1: ALERTA TEMPRANA ==========
            if days_inactive >= config.ping_interval_days and config.status == "ACTIVE":
                print(f"\n📧 PING: Usuario {config.user_id} lleva {days_inactive} días inactivo")
                print("   → Enviando correo de 'Estás bien?'")

                # Registrar en audit log
                audit = AuditLog(
                    user_id=config.user_id,
                    event_type="PING_SENT",
                    description=f"Sistema envió ping después de {days_inactive} días de inactividad",
                )
                db.add(audit)
                # TODO: Aquí irá el código para enviar correo vía SMTP

            # ========== NIVEL 2: TRIGGER FINAL ==========
            elif days_inactive >= config.trigger_after_days and config.status != "TRIGGERED":
                print(
                    f"\n⚠️  CRÍTICO: Usuario {config.user_id} superó {config.trigger_after_days} días sin actividad"
                )
                print("   → ACTIVANDO protocolo de sucesión")

                # Cambiar estado a TRIGGERED
                config.status = "TRIGGERED"

                # Registrar el evento crítico
                audit = AuditLog(
                    user_id=config.user_id,
                    event_type="SWITCH_TRIGGERED",
                    description=f"Dead Man's Switch activado tras {days_inactive} días de inactividad total",
                )
                db.add(audit)

                # TODO: Aquí irá el código para enviar correos a herederos
                # TODO: Aquí irá el código para generar accesos temporales

        db.commit()
        print("\n✅ Evaluación completada")

    except Exception as e:
        print(f"\n❌ Error durante evaluación: {str(e)}")
        db.rollback()

    finally:
        db.close()


def start_scheduler():
    """
    Inicia el scheduler de APScheduler.

    Configura el trabajo para ejecutarse diariamente a las 03:00 AM UTC.
    (Hora óptima para no interferir con picos de tráfico de usuarios)
    """
    scheduler = BackgroundScheduler()

    # Agregar la tarea: ejecutar evaluate_dead_mans_switches diariamente a las 03:00 AM
    scheduler.add_job(
        evaluate_dead_mans_switches,
        "cron",
        hour=3,
        minute=0,
        id="evaluate_switches",
        name="Evaluar Dead Man's Switches",
        replace_existing=True,
    )

    # Para desarrollo/testing, descomenta esto para ejecutar cada 10 segundos:
    # scheduler.add_job(
    #     evaluate_dead_mans_switches,
    #     "interval",
    #     seconds=10,
    #     id="evaluate_switches",
    #     replace_existing=True,
    # )

    scheduler.start()
    print("🔔 Scheduler iniciado - Dead Man's Switch monitoreando inactividad")
