# [NORMA] CFF - Articulo 69-B: Operaciones Inexistentes (EFOS)

## Texto Normativo (Extracto)

Cuando la autoridad fiscal detecte que un contribuyente ha estado emitiendo comprobantes sin contar con los activos, personal, infraestructura o capacidad material, directa o indirectamente, para prestar los servicios o producir, comercializar o entregar los bienes que amparan tales comprobantes, o bien, que dichos contribuyentes se encuentren no localizados, se presumira la inexistencia de las operaciones amparadas en tales comprobantes.

En este supuesto, la autoridad procedera a:
1. Notificar al contribuyente mediante buzón tributario
2. Publicar en el DOF y portal SAT la lista de contribuyentes presuntos
3. Otorgar plazo de 15 días para desvirtuar la presuncion
4. Si no se desvirtua, publicar como definitivo

Los terceros que hayan dado efectos fiscales a los comprobantes podran demostrar la materialidad de las operaciones dentro del plazo que establece la norma.

**Referencia oficial:**  
https://www.diputados.gob.mx/LeyesBiblio/pdf/CFF.pdf

---

# [INTERPRETACION EN REVISAR-IA]

## Ambito de uso (CRITICO)

- **A6 (Proveedor):** Verificacion obligatoria en TODA operacion
- **A3 (Fiscal):** Riesgo maximo de no deducibilidad
- **A7 (Defensa):** Protocolo de defensa prioritario

## Estados en listas 69-B

| Estado | Significado | Riesgo | Accion |
|--------|-------------|--------|--------|
| PRESUNTO | Proceso iniciado, puede desvirtuarse | Alto | Monitorear, preparar evidencia |
| DESVIRTUADO | Proveedor demostro operaciones | Bajo | Documentar, proceder |
| DEFINITIVO | No pudo desvirtuar, operaciones inexistentes | Critico | Protocolo de defensa |
| SENTENCIA FAVORABLE | Tribunal fallo a favor del contribuyente | Bajo | Documentar sentencia |

## Scoring A6 - Senales EFOS

### Senales criticas (+30 puntos riesgo cada una):
- Publicado en lista 69-B definitivos
- RFC cancelado
- No localizado

### Senales altas (+20 puntos):
- Publicado en lista 69-B presuntos
- Opinion 32-D negativa
- Domicilio en zona de alto riesgo EFOS

### Senales medias (+10 puntos):
- Sin empleados registrados en IMSS
- Antiguedad < 2 anos
- Sin presencia digital verificable

### Interpretacion del score:
| Score | Nivel | Accion |
|-------|-------|--------|
| 0-20 | Bajo | Proceder con DD estandar |
| 21-40 | Medio | DD ampliada recomendada |
| 41-60 | Alto | DD profunda obligatoria |
| 61+ | Critico | No operar o documentar exhaustivamente |

## Demostrar materialidad (defensa del receptor)

El contribuyente que recibio CFDI de un EFOS puede defender la deduccion demostrando:

1. **Contrato:** Firmado previo a la operacion con alcance detallado
2. **Entregables:** Evidencia tangible del servicio recibido
3. **Comunicacion:** Correos, minutas, intercambio documentado
4. **Pago:** Evidencia bancaria (no efectivo)
5. **Uso:** Prueba de que el servicio se utilizo en la operacion del negocio
6. **Due diligence:** Verificaciones previas a contratacion

## Protocolo si proveedor aparece en listas

### Si aparece como PRESUNTO:
1. Notificar inmediatamente al cliente
2. Suspender nuevas operaciones
3. Documentar operaciones previas
4. Preparar evidencia de materialidad
5. Monitorear estatus (30 dias)

### Si pasa a DEFINITIVO:
1. Activar protocolo de defensa A7
2. Compilar Defense File completo
3. El cliente tiene 30 dias para acreditar materialidad
4. Evaluar autocorreccion vs defensa

## Tags relacionados

@CFF_69B @EFOS @EDOS @MATERIALIDAD @OPERACIONES_INEXISTENTES @DEFENSE_FILE
