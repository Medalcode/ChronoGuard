# Arquitectura de Seguridad - ChronoGuard

## 🔐 Principio: Zero-Knowledge (Conocimiento Cero)

El corazón de ChronoGuard es la arquitectura **Zero-Knowledge**: ni siquiera el administrador de la base de datos puede ver qué información confidencial guardan los usuarios.

### ¿Cómo funciona?

```
USUARIO (Frontend/Cliente)
│
├─ Ingresa: email + contraseña maestra
│
├─ GENERA LLAVE LOCAL (en el navegador)
│  ├─ Toma: contraseña + vault_salt (del servidor)
│  ├─ Aplica: PBKDF2 con SHA-256 (100,000 iteraciones)
│  └─ Resultado: Llave AES-256 de 256 bits (NUNCA viaja al servidor)
│
├─ CIFRA LOS DATOS LOCALMENTE
│  ├─ Algoritmo: AES-GCM (Galois/Counter Mode)
│  ├─ IV: Vector de inicialización único por cifrado (12 bytes)
│  └─ Resultado: encrypted_payload (texto indescifrableque viaja por HTTPS)
│
└─ ENVÍA AL SERVIDOR
   └─ Solo: email + encrypted_payload (incomprensible)


SERVIDOR (Backend)
│
├─ Recibe: email + encrypted_payload
├─ Almacena tal cual en PostgreSQL
└─ LA LLAVE JAMÁS SE GUARDA EN LA BASE DE DATOS
```

---

## 🛡️ Componentes de Seguridad

### 1. Autenticación (Credenciales)

#### Password Hashing (Bcrypt)
```python
# app/core/security.py: get_password_hash()

password_plain = "MiContraseña123"
password_hash = bcrypt.hash(password_plain)

# Resultado: $2b$12$a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6
# Propiedades:
# - Irreversible: No se puede descifrar
# - Determinístico: Mismo password siempre genera el mismo hash en la BD
# - Lento: Tarda ~0.3 segundos por hash (previene ataques de fuerza bruta)
# - Salted: Cada hash incluye un salt único
```

**¿Por qué bcrypt en lugar de MD5 o SHA?**
- MD5/SHA son RÁPIDOS (malo para contraseñas)
- bcrypt es LENTO y ADAPTATIVO (bueno para seguridad)
- Recomendación NIST: bcrypt, scrypt, Argon2

---

### 2. Cifrado Local (Frontend)

#### Derivación de Llave (PBKDF2)
```javascript
// Frontend (Web Crypto API)

// Usuario ingresa: "MiContraseña123"
// Servidor devolvió: vault_salt = "a1b2c3d4..."

// PBKDF2 aplica:
// 1. Combina contraseña + salt
// 2. Ejecuta función hash 100,000 veces
// 3. Devuelve: 256-bit key para AES-GCM

const masterKey = await crypto.subtle.deriveKey(
  {
    name: "PBKDF2",
    salt: encode(vault_salt),
    iterations: 100000,
    hash: "SHA-256"
  },
  keyMaterial,
  { name: "AES-GCM", length: 256 },
  false,  // ← NO exportable (no se puede extraer de la memoria del navegador)
  ["encrypt", "decrypt"]
);
```

**¿Por qué 100,000 iteraciones?**
- Recomendación NIST (2023): 600,000+
- Usamos 100,000 para balance velocidad/seguridad en MVP
- Producción: Aumentar a 500,000+

#### Cifrado Simétrico (AES-GCM)
```javascript
// Algoritmo: AES-256-GCM
// - AES: Advanced Encryption Standard (estándar militar)
// - 256: Clave de 256 bits (cuánticamente resistente por ahora)
// - GCM: Galois/Counter Mode (cifra + autentica en un paso)

// Entrada: plaintext = "Mi frase semilla es: perro gato sol..."
// Salida: { ciphertext, iv, tag }

const iv = crypto.getRandomValues(new Uint8Array(12));  // IV único
const ciphertext = await crypto.subtle.encrypt(
  { name: "AES-GCM", iv: iv },
  masterKey,
  encode(plaintext)
);

// El "tag" está dentro de ciphertext y autentica el mensaje
// (previene modificación sin key)

// Guardamos: Base64(iv + ciphertext) = encrypted_payload
```

**¿Por qué GCM y no ECB o CBC?**
- ECB: Inseguro (patrones visibles)
- CBC: Requiere manejo manual del IV
- GCM: Cifra + autentica (previene tampering)

---

### 3. Autenticación de Sesión (JWT)

#### JSON Web Token (JWT)
```python
# app/core/security.py: create_access_token()

token_payload = {
    "sub": user_id,       # Subject: a quién pertenece
    "exp": expire_time,   # Expiration: cuándo expira
    "iat": issued_at,     # Issued at: cuándo se emitió
}

# Firmamos con SECRET_KEY (simétrico)
token = jwt.encode(token_payload, SECRET_KEY, algorithm="HS256")

# Resultado: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c
```

**Estructura del JWT:**
```
[Header].[Payload].[Signature]

Header: {"alg":"HS256","typ":"JWT"}
Payload: {"sub":"user_uuid","exp":1234567890}
Signature: HMAC(SECRET_KEY, Header + "." + Payload)
```

**Flujo de uso:**
```
1. Usuario hace login → Servidor emite JWT
2. Cliente guarda JWT en memoria (nunca en localStorage para apps sensibles)
3. Cliente incluye en cada request: Authorization: Bearer <token>
4. Servidor decodifica y valida la firma
5. Después de 30 minutos, token expira → Usuario debe hacer login de nuevo
```

---

### 4. Auditoría (Trazabilidad Legal)

#### AuditLog - Registro Inmutable
```python
# app/models/audit_log.py

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id: UUID                    # Evento único
    user_id: UUID              # Quién
    event_type: str            # QUÉ (LOGIN, ASSET_ACCESSED, SWITCH_TRIGGERED)
    ip_address: str            # DE DÓNDE
    timestamp: DateTime        # CUÁNDO
    description: str           # POR QUÉ
```

**Eventos registrados:**
- `LOGIN`: Usuario ingresa (IP, fecha/hora)
- `PING_SENT`: Sistema envía alerta de inactividad
- `PING_ACKNOWLEDGED`: Usuario confirma estar vivo
- `ASSET_ACCESSED`: Se accede a un activo (quién y cuándo)
- `SWITCH_TRIGGERED`: Se activa el protocolo de sucesión

**Cumplimiento normativo:**
- GDPR (EU): Requiere trazabilidad de accesos
- LGPD (Brasil): Requiere auditoría de datos personales
- Notarias: Requieren prueba de quién autorizó qué

---

## 🔑 Manejo de Llaves

### Vault Salt (El Puente)
```
┌─────────────────────────────────────┐
│         El Secreto del MVP           │
└─────────────────────────────────────┘

vault_salt es una cadena aleatoria de 64 caracteres (256 bits)
generada una sola vez durante el registro.

Por ejemplo: "3f7a2b8c1e9d4a6f5c3e7b1a9d2c4f6e8a1b3c5d7e9f2a4b6c8e1f3a5b7c9d"

PROPIEDADES CRÍTICAS:
1. Único por usuario
2. Criptográficamente seguro (secrets.token_hex())
3. Se guarda en TEXTO PLANO en la BD (el cliente lo necesita)
4. Se devuelve al usuario en cada login
5. Se combina con la contraseña en el cliente
```

**¿Por qué se puede guardar en texto plano?**
```
- El salt SIN la contraseña es inútil
- El salt + contraseña generan la llave local
- Sin conocer la contraseña, no se puede generar la llave
- La llave nunca viaja al servidor
- Incluso si alguien roba el salt, no puede acceder a los datos
```

---

## 🔐 Escenarios de Ataque y Defensa

### Ataque 1: Robo de Base de Datos (DB Breach)
```
ANTES (sin seguridad):
- Atacante obtiene: emails + password_hashes + activos en texto plano
- Resultado: Acceso total a toda la información

CON CHRONOGUARD:
- Atacante obtiene:
  ├─ emails (no confidenciales)
  ├─ password_hashes (indescifrables con bcrypt)
  ├─ vault_salt (inútil sin contraseña)
  └─ encrypted_payloads (incomprensibles sin llave local)
- Resultado: Información completamente protegida
```

### Ataque 2: Man-in-the-Middle (MITM)
```
DEFENSA:
- HTTPS obligatorio (TLS 1.3)
- JWT firmado (no se puede tampering)
- IV único por cifrado (no se pueden reutilizar patrones)
```

### Ataque 3: Fuerza Bruta en Password
```
DEFENSA:
- Bcrypt: ~0.3 segundos por intento
- Para probar 1 millón de passwords: 3,000+ horas
- Adicionalmente: Rate limiting en endpoints (próximo)
```

### Ataque 4: Admin/DBA Lee la BD
```
DEFENSA:
- encrypted_payloads no tienen valor sin la llave del cliente
- Audit log registra intentos de acceso (detección post-facto)
- Separación de responsabilidades (admin de DB ≠ admin de app)
```

---

## 📋 Checklist de Seguridad para Producción

- [ ] Cambiar `ALGORITHM: "HS256"` a `"RS256"` (asimétrico)
- [ ] Aumentar `PBKDF2 iterations` a 500,000+
- [ ] Implementar rate limiting en endpoints de login
- [ ] Usar `HTTPOnly, Secure, SameSite` cookies para JWT
- [ ] Implementar CORS restrictivo (solo dominios autorizados)
- [ ] Rotar `SECRET_KEY` periódicamente
- [ ] Encriptar base de datos en reposo (AWS RDS encryption)
- [ ] Habilitar backup automático de BD
- [ ] Monitorear audit logs para comportamientos sospechosos
- [ ] Implementar 2FA (Two-Factor Authentication)

---

## 🎓 Referencias Técnicas

- NIST Password Guidelines: https://pages.nist.gov/800-63-3/
- OWASP Top 10: https://owasp.org/www-project-top-ten/
- Web Crypto API: https://developer.mozilla.org/en-US/docs/Web/API/Web_Crypto_API
- JWT Best Practices: https://tools.ietf.org/html/rfc8725
- AES-GCM: https://en.wikipedia.org/wiki/Galois/Counter_Mode

---

## 🤔 Preguntas Frecuentes

**P: ¿Qué pasa si el usuario olvida su contraseña?**
A: Sin "recuperación de contraseña", porque con Zero-Knowledge no podemos resetearla. Solución futura: preguntas de seguridad o dispositivo de backup.

**P: ¿Y si alguien intercepta el encrypted_payload?**
A: Es inútil sin la llave AES-256. Además, cada payload tiene un IV único.

**P: ¿Por qué no usar RSA en lugar de AES?**
A: RSA es lento (asimétrico) y débil para volúmenes grandes. AES es rápido y standard.

**P: ¿Qué sucede si un heredero es comprometido?**
A: Se agrega en el siguiente release: requerir múltiples confirmaciones.
