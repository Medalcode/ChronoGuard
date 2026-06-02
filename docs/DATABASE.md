# Modelo de Datos - ChronoGuard

## 📊 Diagrama Entidad-Relación (DER)

```
                    ┌─────────────────────────┐
                    │        users            │
                    ├─────────────────────────┤
                    │ id (PK, UUID)          │
                    │ email (UNIQUE)          │
                    │ password_hash           │
                    │ vault_salt (UNIQUE)     │
                    │ is_active               │
                    │ created_at              │
                    │ updated_at              │
                    └──────────────┬──────────┘
                                   │
                    ┌──────────────┴──────────────┐
                    │                             │
                    ▼                             ▼
    ┌──────────────────────────────┐  ┌─────────────────────────────┐
    │  switch_configurations       │  │   digital_assets (Fase 2)   │
    ├──────────────────────────────┤  ├─────────────────────────────┤
    │ id (PK, UUID)               │  │ id (PK, UUID)              │
    │ user_id (FK) ─┐             │  │ user_id (FK)               │
    │ ping_interval │             │  │ asset_name                 │
    │ trigger_after │             │  │ asset_type                 │
    │ last_active_at                │  │ encrypted_payload          │
    │ status        │             │  │ s3_object_key (nullable)   │
    │ created_at    │             │  │ created_at                 │
    │ updated_at    │             │  └─────────────┬──────────────┘
    └──────────────┘             │                │
                    │             │                │
                    │             │                ▼
                    │             │  ┌─────────────────────────────┐
                    │             │  │  asset_allocations (Fase 2) │
                    │             │  ├─────────────────────────────┤
                    │             │  │ asset_id (FK)              │
                    │             │  │ beneficiary_id (FK)        │
                    │             │  └──────────┬──────────────────┘
                    │             │             │
                    │             │             ▼
                    │             │  ┌─────────────────────────────┐
                    │             │  │  beneficiaries (Fase 2)     │
                    │             │  ├─────────────────────────────┤
                    │             │  │ id (PK, UUID)              │
                    │             └─→│ user_id (FK)               │
                    │                │ full_name                  │
                    │                │ email                      │
                    │                │ role (HEREDERO|GARANTE)    │
                    │                │ public_key (nullable)      │
                    │                └─────────────────────────────┘
                    │
                    ▼
    ┌──────────────────────────────┐
    │    audit_logs                │
    ├──────────────────────────────┤
    │ id (PK, UUID)               │
    │ user_id (FK, nullable)       │
    │ event_type                   │
    │ description                  │
    │ ip_address                   │
    │ timestamp (indexed)          │
    └──────────────────────────────┘
```

---

## 🗂️ Definición de Tablas

### Tabla: `users` ⭐ PRINCIPAL

**Propósito:** Almacenar usuarios y sus credenciales de acceso.

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    vault_salt VARCHAR(64) UNIQUE NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    INDEX email_idx (email),
    INDEX id_idx (id)
);
```

**Campos:**

| Campo | Tipo | Descripción | Ejemplo |
|-------|------|-------------|---------|
| `id` | UUID | Identificador único inmutable | `550e8400-e29b-41d4-a716-446655440000` |
| `email` | VARCHAR(255) | Correo único - Username | `usuario@example.com` |
| `password_hash` | VARCHAR(255) | Hash bcrypt ($2b$12$...) | No es legible |
| `vault_salt` | VARCHAR(64) | Salt para derivar llave local | `3f7a2b8c...` (64 chars hex) |
| `is_active` | BOOLEAN | Cuenta activada | `true` / `false` |
| `created_at` | TIMESTAMP | Timestamp de creación | `2024-05-11 14:23:45.123456+00` |
| `updated_at` | TIMESTAMP | Última actualización | `2024-05-11 14:23:45.123456+00` |

**Restricciones:**
- `email` UNIQUE: No puede haber dos usuarios con el mismo email
- `vault_salt` UNIQUE: Cada usuario tiene un salt único
- `password_hash` NOT NULL: Siempre debe estar presente

---

### Tabla: `switch_configurations` ⭐ CRÍTICA

**Propósito:** Almacenar la configuración del "Dead Man's Switch" para cada usuario.

```sql
CREATE TABLE switch_configurations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID UNIQUE NOT NULL,
    ping_interval_days INTEGER DEFAULT 7,
    trigger_after_days INTEGER DEFAULT 30,
    last_active_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    status VARCHAR(20) DEFAULT 'ACTIVE',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX user_id_idx (user_id),
    INDEX status_idx (status)
);
```

**Campos:**

| Campo | Tipo | Descripción | Ejemplo |
|-------|------|-------------|---------|
| `id` | UUID | Identificador único | Auto-generado |
| `user_id` | UUID | Referencia al usuario | FK → users.id |
| `ping_interval_days` | INTEGER | Cada cuántos días contactar | `7` (1 semana) |
| `trigger_after_days` | INTEGER | Cuándo activar sucesión | `30` (1 mes) |
| `last_active_at` | TIMESTAMP | Última actividad confirmada | `2024-05-11 10:00:00+00` |
| `status` | VARCHAR(20) | Estado del switch | `ACTIVE`, `WARNING`, `TRIGGERED` |
| `created_at` | TIMESTAMP | Creación | Auto |
| `updated_at` | TIMESTAMP | Última actualización | Auto |

**Lógica de Negocio:**
```
Si AHORA - last_active_at > ping_interval_days:
  → Enviar email de "¿Estás bien?"

Si AHORA - last_active_at > trigger_after_days:
  → Cambiar status a TRIGGERED
  → Ejecutar protocolo de sucesión
```

---

### Tabla: `digital_assets` (Fase 2 - Próximamente)

**Propósito:** Almacenar los activos encriptados del usuario (credenciales, documentos).

```sql
CREATE TABLE digital_assets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    asset_name VARCHAR(255),
    asset_type VARCHAR(50),
    encrypted_payload TEXT NOT NULL,
    s3_object_key VARCHAR(500),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX user_id_idx (user_id)
);
```

**asset_type:**
- `CREDENTIAL`: Contraseña, PIN, clave privada
- `SECURE_NOTE`: Nota cifrada de texto
- `DOCUMENT`: Archivo (testamento, poder notarial)

**Ejemplo de encrypted_payload:**
```
base64(iv + aes_gcm_ciphertext)

Es decir: Los primeros 12 bytes son el IV, el resto es el texto cifrado.
El servidor NO sabe qué contiene. Es incomprensible.
```

---

### Tabla: `beneficiaries` (Fase 2 - Próximamente)

**Propósito:** Definir quién recibe acceso a los activos cuando se activa el switch.

```sql
CREATE TABLE beneficiaries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    full_name VARCHAR(255),
    email VARCHAR(255),
    phone_number VARCHAR(20),
    role VARCHAR(20),
    public_key TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX user_id_idx (user_id)
);
```

**role:**
- `HEREDERO`: Recibe acceso a los activos
- `GARANTE`: Confirma que el usuario está inactivo (valida antes de ejecutar)

---

### Tabla: `asset_allocations` (Fase 2 - Próximamente)

**Propósito:** Relación muchos-a-muchos entre activos y beneficiarios.

```sql
CREATE TABLE asset_allocations (
    asset_id UUID NOT NULL,
    beneficiary_id UUID NOT NULL,
    
    PRIMARY KEY (asset_id, beneficiary_id),
    FOREIGN KEY (asset_id) REFERENCES digital_assets(id) ON DELETE CASCADE,
    FOREIGN KEY (beneficiary_id) REFERENCES beneficiaries(id) ON DELETE CASCADE
);
```

**Ejemplo:**
```
Un usuario tiene:
- Asset 1: "Contraseña del banco"
- Asset 2: "Clave privada de cripto"
- Asset 3: "Testamento digital"

Y beneficiarios:
- Heredero A: Mi hijo
- Heredero B: Mi esposa
- Garante: Mi abogado

asset_allocations podría ser:
├─ Asset 1 → Heredero B (solo la esposa recibe el banco)
├─ Asset 2 → Heredero A (solo el hijo recibe cripto)
└─ Asset 3 → Ambos (ambos herederos reciben el testamento)
```

---

### Tabla: `audit_logs` ⭐ SEGURIDAD

**Propósito:** Trazabilidad inmutable de todos los eventos críticos.

```sql
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID,
    event_type VARCHAR(50) NOT NULL,
    description VARCHAR(500),
    ip_address VARCHAR(45),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX user_id_idx (user_id),
    INDEX event_type_idx (event_type),
    INDEX timestamp_idx (timestamp)
);
```

**event_type valores:**

| Evento | Descripción | user_id |
|--------|-------------|---------|
| `LOGIN` | Usuario inicia sesión | Sí |
| `REGISTRATION` | Usuario se registra | Sí |
| `PING_SENT` | Sistema envía alerta | Sí |
| `PING_ACKNOWLEDGED` | Usuario confirma estar vivo | Sí |
| `ASSET_CREATED` | Usuario crea activo cifrado | Sí |
| `ASSET_ACCESSED` | Se accede a un activo | Sí |
| `ASSET_DELETED` | Se elimina un activo | Sí |
| `BENEFICIARY_ADDED` | Se agrega heredero | Sí |
| `SWITCH_TRIGGERED` | Se activa protocolo de sucesión | Sí |
| `SUCCESSION_EXECUTED` | Se liberan activos a herederos | Sí |

---

## 🔍 Queries Útiles para Testing

### Listar todos los usuarios
```sql
SELECT id, email, is_active, created_at FROM users;
```

### Ver configuración del Dead Man's Switch
```sql
SELECT 
    u.email,
    sc.ping_interval_days,
    sc.trigger_after_days,
    sc.last_active_at,
    EXTRACT(DAY FROM NOW() - sc.last_active_at) as dias_inactivo,
    sc.status
FROM switch_configurations sc
JOIN users u ON sc.user_id = u.id;
```

### Identificar usuarios cercanos al trigger
```sql
SELECT 
    u.email,
    sc.trigger_after_days,
    EXTRACT(DAY FROM NOW() - sc.last_active_at) as dias_inactivo
FROM switch_configurations sc
JOIN users u ON sc.user_id = u.id
WHERE EXTRACT(DAY FROM NOW() - sc.last_active_at) > (sc.trigger_after_days * 0.8)
ORDER BY dias_inactivo DESC;
```

### Ver actividad de un usuario
```sql
SELECT event_type, description, ip_address, timestamp
FROM audit_logs
WHERE user_id = '550e8400-e29b-41d4-a716-446655440000'
ORDER BY timestamp DESC
LIMIT 20;
```

### Contar eventos por tipo
```sql
SELECT event_type, COUNT(*) as count
FROM audit_logs
GROUP BY event_type
ORDER BY count DESC;
```

---

## 🗄️ Migraciones (Alembic)

Cuando agregas una tabla nueva o modificas una existente, documenta el cambio:

```bash
# Crear migración automática
alembic revision --autogenerate -m "Add beneficiaries table"

# Ejecutar migración
alembic upgrade head
```

---

## 📈 Índices para Performance

```sql
-- Índices ya configurados en los CREATE TABLE

-- Adicionales recomendados para producción:
CREATE INDEX idx_audit_logs_user_timestamp ON audit_logs(user_id, timestamp DESC);
CREATE INDEX idx_assets_user_created ON digital_assets(user_id, created_at DESC);
CREATE INDEX idx_switch_status_lastactive ON switch_configurations(status, last_active_at);
```

---

## 🚀 Crecimiento Futuro

La arquitectura actual es escalable:

### MVP (Actual)
- users
- switch_configurations
- audit_logs

### Fase 2 (SaaS)
- digital_assets
- beneficiaries
- asset_allocations

### Fase 3 (B2B)
- Agregar tabla `organizations` (multi-tenant)
- Agregar tabla `api_keys` (integración)
- Agregar tabla `subscription` (pago)

---

## 📝 Backup y Recovery

```bash
# Backup completo
pg_dump -h localhost -U postgres chronoguard_dev > backup.sql

# Restore
psql -h localhost -U postgres chronoguard_dev < backup.sql

# Backup incremental con WAL
pg_basebackup -h localhost -U postgres -D /backups/base -Fp -Xs
```

---

## 🔐 Privacidad de Datos

**GDPR Compliance:**
- ✅ encrypted_payloads no son legibles
- ✅ audit_logs permiten prueba de acceso
- ✅ Derecho al olvido: CASCADE DELETE en user_id

**Datos que el usuario puede solicitar:**
- Su lista de activos (sin poder descifrarlos)
- Su histórico de auditoría
- Su configuración de switch
