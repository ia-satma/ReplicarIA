---
id: LIVA_5
ley: Ley del Impuesto al Valor Agregado
articulo: 5
titulo: Acreditamiento del IVA
tags: [iva, acreditamiento, A3, A5]
prioridad: critica
---

# @LIVA_5 - Acreditamiento del IVA

## [NORMA]

**Artículo 5o.** Para que sea acreditable el impuesto al valor agregado 
deberá reunir los siguientes requisitos:

**I.** Que el impuesto al valor agregado corresponda a bienes, servicios o 
al uso o goce temporal de bienes, estrictamente indispensables para la 
realización de actividades distintas de la importación, por las que se 
deba pagar el impuesto establecido en esta Ley o a las que se les aplique 
la tasa de 0%.

**II.** Que el impuesto al valor agregado haya sido trasladado expresamente 
al contribuyente y que conste por separado en los comprobantes fiscales.

**III.** Que el impuesto al valor agregado trasladado al contribuyente 
haya sido efectivamente pagado en el mes de que se trate.

**IV.** Que tratándose del impuesto al valor agregado trasladado que se 
hubiese retenido conforme al artículo 1o.-A de esta Ley, dicha retención 
se entere en los términos y plazos establecidos en la misma.

**V.** Cuando se esté obligado al pago del impuesto al valor agregado o 
cuando sea aplicable la tasa de 0%, sólo por una parte de las actividades 
que realice el contribuyente, se estará a lo siguiente:

a) Cuando el impuesto al valor agregado trasladado o pagado en la 
importación, corresponda a erogaciones por la adquisición de bienes 
distintos a las inversiones, por adquisición de servicios o por el uso 
o goce temporal de bienes, que se utilicen exclusivamente para realizar 
las actividades por las que se deba pagar el impuesto al valor agregado 
o les sea aplicable la tasa 0%, dicho impuesto será acreditable en su 
totalidad.

**Fuente:** https://www.diputados.gob.mx/LeyesBiblio/pdf/LIVA.pdf

---

## [INTERPRETACIÓN REVISAR-IA]

### Uso por Agentes:

| Agente | Cómo lo usa |
|--------|-------------|
| **A3 (Revisar.IA)** | Verifica requisitos de acreditamiento en cada CFDI |
| **A5 (Investigar.IA)** | Analiza proporcionalidad del IVA acreditable |
| **A7 (Auditar.IA)** | Documenta cumplimiento en Defense File |

### Requisitos para acreditamiento:

1. **Estrictamente indispensable**
   - El gasto debe ser necesario para la actividad gravada
   - Misma lógica que @LISR_27_I

2. **IVA trasladado expresamente**
   - Debe aparecer desglosado en el CFDI
   - Validar que el monto de IVA sea correcto (16%)

3. **Efectivamente pagado**
   - El pago debe haberse realizado en el mes
   - Cruzar con estados de cuenta bancarios

4. **CFDI válido**
   - UUID vigente (no cancelado)
   - RFC emisor activo
   - Datos fiscales correctos

### Checklist de A3 para acreditamiento de IVA:

```
□ ¿IVA desglosado en CFDI?
□ ¿Tasa correcta (16%, 8% frontera, 0%)?
□ ¿Pagado en el mes correspondiente?
□ ¿Corresponde a actividad gravada?
□ ¿Proveedor no está en lista 69-B?
□ ¿CFDI vigente (no cancelado)?
```

### Proporcionalidad (Fracción V):

Cuando el contribuyente realiza actividades mixtas (gravadas y exentas):

| Tipo de actividad | IVA acreditable |
|-------------------|-----------------|
| Solo gravadas (16%) | 100% acreditable |
| Solo exentas | 0% acreditable |
| Mixtas | Proporción según ingresos |

**Cálculo de proporción:**
```
Factor = Ingresos gravados / Total de ingresos
IVA acreditable = IVA pagado × Factor
```

### Consecuencias si no se cumple:

- Rechazo del acreditamiento
- IVA se convierte en gasto no deducible
- Posibles recargos y actualizaciones
- Multas del 55% al 75%

### Ejemplo de verificación:

> **CFDI analizado:**
> - Subtotal: $100,000.00
> - IVA: $16,000.00
> - Total: $116,000.00
>
> **Verificación A3:**
> ✅ IVA desglosado correctamente (16%)
> ✅ CFDI vigente
> ✅ Proveedor no en lista 69-B
> ⚠️ Verificar pago efectivo en el mes
>
> **Resultado:** IVA ACREDITABLE (pendiente confirmación de pago)

---

## Referencias cruzadas

- @LISR_27_I (Estrictamente indispensable)
- @LISR_27_III (Amparadas con CFDI)
- @CFF_29A (Requisitos de CFDI)
- @CFF_69B (EFOS/Materialidad)
