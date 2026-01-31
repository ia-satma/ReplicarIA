# [GUIA] Las 3 Capas de Validacion Fiscal - REVISAR.IA

## Objetivo

Este documento establece el marco de validacion de 3 capas que todos los agentes
deben aplicar para evaluar la deducibilidad y defendibilidad de operaciones de servicios.

---

## CAPA 1: FORMAL-FISCAL

### Normativa aplicable
- LISR 27 (Requisitos de deducciones)
- LIVA 5 (Acreditamiento IVA)
- CFF 28-29 (Contabilidad y CFDI)

### Checklist de validacion

| # | Requisito | Evidencia minima | Agente responsable |
|---|-----------|------------------|-------------------|
| 1.1 | CFDI valido | UUID verificado en SAT | A3_FISCAL |
| 1.2 | Descripcion coherente | CFDI con descripcion que coincide con contrato | A3_FISCAL |
| 1.3 | Clave producto/servicio | Clave SAT congruente con servicio prestado | A3_FISCAL |
| 1.4 | Pago bancarizado | Estado de cuenta con pago identificable | A5_FINANZAS |
| 1.5 | Registro contable | Poliza contable con CFDI vinculado | A5_FINANZAS |
| 1.6 | IVA trasladado | IVA expreso y separado en CFDI | A3_FISCAL |
| 1.7 | Proveedor valido | RFC activo, no en lista 69-B | A6_PROVEEDOR |
| 1.8 | Opinion 32-D | Positiva cuando aplica (gobierno/montos) | A6_PROVEEDOR |

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
Demostrar que el servicio REALMENTE se presto, no solo existe el CFDI.

### Checklist de validacion

| # | Requisito | Evidencia minima | Agente responsable |
|---|-----------|------------------|-------------------|
| 2.1 | Contrato detallado | Contrato/SOW con alcance, metricas, entregables | A2_PMO |
| 2.2 | Ordenes de trabajo | SOW, actas de servicio por periodo | A2_PMO |
| 2.3 | Entregables | Informes, reportes, productos digitales | A2_PMO |
| 2.4 | Comunicacion | Correos, tickets, logs de interaccion | A2_PMO |
| 2.5 | Capacidad del proveedor | Web, empleados, infraestructura verificable | A6_PROVEEDOR |
| 2.6 | Uso en operacion | Evidencia de que el servicio se uso en el negocio | A1_SPONSOR |

### Banderas rojas de materialidad
- Proveedor en lista 69-B (presunto o definitivo)
- Solo existe CFDI + contrato, sin mas evidencia
- Proveedor sin infraestructura congruente con el servicio
- Servicios "intangibles" sin entregables documentados

### Resultado de CAPA 2
- **MATERIALIDAD FUERTE**: 6/6 requisitos con evidencia solida
- **MATERIALIDAD DEBIL**: 3-5/6 requisitos documentados
- **SIN MATERIALIDAD**: <3/6 requisitos, alto riesgo 69-B

---

## CAPA 3: RAZON DE NEGOCIOS

### Normativa aplicable
- CFF 5-A (Razon de negocios)
- Jurisprudencia relacionada

### Objetivo
Demostrar que la operacion tiene proposito economico REAL mas alla del beneficio fiscal.

### Preguntas clave a documentar

1. **¿Que problema de negocio resuelve el servicio?**
   - Descripcion clara del problema/necesidad
   - Situacion antes del servicio

2. **¿Cual habria sido el escenario SIN esta operacion?**
   - Impacto en operaciones
   - Alternativas consideradas
   - Por que se eligio esta opcion

3. **¿El beneficio economico supera el beneficio fiscal?**
   - Cuantificacion del BEE (Beneficio Economico Esperado)
   - Comparacion con ahorro fiscal
   - Ratio BEE/BF > 1

### Checklist de validacion

| # | Requisito | Evidencia minima | Agente responsable |
|---|-----------|------------------|-------------------|
| 3.1 | Justificacion interna | Memorandos, minutas, aprobaciones de proyecto | A1_SPONSOR |
| 3.2 | Analisis costo-beneficio | Documento de evaluacion economica | A1_SPONSOR |
| 3.3 | Decision documentada | Acta de consejo, email de aprobacion | A1_SPONSOR |
| 3.4 | Vinculacion con KPIs | Metricas de negocio afectadas | A5_FINANZAS |
| 3.5 | Hipotesis de negocio | Documento explicando la logica de la operacion | A1_SPONSOR |

### Resultado de CAPA 3
- **RN SOLIDA**: 5/5 requisitos bien documentados, BEE > BF
- **RN DEBIL**: 2-4/5 requisitos, BEE cercano a BF
- **SIN RN**: <2/5 requisitos, unico beneficio visible es fiscal

---

## SEMAFORO CONSOLIDADO

### Evaluacion final de operacion

| Color | Capa 1 | Capa 2 | Capa 3 | Dictamen |
|-------|--------|--------|--------|----------|
| VERDE | CUMPLE | MATERIALIDAD FUERTE | RN SOLIDA | Deducible, defendible |
| AMARILLO | CUMPLE* | MATERIALIDAD DEBIL | RN DEBIL | Deducible con observaciones, documentar mas |
| ROJO | NO CUMPLE | SIN MATERIALIDAD | SIN RN | No deducible / Alto riesgo auditoria |

*CUMPLE o CUMPLE CON OBSERVACIONES

### Acciones por color

**VERDE**
- Proceder con deduccion
- Mantener expediente organizado
- Score defendibilidad: 85-100

**AMARILLO**
- Documentar evidencia adicional antes de deducir
- Alertar al cliente sobre gaps
- Score defendibilidad: 60-84
- Considerar reunion con cliente para fortalecer evidencia

**ROJO**
- NO DEDUCIR sin documentacion adicional
- Alertar riesgo alto al cliente
- Score defendibilidad: <60
- Evaluar si se puede remediar antes de cierre fiscal

---

## USO POR AGENTES

| Agente | Capas que valida | Responsabilidad principal |
|--------|------------------|--------------------------|
| A1_SPONSOR | Capa 3 | Razon de negocios, BEE |
| A2_PMO | Capa 2 | Materialidad, entregables |
| A3_FISCAL | Capa 1 | Formal-fiscal, CFDI, LISR 27 |
| A5_FINANZAS | Capa 1, 3 | Pagos, contabilidad, KPIs |
| A6_PROVEEDOR | Capa 1, 2 | Due diligence proveedor |
| A7_DEFENSA | Todas | Consolidar para defensa fiscal |
| A8_AUDITOR | Todas | Verificacion independiente |

---

## Tags relacionados

@3_CAPAS @VALIDACION @SEMAFORO @LISR_27 @CFF_69B @CFF_5A @MATERIALIDAD @RAZON_NEGOCIOS @DEDUCIBILIDAD
