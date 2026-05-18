[![Demo](https://img.shields.io/badge/Demo-Vercel-000000?style=flat-square&logo=vercel)](https://chronoguard-api.vercel.app)

# ChronoGuard 🔐

**Custodia Digital con Dead Man's Switch**

Una plataforma de código abierto para gestionar activos digitales con liberación automática en caso de inactividad o fallecimiento del usuario. Ideal para herederos, empresas familiares y profesionales que necesitan proteger información sensible.

---

## 🎯 Características Principales

- **Dead Man's Switch Automatizado**: Monitoreo de inactividad con protocolo de liberación en cascada
- **Criptografía Zero-Knowledge**: Cifrado simétrico AES-256 en el cliente - el servidor nunca sabe qué contiene la bóveda
- **Seguridad Empresarial**: Hash bcrypt, JWT, auditoría completa de eventos
- **Escalable**: Arquitectura modular lista para crecer desde MVP a SaaS completo
- **PostgreSQL**: Base de datos relacional robusta para integridad de datos críticos

---

## 🏗️ Arquitectura del Proyecto

```
ChronoGuard/
├── app/
│   ├── core/              # Configuración global y seguridad
│   │   ├── config.py      # Variables de entorno (Pydantic)
│   │   └── security.py    # JWT, hashing, criptografía
│   ├── db/                # Conexión a PostgreSQL
│   │   └── database.py    # SQLAlchemy setup
│   ├── models/            # Modelos ORM (Tablas SQL)
│   │   ├── user.py        # Usuario con vault_salt
│   │   ├── switch_configuration.py  # Configuración Dead Man's Switch
│   │   └── audit_log.py   # Trazabilidad de eventos
│   ├── schemas/           # Validación Pydantic (entrada/salida)
│   │   └── user_schema.py # UserCreate, UserResponse, Token
│   ├── api/
│   │   └── v1/
│   │       ├── auth.py    # POST /register, /login
│   │       └── [próximas rutas]
│   ├── services/          # Lógica de Negocio
│   │   ├── auth_service.py
│   │   └── [próximos servicios]
│   ├── workers/           # Tareas en segundo plano
│   │   └── scheduler.py   # Dead Man's Switch - Evaluación diaria
│   └── main.py            # Punto de entrada (FastAPI app)
├── tests/                 # Pruebas con pytest
├── requirements.txt       # Dependencias Python
├── .env.example          # Plantilla de variables de entorno
├── docker-compose.yml    # PostgreSQL local para desarrollo
└── README.md
```

---

## ⚙️ Quick Start (Desarrollo Local)

### Prerrequisitos
- Python 3.11+
- Docker & Docker Compose (para PostgreSQL)
- Git

### 1. Clonar el Repositorio
```bash
git clone https://github.com/Medalcode/ChronoGuard.git
cd ChronoGuard
```

### 2. Levantar PostgreSQL con Docker
```bash
docker-compose up -d
```
Esto crea un contenedor PostgreSQL con credenciales por defecto.

### 3. Configurar Variables de Entorno
```bash
cp .env.example .env
```

Edita `.env` y genera una SECRET_KEY segura:
```bash
openssl rand -hex 32
```

### 4. Crear Entorno Virtual
```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

### 5. Instalar Dependencias
```bash
pip install -r requirements.txt
```

### 6. Iniciar el Servidor de Desarrollo
```bash
uvicorn app.main:app --reload
```

La API estará disponible en `http://localhost:8000`

---

## 📚 Documentación Interactiva

Una vez que el servidor esté corriendo, accede a:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

Aquí puedes probar todos los endpoints directamente desde el navegador.

---

## 🔐 Flujo de Seguridad (Zero-Knowledge)

### Registro de Usuario
```json
POST /api/v1/auth/register
{
  "email": "usuario@example.com",
  "password": "MiContraseñaFuerte123"
}
```

**Qué sucede en el servidor:**
1. Se valida el email (EmailStr de Pydantic)
2. Se genera un `vault_salt` único y criptográfico
3. La contraseña se hashea con bcrypt (irreversible)
4. Se devuelven: JWT para la sesión y vault_salt para el cliente

**Qué sucede en el cliente (Frontend):**
1. Recibe el vault_salt
2. Deriva una llave AES-256 usando PBKDF2(password + vault_salt)
3. Esa llave JAMÁS viaja al servidor
4. Todo lo que el usuario suba (contraseñas, archivos) se cifra localmente con esa llave

**Resultado:** El servidor almacena datos incomprensibles. Ni siquiera el administrador de la BD puede verlos.

---

## 🧪 Testing

Ejecuta las pruebas unitarias:
```bash
pytest tests/ -v
```

Pruebas incluidas:
- ✅ Health check del servidor
- ✅ Registro de usuario
- ✅ Prevención de emails duplicados
- ✅ Login e issuance de JWT
- ✅ Validaciones de Pydantic

---

## 📋 Roadmap MVP → SaaS

### Fase 1: MVP de Título (Semestre 1)
- [x] Arquitectura base con FastAPI
- [ ] Endpoints de autenticación (register, login)
- [ ] Endpoints de bóveda (crear, leer, eliminar activos cifrados)
- [ ] Dead Man's Switch básico (monitoreo + notificaciones)
- [ ] Pruebas unitarias

### Fase 2: SaaS Comercial (Post-Titulación)
- [ ] Integración con Stripe/MercadoPago
- [ ] Almacenamiento de archivos en AWS S3
- [ ] Notificaciones vía WhatsApp (Twilio)
- [ ] Dashboard para herederos
- [ ] Modelo de suscripción

### Fase 3: B2B & Expansión
- [ ] Arquitectura multi-tenant
- [ ] APIs públicas para integradores
- [ ] Smart Contracts para criptomonedas
- [ ] Validación con Registro Civil

---

## 🔧 Variablesde Entorno Importantes

```bash
# Base de Datos
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/chronoguard_dev

# Seguridad (genera con: openssl rand -hex 32)
SECRET_KEY=your-secret-key-here

# Configuración del Dead Man's Switch
DEFAULT_PING_INTERVAL_DAYS=7
DEFAULT_TRIGGER_AFTER_DAYS=30

# Emails (para enviar notificaciones)
SMTP_HOST=smtp.mailtrap.io
SMTP_PORT=465
SMTP_USER=your-username
SMTP_PASSWORD=your-password
```

---

## 📖 Documentación Técnica Detallada

- **[Arquitectura de Seguridad](docs/SECURITY.md)** - Criptografía, JWT, bcrypt
- **[Modelo de Base de Datos](docs/DATABASE.md)** - Esquema SQL y relaciones
- **[API Reference](docs/API.md)** - Especificación de endpoints
- **[Dead Man's Switch](docs/DEAD_MANS_SWITCH.md)** - Lógica de inactividad

---

## 👨‍💻 Desarrollo

### Agregar Nuevos Endpoints

1. **Crear el Schema en `app/schemas/`**
```python
class MyResponseSchema(BaseModel):
    id: UUID
    name: str
    model_config = ConfigDict(from_attributes=True)
```

2. **Crear el Service en `app/services/`**
```python
class MyService:
    @staticmethod
    def do_something(db: Session) -> MyResponseSchema:
        # Lógica aquí
        pass
```

3. **Agregar la Ruta en `app/api/v1/`**
```python
router = APIRouter(prefix="/my-resource", tags=["My Resource"])

@router.get("/", response_model=list[MyResponseSchema])
def get_my_resources(current_user: User = Depends(get_current_user)):
    return MyService.get_all(current_user.id)
```

4. **Incluir el Router en `app/main.py`**

---

## 🐛 Troubleshooting

**Error: "No module named 'app'"**
- Asegúrate de estar en la raíz del proyecto
- Verifica que hayas activado el venv

**Error: "Connection refused" (PostgreSQL)**
- Ejecuta `docker-compose up -d`
- Verifica con `docker ps`

**Error: "SECRET_KEY not provided"**
- Copia `.env.example` a `.env`
- Genera una llave con `openssl rand -hex 32`

---

## 📞 Soporte

Para preguntas o issues:
1. Revisa la documentación en `docs/`
2. Abre un issue en GitHub
3. Contacta al equipo de desarrollo

---

## 📄 Licencia

Proyecto bajo licencia MIT - Ver `LICENSE` para detalles.

---

**Construido con ❤️ para proteger el legado digital**