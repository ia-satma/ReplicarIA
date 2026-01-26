# [NORMA] CFF – Artículo 69-B (EFOS/Materialidad)

## Texto Normativo (Extracto)

> Cuando la autoridad fiscal detecte que un contribuyente ha estado emitiendo comprobantes sin contar con los activos, personal, infraestructura o capacidad material, directa o indirectamente, para prestar los servicios o producir, comercializar o entregar los bienes que amparan tales comprobantes, o bien, que dichos contribuyentes se encuentren no localizados, se presumirá la inexistencia de las operaciones amparadas en tales comprobantes.

> Los contribuyentes podrán manifestar ante la autoridad fiscal lo que a su derecho convenga y aportar la documentación e información que consideren pertinentes para desvirtuar los hechos que llevaron a la autoridad a notificarlos.

**Referencia oficial:**
https://www.diputados.gob.mx/LeyesBiblio/pdf/CFF.pdf

## Listas del SAT

- **Lista de presuntos (Art. 69-B Párrafo 1)**: Contribuyentes en proceso de revisión
- **Lista de definitivos (Art. 69-B Párrafo 3)**: Contribuyentes confirmados como EFOS
- **Lista de desvirtuados**: Contribuyentes que demostraron operaciones reales

---

# [INTERPRETACIÓN EN REVISAR-IA]

## Ámbito de uso

| Agente | Uso |
|--------|-----|
| **A6_PROVEEDOR** | Verifica estatus del proveedor en listas 69-B |
| **A3_FISCAL** | Evalúa riesgo EFOS para deducibilidad |
| **A7_DEFENSA** | Construye defensa si proveedor cae en lista |

## Señales de alerta EFOS (checklist A6)

### Señales de capacidad material
- [ ] Sin empleados registrados en IMSS
- [ ] Domicilio fiscal no localizable
- [ ] Capital social mínimo ($50,000 o menos)
- [ ] Antigüedad menor a 2 años

### Señales en facturación
- [ ] Conceptos genéricos en CFDI
- [ ] Montos sin relación con tamaño de proveedor
- [ ] Patrones de facturación irregular

### Señales de cumplimiento
- [ ] Sin opinión de cumplimiento positiva (32-D)
- [ ] Estatus en listas 69-B (presunto o definitivo)
- [ ] Sin buzón tributario habilitado

## Acciones por estatus

| Estatus | Acción A6 | Acción A3 |
|---------|----------|----------|
| **Limpio** | APROBAR | Deducible normal |
| **Presunto** | APROBAR_CON_CONDICIONES + monitoreo | Reserva fiscal recomendada |
| **Definitivo** | RECHAZAR | No deducible |

## Límites

- La plataforma **NO** presume automáticamente que un proveedor es EFOS
- Solo marca señales de alerta y consulta estatus en listas oficiales
- Cualquier cambio de estatus en listas 69-B debe actualizar dictámenes

## Documentación de buena fe

Para proteger al cliente ante proveedor que caiga en lista:

1. **Due diligence previo documentado** (A6)
   - CSF del proveedor
   - Opinión 32-D
   - Verificación de domicilio
   - Acta constitutiva

2. **Evidencia de operación real**
   - Contrato firmado
   - Entregables recibidos
   - Minutas de trabajo
   - Pagos a cuentas verificadas

3. **Reacción oportuna**
   - Monitoreo trimestral de listas
   - Suspensión de pagos si cae en presunto
   - Valoración de autocorrección

## Buenas prácticas internas

1. Consultar listas 69-B **antes** de contratar (F2)
2. Documentar toda la due diligence en el expediente
3. Establecer cláusula contractual de cooperación fiscal
4. Si proveedor pasa de presunto a definitivo:
   - Reactivar A3/A7 para evaluar impacto
   - Considerar autocorrección proactiva
