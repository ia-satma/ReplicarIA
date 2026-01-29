import json
import logging
import os
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

# AI Provider configuration - uses lazy initialization
AI_PROVIDER = None
chat_fn = None
_provider_initialized = False


def _init_ai_provider():
    """
    Lazy initialization of AI provider.
    Called on first use to ensure env vars are loaded.
    """
    global AI_PROVIDER, chat_fn, _provider_initialized

    if _provider_initialized:
        return

    _provider_initialized = True
    logger.info("DocumentAnalyzer: Initializing AI provider...")

    # Log environment state for debugging
    anthropic_key = os.environ.get('ANTHROPIC_API_KEY', '')
    openai_key = os.environ.get('OPENAI_API_KEY', '')
    logger.info(f"  ANTHROPIC_API_KEY set: {bool(anthropic_key)}")
    logger.info(f"  OPENAI_API_KEY set: {bool(openai_key)}")

    # Try Anthropic first
    try:
        from services.anthropic_provider import chat_completion_sync as anthropic_chat, is_configured as anthropic_configured
        if anthropic_configured():
            AI_PROVIDER = "anthropic"
            chat_fn = anthropic_chat
            logger.info("DocumentAnalyzer: Using Anthropic Claude")
            return
        else:
            logger.info("DocumentAnalyzer: Anthropic not configured, trying OpenAI...")
    except ImportError as e:
        logger.info(f"DocumentAnalyzer: Anthropic import failed: {e}")

    # Fallback to OpenAI
    try:
        from services.openai_provider import chat_completion_sync as openai_chat, is_configured as openai_configured
        if openai_configured():
            AI_PROVIDER = "openai"
            chat_fn = openai_chat
            logger.info("DocumentAnalyzer: Using OpenAI GPT")
            return
        else:
            logger.warning("DocumentAnalyzer: OpenAI not configured (key may be missing or invalid)")
    except ImportError as e:
        logger.warning(f"DocumentAnalyzer: OpenAI import failed: {e}")

    logger.error("DocumentAnalyzer: NO AI PROVIDER AVAILABLE - document analysis will fail!")
    logger.error("  Please configure ANTHROPIC_API_KEY or OPENAI_API_KEY environment variable")


# Initialize on module load (but provider uses lazy init internally)
_init_ai_provider()


def reinit_ai_provider():
    """Force re-initialization of AI provider (useful if env vars change)"""
    global _provider_initialized
    _provider_initialized = False
    _init_ai_provider()


class DocumentAnalyzerService:
    """Servicio de análisis de documentos con IA para extracción de datos"""

    def __init__(self):
        # Ensure provider is initialized
        if not _provider_initialized:
            _init_ai_provider()

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
            logger.info(f"DocumentAnalyzer: Calling AI ({self.provider}) with {len(documentos)} documents")
            texto_respuesta = chat_fn(
                messages=[{"role": "user", "content": prompt}],
                model=self.model,
                max_tokens=2500
            )

            # Check if AI returned an error response
            if texto_respuesta.startswith('{"error"'):
                try:
                    error_data = json.loads(texto_respuesta)
                    error_msg = error_data.get("error", "Error desconocido de IA")
                    logger.error(f"AI provider returned error: {error_msg}")
                    return {
                        "error": f"Error del proveedor de IA: {error_msg}",
                        "datosFaltantes": ["nombre", "rfc", "direccion", "email"],
                        "datosCompletos": False,
                        "fuentes": [],
                        "tipo": tipo_entidad
                    }
                except json.JSONDecodeError:
                    pass  # Not a JSON error, continue processing

            logger.info(f"DocumentAnalyzer: Received {len(texto_respuesta)} chars from AI")

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
