import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import decode_token
from app.db.database import get_db
from app.models.user import User

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """
    Dependencia de FastAPI para validar el token JWT y obtener el usuario actual.

    Este código se ejecuta automáticamente en cualquier ruta protegida donde
    injectes esta dependencia.

    Args:
        credentials: Token Bearer extraído automáticamente del header Authorization
        db: Sesión de base de datos

    Returns:
        User: Objeto del usuario si el token es válido

    Raises:
        HTTPException 401: Si el token es inválido o está expirado
        HTTPException 404: Si el usuario no existe
    """
    token = credentials.credentials

    try:
        # Decodificamos el JWT
        payload = decode_token(token)
        user_id = payload.get("sub")

        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido: no contiene el ID del usuario",
                headers={"WWW-Authenticate": "Bearer"},
            )

    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expirado o inválido",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Buscamos el usuario en la base de datos
    user = db.query(User).filter(User.id == user_id).first()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario inactivo",
        )

    return user
