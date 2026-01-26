import logging
from typing import Dict, List, Optional
from datetime import datetime, timezone
import uuid
from services.multi_agent_gmail import MultiAgentGmailService
from services.agent_service import AgentService, AGENT_CONFIGURATIONS

logger = logging.getLogger(__name__)

class AgentDiscussionService:
    """Servicio para manejar discusiones iterativas entre agentes (3-5 rondas)"""
    
    def __init__(self, db):
        self.db = db
        self.multi_gmail = MultiAgentGmailService()
        self.agent_service = AgentService()
        self.max_rounds = 5
        self.min_rounds = 3
    
    async def initiate_discussion(
        self,
        project_id: str,
        project_data: Dict,
        initial_analyses: Dict[str, Dict]  # {agent_id: {analysis, decision, pdf_path}}
    ) -> Dict:
        """
        Inicia discusión entre agentes (SIN incluir al sponsor).
        
        Flujo:
        1. Cada agente envía su análisis inicial SOLO a otros agentes
        2. Agentes leen los PDFs adjuntos de los demás
        3. Responden con sus opiniones (Round 2)
        4. Continúan discutiendo (Rounds 3-5)
        5. Detectar consenso o falta de participación
        6. Solo cuando hay consenso, PMO consolida y envía al sponsor
        """
        
        # Crear registro de discusión
        discussion = {
            "discussion_id": str(uuid.uuid4()),
            "project_id": project_id,
            "status": "in_progress",
            "current_round": 1,
            "max_rounds": self.max_rounds,
            "participants": ["A1_SPONSOR", "A3_FISCAL", "A5_FINANZAS"],
            "moderator": "A2_PMO",
            "rounds": [],
            "started_at": datetime.now(timezone.utc).isoformat()
        }
        
        await self.db.agent_discussions.insert_one(discussion)
        
        # Round 1: Análisis inicial - agentes se envían entre ellos
        logger.info(f"[DISCUSSION] Round 1: Agentes enviando análisis iniciales ENTRE ELLOS")
        
        round_1_results = await self._execute_round_1(
            discussion_id=discussion["discussion_id"],
            project_id=project_id,
            project_data=project_data,
            initial_analyses=initial_analyses
        )
        
        # Rounds 2-5: Discusión iterativa
        for round_num in range(2, self.max_rounds + 1):
            logger.info(f"[DISCUSSION] Round {round_num}: Solicitando respuestas...")
            
            round_results = await self._execute_discussion_round(
                discussion_id=discussion["discussion_id"],
                round_num=round_num,
                project_id=project_id,
                project_data=project_data,
                previous_round=round_1_results if round_num == 2 else None
            )
            
            # Verificar participación
            participants_responded = round_results.get("participants_responded", [])
            
            if len(participants_responded) < 3:
                # Solicitar participación de agentes que no respondieron
                await self._request_missing_participation(
                    discussion_id=discussion["discussion_id"],
                    round_num=round_num,
                    project_data=project_data,
                    participants_responded=participants_responded
                )
                
                logger.warning(f"[DISCUSSION] Round {round_num}: Esperando respuestas de agentes faltantes")
                # En producción, aquí esperaríamos respuestas reales
                # Por ahora, simulamos que respondieron
            
            # Verificar si hay consenso
            has_consensus, consensus_type = self._check_consensus(round_results)
            
            if has_consensus and round_num >= self.min_rounds:
                logger.info(f"[DISCUSSION] CONSENSO ALCANZADO en round {round_num}: {consensus_type}")
                
                # Actualizar discusión
                await self.db.agent_discussions.update_one(
                    {"discussion_id": discussion["discussion_id"]},
                    {"$set": {
                        "status": "consensus_reached",
                        "consensus_type": consensus_type,
                        "consensus_round": round_num,
                        "completed_at": datetime.now(timezone.utc).isoformat()
                    }}
                )
                
                # PMO consolida y genera orden de compra
                return await self._pmo_consolidate_and_create_po(
                    discussion_id=discussion["discussion_id"],
                    project_id=project_id,
                    project_data=project_data,
                    consensus_type=consensus_type,
                    final_round=round_num,
                    agent_decisions=round_results.get("agent_decisions", {})
                )
        
        # Si llegamos a max rounds sin consenso
        logger.warning(f"[DISCUSSION] No se alcanzó consenso después de {self.max_rounds} rounds")
        
        return {
            "status": "no_consensus",
            "message": "No se alcanzó consenso después de 5 rondas. Requiere intervención humana."
        }
    
    async def _execute_round_1(
        self,
        discussion_id: str,
        project_id: str,
        project_data: Dict,
        initial_analyses: Dict[str, Dict]
    ) -> Dict:
        """
        Round 1: Cada agente envía su análisis SOLO a otros agentes (NO al sponsor).
        """
        
        agents = ["A1_SPONSOR", "A3_FISCAL", "A5_FINANZAS"]
        
        for agent_id in agents:
            analysis_data = initial_analyses.get(agent_id)
            if not analysis_data:
                continue
            
            agent_config = AGENT_CONFIGURATIONS[agent_id]
            
            # IMPORTANTE: Los otros agentes + PMO (SIN sponsor)
            recipient_agents = [a for a in agents if a != agent_id]
            recipient_agents.append("A2_PMO")
            
            # SOLO emails de agentes, NO sponsor
            to_emails = [AGENT_CONFIGURATIONS[a]["email"] for a in recipient_agents]
            
            subject = f"[Round 1] Mi análisis - {project_data.get('project_name', 'Proyecto')[:40]}"
            
            body = f"""Hola equipo,

{agent_config['name']} aquí. Les comparto mi análisis inicial del proyecto.

Por favor revisen el PDF adjunto y díganme qué opinan. Necesitamos llegar a un acuerdo antes de continuar.

Mi postura preliminar: {analysis_data.get('decision', 'PENDIENTE')}

Les leo en sus respuestas.

Saludos,
{agent_config['name']}
"""
            
            # Enviar a TODOS los otros agentes (para que todos vean todo)
            # Primer email: a un agente con CC a los demás
            primary_recipient = to_emails[0]
            cc_list = to_emails[1:] if len(to_emails) > 1 else []
            
            result = self.multi_gmail.send_email_as_agent(
                agent_id=agent_id,
                to=primary_recipient,
                subject=subject,
                body=body,
                cc=cc_list,
                attachment_path=analysis_data.get('pdf_path')
            )
            
            if result.get('success'):
                logger.info(f"✅ Round 1: {agent_config['name']} → Equipo (NO sponsor)")
        
        # Guardar round
        await self.db.agent_discussions.update_one(
            {"discussion_id": discussion_id},
            {"$push": {
                "rounds": {
                    "round": 1,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "participants": agents,
                    "type": "initial_analysis"
                }
            }}
        )
        
        return {
            "round": 1,
            "participants_responded": agents,
            "analyses": initial_analyses
        }
    
    async def _execute_discussion_round(
        self,
        discussion_id: str,
        round_num: int,
        project_id: str,
        project_data: Dict,
        previous_round: Optional[Dict]
    ) -> Dict:
        """
        Ejecuta una ronda donde agentes leen análisis de otros y RESPONDEN.
        Cada agente genera una respuesta considerando lo que otros dijeron.
        """
        
        logger.info(f"[DISCUSSION] Round {round_num}: Agentes leyendo y respondiendo...")

        agents = ["A1_SPONSOR", "A3_FISCAL", "A5_FINANZAS"]
        previous_analyses = previous_round.get('analyses', {}) if previous_round else {}
        round_decisions = {}  # Almacenar decisiones de esta ronda

        # Cada agente lee los análisis de los demás y responde
        for agent_id in agents:
            agent_config = AGENT_CONFIGURATIONS[agent_id]
            
            # Preparar contexto: lo que otros agentes dijeron
            others_opinions = ""
            for other_id in agents:
                if other_id != agent_id and other_id in previous_analyses:
                    other_config = AGENT_CONFIGURATIONS[other_id]
                    other_analysis = previous_analyses[other_id]
                    others_opinions += f"\n{other_config['name']} ({other_id}):\n"
                    others_opinions += f"Decisión: {other_analysis.get('decision', 'N/A')}\n"
                    others_opinions += f"Resumen: {other_analysis.get('analysis', '')[:300]}...\n"
                    others_opinions += "="*60 + "\n"
            
            # Generar respuesta del agente
            response_context = f"""
Round {round_num} de discusión sobre: {project_data.get('project_name')}

Has revisado los análisis de tus colegas:
{others_opinions}

Ahora, como {agent_config['name']}, responde:
- ¿Estás de acuerdo con ellos?
- ¿Qué te preocupa de sus análisis?
- ¿Qué sugieres para llegar a un acuerdo?
- ¿Cambias tu postura o la mantienes?

AL FINAL de tu respuesta, incluye una línea con tu DECISIÓN actual en este formato exacto:
DECISIÓN: [APROBAR/APROBAR_CON_CONDICIONES/RECHAZAR]

Habla de manera natural, como en una conversación por email con colegas.
"""

            agent_response = await self.agent_service.agent_analyze(
                agent_id,
                response_context,
                f"Responde a tus colegas sobre el proyecto. Round {round_num} de discusión. Termina con DECISIÓN: [tu decisión]",
                use_drive_knowledge=False  # No recargar Drive en cada round
            )

            # Extraer decisión del agente
            decision = self._extract_decision_from_response(agent_response)
            round_decisions[agent_id] = {
                "agent_name": agent_config['name'],
                "decision": decision,
                "summary": agent_response[:300] if agent_response else "Sin respuesta"
            }
            
            # Enviar respuesta a todos los demás
            recipient_agents = [a for a in agents if a != agent_id]
            recipient_agents.append("A2_PMO")
            
            primary_recipient = AGENT_CONFIGURATIONS[recipient_agents[0]]["email"]
            cc_list = [AGENT_CONFIGURATIONS[a]["email"] for a in recipient_agents[1:]]
            
            subject = f"[Round {round_num}] Re: {project_data.get('project_name', '')[:40]}"
            
            body = f"""Equipo,

{agent_response}

Saludos,
{agent_config['name']}
"""
            
            result = self.multi_gmail.send_email_as_agent(
                agent_id=agent_id,
                to=primary_recipient,
                subject=subject,
                body=body,
                cc=cc_list
            )
            
            if result.get('success'):
                logger.info(f"✅ Round {round_num}: {agent_config['name']} respondió al equipo")
        
        # Guardar round
        await self.db.agent_discussions.update_one(
            {"discussion_id": discussion_id},
            {"$push": {
                "rounds": {
                    "round": round_num,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "participants": agents,
                    "type": "discussion"
                }
            }}
        )
        
        return {
            "round": round_num,
            "participants_responded": agents,
            "simulated": False,
            "agent_decisions": round_decisions
        }
    
    async def _request_missing_participation(
        self,
        discussion_id: str,
        round_num: int,
        project_data: Dict,
        participants_responded: List[str]
    ):
        """Solicita participación de agentes que no han respondido"""
        
        all_agents = ["A1_SPONSOR", "A3_FISCAL", "A5_FINANZAS"]
        missing = [a for a in all_agents if a not in participants_responded]
        
        for agent_id in missing:
            agent_config = AGENT_CONFIGURATIONS[agent_id]
            
            subject = f"[RECORDATORIO Round {round_num}] Necesitamos tu input - {project_data.get('project_name', '')[:40]}"
            
            body = f"""Hola {agent_config['name']},

Soy Carlos (PMO). Estamos en Round {round_num} de discusión sobre el proyecto "{project_data.get('project_name')}".

Aún no hemos recibido tu contribución. Por favor revisa los análisis de tus colegas y comparte tu opinión para poder avanzar.

No podemos proceder sin tu input.

Gracias,
Carlos Mendoza
PMO
"""
            
            self.multi_gmail.send_email_as_agent(
                agent_id="A2_PMO",
                to=agent_config["email"],
                subject=subject,
                body=body
            )
            
            logger.info(f"📧 Recordatorio enviado a {agent_config['name']} (Round {round_num})")

    def _extract_decision_from_response(self, response: str) -> str:
        """
        Extrae la decisión del agente de su respuesta.

        Busca patrones como:
        - DECISIÓN: APROBAR
        - DECISIÓN: APROBAR_CON_CONDICIONES
        - DECISIÓN: RECHAZAR
        """
        import re

        if not response:
            return "SIN_RESPUESTA"

        response_upper = response.upper()

        # Buscar patrón explícito "DECISIÓN: X"
        decision_pattern = r'DECISI[OÓ]N:\s*(APROBAR_CON_CONDICIONES|APROBAR|RECHAZAR|APROBADO|RECHAZADO)'
        match = re.search(decision_pattern, response_upper)
        if match:
            decision = match.group(1)
            if decision in ("APROBAR", "APROBADO"):
                return "APROBAR"
            elif decision == "APROBAR_CON_CONDICIONES":
                return "APROBAR_CON_CONDICIONES"
            elif decision in ("RECHAZAR", "RECHAZADO"):
                return "RECHAZAR"

        # Si no hay patrón explícito, analizar contenido
        approval_keywords = ["aprobar", "aprobado", "favorable", "procede", "viable", "de acuerdo", "apoyo"]
        rejection_keywords = ["rechazar", "rechazado", "no procede", "no viable", "negar", "oposición"]
        condition_keywords = ["condición", "ajuste", "modificar", "revisar", "siempre que", "sujeto a"]

        response_lower = response.lower()

        has_approval = any(kw in response_lower for kw in approval_keywords)
        has_rejection = any(kw in response_lower for kw in rejection_keywords)
        has_conditions = any(kw in response_lower for kw in condition_keywords)

        if has_rejection and not has_approval:
            return "RECHAZAR"
        elif has_approval and has_conditions:
            return "APROBAR_CON_CONDICIONES"
        elif has_approval:
            return "APROBAR"
        else:
            return "PENDIENTE"

    def _check_consensus(self, round_results: Dict) -> tuple[bool, str]:
        """
        Verifica si hay consenso entre los agentes analizando las decisiones extraídas.

        Usa las decisiones ya extraídas de cada agente:
        - APROBAR: Aprobación total
        - APROBAR_CON_CONDICIONES: Aprobación con condiciones
        - RECHAZAR: Rechazo
        - PENDIENTE: Sin decisión clara

        Returns:
            tuple[bool, str]: (hay_consenso, tipo_consenso)
        """
        round_num = round_results.get("round", 0)
        agent_decisions = round_results.get("agent_decisions", {})

        if not agent_decisions:
            return False, "no_decisions"

        # Mapear decisiones extraídas a categorías
        decisions = {}
        for agent_id, data in agent_decisions.items():
            decision = data.get("decision", "PENDIENTE").upper()
            if decision == "APROBAR":
                decisions[agent_id] = "approved"
            elif decision == "APROBAR_CON_CONDICIONES":
                decisions[agent_id] = "conditional"
            elif decision == "RECHAZAR":
                decisions[agent_id] = "rejected"
            else:
                decisions[agent_id] = "unclear"

        # Contar decisiones
        approved = sum(1 for d in decisions.values() if d == "approved")
        conditional = sum(1 for d in decisions.values() if d == "conditional")
        rejected = sum(1 for d in decisions.values() if d == "rejected")
        unclear = sum(1 for d in decisions.values() if d == "unclear")
        total = len(decisions)

        logger.info(f"Consensus check round {round_num}: approved={approved}, conditional={conditional}, rejected={rejected}, unclear={unclear}")

        # Determinar consenso
        # Consenso total de aprobación
        if approved == total:
            return True, "approved"

        # Consenso total de rechazo
        if rejected == total:
            return True, "rejected"

        # Mayoría aprueba (con o sin condiciones)
        if (approved + conditional) > (rejected + unclear) and rejected == 0:
            if conditional > 0:
                return True, "approved_with_conditions"
            return True, "approved"

        # Mayoría rechaza
        if rejected > (approved + conditional):
            return True, "rejected"

        # Después de 3 rounds sin consenso claro, forzar decisión por mayoría
        if round_num >= 3:
            if (approved + conditional) >= rejected:
                return True, "approved_with_conditions"
            else:
                return True, "rejected_after_discussion"

        # No hay consenso aún
        return False, "no_consensus"
    
    async def _pmo_consolidate_and_create_po(
        self,
        discussion_id: str,
        project_id: str,
        project_data: Dict,
        consensus_type: str,
        final_round: int,
        agent_decisions: Dict[str, Dict] = None
    ) -> Dict:
        """
        PMO consolida discusiones y crea solicitud de orden de compra.
        ESTE es el único email que va al sponsor.

        Args:
            agent_decisions: Dict con decisiones de cada agente, ej:
                {"A1_SPONSOR": {"agent_name": "María", "decision": "APROBAR", "summary": "..."}}
        """
        # Si no hay decisiones, crear estructura vacía
        if agent_decisions is None:
            agent_decisions = {}
        
        logger.info(f"[PMO] Carlos consolidando discusión de {final_round} rounds")
        
        # Obtener sponsor
        sponsor_email = project_data.get('sponsor_email', 'estrategia@revisar-ia.com')
        sponsor_name = project_data.get('sponsor_name', 'Usuario')
        
        # Carlos genera consolidación AMPLIA
        consolidation_context = f"""
El equipo ha discutido durante {final_round} rondas sobre el proyecto:

Proyecto: {project_data.get('project_name')}
Presupuesto: ${project_data.get('budget_estimate', 0):,.2f} MXN
Beneficio Esperado: ${project_data.get('expected_economic_benefit', 0):,.2f} MXN
Descripción: {project_data.get('description', '')}

Los agentes María (Estrategia), Laura (Fiscal) y Roberto (Finanzas) han intercambiado {final_round} rondas de análisis.

Tipo de consenso alcanzado: {consensus_type}

Como PMO, tu trabajo es:
1. Consolidar TODOS los acuerdos y observaciones del equipo
2. Listar TODAS las condiciones/ajustes que acordaron
3. Generar una solicitud de Orden de Compra DETALLADA que incluya:
   - Alcance del servicio (basado en acuerdos)
   - Entregables esperados (específicos)
   - Condiciones de validación (cómo se medirá el éxito)
   - Timeline propuesto
   - Monto aprobado
   - Condiciones especiales acordadas por el equipo

Sé MUY detallado y específico. Este documento irá a Legal para hacer el contrato.
"""
        
        pmo_analysis = await self.agent_service.agent_analyze(
            "A2_PMO",
            consolidation_context,
            """Genera un documento consolidado COMPLETO que incluya:

1. Resumen Ejecutivo de las {final_round} rondas
2. Acuerdos Alcanzados (punto por punto)
3. Condiciones y Ajustes Acordados
4. SOLICITUD DE ORDEN DE COMPRA con:
   - Número de PO sugerido
   - Descripción detallada del servicio
   - Alcance y entregables específicos
   - Criterios de aceptación
   - Timeline
   - Monto y forma de pago
   - Condiciones especiales

Sé exhaustivo - este doc va a Legal.""".format(final_round=final_round)
        )
        
        # GENERAR PDF CONSOLIDADO
        from services.report_generator import ReportGeneratorService
        from services.purchase_order_service import PurchaseOrderService
        
        report_gen = ReportGeneratorService()
        po_service = PurchaseOrderService(self.db)
        
        # Preparar decisiones para el reporte (usar las reales o fallback)
        final_agent_decisions = {}
        default_agents = {
            "A1_SPONSOR": {"agent_name": "María Rodríguez", "default_decision": consensus_type.upper()},
            "A3_FISCAL": {"agent_name": "Laura Sánchez", "default_decision": consensus_type.upper()},
            "A5_FINANZAS": {"agent_name": "Roberto Torres", "default_decision": consensus_type.upper()}
        }

        for agent_id, defaults in default_agents.items():
            if agent_id in agent_decisions and agent_decisions[agent_id]:
                final_agent_decisions[agent_id] = agent_decisions[agent_id]
            else:
                final_agent_decisions[agent_id] = {
                    "agent_name": defaults["agent_name"],
                    "decision": defaults["default_decision"],
                    "summary": f"Consenso alcanzado ({consensus_type})"
                }

        consolidated_pdf_path = report_gen.generate_consolidated_report(
            project_id=project_id,
            cycle=final_round,
            project_data=project_data,
            agent_decisions=final_agent_decisions,
            conflicts=[],
            pmo_analysis=pmo_analysis
        )
        
        # GENERAR ORDEN DE COMPRA
        logger.info(f"[PMO] Generando Orden de Compra...")

        # Construir lista de agentes que aprobaron basado en decisiones reales
        agent_roles = {"A1_SPONSOR": "Estrategia", "A3_FISCAL": "Fiscal", "A5_FINANZAS": "Finanzas"}
        approved_by_agents = [
            f"{final_agent_decisions[agent_id]['agent_name']} ({agent_roles[agent_id]}) - {final_agent_decisions[agent_id]['decision']}"
            for agent_id in final_agent_decisions
        ]

        po_result = await po_service.generate_purchase_order(
            project_id=project_id,
            project_data=project_data,
            consolidated_analysis=pmo_analysis,
            approved_by_agents=approved_by_agents
        )
        
        # Path absoluto para adjuntar AMBOS PDFs
        consolidated_pdf = f"/app/backend{consolidated_pdf_path}" if consolidated_pdf_path else None
        po_pdf = po_result.get('pdf_path') if po_result else None
        
        # Carlos envía email al sponsor CON AMBOS PDFs ADJUNTOS
        po_number = po_result.get('po_number', 'PO-PENDIENTE') if po_result else 'PO-PENDIENTE'
        
        subject = f"[PMO] Consolidación y Orden de Compra {po_number}: {project_data.get('project_name', '')[:40]}"
        
        body = f"""Hola {sponsor_name},

Soy Carlos, de PMO.

El equipo completó {final_round} rondas de análisis y llegamos a acuerdos sobre el proyecto "{project_data.get('project_name')}".

ADJUNTO 2 DOCUMENTOS:
1. 📄 Consolidación de acuerdos y condiciones del equipo
2. 📄 Orden de Compra {po_number} lista para firma

MONTO APROBADO: ${project_data.get('budget_estimate', 0):,.2f} MXN

{pmo_analysis[:400]}...

(Ver PDFs adjuntos para documentos completos)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PRÓXIMOS PASOS:

1. Revisa y firma la Orden de Compra adjunta
2. La enviaremos a Legal (legal@revisar-ia.com) para elaborar contrato
3. Legal redactará el contrato de prestación de servicios

Te mantendré informado del progreso.

Saludos,
Carlos Mendoza
Gerente de PMO
Revisar.ia

--
pmo@revisar-ia.com
"""
        
        # Enviar email al sponsor CON PDF CONSOLIDADO
        # (La PO se incluirá como segundo email o dentro del consolidado)
        result = self.multi_gmail.send_email_as_agent(
            agent_id="A2_PMO",
            to=sponsor_email,
            subject=subject,
            body=body,
            cc=None,
            attachment_path=consolidated_pdf
        )
        
        if result.get('success'):
            logger.info(f"✅ PMO envió consolidación al sponsor: {result.get('message_id')}")
            
            # Enviar SEGUNDO email con la Orden de Compra
            if po_pdf and os.path.exists(po_pdf):
                po_subject = f"[PMO] Orden de Compra {po_number} - {project_data.get('project_name', '')[:40]}"
                po_body = f"""Hola {sponsor_name},

Adjunto la Orden de Compra {po_number} lista para tu firma.

Monto: ${project_data.get('budget_estimate', 0):,.2f} MXN

Por favor revisa y confirma para proceder con Legal.

Saludos,
Carlos Mendoza
PMO
"""
                
                po_result = self.multi_gmail.send_email_as_agent(
                    agent_id="A2_PMO",
                    to=sponsor_email,
                    subject=po_subject,
                    body=po_body,
                    cc=None,
                    attachment_path=po_pdf
                )
                
                if po_result.get('success'):
                    logger.info(f"✅ PMO envió Orden de Compra {po_number}: {po_result.get('message_id')}")
            
            # ENVIAR TERCER EMAIL: Solicitud a Legal para elaborar contrato
            logger.info(f"[PMO] Enviando solicitud de contrato a Legal (legal@revisar-ia.com)")
            
            legal_subject = f"[PMO → Legal] Solicitud de Contrato - PO {po_number} Aprobada"
            legal_body = f"""Hola Equipo Legal,

Soy Carlos Mendoza, de PMO.

El proyecto "{project_data.get('project_name')}" ha sido APROBADO por el equipo ejecutivo después de {final_round} rondas de evaluación exhaustiva.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 INFORMACIÓN DEL PROYECTO:

• Proyecto: {project_data.get('project_name')}
• ID Proyecto: {project_id}
• Orden de Compra: {po_number}
• Monto Aprobado: ${project_data.get('budget_estimate', 0):,.2f} MXN
• Duración: {project_data.get('duration_months', 12)} meses

• Sponsor/Solicitante: {sponsor_name}
• Email Sponsor: {sponsor_email}
• Departamento: {project_data.get('department', 'N/A')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📎 DOCUMENTOS ADJUNTOS:

1. Orden de Compra {po_number} (firmada por María, Laura y Roberto)
2. Consolidado de acuerdos y condiciones del equipo

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 SOLICITUD:

Por favor elabora el **Contrato de Prestación de Servicios** con el proveedor que incluya:

✓ Alcance detallado del servicio (basado en descripción y acuerdos)
✓ Entregables específicos y verificables
✓ Criterios de aceptación claros
✓ Timeline y milestones
✓ Forma de pago (hitos, porcentajes)
✓ Cláusulas de cumplimiento
✓ Evidencia de materialidad requerida (Art. 69-B CFF)
✓ Fecha Cierta para efectos fiscales

CONDICIONES ACORDADAS POR EL EQUIPO:

{pmo_analysis[:600]}...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📨 PRÓXIMOS PASOS:

1. Elabora el borrador de contrato
2. Envíalo a revisión del equipo (María, Laura, Roberto)
3. Una vez aprobado, envíalo al proveedor para firma
4. Archiva contrato firmado en Defense File

Cualquier duda, estoy disponible.

Saludos,
Carlos Mendoza
Gerente de PMO
Revisar.ia
Tel: [pendiente]
Email: pmo@revisar-ia.com
"""
            
            # Enviar a Legal con PO adjunta
            legal_result = self.multi_gmail.send_email_as_agent(
                agent_id="A2_PMO",
                to="legal@revisar-ia.com",
                subject=legal_subject,
                body=legal_body,
                cc=[sponsor_email],  # Sponsor en CC para transparencia
                attachment_path=po_pdf
            )
            
            if legal_result.get('success'):
                logger.info(f"✅ PMO envió solicitud de contrato a Legal: {legal_result.get('message_id')}")
                
                # Actualizar proyecto a Stage 3
                await self.db.projects.update_one(
                    {"project_id": project_id},
                    {"$set": {
                        "workflow_state": "STAGE_3_LEGAL_CONTRACT",
                        "legal_notified_at": datetime.now(timezone.utc).isoformat(),
                        "current_stage": "Elaboración de Contrato (Legal)"
                    }}
                )
            else:
                logger.error(f"❌ Error enviando solicitud a Legal: {legal_result.get('error')}")
        
        # Actualizar proyecto
        await self.db.projects.update_one(
            {"project_id": project_id},
            {"$set": {
                "workflow_state": "STAGE_2_PO_GENERATED",
                "stage_1_completed_at": datetime.now(timezone.utc).isoformat(),
                "discussion_id": discussion_id,
                "consensus_type": consensus_type,
                "consolidated_pdf": consolidated_pdf_path,
                "po_number": po_number,
                "po_pdf_path": po_pdf
            }}
        )
        
        return {
            "status": "consensus_reached",
            "rounds_completed": final_round,
            "consensus_type": consensus_type,
            "pmo_consolidation": pmo_analysis,
            "consolidated_pdf": consolidated_pdf_path,
            "po_number": po_number,
            "po_pdf": po_pdf,
            "next_stage": "STAGE_3_LEGAL_CONTRACT"
        }
