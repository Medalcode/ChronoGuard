"""
ChronoGuard Backend - Punto de Entrada Principal

Este archivo inicializa la aplicación FastAPI y configura todos los componentes:
- Modelos de base de datos
- Rutas de API
- Middleware de seguridad
- Tareas en segundo plano (Background Jobs)
"""

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings
from app.workers.scheduler import start_scheduler

# ============ Crear la Aplicación FastAPI ============
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="API segura de custodia digital con Dead Man's Switch",
)

# ============ Configurar CORS ============
# Permite que el frontend (que probablemente esté en otro puerto) acceda a la API
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============ Incluir Rutas de API v1 ============
# Aquí incluiremos los routers cuando los creemos
# Por ahora, creamos un router básico para pruebas

api_router = APIRouter(prefix=settings.API_V1_STR)


@api_router.get("/health")
def health_check():
    """
    Endpoint de prueba para verificar que la API está funcionando.
    Útil para verificar que PostgreSQL está conectado y la app levantó correctamente.
    """
    return {
        "status": "healthy",
        "project": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
    }


app.include_router(api_router)

# ============ Iniciar el Scheduler en Segundo Plano ============
# El motor de inactividad (Dead Man's Switch) se ejecutará periódicamente
# Este es un componente crítico que revisa la BD y envía emails automáticamente


@app.on_event("startup")
async def startup_event():
    """Se ejecuta cuando la aplicación arranca."""
    start_scheduler()
    print(f"✅ {settings.PROJECT_NAME} iniciada correctamente")
    print("📚 API Docs disponible en: /docs")
    print(f"🔒 Ambiente: {settings.ENVIRONMENT}")


@app.on_event("shutdown")
async def shutdown_event():
    """Se ejecuta cuando la aplicación se apaga."""
    print(f"🛑 {settings.PROJECT_NAME} apagada")


# ============ Manejo de Errores Global ============
@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request, exc):
    """Captura errores de base de datos y los maneja correctamente."""
    return {
        "error": "Database error",
        "detail": str(exc),
    }


if __name__ == "__main__":
    # Para desarrollo, ejecuta con:
    # uvicorn app.main:app --reload
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.ENVIRONMENT == "development",
    )
