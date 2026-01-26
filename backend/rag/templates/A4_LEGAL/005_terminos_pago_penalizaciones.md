---
tipo: terminos_pago_penalizaciones
version: "1.0"
agente: A4_LEGAL
instrucciones: "Seleccione y adapte las cláusulas de pago y penalización aplicables al tipo de contrato. Asegure consistencia con las políticas financieras de la empresa."
---

# Términos de Pago y Penalizaciones

## 1. Propósito

Este documento contiene cláusulas estándar para términos de pago, retenciones y penalizaciones en contratos de servicios intangibles. Las cláusulas están diseñadas para proteger los intereses del cliente mientras mantienen relaciones comerciales justas.

## 2. Datos del Contrato

**Número de Contrato:** {{NUMERO_CONTRATO}}
**Proveedor:** {{NOMBRE_PROVEEDOR}}
**RFC Proveedor:** {{RFC_PROVEEDOR}}
**Monto Total del Contrato:** ${{MONTO_TOTAL}} {{MONEDA}}
**Vigencia:** {{FECHA_INICIO}} al {{FECHA_TERMINO}}

## 3. Cláusulas de Condiciones de Pago

### 3.1 Esquema de Pago por Fases

> **CLÁUSULA [X]. ESTRUCTURA DE PAGOS**
>
> El monto total del contrato se pagará conforme al siguiente esquema:
>
> | Fase | Concepto | Porcentaje | Monto | Condición de Liberación |
> |------|----------|------------|-------|-------------------------|
> | 1 | Anticipo | {{PCT_ANTICIPO}}% | ${{MONTO_ANTICIPO}} | Firma del contrato y SOW |
> | 2 | {{FASE_2}} | {{PCT_FASE_2}}% | ${{MONTO_FASE_2}} | {{CONDICION_FASE_2}} |
> | 3 | {{FASE_3}} | {{PCT_FASE_3}}% | ${{MONTO_FASE_3}} | {{CONDICION_FASE_3}} |
> | 4 | {{FASE_4}} | {{PCT_FASE_4}}% | ${{MONTO_FASE_4}} | {{CONDICION_FASE_4}} |
> | 5 | Finiquito | {{PCT_FINIQUITO}}% | ${{MONTO_FINIQUITO}} | Aceptación final y cierre |
> | | **TOTAL** | 100% | ${{MONTO_TOTAL}} | |
>
> Cada pago estará condicionado a la entrega y aceptación formal de los entregables correspondientes.

### 3.2 Pago por Hitos (Milestones)

> **CLÁUSULA [X]. PAGO CONTRA ENTREGA DE HITOS**
>
> Los pagos se realizarán conforme al cumplimiento de los siguientes hitos:
>
> | Hito | Descripción | Fecha Objetivo | Monto | Criterio de Cumplimiento |
> |------|-------------|----------------|-------|--------------------------|
> | H1 | {{HITO_1}} | {{FECHA_H1}} | ${{MONTO_H1}} | {{CRITERIO_H1}} |
> | H2 | {{HITO_2}} | {{FECHA_H2}} | ${{MONTO_H2}} | {{CRITERIO_H2}} |
> | H3 | {{HITO_3}} | {{FECHA_H3}} | ${{MONTO_H3}} | {{CRITERIO_H3}} |
> | H4 | {{HITO_4}} | {{FECHA_H4}} | ${{MONTO_H4}} | {{CRITERIO_H4}} |
>
> La verificación de cumplimiento de cada hito será realizada por {{RESPONSABLE_VERIFICACION}}.

### 3.3 Pago por Tiempo y Materiales

> **CLÁUSULA [X]. ESQUEMA TIME & MATERIALS**
>
> Para proyectos bajo esquema de tiempo y materiales:
>
> **Tarifas por Hora/Día:**
>
> | Rol | Tarifa Hora | Tarifa Día | Horas Estimadas |
> |-----|-------------|------------|-----------------|
> | {{ROL_1}} | ${{TARIFA_HORA_1}} | ${{TARIFA_DIA_1}} | {{HORAS_EST_1}} |
> | {{ROL_2}} | ${{TARIFA_HORA_2}} | ${{TARIFA_DIA_2}} | {{HORAS_EST_2}} |
> | {{ROL_3}} | ${{TARIFA_HORA_3}} | ${{TARIFA_DIA_3}} | {{HORAS_EST_3}} |
>
> **Tope Máximo:** ${{MONTO_TOPE_MAXIMO}} ({{PORCENTAJE_CONTINGENCIA}}% de contingencia incluido)
>
> **Facturación:** {{FRECUENCIA_FACTURACION}} con reporte detallado de horas

## 4. Condiciones de Facturación

### 4.1 Requisitos de Facturación

> **CLÁUSULA [X]. REQUISITOS PARA FACTURACIÓN**
>
> Para procesar el pago, EL PRESTADOR deberá presentar:
>
> 1. **CFDI válido** con los siguientes datos:
>    - RFC Emisor: {{RFC_PROVEEDOR}}
>    - RFC Receptor: {{RFC_CLIENTE}}
>    - Uso de CFDI: {{USO_CFDI}}
>    - Método de Pago: {{METODO_PAGO}}
>    - Forma de Pago: {{FORMA_PAGO}}
>
> 2. **Documentación soporte:**
>    - Acta de aceptación del entregable correspondiente
>    - Reporte de actividades del período
>    - Evidencia de horas trabajadas (para T&M)
>
> 3. **Formato de factura:**
>    - Concepto detallado según contrato
>    - Referencia al número de contrato: {{NUMERO_CONTRATO}}
>    - Número de orden de compra: {{NUMERO_OC}}

### 4.2 Plazos de Pago

> **CLÁUSULA [X]. TÉRMINOS DE PAGO**
>
> EL CLIENTE realizará los pagos en los siguientes términos:
>
> | Tipo de Pago | Plazo | Contado a partir de |
> |--------------|-------|---------------------|
> | Facturas regulares | {{PLAZO_PAGO_REGULAR}} días | Recepción de factura válida |
> | Anticipo | {{PLAZO_ANTICIPO}} días | Firma del contrato |
> | Finiquito | {{PLAZO_FINIQUITO}} días | Aceptación final documentada |
>
> **Día de Corte:** {{DIA_CORTE}} de cada mes
> **Día de Pago:** {{DIA_PAGO}} del mes siguiente
>
> Las facturas recibidas después del día de corte se programarán para el siguiente período de pago.

## 5. Retenciones

### 5.1 Retención de Garantía

> **CLÁUSULA [X]. FONDO DE GARANTÍA**
>
> EL CLIENTE retendrá el {{PORCENTAJE_RETENCION_GARANTIA}}% de cada factura como fondo de garantía de cumplimiento.
>
> **Monto total de retención:** ${{MONTO_RETENCION_TOTAL}}
>
> **Liberación del fondo:**
> - {{PORCENTAJE_LIBERACION_1}}% al cumplir {{CONDICION_LIBERACION_1}}
> - {{PORCENTAJE_LIBERACION_2}}% al cumplir {{CONDICION_LIBERACION_2}}
> - Saldo restante al término del período de garantía
>
> **Período de garantía:** {{PERIODO_GARANTIA}} después de la aceptación final

### 5.2 Retenciones Fiscales

> **CLÁUSULA [X]. RETENCIONES DE LEY**
>
> EL CLIENTE realizará las siguientes retenciones conforme a disposiciones fiscales:
>
> | Concepto | Base | Tasa | Fundamento |
> |----------|------|------|------------|
> | ISR por servicios profesionales | Monto antes de IVA | {{TASA_ISR_RETENCION}}% | Art. 106 LISR |
> | IVA retenido (si aplica) | IVA facturado | {{TASA_IVA_RETENCION}}% | Art. 1-A LIVA |
>
> EL PRESTADOR expedirá la constancia de retenciones correspondiente en los plazos de ley.

## 6. Penalizaciones por Incumplimiento

### 6.1 Penalización por Retraso

> **CLÁUSULA [X]. PENAS POR MORA**
>
> En caso de retraso en la entrega de los servicios o entregables acordados:
>
> | Días de Retraso | Penalización | Aplicación |
> |-----------------|--------------|------------|
> | 1-{{DIAS_GRACIA}} días | Sin penalización | Período de gracia |
> | {{DIAS_GRACIA}}-{{DIAS_NIVEL_1}} días | {{PCT_PENALIZACION_1}}% del valor del entregable | Por entregable |
> | {{DIAS_NIVEL_1}}-{{DIAS_NIVEL_2}} días | {{PCT_PENALIZACION_2}}% del valor del entregable | Por entregable |
> | Más de {{DIAS_NIVEL_2}} días | Rescisión con causa | Todo el contrato |
>
> **Tope máximo de penalizaciones:** {{PCT_TOPE_PENALIZACIONES}}% del valor total del contrato
>
> Las penalizaciones se deducirán de la siguiente factura o del finiquito.

### 6.2 Penalización por Deficiencia en Calidad

> **CLÁUSULA [X]. INCUMPLIMIENTO DE CALIDAD**
>
> Cuando los entregables no cumplan con los criterios de aceptación acordados:
>
> 1. **Primera observación:** Plazo de {{DIAS_CORRECCION_1}} días hábiles para corrección sin costo
>
> 2. **Segunda observación:** Plazo de {{DIAS_CORRECCION_2}} días hábiles, descuento de {{PCT_DESCUENTO_CALIDAD}}% del entregable
>
> 3. **Tercera observación:** Rechazo del entregable y retención del pago asociado
>
> 4. **Incumplimiento sistemático:** Rescisión del contrato por causa justificada
>
> Los criterios de calidad están definidos en el Anexo {{NUMERO_ANEXO_CALIDAD}}.

### 6.3 Penalización por Cambio de Personal

> **CLÁUSULA [X]. ESTABILIDAD DEL EQUIPO**
>
> El cambio no autorizado de personal clave está sujeto a:
>
> | Tipo de Cambio | Consecuencia |
> |----------------|--------------|
> | Recurso clave sin aviso | Penalización de {{MONTO_PENALIZACION_CAMBIO}} |
> | Más de {{NUM_CAMBIOS}} cambios | Revisión de condiciones contractuales |
> | Cambio de Líder de Proyecto | Derecho a rescisión sin penalidad |
>
> Cualquier cambio de personal requiere notificación con {{DIAS_AVISO_CAMBIO}} días de anticipación y aprobación del cliente.

## 7. Causales de Rescisión

### 7.1 Rescisión por Incumplimiento

> **CLÁUSULA [X]. TERMINACIÓN ANTICIPADA POR CAUSA**
>
> EL CLIENTE podrá rescindir el contrato sin responsabilidad en los siguientes casos:
>
> 1. Retraso acumulado superior a {{DIAS_RETRASO_RESCISION}} días calendario
> 2. Incumplimiento reiterado en calidad ({{NUM_INCUMPLIMIENTOS}} o más rechazos)
> 3. Sustitución no autorizada de personal clave
> 4. Incumplimiento de obligaciones de confidencialidad
> 5. Aparición del PRESTADOR en listas de contribuyentes incumplidos (Art. 69-B CFF)
> 6. {{CAUSAL_RESCISION_ADICIONAL}}
>
> **Consecuencias de rescisión por causa:**
> - Retención de pagos pendientes hasta liquidación de penalizaciones
> - Aplicación del fondo de garantía
> - Derecho a indemnización por daños y perjuicios

### 7.2 Terminación por Conveniencia

> **CLÁUSULA [X]. TERMINACIÓN SIN CAUSA**
>
> Cualquiera de las partes podrá terminar el contrato por conveniencia con:
>
> - Notificación por escrito con {{DIAS_AVISO_TERMINACION}} días de anticipación
> - Pago proporcional por servicios efectivamente prestados
> - Entrega de trabajos en proceso
> - Sin aplicación de penalizaciones
>
> EL CLIENTE pagará los servicios prestados hasta la fecha de terminación efectiva.

## 8. Proceso de Reclamación

### 8.1 Procedimiento para Controversias de Pago

> **CLÁUSULA [X]. RESOLUCIÓN DE CONTROVERSIAS**
>
> En caso de disputa sobre montos o pagos:
>
> 1. **Notificación:** La parte afectada notifica por escrito la controversia
> 2. **Conciliación:** Reunión de conciliación en un plazo de {{DIAS_CONCILIACION}} días
> 3. **Escalamiento:** De no resolverse, escalar a {{NIVEL_ESCALAMIENTO}}
> 4. **Mediación:** Procedimiento de mediación ante {{MEDIADOR}}
> 5. **Arbitraje/Judicial:** En última instancia, según cláusula jurisdiccional
>
> Durante el proceso de controversia, los pagos no disputados continuarán sin interrupción.

## 9. Bonificaciones por Cumplimiento

### 9.1 Incentivos por Desempeño

> **CLÁUSULA [X]. BONIFICACIONES**
>
> EL PRESTADOR podrá hacerse acreedor a las siguientes bonificaciones:
>
> | Criterio | Bonificación | Condición |
> |----------|--------------|-----------|
> | Entrega anticipada | {{PCT_BONO_ANTICIPADO}}% del entregable | Mínimo {{DIAS_ANTICIPACION}} días antes |
> | Cumplimiento perfecto | {{PCT_BONO_CALIDAD}}% del finiquito | Cero rechazos en todo el proyecto |
> | Exceder KPIs | {{PCT_BONO_KPIS}}% del finiquito | Superar metas en {{PCT_EXCEDER}}% |
>
> Las bonificaciones se pagarán junto con el finiquito del proyecto.

## 10. Cláusulas Complementarias

### 10.1 Actualización de Tarifas

> **CLÁUSULA [X]. REVISIÓN DE PRECIOS**
>
> Para contratos con vigencia superior a {{MESES_REVISION}} meses:
>
> - Revisión anual de tarifas alineada a {{INDICE_REFERENCIA}}
> - Incremento máximo permitido: {{PCT_INCREMENTO_MAXIMO}}% anual
> - Notificación con {{DIAS_AVISO_INCREMENTO}} días de anticipación
> - Derecho a terminación si el incremento excede el máximo

### 10.2 Moneda y Tipo de Cambio

> **CLÁUSULA [X]. DISPOSICIONES MONETARIAS**
>
> - Moneda del contrato: {{MONEDA_CONTRATO}}
> - Tipo de cambio aplicable: {{TIPO_CAMBIO_REFERENCIA}}
> - Fecha de determinación: {{FECHA_TIPO_CAMBIO}}
> - Ajuste por variación cambiaria superior a {{PCT_VARIACION_TIPO_CAMBIO}}%

---

*Estas cláusulas son modelos de referencia. Adáptelas según las políticas financieras de la empresa y consulte con asesoría legal.*
