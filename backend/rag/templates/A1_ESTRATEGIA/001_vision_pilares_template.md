---
id: 001_vision_pilares
agente: A1_ESTRATEGIA
tipo: plantilla
version: "1.0"
personalizable: true
campos_requeridos:
  - NOMBRE_EMPRESA
  - PERIODO
  - VISION_DESCRIPCION
  - MISION
  - PILARES
---

# Visión y Pilares Estratégicos {{PERIODO}}

## 1. Introducción

Este documento establece la **visión** y los **pilares estratégicos** de 
{{NOMBRE_EMPRESA}} para el periodo {{PERIODO}}.

## 2. Visión {{PERIODO}}

{{VISION_DESCRIPCION}}

### Mercados Clave
{{#each MERCADOS_CLAVE}}
- {{this}}
{{/each}}

### Segmentos Objetivo
{{#each SEGMENTOS_OBJETIVO}}
- {{this}}
{{/each}}

### Propuesta de Valor
{{PROPUESTA_VALOR}}

## 3. Misión / Propósito

{{MISION}}

### Principios de Ejecución
{{#each PRINCIPIOS_MISION}}
- {{this}}
{{/each}}

## 4. Pilares Estratégicos

{{#each PILARES}}
### {{this.numero}}. {{this.nombre}}

{{this.descripcion}}

**Objetivos clave:**
{{#each this.objetivos}}
- {{this}}
{{/each}}

**Métricas:**
{{#each this.metricas}}
- {{this}}
{{/each}}
{{/each}}

## 5. Metas de Alto Nivel {{PERIODO}}

| Categoría | Meta | Indicador |
|-----------|------|-----------|
{{#each METAS}}
| {{this.categoria}} | {{this.meta}} | {{this.indicador}} |
{{/each}}

## 6. Uso en Evaluación de Proyectos

Los proyectos de servicios/intangibles deben vincularse con al menos uno de los 
pilares estratégicos para demostrar **razón de negocios**.

### Criterios de Alineación
{{#each CRITERIOS_ALINEACION}}
- {{this}}
{{/each}}

Este documento sirve como **marco de referencia** para que, al evaluar proyectos 
de servicios e intangibles, se determine si están alineados con los objetivos y 
pilares estratégicos definidos.
