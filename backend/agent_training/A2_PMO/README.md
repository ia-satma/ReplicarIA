# A2_PMO - Carlos Mendoza (PMO)

## Área de Expertise
- Project Management Office
- Orquestación del proceso multi-agente
- Consolidación de validaciones
- Generación de Purchase Orders y Defense Files

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
   - Usa el endpoint `POST /api/knowledge/agent/A2_PMO/ingest` para procesar los archivos

2. **Vía API:**
   - Usa el endpoint `POST /api/knowledge/agent/A2_PMO/add` con:
   ```json
   {
     "content": "Contenido del documento...",
     "title": "Título del documento"
   }
   ```

## Temas Recomendados para Documentos
- Metodología de gestión de proyectos
- Procesos de consolidación de reportes
- Plantillas de Purchase Order
- Guías de coordinación inter-agentes
- Políticas de documentación
