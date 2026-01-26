---
id: 005_matriz_alineacion_bee
agente: A1_ESTRATEGIA
tipo: plantilla
version: "1.0"
personalizable: true
campos_requeridos:
  - NOMBRE_EMPRESA
  - TIPOLOGIAS_BEE
  - UMBRAL_REVISION
---

# Matriz de Alineación del Beneficio Económico Esperado (BEE)

## 1. Definición Interna de BEE

El **Beneficio Económico Esperado (BEE)** se define como:

> El conjunto de beneficios económicos razonablemente esperados de un proyecto 
> de servicio o intangible, medidos en términos de ahorros de costos, incremento 
> de ingresos, mitigación de riesgos relevantes, mejora de márgenes o 
> cumplimiento de requisitos indispensables para operar, **más allá de cualquier 
> efecto fiscal asociado**.

### Principios Clave
- El BEE debe **ir más allá del simple ahorro de impuestos**
- El BEE debe ser **documentable y cuantificable**
- El BEE debe **vincularse a objetivos estratégicos**

## 2. Estructura Estándar de BEE por Proyecto

Todo proyecto de servicio intangible debe completar:

### 2.1 Objetivo de Negocio
- **Pregunta:** ¿Qué problema de negocio resuelve este servicio?
- **Formato:** {{FORMATO_OBJETIVO_NEGOCIO}}

### 2.2 Tipo(s) de Beneficio Económico

| Tipo | Descripción | Aplica? |
|------|-------------|---------|
| Ahorro de costos | Reducción directa de gastos operativos | ☐ |
| Incremento de ingresos | Aumento en ventas o nuevos mercados | ☐ |
| Mitigación de riesgo | Reducción de exposición a pérdidas | ☐ |
| Cumplimiento obligatorio | Requerimiento legal o regulatorio | ☐ |
| Mejora de márgenes | Incremento en rentabilidad | ☐ |
| Eficiencia operativa | Optimización de procesos | ☐ |

### 2.3 Estimación Cuantitativa
- **Método de cálculo:** {{METODO_CALCULO_BEE}}
- **Rango esperado:** {{RANGO_BEE_DEFAULT}}
- **Horizonte temporal:** {{HORIZONTE_BEE_DEFAULT}}

### 2.4 Supuestos Principales
{{#each SUPUESTOS_EJEMPLO}}
{{@index}}. {{this}}
{{/each}}

### 2.5 Indicadores de Éxito (KPIs)

| KPI | Línea Base | Meta | Plazo |
|-----|------------|------|-------|
{{#each KPIS_EJEMPLO}}
| {{this.nombre}} | {{this.baseline}} | {{this.meta}} | {{this.plazo}} |
{{/each}}

## 3. Criterios de Evaluación del BEE

### BEE Sólido ✅
Un BEE se considera **sólido** cuando:
- ☐ El objetivo es concreto y entendible
- ☐ Hay cuantificación razonable (aunque sea por rangos)
- ☐ El horizonte temporal es congruente con el servicio
- ☐ Está vinculado a OKRs o pilares estratégicos
- ☐ Los supuestos son razonables y documentados

### BEE Débil ⚠️
Un BEE se considera **débil** si:
- ☐ Se describe en términos vagos ("mejorar eficiencia")
- ☐ Carece de aproximación cuantitativa
- ☐ No se puede vincular a objetivos estratégicos
- ☐ El horizonte es incongruente con el monto

### BEE Rechazable ❌
Un BEE se considera **rechazable** si:
- ☐ El único beneficio es ahorro fiscal
- ☐ No hay razón de negocios identificable
- ☐ Los supuestos son irreales o no documentados

## 4. Matriz de Alineación por Tipología

| Tipología | OKRs Típicos | BEE Esperado | Umbral Mínimo |
|-----------|--------------|--------------|---------------|
{{#each TIPOLOGIAS_BEE}}
| {{this.tipologia}} | {{this.okrs}} | {{this.bee}} | {{this.umbral}} |
{{/each}}

## 5. Relación con Art. 5-A CFF

La Matriz BEE:
- **Demuestra razón de negocios** más allá del beneficio fiscal
- **Documenta propósito económico** de la contratación
- **Establece métricas verificables** de éxito
- **Crea trazabilidad** para auditorías SAT

### Preguntas Clave (Test 5-A CFF)
{{#each PREGUNTAS_5A}}
{{@index}}. {{this.pregunta}} {{this.respuesta}}
{{/each}}

## 6. Proceso de Aprobación

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Solicitante    │ ──▶ │  Revisar.ia     │ ──▶ │  Aprobación     │
│  completa BEE   │     │  evalúa con     │     │  Estrategia +   │
│                 │     │  agentes A1-A5  │     │  Finanzas       │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

Todo servicio > ${{UMBRAL_REVISION}} requiere validación de BEE antes de 
contratación.
