"""
Servicio de chat mejorado para ARCHIVO - el archivista digital de Revisar.IA
Usa OpenAI GPT-4o con skills avanzadas
Incluye detección de intenciones y búsqueda de clientes existentes
"""
import os
import re
import json
import logging
import asyncpg
from typing import AsyncGenerator, Dict, Any, List, Optional
from openai import OpenAI

logger = logging.getLogger(__name__)
DATABASE_URL = os.environ.get('DATABASE_URL', '')
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')


class ArchivoChatService:
    """
    Servicio de chat con Claude para el agente ARCHIVO.
    Skills:
    - Extracción de datos de documentos (RFC, razón social, etc.)
    - Conversación guiada para recopilar información
    - Validación de datos mexicanos (RFC, CURP, etc.)
    - Generación de resúmenes y confirmaciones
    """
    
    def __init__(self):
        if not OPENAI_API_KEY:
            logger.warning("OpenAI API Key not configured - ARCHIVO chat will not work")
            self.client = None
        else:
            self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.model = "gpt-4o"
    
    async def buscar_cliente(self, termino: str) -> Dict[str, Any]:
        """
        Busca un cliente por nombre, RFC o nombre comercial en la base de datos.
        El agente usa esto cuando el usuario pregunta si un cliente ya existe.
        """
        if not DATABASE_URL:
            return {
                'encontrado': False,
                'clientes': [],
                'mensaje': 'Base de datos no configurada'
            }
        
        try:
            conn = await asyncpg.connect(DATABASE_URL)
            try:
                rows = await conn.fetch("""
                    SELECT 
                        id, nombre, rfc, razon_social, email,
                        activo, created_at
                    FROM clientes
                    WHERE 
                        LOWER(nombre) LIKE LOWER($1)
                        OR LOWER(COALESCE(razon_social, '')) LIKE LOWER($1)
                        OR LOWER(COALESCE(rfc, '')) LIKE LOWER($1)
                    LIMIT 5
                """, f'%{termino}%')
                
                clientes = []
                for row in rows:
                    clientes.append({
                        'id': row['id'],
                        'nombre': row['nombre'],
                        'rfc': row['rfc'],
                        'razon_social': row['razon_social'],
                        'email': row['email'],
                        'activo': row['activo']
                    })
                
                if clientes:
                    return {
                        'encontrado': True,
                        'clientes': clientes,
                        'mensaje': f"Encontré {len(clientes)} cliente(s) que coinciden con '{termino}'"
                    }
                else:
                    return {
                        'encontrado': False,
                        'clientes': [],
                        'mensaje': f"No encontré ningún cliente con '{termino}'. ¿Quieres darlo de alta?"
                    }
            finally:
                await conn.close()
        except Exception as e:
            logger.error(f"Error buscando cliente: {e}")
            return {
                'encontrado': False,
                'clientes': [],
                'mensaje': f'Error al buscar: {str(e)}'
            }
    
    async def obtener_estadisticas_clientes(self) -> Dict[str, Any]:
        """Obtiene estadísticas generales de clientes para contexto del agente"""
        if not DATABASE_URL:
            return {'total': 0, 'activos': 0}
        
        try:
            conn = await asyncpg.connect(DATABASE_URL)
            try:
                row = await conn.fetchrow("""
                    SELECT 
                        COUNT(*) as total,
                        COUNT(*) FILTER (WHERE activo = true) as activos
                    FROM clientes
                """)
                return {
                    'total': row['total'] if row else 0,
                    'activos': row['activos'] if row else 0
                }
            finally:
                await conn.close()
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {e}")
            return {'total': 0, 'activos': 0}
    
    def _formatear_resultado_busqueda(self, resultado: dict) -> str:
        """Formatea el resultado de búsqueda de clientes para incluir en el prompt"""
        if not resultado:
            return ""
        
        if resultado.get('encontrado'):
            clientes = resultado.get('clientes', [])
            texto = "\n### RESULTADO DE BÚSQUEDA EN BASE DE DATOS:\n"
            texto += f"✅ Se encontraron {len(clientes)} cliente(s):\n"
            for c in clientes:
                texto += f"- **{c.get('nombre', 'Sin nombre')}**"
                if c.get('rfc'):
                    texto += f" (RFC: {c['rfc']})"
                if c.get('razon_social'):
                    texto += f" - {c['razon_social']}"
                texto += f" - {'Activo' if c.get('activo') else 'Inactivo'}\n"
            texto += "\nUSA esta información para responder al usuario."
            return texto
        else:
            return f"\n### RESULTADO DE BÚSQUEDA:\n❌ No se encontró ningún cliente con ese criterio.\nPuedes ofrecer darlo de alta.\n"
    
    def _detectar_intencion_busqueda(self, mensaje: str) -> Optional[str]:
        """Detecta si el usuario quiere buscar un cliente existente y extrae el término"""
        mensaje_lower = mensaje.lower()
        
        palabras_clave = ['ya está', 'existe', 'tiene', 'registrado', 'dado de alta', 'tenemos', 'hay', 'busca', 'encuentra']
        
        if any(palabra in mensaje_lower for palabra in palabras_clave):
            patrones_especificos = [
                r'(?:ya está|existe|tiene|registrado|tenemos|hay)\s+(?:dada de alta|dado de alta|registrada|registrado)?\s*(?:la empresa|el cliente|a)?\s*["\']?(\w+)["\']?\??$',
                r'(?:dada de alta|dado de alta)\s+(?:la empresa|el cliente|a)?\s*["\']?(\w+)["\']?\??$',
                r'(?:buscar?|encuentra?)\s+(?:a|la empresa|el cliente)?\s*["\']?(\w+)["\']?',
                r'(?:información de|datos de|info de)\s+["\']?(\w+)["\']?',
            ]
            
            for patron in patrones_especificos:
                match = re.search(patron, mensaje_lower)
                if match:
                    termino = match.group(1).strip().rstrip('?')
                    if termino and len(termino) > 2 and termino not in ['alta', 'cliente', 'empresa']:
                        logger.info(f"📚 ARCHIVO: Extrayendo término '{termino}' de mensaje")
                        return termino
            
            palabras = mensaje.split()
            for palabra in reversed(palabras):
                palabra_limpia = re.sub(r'[^\w]', '', palabra)
                if len(palabra_limpia) > 3 and palabra[0].isupper():
                    logger.info(f"📚 ARCHIVO: Usando palabra mayúscula '{palabra_limpia}' como término")
                    return palabra_limpia
        
        return None
    
    def get_system_prompt(self, company_context: dict = None, extracted_data: dict = None, user_context: dict = None) -> str:
        """Sistema de prompts con skills especializadas para extracción y onboarding"""
        
        # Contexto del usuario actual
        usuario_email = user_context.get('email', 'desconocido') if user_context else 'desconocido'
        usuario_nombre = user_context.get('nombre', 'Usuario') if user_context else 'Usuario'
        es_admin = user_context.get('is_admin', False) if user_context else False
        cliente_asociado = user_context.get('cliente_nombre', 'Ninguno') if user_context else 'Ninguno'
        resultado_busqueda = user_context.get('resultado_busqueda') if user_context else None
        
        base_prompt = """Eres ARCHIVO 📚, el archivista digital inteligente de Revisar.IA.

## USUARIO ACTUAL
- Email: {usuario_email}
- Nombre: {usuario_nombre}
- Es Administrador: {es_admin}
- Cliente asociado: {cliente_asociado}
{admin_note}

## IMPORTANTE - DETECCIÓN DE INTENCIONES
ANTES de seguir cualquier flujo de onboarding, ANALIZA el mensaje del usuario:

### SI EL USUARIO PREGUNTA SOBRE UN CLIENTE EXISTENTE:
Palabras clave: "ya está", "existe", "tiene", "registrado", "dado de alta", "tenemos"
- SI recibiste información de búsqueda, ÚSALA para responder
- Ejemplo: "¿ya está dada de alta Fortezza?" → Responde con los resultados de búsqueda

{resultado_busqueda_section}

### SI EL USUARIO QUIERE DAR DE ALTA UN CLIENTE NUEVO:
Palabras clave: "nuevo cliente", "dar de alta", "registrar", "agregar"
- Inicia el flujo de recopilación de datos

### SI EL USUARIO PREGUNTA ALGO GENERAL:
- Responde la pregunta directamente, NO sigas el flujo ciegamente

**NUNCA ignores una pregunta del usuario para seguir tu script.**
**SIEMPRE responde lo que el usuario pregunta PRIMERO.**

## TU MISIÓN
Dar la bienvenida a NUEVAS EMPRESAS que quieren registrarse en Revisar.IA, recopilando su información de manera conversacional y eficiente.

## CONTEXTO DE REVISAR.IA
Revisar.IA ayuda a empresas mexicanas que CONTRATAN servicios intangibles (consultoría, software, marketing, legal, etc.) a documentar correctamente estas operaciones ANTES de que el SAT las audite. El objetivo es prevenir problemas fiscales.

## PÚBLICO OBJETIVO
Tus usuarios son empresas que PAGAN por servicios intangibles. NO son los proveedores.
Ejemplo: Una constructora que contrata consultoría de ingeniería. Tu usuario es la constructora.

## DATOS QUE NECESITAS RECOPILAR
1. **Nombre** o **Razón Social** de la empresa
2. **RFC** (formato: 3-4 letras + 6 dígitos fecha + 3 homoclave, ej: ABC210101XY9)
3. **Giro o industria** del negocio
4. **Dirección fiscal** (opcional pero útil)
5. **Email de contacto**
6. **Teléfono** (opcional)
7. **Sitio web** (opcional)

## SKILL: ANÁLISIS DE DOCUMENTOS
Cuando recibas contenido de documentos (marcado con === DOCUMENTO ===):
1. LEE TODO el contenido cuidadosamente
2. EXTRAE datos usando estos patrones:
   - RFC: Busca patrones como "RFC: XXX000000XXX" o el patrón directo [A-ZÑ&]{{3,4}}\\d{{6}}[A-Z0-9]{{3}}
   - Razón Social: Busca después de "Denominación/Razón Social:", "Nombre:", o al inicio de documentos formales
   - Régimen fiscal: Busca "Régimen Fiscal", "Régimen de Capital"
   - Domicilio: Busca "Domicilio fiscal", "Dirección:", incluye calle, colonia, CP, ciudad, estado
   - Email: Patrones de correo electrónico
   - Teléfono: Números de 10 dígitos
3. PRESENTA los datos extraídos de forma estructurada
4. SOLO pregunta por lo que NO encontraste

## SKILL: VALIDACIÓN DE RFC MEXICANO
Un RFC válido tiene:
- Personas morales: 3 letras + 6 dígitos (fecha AAMMDD) + 3 homoclave
- Personas físicas: 4 letras + 6 dígitos + 3 homoclave
Ejemplos válidos: ABC210315XY9, GAFE800101AAA

## SKILL: CONVERSACIÓN GUIADA
- Sé amable pero eficiente
- Si el usuario da información parcial, reconócela y pide solo lo faltante
- Usa emojis moderadamente: 📋 ✅ 📊 ⏳ 🏢 📁
- Cuando tengas suficientes datos (mínimo nombre/razón social + RFC), ofrece crear el registro
- Si el usuario parece confundido, explica brevemente el proceso

## FORMATO DE RESPUESTA CUANDO EXTRAES DATOS
📊 **Información extraída:**
✅ **Razón Social:** [valor]
✅ **RFC:** [valor]
✅ **Giro:** [valor]
✅ **Email:** [valor]
[etc para cada dato encontrado]

⏳ **Datos faltantes:**
- [lista de lo que aún necesitas]

[Pregunta específica sobre el dato más importante que falta]

## FORMATO CUANDO TIENES DATOS SUFICIENTES
📋 **Datos listos para crear el registro:**

🏢 **[Nombre de la empresa]**
- RFC: [valor]
- Giro: [valor]
- Email: [valor]
- [otros datos]

¿Confirmas que estos datos son correctos? Puedes editarlos en el formulario o decirme si hay algo que corregir.

## REGLAS CRÍTICAS
1. NUNCA inventes datos - si no lo tienes, pregunta
2. SIEMPRE responde en español mexicano
3. Si el usuario sube documentos, DEBES analizarlos antes de pedir más información
4. Sé proactivo: ofrece ayuda, sugiere qué documentos pueden ser útiles
5. Mantén el contexto de la conversación - no repitas preguntas ya respondidas""".format(
            usuario_email=usuario_email,
            usuario_nombre=usuario_nombre,
            es_admin='SÍ ✅' if es_admin else 'NO',
            cliente_asociado=cliente_asociado,
            admin_note='\n⚠️ Este usuario es ADMINISTRADOR, tiene acceso completo al sistema.' if es_admin else '',
            resultado_busqueda_section=self._formatear_resultado_busqueda(resultado_busqueda) if resultado_busqueda else ''
        )

        if extracted_data:
            datos_str = json.dumps(extracted_data, ensure_ascii=False, indent=2)
            base_prompt += f"""

## DATOS YA RECOPILADOS EN ESTA SESIÓN
{datos_str}

IMPORTANTE: No vuelvas a pedir estos datos. Enfócate en lo que falta."""

        if company_context:
            base_prompt += f"""

## CONTEXTO DE EMPRESA ACTUAL
{json.dumps(company_context, ensure_ascii=False, indent=2)}"""
        
        return base_prompt
    
    async def chat_stream(
        self, 
        message: str, 
        history: list = None, 
        company_id: str = None,
        company_context: dict = None,
        extracted_data: dict = None,
        user_context: dict = None
    ) -> AsyncGenerator[str, None]:
        """
        Genera respuestas en streaming usando Claude con skills mejoradas.
        Incluye detección de intención de búsqueda y contexto de usuario.
        """
        if not self.client:
            yield "⚠️ Error: El servicio de chat no está configurado. Verifica que OPENAI_API_KEY esté configurada."
            return
        
        if user_context is None:
            user_context = {}
        
        termino_busqueda = self._detectar_intencion_busqueda(message)
        if termino_busqueda:
            logger.info(f"📚 ARCHIVO: Detectada intención de búsqueda para '{termino_busqueda}'")
            resultado = await self.buscar_cliente(termino_busqueda)
            user_context['resultado_busqueda'] = resultado
            logger.info(f"📚 ARCHIVO: Resultado búsqueda: {resultado.get('mensaje', 'sin mensaje')}")
        
        messages = []
        
        if history:
            for msg in history:
                role = msg.get("role")
                content = msg.get("content", "")
                if role in ["user", "assistant"] and content:
                    messages.append({
                        "role": role,
                        "content": content
                    })
        
        messages.append({"role": "user", "content": message})
        
        try:
            stream = self.client.chat.completions.create(
                model=self.model,
                max_tokens=2048,
                messages=[
                    {"role": "system", "content": self.get_system_prompt(company_context, extracted_data, user_context)},
                    *messages
                ],
                stream=True
            )
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Chat error: {e}")

            if "rate_limit" in error_msg.lower():
                yield "⚠️ Demasiadas solicitudes. Por favor espera unos segundos e intenta de nuevo."
            else:
                yield f"⚠️ Error al procesar tu solicitud. Por favor intenta de nuevo."
                logger.error(f"Full error: {error_msg}")
    
    async def extract_data_from_text(self, text: str) -> Dict[str, Any]:
        """
        Extrae datos estructurados de texto usando patrones y Claude
        """
        extracted = {}
        
        rfc_pattern = r'[A-ZÑ&]{3,4}\d{6}[A-Z0-9]{3}'
        rfc_matches = re.findall(rfc_pattern, text.upper())
        if rfc_matches:
            extracted["rfc"] = rfc_matches[0]
        
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        email_matches = re.findall(email_pattern, text.lower())
        if email_matches:
            extracted["email"] = email_matches[0]
        
        phone_pattern = r'(?:\+?52)?[\s.-]?(?:\d{2,3}[\s.-]?){3,4}\d{2,4}'
        phone_matches = re.findall(phone_pattern, text)
        if phone_matches:
            phone = re.sub(r'[^\d]', '', phone_matches[0])
            if len(phone) >= 10:
                extracted["telefono"] = phone[-10:]
        
        razon_patterns = [
            r'(?:Denominación|Razón Social)[:\s]+([A-ZÁÉÍÓÚÑ\s\.,]+(?:S\.?A\.?\s+(?:DE\s+)?C\.?V\.?|S\.?C\.?|S\.?A\.?P\.?I\.?))',
            r'(?:Nombre)[:\s]+([A-ZÁÉÍÓÚÑ\s\.,]+(?:S\.?A\.?\s+(?:DE\s+)?C\.?V\.?|S\.?C\.?|S\.?A\.?P\.?I\.?))',
        ]
        for pattern in razon_patterns:
            match = re.search(pattern, text.upper())
            if match:
                extracted["razon_social"] = match.group(1).strip()
                break
        
        regimen_pattern = r'(?:Régimen[:\s]+)([^\n]+)'
        regimen_match = re.search(regimen_pattern, text, re.IGNORECASE)
        if regimen_match:
            extracted["regimen_fiscal"] = regimen_match.group(1).strip()
        
        cp_pattern = r'(?:C\.?P\.?|Código Postal)[:\s]*(\d{5})'
        cp_match = re.search(cp_pattern, text)
        if cp_match:
            extracted["codigo_postal"] = cp_match.group(1)
        
        return extracted
    
    async def chat_with_extraction(
        self,
        message: str,
        document_content: str = None,
        history: list = None,
        current_data: dict = None
    ) -> Dict[str, Any]:
        """
        Chat que también extrae datos automáticamente del mensaje y documentos
        """
        full_message = message
        extracted = current_data.copy() if current_data else {}
        
        if document_content:
            full_message = f"""El usuario ha subido documentos. Aquí está el contenido:

=== DOCUMENTO ===
{document_content}
=== FIN DOCUMENTO ===

Mensaje del usuario: {message}

INSTRUCCIONES:
1. Analiza el documento y extrae TODA la información relevante
2. Presenta un resumen de lo encontrado con ✅
3. Indica qué datos faltan con ⏳
4. Haz UNA pregunta sobre el dato más importante que falta"""
            
            doc_data = await self.extract_data_from_text(document_content)
            extracted.update(doc_data)
        else:
            msg_data = await self.extract_data_from_text(message)
            extracted.update(msg_data)
        
        response_text = ""
        async for chunk in self.chat_stream(
            message=full_message,
            history=history,
            extracted_data=extracted
        ):
            response_text += chunk
        
        response_data = await self.extract_data_from_text(response_text)
        extracted.update(response_data)
        
        return {
            "response": response_text,
            "extracted_data": extracted,
            "has_minimum_data": bool(extracted.get("rfc") or extracted.get("razon_social") or extracted.get("nombre"))
        }
    
    def classify_document_by_name(self, file_name: str, file_type: str) -> dict:
        """
        Clasifica un documento basándose en el nombre del archivo
        """
        file_name_lower = file_name.lower()
        
        classifications = {
            'csf': ['csf', 'constancia', 'situacion_fiscal', 'sat'],
            'rfc': ['rfc', 'cedula'],
            'acta_constitutiva': ['acta', 'constitutiva', 'constitucion', 'escritura'],
            'poder_legal': ['poder', 'representante', 'apoderado', 'legal'],
            'estado_financiero': ['estado', 'financiero', 'balance', 'resultado', 'eeff'],
            'declaracion_isr': ['declaracion', 'isr', 'anual', 'impuesto'],
            'contrato': ['contrato', 'convenio', 'acuerdo', 'servicio'],
            'cfdi': ['cfdi', 'factura', 'xml', 'comprobante'],
            'comprobante_domicilio': ['domicilio', 'recibo', 'luz', 'agua', 'cfe', 'telmex'],
            'ine': ['ine', 'identificacion', 'credencial', 'ife'],
            'curp': ['curp']
        }
        
        detected = 'otro'
        for doc_type, keywords in classifications.items():
            if any(kw in file_name_lower for kw in keywords):
                detected = doc_type
                break
        
        doc_names = {
            'csf': 'Constancia de Situación Fiscal',
            'rfc': 'Cédula de Identificación Fiscal',
            'acta_constitutiva': 'Acta Constitutiva',
            'poder_legal': 'Poder del Representante Legal',
            'estado_financiero': 'Estado Financiero',
            'declaracion_isr': 'Declaración Anual ISR',
            'contrato': 'Contrato de Servicios',
            'cfdi': 'CFDI / Factura',
            'comprobante_domicilio': 'Comprobante de Domicilio',
            'ine': 'Identificación Oficial (INE)',
            'curp': 'CURP',
            'otro': 'Documento General'
        }
        
        return {
            "success": True,
            "classification": detected,
            "classification_name": doc_names.get(detected, 'Documento'),
            "file_name": file_name,
            "file_type": file_type,
            "summary": f"Documento clasificado como: {doc_names.get(detected, 'Documento')}"
        }
    
    def validate_rfc(self, rfc: str) -> Dict[str, Any]:
        """
        Valida formato de RFC mexicano
        """
        if not rfc:
            return {"valid": False, "error": "RFC vacío"}
        
        rfc = rfc.upper().strip()
        
        pattern_moral = r'^[A-ZÑ&]{3}\d{6}[A-Z0-9]{3}$'
        pattern_fisica = r'^[A-ZÑ&]{4}\d{6}[A-Z0-9]{3}$'
        
        if re.match(pattern_moral, rfc):
            return {"valid": True, "tipo": "moral", "rfc": rfc}
        elif re.match(pattern_fisica, rfc):
            return {"valid": True, "tipo": "fisica", "rfc": rfc}
        else:
            return {"valid": False, "error": "Formato de RFC inválido", "rfc": rfc}
    
    def extract_company_data(self, conversation_history: list) -> dict:
        """
        Extrae datos estructurados de la empresa a partir del historial de conversación
        """
        company_data = {
            "nombre": None,
            "razon_social": None,
            "rfc": None,
            "industria": None,
            "giro": None,
            "facturacion_anual": None,
            "servicios_intangibles": [],
            "email": None,
            "telefono": None,
            "direccion": None,
            "documentos_subidos": []
        }
        
        full_text = ""
        for msg in conversation_history:
            if msg.get("role") == "user":
                full_text += " " + msg.get("content", "")
        
        rfc_pattern = r'[A-ZÑ&]{3,4}\d{6}[A-Z0-9]{3}'
        rfc_match = re.search(rfc_pattern, full_text.upper())
        if rfc_match:
            company_data["rfc"] = rfc_match.group()
        
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        email_match = re.search(email_pattern, full_text)
        if email_match:
            company_data["email"] = email_match.group()
        
        return company_data


archivo_service = ArchivoChatService()
