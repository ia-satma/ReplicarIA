---
id: LISR_25
ley: Ley del Impuesto sobre la Renta
articulo: 25
titulo: Deducciones autorizadas
tags: [deducciones, autorizadas, catalogo, A3]
prioridad: alta
---

# @LISR_25 - Deducciones Autorizadas

## [NORMA]

**Artículo 25.** Los contribuyentes podrán efectuar las deducciones siguientes:

**I.** Las devoluciones que se reciban o los descuentos o bonificaciones 
que se hagan en el ejercicio.

**II.** El costo de lo vendido.

**III.** Los gastos netos de descuentos, bonificaciones o devoluciones.

**IV.** Las inversiones.

**V.** Los créditos incobrables y las pérdidas por caso fortuito, fuerza 
mayor o por enajenación de bienes distintos a los que se refiere el primer 
párrafo de la fracción II de este artículo.

**VI.** Las cuotas a cargo de los patrones pagadas al Instituto Mexicano 
del Seguro Social, incluidas las previstas en la Ley del Seguro de Desempleo.

**VII.** Los intereses devengados a cargo en el ejercicio, sin ajuste alguno.

**VIII.** El ajuste anual por inflación que resulte deducible.

**IX.** Los anticipos y los rendimientos que paguen las sociedades 
cooperativas de producción, así como los anticipos que entreguen las 
sociedades y asociaciones civiles a sus miembros.

**X.** Las aportaciones efectuadas para la creación o incremento de 
reservas para fondos de pensiones o jubilaciones del personal.

**Fuente:** https://www.diputados.gob.mx/LeyesBiblio/pdf/LISR.pdf

---

## [INTERPRETACIÓN REVISAR-IA]

### Catálogo de Deducciones:

Este artículo establece **QUÉ** se puede deducir. El artículo 27 establece 
los **REQUISITOS** que deben cumplir esas deducciones.

### Mapeo de gastos comunes:

| Tipo de gasto | Fracción aplicable | Notas |
|---------------|-------------------|-------|
| Compras de mercancía | II - Costo vendido | COGS |
| Servicios profesionales | III - Gastos | Honorarios, consultoría |
| Arrendamiento | III - Gastos | Rentas de oficina, equipo |
| Publicidad | III - Gastos | Marketing, promoción |
| Viáticos | III - Gastos | Con límites Art. 28 |
| Equipo de cómputo | IV - Inversiones | Depreciación 30% anual |
| Vehículos | IV - Inversiones | Límite $175,000 |
| Sueldos y salarios | III - Gastos | Nómina |
| IMSS patronal | VI - Cuotas IMSS | Seguro social |
| Intereses bancarios | VII - Intereses | Créditos |
| Cuentas incobrables | V - Créditos incobrables | Con requisitos |

### Uso por A3 en análisis:

Cuando A3 analiza un gasto, primero debe ubicar en qué fracción encaja:

```
CLASIFICACIÓN DE GASTO

Concepto: Servicio de consultoría fiscal
Monto: $50,000 + IVA
Proveedor: Consultores ABC, SA de CV

ANÁLISIS LISR 25:
✓ Aplica Fracción III (Gastos)
✓ Es gasto operativo del ejercicio
✓ Procede a verificar requisitos Art. 27
```

### Relación Art. 25 vs Art. 27 vs Art. 28:

```
Art. 25: ¿QUÉ puedo deducir?
    │
    ↓
Art. 27: ¿CÓMO debe cumplirse para deducir?
    │
    ↓
Art. 28: ¿QUÉ NO puedo deducir aunque cumpla requisitos?
```

### Checklist de clasificación:

```
PASO 1: CLASIFICAR EN ART. 25

□ ¿Es devolución/descuento? → Fr. I
□ ¿Es costo de mercancía vendida? → Fr. II
□ ¿Es gasto operativo? → Fr. III
□ ¿Es inversión (activo fijo)? → Fr. IV
□ ¿Es cuenta incobrable/pérdida? → Fr. V
□ ¿Es cuota IMSS? → Fr. VI
□ ¿Es interés de crédito? → Fr. VII
□ ¿Es ajuste inflacionario? → Fr. VIII
□ ¿Es anticipo a socios cooperativa? → Fr. IX
□ ¿Es fondo de pensiones? → Fr. X

PASO 2: VERIFICAR REQUISITOS ART. 27

PASO 3: VERIFICAR QUE NO ESTÉ EN ART. 28
```

### Inversiones (Fracción IV):

Las inversiones se deducen mediante depreciación:

| Tipo de activo | Tasa anual | Fundamento |
|----------------|------------|------------|
| Construcciones | 5% | LISR 34 |
| Maquinaria industrial | 10% | LISR 35 |
| Mobiliario | 10% | LISR 35 |
| Equipo de transporte | 25% | LISR 35 |
| Equipo de cómputo | 30% | LISR 35 |
| Automóviles | 25% | Tope $175,000 |

### Costo de lo vendido (Fracción II):

Para empresas comerciales o manufactureras, el costo de lo vendido 
incluye:

- Adquisición de mercancías
- Materias primas
- Mano de obra directa (manufactura)
- Gastos indirectos de producción

---

## Referencias cruzadas

- @LISR_27 (Requisitos de deducciones)
- @LISR_28 (Gastos no deducibles)
- @LISR_27_I (Estrictamente indispensable)
- @LISR_27_III (Amparado con CFDI)
