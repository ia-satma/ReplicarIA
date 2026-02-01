---
id: SERVICIOS_SAT_URLS
titulo: Servicios en Línea del SAT - Referencias para Validación
version: 1.0
fecha: 2026-01-31
agentes: [A5, A6]
tags: [SAT, servicios, 69B, 32D, CFDI, validador, consultas]
---

# Servicios SAT: URLs de Consulta en Línea

## 1. Lista 69-B CFF (EFOS/EDOS)

### Descripción
Listado de contribuyentes con operaciones presuntamente inexistentes o definitivamente inexistentes.

| Campo | Valor |
|-------|-------|
| **URL** | https://www.sat.gob.mx/consultas/45288/consulta-la-relacion-de-contribuyentes-con-operaciones-presuntamente-inexistentes |
| **Fundamento** | Art. 69-B CFF |
| **Agentes** | A6 (validación proveedores), A3 (riesgo deducibilidad) |

### Tipos de listados:
| Tipo | Significado |
|------|-------------|
| **Presuntos** | En proceso de aclaración, 30 días para desvirtuar |
| **Definitivos** | Sin aclaración válida, operaciones INEXISTENTES |
| **Desvirtuados** | Aclararon presunción satisfactoriamente |
| **Sentencia favorable** | Ganaron juicio contra la presunción |

### Uso en sistema:
```python
# Validación automática de proveedor
if proveedor_rfc in lista_69b_definitivos:
    return {
        "deducible": False,
        "riesgo": "CRÍTICO",
        "fundamento": "@CFF_69B",
        "accion": "Rechazar CFDI - proveedor en lista definitiva"
    }
```

---

## 2. Opinión de Cumplimiento (Art. 32-D CFF)

### Descripción
Consulta del estatus de cumplimiento de obligaciones fiscales de un contribuyente.

| Campo | Valor |
|-------|-------|
| **URL** | https://www.sat.gob.mx/consultas/20777/consulta-tu-opinion-de-cumplimiento-de-obligaciones-fiscales |
| **Fundamento** | Art. 32-D CFF |
| **Agentes** | A6 (validación proveedores) |

### Resultados posibles:
| Resultado | Significado |
|-----------|-------------|
| **Positiva** | Cumple con obligaciones fiscales |
| **Negativa** | Tiene incumplimientos pendientes |
| **En proceso** | Aclaración en trámite |

### Uso en sistema:
```python
# Validación para contratos con gobierno (obligatorio)
if contrato_gobierno and opinion != "POSITIVA":
    return {
        "viable": False,
        "riesgo": "ALTO",
        "fundamento": "@CFF_32D",
        "accion": "No procede contratación sin opinión positiva"
    }
```

---

## 3. Validador de CFDI

### Descripción
Verificación de autenticidad y vigencia de un CFDI ante el SAT.

| Campo | Valor |
|-------|-------|
| **URL** | https://verificacfdi.facturaelectronica.sat.gob.mx/ |
| **Fundamento** | Art. 29-A CFF, RMF 2.7.1 |
| **Agentes** | A5 (validación CFDI) |

### Parámetros de consulta:
| Dato | Descripción |
|------|-------------|
| **UUID** | Folio fiscal del CFDI |
| **RFC Emisor** | RFC de quien expidió |
| **RFC Receptor** | RFC de quien recibió |
| **Total** | Monto total del CFDI |

### Estados posibles:
| Estado | Significado | Deducible |
|--------|-------------|-----------|
| **Vigente** | CFDI válido y activo | ✅ Sí |
| **Cancelado** | CFDI anulado | ❌ No |
| **No encontrado** | UUID inválido o apócrifo | ❌ No |

### Uso en sistema:
```python
# Validación antes de registrar gasto
resultado = validar_cfdi_sat(uuid, rfc_emisor, rfc_receptor, total)
if resultado.status != "VIGENTE":
    return {
        "deducible": False,
        "riesgo": "CRÍTICO",
        "fundamento": "@LISR_27_III",
        "accion": f"CFDI {resultado.status} - no deducible"
    }
```

---

## 4. Consulta de RFC

### Descripción
Verificación de validez de un RFC y datos fiscales básicos.

| Campo | Valor |
|-------|-------|
| **URL** | https://www.sat.gob.mx/aplicacion/operacion/31274/consulta-tu-clave-de-rfc-mediante-curp |
| **Fundamento** | Art. 27 CFF |
| **Agentes** | A6 (validación proveedores) |

---

## 5. Consulta de Catálogos SAT

### Descripción
Catálogos oficiales para llenado de CFDI (productos, servicios, unidades, etc.).

| Campo | Valor |
|-------|-------|
| **URL** | http://pys.sat.gob.mx/PyS/catPyS.aspx |
| **Fundamento** | Anexo 20 RMF |
| **Agentes** | A5 (validación CFDI) |

---

## 6. Documentos Técnicos CFDI (Anexo 20)

### Descripción
Especificaciones técnicas del CFDI 4.0 (esquemas XSD, guías de llenado).

| Campo | Valor |
|-------|-------|
| **URL** | https://www.sat.gob.mx/consulta/70515/consulta-los-documentos-tecnicos-del-cfdi |
| **Fundamento** | RMF Anexo 20 |
| **Agentes** | A5 (validación técnica) |

---

## Integración con Sistema

### Frecuencia de consulta recomendada:

| Servicio | Frecuencia | Caché |
|----------|------------|-------|
| Lista 69-B | Semanal (batch) | Sí, 7 días |
| Opinión 32-D | Por operación | No caché |
| Validador CFDI | Por CFDI nuevo | Sí, permanente |
| RFC | Por proveedor nuevo | Sí, 30 días |

---

## Referencias Cruzadas

- `@CFF_69B` - EFOS/Materialidad
- `@CFF_32D` - Opinión de cumplimiento
- `@CFF_29_29A` - Requisitos CFDI
- `@LISR_27_III` - Amparado con comprobante fiscal

---

**Nota:** Estos servicios son dinámicos y pueden requerir autenticación con e.firma para ciertas consultas.
