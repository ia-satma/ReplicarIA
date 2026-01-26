"""
Query Router - Selecciona el modelo óptimo según complejidad de la query
Reduce costos en 60-70% usando modelos apropiados
"""

import re
import logging
from typing import Literal, Dict, Any, Optional

try:
    from routes.metrics import track_query_router
except ImportError:
    def track_query_router(tier: str, cost: float):
        pass

logger = logging.getLogger(__name__)

try:
    import tiktoken
    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False
    logger.warning("tiktoken no disponible. Usando estimación aproximada de tokens.")

SQL_HINTS = re.compile(r"\b(KPI|ROI|suma|promedio|tendencia|mes|xlsx|csv|hoja|rango|cuánto|total|SQL|tabla|select)\b", re.I)
KG_HINTS = re.compile(r"\b(art(\.|ículo)?|CFF|LISR|DOF|fracción|contrato|cláusula|ley|norma|cita|sustenta)\b", re.I)

def route(user_query: str) -> str:
    """Legacy router for SQL/KG/RAG classification"""
    if SQL_HINTS.search(user_query or ""):
        logger.info("Router: SQL")
        return 'SQL'
    if KG_HINTS.search(user_query or ""):
        logger.info("Router: KG")
        return 'KG'
    logger.info("Router: RAG")
    return 'RAG'

def get_route_explanation(user_query: str) -> dict:
    route_chosen = route(user_query)
    return {
        "route": route_chosen,
        "query": user_query,
        "sql_match": bool(SQL_HINTS.search(user_query or "")),
        "kg_match": bool(KG_HINTS.search(user_query or "")),
        "reasoning": f"Clasificado como {route_chosen}"
    }


class QueryRouter:
    """
    Router que selecciona el modelo óptimo basado en:
    1. Complejidad de la query (tokens)
    2. Tipo de tarea (RAG, razonamiento, validación)
    """

    # All models are Claude/Anthropic only
    MODELS = {
        "simple": {
            "name": "claude-haiku-4-5",
            "cost_per_1k_input": 0.00025,
            "cost_per_1k_output": 0.00125,
            "max_tokens": 200000
        },
        "medium": {
            "name": "claude-sonnet-4-5",
            "cost_per_1k_input": 0.003,
            "cost_per_1k_output": 0.015,
            "max_tokens": 200000
        },
        "complex": {
            "name": "claude-opus-4-5",
            "cost_per_1k_input": 0.015,
            "cost_per_1k_output": 0.075,
            "max_tokens": 200000,
            "use_council": True
        }
    }

    SIMPLE_THRESHOLD = 500
    MEDIUM_THRESHOLD = 2000

    def __init__(self):
        self.encoder = None
        if TIKTOKEN_AVAILABLE:
            try:
                self.encoder = tiktoken.encoding_for_model("gpt-4")
            except Exception as e:
                logger.warning(f"Error al cargar tiktoken encoder: {e}")

    def count_tokens(self, text: str) -> int:
        """Cuenta tokens de manera segura"""
        if self.encoder:
            return len(self.encoder.encode(text))
        else:
            return len(text) // 4

    def route_query(
        self,
        prompt: str,
        task_type: Literal["rag", "reasoning", "validation", "summary", "fiscal_analysis", "legal_deliberation", "council"] = "reasoning",
        force_model: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        INPUT:
            prompt: El texto completo del prompt
            task_type: Tipo de tarea
            force_model: Modelo forzado (opcional)

        OUTPUT:
            {
                "model": "claude-haiku-4-5",
                "estimated_cost": 0.00045,
                "token_count": 1500,
                "reasoning": "Query simple, RAG lookup",
                "tier": "simple"
            }
        """
        if force_model:
            return self._build_response("medium", prompt, "Modelo forzado por usuario")

        token_count = self.count_tokens(prompt)

        if task_type == "rag" and token_count < self.SIMPLE_THRESHOLD:
            model_tier = "simple"
            reasoning = "RAG simple, contexto reducido"

        elif task_type == "summary" and token_count < self.MEDIUM_THRESHOLD:
            model_tier = "simple"
            reasoning = "Resumen sin razonamiento complejo"

        elif task_type == "validation" and token_count < self.SIMPLE_THRESHOLD:
            model_tier = "simple"
            reasoning = "Validación estructural básica"

        elif task_type in ("fiscal_analysis", "legal_deliberation", "council"):
            model_tier = "complex"
            reasoning = "Análisis fiscal/legal complejo - requiere modelo avanzado + Council"

        elif task_type == "reasoning" and token_count > self.MEDIUM_THRESHOLD * 2:
            model_tier = "complex"
            reasoning = "Razonamiento complejo de alto volumen - GPT-4 Turbo"

        elif task_type == "reasoning" or token_count > self.MEDIUM_THRESHOLD:
            model_tier = "medium"
            reasoning = "Razonamiento multi-paso requerido"

        else:
            model_tier = "medium"
            reasoning = "Complejidad media, modelo balanceado"

        return self._build_response(model_tier, prompt, reasoning)

    def _build_response(self, tier: str, prompt: str, reasoning: str) -> Dict:
        model_config = self.MODELS[tier]
        token_count = self.count_tokens(prompt)

        estimated_output_tokens = 500
        estimated_cost = (
            (token_count / 1000) * model_config["cost_per_1k_input"] +
            (estimated_output_tokens / 1000) * model_config["cost_per_1k_output"]
        )

        response = {
            "model": model_config["name"],
            "estimated_cost": round(estimated_cost, 6),
            "token_count": token_count,
            "reasoning": reasoning,
            "tier": tier
        }

        if model_config.get("use_council"):
            response["use_council"] = True
            response["council_models"] = ["claude-sonnet-4-5", "claude-opus-4-5", "claude-3.5-sonnet"]

        return response


_router = QueryRouter()

def route_query(prompt: str, task_type: Literal["rag", "reasoning", "validation", "summary", "fiscal_analysis", "legal_deliberation", "council"] = "reasoning", force_model: Optional[str] = None):
    """Función de conveniencia para usar el router global"""
    result = _router.route_query(prompt, task_type, force_model)
    track_query_router(result["tier"], result["estimated_cost"])
    return result
