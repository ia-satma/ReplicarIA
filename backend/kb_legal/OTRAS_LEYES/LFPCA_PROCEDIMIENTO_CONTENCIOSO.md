---
id: LFPCA
ley: Ley Federal de Procedimiento Contencioso Administrativo
titulo: Procedimiento de nulidad ante TFJA
tags: [defensa, nulidad, tfja, demanda, pruebas, A7]
prioridad: alta
---

# LFPCA - Procedimiento Contencioso Administrativo

## [NORMA]

### @LFPCA_DEMANDA - Requisitos de la Demanda (Arts. 13-14)

**Artículo 13.** La demanda se presentará por escrito directamente ante 
la sala regional competente, dentro de los plazos que esta Ley señala.

**Artículo 14.** La demanda deberá indicar:

**I.** El nombre del demandante, su domicilio para oír y recibir notificaciones, 
así como su correo electrónico y el nombre del representante legal.

**II.** La resolución que se impugna.

**III.** La autoridad o autoridades demandadas.

**IV.** Los hechos que den motivo a la demanda.

**V.** Las pruebas que ofrezca.

**VI.** Los conceptos de impugnación.

**VII.** El nombre y domicilio del tercero interesado, cuando lo haya.

**VIII.** Lo que se pida, señalando en caso de solicitar una sentencia 
de condena, las cantidades o actos cuyo cumplimiento se demanda.

### @LFPCA_PLAZOS - Plazos Procesales (Art. 13)

**Plazos para presentar demanda:**

| Tipo de acto | Plazo |
|--------------|-------|
| Resolución definitiva | 30 días hábiles |
| Negativa ficta | 45 días hábiles |
| Actos administrativos | 30 días hábiles |

El plazo comienza a correr a partir del día siguiente a aquél en que 
surta efectos la notificación de la resolución impugnada.

### @LFPCA_PRUEBAS - Medios de Prueba (Art. 40)

**Artículo 40.** En los juicios que se tramiten ante el Tribunal, serán 
admisibles toda clase de pruebas, excepto la de confesión de las autoridades 
mediante absolución de posiciones y la petición de informes.

**Pruebas admisibles:**
- Documentales (públicas y privadas)
- Periciales
- Testimoniales
- Inspección
- Presuncionales
- Instrumentales
- Cualquier otra que produzca convicción

### @LFPCA_VALOR - Valoración de Pruebas (Art. 46)

**Artículo 46.** El Magistrado Instructor, hasta antes de que se dicte la 
sentencia, podrá acordar la exhibición de cualquier documento que tenga 
relación con los hechos controvertidos o para ordenar la práctica de 
cualquier diligencia.

Las pruebas se valorarán de acuerdo con las reglas de la sana crítica.

---

## [INTERPRETACIÓN REVISAR-IA]

### Uso por A7 en Defense Files:

El agente A7 (Auditar.IA) debe considerar estos artículos cuando el 
contribuyente necesite impugnar una resolución ante el TFJA.

### Checklist para preparación de juicio de nulidad:

```
PREPARACIÓN DE DEMANDA DE NULIDAD

1. VERIFICAR PLAZOS
   □ ¿Cuándo se notificó la resolución?
   □ ¿Quedan días hábiles para presentar?
   □ ¿Es resolución definitiva?

2. IDENTIFICAR ELEMENTOS DE DEMANDA (@LFPCA_DEMANDA)
   □ Datos del contribuyente
   □ Resolución impugnada (número, fecha)
   □ Autoridad demandada
   □ Hechos cronológicos
   □ Conceptos de impugnación
   □ Pruebas a ofrecer
   □ Pretensiones específicas

3. PREPARAR PRUEBAS (@LFPCA_PRUEBAS)
   □ Documentales: Expediente de materialidad
   □ Periciales: Si se requiere opinión técnica
   □ Testimoniales: Si hay testigos de las operaciones
   □ Inspección: Si hay elementos físicos verificables

4. ARGUMENTOS DE NULIDAD COMUNES
   □ Falta de fundamentación y motivación
   □ Violación a derechos del contribuyente
   □ Vicios de procedimiento
   □ Incorrecta valoración de pruebas
   □ Caducidad de facultades de comprobación
```

### Tipos de sentencias:

| Sentido | Descripción | Efecto |
|---------|-------------|--------|
| Nulidad lisa y llana | Se anula totalmente la resolución | Queda sin efectos |
| Nulidad para efectos | Se anula pero SAT puede corregir | SAT emite nueva resolución |
| Validez | Se confirma la resolución | Subsiste el crédito |
| Sobreseimiento | No se entra al fondo | Proceso termina sin decisión |

### Conceptos de impugnación frecuentes:

1. **Vicios de procedimiento**
   - Notificación incorrecta
   - Falta de citatorio previo
   - Exceso en plazos de auditoría

2. **Falta de fundamentación**
   - No cita artículos aplicables
   - Cita artículos incorrectos
   - Legislación derogada

3. **Falta de motivación**
   - No explica razonamiento
   - Conclusiones sin sustento
   - Presunciones no desvirtuadas

4. **Violación a derechos**
   - Sin derecho de audiencia (@LFDC_AUDIEN)
   - Presunción de mala fe (@LFDC_BUENAFE)
   - Sin resolución motivada (@LFDC_MOTIVA)

### Documento base para A7:

```
ANÁLISIS PARA DEMANDA DE NULIDAD

RESOLUCIÓN IMPUGNADA:
- Número: [XXX]
- Fecha: [DD-MMM-AAAA]
- Notificación: [DD-MMM-AAAA]
- Autoridad: [SAT / AGAFF / etc.]

PLAZO LÍMITE PARA DEMANDA: [Calcular 30 días hábiles]

CONCEPTOS DE IMPUGNACIÓN IDENTIFICADOS:

1. [Vicio o violación identificada]
   Fundamento: @LFPCA_XX, @LFDC_XX
   Argumentación: [...]

2. [Segundo concepto]
   [...]

PRUEBAS A OFRECER:
- Documental: Expediente de materialidad (ver @TESIS_MAT_002)
- [Otras pruebas]

PRETENSIÓN: Nulidad lisa y llana de la resolución impugnada.
```

---

## Referencias cruzadas

- @LFDC_INFO (Derecho a información)
- @LFDC_AUDIEN (Derecho de audiencia)
- @LFDC_MOTIVA (Resolución motivada)
- @LOTFJA_COMP (Competencia del TFJA)
- @TESIS_MAT_002 (Elementos de prueba para materialidad)
