# Plantilla de Expediente de Defensa Fiscal

## DUREZZA 4.0 - Defense File Structure

---

## CARÁTULA DEL EXPEDIENTE

```
═══════════════════════════════════════════════════════════════
                    EXPEDIENTE DE DEFENSA FISCAL
                         DUREZZA 4.0
═══════════════════════════════════════════════════════════════

Proyecto ID:        {{PROJECT_ID}}
Contribuyente:      {{RAZON_SOCIAL}}
RFC:                {{RFC}}

Proveedor:          {{PROVEEDOR_NOMBRE}}
RFC Proveedor:      {{RFC_PROVEEDOR}}

Servicio:           {{DESCRIPCION_SERVICIO}}
Monto Total:        ${{MONTO}} MXN + IVA
Período:            {{FECHA_INICIO}} a {{FECHA_FIN}}

Nivel de Riesgo:    {{VERDE | AMARILLO | ROJO}}
Score de Defensa:   {{SCORE}}/100

Generado:           {{FECHA_GENERACION}}
Versión:            {{VERSION}}
═══════════════════════════════════════════════════════════════
```

---

## ÍNDICE DEL EXPEDIENTE

### Sección 1: Resumen Ejecutivo
- 1.1 Síntesis de la operación
- 1.2 Análisis de riesgo
- 1.3 Fortalezas y debilidades
- 1.4 Recomendaciones

### Sección 2: Documentación Contractual
- 2.1 Contrato principal
- 2.2 Anexos técnicos
- 2.3 Órdenes de trabajo
- 2.4 Adendas (si aplica)

### Sección 3: Evidencia de Materialidad
- 3.1 Entregables recibidos
- 3.2 Comunicaciones relevantes
- 3.3 Minutas de reunión
- 3.4 Fotografías/Videos
- 3.5 Timeline de actividades

### Sección 4: Documentación Fiscal
- 4.1 CFDI(s) emitidos
- 4.2 Complementos de pago
- 4.3 Comprobantes bancarios
- 4.4 Registro contable

### Sección 5: Validación del Proveedor
- 5.1 Consulta Lista 69-B
- 5.2 Opinión de Cumplimiento 32-D
- 5.3 Constancia de Situación Fiscal
- 5.4 Verificación de domicilio
- 5.5 Due diligence realizado

### Sección 6: Fundamentos Legales
- 6.1 Marco normativo aplicable
- 6.2 Jurisprudencia relevante
- 6.3 Criterios del SAT favorables

### Sección 7: Argumentos de Defensa
- 7.1 Razón de negocios
- 7.2 Materialidad de la operación
- 7.3 Precio de mercado
- 7.4 Cumplimiento formal

---

## SECCIÓN 1: RESUMEN EJECUTIVO

### 1.1 Síntesis de la Operación

**Descripción:**
{{DESCRIPCION_DETALLADA_DEL_SERVICIO}}

**Justificación del gasto:**
{{RAZON_DE_NEGOCIOS}}

**Resultados obtenidos:**
{{BENEFICIOS_TANGIBLES}}

### 1.2 Análisis de Riesgo

| Factor | Score | Observación |
|--------|-------|-------------|
| Proveedor en 69-B | {{SCORE_69B}} | {{OBS_69B}} |
| Opinión 32-D | {{SCORE_32D}} | {{OBS_32D}} |
| Materialidad documentada | {{SCORE_MAT}} | {{OBS_MAT}} |
| Precio de mercado | {{SCORE_PRECIO}} | {{OBS_PRECIO}} |
| Documentación completa | {{SCORE_DOC}} | {{OBS_DOC}} |
| **SCORE TOTAL** | **{{SCORE_TOTAL}}/100** | |

### 1.3 Fortalezas del Expediente
1. {{FORTALEZA_1}}
2. {{FORTALEZA_2}}
3. {{FORTALEZA_3}}

### 1.4 Debilidades Identificadas
1. {{DEBILIDAD_1}} - **Mitigación:** {{MITIGACION_1}}
2. {{DEBILIDAD_2}} - **Mitigación:** {{MITIGACION_2}}

### 1.5 Recomendaciones
- {{RECOMENDACION_1}}
- {{RECOMENDACION_2}}

---

## SECCIÓN 2: DOCUMENTACIÓN CONTRACTUAL

### 2.1 Contrato Principal

| Campo | Valor |
|-------|-------|
| Número de contrato | {{NUM_CONTRATO}} |
| Fecha de firma | {{FECHA_FIRMA}} |
| Vigencia | {{VIGENCIA}} |
| Monto | {{MONTO}} |
| Forma de pago | {{FORMA_PAGO}} |

**Archivo:** `contratos/contrato_{{NUM}}.pdf`

### 2.2 Anexos Técnicos

| Anexo | Descripción | Archivo |
|-------|-------------|---------|
| A | Alcance detallado | anexo_a.pdf |
| B | Cronograma | anexo_b.pdf |
| C | Tarifas | anexo_c.pdf |

---

## SECCIÓN 3: EVIDENCIA DE MATERIALIDAD

### 3.1 Entregables Recibidos

| # | Entregable | Fecha | Archivo |
|---|------------|-------|---------|
| 1 | {{ENTREGABLE_1}} | {{FECHA_1}} | entregables/{{FILE_1}} |
| 2 | {{ENTREGABLE_2}} | {{FECHA_2}} | entregables/{{FILE_2}} |

### 3.2 Comunicaciones Relevantes

| Fecha | De | Para | Asunto | Archivo |
|-------|----|----|--------|---------|
| {{FECHA}} | {{DE}} | {{PARA}} | {{ASUNTO}} | correos/{{FILE}} |

### 3.3 Timeline de Actividades

```
{{FECHA_1}} ─── Firma de contrato
     │
{{FECHA_2}} ─── Inicio de trabajos
     │
{{FECHA_3}} ─── Entrega parcial 1
     │
{{FECHA_4}} ─── Revisión y feedback
     │
{{FECHA_5}} ─── Entrega final
     │
{{FECHA_6}} ─── Aceptación formal
     │
{{FECHA_7}} ─── Emisión de CFDI
     │
{{FECHA_8}} ─── Pago realizado
```

---

## SECCIÓN 4: DOCUMENTACIÓN FISCAL

### 4.1 CFDI Emitidos

| Folio | UUID | Fecha | Subtotal | IVA | Total |
|-------|------|-------|----------|-----|-------|
| {{FOLIO}} | {{UUID}} | {{FECHA}} | {{SUBTOTAL}} | {{IVA}} | {{TOTAL}} |

**Validación SAT:** ✅ Vigente

### 4.2 Complementos de Pago

| Folio Complemento | Fecha Pago | Monto | Archivo |
|-------------------|------------|-------|---------|
| {{FOLIO_CP}} | {{FECHA}} | {{MONTO}} | pagos/{{FILE}} |

### 4.3 Comprobantes Bancarios

| Fecha | Banco | Referencia | Monto | Archivo |
|-------|-------|------------|-------|---------|
| {{FECHA}} | {{BANCO}} | {{REF}} | {{MONTO}} | bancos/{{FILE}} |

---

## SECCIÓN 5: VALIDACIÓN DEL PROVEEDOR

### 5.1 Consulta Lista 69-B

**Fecha de consulta:** {{FECHA}}
**Resultado:** ✅ NO ENCONTRADO
**Folio de verificación:** {{FOLIO}}
**Archivo:** validaciones/69b_{{FECHA}}.pdf

### 5.2 Opinión de Cumplimiento 32-D

**Fecha de emisión:** {{FECHA}}
**Sentido:** ✅ POSITIVA
**Vigencia hasta:** {{VIGENCIA}}
**Folio SAT:** {{FOLIO}}
**Archivo:** validaciones/32d_{{FECHA}}.pdf

---

## SECCIÓN 6: FUNDAMENTOS LEGALES

### 6.1 Marco Normativo

| Ordenamiento | Artículos | Aplicación |
|--------------|-----------|------------|
| CFF | 29, 29-A, 69-B | Comprobantes y EFOS |
| LISR | 25, 27 | Deducciones |
| LIVA | 4, 5 | Acreditamiento |
| RMF 2026 | 3.10.2, 3.18.2 | Procedimientos |

### 6.2 Jurisprudencia Favorable

| Tesis | Rubro | Aplicación |
|-------|-------|------------|
| 2a./J. 78/2016 | Estrictamente indispensable | Interpretación amplia |
| 2a./J. 104/2017 | Defensa vs 69-B | Carga probatoria |

---

## SECCIÓN 7: ARGUMENTOS DE DEFENSA

### 7.1 Razón de Negocios
{{ARGUMENTO_RAZON_NEGOCIOS}}

### 7.2 Materialidad de la Operación
{{ARGUMENTO_MATERIALIDAD}}

### 7.3 Precio de Mercado
{{ARGUMENTO_PRECIO}}

### 7.4 Cumplimiento Formal
{{ARGUMENTO_CUMPLIMIENTO}}

---

## CHECKLIST DE COMPLETITUD

- [ ] Contrato firmado
- [ ] CFDI válido
- [ ] Pago bancario comprobado
- [ ] Entregables documentados
- [ ] 69-B verificado
- [ ] 32-D vigente
- [ ] Timeline completo
- [ ] Comunicaciones archivadas

**Completitud del expediente:** {{PORCENTAJE}}%

---

*Expediente generado por DUREZZA 4.0 - Revisar.IA*
*Fecha de generación: {{FECHA_HORA}}*
