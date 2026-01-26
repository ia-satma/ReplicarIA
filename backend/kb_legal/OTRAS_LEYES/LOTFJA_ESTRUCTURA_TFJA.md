---
id: LOTFJA_TFJA
ley: Ley Orgánica del Tribunal Federal de Justicia Administrativa
titulo: Estructura y competencia del TFJA
tags: [tfja, tribunal, competencia, defensa, A7]
prioridad: media
---

# @LOTFJA_TFJA - Estructura del Tribunal Federal de Justicia Administrativa

## [NORMA]

**Artículo 3.** El Tribunal Federal de Justicia Administrativa conocerá 
de los juicios que se promuevan contra las resoluciones definitivas, actos 
administrativos y procedimientos que se indican a continuación:

**I.** Las dictadas por autoridades fiscales federales y organismos fiscales 
autónomos, en que se determine la existencia de una obligación fiscal, se 
fije en cantidad líquida o se den las bases para su liquidación.

**II.** Las que nieguen la devolución de un ingreso de los regulados por 
el Código Fiscal de la Federación, indebidamente percibido por el Estado.

**III.** Las que impongan multas por infracción a las normas administrativas 
federales.

**IV.** Las que causen un agravio en materia fiscal distinto al que se 
refieren las fracciones anteriores.

**Fuente:** https://www.diputados.gob.mx/LeyesBiblio/pdf/LOTFJA.pdf

---

## [INTERPRETACIÓN REVISAR-IA]

### Estructura del TFJA:

```
TRIBUNAL FEDERAL DE JUSTICIA ADMINISTRATIVA

├── SALA SUPERIOR
│   ├── Sección Primera (criterios jurisdiccionales)
│   ├── Sección Segunda (criterios jurisdiccionales)
│   └── Pleno (contradicción de criterios)
│
├── SALAS REGIONALES
│   ├── Metropolitanas (CDMX)
│   ├── Regionales (por circunscripción)
│   └── Especializadas (propiedad intelectual, etc.)
│
└── SALAS ESPECIALIZADAS
    ├── En materia de comercio exterior
    └── En propiedad intelectual
```

### Competencia por materia:

| Materia | Sala competente | Ejemplo |
|---------|-----------------|---------|
| **Fiscal federal** | Regional | Créditos SAT, devoluciones |
| **Comercio exterior** | Especializada | Aranceles, IMMEX |
| **Responsabilidades** | Regional | Sanciones a servidores |
| **Propiedad intelectual** | Especializada | Marcas, patentes |

### Competencia territorial:

La demanda se presenta ante la Sala Regional de la circunscripción donde:
- Se encuentre el domicilio fiscal del demandante, O
- Donde se ubique la autoridad que emitió el acto

### Tipos de juicio:

| Tipo | Cuantía | Plazo demanda | Características |
|------|---------|---------------|-----------------|
| **Ordinario** | Sin límite | 30 días | Procedimiento completo |
| **Sumario** | <5 UMA anuales | 30 días | Simplificado |
| **En línea** | Cualquiera | 30 días | Sistema de Justicia en Línea |

### Proceso típico en juicio de nulidad:

```
1. DEMANDA (30 días hábiles)
   ├── Requisitos Art. 14 LFPCA
   └── Exhibir resolución impugnada

2. CONTESTACIÓN (45 días)
   └── Autoridad presenta defensa

3. AMPLIACIÓN (20 días)
   └── Si hay hechos supervenientes

4. PRUEBAS
   ├── Documentales
   ├── Periciales
   └── Otras admisibles

5. ALEGATOS (5 días)
   └── Conclusiones de las partes

6. SENTENCIA
   ├── Nulidad
   ├── Validez
   └── Sobreseimiento
```

### Uso en Defense Files (A7):

Cuando se prepara expediente para posible litigio:

```
PREPARACIÓN PARA JUICIO DE NULIDAD

TRIBUNAL COMPETENTE:
- Sala Regional: [Metropolitana / Regional de XX]
- Fundamento: Art. 3, Fr. I LOTFJA

ACTO IMPUGNADO:
- Tipo: Determinación de crédito fiscal
- Autoridad: SAT / AGAFF / AGR
- Número: [XXX]
- Fecha: [DD-MMM-AAAA]

PLAZO PARA DEMANDAR:
- Notificación: [Fecha]
- Límite: [Fecha + 30 días hábiles]

CONCEPTOS DE IMPUGNACIÓN PREPARADOS:
1. [Concepto 1] - @LFPCA_DEMANDA
2. [Concepto 2]
...

PRUEBAS A OFRECER:
- Ver expediente de materialidad @TESIS_MAT_002
```

### Recursos posteriores a sentencia:

| Recurso | Ante quién | Plazo | Para qué |
|---------|------------|-------|----------|
| **Revisión** | Sala Superior | 15 días | Contradicción criterios |
| **Amparo directo** | Tribunal Colegiado | 15 días | Contra sentencia definitiva |
| **Queja** | Sala Superior | 15 días | Incumplimiento sentencia |

---

## Referencias cruzadas

- @LFPCA_BASE (Procedimiento contencioso)
- @LFPCA_DEMANDA (Requisitos de demanda)
- @LFPCA_PRUEBAS (Medios de prueba)
- @LFDC_DERECHOS (Derechos del contribuyente)
