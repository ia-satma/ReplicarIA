"""
Rutas API para artículos legales de la Knowledge Base.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
import logging

from services.kb.articulos_legales import articulos_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/kb/articulos", tags=["Artículos Legales"])


@router.get("/")
async def listar_articulos(limit: int = Query(100, ge=1, le=500)):
    """Lista todos los artículos legales indexados."""
    try:
        articulos = await articulos_service.obtener_todos_articulos(limit)
        return {
            "success": True,
            "total": len(articulos),
            "articulos": articulos
        }
    except Exception as e:
        logger.error(f"Error listando artículos: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/estadisticas")
async def obtener_estadisticas():
    """Obtiene estadísticas de artículos legales."""
    try:
        stats = await articulos_service.obtener_estadisticas()
        return {
            "success": True,
            **stats
        }
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tag/{tag}")
async def buscar_por_tag(tag: str):
    """Busca un artículo por su tag (@CFF_5A, @LISR_27_I, etc.)"""
    try:
        if not tag.startswith("@"):
            tag = f"@{tag}"
        
        articulo = await articulos_service.buscar_articulo(tag)
        
        if not articulo:
            raise HTTPException(status_code=404, detail=f"Artículo {tag} no encontrado")
        
        return {
            "success": True,
            "articulo": articulo
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error buscando artículo {tag}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/categoria/{categoria}")
async def buscar_por_categoria(categoria: str):
    """Busca artículos por categoría (deducciones, efos, cfdi, etc.)"""
    try:
        articulos = await articulos_service.buscar_articulos_por_categoria(categoria)
        return {
            "success": True,
            "categoria": categoria,
            "total": len(articulos),
            "articulos": articulos
        }
    except Exception as e:
        logger.error(f"Error buscando por categoría {categoria}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ley/{ley}")
async def buscar_por_ley(ley: str):
    """Busca artículos por ley (CFF, LISR, LIVA, etc.)"""
    try:
        articulos = await articulos_service.buscar_articulos_por_ley(ley.upper())
        return {
            "success": True,
            "ley": ley.upper(),
            "total": len(articulos),
            "articulos": articulos
        }
    except Exception as e:
        logger.error(f"Error buscando por ley {ley}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/deducciones")
async def fundamentos_deducciones():
    """Obtiene todos los fundamentos para análisis de deducciones."""
    try:
        fundamentos = await articulos_service.obtener_fundamentos_para_deduccion()
        return {
            "success": True,
            "descripcion": "Fundamentos legales para verificar deducibilidad de gastos",
            "total": len(fundamentos),
            "fundamentos": fundamentos
        }
    except Exception as e:
        logger.error(f"Error obteniendo fundamentos deducciones: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agente/{agente_id}")
async def contexto_para_agente(agente_id: str):
    """Genera el contexto legal relevante para un agente específico."""
    try:
        agente = agente_id.upper()
        if not agente.startswith("A") and agente not in ["ARCHIVO", "KNOWLEDGE_BASE"]:
            agente = f"A{agente}"
        
        contexto = await articulos_service.generar_contexto_legal_para_agente(agente)
        
        pool = await articulos_service.get_pool()
        async with pool.acquire() as conn:
            articulos = await conn.fetch("""
                SELECT tag, titulo, prioridad
                FROM kb_articulos_legales 
                WHERE $1 = ANY(agentes_usan)
                ORDER BY prioridad, tag
            """, agente)
        
        return {
            "success": True,
            "agente": agente,
            "total_articulos": len(articulos),
            "articulos": [dict(a) for a in articulos],
            "contexto_prompt": contexto
        }
    except Exception as e:
        logger.error(f"Error generando contexto para agente {agente_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/buscar")
async def buscar_texto(q: str = Query(..., min_length=2)):
    """Busca artículos por texto en norma o título."""
    try:
        resultados = await articulos_service.buscar_por_texto(q)
        return {
            "success": True,
            "query": q,
            "total": len(resultados),
            "resultados": resultados
        }
    except Exception as e:
        logger.error(f"Error buscando '{q}': {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/checklist-deducibilidad")
async def checklist_deducibilidad():
    """Retorna el checklist estándar de deducibilidad con fundamentos."""
    checklist = [
        {
            "orden": 1,
            "tag": "@LISR_27_I",
            "verificacion": "¿Es estrictamente indispensable para el giro?",
            "riesgo_incumplimiento": "Rechazo total de la deducción"
        },
        {
            "orden": 2,
            "tag": "@LISR_27_III",
            "verificacion": "¿Tiene CFDI válido y vigente?",
            "riesgo_incumplimiento": "No deducible sin comprobante fiscal"
        },
        {
            "orden": 3,
            "tag": "@LISR_27_IV",
            "verificacion": "¿Forma de pago correcta (>$2,000 bancarizado)?",
            "riesgo_incumplimiento": "No deducible si pago en efectivo > $2,000"
        },
        {
            "orden": 4,
            "tag": "@LISR_27_XVIII",
            "verificacion": "¿Registrado en contabilidad?",
            "riesgo_incumplimiento": "Falta de soporte contable"
        },
        {
            "orden": 5,
            "tag": "@LISR_27_XIX",
            "verificacion": "¿Si es parte relacionada, precio de mercado?",
            "riesgo_incumplimiento": "Ajuste a valores de mercado, posible recaracterización"
        },
        {
            "orden": 6,
            "tag": "@CFF_69B",
            "verificacion": "¿Proveedor NO está en lista 69-B?",
            "riesgo_incumplimiento": "30 días para acreditar materialidad o autocorregir"
        },
        {
            "orden": 7,
            "tag": "@CFF_5A",
            "verificacion": "¿Tiene razón de negocios documentada?",
            "riesgo_incumplimiento": "Recaracterización de la operación"
        }
    ]
    
    return {
        "success": True,
        "descripcion": "Checklist estándar para verificar deducibilidad de gastos",
        "total_verificaciones": len(checklist),
        "checklist": checklist
    }
