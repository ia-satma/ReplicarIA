"""
Deep Research Engine - Servicio de Auto-completado Inteligente de Formularios
Investiga automáticamente datos empresariales a partir de inputs mínimos.
Usa OpenAI GPT-4o + Web Scraping para máxima efectividad.
"""
import os
import re
import json
import logging
from typing import Dict, Any, List, Optional, Tuple, cast
from urllib.parse import urljoin, urlparse
from datetime import datetime

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# AI Provider initialization - lazy loading
AI_PROVIDER = None
ai_client = None
chat_fn = None
_provider_initialized = False


def _init_ai_provider():
    """Lazy initialization of AI provider for DeepResearchService"""
    global AI_PROVIDER, ai_client, chat_fn, _provider_initialized

    if _provider_initialized:
        return

    _provider_initialized = True
    logger.info("DeepResearchService: Initializing AI provider...")

    # Try Anthropic first
    try:
        from services.anthropic_provider import chat_completion_sync as anthropic_chat, is_configured as anthropic_configured
        if anthropic_configured():
            AI_PROVIDER = "anthropic"
            chat_fn = anthropic_chat
            logger.info("DeepResearchService: Using Anthropic Claude")
            return
    except ImportError as e:
        logger.info(f"DeepResearchService: Anthropic not available: {e}")

    # Fallback to OpenAI
    try:
        from services.openai_provider import chat_completion_sync, is_configured
        if is_configured():
            AI_PROVIDER = "openai"
            chat_fn = chat_completion_sync
            logger.info("DeepResearchService: Using OpenAI GPT")
            return
    except ImportError as e:
        logger.info(f"DeepResearchService: OpenAI not available: {e}")

    logger.warning("DeepResearchService: No AI provider available - research features will be limited")


# Initialize on module load
_init_ai_provider()


class DeepResearchService:
    """
    Servicio de investigación profunda para auto-completado de formularios.
    Orquesta múltiples fuentes de datos: web scraping, análisis de documentos,
    validación de RFC y verificación con IA.
    """

    def __init__(self):
        # Ensure provider is initialized
        if not _provider_initialized:
            _init_ai_provider()

        self.provider = AI_PROVIDER
        self.chat_fn = chat_fn
        self.available = AI_PROVIDER is not None

        if self.available:
            logger.info(f"DeepResearchService inicializado con {AI_PROVIDER}")
        else:
            logger.warning("DeepResearchService: Ningún proveedor AI configurado")

        self.model = "claude-sonnet-4-20250514" if AI_PROVIDER == "anthropic" else "gpt-4o"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'es-MX,es;q=0.9,en;q=0.8',
        })
        self.request_timeout = 15
        
        self.RFC_TABLA_VERIFICADOR = "0123456789ABCDEFGHIJKLMN&OPQRSTUVWXYZ Ñ"
    
    async def investigar_empresa(
        self,
        sitio_web: Optional[str] = None,
        rfc: Optional[str] = None,
        nombre: Optional[str] = None,
        documento: Optional[str] = None,
        tipo_documento: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Método principal que orquesta toda la investigación de una empresa.
        
        Args:
            sitio_web: URL del sitio web de la empresa
            rfc: RFC de la empresa
            nombre: Nombre o razón social
            documento: Contenido de documento (texto extraído)
            tipo_documento: Tipo de documento (csf, acta_constitutiva, contrato, etc.)
        
        Returns:
            Dict con datos completos, confidence scores y campos que necesitan confirmación
        """
        logger.info(f"Iniciando investigación: sitio={sitio_web}, rfc={rfc}, nombre={nombre}")
        
        data: Dict[str, Any] = {}
        field_confidence: Dict[str, Dict[str, Any]] = {}
        sources: List[str] = []
        
        if rfc:
            rfc_validation = self.validar_rfc(rfc)
            if rfc_validation["valido"]:
                data["rfc"] = rfc.upper().strip()
                field_confidence["rfc"] = {
                    "confidence": 100 if rfc_validation["digito_verificador_valido"] else 85,
                    "source": "input validado"
                }
                data["tipo_persona"] = rfc_validation["tipo_persona"]
                field_confidence["tipo_persona"] = {"confidence": 100, "source": "RFC"}
        
        if nombre:
            data["nombre"] = nombre.strip()
            field_confidence["nombre"] = {"confidence": 70, "source": "input usuario"}
        
        if documento:
            doc_data = await self.analizar_documento(documento, tipo_documento)
            if doc_data.get("success"):
                sources.append(f"Documento: {tipo_documento or 'analizado'}")
                for campo, valor in doc_data.get("datos", {}).items():
                    if valor and (campo not in data or field_confidence.get(campo, {}).get("confidence", 0) < 90):
                        data[campo] = valor
                        field_confidence[campo] = {
                            "confidence": doc_data.get("confianza_campos", {}).get(campo, 85),
                            "source": f"documento ({tipo_documento or 'analizado'})"
                        }
        
        if sitio_web:
            web_data = await self.investigar_sitio_web(sitio_web)
            if web_data.get("success"):
                sources.append(sitio_web)
                if not data.get("sitio_web"):
                    data["sitio_web"] = sitio_web
                    field_confidence["sitio_web"] = {"confidence": 100, "source": "input usuario"}
                
                for campo, valor in web_data.get("datos", {}).items():
                    if valor:
                        current_confidence = field_confidence.get(campo, {}).get("confidence", 0)
                        new_confidence = web_data.get("confianza_campos", {}).get(campo, 70)
                        
                        if campo not in data or current_confidence < new_confidence:
                            data[campo] = valor
                            field_confidence[campo] = {
                                "confidence": new_confidence,
                                "source": "sitio web"
                            }
        
        if data and self.available:
            validation_result = await self.validar_con_claude(data)
            if validation_result.get("success"):
                for campo, info in validation_result.get("field_confidence", {}).items():
                    if campo in field_confidence:
                        current = field_confidence[campo]["confidence"]
                        adjusted = info.get("adjusted_confidence", current)
                        field_confidence[campo]["confidence"] = min(current, adjusted)
                        if info.get("warning"):
                            field_confidence[campo]["warning"] = info["warning"]
                
                if validation_result.get("datos_corregidos"):
                    for campo, valor in validation_result["datos_corregidos"].items():
                        if valor and valor != data.get(campo):
                            data[campo] = valor
                            field_confidence[campo]["source"] += " (corregido por IA)"
        
        needs_confirmation = []
        for campo, info in field_confidence.items():
            if info.get("confidence", 0) < 80 or info.get("warning"):
                needs_confirmation.append(campo)
        
        campos_importantes = ["rfc", "razon_social", "nombre", "email", "telefono", "direccion"]
        for campo in campos_importantes:
            if campo not in data:
                needs_confirmation.append(campo)
        
        needs_confirmation = list(set(needs_confirmation))
        
        total_confidence = 0
        campos_con_confianza = 0
        for info in field_confidence.values():
            total_confidence += info.get("confidence", 0)
            campos_con_confianza += 1
        
        overall_confidence = int(total_confidence / campos_con_confianza) if campos_con_confianza > 0 else 0
        
        completeness_bonus = min(20, len(data) * 2)
        overall_confidence = min(100, overall_confidence + completeness_bonus - len(needs_confirmation) * 3)
        overall_confidence = max(0, overall_confidence)
        
        return {
            "success": True,
            "confidence": overall_confidence,
            "data": data,
            "field_confidence": field_confidence,
            "needs_confirmation": needs_confirmation,
            "sources": sources,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def investigar_sitio_web(self, url: str) -> Dict[str, Any]:
        """
        Realiza scraping web y análisis con IA para extraer datos empresariales.
        Usa Firecrawl si está configurado, o fallback a requests+bs4.
        """
        if not url:
            return {"success": False, "error": "URL no proporcionada"}
        
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
            
        logger.info(f"Investigando sitio web: {url}")
        
        # 1. Intentar con Firecrawl primero
        firecrawl_key = os.getenv("FIRECRAWL_API_KEY")
        firecrawl_data = None
        
        if firecrawl_key and firecrawl_key.strip():
            try:
                from firecrawl import FirecrawlApp
                app = FirecrawlApp(api_key=firecrawl_key)
                
                logger.info("Usando Firecrawl para scraping...")
                scrape_result = app.scrape_url(url, params={'formats': ['markdown']})
                
                if scrape_result and 'markdown' in scrape_result:
                    firecrawl_data = scrape_result['markdown']
                    logger.info("Scraping con Firecrawl exitoso")
            except Exception as e:
                logger.warning(f"Error usando Firecrawl: {e}. Usando fallback.")
        
        # 2. Procesar datos de Firecrawl si existen
        if firecrawl_data:
            # Análisis con IA sobre el markdown limpio
            if self.available:
                ai_datos = await self._analizar_markdown_con_claude(firecrawl_data, url)
                if ai_datos.get("success"):
                    # Extraer también con regex sobre el markdown para doble verificación
                    regex_datos = self._extraer_datos_con_regex([{"text": firecrawl_data}])
                    merged_datos = self._merge_datos(ai_datos.get("datos", {}), regex_datos.get("datos", {}))
                    
                    return {
                        "success": True,
                        "datos": merged_datos,
                        "confianza_campos": ai_datos.get("confianza_campos", {})
                    }
        
        # 3. Fallback a método tradicional (Requests + BS4)
        logger.info("Usando método tradicional (Requests + BS4)")
        pages_to_check = [
            "", "/contacto", "/contact", "/nosotros", "/about", 
            "/about-us", "/quienes-somos", "/aviso-de-privacidad", 
            "/privacy", "/legal", "/terminos"
        ]
        
        all_content = []
        parsed_url = urlparse(url)
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
        
        for page in pages_to_check:
            try:
                page_url = urljoin(base_url, page)
                response = self.session.get(page_url, timeout=self.request_timeout, allow_redirects=True)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'lxml')
                    for script in soup(["script", "style", "nav", "header", "footer", "aside"]):
                        script.decompose()
                    
                    text = soup.get_text(separator=' ', strip=True)
                    text = re.sub(r'\s+', ' ', text)
                    if len(text) > 100:
                        all_content.append({
                            "url": page_url,
                            "text": text[:8000],
                            "title": soup.title.string if soup.title else ""
                        })
            except Exception:
                continue
        
        if not all_content:
            return {"success": False, "error": "No se pudo acceder al sitio web"}
            
        datos = self._extraer_datos_con_regex(all_content)
        
        if self.available:
            ai_datos = await self._analizar_contenido_con_claude(all_content, url)
            if ai_datos.get("success"):
                datos["datos"] = self._merge_datos(datos.get("datos", {}), ai_datos.get("datos", {}))
                datos["confianza_campos"] = ai_datos.get("confianza_campos", {})
        
        datos["success"] = True
        return datos

    def _merge_datos(self, d1: Dict, d2: Dict) -> Dict:
        """Helper para combinar diccionarios de datos priorizando d2 sobre d1 si no es nulo"""
        merged = d1.copy()
        for k, v in d2.items():
            if v:
                merged[k] = v
        return merged

    async def _analizar_markdown_con_claude(self, markdown: str, url: str) -> Dict[str, Any]:
        """Usa Claude para analizar markdown de Firecrawl."""
        if not self.available or not self.chat_fn:
            return {"success": False, "error": "Cliente AI no disponible"}
            
        prompt = f"""Analiza el siguiente contenido extraído del sitio web {url}.
Extrae TODOS los datos empresariales disponibles.

CONTENIDO (Markdown):
{markdown[:15000]}

Responde en JSON con esta estructura exacta:
{{
    "nombre": "Nombre comercial",
    "razon_social": "Razón social completa",
    "rfc": "RFC (formato MX)",
    "giro": "Industria/Giro",
    "direccion": "Dirección completa",
    "codigo_postal": "CP",
    "telefono": "Solo dígitos",
    "email": "Email contacto",
    "descripcion": "Descripción breve",
    "vision": "Visión de la empresa",
    "mision": "Misión de la empresa",
    "confianza": {{ "campo": 0-100 }}
}}
"""
        return await self._ejecutar_prompt_json(prompt)

    async def _ejecutar_prompt_json(self, prompt: str) -> Dict[str, Any]:
        """Helper genérico para ejecutar prompts que retornan JSON"""
        try:
            content = self.chat_fn(
                messages=[{"role": "user", "content": prompt}],
                model=self.model,
                max_tokens=2000
            )
            
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            result = json.loads(content.strip())
            confianza = result.pop("confianza", {})
            
            return {
                "success": True,
                "datos": {k: v for k, v in result.items() if v and v != "null"},
                "confianza_campos": confianza
            }
        except Exception as e:
            logger.error(f"Error en análisis AI: {e}")
            return {"success": False, "error": str(e)}

    # Manteniendo el método original para compatibilidad con el fallback
    async def _analizar_contenido_con_claude(self, content_list: List[Dict], url: str) -> Dict[str, Any]:
        """Usa Claude para analizar contenido raw de BS4."""
        combined_content = "\n\n---\n\n".join([
            f"Página: {c['url']}\nTítulo: {c['title']}\nContenido:\n{c['text'][:4000]}"
            for c in content_list[:5]
        ])
        
        prompt = f"""Analiza el siguiente contenido del sitio {url}.
Extrae datos empresariales (Nombre, RFC, Dirección, Misión, Visión, etc).

CONTENIDO:
{combined_content}

Responde en JSON con estructura: {{ "campo": "valor", "confianza": {{...}} }}
"""
        return await self._ejecutar_prompt_json(prompt)
    
    def validar_rfc(self, rfc: str) -> Dict[str, Any]:
        """
        Valida un RFC mexicano verificando formato, tipo y dígito verificador.
        
        Args:
            rfc: RFC a validar
        
        Returns:
            Dict con resultado de validación
        """
        if not rfc:
            return {"valido": False, "error": "RFC vacío"}
        
        rfc = rfc.upper().strip().replace(" ", "").replace("-", "")
        
        if len(rfc) == 12:
            tipo_persona = "moral"
            pattern = r'^[A-ZÑ&]{3}\d{6}[A-Z0-9]{3}$'
        elif len(rfc) == 13:
            tipo_persona = "fisica"
            pattern = r'^[A-ZÑ&]{4}\d{6}[A-Z0-9]{3}$'
        else:
            return {
                "valido": False,
                "error": f"Longitud inválida: {len(rfc)} (debe ser 12 o 13)",
                "tipo_persona": None
            }
        
        if not re.match(pattern, rfc):
            return {
                "valido": False,
                "error": "Formato inválido",
                "tipo_persona": tipo_persona
            }
        
        fecha_str: Optional[str] = None
        if len(rfc) >= 7:
            fecha_str = rfc[3:9] if tipo_persona == "moral" else rfc[4:10]
            try:
                year = int(fecha_str[0:2])
                month = int(fecha_str[2:4])
                day = int(fecha_str[4:6])
                
                if not (1 <= month <= 12):
                    return {
                        "valido": False,
                        "error": f"Mes inválido en fecha: {month}",
                        "tipo_persona": tipo_persona
                    }
                if not (1 <= day <= 31):
                    return {
                        "valido": False,
                        "error": f"Día inválido en fecha: {day}",
                        "tipo_persona": tipo_persona
                    }
            except ValueError:
                return {
                    "valido": False,
                    "error": "Fecha inválida en RFC",
                    "tipo_persona": tipo_persona
                }
        
        digito_valido = self._verificar_digito_rfc(rfc)
        
        return {
            "valido": True,
            "rfc": rfc,
            "tipo_persona": tipo_persona,
            "digito_verificador_valido": digito_valido,
            "fecha_nacimiento_constitucion": fecha_str if len(rfc) >= 7 else None
        }
    
    def _verificar_digito_rfc(self, rfc: str) -> bool:
        """
        Verifica el dígito verificador del RFC usando el algoritmo del SAT.
        """
        try:
            tabla = "0123456789ABCDEFGHIJKLMN&OPQRSTUVWXYZ Ñ"
            
            rfc_sin_digito = rfc[:-1]
            digito_declarado = rfc[-1]
            
            if len(rfc) == 12:
                rfc_sin_digito = " " + rfc_sin_digito
            
            suma = 0
            for i, char in enumerate(rfc_sin_digito):
                indice = tabla.find(char)
                if indice == -1:
                    return False
                suma += indice * (13 - i)
            
            residuo = suma % 11
            
            if residuo == 0:
                digito_esperado = "0"
            elif residuo == 10:
                digito_esperado = "A"
            else:
                digito_esperado = str(11 - residuo)
            
            return digito_declarado == digito_esperado
            
        except Exception as e:
            logger.debug(f"Error verificando dígito RFC: {e}")
            return False
    
    async def analizar_documento(
        self,
        contenido: str,
        tipo: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analiza el contenido de un documento para extraer datos empresariales.
        
        Args:
            contenido: Texto extraído del documento
            tipo: Tipo de documento (csf, acta_constitutiva, contrato, estado_financiero, etc.)
        
        Returns:
            Dict con datos extraídos y niveles de confianza
        """
        if not contenido or not contenido.strip():
            return {"success": False, "error": "Contenido vacío"}
        
        if not self.available:
            return await self._analizar_documento_regex(contenido)
        
        tipo_context = ""
        if tipo:
            tipo_map = {
                "csf": "Constancia de Situación Fiscal del SAT",
                "acta_constitutiva": "Acta Constitutiva de sociedad mexicana",
                "contrato": "Contrato comercial o de servicios",
                "estado_financiero": "Estado financiero o balance",
                "poder_legal": "Poder notarial o representación legal",
                "opinion_cumplimiento": "Opinión de cumplimiento 32-D del SAT"
            }
            tipo_context = f"\nTIPO DE DOCUMENTO: {tipo_map.get(tipo, tipo)}"
        
        prompt = f"""Analiza el siguiente documento de una empresa mexicana y extrae todos los datos empresariales disponibles.
{tipo_context}

CONTENIDO DEL DOCUMENTO:
{contenido[:15000]}

Extrae la información en formato JSON:
{{
    "rfc": "RFC completo si está presente",
    "razon_social": "Razón social o denominación completa",
    "nombre": "Nombre comercial si es diferente",
    "regimen_fiscal": "Régimen fiscal (ej: Régimen General de Ley Personas Morales)",
    "clave_regimen_fiscal": "Clave numérica del régimen (ej: 601)",
    "tipo_persona": "moral o fisica",
    "direccion": "Dirección fiscal completa",
    "calle": "Nombre de la calle",
    "numero_exterior": "Número exterior",
    "numero_interior": "Número interior",
    "colonia": "Colonia",
    "codigo_postal": "CP de 5 dígitos",
    "ciudad": "Ciudad o municipio",
    "estado": "Estado de México",
    "telefono": "Teléfono (solo dígitos)",
    "email": "Email de contacto",
    "fecha_constitucion": "Fecha de constitución en formato YYYY-MM-DD",
    "objeto_social": "Descripción del objeto social",
    "representante_legal": "Nombre del representante legal",
    "capital_social": "Monto del capital social",
    "actividad_economica": "Actividad económica principal",
    "confianza_por_campo": {{
        "rfc": 0-100,
        "razon_social": 0-100,
        ... (nivel de confianza para cada campo extraído)
    }}
}}

REGLAS:
- Si un dato no está presente claramente, usa null
- El RFC debe tener formato válido (12 chars moral, 13 chars física)
- Asigna confianza alta (90-100) solo si el dato está explícitamente indicado
- Asigna confianza media (70-89) si el dato se infiere del contexto
- Asigna confianza baja (50-69) si hay ambigüedad
- Responde SOLO con JSON válido"""

        try:
            if not self.chat_fn:
                return await self._analizar_documento_regex(contenido)
            content = self.chat_fn(
                messages=[{"role": "user", "content": prompt}],
                model=self.model,
                max_tokens=2500
            )

            # Check if API returned an error
            if not content or content.startswith('{"error"'):
                logger.warning(f"AI API returned error or empty response, using regex fallback")
                return await self._analizar_documento_regex(contenido)

            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            result = json.loads(content.strip())

            # Check if parsed result contains an error field (API error wrapped in JSON)
            if "error" in result and len(result) <= 2:
                logger.warning(f"AI API error in response: {result.get('error', 'unknown')}")
                return await self._analizar_documento_regex(contenido)
            
            confianza = result.pop("confianza_por_campo", {})
            
            datos = {}
            for key, value in result.items():
                if value and value != "null" and key != "confianza_por_campo":
                    datos[key] = value
            
            return {
                "success": True,
                "datos": datos,
                "confianza_campos": confianza,
                "tipo_documento": tipo
            }
            
        except json.JSONDecodeError as e:
            logger.error(f"Error parseando respuesta de Claude en documento: {e}")
            return await self._analizar_documento_regex(contenido)
        except Exception as e:
            logger.error(f"Error analizando documento con Claude: {e}")
            return {"success": False, "error": str(e)}
    
    async def _analizar_documento_regex(self, contenido: str) -> Dict[str, Any]:
        """Fallback: extrae datos usando regex cuando Claude no está disponible."""
        datos = {}
        confianza = {}
        
        rfc_pattern = r'\b([A-ZÑ&]{3,4}\d{6}[A-Z0-9]{3})\b'
        rfc_matches = re.findall(rfc_pattern, contenido.upper())
        for match in rfc_matches:
            validation = self.validar_rfc(match)
            if validation["valido"]:
                datos["rfc"] = match
                confianza["rfc"] = 90
                datos["tipo_persona"] = validation["tipo_persona"]
                break
        
        razon_patterns = [
            r'(?:Denominación|Razón Social|Nombre)[:\s]+([A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑ\s\.,]+(?:S\.?A\.?\s*(?:DE\s+)?C\.?V\.?|S\.?C\.?|S\.?A\.?P\.?I\.?|S\.?R\.?L\.?))',
            r'([A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑ\s\.,]+(?:S\.A\.\s*DE\s*C\.V\.|SOCIEDAD ANÓNIMA|S\.A\.P\.I\.))',
        ]
        for pattern in razon_patterns:
            match = re.search(pattern, contenido.upper())
            if match:
                datos["razon_social"] = match.group(1).strip()
                confianza["razon_social"] = 75
                break
        
        regimen_patterns = [
            r'(?:Régimen|Regimen)[:\s]+([^\n\r]+)',
            r'(\d{3})\s*[-–]\s*(?:Régimen|Regimen)',
        ]
        for pattern in regimen_patterns:
            match = re.search(pattern, contenido, re.IGNORECASE)
            if match:
                datos["regimen_fiscal"] = match.group(1).strip()
                confianza["regimen_fiscal"] = 70
                break
        
        cp_pattern = r'(?:C\.?P\.?|Código Postal)[:\s]*(\d{5})'
        cp_match = re.search(cp_pattern, contenido, re.IGNORECASE)
        if cp_match:
            datos["codigo_postal"] = cp_match.group(1)
            confianza["codigo_postal"] = 85
        
        email_pattern = r'\b([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\b'
        email_matches = re.findall(email_pattern, contenido.lower())
        if email_matches:
            datos["email"] = email_matches[0]
            confianza["email"] = 80
        
        return {
            "success": True,
            "datos": datos,
            "confianza_campos": confianza,
            "metodo": "regex_fallback"
        }
    
    async def validar_con_claude(self, datos: Dict[str, Any]) -> Dict[str, Any]:
        """
        Usa Claude para validar coherencia de datos y ajustar confianza.
        
        Args:
            datos: Diccionario con los datos recopilados
        
        Returns:
            Dict con validación, ajustes de confianza y correcciones sugeridas
        """
        if not self.available or not datos:
            return {"success": False, "error": "Validación no disponible"}
        
        prompt = f"""Eres un experto en datos empresariales mexicanos. Analiza los siguientes datos y valida su coherencia.

DATOS A VALIDAR:
{json.dumps(datos, ensure_ascii=False, indent=2)}

Verifica:
1. Si el RFC corresponde al tipo de persona indicado
2. Si la razón social tiene formato correcto para empresa mexicana
3. Si el código postal corresponde al estado mencionado (si hay ambos)
4. Si el email parece legítimo y relacionado con la empresa
5. Si hay inconsistencias entre los datos

Responde en JSON:
{{
    "coherencia_general": 0-100,
    "problemas_detectados": ["lista de problemas encontrados"],
    "field_confidence": {{
        "campo": {{
            "adjusted_confidence": 0-100,
            "warning": "advertencia si hay problema" o null,
            "valido": true/false
        }}
    }},
    "datos_corregidos": {{
        "campo": "valor corregido si detectaste error obvio"
    }},
    "sugerencias": ["lista de sugerencias para mejorar los datos"]
}}

IMPORTANTE: Solo corrige datos si hay errores OBVIOS (ej: espacios extra, mayúsculas/minúsculas).
No inventes datos que no tengas.
Responde SOLO con JSON válido."""

        try:
            if not self.chat_fn:
                return {"success": False, "error": "AI no disponible"}
            content = self.chat_fn(
                messages=[{"role": "user", "content": prompt}],
                model=self.model,
                max_tokens=1500
            )
            
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            result = json.loads(content.strip())
            result["success"] = True
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Error parseando validación de Claude: {e}")
            return {"success": False, "error": "Error parseando respuesta"}
        except Exception as e:
            logger.error(f"Error en validación con Claude: {e}")
            return {"success": False, "error": str(e)}
    
    async def buscar_en_fuentes_publicas(
        self,
        rfc: Optional[str] = None,
        nombre: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Busca información en fuentes públicas mexicanas (simulado, para extensión futura).
        Puede integrarse con APIs del SAT, IMSS, etc.
        """
        logger.info(f"Buscando en fuentes públicas: rfc={rfc}, nombre={nombre}")
        
        return {
            "success": True,
            "fuentes_consultadas": [],
            "datos_encontrados": {},
            "nota": "Integración con fuentes públicas pendiente de implementación"
        }


deep_research_service = DeepResearchService()
