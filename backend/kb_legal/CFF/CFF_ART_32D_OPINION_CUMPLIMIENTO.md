---
id: CFF_32D
ley: Código Fiscal de la Federación
articulo: 32-D
titulo: Opinión de cumplimiento de obligaciones fiscales
tags: [cumplimiento, opinion, 32d, proveedores, A6, A3]
prioridad: alta
---

# @CFF_32D - Opinión de Cumplimiento Fiscal

## [NORMA]

**Artículo 32-D.** La Administración Pública Federal, Centralizada y 
Paraestatal, así como la Procuraduría General de la República, en ningún 
caso contratarán adquisiciones, arrendamientos, servicios u obra pública 
con los particulares que:

**I.** Tengan a su cargo créditos fiscales firmes.

**II.** Tengan a su cargo créditos fiscales determinados, firmes o no, 
que no se encuentren pagados o garantizados en alguna de las formas 
permitidas por este Código.

**III.** No se encuentren inscritos en el Registro Federal de Contribuyentes.

**IV.** Habiendo vencido el plazo para presentar alguna declaración, 
provisional o del ejercicio, y con independencia de que en la misma 
resulte o no cantidad a pagar, ésta no haya sido presentada.

**V.** Habiendo vencido el plazo para expedir comprobantes fiscales 
digitales por Internet, la autoridad detecte que el contribuyente no 
los haya expedido o los haya expedido sin que cumplan con los requisitos.

**Fuente:** https://www.diputados.gob.mx/LeyesBiblio/pdf/CFF.pdf

---

## [INTERPRETACIÓN REVISAR-IA]

### Uso en Due Diligence de Proveedores (A6):

La opinión de cumplimiento 32-D es un documento esencial para verificar 
que un proveedor está al corriente con sus obligaciones fiscales.

### Cómo obtenerla:

```
Portal SAT → Otros trámites y servicios → Opinión del cumplimiento

URL: https://www.sat.gob.mx/aplicacion/operacion/53027/genera-tu-constancia-de-situacion-fiscal
```

### Resultados posibles:

| Resultado | Significado | Riesgo | Acción |
|-----------|-------------|--------|--------|
| **POSITIVA** | Cumple obligaciones | ✅ Bajo | Operar normalmente |
| **NEGATIVA** | No cumple obligaciones | 🔴 Alto | Evaluar continuar relación |
| **EN SUSPENSIÓN** | Suspensión de actividades | ⚠️ Medio | Verificar motivo |
| **NO INSCRITO** | No existe en RFC | 🔴 Crítico | No operar |

### Checklist de verificación A6:

```
VERIFICACIÓN DE PROVEEDOR - OPINIÓN 32-D

□ RFC del proveedor: ________________
□ Fecha de consulta: ________________
□ Resultado: [ ] Positiva [ ] Negativa [ ] Suspensión

SI POSITIVA:
  □ Vigencia de la opinión (30 días naturales)
  □ Archivar copia en expediente del proveedor

SI NEGATIVA:
  □ Verificar si es crédito fiscal en garantía
  □ Solicitar aclaración al proveedor
  □ Evaluar riesgo de continuar operaciones
  □ Documentar decisión empresarial
```

### Vigencia y periodicidad:

| Concepto | Detalle |
|----------|---------|
| Vigencia | 30 días naturales desde emisión |
| Consulta recomendada | Antes de cada pago significativo |
| Archivo | Conservar con documentación del CFDI |

### Impacto en deducibilidad:

Una opinión 32-D negativa **no invalida automáticamente** la deducción, 
pero representa un **riesgo elevado** que la autoridad puede considerar:

1. **Riesgo de proveedor con problemas fiscales**
2. **Posible inclusión futura en lista 69-B**
3. **Cuestionamiento de due diligence**

### Uso en Defense Files (A7):

Cuando el SAT cuestiona operaciones con un proveedor, la opinión 32-D 
positiva al momento de la operación demuestra:

```
EVIDENCIA DE DUE DILIGENCE

El contribuyente solicitó opinión de cumplimiento 32-D del proveedor
[NOMBRE] con RFC [XXX] previo a la contratación.

Resultado: POSITIVA
Fecha de consulta: [DD-MMM-AAAA]
Vigente al momento de la operación: SÍ

Este documento acredita que el contribuyente actuó con la debida 
diligencia al verificar el cumplimiento fiscal de su proveedor, 
conforme al artículo 32-D del CFF.

[Adjuntar copia de la opinión]
```

### Señales de alerta si opinión es negativa:

| Señal | Riesgo | Recomendación |
|-------|--------|---------------|
| Créditos fiscales firmes | Alto | Evitar operaciones |
| Declaraciones no presentadas | Medio-Alto | Solicitar regularización |
| No localizado | Crítico | No operar bajo ningún concepto |
| Suspensión de actividades | Alto | Verificar fecha de suspensión |

### Relación con otras verificaciones:

```
VERIFICACIÓN COMPLETA DE PROVEEDOR

1. Opinión 32-D (@CFF_32D)
   ├── Estado de cumplimiento fiscal
   └── Vigencia de 30 días

2. Lista 69-B (@CFF_69B)
   ├── No presunto
   └── No definitivo

3. Lista Art. 69 (@CFF_69)
   ├── No incumplido
   └── No cancelado
   └── No no localizado

4. Constancia de situación fiscal
   ├── RFC activo
   ├── Domicilio vigente
   └── Régimen fiscal correcto
```

---

## Referencias cruzadas

- @CFF_69 (Listas públicas de incumplidos)
- @CFF_69B (EFOS - Operaciones inexistentes)
- @LISR_27_I (Estrictamente indispensable)
- @TESIS_MAT_002 (Materialidad - capacidad del proveedor)
