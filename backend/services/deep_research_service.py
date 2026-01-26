"""
Deep Research Engine - Servicio de Auto-completado Inteligente de Formularios
Investiga automáticamente datos empresariales a partir de inputs mínimos.
Usa Claude via Replit AI Integrations + Web Scraping para máxima efectividad.
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
from anthropic import Anthropic

logger = logging.getLogger(__name__)


class DeepResearchService:
    """
    Servicio de investigación profunda para auto-completado de formularios.
    Orquesta múltiples fuentes de datos: web scraping, análisis de documentos,
    validación de RFC y verificación con IA.
    """
    
    def __init__(self):
        api_key = os.environ.get('AI_INTEGRATIONS_ANTHROPIC_API_KEY')
        base_url = os.environ.get('AI_INTEGRATIONS_ANTHROPIC_BASE_URL')
        
        if api_key and base_url:
            self.client = Anthropic(api_key=api_key, base_url=base_url)
            self.available = True
            logger.info("DeepResearchService inicializado con Replit AI Integrations")
        else:
            self.client = None
            self.available = False
            logger.warning("DeepResearchService: Anthropic no configurado")
        
        self.model = "claude-sonnet-4-5"
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
        
        Args:
            url: URL del sitio web a investigar
        
        Returns:
            Dict con datos extraídos y niveles de confianza
        """
        if not url:
            return {"success": False, "error": "URL no proporcionada"}
        
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        logger.info(f"Investigando sitio web: {url}")
        
        pages_to_check = [
            "",
            "/contacto",
            "/contact",
            "/nosotros",
            "/about",
            "/about-us",
            "/quienes-somos",
            "/aviso-de-privacidad",
            "/privacy",
            "/legal",
            "/terminos",
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
                        logger.debug(f"Contenido extraído de: {page_url}")
                        
            except requests.RequestException as e:
                logger.debug(f"No se pudo acceder a {page}: {e}")
                continue
            except Exception as e:
                logger.warning(f"Error procesando {page}: {e}")
                continue
        
        if not all_content:
            return {"success": False, "error": "No se pudo acceder al sitio web"}
        
        datos = self._extraer_datos_con_regex(all_content)
        
        if self.available:
            ai_datos = await self._analizar_contenido_con_claude(all_content, url)
            if ai_datos.get("success"):
                for campo, valor in ai_datos.get("datos", {}).items():
                    if valor and not datos.get("datos", {}).get(campo):
                        if "datos" not in datos:
                            datos["datos"] = {}
                        datos["datos"][campo] = valor
                        if "confianza_campos" not in datos:
                            datos["confianza_campos"] = {}
                        datos["confianza_campos"][campo] = ai_datos.get("confianza_campos", {}).get(campo, 75)
        
        datos["success"] = True
        return datos
    
    def _extraer_datos_con_regex(self, content_list: List[Dict]) -> Dict[str, Any]:
        """Extrae datos usando patrones regex del contenido web."""
        datos = {}
        confianza = {}
        
        all_text = " ".join([c["text"] for c in content_list])
        
        rfc_pattern = r'\b([A-ZÑ&]{3,4}\d{6}[A-Z0-9]{3})\b'
        rfc_matches = re.findall(rfc_pattern, all_text.upper())
        if rfc_matches:
            for match in rfc_matches:
                validation = self.validar_rfc(match)
                if validation["valido"]:
                    datos["rfc"] = match
                    confianza["rfc"] = 90 if validation["digito_verificador_valido"] else 75
                    break
        
        email_pattern = r'\b([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\b'
        email_matches = re.findall(email_pattern, all_text.lower())
        if email_matches:
            for email in email_matches:
                if not any(x in email for x in ['example', 'test', 'demo', '@sentry', '@google', '@facebook']):
                    datos["email"] = email
                    confianza["email"] = 85
                    break
        
        phone_patterns = [
            r'\b(?:\+?52)?[\s.-]?(?:\(?\d{2,3}\)?[\s.-]?)?\d{4}[\s.-]?\d{4}\b',
            r'\b(?:\+?52)?[\s.-]?\d{10}\b',
            r'\b\d{3}[\s.-]\d{3}[\s.-]\d{4}\b',
        ]
        for pattern in phone_patterns:
            phone_matches = re.findall(pattern, all_text)
            if phone_matches:
                phone = re.sub(r'[^\d+]', '', phone_matches[0])
                if len(phone) >= 10:
                    datos["telefono"] = phone[-10:]
                    confianza["telefono"] = 80
                    break
        
        cp_pattern = r'\b(?:C\.?P\.?|Código Postal)[\s:]*(\d{5})\b'
        cp_match = re.search(cp_pattern, all_text, re.IGNORECASE)
        if cp_match:
            datos["codigo_postal"] = cp_match.group(1)
            confianza["codigo_postal"] = 85
        
        return {"datos": datos, "confianza_campos": confianza}
    
    async def _analizar_contenido_con_claude(self, content_list: List[Dict], url: str) -> Dict[str, Any]:
        """Usa Claude para analizar el contenido web y extraer datos estructurados."""
        if not self.client:
            return {"success": False, "error": "Cliente AI no disponible"}
        
        combined_content = "\n\n---\n\n".join([
            f"Página: {c['url']}\nTítulo: {c['title']}\nContenido:\n{c['text'][:4000]}"
            for c in content_list[:5]
        ])
        
        prompt = f"""Analiza el siguiente contenido extraído del sitio web {url} de una empresa mexicana.
Extrae TODOS los datos empresariales que puedas encontrar.

CONTENIDO DEL SITIO WEB:
{combined_content}

Responde en JSON con esta estructura exacta:
{{
    "nombre": "Nombre comercial de la empresa",
    "razon_social": "Razón social completa (si es diferente del nombre)",
    "rfc": "RFC si está visible (formato: 3-4 letras + 6 dígitos + 3 homoclave)",
    "giro": "Giro o industria del negocio",
    "direccion": "Dirección completa",
    "ciudad": "Ciudad",
    "estado": "Estado de México",
    "codigo_postal": "CP de 5 dígitos",
    "telefono": "Teléfono principal (solo dígitos)",
    "email": "Email de contacto principal",
    "descripcion": "Breve descripción de qué hace la empresa",
    "servicios": ["Lista de servicios principales"],
    "confianza": {{
        "nombre": 0-100,
        "razon_social": 0-100,
        "rfc": 0-100,
        ... (para cada campo)
    }}
}}

REGLAS:
- Si un campo no está disponible, usa null
- El RFC debe tener formato válido mexicano
- Los teléfonos deben ser solo dígitos (10 dígitos)
- Incluye nivel de confianza (0-100) para cada campo basado en qué tan claro está en el contenido
- Responde SOLO con el JSON, sin explicaciones"""

        try:
            if not self.client:
                return {}
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}]
            )
            
            content = getattr(response.content[0], 'text', '')
            
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            result = json.loads(content.strip())
            
            datos = {}
            confianza = result.pop("confianza", {})
            
            for key, value in result.items():
                if value and value != "null" and key != "confianza":
                    datos[key] = value
            
            return {
                "success": True,
                "datos": datos,
                "confianza_campos": {k: v for k, v in confianza.items() if v and v > 0}
            }
            
        except json.JSONDecodeError as e:
            logger.error(f"Error parseando respuesta de Claude: {e}")
            return {"success": False, "error": "Error parseando respuesta de IA"}
        except Exception as e:
            logger.error(f"Error en análisis con Claude: {e}")
            return {"success": False, "error": str(e)}
    
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
            if not self.client:
                return {}
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2500,
                messages=[{"role": "user", "content": prompt}]
            )
            
            content = getattr(response.content[0], 'text', '')
            
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            result = json.loads(content.strip())
            
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
            if not self.client:
                return {"success": False, "error": "AI no disponible"}
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1500,
                messages=[{"role": "user", "content": prompt}]
            )
            
            content = getattr(response.content[0], 'text', '')
            
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
