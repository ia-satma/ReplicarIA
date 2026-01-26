---
tipo: normativo
version: "1.0"
agente: A3_FISCAL
instrucciones: "Guía para demostrar la materialidad y existencia de operaciones conforme al Artículo 69-B del CFF. Esencial para defenderse de presunciones de operaciones simuladas."
---

# Guía de Materialidad de Operaciones – Artículo 69-B CFF

## 1. Marco Normativo

### Artículo 69-B del Código Fiscal de la Federación

El Art. 69-B establece el procedimiento mediante el cual el SAT puede presumir **inexistentes** las operaciones amparadas en comprobantes fiscales emitidos por contribuyentes que se ubican en los supuestos de operaciones simuladas (EFOS).

**Implicaciones clave:**
- Los CFDI de proveedores en lista definitiva 69-B **no generan efectos fiscales**
- El contribuyente receptor debe **demostrar materialidad** para conservar efectos
- Plazo de 30 días hábiles para desvirtuar presunción

### Definición de Materialidad

La **materialidad** implica demostrar que:
1. La operación **efectivamente se realizó**
2. El servicio/bien **fue recibido** por el contribuyente
3. Existe **evidencia documental y física** de la transacción
4. Hubo **flujo real de recursos** (pago efectivo)

## 2. Elementos de Prueba de Materialidad

### 2.1 Pirámide de Evidencia

```
                    ┌─────────────────┐
                    │   ENTREGABLES   │  ← Peso máximo
                    │    TANGIBLES    │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │  COMUNICACIONES │
                    │   OPERATIVAS    │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │   PAGOS Y       │
                    │   FACTURACIÓN   │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │   CONTRATOS Y   │  ← Base documental
                    │   PROPUESTAS    │
                    └─────────────────┘
```

### 2.2 Catálogo de Evidencias

| Categoría | Evidencia | Peso Probatorio | Obligatoriedad |
|-----------|-----------|-----------------|----------------|
| **Documental** | Contrato firmado | Alto | Obligatorio |
| | Propuesta comercial | Medio | Recomendado |
| | Orden de compra | Medio | Obligatorio |
| **Financiera** | CFDI timbrado | Alto | Obligatorio |
| | Estado de cuenta bancario | Alto | Obligatorio |
| | Póliza contable | Medio | Obligatorio |
| **Operativa** | Entregables recibidos | Muy Alto | Obligatorio |
| | Correos de coordinación | Alto | Recomendado |
| | Minutas de reuniones | Alto | Recomendado |
| | Reportes de avance | Alto | Recomendado |
| **Capacidad** | CV de personal asignado | Medio | Según tipología |
| | Acta constitutiva proveedor | Bajo | Verificación |
| | Comprobante de domicilio | Bajo | Verificación |

## 3. Procedimiento de Verificación de Materialidad

### Paso 1: Verificación Documental

**Checklist Documental:**

| # | Documento | Presente | Válido | Observaciones |
|---|-----------|----------|--------|---------------|
| 1 | Contrato de servicios | ☐ | ☐ | {{OBS_CONTRATO}} |
| 2 | CFDI(s) del periodo | ☐ | ☐ | {{OBS_CFDI}} |
| 3 | Comprobante de pago | ☐ | ☐ | {{OBS_PAGO}} |
| 4 | Propuesta/cotización | ☐ | ☐ | {{OBS_PROPUESTA}} |
| 5 | Orden de compra | ☐ | ☐ | {{OBS_OC}} |

### Paso 2: Verificación de Flujo Financiero

**Trazabilidad del Pago:**

```
Cuenta origen: {{CUENTA_ORIGEN}}
         │
         ▼
Transferencia SPEI: {{REFERENCIA_SPEI}}
Fecha: {{FECHA_TRANSFERENCIA}}
Monto: {{MONTO_TRANSFERENCIA}}
         │
         ▼
Cuenta destino: {{CUENTA_DESTINO}}
Titular: {{TITULAR_CUENTA_DESTINO}}
```

**Validaciones:**
- [ ] Cuenta destino coincide con RFC del proveedor
- [ ] Monto coincide con CFDI
- [ ] Fecha de pago es congruente con periodo de servicio
- [ ] No hay devolución del pago al pagador

### Paso 3: Verificación de Entregables

**Matriz de Entregables:**

| Entregable | Fecha Compromiso | Fecha Recepción | Evidencia | Estado |
|------------|------------------|-----------------|-----------|--------|
| {{ENTREGABLE_1}} | {{FECHA_COMP_1}} | {{FECHA_REC_1}} | {{EVIDENCIA_1}} | {{ESTADO_1}} |
| {{ENTREGABLE_2}} | {{FECHA_COMP_2}} | {{FECHA_REC_2}} | {{EVIDENCIA_2}} | {{ESTADO_2}} |
| {{ENTREGABLE_3}} | {{FECHA_COMP_3}} | {{FECHA_REC_3}} | {{EVIDENCIA_3}} | {{ESTADO_3}} |

### Paso 4: Verificación de Comunicaciones

**Línea de Tiempo de Interacciones:**

| Fecha | Tipo | Participantes | Asunto | Evidencia |
|-------|------|---------------|--------|-----------|
| {{FECHA_COM_1}} | {{TIPO_COM_1}} | {{PARTICIPANTES_1}} | {{ASUNTO_1}} | {{EVIDENCIA_COM_1}} |
| {{FECHA_COM_2}} | {{TIPO_COM_2}} | {{PARTICIPANTES_2}} | {{ASUNTO_2}} | {{EVIDENCIA_COM_2}} |
| {{FECHA_COM_3}} | {{TIPO_COM_3}} | {{PARTICIPANTES_3}} | {{ASUNTO_3}} | {{EVIDENCIA_COM_3}} |

## 4. Score de Materialidad

### Metodología de Cálculo

```
Score Materialidad = (Doc × 0.20) + (Fin × 0.25) + (Ent × 0.35) + (Com × 0.20)

Donde:
- Doc = Score documental (0-100)
- Fin = Score financiero (0-100)
- Ent = Score entregables (0-100)
- Com = Score comunicaciones (0-100)
```

### Umbrales de Riesgo

| Rango Score | Nivel | Dictamen | Acción |
|-------------|-------|----------|--------|
| 90-100 | Óptimo | ✅ Materialidad demostrada | Aprobar |
| 75-89 | Aceptable | ⚠️ Materialidad suficiente | Aprobar con observaciones |
| 60-74 | Riesgoso | ⚠️ Materialidad débil | Requerir documentación adicional |
| 40-59 | Crítico | ❌ Materialidad insuficiente | No aprobar / Revisar |
| 0-39 | Inaceptable | ❌ Sin materialidad | Rechazar operación |

## 5. Red Flags de Operaciones Simuladas

### Indicadores de Alerta

| Indicador | Descripción | Peso |
|-----------|-------------|------|
| 🔴 Proveedor en lista 69-B | RFC en lista definitiva SAT | Bloqueante |
| 🔴 Pago en efectivo | Operaciones > $2,000 MXN | Crítico |
| 🔴 Sin entregables | No hay evidencia de servicio | Crítico |
| 🔴 Operación circular | Recursos regresan al pagador | Crítico |
| 🟠 Proveedor recién constituido | < {{MESES_MINIMOS}} meses operando | Alto |
| 🟠 Sin personal | Proveedor sin empleados | Alto |
| 🟠 Domicilio virtual | Sin presencia física real | Alto |
| 🟡 Precio atípico | Desviación > {{DESVIACION_PRECIO}}% vs mercado | Medio |
| 🟡 Única operación | Sin historial con el proveedor | Medio |

## 6. Dictamen de Materialidad

### Formato de Dictamen

```
══════════════════════════════════════════════════════════════
           DICTAMEN DE MATERIALIDAD – Art. 69-B CFF
══════════════════════════════════════════════════════════════
Proyecto:          {{ID_PROYECTO}}
Proveedor:         {{NOMBRE_PROVEEDOR}}
RFC:               {{RFC_PROVEEDOR}}
Monto:             {{MONTO_OPERACION}}
Fecha Evaluación:  {{FECHA_EVALUACION}}
══════════════════════════════════════════════════════════════

ESTATUS LISTA 69-B: {{ESTATUS_69B}}
  └── Fecha consulta: {{FECHA_CONSULTA_69B}}
  └── Resultado: {{RESULTADO_69B}}

SCORE DE MATERIALIDAD: {{SCORE_MATERIALIDAD}}/100

Componentes:
├── Documental:      {{SCORE_DOC}}/100 (×0.20 = {{POND_DOC}})
├── Financiero:      {{SCORE_FIN}}/100 (×0.25 = {{POND_FIN}})
├── Entregables:     {{SCORE_ENT}}/100 (×0.35 = {{POND_ENT}})
└── Comunicaciones:  {{SCORE_COM}}/100 (×0.20 = {{POND_COM}})

RESULTADO: {{RESULTADO_DICTAMEN}}

OBSERVACIONES:
{{OBSERVACIONES_MATERIALIDAD}}

DOCUMENTACIÓN FALTANTE:
{{DOCUMENTACION_FALTANTE}}

RECOMENDACIONES:
{{RECOMENDACIONES_MATERIALIDAD}}
══════════════════════════════════════════════════════════════
```

## 7. Procedimiento de Defensa ante SAT

### Escenario: Proveedor incluido en Lista 69-B

**Pasos para Desvirtuar:**

1. **Recopilación de evidencia** (Días 1-10)
   - Reunir toda documentación de materialidad
   - Obtener declaraciones de personal involucrado
   - Solicitar confirmación de entregables

2. **Preparación de escrito** (Días 11-20)
   - Elaborar escrito de defensa
   - Anexar evidencias organizadas
   - Incluir peritajes si aplica

3. **Presentación ante SAT** (Días 21-30)
   - Presentar escrito dentro del plazo legal
   - Obtener acuse de recibo
   - Dar seguimiento

**Documentación Recomendada para Defensa:**
- {{DOC_DEFENSA_1}}
- {{DOC_DEFENSA_2}}
- {{DOC_DEFENSA_3}}
- {{DOC_DEFENSA_4}}
- {{DOC_DEFENSA_5}}

