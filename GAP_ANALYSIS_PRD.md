# GAP Analysis: PRD revisar.ia vs ReplicarIA

**Fecha:** 30 Enero 2026
**Objetivo:** Alinear desarrollo actual con visión del PRD

---

## 1. COMPARATIVA PUNTO POR PUNTO

### 1.1 Problem Statement (PRD)

| Requerimiento PRD | Estado Actual | Gap |
|-------------------|---------------|-----|
| Revisión manual es lenta y cara | Sistema automatizado con 11 agentes | Orientado a fiscal, no contratos |
| Aplicación inconsistente de reglas | 4 pilares de cumplimiento definidos | Solo reglas fiscales mexicanas |
| Riesgo de omitir issues críticos | Sistema de scoring 0-100 | No analiza cláusulas contractuales |
| Dificultad manteniendo estándares | Checklists por tipología | No hay reglas de contratos |

**Diagnóstico:** El sistema resuelve el problema pero para **auditorías fiscales SAT**, no para **revisión de contratos genéricos**.

---

### 1.2 Usuarios Target (PRD)

| Usuario PRD | Usuario Actual ReplicarIA | Alineación |
|-------------|---------------------------|------------|
| Abogados | No contemplado directamente | Agregar rol |
| Contadores | Equipo de Cumplimiento | Parcial |
| Consultores | Sponsors/Ejecutivos | Parcial |
| Revisores de contratos | No existe | Crear rol |

**Gap:** Faltan perfiles específicos de usuarios legales.

---

### 1.3 Functional Requirements MVP

| ID | Requerimiento PRD | Estado | Implementación Actual |
|----|-------------------|--------|----------------------|
| FR-1 | Upload documento (PDF, DOCX, TXT) | Parcial | Soporta PDF, DOCX, TXT + más |
| FR-2 | Extraer y procesar contenido | Parcial | OCR con Tesseract, Vision API |
| FR-3 | Analizar contra reglas compliance | NO | Solo 4 pilares fiscales |
| FR-4 | Mostrar issues con highlighting | NO | No hay highlighting en documento |
| FR-5 | Sugerencias con lenguaje alternativo | NO | Solo "aprobar/ajustar/rechazar" |
| FR-6 | Exportar documento anotado | NO | Solo reportes PDF separados |

**Crítico:** Los requerimientos 3, 4, 5 y 6 NO están implementados.

---

### 1.4 Non-Functional Requirements

| Requerimiento | Especificación PRD | Estado Actual |
|---------------|-------------------|---------------|
| Performance | < 2 minutos para 50 páginas | No medido, probablemente más lento |
| Seguridad | Sin almacenamiento post-sesión | Almacena en MongoDB + pCloud |
| Usabilidad | Sin entrenamiento requerido | Requiere onboarding empresa |

**Gap:** El modelo actual es enterprise (persistente), el PRD pide SaaS simple (efímero).

---

### 1.5 Scope - In Scope MVP

| Feature PRD | Estado | Notas |
|-------------|--------|-------|
| Single document upload | SI | Funciona |
| Pre-built contract compliance rules | NO | No existen reglas de contratos |
| AI-generated suggestions | PARCIAL | Genera deliberaciones, no sugerencias inline |
| Issue highlighting | NO | No implementado |
| Web-based interface | SI | React + Tailwind |

---

### 1.6 Scope - Out of Scope (Futuro)

| Feature Futuro | Estado Actual |
|----------------|---------------|
| Batch processing | NO |
| User accounts & history | SI (ya existe) |
| Team collaboration | PARCIAL |
| API third-party | NO |
| Industry-specific modules | SI (solo fiscal MX) |

**Oportunidad:** Ya tenemos cuentas de usuario y colaboración parcial.

---

### 1.7 User Flow MVP (PRD)

```
PRD Flow:
1. Upload documento        → EXISTE
2. Extraer contenido       → EXISTE (parcial)
3. Analizar vs reglas      → NO EXISTE
4. Mostrar issues          → NO EXISTE (no inline)
5. Aceptar/rechazar        → NO EXISTE
6. Exportar anotado        → NO EXISTE
```

```
Flow Actual ReplicarIA:
1. Onboarding empresa      → EXTRA (no en PRD)
2. Crear proyecto          → DIFERENTE
3. Subir múltiples docs    → DIFERENTE
4. Deliberación 11 agentes → DIFERENTE
5. Ver scoring             → DIFERENTE
6. Generar Defense File    → DIFERENTE
```

**Gap Crítico:** Los flujos son completamente diferentes.

---

## 2. DECISIÓN ESTRATÉGICA REQUERIDA

### Opción A: Pivotar ReplicarIA hacia PRD
- Simplificar el sistema actual
- Eliminar complejidad de 11 agentes
- Enfocar en revisión de contratos
- **Riesgo:** Perder funcionalidad fiscal valiosa

### Opción B: Crear Módulo Nuevo "Revisar Contratos"
- Mantener sistema fiscal actual
- Agregar nuevo módulo de contratos
- Reutilizar infraestructura
- **Riesgo:** Complejidad aumentada

### Opción C: Dos Productos Separados
- **ReplicarIA/Durezza:** Sistema fiscal SAT (actual)
- **revisar.ia:** SaaS simple de contratos (nuevo)
- **Riesgo:** Duplicar esfuerzo de mantenimiento

**Recomendación:** Opción B - Agregar módulo de contratos reutilizando infraestructura.

---

## 3. PLAN DE TRABAJO - OPCIÓN B

### FASE 1: Foundation (Semana 1-2)

#### 1.1 Backend: Motor de Reglas de Contratos
```
/backend/services/contract_review/
├── __init__.py
├── document_extractor.py      # Extraer texto estructurado
├── clause_detector.py         # Identificar cláusulas
├── compliance_rules.py        # Reglas pre-definidas
├── contract_analyzer.py       # Análisis con LLM
└── suggestion_generator.py    # Generar sugerencias
```

**Tareas:**
- [ ] Crear servicio de extracción de texto (PDF/DOCX)
- [ ] Crear detector de cláusulas con GPT-4o
- [ ] Definir 20 reglas iniciales de compliance
- [ ] Crear analizador que compare vs reglas

#### 1.2 Backend: Nuevos Endpoints
```python
# /backend/routes/contract_review.py

POST /api/contracts/upload      # Subir contrato
POST /api/contracts/analyze     # Analizar contrato
GET  /api/contracts/{id}/issues # Ver issues encontrados
POST /api/contracts/{id}/accept # Aceptar sugerencia
GET  /api/contracts/{id}/export # Exportar anotado
```

**Tareas:**
- [ ] Crear router contract_review.py
- [ ] Implementar endpoint de upload
- [ ] Implementar endpoint de análisis
- [ ] Implementar endpoint de issues

---

### FASE 2: Frontend MVP (Semana 3-4)

#### 2.1 Nueva Página de Revisión
```
/frontend/src/pages/
└── ContractReviewPage.jsx

/frontend/src/components/contract-review/
├── DocumentUploader.jsx       # Upload con drag & drop
├── AnalysisProgress.jsx       # Barra de progreso
├── IssuesList.jsx             # Lista de issues
├── IssueCard.jsx              # Card individual
├── SuggestionModal.jsx        # Modal con sugerencia
└── DocumentViewer.jsx         # Vista del documento
```

**Tareas:**
- [ ] Crear página principal ContractReviewPage
- [ ] Implementar uploader con preview
- [ ] Crear visualizador de issues
- [ ] Implementar modal de sugerencias
- [ ] Crear exportador básico

#### 2.2 Integración con Sistema Actual
- [ ] Agregar link en sidebar
- [ ] Reutilizar AuthContext
- [ ] Reutilizar componentes UI existentes

---

### FASE 3: Reglas de Compliance (Semana 5-6)

#### 3.1 Reglas Iniciales (20 mínimo)

**Categoría: Términos Generales**
1. Verificar fecha de vigencia
2. Verificar partes identificadas
3. Verificar objeto del contrato
4. Verificar jurisdicción aplicable

**Categoría: Financieros**
5. Verificar términos de pago
6. Verificar penalizaciones
7. Verificar ajustes de precio
8. Verificar garantías

**Categoría: Legales**
9. Verificar cláusula de confidencialidad
10. Verificar propiedad intelectual
11. Verificar limitación de responsabilidad
12. Verificar fuerza mayor

**Categoría: Operativos**
13. Verificar SLAs definidos
14. Verificar entregables
15. Verificar cronograma
16. Verificar proceso de cambios

**Categoría: Terminación**
17. Verificar causales de rescisión
18. Verificar proceso de terminación
19. Verificar efectos post-terminación
20. Verificar arbitraje/mediación

**Tareas:**
- [ ] Documentar cada regla con criterios
- [ ] Crear prompts para cada verificación
- [ ] Implementar scoring por regla
- [ ] Crear UI de configuración de reglas

---

### FASE 4: Polish & Testing (Semana 7-8)

#### 4.1 Performance
- [ ] Optimizar para < 2 min en 50 páginas
- [ ] Implementar procesamiento async
- [ ] Agregar cache de análisis

#### 4.2 UX
- [ ] Mejorar feedback de progreso
- [ ] Agregar tooltips explicativos
- [ ] Implementar undo/redo

#### 4.3 Testing
- [ ] Unit tests para extractores
- [ ] Integration tests para análisis
- [ ] E2E tests para flujo completo

---

## 4. ARCHIVOS A CREAR

### Backend (9 archivos nuevos)
```
backend/
├── routes/
│   └── contract_review.py           # NUEVO
├── services/
│   └── contract_review/
│       ├── __init__.py              # NUEVO
│       ├── document_extractor.py    # NUEVO
│       ├── clause_detector.py       # NUEVO
│       ├── compliance_rules.py      # NUEVO
│       ├── contract_analyzer.py     # NUEVO
│       └── suggestion_generator.py  # NUEVO
└── models/
    └── contract_models.py           # NUEVO
```

### Frontend (8 archivos nuevos)
```
frontend/src/
├── pages/
│   └── ContractReviewPage.jsx       # NUEVO
└── components/
    └── contract-review/
        ├── DocumentUploader.jsx     # NUEVO
        ├── AnalysisProgress.jsx     # NUEVO
        ├── IssuesList.jsx           # NUEVO
        ├── IssueCard.jsx            # NUEVO
        ├── SuggestionModal.jsx      # NUEVO
        └── DocumentViewer.jsx       # NUEVO
```

---

## 5. RESUMEN DE GAPS

| Área | PRD | Actual | Acción |
|------|-----|--------|--------|
| Propósito | Revisión contratos | Auditoría fiscal | Agregar módulo |
| Upload | Simple | Multi-documento | Simplificar flujo |
| Análisis | Reglas compliance | 4 pilares fiscales | Crear motor reglas |
| Output | Doc anotado | PDF separado | Crear exportador |
| UX | Self-service | Enterprise | Nueva página simple |
| Users | Abogados | Fiscalistas | Agregar roles |

---

## 6. ESTIMACIÓN DE ESFUERZO

| Fase | Duración | Complejidad |
|------|----------|-------------|
| 1. Foundation | 2 semanas | Alta |
| 2. Frontend MVP | 2 semanas | Media |
| 3. Reglas | 2 semanas | Media |
| 4. Polish | 2 semanas | Baja |
| **TOTAL** | **8 semanas** | - |

---

## 7. PRÓXIMOS PASOS INMEDIATOS

1. **Decidir estrategia** (Opción A, B o C)
2. **Crear branch** `feature/contract-review`
3. **Implementar** `document_extractor.py`
4. **Crear** 5 reglas de prueba
5. **Probar** con contrato real

---

## 8. OPEN QUESTIONS DEL PRD

| Pregunta | Propuesta de Respuesta |
|----------|------------------------|
| ¿Qué cláusulas en rule set inicial? | 20 reglas definidas arriba |
| ¿Qué LLM usar? | GPT-4o (ya integrado) |
| ¿Jurisdicciones? | México primero, expandir después |
| ¿Idiomas? | Español primero |
| ¿Pricing? | Freemium: 5 docs gratis/mes |
| ¿Tamaño máximo? | 50 páginas (como PRD) |

---

*Documento generado automáticamente - Revisar con equipo de producto*
