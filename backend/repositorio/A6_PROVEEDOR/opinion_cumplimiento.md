# Opinión de Cumplimiento (32-D)

## Guía de Verificación y Uso

---

## 1. ¿Qué es la Opinión 32-D?

Es el documento emitido por el SAT que indica si un contribuyente está al corriente en el cumplimiento de sus obligaciones fiscales.

### Base Legal
**Artículo 32-D del Código Fiscal de la Federación**

Regla 3.10.2 de la Resolución Miscelánea Fiscal

---

## 2. Tipos de Opinión

### Positiva ✅
El contribuyente:
- Está inscrito en el RFC
- Está al corriente en declaraciones
- No tiene créditos fiscales firmes
- No está en lista 69-B

### Negativa ❌
El contribuyente:
- Tiene obligaciones pendientes
- Tiene créditos fiscales firmes
- Está en proceso de embargo
- Está en lista 69-B

### En Suspensión ⏸️
El contribuyente tiene:
- Medios de defensa en trámite
- Facilidades de pago autorizadas
- Situación fiscal en revisión

---

## 3. Cómo Obtener la Opinión

### Por el Portal del SAT
1. Ingresar a sat.gob.mx
2. Iniciar sesión con e.firma o contraseña
3. Ir a "Otros trámites y servicios"
4. Seleccionar "Opinión del cumplimiento"
5. Descargar el PDF

### Elementos del Documento
| Campo | Descripción |
|-------|-------------|
| RFC | Identificador del contribuyente |
| Razón Social | Nombre o denominación |
| Fecha de emisión | Momento de generación |
| Vigencia | 30 días naturales |
| Sentido | Positiva/Negativa |
| Folio | Número de verificación |

---

## 4. Vigencia y Actualización

### Vigencia Oficial
- **30 días naturales** desde la fecha de emisión

### Recomendación DUREZZA
- Solicitar opinión actualizada antes de cada pago significativo
- Monitoreo mensual para proveedores recurrentes
- Alerta automática cuando próxima a vencer

---

## 5. Obligaciones que Considera

### Para Personas Morales
- [ ] RFC activo y localizable
- [ ] Declaraciones anuales presentadas
- [ ] Declaraciones mensuales presentadas
- [ ] Pagos provisionales al corriente
- [ ] Sin créditos fiscales firmes
- [ ] Sin operaciones inexistentes (69-B)
- [ ] Contabilidad electrónica enviada

### Para Personas Físicas
- [ ] RFC activo
- [ ] Declaración anual presentada
- [ ] Pagos provisionales (si aplica)
- [ ] Sin adeudos fiscales
- [ ] Sin operaciones inexistentes

---

## 6. Causas Comunes de Opinión Negativa

### Declaraciones
| Causa | Solución |
|-------|----------|
| Declaración anual pendiente | Presentar declaración |
| Declaraciones mensuales omitidas | Presentar con actualizaciones |
| Diferencias ISR/IVA | Aclarar o pagar diferencias |

### Créditos Fiscales
| Causa | Solución |
|-------|----------|
| Adeudo determinado | Pagar o impugnar |
| Multas pendientes | Pagar o solicitar condonación |
| Requerimiento no atendido | Responder al requerimiento |

### Otras
| Causa | Solución |
|-------|----------|
| Domicilio no localizado | Actualizar domicilio |
| Lista 69-B presunto | Desvirtuar presunción |
| Buzón tributario inactivo | Activar buzón |

---

## 7. Verificación de Autenticidad

### Por QR
1. Escanear código QR del documento
2. Validar en portal del SAT
3. Comparar datos

### Por Portal
URL: https://www.sat.gob.mx/aplicacion/operacion/53027/verifica-la-autenticidad-de-tu-opinion-de-cumplimiento

### Elementos a Verificar
- [ ] Folio de la opinión
- [ ] RFC del contribuyente
- [ ] Fecha de emisión
- [ ] Sentido (positiva/negativa)

---

## 8. Uso en Contrataciones

### Obligatoriedad
La opinión 32-D es obligatoria para:
- Contrataciones con gobierno
- Licitaciones públicas
- Subsidios y estímulos fiscales

### Recomendación para Sector Privado
Aunque no es obligatoria, se recomienda solicitarla para:
- Contratos superiores a $100,000 MXN
- Proveedores nuevos
- Servicios recurrentes
- Operaciones de alto riesgo

---

## 9. Formato de Validación

### Registro de Verificación
```
================================================
VERIFICACIÓN DE OPINIÓN 32-D
================================================
Proveedor: {{RAZON_SOCIAL}}
RFC: {{RFC}}
Fecha de emisión: {{FECHA_EMISION}}
Vigencia hasta: {{FECHA_VIGENCIA}}
Folio SAT: {{FOLIO}}

RESULTADO: {{POSITIVA | NEGATIVA}}

Verificado por: {{USUARIO}}
Fecha verificación: {{FECHA_VERIFICACION}}
Método: {{PORTAL | QR}}
================================================
```

---

## 10. Integración en DUREZZA 4.0

### Automatización
| Acción | Frecuencia | Agente |
|--------|------------|--------|
| Solicitud inicial | Alta de proveedor | A6 |
| Verificación | Mensual | A6 |
| Alerta de vencimiento | 5 días antes | A6 |
| Bloqueo automático | Si vence | A6 |

### Reglas de Negocio
```python
def validar_32d(proveedor):
    opinion = consultar_sat(proveedor.rfc)

    if opinion.sentido == "NEGATIVA":
        return {
            "status": "RECHAZADO",
            "mensaje": "Opinión de cumplimiento negativa"
        }

    dias_vigencia = (opinion.vigencia - hoy).days

    if dias_vigencia < 0:
        return {
            "status": "VENCIDO",
            "mensaje": "Solicitar opinión actualizada"
        }
    elif dias_vigencia < 5:
        return {
            "status": "POR_VENCER",
            "mensaje": "Renovar pronto"
        }
    else:
        return {
            "status": "VIGENTE",
            "mensaje": "Puede operar"
        }
```

---

## 11. Archivo y Conservación

### Estructura de Carpetas
```
/proveedores/{{RFC}}/
├── opiniones_32d/
│   ├── 32d_{{FECHA1}}.pdf
│   ├── 32d_{{FECHA2}}.pdf
│   └── 32d_{{FECHA3}}.pdf
└── verificaciones/
    └── log_verificaciones.csv
```

### Período de Conservación
- **5 años** desde la fecha de la operación relacionada

---
*La opinión 32-D es esencial para mitigar riesgo fiscal en operaciones con terceros.*
