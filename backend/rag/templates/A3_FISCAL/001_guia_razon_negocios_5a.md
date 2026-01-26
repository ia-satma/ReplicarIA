---
tipo: normativo
version: "1.0"
agente: A3_FISCAL
instrucciones: "Guía para evaluar y documentar la razón de negocios conforme al Artículo 5-A del Código Fiscal de la Federación. Aplicar a toda operación de servicios intangibles."
---

# Guía de Razón de Negocios – Artículo 5-A CFF

## 1. Marco Normativo

### Artículo 5-A del Código Fiscal de la Federación

El Artículo 5-A CFF establece que los actos jurídicos que carezcan de una **razón de negocios** y que generen un beneficio fiscal directo o indirecto, tendrán los efectos fiscales que correspondan a los actos que sí hubieran tenido razón de negocios.

**Texto normativo clave:**
> "Los actos jurídicos que carezcan de una razón de negocios y que generen un beneficio fiscal directo o indirecto, tendrán los efectos fiscales que correspondan a los que se habrían realizado para la obtención del beneficio económico razonablemente esperado por el contribuyente."

### Definición de Razón de Negocios

La **razón de negocios** existe cuando el acto jurídico:
1. Genera un **beneficio económico razonablemente esperado**
2. Dicho beneficio es **cuantificable** y **presente o futuro**
3. El beneficio económico es **distinto del beneficio fiscal**

## 2. Criterios de Evaluación

### 2.1 Beneficio Económico Esperado (BEE)

El BEE debe ser:

| Criterio | Descripción | Evidencia Requerida |
|----------|-------------|---------------------|
| Real | Basado en hechos verificables | {{EVIDENCIA_REALIDAD}} |
| Cuantificable | Medible en términos económicos | {{EVIDENCIA_CUANTIFICACION}} |
| Razonable | Congruente con el giro del negocio | {{EVIDENCIA_RAZONABILIDAD}} |
| Documentado | Soportado antes de la operación | {{EVIDENCIA_DOCUMENTACION}} |

### 2.2 Sustancia Económica

La operación debe demostrar:

1. **Sustancia sobre forma:** La realidad económica prevalece sobre la forma jurídica
2. **Propósito comercial:** Existe una razón de negocio más allá del beneficio fiscal
3. **Flujo económico real:** Hay movimiento efectivo de recursos

### 2.3 Elementos Probatorios

| Elemento | Peso Probatorio | Documentación |
|----------|-----------------|---------------|
| Contrato | Alto | Contrato firmado con términos comerciales |
| Facturación | Alto | CFDIs correctamente timbrados |
| Pago | Alto | Transferencias bancarias rastreables |
| Entregables | Muy Alto | Evidencia física/digital del servicio |
| Comunicaciones | Medio | Correos, minutas, reportes |
| Beneficio demostrado | Muy Alto | Métricas de impacto |

## 3. Procedimiento de Análisis

### Paso 1: Identificación de la Operación

```
┌─────────────────────────────────────────────────────────────┐
│                 FICHA DE OPERACIÓN                          │
├─────────────────────────────────────────────────────────────┤
│ ID Proyecto:     {{ID_PROYECTO}}                            │
│ Tipo Servicio:   {{TIPO_SERVICIO}}                          │
│ Monto:           {{MONTO_OPERACION}}                        │
│ Proveedor:       {{NOMBRE_PROVEEDOR}}                       │
│ RFC Proveedor:   {{RFC_PROVEEDOR}}                          │
│ Periodo:         {{PERIODO_SERVICIO}}                       │
└─────────────────────────────────────────────────────────────┘
```

### Paso 2: Análisis de Razón de Negocios

**Cuestionario de Evaluación:**

| # | Pregunta | Respuesta | Evidencia |
|---|----------|-----------|-----------|
| 1 | ¿Cuál es el propósito comercial de la operación? | {{PROPOSITO_COMERCIAL}} | {{EVIDENCIA_1}} |
| 2 | ¿Qué beneficio económico específico se espera? | {{BEE_ESPERADO}} | {{EVIDENCIA_2}} |
| 3 | ¿El beneficio es cuantificable? | {{ES_CUANTIFICABLE}} | {{EVIDENCIA_3}} |
| 4 | ¿Se habría realizado la operación sin el beneficio fiscal? | {{SIN_BENEFICIO_FISCAL}} | {{EVIDENCIA_4}} |
| 5 | ¿Existe sustancia económica real? | {{SUSTANCIA_REAL}} | {{EVIDENCIA_5}} |

### Paso 3: Cuantificación del BEE

**Metodología de Cuantificación:**

| Tipo de BEE | Fórmula/Método | Ejemplo |
|-------------|----------------|---------|
| Incremento de ingresos | {{FORMULA_INGRESOS}} | {{EJEMPLO_INGRESOS}} |
| Reducción de costos | {{FORMULA_COSTOS}} | {{EJEMPLO_COSTOS}} |
| Eficiencia operativa | {{FORMULA_EFICIENCIA}} | {{EJEMPLO_EFICIENCIA}} |
| Mitigación de riesgos | {{FORMULA_RIESGOS}} | {{EJEMPLO_RIESGOS}} |
| Valor intangible | {{FORMULA_INTANGIBLE}} | {{EJEMPLO_INTANGIBLE}} |

**Matriz de Cuantificación:**

```
BEE Total = {{BEE_INGRESOS}} + {{BEE_COSTOS}} + {{BEE_EFICIENCIA}} + {{BEE_RIESGOS}}

BEE/Monto Operación = {{RATIO_BEE}} (debe ser > {{UMBRAL_MINIMO_BEE}}%)
```

### Paso 4: Documentación Contemporánea

La documentación debe prepararse **antes o durante** la operación, no después:

| Documento | Momento de Preparación | Contenido Clave |
|-----------|------------------------|-----------------|
| Estudio de necesidad | Antes del contrato | Justificación de la contratación |
| Propuesta comercial | Antes del contrato | Alcance, entregables, precio |
| Análisis costo-beneficio | Antes del contrato | Cuantificación de BEE |
| Contrato | Inicio de operación | Términos y condiciones |
| Plan de trabajo | Inicio de operación | Cronograma, responsables |
| Reportes de avance | Durante operación | Progreso, entregables |
| Evaluación final | Fin de operación | Cumplimiento, resultados |

## 4. Red Flags (Señales de Alerta)

### Indicadores de Ausencia de Razón de Negocios

| Red Flag | Descripción | Nivel de Riesgo |
|----------|-------------|-----------------|
| 🔴 Sin entregables tangibles | No hay evidencia de servicio prestado | Crítico |
| 🔴 BEE no cuantificado | No se puede medir el beneficio | Crítico |
| 🔴 Operación circular | Dinero regresa al pagador | Crítico |
| 🟠 Precio fuera de mercado | Muy alto o bajo vs comparables | Alto |
| 🟠 Proveedor sin capacidad | No puede prestar el servicio | Alto |
| 🟡 Documentación tardía | Generada después de operación | Medio |
| 🟡 Comunicaciones escasas | Poca interacción documentada | Medio |

## 5. Dictamen de Razón de Negocios

### Formato de Dictamen

```
══════════════════════════════════════════════════════════════
          DICTAMEN DE RAZÓN DE NEGOCIOS – Art. 5-A CFF
══════════════════════════════════════════════════════════════
Proyecto:          {{ID_PROYECTO}}
Fecha Evaluación:  {{FECHA_EVALUACION}}
Evaluador:         A3_FISCAL
══════════════════════════════════════════════════════════════

RESULTADO: {{RESULTADO_DICTAMEN}}

FUNDAMENTO:
{{FUNDAMENTO_DICTAMEN}}

SCORE DE RAZÓN DE NEGOCIOS: {{SCORE_RN}}/100

Componentes del Score:
├── Propósito comercial:    {{SCORE_PROPOSITO}}/25
├── BEE cuantificado:       {{SCORE_BEE}}/25
├── Sustancia económica:    {{SCORE_SUSTANCIA}}/25
└── Documentación:          {{SCORE_DOCUMENTACION}}/25

OBSERVACIONES:
{{OBSERVACIONES_DICTAMEN}}

RECOMENDACIONES:
{{RECOMENDACIONES_DICTAMEN}}
══════════════════════════════════════════════════════════════
```

## 6. Jurisprudencia y Precedentes Relevantes

### Criterios del SAT y PRODECON

| Criterio | Fuente | Aplicación |
|----------|--------|------------|
| {{CRITERIO_1}} | {{FUENTE_1}} | {{APLICACION_1}} |
| {{CRITERIO_2}} | {{FUENTE_2}} | {{APLICACION_2}} |
| {{CRITERIO_3}} | {{FUENTE_3}} | {{APLICACION_3}} |

### Tesis Relevantes

- **Tesis {{NUMERO_TESIS_1}}:** {{CONTENIDO_TESIS_1}}
- **Tesis {{NUMERO_TESIS_2}}:** {{CONTENIDO_TESIS_2}}

