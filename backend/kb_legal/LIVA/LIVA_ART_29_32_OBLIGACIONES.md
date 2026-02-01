---
id: LIVA_ART_29_32
titulo: Ley del IVA - Obligaciones Formales
version: 1.0
fecha: 2026-01-31
url_oficial: https://www.diputados.gob.mx/LeyesBiblio/pdf/LIVA.pdf
agentes: [A3, A5]
tags: [LIVA, IVA, obligaciones, CFDI, declaraciones]
---

# LIVA: Obligaciones Formales (Arts. 29, 32)

## Artículo 29 - Exportación de Servicios

### Servicios que se consideran exportados (tasa 0%):

| Fracción | Servicio |
|----------|----------|
| I | Asistencia técnica, transferencia de tecnología a residentes en extranjero |
| II | Publicidad para difusión en el extranjero |
| III | Comisiones por ventas de exportación |
| IV | Seguros y reaseguros sobre bienes exportados |
| V | Operaciones de financiamiento con residentes en extranjero |
| VI | Filmación, procesamiento de películas para proyección en extranjero |
| VII | Servicios de hotelería y turismo a convenciones internacionales |

### Requisitos para tasa 0%:
1. Que el servicio se aproveche totalmente en el extranjero
2. Pago mediante transferencia o cheque nominativo
3. Conservar documentación comprobatoria

---

## Artículo 32 - Obligaciones de los Contribuyentes

### Obligaciones principales:

| Fracción | Obligación |
|----------|------------|
| **I** | Llevar contabilidad conforme al CFF |
| **II** | Separar operaciones gravadas de exentas |
| **III** | Expedir CFDI con IVA trasladado expresamente |
| **IV** | Presentar declaraciones (mensual provisional, anual informativa) |
| **V** | Proporcionar información sobre clientes y proveedores |
| **VI** | Expedir constancias de retención |
| **VII** | Presentar DIOT (Declaración Informativa de Operaciones con Terceros) |

---

## CFDI y Traslado del IVA

> **Requisito crítico:** El IVA debe estar **trasladado expresamente y por separado** 
> en el CFDI para ser acreditable.

### Elementos obligatorios en CFDI:
```
- Importe base gravable
- Tasa aplicable (16%, 8%, 0%)
- Monto del IVA trasladado
- Tipo de factor: Tasa
- Objeto del impuesto: 01, 02, 03
```

---

## DIOT - Declaración Informativa

### Contenido:
- RFC de terceros (proveedores)
- Montos de operaciones
- IVA pagado
- País de residencia (si extranjero)

### Plazo:
- Mensual, a más tardar el día 17 del mes siguiente

### Consecuencia de omisión:
```
⚠️ Sin DIOT presentada, el SAT puede rechazar 
   el acreditamiento del IVA aunque esté pagado.
```

---

## Implicaciones para Revisar.IA

### Checklist de validación IVA (A3):

```
□ ¿CFDI tiene IVA trasladado expresamente?
□ ¿Tasa correcta según tipo de operación?
□ ¿Objeto del impuesto correcto (01=Sí objeto, 02=No objeto)?
□ ¿Operación incluida en DIOT del periodo?
□ ¿Pago efectivamente realizado en el periodo?
```

---

## Referencias Cruzadas

- `@LIVA_5` - Requisitos de acreditamiento
- `@CFF_29_29A` - Requisitos de CFDI
- `@LISR_27_III` - Amparado con comprobante fiscal

---

**Fuente:** [LIVA Texto Vigente](https://www.diputados.gob.mx/LeyesBiblio/pdf/LIVA.pdf)
