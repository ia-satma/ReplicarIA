# Sistema de Agentes - ReplicarIA

> **Fuente Única de Verdad**: `backend/config/agents_registry.py`

Este documento describe la arquitectura completa del sistema multi-agente de ReplicarIA.

## Resumen

| Tipo | Cantidad | Descripción |
|------|----------|-------------|
| **Principales** | 7 | Agentes del flujo F0-F9, pueden bloquear fases |
| **Especializados** | 3 | Funciones transversales (auditoría, knowledge, control) |
| **Subagentes** | 8 | Apoyan a agentes principales (3 fiscales, 5 PMO) |
| **Total** | **18** | Agentes activos en el sistema |

---

## Agentes Principales (7)

Estos agentes participan directamente en el flujo de validación F0-F9.

### A1_SPONSOR - María Rodríguez
| Campo | Valor |
|-------|-------|
| **Rol** | Sponsor / Evaluador Estratégico |
| **Departamento** | Dirección Estratégica |
| **Descripción** | Evalúa razón de negocios y beneficio económico esperado (BEE) |
| **Icono** | 🎯 |
| **Color** | indigo |
| **Fases** | F0, F4, F5, F9 |
| **Puede Bloquear** | Sí (F0) |
| **Modelo LLM** | claude-sonnet |
| **pCloud** | A1_ESTRATEGIA |

### A2_PMO - Carlos Mendoza
| Campo | Valor |
|-------|-------|
| **Rol** | Orquestador del Proceso F0-F9 |
| **Departamento** | PMO |
| **Descripción** | Controla flujo de fases, verifica checklists y candados |
| **Icono** | 📋 |
| **Color** | blue |
| **Fases** | F0-F9 (todas) |
| **Puede Bloquear** | Sí (F2, F6, F8) |
| **Modelo LLM** | claude-sonnet |
| **pCloud** | A2_PMO |
| **Subagentes** | S_ANALIZADOR, S_CLASIFICADOR, S_RESUMIDOR, S_VERIFICADOR, S_REDACTOR |

### A3_FISCAL - Laura Sánchez
| Campo | Valor |
|-------|-------|
| **Rol** | Especialista en Cumplimiento Fiscal |
| **Departamento** | Fiscal |
| **Descripción** | Evalúa 4 pilares fiscales y emite VBC Fiscal (CFF, LISR, LIVA) |
| **Icono** | ⚖️ |
| **Color** | purple |
| **Fases** | F0, F1, F4, F6 |
| **Puede Bloquear** | Sí (F0, F6) |
| **Modelo LLM** | claude-sonnet |
| **pCloud** | A3_FISCAL |
| **Subagentes** | S1_TIPIFICACION, S2_MATERIALIDAD, S3_RIESGOS |

### A4_LEGAL - Ana García
| Campo | Valor |
|-------|-------|
| **Rol** | Especialista en Contratos y Trazabilidad |
| **Departamento** | Legal |
| **Descripción** | Revisa contratos, SOW y emite VBC Legal |
| **Icono** | 📜 |
| **Color** | red |
| **Fases** | F1, F6 |
| **Puede Bloquear** | Sí (F1, F6) |
| **Modelo LLM** | claude-sonnet |
| **pCloud** | A4_LEGAL |

### A5_FINANZAS - Roberto Sánchez
| Campo | Valor |
|-------|-------|
| **Rol** | Director Financiero / Controller |
| **Departamento** | Finanzas |
| **Descripción** | Evalúa proporción económica, presupuesto y 3-way match |
| **Icono** | 💰 |
| **Color** | emerald |
| **Fases** | F2, F4, F8 |
| **Puede Bloquear** | Sí (F2, F8) |
| **Modelo LLM** | claude-sonnet |
| **pCloud** | A5_FINANZAS |

### A6_PROVEEDOR - Agente Due Diligence
| Campo | Valor |
|-------|-------|
| **Rol** | Validador de Proveedores |
| **Departamento** | Validación de Proveedores |
| **Descripción** | Gestiona entregables y evidencias de ejecución del proveedor |
| **Icono** | 🔍 |
| **Color** | yellow |
| **Fases** | F3, F4, F5 |
| **Puede Bloquear** | No |
| **Modelo LLM** | claude-sonnet |
| **pCloud** | A6_PROVEEDOR |

### A7_DEFENSA - Laura Vázquez
| Campo | Valor |
|-------|-------|
| **Rol** | Directora de Defense File |
| **Departamento** | Defensa Fiscal |
| **Descripción** | Consolida expediente de defensa y evalúa defendibilidad |
| **Icono** | 🛡️ |
| **Color** | orange |
| **Fases** | F6, F7, F9 |
| **Puede Bloquear** | No |
| **Modelo LLM** | claude-sonnet |
| **pCloud** | A7_DEFENSA |

---

## Agentes Especializados (3)

Agentes con funciones transversales que no participan directamente en el flujo F0-F9.

### A8_AUDITOR - Diego Ramírez
| Campo | Valor |
|-------|-------|
| **Rol** | Auditor Documental |
| **Departamento** | Auditoría Documental |
| **Descripción** | Verifica estructura y completitud de documentos |
| **Icono** | 📊 |
| **Color** | cyan |
| **Fases** | F4, F6, F8 |
| **Modelo LLM** | claude-sonnet |
| **pCloud** | A8_AUDITOR |

### KB_CURATOR - Dra. Elena Vázquez
| Campo | Valor |
|-------|-------|
| **Rol** | Curadora de Conocimiento |
| **Departamento** | Gestión del Conocimiento |
| **Descripción** | Fuente normativa RAG para todos los agentes |
| **Icono** | 📚 |
| **Color** | violet |
| **Fases** | Siempre disponible |
| **Modelo LLM** | claude-sonnet |
| **pCloud** | KNOWLEDGE_BASE |

### DEVILS_ADVOCATE - Abogado del Diablo
| Campo | Valor |
|-------|-------|
| **Rol** | Control Interno y Aprendizaje |
| **Departamento** | Control Interno |
| **Descripción** | Cuestiona sistemáticamente, detecta patrones de riesgo |
| **Icono** | 😈 |
| **Color** | gray |
| **Fases** | Solo admin |
| **Modelo LLM** | claude-sonnet |

---

## Subagentes (8)

### Subagentes Fiscales (reportan a A3_FISCAL)

| ID | Nombre | Rol | Icono | Fases |
|----|--------|-----|-------|-------|
| S1_TIPIFICACION | Patricia López | Clasificador de Tipología | 🏷️ | F0 |
| S2_MATERIALIDAD | Fernando Ruiz | Especialista en Materialidad (Art. 69-B CFF) | 📎 | F5, F6 |
| S3_RIESGOS | Gabriela Vega | Detector de Riesgos (EFOS, precios de transferencia) | ⚠️ | F0, F2, F6 |

### Subagentes PMO (reportan a A2_PMO)

| ID | Nombre | Rol | Icono |
|----|--------|-----|-------|
| S_ANALIZADOR | Subagente Analizador | Extrae y analiza datos de documentos | 🔬 |
| S_CLASIFICADOR | Subagente Clasificador | Clasifica issues por severidad y tipo | 📁 |
| S_RESUMIDOR | Subagente Resumidor | Genera resúmenes ejecutivos | 📝 |
| S_VERIFICADOR | Subagente Verificador | Verifica completitud y calidad de outputs | ✅ |
| S_REDACTOR | Subagente Redactor | Genera documentos formales y comunicaciones | ✍️ |

---

## Flujo de Deliberación

```
Proyecto → A1_SPONSOR (F0) → A3_FISCAL (F0) → A5_FINANZAS (F2) → A4_LEGAL (F1)
                ↓                  ↓                  ↓               ↓
           [RECHAZAR]         [RECHAZAR]         [RECHAZAR]      [RECHAZAR]
                ↓                  ↓                  ↓               ↓
           EXIT EARLY         EXIT EARLY         EXIT EARLY      EXIT EARLY
                                                                     ↓
                                                            [APROBADO] → A7_DEFENSA
```

### Pipeline de Deliberación
1. **A1_SPONSOR** evalúa razón de negocios
2. Si RECHAZA → termina temprano
3. **A3_FISCAL** evalúa cumplimiento fiscal
4. Si RECHAZA → termina temprano
5. **A5_FINANZAS** evalúa proporción económica
6. Si RECHAZA → termina temprano
7. **A4_LEGAL** evalúa contratos
8. Si RECHAZA → termina temprano
9. **A7_DEFENSA** consolida defense file

---

## Agentes que Pueden Bloquear

| Agente | Fases Bloqueables |
|--------|-------------------|
| A1_SPONSOR | F0 |
| A2_PMO | F2, F6, F8 |
| A3_FISCAL | F0, F6 |
| A4_LEGAL | F1, F6 |
| A5_FINANZAS | F2, F8 |

---

## Aliases de Compatibilidad

Para mantener compatibilidad con código legacy, se definen los siguientes aliases:

```python
AGENT_ID_ALIASES = {
    "A1_ESTRATEGIA": "A1_SPONSOR",
    "A1_RECEPCION": "A1_SPONSOR",
    "A2_ANALISIS": "A3_FISCAL",
    "A3_NORMATIVO": "A3_FISCAL",
    "A4_CONTABLE": "A5_FINANZAS",
    "A5_OPERATIVO": "A6_PROVEEDOR",
    "A6_FINANCIERO": "A5_FINANZAS",
    "A7_LEGAL": "A4_LEGAL",
    "A8_REDTEAM": "DEVILS_ADVOCATE",
    "A9_SINTESIS": "A7_DEFENSA",
    "A10_ARCHIVO": "KB_CURATOR",
    "LEGAL": "A4_LEGAL",
}
```

---

## API Endpoints

### Agentes
| Endpoint | Descripción |
|----------|-------------|
| `GET /api/agents/available` | Lista todos los agentes con metadata |
| `GET /api/agents/registry` | Registry completo con stats y aliases |
| `GET /api/agents/by-phase/{phase}` | Agentes activos en una fase |
| `GET /api/agents/hierarchy` | Árbol de agentes con subagentes |
| `GET /api/agents/stats` | Estadísticas de deliberaciones |
| `POST /api/agents/chat` | Chat con agentes |
| `POST /api/agents/invoke` | Invocar agente específico |

### pCloud y Onboarding Automático
| Endpoint | Descripción |
|----------|-------------|
| `POST /pcloud/setup-complete` | Setup inicial de todas las carpetas |
| `GET /pcloud/folders` | Lista carpetas de agentes en pCloud |
| `POST /pcloud/sync/{agent_id}` | Sincroniza documentos de un agente a RAG |
| `POST /pcloud/sync-all` | Sincroniza todos los agentes |
| **Onboarding** | |
| `POST /pcloud/onboarding/setup` | Crea carpetas CLIENTES_NUEVOS y CLIENTES |
| `GET /pcloud/onboarding/scan` | Escanea empresas pendientes de procesar |
| `POST /pcloud/onboarding/process/{folder_id}` | Procesa una carpeta de cliente |
| `POST /pcloud/onboarding/process-all` | Procesa TODAS las empresas pendientes |
| `GET /pcloud/onboarding/watcher/status` | Estado del watcher automático |
| `POST /pcloud/onboarding/watcher/start` | Inicia monitoreo automático |
| `POST /pcloud/onboarding/watcher/stop` | Detiene monitoreo automático |

---

## Archivos del Sistema

| Archivo | Descripción |
|---------|-------------|
| `backend/config/agents_registry.py` | **FUENTE ÚNICA DE VERDAD** |
| `backend/services/pcloud_service.py` | Integración con pCloud |
| `backend/services/pcloud_onboarding_service.py` | Onboarding automático de empresas |
| `backend/services/rag_service.py` | Colecciones RAG por agente |
| `backend/routes/pcloud_routes.py` | Endpoints de pCloud y onboarding |
| `backend/routes/agents_stats_routes.py` | Endpoints de agentes |
| `frontend/src/components/agents/AgentsDashboard.jsx` | Dashboard con agentMap sincronizado |
| `frontend/src/components/agents/AgentPanel.jsx` | Panel de selección de agentes |

---

## Estructura de pCloud

Cada agente tiene su propia carpeta en pCloud para almacenar conocimiento especializado.

### Carpetas Principales
```
REVISAR.IA (ID: 29789401752)
├── A1_ESTRATEGIA/     # A1_SPONSOR - Estrategia y BEE
├── A2_PMO/            # A2_PMO - Orquestación y flujos
├── A3_FISCAL/         # A3_FISCAL - CFF, LISR, LIVA
├── A4_LEGAL/          # A4_LEGAL - Contratos y SOW
├── A5_FINANZAS/       # A5_FINANZAS - 3-way match
├── A6_PROVEEDOR/      # A6_PROVEEDOR - Due diligence
├── A7_DEFENSA/        # A7_DEFENSA - Defense files
├── A8_AUDITOR/        # A8_AUDITOR - Auditoría
├── KNOWLEDGE_BASE/    # KB_CURATOR - Base normativa
├── DEFENSE_FILES/     # Expedientes de defensa
├── PROYECTOS/         # Archivos de proyectos
├── SUB_TIPIFICACION/  # S1 - Tipología de servicios
├── SUB_MATERIALIDAD/  # S2 - Evidencias Art. 69-B
├── SUB_RIESGOS/       # S3 - EFOS y riesgos
├── SUB_ANALIZADOR/    # S_ANALIZADOR - Análisis datos
├── SUB_CLASIFICADOR/  # S_CLASIFICADOR - Clasificación
├── SUB_RESUMIDOR/     # S_RESUMIDOR - Resúmenes
├── SUB_VERIFICADOR/   # S_VERIFICADOR - QA
├── CLIENTES_NUEVOS/   # 🆕 Onboarding automático - carpetas nuevas
│   └── {RFC_O_NOMBRE}/
│       ├── _info.json       # Opcional: datos de la empresa
│       ├── acta_constitutiva.pdf
│       └── ...
├── CLIENTES/          # 🆕 Empresas ya procesadas (se mueven aquí)
└── SUB_REDACTOR/      # S_REDACTOR - Documentos
```

### Capacidades por Agente

| Agente | Carpeta pCloud | Colección RAG | Puede Crear Agentes | Puede Ingestar |
|--------|----------------|---------------|---------------------|----------------|
| A1_SPONSOR | A1_ESTRATEGIA | estrategia_knowledge | ❌ | ✅ |
| A2_PMO | A2_PMO | pmo_knowledge | ✅ (subagentes) | ✅ |
| A3_FISCAL | A3_FISCAL | fiscal_knowledge | ✅ (subagentes) | ✅ |
| A4_LEGAL | A4_LEGAL | legal_knowledge | ❌ | ✅ |
| A5_FINANZAS | A5_FINANZAS | finanzas_knowledge | ❌ | ✅ |
| A6_PROVEEDOR | A6_PROVEEDOR | proveedor_knowledge | ❌ | ✅ |
| A7_DEFENSA | A7_DEFENSA | defensa_knowledge | ❌ | ✅ |
| A8_AUDITOR | A8_AUDITOR | auditor_knowledge | ❌ | ✅ |
| KB_CURATOR | KNOWLEDGE_BASE | knowledge_base | ❌ | ✅ (admin) |
| DEVILS_ADVOCATE | - | control_knowledge | ❌ | ❌ |

### Subagentes con Carpeta Propia

| Subagente | Carpeta pCloud | Colección RAG (heredada) |
|-----------|----------------|--------------------------|
| S1_TIPIFICACION | SUB_TIPIFICACION | fiscal_knowledge |
| S2_MATERIALIDAD | SUB_MATERIALIDAD | fiscal_knowledge |
| S3_RIESGOS | SUB_RIESGOS | fiscal_knowledge |
| S_ANALIZADOR | SUB_ANALIZADOR | pmo_knowledge |
| S_CLASIFICADOR | SUB_CLASIFICADOR | pmo_knowledge |
| S_RESUMIDOR | SUB_RESUMIDOR | pmo_knowledge |
| S_VERIFICADOR | SUB_VERIFICADOR | pmo_knowledge |
| S_REDACTOR | SUB_REDACTOR | pmo_knowledge |

---

## Flujo de Conocimiento (RAG)

```
pCloud Folder         →  IngestionService  →  ChromaDB Collection
     ↓                         ↓                      ↓
[Documentos PDF/DOCX]   [Extrae texto]        [Embeddings]
     ↓                         ↓                      ↓
                        [Chunking]             [Query por agente]
                               ↓                      ↓
                        [PostgreSQL]           [Contexto para LLM]
```

### Sincronización Automática
```bash
POST /pcloud/sync/{agent_id}   # Sincroniza un agente
POST /pcloud/sync-all          # Sincroniza todos
POST /pcloud/setup-complete    # Setup inicial completo
```

---

## Onboarding Automático de Empresas

El sistema puede detectar y procesar automáticamente nuevas empresas desde pCloud.

### Flujo de Onboarding
```
pCloud: CLIENTES_NUEVOS/{carpeta}  →  Sistema detecta  →  Procesa documentos
              ↓                            ↓                     ↓
        [_info.json]                  [Lee RFC/datos]      [Crea empresa]
        [documentos]                  [Analiza PDFs]       [Ingesta en RAG]
              ↓                            ↓                     ↓
                                    Mueve a CLIENTES/    ✅ Empresa lista
```

### Estructura de Carpeta para Nueva Empresa
```
CLIENTES_NUEVOS/
└── ABC123456XYZ/              # Nombre = RFC o nombre de empresa
    ├── _info.json             # Opcional - datos manuales
    ├── acta_constitutiva.pdf
    ├── cedula_fiscal.pdf
    └── otros_documentos.pdf
```

### Formato de _info.json (Opcional)
```json
{
  "nombre_comercial": "Mi Empresa SA",
  "razon_social": "Mi Empresa SA de CV",
  "rfc": "ABC123456XYZ",
  "industria": "SERVICIOS_PROFESIONALES",
  "email": "contacto@miempresa.com",
  "telefono": "5555555555",
  "direccion": "Av. Principal 123, CDMX"
}
```

### Opciones de Procesamiento
1. **Manual**: `POST /pcloud/onboarding/process-all` - Procesa todo lo pendiente
2. **Individual**: `POST /pcloud/onboarding/process/{folder_id}` - Una empresa
3. **Automático**: Activar watcher con `POST /pcloud/onboarding/watcher/start`

### Watcher Automático
El watcher monitorea `CLIENTES_NUEVOS/` cada 5 minutos (configurable):
```bash
# Iniciar watcher (intervalo en segundos, mínimo 60)
POST /pcloud/onboarding/watcher/start?interval_seconds=300

# Ver estado
GET /pcloud/onboarding/watcher/status

# Detener
POST /pcloud/onboarding/watcher/stop
```

---

## Cómo Agregar un Nuevo Agente

1. Agregar en `backend/config/agents_registry.py` → `AGENTS_REGISTRY`
2. Si es subagente, especificar `parent_agent`
3. Definir `phases` donde participa
4. Si puede bloquear, definir `can_block=True` y `blocking_phases`
5. Asignar `pcloud_folder` si necesita conocimiento propio
6. Agregar folder en `pcloud_service.py` → `REQUIRED_SUBFOLDERS`
7. Agregar colección en `rag_service.py` → `AGENT_COLLECTIONS`
8. Los componentes frontend se actualizan automáticamente via API

---

## Archivos Sincronizados

| Archivo | Sincronizar Con |
|---------|-----------------|
| `backend/config/agents_registry.py` | **FUENTE ÚNICA** |
| `backend/services/pcloud_service.py` | `REQUIRED_SUBFOLDERS`, `AGENT_FOLDER_IDS` |
| `backend/services/rag_service.py` | `AGENT_COLLECTIONS` |
| `frontend/src/components/agents/AgentsDashboard.jsx` | `agentMap` |
| `frontend/src/components/agents/AgentPanel.jsx` | `AGENTS` array |

---

*Última actualización: 2026-02-02*
