from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
import jwt

from app.db.database import get_db
from app.core.config import settings
from app.core.security import decode_token
from app.models.user import User

# Definimos el esquema de autenticación (dónde el cliente puede obtener el token)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> User:
    """
    Dependencia de FastAPI para obtener el usuario autenticado actual.
    
    1. Extrae el token del header (Authorization: Bearer <token>)
    2. Decodifica y valida el token JWT
    3. Busca al usuario en la base de datos
    4. Verifica que el usuario esté activo
    
    Si alguna validación falla, arroja HTTP 401 (Unauthorized) o HTTP 400.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = decode_token(token)
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except jwt.InvalidTokenError:
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id).first()
    
    if user is None:
        raise credentials_exception
        
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Usuario inactivo")
        
    return user
