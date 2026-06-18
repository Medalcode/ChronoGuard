import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.v1.dependencies import get_current_user
from app.core.config import settings
from app.db.database import get_db
from app.schemas.user_schema import Token, UserCreate, UserLogin, UserResponse
from app.services.auth_service import AuthService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Autenticación"])


def _check_rate_limit(request: Request):
    if settings.ENVIRONMENT == "test":
        return
    ip = request.client.host if request.client else "unknown"
    state = request.app.state
    if not hasattr(state, "_rate_limits"):
        state._rate_limits = {}

    now = __import__("time").time()
    window = state._rate_limits.get(ip, [])
    window = [t for t in window if t > now - 60]
    window.append(now)
    state._rate_limits[ip] = window

    if len(window) > settings.RATE_LIMIT_PER_MINUTE:
        logger.warning("Rate limit exceeded for IP: %s", ip)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Demasiadas solicitudes. Intenta de nuevo en un minuto.",
        )


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
def register(
    request: Request,
    user_in: UserCreate,
    db: Session = Depends(get_db),
):
    _check_rate_limit(request)
    user_response, access_token = AuthService.register_user(user_in, db)

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "vault_salt": user_response.vault_salt,
    }


@router.post("/login", response_model=Token)
def login(
    request: Request,
    user_in: UserLogin,
    db: Session = Depends(get_db),
):
    _check_rate_limit(request)
    user_response, access_token = AuthService.login_user(user_in.email, user_in.password, db)

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "vault_salt": user_response.vault_salt,
    }


@router.get("/me", response_model=UserResponse)
def get_current_user_info(
    current_user=Depends(get_current_user),
):
    return current_user
