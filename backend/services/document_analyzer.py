import json
import logging
import os
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

# Try Anthropic first, then OpenAI as fallback
AI_PROVIDER = None
chat_fn = None

try:
    from services.anthropic_provider import chat_completion_sync as anthropic_chat, is_configured as anthropic_configured
    if anthropic_configured():
        AI_PROVIDER = "anthropic"
        chat_fn = anthropic_chat
        logger.info("DocumentAnalyzer using Anthropic Claude")
except ImportError:
    pass

if not AI_PROVIDER:
    try:
        from services.openai_provider import chat_completion_sync as openai_chat, is_configured as openai_configured
        if openai_configured():
            AI_PROVIDER = "openai"
            chat_fn = openai_chat
            logger.info("DocumentAnalyzer using OpenAI")
    except ImportError:
        pass

if not AI_PROVIDER:
    logger.warning("No AI provider available for DocumentAnalyzer")


class DocumentAnalyzerService:
    """Servicio de análisis de documentos con IA para extracción de datos"""

    def __init__(self):
        self.provider = AI_PROVIDER
        self.model = "claude-sonnet-4-20250514" if AI_PROVIDER == "anthropic" else "gpt-4o"

        if not self.provider:
            logger.warning("No AI provider configured for DocumentAnalyzer")

    async def analizar_documentos(
        self,
        documentos: List[Dict[str, Any]],
        tipo_entidad: str = "cliente"
    ) -> Dict[str, Any]:
        """
        Analiza múltiples documentos y extrae datos de cliente/proveedor
        """
        if not self.provider or not chat_fn:
            return {
                "error": "Servicio de IA no configurado. Configure ANTHROPIC_API_KEY o OPENAI_API_KEY.",
                "datosFaltantes": ["nombre", "rfc", "direccion", "email"],
                "datosCompletos": False,
                "fuentes": []
            }

        textos = "\n\n---DOCUMENTO---\n".join([
            f"Archivo: {d['nombre']}\n{d['texto'][:8000]}"
            for d in documentos
        ])

        prompt = f"""Analiza los siguientes documentos de un {tipo_entidad} mexicano y extrae todos los datos que puedas encontrar.

DOCUMENTOS:
{textos}

Extrae los siguientes datos si están disponibles:
- nombre (nombre comercial de la empresa)
- rfc (RFC mexicano, formato: 3-4 letras + 6 números fecha + 3 caracteres homoclave, ejemplo: ABC123456XYZ)
- razon_social (razón social completa incluyendo tipo de sociedad)
- direccion (dirección fiscal completa: calle, número, colonia, ciudad, CP)
- telefono (teléfono de contacto con formato +52 o 10 dígitos)
- email (correo electrónico corporativo)
- giro (actividad económica o giro del negocio)
- regimen_fiscal (régimen fiscal si se menciona)
- sitio_web (página web si se menciona)
- representante_legal (nombre del representante legal si aparece)
- capital_social (capital social si se menciona)

INSTRUCCIONES CRÍTICAS:
1. Solo extrae datos que estén CLARAMENTE en los documentos
2. Si un dato no está claro o es ambiguo, no lo incluyas
3. El RFC mexicano tiene formato específico: 3-4 letras + 6 dígitos (fecha) + 3 caracteres (homoclave)
4. Para la razón social, incluye el tipo de sociedad (S.A. de C.V., S.C., etc.)
5. Indica la confianza (0-1) basada en qué tan claro está el dato

Responde ÚNICAMENTE con un JSON válido con esta estructura exacta:
{{
  "nombre": "Nombre comercial o null",
  "rfc": "RFC o null",
  "razon_social": "Razón social o null",
  "direccion": "Dirección o null",
  "telefono": "Teléfono o null",
  "email": "Email o null",
  "giro": "Giro o null",
  "regimen_fiscal": "Régimen o null",
  "sitio_web": "URL o null",
  "representante_legal": "Nombre o null",
  "capital_social": "Cantidad o null",
  "fuentes": [
    {{"campo": "nombre", "fuente": "documento", "confianza": 0.95, "archivo": "nombre_archivo.pdf"}},
    {{"campo": "rfc", "fuente": "documento", "confianza": 0.99, "archivo": "csf.pdf"}}
  ],
  "observaciones": "Notas adicionales sobre la calidad de los datos"
}}"""

        try:
            texto_respuesta = chat_fn(
                messages=[{"role": "user", "content": prompt}],
                model=self.model,
                max_tokens=2500
            )

            if "```json" in texto_respuesta:
                texto_respuesta = texto_respuesta.split("```json")[1].split("```")[0]
            elif "```" in texto_respuesta:
                texto_respuesta = texto_respuesta.split("```")[1].split("```")[0]

            datos = json.loads(texto_respuesta.strip())

            for key in datos:
                if datos[key] == "null" or datos[key] == "":
                    datos[key] = None

            campos_requeridos = ["nombre", "rfc", "email"]
            campos_opcionales = ["direccion", "telefono", "giro", "razon_social"]

            datos_faltantes = []
            for campo in campos_requeridos:
                if not datos.get(campo):
                    datos_faltantes.append(campo)
            for campo in campos_opcionales:
                if not datos.get(campo):
                    datos_faltantes.append(campo)

            datos["datosFaltantes"] = datos_faltantes
            datos["datosCompletos"] = len([c for c in campos_requeridos if not datos.get(c)]) == 0
            datos["tipo"] = tipo_entidad

            return datos

        except json.JSONDecodeError as e:
            logger.error(f"Error parsing AI response: {e}")
            return {
                "error": "Error al procesar respuesta de IA",
                "datosFaltantes": ["nombre", "rfc", "direccion", "email"],
                "datosCompletos": False,
                "fuentes": [],
                "tipo": tipo_entidad
            }
        except Exception as e:
            logger.error(f"Error analyzing documents: {e}")
            return {
                "error": str(e),
                "datosFaltantes": ["nombre", "rfc", "direccion", "email"],
                "datosCompletos": False,
                "fuentes": [],
                "tipo": tipo_entidad
            }


document_analyzer = DocumentAnalyzerService()
