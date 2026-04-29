from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Configuración global de ChronoGuard.
    Las variables se cargan desde el archivo .env en la raíz del proyecto.
    """

    # ============ Metadata del Proyecto ============
    PROJECT_NAME: str = "ChronoGuard API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"

    # ============ Base de Datos (PostgreSQL) ============
    # Ejemplo: postgresql://postgres:password@localhost:5432/chronoguard_db
    DATABASE_URL: str

    # ============ Seguridad y JWT ============
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # ============ Configuración del Motor de Inactividad ============
    DEFAULT_PING_INTERVAL_DAYS: int = 7
    DEFAULT_TRIGGER_AFTER_DAYS: int = 30

    # ============ Configuración de Emails ============
    SMTP_HOST: str | None = None
    SMTP_PORT: int | None = None
    SMTP_USER: str | None = None
    SMTP_PASSWORD: str | None = None
    EMAILS_FROM_EMAIL: str | None = None

    # ============ CORS y Seguridad ============
    ALLOWED_ORIGINS: list = [
        "http://localhost:3000",  # Frontend local
        "http://localhost:8000",  # API local
    ]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Instancia global de configuración
settings = Settings()
