#!/bin/bash
# Windows Setup Script
# Para PowerShell, ejecuta: .\setup.bat

echo Starting ChronoGuard Setup...

if not exist ".env" (
    echo Creating .env file...
    copy .env.example .env
    echo Please edit .env and add a SECRET_KEY (generate with: openssl rand -hex 32)
)

if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Installing dependencies...
pip install -r requirements.txt

echo Starting PostgreSQL...
docker-compose up -d

echo.
echo Setup completed!
echo Run "uvicorn app.main:app --reload" to start the server
echo Access docs at http://localhost:8000/docs
