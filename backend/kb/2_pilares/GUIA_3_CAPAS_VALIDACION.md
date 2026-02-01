---
id: GUIA_3_CAPAS_VALIDACION_V2
titulo: Guía de 3 Capas de Validación - Deducibilidad Integral
version: 2.0
fecha: 2026-01-31
agentes: [A1, A3, A5, A6, A7, A8]
tags: [validacion, deducibilidad, materialidad, razon_negocios, evidencia]
---

# Guía de Validación: 3 Capas de Deducibilidad

## Modelo de Validación

Toda operación de servicios debe validarse en **tres capas**:

```
┌─────────────────────────────────────────────────────────────┐
│  CAPA 1: FORMAL-FISCAL                                      │
│  ├─ CFDI válido y vigente                                   │
│  ├─ Requisitos LISR 27                                      │
│  ├─ Requisitos LIVA 5 (IVA)                                 │
│  └─ CFF 29/29-A (comprobación)                              │
├─────────────────────────────────────────────────────────────┤
│  CAPA 2: MATERIALIDAD (CFF 69-B)                            │
│  ├─ Proveedor fuera de lista 69-B                           │
│  ├─ Evidencia de prestación efectiva                        │
│  └─ Cadena documental completa                              │
├─────────────────────────────────────────────────────────────┤
│  CAPA 3: RAZÓN DE NEGOCIOS (CFF 5-A)                        │
│  ├─ Propósito económico documentado                         │
│  ├─ Vinculación con actividad del contribuyente             │
│  └─ Justificación gerencial                                 │
└─────────────────────────────────────────────────────────────┘
```

---

## Capa 1: Formal-Fiscal

### LISR 27 - Checklist de Requisitos

| Fracción | Requisito | Condición Lógica | Evidencia Mínima |
|----------|-----------|------------------|------------------|
| **I** | Estrictamente indispensable | Gasto vinculado al giro | Contrato + descripción del servicio |
| **III** | Amparado con CFDI | UUID válido en SAT | Consulta validador CFDI |
| **IV** | Forma de pago | >$2,000 bancarizado | Estado de cuenta bancario |
| **V** | Retenciones | ISR/IVA retenido si aplica | Constancia de retención |
| **XVIII** | Registro contable | Póliza con CFDI vinculado | Póliza contable |
| **XIX** | Partes relacionadas | Precio de mercado | Estudio de precios de transferencia |

### LIVA 5 - Acreditamiento IVA

| Requisito | Condición | Evidencia |
|-----------|-----------|-----------|
| IVA trasladado | Campo en CFDI | CFDI con desglose |
| IVA pagado | Erogación efectiva | Estado de cuenta |
| Gasto deducible ISR | Cumple capa 1 | Análisis integral |

### CFF 29/29-A - Comprobación

| Elemento CFDI | Validación |
|---------------|------------|
| UUID | Vigente en SAT |
| RFC Emisor | Válido, no en 69-B definitivo |
| UsoCFDI | Coherente con tipo de gasto |
| ClaveProdServ | Corresponde al servicio real |
| ObjetoImp | Correctamente configurado |

---

## Capa 2: Materialidad

### Validación de Proveedor

| Check | Fuente | Riesgo si falla |
|-------|--------|-----------------|
| No en lista 69-B | SAT portal | 🔴 CRÍTICO |
| Opinión 32-D positiva | SAT portal | 🟡 ALTO (si aplica) |
| RFC activo | SAT | 🔴 CRÍTICO |
| Registro REPSE | STPS (si aplica) | 🔴 CRÍTICO |

### Evidencia de Prestación Efectiva

| Tipo de Evidencia | Descripción | Peso Probatorio |
|-------------------|-------------|-----------------|
| **Contrato/SOW** | Descripción detallada de servicios | ⭐⭐ |
| **Orden de trabajo** | Solicitud formal del servicio | ⭐⭐ |
| **Entregables** | Reportes, informes, productos | ⭐⭐⭐ |
| **Correos/comunicaciones** | Gestión del servicio | ⭐⭐ |
| **Actas de recepción** | Conformidad del cliente | ⭐⭐⭐ |
| **Logs/registros** | Uso de sistemas, accesos | ⭐⭐ |
| **Pagos bancarizados** | Transferencias identificables | ⭐⭐⭐ |

### Banderas de Riesgo Materialidad

```python
def evaluar_materialidad(operacion):
    banderas = []
    
    if proveedor_en_lista_69b(operacion.rfc_emisor):
        banderas.append("🔴 PROVEEDOR EN LISTA 69-B")
    
    if sin_entregables(operacion):
        banderas.append("🟡 SIN ENTREGABLES DOCUMENTADOS")
    
    if solo_cfdi_contrato(operacion):
        banderas.append("🟡 SOLO CFDI Y CONTRATO - DÉBIL")
    
    if proveedor_sin_infraestructura(operacion):
        banderas.append("🟡 PROVEEDOR SIN CAPACIDAD APARENTE")
    
    if descripcion_generica(operacion.cfdi.concepto):
        banderas.append("🟡 DESCRIPCIÓN GENÉRICA EN CFDI")
    
    return banderas
```

---

## Capa 3: Razón de Negocios

### Preguntas de Validación

| Pregunta | Respuesta Esperada |
|----------|-------------------|
| ¿Qué problema de negocio resuelve? | Descripción concreta de necesidad |
| ¿Qué pasaría sin este servicio? | Impacto operativo identificable |
| ¿Quién aprobó la contratación? | Evidencia de decisión gerencial |
| ¿El precio es razonable? | Comparables o justificación |

### Evidencia Documental

| Documento | Propósito |
|-----------|-----------|
| Memorando/minuta interna | Justificación de la necesidad |
| Aprobación de directivos | Cadena de autorización |
| Análisis costo-beneficio | Evaluación económica |
| KPIs afectados | Vinculación con resultados |
| Comparativos de mercado | Justificación del proveedor |

### Banderas de Riesgo Razón de Negocios

```python
def evaluar_razon_negocios(operacion):
    banderas = []
    
    if sin_aprobacion_gerencial(operacion):
        banderas.append("🟡 SIN APROBACIÓN DOCUMENTADA")
    
    if beneficio_solo_fiscal(operacion):
        banderas.append("🔴 SOLO BENEFICIO FISCAL APARENTE")
    
    if precio_fuera_mercado(operacion):
        banderas.append("🟡 PRECIO FUERA DE MERCADO")
    
    if proveedor_parte_relacionada(operacion) and sin_tp(operacion):
        banderas.append("🟡 PARTE RELACIONADA SIN TP")
    
    return banderas
```

---

## Semáforo de Deducibilidad

### Resultado Consolidado

| Color | Significado | Criterio |
|-------|-------------|----------|
| 🟢 **VERDE** | Deducible | Cumple 3 capas con evidencia robusta |
| 🟡 **AMARILLO** | Revisar | Formales OK, débil en materialidad o razón de negocios |
| 🔴 **ROJO** | No deducible | Proveedor 69-B, sin CFDI válido, o sin evidencia mínima |

### Matriz de Decisión

| Capa 1 | Capa 2 | Capa 3 | Resultado |
|--------|--------|--------|-----------|
| ✅ | ✅ | ✅ | 🟢 VERDE |
| ✅ | ✅ | ⚠️ | 🟡 AMARILLO |
| ✅ | ⚠️ | ✅ | 🟡 AMARILLO |
| ✅ | ⚠️ | ⚠️ | 🟡 AMARILLO (con alerta) |
| ❌ | cualquier | cualquier | 🔴 ROJO |
| cualquier | ❌ | cualquier | 🔴 ROJO |

---

## Evidencias Mínimas por Tipo de Servicio

### Servicios de Consultoría/Asesoría

| Evidencia | Obligatoria |
|-----------|-------------|
| Contrato con alcance específico | ✅ |
| Entregables (reportes, informes) | ✅ |
| Correos de gestión/revisión | ✅ |
| Acta de recepción conformidad | Recomendada |

### Servicios de TI/Desarrollo

| Evidencia | Obligatoria |
|-----------|-------------|
| SOW/Orden de trabajo | ✅ |
| Código fuente/sistema entregado | ✅ |
| Logs de acceso/desarrollo | ✅ |
| Documentación técnica | Recomendada |

### Servicios de Marketing/Publicidad

| Evidencia | Obligatoria |
|-----------|-------------|
| Brief de campaña | ✅ |
| Materiales producidos | ✅ |
| Reportes de métricas | ✅ |
| Facturas de medios | Recomendada |

### Servicios de Outsourcing/REPSE

| Evidencia | Obligatoria |
|-----------|-------------|
| Contrato de subcontratación | ✅ |
| Registro REPSE vigente | ✅ |
| Listas de personal | ✅ |
| Constancias IMSS/INFONAVIT | ✅ |

---

## Referencias Normativas

- `@LISR_27_I` a `@LISR_27_XIX` - Requisitos de deducciones
- `@CFF_5A` - Razón de negocios
- `@CFF_69B` - Materialidad/EFOS
- `@LIVA_5` - Acreditamiento IVA
- `@NOM151` - Conservación electrónica

---

**Versión:** 2.0 | **Fecha:** 2026-01-31
