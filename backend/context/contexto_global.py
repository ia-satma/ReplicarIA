"""
Contexto Global Unificado - Revisar.IA
Sistema de Auditoría de Intangibles

Este módulo unifica todo el contexto que los agentes necesitan:
- Normativa fiscal mexicana
- Tipologías de servicio
- Umbrales de revisión humana
- POE de fases F0-F9

Es el "cerebro" del sistema que todos los agentes compartirán.
"""

from typing import Dict, List, Any, Optional

from .contexto_normativo_fiscal import (
    CONTEXTO_NORMATIVO,
    obtener_normativa,
    obtener_criterios_evaluacion,
    obtener_normativa_por_pilar
)

from .tipologias_servicio import (
    TIPOLOGIAS_SERVICIO,
    obtener_tipologia,
    obtener_riesgo_inherente,
    requiere_revision_humana_por_tipologia,
    obtener_documentos_tipicos,
    obtener_alertas_especiales,
    listar_tipologias,
    obtener_tipologias_alto_riesgo
)

from .umbrales_revision import (
    UMBRALES_REVISION_HUMANA,
    ResultadoRevision,
    requiere_revision_humana,
    es_fase_critica,
    obtener_umbral_monto,
    obtener_umbral_risk_score,
    obtener_tipologias_siempre_humano,
    clasificar_por_risk_score
)

from .poe_fases import (
    POE_FASES,
    obtener_config_fase,
    es_candado_duro,
    get_bloqueos_fase,
    get_agentes_obligatorios,
    get_documentos_minimos,
    get_condicion_avance,
    listar_fases,
    get_candados_duros,
    get_fase_siguiente,
    get_fase_anterior
)


CONTEXTO_GLOBAL: Dict[str, Any] = {
    "normativo": CONTEXTO_NORMATIVO,
    "tipologias": TIPOLOGIAS_SERVICIO,
    "umbrales": UMBRALES_REVISION_HUMANA,
    "poe": POE_FASES
}


class ContextoGlobalService:
    """
    Servicio centralizado para acceder al contexto global del sistema.
    Proporciona métodos convenientes para consultar normativa, tipologías,
    umbrales y configuración de fases.
    """
    
    @staticmethod
    def get_contexto_completo() -> Dict[str, Any]:
        """Obtiene todo el contexto global."""
        return CONTEXTO_GLOBAL
    
    @staticmethod
    def get_normativa(ley: str = None, articulo: str = None) -> Any:
        """Obtiene normativa fiscal."""
        if ley is None:
            return CONTEXTO_NORMATIVO
        return obtener_normativa(ley, articulo)
    
    @staticmethod
    def get_criterios_pilar(pilar: str) -> Dict[str, Any]:
        """Obtiene normativa aplicable a un pilar específico."""
        return obtener_normativa_por_pilar(pilar)
    
    @staticmethod
    def get_tipologia(codigo: str) -> Optional[Dict[str, Any]]:
        """Obtiene configuración de una tipología."""
        return obtener_tipologia(codigo)
    
    @staticmethod
    def get_config_fase(fase: str) -> Optional[Dict[str, Any]]:
        """Obtiene configuración de una fase."""
        return obtener_config_fase(fase)
    
    @staticmethod
    def evaluar_revision_humana(
        proyecto: Dict[str, Any],
        risk_score: float,
        proveedor: Dict[str, Any]
    ) -> ResultadoRevision:
        """Evalúa si se requiere revisión humana."""
        return requiere_revision_humana(proyecto, risk_score, proveedor)
    
    @staticmethod
    def get_contexto_para_agente(
        agente: str,
        fase: str,
        tipologia: str = None
    ) -> Dict[str, Any]:
        """
        Construye el contexto específico que un agente necesita para una fase.
        
        Args:
            agente: Código del agente (A1_SPONSOR, A3_FISCAL, etc.)
            fase: Fase actual (F0, F1, etc.)
            tipologia: Tipología del proyecto (opcional)
        
        Returns:
            Diccionario con el contexto relevante para ese agente/fase
        """
        contexto = {
            "fase": obtener_config_fase(fase),
            "agentes_requeridos": get_agentes_obligatorios(fase),
            "documentos_minimos": get_documentos_minimos(fase),
            "condicion_avance": get_condicion_avance(fase),
            "bloqueos_posibles": get_bloqueos_fase(fase),
            "es_candado_duro": es_candado_duro(fase),
            "umbrales": UMBRALES_REVISION_HUMANA
        }
        
        if tipologia:
            contexto["tipologia"] = obtener_tipologia(tipologia)
            contexto["documentos_tipicos"] = obtener_documentos_tipicos(tipologia)
            contexto["alertas_especiales"] = obtener_alertas_especiales(tipologia)
        
        mapeo_agente_normativa = {
            "A1_SPONSOR": ["CFF_5A", "LISR_27"],
            "A3_FISCAL": ["CFF_5A", "CFF_69B", "LISR_27", "LISR_28", "RMF"],
            "A4_LEGAL": ["NOM_151", "CONTRATOS"],
            "A5_FINANZAS": ["LISR_27", "RMF_TP"],
            "A6_PROVEEDOR": ["CFF_69B", "EFOS"],
            "A7_DEFENSA": ["CFF_5A", "CFF_42", "CFF_69B", "LISR_27"],
            "SUB_TIPIFICACION": [],
            "SUB_MATERIALIDAD": ["CFF_5A", "CFF_69B", "NOM_151"],
            "SUB_RIESGOS_ESPECIALES": ["LISR_76", "LISR_179", "LISR_180", "RMF_TP"]
        }
        
        normativa_relevante = mapeo_agente_normativa.get(agente, [])
        contexto["normativa_aplicable"] = {}
        
        for ref in normativa_relevante:
            if ref.startswith("CFF_"):
                articulo = "articulo_" + ref.split("_")[1]
                norm = obtener_normativa("CFF", articulo)
                if norm:
                    contexto["normativa_aplicable"][ref] = norm
            elif ref.startswith("LISR_"):
                articulo = "articulo_" + ref.split("_")[1]
                norm = obtener_normativa("LISR", articulo)
                if norm:
                    contexto["normativa_aplicable"][ref] = norm
            elif ref == "NOM_151":
                contexto["normativa_aplicable"]["NOM_151"] = CONTEXTO_NORMATIVO.get("NOM_151")
            elif ref.startswith("RMF"):
                contexto["normativa_aplicable"]["RMF"] = CONTEXTO_NORMATIVO.get("RMF")
        
        return contexto
    
    @staticmethod
    def validar_documentos_fase(
        fase: str,
        documentos_presentes: List[str]
    ) -> Dict[str, Any]:
        """
        Valida si los documentos presentes cumplen con los mínimos de la fase.
        
        Returns:
            Dict con: completo (bool), faltantes (list), porcentaje (float)
        """
        docs_minimos = get_documentos_minimos(fase)
        obligatorios = [d for d in docs_minimos if d.get("obligatorio", False)]
        
        faltantes = []
        for doc in obligatorios:
            tipo = doc.get("tipo_documento", doc.get("nombre", ""))
            if tipo not in documentos_presentes:
                faltantes.append(doc["nombre"])
        
        total_obligatorios = len(obligatorios)
        cumplidos = total_obligatorios - len(faltantes)
        porcentaje = (cumplidos / total_obligatorios * 100) if total_obligatorios > 0 else 100
        
        return {
            "completo": len(faltantes) == 0,
            "faltantes": faltantes,
            "porcentaje": porcentaje,
            "cumplidos": cumplidos,
            "total_obligatorios": total_obligatorios
        }
    
    @staticmethod
    def puede_avanzar_fase(
        fase_actual: str,
        deliberaciones_agentes: Dict[str, str],
        documentos_presentes: List[str]
    ) -> Dict[str, Any]:
        """
        Evalúa si un proyecto puede avanzar de fase.
        
        Args:
            fase_actual: Fase actual del proyecto
            deliberaciones_agentes: Dict {agente: decision} (APROBAR, RECHAZAR, etc.)
            documentos_presentes: Lista de tipos de documentos presentes
        
        Returns:
            Dict con: puede_avanzar (bool), razones_bloqueo (list)
        """
        config = obtener_config_fase(fase_actual)
        if not config:
            return {"puede_avanzar": False, "razones_bloqueo": ["Fase no válida"]}
        
        razones_bloqueo = []
        
        agentes_obligatorios = config.get("agentes_obligatorios", [])
        for agente in agentes_obligatorios:
            if agente not in deliberaciones_agentes:
                razones_bloqueo.append(f"Falta deliberación de {agente}")
            elif deliberaciones_agentes[agente] == "RECHAZAR":
                razones_bloqueo.append(f"{agente} ha rechazado el proyecto")
        
        validacion_docs = ContextoGlobalService.validar_documentos_fase(fase_actual, documentos_presentes)
        if not validacion_docs["completo"]:
            for doc in validacion_docs["faltantes"]:
                razones_bloqueo.append(f"Documento faltante: {doc}")
        
        return {
            "puede_avanzar": len(razones_bloqueo) == 0,
            "razones_bloqueo": razones_bloqueo,
            "fase_siguiente": get_fase_siguiente(fase_actual) if len(razones_bloqueo) == 0 else None
        }


contexto_service = ContextoGlobalService()
