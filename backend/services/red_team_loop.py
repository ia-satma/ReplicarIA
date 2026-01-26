"""
RED TEAM SIMULATOR LOOP
Simula ataques del SAT al expediente para encontrar vulnerabilidades
Itera hasta que no encuentre nuevas vulnerabilidades
"""

import os
import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field

from services.loop_orchestrator import LoopOrchestrator, LoopResult

logger = logging.getLogger(__name__)

ATTACK_VECTORS = [
    {
        "id": "ART_5A_RAZON_NEGOCIOS",
        "name": "Cuestionamiento de Razón de Negocios (Art. 5-A CFF)",
        "prompts": [
            "¿Cuál es la justificación económica real más allá del beneficio fiscal?",
            "¿Existe un objetivo de negocio cuantificable y verificable?",
            "¿El servicio es necesario para la operación o es artificialmente creado?"
        ]
    },
    {
        "id": "ART_69B_SIMULACION",
        "name": "Detección de Operaciones Simuladas (Art. 69-B CFF)",
        "prompts": [
            "¿El proveedor tiene capacidad material para prestar el servicio?",
            "¿Existe evidencia de que el servicio realmente se prestó?",
            "¿Los precios son congruentes con el mercado?"
        ]
    },
    {
        "id": "MATERIALIDAD",
        "name": "Cuestionamiento de Materialidad",
        "prompts": [
            "¿Hay entregables tangibles y verificables?",
            "¿Se puede demostrar el uso/consumo del servicio?",
            "¿Existe trazabilidad del beneficio obtenido?"
        ]
    },
    {
        "id": "DOCUMENTAL",
        "name": "Inconsistencias Documentales",
        "prompts": [
            "¿Las fechas de los documentos son congruentes entre sí?",
            "¿Los montos coinciden entre contrato, factura y pago?",
            "¿Hay documentos faltantes en la cadena de evidencia?"
        ]
    },
    {
        "id": "PRECIOS_TRANSFERENCIA",
        "name": "Precios de Transferencia",
        "prompts": [
            "¿El precio es arm's length (independiente)?",
            "¿Existe estudio de precios de transferencia?",
            "¿Se usó metodología reconocida por la OCDE?"
        ]
    },
    {
        "id": "SUSTANCIA_ECONOMICA",
        "name": "Sustancia sobre Forma",
        "prompts": [
            "¿La operación tiene sustancia económica real?",
            "¿Se busca únicamente un beneficio fiscal?",
            "¿El flujo de dinero tiene sentido de negocios?"
        ]
    },
    {
        "id": "CAPACIDAD_PROVEEDOR",
        "name": "Capacidad del Proveedor",
        "prompts": [
            "¿El proveedor tiene infraestructura para el servicio?",
            "¿Tiene personal calificado documentado?",
            "¿Tiene historial de servicios similares?"
        ]
    }
]

SEVERITY_ORDER = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}


@dataclass
class Vulnerability:
    id: str
    severity: str
    description: str
    vector_id: str
    vector_name: str
    articulo_aplicable: str = ""
    evidencia_faltante: str = ""
    recommendation: str = ""


@dataclass
class RedTeamReport:
    project_id: str
    fecha: str
    total_iteraciones: int
    vectores_testeados: int
    vulnerabilidades_encontradas: int
    nivel_riesgo: str
    vulnerabilidades: List[Vulnerability]
    recomendaciones: List[Dict[str, Any]]
    conclusion: str
    bulletproof: bool


class RedTeamLoop:
    """
    Simulador Red Team para expedientes fiscales
    Simula ataques del SAT para encontrar vulnerabilidades
    """
    
    def __init__(self):
        self.orchestrator = LoopOrchestrator(
            max_iterations=10,
            timeout_seconds=600,
            completion_marker="BULLETPROOF",
            delay_between_iterations=1.0
        )
        self.attack_vectors = ATTACK_VECTORS
    
    async def simulate_attack(
        self,
        project_id: str,
        project_data: Dict[str, Any]
    ) -> RedTeamReport:
        """
        Ejecuta simulación Red Team sobre un proyecto
        
        Args:
            project_id: ID del proyecto
            project_data: Datos del proyecto a analizar
        """
        context = {
            "project_id": project_id,
            "project_data": project_data,
            "attacked_vectors": [],
            "vulnerabilities": [],
            "consecutive_no_findings": 0
        }
        
        result = await self.orchestrator.execute_loop(
            self._red_team_task,
            context,
            task_name=f"Red Team Attack: {project_id}"
        )
        
        report = self._generate_report(project_id, result)
        return report
    
    async def _red_team_task(self, context: Dict, iteration: int) -> Dict[str, Any]:
        """Tarea de ataque Red Team (cada iteración)"""
        project_data = context["project_data"]
        attacked_vectors = context.get("attacked_vectors", [])
        vulnerabilities = context.get("vulnerabilities", [])
        consecutive_no_findings = context.get("consecutive_no_findings", 0)
        
        available_vectors = [v for v in self.attack_vectors if v["id"] not in attacked_vectors]
        
        if not available_vectors or consecutive_no_findings >= 2:
            return {
                "status": "BULLETPROOF",
                "complete": True,
                "total_vulnerabilities": len(vulnerabilities),
                "tested_vectors": len(attacked_vectors),
                "attacked_vectors": attacked_vectors,
                "vulnerabilities": vulnerabilities,
                "message": "Expediente resistió todos los vectores de ataque" if not vulnerabilities
                          else f"Se encontraron {len(vulnerabilities)} vulnerabilidades documentadas"
            }
        
        current_vector = available_vectors[0]
        logger.info(f"[RedTeam] Iteración {iteration}: Atacando con {current_vector['name']}")
        
        attack_result = await self._execute_attack_vector(current_vector, project_data)
        
        new_vulnerabilities = attack_result.get("vulnerabilities", [])
        
        if not new_vulnerabilities:
            return {
                "status": "CONTINUE",
                "attacked_vectors": attacked_vectors + [current_vector["id"]],
                "vulnerabilities": vulnerabilities,
                "consecutive_no_findings": consecutive_no_findings + 1,
                "findings": [{
                    "type": "VECTOR_PASSED",
                    "severity": "INFO",
                    "vector": current_vector["id"],
                    "message": f"Vector {current_vector['name']}: Sin vulnerabilidades detectadas"
                }]
            }
        
        formatted_vulns = [
            {
                **v,
                "vector_id": current_vector["id"],
                "vector_name": current_vector["name"]
            }
            for v in new_vulnerabilities
        ]
        
        return {
            "status": "CONTINUE",
            "attacked_vectors": attacked_vectors + [current_vector["id"]],
            "vulnerabilities": vulnerabilities + formatted_vulns,
            "consecutive_no_findings": 0,
            "findings": [
                {
                    "type": "VULNERABILITY_FOUND",
                    "severity": v.get("severity", "MEDIUM"),
                    "vector": current_vector["id"],
                    "message": v.get("description", ""),
                    "recommendation": v.get("recommendation", "")
                }
                for v in new_vulnerabilities
            ]
        }
    
    async def _execute_attack_vector(
        self,
        vector: Dict[str, Any],
        project_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Ejecuta un vector de ataque específico usando LLM"""
        
        system_prompt = f"""Eres un auditor fiscal del SAT mexicano con 20 años de experiencia.
Tu trabajo es encontrar TODAS las debilidades en expedientes de deducción de intangibles.
Eres escéptico, meticuloso y conoces todos los trucos que usan los contribuyentes.

REGLAS:
1. Busca inconsistencias, omisiones y debilidades documentales
2. Cuestiona la sustancia económica de cada operación
3. Identifica banderas rojas que justificarían una auditoría profunda
4. Sé específico: cita artículos del CFF, LISR, y criterios normativos
5. Califica la severidad: CRITICAL, HIGH, MEDIUM, LOW

VECTOR DE ATAQUE: {vector['name']}
PREGUNTAS CLAVE: {' | '.join(vector['prompts'])}"""
        
        user_prompt = f"""Analiza este expediente y encuentra vulnerabilidades:

DATOS DEL PROYECTO:
{json.dumps(project_data, indent=2, ensure_ascii=False)}

Responde en JSON:
{{
  "vulnerabilities": [
    {{
      "id": "string",
      "severity": "CRITICAL|HIGH|MEDIUM|LOW",
      "description": "descripción específica",
      "articulo_aplicable": "Art. X del CFF/LISR",
      "evidencia_faltante": "qué falta para defenderse",
      "recommendation": "cómo corregir"
    }}
  ],
  "passed_checks": ["lista de verificaciones que SÍ pasaron"],
  "overall_risk": "CRITICAL|HIGH|MEDIUM|LOW"
}}"""
        
        try:
            from openai import OpenAI

            # Initialize OpenAI with OPENAI_API_KEY
            openai_api_key = os.environ.get('OPENAI_API_KEY')

            if not openai_api_key:
                logger.warning("[RedTeam] No OpenAI credentials - using fallback attack")
                return await self._fallback_attack(vector, project_data)

            client = OpenAI(api_key=openai_api_key)
            logger.info("[RedTeam] Using OpenAI GPT-4o")

            response = client.chat.completions.create(
                model="gpt-4o",
                max_tokens=2000,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt + "\n\nResponde SOLO con JSON válido."}
                ]
            )

            result_text = response.choices[0].message.content if response.choices else "{}"
            # Try to parse JSON from response
            try:
                result = json.loads(result_text)
            except json.JSONDecodeError:
                # Try to extract JSON from the response
                import re
                json_match = re.search(r'\{[\s\S]*\}', result_text)
                if json_match:
                    result = json.loads(json_match.group())
                else:
                    result = {"vulnerabilities": [], "passed_checks": [], "overall_risk": "LOW"}
            return result

        except Exception as e:
            logger.error(f"[RedTeam] Error en ataque LLM (OpenAI): {e}")
            return await self._fallback_attack(vector, project_data)
    
    async def _fallback_attack(
        self,
        vector: Dict[str, Any],
        project_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Análisis de fallback sin LLM basado en reglas"""
        vulnerabilities = []
        
        if vector["id"] == "ART_5A_RAZON_NEGOCIOS":
            if not project_data.get("justificacion_economica"):
                vulnerabilities.append({
                    "id": "RN_001",
                    "severity": "HIGH",
                    "description": "Falta justificación económica documentada",
                    "articulo_aplicable": "Art. 5-A CFF",
                    "recommendation": "Documentar razón de negocios con análisis costo-beneficio"
                })
            if not project_data.get("beneficio_esperado"):
                vulnerabilities.append({
                    "id": "RN_002",
                    "severity": "MEDIUM",
                    "description": "No se especifica el beneficio económico esperado",
                    "articulo_aplicable": "Art. 5-A CFF",
                    "recommendation": "Cuantificar beneficio económico esperado"
                })
        
        elif vector["id"] == "ART_69B_SIMULACION":
            if project_data.get("risk_score", 0) > 50:
                vulnerabilities.append({
                    "id": "SIM_001",
                    "severity": "HIGH",
                    "description": f"Risk score elevado ({project_data.get('risk_score')})",
                    "articulo_aplicable": "Art. 69-B CFF",
                    "recommendation": "Reforzar documentación de materialidad"
                })
        
        elif vector["id"] == "MATERIALIDAD":
            docs = project_data.get("documentos", [])
            if not any(d.get("tipo") == "evidencia" and d.get("validado") for d in docs):
                vulnerabilities.append({
                    "id": "MAT_001",
                    "severity": "CRITICAL",
                    "description": "No hay evidencias validadas del servicio",
                    "articulo_aplicable": "Art. 27 LISR",
                    "recommendation": "Subir y validar evidencias de entrega"
                })
        
        elif vector["id"] == "DOCUMENTAL":
            docs = project_data.get("documentos", [])
            required_docs = ["contrato", "factura", "comprobante_pago"]
            missing = [d for d in required_docs if not any(doc.get("tipo") == d for doc in docs)]
            if missing:
                vulnerabilities.append({
                    "id": "DOC_001",
                    "severity": "HIGH",
                    "description": f"Documentos faltantes: {', '.join(missing)}",
                    "articulo_aplicable": "Art. 29-A CFF",
                    "recommendation": f"Subir documentos: {', '.join(missing)}"
                })
        
        elif vector["id"] == "PRECIOS_TRANSFERENCIA":
            monto = project_data.get("monto_contrato", 0)
            if monto > 1000000 and not project_data.get("estudio_precios_transferencia"):
                vulnerabilities.append({
                    "id": "PT_001",
                    "severity": "MEDIUM",
                    "description": "Operación significativa sin estudio de precios de transferencia",
                    "articulo_aplicable": "Art. 76 y 180 LISR",
                    "recommendation": "Considerar elaborar estudio de PT si aplica"
                })
        
        return {"vulnerabilities": vulnerabilities, "passed_checks": []}
    
    def _generate_report(self, project_id: str, result: LoopResult) -> RedTeamReport:
        """Genera reporte de Red Team"""
        final_result = result.result or {}
        vulnerabilities = final_result.get("vulnerabilities", [])
        
        formatted_vulns = [
            Vulnerability(
                id=v.get("id", f"V{i}"),
                severity=v.get("severity", "MEDIUM"),
                description=v.get("description", ""),
                vector_id=v.get("vector_id", ""),
                vector_name=v.get("vector_name", ""),
                articulo_aplicable=v.get("articulo_aplicable", ""),
                evidencia_faltante=v.get("evidencia_faltante", ""),
                recommendation=v.get("recommendation", "")
            )
            for i, v in enumerate(vulnerabilities)
        ]
        
        nivel_riesgo = self._calculate_overall_risk(vulnerabilities)
        
        recomendaciones = sorted(
            [
                {
                    "prioridad": v.get("severity", "MEDIUM"),
                    "accion": v.get("recommendation", ""),
                    "vector": v.get("vector_id", "")
                }
                for v in vulnerabilities if v.get("recommendation")
            ],
            key=lambda x: SEVERITY_ORDER.get(x["prioridad"], 3)
        )
        
        bulletproof = result.success and nivel_riesgo in ["LOW", "MEDIUM"]
        
        conclusion = (
            "El expediente ha pasado la simulación de auditoría SAT - BULLETPROOF"
            if bulletproof
            else f"Se requieren correcciones. Nivel de riesgo: {nivel_riesgo}"
        )
        
        return RedTeamReport(
            project_id=project_id,
            fecha=datetime.now(timezone.utc).isoformat(),
            total_iteraciones=result.iterations,
            vectores_testeados=len(final_result.get("attacked_vectors", [])),
            vulnerabilidades_encontradas=len(vulnerabilities),
            nivel_riesgo=nivel_riesgo,
            vulnerabilidades=formatted_vulns,
            recomendaciones=recomendaciones,
            conclusion=conclusion,
            bulletproof=bulletproof
        )
    
    def _calculate_overall_risk(self, vulnerabilities: List[Dict]) -> str:
        """Calcula nivel de riesgo general"""
        if any(v.get("severity") == "CRITICAL" for v in vulnerabilities):
            return "CRITICAL"
        high_count = sum(1 for v in vulnerabilities if v.get("severity") == "HIGH")
        if high_count >= 2:
            return "CRITICAL"
        if high_count >= 1:
            return "HIGH"
        if any(v.get("severity") == "MEDIUM" for v in vulnerabilities):
            return "MEDIUM"
        return "LOW"


red_team_loop = RedTeamLoop()
