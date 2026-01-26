---
tipo: plantilla
version: "1.0"
agente: A2_PMO
instrucciones: "Complete los campos {{}} para personalizar las plantillas de consolidación de POs y reportes según las necesidades de su organización."
---

# Plantillas de Consolidación PO y Reportes

## 1. Introducción

Este documento contiene las plantillas estándar para:
- Órdenes de Compra (PO) de servicios intangibles
- Reportes de avance de proyectos
- Consolidación de dictámenes multiagente

## 2. Plantilla de Orden de Compra

### Encabezado PO

```
══════════════════════════════════════════════════════════════
                    ORDEN DE COMPRA
══════════════════════════════════════════════════════════════
Número PO:        {{NUMERO_PO}}
Fecha Emisión:    {{FECHA_EMISION}}
ID Proyecto:      {{ID_PROYECTO}}
══════════════════════════════════════════════════════════════
```

### Datos del Solicitante

| Campo | Valor |
|-------|-------|
| Empresa Solicitante | {{RAZON_SOCIAL_CLIENTE}} |
| RFC | {{RFC_CLIENTE}} |
| Área Solicitante | {{AREA_SOLICITANTE}} |
| Responsable | {{NOMBRE_RESPONSABLE}} |
| Correo | {{EMAIL_RESPONSABLE}} |
| Centro de Costos | {{CENTRO_COSTOS}} |

### Datos del Proveedor

| Campo | Valor |
|-------|-------|
| Razón Social | {{RAZON_SOCIAL_PROVEEDOR}} |
| RFC | {{RFC_PROVEEDOR}} |
| Representante Legal | {{REP_LEGAL_PROVEEDOR}} |
| Dirección Fiscal | {{DIRECCION_PROVEEDOR}} |
| Contacto | {{CONTACTO_PROVEEDOR}} |
| Correo | {{EMAIL_PROVEEDOR}} |

### Descripción del Servicio

| Campo | Detalle |
|-------|---------|
| Tipología | {{TIPOLOGIA_SERVICIO}} |
| Descripción | {{DESCRIPCION_SERVICIO}} |
| Alcance | {{ALCANCE_SERVICIO}} |
| Entregables | {{LISTA_ENTREGABLES}} |
| Fecha Inicio | {{FECHA_INICIO}} |
| Fecha Fin | {{FECHA_FIN}} |

### Condiciones Comerciales

| Concepto | Valor |
|----------|-------|
| Monto Total (antes de IVA) | {{MONTO_SUBTOTAL}} |
| IVA (16%) | {{MONTO_IVA}} |
| Monto Total | {{MONTO_TOTAL}} |
| Moneda | {{MONEDA}} |
| Forma de Pago | {{FORMA_PAGO}} |
| Condiciones de Pago | {{CONDICIONES_PAGO}} |

### Campos Obligatorios para Validación Fiscal

| Campo | Valor | Validación |
|-------|-------|------------|
| Código SAT | {{CODIGO_SAT}} | Requerido |
| Método de Pago | {{METODO_PAGO}} | Requerido |
| Uso CFDI | {{USO_CFDI}} | Requerido |
| Beneficio Económico Esperado | {{BEE_DESCRIPCION}} | Requerido |
| OKR Relacionado | {{OKR_VINCULADO}} | Requerido |

## 3. Plantilla de Reporte de Avance

### Encabezado

```
══════════════════════════════════════════════════════════════
              REPORTE DE AVANCE DE PROYECTO
══════════════════════════════════════════════════════════════
ID Proyecto:      {{ID_PROYECTO}}
Período:          {{PERIODO_REPORTE}}
Fase Actual:      {{FASE_ACTUAL}}
══════════════════════════════════════════════════════════════
```

### Resumen Ejecutivo

| Indicador | Estado | Valor |
|-----------|--------|-------|
| Avance General | {{SEMAFORO_AVANCE}} | {{PORCENTAJE_AVANCE}}% |
| Presupuesto | {{SEMAFORO_PRESUPUESTO}} | {{VARIACION_PRESUPUESTO}} |
| Tiempo | {{SEMAFORO_TIEMPO}} | {{VARIACION_TIEMPO}} |
| Riesgo | {{SEMAFORO_RIESGO}} | Score: {{SCORE_RIESGO}} |

### Estado por Agente

| Agente | Estado | Dictamen | Fecha |
|--------|--------|----------|-------|
| A1_SPONSOR | {{ESTADO_A1}} | {{DICTAMEN_A1}} | {{FECHA_A1}} |
| A2_PMO | {{ESTADO_A2}} | {{DICTAMEN_A2}} | {{FECHA_A2}} |
| A3_FISCAL | {{ESTADO_A3}} | {{DICTAMEN_A3}} | {{FECHA_A3}} |
| A4_LEGAL | {{ESTADO_A4}} | {{DICTAMEN_A4}} | {{FECHA_A4}} |
| A5_FINANZAS | {{ESTADO_A5}} | {{DICTAMEN_A5}} | {{FECHA_A5}} |
| A6_PROVEEDOR | {{ESTADO_A6}} | {{DICTAMEN_A6}} | {{FECHA_A6}} |

### Hitos del Proyecto

| Hito | Fecha Planeada | Fecha Real | Estado |
|------|----------------|------------|--------|
| {{HITO_1}} | {{FECHA_PLAN_1}} | {{FECHA_REAL_1}} | {{ESTADO_HITO_1}} |
| {{HITO_2}} | {{FECHA_PLAN_2}} | {{FECHA_REAL_2}} | {{ESTADO_HITO_2}} |
| {{HITO_3}} | {{FECHA_PLAN_3}} | {{FECHA_REAL_3}} | {{ESTADO_HITO_3}} |
| {{HITO_4}} | {{FECHA_PLAN_4}} | {{FECHA_REAL_4}} | {{ESTADO_HITO_4}} |

### Riesgos Identificados

| ID | Riesgo | Probabilidad | Impacto | Mitigación |
|----|--------|--------------|---------|------------|
| R1 | {{RIESGO_1}} | {{PROB_1}} | {{IMPACTO_1}} | {{MITIGACION_1}} |
| R2 | {{RIESGO_2}} | {{PROB_2}} | {{IMPACTO_2}} | {{MITIGACION_2}} |
| R3 | {{RIESGO_3}} | {{PROB_3}} | {{IMPACTO_3}} | {{MITIGACION_3}} |

### Acciones Pendientes

| # | Acción | Responsable | Fecha Límite | Prioridad |
|---|--------|-------------|--------------|-----------|
| 1 | {{ACCION_1}} | {{RESP_ACCION_1}} | {{FECHA_ACCION_1}} | {{PRIORIDAD_1}} |
| 2 | {{ACCION_2}} | {{RESP_ACCION_2}} | {{FECHA_ACCION_2}} | {{PRIORIDAD_2}} |
| 3 | {{ACCION_3}} | {{RESP_ACCION_3}} | {{FECHA_ACCION_3}} | {{PRIORIDAD_3}} |

## 4. Plantilla de Consolidación Multiagente

### Resumen de Dictámenes

```
══════════════════════════════════════════════════════════════
           CONSOLIDACIÓN DE DICTÁMENES MULTIAGENTE
══════════════════════════════════════════════════════════════
ID Proyecto:      {{ID_PROYECTO}}
Fecha:            {{FECHA_CONSOLIDACION}}
Versión:          {{VERSION_EXPEDIENTE}}
══════════════════════════════════════════════════════════════
```

### Matriz de Evaluación

| Dimensión | Agente | Resultado | Score | Observaciones |
|-----------|--------|-----------|-------|---------------|
| Estratégica | A1 | {{RESULTADO_ESTRATEGICO}} | {{SCORE_A1}}/100 | {{OBS_A1}} |
| Fiscal | A3 | {{RESULTADO_FISCAL}} | {{SCORE_A3}}/100 | {{OBS_A3}} |
| Legal | A4 | {{RESULTADO_LEGAL}} | {{SCORE_A4}}/100 | {{OBS_A4}} |
| Financiera | A5 | {{RESULTADO_FINANCIERO}} | {{SCORE_A5}}/100 | {{OBS_A5}} |
| Proveedor | A6 | {{RESULTADO_PROVEEDOR}} | {{SCORE_A6}}/100 | {{OBS_A6}} |

### Score Consolidado

| Componente | Peso | Score | Ponderado |
|------------|------|-------|-----------|
| Alineación Estratégica | {{PESO_ESTRATEGIA}}% | {{SCORE_A1}} | {{POND_A1}} |
| Cumplimiento Fiscal | {{PESO_FISCAL}}% | {{SCORE_A3}} | {{POND_A3}} |
| Solidez Legal | {{PESO_LEGAL}}% | {{SCORE_A4}} | {{POND_A4}} |
| Viabilidad Financiera | {{PESO_FINANZAS}}% | {{SCORE_A5}} | {{POND_A5}} |
| Confiabilidad Proveedor | {{PESO_PROVEEDOR}}% | {{SCORE_A6}} | {{POND_A6}} |
| **TOTAL** | 100% | - | **{{SCORE_TOTAL}}** |

### Dictamen Final

**Recomendación:** {{RECOMENDACION_FINAL}}

**Condiciones (si aplica):**
- {{CONDICION_1}}
- {{CONDICION_2}}
- {{CONDICION_3}}

**Firmas de Conformidad:**

| Rol | Nombre | Fecha |
|-----|--------|-------|
| Coordinador PMO | {{FIRMA_PMO}} | {{FECHA_FIRMA_PMO}} |
| Director Fiscal | {{FIRMA_FISCAL}} | {{FECHA_FIRMA_FISCAL}} |
| Director Finanzas | {{FIRMA_FINANZAS}} | {{FECHA_FIRMA_FINANZAS}} |

