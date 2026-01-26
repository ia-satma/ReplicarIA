---
tipo: metodologia
version: "1.0"
agente: A2_PMO
instrucciones: "Guía de protocolos de comunicación y coordinación entre agentes del sistema. Define flujos de información y escalamiento."
---

# Guía de Coordinación Multiagente

## 1. Introducción

Esta guía establece los **protocolos de comunicación y coordinación** entre los agentes del sistema de evaluación de servicios intangibles. Su objetivo es:

- Definir flujos de información claros
- Establecer puntos de decisión y escalamiento
- Garantizar trazabilidad de interacciones
- Optimizar tiempos de respuesta

## 2. Arquitectura de Agentes

### Mapa de Agentes

| ID | Nombre | Rol Principal | Dependencias |
|----|--------|---------------|--------------|
| A1 | SPONSOR/Estrategia | Validación estratégica y BEE | Ninguna (Iniciador) |
| A2 | PMO | Coordinación y consolidación | Todos los agentes |
| A3 | FISCAL | Cumplimiento fiscal | A1, A6 |
| A4 | LEGAL | Cumplimiento legal | A3 |
| A5 | FINANZAS | Viabilidad financiera | A1, A3 |
| A6 | PROVEEDOR | Validación de proveedor | A3 |
| A7 | DEFENSA | Generación de expediente | Todos |

### Flujo de Comunicación Estándar

```
┌─────────┐    ┌─────────┐    ┌─────────┐
│   A1    │───▶│   A2    │───▶│   A3    │
│ SPONSOR │    │   PMO   │    │ FISCAL  │
└─────────┘    └────┬────┘    └────┬────┘
                    │              │
               ┌────▼────┐    ┌────▼────┐
               │   A5    │    │   A6    │
               │FINANZAS │    │PROVEEDOR│
               └────┬────┘    └────┬────┘
                    │              │
               ┌────▼────┐    ┌────▼────┐
               │   A4    │    │   A7    │
               │  LEGAL  │    │ DEFENSA │
               └─────────┘    └─────────┘
```

## 3. Protocolos de Comunicación

### 3.1 Formato de Mensaje Estándar

```json
{
  "id_mensaje": "{{ID_MENSAJE}}",
  "proyecto_id": "{{ID_PROYECTO}}",
  "agente_origen": "{{AGENTE_ORIGEN}}",
  "agente_destino": "{{AGENTE_DESTINO}}",
  "tipo_mensaje": "{{TIPO_MENSAJE}}",
  "prioridad": "{{PRIORIDAD}}",
  "contenido": {
    "accion_requerida": "{{ACCION}}",
    "datos": {},
    "documentos_adjuntos": []
  },
  "timestamp": "{{TIMESTAMP}}",
  "sla_respuesta": "{{SLA_HORAS}}"
}
```

### 3.2 Tipos de Mensaje

| Tipo | Descripción | SLA Estándar |
|------|-------------|--------------|
| SOLICITUD_EVALUACION | Solicita evaluación de agente | {{SLA_EVALUACION}} horas |
| RESPUESTA_DICTAMEN | Respuesta con dictamen | {{SLA_DICTAMEN}} horas |
| SOLICITUD_INFORMACION | Pide información adicional | {{SLA_INFO}} horas |
| ALERTA_BLOQUEO | Notifica candado duro | Inmediato |
| ESCALAMIENTO | Escala a nivel superior | {{SLA_ESCALAMIENTO}} horas |
| NOTIFICACION | Informativo sin acción | N/A |

### 3.3 Niveles de Prioridad

| Nivel | Código | SLA Reducción | Criterio |
|-------|--------|---------------|----------|
| Crítica | P1 | 75% | {{CRITERIO_P1}} |
| Alta | P2 | 50% | {{CRITERIO_P2}} |
| Normal | P3 | 0% | {{CRITERIO_P3}} |
| Baja | P4 | +50% | {{CRITERIO_P4}} |

## 4. Puntos de Decisión

### 4.1 Gates de Control

| Gate | Fase | Agentes Involucrados | Decisión |
|------|------|---------------------|----------|
| G1 | F1→F2 | A1, A2 | Procede a evaluación |
| G2 | F3→F4 | A3, A2 | Cumple requisitos fiscales |
| G3 | F5→F6 | A4, A2 | Contrato aprobado |
| G4 | F7→F8 | Todos | Aprobación consolidada |

### 4.2 Reglas de Consenso

**Unanimidad Requerida:**
- {{REGLA_UNANIMIDAD_1}}
- {{REGLA_UNANIMIDAD_2}}

**Mayoría Calificada (4/6):**
- {{REGLA_MAYORIA_1}}
- {{REGLA_MAYORIA_2}}

**Veto Individual:**
- A3 (Fiscal): Proveedor en lista 69-B
- A4 (Legal): Contrato sin cláusulas esenciales
- A5 (Finanzas): Monto supera {{UMBRAL_VETO_FINANZAS}}

## 5. Procedimientos de Escalamiento

### 5.1 Niveles de Escalamiento

| Nivel | Disparador | Responsable | Tiempo Máximo |
|-------|------------|-------------|---------------|
| N1 | SLA vencido | Agente origen | {{TIEMPO_N1}} |
| N2 | Conflicto entre agentes | A2_PMO | {{TIEMPO_N2}} |
| N3 | Bloqueo crítico | {{RESPONSABLE_N3}} | {{TIEMPO_N3}} |
| N4 | Decisión ejecutiva | {{RESPONSABLE_N4}} | {{TIEMPO_N4}} |

### 5.2 Matriz de Escalamiento

| Situación | Nivel | Acción |
|-----------|-------|--------|
| Dictámenes contradictorios | N2 | Reunión de deliberación |
| Información faltante >48h | N2 | Notificación a sponsor |
| Candado duro activado | N3 | Revisión por {{COMITE_REVISION}} |
| Monto > {{UMBRAL_EJECUTIVO}} | N4 | Aprobación ejecutiva |

## 6. Protocolos de Deliberación

### 6.1 Convocatoria

Cuando se requiere deliberación multiagente:

1. A2_PMO convoca con {{ANTICIPACION_MINIMA}} horas de anticipación
2. Agenda incluye:
   - Resumen del caso
   - Dictámenes de cada agente
   - Puntos de discrepancia
   - Documentación soporte

### 6.2 Formato de Deliberación

```
══════════════════════════════════════════════════════════════
              ACTA DE DELIBERACIÓN MULTIAGENTE
══════════════════════════════════════════════════════════════
Proyecto:     {{ID_PROYECTO}}
Fecha:        {{FECHA_DELIBERACION}}
Participantes: {{LISTA_PARTICIPANTES}}
══════════════════════════════════════════════════════════════

RESUMEN DEL CASO:
{{RESUMEN_CASO}}

POSICIONES POR AGENTE:
- A1: {{POSICION_A1}}
- A3: {{POSICION_A3}}
- A4: {{POSICION_A4}}
- A5: {{POSICION_A5}}
- A6: {{POSICION_A6}}

PUNTOS DE ACUERDO:
{{PUNTOS_ACUERDO}}

PUNTOS DE DESACUERDO:
{{PUNTOS_DESACUERDO}}

DECISIÓN FINAL:
{{DECISION_FINAL}}

VOTOS:
- A favor: {{VOTOS_FAVOR}}
- En contra: {{VOTOS_CONTRA}}
- Abstención: {{ABSTENCIONES}}
══════════════════════════════════════════════════════════════
```

## 7. Trazabilidad y Auditoría

### 7.1 Registro Obligatorio

Toda comunicación entre agentes debe registrar:
- ID único de mensaje
- Timestamp de envío y recepción
- Contenido completo
- Documentos adjuntos (hash SHA-256)
- Respuesta asociada

### 7.2 Retención de Registros

| Tipo | Retención Mínima |
|------|------------------|
| Mensajes operativos | {{RETENCION_OPERATIVO}} años |
| Dictámenes | {{RETENCION_DICTAMEN}} años |
| Actas de deliberación | {{RETENCION_ACTAS}} años |
| Expedientes completos | {{RETENCION_EXPEDIENTE}} años |

## 8. Indicadores de Desempeño

### KPIs de Coordinación

| Indicador | Meta | Medición |
|-----------|------|----------|
| Tiempo promedio de respuesta | < {{META_TIEMPO_RESPUESTA}} horas | Semanal |
| Tasa de cumplimiento SLA | > {{META_SLA}}% | Mensual |
| Escalamientos por proyecto | < {{META_ESCALAMIENTOS}} | Mensual |
| Tasa de retrabajos | < {{META_RETRABAJOS}}% | Trimestral |

