import logging
from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import (
    create_access_token,
    generate_vault_salt,
    get_password_hash,
    verify_password,
)
from app.models.switch_configuration import SwitchConfiguration
from app.models.user import User
from app.schemas.user_schema import UserCreate, UserResponse

logger = logging.getLogger(__name__)


def _now() -> datetime:
    return datetime.now(UTC)


def _as_aware(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt


class AuthService:

    @staticmethod
    def register_user(user_in: UserCreate, db: Session) -> tuple[UserResponse, str]:
        existing_user = db.query(User).filter(User.email == user_in.email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El correo electrónico ya está registrado",
            )

        password_hash = get_password_hash(user_in.password)
        vault_salt = generate_vault_salt()

        new_user = User(
            email=user_in.email,
            password_hash=password_hash,
            vault_salt=vault_salt,
        )
        db.add(new_user)
        db.flush()

        switch_config = SwitchConfiguration(
            user_id=new_user.id,
            ping_interval_days=settings.DEFAULT_PING_INTERVAL_DAYS,
            trigger_after_days=settings.DEFAULT_TRIGGER_AFTER_DAYS,
        )
        db.add(switch_config)

        logger.info("User registered: %s (switch config auto-created)", new_user.email)

        db.commit()
        db.refresh(new_user)

        access_token = create_access_token(new_user.id)
        user_response = UserResponse.model_validate(new_user)

        return user_response, access_token

    @staticmethod
    def login_user(email: str, password: str, db: Session) -> tuple[UserResponse, str]:
        user = db.query(User).filter(User.email == email).first()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Correo o contraseña incorrectos",
                headers={"WWW-Authenticate": "Bearer"},
            )

        locked_until = _as_aware(user.locked_until)
        if locked_until and locked_until > _now():
            remaining = int((locked_until - _now()).total_seconds())
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Cuenta bloqueada. Intenta de nuevo en {remaining} segundos",
            )

        if not verify_password(password, user.password_hash):
            user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
            if user.failed_login_attempts >= settings.MAX_LOGIN_ATTEMPTS:
                user.locked_until = _now() + timedelta(
                    minutes=settings.ACCOUNT_LOCKOUT_MINUTES
                )
                logger.warning(
                    "Account locked: %s (attempts=%d)",
                    user.email,
                    user.failed_login_attempts,
                )
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Correo o contraseña incorrectos",
                headers={"WWW-Authenticate": "Bearer"},
            )

        user.failed_login_attempts = 0
        user.locked_until = None

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Usuario inactivo",
            )

        access_token = create_access_token(user.id)
        user_response = UserResponse.model_validate(user)

        logger.info("User logged in: %s", user.email)

        db.commit()

        return user_response, access_token
