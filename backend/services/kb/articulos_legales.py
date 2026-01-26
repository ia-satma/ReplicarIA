"""
Servicio para gestión de artículos legales en la Knowledge Base.
Permite buscar y consultar fundamentos legales por tags (@CFF_5A, @LISR_27_I, etc.)
"""

import asyncpg
import os
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class ArticulosLegalesService:
    """Servicio para consulta de artículos legales indexados."""
    
    def __init__(self):
        self.pool = None
    
    async def get_pool(self):
        if not self.pool:
            self.pool = await asyncpg.create_pool(
                os.environ.get('DATABASE_URL'),
                min_size=1,
                max_size=5
            )
        return self.pool

    async def buscar_articulo(self, tag: str) -> Optional[Dict]:
        """Busca un artículo por su tag (@CFF_5A, @LISR_27_I, etc.)"""
        pool = await self.get_pool()
        async with pool.acquire() as conn:
            result = await conn.fetchrow("""
                SELECT id, tag, ley, articulo, fraccion, titulo,
                       texto_norma, interpretacion, prioridad, categoria,
                       agentes_usan, url_fuente, ultima_reforma
                FROM kb_articulos_legales WHERE tag = $1
            """, tag)
            
            if result:
                return dict(result)
            return None

    async def buscar_articulos_por_categoria(self, categoria: str) -> List[Dict]:
        """Busca artículos por categoría (deducciones, efos, cfdi, etc.)"""
        pool = await self.get_pool()
        async with pool.acquire() as conn:
            results = await conn.fetch("""
                SELECT id, tag, ley, articulo, fraccion, titulo,
                       prioridad, categoria, agentes_usan
                FROM kb_articulos_legales 
                WHERE categoria = $1
                ORDER BY 
                    CASE prioridad 
                        WHEN 'critica' THEN 1
                        WHEN 'alta' THEN 2
                        WHEN 'media' THEN 3
                        ELSE 4
                    END,
                    tag
            """, categoria)
            
            return [dict(r) for r in results]

    async def buscar_articulos_por_ley(self, ley: str) -> List[Dict]:
        """Busca artículos por ley (CFF, LISR, LIVA, etc.)"""
        pool = await self.get_pool()
        async with pool.acquire() as conn:
            results = await conn.fetch("""
                SELECT id, tag, ley, articulo, fraccion, titulo,
                       prioridad, categoria, agentes_usan
                FROM kb_articulos_legales 
                WHERE ley = $1
                ORDER BY articulo, fraccion NULLS FIRST
            """, ley)
            
            return [dict(r) for r in results]

    async def obtener_fundamentos_para_deduccion(self) -> List[Dict]:
        """Obtiene todos los fundamentos para análisis de deducciones."""
        tags_deduccion = [
            '@LISR_27_I', '@LISR_27_III', '@LISR_27_IV', 
            '@LISR_27_XVIII', '@LISR_27_XIX',
            '@CFF_69B', '@CFF_5A'
        ]
        
        pool = await self.get_pool()
        async with pool.acquire() as conn:
            results = await conn.fetch("""
                SELECT tag, titulo, texto_norma, interpretacion
                FROM kb_articulos_legales 
                WHERE tag = ANY($1)
                ORDER BY 
                    CASE tag
                        WHEN '@LISR_27_I' THEN 1
                        WHEN '@LISR_27_III' THEN 2
                        WHEN '@LISR_27_IV' THEN 3
                        WHEN '@CFF_69B' THEN 4
                        WHEN '@CFF_5A' THEN 5
                        ELSE 10
                    END
            """, tags_deduccion)
            
            return [dict(r) for r in results]

    async def generar_contexto_legal_para_agente(self, agente_id: str) -> str:
        """Genera el contexto legal relevante para un agente específico."""
        pool = await self.get_pool()
        async with pool.acquire() as conn:
            results = await conn.fetch("""
                SELECT tag, titulo, interpretacion
                FROM kb_articulos_legales 
                WHERE $1 = ANY(agentes_usan)
                AND prioridad IN ('critica', 'alta')
                ORDER BY 
                    CASE prioridad 
                        WHEN 'critica' THEN 1
                        ELSE 2
                    END
            """, agente_id)
            
            if not results:
                return ""
            
            contexto = "FUNDAMENTOS LEGALES DISPONIBLES:\n\n"
            for art in results:
                contexto += f"• {art['tag']} - {art['titulo']}\n"
            
            return contexto

    async def obtener_todos_articulos(self, limit: int = 100) -> List[Dict]:
        """Obtiene todos los artículos legales."""
        pool = await self.get_pool()
        async with pool.acquire() as conn:
            results = await conn.fetch("""
                SELECT id, tag, ley, articulo, fraccion, titulo,
                       prioridad, categoria, agentes_usan, created_at
                FROM kb_articulos_legales 
                ORDER BY 
                    CASE prioridad 
                        WHEN 'critica' THEN 1
                        WHEN 'alta' THEN 2
                        WHEN 'media' THEN 3
                        ELSE 4
                    END,
                    ley, articulo
                LIMIT $1
            """, limit)
            
            return [dict(r) for r in results]

    async def obtener_estadisticas(self) -> Dict:
        """Obtiene estadísticas de artículos legales."""
        pool = await self.get_pool()
        async with pool.acquire() as conn:
            total = await conn.fetchval("SELECT COUNT(*) FROM kb_articulos_legales")
            
            por_ley = await conn.fetch("""
                SELECT ley, COUNT(*) as count 
                FROM kb_articulos_legales 
                GROUP BY ley ORDER BY count DESC
            """)
            
            por_prioridad = await conn.fetch("""
                SELECT prioridad, COUNT(*) as count 
                FROM kb_articulos_legales 
                GROUP BY prioridad ORDER BY 
                    CASE prioridad 
                        WHEN 'critica' THEN 1
                        WHEN 'alta' THEN 2
                        WHEN 'media' THEN 3
                        ELSE 4
                    END
            """)
            
            por_categoria = await conn.fetch("""
                SELECT categoria, COUNT(*) as count 
                FROM kb_articulos_legales 
                GROUP BY categoria ORDER BY count DESC
            """)
            
            return {
                "total": total,
                "por_ley": [dict(r) for r in por_ley],
                "por_prioridad": [dict(r) for r in por_prioridad],
                "por_categoria": [dict(r) for r in por_categoria]
            }

    async def buscar_por_texto(self, query: str) -> List[Dict]:
        """Busca artículos por texto en norma o título."""
        pool = await self.get_pool()
        async with pool.acquire() as conn:
            results = await conn.fetch("""
                SELECT id, tag, ley, articulo, fraccion, titulo,
                       prioridad, categoria
                FROM kb_articulos_legales 
                WHERE 
                    titulo ILIKE $1 OR
                    texto_norma ILIKE $1 OR
                    tag ILIKE $1
                ORDER BY prioridad, tag
                LIMIT 20
            """, f"%{query}%")
            
            return [dict(r) for r in results]


articulos_service = ArticulosLegalesService()
