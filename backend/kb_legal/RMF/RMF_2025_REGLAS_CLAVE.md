---
id: RMF_2025_REGLAS_CLAVE
titulo: Resolución Miscelánea Fiscal 2025 - Reglas Clave
version: 1.0
fecha: 2026-01-31
url_oficial: https://www.dof.gob.mx/nota_detalle.php?codigo=5719364&fecha=27/12/2024
agentes: [A3, A5, A8]
tags: [RMF, 2025, CFDI, intangibles, REPSE, partes_relacionadas]
---

# RMF 2025: Reglas Clave para Revisar.IA

## Información General

| Campo | Valor |
|-------|-------|
| **Publicación** | DOF 27 de diciembre de 2024 |
| **Vigencia** | Ejercicio fiscal 2025 |
| **Modificaciones** | Consultar DOF para 1a, 2a, 3a modificación |

---

## Reglas de CFDI (Título II, Capítulo II)

### Regla 2.7.1.X - Requisitos Generales

| Aspecto | Regla Aplicable |
|---------|-----------------|
| **Uso del CFDI** | Debe corresponder a la operación real |
| **Clave de producto/servicio** | Catálogo del SAT (Anexo 20) |
| **Método de pago** | PUE (Pago en Una sola Exhibición) o PPD (Pago en Parcialidades o Diferido) |
| **Forma de pago** | Según catálogo: 01, 02, 03, 04, etc. |
| **Objeto del impuesto** | 01=Sí objeto, 02=No objeto, 03=Sí objeto no obligado |

### Regla 2.7.1.39 - Cancelación de CFDI

```
⚠️ Plazo para cancelar: Hasta el 31 de enero del año siguiente
   al de su expedición.
   Excepciones: CFDI de nómina (plazo especial).
```

---

## Reglas de Intangibles y Servicios (REPSE)

### Regla 3.3.1.X - Servicios Especializados

| Requisito | Descripción |
|-----------|-------------|
| **Registro REPSE** | Obligatorio para prestadores de servicios especializados |
| **Validación** | Consultar registro en portal STPS |
| **Información en CFDI** | Incluir número de registro REPSE |

### URL de consulta REPSE:
```
https://repse.stps.gob.mx/
```

### Implicaciones:
```
SI proveedor requiere REPSE y NO lo tiene:
   → Gasto NO DEDUCIBLE
   → IVA NO ACREDITABLE
   → Responsabilidad solidaria
```

---

## Reglas de Partes Relacionadas

### Regla 3.9.X - Documentación de Precios de Transferencia

| Monto de operaciones | Obligación |
|---------------------|------------|
| > $13 millones | Declaración informativa de partes relacionadas |
| > $100 millones | Estudio de precios de transferencia completo |
| Cualquier monto | Documentación soporte de arm's length |

### Regla 3.9.5 - Información de operaciones relevantes

Operaciones que deben reportarse:
- Préstamos entre partes relacionadas
- Reestructuras corporativas
- Transmisión de intangibles
- Acuerdos de contribución de costos

---

## Reglas de Esquemas Reportables (Título VI)

### Regla 2.21.X - Revelación de Esquemas

| Aspecto | Regla |
|---------|-------|
| **Quién reporta** | Asesor fiscal o contribuyente |
| **Plazo** | 30 días siguientes a implementación |
| **Formato** | Declaración informativa en portal SAT |

### Esquemas que deben reportarse:
1. Evitan el intercambio de información fiscal
2. Involucran operaciones entre partes relacionadas
3. Evitan aplicación de BEPS
4. Involucran pérdidas fiscales
5. Implican recaracterización de ingresos

---

## Reglas de Contabilidad Electrónica

### Regla 2.8.1.X - Envío de Contabilidad

| Obligación | Periodicidad |
|------------|--------------|
| **Catálogo de cuentas** | Una vez (y cuando se modifique) |
| **Balanza de comprobación** | Mensual |
| **Pólizas y auxiliares** | Solo cuando lo requiera la autoridad |

---

## Anexo 20 - CFDI 4.0

### Referencia técnica:
```
URL: https://www.sat.gob.mx/consulta/70515/consulta-los-documentos-tecnicos-del-cfdi
Contenido:
- Esquema XSD
- Catálogos de uso
- Guía de llenado
- Validaciones técnicas
```

### Campos críticos para validación:
| Campo | Validación |
|-------|------------|
| `UsoCFDI` | Debe coincidir con tipo de gasto |
| `ClaveProdServ` | Del catálogo oficial SAT |
| `ObjetoImp` | 01, 02, 03 según corresponda |
| `MetodoPago` | PUE o PPD |
| `FormaPago` | Catálogo de formas de pago |

---

## Referencias Cruzadas

- `@CFF_29_29A` - Requisitos de CFDI
- `@LISR_27_III` - Amparado con comprobante fiscal
- `@LISR_27_XIX` - Partes relacionadas
- `@LIVA_5` - Acreditamiento IVA

---

**Fuente:** [RMF 2025 - DOF](https://www.dof.gob.mx/nota_detalle.php?codigo=5719364&fecha=27/12/2024)
