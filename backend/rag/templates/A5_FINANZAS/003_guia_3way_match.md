---
tipo: guia_3way_match
version: "1.0"
agente: A5_FINANZAS
instrucciones: "Esta guía establece el procedimiento estándar para la conciliación 3-Way Match. Aplique estos controles a todas las transacciones de servicios intangibles."
---

# Guía de Conciliación 3-Way Match

## 1. Objetivo

Establecer el procedimiento para la conciliación de tres vías (3-Way Match) que valida la consistencia entre la Orden de Compra (PO), la Recepción del Servicio y la Factura del proveedor, asegurando que solo se paguen servicios autorizados y efectivamente recibidos.

## 2. Alcance

Este procedimiento aplica a:
- Todos los servicios profesionales e intangibles
- Contratos con valor superior a ${{MONTO_MINIMO_3WAY}} {{MONEDA}}
- Todos los proveedores de servicios externos

**Excepciones (requieren autorización de {{ROL_AUTORIZADOR_EXCEPCION}}):**
- Servicios de emergencia documentados
- Montos menores a ${{MONTO_MINIMO_3WAY}}
- {{EXCEPCION_ADICIONAL}}

## 3. Componentes del 3-Way Match

### 3.1 Documento 1: Orden de Compra (PO)

| Campo | Descripción | Validación |
|-------|-------------|------------|
| Número de PO | Identificador único | Formato: {{FORMATO_PO}} |
| Proveedor | Razón social y RFC | Verificado contra padrón |
| Descripción | Detalle del servicio | Coincide con contrato |
| Monto | Valor sin IVA | Dentro de presupuesto |
| Fecha | Fecha de emisión | Dentro de vigencia |
| Autorizaciones | Firmas requeridas | Completas según matriz |

### 3.2 Documento 2: Recepción de Servicio

| Campo | Descripción | Validación |
|-------|-------------|------------|
| Número de Recepción | Identificador único | Formato: {{FORMATO_RECEPCION}} |
| Referencia a PO | Número de PO relacionado | Debe existir PO válida |
| Descripción | Servicio recibido | Coincide con PO |
| Fecha de recepción | Fecha efectiva | Dentro de vigencia PO |
| Cantidad/Monto | Valor recibido | ≤ Valor de PO |
| Responsable | Quien recibe | Autorizado para recibir |
| Evidencia | Documentos soporte | Según tipo de servicio |

### 3.3 Documento 3: Factura (CFDI)

| Campo | Descripción | Validación |
|-------|-------------|------------|
| UUID | Folio fiscal | Válido en SAT |
| Emisor | RFC proveedor | Coincide con PO |
| Receptor | RFC cliente | Correcto |
| Concepto | Descripción servicio | Coincide con PO/Recepción |
| Monto | Subtotal | ≤ Monto recibido |
| Fecha | Fecha de emisión | Posterior a recepción |
| Forma de pago | Método acordado | Según contrato |

## 4. Proceso de Conciliación

### 4.1 Diagrama de Flujo

```
[PO Emitida] → [Servicio Prestado] → [Recepción Registrada] → [Factura Recibida]
                                            ↓
                                    [3-Way Match]
                                    ↙    ↓    ↘
                            [Match]  [Parcial]  [No Match]
                               ↓         ↓          ↓
                           [Pago]   [Revisión]  [Rechazo]
```

### 4.2 Pasos del Proceso

| Paso | Actividad | Responsable | Sistema | SLA |
|------|-----------|-------------|---------|-----|
| 1 | Registrar recepción de servicio | {{ROL_RECEPCION}} | {{SISTEMA_RECEPCION}} | {{SLA_RECEPCION}} días |
| 2 | Recibir factura del proveedor | {{ROL_RECEPCION_FACTURA}} | {{SISTEMA_FACTURAS}} | N/A |
| 3 | Validar factura vs SAT | {{ROL_VALIDACION}} | {{SISTEMA_VALIDACION}} | {{SLA_VALIDACION}} horas |
| 4 | Ejecutar conciliación 3-Way | {{ROL_CONCILIACION}} | {{SISTEMA_CONCILIACION}} | {{SLA_CONCILIACION}} días |
| 5 | Resolver discrepancias | {{ROL_RESOLUCION}} | Manual | {{SLA_RESOLUCION}} días |
| 6 | Aprobar para pago | {{ROL_APROBACION_PAGO}} | {{SISTEMA_PAGOS}} | {{SLA_APROBACION}} días |
| 7 | Ejecutar pago | {{ROL_TESORERIA}} | {{SISTEMA_TESORERIA}} | Según términos |

## 5. Criterios de Conciliación

### 5.1 Criterios de Match Exacto

Para que el match sea automático, deben coincidir:

| Elemento | Criterio | Tolerancia |
|----------|----------|------------|
| Número de PO | Exacto | 0% |
| Proveedor (RFC) | Exacto | 0% |
| Monto (subtotal) | Dentro de tolerancia | ±{{TOLERANCIA_MONTO}}% |
| Cantidad (unidades) | Exacta | 0 |
| Descripción | Sustancialmente igual | N/A |

### 5.2 Tolerancias Permitidas

| Concepto | Tolerancia | Autorización Adicional |
|----------|------------|----------------------|
| Diferencia de monto | ≤ ${{TOLERANCIA_MONTO_ABS}} o {{TOLERANCIA_MONTO_PCT}}% | No requerida |
| Diferencia de monto | > ${{TOLERANCIA_MONTO_ABS}} y ≤ {{TOLERANCIA_MONTO_MAX}}% | {{AUTORIZADOR_TOLERANCIA_1}} |
| Diferencia de monto | > {{TOLERANCIA_MONTO_MAX}}% | {{AUTORIZADOR_TOLERANCIA_2}} |
| Tipo de cambio | ±{{TOLERANCIA_TC}}% | Automático |
| Redondeos | ≤ ${{TOLERANCIA_REDONDEO}} | Automático |

### 5.3 Reglas de Conciliación por Tipo de Servicio

| Tipo de Servicio | Elementos Adicionales a Validar | Evidencia Requerida |
|------------------|--------------------------------|---------------------|
| Consultoría | Horas facturadas vs reportadas | Timesheets |
| Desarrollo TI | Entregables vs contrato | Actas de aceptación |
| Marketing | Métricas de campaña | Reportes de desempeño |
| Capacitación | Asistentes y horas | Listas de asistencia |
| {{TIPO_SERVICIO_ADICIONAL}} | {{VALIDACION_ADICIONAL}} | {{EVIDENCIA_ADICIONAL}} |

## 6. Manejo de Discrepancias

### 6.1 Tipos de Discrepancias

| Código | Discrepancia | Causa Común | Resolución |
|--------|--------------|-------------|------------|
| D-01 | Monto mayor a PO | Trabajos adicionales | Modificar PO o rechazar excedente |
| D-02 | Monto mayor a recepción | Error en recepción | Corregir recepción o devolver factura |
| D-03 | Servicio no recibido | Factura anticipada | Retener hasta recepción |
| D-04 | PO no encontrada | Error de referencia | Solicitar corrección al proveedor |
| D-05 | Datos fiscales incorrectos | Error del proveedor | Solicitar sustitución de CFDI |
| D-06 | Factura duplicada | Error administrativo | Rechazar duplicado |
| D-07 | Proveedor diferente | Subcontratación | Verificar autorización |

### 6.2 Proceso de Resolución

| Paso | Actividad | Responsable | Plazo |
|------|-----------|-------------|-------|
| 1 | Identificar discrepancia | Sistema/{{ROL_IDENTIFICACION}} | Automático |
| 2 | Notificar a involucrados | Sistema | Inmediato |
| 3 | Investigar causa raíz | {{ROL_INVESTIGACION}} | {{PLAZO_INVESTIGACION}} días |
| 4 | Proponer solución | {{ROL_INVESTIGACION}} | {{PLAZO_PROPUESTA}} días |
| 5 | Aprobar solución | {{ROL_APROBADOR_SOLUCION}} | {{PLAZO_APROBACION_SOLUCION}} días |
| 6 | Implementar corrección | {{ROL_IMPLEMENTACION}} | {{PLAZO_IMPLEMENTACION}} días |
| 7 | Documentar resolución | {{ROL_DOCUMENTACION}} | {{PLAZO_DOCUMENTACION}} días |

### 6.3 Escalamiento

| Nivel | Condición | Escalamiento a | Plazo de Respuesta |
|-------|-----------|----------------|-------------------|
| 1 | Discrepancia no resuelta en {{PLAZO_NIVEL_1}} días | {{ESCALAMIENTO_1}} | {{RESPUESTA_1}} días |
| 2 | Sin resolución después de escalamiento 1 | {{ESCALAMIENTO_2}} | {{RESPUESTA_2}} días |
| 3 | Impacto mayor a ${{MONTO_NIVEL_3}} | {{ESCALAMIENTO_3}} | {{RESPUESTA_3}} días |

## 7. Controles y Validaciones

### 7.1 Validaciones Automáticas

| Validación | Descripción | Acción si Falla |
|------------|-------------|-----------------|
| RFC en padrón SAT | Verificar que proveedor no esté en 69-B | Bloquear pago |
| CFDI válido | Consulta a servicio del SAT | Rechazar factura |
| PO activa | Verificar estatus de la PO | No procesar |
| Presupuesto disponible | Verificar partida presupuestal | Alertar |
| Duplicados | Detectar facturas duplicadas | Rechazar |
| Fechas consistentes | Recepción ≥ Inicio PO, Factura ≥ Recepción | Alertar |

### 7.2 Validaciones Manuales

| Validación | Responsable | Frecuencia |
|------------|-------------|------------|
| Revisión de evidencia de servicio | {{ROL_REVISION_EVIDENCIA}} | Cada transacción |
| Verificación de calidad del entregable | {{ROL_VERIFICACION_CALIDAD}} | Por entregable |
| Confirmación de precios de mercado | {{ROL_VERIFICACION_PRECIOS}} | Contratos nuevos |
| Auditoría de muestra | {{ROL_AUDITORIA_MUESTRA}} | {{FRECUENCIA_AUDITORIA}} |

## 8. Reportes y Monitoreo

### 8.1 KPIs del Proceso

| Indicador | Fórmula | Meta | Frecuencia |
|-----------|---------|------|------------|
| % Match automático | Matches auto / Total × 100 | ≥ {{META_MATCH_AUTO}}% | Semanal |
| Tiempo promedio de conciliación | Suma días / Núm transacciones | ≤ {{META_TIEMPO_CONCILIACION}} días | Semanal |
| % Discrepancias | Discrepancias / Total × 100 | ≤ {{META_DISCREPANCIAS}}% | Semanal |
| Tiempo resolución discrepancias | Promedio días resolución | ≤ {{META_TIEMPO_RESOLUCION}} días | Mensual |
| Facturas rechazadas | Rechazadas / Recibidas × 100 | ≤ {{META_RECHAZOS}}% | Mensual |

### 8.2 Reportes Estándar

| Reporte | Contenido | Frecuencia | Destinatarios |
|---------|-----------|------------|---------------|
| Estatus de conciliación | Transacciones pendientes | {{FRECUENCIA_ESTATUS}} | {{DESTINATARIOS_ESTATUS}} |
| Antigüedad de pendientes | Aging de facturas | {{FRECUENCIA_ANTIGUEDAD}} | {{DESTINATARIOS_ANTIGUEDAD}} |
| Discrepancias abiertas | Detalle de excepciones | {{FRECUENCIA_DISCREPANCIAS}} | {{DESTINATARIOS_DISCREPANCIAS}} |
| Dashboard ejecutivo | KPIs consolidados | {{FRECUENCIA_DASHBOARD}} | {{DESTINATARIOS_DASHBOARD}} |

## 9. Documentación y Archivo

### 9.1 Expediente por Transacción

Cada transacción debe mantener:

```
/TRANSACCION_{{NUMERO_PO}}/
├── 01_PO/
│   ├── orden_compra.pdf
│   └── autorizaciones/
├── 02_RECEPCION/
│   ├── acta_recepcion.pdf
│   └── evidencia/
├── 03_FACTURA/
│   ├── cfdi.xml
│   ├── pdf_factura.pdf
│   └── validacion_sat.pdf
├── 04_CONCILIACION/
│   ├── reporte_match.pdf
│   └── discrepancias/ (si aplica)
└── 05_PAGO/
    ├── autorizacion_pago.pdf
    └── comprobante_pago.pdf
```

### 9.2 Período de Conservación

| Documento | Período | Fundamento |
|-----------|---------|------------|
| Órdenes de compra | {{CONSERVACION_PO}} años | Art. 30 CFF |
| Recepciones | {{CONSERVACION_RECEPCION}} años | Art. 30 CFF |
| CFDIs | {{CONSERVACION_CFDI}} años | Art. 30 CFF |
| Expediente completo | {{CONSERVACION_EXPEDIENTE}} años | Política interna |

## 10. Roles y Responsabilidades

### 10.1 Matriz RACI

| Actividad | Solicitante | Compras | Finanzas | Proveedor |
|-----------|-------------|---------|----------|-----------|
| Emisión de PO | I | R/A | C | I |
| Recepción de servicio | R/A | I | I | I |
| Validación de factura | I | C | R/A | I |
| Conciliación 3-Way | I | I | R/A | - |
| Resolución discrepancias | C | C | R/A | C |
| Aprobación de pago | I | C | R/A | I |
| Ejecución de pago | - | - | R/A | I |

**R** = Responsable, **A** = Aprobador, **C** = Consultado, **I** = Informado

### 10.2 Contactos Clave

| Rol | Nombre | Email | Teléfono |
|-----|--------|-------|----------|
| Coordinador 3-Way Match | {{NOMBRE_COORDINADOR}} | {{EMAIL_COORDINADOR}} | {{TEL_COORDINADOR}} |
| Escalamiento Nivel 1 | {{NOMBRE_ESCAL_1}} | {{EMAIL_ESCAL_1}} | {{TEL_ESCAL_1}} |
| Escalamiento Nivel 2 | {{NOMBRE_ESCAL_2}} | {{EMAIL_ESCAL_2}} | {{TEL_ESCAL_2}} |

---

*Este procedimiento es obligatorio para todas las transacciones dentro del alcance definido. Las excepciones deben ser autorizadas y documentadas.*
