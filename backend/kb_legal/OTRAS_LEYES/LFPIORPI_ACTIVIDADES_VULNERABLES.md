---
id: LFPIORPI_VULNERABLES
ley: Ley Federal para la Prevención e Identificación de Operaciones con Recursos de Procedencia Ilícita
titulo: Actividades vulnerables y obligaciones
tags: [pld, vulnerables, avisos, umbrales, A6, A7]
prioridad: media
---

# @LFPIORPI_VULNERABLES - Actividades Vulnerables (PLD)

## [NORMA]

**Artículo 17.** Para efectos de esta Ley se consideran Actividades 
Vulnerables y, por tanto, objeto de identificación en los términos del 
artículo 18 de la misma:

**I.** La prestación de servicios profesionales de manera independiente, 
cuando se prepare para un cliente o se lleve a cabo en nombre y 
representación del cliente cualquier operación relacionada con:
- Compraventa de bienes inmuebles
- Administración y manejo de recursos
- Apertura o gestión de cuentas
- Organización de aportaciones para sociedades
- Compraventa de entidades mercantiles

**II.** Los servicios de fe pública de notarios y corredores públicos.

**III.** Los servicios de comercio exterior como agente o apoderado aduanal.

**IV.** La constitución de personas morales o la celebración de contratos 
de asociación.

**V.** Los servicios de construcción o desarrollo de bienes inmuebles.

**VI.** Los servicios de comercialización o intermediación de metales 
preciosos, piedras preciosas, joyas o relojes.

**VII.** La comercialización de vehículos aéreos, marítimos o terrestres.

**VIII.** La oferta de mutualidades o de seguros.

**IX.** Los blindajes a vehículos terrestres.

**X.** El arrendamiento de inmuebles.

**XI.** Las operaciones con activos virtuales.

**Fuente:** https://www.diputados.gob.mx/LeyesBiblio/pdf/LFPIORPI.pdf

---

## [INTERPRETACIÓN REVISAR-IA]

### Umbrales de identificación y aviso:

| Actividad | Umbral identificación | Umbral aviso |
|-----------|----------------------|--------------|
| Inmuebles | Cualquier monto | >8,025 UMA |
| Vehículos nuevos | >3,210 UMA | >6,420 UMA |
| Vehículos usados | >1,605 UMA | >3,210 UMA |
| Joyas/metales | >805 UMA | >1,605 UMA |
| Obras de arte | >4,815 UMA | >9,630 UMA |
| Juegos con apuesta | >325 UMA | >645 UMA |
| Activos virtuales | >645 UMA | >1,605 UMA |

**Nota:** 1 UMA 2025 ≈ $113.14 MXN

### Uso en verificación de proveedores (A6):

Cuando un proveedor realiza actividades vulnerables, A6 debe verificar:

```
VERIFICACIÓN DE PROVEEDOR EN ACTIVIDAD VULNERABLE

Proveedor: [Nombre]
RFC: [XXX]
Actividad: [Describir]

1. ¿ES ACTIVIDAD VULNERABLE?
   □ Consultar catálogo Art. 17 LFPIORPI
   □ Resultado: [ ] Sí es vulnerable [ ] No es vulnerable

2. SI ES VULNERABLE:
   □ ¿Está registrado ante la SHCP como sujeto obligado?
   □ ¿Cumple con obligaciones de identificación?
   □ ¿Presenta avisos cuando corresponde?

3. DOCUMENTACIÓN ADICIONAL:
   □ Constancia de registro ante SHCP (si aplica)
   □ Política de prevención de lavado
   □ Aviso al cliente de ser actividad vulnerable
```

### Obligaciones del sujeto obligado:

| Obligación | Descripción | Plazo |
|------------|-------------|-------|
| **Registro** | Inscribirse ante SHCP | 60 días desde inicio actividad |
| **Identificación** | Identificar clientes y usuarios | En cada operación |
| **Aviso** | Presentar aviso mensual | 17 del mes siguiente |
| **Conservación** | Guardar documentación | 5 años |
| **Capacitación** | Capacitar al personal | Anual |

### Riesgos para el contribuyente:

Operar con proveedores que realizan actividades vulnerables sin cumplir 
obligaciones puede implicar:

1. **Riesgo reputacional** - Asociación con PLD
2. **Riesgo de auditoría** - Mayor escrutinio SAT/UIF
3. **Riesgo de materialidad** - Cuestionamiento de operaciones

### Documentación sugerida para Defense Files:

Cuando se operó con proveedor en actividad vulnerable:

```
EVIDENCIA DE CUMPLIMIENTO PLD

El proveedor [NOMBRE] realiza la actividad vulnerable de 
[DESCRIPCIÓN] conforme al artículo 17, fracción [X] de la LFPIORPI.

VERIFICACIÓN REALIZADA:
□ Registro ante SHCP: [Número de registro]
□ Identificación del cliente: [Realizada fecha XXX]
□ Documentos de identificación: [En expediente]

El contribuyente [CLIENTE] cumplió con proporcionar la información 
de identificación requerida por el proveedor para dar cumplimiento 
a las obligaciones de la LFPIORPI.

MONTO DE LA OPERACIÓN: $[XXX]
UMBRAL APLICABLE: [XXX UMA]
CORRESPONDE AVISO: [ ] Sí [ ] No

[Si corresponde aviso, verificar que proveedor lo presentó]
```

### Principales actividades vulnerables por sector:

| Sector | Actividad vulnerable | Fracción |
|--------|---------------------|----------|
| **Inmobiliario** | Compraventa, arrendamiento | I, V, X |
| **Automotriz** | Venta de vehículos | VII |
| **Joyería** | Comercio de joyas/metales | VI |
| **Legal** | Servicios notariales, corporativos | I, II, IV |
| **Aduanas** | Agentes aduanales | III |
| **Fintech** | Operaciones con criptoactivos | XI |

---

## Referencias cruzadas

- @CFF_69B (EFOS - conexión con PLD)
- @CFF_32D (Opinión de cumplimiento)
- @TESIS_MAT_002 (Capacidad del proveedor)
