# Tipología: Campaña Marketing Digital para Cadena de Gimnasios

## Caso de Uso: GymMax - Campaña Elite Q3 2026

Este documento representa un caso de uso integrado que recorre el flujo F0-F9 completo con todos los agentes A1-A7.

---

## 1. Descripción del Escenario

**Cliente:** Cadena de gimnasios "GymMax" (5 sucursales)
**Servicio:** Campaña de marketing digital para lanzamiento de membresía "Elite"
**Proveedor:** Agencia Digital FitAds, S.A. de C.V.
**Monto:** $900,000 MXN
**Horizonte:** 6-12 meses

## 2. Riesgo Fiscal Inherente: MEDIO-ALTO

### Factores de riesgo específicos del caso
- Servicios intangibles (publicidad digital)
- Resultados difíciles de atribuir exclusivamente
- Industria con alta rotación de proveedores de marketing
- Montos significativos para servicios de agencia

---

## 3. Flujo F0-F9 Integrado

### F0 - SIB/BEE (Service Initiation Brief)

**Datos del proyecto:**
```json
{
  "nombre_proyecto": "Campaña Digital Elite Q3 2026",
  "descripcion": "Campaña digital en Meta/Google/YouTube para captar socios membresía Elite en 5 clubes",
  "tipo_servicio": "MARKETING_DIGITAL",
  "problema_a_resolver": "Bajo porcentaje de socios en membresía premium (actualmente 15%)",
  "objetivo_principal": "+500 nuevas membresías Elite en 3 meses, ROAS mínimo 3x",
  "tipo_beneficio": "INGRESOS",
  "monto_estimado": 900000,
  "horizonte_meses": 12,
  "vinculacion": {
    "pilar_estrategico": "Crecimiento en segmento premium",
    "okr_relacionado": "OKR 2026-01: Incrementar socios activos 20%"
  },
  "kpis": [
    {"nombre": "Leads generados", "valor_objetivo": "3000", "unidad": "leads"},
    {"nombre": "Conversiones", "valor_objetivo": "500", "unidad": "membresías"},
    {"nombre": "ROAS", "valor_objetivo": "3.0", "unidad": "ratio"}
  ]
}
```

**Dictamen A1_ESTRATEGIA:**
```json
{
  "razon_negocios_identificada": "Incremento de socios premium para mejorar margen y reducir churn",
  "razon_negocios_solidez": "FUERTE",
  "score": {
    "sustancia_economica": 5,
    "proposito_concreto": 5,
    "coherencia_estrategica": 4,
    "bee_describible": 4,
    "documentacion_contemporanea": 4,
    "total": 22
  },
  "estado": "CONFORME",
  "recomendacion_f2": "AVANZAR"
}
```

---

### F1 - Alta de Proveedor

**Datos del proveedor:**
```json
{
  "datos_legales_fiscales": {
    "rfc": "AFD190515XX9",
    "razon_social": "Agencia Digital FitAds, S.A. de C.V.",
    "objeto_social": "Servicios de publicidad y marketing digital",
    "capital_social": 500000,
    "fecha_constitucion": "2019-05-15"
  },
  "datos_contacto_operativos": {
    "sitio_web": "https://fitads.com.mx",
    "email_principal": "contacto@fitads.com.mx"
  },
  "documentos": [
    {"tipo": "CSF", "verificado": true},
    {"tipo": "OPINION_32D", "verificado": true},
    {"tipo": "ACTA_CONSTITUTIVA", "verificado": true}
  ],
  "estatus_lista_69b": "LIMPIO"
}
```

**Dictamen A6_PROVEEDOR:**
```json
{
  "score": {
    "capacidad_juridica": 18,
    "capacidad_material": 28,
    "cumplimiento_fiscal": 30,
    "historial_comercial": 9,
    "total": 85
  },
  "nivel_riesgo": "BAJO",
  "flags": [],
  "recomendacion": "APROBAR"
}
```

---

### F2 - Candado de Inicio

**Verificación A2_PMO:**
```
✓ A1_ESTRATEGIA = CONFORME (score 22/25)
✓ A6_PROVEEDOR = APROBAR (score 85/100)
✓ SOW preliminar cargado
✓ No hay flags bloqueantes

RESULTADO: F2 COMPLETA (sin excepción)
```

**SOW Preliminar:**
- Alcance: Campaña 360° en Meta, Google, YouTube
- Entregables: Piezas creativas, plan de medios, reportes mensuales
- Duración: 3 meses de ejecución + 9 de seguimiento

---

### F3-F4 - Ejecución y Revisión

**Minutas registradas:**
1. Kickoff - Definición de audiencias y mensajes clave
2. Revisión creativa V1 - Ajustes en segmentación
3. Mid-campaign review - Optimización de presupuesto por canal
4. Pre-cierre - Validación de resultados preliminares

**Entregables V1/V2:**
- Brief aprobado (V1, VF)
- Plan de medios (V1, V2, VF)
- Creatividades (20 piezas: imagen + video)
- Reportes semanales de performance

---

### F5 - Entrega y Aceptación

**Resultados de campaña:**
```json
{
  "leads_generados": 3200,
  "conversiones": 520,
  "roas_real": 3.2,
  "inversion_publicitaria": 600000,
  "fee_agencia": 300000
}
```

**Acta de Aceptación Técnica:**
- Firmada por: Director de Marketing GymMax
- Fecha: 2026-09-30
- Observaciones: "Objetivos cumplidos y superados"

---

### F6 - Candado Fiscal/Legal

**Dictamen A3_FISCAL:**
```json
{
  "cumplimiento_lisr27": "CUMPLE",
  "score": {
    "estricta_indispensabilidad": 25,
    "documentacion_cfdi": 22,
    "bancarizacion": 15,
    "registro_contable": 10,
    "riesgo_efos": 25,
    "total": 97
  },
  "cfdi_concepto_especifico": true,
  "materialidad_suficiente": true,
  "porcentaje_materialidad": 95,
  "recomendacion_f6": "APROBAR",
  "dictamen_deducibilidad": "Deducción procedente. Cumple requisitos LISR 27."
}
```

**Dictamen A4_LEGAL:**
```json
{
  "tipo_contrato": "MARKETING",
  "tiene_contrato": true,
  "clausulas_presentes": 9,
  "clausulas_faltantes": 1,
  "score": {
    "objeto_alcance": 5,
    "entregables_aceptacion": 5,
    "cooperacion_evidencia": 5,
    "pi_confidencialidad": 5,
    "cumplimiento_regulatorio": 3,
    "total": 23
  },
  "recomendacion_f6": "APROBAR_CON_MODIFICACIONES",
  "areas_mejora": ["Reforzar cláusula de terminación para futuros contratos"]
}
```

**Dictamen A5_FINANZAS:**
```json
{
  "analisis": {
    "inversion": 900000,
    "beneficios_esperados": 6240000,
    "horizonte_meses": 12
  },
  "metricas": {
    "roi": 5.93,
    "npv": 4890909,
    "payback_meses": 1.7,
    "beneficio_neto": 5340000
  },
  "score": {
    "roi_razonabilidad": 5,
    "npv_positivo": 5,
    "payback_aceptable": 5,
    "bee_cuantificable": 5,
    "precio_mercado": 5,
    "total": 25
  },
  "recomendacion": "APROBAR"
}
```

**Cálculo del beneficio:**
- 520 membresías Elite × $1,000/mes × 12 meses = $6,240,000 MXN

---

### F7 - Auditoría Interna

**Checklist de documentación:**
- ✓ Contrato firmado antes de ejecución
- ✓ SOW con KPIs específicos
- ✓ Brief y plan de medios aprobados
- ✓ Creatividades y piezas publicitarias
- ✓ Reportes de plataformas (Meta, Google)
- ✓ Acta de aceptación firmada
- ✓ CFDI con concepto específico
- ✓ Comprobante de pago bancario

---

### F8 - Candado de Pago

**3-Way Match:**
```
PO/SOW:      $900,000 MXN
Acta cierre: $900,000 MXN (servicios completos)
CFDI:        $900,000 MXN

MATCH: ✓ VÁLIDO
```

**Liberación de pago:**
- Sin vetos activos
- Pago vía transferencia SPEI
- Fecha: 2026-10-05

---

### F9 - Seguimiento BEE

**Resultados reales a 12 meses:**
```json
{
  "membresías_elite_vendidas": 520,
  "membresías_objetivo": 500,
  "cumplimiento_meta": "104%",
  "roas_real": 3.2,
  "roas_objetivo": 3.0,
  "mejora_mix_premium": "15% → 23%",
  "roi_real": "593%"
}
```

**Actualización A1:**
- Narrativa de éxito documentada
- Proyecto sirve como caso de referencia para futuras campañas

---

## 4. Defense File Resultante

### Estructura del Defense File

| Sección | Contenido | Score |
|---------|-----------|-------|
| 05 - Razón de Negocios | Dictamen A1: CONFORME 22/25 | ✓ |
| 06 - Beneficio Económico | Dictamen A5: ROI 593%, NPV $4.9M | ✓ |
| 07 - Materialidad | 95% evidencias completas | ✓ |
| 08 - Fiscal | Dictamen A3: APROBAR 97/100 | ✓ |
| 09 - Proveedor | Dictamen A6: APROBAR 85/100 | ✓ |
| 10 - Legal | Dictamen A4: APROBAR 23/25 | ✓ |

### Scores consolidados

- **Score Materialidad:** 95%
- **Score Trazabilidad:** 100% (10/10 fases documentadas)
- **Score Defensa:** 96%

---

## 5. Narrativa ante SAT

**Ante un requerimiento de información, GymMax puede demostrar:**

1. **PARA QUÉ SE HIZO** (Razón de Negocios)
   - Incrementar socios en membresía premium
   - Mejorar margen operativo de la cadena
   - Alineado con OKR corporativo 2026

2. **QUÉ SE RECIBIÓ** (Materialidad)
   - Brief y plan de medios aprobados
   - 20 piezas creativas (imágenes y videos)
   - Campañas publicadas en Meta/Google/YouTube
   - Reportes mensuales de performance
   - Acta de aceptación firmada

3. **CUÁNTO COSTÓ** (Documentación)
   - CFDI $900,000 con concepto específico
   - Pago bancarizado vía SPEI
   - Desglose: $600K pauta + $300K fee agencia

4. **QUÉ VALOR GENERÓ** (BEE realizado)
   - 520 nuevas membresías Elite (104% de meta)
   - ROAS 3.2x (superó objetivo de 3.0x)
   - Ingresos adicionales $6.24M anuales
   - ROI real 593%

5. **DILIGENCIA CON PROVEEDOR** (Due Diligence)
   - Opinión 32-D positiva
   - Sin antecedentes 69-B
   - 5 años de experiencia
   - Presencia web y portafolio verificados

---

## 6. Lecciones y Mejores Prácticas

### Lo que funcionó bien
- SIB completo con KPIs específicos desde F0
- Due diligence exhaustivo antes de contratar
- Documentación contemporánea (minutas, versiones)
- Seguimiento de resultados reales en F9

### Recomendaciones para futuros proyectos similares
1. Exigir acceso a dashboards de plataformas publicitarias
2. Establecer reviews quincenales, no solo mensuales
3. Incluir cláusula de cooperación fiscal más detallada
4. Documentar screenshots de campañas activas
