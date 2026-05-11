# Dead Man's Switch - Lógica de Automatización

## 🔔 ¿Qué es el Dead Man's Switch?

Un "Dead Man's Switch" es un mecanismo de seguridad que se **activa automáticamente en caso de inactividad**.

### Ejemplo del Mundo Real:
```
Conductor de tren → Mantiene botón presionado mientras conduce
Si suelta el botón (incapacidad, muerte) → Frenos se aplican automáticamente
```

### En ChronoGuard:
```
Usuario → Usa la app regularmente
Si NO usa la app en X días → Se ejecuta protocolo de liberación de activos
```

---

## 📋 Flujo de Lógica

### Escenario Normal (Usuario Activo)

```
Día 1: Usuario hace login
  └─ last_active_at = NOW()
  └─ status = ACTIVE
  └─ 0 días de inactividad

Día 4: Usuario abre la app
  └─ Hace un POST /switch/ping
  └─ last_active_at = NOW() (se reinicia)
  └─ 0 días de inactividad

Día 20: Usuario no hace nada
  └─ Scheduler corre a las 03:00 AM
  └─ Detecta: 20 días sin actividad
  └─ ping_interval_days = 7 (configurado)
  └─ PERO: 20 > 7, Y última vez que se envió ping fue hace poco
  └─ No hace nada extra (ya está avisado)
```

---

### Escenario de Alerta (Nivel 1)

```
Día 8: Usuario lleva 8 días sin actividad
  └─ Scheduler corre a las 03:00 AM
  └─ Calcula: 8 días >= ping_interval_days (7)
  └─ ACCIÓN:
     ├─ Envía email: "¿Estás bien? Por favor confirma"
     ├─ Email contiene enlace a /confirm-alive
     └─ Registra en audit_logs: PING_SENT

Usuario recibe email → Haz clic en enlace
  └─ Endpoint redirige a /switch/ping
  └─ last_active_at = NOW()
  └─ Estado vuelve a ACTIVE
  └─ Contador se reinicia
```

---

### Escenario de Trigger (Nivel 2 - CRÍTICO)

```
Día 30: Usuario lleva 30 días sin actividad
  └─ Scheduler corre a las 03:00 AM
  └─ Calcula: 30 días >= trigger_after_days (30)
  └─ Y status != TRIGGERED (aún no activado)
  └─ ACCIÓN MASIVA:
     ├─ Cambiar status = TRIGGERED
     ├─ Registrar en audit_logs: SWITCH_TRIGGERED
     ├─ Buscar en beneficiaries los herederos
     ├─ Para cada heredero:
     │  ├─ Generar access_token temporal (24 horas)
     │  ├─ Listar sus activos asignados (asset_allocations)
     │  └─ Enviar email:
     │     "Has sido designado como heredero. 
     │      Acceso temporal a activos disponibles."
     └─ Ejecutar protocolo de liberación

Heredero recibe email → Accede con token temporal
  └─ Puede leer (desencriptar) los activos asignados
  └─ Genera reporte o descarga la información
  └─ Token expira en 24 horas
  └─ Todas las acciones quedan en audit_logs
```

---

## ⚙️ Configuración del Switch

### Parámetros Ajustables

```python
# Usuario configura en la app:

ping_interval_days = 7      # Cada cuánto contactar (en días)
trigger_after_days = 30     # Cuándo ejecutar sucesión (en días)

# Lógica:
- Si dias_inactivos >= ping_interval_days:
    → Enviar alerta
  
- Si dias_inactivos >= trigger_after_days:
    → Activar protocolo de sucesión
```

### Escenarios de Configuración

#### Escenario 1: Persona Muy Ocupada
```
ping_interval_days = 30    # No molestar tan frecuente
trigger_after_days = 90    # 3 meses antes de activar
```

#### Escenario 2: Persona Cautelosa
```
ping_interval_days = 3     # Pingear semanalmente (3 veces)
trigger_after_days = 14    # 2 semanas
```

#### Escenario 3: Profesional Viajero
```
ping_interval_days = 14    # Cada 2 semanas
trigger_after_days = 60    # 2 meses (viajes largos)
```

---

## 🔄 Implementación del Scheduler

### Archivo: `app/workers/scheduler.py`

```python
def evaluate_dead_mans_switches():
    """Corre diariamente a las 03:00 AM UTC"""
    
    # 1. Conectar a BD
    db = SessionLocal()
    
    # 2. Obtener todas las configuraciones
    configs = db.query(SwitchConfiguration).all()
    
    # 3. Para cada usuario
    for config in configs:
        # 4. Calcular días inactivos
        dias_inactivos = (NOW() - config.last_active_at).days
        
        # 5. NIVEL 1: Alerta
        if dias_inactivos >= config.ping_interval_days and config.status == "ACTIVE":
            send_email(config.user_id, "ping")
            audit_log(config.user_id, "PING_SENT")
        
        # 6. NIVEL 2: Trigger
        elif dias_inactivos >= config.trigger_after_days and config.status != "TRIGGERED":
            config.status = "TRIGGERED"
            execute_succession_protocol(config.user_id)
            audit_log(config.user_id, "SWITCH_TRIGGERED")
    
    # 7. Guardar cambios
    db.commit()
```

### Configuración de Frecuencia

```python
# Ejecutar diariamente a las 03:00 AM UTC
scheduler.add_job(
    evaluate_dead_mans_switches,
    "cron",
    hour=3,
    minute=0,
    id="evaluate_switches"
)

# Alternativa para testing (cada 10 segundos):
# scheduler.add_job(
#     evaluate_dead_mans_switches,
#     "interval",
#     seconds=10
# )
```

---

## 📧 Emails Enviados

### Email 1: Alerta de Ping
```
Asunto: ChronoGuard - ¿Estás bien?

Cuerpo:
Hola [Nombre],

Hemos detectado que llevas [X] días sin acceder a tu bóveda de ChronoGuard.

Para confirmar que todo está en orden, por favor haz clic en el enlace abajo:
[LINK: /confirm-alive?token=xxxxx]

Este enlace expira en 24 horas.

Si no hiciste clic, no te preocupes - recibirás un recordatorio en [Y] días.

Equipo ChronoGuard
```

### Email 2: Activación de Sucesión (a Herederos)
```
Asunto: ⚠️ IMPORTANTE - Has sido designado como heredero digital

Cuerpo:
Hola [Nombre del Heredero],

Has sido designado como beneficiario de la bóveda digital de [Usuario].

Debido a que [Usuario] ha estado inactivo por más de [X] días,
el protocolo de liberación de activos ha sido activado.

Acceso Temporal:
- Token: [TEMPORAL_TOKEN]
- Válido hasta: [TIMESTAMP + 24 HORAS]
- Acceso en: https://app.chronoguard.com/heredero/acceso

Activos disponibles para ti:
1. Contraseña del Banco
2. Documentos de Identidad
3. Testamento Digital

SEGURIDAD: Este email contiene información sensible. No lo compartas.

Equipo ChronoGuard
```

---

## 🔐 Tokens Temporales para Herederos

### Generación

```python
# El servidor genera un JWT temporal
temp_token = jwt.encode(
    {
        "sub": beneficiary_id,
        "type": "temporary_access",
        "exp": NOW() + timedelta(hours=24),
        "assets": [asset_id_1, asset_id_2]  # Assets asignados
    },
    SECRET_KEY,
    algorithm="HS256"
)
```

### Validación

```python
# Cuando el heredero intenta acceder:
@app.get("/vault/assets")
def get_assets(current_user=Depends(get_current_user)):
    # Si es un temp token, solo devuelve los assets asignados
    if current_user.token_type == "temporary_access":
        return [a for a in assets if a.id in current_user.assets]
    # Si no, devuelve todos sus assets
    else:
        return assets
```

---

## 📊 Estados Posibles

```
┌─────────────┐
│   ACTIVE    │  Estado normal, monitoreando inactividad
└──────┬──────┘
       │ (después de ping_interval_days)
       ▼
┌─────────────┐
│  WARNING    │  Usuario recibió alerta, en modo "advertencia"
└──────┬──────┘
       │ (si no responde y continúa inactivo)
       ▼
┌──────────────┐
│  TRIGGERED   │  Se activó protocolo, herederos notificados
└──────────────┘
       │
       └─→ Sin reversión automática (requiere intervención manual)
```

---

## 🔄 Escenario Completo: Paso a Paso

```
VIERNES 8 DE MAYO
├─ Usuario Juan se registra
├─ Configura: ping_interval_days=7, trigger_after_days=30
├─ Designa a su hijo Carlos como heredero
└─ Sube contraseñas cifradas a la bóveda

MARTES 15 DE MAYO (7 días después)
├─ Scheduler corre a las 03:00 AM
├─ Detecta: Juan lleva 7 días sin actividad
├─ ALERTA NIVEL 1:
│  ├─ Envía email a Juan: "¿Estás bien?"
│  ├─ Registra evento en audit_logs: PING_SENT
│  └─ Status sigue en ACTIVE

MIÉRCOLES 16 DE MAYO (8 días después)
├─ Juan recibe email
├─ Haz clic en enlace: /confirm-alive
├─ GET /switch/ping → last_active_at = NOW()
├─ Contador se reinicia a 0 días
└─ Todo vuelve a la normalidad

[Pero si Juan NO hubiera respondido...]

VIERNES 8 DE JUNIO (30 días después, si no respondía)
├─ Scheduler corre a las 03:00 AM
├─ Detecta: Juan lleva 30 días sin actividad
├─ TRIGGER NIVEL 2:
│  ├─ Cambiar status = TRIGGERED
│  ├─ Buscar beneficiarios: Carlos (heredero)
│  ├─ Buscar activos de Carlos: Contraseña del banco
│  ├─ Generar token temporal válido 24 horas
│  ├─ Enviar email a Carlos:
│  │  "Has sido designado como heredero.
│  │   Acceso temporal a: Contraseña del banco"
│  ├─ Registrar en audit_logs: SWITCH_TRIGGERED
│  └─ Esperar acceso de Carlos

SÁBADO 9 DE JUNIO
├─ Carlos recibe email
├─ Accede a https://app.chronoguard.com/heredero/acceso
├─ Se autentica con token temporal
├─ Ve: "Contraseña del banco (confidencial)"
├─ Puede desencriptar localmente con su llave
├─ Ve el contenido cifrado
└─ Token expira en 24 horas

[En audit_logs quedó registrado TODO]
```

---

## 🛡️ Seguridad del Scheduler

### Amenaza 1: Duplicadas de Ejecución
```python
# Usar locks en la BD para evitar race conditions
scheduler.add_job(..., misfire_grace_time=60)
```

### Amenaza 2: Emails No Llegarán
```python
# Retry automático con exponential backoff
max_retries = 3
retry_delay = exponential_backoff(attempt)
```

### Amenaza 3: Server Se Cae
```python
# Guardar último timestamp de ejecución
# Si falla, corre de nuevo con task_id persistente
```

---

## 📝 Logs del Scheduler (Testing)

Para ver qué hace el scheduler en desarrollo:

```bash
# Terminal 1: Inicia servidor
uvicorn app.main:app --reload

# Terminal 2: Modifica scheduler para ejecutar cada 10 seg
# Edita app/workers/scheduler.py: scheduler.add_job(..., "interval", seconds=10)

# Verás en logs:
# [03:00:00] Iniciando evaluación de Dead Man's Switches...
# [03:00:00] 📧 PING: Usuario 550e... lleva 8 días inactivo
# [03:00:00] ⚠️  CRÍTICO: Usuario 550e... superó 30 días...
# [03:00:00] ✅ Evaluación completada
```

---

## 🚀 Próximas Mejoras

### MVP (Actual)
- [x] Scheduler básico
- [x] Notificaciones por email
- [x] Status transitions

### Fase 2 (SaaS)
- [ ] Notificaciones por SMS (Twilio)
- [ ] Notificaciones por WhatsApp
- [ ] Múltiples niveles de confirmación (garantes)
- [ ] Integración con Registro Civil (validar defunción)
- [ ] Reversión manual del trigger

### Fase 3 (B2B)
- [ ] Webhooks para integradores
- [ ] Smart Contracts para transferencias de cripto
- [ ] Notificaciones push (mobile app)
