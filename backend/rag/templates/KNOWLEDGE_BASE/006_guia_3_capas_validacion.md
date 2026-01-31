---
tipo: normativo_validacion
version: "1.0"
agente: KNOWLEDGE_BASE
instrucciones: "Guía de las 3 capas de validación fiscal que todos los agentes deben aplicar para evaluar la deducibilidad y defendibilidad de operaciones de servicios. Documento universal de referencia."
---

# Las 3 Capas de Validación Fiscal - REVISAR.IA

## Objetivo

Este documento establece el marco de validación de 3 capas que todos los agentes
deben aplicar para evaluar la deducibilidad y defendibilidad de operaciones de servicios.

---

## CAPA 1: FORMAL-FISCAL

### Normativa aplicable
- LISR 27 (Requisitos de deducciones)
- LIVA 5 (Acreditamiento IVA)
- CFF 28-29 (Contabilidad y CFDI)

### Checklist de validación

| # | Requisito | Evidencia mínima | Agente responsable |
|---|-----------|------------------|-------------------|
| 1.1 | CFDI válido | UUID verificado en SAT | A3_FISCAL |
| 1.2 | Descripción coherente | CFDI con descripción que coincide con contrato | A3_FISCAL |
| 1.3 | Clave producto/servicio | Clave SAT congruente con servicio prestado | A3_FISCAL |
| 1.4 | Pago bancarizado | Estado de cuenta con pago identificable | A5_FINANZAS |
| 1.5 | Registro contable | Póliza contable con CFDI vinculado | A5_FINANZAS |
| 1.6 | IVA trasladado | IVA expreso y separado en CFDI | A3_FISCAL |
| 1.7 | Proveedor válido | RFC activo, no en lista 69-B | A6_PROVEEDOR |
| 1.8 | Opinión 32-D | Positiva cuando aplica (gobierno/montos) | A6_PROVEEDOR |

### Resultado de CAPA 1
- **CUMPLE**: 8/8 requisitos OK
- **CUMPLE CON OBSERVACIONES**: 6-7/8 requisitos OK
- **NO CUMPLE**: <6/8 requisitos OK

---

## CAPA 2: MATERIALIDAD

### Normativa aplicable
- CFF 69-B (Operaciones inexistentes / EFOS)
- Jurisprudencia de materialidad

### Objetivo
Demostrar que el servicio REALMENTE se prestó, no solo existe el CFDI.

### Checklist de validación

| # | Requisito | Evidencia mínima | Agente responsable |
|---|-----------|------------------|-------------------|
| 2.1 | Contrato detallado | Contrato/SOW con alcance, métricas, entregables | A2_PMO |
| 2.2 | Órdenes de trabajo | SOW, actas de servicio por periodo | A2_PMO |
| 2.3 | Entregables | Informes, reportes, productos digitales | A2_PMO |
| 2.4 | Comunicación | Correos, tickets, logs de interacción | A2_PMO |
| 2.5 | Capacidad del proveedor | Web, empleados, infraestructura verificable | A6_PROVEEDOR |
| 2.6 | Uso en operación | Evidencia de que el servicio se usó en el negocio | A1_SPONSOR |

### Banderas rojas de materialidad
- Proveedor en lista 69-B (presunto o definitivo)
- Solo existe CFDI + contrato, sin más evidencia
- Proveedor sin infraestructura congruente con el servicio
- Servicios "intangibles" sin entregables documentados

### Resultado de CAPA 2
- **MATERIALIDAD FUERTE**: 6/6 requisitos con evidencia sólida
- **MATERIALIDAD DÉBIL**: 3-5/6 requisitos documentados
- **SIN MATERIALIDAD**: <3/6 requisitos, alto riesgo 69-B

---

## CAPA 3: RAZÓN DE NEGOCIOS

### Normativa aplicable
- CFF 5-A (Razón de negocios)
- Jurisprudencia relacionada

### Objetivo
Demostrar que la operación tiene propósito económico REAL más allá del beneficio fiscal.

### Preguntas clave a documentar

1. **¿Qué problema de negocio resuelve el servicio?**
   - Descripción clara del problema/necesidad
   - Situación antes del servicio

2. **¿Cuál habría sido el escenario SIN esta operación?**
   - Impacto en operaciones
   - Alternativas consideradas
   - Por qué se eligió esta opción

3. **¿El beneficio económico supera el beneficio fiscal?**
   - Cuantificación del BEE (Beneficio Económico Esperado)
   - Comparación con ahorro fiscal
   - Ratio BEE/BF > 1

### Checklist de validación

| # | Requisito | Evidencia mínima | Agente responsable |
|---|-----------|------------------|-------------------|
| 3.1 | Justificación interna | Memorandos, minutas, aprobaciones de proyecto | A1_SPONSOR |
| 3.2 | Análisis costo-beneficio | Documento de evaluación económica | A1_SPONSOR |
| 3.3 | Decisión documentada | Acta de consejo, email de aprobación | A1_SPONSOR |
| 3.4 | Vinculación con KPIs | Métricas de negocio afectadas | A5_FINANZAS |
| 3.5 | Hipótesis de negocio | Documento explicando la lógica de la operación | A1_SPONSOR |

### Resultado de CAPA 3
- **RN SÓLIDA**: 5/5 requisitos bien documentados, BEE > BF
- **RN DÉBIL**: 2-4/5 requisitos, BEE cercano a BF
- **SIN RN**: <2/5 requisitos, único beneficio visible es fiscal

---

## SEMÁFORO CONSOLIDADO

### Evaluación final de operación

| Color | Capa 1 | Capa 2 | Capa 3 | Dictamen |
|-------|--------|--------|--------|----------|
| VERDE | CUMPLE | MATERIALIDAD FUERTE | RN SÓLIDA | Deducible, defendible |
| AMARILLO | CUMPLE* | MATERIALIDAD DÉBIL | RN DÉBIL | Deducible con observaciones, documentar más |
| ROJO | NO CUMPLE | SIN MATERIALIDAD | SIN RN | No deducible / Alto riesgo auditoría |

*CUMPLE o CUMPLE CON OBSERVACIONES

### Acciones por color

**VERDE**
- Proceder con deducción
- Mantener expediente organizado
- Score defendibilidad: 85-100

**AMARILLO**
- Documentar evidencia adicional antes de deducir
- Alertar al cliente sobre gaps
- Score defendibilidad: 60-84
- Considerar reunión con cliente para fortalecer evidencia

**ROJO**
- NO DEDUCIR sin documentación adicional
- Alertar riesgo alto al cliente
- Score defendibilidad: <60
- Evaluar si se puede remediar antes de cierre fiscal

---

## USO POR AGENTES

| Agente | Capas que valida | Responsabilidad principal |
|--------|------------------|--------------------------|
| A1_SPONSOR | Capa 3 | Razón de negocios, BEE |
| A2_PMO | Capa 2 | Materialidad, entregables |
| A3_FISCAL | Capa 1 | Formal-fiscal, CFDI, LISR 27 |
| A5_FINANZAS | Capa 1, 3 | Pagos, contabilidad, KPIs |
| A6_PROVEEDOR | Capa 1, 2 | Due diligence proveedor |
| A7_DEFENSA | Todas | Consolidar para defensa fiscal |
| A8_AUDITOR | Todas | Verificación independiente |

---

## Tags relacionados

@3_CAPAS @VALIDACION @SEMAFORO @LISR_27 @CFF_69B @CFF_5A @MATERIALIDAD @RAZON_NEGOCIOS @DEDUCIBILIDAD
