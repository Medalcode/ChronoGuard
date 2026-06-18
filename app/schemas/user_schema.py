import re
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class UserCreate(BaseModel):
    email: EmailStr = Field(..., description="Correo electrónico único del usuario")
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Contraseña maestra. Debe contener mayúscula, minúscula, número y un carácter especial.",
    )

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        if not re.search(r"[A-Z]", v):
            raise ValueError("La contraseña debe contener al menos una mayúscula")
        if not re.search(r"[a-z]", v):
            raise ValueError("La contraseña debe contener al menos una minúscula")
        if not re.search(r"\d", v):
            raise ValueError("La contraseña debe contener al menos un número")
        if not re.search(r"[@$!%*?&._-]", v):
            raise ValueError("La contraseña debe contener al menos un carácter especial (@$!%*?&._-)")
        return v


class UserLogin(BaseModel):
    email: EmailStr = Field(..., description="Correo electrónico registrado")
    password: str = Field(..., description="Contraseña maestra")


class UserResponse(BaseModel):
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


class Token(BaseModel):
    access_token: str = Field(..., description="JWT para autenticación en requests futuros")
    token_type: str = Field(default="bearer", description="Tipo de token")
    vault_salt: str = Field(
        ...,
        description="Salt del usuario (necesario para el cliente derivar la llave local)",
    )
