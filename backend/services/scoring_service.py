"""
Servicio de Scoring - Revisar.IA
Persiste risk score por pilar después de deliberación de A3_FISCAL
"""
from typing import Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


async def actualizar_risk_score_proyecto(
    proyecto_id: str,
    risk_score_total: int,
    desglose: Dict[str, int],
    db=None
) -> Dict[str, Any]:
    """
    Actualiza el risk score del proyecto después de deliberación de A3_FISCAL.
    """
    update_data = {
        "risk_score_total": risk_score_total,
        "risk_score_razon_negocios": desglose.get("razon_negocios", 0),
        "risk_score_beneficio_economico": desglose.get("beneficio_economico", 0),
        "risk_score_materialidad": desglose.get("materialidad", 0),
        "risk_score_trazabilidad": desglose.get("trazabilidad", 0),
        "risk_score_updated_at": datetime.utcnow().isoformat()
    }
    
    logger.info(
        f"Risk score actualizado para {proyecto_id}: "
        f"Total={risk_score_total}, "
        f"RN={desglose.get('razon_negocios')}, "
        f"BE={desglose.get('beneficio_economico')}, "
        f"MA={desglose.get('materialidad')}, "
        f"TR={desglose.get('trazabilidad')}"
    )
    
    return update_data


def extraer_risk_score_de_a3(output_dict: Dict[str, Any]) -> tuple:
    """Extrae risk score total y desglose del output de A3_FISCAL"""
    risk_total = output_dict.get("risk_score_total", 0)
    conclusion_pilares = output_dict.get("conclusion_por_pilar", {})
    
    desglose = {
        "razon_negocios": conclusion_pilares.get("razon_negocios", {}).get("riesgo_puntos", 0),
        "beneficio_economico": conclusion_pilares.get("beneficio_economico", {}).get("riesgo_puntos", 0),
        "materialidad": conclusion_pilares.get("materialidad", {}).get("riesgo_puntos", 0),
        "trazabilidad": conclusion_pilares.get("trazabilidad", {}).get("riesgo_puntos", 0)
    }
    
    return risk_total, desglose
