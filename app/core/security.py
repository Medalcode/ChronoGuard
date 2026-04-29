import secrets
from datetime import UTC, datetime, timedelta

import jwt
from passlib.context import CryptContext

from app.core.config import settings

# ============ Configuración del Hashing de Contraseñas ============
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def generate_vault_salt() -> str:
    """
    Genera una cadena aleatoria criptográficamente segura.
    Este salt es único por usuario y se envía al frontend para derivar la llave AES-GCM local.

    Returns:
        str: Una cadena hexadecimal de 64 caracteres (256 bits).
    """
    return secrets.token_hex(32)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifica si una contraseña en texto plano coincide con su hash bcrypt.

    Args:
        plain_password: Contraseña ingresada por el usuario.
        hashed_password: Hash almacenado en la base de datos.

    Returns:
        bool: True si coinciden, False en caso contrario.
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Genera el hash bcrypt de una contraseña en texto plano.

    Args:
        password: Contraseña en texto plano.

    Returns:
        str: Hash bcrypt de la contraseña.
    """
    return pwd_context.hash(password)


def create_access_token(subject: str | int) -> str:
    """
    Genera un JSON Web Token (JWT) para la sesión del usuario.

    Args:
        subject: Generalmente el ID del usuario (UUID como string).

    Returns:
        str: Token JWT codificado.
    """
    expire = datetime.now(UTC) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    # Payload del token: quién es (sub) y cuándo expira (exp)
    to_encode = {"exp": expire, "sub": str(subject)}

    # Firmamos el token con la SECRET_KEY
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    return encoded_jwt


def decode_token(token: str) -> dict:
    """
    Decodifica y valida un JWT.

    Args:
        token: Token JWT a decodificar.

    Returns:
        dict: Payload del token si es válido.

    Raises:
        jwt.InvalidTokenError: Si el token es inválido o está expirado.
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except jwt.InvalidTokenError:
        raise
