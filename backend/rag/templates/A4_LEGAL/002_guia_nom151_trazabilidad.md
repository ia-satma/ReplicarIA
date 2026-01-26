---
tipo: guia_normativa
version: "1.0"
agente: A4_LEGAL
instrucciones: "Esta guía establece los requisitos de conservación documental conforme a NOM-151. Aplique estos lineamientos a todos los documentos electrónicos relacionados con servicios intangibles."
---

# Guía NOM-151 y Trazabilidad Documental

## 1. Introducción

La NOM-151-SCFI-2016 establece los requisitos para la conservación de mensajes de datos y digitalización de documentos. Esta guía aplica estos requisitos a la documentación de servicios intangibles para asegurar su validez probatoria ante autoridades fiscales.

## 2. Fundamento Legal

### 2.1 Marco Normativo Aplicable

| Ordenamiento | Artículos Relevantes | Aplicación |
|--------------|---------------------|------------|
| Código de Comercio | Art. 89-94 | Mensajes de datos como prueba |
| Código Fiscal de la Federación | Art. 28-30 | Conservación de contabilidad |
| NOM-151-SCFI-2016 | Completa | Requisitos técnicos de conservación |
| LFPDPPP | Art. 9, 11, 12 | Protección de datos en documentos |

### 2.2 Período de Conservación Obligatorio

Conforme al artículo 30 del CFF, los documentos deben conservarse por:
- **Período base:** 5 años contados a partir de la fecha de presentación de la declaración
- **Casos especiales:** {{PERIODO_CONSERVACION_ESPECIAL}} años cuando {{SUPUESTO_PERIODO_ESPECIAL}}

## 3. Requisitos de Conservación NOM-151

### 3.1 Elementos Técnicos Obligatorios

Para que un documento electrónico tenga validez probatoria, debe cumplir:

| Requisito | Descripción | Verificación |
|-----------|-------------|--------------|
| **Integridad** | El documento no ha sido alterado desde su creación | Hash SHA-256 o superior |
| **Atribuibilidad** | Identifica claramente al emisor | Firma electrónica o certificado |
| **Accesibilidad** | Disponible para consulta cuando se requiera | Sistema de gestión documental |
| **Conservación** | Mantenido en su formato original o migrado correctamente | Constancia de conservación |

### 3.2 Firma Electrónica Avanzada (FIEL/e.firma)

Para documentos que requieren firma electrónica:

1. **Contratos marco:** Requieren firma FIEL de ambas partes
2. **Facturas electrónicas:** CFDI con sello digital vigente
3. **Entregables digitales:** Firma electrónica simple con trazabilidad
4. **Actas de aceptación:** Firma electrónica avanzada recomendada

### 3.3 Constancia de Conservación de Mensajes de Datos (CCMD)

La CCMD debe contener:
- Identificación del prestador de servicios de certificación
- Fecha y hora de emisión
- Hash del documento conservado
- Período de conservación garantizado
- Número de folio o identificador único

## 4. Documentos Críticos para Servicios Intangibles

### 4.1 Matriz de Documentos y Requisitos

| Documento | Formato | Conservación | Firma Requerida | Plazo |
|-----------|---------|--------------|-----------------|-------|
| Contrato de servicios | PDF/A | NOM-151 | FIEL ambas partes | {{PLAZO_CONTRATO}} años |
| Statement of Work | PDF/A | NOM-151 | Electrónica simple | {{PLAZO_SOW}} años |
| Facturas (CFDI) | XML + PDF | SAT | FIEL emisor | {{PLAZO_CFDI}} años |
| Entregables técnicos | Formato original | NOM-151 | Electrónica simple | {{PLAZO_ENTREGABLES}} años |
| Actas de aceptación | PDF/A | NOM-151 | Electrónica avanzada | {{PLAZO_ACTAS}} años |
| Evidencia de reuniones | PDF/A | Interno | N/A | {{PLAZO_MINUTAS}} años |
| Correspondencia | EML/PDF | NOM-151 | Según contenido | {{PLAZO_CORRESPONDENCIA}} años |

### 4.2 Expediente Digital de Materialidad

Para cada servicio contratado, mantener expediente con:

```
/EXPEDIENTE_{{ID_PROYECTO}}/
├── 01_CONTRATACION/
│   ├── contrato_firmado.pdf
│   ├── sow_aprobado.pdf
│   └── ordenes_compra/
├── 02_EJECUCION/
│   ├── entregables/
│   ├── minutas_reunion/
│   └── comunicaciones/
├── 03_ACEPTACION/
│   ├── actas_aceptacion/
│   └── evaluaciones_calidad/
├── 04_FACTURACION/
│   ├── cfdis/
│   └── comprobantes_pago/
└── 05_CONSTANCIAS/
    ├── ccmd/
    └── evidencia_digitalizada/
```

## 5. Proceso de Digitalización Certificada

### 5.1 Requisitos para Digitalización

Cuando se digitalicen documentos físicos:

1. **Resolución mínima:** 200 DPI para texto, 300 DPI para imágenes
2. **Formato:** PDF/A-1 o PDF/A-2
3. **Color:** Escala de grises mínimo, color cuando sea relevante
4. **OCR:** Aplicar reconocimiento óptico de caracteres
5. **Metadatos:** Incluir fecha, responsable, origen

### 5.2 Procedimiento de Digitalización

| Paso | Actividad | Responsable | Evidencia |
|------|-----------|-------------|-----------|
| 1 | Preparar documentos físicos | {{ROL_PREPARACION}} | Lista de verificación |
| 2 | Escanear conforme especificaciones | {{ROL_DIGITALIZACION}} | Log de escaneo |
| 3 | Verificar calidad de imagen | {{ROL_VERIFICACION}} | Checklist calidad |
| 4 | Aplicar OCR y metadatos | {{ROL_PROCESAMIENTO}} | Archivo procesado |
| 5 | Generar CCMD | Prestador certificado | Constancia NOM-151 |
| 6 | Almacenar en repositorio | {{ROL_ALMACENAMIENTO}} | Confirmación sistema |

## 6. Trazabilidad de Documentos

### 6.1 Elementos de Trazabilidad

Cada documento debe mantener registro de:

- **Origen:** Quién lo creó y cuándo
- **Modificaciones:** Historial de cambios con timestamp
- **Accesos:** Log de consultas y descargas
- **Ubicación:** Ruta de almacenamiento actual
- **Estado:** Vigente, archivado, destruido

### 6.2 Cadena de Custodia Digital

```
[Creación] → [Revisión] → [Aprobación] → [Conservación] → [Consulta/Uso]
     ↓            ↓            ↓              ↓               ↓
  Timestamp   Comentarios   Firma Elec.    CCMD          Log acceso
```

## 7. Gestión de Metadatos

### 7.1 Metadatos Obligatorios

| Campo | Descripción | Ejemplo |
|-------|-------------|---------|
| titulo | Nombre descriptivo del documento | "Contrato Consultoría SAP 2026" |
| fecha_creacion | Fecha ISO 8601 | 2026-01-15T10:30:00-06:00 |
| autor | Responsable de creación | {{AUTOR_DOCUMENTO}} |
| tipo_documento | Clasificación interna | contrato, entregable, factura |
| proyecto_id | Identificador del proyecto | PROJ-{{ID_PROYECTO}} |
| version | Número de versión | 1.0, 1.1, 2.0 |
| estado | Estado del documento | borrador, vigente, archivado |
| clasificacion | Nivel de confidencialidad | publico, interno, confidencial |

### 7.2 Metadatos Fiscales

| Campo | Descripción | Obligatorio |
|-------|-------------|-------------|
| rfc_emisor | RFC del prestador | Sí |
| rfc_receptor | RFC del cliente | Sí |
| monto_operacion | Valor en MXN | Sí |
| ejercicio_fiscal | Año fiscal aplicable | Sí |
| tipologia_servicio | Clasificación del servicio | Sí |

## 8. Validación y Auditoría

### 8.1 Checklist de Cumplimiento NOM-151

- [ ] Documento en formato PDF/A
- [ ] Hash de integridad generado
- [ ] Firma electrónica válida (cuando aplique)
- [ ] Metadatos completos
- [ ] CCMD emitida por prestador autorizado
- [ ] Almacenado en repositorio seguro
- [ ] Respaldo actualizado
- [ ] Registro en bitácora de trazabilidad

### 8.2 Auditoría Periódica

| Actividad | Frecuencia | Responsable |
|-----------|------------|-------------|
| Verificación de integridad | {{FRECUENCIA_INTEGRIDAD}} | {{ROL_AUDITORIA}} |
| Validación de firmas | {{FRECUENCIA_FIRMAS}} | {{ROL_AUDITORIA}} |
| Prueba de recuperación | {{FRECUENCIA_RECUPERACION}} | {{ROL_TI}} |
| Revisión de metadatos | {{FRECUENCIA_METADATOS}} | {{ROL_DOCUMENTAL}} |

## 9. Proveedores de Servicios de Certificación

### 9.1 Prestadores Autorizados

Para la emisión de CCMD, utilizar prestadores autorizados por la Secretaría de Economía:

| Prestador | Servicios | Contacto |
|-----------|-----------|----------|
| {{PRESTADOR_1}} | CCMD, Firma, Almacenamiento | {{CONTACTO_PRESTADOR_1}} |
| {{PRESTADOR_2}} | CCMD, Digitalización | {{CONTACTO_PRESTADOR_2}} |

### 9.2 Criterios de Selección

1. Autorización vigente de la Secretaría de Economía
2. Certificación ISO 27001
3. Experiencia en sector empresarial
4. Capacidad de almacenamiento por período requerido
5. SLA de disponibilidad mínimo 99.5%

## 10. Procedimiento ante Requerimiento de Autoridad

En caso de requerimiento de información por parte del SAT u otra autoridad:

1. **Identificar documentos solicitados** en expediente digital
2. **Verificar integridad** mediante validación de hash
3. **Obtener CCMD vigente** de documentos electrónicos
4. **Preparar copia certificada** en formato requerido
5. **Documentar entrega** con acuse de recibo
6. **Mantener evidencia** del proceso de atención

---

*Este documento es una guía de referencia. Consulte con especialistas legales para casos específicos.*
