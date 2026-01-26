---
tipo: plantilla
version: "1.0"
agente: A2_PMO
instrucciones: "Complete los campos {{}} para personalizar las listas de verificación según la tipología de servicio aplicable a su organización."
---

# Checklist por Tipología de Servicio

## 1. Introducción

Este documento contiene las **listas de verificación** específicas para cada tipología de servicio intangible. Cada checklist define:

- Documentos requeridos
- Evidencias necesarias
- Criterios de validación
- Responsables de verificación

## 2. Tipologías de Servicio

### Clasificación General

| Código | Tipología | Riesgo Base | Documentación |
|--------|-----------|-------------|---------------|
| TIP-01 | Consultoría Estratégica | {{RIESGO_TIP01}} | Alta |
| TIP-02 | Servicios de Software/SaaS | {{RIESGO_TIP02}} | Alta |
| TIP-03 | Servicios Intragrupo | {{RIESGO_TIP03}} | Muy Alta |
| TIP-04 | Management Fees | {{RIESGO_TIP04}} | Muy Alta |
| TIP-05 | Servicios Profesionales | {{RIESGO_TIP05}} | Media |
| TIP-06 | Licenciamiento/Regalías | {{RIESGO_TIP06}} | Alta |
| TIP-07 | Capacitación/Entrenamiento | {{RIESGO_TIP07}} | Media |
| TIP-08 | Marketing/Publicidad | {{RIESGO_TIP08}} | Alta |

## 3. Checklist TIP-01: Consultoría Estratégica

### Documentos Obligatorios

| # | Documento | Responsable | Validador | Estado |
|---|-----------|-------------|-----------|--------|
| 1 | Contrato de servicios firmado | {{RESP_CONTRATO}} | A4_LEGAL | ☐ |
| 2 | Propuesta técnica/comercial | {{RESP_PROPUESTA}} | A1_SPONSOR | ☐ |
| 3 | CV de consultores asignados | {{RESP_CV}} | A6_PROVEEDOR | ☐ |
| 4 | Cronograma de entregables | {{RESP_CRONOGRAMA}} | A2_PMO | ☐ |
| 5 | Definición de BEE cuantificado | {{RESP_BEE}} | A5_FINANZAS | ☐ |

### Evidencias de Materialidad

| # | Evidencia | Frecuencia | Formato |
|---|-----------|------------|---------|
| 1 | Minutas de reuniones | {{FREC_MINUTAS}} | PDF firmado |
| 2 | Reportes de avance | {{FREC_REPORTES}} | Documento ejecutivo |
| 3 | Entregables parciales | Por hito | Según contrato |
| 4 | Control de horas | {{FREC_HORAS}} | Timesheet |
| 5 | Correos de coordinación | Continuo | Exportación email |

### Criterios de Validación Fiscal

- [ ] Razón de negocios documentada (Art. 5-A CFF)
- [ ] Proveedor no en lista 69-B
- [ ] Precio de mercado justificado
- [ ] Entregables verificables
- [ ] BEE superior al {{UMBRAL_BEE_MINIMO}}% del monto

## 4. Checklist TIP-02: Servicios de Software/SaaS

### Documentos Obligatorios

| # | Documento | Responsable | Validador | Estado |
|---|-----------|-------------|-----------|--------|
| 1 | Contrato de licenciamiento/servicio | {{RESP_CONTRATO}} | A4_LEGAL | ☐ |
| 2 | Especificaciones técnicas | {{RESP_SPECS}} | {{AREA_TI}} | ☐ |
| 3 | SLA de servicio | {{RESP_SLA}} | A2_PMO | ☐ |
| 4 | Estudio de necesidad tecnológica | {{RESP_ESTUDIO}} | A1_SPONSOR | ☐ |
| 5 | Comparativo de mercado | {{RESP_COMPARATIVO}} | A5_FINANZAS | ☐ |

### Evidencias de Materialidad

| # | Evidencia | Frecuencia | Formato |
|---|-----------|------------|---------|
| 1 | Logs de acceso/uso | {{FREC_LOGS}} | Exportación sistema |
| 2 | Reportes de uptime | {{FREC_UPTIME}} | Dashboard |
| 3 | Tickets de soporte | Continuo | Sistema ticketing |
| 4 | Usuarios activos | {{FREC_USUARIOS}} | Reporte de licencias |
| 5 | Integraciones activas | {{FREC_INTEGRACIONES}} | Documentación técnica |

### Criterios de Validación Fiscal

- [ ] Código SAT correcto (desarrollo vs licenciamiento)
- [ ] Retención aplicable identificada
- [ ] Precio comparable con mercado
- [ ] Usuarios beneficiados documentados
- [ ] Impacto operativo cuantificado

## 5. Checklist TIP-03: Servicios Intragrupo

### Documentos Obligatorios

| # | Documento | Responsable | Validador | Estado |
|---|-----------|-------------|-----------|--------|
| 1 | Contrato intercompañía | {{RESP_CONTRATO}} | A4_LEGAL | ☐ |
| 2 | Estudio de precios de transferencia | {{RESP_PT}} | A3_FISCAL | ☐ |
| 3 | Política de asignación de costos | {{RESP_POLITICA}} | A5_FINANZAS | ☐ |
| 4 | Justificación de necesidad | {{RESP_JUSTIFICACION}} | A1_SPONSOR | ☐ |
| 5 | Organigrama funcional | {{RESP_ORGANIGRAMA}} | A6_PROVEEDOR | ☐ |

### Evidencias de Materialidad

| # | Evidencia | Frecuencia | Formato |
|---|-----------|------------|---------|
| 1 | Reportes de servicios prestados | {{FREC_REPORTES}} | Documento detallado |
| 2 | Asignación de personal | {{FREC_ASIGNACION}} | Timesheet/nómina |
| 3 | Beneficios recibidos | {{FREC_BENEFICIOS}} | Reporte cuantificado |
| 4 | Correos de coordinación | Continuo | Exportación email |
| 5 | Actas de comité | {{FREC_ACTAS}} | PDF firmado |

### Criterios de Validación Fiscal (Reforzados)

- [ ] Arm's length principle demostrado
- [ ] Documentación contemporánea
- [ ] Beneficio test satisfecho
- [ ] Duplicidad de funciones descartada
- [ ] Valor agregado específico documentado
- [ ] Comparables de mercado identificados

## 6. Checklist TIP-04: Management Fees

### Documentos Obligatorios

| # | Documento | Responsable | Validador | Estado |
|---|-----------|-------------|-----------|--------|
| 1 | Contrato marco de servicios | {{RESP_CONTRATO}} | A4_LEGAL | ☐ |
| 2 | Metodología de cálculo de fee | {{RESP_METODOLOGIA}} | A5_FINANZAS | ☐ |
| 3 | Estudio de precios de transferencia | {{RESP_PT}} | A3_FISCAL | ☐ |
| 4 | Catálogo de servicios incluidos | {{RESP_CATALOGO}} | A6_PROVEEDOR | ☐ |
| 5 | KPIs de desempeño | {{RESP_KPIS}} | A1_SPONSOR | ☐ |

### Evidencias de Materialidad

| # | Evidencia | Frecuencia | Formato |
|---|-----------|------------|---------|
| 1 | Desglose de servicios prestados | {{FREC_DESGLOSE}} | Excel detallado |
| 2 | Horas de dedicación | {{FREC_HORAS}} | Timesheet |
| 3 | Decisiones tomadas/apoyadas | {{FREC_DECISIONES}} | Actas/minutas |
| 4 | Reportes de gestión | {{FREC_GESTION}} | Presentación ejecutiva |
| 5 | Benchmark de mercado | {{FREC_BENCHMARK}} | Estudio comparativo |

### Criterios de Validación Fiscal (Críticos)

- [ ] ⚠️ Shareholder activity test negativo
- [ ] ⚠️ Duplicate cost test negativo
- [ ] Servicios específicos identificados
- [ ] Beneficio directo demostrable
- [ ] Método de asignación razonable
- [ ] Documentación robusta contemporánea

## 7. Checklist TIP-05: Servicios Profesionales

### Documentos Obligatorios

| # | Documento | Responsable | Validador | Estado |
|---|-----------|-------------|-----------|--------|
| 1 | Contrato de prestación de servicios | {{RESP_CONTRATO}} | A4_LEGAL | ☐ |
| 2 | Propuesta de servicios | {{RESP_PROPUESTA}} | A1_SPONSOR | ☐ |
| 3 | Credenciales del profesional/firma | {{RESP_CREDENCIALES}} | A6_PROVEEDOR | ☐ |
| 4 | Alcance y entregables | {{RESP_ALCANCE}} | A2_PMO | ☐ |

### Evidencias de Materialidad

| # | Evidencia | Frecuencia | Formato |
|---|-----------|------------|---------|
| 1 | Entregables recibidos | Por hito | Según contrato |
| 2 | Comunicaciones de trabajo | Continuo | Email/mensajes |
| 3 | Reportes de avance | {{FREC_AVANCE}} | Documento |
| 4 | Actas de entrega | Por entregable | PDF firmado |

## 8. Matriz de Documentación Cruzada

| Documento | TIP-01 | TIP-02 | TIP-03 | TIP-04 | TIP-05 |
|-----------|--------|--------|--------|--------|--------|
| Contrato firmado | ✓ | ✓ | ✓ | ✓ | ✓ |
| Estudio PT | - | - | ✓ | ✓ | - |
| BEE cuantificado | ✓ | ✓ | ✓ | ✓ | ✓ |
| CVs/Credenciales | ✓ | - | ✓ | ✓ | ✓ |
| Comparativo mercado | ✓ | ✓ | ✓ | ✓ | ✓ |
| Minutas/Actas | ✓ | - | ✓ | ✓ | ✓ |
| Entregables | ✓ | ✓ | ✓ | ✓ | ✓ |
| Logs/Reportes uso | - | ✓ | - | - | - |

## 9. Umbrales de Riesgo por Tipología

| Tipología | Monto Bajo | Monto Medio | Monto Alto | Monto Crítico |
|-----------|------------|-------------|------------|---------------|
| TIP-01 | < {{UMBRAL_01_BAJO}} | {{UMBRAL_01_MEDIO}} | {{UMBRAL_01_ALTO}} | > {{UMBRAL_01_CRITICO}} |
| TIP-02 | < {{UMBRAL_02_BAJO}} | {{UMBRAL_02_MEDIO}} | {{UMBRAL_02_ALTO}} | > {{UMBRAL_02_CRITICO}} |
| TIP-03 | < {{UMBRAL_03_BAJO}} | {{UMBRAL_03_MEDIO}} | {{UMBRAL_03_ALTO}} | > {{UMBRAL_03_CRITICO}} |
| TIP-04 | < {{UMBRAL_04_BAJO}} | {{UMBRAL_04_MEDIO}} | {{UMBRAL_04_ALTO}} | > {{UMBRAL_04_CRITICO}} |
| TIP-05 | < {{UMBRAL_05_BAJO}} | {{UMBRAL_05_MEDIO}} | {{UMBRAL_05_ALTO}} | > {{UMBRAL_05_CRITICO}} |

