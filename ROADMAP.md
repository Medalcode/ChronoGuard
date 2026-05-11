# Roadmap de Desarrollo - ChronoGuard

## 🎯 Fase 1: MVP (COMPLETADA ✅)

### Arquitectura Base
- [x] Estructura de carpetas profesional
- [x] Configuración con Pydantic
- [x] Conexión a PostgreSQL
- [x] Modelos SQLAlchemy (User, SwitchConfiguration, AuditLog)
- [x] Esquemas Pydantic (validación entrada/salida)

### Autenticación
- [x] Generación de vault_salt criptográfico
- [x] Hashing de contraseña con bcrypt
- [x] Creación de JWT (JSON Web Tokens)
- [x] Endpoints: POST /auth/register, POST /auth/login
- [x] Dependencia de inyección para usuarios autenticados

### Dead Man's Switch (Base)
- [x] Modelo SwitchConfiguration
- [x] Scheduler con APScheduler
- [x] Lógica de monitoreo de inactividad
- [x] AuditLog para trazabilidad

### Testing
- [x] Pruebas unitarias básicas con pytest
- [x] Fixtures para BD en memoria

### Documentación
- [x] README.md completo
- [x] GETTING_STARTED.md
- [x] docs/SECURITY.md
- [x] docs/DATABASE.md
- [x] docs/API.md
- [x] docs/DEAD_MANS_SWITCH.md

---

## 📦 Fase 2: MVP Completo (PRÓXIMO - Semanas 1-4)

### Endpoints de Bóveda (Guardar/Recuperar Activos)

#### 1. Modelo: digital_assets
```python
# app/models/digital_asset.py
class DigitalAsset(Base):
    __tablename__ = "digital_assets"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    asset_name = Column(String(255), nullable=False)
    asset_type = Column(String(50), nullable=False)  # CREDENTIAL, SECURE_NOTE, DOCUMENT
    encrypted_payload = Column(Text, nullable=False)  # Base64(iv + ciphertext)
    s3_object_key = Column(String(500), nullable=True)  # Para archivos grandes
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
```

#### 2. Schema: asset_schema.py
```python
class AssetCreate(BaseModel):
    asset_name: str
    asset_type: str  # CREDENTIAL, SECURE_NOTE, DOCUMENT
    encrypted_payload: str  # Base64
    
class AssetResponse(BaseModel):
    id: UUID
    asset_name: str
    asset_type: str
    encrypted_payload: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
```

#### 3. Service: vault_service.py
```python
class VaultService:
    @staticmethod
    def create_asset(user_id: UUID, asset_in: AssetCreate, db: Session) -> DigitalAsset:
        # Crear y guardar
        
    @staticmethod
    def get_user_assets(user_id: UUID, db: Session) -> List[DigitalAsset]:
        # Listar activos del usuario
        
    @staticmethod
    def delete_asset(asset_id: UUID, user_id: UUID, db: Session) -> bool:
        # Verificar propiedad y eliminar
```

#### 4. Router: app/api/v1/vault.py
```python
@router.post("/assets", response_model=AssetResponse)
def create_asset(
    asset_in: AssetCreate,
    current_user: User = Depends(get_current_user)
):
    # POST /api/v1/vault/assets
    
@router.get("/assets", response_model=List[AssetResponse])
def list_assets(
    current_user: User = Depends(get_current_user)
):
    # GET /api/v1/vault/assets
    
@router.delete("/assets/{asset_id}")
def delete_asset(
    asset_id: UUID,
    current_user: User = Depends(get_current_user)
):
    # DELETE /api/v1/vault/assets/{asset_id}
```

---

### Endpoints de Sucesión (Herederos)

#### 1. Modelo: beneficiary.py
```python
class Beneficiary(Base):
    __tablename__ = "beneficiaries"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    full_name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    phone_number = Column(String(20), nullable=True)
    role = Column(String(20), nullable=False)  # HEREDERO, GARANTE
    public_key = Column(Text, nullable=True)  # Para cifrado asimétrico futuro
    created_at = Column(DateTime(timezone=True), server_default=func.now())
```

#### 2. Modelo: asset_allocation.py
```python
class AssetAllocation(Base):
    __tablename__ = "asset_allocations"
    
    asset_id = Column(UUID(as_uuid=True), ForeignKey("digital_assets.id", ondelete="CASCADE"), primary_key=True)
    beneficiary_id = Column(UUID(as_uuid=True), ForeignKey("beneficiaries.id", ondelete="CASCADE"), primary_key=True)
```

#### 3. Router: app/api/v1/succession.py
```python
@router.post("/beneficiaries", response_model=BeneficiaryResponse)
def add_beneficiary(
    beneficiary_in: BeneficiaryCreate,
    current_user: User = Depends(get_current_user)
):
    # POST /api/v1/succession/beneficiaries
    
@router.post("/allocations")
def allocate_asset(
    asset_id: UUID,
    beneficiary_id: UUID,
    current_user: User = Depends(get_current_user)
):
    # POST /api/v1/succession/allocations
```

---

### Endpoints del Switch (Completar)

#### 1. Router: app/api/v1/switch.py
```python
@router.get("/config", response_model=SwitchConfigResponse)
def get_config(current_user: User = Depends(get_current_user)):
    # GET /api/v1/switch/config
    
@router.put("/config", response_model=SwitchConfigResponse)
def update_config(
    config_in: SwitchConfigUpdate,
    current_user: User = Depends(get_current_user)
):
    # PUT /api/v1/switch/config
    
@router.post("/ping", response_model=dict)
def confirm_alive(current_user: User = Depends(get_current_user)):
    # POST /api/v1/switch/ping
    # Actualiza last_active_at
```

---

### Envío de Correos

#### 1. Service: email_service.py
```python
class EmailService:
    @staticmethod
    def send_ping_email(user_email: str, confirm_link: str):
        # Email: "¿Estás bien?"
        
    @staticmethod
    def send_succession_email(beneficiary_email: str, assets: List[str], temp_token: str):
        # Email: "Has sido designado como heredero"
        
    @staticmethod
    def send_trigger_notification(user_email: str):
        # Email: "Se ha activado el protocolo"
```

#### 2. Integración SMTP en config.py
```python
# Usar variables SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD
```

---

### Pruebas Expandidas
- [ ] Tests para endpoints de vault
- [ ] Tests para endpoints de sucesión
- [ ] Tests para endpoints de switch
- [ ] Tests de integración completos

---

## 🚀 Fase 3: SaaS Comercial (Después de Titulación)

### Infraestructura Cloud
- [ ] Deploy a AWS Lambda
- [ ] S3 para almacenamiento de documentos
- [ ] CloudFront para CDN
- [ ] RDS para PostgreSQL administrado

### Frontend Web (React/Vue)
- [ ] Interfaz de registro/login
- [ ] Dashboard principal
- [ ] Formulario para agregar activos cifrados
- [ ] Gestor de herederos
- [ ] Configuración del Dead Man's Switch
- [ ] Panel de heredero (vista temporal)

### Pagos
- [ ] Integración Stripe
- [ ] Modelos de suscripción (Freemium, Pro, Enterprise)
- [ ] Webhooks de facturación

### Notificaciones Avanzadas
- [ ] SMS vía Twilio
- [ ] WhatsApp vía Twilio
- [ ] Push notifications (mobile)

### Compliance Regulatorio
- [ ] Integración con Registro Civil (validar defunción)
- [ ] Conformidad GDPR
- [ ] Conformidad LGPD
- [ ] Cláusulas legales de notarias

---

## 📝 Instrucciones Fase 2: Paso a Paso

### Semana 1: Endpoints de Bóveda

1. **Crear modelo digital_asset.py**
   ```bash
   # Copiar patrón de models/user.py
   # Cambiar por campos apropiados para assets
   ```

2. **Crear schema asset_schema.py**
   ```bash
   # Validar: asset_name (string), asset_type (enum), encrypted_payload (base64)
   ```

3. **Crear service vault_service.py**
   ```bash
   # Métodos: create, get_all, delete, get_by_id
   ```

4. **Crear router app/api/v1/vault.py**
   ```bash
   # POST /assets, GET /assets, DELETE /assets/{id}
   # Incluir en app/main.py
   ```

5. **Escribir tests**
   ```bash
   # pytest tests/test_vault.py
   ```

### Semana 2: Endpoints de Sucesión

Similar a Semana 1, pero para:
- models/beneficiary.py
- models/asset_allocation.py
- schemas/beneficiary_schema.py
- services/succession_service.py
- api/v1/succession.py

### Semana 3: Endpoints del Switch + Emails

1. Completar app/api/v1/switch.py
2. Crear app/services/email_service.py
3. Integrar emails en scheduler.py
4. Tests completos

### Semana 4: Testing e Integración

- Tests de integración
- Documentación de API actualizada
- Manual de usuario

---

## 🔍 Checklist para Cada Nuevo Endpoint

Cuando agregues un nuevo endpoint, verifica:

- [ ] Crear modelo en `models/`
- [ ] Crear schema (Create + Response) en `schemas/`
- [ ] Crear servicio en `services/`
- [ ] Crear router en `api/v1/`
- [ ] Incluir router en `main.py`
- [ ] Escribir tests en `tests/`
- [ ] Documentar en `docs/API.md`
- [ ] Verificar seguridad (autenticación, autorización)
- [ ] Agregar auditoría si es crítico
- [ ] Probarlo en http://localhost:8000/docs

---

## 🧪 Comandos Útiles para Desarrollo

```bash
# Iniciar servidor con auto-reload
uvicorn app.main:app --reload

# Correr tests
pytest tests/ -v

# Correr un test específico
pytest tests/test_auth.py::test_register_user -v

# Ver cobertura
pytest tests/ --cov=app

# Conectar a PostgreSQL
psql -h localhost -U postgres -d chronoguard_dev

# Crear migración
alembic revision --autogenerate -m "Descripción"

# Ejecutar migración
alembic upgrade head
```

---

## 💡 Consejos Técnicos

1. **Sempre testea primero**
   - Write test → Red → Green → Refactor

2. **Mantén la separación de capas**
   - Routes NO contienen lógica (solo llaman services)
   - Services contienen TODA la lógica
   - Models son solo schemas de BD

3. **Documenta mientras codeas**
   - Docstrings en funciones
   - Comments en lógica compleja
   - Actualiza docs/ al agregar features

4. **Seguridad siempre**
   - Valida entrada con Pydantic
   - Verifica autenticación/autorización
   - Registra en audit_logs
   - No expongas información sensible en respuestas

5. **Escalabilidad**
   - Usa índices en queries frecuentes
   - Async/await para I/O (emails, APIs externas)
   - Rate limiting en endpoints públicos

---

## 📞 Debugging Rápido

```python
# En cualquier endpoint, para ver estado actual:
print(f"DEBUG: User ID = {current_user.id}")
print(f"DEBUG: Switch Config = {config}")

# O mejor, usa logging:
import logging
logger = logging.getLogger(__name__)
logger.info(f"User {current_user.id} accessed vault")
```

---

## 🎓 Recursos para Continuar

- FastAPI: https://fastapi.tiangolo.com/tutorial/
- SQLAlchemy: https://docs.sqlalchemy.org/en/20/orm/quickstart.html
- Pytest: https://docs.pytest.org/en/7.1.x/
- PostgreSQL: https://www.postgresql.org/docs/

---

**¡Ahora estás listo para continuar! 🚀**
