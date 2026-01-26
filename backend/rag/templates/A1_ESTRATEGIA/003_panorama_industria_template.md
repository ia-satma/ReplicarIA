---
id: 003_panorama_industria
agente: A1_ESTRATEGIA
tipo: plantilla
version: "1.0"
personalizable: true
campos_requeridos:
  - NOMBRE_EMPRESA
  - INDUSTRIA
  - PERIODO
---

# Análisis del Panorama de la Industria – {{PERIODO}}

## 1. Perfil de la Empresa

| Campo | Valor |
|-------|-------|
| Nombre | {{NOMBRE_EMPRESA}} |
| Industria | {{INDUSTRIA}} |
| Sub-industria | {{SUB_INDUSTRIA}} |
| Antigüedad | {{AÑOS_OPERACION}} años |
| Tamaño | {{TAMAÑO_EMPRESA}} |
| Presencia geográfica | {{PRESENCIA_GEOGRAFICA}} |

## 2. Entorno Macroeconómico

### Contexto Nacional
- **Crecimiento PIB proyectado:** {{PIB_PROYECTADO}}
- **Inflación esperada:** {{INFLACION_ESPERADA}}
- **Tendencia tasas de interés:** {{TENDENCIA_TASAS}}
- **Tipo de cambio:** {{TIPO_CAMBIO}}

### Factores Relevantes para {{INDUSTRIA}}
{{#each FACTORES_MACRO}}
- {{this}}
{{/each}}

## 3. Tendencias Sectoriales

### Principales Tendencias en {{INDUSTRIA}}

{{#each TENDENCIAS}}
{{this.numero}}. **{{this.nombre}}**
   - Descripción: {{this.descripcion}}
   - Impacto esperado: {{this.impacto}}
{{/each}}

### Segmentos de Mayor Crecimiento
{{#each SEGMENTOS_CRECIMIENTO}}
- {{this}}
{{/each}}

### Factores Condicionantes
{{#each FACTORES_CONDICIONANTES}}
- {{this}}
{{/each}}

## 4. Entorno Regulatorio

### Normatividad Aplicable
| Regulación | Descripción | Impacto |
|------------|-------------|---------|
{{#each REGULACIONES}}
| {{this.nombre}} | {{this.descripcion}} | {{this.impacto}} |
{{/each}}

### Cambios Regulatorios Esperados
{{#each CAMBIOS_REGULATORIOS}}
- {{this}}
{{/each}}

## 5. Análisis Competitivo

### Principales Competidores
| Competidor | Fortalezas | Debilidades |
|------------|------------|-------------|
{{#each COMPETIDORES}}
| {{this.nombre}} | {{this.fortalezas}} | {{this.debilidades}} |
{{/each}}

### Ventajas Competitivas de {{NOMBRE_EMPRESA}}
{{#each VENTAJAS_COMPETITIVAS}}
- {{this}}
{{/each}}

## 6. Implicaciones para Planeación

La empresa necesita:
{{#each NECESIDADES_PLANEACION}}
- {{this}}
{{/each}}

Este documento es un **insumo de contexto** basado en información pública y 
análisis internos.
