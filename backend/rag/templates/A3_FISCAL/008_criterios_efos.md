---
tipo: metodologia
version: "1.0"
agente: A3_FISCAL
instrucciones: "Guía de indicadores de riesgo para detección de Empresas que Facturan Operaciones Simuladas (EFOS). Aplicar en evaluación de proveedores y operaciones."
---

# Criterios de Detección de EFOS

## 1. Introducción

Las **Empresas que Facturan Operaciones Simuladas (EFOS)** son contribuyentes que emiten comprobantes fiscales sin contar con los activos, personal, infraestructura o capacidad material para prestar los servicios o entregar los bienes amparados en dichos comprobantes.

Este documento establece los **criterios de detección** para identificar potenciales EFOS antes de realizar operaciones.

## 2. Definiciones

### EFOS (Empresas que Facturan Operaciones Simuladas)
Contribuyentes que emiten CFDI para amparar operaciones inexistentes.

### EDOS (Empresas que Deducen Operaciones Simuladas)
Contribuyentes que utilizan CFDI de EFOS para deducir gastos ficticios.

### Operación Simulada
Acto jurídico aparente que no corresponde a una transacción económica real.

## 3. Indicadores de Riesgo

### 3.1 Indicadores Estructurales (Alta Severidad)

| Indicador | Descripción | Score Riesgo |
|-----------|-------------|--------------|
| 🔴 Sin domicilio fiscal real | Domicilio virtual o inexistente | 25 |
| 🔴 Sin empleados registrados | 0 trabajadores en IMSS | 25 |
| 🔴 Antigüedad < 6 meses | Empresa recién constituida | 20 |
| 🔴 Sin activos fijos | Balance sin maquinaria/equipo | 20 |
| 🔴 Capital social mínimo | $50,000 MXN o menor | 15 |
| 🔴 Objeto social amplio | Puede facturar cualquier concepto | 15 |

### 3.2 Indicadores Operativos (Media-Alta Severidad)

| Indicador | Descripción | Score Riesgo |
|-----------|-------------|--------------|
| 🟠 Único cliente significativo | > 90% facturación a un cliente | 20 |
| 🟠 Facturación desproporcionada | Ventas >> capacidad operativa | 20 |
| 🟠 Sin gastos operativos | Nómina, renta, servicios = 0 | 20 |
| 🟠 Múltiples giros incompatibles | Servicios sin relación entre sí | 15 |
| 🟠 Cambios frecuentes de representante | > 2 cambios en 12 meses | 15 |
| 🟠 Sin presencia digital | Sin página web, LinkedIn, etc. | 10 |

### 3.3 Indicadores Financieros (Media Severidad)

| Indicador | Descripción | Score Riesgo |
|-----------|-------------|--------------|
| 🟡 Márgenes atípicos | > 80% margen bruto en servicios | 15 |
| 🟡 Pagos solo en efectivo | Preferencia por cash | 15 |
| 🟡 Sin cuentas bancarias activas | Opera sin bancarización | 20 |
| 🟡 Facturación irregular | Picos inexplicables | 10 |
| 🟡 Precios muy bajos | < 50% del mercado | 15 |
| 🟡 Precios muy altos | > 150% del mercado | 15 |

### 3.4 Indicadores Documentales (Baja-Media Severidad)

| Indicador | Descripción | Score Riesgo |
|-----------|-------------|--------------|
| 🟢 Documentación incompleta | Falta de contratos, propuestas | 10 |
| 🟢 CFDI genéricos | "Servicios profesionales" sin detalle | 10 |
| 🟢 Sin referencias comerciales | No se pueden verificar antecedentes | 10 |
| 🟢 Comunicación solo por WhatsApp | Sin correo corporativo | 10 |
| 🟢 Representante no localizable | Difícil contactar | 15 |

## 4. Matriz de Evaluación de Riesgo EFOS

### Cálculo del Score de Riesgo

```
Score Total = Σ (Indicadores detectados × Peso)

Clasificación:
├── 0-25:   Riesgo Bajo      ✅ Proceder con precaución normal
├── 26-50:  Riesgo Medio     ⚠️ Verificación reforzada requerida
├── 51-75:  Riesgo Alto      🔶 Aprobación especial necesaria
└── 76+:    Riesgo Crítico   ❌ No proceder / Bloquear
```

### Formato de Evaluación

```
══════════════════════════════════════════════════════════════
              EVALUACIÓN DE RIESGO EFOS
══════════════════════════════════════════════════════════════
Proveedor:        {{NOMBRE_PROVEEDOR}}
RFC:              {{RFC_PROVEEDOR}}
Fecha evaluación: {{FECHA_EVALUACION}}
Evaluador:        {{EVALUADOR}}
══════════════════════════════════════════════════════════════

INDICADORES ESTRUCTURALES:
☐ Sin domicilio fiscal real                    [_25_]
☐ Sin empleados registrados                    [_25_]
☐ Antigüedad < 6 meses                         [_20_]
☐ Sin activos fijos                            [_20_]
☐ Capital social mínimo                        [_15_]
☐ Objeto social amplio                         [_15_]
                                    Subtotal: [____]

INDICADORES OPERATIVOS:
☐ Único cliente significativo                  [_20_]
☐ Facturación desproporcionada                 [_20_]
☐ Sin gastos operativos                        [_20_]
☐ Múltiples giros incompatibles               [_15_]
☐ Cambios frecuentes de representante         [_15_]
☐ Sin presencia digital                        [_10_]
                                    Subtotal: [____]

INDICADORES FINANCIEROS:
☐ Márgenes atípicos                            [_15_]
☐ Pagos solo en efectivo                       [_15_]
☐ Sin cuentas bancarias activas               [_20_]
☐ Facturación irregular                        [_10_]
☐ Precios fuera de mercado                     [_15_]
                                    Subtotal: [____]

INDICADORES DOCUMENTALES:
☐ Documentación incompleta                     [_10_]
☐ CFDI genéricos                               [_10_]
☐ Sin referencias comerciales                  [_10_]
☐ Comunicación informal                        [_10_]
☐ Representante no localizable                [_15_]
                                    Subtotal: [____]

══════════════════════════════════════════════════════════════
                    SCORE TOTAL: [______]
              NIVEL DE RIESGO:   [__________]
══════════════════════════════════════════════════════════════
```

## 5. Procedimiento de Verificación Detallada

### 5.1 Verificaciones Obligatorias

| Verificación | Fuente | Responsable |
|--------------|--------|-------------|
| Lista 69-B SAT | Portal SAT | {{RESP_69B}} |
| Constancia de situación fiscal | SAT/Proveedor | {{RESP_CSF}} |
| Opinión de cumplimiento | Portal SAT | {{RESP_OPINION}} |
| Verificación de domicilio | Física/Google Maps | {{RESP_DOMICILIO}} |
| Búsqueda en IMSS | Portal IMSS | {{RESP_IMSS}} |

### 5.2 Verificaciones Recomendadas

| Verificación | Fuente | Cuándo Aplicar |
|--------------|--------|----------------|
| Acta constitutiva | Proveedor/RPP | Operaciones > {{UMBRAL_ACTA}} |
| Estados financieros | Proveedor | Operaciones > {{UMBRAL_EDOS}} |
| Referencias comerciales | Otros clientes | Proveedor nuevo |
| Visita a instalaciones | Presencial | Riesgo medio-alto |
| Due diligence completo | Tercero especializado | Riesgo alto |

### 5.3 Checklist de Due Diligence

```
┌─────────────────────────────────────────────────────────────┐
│              DUE DILIGENCE ANTI-EFOS                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ DOCUMENTOS SOLICITADOS:                                     │
│ ☐ Acta constitutiva                                        │
│ ☐ Poder del representante legal                            │
│ ☐ Identificación oficial del representante                 │
│ ☐ Constancia de situación fiscal vigente                   │
│ ☐ Opinión de cumplimiento positiva                         │
│ ☐ Comprobante de domicilio fiscal                          │
│ ☐ Estados financieros último ejercicio                     │
│ ☐ Currículum empresarial                                   │
│ ☐ Referencias comerciales (mínimo 3)                       │
│                                                             │
│ VERIFICACIONES REALIZADAS:                                  │
│ ☐ Consulta lista 69-B SAT                                  │
│ ☐ Verificación de RFC activo                               │
│ ☐ Validación de domicilio (Google Maps/Visita)             │
│ ☐ Consulta de trabajadores IMSS                            │
│ ☐ Búsqueda en medios/internet                              │
│ ☐ Verificación de referencias                              │
│ ☐ Análisis de capacidad operativa                          │
│                                                             │
│ RESULTADO: ☐ Aprobado  ☐ Rechazado  ☐ Condicionado         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 6. Señales de Alerta Durante la Operación

### Red Flags Post-Contratación

| Señal | Acción Inmediata |
|-------|------------------|
| Cambio de cuenta bancaria | Verificar y documentar |
| Solicitud de pago en efectivo | Rechazar / Escalar |
| Facturación anticipada sin entrega | No pagar |
| Incomunicación prolongada | Investigar |
| Cambio de representante legal | Re-verificar |
| Modificación de domicilio fiscal | Re-verificar |
| Quejas de otros proveedores | Investigar |

### Monitoreo Continuo

| Aspecto | Frecuencia | Herramienta |
|---------|------------|-------------|
| Lista 69-B | {{FREC_MONITOREO_69B}} | {{HERRAMIENTA_69B}} |
| Estatus RFC | {{FREC_MONITOREO_RFC}} | {{HERRAMIENTA_RFC}} |
| Opinión cumplimiento | {{FREC_MONITOREO_OPINION}} | {{HERRAMIENTA_OPINION}} |
| Alertas de mercado | Continuo | {{HERRAMIENTA_ALERTAS}} |

## 7. Acciones por Nivel de Riesgo

### Riesgo Bajo (0-25)

- ✅ Proceder con contratación normal
- Documentar verificación realizada
- Programar monitoreo periódico

### Riesgo Medio (26-50)

- ⚠️ Solicitar documentación adicional
- Verificar referencias comerciales
- Considerar visita a instalaciones
- Aprobación de {{APROBADOR_MEDIO}}

### Riesgo Alto (51-75)

- 🔶 Realizar due diligence completo
- Visita obligatoria a instalaciones
- Validar capacidad operativa
- Aprobación de {{APROBADOR_ALTO}}
- Condiciones especiales de pago

### Riesgo Crítico (76+)

- ❌ NO PROCEDER con la operación
- Documentar razones del rechazo
- Buscar proveedor alternativo
- Reportar a {{REPORTE_CRITICO}}

## 8. Documentación de Evaluación

### Expediente Mínimo

| Documento | Retención | Formato |
|-----------|-----------|---------|
| Ficha de evaluación EFOS | {{RETENCION_FICHA}} años | PDF |
| Constancia de situación fiscal | {{RETENCION_CSF}} años | PDF |
| Evidencia de verificación 69-B | {{RETENCION_69B}} años | Screenshot + hash |
| Due diligence (si aplica) | {{RETENCION_DD}} años | PDF |
| Aprobación documentada | {{RETENCION_APROBACION}} años | Email/Firma |

### Control de Versiones

| Versión | Fecha | Cambios | Aprobó |
|---------|-------|---------|--------|
| {{VERSION_1}} | {{FECHA_V1}} | {{CAMBIOS_V1}} | {{APROBO_V1}} |
| {{VERSION_2}} | {{FECHA_V2}} | {{CAMBIOS_V2}} | {{APROBO_V2}} |
| {{VERSION_ACTUAL}} | {{FECHA_ACTUAL}} | Versión vigente | {{APROBO_ACTUAL}} |

## 9. Indicadores de Gestión

### KPIs del Proceso

| Indicador | Meta | Medición |
|-----------|------|----------|
| % proveedores evaluados | 100% | {{FRECUENCIA_KPI_1}} |
| Score promedio de riesgo | < {{META_SCORE}} | {{FRECUENCIA_KPI_2}} |
| Proveedores rechazados | Documentar 100% | {{FRECUENCIA_KPI_3}} |
| Tiempo de evaluación | < {{TIEMPO_EVALUACION}} horas | {{FRECUENCIA_KPI_4}} |
| Incidentes con EFOS | 0 | {{FRECUENCIA_KPI_5}} |

