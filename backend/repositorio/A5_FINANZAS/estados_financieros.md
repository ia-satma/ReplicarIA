# Estados Financieros - Template de Análisis

---

## Estado de Situación Financiera (Balance General)

### Empresa: {{NOMBRE_EMPRESA}}
### Período: {{PERIODO}}

| Concepto | {{AÑO_ACTUAL}} | {{AÑO_ANTERIOR}} | Variación |
|----------|----------------|------------------|-----------|
| **ACTIVO** | | | |
| Activo Circulante | | | |
| - Efectivo y equivalentes | {{EFECTIVO}} | {{EFECTIVO_ANT}} | {{VAR_EFECTIVO}} |
| - Cuentas por cobrar | {{CXC}} | {{CXC_ANT}} | {{VAR_CXC}} |
| - Inventarios | {{INV}} | {{INV_ANT}} | {{VAR_INV}} |
| **Total Activo Circulante** | {{TOTAL_AC}} | {{TOTAL_AC_ANT}} | |
| Activo No Circulante | | | |
| - Propiedades, planta y equipo | {{PPE}} | {{PPE_ANT}} | |
| - Activos intangibles | {{INTANG}} | {{INTANG_ANT}} | |
| **Total Activo No Circulante** | {{TOTAL_ANC}} | {{TOTAL_ANC_ANT}} | |
| **TOTAL ACTIVO** | {{TOTAL_ACTIVO}} | {{TOTAL_ACTIVO_ANT}} | |
| | | | |
| **PASIVO** | | | |
| Pasivo Circulante | | | |
| - Cuentas por pagar | {{CXP}} | {{CXP_ANT}} | |
| - Impuestos por pagar | {{IMP_PAGAR}} | {{IMP_PAGAR_ANT}} | |
| **Total Pasivo Circulante** | {{TOTAL_PC}} | {{TOTAL_PC_ANT}} | |
| Pasivo No Circulante | | | |
| - Deuda a largo plazo | {{DEUDA_LP}} | {{DEUDA_LP_ANT}} | |
| **Total Pasivo** | {{TOTAL_PASIVO}} | {{TOTAL_PASIVO_ANT}} | |
| | | | |
| **CAPITAL CONTABLE** | | | |
| - Capital social | {{CAP_SOCIAL}} | {{CAP_SOCIAL_ANT}} | |
| - Utilidades retenidas | {{UTIL_RET}} | {{UTIL_RET_ANT}} | |
| - Resultado del ejercicio | {{RESULTADO}} | {{RESULTADO_ANT}} | |
| **Total Capital** | {{TOTAL_CAPITAL}} | {{TOTAL_CAPITAL_ANT}} | |
| **TOTAL PASIVO + CAPITAL** | {{TOTAL_PYC}} | {{TOTAL_PYC_ANT}} | |

---

## Estado de Resultados

| Concepto | {{AÑO_ACTUAL}} | {{AÑO_ANTERIOR}} | Variación % |
|----------|----------------|------------------|-------------|
| Ingresos por servicios | {{INGRESOS}} | {{INGRESOS_ANT}} | {{VAR_ING}} |
| Costo de ventas | {{COSTO}} | {{COSTO_ANT}} | {{VAR_COSTO}} |
| **Utilidad Bruta** | {{UTIL_BRUTA}} | {{UTIL_BRUTA_ANT}} | |
| Gastos de operación | {{GASTOS_OP}} | {{GASTOS_OP_ANT}} | |
| - Gastos de administración | {{GASTOS_ADMIN}} | | |
| - Gastos de venta | {{GASTOS_VENTA}} | | |
| **Utilidad de Operación** | {{UTIL_OP}} | {{UTIL_OP_ANT}} | |
| Gastos financieros | {{GASTOS_FIN}} | {{GASTOS_FIN_ANT}} | |
| **Utilidad antes de impuestos** | {{UAI}} | {{UAI_ANT}} | |
| ISR | {{ISR}} | {{ISR_ANT}} | |
| **Utilidad Neta** | {{UTIL_NETA}} | {{UTIL_NETA_ANT}} | |

---

## Razones Financieras

### Liquidez
| Razón | Fórmula | Resultado | Benchmark |
|-------|---------|-----------|-----------|
| Razón circulante | AC/PC | {{RC}} | > 1.5 |
| Prueba ácida | (AC-Inv)/PC | {{PA}} | > 1.0 |
| Capital de trabajo | AC - PC | {{CT}} | Positivo |

### Rentabilidad
| Razón | Fórmula | Resultado | Benchmark |
|-------|---------|-----------|-----------|
| Margen bruto | UB/Ingresos | {{MB}}% | > 30% |
| Margen operativo | UO/Ingresos | {{MO}}% | > 15% |
| Margen neto | UN/Ingresos | {{MN}}% | > 10% |
| ROE | UN/Capital | {{ROE}}% | > 15% |
| ROA | UN/Activos | {{ROA}}% | > 10% |

### Apalancamiento
| Razón | Fórmula | Resultado | Benchmark |
|-------|---------|-----------|-----------|
| Endeudamiento | Pasivo/Activo | {{END}}% | < 50% |
| Deuda/Capital | Pasivo/Capital | {{DC}} | < 1.0 |

---

## Análisis para Validación Fiscal

### Indicadores de Sustancia Económica
- [ ] Ingresos consistentes con operaciones declaradas
- [ ] Gastos proporcionales al nivel de operación
- [ ] Márgenes dentro de rangos de industria
- [ ] Capital suficiente para operaciones

### Señales de Alerta
- Márgenes de utilidad anormalmente altos o bajos
- Crecimiento de ingresos sin incremento proporcional en activos
- Gastos excesivos en proporción a ingresos
- Falta de inversión en activos fijos

---
*Template para análisis financiero - Completar con datos reales.*
