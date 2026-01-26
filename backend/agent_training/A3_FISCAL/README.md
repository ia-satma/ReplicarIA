# A3_FISCAL - Laura Sánchez (Fiscal)

## Área de Expertise
- Especialista Fiscal
- Cumplimiento fiscal mexicano (CFF, LISR, RLSR)
- Razón de Negocios (Art. 5-A CFF)
- Estricta Indispensabilidad (Art. 27 LISR)
- Materialidad del Servicio (Art. 69-B CFF)
- Análisis de riesgos fiscales

## Estructura de Carpetas

### `/knowledge/`
Documentos de texto que serán procesados e incorporados al sistema RAG para consultas del agente.
- Archivos soportados: `.txt`, `.md`
- Los documentos serán divididos en chunks y almacenados como embeddings

### `/templates/`
Plantillas de documentos que el agente puede usar como referencia para generar reportes.

## Cómo Agregar Conocimiento

1. **Vía Archivos Locales:**
   - Coloca archivos `.txt` o `.md` en la carpeta `/knowledge/`
   - Usa el endpoint `POST /api/knowledge/agent/A3_FISCAL/ingest` para procesar los archivos

2. **Vía API:**
   - Usa el endpoint `POST /api/knowledge/agent/A3_FISCAL/add` con:
   ```json
   {
     "content": "Contenido del documento...",
     "title": "Título del documento"
   }
   ```

## Temas Recomendados para Documentos
- Guías de cumplimiento fiscal
- Normativa fiscal mexicana actualizada
- Casos de auditoría SAT
- Criterios de materialidad
- Políticas de documentación fiscal
