from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# ============ Configuración de SQLAlchemy ============
# El engine es la conexión a PostgreSQL
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,  # Verifica la conexión antes de usarla (previene desconexiones)
    echo=settings.ENVIRONMENT == "development",  # Imprime SQL si estamos en desarrollo
)

# SessionLocal es la fábrica de sesiones que usaremos en las rutas
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base es la clase padre de todos nuestros modelos SQLAlchemy
Base = declarative_base()


def get_db():
    """
    Dependencia de FastAPI para inyectar una sesión de base de datos en las rutas.

    Yields:
        Session: Una sesión de SQLAlchemy conectada a PostgreSQL.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
