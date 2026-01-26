import os
import base64
import logging
from datetime import datetime
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# OpenAI provider
try:
    from services.openai_provider import openai_client, is_configured
    OPENAI_AVAILABLE = is_configured()
except ImportError:
    OPENAI_AVAILABLE = False
    openai_client = None
    logger.warning("OpenAI provider not available for ProveedorOCRService")


class ProveedorOCRService:
    """
    Servicio OCR para documentos de proveedores usando OpenAI GPT-4o Vision.
    """
    def __init__(self):
        if OPENAI_AVAILABLE:
            self.client = openai_client
            self.available = True
            logger.info("OCR de proveedores usando OpenAI GPT-4o Vision")
        else:
            self.client = None
            self.available = False
            logger.warning("OpenAI API no disponible para OCR de proveedores")

    def _get_media_type(self, media_type: str) -> str:
        valid_types = ["image/jpeg", "image/png", "image/webp", "image/gif", "application/pdf"]
        if media_type in valid_types:
            return media_type
        if media_type.startswith("image/"):
            return "image/jpeg"
        return "application/pdf"

    async def extraer_constancia_fiscal(self, archivo_base64: str, media_type: str) -> Dict[str, Any]:
        if not self.available:
            return {"exito": False, "error": "Servicio OCR no disponible"}

        prompt = """Analiza esta Constancia de Situación Fiscal del SAT de México.
Extrae los siguientes datos en formato JSON:

{
  "rfc": "RFC del contribuyente",
  "razon_social": "Nombre o razón social completa",
  "regimen_fiscal": "Régimen fiscal (ej: Régimen General de Ley Personas Morales)",
  "clave_regimen_fiscal": "Clave numérica del régimen (ej: 601)",
  "fecha_emision": "Fecha de emisión en formato YYYY-MM-DD",
  "estatus_rfc": "activo, suspendido, cancelado o no_localizado",
  "fecha_inicio_operaciones": "Fecha de inicio de operaciones en formato YYYY-MM-DD",
  "domicilio": {
    "calle": "Nombre de la calle",
    "numero_exterior": "Número exterior",
    "numero_interior": "Número interior (si aplica)",
    "colonia": "Colonia",
    "codigo_postal": "CP de 5 dígitos",
    "municipio": "Municipio o alcaldía",
    "estado": "Estado"
  },
  "obligaciones_fiscales": ["Lista de obligaciones fiscales registradas"]
}

Si no puedes identificar algún campo, déjalo como null.
Responde SOLO con el JSON, sin explicaciones adicionales."""

        try:
            # OpenAI Vision API format
            response = self.client.chat.completions.create(
                model="gpt-4o",
                max_tokens=2000,
                messages=[{
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{self._get_media_type(media_type)};base64,{archivo_base64}"
                            }
                        },
                        {"type": "text", "text": prompt}
                    ]
                }]
            )

            content = response.choices[0].message.content
            import json
            
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            datos = json.loads(content.strip())
            
            campos_encontrados = [k for k, v in datos.items() if v is not None]
            
            return {
                "exito": True,
                "datos_extraidos": datos,
                "nivel_confianza": "alto" if len(campos_encontrados) >= 6 else ("medio" if len(campos_encontrados) >= 3 else "bajo"),
                "campos_extraidos": campos_encontrados
            }

        except Exception as e:
            logger.error(f"Error en OCR de constancia fiscal: {str(e)}")
            return {"exito": False, "error": str(e)}

    async def extraer_acta_constitutiva(self, archivo_base64: str, media_type: str) -> Dict[str, Any]:
        if not self.available:
            return {"exito": False, "error": "Servicio OCR no disponible"}

        prompt = """Analiza esta Acta Constitutiva de una sociedad mexicana.
Extrae los siguientes datos en formato JSON:

{
  "razon_social": "Denominación o razón social de la sociedad",
  "tipo_sociedad": "Tipo de sociedad (SA, SAPI, SC, SRL, etc.)",
  "fecha_escritura": "Fecha de la escritura en formato YYYY-MM-DD",
  "notario": "Nombre del notario público",
  "numero_notaria": "Número de notaría",
  "entidad_notaria": "Estado donde se ubica la notaría",
  "numero_escritura": "Número de escritura pública",
  "objeto_social": "Resumen del objeto social (máx 500 caracteres)",
  "capital_social": {
    "monto_suscrito": 0,
    "monto_pagado": 0,
    "moneda": "MXN"
  },
  "socios_principales": [
    {
      "nombre": "Nombre del socio",
      "porcentaje_participacion": 0
    }
  ],
  "administrador_unico": "Nombre del administrador único o presidente del consejo",
  "duracion_sociedad": "Duración de la sociedad (ej: 99 años, indefinida)",
  "folio_mercantil": "Número de folio mercantil (si aparece)"
}

Si no puedes identificar algún campo, déjalo como null.
Responde SOLO con el JSON, sin explicaciones adicionales."""

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-5",
                max_tokens=3000,
                messages=[{
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": self._get_media_type(media_type),
                                "data": archivo_base64
                            }
                        },
                        {"type": "text", "text": prompt}
                    ]
                }]
            )

            content = response.content[0].text
            import json
            
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            datos = json.loads(content.strip())
            campos_encontrados = [k for k, v in datos.items() if v is not None]
            
            return {
                "exito": True,
                "datos_extraidos": datos,
                "nivel_confianza": "alto" if len(campos_encontrados) >= 7 else ("medio" if len(campos_encontrados) >= 4 else "bajo"),
                "campos_extraidos": campos_encontrados
            }

        except Exception as e:
            logger.error(f"Error en OCR de acta constitutiva: {str(e)}")
            return {"exito": False, "error": str(e)}

    async def extraer_opinion_cumplimiento(self, archivo_base64: str, media_type: str) -> Dict[str, Any]:
        if not self.available:
            return {"exito": False, "error": "Servicio OCR no disponible"}

        prompt = """Analiza esta Opinión de Cumplimiento (32-D) del SAT de México.
Extrae los siguientes datos en formato JSON:

{
  "rfc": "RFC del contribuyente",
  "razon_social": "Nombre o razón social",
  "tipo_opinion": "positiva, negativa, no_localizado o no_presentada",
  "fecha_emision": "Fecha de emisión en formato YYYY-MM-DD",
  "vigencia_hasta": "Fecha de vigencia (generalmente 30 días después) en formato YYYY-MM-DD",
  "numero_operacion": "Número de operación o folio",
  "cadena_original": "Primeros 50 caracteres de la cadena original (si es visible)"
}

Si no puedes identificar algún campo, déjalo como null.
Responde SOLO con el JSON, sin explicaciones adicionales."""

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-5",
                max_tokens=1500,
                messages=[{
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": self._get_media_type(media_type),
                                "data": archivo_base64
                            }
                        },
                        {"type": "text", "text": prompt}
                    ]
                }]
            )

            content = response.content[0].text
            import json
            
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            datos = json.loads(content.strip())
            campos_encontrados = [k for k, v in datos.items() if v is not None]
            
            return {
                "exito": True,
                "datos_extraidos": datos,
                "nivel_confianza": "alto" if len(campos_encontrados) >= 5 else ("medio" if len(campos_encontrados) >= 3 else "bajo"),
                "campos_extraidos": campos_encontrados
            }

        except Exception as e:
            logger.error(f"Error en OCR de opinión de cumplimiento: {str(e)}")
            return {"exito": False, "error": str(e)}

    async def extraer_repse(self, archivo_base64: str, media_type: str) -> Dict[str, Any]:
        if not self.available:
            return {"exito": False, "error": "Servicio OCR no disponible"}

        prompt = """Analiza este documento de REPSE (Registro de Prestadoras de Servicios Especializados) de la STPS de México.
Extrae los siguientes datos en formato JSON:

{
  "rfc": "RFC de la empresa registrada",
  "razon_social": "Nombre o razón social",
  "numero_registro": "Número de registro REPSE",
  "fecha_registro": "Fecha de registro en formato YYYY-MM-DD",
  "fecha_vigencia": "Fecha de vigencia en formato YYYY-MM-DD",
  "objeto_autorizado": "Descripción del objeto social autorizado",
  "actividades_autorizadas": ["Lista de actividades autorizadas para subcontratación"],
  "domicilio": "Domicilio registrado (texto completo)",
  "estatus": "Vigente, No vigente, Cancelado"
}

Si no puedes identificar algún campo, déjalo como null.
Responde SOLO con el JSON, sin explicaciones adicionales."""

        try:
            # OpenAI Vision API format
            response = self.client.chat.completions.create(
                model="gpt-4o",
                max_tokens=2000,
                messages=[{
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{self._get_media_type(media_type)};base64,{archivo_base64}"
                            }
                        },
                        {"type": "text", "text": prompt}
                    ]
                }]
            )

            content = response.choices[0].message.content
            import json
            
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            datos = json.loads(content.strip())
            campos_encontrados = [k for k, v in datos.items() if v is not None]
            
            return {
                "exito": True,
                "datos_extraidos": datos,
                "nivel_confianza": "alto" if len(campos_encontrados) >= 6 else ("medio" if len(campos_encontrados) >= 3 else "bajo"),
                "campos_extraidos": campos_encontrados
            }

        except Exception as e:
            logger.error(f"Error en OCR de REPSE: {str(e)}")
            return {"exito": False, "error": str(e)}

    async def clasificar_documento(self, archivo_base64: str, media_type: str) -> Dict[str, Any]:
        if not self.available:
            return {"exito": False, "error": "Servicio OCR no disponible"}

        prompt = """Analiza este documento y determina qué tipo de documento fiscal/legal mexicano es.

Responde en formato JSON:
{
  "tipo_documento": "uno de: constancia_situacion_fiscal, acta_constitutiva, opinion_cumplimiento, repse, contrato, factura_cfdi, identificacion, poder_notarial, otro",
  "confianza": "alta, media o baja",
  "descripcion": "Breve descripción de lo que contiene el documento"
}

Responde SOLO con el JSON."""

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-5",
                max_tokens=500,
                messages=[{
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": self._get_media_type(media_type),
                                "data": archivo_base64
                            }
                        },
                        {"type": "text", "text": prompt}
                    ]
                }]
            )

            content = response.content[0].text
            import json
            
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            datos = json.loads(content.strip())
            
            return {
                "exito": True,
                "clasificacion": datos
            }

        except Exception as e:
            logger.error(f"Error clasificando documento: {str(e)}")
            return {"exito": False, "error": str(e)}
