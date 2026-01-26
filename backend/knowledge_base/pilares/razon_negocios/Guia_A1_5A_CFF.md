# Guía A1: Razón de Negocios (Art. 5-A CFF)

## Definición interna

La **Razón de Negocios** es el propósito empresarial, económico o comercial que justifica una operación, distinto e independiente del beneficio fiscal que pudiera generar.

En Revisar.ia, A1 es responsable de documentar y evaluar la razón de negocios de cada proyecto en F0.

---

## Marco normativo aplicable

- **Art. 5-A CFF**: Presunción de simulación si no hay razón de negocios
- **Art. 27-I LISR**: Estricta indispensabilidad
- **Jurisprudencia**: "Razonablemente necesario" vs "absolutamente indispensable"

---

## Criterios de scoring A1

### Escala: 0-25 puntos

| Criterio | Puntos | Pregunta evaluadora |
|----------|--------|---------------------|
| **Sustancia económica** | 0-5 | ¿Tiene sentido la operación sin beneficio fiscal? |
| **Propósito concreto** | 0-5 | ¿El objetivo está claramente formulado? |
| **Coherencia estratégica** | 0-5 | ¿Está ligado a OKRs o pilares estratégicos? |
| **BEE describible** | 0-5 | ¿Se entiende el mecanismo causa-efecto del beneficio? |
| **Documentación contemporánea** | 0-5 | ¿Hay evidencia del momento de la decisión? |

### Traducción a estados

| Estado | Score | Criterio |
|--------|-------|----------|
| **CONFORME** | ≥ 18 | Sin red flags críticos |
| **CONDICIONADA** | 12-17 | Áreas a mejorar (KPIs poco claros, falta amarre a OKRs) |
| **NO_CONFORME** | < 12 | Red flags estratégicos graves o sin RN identificable |

---

## Componentes del dictamen A1

### 1. Razón de Negocios

- **Problema de negocio**: ¿Qué se quiere resolver?
- **Solución propuesta**: ¿Por qué este servicio es la respuesta?
- **Objetivo medible**: ¿Qué se espera lograr?

### 2. Beneficio Económico Esperado (BEE)

- **Tipo de beneficio**: Ingresos, ahorros, mitigación de riesgos, cumplimiento
- **Mecanismo**: ¿Cómo el servicio genera el beneficio?
- **Horizonte**: ¿En cuánto tiempo se espera materializar?
- **KPIs**: ¿Cómo se medirá?

### 3. Alineación estratégica

- **OKRs relacionados**: Objetivos corporativos que soporta
- **Pilares estratégicos**: Áreas de enfoque de la empresa
- **Coherencia**: No contradice otras decisiones internas

### 4. Supuestos clave

- Condiciones de mercado asumidas
- Capacidades internas requeridas
- Dependencias externas

### 5. Red flags identificados

- Objetivos vagos
- Timing sospechoso
- Repetición sin aprendizaje
- Desacople con actividad preponderante

---

## Ejemplos por estado

### CONFORME (Score 22/25)

> **Proyecto**: Campaña de membresía premium Q3 2026
> 
> **Razón de negocios**: Incrementar ventas de membresía premium 30% mediante campaña digital segmentada, alineado con OKR de crecimiento en socios activos.
> 
> **BEE**: Incremento de $3.6M en ingresos anuales por 300 nuevos socios premium a $1,000/mes.
> 
> **Alineación**: OKR 2026-01 (Incrementar socios activos 20%)

### CONDICIONADA (Score 15/25)

> **Proyecto**: Estudio de mercado retail
> 
> **Razón de negocios**: Entender el mercado para tomar decisiones de expansión.
> 
> **Observaciones A1**:
> - KPIs no definidos (¿cómo se mide éxito del estudio?)
> - Sin liga clara a decisión de inversión
> - Recomendación: Definir qué decisiones se tomarán con el estudio

### NO_CONFORME (Score 8/25)

> **Proyecto**: Consultoría estratégica general
> 
> **Razón de negocios**: "Mejorar posicionamiento competitivo"
> 
> **Red flags**:
> - Objetivo completamente vago
> - Sin métricas de éxito
> - No se identifica problema específico a resolver
> - Similar a consultorías previas sin implementación

---

## Red flags estratégicos

### Lista de señales de alerta

| Flag | Descripción | Impacto en score |
|------|-------------|-----------------|
| **Objetivos vagos** | "Mejorar posicionamiento" sin métricas | -3 a -5 |
| **Timing sospechoso** | Contratación masiva en diciembre | -2 a -3 |
| **Repetición sin aprendizaje** | Mismo estudio año tras año | -3 a -5 |
| **Desacople estratégico** | Sin conexión con actividad preponderante | -4 a -5 |
| **Falta de BEE** | "Hay que estar en redes" sin objetivo | -3 a -5 |
| **Solo beneficio fiscal** | Único beneficio identificable es fiscal | Bloquea aprobación |

---

## Interacción con otros agentes

### Con A2 (PMO)
- Si A1 = NO_CONFORME → A2 bloquea F2 salvo excepción
- Estado de A1 visible en dashboard de proyecto

### Con A3 (Fiscal)
- A3 usa dictamen A1 para Art. 5-A CFF
- Si A1 = NO_CONFORME → A3 marca riesgo alto automáticamente

### Con A5 (Finanzas)
- A5 toma BEE cualitativo de A1 para cuantificar
- Si BEE de A1 es confuso → A5 marca modelo de baja calidad

### Con A7 (Defensa)
- Dictamen A1 es sección 5 del Defense File
- Argumentos de RN vienen de A1
