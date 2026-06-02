#!/bin/bash

# ChronoGuard - Quick Start Script
# Este script automatiza la configuración inicial del proyecto

set -e

echo "🚀 ChronoGuard - Setup Inicial"
echo "=============================="

# Crear .env si no existe
if [ ! -f ".env" ]; then
    echo "📝 Creando archivo .env..."
    cp .env.example .env
    
    # Generar SECRET_KEY segura
    SECRET_KEY=$(openssl rand -hex 32)
    sed -i.bak "s/your-secret-key-change-this-in-production-use-openssl-rand-hex-32/$SECRET_KEY/" .env
    rm -f .env.bak
    
    echo "✅ SECRET_KEY generada y guardada en .env"
else
    echo "ℹ️  Archivo .env ya existe, saltando..."
fi

# Crear venv
if [ ! -d "venv" ]; then
    echo "📦 Creando entorno virtual..."
    python -m venv venv
    echo "✅ Entorno virtual creado"
else
    echo "ℹ️  Entorno virtual ya existe"
fi

# Activar venv
echo "🔓 Activando entorno virtual..."
source venv/bin/activate

# Instalar dependencias
echo "📚 Instalando dependencias..."
pip install -q -r requirements.txt
echo "✅ Dependencias instaladas"

# Levantar PostgreSQL con Docker
echo "🐘 Levantando PostgreSQL..."
docker-compose up -d
echo "✅ PostgreSQL levantado (espera 5 segundos para que esté listo...)"
sleep 5

echo ""
echo "════════════════════════════════════════════"
echo "✅ SETUP COMPLETADO EXITOSAMENTE"
echo "════════════════════════════════════════════"
echo ""
echo "🚀 Para iniciar el servidor, ejecuta:"
echo "   uvicorn app.main:app --reload"
echo ""
echo "📚 Accede a la documentación en:"
echo "   - Swagger UI: http://localhost:8000/docs"
echo "   - ReDoc: http://localhost:8000/redoc"
echo ""
echo "🐳 Para ver PostgreSQL en Web:"
echo "   - pgAdmin: http://localhost:5050"
echo "   - Email: admin@chronoguard.local"
echo "   - Password: admin"
echo ""
echo "🧪 Para correr tests:"
echo "   pytest tests/ -v"
echo ""
