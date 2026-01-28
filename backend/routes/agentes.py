"""
Rutas de API para Configuración de Agentes - Revisar.IA
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any

from config_agentes import (
    AGENT_CONFIGS,
    get_agent_config,
    get_agentes_para_fase,
    get_agentes_que_bloquean,
    get_agentes_que_emiten_vbc,
    get_normativa_requerida_por_agente,
    get_output_schema,
    get_contexto_requerido,
    listar_todos_los_agentes,
    get_plantilla_respuesta
)
from services.durezza_database import durezza_db
from config.contexto_requerido import CONTEXTO_POR_AGENTE
from services.contexto_service import (
    obtener_resumen_contexto_agente,
    listar_todos_agentes_contexto
)

router = APIRouter(prefix="/api/agentes", tags=["Agentes Revisar.IA"])


@router.get("")
async def list_agentes() -> Dict[str, Any]:
    """Lista todos los agentes disponibles"""
    return {
        "agentes": listar_todos_los_agentes(),
        "total": len(AGENT_CONFIGS)
    }


@router.get("/config/{agent_id}")
async def get_agente_config(agent_id: str) -> Dict[str, Any]:
    """Obtiene la configuración completa de un agente"""
    config = get_agent_config(agent_id)
    if not config:
        raise HTTPException(status_code=404, detail=f"Agente {agent_id} no encontrado")
    return config


@router.get("/fase/{fase}")
async def get_agentes_por_fase(fase: str) -> Dict[str, Any]:
    """Obtiene todos los agentes que participan en una fase"""
    fase_upper = fase.upper()
    agentes = get_agentes_para_fase(fase_upper)
    return {
        "fase": fase_upper,
        "agentes": [a["id"] for a in agentes],
        "total": len(agentes),
        "detalles": [{"id": a["id"], "nombre": a["nombre"], "rol": a["rol"][:100] + "..."} for a in agentes]
    }


@router.get("/bloqueadores")
async def get_agentes_bloqueadores() -> Dict[str, Any]:
    """Obtiene todos los agentes que pueden bloquear el avance"""
    agentes = get_agentes_que_bloquean()
    return {
        "agentes": [{"id": a["id"], "nombre": a["nombre"]} for a in agentes],
        "total": len(agentes)
    }


@router.get("/vbc")
async def get_agentes_vbc() -> Dict[str, Any]:
    """Obtiene todos los agentes que emiten Visto Bueno Crítico"""
    agentes = get_agentes_que_emiten_vbc()
    return {
        "agentes": [{"id": a["id"], "nombre": a["nombre"]} for a in agentes],
        "total": len(agentes)
    }


@router.get("/output-schema/{agent_id}")
async def get_agente_output_schema(agent_id: str) -> Dict[str, Any]:
    """Obtiene el schema de output de un agente"""
    schema = get_output_schema(agent_id)
    if not schema:
        raise HTTPException(status_code=404, detail=f"Agente {agent_id} no encontrado")
    return {
        "agent_id": agent_id,
        "output_schema": schema
    }


@router.get("/contexto/{agent_id}")
async def get_agente_contexto(agent_id: str) -> Dict[str, Any]:
    """Obtiene los campos de contexto requeridos por un agente"""
    contexto = get_contexto_requerido(agent_id)
    if not contexto:
        raise HTTPException(status_code=404, detail=f"Agente {agent_id} no encontrado")
    return {
        "agent_id": agent_id,
        "contexto_requerido": contexto
    }


@router.get("/normativa/{agent_id}")
async def get_agente_normativa(agent_id: str) -> Dict[str, Any]:
    """Obtiene la normativa que un agente necesita conocer"""
    normativa = get_normativa_requerida_por_agente(agent_id)
    return {
        "agent_id": agent_id,
        "normativa_relevante": normativa
    }


@router.get("/plantilla/{agent_id}")
async def get_agente_plantilla(agent_id: str) -> Dict[str, Any]:
    """Obtiene la plantilla de respuesta de un agente"""
    plantilla = get_plantilla_respuesta(agent_id)
    if not plantilla:
        raise HTTPException(status_code=404, detail=f"Agente {agent_id} no encontrado")
    return {
        "agent_id": agent_id,
        "plantilla_respuesta": plantilla
    }


@router.post("/seed")
async def seed_agent_configs() -> Dict[str, Any]:
    """Inserta/actualiza todas las configuraciones de agentes en la BD"""
    results = []
    errors = []
    
    for agent_id, config in AGENT_CONFIGS.items():
        try:
            contexto_req = config["contexto_requerido"]
            contexto_list = contexto_req.get("obligatorio", []) + contexto_req.get("deseable", [])
            
            agent_data = {
                "agente": config["id"],
                "nombre_display": config["nombre"],
                "descripcion_rol": config["rol"],
                "contexto_requerido": contexto_list,
                "normativa_relevante": config["normativa_relevante"],
                "output_schema": config["output_schema"],
                "plantilla_respuesta": config.get("plantilla_respuesta", ""),
                "fases_donde_participa": config["fases_participacion"],
                "puede_bloquear_avance": config.get("puede_bloquear_avance", False),
                "puede_aprobar_final": config.get("puede_aprobar_final", False),
                "requiere_validacion_humana_default": config.get("requiere_validacion_humana_default", False),
                "activo": True
            }
            result = await durezza_db.create_agent_config(agent_data)
            results.append({"agent_id": agent_id, "status": "ok", "id": result.get("id")})
        except Exception as e:
            errors.append({"agent_id": agent_id, "error": str(e)})
    
    return {
        "success": len(results),
        "errors": len(errors),
        "results": results,
        "error_details": errors
    }


@router.get("/db")
async def get_all_agents_from_db() -> List[Dict[str, Any]]:
    """Obtiene todas las configuraciones de agentes desde la BD"""
    return await durezza_db.get_agent_configs(activo=True)


@router.get("/db/{agent_id}")
async def get_agent_from_db(agent_id: str) -> Dict[str, Any]:
    """Obtiene una configuración de agente desde la BD"""
    config = await durezza_db.get_agent_config(agent_id)
    if not config:
        raise HTTPException(status_code=404, detail=f"Agente {agent_id} no encontrado en BD")
    return config


@router.get("/contexto-requerido")
async def listar_contexto_todos_agentes() -> Dict[str, Any]:
    """Lista el contexto requerido por todos los agentes"""
    return {
        "agentes": listar_todos_agentes_contexto(),
        "total": len(CONTEXTO_POR_AGENTE)
    }


@router.get("/{agente_id}/contexto-requerido")
async def obtener_contexto_agente_detallado(agente_id: str) -> Dict[str, Any]:
    """
    Obtiene el contexto requerido por un agente específico.
    Incluye campos obligatorios, deseables y output esperado.
    """
    agente_upper = agente_id.upper()
    if agente_upper not in CONTEXTO_POR_AGENTE:
        raise HTTPException(
            status_code=404, 
            detail=f"Agente {agente_id} no encontrado"
        )
    
    return obtener_resumen_contexto_agente(agente_upper)
