import logging
from datetime import UTC, datetime

from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.models.audit_log import AuditLog
from app.models.switch_configuration import SwitchConfiguration

logger = logging.getLogger(__name__)


def evaluate_dead_mans_switches():
    db: Session = SessionLocal()

    try:
        logger.info("Iniciando evaluación de Dead Man's Switches...")

        configs = db.query(SwitchConfiguration).all()

        if not configs:
            logger.info("No hay usuarios configurados aún")
            return

        for config in configs:
            days_inactive = (datetime.now(UTC) - config.last_active_at).days

            if days_inactive >= config.ping_interval_days and config.status == "ACTIVE":
                logger.info(
                    "PING: Usuario %s lleva %d días inactivo",
                    config.user_id,
                    days_inactive,
                )

                audit = AuditLog(
                    user_id=config.user_id,
                    event_type="PING_SENT",
                    description=f"Ping enviado tras {days_inactive} días de inactividad",
                )
                db.add(audit)

            elif days_inactive >= config.trigger_after_days and config.status != "TRIGGERED":
                logger.warning(
                    "TRIGGER: Usuario %s superó %d días sin actividad",
                    config.user_id,
                    config.trigger_after_days,
                )

                config.status = "TRIGGERED"

                audit = AuditLog(
                    user_id=config.user_id,
                    event_type="SWITCH_TRIGGERED",
                    description=f"Dead Man's Switch activado tras {days_inactive} días de inactividad",
                )
                db.add(audit)

        db.commit()
        logger.info("Evaluación completada")

    except Exception as e:
        logger.error("Error durante evaluación: %s", e)
        db.rollback()

    finally:
        db.close()


def start_scheduler():
    scheduler = BackgroundScheduler()

    scheduler.add_job(
        evaluate_dead_mans_switches,
        "cron",
        hour=3,
        minute=0,
        id="evaluate_switches",
        name="Evaluar Dead Man's Switches",
        replace_existing=True,
    )

    scheduler.start()
    logger.info("Scheduler iniciado - Dead Man's Switch monitoreando inactividad")
