"""
Servicio de Autenticación - Lógica de Negocio

Este módulo contiene toda la lógica de registro e inicio de sesión.
Separa la lógica de negocio de las rutas HTTP para mantener el código limpio y testeable.
"""

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import (
    create_access_token,
    generate_vault_salt,
    get_password_hash,
    verify_password,
)
from app.models.user import User
from app.schemas.user_schema import UserCreate, UserResponse


class AuthService:
    """
    Servicio de autenticación.
    Contiene toda la lógica para registro, login y validación de usuarios.
    """

    @staticmethod
    def register_user(user_in: UserCreate, db: Session) -> tuple[UserResponse, str]:
        """
        Registra un nuevo usuario en la base de datos.

        Args:
            user_in: Datos de entrada del usuario (email, password)
            db: Sesión de base de datos

        Returns:
            tuple: (UserResponse, access_token)

        Raises:
            HTTPException 400: Si el email ya está registrado
        """

        # Verificar si el email ya existe
        existing_user = db.query(User).filter(User.email == user_in.email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El correo electrónico ya está registrado",
            )

        # Generar seguridad
        password_hash = get_password_hash(user_in.password)
        vault_salt = generate_vault_salt()

        # Crear el nuevo usuario
        new_user = User(
            email=user_in.email,
            password_hash=password_hash,
            vault_salt=vault_salt,
        )

        # Guardar en la base de datos
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        # Generar token JWT
        access_token = create_access_token(new_user.id)

        # Convertir a UserResponse (excluye password_hash, incluye vault_salt)
        user_response = UserResponse.from_orm(new_user)

        return user_response, access_token

    @staticmethod
    def login_user(email: str, password: str, db: Session) -> tuple[UserResponse, str]:
        """
        Autentica un usuario existente.

        Args:
            email: Correo del usuario
            password: Contraseña del usuario
            db: Sesión de base de datos

        Returns:
            tuple: (UserResponse, access_token)

        Raises:
            HTTPException 401: Si las credenciales son inválidas
        """

        # Buscar el usuario
        user = db.query(User).filter(User.email == email).first()

        if not user or not verify_password(password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Correo o contraseña incorrectos",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Usuario inactivo",
            )

        # Generar token JWT
        access_token = create_access_token(user.id)

        # Convertir a UserResponse
        user_response = UserResponse.from_orm(user)

        return user_response, access_token
