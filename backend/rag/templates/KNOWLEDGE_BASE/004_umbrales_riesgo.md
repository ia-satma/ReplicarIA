---
tipo: umbrales_riesgo
version: "1.0"
agente: KNOWLEDGE_BASE
instrucciones: "Definición de umbrales de riesgo y niveles de escrutinio por tipo de operación. Documento universal de referencia."
---

# Umbrales de Riesgo por Tipo de Operación

## 1. Introducción

Este documento define los **umbrales de riesgo** que determinan el nivel de escrutinio, documentación y aprobación requeridos para operaciones de servicios intangibles.

### 1.1 Propósito

- Clasificar operaciones por nivel de riesgo
- Definir requisitos de documentación proporcionales
- Establecer niveles de aprobación requeridos
- Guiar la priorización de revisiones

### 1.2 Factores de Riesgo

| Factor | Descripción | Peso |
|--------|-------------|------|
| Monto | Valor económico de la operación | 30% |
| Tipología | Naturaleza del servicio | 25% |
| Proveedor | Perfil de riesgo del prestador | 25% |
| Partes Relacionadas | Operación intragrupo | 20% |

---

## 2. Umbrales por Monto

### 2.1 Clasificación de Montos

| Nivel | Rango (MXN) | Rango (USD aprox.) | Clasificación |
|-------|-------------|-------------------|---------------|
| 1 | Hasta $500,000 | Hasta $25,000 | Bajo |
| 2 | $500,001 - $2,000,000 | $25,001 - $100,000 | Medio |
| 3 | $2,000,001 - $10,000,000 | $100,001 - $500,000 | Alto |
| 4 | $10,000,001 - $50,000,000 | $500,001 - $2,500,000 | Muy Alto |
| 5 | Más de $50,000,000 | Más de $2,500,000 | Crítico |

### 2.2 Requisitos por Nivel de Monto

#### Nivel 1: Monto Bajo (Hasta $500,000 MXN)

| Requisito | Obligatorio | Opcional |
|-----------|-------------|----------|
| Contrato firmado | ✅ | |
| CFDI válido | ✅ | |
| Entregables | ✅ | |
| Acta de aceptación | ✅ | |
| Business case | | ✅ |
| Dictamen técnico | | ✅ |

**Aprobación:** Gerente de área

#### Nivel 2: Monto Medio ($500,001 - $2,000,000 MXN)

| Requisito | Obligatorio | Opcional |
|-----------|-------------|----------|
| Contrato firmado | ✅ | |
| CFDI válido | ✅ | |
| Entregables | ✅ | |
| Acta de aceptación | ✅ | |
| Minutas de reuniones | ✅ | |
| Business case | ✅ | |
| Verificación 32-D | ✅ | |
| Dictamen técnico | | ✅ |

**Aprobación:** Director de área

#### Nivel 3: Monto Alto ($2,000,001 - $10,000,000 MXN)

| Requisito | Obligatorio | Opcional |
|-----------|-------------|----------|
| Contrato firmado | ✅ | |
| CFDI válido | ✅ | |
| Entregables | ✅ | |
| Acta de aceptación | ✅ | |
| Minutas de reuniones | ✅ | |
| Business case | ✅ | |
| BEE cuantificado | ✅ | |
| Due diligence proveedor | ✅ | |
| Verificación 32-D y 69-B | ✅ | |
| Dictamen técnico | ✅ | |

**Aprobación:** VP o C-Level + Finanzas

#### Nivel 4: Monto Muy Alto ($10,000,001 - $50,000,000 MXN)

| Requisito | Obligatorio |
|-----------|-------------|
| Todo lo anterior | ✅ |
| Análisis de alternativas documentado | ✅ |
| Benchmarking de precios | ✅ |
| Dictamen de valuación | ✅ |
| Opinión fiscal | ✅ |
| Auditoría de materialidad | ✅ |

**Aprobación:** CEO + CFO + Comité de Riesgos

#### Nivel 5: Monto Crítico (Más de $50,000,000 MXN)

| Requisito | Obligatorio |
|-----------|-------------|
| Todo lo anterior | ✅ |
| Aprobación de Consejo de Administración | ✅ |
| Dictamen de auditor externo | ✅ |
| Análisis de impacto fiscal | ✅ |
| Defense file preventivo | ✅ |

**Aprobación:** Consejo de Administración

---

## 3. Umbrales por Tipología de Servicio

### 3.1 Matriz de Riesgo por Tipología

| Tipología | Riesgo Base | Multiplicador de Monto |
|-----------|-------------|------------------------|
| Capacitación | Bajo | 1.0x |
| Licenciamiento Software | Bajo | 1.0x |
| Marketing/Publicidad | Medio | 1.2x |
| Desarrollo Software | Medio | 1.2x |
| Consultoría Operativa | Medio | 1.3x |
| Legal/Fiscal | Medio | 1.3x |
| Consultoría Estratégica | Alto | 1.5x |
| I+D | Alto | 1.5x |
| Asistencia Técnica | Alto | 1.5x |
| Management Fees | Muy Alto | 2.0x |

### 3.2 Ajuste de Umbral por Tipología

**Fórmula:**
```
Monto Ajustado = Monto Real × Multiplicador de Tipología
```

**Ejemplo:**
- Servicio de consultoría estratégica por $1,500,000
- Multiplicador: 1.5x
- Monto ajustado: $2,250,000 → Nivel 3 (Alto)

---

## 4. Umbrales por Perfil de Proveedor

### 4.1 Clasificación de Proveedores

| Categoría | Criterios | Factor de Riesgo |
|-----------|-----------|------------------|
| **AAA** | Proveedor conocido, historial positivo, 32-D positiva, no 69-B | 0.8x |
| **AA** | Proveedor nuevo, verificaciones satisfactorias | 1.0x |
| **A** | Proveedor con alertas menores | 1.2x |
| **B** | Proveedor de reciente creación, sin historial | 1.5x |
| **C** | Proveedor con indicadores de riesgo | 2.0x |
| **Rechazado** | Publicado en 69-B o sin verificaciones | No operar |

### 4.2 Indicadores de Riesgo del Proveedor

| Indicador | Descripción | Impacto |
|-----------|-------------|---------|
| Antigüedad < 2 años | Empresa de reciente creación | +0.3x |
| Sin empleados reportados | Sin nómina ante IMSS | +0.5x |
| Domicilio no verificable | No localizable en domicilio fiscal | +0.5x |
| Capital social mínimo | $50,000 o menos | +0.2x |
| Cambios frecuentes de domicilio | Más de 2 en 3 años | +0.3x |
| Actividad incongruente | Objeto social no relacionado | +0.5x |

### 4.3 Umbrales de Verificación Obligatoria

| Monto de Operación | Verificación Mínima |
|-------------------|---------------------|
| Cualquier monto | Constancia situación fiscal + 32-D |
| >$500,000 | + Verificación lista 69-B |
| >$2,000,000 | + Acta constitutiva + Poderes |
| >$5,000,000 | + Capacidad operativa + Referencias |
| >$10,000,000 | + Auditoría de proveedor |

---

## 5. Umbrales para Partes Relacionadas

### 5.1 Requisitos Adicionales

| Monto | Requisitos Adicionales |
|-------|------------------------|
| Cualquiera | Contrato arm's length, metodología de precio |
| >$1,000,000 | Estudio simplificado de precios de transferencia |
| >$5,000,000 | Estudio completo de precios de transferencia |
| >$20,000,000 | Dictamen de PT por tercero independiente |
| >$50,000,000 | Acuerdo anticipado de precios (APA) recomendado |

### 5.2 Multiplicador de Partes Relacionadas

Cuando la operación es entre partes relacionadas, aplicar multiplicador adicional de **1.5x** al monto ajustado.

**Ejemplo:**
- Management fee por $3,000,000
- Multiplicador tipología (MF): 2.0x
- Multiplicador partes relacionadas: 1.5x
- Monto ajustado: $3,000,000 × 2.0 × 1.5 = $9,000,000 → Nivel 3 (Alto)

---

## 6. Matriz de Decisión Consolidada

### 6.1 Cálculo del Nivel de Riesgo

```
Monto Ajustado = Monto Real × Factor Tipología × Factor Proveedor × Factor PR
```

Donde:
- Factor Tipología: 1.0x a 2.0x según tipo de servicio
- Factor Proveedor: 0.8x a 2.0x según perfil
- Factor PR: 1.0x (independiente) o 1.5x (parte relacionada)

### 6.2 Tabla de Decisión

| Monto Ajustado | Nivel | Documentación | Aprobación |
|----------------|-------|---------------|------------|
| Hasta $500K | Bajo | Básica | Gerente |
| $500K - $2M | Medio | Estándar | Director |
| $2M - $10M | Alto | Reforzada | VP + Finanzas |
| $10M - $50M | Muy Alto | Completa | C-Level + Comité |
| >$50M | Crítico | Defense File | Consejo |

---

## 7. Alertas Automáticas

### 7.1 Alertas por Monto

| Tipo de Alerta | Trigger | Acción |
|----------------|---------|--------|
| Información | >$500,000 | Notificación a Finanzas |
| Atención | >$2,000,000 | Notificación a Fiscal |
| Advertencia | >$5,000,000 | Notificación a Dirección |
| Crítica | >$10,000,000 | Escalamiento inmediato |

### 7.2 Alertas por Proveedor

| Tipo de Alerta | Trigger | Acción |
|----------------|---------|--------|
| 32-D Negativa | Opinión de cumplimiento negativa | Bloqueo de pago |
| Lista 69-B | Proveedor publicado | Bloqueo de pago + Revisión |
| Cambio de estatus | Modificación de situación fiscal | Notificación a Fiscal |
| Domicilio no localizado | Buzón tributario rebotado | Verificación adicional |

### 7.3 Alertas por Acumulación

| Tipo de Alerta | Trigger | Acción |
|----------------|---------|--------|
| Concentración proveedor | >30% de compras a un proveedor | Revisión de dependencia |
| Acumulación anual | >$20M anuales a un proveedor | Revisión de materialidad |
| Operaciones frecuentes | >12 operaciones/año con mismo proveedor | Consolidar en contrato |

---

## 8. Procedimiento de Escalamiento

### 8.1 Flujo de Escalamiento

```
Operación identificada
        ↓
Cálculo de Monto Ajustado
        ↓
Determinación de Nivel
        ↓
  ┌─────┴─────┬─────────┬─────────┬─────────┐
  ↓           ↓         ↓         ↓         ↓
Bajo        Medio     Alto     Muy Alto  Crítico
  ↓           ↓         ↓         ↓         ↓
Gerente   Director   VP+Fin   C-Level   Consejo
```

### 8.2 Tiempos de Respuesta

| Nivel | Tiempo Máximo de Aprobación |
|-------|----------------------------|
| Bajo | 3 días hábiles |
| Medio | 5 días hábiles |
| Alto | 10 días hábiles |
| Muy Alto | 15 días hábiles |
| Crítico | 30 días hábiles |

---

## 9. Excepciones

### 9.1 Proceso de Excepción

Las excepciones a estos umbrales requieren:
1. Justificación documentada
2. Aprobación del nivel inmediato superior
3. Registro en bitácora de excepciones
4. Revisión posterior por Auditoría Interna

### 9.2 Excepciones No Permitidas

No se permiten excepciones para:
- Proveedores en lista 69-B definitiva
- Operaciones sin CFDI
- Pagos no bancarizados >$2,000
- Servicios sin contrato

---

## 10. Revisión de Umbrales

### 10.1 Frecuencia de Revisión

- **Anual:** Revisión de montos por inflación
- **Semestral:** Revisión de multiplicadores por tipología
- **Trimestral:** Actualización de perfiles de proveedores
- **Continuo:** Monitoreo de listas 69-B y 32-D

### 10.2 Criterios de Ajuste

| Factor | Criterio de Ajuste |
|--------|-------------------|
| Inflación | Actualización anual por INPC |
| Regulación | Cambios en normativa fiscal |
| Experiencia | Resultados de auditorías |
| Industria | Prácticas del sector |

---

*Este documento define los umbrales de riesgo aplicables a operaciones de servicios intangibles.*
