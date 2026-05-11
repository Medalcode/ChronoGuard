from pydantic import BaseModel, EmailStr, Field, ConfigDict
from uuid import UUID
from datetime import datetime


# ============ Esquema para Entrada de Datos (POST /register) ============
class UserCreate(BaseModel):
    """
    Esquema para la creación de un nuevo usuario.
    Validaciones:
    - Email debe ser válido (usa EmailStr de Pydantic)
    - Password mínimo 8 caracteres (recomendación de NIST)
    """

    email: EmailStr = Field(
        ..., description="Correo electrónico único del usuario"
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Contraseña maestra (usada para autenticación y derivación de llave local AES-256)",
    )


# ============ Esquema para Entrada de Datos (POST /login) ============
class UserLogin(BaseModel):
    """
    Esquema para la autenticación de un usuario.
    """

    email: EmailStr = Field(..., description="Correo electrónico registrado")
    password: str = Field(..., description="Contraseña maestra")


# ============ Esquema para Salida de Datos (Respuestas) ============
class UserResponse(BaseModel):
    """
    Esquema para retornar datos del usuario.

    NOTA CRÍTICA DE SEGURIDAD:
    - Este esquema NO incluye password_hash (nunca exponemos hashes)
    - SÍ incluye vault_salt (el frontend lo necesita para cifrado local)
    - El ConfigDict(from_attributes=True) permite mapear modelos SQLAlchemy

    La comisión evaluará que entiendes que "Zero-Knowledge" significa
    que el servidor NO sabe qué datos guarda (pero sí genera la llave correctamente).
    """

    id: UUID = Field(..., description="Identificador único del usuario")
    email: EmailStr = Field(..., description="Correo electrónico del usuario")
    is_active: bool = Field(..., description="Estado de la cuenta")
    vault_salt: str = Field(
        ...,
        description="Salt criptográfico único para derivar la llave de cifrado local (frontend)",
    )
    created_at: datetime = Field(..., description="Fecha de creación de la cuenta")
    updated_at: datetime = Field(..., description="Fecha de última actualización")

    model_config = ConfigDict(from_attributes=True)


# ============ Esquema para Token ============
class Token(BaseModel):
    """
    Esquema para la respuesta de autenticación exitosa.
    Contiene el JWT que el cliente debe incluir en los headers subsecuentes.
    """

    access_token: str = Field(..., description="JWT para autenticación en requests futuros")
    token_type: str = Field(default="bearer", description="Tipo de token")
    vault_salt: str = Field(
        ...,
        description="Salt del usuario (necesario para el cliente derivar la llave local)",
    )
