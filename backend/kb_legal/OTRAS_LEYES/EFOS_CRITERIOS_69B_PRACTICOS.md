---
id: EFOS_CRITERIOS
ley: Criterios SAT / Art. 69-B CFF
titulo: Criterios prácticos para identificación de EFOS
tags: [efos, 69b, indicadores, scoring, A6, A3]
prioridad: alta
---

# @EFOS_CRITERIOS - Criterios Prácticos EFOS

## [RESUMEN OPERATIVO]

Este documento consolida los indicadores que utiliza el SAT para identificar 
Empresas que Facturan Operaciones Simuladas (EFOS) y los criterios que 
Revisar.IA usa para evaluar riesgo.

---

## Indicadores SAT para presunción EFOS:

### 1. Perfil del contribuyente:

| Indicador | Descripción | Peso |
|-----------|-------------|------|
| **Domicilio fiscal** | No localizable / virtual | 🔴 Crítico |
| **Personal** | Sin empleados o mínimos | 🔴 Alto |
| **Activos** | Sin activos para operar | 🔴 Alto |
| **Antigüedad** | Empresa recién constituida | ⚠️ Medio |
| **Capital social** | Mínimo legal ($50,000) | ⚠️ Medio |

### 2. Perfil de facturación:

| Indicador | Descripción | Peso |
|-----------|-------------|------|
| **Volumen** | Facturación desproporcionada vs estructura | 🔴 Crítico |
| **Diversidad** | Muchos giros no relacionados | 🔴 Alto |
| **Clientes** | Mismos clientes siempre | ⚠️ Medio |
| **Montos** | Montos redondos repetitivos | ⚠️ Medio |
| **Conceptos** | Descripciones genéricas | 🔴 Alto |

### 3. Perfil financiero:

| Indicador | Descripción | Peso |
|-----------|-------------|------|
| **Pagos** | Movimientos circulares | 🔴 Crítico |
| **Cuentas** | Múltiples cuentas inactivas | ⚠️ Medio |
| **Flujo** | Retiro inmediato de fondos | 🔴 Alto |
| **Bancarización** | Operaciones en efectivo | 🔴 Alto |

---

## Scoring de Riesgo A6:

El agente A6 (Tráfico.IA) calcula un score de riesgo basado en estos 
indicadores:

```
SCORING DE PROVEEDOR

DATOS PÚBLICOS:
□ Lista 69-B Presunto    → +50 puntos
□ Lista 69-B Definitivo  → +100 puntos (CRÍTICO)
□ No localizado          → +40 puntos
□ Opinión 32-D negativa  → +30 puntos
□ RFC reciente (<2 años) → +10 puntos

PERFIL OPERATIVO (si disponible):
□ Sin empleados IMSS     → +25 puntos
□ Domicilio virtual      → +20 puntos
□ Múltiples giros        → +15 puntos
□ Capital mínimo         → +10 puntos

HISTORIAL:
□ Cambios frecuentes RFC → +15 puntos
□ Socios en otras EFOS   → +30 puntos

CÁLCULO:
0-20 puntos    → BAJO
21-40 puntos   → MEDIO
41-60 puntos   → ALTO
61+ puntos     → CRÍTICO
```

### Interpretación del score:

| Score | Nivel | Acción recomendada |
|-------|-------|-------------------|
| **0-20** | ✅ Bajo | Operar normalmente |
| **21-40** | ⚠️ Medio | Documentar operación extra |
| **41-60** | 🔶 Alto | Evaluar continuar relación |
| **61+** | 🔴 Crítico | No operar / autocorregir |

---

## Señales de alerta en CFDIs:

### Conceptos sospechosos:

```
CONCEPTOS GENÉRICOS (alto riesgo):
❌ "Servicios varios"
❌ "Consultoría"
❌ "Asesoría" 
❌ "Servicios profesionales"
❌ "Comisiones"
❌ "Intermediación"

CONCEPTOS ESPECÍFICOS (bajo riesgo):
✅ "Desarrollo de software sistema inventarios - Entrega fase 1"
✅ "Servicio de auditoría fiscal ejercicio 2024"
✅ "Mantenimiento preventivo maquinaria CNC modelo X - Mayo 2025"
```

### Patrones de facturación:

| Patrón | Riesgo | Descripción |
|--------|--------|-------------|
| Montos redondos | Alto | $50,000, $100,000 exactos |
| Misma descripción | Alto | CFDIs idénticos cada mes |
| Múltiples conceptos | Alto | 10+ servicios distintos |
| Precio inconsistente | Alto | Mismo servicio, precios muy diferentes |

---

## Checklist de Due Diligence (A6):

```
VERIFICACIÓN PRE-CONTRATACIÓN

1. LISTAS SAT
   □ 69-B Presuntos: NO APARECE
   □ 69-B Definitivos: NO APARECE
   □ No localizados: NO APARECE
   □ 32-D: POSITIVA

2. PERFIL BÁSICO
   □ RFC activo y vigente
   □ Domicilio localizable
   □ Antigüedad razonable
   □ Objeto social congruente

3. CAPACIDAD OPERATIVA
   □ Personal registrado IMSS
   □ Infraestructura visible
   □ Referencias comerciales
   □ Página web / presencia

4. DOCUMENTACIÓN
   □ Acta constitutiva
   □ Poder del representante
   □ Comprobante de domicilio
   □ Identificación representante

RESULTADO: [ ] APROBADO  [ ] OBSERVADO  [ ] RECHAZADO
```

---

## Para Defense Files (A7):

Cuando el SAT cuestiona operaciones con un proveedor, el Defense File 
debe incluir:

```
EXPEDIENTE DE MATERIALIDAD

1. VERIFICACIÓN PRE-CONTRATACIÓN
   - Fecha de verificación: [XXX]
   - Resultado 69-B: No publicado
   - Resultado 32-D: Positiva
   - Score de riesgo: [XX] puntos (BAJO)

2. CAPACIDAD DEL PROVEEDOR
   - Empleados IMSS: [XX]
   - Domicilio verificado: [Dirección + evidencia]
   - Antigüedad: [XX años]
   - Capital social: $[XXX]

3. REALIDAD DE LA OPERACIÓN
   - Contrato: [Número/fecha]
   - Entregables: [Lista]
   - Comunicaciones: [XX emails/documentos]

4. FLUJO FINANCIERO
   - Forma de pago: Transferencia bancaria
   - Cuenta destino: [Banco] [últimos 4 dígitos]
   - Estado de cuenta: [Adjunto]

CONCLUSIÓN: Operación con sustancia económica real.
```

---

## Referencias cruzadas

- @CFF_69B (Artículo 69-B completo)
- @CFF_69 (Listas públicas)
- @CFF_32D (Opinión de cumplimiento)
- @TESIS_MAT_001 (Carga probatoria)
- @TESIS_MAT_002 (Elementos de prueba)
