# A5_FINANZAS - Roberto Torres (Finanzas)

## Área de Expertise
- Director Financiero
- Políticas Presupuestales
- Análisis financiero de proyectos
- Cálculo de ROI
- Viabilidad financiera
- Benchmarks del sector

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
   - Usa el endpoint `POST /api/knowledge/agent/A5_FINANZAS/ingest` para procesar los archivos

2. **Vía API:**
   - Usa el endpoint `POST /api/knowledge/agent/A5_FINANZAS/add` con:
   ```json
   {
     "content": "Contenido del documento...",
     "title": "Título del documento"
   }
   ```

## Temas Recomendados para Documentos
- Políticas presupuestales vigentes
- Criterios de evaluación de inversiones
- Metodología de cálculo de ROI
- Análisis de riesgos financieros
- Benchmarks de la industria
