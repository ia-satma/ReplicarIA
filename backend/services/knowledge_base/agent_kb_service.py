import logging
import json
from typing import Optional, List, Dict, Any
from sqlalchemy import text

logger = logging.getLogger(__name__)

class AgentKBService:
    def __init__(self, session_factory, embeddings_service):
        self.session_factory = session_factory
        self.embeddings_service = embeddings_service
    
    async def get_contexto_para_agente(
        self,
        agente_id: str,
        query: str,
        max_chunks: int = 5
    ) -> str:
        try:
            query_embedding = await self.embeddings_service.generate_embedding(query)
            
            async with self.session_factory() as session:
                results = await session.execute(
                    text('''
                        SELECT 
                            c.contenido,
                            c.metadata,
                            d.nombre as documento,
                            d.version
                        FROM kb_chunks c
                        JOIN kb_documentos d ON d.id = c.documento_id
                        JOIN kb_chunk_agente ca ON ca.chunk_id = c.id
                        WHERE ca.agente_id = :agente
                        AND d.estado = 'procesado'
                        AND d.es_version_vigente = TRUE
                        ORDER BY c.created_at DESC
                        LIMIT :limit
                    '''),
                    {'agente': agente_id, 'limit': max_chunks}
                )
                rows = results.fetchall()
                
                if not rows:
                    return ''
                
                contexto = '\n\n--- CONOCIMIENTO DEL ACERVO LEGAL ---\n'
                
                for row in rows:
                    contexto += f"\n[{row[2]} {row[3] or ''}]\n"
                    contexto += f"{row[0]}\n"
                    metadata = json.loads(row[1]) if row[1] else {}
                    if metadata.get('articulo'):
                        contexto += f"(Art. {metadata['articulo']})\n"
                
                contexto += '\n--- FIN CONOCIMIENTO ---\n'
                
                return contexto
        except Exception as e:
            logger.error(f"Error getting KB context for agent {agente_id}: {e}")
            return ''
    
    async def registrar_uso_chunk(self, chunk_id: str, agente_id: str, feedback_positivo: bool = True):
        try:
            async with self.session_factory() as session:
                if feedback_positivo:
                    await session.execute(
                        text('''
                            UPDATE kb_chunk_agente 
                            SET usado_en_respuestas = usado_en_respuestas + 1,
                                feedback_positivo = feedback_positivo + 1
                            WHERE chunk_id = :chunk AND agente_id = :agente
                        '''),
                        {'chunk': chunk_id, 'agente': agente_id}
                    )
                else:
                    await session.execute(
                        text('''
                            UPDATE kb_chunk_agente 
                            SET usado_en_respuestas = usado_en_respuestas + 1,
                                feedback_negativo = feedback_negativo + 1
                            WHERE chunk_id = :chunk AND agente_id = :agente
                        '''),
                        {'chunk': chunk_id, 'agente': agente_id}
                    )
                await session.commit()
        except Exception as e:
            logger.error(f"Error registering chunk usage: {e}")
    
    async def get_solicitudes_pendientes(self, agente_id: Optional[str] = None) -> List[Dict[str, Any]]:
        try:
            async with self.session_factory() as session:
                if agente_id:
                    results = await session.execute(
                        text('''
                            SELECT id, categoria, descripcion, prioridad, solicitado_por, razon, estado, created_at
                            FROM kb_solicitudes
                            WHERE estado = 'pendiente' AND solicitado_por = :agente
                            ORDER BY 
                                CASE prioridad 
                                    WHEN 'critica' THEN 1 
                                    WHEN 'alta' THEN 2 
                                    WHEN 'media' THEN 3 
                                    WHEN 'baja' THEN 4 
                                END,
                                created_at DESC
                        '''),
                        {'agente': agente_id}
                    )
                else:
                    results = await session.execute(
                        text('''
                            SELECT id, categoria, descripcion, prioridad, solicitado_por, razon, estado, created_at
                            FROM kb_solicitudes
                            WHERE estado = 'pendiente'
                            ORDER BY 
                                CASE prioridad 
                                    WHEN 'critica' THEN 1 
                                    WHEN 'alta' THEN 2 
                                    WHEN 'media' THEN 3 
                                    WHEN 'baja' THEN 4 
                                END,
                                created_at DESC
                        ''')
                    )
                
                return [{
                    "id": str(row[0]),
                    "categoria": row[1],
                    "descripcion": row[2],
                    "prioridad": row[3],
                    "solicitado_por": row[4],
                    "razon": row[5],
                    "estado": row[6],
                    "created_at": row[7].isoformat() if row[7] else None
                } for row in results.fetchall()]
        except Exception as e:
            logger.error(f"Error getting pending solicitudes: {e}")
            return []
    
    async def crear_solicitud(
        self,
        categoria: str,
        descripcion: str,
        solicitado_por: str,
        razon: str,
        prioridad: str = 'media'
    ) -> Optional[str]:
        try:
            async with self.session_factory() as session:
                result = await session.execute(
                    text('''
                        INSERT INTO kb_solicitudes (categoria, descripcion, prioridad, solicitado_por, razon)
                        VALUES (:cat, :desc, :pri, :sol, :razon)
                        RETURNING id
                    '''),
                    {'cat': categoria, 'desc': descripcion, 'pri': prioridad, 'sol': solicitado_por, 'razon': razon}
                )
                await session.commit()
                row = result.fetchone()
                return str(row[0]) if row else None
        except Exception as e:
            logger.error(f"Error creating solicitud: {e}")
            return None
