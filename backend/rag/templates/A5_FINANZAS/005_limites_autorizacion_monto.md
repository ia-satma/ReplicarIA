---
tipo: limites_autorizacion_monto
version: "1.0"
agente: A5_FINANZAS
instrucciones: "Complete los campos {{}} con los montos y niveles de autorización de su empresa. Esta matriz debe mantenerse actualizada y comunicada a todos los niveles de la organización."
---

# Matriz de Autorización por Montos

## 1. Objetivo

Establecer los niveles de autorización requeridos para la aprobación de gastos e inversiones en servicios intangibles, asegurando un control adecuado según el monto y naturaleza de la transacción.

## 2. Alcance

**Empresa:** {{NOMBRE_EMPRESA}}
**Vigencia:** {{FECHA_VIGENCIA_INICIO}} al {{FECHA_VIGENCIA_FIN}}
**Aprobado por:** {{APROBADOR_MATRIZ}}
**Última actualización:** {{FECHA_ULTIMA_ACTUALIZACION}}

## 3. Matriz Principal de Autorización

### 3.1 Niveles de Autorización por Monto

| Nivel | Rango de Monto (MXN) | Autorizadores Requeridos | Documentación Mínima |
|-------|---------------------|--------------------------|---------------------|
| **1** | $0 - ${{LIMITE_N1}} | {{AUTORIZADOR_N1}} | Solicitud interna |
| **2** | ${{LIMITE_N1}} - ${{LIMITE_N2}} | {{AUTORIZADOR_N2_1}} + {{AUTORIZADOR_N2_2}} | Solicitud + Cotización |
| **3** | ${{LIMITE_N2}} - ${{LIMITE_N3}} | {{AUTORIZADOR_N3_1}} + {{AUTORIZADOR_N3_2}} + {{AUTORIZADOR_N3_3}} | Solicitud + 3 Cotizaciones + Business Case |
| **4** | ${{LIMITE_N3}} - ${{LIMITE_N4}} | {{AUTORIZADOR_N4_1}} + {{AUTORIZADOR_N4_2}} + {{AUTORIZADOR_N4_3}} | Nivel 3 + Análisis Financiero |
| **5** | > ${{LIMITE_N4}} | Comité de Dirección + Consejo | Nivel 4 + Presentación a Consejo |

### 3.2 Detalle de Autorizadores por Nivel

| Nivel | Cargo/Rol | Facultad | Límite Individual |
|-------|-----------|----------|-------------------|
| 1 | {{CARGO_N1}} | Primera firma | ${{LIMITE_INDIVIDUAL_N1}} |
| 2 | {{CARGO_N2_1}} | Primera firma | ${{LIMITE_INDIVIDUAL_N2_1}} |
| 2 | {{CARGO_N2_2}} | Segunda firma | ${{LIMITE_INDIVIDUAL_N2_2}} |
| 3 | {{CARGO_N3_1}} | Primera firma | ${{LIMITE_INDIVIDUAL_N3_1}} |
| 3 | {{CARGO_N3_2}} | Segunda firma | ${{LIMITE_INDIVIDUAL_N3_2}} |
| 3 | {{CARGO_N3_3}} | Tercera firma | ${{LIMITE_INDIVIDUAL_N3_3}} |
| 4 | {{CARGO_N4_1}} | Primera firma | ${{LIMITE_INDIVIDUAL_N4_1}} |
| 4 | {{CARGO_N4_2}} | Segunda firma | ${{LIMITE_INDIVIDUAL_N4_2}} |
| 4 | {{CARGO_N4_3}} | Tercera firma | ${{LIMITE_INDIVIDUAL_N4_3}} |
| 5 | Comité de Dirección | Colegiada | Sin límite |
| 5 | Consejo de Administración | Máxima autoridad | Sin límite |

## 4. Matrices Especializadas por Tipo de Gasto

### 4.1 Servicios de Consultoría

| Rango de Monto | Autorización Requerida | Requisitos Adicionales |
|----------------|----------------------|----------------------|
| $0 - ${{LIMITE_CONS_1}} | {{AUTORIZADOR_CONS_1}} | Contrato estándar |
| ${{LIMITE_CONS_1}} - ${{LIMITE_CONS_2}} | {{AUTORIZADOR_CONS_2}} | + Análisis de proveedor |
| ${{LIMITE_CONS_2}} - ${{LIMITE_CONS_3}} | {{AUTORIZADOR_CONS_3}} | + Comparativo de mercado |
| > ${{LIMITE_CONS_3}} | {{AUTORIZADOR_CONS_4}} | + Comité de Selección |

### 4.2 Servicios de Tecnología

| Rango de Monto | Autorización Requerida | Requisitos Adicionales |
|----------------|----------------------|----------------------|
| $0 - ${{LIMITE_TI_1}} | {{AUTORIZADOR_TI_1}} | Evaluación técnica |
| ${{LIMITE_TI_1}} - ${{LIMITE_TI_2}} | {{AUTORIZADOR_TI_2}} | + Seguridad informática |
| ${{LIMITE_TI_2}} - ${{LIMITE_TI_3}} | {{AUTORIZADOR_TI_3}} | + Arquitectura empresarial |
| > ${{LIMITE_TI_3}} | {{AUTORIZADOR_TI_4}} | + Comité de TI |

### 4.3 Servicios de Marketing

| Rango de Monto | Autorización Requerida | Requisitos Adicionales |
|----------------|----------------------|----------------------|
| $0 - ${{LIMITE_MKT_1}} | {{AUTORIZADOR_MKT_1}} | Brief aprobado |
| ${{LIMITE_MKT_1}} - ${{LIMITE_MKT_2}} | {{AUTORIZADOR_MKT_2}} | + Plan de medios |
| ${{LIMITE_MKT_2}} - ${{LIMITE_MKT_3}} | {{AUTORIZADOR_MKT_3}} | + ROI proyectado |
| > ${{LIMITE_MKT_3}} | {{AUTORIZADOR_MKT_4}} | + Comité Comercial |

### 4.4 Servicios Legales y Fiscales

| Rango de Monto | Autorización Requerida | Requisitos Adicionales |
|----------------|----------------------|----------------------|
| $0 - ${{LIMITE_LEG_1}} | {{AUTORIZADOR_LEG_1}} | Justificación de necesidad |
| ${{LIMITE_LEG_1}} - ${{LIMITE_LEG_2}} | {{AUTORIZADOR_LEG_2}} | + Alcance detallado |
| ${{LIMITE_LEG_2}} - ${{LIMITE_LEG_3}} | {{AUTORIZADOR_LEG_3}} | + Opinión de Jurídico interno |
| > ${{LIMITE_LEG_3}} | {{AUTORIZADOR_LEG_4}} | + Director General |

## 5. Autorizaciones Especiales

### 5.1 Partes Relacionadas

| Monto | Autorización Adicional | Documentación Extra |
|-------|----------------------|---------------------|
| Cualquier monto | {{AUTORIZADOR_PARTES_REL}} | Estudio de precios de transferencia |
| > ${{LIMITE_PR_1}} | Consejo de Administración | Opinión de auditor externo |

### 5.2 Contratos Plurianuales

| Plazo | Autorización Adicional |
|-------|----------------------|
| 1-2 años | Director de Área |
| 2-3 años | {{AUTORIZADOR_PLURIANUAL_2}} |
| > 3 años | Consejo de Administración |

### 5.3 Proveedores Nuevos (Sin Historial)

| Monto | Autorización Adicional | Requisitos |
|-------|----------------------|------------|
| Hasta ${{LIMITE_NUEVO_1}} | {{AUTORIZADOR_NUEVO_1}} | Due diligence básico |
| ${{LIMITE_NUEVO_1}} - ${{LIMITE_NUEVO_2}} | {{AUTORIZADOR_NUEVO_2}} | Due diligence completo |
| > ${{LIMITE_NUEVO_2}} | {{AUTORIZADOR_NUEVO_3}} | + Visita a instalaciones |

### 5.4 Servicios de Emergencia

| Monto | Autorización | Plazo de Regularización |
|-------|--------------|------------------------|
| Hasta ${{LIMITE_EMERGENCIA_1}} | {{AUTORIZADOR_EMERGENCIA_1}} | {{PLAZO_REG_1}} días |
| ${{LIMITE_EMERGENCIA_1}} - ${{LIMITE_EMERGENCIA_2}} | {{AUTORIZADOR_EMERGENCIA_2}} | {{PLAZO_REG_2}} días |
| > ${{LIMITE_EMERGENCIA_2}} | {{AUTORIZADOR_EMERGENCIA_3}} | {{PLAZO_REG_3}} días |

**Definición de emergencia:** {{DEFINICION_EMERGENCIA}}

## 6. Delegación de Facultades

### 6.1 Reglas de Delegación

| Regla | Descripción |
|-------|-------------|
| Delegación temporal | Requiere notificación escrita a {{AREA_NOTIFICACION}} |
| Plazo máximo | {{PLAZO_MAX_DELEGACION}} días |
| Nivel de delegación | Solo a nivel inmediato inferior |
| Monto delegable | Hasta {{PCT_DELEGABLE}}% del límite propio |

### 6.2 Delegaciones Vigentes

| Delegante | Delegado | Facultad | Monto Máximo | Vigencia |
|-----------|----------|----------|--------------|----------|
| {{DELEGANTE_1}} | {{DELEGADO_1}} | {{FACULTAD_1}} | ${{MONTO_DELEGADO_1}} | {{VIGENCIA_1}} |
| {{DELEGANTE_2}} | {{DELEGADO_2}} | {{FACULTAD_2}} | ${{MONTO_DELEGADO_2}} | {{VIGENCIA_2}} |

### 6.3 Suplencias Definidas

| Titular | Suplente 1 | Suplente 2 | Condición de Activación |
|---------|------------|------------|------------------------|
| {{TITULAR_1}} | {{SUPLENTE_1_1}} | {{SUPLENTE_1_2}} | Ausencia > {{DIAS_AUSENCIA}} días |
| {{TITULAR_2}} | {{SUPLENTE_2_1}} | {{SUPLENTE_2_2}} | Ausencia > {{DIAS_AUSENCIA}} días |
| {{TITULAR_3}} | {{SUPLENTE_3_1}} | {{SUPLENTE_3_2}} | Ausencia > {{DIAS_AUSENCIA}} días |

## 7. Proceso de Autorización

### 7.1 Flujo de Aprobación

```
[Solicitante] → [Validación Presupuestal] → [Autorizador(es)] → [Compras] → [Contrato]
                         ↓
                  [Sin presupuesto]
                         ↓
              [Solicitud de Adición]
                         ↓
              [Aprobación Adicional]
```

### 7.2 Tiempos de Respuesta (SLA)

| Nivel | Tiempo Máximo de Respuesta |
|-------|---------------------------|
| Nivel 1 | {{SLA_N1}} horas hábiles |
| Nivel 2 | {{SLA_N2}} días hábiles |
| Nivel 3 | {{SLA_N3}} días hábiles |
| Nivel 4 | {{SLA_N4}} días hábiles |
| Nivel 5 | Siguiente sesión de Comité/Consejo |

### 7.3 Escalamiento por Falta de Respuesta

| Tiempo Excedido | Acción | Notificación a |
|-----------------|--------|----------------|
| +50% del SLA | Recordatorio automático | Autorizador |
| +100% del SLA | Escalamiento | Superior inmediato |
| +150% del SLA | Escalamiento crítico | {{ESCALAMIENTO_CRITICO}} |

## 8. Controles y Auditoría

### 8.1 Controles Preventivos

| Control | Descripción | Responsable |
|---------|-------------|-------------|
| Segregación de funciones | Solicitante ≠ Autorizador | Sistema |
| Validación presupuestal | Verificar partida disponible | Finanzas |
| Límites en sistema | Bloqueo por exceso de facultad | Sistema |
| Verificación 69-B | Consulta automática antes de pago | Sistema |

### 8.2 Controles Detectivos

| Control | Frecuencia | Responsable |
|---------|------------|-------------|
| Revisión de autorizaciones | {{FRECUENCIA_REVISION_AUT}} | {{RESPONSABLE_REVISION_AUT}} |
| Muestra aleatoria de transacciones | {{FRECUENCIA_MUESTRA}} | Auditoría Interna |
| Verificación de delegaciones | {{FRECUENCIA_DELEGACIONES}} | {{RESPONSABLE_DELEGACIONES}} |

### 8.3 Indicadores de Control

| Indicador | Fórmula | Meta | Frecuencia |
|-----------|---------|------|------------|
| % Transacciones con autorización completa | Autorizadas correctamente / Total | {{META_AUT_COMPLETA}}% | Mensual |
| Tiempo promedio de autorización | Suma días / Transacciones | ≤ {{META_TIEMPO_AUT}} días | Mensual |
| % Excepciones a la política | Excepciones / Total | ≤ {{META_EXCEPCIONES}}% | Mensual |
| Transacciones sin presupuesto | Sin partida / Total | ≤ {{META_SIN_PRESUP}}% | Mensual |

## 9. Excepciones y Casos Especiales

### 9.1 Proceso de Excepción

| Paso | Actividad | Responsable |
|------|-----------|-------------|
| 1 | Solicitud formal de excepción | Solicitante |
| 2 | Justificación documentada | Solicitante |
| 3 | Opinión de Finanzas | {{ROL_OPINION_FIN}} |
| 4 | Aprobación de excepción | {{APROBADOR_EXCEPCIONES}} |
| 5 | Registro en bitácora | {{ROL_REGISTRO_EXCEPCIONES}} |

### 9.2 Criterios para Excepción

| Criterio | Aplica | No Aplica |
|----------|--------|-----------|
| Emergencia documentada | ✓ | |
| Oportunidad de mercado única | ✓ | |
| Requerimiento regulatorio urgente | ✓ | |
| Conveniencia administrativa | | ✗ |
| Evitar proceso de cotización | | ✗ |

## 10. Actualización y Vigencia

### 10.1 Proceso de Actualización

| Evento | Acción | Aprobación |
|--------|--------|------------|
| Cambio en estructura organizacional | Revisar autorizadores | {{APROBADOR_CAMBIOS_EST}} |
| Actualización de montos (anual) | Ajuste por inflación | {{APROBADOR_ACTUALIZACION}} |
| Cambio de política | Revisión completa | Consejo de Administración |

### 10.2 Comunicación de Cambios

| Cambio | Plazo de Comunicación | Medio |
|--------|----------------------|-------|
| Nuevos autorizadores | {{PLAZO_COM_AUTORIZADORES}} días previos | Correo + Sistema |
| Modificación de montos | {{PLAZO_COM_MONTOS}} días previos | Memorándum oficial |
| Cambio de política | {{PLAZO_COM_POLITICA}} días previos | Comunicación de Dirección |

## 11. Directorio de Autorizadores

| Nivel | Nombre | Cargo | Email | Teléfono |
|-------|--------|-------|-------|----------|
| 1 | {{NOMBRE_AUT_1}} | {{CARGO_AUT_1}} | {{EMAIL_AUT_1}} | {{TEL_AUT_1}} |
| 2 | {{NOMBRE_AUT_2}} | {{CARGO_AUT_2}} | {{EMAIL_AUT_2}} | {{TEL_AUT_2}} |
| 3 | {{NOMBRE_AUT_3}} | {{CARGO_AUT_3}} | {{EMAIL_AUT_3}} | {{TEL_AUT_3}} |
| 4 | {{NOMBRE_AUT_4}} | {{CARGO_AUT_4}} | {{EMAIL_AUT_4}} | {{TEL_AUT_4}} |
| 5 | {{NOMBRE_AUT_5}} | {{CARGO_AUT_5}} | {{EMAIL_AUT_5}} | {{TEL_AUT_5}} |

---

*Esta matriz debe ser revisada anualmente o cuando existan cambios organizacionales significativos.*
