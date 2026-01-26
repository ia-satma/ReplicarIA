import json
import logging
import os
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

# OpenAI provider
try:
    from services.openai_provider import openai_client, chat_completion_sync, is_configured
    OPENAI_AVAILABLE = is_configured()
except ImportError:
    OPENAI_AVAILABLE = False
    openai_client = None


class WebSearchService:
    """Servicio de búsqueda web para completar datos de empresas"""

    def __init__(self):
        if OPENAI_AVAILABLE:
            self.client = openai_client
            logger.info("WebSearchService initialized with OpenAI")
        else:
            logger.warning("OpenAI not configured for web search")
            self.client = None

        self.model = "gpt-4o"
    
    async def buscar_datos_empresa(
        self,
        nombre: Optional[str] = None,
        rfc: Optional[str] = None,
        campos_faltantes: List[str] = None
    ) -> Dict[str, Any]:
        """
        Busca datos faltantes de una empresa en fuentes públicas
        
        Nota: Sin acceso a web search real, simula respuesta basada en conocimiento
        """
        if not self.client:
            return {
                "datos_encontrados": {},
                "fuentes_nuevas": [],
                "aun_faltantes": campos_faltantes or []
            }
        
        if not nombre and not rfc:
            return {
                "datos_encontrados": {},
                "fuentes_nuevas": [],
                "aun_faltantes": campos_faltantes or []
            }
        
        campos = campos_faltantes or ["direccion", "telefono", "email", "sitio_web", "giro"]
        
        prompt = f"""Eres un asistente que ayuda a completar información de empresas mexicanas.

Tengo una empresa con estos datos conocidos:
- Nombre/Razón Social: {nombre or 'No proporcionado'}
- RFC: {rfc or 'No proporcionado'}

Necesito encontrar estos campos faltantes: {', '.join(campos)}

IMPORTANTE:
1. NO inventes datos
2. Si no puedes proporcionar un dato con alta confianza, no lo incluyas
3. Para empresas conocidas, puedes inferir el dominio del sitio web del nombre
4. El formato de teléfonos mexicanos es +52 seguido de 10 dígitos

Si el RFC sigue el patrón correcto y tienes información sobre la empresa, proporciona lo que sepas.
Si no conoces la empresa o no tienes información, responde con campos vacíos.

Responde SOLO con JSON:
{{
  "datos_encontrados": {{
    "direccion": "Dirección si la conoces o null",
    "telefono": "Teléfono si lo conoces o null",
    "email": "Email si lo conoces o null",
    "sitio_web": "URL si la conoces o null",
    "giro": "Actividad si la conoces o null"
  }},
  "fuentes_nuevas": [
    {{"campo": "sitio_web", "fuente": "inferencia", "confianza": 0.6}}
  ],
  "notas": "Observaciones sobre los datos"
}}"""

        try:
            texto = chat_completion_sync(
                messages=[{"role": "user", "content": prompt}],
                model=self.model,
                max_tokens=1500
            )
            
            if "```json" in texto:
                texto = texto.split("```json")[1].split("```")[0]
            elif "```" in texto:
                texto = texto.split("```")[1].split("```")[0]
            
            resultado = json.loads(texto.strip())
            
            datos_encontrados = {}
            fuentes_nuevas = []
            
            for campo, valor in resultado.get("datos_encontrados", {}).items():
                if valor and valor != "null" and valor.strip():
                    datos_encontrados[campo] = valor
                    fuente_info = next(
                        (f for f in resultado.get("fuentes_nuevas", []) if f.get("campo") == campo),
                        {"campo": campo, "fuente": "web", "confianza": 0.7}
                    )
                    fuentes_nuevas.append(fuente_info)
            
            aun_faltantes = [c for c in campos if c not in datos_encontrados]
            
            return {
                "datos_encontrados": datos_encontrados,
                "fuentes_nuevas": fuentes_nuevas,
                "aun_faltantes": aun_faltantes,
                "notas": resultado.get("notas", "")
            }
            
        except Exception as e:
            logger.error(f"Error in web search: {e}")
            return {
                "datos_encontrados": {},
                "fuentes_nuevas": [],
                "aun_faltantes": campos_faltantes or []
            }
    
    async def investigar_empresa(
        self,
        nombre: Optional[str] = None,
        rfc: Optional[str] = None,
        campos_buscar: List[str] = None
    ) -> Dict[str, Any]:
        """
        Investigación más profunda de una empresa
        """
        return await self.buscar_datos_empresa(nombre, rfc, campos_buscar)


web_search_service = WebSearchService()
