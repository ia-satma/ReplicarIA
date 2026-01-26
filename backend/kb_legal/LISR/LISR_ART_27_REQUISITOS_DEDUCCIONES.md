---
id: LISR_27
ley: Ley del Impuesto sobre la Renta
articulo: 27
titulo: Requisitos de las deducciones
tags: [deducciones, requisitos, A1, A3, A5, A7]
prioridad: critica
---

# @LISR_27 - Requisitos de las Deducciones

## [NORMA]

**Artículo 27.** Las deducciones autorizadas en este Título deberán reunir 
los siguientes requisitos:

---

### Fracción I - Estrictamente indispensables @LISR_27_I

> **I.** Ser estrictamente indispensables para los fines de la actividad del 
> contribuyente, salvo que se trate de donativos no onerosos ni remunerativos...

**[INTERPRETACIÓN]**

| Agente | Uso |
|--------|-----|
| A1 | Evalúa si el gasto es necesario para el giro del negocio |
| A3 | Verifica relación gasto-actividad en cada CFDI |
| A7 | Justifica indispensabilidad en Defense File |

**Checklist de indispensabilidad:**
- [ ] ¿El gasto está relacionado con la actividad económica?
- [ ] ¿Sin este gasto, podría operar el negocio?
- [ ] ¿Es proporcional al tamaño/volumen de operaciones?
- [ ] ¿Hay evidencia de que se utilizó para generar ingresos?

---

### Fracción III - Amparadas con CFDI @LISR_27_III

> **III.** Estar amparadas con un comprobante fiscal y que los pagos cuyo 
> monto exceda de $2,000.00 se efectúen mediante transferencia electrónica...

**[INTERPRETACIÓN]**

**Requisitos del CFDI:**
- UUID válido y vigente
- RFC emisor correcto
- RFC receptor correcto
- Uso de CFDI apropiado
- Método de pago correcto (PUE/PPD)
- Forma de pago correcta

**Validaciones automáticas de A3:**
```
✓ CFDI existe en SAT
✓ Status: Vigente (no cancelado)
✓ RFC emisor activo
✓ Datos fiscales correctos
```

---

### Fracción IV - Forma de pago @LISR_27_IV

> **IV.** Estar debidamente registradas en contabilidad y que sean restadas 
> una sola vez...
> 
> Tratándose de pagos cuyo monto exceda de $2,000.00, éstos deberán efectuarse 
> mediante cheque nominativo, tarjeta de crédito, de débito, de servicios, 
> o monedero electrónico, o transferencia electrónica de fondos...

**[INTERPRETACIÓN]**

| Monto | Forma de pago requerida |
|-------|-------------------------|
| ≤ $2,000 | Cualquiera (incluso efectivo) |
| > $2,000 | Bancarizado obligatorio |

**Verificación de A3:**
- Forma de pago en CFDI vs monto
- Si > $2,000 y forma_pago = "01" (efectivo) → ⚠️ NO DEDUCIBLE

---

### Fracción XVIII - Registro en contabilidad @LISR_27_XVIII

> **XVIII.** Que al realizar las operaciones correspondientes o a más tardar 
> el último día del ejercicio se reúnan los requisitos que para cada deducción 
> en particular establece esta Ley...

**[INTERPRETACIÓN]**

**Evidencia requerida:**
- Póliza contable con referencia al CFDI
- Cuenta contable apropiada
- Fecha de registro dentro del ejercicio

---

### Fracción XIX - Partes relacionadas @LISR_27_XIX

> **XIX.** Que tratándose de pagos efectuados a personas morales que se 
> consideren partes relacionadas, el precio o monto de la contraprestación 
> sea igual al que hubieran pactado partes independientes en operaciones 
> comparables...

**[INTERPRETACIÓN]**

**CRÍTICO para servicios intra-grupo (management fees):**

| Verificación | Agente |
|--------------|--------|
| ¿Es parte relacionada? | A3, A6 |
| ¿Precio es de mercado? | A5 |
| ¿Hay estudio de precios de transferencia? | A3 |
| ¿Se documenta la metodología? | A7 |

**Riesgo si no se cumple:**
- Rechazo total de la deducción
- Ajuste a valores de mercado
- Posible recaracterización (@CFF_5A)

---

## Resumen: Checklist A3 para cada CFDI

```
□ @LISR_27_I   ¿Es estrictamente indispensable?
□ @LISR_27_III ¿Tiene CFDI válido y vigente?
□ @LISR_27_IV  ¿Forma de pago correcta (>$2,000 bancarizado)?
□ @LISR_27_XVIII ¿Registrado en contabilidad?
□ @LISR_27_XIX ¿Si es parte relacionada, precio de mercado?
□ @CFF_69B     ¿Proveedor NO está en lista 69-B?
□ @CFF_5A      ¿Tiene razón de negocios?
```

---

## Referencias cruzadas

- @LISR_25 (Deducciones autorizadas)
- @LISR_28 (Gastos no deducibles)
- @CFF_29A (Requisitos de CFDI)
- @CFF_5A (Razón de negocios)
- @CFF_69B (EFOS/Materialidad)
