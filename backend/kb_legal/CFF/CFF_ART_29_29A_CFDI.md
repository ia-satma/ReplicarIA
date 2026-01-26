---
id: CFF_29_29A
ley: Código Fiscal de la Federación
articulos: 29, 29-A
titulo: Obligación y requisitos de CFDI
tags: [cfdi, factura, comprobante, requisitos, A3]
prioridad: critica
---

# @CFF_29 y @CFF_29A - Comprobantes Fiscales Digitales por Internet

## [NORMA]

### Artículo 29 - Obligación de expedir CFDI

**Artículo 29.** Cuando las leyes fiscales establezcan la obligación de expedir 
comprobantes fiscales por los actos o actividades que realicen, por los ingresos 
que se perciban o por las retenciones de contribuciones que efectúen, los 
contribuyentes deberán emitirlos mediante documentos digitales a través de la 
página de Internet del Servicio de Administración Tributaria.

Los comprobantes fiscales digitales deberán contener el sello digital del 
contribuyente que lo expida, el cual deberá estar amparado por un certificado 
expedido por el SAT.

### Artículo 29-A - Requisitos de los CFDI

**Artículo 29-A.** Los comprobantes fiscales digitales a que se refiere el 
artículo 29 de este Código, deberán contener los siguientes requisitos:

**I.** La clave del registro federal de contribuyentes de quien los expida y 
el régimen fiscal en que tributen.

**II.** El número de folio y el sello digital del SAT, así como el sello digital 
del contribuyente que lo expide.

**III.** El lugar y fecha de expedición.

**IV.** La clave del registro federal de contribuyentes de la persona a favor 
de quien se expida.

**V.** La cantidad, unidad de medida y clase de los bienes o mercancías o 
descripción del servicio o del uso o goce que amparen.

**VI.** El valor unitario consignado en número.

**VII.** El importe total consignado en número o letra.

**VIII.** Tratándose de mercancías de importación: número y fecha del documento 
aduanero, así como la aduana por la cual se realizó la importación.

**IX.** Los contenidos en las disposiciones fiscales, que sean requeridos y dé 
a conocer el SAT mediante reglas de carácter general.

**Fuente:** https://www.diputados.gob.mx/LeyesBiblio/pdf/CFF.pdf

---

## [INTERPRETACIÓN REVISAR-IA]

### Uso por Agentes:

| Agente | Cómo lo usa |
|--------|-------------|
| **A3 (Revisar.IA)** | Valida que cada CFDI cumpla todos los requisitos del 29-A |
| **A6 (Tráfico.IA)** | Verifica RFC del emisor y datos del proveedor |
| **A7 (Auditar.IA)** | Documenta cumplimiento de requisitos en Defense File |

### Checklist de validación CFDI (Art. 29-A):

```
✓ Fracción I   - RFC emisor válido y régimen fiscal correcto
✓ Fracción II  - UUID (folio fiscal) y sellos digitales
✓ Fracción III - Lugar y fecha de expedición
✓ Fracción IV  - RFC receptor correcto
✓ Fracción V   - Descripción clara del servicio/bien
✓ Fracción VI  - Valor unitario numérico
✓ Fracción VII - Importe total
✓ Fracción VIII - Datos aduaneros (si aplica importación)
✓ Fracción IX  - Requisitos adicionales RMF
```

### Validaciones automáticas de A3:

| Elemento | Validación | Consecuencia si falla |
|----------|------------|----------------------|
| UUID | Existe en SAT | CFDI inválido |
| Status | Vigente | No deducible si cancelado |
| RFC emisor | Activo, no en lista 69-B | Ver @CFF_69B |
| RFC receptor | Coincide con contribuyente | Error de emisión |
| Uso CFDI | Apropiado para la operación | Revisar código |
| Método pago | PUE (inmediato) o PPD (diferido) | Afecta momento de deducción |
| Forma pago | Correcta vs monto (>$2,000) | @LISR_27_IV |

### Campos críticos para deducibilidad:

1. **UUID (Folio Fiscal)**
   - Identificador único de 36 caracteres
   - Formato: 8-4-4-4-12 (ej: 8A3D4F2E-1234-5678-90AB-CDEF12345678)
   - Valida existencia y vigencia en SAT

2. **Uso de CFDI**
   - G01: Adquisición de mercancías
   - G02: Devoluciones, descuentos o bonificaciones
   - G03: Gastos en general
   - I01: Construcciones
   - D01-D10: Deducciones personales

3. **Método de pago**
   - PUE: Pago en Una sola Exhibición
   - PPD: Pago en Parcialidades o Diferido
   - PPD requiere complemento de pago para deducir

4. **Forma de pago**
   - 01: Efectivo (≤$2,000 para deducir)
   - 02: Cheque nominativo
   - 03: Transferencia electrónica
   - 04: Tarjeta de crédito
   - 99: Por definir (requiere complemento)

### Errores comunes que invalidan CFDI:

| Error | Impacto | Solución |
|-------|---------|----------|
| RFC incorrecto | No deducible | Solicitar sustitución |
| CFDI cancelado | Inválido | Solicitar nuevo CFDI |
| Descripción genérica | Riesgo fiscal | Solicitar complemento |
| Forma pago incorrecta | No deducible | Verificar antes de recibir |

### Ejemplo de análisis A3:

> **CFDI analizado:**
> - UUID: 8A3D4F2E-1234-5678-90AB-CDEF12345678
> - Emisor: ABC SERVICIOS SA DE CV (RFC: ABC123456789)
> - Receptor: CLIENTE SA DE CV
> - Concepto: "Servicios de consultoría fiscal"
> - Subtotal: $50,000.00
> - IVA: $8,000.00
> - Total: $58,000.00
> - Forma pago: 03 (Transferencia)
> - Uso CFDI: G03 (Gastos en general)
>
> **Validación A3:**
> ✅ UUID válido y vigente en SAT
> ✅ RFC emisor activo, no en lista 69-B
> ✅ Descripción específica del servicio
> ✅ Forma de pago correcta (transferencia)
> ⚠️ Revisar: ¿Existe contrato de servicios?
> ⚠️ Revisar: ¿Hay entregables documentados?
>
> **Conclusión:** CFDI VÁLIDO - Pendiente documentación de materialidad

---

## Referencias cruzadas

- @LISR_27_III (Amparadas con CFDI)
- @LISR_27_IV (Forma de pago)
- @CFF_69B (EFOS - verificar emisor)
- @LIVA_5 (Requisitos acreditamiento IVA)
