"""
Servicio para preparar el contexto que se envía a cada agente.
Filtra y estructura los datos según lo que cada agente necesita.
"""

from typing import Dict, Optional, List
from datetime import datetime
import logging

from config.contexto_requerido import (
    get_contexto_requerido,
    get_campos_obligatorios,
    get_campos_deseables,
    validar_contexto_completo
)

logger = logging.getLogger(__name__)


class ContextoIncompleto(Exception):
    """Excepción cuando faltan campos obligatorios"""
    def __init__(self, agente_id: str, campos_faltantes: list):
        self.agente_id = agente_id
        self.campos_faltantes = campos_faltantes
        super().__init__(
            f"Contexto incompleto para {agente_id}. "
            f"Faltan: {', '.join(campos_faltantes)}"
        )


async def preparar_contexto_para_agente(
    agente_id: str,
    proyecto: Dict,
    proveedor: Optional[Dict] = None,
    empresa: Optional[Dict] = None,
    documentos: Optional[Dict] = None,
    deliberaciones: Optional[list] = None,
    extras: Optional[Dict] = None,
    validar_obligatorios: bool = True
) -> Dict:
    """
    Prepara el contexto filtrado para un agente específico.
    
    Args:
        agente_id: ID del agente (A1_SPONSOR, A3_FISCAL, etc.)
        proyecto: Datos del proyecto
        proveedor: Datos del proveedor (opcional)
        empresa: Datos de la empresa (opcional)
        documentos: Diccionario de documentos (opcional)
        deliberaciones: Lista de deliberaciones previas (opcional)
        extras: Campos adicionales (opcional)
        validar_obligatorios: Si True, lanza excepción si faltan obligatorios
    
    Returns:
        Diccionario con contexto filtrado para el agente
    
    Raises:
        ContextoIncompleto si validar_obligatorios=True y faltan campos
    """
    
    config = get_contexto_requerido(agente_id)
    if not config:
        logger.warning(f"No hay configuración de contexto para {agente_id}")
        return {}
    
    contexto = {
        "proyecto": proyecto or {},
        "proveedor": proveedor or {},
        "empresa": empresa or {},
        "documentos": documentos or {},
        "deliberaciones": deliberaciones or [],
        **(extras or {})
    }
    
    if validar_obligatorios:
        validacion = validar_contexto_completo(agente_id, contexto)
        
        if not validacion["completo"]:
            logger.error(
                f"Contexto incompleto para {agente_id}: "
                f"faltan {validacion['campos_faltantes']}"
            )
            raise ContextoIncompleto(agente_id, validacion["campos_faltantes"])
    
    campos_relevantes = (
        get_campos_obligatorios(agente_id) + 
        get_campos_deseables(agente_id)
    )
    
    contexto_filtrado = _filtrar_contexto(contexto, campos_relevantes)
    
    contexto_filtrado["_meta"] = {
        "agente_id": agente_id,
        "campos_incluidos": list(contexto_filtrado.keys()),
        "timestamp": datetime.utcnow().isoformat()
    }
    
    logger.info(
        f"Contexto preparado para {agente_id}: "
        f"{len(contexto_filtrado)} campos"
    )
    
    return contexto_filtrado


def _filtrar_contexto(contexto: Dict, campos: list) -> Dict:
    """Filtra el contexto para incluir solo los campos especificados"""
    resultado = {}
    
    for campo in campos:
        partes = campo.split('.')
        
        valor = contexto
        for parte in partes:
            if isinstance(valor, dict) and parte in valor:
                valor = valor[parte]
            else:
                valor = None
                break
        
        if valor is not None:
            actual = resultado
            for i, parte in enumerate(partes[:-1]):
                if parte not in actual:
                    actual[parte] = {}
                actual = actual[parte]
            actual[partes[-1]] = valor
    
    return resultado


def obtener_resumen_contexto_agente(agente_id: str) -> Dict:
    """Retorna resumen de qué contexto necesita un agente"""
    config = get_contexto_requerido(agente_id)
    
    return {
        "agente_id": agente_id,
        "descripcion": config.get("descripcion", ""),
        "campos_obligatorios": config.get("contexto_requerido", {}).get("obligatorio", []),
        "campos_deseables": config.get("contexto_requerido", {}).get("deseable", []),
        "campos_no_necesita": config.get("contexto_requerido", {}).get("no_necesita", []),
        "output_esperado": config.get("output_esperado", [])
    }


def listar_todos_agentes_contexto() -> List[Dict]:
    """Lista el contexto requerido de todos los agentes"""
    from config.contexto_requerido import CONTEXTO_POR_AGENTE
    
    return [
        obtener_resumen_contexto_agente(agente_id)
        for agente_id in CONTEXTO_POR_AGENTE.keys()
    ]
