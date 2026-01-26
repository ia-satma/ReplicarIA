"""
Servicio de Contexto Evolutivo de Clientes
Provee contexto sobre clientes a los agentes de IA A1-A7
"""
import os
import json
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List

import asyncpg

logger = logging.getLogger(__name__)

# OpenAI provider
try:
    from services.openai_provider import chat_completion_sync, is_configured
    OPENAI_AVAILABLE = is_configured()
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI provider not available for ClienteContextoService")

DATABASE_URL = os.environ.get('DATABASE_URL', '')


class ClienteContextoService:
    """
    Servicio para gestionar el contexto evolutivo de clientes.
    Proporciona información contextual a los agentes A1-A7.
    """

    def __init__(self):
        self._pool: Optional[asyncpg.Pool] = None
        self.client = OPENAI_AVAILABLE
        self.model = "gpt-4o"

        if not self.client:
            logger.warning("OpenAI AI integration not configured")
    
    async def _get_pool(self) -> asyncpg.Pool:
        """Obtiene o crea el pool de conexiones a PostgreSQL"""
        if self._pool is None:
            if not DATABASE_URL:
                raise RuntimeError("DATABASE_URL no está configurada")
            
            db_url = DATABASE_URL
            if db_url.startswith('postgres://'):
                db_url = db_url.replace('postgres://', 'postgresql://', 1)
            
            self._pool = await asyncpg.create_pool(
                db_url,
                min_size=2,
                max_size=10,
                command_timeout=60
            )
        return self._pool
    
    async def close(self):
        """Cierra el pool de conexiones"""
        if self._pool:
            await self._pool.close()
            self._pool = None
    
    async def get_contexto_para_agente(
        self,
        cliente_id: int,
        agente_id: str
    ) -> str:
        """
        Obtiene el contexto formateado de un cliente para un agente específico.
        
        Args:
            cliente_id: ID del cliente
            agente_id: ID del agente (A1, A2, A3, etc.)
        
        Returns:
            Contexto formateado en español con secciones claras
        """
        pool = await self._get_pool()
        
        async with pool.acquire() as conn:
            cliente = await conn.fetchrow(
                """
                SELECT id, nombre, rfc, razon_social, direccion, email, telefono,
                       giro, regimen_fiscal, tipo_persona, actividad_economica,
                       estado, notas_internas, created_at, updated_at
                FROM clientes
                WHERE id = $1
                """,
                cliente_id
            )
            
            if not cliente:
                return f"[ERROR] Cliente con ID {cliente_id} no encontrado."
            
            documentos = await conn.fetch(
                """
                SELECT nombre_archivo, tipo_documento, categoria, subcategoria,
                       resumen_ia, fecha_documento, fecha_vigencia_fin, version,
                       es_version_actual, created_at
                FROM clientes_documentos
                WHERE cliente_id = $1 AND activo = true
                ORDER BY created_at DESC
                LIMIT 20
                """,
                cliente_id
            )
            
            interacciones = await conn.fetch(
                """
                SELECT agente_id, agente_nombre, tipo, pregunta_usuario,
                       respuesta_agente, hallazgos, recomendaciones, alertas,
                       fue_util, created_at
                FROM clientes_interacciones
                WHERE cliente_id = $1 AND agente_id = $2
                ORDER BY created_at DESC
                LIMIT 10
                """,
                cliente_id, agente_id
            )
            
            historial = await conn.fetch(
                """
                SELECT tipo_cambio, campo_modificado, valor_anterior, valor_nuevo,
                       descripcion, origen, agente_id, created_at
                FROM clientes_historial
                WHERE cliente_id = $1
                ORDER BY created_at DESC
                LIMIT 15
                """,
                cliente_id
            )
            
            contexto_evolutivo = await conn.fetchrow(
                """
                SELECT resumen_ejecutivo, perfil_fiscal, evolucion_6_meses,
                       documentos_mas_recientes, documentos_por_vencer,
                       documentos_faltantes, resumen_interacciones,
                       agentes_mas_consultados, temas_frecuentes, alertas_activas,
                       ultima_actualizacion, version
                FROM clientes_contexto
                WHERE cliente_id = $1
                """,
                cliente_id
            )
        
        contexto = self._formatear_contexto(
            cliente=dict(cliente),
            documentos=[dict(d) for d in documentos],
            interacciones=[dict(i) for i in interacciones],
            historial=[dict(h) for h in historial],
            contexto_evolutivo=dict(contexto_evolutivo) if contexto_evolutivo else None,
            agente_id=agente_id
        )
        
        return contexto
    
    def _formatear_contexto(
        self,
        cliente: Dict[str, Any],
        documentos: List[Dict[str, Any]],
        interacciones: List[Dict[str, Any]],
        historial: List[Dict[str, Any]],
        contexto_evolutivo: Optional[Dict[str, Any]],
        agente_id: str
    ) -> str:
        """Formatea el contexto en español con secciones claras"""
        
        secciones = []
        
        secciones.append("=" * 60)
        secciones.append(f"CONTEXTO DE CLIENTE PARA AGENTE {agente_id}")
        secciones.append("=" * 60)
        
        secciones.append("\n📋 DATOS DEL CLIENTE")
        secciones.append("-" * 40)
        secciones.append(f"• ID: {cliente.get('id')}")
        secciones.append(f"• Nombre: {cliente.get('nombre') or 'No especificado'}")
        secciones.append(f"• RFC: {cliente.get('rfc') or 'No especificado'}")
        secciones.append(f"• Razón Social: {cliente.get('razon_social') or 'No especificada'}")
        secciones.append(f"• Giro: {cliente.get('giro') or 'No especificado'}")
        secciones.append(f"• Régimen Fiscal: {cliente.get('regimen_fiscal') or 'No especificado'}")
        secciones.append(f"• Tipo Persona: {cliente.get('tipo_persona') or 'No especificado'}")
        secciones.append(f"• Estado: {cliente.get('estado') or 'Activo'}")
        if cliente.get('actividad_economica'):
            secciones.append(f"• Actividad Económica: {cliente['actividad_economica']}")
        if cliente.get('notas_internas'):
            secciones.append(f"• Notas Internas: {cliente['notas_internas']}")
        
        if contexto_evolutivo:
            secciones.append("\n📊 RESUMEN EJECUTIVO")
            secciones.append("-" * 40)
            if contexto_evolutivo.get('resumen_ejecutivo'):
                secciones.append(contexto_evolutivo['resumen_ejecutivo'])
            
            if contexto_evolutivo.get('alertas_activas'):
                alertas = contexto_evolutivo['alertas_activas']
                if isinstance(alertas, str):
                    alertas = json.loads(alertas) if alertas else []
                if alertas:
                    secciones.append("\n⚠️ ALERTAS ACTIVAS:")
                    for alerta in alertas[:5]:
                        if isinstance(alerta, dict):
                            secciones.append(f"  • {alerta.get('mensaje', alerta)}")
                        else:
                            secciones.append(f"  • {alerta}")
            
            if contexto_evolutivo.get('documentos_por_vencer'):
                docs_vencer = contexto_evolutivo['documentos_por_vencer']
                if isinstance(docs_vencer, str):
                    docs_vencer = json.loads(docs_vencer) if docs_vencer else []
                if docs_vencer:
                    secciones.append("\n📅 DOCUMENTOS POR VENCER:")
                    for doc in docs_vencer[:5]:
                        if isinstance(doc, dict):
                            secciones.append(f"  • {doc.get('nombre', doc)} - Vence: {doc.get('fecha_vencimiento', 'N/A')}")
                        else:
                            secciones.append(f"  • {doc}")
            
            if contexto_evolutivo.get('documentos_faltantes'):
                docs_faltantes = contexto_evolutivo['documentos_faltantes']
                if docs_faltantes:
                    secciones.append("\n📋 DOCUMENTOS FALTANTES:")
                    for doc in docs_faltantes[:5]:
                        secciones.append(f"  • {doc}")
        
        if documentos:
            secciones.append("\n📁 DOCUMENTOS RECIENTES")
            secciones.append("-" * 40)
            for doc in documentos[:10]:
                nombre = doc.get('nombre_archivo', 'Sin nombre')
                tipo = doc.get('tipo_documento') or doc.get('categoria', 'General')
                version = doc.get('version', 1)
                fecha = doc.get('created_at')
                fecha_str = fecha.strftime('%Y-%m-%d') if fecha else 'N/A'
                secciones.append(f"  • [{tipo}] {nombre} (v{version}) - {fecha_str}")
                if doc.get('resumen_ia'):
                    resumen = doc['resumen_ia'][:150] + "..." if len(doc['resumen_ia']) > 150 else doc['resumen_ia']
                    secciones.append(f"    Resumen: {resumen}")
        
        if interacciones:
            secciones.append(f"\n💬 INTERACCIONES PREVIAS CON {agente_id}")
            secciones.append("-" * 40)
            for inter in interacciones[:5]:
                fecha = inter.get('created_at')
                fecha_str = fecha.strftime('%Y-%m-%d %H:%M') if fecha else 'N/A'
                tipo = inter.get('tipo', 'consulta')
                secciones.append(f"\n  [{fecha_str}] Tipo: {tipo}")
                if inter.get('pregunta_usuario'):
                    pregunta = inter['pregunta_usuario'][:200] + "..." if len(inter['pregunta_usuario']) > 200 else inter['pregunta_usuario']
                    secciones.append(f"    Pregunta: {pregunta}")
                if inter.get('hallazgos'):
                    hallazgos = inter['hallazgos']
                    if isinstance(hallazgos, str):
                        hallazgos = json.loads(hallazgos) if hallazgos else {}
                    if isinstance(hallazgos, dict) and hallazgos:
                        secciones.append(f"    Hallazgos: {json.dumps(hallazgos, ensure_ascii=False)[:200]}")
                if inter.get('recomendaciones'):
                    recs = inter['recomendaciones']
                    if isinstance(recs, str):
                        recs = json.loads(recs) if recs else {}
                    if isinstance(recs, dict) and recs:
                        secciones.append(f"    Recomendaciones: {json.dumps(recs, ensure_ascii=False)[:200]}")
        
        if historial:
            secciones.append("\n📜 HISTORIAL DE CAMBIOS RECIENTES")
            secciones.append("-" * 40)
            for h in historial[:10]:
                fecha = h.get('created_at')
                fecha_str = fecha.strftime('%Y-%m-%d %H:%M') if fecha else 'N/A'
                tipo = h.get('tipo_cambio', 'modificación')
                campo = h.get('campo_modificado', '')
                desc = h.get('descripcion', '')
                if desc:
                    secciones.append(f"  • [{fecha_str}] {tipo}: {desc}")
                elif campo:
                    secciones.append(f"  • [{fecha_str}] {tipo}: {campo} cambió de '{h.get('valor_anterior', 'N/A')}' a '{h.get('valor_nuevo', 'N/A')}'")
                else:
                    secciones.append(f"  • [{fecha_str}] {tipo}")
        
        secciones.append("\n" + "=" * 60)
        secciones.append(f"Generado: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
        secciones.append("=" * 60)
        
        return "\n".join(secciones)
    
    async def actualizar_contexto_evolutivo(self, cliente_id: int) -> None:
        """
        Usa Anthropic Claude para analizar todos los datos del cliente
        y generar/actualizar el contexto evolutivo.
        
        Args:
            cliente_id: ID del cliente a actualizar
        """
        if not self.client:
            logger.warning("Anthropic no configurado, no se puede actualizar contexto evolutivo")
            return
        
        pool = await self._get_pool()
        
        async with pool.acquire() as conn:
            cliente = await conn.fetchrow(
                """
                SELECT id, nombre, rfc, razon_social, giro, regimen_fiscal,
                       tipo_persona, actividad_economica, estado, notas_internas,
                       created_at, updated_at
                FROM clientes
                WHERE id = $1
                """,
                cliente_id
            )
            
            if not cliente:
                logger.error(f"Cliente {cliente_id} no encontrado")
                return
            
            documentos = await conn.fetch(
                """
                SELECT nombre_archivo, tipo_documento, categoria, resumen_ia,
                       fecha_documento, fecha_vigencia_fin, version, created_at
                FROM clientes_documentos
                WHERE cliente_id = $1 AND activo = true
                ORDER BY created_at DESC
                LIMIT 50
                """,
                cliente_id
            )
            
            interacciones = await conn.fetch(
                """
                SELECT agente_id, tipo, pregunta_usuario, hallazgos,
                       recomendaciones, alertas, fue_util, created_at
                FROM clientes_interacciones
                WHERE cliente_id = $1
                ORDER BY created_at DESC
                LIMIT 30
                """,
                cliente_id
            )
            
            historial = await conn.fetch(
                """
                SELECT tipo_cambio, campo_modificado, descripcion, created_at
                FROM clientes_historial
                WHERE cliente_id = $1
                ORDER BY created_at DESC
                LIMIT 20
                """,
                cliente_id
            )
            
            contexto_actual = await conn.fetchrow(
                "SELECT version FROM clientes_contexto WHERE cliente_id = $1",
                cliente_id
            )
        
        prompt = self._construir_prompt_analisis(
            cliente=dict(cliente),
            documentos=[dict(d) for d in documentos],
            interacciones=[dict(i) for i in interacciones],
            historial=[dict(h) for h in historial]
        )
        
        try:
            texto_respuesta = chat_completion_sync(
                messages=[{"role": "user", "content": prompt}],
                model=self.model,
                max_tokens=3000
            )
            
            if "```json" in texto_respuesta:
                texto_respuesta = texto_respuesta.split("```json")[1].split("```")[0]
            elif "```" in texto_respuesta:
                texto_respuesta = texto_respuesta.split("```")[1].split("```")[0]
            
            analisis = json.loads(texto_respuesta.strip())
            
        except json.JSONDecodeError as e:
            logger.error(f"Error parseando respuesta de IA: {e}")
            return
        except Exception as e:
            logger.error(f"Error llamando a OpenAI: {e}")
            return
        
        version_actual = contexto_actual['version'] if contexto_actual else 0
        nueva_version = version_actual + 1
        
        async with pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO clientes_contexto (
                    cliente_id, resumen_ejecutivo, perfil_fiscal, evolucion_6_meses,
                    documentos_mas_recientes, documentos_por_vencer, documentos_faltantes,
                    resumen_interacciones, agentes_mas_consultados, temas_frecuentes,
                    alertas_activas, ultima_actualizacion, version
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
                ON CONFLICT (cliente_id) DO UPDATE SET
                    resumen_ejecutivo = EXCLUDED.resumen_ejecutivo,
                    perfil_fiscal = EXCLUDED.perfil_fiscal,
                    evolucion_6_meses = EXCLUDED.evolucion_6_meses,
                    documentos_mas_recientes = EXCLUDED.documentos_mas_recientes,
                    documentos_por_vencer = EXCLUDED.documentos_por_vencer,
                    documentos_faltantes = EXCLUDED.documentos_faltantes,
                    resumen_interacciones = EXCLUDED.resumen_interacciones,
                    agentes_mas_consultados = EXCLUDED.agentes_mas_consultados,
                    temas_frecuentes = EXCLUDED.temas_frecuentes,
                    alertas_activas = EXCLUDED.alertas_activas,
                    ultima_actualizacion = EXCLUDED.ultima_actualizacion,
                    version = EXCLUDED.version
                """,
                cliente_id,
                analisis.get('resumen_ejecutivo', ''),
                json.dumps(analisis.get('perfil_fiscal', {})),
                json.dumps(analisis.get('evolucion_6_meses', {})),
                json.dumps(analisis.get('documentos_mas_recientes', [])),
                json.dumps(analisis.get('documentos_por_vencer', [])),
                analisis.get('documentos_faltantes', []),
                analisis.get('resumen_interacciones', ''),
                analisis.get('agentes_mas_consultados', []),
                analisis.get('temas_frecuentes', []),
                json.dumps(analisis.get('alertas_activas', [])),
                datetime.now(timezone.utc),
                nueva_version
            )
        
        logger.info(f"Contexto evolutivo actualizado para cliente {cliente_id}, versión {nueva_version}")
    
    def _construir_prompt_analisis(
        self,
        cliente: Dict[str, Any],
        documentos: List[Dict[str, Any]],
        interacciones: List[Dict[str, Any]],
        historial: List[Dict[str, Any]]
    ) -> str:
        """Construye el prompt para el análisis con IA"""
        
        docs_info = []
        for d in documentos[:30]:
            fecha = d.get('created_at')
            fecha_str = fecha.strftime('%Y-%m-%d') if fecha else 'N/A'
            docs_info.append(f"- {d.get('nombre_archivo')}: {d.get('tipo_documento', 'General')} ({fecha_str})")
        
        inter_info = []
        for i in interacciones[:20]:
            fecha = i.get('created_at')
            fecha_str = fecha.strftime('%Y-%m-%d') if fecha else 'N/A'
            inter_info.append(f"- Agente {i.get('agente_id')}: {i.get('tipo', 'consulta')} ({fecha_str})")
        
        hist_info = []
        for h in historial[:15]:
            fecha = h.get('created_at')
            fecha_str = fecha.strftime('%Y-%m-%d') if fecha else 'N/A'
            hist_info.append(f"- {h.get('tipo_cambio')}: {h.get('descripcion', h.get('campo_modificado', 'N/A'))} ({fecha_str})")
        
        return f"""Eres un analista fiscal experto mexicano. Analiza la siguiente información de un cliente y genera un contexto evolutivo completo.

DATOS DEL CLIENTE:
- Nombre: {cliente.get('nombre')}
- RFC: {cliente.get('rfc')}
- Razón Social: {cliente.get('razon_social')}
- Giro: {cliente.get('giro')}
- Régimen Fiscal: {cliente.get('regimen_fiscal')}
- Tipo Persona: {cliente.get('tipo_persona')}
- Actividad Económica: {cliente.get('actividad_economica')}
- Estado: {cliente.get('estado')}
- Notas Internas: {cliente.get('notas_internas')}

DOCUMENTOS ({len(documentos)} archivos):
{chr(10).join(docs_info) if docs_info else 'No hay documentos registrados'}

INTERACCIONES CON AGENTES ({len(interacciones)} registros):
{chr(10).join(inter_info) if inter_info else 'No hay interacciones registradas'}

HISTORIAL DE CAMBIOS ({len(historial)} registros):
{chr(10).join(hist_info) if hist_info else 'No hay historial registrado'}

Genera un análisis completo en formato JSON con la siguiente estructura:
{{
    "resumen_ejecutivo": "Resumen de 2-3 párrafos del estado actual del cliente, su perfil fiscal, y puntos clave a considerar",
    "perfil_fiscal": {{
        "clasificacion": "tipo de contribuyente",
        "regimen": "régimen fiscal",
        "obligaciones_principales": ["lista de obligaciones"],
        "riesgos_identificados": ["lista de riesgos"],
        "oportunidades": ["lista de oportunidades"]
    }},
    "evolucion_6_meses": {{
        "tendencia": "mejora/estable/deterioro",
        "cambios_relevantes": ["lista de cambios importantes"],
        "proyeccion": "breve proyección"
    }},
    "documentos_mas_recientes": [
        {{"nombre": "nombre del doc", "tipo": "tipo", "fecha": "fecha"}}
    ],
    "documentos_por_vencer": [
        {{"nombre": "nombre del doc", "fecha_vencimiento": "fecha", "prioridad": "alta/media/baja"}}
    ],
    "documentos_faltantes": ["lista de documentos que deberían existir pero no están"],
    "resumen_interacciones": "Resumen de las interacciones con los agentes, patrones observados",
    "agentes_mas_consultados": ["A1", "A3", etc],
    "temas_frecuentes": ["tema1", "tema2", etc],
    "alertas_activas": [
        {{"tipo": "tipo de alerta", "mensaje": "descripción", "prioridad": "alta/media/baja"}}
    ]
}}

Responde ÚNICAMENTE con el JSON, sin texto adicional."""
    
    async def registrar_interaccion(
        self,
        cliente_id: int,
        agente_id: str,
        agente_nombre: str,
        tipo: str,
        pregunta_usuario: str,
        respuesta_agente: str,
        documentos_consultados: Optional[List[str]] = None,
        chunks_usados: Optional[List[str]] = None,
        hallazgos: Optional[Dict[str, Any]] = None,
        recomendaciones: Optional[Dict[str, Any]] = None,
        alertas: Optional[Dict[str, Any]] = None,
        chat_id: Optional[str] = None,
        duracion_ms: Optional[int] = None,
        tokens_usados: Optional[int] = None
    ) -> None:
        """
        Registra una interacción del agente con el cliente.
        También registra en el historial de cambios.
        
        Args:
            cliente_id: ID del cliente
            agente_id: ID del agente (A1, A2, etc.)
            agente_nombre: Nombre descriptivo del agente
            tipo: Tipo de interacción (consulta, análisis, alerta, etc.)
            pregunta_usuario: Pregunta o solicitud del usuario
            respuesta_agente: Respuesta generada por el agente
            documentos_consultados: Lista de IDs de documentos consultados
            chunks_usados: Lista de IDs de chunks RAG usados
            hallazgos: Hallazgos del análisis (JSON)
            recomendaciones: Recomendaciones del agente (JSON)
            alertas: Alertas generadas (JSON)
            chat_id: ID del chat si aplica
            duracion_ms: Duración de la consulta en milisegundos
            tokens_usados: Tokens consumidos
        """
        pool = await self._get_pool()
        now = datetime.now(timezone.utc)
        
        async with pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO clientes_interacciones (
                    cliente_id, agente_id, agente_nombre, tipo, pregunta_usuario,
                    respuesta_agente, documentos_consultados, chunks_usados,
                    hallazgos, recomendaciones, alertas, chat_id,
                    duracion_ms, tokens_usados, created_at
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15)
                """,
                cliente_id,
                agente_id,
                agente_nombre,
                tipo,
                pregunta_usuario,
                respuesta_agente,
                documentos_consultados or [],
                chunks_usados or [],
                json.dumps(hallazgos) if hallazgos else None,
                json.dumps(recomendaciones) if recomendaciones else None,
                json.dumps(alertas) if alertas else None,
                chat_id,
                duracion_ms,
                tokens_usados,
                now
            )
            
            descripcion = f"Interacción con {agente_nombre}: {tipo}"
            if pregunta_usuario:
                descripcion += f" - {pregunta_usuario[:100]}"
            
            await conn.execute(
                """
                INSERT INTO clientes_historial (
                    cliente_id, tipo_cambio, descripcion, origen,
                    agente_id, chat_id, created_at
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                """,
                cliente_id,
                "interaccion_agente",
                descripcion,
                "agente_ia",
                agente_id,
                chat_id,
                now
            )
        
        logger.info(f"Interacción registrada: cliente={cliente_id}, agente={agente_id}, tipo={tipo}")


cliente_contexto_service = ClienteContextoService()
