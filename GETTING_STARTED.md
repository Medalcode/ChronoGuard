# ChronoGuard - Getting Started

## Inicio Rápido (5 minutos)

### Linux/macOS
```bash
chmod +x setup.sh
./setup.sh
uvicorn app.main:app --reload
```

### Windows
```bash
setup.bat
uvicorn app.main:app --reload
```

Luego abre http://localhost:8000/docs

---

## Instalación Manual Paso a Paso

### 1. Clonar el Repositorio
```bash
git clone https://github.com/Medalcode/ChronoGuard.git
cd ChronoGuard
```

### 2. Crear Entorno Virtual
```bash
# Linux/macOS
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

### 3. Generar Contraseña Segura
```bash
openssl rand -hex 32
```

### 4. Configurar Variables de Entorno
```bash
cp .env.example .env
```

Edita `.env` y reemplaza:
```
SECRET_KEY=<resultado-del-comando-anterior>
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/chronoguard_dev
```

### 5. Instalar Dependencias
```bash
pip install -r requirements.txt
```

### 6. Iniciar PostgreSQL
```bash
docker-compose up -d
```

Verifica con:
```bash
docker ps  # Deberías ver postgres y pgadmin corriendo
```

### 7. Iniciar el Servidor
```bash
uvicorn app.main:app --reload
```

Deberías ver:
```
INFO:     Application startup complete
```

---

## 🧪 Probar la API

### Registrar Usuario (sin autenticación)
```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "SecurePassword123"
  }'
```

Respuesta esperada:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "vault_salt": "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6"
}
```

### Guardar el Token
```bash
# Usar en requests posteriores
TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### Hacer Login
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "SecurePassword123"
  }'
```

### Verificar Health Check
```bash
curl http://localhost:8000/api/v1/health
```

---

## 📊 Acceder a Herramientas Web

### Swagger UI (para probar endpoints)
- URL: http://localhost:8000/docs
- Prueba endpoints directamente en el navegador
- Los JWT se pueden pegar en la caja "Authorize"

### ReDoc (documentación bonita)
- URL: http://localhost:8000/redoc

### pgAdmin (administrar PostgreSQL)
- URL: http://localhost:5050
- Email: `admin@chronoguard.local`
- Password: `admin`
- Servidor: `postgres` (desde Docker)
- Usuario: `postgres`
- Password: `postgres`

---

## 🔍 Estructura de Archivos a Entender

```
app/
├── main.py                           # ← Punto de entrada
├── core/
│   ├── config.py                     # Variables de entorno (Pydantic)
│   └── security.py                   # JWT, bcrypt, criptografía
├── db/
│   └── database.py                   # Conexión SQLAlchemy
├── models/                           # ← Tablas SQL
│   ├── user.py
│   ├── switch_configuration.py
│   └── audit_log.py
├── schemas/                          # ← Validación entrada/salida
│   └── user_schema.py
├── api/v1/
│   ├── auth.py                       # ← Rutas REST
│   └── [próximas rutas]
├── services/                         # ← Lógica de negocio
│   ├── auth_service.py
│   └── [próximos servicios]
└── workers/
    └── scheduler.py                  # ← Dead Man's Switch
```

---

## 🐛 Troubleshooting

### Error: "Connection refused" en PostgreSQL
```bash
# Verificar que Docker está corriendo
docker ps

# Si no está, levanta PostgreSQL
docker-compose up -d

# Espera 5 segundos para que esté listo
sleep 5
```

### Error: "ModuleNotFoundError: No module named 'app'"
```bash
# Asegúrate de estar en la raíz del proyecto
pwd  # Deberías ver: .../ChronoGuard

# Verifica que el venv está activado
which python  # Deberías ver: .../venv/bin/python
```

### Error: "SECRET_KEY not provided"
```bash
# Genera y copia en .env
openssl rand -hex 32
# Edita .env con la llave
```

### Error: "Key already exists in database"
```bash
# PostgreSQL mantiene datos. Para resetear:
docker-compose down -v
docker-compose up -d
sleep 5
# Reinicia el servidor
```

---

## 📝 Próximos Pasos

Después de que todo funcione:

1. **Leer la Documentación**
   - Abre `docs/SECURITY.md` - Entiende la criptografía
   - Abre `docs/DATABASE.md` - Entiende las tablas

2. **Entender el Flujo**
   - Abre `app/main.py` - El punto de entrada
   - Abre `app/api/v1/auth.py` - Un endpoint REST completo
   - Abre `app/services/auth_service.py` - La lógica detrás

3. **Correr Tests**
   ```bash
   pytest tests/test_auth.py -v
   ```

4. **Empezar a Programar**
   - Crea nuevos endpoints en `app/api/v1/`
   - Agrega servicios en `app/services/`
   - Escribe tests en `tests/`

---

## 📚 Recursos

- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [SQLAlchemy ORM](https://docs.sqlalchemy.org/en/20/orm/)
- [Pydantic](https://docs.pydantic.dev/)
- [JWT.io](https://jwt.io/)

---

## ✅ Checklist de Confirmación

Ejecuta esto para verificar que todo está funcionando:

```bash
# Terminal 1: Inicia el servidor
uvicorn app.main:app --reload

# Terminal 2: Prueba endpoints
curl http://localhost:8000/api/v1/health
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test1234"}'
```

Si ves respuestas JSON sin errores, ¡estás listo para empezar! 🎉
