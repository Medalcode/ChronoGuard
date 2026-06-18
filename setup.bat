@echo off
:: ChronoGuard - Quick Start Script for Windows
:: Ejecuta con: .\setup.bat

echo ====================================
echo    ChronoGuard - Setup Inicial
echo ====================================

IF NOT EXIST ".env" (
    echo [1/4] Creando archivo .env...
    copy .env.example .env >nul
    echo   ^> Edita .env y agrega una SECRET_KEY
) ELSE (
    echo [1/4] Archivo .env ya existe
)

IF NOT EXIST "venv" (
    echo [2/4] Creando entorno virtual...
    python -m venv venv
) ELSE (
    echo [2/4] Entorno virtual ya existe
)

echo [3/4] Instalando dependencias...
call venv\Scripts\activate.bat
pip install -q -r requirements.txt

echo [4/4] Levantando PostgreSQL...
docker-compose up -d

echo.
echo ====================================
echo     SETUP COMPLETADO
echo ====================================
echo.
echo Para iniciar el servidor:
echo   uvicorn app.main:app --reload
echo.
echo Documentacion:
echo   http://localhost:8000/docs
echo.
echo Para correr tests:
echo   pytest tests/ -v
echo.

pause
