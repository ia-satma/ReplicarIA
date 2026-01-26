---
id: 002_planeacion_okrs
agente: A1_ESTRATEGIA
tipo: plantilla
version: "1.0"
personalizable: true
campos_requeridos:
  - NOMBRE_EMPRESA
  - PERIODO
  - OKRS_CORPORATIVOS
  - OKRS_POR_AREA
---

# Planeación Estratégica OKRs {{PERIODO}}

## 1. Introducción

Este documento consolida los **Objetivos y Resultados Clave (OKRs)** definidos 
para {{NOMBRE_EMPRESA}} en el ejercicio {{PERIODO}}, alineados con la Visión y 
Pilares Estratégicos.

Su función es:
- Proveer un marco para evaluar si un proyecto de servicios/intangibles 
  contribuye a objetivos estratégicos específicos.
- Servir de referencia para formular y validar el **Beneficio Económico 
  Esperado (BEE)** de dichos proyectos.

## 2. OKRs Corporativos {{PERIODO}}

{{#each OKRS_CORPORATIVOS}}
### {{this.codigo}} – {{this.titulo}}

**Objetivo:** {{this.descripcion}}

| Key Result | Meta | Responsable |
|------------|------|-------------|
{{#each this.key_results}}
| {{this.id}} | {{this.meta}} | {{this.responsable}} |
{{/each}}

**Iniciativas vinculadas:**
{{#each this.iniciativas}}
- {{this}}
{{/each}}
{{/each}}

## 3. OKRs por Área

{{#each OKRS_POR_AREA}}
### {{this.area}}

**Código:** {{this.codigo}}
**Objetivo:** {{this.objetivo}}

**Key Results:**
{{#each this.key_results}}
- {{this.id}}: {{this.descripcion}} (Meta: {{this.meta}})
{{/each}}
{{/each}}

## 4. Relación OKRs ↔ BEE de Proyectos

Cada proyecto de servicio intangible debe indicar:
1. **Qué objetivo(s) apoya** (por ID de objetivo)
2. **El BEE en términos de OKRs** (impactos en ingresos, márgenes, 
   productividad, reducción de riesgos)

### Matriz de Vinculación

| Tipo de Servicio | OKRs Relacionados | Ejemplo de BEE |
|------------------|-------------------|----------------|
{{#each VINCULACIONES_TIPOLOGIA}}
| {{this.tipologia}} | {{this.okrs}} | {{this.bee_ejemplo}} |
{{/each}}

## 5. Revisión y Actualización

- **Frecuencia de revisión:** {{FRECUENCIA_REVISION}}
- **Responsable:** {{RESPONSABLE_OKRS}}
- **Próxima revisión:** {{FECHA_PROXIMA_REVISION}}
