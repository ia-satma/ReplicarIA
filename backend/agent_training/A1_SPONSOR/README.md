# A1_SPONSOR - María Rodríguez (Estrategia)

## Área de Expertise
- Dirección Estratégica
- Visión y Pilares Estratégicos 2026-2030
- Planeación Estratégica con OKRs
- Análisis de panorama de industria

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
   - Usa el endpoint `POST /api/knowledge/agent/A1_SPONSOR/ingest` para procesar los archivos

2. **Vía API:**
   - Usa el endpoint `POST /api/knowledge/agent/A1_SPONSOR/add` con:
   ```json
   {
     "content": "Contenido del documento...",
     "title": "Título del documento"
   }
   ```

## Temas Recomendados para Documentos
- Misión y visión corporativa
- Objetivos estratégicos anuales
- Análisis FODA del grupo
- Políticas de gobierno corporativo
- Lineamientos para aprobación de proyectos
