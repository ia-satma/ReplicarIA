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

| Endpoint | Descripción |
|----------|-------------|
| `GET /api/agents/available` | Lista todos los agentes con metadata |
| `GET /api/agents/registry` | Registry completo con stats y aliases |
| `GET /api/agents/by-phase/{phase}` | Agentes activos en una fase |
| `GET /api/agents/hierarchy` | Árbol de agentes con subagentes |
| `GET /api/agents/stats` | Estadísticas de deliberaciones |
| `POST /api/agents/chat` | Chat con agentes |
| `POST /api/agents/invoke` | Invocar agente específico |

---

## Archivos del Sistema

| Archivo | Descripción |
|---------|-------------|
| `backend/config/agents_registry.py` | **FUENTE ÚNICA DE VERDAD** |
| `frontend/src/components/agents/AgentsDashboard.jsx` | Dashboard con agentMap sincronizado |
| `frontend/src/components/agents/AgentPanel.jsx` | Panel de selección de agentes |
| `backend/routes/agents_stats_routes.py` | Endpoints de API |

---

## Cómo Agregar un Nuevo Agente

1. Agregar en `backend/config/agents_registry.py` → `AGENTS_REGISTRY`
2. Si es subagente, especificar `parent_agent`
3. Definir `phases` donde participa
4. Si puede bloquear, definir `can_block=True` y `blocking_phases`
5. Los componentes frontend se actualizan automáticamente via API

---

*Última actualización: 2026-02-02*
