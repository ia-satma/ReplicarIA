# Plan de Acción: ReplicarIA - 2 Semanas

**Objetivo:** Sistema fiscal funcionando end-to-end para clientes actuales
**Fecha:** 30 Enero 2026
**Prioridad:** CRÍTICO - Hay clientes pagando

---

## SEMANA 1: Hacer que Funcione

### Día 1-2: Configuración y Variables de Entorno

**Problema:** Sin variables configuradas, nada funciona.

```bash
# Variables CRÍTICAS (sin estas NO funciona):
OPENAI_API_KEY=sk-...          # IA de los agentes
MONGO_URL=mongodb+srv://...     # Base de datos principal
DATABASE_URL=postgresql://...   # Usuarios y auth
SECRET_KEY=clave-minimo-32-chars  # JWT tokens

# Variables IMPORTANTES (degradado sin estas):
DREAMHOST_EMAIL_PASSWORD=...    # Emails entre agentes
PCLOUD_USERNAME=...             # Storage de archivos
PCLOUD_PASSWORD=...
```

**Tareas:**
- [ ] Crear archivo `.env` con todas las variables
- [ ] Verificar que OPENAI_API_KEY sea válida (test simple)
- [ ] Verificar conexión a MongoDB
- [ ] Verificar conexión a PostgreSQL
- [ ] Documentar en README cómo configurar

---

### Día 2-3: Fallback de IA (CRÍTICO)

**Problema:** Si OpenAI falla, el sistema muere.

**Archivo a modificar:** `backend/services/openai_provider.py`

```python
# ANTES (actual):
def _get_client():
    if not api_key:
        return None  # ← MUERE

# DESPUÉS (con fallback):
def _get_client():
    if not api_key:
        return _get_anthropic_fallback()  # ← Plan B
```

**Tareas:**
- [ ] Agregar Anthropic como fallback en openai_provider.py
- [ ] Crear función _get_anthropic_fallback()
- [ ] Modificar agentic_reasoning_service.py para usar fallback
- [ ] Test: Deshabilitar OpenAI, verificar que Anthropic funciona

---

### Día 3-4: Arreglar Flujo de Deliberación

**Problema:** El sistema dice "11 agentes" pero solo hay 4 implementados.

**Decisión:** Mantener 4 agentes pero que funcionen BIEN.

**Agentes reales implementados:**
1. A1_ESTRATEGIA (María) - Razón de Negocios
2. A3_FISCAL (Laura) - Deducibilidad
3. A5_FINANZAS (Roberto) - ROI/BEE
4. A4_LEGAL - Compliance

**Tareas:**
- [ ] Actualizar documentación (cambiar "11" por "4")
- [ ] Verificar que los 4 agentes ejecutan correctamente
- [ ] Agregar timeout por agente (máx 60 segundos c/u)
- [ ] Agregar retry si un agente falla (máx 2 intentos)

---

### Día 4-5: Error Handling Robusto

**Problema:** 18 bloques try-except sin plan B real.

**Archivo principal:** `backend/services/deliberation_orchestrator.py`

**Tareas:**
- [ ] Revisar cada try-except y agregar fallback real
- [ ] Si MongoDB falla → Guardar en PostgreSQL temporalmente
- [ ] Si agente falla → Continuar con los otros, marcar como "pendiente"
- [ ] Agregar logs estructurados (no solo print)

---

### Día 5-6: Test End-to-End Manual

**Flujo a probar:**
```
1. POST /api/projects/submit (crear proyecto)
2. GET /api/projects/processing-status/{id} (poll cada 2s)
3. Verificar que 4 agentes deliberan
4. GET /api/defense-file/download/{id} (descargar PDF)
5. Verificar PDF tiene contenido de cada agente
```

**Tareas:**
- [ ] Crear script de test e2e
- [ ] Probar con proyecto real de cliente
- [ ] Documentar cualquier error encontrado
- [ ] Fix bugs encontrados

---

## SEMANA 2: Estabilizar y Optimizar

### Día 7-8: Índices de Base de Datos

**Problema:** Queries lentas sin índices.

```javascript
// MongoDB - ejecutar en shell
db.projects.createIndex({"empresa_id": 1})
db.projects.createIndex({"created_at": -1})
db.defense_files.createIndex({"project_id": 1})
db.deliberations.createIndex({"project_id": 1, "agent_id": 1})
```

**Tareas:**
- [ ] Crear script de índices MongoDB
- [ ] Ejecutar en producción
- [ ] Verificar mejora de performance

---

### Día 8-9: Health Check Mejorado

**Problema:** `/api/health` no verifica dependencias reales.

**Archivo:** `backend/server.py`

```python
@api_router.get("/health")
async def health_check():
    checks = {
        "mongodb": await check_mongodb(),
        "postgresql": await check_postgresql(),
        "openai": check_openai_key(),
        "status": "healthy" if all_ok else "degraded"
    }
    return checks
```

**Tareas:**
- [ ] Agregar verificación real de MongoDB
- [ ] Agregar verificación real de PostgreSQL
- [ ] Agregar verificación de API key OpenAI
- [ ] Retornar status "degraded" si algo falla

---

### Día 9-10: Rate Limiting Básico

**Problema:** Sin límites, un cliente puede saturar OpenAI.

**Implementación simple:**

```python
# backend/middleware/rate_limit.py
from slowapi import Limiter
limiter = Limiter(key_func=get_empresa_id)

@app.post("/api/projects/submit")
@limiter.limit("10/hour")  # Máx 10 proyectos por hora por empresa
async def submit_project():
    ...
```

**Tareas:**
- [ ] Instalar slowapi
- [ ] Agregar rate limit a /api/projects/submit
- [ ] Agregar rate limit a endpoints de deliberación
- [ ] Retornar error 429 con mensaje claro

---

### Día 10-11: Monitoreo Básico

**Problema:** Sin visibilidad de errores en producción.

**Opción rápida:** Sentry (gratis hasta 5k eventos/mes)

```python
# backend/server.py
import sentry_sdk
sentry_sdk.init(dsn=os.environ.get("SENTRY_DSN"))
```

**Tareas:**
- [ ] Crear cuenta Sentry
- [ ] Agregar SENTRY_DSN a .env
- [ ] Integrar en server.py
- [ ] Verificar que errores aparecen en dashboard

---

### Día 11-12: Documentación para Clientes

**Problema:** Clientes no saben cómo usar el sistema.

**Tareas:**
- [ ] Crear guía rápida "Cómo crear tu primer proyecto"
- [ ] Crear FAQ de errores comunes
- [ ] Documentar qué significa cada score (0-25 por pilar)
- [ ] Crear video corto (5 min) del flujo completo

---

### Día 13-14: Buffer y Deploy

**Tareas:**
- [ ] Fix de bugs encontrados durante la semana
- [ ] Deploy a producción
- [ ] Smoke test con 1 cliente real
- [ ] Monitorear errores en Sentry

---

## Checklist Final

### Antes de entregar a clientes:

```
[ ] OpenAI API funcionando
[ ] MongoDB conectada
[ ] PostgreSQL conectada
[ ] 4 agentes deliberan correctamente
[ ] PDF se genera con contenido
[ ] Health check retorna estado real
[ ] Rate limiting activo
[ ] Sentry capturando errores
[ ] Documentación básica lista
```

---

## Qué NO Hacer en Estas 2 Semanas

❌ NO agregar nuevos agentes (7 faltantes)
❌ NO crear módulo de revisión de contratos
❌ NO refactorizar código que funciona
❌ NO cambiar arquitectura de BD
❌ NO agregar features nuevas

**Enfoque:** Hacer que lo actual funcione BIEN.

---

## Después de las 2 Semanas (Backlog)

1. Implementar agentes faltantes (si hay demanda)
2. Mejorar UX del frontend
3. Agregar notificaciones push
4. Dashboard de métricas para clientes
5. API para integraciones terceros

---

## Archivos Críticos a Modificar

| Archivo | Cambio | Prioridad |
|---------|--------|-----------|
| `backend/services/openai_provider.py` | Fallback Anthropic | CRÍTICO |
| `backend/services/deliberation_orchestrator.py` | Error handling | CRÍTICO |
| `backend/server.py` | Health check real | ALTO |
| `backend/.env` | Variables completas | CRÍTICO |
| `README.md` | Documentación setup | ALTO |

---

*Plan creado el 30 Enero 2026 - Revisar progreso diario*
