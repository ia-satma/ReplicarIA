---
tipo: normativo
version: "1.0"
agente: A3_FISCAL
instrucciones: "Guía para evaluar el cumplimiento de requisitos de deducción conforme al Artículo 27 de la Ley del Impuesto Sobre la Renta. Aplica a todas las deducciones por servicios intangibles."
---

# Requisitos de Deducción – Artículo 27 LISR

## 1. Marco Normativo

### Artículo 27 de la Ley del ISR

El Artículo 27 LISR establece los **requisitos generales** que deben cumplir las deducciones autorizadas. Para servicios intangibles, los principales son:

1. **Estrictamente indispensables** para los fines de la actividad
2. Deducción **efectivamente erogada** en el ejercicio
3. Comprobada con **CFDI** que cumpla requisitos fiscales
4. Pagos mayores a $2,000 mediante **transferencia electrónica**
5. Registro correcto en **contabilidad**
6. Cumplir requisitos específicos según tipo de gasto

## 2. Requisito de Estricta Indispensabilidad

### Definición

Un gasto es **estrictamente indispensable** cuando:

> "Es necesario para el desarrollo de las actividades del contribuyente y sin el cual no podrían llevarse a cabo dichas actividades de manera óptima."

### Criterios de Evaluación

| Criterio | Pregunta Clave | Evidencia |
|----------|----------------|-----------|
| Necesidad | ¿El servicio es necesario para operar? | {{EVIDENCIA_NECESIDAD}} |
| Conexión | ¿Existe relación directa con la actividad? | {{EVIDENCIA_CONEXION}} |
| Razonabilidad | ¿El monto es razonable vs beneficio? | {{EVIDENCIA_RAZONABILIDAD}} |
| Proporcionalidad | ¿Es proporcional a las operaciones? | {{EVIDENCIA_PROPORCIONALIDAD}} |

### Test de Indispensabilidad

```
┌─────────────────────────────────────────────────────────────┐
│              TEST DE ESTRICTA INDISPENSABILIDAD             │
├─────────────────────────────────────────────────────────────┤
│ Proyecto: {{ID_PROYECTO}}                                   │
│ Servicio: {{TIPO_SERVICIO}}                                 │
│ Monto:    {{MONTO_OPERACION}}                               │
├─────────────────────────────────────────────────────────────┤
│ 1. ¿Sin este servicio, la operación del negocio se vería   │
│    afectada negativamente?                                  │
│    Respuesta: {{RESPUESTA_1}}                               │
│                                                             │
│ 2. ¿El servicio contribuye directamente a generar          │
│    ingresos o reducir costos operativos?                    │
│    Respuesta: {{RESPUESTA_2}}                               │
│                                                             │
│ 3. ¿El servicio está relacionado con el objeto social      │
│    de la empresa?                                           │
│    Respuesta: {{RESPUESTA_3}}                               │
│                                                             │
│ 4. ¿Se puede justificar el monto en relación al            │
│    beneficio obtenido?                                      │
│    Respuesta: {{RESPUESTA_4}}                               │
├─────────────────────────────────────────────────────────────┤
│ RESULTADO: {{RESULTADO_TEST}}                               │
└─────────────────────────────────────────────────────────────┘
```

## 3. Requisitos Documentales (Fracción III)

### Requisitos del CFDI

| Requisito | Especificación | Validación |
|-----------|----------------|------------|
| RFC Emisor | Válido y activo | ☐ Verificado en SAT |
| RFC Receptor | Correcto del contribuyente | ☐ Coincide |
| Descripción | Detallada del servicio | ☐ Suficiente |
| Código SAT | Correcto para el servicio | ☐ {{CODIGO_SAT}} |
| Uso CFDI | Apropiado para deducción | ☐ {{USO_CFDI}} |
| Método de pago | PUE o PPD según corresponda | ☐ {{METODO_PAGO}} |
| Forma de pago | Conforme a operación | ☐ {{FORMA_PAGO}} |

### Documentación Complementaria Obligatoria

| Documento | Requisito | Fundamento |
|-----------|-----------|------------|
| Contrato | Servicios > {{UMBRAL_CONTRATO}} | Art. 27 Fr. III |
| Orden de compra | Trazabilidad | Mejores prácticas |
| Acta de entrega | Servicios prestados | Art. 27 Fr. I |
| Estado de cuenta | Pago bancarizado | Art. 27 Fr. III |

## 4. Requisito de Pago (Fracción VIII)

### Formas de Pago Permitidas

| Forma | Límite | Requisitos |
|-------|--------|------------|
| Transferencia electrónica | Sin límite | Desde cuenta del contribuyente |
| Cheque nominativo | Sin límite | Para abono en cuenta |
| Tarjeta de crédito/débito | Sin límite | A nombre del contribuyente |
| Efectivo | ≤ $2,000 MXN | Solo operaciones menores |

### Verificación de Pago

```
══════════════════════════════════════════════════════════════
               VERIFICACIÓN DE PAGO – Art. 27 Fr. VIII
══════════════════════════════════════════════════════════════
CFDI relacionado:     {{FOLIO_CFDI}}
Monto total:          {{MONTO_CFDI}}
══════════════════════════════════════════════════════════════

DETALLE DE PAGOS:

Pago 1:
├── Fecha:            {{FECHA_PAGO_1}}
├── Monto:            {{MONTO_PAGO_1}}
├── Forma:            {{FORMA_PAGO_1}}
├── Referencia:       {{REFERENCIA_1}}
├── Cuenta origen:    {{CUENTA_ORIGEN_1}}
└── Cuenta destino:   {{CUENTA_DESTINO_1}}

Pago 2 (si aplica):
├── Fecha:            {{FECHA_PAGO_2}}
├── Monto:            {{MONTO_PAGO_2}}
├── Forma:            {{FORMA_PAGO_2}}
├── Referencia:       {{REFERENCIA_2}}
├── Cuenta origen:    {{CUENTA_ORIGEN_2}}
└── Cuenta destino:   {{CUENTA_DESTINO_2}}

TOTAL PAGADO:         {{TOTAL_PAGADO}}
DIFERENCIA:           {{DIFERENCIA}}
ESTATUS:              {{ESTATUS_PAGO}}
══════════════════════════════════════════════════════════════
```

## 5. Requisitos por Tipo de Servicio

### 5.1 Servicios de Consultoría

| Requisito Específico | Fundamento | Verificación |
|---------------------|------------|--------------|
| Descripción detallada en contrato | Art. 27 Fr. I | ☐ |
| Entregables definidos | Art. 27 Fr. I | ☐ |
| CVs de consultores (si aplica) | Materialidad | ☐ |
| Reportes de avance | Materialidad | ☐ |

### 5.2 Servicios de Software/Licenciamiento

| Requisito Específico | Fundamento | Verificación |
|---------------------|------------|--------------|
| Licencia documentada | Art. 27 Fr. I | ☐ |
| Período de uso | Art. 27 Fr. IV | ☐ |
| Usuarios autorizados | Materialidad | ☐ |
| Código SAT correcto | Art. 29-A CFF | ☐ |

### 5.3 Servicios Intragrupo

| Requisito Específico | Fundamento | Verificación |
|---------------------|------------|--------------|
| Estudio de precios de transferencia | Art. 76 Fr. IX | ☐ |
| Contrato intercompañía | Art. 27 Fr. I | ☐ |
| Metodología de asignación | Art. 76 LISR | ☐ |
| Beneficio demostrable | Art. 27 Fr. I | ☐ |

### 5.4 Regalías

| Requisito Específico | Fundamento | Verificación |
|---------------------|------------|--------------|
| Registro de propiedad intelectual | Art. 27 Fr. I | ☐ |
| Contrato de licencia | Art. 27 Fr. I | ☐ |
| Retención ISR (si aplica) | Art. 153-154 LISR | ☐ |
| Base de cálculo de regalía | Materialidad | ☐ |

## 6. Gastos No Deducibles Relacionados

### Partidas Expresamente No Deducibles (Art. 28 LISR)

| Concepto | Fracción | Aplicación |
|----------|----------|------------|
| Gastos sin requisitos fiscales | I | Todo servicio sin CFDI válido |
| Pagos a paraísos fiscales | XXIII | Servicios de REFIPRES |
| Pagos a EFOS | I, XVII | Proveedores en lista 69-B |
| Gastos de representación | V | Limitaciones específicas |
| Gastos personales | I | Sin relación con actividad |

## 7. Matriz de Deducibilidad

### Análisis de Deducibilidad

| Criterio | Peso | Cumple | Score |
|----------|------|--------|-------|
| Estrictamente indispensable | 25% | {{CUMPLE_INDISPENSABLE}} | {{SCORE_INDISPENSABLE}} |
| CFDI con requisitos | 20% | {{CUMPLE_CFDI}} | {{SCORE_CFDI}} |
| Pago bancarizado | 20% | {{CUMPLE_PAGO}} | {{SCORE_PAGO}} |
| Registro contable | 15% | {{CUMPLE_CONTABLE}} | {{SCORE_CONTABLE}} |
| Documentación soporte | 20% | {{CUMPLE_SOPORTE}} | {{SCORE_SOPORTE}} |
| **TOTAL** | 100% | - | **{{SCORE_TOTAL}}** |

### Umbrales de Deducibilidad

| Rango | Nivel | Dictamen |
|-------|-------|----------|
| 90-100 | Óptimo | ✅ Totalmente deducible |
| 75-89 | Aceptable | ⚠️ Deducible con observaciones |
| 60-74 | Riesgoso | ⚠️ Deducibilidad cuestionable |
| < 60 | Crítico | ❌ No deducible / Alto riesgo |

## 8. Dictamen de Deducibilidad

```
══════════════════════════════════════════════════════════════
          DICTAMEN DE DEDUCIBILIDAD – Art. 27 LISR
══════════════════════════════════════════════════════════════
Proyecto:     {{ID_PROYECTO}}
Servicio:     {{TIPO_SERVICIO}}
Monto:        {{MONTO_OPERACION}}
Proveedor:    {{NOMBRE_PROVEEDOR}}
RFC:          {{RFC_PROVEEDOR}}
══════════════════════════════════════════════════════════════

SCORE DE DEDUCIBILIDAD: {{SCORE_DEDUCIBILIDAD}}/100

RESULTADO: {{RESULTADO_DEDUCIBILIDAD}}

REQUISITOS CUMPLIDOS:
{{REQUISITOS_CUMPLIDOS}}

REQUISITOS PENDIENTES:
{{REQUISITOS_PENDIENTES}}

RIESGOS IDENTIFICADOS:
{{RIESGOS_DEDUCIBILIDAD}}

RECOMENDACIONES:
{{RECOMENDACIONES_DEDUCIBILIDAD}}
══════════════════════════════════════════════════════════════
```

