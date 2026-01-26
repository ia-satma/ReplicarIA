---
id: 004_plan_estrategico_anual
agente: A1_ESTRATEGIA
tipo: plantilla
version: "1.0"
personalizable: true
campos_requeridos:
  - NOMBRE_EMPRESA
  - PERIODO
  - PRIORIDADES
  - PROYECTOS_ESTRATEGICOS
---

# Plan Estratégico Anual – {{PERIODO}}

## 1. Objetivo del Documento

Describir las **líneas de acción prioritarias** y los **proyectos estratégicos** 
de {{NOMBRE_EMPRESA}} para el ejercicio {{PERIODO}}, para alinear:
- Decisiones de inversión
- Contratación de servicios e intangibles
- Recursos humanos y financieros

## 2. Prioridades Estratégicas {{PERIODO}}

{{#each PRIORIDADES}}
### Prioridad {{this.numero}}: {{this.nombre}}

- **Descripción:** {{this.descripcion}}
- **Áreas involucradas:** {{this.areas}}
- **Presupuesto estimado:** {{this.presupuesto}}
- **Servicios requeridos:** {{this.servicios}}
{{/each}}

## 3. Mapa de Proyectos Estratégicos

| # | Proyecto | Tipo | Área Responsable | OKR Relacionado | Servicios Clave |
|---|----------|------|------------------|-----------------|-----------------|
{{#each PROYECTOS_ESTRATEGICOS}}
| {{this.numero}} | {{this.nombre}} | {{this.tipo}} | {{this.area}} | {{this.okr}} | {{this.servicios}} |
{{/each}}

## 4. Cronograma de Iniciativas

| Iniciativa | Q1 | Q2 | Q3 | Q4 |
|------------|----|----|----|----|
{{#each INICIATIVAS}}
| {{this.nombre}} | {{this.q1}} | {{this.q2}} | {{this.q3}} | {{this.q4}} |
{{/each}}

## 5. Presupuesto de Servicios Estratégicos

| Categoría | Presupuesto {{PERIODO}} | % del Total |
|-----------|------------------------|-------------|
{{#each PRESUPUESTO_SERVICIOS}}
| {{this.categoria}} | {{this.monto}} | {{this.porcentaje}} |
{{/each}}
| **Total** | **{{PRESUPUESTO_TOTAL}}** | **100%** |

## 6. Relación con Revisar.ia

Toda contratación de servicios estratégicos e intangibles **deberá canalizarse** 
a través de la plataforma Revisar.ia para:
- Validar alineación con OKRs
- Evaluar beneficio económico esperado
- Asegurar cumplimiento fiscal (Art. 5-A CFF, 27 LISR)
- Documentar materialidad y trazabilidad

El Plan Estratégico Anual sirve como referencia para que los agentes de 
Estrategia, Fiscal, Legal y Finanzas evalúen si un proyecto está alineado.
