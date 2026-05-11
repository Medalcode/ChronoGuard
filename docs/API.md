# API Reference - ChronoGuard

## Base URL
```
http://localhost:8000/api/v1  (desarrollo)
https://api.chronoguard.com/api/v1  (producción)
```

---

## 🔐 Autenticación

### Esquema: Bearer Token (JWT)

Todos los endpoints protegidos requieren un header:
```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**¿Cómo obtener el token?**
1. Registrarse con POST /auth/register
2. O hacer login con POST /auth/login
3. Guardar el `access_token` de la respuesta

---

## 📝 Endpoints de Autenticación

### POST `/auth/register`
**Crear un nuevo usuario.**

**Descripción:**
Registra un nuevo usuario en ChronoGuard. Durante este proceso:
1. Se valida que el email sea único
2. Se genera un `vault_salt` criptográfico
3. La contraseña se hashea con bcrypt
4. Se devuelve un JWT para mantener sesión

**Request:**
```json
{
  "email": "usuario@example.com",
  "password": "MiContraseñaFuerte123"
}
```

**Validaciones:**
- `email`: Debe ser un email válido
- `password`: Mínimo 8 caracteres

**Response (201 Created):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI1NTBlODQwMC1lMjliLTQxZDQtYTcxNi00NDY2NTU0NDAwMDAiLCJleHAiOjE3MTUzOTI3NTN9.XyZ...",
  "token_type": "bearer",
  "vault_salt": "3f7a2b8c1e9d4a6f5c3e7b1a9d2c4f6e8a1b3c5d7e9f2a4b6c8e1f3a5b7c9d"
}
```

**En el Frontend (después de recibir vault_salt):**
```javascript
// Derivar la llave local
const masterKey = await deriveKey(password, vault_salt);

// Guardar el access_token en memoria (no localStorage)
sessionStorage.setItem('access_token', access_token);

// Ahora el usuario puede hacer POST /vault/assets con datos cifrados
```

**Errores posibles:**
```json
400: {"detail": "El correo electrónico ya está registrado"}
422: {"detail": [{"loc": ["body", "email"], "msg": "invalid email format"}]}
```

---

### POST `/auth/login`
**Autenticar un usuario existente.**

**Request:**
```json
{
  "email": "usuario@example.com",
  "password": "MiContraseñaFuerte123"
}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "vault_salt": "3f7a2b8c1e9d4a6f5c3e7b1a9d2c4f6e8a1b3c5d7e9f2a4b6c8e1f3a5b7c9d"
}
```

**Errores posibles:**
```json
401: {"detail": "Correo o contraseña incorrectos", "headers": {"WWW-Authenticate": "Bearer"}}
403: {"detail": "Usuario inactivo"}
```

---

### GET `/health`
**Verificar que la API está funcionando.**

No requiere autenticación.

**Response (200 OK):**
```json
{
  "status": "healthy",
  "project": "ChronoGuard API",
  "version": "1.0.0",
  "environment": "development"
}
```

---

## 📦 Endpoints de Bóveda (Próximas fases)

### POST `/vault/assets`
**Crear un nuevo activo cifrado.**

**⚠️ NOTA IMPORTANTE:**
El `encrypted_payload` DEBE estar cifrado en el cliente ANTES de enviarlo.

**Request:**
```json
{
  "asset_name": "Mi Wallet de Bitcoin",
  "asset_type": "CREDENTIAL",
  "encrypted_payload": "base64(iv + aes_gcm_ciphertext)"
}
```

**Headers:**
```http
Authorization: Bearer <token>
```

**Response (201 Created):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440001",
  "asset_name": "Mi Wallet de Bitcoin",
  "asset_type": "CREDENTIAL",
  "created_at": "2024-05-11T14:23:45.123456+00:00"
}
```

---

### GET `/vault/assets`
**Listar todos los activos del usuario autenticado.**

**Headers:**
```http
Authorization: Bearer <token>
```

**Response (200 OK):**
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440001",
    "asset_name": "Mi Wallet de Bitcoin",
    "asset_type": "CREDENTIAL",
    "encrypted_payload": "base64(...)",
    "created_at": "2024-05-11T14:23:45.123456+00:00"
  },
  {
    "id": "550e8400-e29b-41d4-a716-446655440002",
    "asset_name": "Testamento Digital",
    "asset_type": "DOCUMENT",
    "encrypted_payload": "base64(...)",
    "created_at": "2024-05-11T14:30:00.123456+00:00"
  }
]
```

**En el Frontend (después de recibir los encrypted_payloads):**
```javascript
// Desencriptar localmente
for (const asset of assets) {
  const plaintext = await decryptAsset(asset.encrypted_payload, masterKey);
  console.log(`${asset.asset_name}: ${plaintext}`);
}
```

---

### DELETE `/vault/assets/{asset_id}`
**Eliminar un activo.**

**Parameters:**
- `asset_id` (path): UUID del activo

**Headers:**
```http
Authorization: Bearer <token>
```

**Response (204 No Content):**
```
(sin body)
```

---

## ⏰ Endpoints del Dead Man's Switch

### GET `/switch/config`
**Obtener la configuración actual del usuario.**

**Headers:**
```http
Authorization: Bearer <token>
```

**Response (200 OK):**
```json
{
  "ping_interval_days": 7,
  "trigger_after_days": 30,
  "last_active_at": "2024-05-11T10:00:00.123456+00:00",
  "status": "ACTIVE",
  "days_since_last_activity": 0
}
```

---

### PUT `/switch/config`
**Actualizar los parámetros del Dead Man's Switch.**

**Request:**
```json
{
  "ping_interval_days": 14,
  "trigger_after_days": 60
}
```

**Headers:**
```http
Authorization: Bearer <token>
```

**Response (200 OK):**
```json
{
  "ping_interval_days": 14,
  "trigger_after_days": 60,
  "status": "ACTIVE"
}
```

---

### POST `/switch/ping`
**Confirmar que el usuario está vivo.**

Este endpoint:
1. Actualiza `last_active_at` al timestamp actual
2. Reinicia el contador de inactividad
3. Registra un evento en audit_logs

**Request:**
```json
{}
```

**Headers:**
```http
Authorization: Bearer <token>
```

**Response (200 OK):**
```json
{
  "message": "Confirmación de vida registrada",
  "last_active_at": "2024-05-11T14:23:45.123456+00:00"
}
```

**¿Cuándo llamarlo?**
- Cuando el usuario abre la app
- Cuando hace cualquier acción relevante
- Cuando hace clic en "Confirmar que estoy bien" desde el email

---

## 👥 Endpoints de Sucesión (Próximas fases)

### POST `/succession/beneficiaries`
**Agregar un beneficiario/heredero.**

**Request:**
```json
{
  "full_name": "Mi Hijo",
  "email": "hijo@example.com",
  "phone_number": "+56912345678",
  "role": "HEREDERO"
}
```

**Response (201 Created):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440003",
  "full_name": "Mi Hijo",
  "email": "hijo@example.com",
  "role": "HEREDERO"
}
```

---

### POST `/succession/allocations`
**Vincular un activo a un beneficiario.**

**Request:**
```json
{
  "asset_id": "550e8400-e29b-41d4-a716-446655440001",
  "beneficiary_id": "550e8400-e29b-41d4-a716-446655440003"
}
```

**Response (201 Created):**
```json
{
  "asset_id": "550e8400-e29b-41d4-a716-446655440001",
  "beneficiary_id": "550e8400-e29b-41d4-a716-446655440003"
}
```

---

## 📊 Respuestas de Error

Todos los errores siguen el formato HTTP estándar:

### 400 Bad Request
```json
{
  "detail": "Descripción del error de validación"
}
```

### 401 Unauthorized
```json
{
  "detail": "Token expirado o inválido",
  "headers": {"WWW-Authenticate": "Bearer"}
}
```

### 403 Forbidden
```json
{
  "detail": "No tienes permiso para acceder a este recurso"
}
```

### 404 Not Found
```json
{
  "detail": "Usuario no encontrado"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Error interno del servidor"
}
```

---

## 🧪 Ejemplos con curl

### Registrarse
```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "SecurePassword123"
  }'
```

### Hacer login
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "SecurePassword123"
  }'
```

### Guardar el token
```bash
TOKEN=$(curl -s -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "SecurePassword123"
  }' | jq -r '.access_token')

echo "Token: $TOKEN"
```

### Usar el token en requests posteriores
```bash
curl -X GET "http://localhost:8000/api/v1/switch/config" \
  -H "Authorization: Bearer $TOKEN"
```

### Enviar ping (confirmar que estoy vivo)
```bash
curl -X POST "http://localhost:8000/api/v1/switch/ping" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{}'
```

---

## 📚 Documentación Interactiva

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

Aquí puedes:
- Ver todos los endpoints
- Leer la documentación automática
- Probar los endpoints directamente
- Copiar los ejemplos de curl
