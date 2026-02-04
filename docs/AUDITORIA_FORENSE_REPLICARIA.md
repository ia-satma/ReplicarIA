# 🔬 AUDITORÍA FORENSE - ReplicarIA

## Resumen Ejecutivo

**Diagnóstico:** El proyecto tiene una arquitectura monolítica con **130+ servicios** y **70+ rutas** que crean múltiples puntos de falla. La alta interdependencia entre servicios causa efecto dominó cuando algo falla.

**Recomendación:** Migración gradual a arquitectura de **Cloudflare Workers** donde cada agente/función es independiente.

---

## 📊 INVENTARIO DEL SISTEMA

### Servicios (130+ archivos)

| Categoría | Cantidad | Tamaño Total | Complejidad |
|-----------|----------|--------------|-------------|
| Agentes (a*_service) | 8 | ~80KB | ALTA |
| Deliberación | 3 | ~200KB | MUY ALTA |
| Defense File | 5 | ~150KB | ALTA |
| Knowledge Base | 6 | ~100KB | ALTA |
| Autenticación | 4 | ~80KB | MEDIA |
| Email | 3 | ~60KB | MEDIA |
| pCloud | 2 | ~95KB | ALTA |
| Workflow | 3 | ~100KB | MUY ALTA |
| Database | 4 | ~70KB | MEDIA |
| Otros | 90+ | ~500KB | VARIABLE |

### Rutas/Endpoints (70+ archivos)

| Archivo | Tamaño | Endpoints Estimados |
|---------|--------|---------------------|
| biblioteca_routes.py | 61KB | ~50+ |
| archivo_routes.py | 52KB | ~40+ |
| unified_auth_routes.py | 48KB | ~30+ |
| onboarding_routes.py | 45KB | ~25+ |
| kb_routes.py | 42KB | ~35+ |
| devils_advocate_routes.py | 40KB | ~20+ |
| projects.py | 39KB | ~30+ |
| Otros 63 archivos | ~300KB | ~200+ |

**Total estimado: 400+ endpoints**

---

## 🔴 PUNTOS CRÍTICOS DE FALLA

### 1. Deliberation Orchestrator (93KB)
```
Ubicación: services/deliberation_orchestrator.py
Dependencias:
├── dreamhost_email_service
├── rag_service
├── defense_file_service
├── agentic_reasoning_service
├── report_generator
├── evidence_portfolio_service
├── event_emitter
├── auditor_service
├── AGENT_CONFIGURATIONS
├── inyeccion_contexto_service
├── reglas_tipologia
├── validation_service
├── deliberation_state_repository
└── cliente_contexto_service

Riesgo: MUY ALTO - Si falla, TODO el flujo F0-F9 se detiene
```

### 2. Legal Validation Service (83KB)
```
Ubicación: services/legal_validation_service.py
Función: Validación de cumplimiento LISR/CFF
Riesgo: ALTO - Bloquea validaciones fiscales
```

### 3. pCloud Service (71KB)
```
Ubicación: services/pcloud_service.py
Función: Almacenamiento de documentos
Dependencia externa: API de pCloud
Riesgo: ALTO - Sin acceso a documentos, nada funciona
```

### 4. Devils Advocate Service (71KB)
```
Ubicación: services/devils_advocate_service.py
Función: Cuestionamiento de dictámenes
Riesgo: MEDIO - Funcionalidad opcional pero compleja
```

### 5. Agent Service (52KB)
```
Ubicación: services/agent_service.py
Función: Lógica central de agentes
Riesgo: MUY ALTO - Todos los agentes dependen de esto
```

### 6. Workflow Orchestrator (43KB)
```
Ubicación: services/workflow_orchestrator.py
Función: Gestión de flujos F0-F9
Riesgo: ALTO - Controla transiciones de fase
```

### 7. Email Service (38KB)
```
Ubicación: services/dreamhost_email_service.py
Dependencia: Dreamhost SMTP
Riesgo: ALTO - Comunicación con usuarios falla
```

---

## 🔗 DEPENDENCIAS EXTERNAS

| Servicio | Dependencia | Riesgo si Falla |
|----------|-------------|-----------------|
| Base de datos | PostgreSQL | TODO se detiene |
| Almacenamiento | pCloud API | Sin documentos |
| IA Principal | Anthropic/OpenAI | Agentes no funcionan |
| Email | Dreamhost SMTP | Sin notificaciones |
| RAG/Embeddings | ChromaDB/OpenAI | Sin búsqueda semántica |
| Validación SAT | SOAP SAT | Sin validación CFDI |

---

## 📦 MODELO DE DATOS

### Entidades Principales

```
Empresa (empresa.py)
├── id, nombre, rfc, giro
├── regimen_fiscal, domicilio
└── configuracion_agentes

Proyecto/ProyectoSIB (proyecto_sib.py)
├── id, empresa_id, proveedor_id
├── tipologia, monto, descripcion
├── fase_actual (F0-F9)
├── dictamenes[]
└── documentos[]

Proveedor (proveedor.py) - 22KB, MUY COMPLEJO
├── datos_basicos (RFC, razón social, etc.)
├── datos_fiscales (régimen, actividades)
├── due_diligence (scoring, riesgos)
├── documentos[]
└── histórico_transacciones[]

DefenseFile (defense_file.py)
├── proyecto_id
├── secciones (13 secciones documentadas)
├── evidencias[]
├── dictamenes_agentes[]
└── estado_consolidación
```

---

## 🔄 FLUJO DE DATOS CRÍTICO

```
ENTRADA (Frontend/API)
        │
        ▼
┌───────────────────┐
│    server.py      │ ◄── 70+ rutas, 50+ try/except
│   (1559 líneas)   │
└────────┬──────────┘
         │
         ▼
┌───────────────────────────────────────────────────────────────┐
│                  SERVICIOS CRÍTICOS                            │
│                                                                │
│  deliberation_orchestrator ◄──► agent_service                 │
│           │                           │                        │
│           ▼                           ▼                        │
│  workflow_orchestrator ◄────► legal_validation_service        │
│           │                           │                        │
│           ▼                           ▼                        │
│  defense_file_service ◄─────► pcloud_service                  │
│           │                           │                        │
│           ▼                           ▼                        │
│  email_service ◄────────────► rag_service                     │
│                                                                │
└───────────────────────────────────────────────────────────────┘
         │
         ▼
┌───────────────────────────────────────────────────────────────┐
│                  BASES DE DATOS                                │
│                                                                │
│  PostgreSQL ◄──► database_pg.py                               │
│  ChromaDB   ◄──► rag_service.py                               │
│  pCloud     ◄──► pcloud_service.py (archivos)                 │
│                                                                │
└───────────────────────────────────────────────────────────────┘
```

---

## ⚡ ANÁLISIS DE FRAGILIDAD

### server.py tiene 50+ bloques try/except para importar rutas

Esto indica:
1. **Alta probabilidad de fallas en imports**
2. **Dependencias circulares** posibles
3. **Modo degradado** es común

### Servicios con más de 10 imports internos

| Servicio | Imports Internos | Riesgo |
|----------|------------------|--------|
| deliberation_orchestrator | 15+ | CRÍTICO |
| agent_service | 12+ | ALTO |
| workflow_orchestrator | 10+ | ALTO |
| legal_validation_service | 10+ | ALTO |

---

## 🔧 PLAN DE MIGRACIÓN A WORKERS

### Fase 1: Workers Independientes (Reemplazar servicios simples)

| Worker | Reemplaza | Complejidad | Tiempo Est. |
|--------|-----------|-------------|-------------|
| ✅ oraculo-estrategico | deep_research_service + a6_scoring | ALTA | HECHO |
| s-redactor | email_service + notificaciones | MEDIA | 2-3 horas |
| s-analizador | document_analyzer + OCR | MEDIA | 2-3 horas |
| a3-fiscal | a3_fiscal_service + verificacion_69b | ALTA | 4-6 horas |

### Fase 2: Workers Coordinados (Reemplazar orquestadores)

| Worker | Reemplaza | Complejidad | Tiempo Est. |
|--------|-----------|-------------|-------------|
| a2-pmo | workflow_orchestrator + fase_service | MUY ALTA | 8-12 horas |
| workers-hub | deliberation_orchestrator | MUY ALTA | 6-8 horas |

### Fase 3: Workers de Almacenamiento (Reemplazar backends)

| Worker | Reemplaza | Complejidad | Tiempo Est. |
|--------|-----------|-------------|-------------|
| svc-database | database_pg + database | ALTA | 8-12 horas |
| svc-storage | pcloud_service | MEDIA | 4-6 horas |
| svc-auth | unified_auth_service | ALTA | 6-8 horas |

---

## 🎯 PRIORIDAD DE MIGRACIÓN

### URGENTE (Esta semana)

1. **S_REDACTOR** - Emails están fallando
2. **S_ALERTAS** - Notificaciones críticas
3. **A3_FISCAL** - Validación fiscal bloqueada

### IMPORTANTE (Próximas 2 semanas)

4. **S_ANALIZADOR** - OCR/Análisis de documentos
5. **A2_PMO** - Coordinación de flujos
6. **S2_MATERIALIDAD** - Documentación SAT

### DESPUÉS

7. Resto de agentes
8. Servicios de infraestructura

---

## 📋 CHECKLIST DE MIGRACIÓN POR WORKER

Para cada Worker:

- [ ] Identificar servicio(s) a reemplazar
- [ ] Extraer lógica core sin dependencias
- [ ] Crear Worker con endpoints equivalentes
- [ ] Probar en aislamiento
- [ ] Crear wrapper en backend (para compatibilidad)
- [ ] Migrar llamadas gradualmente
- [ ] Monitorear errores
- [ ] Deprecar servicio original

---

## 💡 VENTAJAS DE LA MIGRACIÓN

| Aspecto | Actual (Monolito) | Después (Workers) |
|---------|-------------------|-------------------|
| Tolerancia a fallos | Si algo falla, todo falla | Falla aislada |
| Escalabilidad | Escalar todo o nada | Escalar por función |
| Despliegue | Redesplegar TODO | Desplegar solo el Worker |
| Debugging | Logs mezclados | Logs por Worker |
| Costos | Servidor siempre encendido | Pago por uso |
| Latencia | Variable (servidor cargado) | Consistente (edge) |

---

## ⚠️ RIESGOS DE LA MIGRACIÓN

1. **Consistencia de datos** - Asegurar transacciones entre Workers
2. **Latencia de red** - Más llamadas HTTP entre servicios
3. **Debugging distribuido** - Trazar errores es más difícil
4. **Curva de aprendizaje** - Nuevo paradigma de desarrollo

---

## 📅 TIMELINE PROPUESTO

```
SEMANA 1: Fundamentos
├── Día 1-2: Crear Workers críticos (S_REDACTOR, S_ALERTAS)
├── Día 3-4: Crear A3_FISCAL Worker
└── Día 5: Testing y ajustes

SEMANA 2: Orquestación
├── Día 1-3: Crear A2_PMO Worker
├── Día 4-5: Integrar con Hub
└── Testing de flujos básicos

SEMANA 3: Almacenamiento
├── Día 1-3: Crear SVC_DATABASE (D1)
├── Día 4-5: Crear SVC_STORAGE (R2)
└── Migrar datos

SEMANA 4: Resto de agentes
├── A1, A4, A5, A7, A8
├── Subagentes restantes
└── Testing completo

SEMANA 5: Deprecación
├── Desactivar servicios viejos
├── Monitoreo intensivo
└── Documentación final
```

---

## CONCLUSIÓN

La plataforma actual es **insostenible** por su complejidad y acoplamiento. La migración a Workers es **necesaria** para:

1. Estabilizar el sistema
2. Facilitar mantenimiento
3. Escalar según demanda
4. Reducir costos operativos

Cada Worker que migremos es un **punto menos de falla** en el sistema.
