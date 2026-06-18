import logging
from contextlib import asynccontextmanager

import jwt
from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from app.api.v1.auth import router as auth_router
from app.core.config import settings
from app.workers.scheduler import start_scheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("%s iniciada correctamente", settings.PROJECT_NAME)
    logger.info("Ambiente: %s", settings.ENVIRONMENT)
    start_scheduler()
    yield
    logger.info("%s apagada", settings.PROJECT_NAME)


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="API segura de custodia digital con Dead Man's Switch",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api_router = APIRouter(prefix=settings.API_V1_STR)


@api_router.get("/health")
def health_check():
    return {
        "status": "healthy",
        "project": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
    }


api_router.include_router(auth_router)
app.include_router(api_router)


@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request, exc):
    logger.error("Database error: %s", exc)
    return JSONResponse(
        status_code=500,
        content={"error": "Database error", "detail": str(exc)},
    )


@app.exception_handler(jwt.PyJWTError)
async def jwt_exception_handler(request, exc):
    return JSONResponse(
        status_code=401,
        content={"detail": "Token inválido o expirado", "error": str(exc)},
        headers={"WWW-Authenticate": "Bearer"},
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.ENVIRONMENT == "development",
    )
