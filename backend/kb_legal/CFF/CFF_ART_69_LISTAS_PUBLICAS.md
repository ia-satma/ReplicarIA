---
id: CFF_69
ley: Código Fiscal de la Federación
articulo: 69
titulo: Publicación de contribuyentes incumplidos
tags: [listas, incumplidos, no_localizado, cancelado, A6, A3]
prioridad: alta
---

# @CFF_69 - Listas Públicas de Contribuyentes

## [NORMA]

**Artículo 69.** El personal oficial que intervenga en los diversos trámites 
relativos a la aplicación de las disposiciones tributarias estará obligado 
a guardar absoluta reserva en lo concerniente a las declaraciones y datos 
suministrados por los contribuyentes o por terceros con ellos relacionados.

**Excepciones (publicación permitida):**

El SAT publicará en su página de Internet el nombre, denominación o razón 
social y clave del RFC de quienes:

**I.** Tengan créditos fiscales firmes.

**II.** Tengan créditos fiscales exigibles no pagados ni garantizados.

**III.** Se les hubiera condonado algún crédito fiscal.

**IV.** Tengan sentencia condenatoria firme por delitos fiscales.

**V.** Tengan cancelado o condonado algún crédito y a quiénes se les 
hubiere aceptado propuesta de pago.

**VI.** Se les haya determinado la comisión de defraudación fiscal.

También se publicará la relación de contribuyentes que:
- No son localizados en su domicilio fiscal
- Se les canceló o suspendió el certificado de sello digital
- No desvirtuaron presunción de operaciones inexistentes (69-B)

**Fuente:** https://www.diputados.gob.mx/LeyesBiblio/pdf/CFF.pdf

---

## [INTERPRETACIÓN REVISAR-IA]

### Listas publicadas por el SAT:

| Lista | Contenido | URL SAT | Riesgo |
|-------|-----------|---------|--------|
| **Créditos firmes** | Adeudos definitivos | Portal SAT | 🔴 Alto |
| **Créditos exigibles** | Adeudos en cobro | Portal SAT | 🔴 Alto |
| **No localizados** | Sin domicilio | Portal SAT | 🔴 Crítico |
| **69-B Presuntos** | Presunta facturación falsa | DOF/SAT | 🔴 Crítico |
| **69-B Definitivos** | Confirmados EFOS | DOF/SAT | 🔴 Crítico |
| **Sentenciados** | Delitos fiscales | Portal SAT | 🔴 Crítico |

### Verificación automática A6:

```
CONSULTA DE LISTAS SAT

Proveedor: [NOMBRE]
RFC: [XXX]
Fecha consulta: [DD-MMM-AAAA]

□ Lista de créditos firmes:           [ ] NO APARECE  [ ] APARECE
□ Lista de créditos exigibles:        [ ] NO APARECE  [ ] APARECE
□ Lista de no localizados:            [ ] NO APARECE  [ ] APARECE
□ Lista 69-B presuntos:               [ ] NO APARECE  [ ] APARECE
□ Lista 69-B definitivos:             [ ] NO APARECE  [ ] APARECE
□ Lista de sentenciados:              [ ] NO APARECE  [ ] APARECE

RESULTADO GLOBAL: [ ] LIMPIO  [ ] CON ALERTAS
```

### Impacto por tipo de lista:

| Lista | Impacto en operaciones | Acción recomendada |
|-------|----------------------|-------------------|
| **Créditos firmes** | Riesgo de insolvencia | Evaluar garantías |
| **No localizado** | Alto riesgo EFOS | NO operar |
| **69-B Presunto** | CFDI en riesgo | Documentar materialidad |
| **69-B Definitivo** | CFDI rechazado | Autocorregirse o litigar |
| **Sentenciado** | Riesgo reputacional | NO operar |

### Consecuencias para el cliente:

Cuando un proveedor aparece en alguna lista:

1. **Lista de no localizados**
   - Alta probabilidad de EFOS
   - Operaciones probablemente cuestionadas
   - Riesgo de perder deducción

2. **Lista 69-B Presuntos**
   - 30 días para acreditar materialidad
   - O autocorregirse

3. **Lista 69-B Definitivos**
   - Operaciones consideradas inexistentes
   - Deducción improcedente (salvo litigio)

### Texto para Defense Files:

```
VERIFICACIÓN DE LISTAS PÚBLICAS SAT (Art. 69 CFF)

PROVEEDOR: [Nombre completo]
RFC: [XXX]

Verificación realizada el [fecha] en las siguientes listas:

1. Créditos fiscales firmes:     NO APARECE ✓
2. Créditos exigibles no pagados: NO APARECE ✓
3. Contribuyentes no localizados: NO APARECE ✓
4. Lista 69-B Presuntos:          NO APARECE ✓
5. Lista 69-B Definitivos:        NO APARECE ✓
6. Sentencias por delitos fiscales: NO APARECE ✓

CONCLUSIÓN: El proveedor no presenta alertas en las listas 
públicas del SAT al momento de la operación.

[Adjuntar evidencia de consulta - capturas de pantalla]
```

### URLs de consulta:

```
Portal SAT - Listas:
https://www.sat.gob.mx/consultas/lista-negra-69-b
https://www.sat.gob.mx/consultas/contribuyentes-incumplidos

DOF - Publicaciones 69-B:
https://www.dof.gob.mx/nota_detalle.php?codigo=[búsqueda]
```

### Diferencia entre Art. 69 y Art. 69-B:

| Aspecto | Art. 69 | Art. 69-B |
|---------|---------|-----------|
| **Enfoque** | Incumplimiento general | Operaciones inexistentes |
| **Listas** | Créditos, no localizados | EFOS presuntos/definitivos |
| **Impacto** | Riesgo de solvencia | Deducción improcedente |
| **Defensa** | Pago o garantía | Probar materialidad |

---

## Referencias cruzadas

- @CFF_69B (EFOS - Operaciones inexistentes)
- @CFF_32D (Opinión de cumplimiento)
- @TESIS_MAT_001 (Carga probatoria materialidad)
- @LISR_27_III (CFDI válido)
