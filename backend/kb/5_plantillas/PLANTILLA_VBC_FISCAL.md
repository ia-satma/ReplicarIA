# Plantilla: VBC - Verificación de Base de Cumplimiento Fiscal

## Información del Documento

| Campo | Valor |
|-------|-------|
| Número de VBC | VBC-[YYYY]-[###] |
| Proyecto asociado | [____] |
| Fecha de elaboración | [DD/MM/AAAA] |
| Elaborado por | [Agente A3 - Fiscal] |
| Revisado por | [____] |

---

## 1. Datos del Contribuyente

| Campo | Valor |
|-------|-------|
| Razón Social | [____] |
| RFC | [____] |
| Régimen Fiscal | [____] |
| Domicilio Fiscal | [____] |
| Actividad Preponderante | [____] |

---

## 2. Datos del Proveedor

| Campo | Valor |
|-------|-------|
| Razón Social | [____] |
| RFC | [____] |
| Estatus RFC (Portal SAT) | ☐ Activo ☐ Suspendido ☐ Cancelado |
| Listado 69-B | ☐ No aparece ☐ Presunción ☐ Definitivo |
| Opinión 32-D | ☐ Positiva ☐ Negativa ☐ No disponible |
| Fecha de verificación | [DD/MM/AAAA] |

---

## 3. Verificación de los 4 Pilares Fiscales

### 3.1 Pilar 1: Razón de Negocios (Art. 5-A CFF)

**Definición Legal:** Los actos jurídicos carecen de razón de negocios cuando el beneficio económico cuantificable razonablemente esperado sea menor al beneficio fiscal.

| Criterio | Cumple | Evidencia | Observaciones |
|----------|--------|-----------|---------------|
| Vinculación con el giro | ☐ Sí ☐ No | [____] | [____] |
| Objetivo económico documentado | ☐ Sí ☐ No | SIB Sección 1 | [____] |
| Beneficio más allá del fiscal | ☐ Sí ☐ No | BEE > Ahorro ISR | [____] |
| Sponsor interno identificado | ☐ Sí ☐ No | [____] | [____] |

**Evaluación Razón de Negocios:**

| Concepto | Monto |
|----------|-------|
| Monto del servicio | $[____] |
| Ahorro fiscal estimado (30%) | $[____] |
| Beneficio económico esperado | $[____] |
| **Diferencia (BEE - Ahorro)** | **$[____]** |

☐ **RAZÓN DE NEGOCIOS ACREDITADA** - BEE > Beneficio Fiscal
☐ **RAZÓN DE NEGOCIOS NO CLARA** - Requiere documentación adicional
☐ **SIN RAZÓN DE NEGOCIOS** - Alto riesgo de rechazo

**Puntuación Pilar 1:** [__]/25 puntos de riesgo

---

### 3.2 Pilar 2: Beneficio Económico Esperado (Art. 5-A CFF)

| Criterio | Cumple | Evidencia | Observaciones |
|----------|--------|-----------|---------------|
| BEE cuantificado | ☐ Sí ☐ No | SIB Sección 2 | [____] |
| ROI documentado | ☐ Sí ☐ No | [____]x | [____] |
| KPIs definidos | ☐ Sí ☐ No | [Lista] | [____] |
| Horizonte temporal razonable | ☐ Sí ☐ No | [__] meses | [____] |
| Metodología de cálculo | ☐ Sí ☐ No | [____] | [____] |

**Detalle del BEE:**

| Indicador | Meta | Método de Medición | Fecha de Evaluación |
|-----------|------|-------------------|---------------------|
| [____] | [____] | [____] | [DD/MM/AAAA] |
| [____] | [____] | [____] | [DD/MM/AAAA] |
| [____] | [____] | [____] | [DD/MM/AAAA] |

☐ **BEE DOCUMENTADO Y RAZONABLE**
☐ **BEE REQUIERE FORTALECIMIENTO**
☐ **BEE NO ACREDITADO**

**Puntuación Pilar 2:** [__]/25 puntos de riesgo

---

### 3.3 Pilar 3: Materialidad (Art. 69-B CFF)

| Criterio | Cumple | Evidencia | Observaciones |
|----------|--------|-----------|---------------|
| Proveedor con capacidad operativa | ☐ Sí ☐ No | [____] | [____] |
| Servicio efectivamente prestado | ☐ Sí ☐ No | Acta AAT | [____] |
| Entregables específicos recibidos | ☐ Sí ☐ No | [Lista] | [____] |
| Evidencia de trabajo (minutas, correos) | ☐ Sí ☐ No | [Cantidad] | [____] |
| Personal identificable del proveedor | ☐ Sí ☐ No | [Nombres] | [____] |
| Uso/implementación del entregable | ☐ Sí ☐ No | [____] | [____] |

**Checklist de Materialidad:**

- [ ] Contrato/SOW firmado antes de iniciar
- [ ] Minutas de al menos 3 reuniones de trabajo
- [ ] Correos de coordinación durante ejecución
- [ ] Versiones intermedias de entregables
- [ ] Acta de aceptación técnica firmada
- [ ] Evidencia de uso post-entrega
- [ ] CFDI coincide con descripción de servicio

☐ **MATERIALIDAD ACREDITADA**
☐ **MATERIALIDAD PARCIAL** - Fortalecer evidencia
☐ **MATERIALIDAD NO ACREDITADA** - Alto riesgo

**Puntuación Pilar 3:** [__]/25 puntos de riesgo

---

### 3.4 Pilar 4: Trazabilidad (NOM-151)

| Criterio | Cumple | Evidencia | Observaciones |
|----------|--------|-----------|---------------|
| Documentos con fecha cierta | ☐ Sí ☐ No | [____] | [____] |
| Conservación digital adecuada | ☐ Sí ☐ No | Revisar-IA | [____] |
| Integridad verificable | ☐ Sí ☐ No | Hash SHA-256 | [____] |
| Cadena de custodia clara | ☐ Sí ☐ No | [____] | [____] |
| Acceso controlado | ☐ Sí ☐ No | Permisos | [____] |

**Documentos Conservados:**

| # | Documento | Fecha | Hash | Ubicación |
|---|-----------|-------|------|-----------|
| 1 | SIB | [____] | [____] | Revisar-IA |
| 2 | SOW | [____] | [____] | Revisar-IA |
| 3 | Contrato | [____] | [____] | Revisar-IA |
| 4 | Minutas | [____] | [____] | Revisar-IA |
| 5 | Entregables | [____] | [____] | Revisar-IA |
| 6 | Acta AAT | [____] | [____] | Revisar-IA |
| 7 | CFDI | [____] | [____] | SAT |

☐ **TRAZABILIDAD COMPLETA**
☐ **TRAZABILIDAD PARCIAL**
☐ **TRAZABILIDAD INSUFICIENTE**

**Puntuación Pilar 4:** [__]/25 puntos de riesgo

---

## 4. Verificación del CFDI

### 4.1 Datos del Comprobante

| Campo | CFDI | SOW/Contrato | Coincide |
|-------|------|--------------|----------|
| RFC Emisor | [____] | [____] | ☐ Sí ☐ No |
| RFC Receptor | [____] | [____] | ☐ Sí ☐ No |
| Descripción | [____] | [____] | ☐ Sí ☐ No |
| Monto | $[____] | $[____] | ☐ Sí ☐ No |
| Fecha | [____] | [____] | ☐ Sí ☐ No |

### 4.2 Three-Way Match

| Elemento | Contrato | CFDI | Pago | Match |
|----------|----------|------|------|-------|
| Proveedor | [____] | [____] | [____] | ☐ |
| Monto | $[____] | $[____] | $[____] | ☐ |
| Concepto | [____] | [____] | [____] | ☐ |
| Fecha | [____] | [____] | [____] | ☐ |

☐ **THREE-WAY MATCH COMPLETO**
☐ **DISCREPANCIAS DETECTADAS** - [Detalle]

---

## 5. Resumen de Riesgo Fiscal

### 5.1 Puntuación por Pilar

| Pilar | Puntos (0-25) | Nivel | Color |
|-------|---------------|-------|-------|
| Razón de Negocios | [__] | [____] | 🟢🟡🟠🔴 |
| Beneficio Económico | [__] | [____] | 🟢🟡🟠🔴 |
| Materialidad | [__] | [____] | 🟢🟡🟠🔴 |
| Trazabilidad | [__] | [____] | 🟢🟡🟠🔴 |
| **TOTAL** | **[__]/100** | | |

### 5.2 Índice de Defendibilidad

| Rango | Nivel | Significado |
|-------|-------|-------------|
| 0-20 | Bajo | Expediente sólido, alta defendibilidad |
| 21-40 | Moderado | Defendible con algunas áreas de mejora |
| 41-60 | Alto | Requiere fortalecimiento significativo |
| 61-100 | Crítico | Alto riesgo de rechazo por SAT |

**Índice de Defendibilidad del Proyecto:** [__]/100

### 5.3 Recomendaciones

| Prioridad | Área | Recomendación | Responsable | Fecha Límite |
|-----------|------|---------------|-------------|--------------|
| Alta | [____] | [____] | [____] | [DD/MM/AAAA] |
| Media | [____] | [____] | [____] | [DD/MM/AAAA] |
| Baja | [____] | [____] | [____] | [DD/MM/AAAA] |

---

## 6. Dictamen Fiscal

### 6.1 Conclusión

☐ **DEDUCCIÓN PROCEDENTE** - Cumple con requisitos fiscales para deducción.

☐ **DEDUCCIÓN CONDICIONADA** - Procedente sujeta a subsanar observaciones.

☐ **DEDUCCIÓN EN RIESGO** - Deficiencias significativas identificadas.

☐ **DEDUCCIÓN NO RECOMENDADA** - Alto riesgo de rechazo, no proceder con pago.

### 6.2 Fundamento Legal

Este dictamen se emite con fundamento en:
- Artículo 5-A del Código Fiscal de la Federación
- Artículo 27 de la Ley del Impuesto sobre la Renta
- Artículo 69-B del Código Fiscal de la Federación
- NOM-151-SCFI-2016

### 6.3 Jurisprudencia de Soporte

El uso de inteligencia artificial para este análisis está respaldado por:
- Tesis II.2o.C. J/1 K (12a.) - SCJN
- Registro: 2031639
- La IA como herramienta auxiliar válida en procesos de análisis y decisión

---

## 7. Firmas

### Elaborado por:

| Agente | Identificador | Timestamp |
|--------|---------------|-----------|
| A3 Fiscal | [ID-Agente] | [ISO-8601] |

### Revisado por:

| Rol | Nombre | Firma | Fecha |
|-----|--------|-------|-------|
| Contador/Fiscal | [____] | _________ | [DD/MM/AAAA] |
| Director Financiero | [____] | _________ | [DD/MM/AAAA] |

---

## 8. Historial de Versiones

| Versión | Fecha | Cambios | Autor |
|---------|-------|---------|-------|
| 1.0 | [____] | Versión inicial | A3 |
| [__] | [____] | [____] | [____] |

---

## Anexos

- [ ] Anexo 1: Consulta de estatus RFC (captura)
- [ ] Anexo 2: Consulta lista 69-B (captura)
- [ ] Anexo 3: Opinión 32-D (PDF)
- [ ] Anexo 4: CFDI XML validado
- [ ] Anexo 5: Cálculo detallado del BEE

---

## Código de Verificación

```
VBC ID: [UUID]
Hash documento: [SHA-256]
Timestamp: [ISO-8601]
Verificación: https://revisar.ia/vbc/[id]
```
