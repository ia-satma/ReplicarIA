# Lista 69-B - Operaciones Inexistentes

## Guía de Consulta y Verificación

---

## 1. ¿Qué es la Lista 69-B?

Es el listado publicado por el SAT de contribuyentes que se presume realizaron operaciones inexistentes (EFOS - Empresas que Facturan Operaciones Simuladas).

### Base Legal
**Artículo 69-B del Código Fiscal de la Federación**

La autoridad fiscal puede presumir la inexistencia de operaciones cuando:
1. No se localice al contribuyente en su domicilio
2. No cuente con infraestructura, personal o capacidad material
3. No demuestre la adquisición de bienes o servicios para operar

---

## 2. Tipos de Publicación

### Lista Definitiva (Párrafo Cuarto)
Contribuyentes que:
- No desvirtuaron la presunción
- No ejercieron su derecho de defensa
- Perdieron medios de defensa

**Efecto:** Sus CFDI **NO** pueden producir efectos fiscales.

### Lista Presunta (Párrafo Primero)
Contribuyentes en proceso de aclaración:
- Notificados por la autoridad
- Con plazo para desvirtuar

**Efecto:** Alerta preventiva, aún pueden aclarar.

### Lista de Sentencias Favorables
Contribuyentes que:
- Obtuvieron sentencia favorable
- Desvirtuaron la presunción

---

## 3. Cómo Consultar

### Portal del SAT
URL: https://www.sat.gob.mx/consultas/76674/consulta-la-relacion-de-contribuyentes-incumplidos

### API de Consulta
```bash
GET /api/sat/lista69b/{rfc}
```

### Respuesta Esperada
```json
{
  "rfc": "{{RFC}}",
  "status": "NO_ENCONTRADO | DEFINITIVO | PRESUNTO | DESVIRTUADO",
  "fecha_publicacion": "{{FECHA}}",
  "situacion": "{{SITUACION}}",
  "numero_oficio": "{{OFICIO}}"
}
```

---

## 4. Consecuencias de Operar con EFOS

### Para el Receptor del CFDI
1. **No deducibilidad:** El gasto no es deducible para ISR
2. **No acreditamiento:** El IVA no es acreditable
3. **Presunción de complicidad:** Posible revisión fiscal
4. **Responsabilidad solidaria:** En casos graves

### Plazos de Defensa
- **30 días** para demostrar la adquisición efectiva
- Aportar toda documentación comprobatoria

---

## 5. Documentación para Desvirtuar

### Evidencia Requerida
- [ ] Contrato de servicios firmado
- [ ] Ordenes de trabajo o pedidos
- [ ] Evidencia de entrega (correos, minutas)
- [ ] Comprobante de pago bancario
- [ ] Registro contable del gasto
- [ ] Comunicaciones de coordinación

### Elementos Adicionales Sugeridos
- Fotografías de reuniones
- Bitácoras de trabajo
- Testimoniales de terceros
- Peritaje contable

---

## 6. Validación Preventiva

### Antes de Contratar
1. Consultar RFC en lista 69-B
2. Verificar opinión de cumplimiento (32-D)
3. Validar domicilio fiscal activo
4. Confirmar actividad económica compatible
5. Solicitar referencias comerciales

### Durante la Relación
1. Monitoreo periódico en lista 69-B
2. Actualización de 32-D cada 30 días
3. Documentar todas las interacciones
4. Conservar evidencia de materialidad

### Checklist de Validación Inicial
| Verificación | Resultado | Fecha |
|--------------|-----------|-------|
| Lista 69-B | {{RESULTADO}} | {{FECHA}} |
| Opinión 32-D | {{RESULTADO}} | {{FECHA}} |
| Domicilio SAT | {{RESULTADO}} | {{FECHA}} |
| Actividad económica | {{RESULTADO}} | {{FECHA}} |

---

## 7. Integración en DUREZZA 4.0

### Automatización
| Acción | Frecuencia | Agente |
|--------|------------|--------|
| Consulta inicial | Al crear proveedor | A6 |
| Monitoreo continuo | Semanal | A6 |
| Alerta de cambio | Inmediata | A6, A7 |
| Generación de evidencia | Por transacción | A7 |

### Alertas del Sistema
| Nivel | Condición | Acción |
|-------|-----------|--------|
| 🟢 Verde | No encontrado | Continuar |
| 🟡 Amarillo | Presunto | Revisar con cuidado |
| 🔴 Rojo | Definitivo | Rechazar operación |

---

## 8. Actualización de la Lista

### Frecuencia de Publicación
- **DOF:** Cada 15 días hábiles aproximadamente
- **Portal SAT:** Actualización continua

### Fuentes Oficiales
- Diario Oficial de la Federación (DOF)
- Portal del SAT
- Servicio de Administración Tributaria

---

## 9. Formato de Reporte de Verificación

```
================================================
REPORTE DE VERIFICACIÓN LISTA 69-B
================================================
RFC Consultado: {{RFC}}
Razón Social: {{RAZON_SOCIAL}}
Fecha de Consulta: {{FECHA_HORA}}

RESULTADO: {{STATUS}}

Detalle:
- Situación actual: {{SITUACION}}
- Fecha de publicación: {{FECHA_PUB}}
- Número de oficio: {{NUM_OFICIO}}

Recomendación: {{RECOMENDACION}}
================================================
```

---
*La lista se actualiza constantemente - Siempre consultar antes de cada operación.*
