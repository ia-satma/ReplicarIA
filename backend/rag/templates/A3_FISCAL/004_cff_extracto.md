---
tipo: normativo
version: "1.0"
agente: A3_FISCAL
instrucciones: "Extracto de artículos clave del Código Fiscal de la Federación aplicables a la evaluación de servicios intangibles. Referencia normativa obligatoria."
---

# Extracto del Código Fiscal de la Federación (CFF)

## 1. Artículos Fundamentales para Servicios Intangibles

### Artículo 5-A – Razón de Negocios

**Texto Legal:**

> Los actos jurídicos que carezcan de una razón de negocios y que generen un beneficio fiscal directo o indirecto, tendrán los efectos fiscales que correspondan a los que se habrían realizado para la obtención del beneficio económico razonablemente esperado por el contribuyente.

**Elementos Clave:**
| Elemento | Definición | Aplicación |
|----------|------------|------------|
| Razón de negocios | Beneficio económico cuantificable distinto del fiscal | {{APLICACION_RN}} |
| Beneficio fiscal | Reducción de carga tributaria | {{APLICACION_BF}} |
| Recaracterización | SAT puede dar efectos distintos | {{APLICACION_RECAR}} |

**Autoridad competente:** SAT puede ejercer esta facultad en cualquier revisión.

---

### Artículo 17-H Bis – Restricción de CSD

**Supuestos de restricción temporal:**

| Fracción | Supuesto | Consecuencia |
|----------|----------|--------------|
| I | Omisión de declaraciones | No puede timbrar CFDI |
| IV | Inconsistencia en domicilio | Restricción temporal |
| IX | Operaciones inexistentes detectadas | Bloqueo inmediato |

**Procedimiento de aclaración:** {{PROCEDIMIENTO_17H_BIS}}

---

### Artículo 29 – Obligación de Expedir CFDI

**Requisitos del CFDI:**

| Requisito | Descripción | Validación |
|-----------|-------------|------------|
| RFC emisor | Válido y activo | API SAT |
| RFC receptor | Correcto | Verificar coincidencia |
| Descripción | Servicio o bien | Detalle suficiente |
| Valor unitario | Sin errores | Cuadre con contrato |
| Fecha | Dentro de 24 horas | Regla general |

---

### Artículo 29-A – Requisitos de los CFDI

**Requisitos obligatorios:**

1. Clave del RFC de quien lo expide
2. Régimen fiscal del emisor
3. Número de folio asignado por el SAT
4. Sello digital del SAT
5. Lugar y fecha de expedición
6. Clave del RFC del receptor
7. Cantidad, unidad de medida y clase de bienes/servicios
8. Valor unitario consignado en número
9. Importe total
10. Forma de pago (efectivo, transferencia, etc.)

**Códigos SAT relevantes para servicios:**

| Código | Descripción | Uso Típico |
|--------|-------------|------------|
| {{CODIGO_SAT_1}} | {{DESC_CODIGO_1}} | {{USO_CODIGO_1}} |
| {{CODIGO_SAT_2}} | {{DESC_CODIGO_2}} | {{USO_CODIGO_2}} |
| {{CODIGO_SAT_3}} | {{DESC_CODIGO_3}} | {{USO_CODIGO_3}} |
| {{CODIGO_SAT_4}} | {{DESC_CODIGO_4}} | {{USO_CODIGO_4}} |

---

### Artículo 42 – Facultades de Comprobación

**Facultades del SAT:**

| Fracción | Facultad | Alcance |
|----------|----------|---------|
| II | Revisión de gabinete | Solicitud de documentación |
| III | Visita domiciliaria | Revisión en sitio |
| IV | Revisión de dictámenes | Contadores públicos |
| IX | Revisión electrónica | Mediante buzón tributario |

**Plazos de auditoría:**
- General: 12 meses
- Grupo multinacional: 18 meses
- Prórroga: 6 meses adicionales

---

### Artículo 46 – Desarrollo de Visitas Domiciliarias

**Derechos del contribuyente:**

1. Conocer los hechos u omisiones detectados
2. Presentar pruebas y alegatos
3. Ser informado del resultado
4. Impugnar resoluciones

**Obligaciones del contribuyente:**

1. Proporcionar documentación requerida
2. Permitir acceso a instalaciones
3. Designar testigos
4. Firmar actas correspondientes

---

### Artículo 69-B – Operaciones Inexistentes (EFOS)

**Procedimiento de presunción:**

```
┌─────────────────────────────────────────────────────────────┐
│                 PROCEDIMIENTO 69-B CFF                      │
├─────────────────────────────────────────────────────────────┤
│ 1. SAT detecta operaciones simuladas                        │
│                    ▼                                        │
│ 2. Publicación en DOF (lista presunta)                      │
│                    ▼                                        │
│ 3. Plazo 15 días para aportar documentación                 │
│                    ▼                                        │
│ 4. Valoración de pruebas por SAT                            │
│                    ▼                                        │
│ 5. Publicación definitiva o desvirtuamiento                 │
│                    ▼                                        │
│ 6. Efectos para receptores de CFDI                          │
└─────────────────────────────────────────────────────────────┘
```

**Listas publicadas:**

| Lista | Estado | Efecto |
|-------|--------|--------|
| Presuntos | En proceso | Alerta |
| Definitivos | Confirmado | CFDI sin efectos fiscales |
| Desvirtuados | Aclarado | Sin efecto negativo |
| Favorables | Sentencia favorable | Restituidos |

---

### Artículo 69-B Bis – Transmisión Indebida de Pérdidas

**Supuestos:**

1. Transmisión de pérdidas fiscales sin razón de negocios
2. Reestructuras con propósito de aprovechamiento de pérdidas
3. Fusiones/escisiones sin sustancia económica

**Consecuencia:** Pérdidas no podrán disminuirse de la utilidad fiscal.

---

### Artículo 76 – Obligaciones de las Personas Morales

**Obligaciones relevantes para servicios intangibles:**

| Fracción | Obligación | Periodicidad |
|----------|------------|--------------|
| I | Llevar contabilidad | Permanente |
| III | Expedir CFDI | Por operación |
| VI | Presentar declaraciones | Mensual/Anual |
| IX | Documentar operaciones PT | Anual |

---

### Artículo 81-83 – Infracciones y Sanciones

**Infracciones relacionadas:**

| Artículo | Infracción | Sanción |
|----------|------------|---------|
| 81 Fr. I | No presentar declaraciones | {{SANCION_81_I}} |
| 81 Fr. VI | No expedir CFDI | {{SANCION_81_VI}} |
| 83 Fr. VII | Contabilidad irregular | {{SANCION_83_VII}} |
| 83 Fr. IX | No conservar contabilidad | {{SANCION_83_IX}} |

---

## 2. Artículos de Procedimiento

### Artículo 121 – Recurso de Revocación

**Características:**

| Aspecto | Detalle |
|---------|---------|
| Plazo | 30 días hábiles |
| Ante | SAT |
| Suspensión | Con garantía del interés fiscal |
| Resolución | 3 meses |

### Artículo 125 – Juicio Contencioso

**Alternativa al recurso de revocación:**

| Aspecto | Detalle |
|---------|---------|
| Plazo | 30 días hábiles |
| Ante | TFJA |
| Instancias | Juicio sumario o ordinario |

---

## 3. Tabla de Referencia Rápida

### Plazos Clave

| Concepto | Plazo | Fundamento |
|----------|-------|------------|
| Conservación de contabilidad | 5 años | Art. 30 CFF |
| Prescripción créditos fiscales | 5 años | Art. 146 CFF |
| Caducidad facultades | 5 años | Art. 67 CFF |
| Recurso de revocación | 30 días | Art. 121 CFF |
| Juicio contencioso | 30 días | Art. 125 CFF |
| Respuesta a requerimientos | 15 días | Art. 53 CFF |

### Montos de Referencia

| Concepto | Monto/Porcentaje | Fundamento |
|----------|------------------|------------|
| Límite pago efectivo | $2,000 MXN | Art. 27 Fr. III LISR |
| Actualización | INPC | Art. 17-A CFF |
| Recargos moratorios | {{TASA_RECARGOS}}% mensual | Art. 21 CFF |
| Multa mínima | {{MULTA_MINIMA}} UMA | Varios |
| Multa máxima | {{MULTA_MAXIMA}} UMA | Varios |

