"""
Continuous Learning System for Knowledge Base
Analyzes gaps, evaluates chunk quality, and generates improvement suggestions
"""
import logging
from datetime import datetime
from typing import Dict, Any, List
from sqlalchemy import text

logger = logging.getLogger(__name__)

class ContinuousLearningService:
    def __init__(self, session_factory, anthropic_client=None):
        self.session_factory = session_factory
        self.anthropic = anthropic_client
    
    async def analizar_gaps_y_sugerencias(self) -> Dict[str, Any]:
        """Analyze failed queries and problematic chunks to generate improvement suggestions"""
        results = {
            "queries_fallidas": [],
            "chunks_problematicos": [],
            "solicitudes_creadas": 0,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        async with self.session_factory() as session:
            queries_result = await session.execute(
                text('''
                    SELECT query, agente_id, COUNT(*) as count
                    FROM kb_search_log
                    WHERE results_count = 0
                    AND created_at > NOW() - INTERVAL '7 days'
                    GROUP BY query, agente_id
                    ORDER BY count DESC
                    LIMIT 20
                ''')
            )
            queries_fallidas = queries_result.fetchall()
            
            chunks_result = await session.execute(
                text('''
                    SELECT c.id, c.contenido, c.documento_id, ca.feedback_negativo, ca.agente_id
                    FROM kb_chunks c
                    JOIN kb_chunk_agente ca ON ca.chunk_id = c.id
                    WHERE ca.feedback_negativo > ca.feedback_positivo
                    AND ca.usado_en_respuestas > 5
                ''')
            )
            chunks_problematicos = chunks_result.fetchall()
            
            for row in queries_fallidas:
                query, agente_id, count = row[0], row[1], row[2]
                results["queries_fallidas"].append({
                    "query": query,
                    "agente_id": agente_id,
                    "count": count
                })
                
                if count >= 3:
                    await session.execute(
                        text('''
                            INSERT INTO kb_solicitudes (categoria, descripcion, prioridad, solicitado_por, razon)
                            SELECT 'general', :desc, 'alta', :agente, :razon
                            WHERE NOT EXISTS (
                                SELECT 1 FROM kb_solicitudes 
                                WHERE descripcion = :desc AND estado = 'pendiente'
                            )
                        '''),
                        {
                            'desc': f'Información sobre: {query}',
                            'agente': agente_id,
                            'razon': f'Consultado {count} veces sin resultados en los últimos 7 días'
                        }
                    )
                    results["solicitudes_creadas"] += 1
            
            for row in chunks_problematicos:
                chunk_id, contenido, doc_id, feedback_neg, agente = row
                results["chunks_problematicos"].append({
                    "chunk_id": str(chunk_id),
                    "feedback_negativo": feedback_neg,
                    "agente_id": agente
                })
                
                if self.anthropic:
                    try:
                        response = self.anthropic.messages.create(
                            model='claude-sonnet-4-5',
                            max_tokens=500,
                            messages=[{
                                'role': 'user',
                                'content': f'''Este chunk de conocimiento tiene más feedback negativo que positivo.
                                
CHUNK:
{contenido[:1000]}

¿Qué problema podría tener? ¿Está incompleto, desactualizado, mal chunkeado?
Responde en JSON: {{ "problema": "...", "sugerencia": "..." }}'''
                            }]
                        )
                        
                        await session.execute(
                            text('''
                                INSERT INTO kb_solicitudes (categoria, descripcion, prioridad, solicitado_por, razon)
                                VALUES ('revision', :desc, 'media', 'sistema', :razon)
                            '''),
                            {
                                'desc': f'Revisar chunk ID {chunk_id}',
                                'razon': 'Chunk con feedback negativo alto'
                            }
                        )
                        results["solicitudes_creadas"] += 1
                    except Exception as e:
                        logger.error(f"Error analyzing chunk {chunk_id}: {e}")
            
            await session.commit()
        
        return results
    
    async def calcular_metricas_evolucion(self) -> Dict[str, Any]:
        """Calculate weekly evolution metrics and store in history"""
        fecha_hoy = datetime.now().strftime('%Y-%m-%d')
        
        async with self.session_factory() as session:
            metricas_result = await session.execute(
                text('''
                    SELECT 
                        COUNT(DISTINCT d.id) as documentos,
                        COUNT(c.id) as chunks,
                        COALESCE(AVG(c.score_calidad), 0) as calidad_promedio,
                        (SELECT COUNT(*) FROM kb_search_log WHERE results_count > 0 AND created_at > NOW() - INTERVAL '7 days') as busquedas_exitosas,
                        (SELECT COUNT(*) FROM kb_search_log WHERE results_count = 0 AND created_at > NOW() - INTERVAL '7 days') as busquedas_fallidas
                    FROM kb_documentos d
                    LEFT JOIN kb_chunks c ON c.documento_id = d.id
                ''')
            )
            metricas = metricas_result.fetchone()
            
            await session.execute(
                text('''
                    INSERT INTO kb_metricas_historico (fecha, documentos, chunks, calidad_promedio, busquedas_exitosas, busquedas_fallidas)
                    VALUES (:fecha, :docs, :chunks, :calidad, :exitosas, :fallidas)
                    ON CONFLICT (fecha) DO UPDATE SET
                        documentos = EXCLUDED.documentos,
                        chunks = EXCLUDED.chunks,
                        calidad_promedio = EXCLUDED.calidad_promedio,
                        busquedas_exitosas = EXCLUDED.busquedas_exitosas,
                        busquedas_fallidas = EXCLUDED.busquedas_fallidas
                '''),
                {
                    'fecha': fecha_hoy,
                    'docs': metricas[0],
                    'chunks': metricas[1],
                    'calidad': float(metricas[2]),
                    'exitosas': metricas[3],
                    'fallidas': metricas[4]
                }
            )
            await session.commit()
            
            return {
                "fecha": fecha_hoy,
                "documentos": metricas[0],
                "chunks": metricas[1],
                "calidad_promedio": float(metricas[2]),
                "busquedas_exitosas": metricas[3],
                "busquedas_fallidas": metricas[4],
                "tasa_exito": metricas[3] / (metricas[3] + metricas[4]) if (metricas[3] + metricas[4]) > 0 else 0
            }
    
    async def get_tendencias(self, dias: int = 30) -> List[Dict[str, Any]]:
        """Get historical trends for the KB metrics"""
        async with self.session_factory() as session:
            result = await session.execute(
                text('''
                    SELECT fecha, documentos, chunks, calidad_promedio, busquedas_exitosas, busquedas_fallidas
                    FROM kb_metricas_historico
                    WHERE fecha > NOW() - INTERVAL ':dias days'
                    ORDER BY fecha DESC
                '''.replace(':dias', str(dias)))
            )
            
            return [{
                "fecha": row[0].isoformat() if row[0] else None,
                "documentos": row[1],
                "chunks": row[2],
                "calidad_promedio": float(row[3]) if row[3] else 0,
                "busquedas_exitosas": row[4],
                "busquedas_fallidas": row[5]
            } for row in result.fetchall()]
