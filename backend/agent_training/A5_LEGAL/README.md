# A5_LEGAL - Equipo Legal

## Área de Expertise
- Elaboración de contratos
- Revisión legal de Purchase Orders
- Documentación para Defense File
- Cumplimiento normativo
- Análisis de riesgos legales

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
   - Usa el endpoint `POST /api/knowledge/agent/A5_LEGAL/ingest` para procesar los archivos

2. **Vía API:**
   - Usa el endpoint `POST /api/knowledge/agent/A5_LEGAL/add` con:
   ```json
   {
     "content": "Contenido del documento...",
     "title": "Título del documento"
   }
   ```

## Temas Recomendados para Documentos
- Modelos de contratos
- Cláusulas legales estándar
- Regulaciones aplicables
- Criterios de revisión legal
- Políticas de compliance
