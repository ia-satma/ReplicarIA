---
tipo: referencia
version: "1.0"
agente: A3_FISCAL
instrucciones: "Compendio de casos típicos de auditoría SAT y precedentes relevantes. Utilizar como referencia para identificar riesgos y preparar defensas."
---

# Casos de Auditoría SAT – Precedentes y Análisis

## 1. Introducción

Este documento compila **casos típicos de auditoría** del SAT relacionados con servicios intangibles, incluyendo:

- Patrones de revisión frecuentes
- Hallazgos comunes
- Defensas exitosas
- Lecciones aprendidas

## 2. Categorías de Casos

### Distribución por Tipo

| Categoría | Frecuencia | Riesgo Promedio |
|-----------|------------|-----------------|
| Operaciones simuladas (69-B) | {{FRECUENCIA_69B}}% | Crítico |
| Falta de razón de negocios | {{FRECUENCIA_5A}}% | Alto |
| Precios de transferencia | {{FRECUENCIA_PT}}% | Alto |
| Deducibilidad cuestionada | {{FRECUENCIA_DED}}% | Medio-Alto |
| Formalidades CFDI | {{FRECUENCIA_CFDI}}% | Medio |

## 3. Casos Típicos por Categoría

### 3.1 Operaciones Simuladas (Art. 69-B)

#### Caso A: Consultoría sin Entregables

```
══════════════════════════════════════════════════════════════
                    CASO: CONSUL-001
══════════════════════════════════════════════════════════════
Sector:           {{SECTOR_A}}
Monto:            {{MONTO_A}}
Tipología:        Consultoría estratégica
══════════════════════════════════════════════════════════════

SITUACIÓN:
Empresa contrata servicios de consultoría por ${{MONTO_A}} con
proveedor que posteriormente aparece en lista 69-B.

HALLAZGOS DEL SAT:
├── Sin entregables documentados
├── Único contacto: representante legal
├── No hay correos de trabajo
├── Pagos fraccionados en efectivo < $2,000
└── Proveedor sin empleados registrados

DEFENSA INTENTADA:
"Se realizaron sesiones de asesoría verbal"

RESULTADO:
❌ CFDI declarados sin efectos fiscales
❌ Crédito fiscal por ISR omitido + recargos
❌ Multa 55% del impuesto

LECCIÓN:
Siempre documentar entregables tangibles y comunicaciones.
══════════════════════════════════════════════════════════════
```

#### Caso B: Servicios Intragrupo Cuestionados

```
══════════════════════════════════════════════════════════════
                    CASO: INTRA-002
══════════════════════════════════════════════════════════════
Sector:           {{SECTOR_B}}
Monto:            {{MONTO_B}}
Tipología:        Management fees intragrupo
══════════════════════════════════════════════════════════════

SITUACIÓN:
Subsidiaria mexicana paga management fees a matriz extranjera
sin estudio de precios de transferencia contemporáneo.

HALLAZGOS DEL SAT:
├── Sin estudio de PT del ejercicio
├── Metodología de asignación no documentada
├── Servicios duplicados con áreas internas
├── No se demostró beneficio específico
└── Tasa de margen superior al mercado

DEFENSA EXITOSA:
├── Se presentó estudio PT elaborado posteriormente
├── Se demostró beneficio con métricas de desempeño
├── Se identificaron servicios específicos no duplicados
└── Comparables de mercado respaldaron precio

RESULTADO:
⚠️ Ajuste parcial del 30% del monto
✅ Se conservó deducibilidad del 70%

LECCIÓN:
Documentar contemporáneamente y cuantificar beneficios.
══════════════════════════════════════════════════════════════
```

### 3.2 Razón de Negocios (Art. 5-A)

#### Caso C: Reestructura sin Sustancia

```
══════════════════════════════════════════════════════════════
                    CASO: REESTR-003
══════════════════════════════════════════════════════════════
Sector:           {{SECTOR_C}}
Monto:            {{MONTO_C}}
Tipología:        Reestructura corporativa / servicios
══════════════════════════════════════════════════════════════

SITUACIÓN:
Grupo empresarial crea entidad intermediaria para facturar
servicios y generar deducciones en entidad operativa.

HALLAZGOS DEL SAT:
├── Entidad sin sustancia (sin empleados propios)
├── Único cliente: empresas del grupo
├── Margen superior al mercado
├── Sin valor agregado identificable
└── Beneficio fiscal único propósito aparente

ARGUMENTOS DEL SAT:
"La operación carece de razón de negocios conforme al
Art. 5-A CFF, siendo su único propósito la erosión de
la base gravable de la entidad operativa."

RESULTADO:
❌ Recaracterización de operaciones
❌ Crédito fiscal significativo
❌ Posible responsabilidad solidaria

LECCIÓN:
Las estructuras deben tener sustancia económica real.
══════════════════════════════════════════════════════════════
```

#### Caso D: Software sin Uso Demostrado

```
══════════════════════════════════════════════════════════════
                    CASO: SOFT-004
══════════════════════════════════════════════════════════════
Sector:           {{SECTOR_D}}
Monto:            {{MONTO_D}}
Tipología:        Licenciamiento de software
══════════════════════════════════════════════════════════════

SITUACIÓN:
Empresa deduce licencias de software especializado sin
poder demostrar uso efectivo.

HALLAZGOS DEL SAT:
├── Sin logs de acceso al sistema
├── Usuarios asignados no existen en nómina
├── Capacitación no documentada
├── Proveedor sin representación en México
└── Facturación desde país de baja tributación

DEFENSA EXITOSA:
├── Se obtuvieron logs de uso del proveedor
├── Se demostró integración con sistemas internos
├── Personal capacitado identificado con evidencia
└── Se justificó necesidad operativa del software

RESULTADO:
✅ Deducción confirmada tras pruebas adicionales

LECCIÓN:
Conservar evidencia de uso de servicios digitales.
══════════════════════════════════════════════════════════════
```

### 3.3 Precios de Transferencia

#### Caso E: Servicios Técnicos Sobrevaluados

```
══════════════════════════════════════════════════════════════
                    CASO: PT-005
══════════════════════════════════════════════════════════════
Sector:           {{SECTOR_E}}
Monto:            {{MONTO_E}}
Tipología:        Servicios técnicos de parte relacionada
══════════════════════════════════════════════════════════════

SITUACIÓN:
Empresa mexicana contrata servicios técnicos de relacionada
extranjera a tarifas superiores al mercado.

HALLAZGOS DEL SAT:
├── Margen del 45% vs mercado 15-25%
├── Comparables no apropiados en estudio PT
├── Funciones duplicadas con personal local
├── Sin análisis de beneficio recibido

DEFENSA PARCIALMENTE EXITOSA:
├── Se reelaboró estudio con mejores comparables
├── Se demostró valor agregado técnico específico
├── Se aceptó ajuste de margen a rango

RESULTADO:
⚠️ Ajuste al extremo superior del rango intercuartil
⚠️ Crédito fiscal reducido vs pretensión original

LECCIÓN:
Estudios de PT robustos con comparables apropiados.
══════════════════════════════════════════════════════════════
```

## 4. Patrones de Revisión del SAT

### Indicadores que Disparan Revisión

| Indicador | Descripción | Probabilidad de Revisión |
|-----------|-------------|--------------------------|
| Proveedor en lista 69-B | Cualquier operación con EFOS | {{PROB_69B}}% |
| Ratio servicios/ingresos alto | > {{RATIO_SERVICIOS}}% | {{PROB_RATIO}}% |
| Operaciones con REFIPRES | Países de baja tributación | {{PROB_REFIPRES}}% |
| Pérdidas fiscales recurrentes | > {{AÑOS_PERDIDAS}} años | {{PROB_PERDIDAS}}% |
| Variación significativa ISR | > {{VARIACION_ISR}}% vs año anterior | {{PROB_VARIACION}}% |
| Precios de transferencia | Operaciones > ${{UMBRAL_PT}} | {{PROB_PT}}% |

### Documentos más Solicitados

| Ranking | Documento | Frecuencia de Solicitud |
|---------|-----------|-------------------------|
| 1 | Contratos de servicios | {{FREC_CONTRATOS}}% |
| 2 | Estados de cuenta bancarios | {{FREC_BANCOS}}% |
| 3 | CFDI y complementos de pago | {{FREC_CFDI}}% |
| 4 | Estudios de precios de transferencia | {{FREC_PT}}% |
| 5 | Entregables de servicios | {{FREC_ENTREGABLES}}% |
| 6 | Correos y comunicaciones | {{FREC_CORREOS}}% |

## 5. Defensas Exitosas - Mejores Prácticas

### Elementos Clave de Defensa

| Elemento | Peso en Defensa | Preparación |
|----------|-----------------|-------------|
| Documentación contemporánea | Alto | Antes/durante operación |
| Entregables tangibles | Muy Alto | Por hito de servicio |
| Cuantificación de beneficio | Alto | Antes de contratación |
| Comparables de mercado | Medio-Alto | Al inicio de relación |
| Comunicaciones operativas | Medio | Durante operación |
| Testimonio de personal | Medio | Post-operación |

### Estrategias de Defensa por Tipo

```
┌─────────────────────────────────────────────────────────────┐
│           ESTRATEGIA DE DEFENSA - MATRIZ                    │
├────────────────────┬────────────────────────────────────────┤
│ TIPO DE HALLAZGO   │ ESTRATEGIA PRINCIPAL                   │
├────────────────────┼────────────────────────────────────────┤
│ Operación simulada │ Demostrar materialidad con evidencia   │
│                    │ física, testigos, flujo de trabajo     │
├────────────────────┼────────────────────────────────────────┤
│ Sin razón negocios │ Cuantificar BEE, mostrar alineación    │
│                    │ estratégica, resultados obtenidos      │
├────────────────────┼────────────────────────────────────────┤
│ Precios fuera mkt  │ Estudio PT robusto, comparables        │
│                    │ apropiados, funciones diferenciadas    │
├────────────────────┼────────────────────────────────────────┤
│ Formalidades CFDI  │ Corrección de comprobantes,            │
│                    │ complementos, carta de corrección      │
└────────────────────┴────────────────────────────────────────┘
```

## 6. Jurisprudencia Relevante

### Tesis Favorables al Contribuyente

| Número | Tema | Criterio |
|--------|------|----------|
| {{TESIS_FAV_1}} | Razón de negocios | {{CRITERIO_FAV_1}} |
| {{TESIS_FAV_2}} | Materialidad | {{CRITERIO_FAV_2}} |
| {{TESIS_FAV_3}} | Deducibilidad | {{CRITERIO_FAV_3}} |

### Tesis Favorables al SAT

| Número | Tema | Criterio |
|--------|------|----------|
| {{TESIS_SAT_1}} | Carga de prueba | {{CRITERIO_SAT_1}} |
| {{TESIS_SAT_2}} | Documentación | {{CRITERIO_SAT_2}} |
| {{TESIS_SAT_3}} | Sustancia | {{CRITERIO_SAT_3}} |

## 7. Recomendaciones Preventivas

### Antes de la Operación

1. Documentar razón de negocios y BEE
2. Verificar proveedor en listas SAT
3. Obtener cotizaciones comparativas
4. Definir entregables específicos

### Durante la Operación

1. Mantener comunicaciones documentadas
2. Solicitar reportes de avance
3. Documentar entregables recibidos
4. Verificar pagos bancarizados

### Después de la Operación

1. Evaluar beneficio obtenido
2. Conservar expediente completo
3. Actualizar estudio de PT si aplica
4. Revisar exposición en declaraciones

