# Arquitectura de Microfunciones - Workers + ReplicarIA

## Visión General

Esta arquitectura permite que **Cloudflare Workers** actúen como **microfunciones especializadas** que complementan y aseguran el funcionamiento de los agentes de ReplicarIA. Cada Worker es un "trabajador" independiente pero interconectado que desahoga tareas específicas.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           REPLICAR.IA PLATFORM                               │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                         AGENTES PRINCIPALES                          │    │
│  │  A1_SPONSOR │ A2_PMO │ A3_FISCAL │ A4_LEGAL │ A5_FINANZAS │ A6_PROV │    │
│  └──────┬──────────┬─────────┬──────────┬──────────┬──────────┬────────┘    │
│         │          │         │          │          │          │             │
│         └──────────┴─────────┴──────────┴──────────┴──────────┘             │
│                                   │                                          │
│  ┌────────────────────────────────▼────────────────────────────────────┐    │
│  │                    workers_hub_service.py                            │    │
│  │  - Ejecuta tareas en Workers                                         │    │
│  │  - Maneja pipelines                                                  │    │
│  │  - Recibe callbacks                                                  │    │
│  │  - Coordina con agentes                                              │    │
│  └────────────────────────────────┬────────────────────────────────────┘    │
│                                   │                                          │
│  ┌────────────────────────────────▼────────────────────────────────────┐    │
│  │                     /webhooks/worker-callback                        │    │
│  │  - Endpoint para recibir resultados                                  │    │
│  │  - Notifica a agentes                                                │    │
│  │  - Actualiza estado de proyectos                                     │    │
│  └────────────────────────────────┬────────────────────────────────────┘    │
└───────────────────────────────────│─────────────────────────────────────────┘
                                    │
                        ════════════╪════════════
                        HTTPS (Internet)
                        ════════════╪════════════
                                    │
┌───────────────────────────────────▼─────────────────────────────────────────┐
│                         CLOUDFLARE WORKERS EDGE                              │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                         WORKERS HUB                                   │   │
│  │                   (Orquestador Central)                               │   │
│  │                                                                       │   │
│  │   /execute     - Ejecutar tarea individual                           │   │
│  │   /pipeline    - Ejecutar secuencia de tareas                        │   │
│  │   /webhook/*   - Recibir eventos de ReplicarIA                       │   │
│  │   /proxy/*     - Enrutar a Worker específico                         │   │
│  └─────────────────────────────┬────────────────────────────────────────┘   │
│                                │                                             │
│         ┌──────────────────────┼──────────────────────┐                     │
│         │                      │                      │                     │
│         ▼                      ▼                      ▼                     │
│  ┌─────────────┐       ┌─────────────┐       ┌─────────────┐               │
│  │   ORÁCULO   │       │   LECTOR    │       │  REDACTOR   │               │
│  │ ESTRATÉGICO │       │   DOCS      │       │   COMMS     │               │
│  │             │       │             │       │             │               │
│  │ •investigar │       │ •OCR        │       │ •emails     │               │
│  │ •due dilig  │       │ •PDF        │       │ •reportes   │               │
│  │ •PESTEL     │       │ •imágenes   │       │ •resúmenes  │               │
│  │ •Porter     │       │             │       │             │               │
│  │ •ESG        │       │             │       │             │               │
│  │ •materialid │       │             │       │             │               │
│  └─────────────┘       └─────────────┘       └─────────────┘               │
│                                                                              │
│         ┌──────────────────────┬──────────────────────┐                     │
│         ▼                      ▼                      ▼                     │
│  ┌─────────────┐       ┌─────────────┐       ┌─────────────┐               │
│  │  VALIDADOR  │       │   SCRAPER   │       │   FUTURO    │               │
│  │     SAT     │       │    WEB      │       │   WORKER    │               │
│  │             │       │             │       │             │               │
│  │ •Lista 69-B │       │ •scraping   │       │ •nueva      │               │
│  │ •CFDI       │       │ •monitoreo  │       │  capacidad  │               │
│  │ •32-D       │       │             │       │             │               │
│  └─────────────┘       └─────────────┘       └─────────────┘               │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

## Flujo de Comunicación

### 1. ReplicarIA → Workers (Ejecutar Tarea)

```python
# Desde un agente o servicio de ReplicarIA
from services.workers_hub_service import workers_hub_service

# Opción 1: Tarea individual
result = await workers_hub_service.ejecutar_tarea(
    tarea="investigacion",
    parametros={"empresa": "Acme Corp", "sitio_web": "https://acme.mx"},
    agente_id="A6_PROVEEDOR",
    empresa_id="EMP-001",
    proyecto_id="PROJ-123"
)

# Opción 2: Pipeline de tareas
result = await workers_hub_service.ejecutar_pipeline(
    pasos=[
        {"tarea": "scraping", "parametros": {"url": "https://proveedor.mx"}},
        {"tarea": "investigacion", "parametros": {"empresa": "..."}},
        {"tarea": "materialidad", "parametros": {"monto": 100000}}
    ],
    empresa_id="EMP-001",
    callback_url="/webhooks/worker-callback"
)

# Opción 3: Métodos de conveniencia
result = await workers_hub_service.investigar_proveedor(
    empresa="Digital Solutions",
    rfc="DSM180115ABC",
    sitio_web="https://digitalsolutions.mx",
    monto=500000
)
```

### 2. Workers → ReplicarIA (Callback)

Cuando un Worker termina una tarea asíncrona:

```javascript
// Dentro del Worker
await fetch(callback_url, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-Worker-Callback': 'true'
  },
  body: JSON.stringify({
    tarea: 'investigacion',
    resultado: { /* datos */ },
    agente_id: 'A6_PROVEEDOR',
    empresa_id: 'EMP-001',
    proyecto_id: 'PROJ-123'
  })
});
```

### 3. ReplicarIA → Workers Hub (Webhook de Eventos)

Cuando ocurre un evento en ReplicarIA que requiere acción de Workers:

```python
# En deliberation_orchestrator o similar
await aiohttp.post(
    f"{WORKERS_HUB_URL}/webhook/replicaria",
    json={
        "evento": "nuevo_proveedor",
        "datos": {
            "empresa": "Nuevo Proveedor S.A.",
            "rfc": "NPS...",
            "sitio_web": "https://..."
        },
        "proyecto_id": "PROJ-456",
        "empresa_id": "EMP-001"
    }
)
```

## Mapeo de Workers por Agente

| Agente | Workers que Usa | Tareas Típicas |
|--------|-----------------|----------------|
| A1_SPONSOR | oraculo-estrategico | PESTEL, Porter, análisis estratégico |
| A2_PMO | redactor-comunicaciones | Notificaciones, coordinación |
| A3_FISCAL | validador-sat, oraculo | Lista 69-B, CFDI, razón de negocios |
| A4_LEGAL | lector-documentos | Análisis de contratos |
| A5_FINANZAS | oraculo-estrategico | Análisis económico |
| A6_PROVEEDOR | oraculo-estrategico, validador-sat | Due diligence completo |
| A7_DEFENSA | redactor, lector | Reportes, consolidación |
| A8_AUDITOR | lector-documentos | OCR, análisis PDF |
| S2_MATERIALIDAD | oraculo-estrategico | Documentación SAT |
| S3_RIESGOS | validador-sat | Verificación 69-B |
| KB_CURATOR | scraper-web | Actualización de conocimiento |

## Configuración

### Variables de Entorno (ReplicarIA)

```bash
# URL del Hub central
WORKERS_HUB_URL=https://workers-hub.tu-cuenta.workers.dev

# URL del Oráculo (si se usa directo)
ORACULO_WORKER_URL=https://oraculo-estrategico.tu-cuenta.workers.dev

# API Key para autenticación (opcional)
WORKERS_API_KEY=tu-api-key-secreto
```

### Variables de Entorno (Workers)

```bash
# En cada Worker (configurar con wrangler secret)
ANTHROPIC_API_KEY=sk-ant-...
PERPLEXITY_API_KEY=pplx-...
FIRECRAWL_API_KEY=fc-...

# URL de callback de ReplicarIA
REPLICARIA_CALLBACK_URL=https://api.revisar-ia.com/webhooks/worker-callback
```

## Endpoints del Hub

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/health` | Health check del Hub |
| GET | `/workers` | Lista de Workers registrados |
| GET | `/workers/health` | Health de todos los Workers |
| POST | `/execute` | Ejecutar tarea individual |
| POST | `/pipeline` | Ejecutar pipeline de tareas |
| POST | `/webhook/replicaria` | Recibir eventos de ReplicarIA |
| * | `/proxy/{worker}/*` | Proxy a Worker específico |

## Endpoints de ReplicarIA

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/webhooks/worker-callback` | Recibir callbacks de Workers |
| GET | `/webhooks/workers/status` | Estado de Workers |
| GET | `/webhooks/workers/capabilities` | Capacidades disponibles |
| POST | `/webhooks/workers/execute` | Ejecutar tarea desde API |
| POST | `/webhooks/workers/pipeline` | Ejecutar pipeline desde API |
| POST | `/webhooks/workers/due-diligence` | Due diligence directo |
| POST | `/webhooks/workers/materialidad` | Materialidad directo |
| POST | `/webhooks/workers/verificar-69b` | Verificar lista 69-B |

## Agregar Nuevo Worker

### 1. Crear el Worker

```javascript
// nuevo-worker/worker.js
export default {
  async fetch(request, env) {
    // Implementar endpoints...
    // /health - obligatorio
    // /api/{tarea} - endpoints de tareas
  }
};
```

### 2. Registrar en el Hub

Editar `workers-hub/worker.js`:

```javascript
const WORKERS_REGISTRY = {
  // ... workers existentes
  'nuevo-worker': {
    url: 'https://nuevo-worker.tu-cuenta.workers.dev',
    capabilities: ['nueva_tarea', 'otra_tarea'],
    agentes: ['A1_SPONSOR', 'A3_FISCAL'],
    timeout: 60000
  }
};
```

### 3. Agregar Herramienta en ReplicarIA (Opcional)

```python
# backend/services/tools/nuevas_tools.py
@tool(
    name="nueva_tarea",
    description="Descripción de la nueva tarea",
    parameters={...}
)
async def nueva_tarea(parametro: str) -> Dict[str, Any]:
    from services.workers_hub_service import workers_hub_service
    return await workers_hub_service.ejecutar_tarea(
        tarea="nueva_tarea",
        parametros={"parametro": parametro}
    )
```

## Manejo de Errores

### Timeouts

Cada Worker tiene un timeout configurado. Si se excede:

```python
WorkerResult(
    success=False,
    error="Timeout esperando Worker",
    worker_id="timeout"
)
```

### Workers No Disponibles

Si el Hub no encuentra un Worker para la tarea:

```json
{
  "error": "No hay Worker disponible para la tarea: xyz",
  "tareas_disponibles": ["investigacion", "due_diligence", ...]
}
```

### Reintentos

El servicio no hace reintentos automáticos. Implementar en el llamador si es necesario:

```python
max_retries = 3
for attempt in range(max_retries):
    result = await workers_hub_service.ejecutar_tarea(...)
    if result.success:
        break
    await asyncio.sleep(2 ** attempt)  # Backoff exponencial
```

## Monitoreo

### Logs

Todos los servicios registran en el logger estándar:

```python
logger.info(f"Ejecutando tarea: {tarea} (agente: {agente_id})")
logger.error(f"Error ejecutando tarea {tarea}: {e}")
```

### Métricas (Futuro)

Integrar con el sistema de métricas existente en `routes/metrics.py`:

```python
from routes.metrics import track_worker_execution, track_worker_latency

# En workers_hub_service.py
await track_worker_execution(tarea, result.success)
await track_worker_latency(tarea, elapsed_time)
```

## Seguridad

1. **Autenticación**: Los Workers pueden validar un token Bearer
2. **CORS**: El Hub permite cualquier origen (ajustar en producción)
3. **Rate Limiting**: Implementar en Cloudflare dashboard
4. **Validación de Callbacks**: Verificar header `X-Worker-Callback`

## Próximos Pasos

1. [ ] Implementar Workers adicionales (lector-documentos, redactor, validador-sat, scraper)
2. [ ] Agregar autenticación JWT entre servicios
3. [ ] Implementar cache de resultados en KV
4. [ ] Dashboard de monitoreo de Workers
5. [ ] Alertas cuando Workers fallan
6. [ ] Rate limiting por empresa
