# Configuración de Agentes - Cuentas de Email @revisar-ia.com

## Cuentas de Email Configuradas (11 Agentes)

### Agentes Principales (7)

#### A1 - María Rodríguez (Directora de Estrategia)
- **Email:** estrategia@revisar-ia.com
- **LLM:** Claude 3.7 Sonnet
- **pCloud Folder:** A1_ESTRATEGIA
- **Función:** Validación estratégica de proyectos

#### A2 - Carlos Mendoza (PMO)
- **Email:** pmo@revisar-ia.com
- **LLM:** Claude 3.7 Sonnet
- **pCloud Folder:** A2_PMO
- **Función:** Consolidación, orquestación, generación de PO y reportes

#### A3 - Laura Sánchez (Fiscal)
- **Email:** fiscal@revisar-ia.com
- **LLM:** Claude 3.7 Sonnet
- **pCloud Folder:** A3_FISCAL
- **Función:** Cumplimiento fiscal, razón de negocios, materialidad

#### A4 - Ana Martínez (Legal)
- **Email:** legal@revisar-ia.com
- **LLM:** Claude 3.7 Sonnet
- **pCloud Folder:** A4_LEGAL
- **Función:** Contratos, revisión legal, Defense File, auditorías SAT

#### A5 - Roberto Torres (Finanzas)
- **Email:** finanzas@revisar-ia.com
- **LLM:** Claude 3.7 Sonnet
- **pCloud Folder:** A5_FINANZAS
- **Función:** Análisis financiero, ROI, viabilidad presupuestal

#### A8 - Diego Ramírez (Auditor Documental)
- **Email:** auditoria@revisar-ia.com
- **LLM:** Claude 3.7 Sonnet
- **pCloud Folder:** A8_AUDITOR
- **Función:** Verificación de cumplimiento documental, auditoría de Defense File

#### PROV - Comunicaciones Proveedor
- **Email:** proveedor@revisar-ia.com
- **Función:** Comunicación con proveedores externos

---

### Subagentes Especializados (4)

#### SUB_TIP - Patricia López (Tipificación de Servicios)
- **Email:** tipificacion@revisar-ia.com
- **LLM:** Claude 3.7 Sonnet
- **pCloud Folder:** SUB_TIPIFICACION
- **Función:** Clasificación de servicios según tipología fiscal

#### SUB_MAT - Fernando Ruiz (Materialidad)
- **Email:** materialidad@revisar-ia.com
- **LLM:** Claude 3.7 Sonnet
- **pCloud Folder:** SUB_MATERIALIDAD
- **Función:** Monitoreo de materialidad de servicios

#### SUB_RISK - Gabriela Vega (Riesgos Especiales)
- **Email:** riesgos@revisar-ia.com
- **LLM:** Claude 3.7 Sonnet
- **pCloud Folder:** SUB_RIESGOS
- **Función:** Detección de riesgos fiscales especiales

#### A7 - Héctor Mora (Defense File)
- **Email:** defensa@revisar-ia.com
- **LLM:** Claude 3.7 Sonnet
- **pCloud Folder:** A7_DEFENSA
- **Función:** Generación de expedientes de defensa fiscal

---

## Resumen de Correos Configurados

| ID | Agente | Email | Tipo |
|-----|--------|-------|------|
| A1 | María Rodríguez | estrategia@revisar-ia.com | Principal |
| A2 | Carlos Mendoza | pmo@revisar-ia.com | Principal |
| A3 | Laura Sánchez | fiscal@revisar-ia.com | Principal |
| A4 | Ana Martínez | legal@revisar-ia.com | Principal |
| A5 | Roberto Torres | finanzas@revisar-ia.com | Principal |
| A8 | Diego Ramírez | auditoria@revisar-ia.com | Principal |
| PROV | Comunicaciones | proveedor@revisar-ia.com | Externo |
| SUB_TIP | Patricia López | tipificacion@revisar-ia.com | Subagente |
| SUB_MAT | Fernando Ruiz | materialidad@revisar-ia.com | Subagente |
| SUB_RISK | Gabriela Vega | riesgos@revisar-ia.com | Subagente |
| A7 | Héctor Mora | defensa@revisar-ia.com | Subagente |

---

## Contraseña Compartida
Todos los agentes usan la misma contraseña configurada en el secret `DREAMHOST_EMAIL_PASSWORD`.

---

## Trazabilidad en Defense File

Cada proyecto registra en su Defense File:
1. **Opiniones de agentes/subagentes** - Deliberaciones, validaciones, rechazos
2. **Órdenes de compra** - Con monto, vendor, status
3. **Solicitudes de contrato a Legal** - Tipo de contrato, términos
4. **Cambios solicitados al proveedor** - Ajustes, correcciones, documentación adicional
5. **Bitácora de comunicaciones** - Todos los emails entre agentes
6. **Consolidación PMO** - Reporte consolidado final
7. **Historial de versiones** - Cada cambio con timestamp y usuario

---

Última actualización: 2026-01-19
