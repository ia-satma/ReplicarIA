# KB Tags - Indice Maestro de Referencias

## Estructura de Tags

Los tags se usan para vincular documentos de la KB entre si y para que los agentes referencien normas especificas.

Formato: @[LEY]_[ARTICULO] o @[CONCEPTO]

---

## Tags por Ley

### Codigo Fiscal de la Federacion (CFF)

| Tag | Descripcion | Archivo | Agentes |
|-----|-------------|---------|---------|
| @CFF_5 | Interpretacion de normas | /1_normativa/cff/CFF_5_INTERPRETACION.md | A3, A4, A7 |
| @CFF_5A | Razon de negocios | /1_normativa/cff/CFF_5A_RAZON_NEGOCIOS.md | A1, A3, A7 |
| @CFF_27 | Requisitos RFC | /1_normativa/cff/CFF_27_REQUISITOS_RFC.md | A6 |
| @CFF_29 | Comprobantes fiscales | /1_normativa/cff/CFF_29_29A_CFDI.md | A3, A6 |
| @CFF_29A | Requisitos CFDI | /1_normativa/cff/CFF_29_29A_CFDI.md | A3, A6 |
| @CFF_32D | Opinion cumplimiento | /1_normativa/cff/CFF_32D_OPINION_CUMPLIMIENTO.md | A6 |
| @CFF_69 | Listas publicas | /1_normativa/cff/CFF_69_LISTAS_PUBLICAS.md | A6 |
| @CFF_69B | EFOS/Materialidad | /1_normativa/cff/CFF_69B_EFOS_MATERIALIDAD.md | A3, A6, A7 |

### Ley del Impuesto sobre la Renta (LISR)

| Tag | Descripcion | Archivo | Agentes |
|-----|-------------|---------|---------|
| @LISR_25 | Deducciones autorizadas | /1_normativa/lisr/LISR_25_DEDUCCIONES_AUTORIZADAS.md | A3, A5 |
| @LISR_27 | Requisitos deducciones | /1_normativa/lisr/LISR_27_REQUISITOS_DEDUCCIONES.md | A3, A7 |
| @LISR_27_I | Estrictamente indispensable | /1_normativa/lisr/LISR_27_REQUISITOS_DEDUCCIONES.md | A1, A3 |
| @LISR_27_III | CFDI y pago | /1_normativa/lisr/LISR_27_REQUISITOS_DEDUCCIONES.md | A3 |
| @LISR_27_IV | Registro contable | /1_normativa/lisr/LISR_27_REQUISITOS_DEDUCCIONES.md | A3, A5 |
| @LISR_27_XVIII | IVA trasladado | /1_normativa/lisr/LISR_27_REQUISITOS_DEDUCCIONES.md | A3 |
| @LISR_27_XIX | Efectivamente pagado | /1_normativa/lisr/LISR_27_REQUISITOS_DEDUCCIONES.md | A3 |
| @LISR_28 | Gastos no deducibles | /1_normativa/lisr/LISR_28_GASTOS_NO_DEDUCIBLES.md | A3 |

### Ley del IVA (LIVA)

| Tag | Descripcion | Archivo | Agentes |
|-----|-------------|---------|---------|
| @LIVA_5 | Acreditamiento IVA | /1_normativa/liva/LIVA_5_ACREDITAMIENTO_IVA.md | A3, A5 |
| @LIVA | Articulos clave | /1_normativa/liva/LIVA_ARTICULOS_CLAVE.md | A3 |

### Otras Normas

| Tag | Descripcion | Archivo | Agentes |
|-----|-------------|---------|---------|
| @NOM151 | Trazabilidad documental | /1_normativa/nom151/NOM_151_SCFI_2016_TRAZABILIDAD.md | A2, A7 |
| @RMF | Reglas miscelanea | /1_normativa/rmf/RMF_2026_SERVICIOS_CFDI.md | A3 |

---

## Tags de Jurisprudencia

| Tag | Descripcion | Archivo | Agentes |
|-----|-------------|---------|---------|
| @TESIS_IA | IA como auxiliar | /1_normativa/jurisprudencia/TESIS_IA_SCJN_2031639.md | Todos |
| @TESIS_RN | Razon de negocios | /1_normativa/jurisprudencia/TESIS_RAZON_NEGOCIOS_5A.md | A1, A7 |
| @TESIS_MATERIALIDAD | Materialidad operaciones | /1_normativa/jurisprudencia/TESIS_MATERIALIDAD_69B.md | A3, A6, A7 |
| @TESIS_INDISPENSABILIDAD | Estricta indispensabilidad | /1_normativa/jurisprudencia/TESIS_ESTRICTA_INDISPENSABILIDAD.md | A1, A3 |

---

## Tags Conceptuales

| Tag | Descripcion | Archivos relacionados |
|-----|-------------|----------------------|
| @RAZON_NEGOCIOS | Concepto razon negocios | CFF_5A, GUIA_A1_5A_CFF |
| @BENEFICIO_ECONOMICO | BEE cuantificacion | GUIA_A1_A5_BEE |
| @MATERIALIDAD | Evidencia de operaciones | GUIA_MATERIALIDAD, CFF_69B |
| @TRAZABILIDAD | Fecha cierta e integridad | GUIA_TRAZABILIDAD, NOM151 |
| @EFOS | Operaciones inexistentes | CFF_69B, CRITERIOS_EFOS |
| @DUE_DILIGENCE | Verificacion proveedores | GUIA_DD_PROVEEDOR |
| @DEFENSE_FILE | Expediente de defensa | PLANTILLA_DICTAMEN_A7 |
| @CHECKLIST | Listas de verificacion | LISR_27, GUIA_MATERIALIDAD |
| @SIB | Sustancia Intangible | PLANTILLA_SIB_BEE |

---

## Consumo de KB por Agente

| Agente | Tags principales | Carpetas que consume |
|--------|------------------|---------------------|
| A1 Estrategia | @CFF_5A, @LISR_27_I, @BENEFICIO_ECONOMICO | 2_pilares/razon_negocios, 3_tipologias |
| A2 PMO | @NOM151, @TRAZABILIDAD | 2_pilares/trazabilidad |
| A3 Fiscal | @LISR_27, @CFF_69B, @LIVA_5 | 1_normativa/lisr, 1_normativa/cff |
| A4 Legal | @CFF_5, @NOM151 | 1_normativa/jurisprudencia |
| A5 Finanzas | @LISR_25, @LIVA_5, @BENEFICIO_ECONOMICO | 2_pilares/beneficio_economico |
| A6 Proveedor | @CFF_69B, @CFF_32D, @DUE_DILIGENCE | 4_efos_proveedores |
| A7 Defensa | @CFF_5A, @CFF_69B, @LISR_27, @TESIS_* | 1_normativa, 5_plantillas |
| AUDITOR | Todos | Todos (validacion) |
| ARCHIVO | @NOM151, @TRAZABILIDAD | 2_pilares/trazabilidad |

---

## Actualizacion de KB

### Proceso para agregar nuevo contenido:
1. Identificar ley/articulo/concepto
2. Crear archivo con formato estandar
3. Agregar seccion [NORMA] con texto oficial
4. Agregar seccion [INTERPRETACION EN REVISAR-IA]
5. Definir tags aplicables
6. Actualizar este indice
7. Vincular a agentes consumidores

### Versionamiento:
- Fecha de ultima actualizacion: 2026-01-23
- Version KB: 2.0
- Archivos totales: 30+
- Tags definidos: 35+
