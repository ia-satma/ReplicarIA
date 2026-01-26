---
id: CFF_69B
ley: Código Fiscal de la Federación
articulo: 69-B
titulo: Operaciones inexistentes (EFOS/EDOS)
tags: [efos, edos, materialidad, 69b, lista_negra, A3, A6, A7]
prioridad: critica
---

# @CFF_69B - Operaciones Inexistentes (EFOS/EDOS)

## [NORMA]

**Artículo 69-B.** Cuando la autoridad fiscal detecte que un contribuyente ha 
estado emitiendo comprobantes sin contar con los activos, personal, infraestructura 
o capacidad material, directa o indirectamente, para prestar los servicios o 
producir, comercializar o entregar los bienes que amparan tales comprobantes, 
o bien, que dichos contribuyentes se encuentren no localizados, se presumirá 
la inexistencia de las operaciones amparadas en tales comprobantes.

**Los contribuyentes que hayan dado cualquier efecto fiscal a los comprobantes 
fiscales expedidos por un contribuyente incluido en el listado a que se refiere 
el cuarto párrafo de este artículo, contarán con treinta días siguientes al de 
la citada publicación para acreditar ante la propia autoridad, que efectivamente 
adquirieron los bienes o recibieron los servicios que amparan los citados 
comprobantes fiscales, o bien procederán en el mismo plazo a corregir su 
situación fiscal...**

**Fuente:** https://www.diputados.gob.mx/LeyesBiblio/pdf/CFF.pdf

---

## [INTERPRETACIÓN REVISAR-IA]

### Procedimiento 69-B:

```
1. SAT detecta indicios de EFOS
         ↓
2. Publica en DOF como "PRESUNTO" (1er listado)
         ↓
3. Contribuyente tiene 15 días para aportar pruebas
         ↓
4. Si no desvirtúa → Publica como "DEFINITIVO" (2do listado)
         ↓
5. Clientes del EFOS tienen 30 días para:
   a) Acreditar materialidad, O
   b) Autocorregirse
```

### Uso por Agentes:

| Agente | Acción |
|--------|--------|
| **A3** | Verifica si proveedor está en lista 69-B (presunto/definitivo) |
| **A6** | Consulta automática de Lista 69-B para cada proveedor |
| **A7** | Prepara Defense File con evidencia de materialidad |

### Evidencia de materialidad requerida:

1. **Capacidad del proveedor**
   - ¿Tiene empleados?
   - ¿Tiene infraestructura?
   - ¿Tiene domicilio localizable?

2. **Realidad de la operación**
   - Contrato firmado
   - Entregables recibidos
   - Evidencia fotográfica (si aplica)
   - Comunicaciones (emails, WhatsApp)

3. **Flujo financiero**
   - Pago por transferencia bancaria
   - Estado de cuenta mostrando el pago
   - Conciliación bancaria

4. **Razonabilidad**
   - Precio de mercado
   - Relación comercial previa
   - Necesidad del servicio/bien

### Niveles de riesgo para A3:

| Status proveedor | Riesgo | Acción |
|------------------|--------|--------|
| No publicado | ✅ Bajo | Documentar materialidad preventivamente |
| Presunto | ⚠️ Alto | Preparar defensa, juntar evidencia YA |
| Definitivo | 🔴 Crítico | 30 días para acreditar o autocorregir |
| Desvirtuado | ✅ OK | Conservar constancia de desvirtuación |
| Sentencia favorable | ✅ OK | Conservar sentencia |

### Consecuencias si no se acredita:

- Rechazo de deducción
- Rechazo de acreditamiento de IVA
- Posible responsabilidad solidaria
- Multas 55% al 75% de contribuciones omitidas

---

## Referencias cruzadas

- @CFF_5 (Interpretación estricta)
- @LISR_27_I (Estrictamente indispensable)
- @LISR_27_III (Amparadas con CFDI)
