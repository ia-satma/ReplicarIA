---
tipo: politicas_presupuestales
version: "1.0"
agente: A5_FINANZAS
instrucciones: "Complete los campos {{}} con las políticas específicas de su empresa. Este documento establece el marco de control presupuestal para servicios intangibles."
---

# Políticas Presupuestales para Servicios Intangibles

## 1. Objetivo

Establecer las políticas, procedimientos y niveles de autorización para la aprobación y ejercicio del presupuesto destinado a la contratación de servicios profesionales e intangibles, asegurando el uso eficiente de recursos y el cumplimiento de requisitos fiscales.

## 2. Alcance

Esta política aplica a:
- Servicios profesionales y de consultoría
- Servicios tecnológicos y de desarrollo
- Servicios de marketing y publicidad
- Servicios legales y de auditoría
- Cualquier servicio clasificado como intangible

**Empresa:** {{NOMBRE_EMPRESA}}
**Vigencia:** Ejercicio {{PERIODO_FISCAL}}
**Aprobado por:** {{APROBADOR_POLITICA}}
**Fecha de Aprobación:** {{FECHA_APROBACION}}

## 3. Clasificación de Gastos

### 3.1 Categorías de Servicios Intangibles

| Código | Categoría | Descripción | Cuenta Contable |
|--------|-----------|-------------|-----------------|
| SI-01 | Consultoría Estratégica | Asesoría en estrategia y transformación | {{CUENTA_CONSULTORIA}} |
| SI-02 | Consultoría Fiscal | Servicios fiscales y cumplimiento | {{CUENTA_FISCAL}} |
| SI-03 | Servicios Legales | Asesoría legal y contratos | {{CUENTA_LEGAL}} |
| SI-04 | Tecnología | Desarrollo, implementación y soporte TI | {{CUENTA_TI}} |
| SI-05 | Marketing | Publicidad, branding, digital | {{CUENTA_MARKETING}} |
| SI-06 | Capacitación | Formación y desarrollo de talento | {{CUENTA_CAPACITACION}} |
| SI-07 | Auditoría | Auditoría interna y externa | {{CUENTA_AUDITORIA}} |
| SI-08 | {{CATEGORIA_ADICIONAL}} | {{DESC_CATEGORIA_ADICIONAL}} | {{CUENTA_ADICIONAL}} |

### 3.2 Clasificación por Naturaleza

| Tipo | Descripción | Tratamiento Presupuestal |
|------|-------------|-------------------------|
| CAPEX | Inversión en activos intangibles | Capitalizable, amortización |
| OPEX | Gasto operativo recurrente | Gasto del ejercicio |
| Proyecto | Gasto único de proyecto | Presupuesto de proyecto |

## 4. Proceso de Presupuestación

### 4.1 Ciclo Presupuestal Anual

| Etapa | Actividad | Fecha | Responsable |
|-------|-----------|-------|-------------|
| 1 | Solicitud de necesidades por área | {{FECHA_SOLICITUD}} | Directores de área |
| 2 | Consolidación y primera revisión | {{FECHA_CONSOLIDACION}} | {{ROL_CONSOLIDACION}} |
| 3 | Revisión ejecutiva | {{FECHA_REVISION_EJECUTIVA}} | {{ROL_REVISION}} |
| 4 | Ajustes y negociación | {{FECHA_AJUSTES}} | Finanzas + Áreas |
| 5 | Aprobación por Consejo | {{FECHA_APROBACION_CONSEJO}} | Consejo de Administración |
| 6 | Comunicación de presupuesto | {{FECHA_COMUNICACION}} | {{ROL_COMUNICACION}} |

### 4.2 Formato de Solicitud de Presupuesto

Para cada línea de gasto de servicios intangibles, documentar:

| Campo | Descripción | Obligatorio |
|-------|-------------|-------------|
| Categoría | Clasificación del servicio | Sí |
| Descripción | Detalle del servicio requerido | Sí |
| Proveedor tentativo | Si aplica | No |
| Monto estimado | En MXN | Sí |
| Periodicidad | Único, mensual, anual | Sí |
| Justificación de negocio | Razón de la necesidad | Sí |
| OKR/Objetivo vinculado | Alineación estratégica | Sí |
| BEE esperado | Beneficio económico | Sí |
| Trimestre requerido | Q1, Q2, Q3, Q4 | Sí |

## 5. Niveles de Autorización

### 5.1 Matriz de Autorización por Monto

| Rango de Monto (MXN) | Aprobador 1 | Aprobador 2 | Aprobador 3 |
|---------------------|-------------|-------------|-------------|
| Hasta ${{LIMITE_NIVEL_1}} | {{ROL_NIVEL_1}} | - | - |
| ${{LIMITE_NIVEL_1}} a ${{LIMITE_NIVEL_2}} | {{ROL_NIVEL_2_A}} | {{ROL_NIVEL_2_B}} | - |
| ${{LIMITE_NIVEL_2}} a ${{LIMITE_NIVEL_3}} | {{ROL_NIVEL_3_A}} | {{ROL_NIVEL_3_B}} | {{ROL_NIVEL_3_C}} |
| Mayor a ${{LIMITE_NIVEL_3}} | {{ROL_NIVEL_4_A}} | {{ROL_NIVEL_4_B}} | Consejo |

### 5.2 Autorización por Categoría Especial

| Categoría | Autorización Adicional | Motivo |
|-----------|----------------------|--------|
| Partes relacionadas | {{AUTORIZADOR_PARTES_RELACIONADAS}} | Control de precios de transferencia |
| Proveedores nuevos | {{AUTORIZADOR_NUEVOS_PROVEEDORES}} | Due diligence |
| Contratos +12 meses | {{AUTORIZADOR_LARGO_PLAZO}} | Compromiso plurianual |
| {{CATEGORIA_ESPECIAL}} | {{AUTORIZADOR_ESPECIAL}} | {{MOTIVO_ESPECIAL}} |

### 5.3 Requisitos por Nivel de Aprobación

| Nivel | Monto | Documentación Requerida |
|-------|-------|------------------------|
| 1 | Hasta ${{LIMITE_NIVEL_1}} | Solicitud interna, cotización |
| 2 | Hasta ${{LIMITE_NIVEL_2}} | Nivel 1 + Análisis costo-beneficio |
| 3 | Hasta ${{LIMITE_NIVEL_3}} | Nivel 2 + Comparativo de proveedores (mín. 3) |
| 4 | Mayor a ${{LIMITE_NIVEL_3}} | Nivel 3 + Presentación ejecutiva + Aprobación Consejo |

## 6. Control de Ejercicio Presupuestal

### 6.1 Reglas de Ejercicio

1. **Disponibilidad presupuestal:** Todo gasto debe contar con partida presupuestal autorizada
2. **No sobregiro:** No se permite exceder el presupuesto sin autorización
3. **Transferencias:** Requieren aprobación de {{AUTORIZADOR_TRANSFERENCIAS}}
4. **Cancelaciones:** Se reportan a Finanzas para reasignación

### 6.2 Umbrales de Alerta

| Indicador | Nivel Verde | Nivel Amarillo | Nivel Rojo |
|-----------|-------------|----------------|------------|
| % Ejercido vs Tiempo | ≤ {{PCT_VERDE_TIEMPO}} | {{PCT_VERDE_TIEMPO}}-{{PCT_AMARILLO_TIEMPO}} | > {{PCT_ROJO_TIEMPO}} |
| Desviación vs Plan | ≤ {{PCT_VERDE_DESVIACION}} | {{PCT_VERDE_DESVIACION}}-{{PCT_AMARILLO_DESVIACION}} | > {{PCT_ROJO_DESVIACION}} |
| Compromisos pendientes | ≤ {{PCT_VERDE_COMPROMISOS}} | {{PCT_VERDE_COMPROMISOS}}-{{PCT_AMARILLO_COMPROMISOS}} | > {{PCT_ROJO_COMPROMISOS}} |

### 6.3 Reporte de Seguimiento

**Frecuencia de reportes:**

| Reporte | Frecuencia | Destinatarios |
|---------|------------|---------------|
| Estatus de ejercicio | {{FRECUENCIA_ESTATUS}} | Directores de área |
| Análisis de desviaciones | {{FRECUENCIA_DESVIACIONES}} | {{DESTINATARIOS_DESVIACIONES}} |
| Proyección de cierre | {{FRECUENCIA_PROYECCION}} | {{DESTINATARIOS_PROYECCION}} |
| Reporte ejecutivo | {{FRECUENCIA_EJECUTIVO}} | Comité de Dirección |

## 7. Modificaciones Presupuestales

### 7.1 Tipos de Modificaciones

| Tipo | Descripción | Aprobación |
|------|-------------|------------|
| Transferencia | Mover recursos entre partidas | {{AUTORIZADOR_TRANSFERENCIAS}} |
| Adición | Incremento al presupuesto total | {{AUTORIZADOR_ADICIONES}} |
| Reducción | Disminución de partida | {{AUTORIZADOR_REDUCCIONES}} |
| Cancelación | Eliminación de partida | {{AUTORIZADOR_CANCELACIONES}} |

### 7.2 Proceso de Modificación

1. **Solicitud:** Área solicitante presenta formato de modificación
2. **Análisis:** Finanzas evalúa impacto y disponibilidad
3. **Aprobación:** Según matriz de autorización
4. **Registro:** Actualización en sistema presupuestal
5. **Comunicación:** Notificación a interesados

### 7.3 Límites de Modificación

| Modificación | Límite sin Consejo | Requiere Consejo |
|--------------|-------------------|------------------|
| Transferencia entre áreas | ${{LIMITE_TRANSFERENCIA_AREAS}} | Mayor a límite |
| Adición total anual | {{PCT_LIMITE_ADICION}}% del presupuesto | Mayor a límite |
| Por evento individual | ${{LIMITE_EVENTO_INDIVIDUAL}} | Mayor a límite |

## 8. Compromisos y Devengado

### 8.1 Registro de Compromisos

Todo contrato firmado genera un compromiso presupuestal:

| Momento | Acción | Responsable |
|---------|--------|-------------|
| Firma de contrato | Registro de compromiso | {{ROL_REGISTRO_COMPROMISO}} |
| Recepción de servicio | Devengado | {{ROL_DEVENGADO}} |
| Facturación | Programación de pago | {{ROL_PAGOS}} |
| Pago | Ejercido | Tesorería |

### 8.2 Control de Compromisos Plurianuales

Para contratos que exceden el ejercicio fiscal:

- Registro del compromiso total
- Distribución por ejercicio fiscal
- Autorización de {{AUTORIZADOR_PLURIANUAL}}
- Reserva presupuestal para ejercicios futuros

## 9. Cierre Presupuestal

### 9.1 Calendario de Cierre

| Actividad | Fecha Límite |
|-----------|--------------|
| Último día para comprometer | {{FECHA_LIMITE_COMPROMISO}} |
| Último día para devengar | {{FECHA_LIMITE_DEVENGADO}} |
| Conciliación final | {{FECHA_CONCILIACION_FINAL}} |
| Cierre contable | {{FECHA_CIERRE_CONTABLE}} |

### 9.2 Tratamiento de Remanentes

| Situación | Tratamiento |
|-----------|-------------|
| Subejercicio < {{PCT_SUBEJERCICIO_MENOR}}% | Se cancela, no transfiere |
| Subejercicio {{PCT_SUBEJERCICIO_MENOR}}-{{PCT_SUBEJERCICIO_MAYOR}}% | Análisis caso por caso |
| Proyectos en proceso | Puede transferirse al siguiente ejercicio |

## 10. Responsabilidades

### 10.1 Matriz de Responsabilidades

| Rol | Responsabilidades |
|-----|-------------------|
| Solicitante (Área) | Identificar necesidades, justificar, gestionar |
| Director de Área | Aprobar en su nivel, vigilar ejercicio |
| Finanzas | Consolidar, controlar, reportar |
| Compras | Proceso de contratación, negociación |
| Contraloría | Verificar cumplimiento de políticas |
| Consejo | Aprobar presupuesto anual y adiciones mayores |

### 10.2 Incumplimientos

| Incumplimiento | Consecuencia |
|----------------|--------------|
| Gasto sin presupuesto | Responsabilidad del área, proceso administrativo |
| Sobregiro no autorizado | Sanción conforme a políticas internas |
| Falta de documentación | Retención de pago hasta regularización |

---

*Este documento es el marco normativo para el manejo presupuestal de servicios intangibles. Consulte con el área de Finanzas para casos específicos.*
