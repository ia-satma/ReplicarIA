---
tipo: metodologia
version: "1.0"
agente: A3_FISCAL
instrucciones: "Complete los campos {{}} para personalizar la política de verificación de proveedores en lista 69-B según los procedimientos de su organización."
---

# Política de Verificación Lista 69-B

## 1. Objetivo

Establecer el procedimiento obligatorio para verificar que los proveedores de la organización **no se encuentren en las listas del Artículo 69-B del CFF** antes de realizar operaciones comerciales.

## 2. Alcance

Esta política aplica a:
- Todas las operaciones de compra de bienes y servicios
- Contrataciones con cualquier proveedor nuevo
- Renovaciones de contratos existentes
- Pagos recurrentes a proveedores activos

## 3. Marco Normativo

### Artículo 69-B del CFF

El SAT publica listas de contribuyentes que:
- Emiten comprobantes que amparan operaciones inexistentes
- No han desvirtuado la presunción de operaciones simuladas

### Consecuencias de Operar con Proveedores en Lista

| Estado en Lista | Consecuencia para el Cliente |
|-----------------|------------------------------|
| Lista Presunta | Alerta preventiva |
| Lista Definitiva | CFDI sin efectos fiscales |
| Lista de Desvirtuados | Sin consecuencia |
| Sentencia Favorable | Sin consecuencia |

## 4. Procedimiento de Verificación

### 4.1 Verificación de Proveedor Nuevo

```
┌─────────────────────────────────────────────────────────────┐
│           FLUJO DE ALTA DE PROVEEDOR NUEVO                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐                                          │
│  │  SOLICITUD   │                                          │
│  │  DE ALTA     │                                          │
│  └──────┬───────┘                                          │
│         ▼                                                   │
│  ┌──────────────┐     ┌──────────────┐                     │
│  │ VERIFICACIÓN │────▶│   EN LISTA   │──▶ ❌ RECHAZAR      │
│  │    69-B      │     │  DEFINITIVA  │                     │
│  └──────┬───────┘     └──────────────┘                     │
│         ▼                                                   │
│  ┌──────────────┐     ┌──────────────┐                     │
│  │  LIMPIO O    │────▶│  EN LISTA    │──▶ ⚠️ ALERTA       │
│  │ DESVIRTUADO  │     │  PRESUNTA    │                     │
│  └──────┬───────┘     └──────────────┘                     │
│         ▼                                                   │
│  ┌──────────────┐                                          │
│  │     ALTA     │                                          │
│  │   APROBADA   │                                          │
│  └──────────────┘                                          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 Frecuencia de Verificación

| Tipo de Proveedor | Frecuencia | Responsable |
|-------------------|------------|-------------|
| Nuevo | Al momento de alta | {{RESP_ALTA}} |
| Recurrente | {{FRECUENCIA_RECURRENTE}} | {{RESP_RECURRENTE}} |
| Alto monto (> {{UMBRAL_ALTO_MONTO}}) | Previo a cada pago | {{RESP_ALTO_MONTO}} |
| Todos | Auditoría {{FRECUENCIA_AUDITORIA}} | {{RESP_AUDITORIA}} |

### 4.3 Fuentes de Consulta

**Portal SAT Oficial:**
- URL: https://www.sat.gob.mx/consultas/00000/consulta-de-los-listados-69-b
- Actualización: Periódica (verificar fecha)

**Campos a verificar:**

| Campo | Descripción | Acción |
|-------|-------------|--------|
| RFC | Registro Federal de Contribuyentes | Buscar exacto |
| Nombre/Razón Social | Denominación | Confirmar coincidencia |
| Estatus | Presunto/Definitivo/Desvirtuado | Determinar acción |
| Fecha publicación | Fecha de inclusión en lista | Verificar vigencia |

### 4.4 Registro de Verificación

```
══════════════════════════════════════════════════════════════
              FICHA DE VERIFICACIÓN 69-B
══════════════════════════════════════════════════════════════
Proveedor:        {{NOMBRE_PROVEEDOR}}
RFC:              {{RFC_PROVEEDOR}}
Fecha consulta:   {{FECHA_CONSULTA}}
Consultado por:   {{NOMBRE_CONSULTA}}
══════════════════════════════════════════════════════════════

RESULTADO DE CONSULTA:

☐ NO APARECE EN LISTAS - Proveedor limpio
☐ LISTA PRESUNTA - Alerta activa
☐ LISTA DEFINITIVA - OPERACIÓN BLOQUEADA
☐ DESVIRTUADO - Sin restricción
☐ SENTENCIA FAVORABLE - Sin restricción

Captura de pantalla: {{ARCHIVO_EVIDENCIA}}
Hash de evidencia:   {{HASH_EVIDENCIA}}

DECISIÓN:
{{DECISION_VERIFICACION}}

Autorizado por: {{AUTORIZADOR}}
══════════════════════════════════════════════════════════════
```

## 5. Acciones por Resultado

### 5.1 Proveedor Limpio

| Acción | Responsable | Plazo |
|--------|-------------|-------|
| Registrar verificación en expediente | {{RESP_REGISTRO}} | Inmediato |
| Aprobar alta/operación | {{RESP_APROBACION}} | {{PLAZO_APROBACION}} |
| Programar siguiente verificación | Sistema | Automático |

### 5.2 Proveedor en Lista Presunta

| Acción | Responsable | Plazo |
|--------|-------------|-------|
| Notificar a {{NOTIFICAR_PRESUNTA}} | {{RESP_NOTIFICACION}} | 24 horas |
| Solicitar aclaración al proveedor | {{RESP_ACLARACION}} | {{PLAZO_ACLARACION}} |
| Evaluar riesgo de continuar | {{RESP_EVALUACION}} | {{PLAZO_EVALUACION}} |
| Decisión documentada | {{COMITE_DECISION}} | {{PLAZO_DECISION}} |

**Evaluación de Riesgo para Lista Presunta:**

| Factor | Peso | Evaluación |
|--------|------|------------|
| Antigüedad de relación | {{PESO_ANTIGUEDAD}}% | {{EVAL_ANTIGUEDAD}} |
| Historial de operaciones | {{PESO_HISTORIAL}}% | {{EVAL_HISTORIAL}} |
| Materialidad demostrada | {{PESO_MATERIALIDAD}}% | {{EVAL_MATERIALIDAD}} |
| Monto en riesgo | {{PESO_MONTO}}% | {{EVAL_MONTO}} |
| Plazo desde publicación | {{PESO_PLAZO}}% | {{EVAL_PLAZO}} |

### 5.3 Proveedor en Lista Definitiva

| Acción | Responsable | Plazo |
|--------|-------------|-------|
| ⛔ BLOQUEAR OPERACIONES INMEDIATAMENTE | {{RESP_BLOQUEO}} | Inmediato |
| Notificar a {{NOTIFICAR_DEFINITIVA}} | {{RESP_NOTIFICACION}} | 24 horas |
| Revisar operaciones históricas | {{RESP_REVISION}} | {{PLAZO_REVISION}} |
| Preparar expediente de defensa | {{RESP_DEFENSA}} | {{PLAZO_DEFENSA}} |
| Consultar con asesor fiscal | {{ASESOR_FISCAL}} | {{PLAZO_ASESORIA}} |

**Protocolo de Emergencia:**

```
⚠️ ALERTA: PROVEEDOR EN LISTA DEFINITIVA 69-B

1. DETENER inmediatamente cualquier pago pendiente
2. NO UTILIZAR CFDIs de este proveedor
3. NOTIFICAR a:
   - {{NOTIFICAR_1}}
   - {{NOTIFICAR_2}}
   - {{NOTIFICAR_3}}
4. RECOPILAR toda evidencia de materialidad
5. CONVOCAR reunión de crisis en máximo 48 horas
```

## 6. Monitoreo Continuo

### 6.1 Sistema de Alertas

| Tipo de Alerta | Disparador | Destinatarios |
|----------------|------------|---------------|
| Nueva publicación SAT | Actualización de listas | {{DESTINATARIOS_NUEVA_PUB}} |
| Proveedor activo en lista | Match con base de proveedores | {{DESTINATARIOS_MATCH}} |
| Verificación vencida | Plazo cumplido | {{DESTINATARIOS_VENCIDA}} |
| Cambio de estatus | Presunto → Definitivo | {{DESTINATARIOS_CAMBIO}} |

### 6.2 Dashboard de Monitoreo

| Indicador | Meta | Frecuencia de Revisión |
|-----------|------|------------------------|
| % proveedores verificados | 100% | {{FREC_INDICADOR_1}} |
| Verificaciones vencidas | 0 | {{FREC_INDICADOR_2}} |
| Proveedores en lista presunta | Minimizar | {{FREC_INDICADOR_3}} |
| Tiempo promedio de verificación | < {{TIEMPO_META}} horas | {{FREC_INDICADOR_4}} |

## 7. Responsabilidades

### Matriz RACI

| Actividad | {{ROL_1}} | {{ROL_2}} | {{ROL_3}} | {{ROL_4}} |
|-----------|-----------|-----------|-----------|-----------|
| Verificación inicial | R | A | C | I |
| Verificación periódica | R | A | I | I |
| Decisión lista presunta | C | R | A | I |
| Bloqueo lista definitiva | R | R | A | I |
| Preparación de defensa | I | R | A | C |
| Auditoría del proceso | I | C | R | A |

**Leyenda:** R=Responsable, A=Aprobador, C=Consultado, I=Informado

## 8. Sanciones por Incumplimiento

### Internas

| Incumplimiento | Sanción |
|----------------|---------|
| No verificar proveedor nuevo | {{SANCION_1}} |
| Operar con proveedor en lista definitiva | {{SANCION_2}} |
| No documentar verificación | {{SANCION_3}} |
| No reportar alerta | {{SANCION_4}} |

### Fiscales

| Consecuencia | Impacto |
|--------------|---------|
| Rechazo de deducción | 100% del monto |
| ISR omitido | 30% del gasto rechazado |
| Recargos | {{TASA_RECARGOS}}% mensual |
| Multas | 55% - 75% del ISR |

## 9. Actualización de Política

| Aspecto | Frecuencia | Responsable |
|---------|------------|-------------|
| Revisión de política | {{FREC_REVISION_POLITICA}} | {{RESP_REVISION}} |
| Actualización de umbrales | {{FREC_UMBRALES}} | {{RESP_UMBRALES}} |
| Capacitación del personal | {{FREC_CAPACITACION}} | {{RESP_CAPACITACION}} |

**Última actualización:** {{FECHA_ULTIMA_ACTUALIZACION}}
**Próxima revisión:** {{FECHA_PROXIMA_REVISION}}
**Aprobado por:** {{APROBADOR_POLITICA}}

