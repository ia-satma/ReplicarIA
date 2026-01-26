---
tipo: normativo
version: "1.0"
agente: A3_FISCAL
instrucciones: "Extracto de artículos clave de la Ley del Impuesto Sobre la Renta (LISR) aplicables a la deducción de servicios intangibles. Referencia normativa para análisis de deducibilidad."
---

# Extracto de la Ley del Impuesto Sobre la Renta (LISR)

## 1. Deducciones Autorizadas

### Artículo 25 – Deducciones Autorizadas para Personas Morales

**Deducciones permitidas:**

| Fracción | Concepto | Aplicación a Servicios |
|----------|----------|------------------------|
| I | Devoluciones, descuentos o bonificaciones | Ajustes a facturación |
| II | Costo de lo vendido | Servicios de terceros en producción |
| III | Gastos netos | **Servicios profesionales e intangibles** |
| IV | Inversiones | Activos intangibles |
| VII | Intereses devengados | Financiamiento de servicios |
| X | Anticipos | Pagos adelantados de servicios |

### Artículo 27 – Requisitos de las Deducciones

**Requisitos generales:**

| Fracción | Requisito | Verificación |
|----------|-----------|--------------|
| I | Estrictamente indispensables | Test de indispensabilidad |
| III | Amparadas con CFDI | Validación en SAT |
| III | Pago > $2,000 bancarizado | Estado de cuenta |
| IV | Registradas en contabilidad | Pólizas contables |
| V | Retenciones enteradas (si aplica) | Declaraciones |
| VIII | Efectivamente erogadas | Flujo de efectivo |

**Requisitos específicos para servicios:**

```
┌─────────────────────────────────────────────────────────────┐
│          REQUISITOS ESPECÍFICOS - SERVICIOS                 │
├─────────────────────────────────────────────────────────────┤
│ ✓ Descripción detallada del servicio en CFDI               │
│ ✓ Código SAT correcto                                       │
│ ✓ Uso CFDI apropiado (G03 - Gastos en general)             │
│ ✓ Contrato para servicios mayores a {{UMBRAL_CONTRATO}}    │
│ ✓ Evidencia de prestación del servicio                      │
│ ✓ Pago desde cuenta del contribuyente                       │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Deducciones No Autorizadas

### Artículo 28 – Gastos No Deducibles

**Partidas no deducibles relevantes:**

| Fracción | Concepto | Descripción |
|----------|----------|-------------|
| I | Sin requisitos fiscales | Gastos sin CFDI o requisitos del Art. 27 |
| III | Obsequios y atenciones | Excepto estrictamente indispensables |
| V | Gastos de representación | Con limitaciones |
| VII | Provisiones preventivas | Reservas no materializadas |
| VIII | Intereses no deducibles | Capitalización delgada (3:1) |
| XVII | Pagos a REFIPRES | Con excepciones |
| XXIII | Operaciones con EFOS | Lista 69-B definitiva |
| XXX | Pagos sin materialidad | Art. 69-B relacionados |

**Gastos parcialmente deducibles:**

| Concepto | Límite Deducible | Fundamento |
|----------|------------------|------------|
| Consumo en restaurantes | 91.5% | Art. 28 Fr. XX |
| Automóviles | $175,000 MOI | Art. 36 |
| Aviones | Límites específicos | Art. 36 |
| Donativos | 7% utilidad fiscal | Art. 27 Fr. I |

---

## 3. Precios de Transferencia

### Artículo 76 Fracciones IX, X, XII – Obligaciones PT

**Operaciones entre partes relacionadas:**

| Obligación | Descripción | Plazo |
|------------|-------------|-------|
| Declaración informativa | Operaciones con relacionadas | Diciembre del ejercicio siguiente |
| Estudio de PT | Documentación contemporánea | Durante el ejercicio |
| Master file | Grupos multinacionales | 12 meses después del ejercicio |
| Local file | Documentación local | 12 meses después del ejercicio |
| CbCR | Country by Country Report | 12 meses (matriz) |

### Artículo 179 – Métodos de Precios de Transferencia

**Métodos aplicables:**

| Método | Siglas | Uso Principal |
|--------|--------|---------------|
| Precio Comparable No Controlado | CUP | Transacciones con comparables directos |
| Precio de Reventa | PR | Distribuidores |
| Costo Adicionado | CA | Manufactureros, servicios |
| Partición de Utilidades | PU | Operaciones integradas |
| Residual de Partición | RPU | Intangibles únicos |
| Márgenes Transaccionales | TNMM | Servicios, general |

**Orden de prelación:**

1. CUP (preferente cuando hay comparables)
2. Demás métodos según mejor refleje arm's length

---

## 4. Servicios Específicos

### Servicios Técnicos y de Asistencia Técnica

**Artículo 167 LISR – Retención a residentes en el extranjero:**

| Concepto | Tasa de Retención | Condiciones |
|----------|-------------------|-------------|
| Regalías | 25% (general) / 10% (software) | Sin establecimiento permanente |
| Asistencia técnica | 25% | Sin EP |
| Publicidad | 25% | Sin EP |
| Servicios independientes | 25% | Sin EP |

**Tratados para evitar doble tributación:**
- Tasas reducidas según tratado aplicable
- Requisito de residencia fiscal certificada
- Formato de retención correspondiente

### Regalías y Asistencia Técnica (Artículos 15-B CFF y 167 LISR)

**Definición de regalías (Art. 15-B CFF):**

> "Los pagos de cualquier clase por el uso o goce temporal de patentes, certificados de invención o mejora, marcas de fábrica, nombres comerciales, derechos de autor..."

**Tipos de regalías:**

| Tipo | Descripción | Tratamiento |
|------|-------------|-------------|
| Propiedad industrial | Patentes, marcas, diseños | Deducible con requisitos |
| Derechos de autor | Software, contenido | Deducible con requisitos |
| Know-how | Conocimientos técnicos | Documentación reforzada |
| Franquicias | Uso de modelo de negocio | Contrato específico |

---

## 5. Ajuste Anual por Inflación

### Artículos 44-46 – Componente Inflacionario

**Impacto en cuentas por pagar:**

| Concepto | Tratamiento |
|----------|-------------|
| Deudas contratadas | Generan ajuste inflacionario |
| Anticipos recibidos | No generan ajuste |
| Provisiones | No generan ajuste |

**Cálculo:**
```
Ajuste Anual por Inflación = Promedio Anual de Deudas × Factor de Ajuste

Factor de Ajuste = (INPC dic ejercicio / INPC dic ejercicio anterior) - 1
```

---

## 6. Tablas de Referencia

### Tasas de ISR Personas Morales

| Ejercicio | Tasa |
|-----------|------|
| {{EJERCICIO_1}} | {{TASA_1}}% |
| {{EJERCICIO_2}} | {{TASA_2}}% |
| {{EJERCICIO_ACTUAL}} | 30% |

### Límites de Deducción

| Concepto | Límite | Fundamento |
|----------|--------|------------|
| Automóviles | $175,000 | Art. 36 Fr. II |
| Automóviles eléctricos | $250,000 | Art. 36 Fr. II |
| Arrendamiento auto | $200/día | Art. 28 Fr. XIII |
| Viáticos nacionales | $750/día | Art. 28 Fr. V |
| Viáticos extranjero | $1,500/día | Art. 28 Fr. V |

### Depreciación de Intangibles (Art. 33)

| Tipo de Activo Intangible | Tasa Máxima Anual |
|---------------------------|-------------------|
| Gastos diferidos | 5% |
| Gastos preoperativos | 10% |
| Regalías pagadas por adelantado | Según contrato |
| Software (desarrollo propio) | 30% |
| Otros intangibles | 15% |

---

## 7. Infracciones y Sanciones Relacionadas

### Multas por Incumplimiento

| Infracción | Sanción | Fundamento |
|------------|---------|------------|
| No expedir CFDI | $17,020 a $97,330 | Art. 84 Fr. IV CFF |
| CFDI sin requisitos | $17,020 a $97,330 | Art. 84 Fr. IV CFF |
| No llevar contabilidad | $1,400 a $17,370 | Art. 84 Fr. I CFF |
| Deducción indebida | 55% a 75% de contribución omitida | Art. 76 CFF |

### Actualización y Recargos

| Concepto | Cálculo |
|----------|---------|
| Actualización | INPC mes pago / INPC mes causación |
| Recargos | {{TASA_RECARGOS}}% mensual sobre monto actualizado |
| Multas | 55% - 75% del impuesto omitido |

---

## 8. Casos Especiales

### Pagos a Partes Relacionadas

**Requisitos adicionales:**

1. Precios de mercado (arm's length)
2. Estudio de precios de transferencia
3. Declaración informativa
4. Documentación contemporánea

### Servicios Intragrupo

**Requisitos LISR/CFF:**

| Requisito | Fundamento | Verificación |
|-----------|------------|--------------|
| Beneficio demostrable | Art. 27 Fr. I | Cuantificación de BEE |
| Precio de mercado | Art. 179 | Estudio PT |
| No duplicación | Práctica internacional | Análisis de funciones |
| No shareholder activity | OCDE Guidelines | Identificación de actividades |

