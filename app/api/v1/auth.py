"""
Router de Autenticación - API v1

Define los endpoints REST para:
- POST /register: Crear nuevo usuario
- POST /login: Autenticarse
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.user_schema import UserCreate, UserLogin, UserResponse, Token
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Autenticación"])


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
def register(
    user_in: UserCreate,
    db: Session = Depends(get_db),
):
    """
    Registra un nuevo usuario en ChronoGuard.

    **Flujo de seguridad:**
    1. El backend recibe email y password
    2. Se genera un vault_salt único y criptográfico
    3. La contraseña se hashea con bcrypt (irreversible)
    4. El usuario y salt se guardan en PostgreSQL
    5. Se devuelve un JWT para mantener la sesión

    **Uso en Cliente:**
    El frontend recibe el vault_salt y lo usa para derivar la llave de cifrado local (AES-256)
    sin que el servidor jamás conozca esa llave.

    **Ejemplo de Request:**
    ```json
    {
        "email": "usuario@example.com",
        "password": "MiContraseña123"
    }
    ```

    **Ejemplo de Response:**
    ```json
    {
        "access_token": "eyJhbGciOiJIUzI1NiIsInR5...",
        "token_type": "bearer",
        "vault_salt": "a1b2c3d4e5f6..."
    }
    ```
    """
    user_response, access_token = AuthService.register_user(user_in, db)

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "vault_salt": user_response.vault_salt,
    }


@router.post("/login", response_model=Token)
def login(
    user_in: UserLogin,
    db: Session = Depends(get_db),
):
    """
    Autentica un usuario existente.

    **Flujo de seguridad:**
    1. Buscamos el usuario por email
    2. Verificamos la contraseña contra el hash bcrypt
    3. Si es válida, generamos un JWT de corta duración
    4. Devolvemos el JWT y el vault_salt

    **Uso en Cliente:**
    El cliente incluirá el JWT en el header Authorization: Bearer <token>
    en los requests subsecuentes. El servidor valida el token antes de procesar la petición.

    **Ejemplo de Request:**
    ```json
    {
        "email": "usuario@example.com",
        "password": "MiContraseña123"
    }
    ```

    **Ejemplo de Response:**
    ```json
    {
        "access_token": "eyJhbGciOiJIUzI1NiIsInR5...",
        "token_type": "bearer",
        "vault_salt": "a1b2c3d4e5f6..."
    }
    ```
    """
    user_response, access_token = AuthService.login_user(
        user_in.email, user_in.password, db
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "vault_salt": user_response.vault_salt,
    }


@router.get("/me", response_model=UserResponse)
def get_current_user_info(
    current_user=Depends(lambda db=Depends(get_db): db),
):
    """
    Devuelve la información del usuario actualmente autenticado.

    Requiere un JWT válido en el header Authorization.
    """
    # Esto se rellenará cuando conectemos la dependencia de usuarios
    pass
