"""
Deliberation Service - Servicio de deliberación multi-agente para Revisar.IA
Coordina consenso entre agentes A1, A3, A4, A5, A6 para evaluación de proyectos
"""
import os
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

try:
    from services.agent_service import agent_service, ANTHROPIC_FALLBACK
except ImportError:
    agent_service = None
    ANTHROPIC_FALLBACK = False
    logger.warning("agent_service not available for deliberation")


class DeliberationService:
    
    def __init__(self):
        self.agent_order = ["A6_PROVEEDOR", "A3_FISCAL", "A5_FINANZAS", "A4_LEGAL", "A1_ESTRATEGIA"]
        self._configured = ANTHROPIC_FALLBACK
        
    def is_available(self) -> bool:
        return self._configured
    
    async def deliberate(
        self,
        proyecto_id: str,
        agent_inputs: Dict[str, Dict],
        max_rounds: int = 2
    ) -> Dict[str, Any]:
        """
        Ejecuta deliberación multi-agente
        
        Args:
            proyecto_id: ID del proyecto
            agent_inputs: Dict con entradas por agente {agent_id: {analysis: str, score: int}}
            max_rounds: Número máximo de rondas de deliberación
            
        Returns:
            Dict con resultado de deliberación incluyendo consenso y dictamen
        """
        if not self._configured:
            logger.info(f"📋 [DEMO] Deliberación simulada para proyecto {proyecto_id}")
            return self._demo_deliberation(proyecto_id, agent_inputs)
        
        try:
            deliberation_history = []
            current_round = 1
            consensus_reached = False
            
            while current_round <= max_rounds and not consensus_reached:
                logger.info(f"--- Ronda de deliberación {current_round}/{max_rounds} ---")
                
                round_responses = {}
                
                for agent_id in self.agent_order:
                    if agent_id not in agent_inputs:
                        continue
                    
                    agent_response = await self._get_agent_opinion(
                        agent_id=agent_id,
                        proyecto_id=proyecto_id,
                        agent_input=agent_inputs.get(agent_id, {}),
                        previous_opinions=round_responses,
                        round_number=current_round
                    )
                    
                    round_responses[agent_id] = agent_response
                
                deliberation_history.append({
                    "round": current_round,
                    "responses": round_responses,
                    "timestamp": datetime.utcnow().isoformat()
                })
                
                consensus_reached = self._check_consensus(round_responses)
                current_round += 1
            
            final_dictamen = self._consolidate_dictamen(deliberation_history, agent_inputs)
            
            return {
                "success": True,
                "proyecto_id": proyecto_id,
                "consenso": consensus_reached,
                "rondas": len(deliberation_history),
                "dictamen": final_dictamen,
                "history": deliberation_history,
                "simulado": False,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error en deliberación: {e}")
            return self._demo_deliberation(proyecto_id, agent_inputs)
    
    async def _get_agent_opinion(
        self,
        agent_id: str,
        proyecto_id: str,
        agent_input: Dict,
        previous_opinions: Dict,
        round_number: int
    ) -> Dict[str, Any]:
        """Obtiene opinión de un agente considerando opiniones previas"""
        
        context_parts = [
            f"Proyecto ID: {proyecto_id}",
            f"Ronda de deliberación: {round_number}",
            f"Tu análisis previo: {agent_input.get('analysis', 'N/A')[:500]}",
            f"Tu puntuación: {agent_input.get('score', 'N/A')}",
        ]
        
        if previous_opinions:
            context_parts.append("\nOpiniones de otros agentes en esta ronda:")
            for other_agent, opinion in previous_opinions.items():
                context_parts.append(f"- {other_agent}: {opinion.get('resumen', 'N/A')[:200]}")
        
        context = "\n".join(context_parts)
        
        query = """
        Basándote en tu análisis previo y las opiniones de otros agentes, proporciona:
        1. Tu dictamen actualizado (APROBAR, CONDICIONAR, RECHAZAR)
        2. Resumen de tu posición (max 100 palabras)
        3. Condiciones o riesgos identificados
        4. ¿Estás de acuerdo con el consenso emergente?
        
        Responde en formato estructurado.
        """
        
        try:
            if agent_service:
                result = await agent_service.execute_agent(agent_id, {"context": context, "query": query})
                analysis = result.get("analysis", "")
                
                return {
                    "dictamen": self._extract_dictamen(analysis),
                    "resumen": analysis[:300],
                    "de_acuerdo": "sí" in analysis.lower() or "de acuerdo" in analysis.lower(),
                    "score": agent_input.get("score", 75)
                }
        except Exception as e:
            logger.error(f"Error getting opinion from {agent_id}: {e}")
        
        return {
            "dictamen": "CONDICIONAR",
            "resumen": f"Análisis de {agent_id} pendiente",
            "de_acuerdo": True,
            "score": agent_input.get("score", 75)
        }
    
    def _extract_dictamen(self, analysis: str) -> str:
        """Extrae el dictamen del análisis"""
        analysis_lower = analysis.lower()
        
        if "rechazar" in analysis_lower or "no procede" in analysis_lower:
            return "RECHAZAR"
        elif "condicionar" in analysis_lower or "con reservas" in analysis_lower:
            return "CONDICIONAR"
        elif "aprobar" in analysis_lower or "procede" in analysis_lower:
            return "APROBAR"
        
        return "CONDICIONAR"
    
    def _check_consensus(self, responses: Dict) -> bool:
        """Verifica si hay consenso entre agentes"""
        if len(responses) < 2:
            return False
        
        dictamenes = [r.get("dictamen", "CONDICIONAR") for r in responses.values()]
        
        dictamen_count = {}
        for d in dictamenes:
            dictamen_count[d] = dictamen_count.get(d, 0) + 1
        
        max_count = max(dictamen_count.values())
        return max_count >= len(dictamenes) * 0.6
    
    def _consolidate_dictamen(self, history: List[Dict], inputs: Dict) -> Dict[str, Any]:
        """Consolida el dictamen final basado en el historial de deliberación"""
        
        scores = []
        dictamenes = []
        
        for agent_id, data in inputs.items():
            if "score" in data:
                scores.append(data["score"])
        
        if history:
            last_round = history[-1].get("responses", {})
            for agent_id, response in last_round.items():
                dictamenes.append(response.get("dictamen", "CONDICIONAR"))
        
        avg_score = sum(scores) / len(scores) if scores else 75
        
        if avg_score >= 80 and dictamenes.count("RECHAZAR") == 0:
            dictamen_final = "APROBAR"
        elif avg_score < 50 or dictamenes.count("RECHAZAR") > len(dictamenes) * 0.3:
            dictamen_final = "RECHAZAR"
        else:
            dictamen_final = "CONDICIONAR"
        
        return {
            "dictamen": dictamen_final,
            "score_promedio": round(avg_score, 2),
            "votos": {
                "aprobar": dictamenes.count("APROBAR"),
                "condicionar": dictamenes.count("CONDICIONAR"),
                "rechazar": dictamenes.count("RECHAZAR")
            },
            "materialidad": round(avg_score, 0),
            "fecha": datetime.utcnow().isoformat()
        }
    
    def _demo_deliberation(self, proyecto_id: str, agent_inputs: Dict) -> Dict[str, Any]:
        """Genera deliberación demo cuando no hay LLM disponible"""
        
        scores = []
        for agent_id, data in agent_inputs.items():
            if "score" in data:
                scores.append(data.get("score", 75))
        
        avg_score = sum(scores) / len(scores) if scores else 75
        
        return {
            "success": True,
            "proyecto_id": proyecto_id,
            "consenso": True,
            "rondas": 1,
            "dictamen": {
                "dictamen": "CONDICIONAR",
                "score_promedio": avg_score,
                "votos": {
                    "aprobar": len(agent_inputs) - 1,
                    "condicionar": 1,
                    "rechazar": 0
                },
                "materialidad": round(avg_score, 0),
                "fecha": datetime.utcnow().isoformat()
            },
            "history": [],
            "simulado": True,
            "timestamp": datetime.utcnow().isoformat()
        }


deliberation_service = DeliberationService()


async def deliberate(proyecto_id: str, agent_inputs: Dict) -> Dict[str, Any]:
    """Función wrapper para deliberación"""
    return await deliberation_service.deliberate(proyecto_id, agent_inputs)
