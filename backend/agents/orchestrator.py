"""
Orquestador Principal de Agentes Autónomos
Coordina el monitoreo, reparación y documentación automática del sistema.
"""
import os
import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class AgentReport:
    agent_id: str
    timestamp: datetime
    status: str
    issues: List[Dict[str, Any]] = field(default_factory=list)
    fixes: List[Dict[str, Any]] = field(default_factory=list)
    duration_ms: float = 0


@dataclass 
class OrchestratorStatus:
    is_running: bool = False
    last_cycle: Optional[datetime] = None
    cycles_completed: int = 0
    total_issues_found: int = 0
    total_fixes_applied: int = 0


class AgentOrchestrator:
    """Orquestador principal que coordina todos los agentes autónomos"""
    
    def __init__(self):
        self._status = OrchestratorStatus()
        self._task: Optional[asyncio.Task] = None
        self._interval_minutes = 5
        self._reports_history: List[AgentReport] = []
        self._max_history = 100
        
        from .health.monitor import health_monitor
        self.health_monitor = health_monitor
    
    async def start(self, interval_minutes: int = 5):
        """Inicia el ciclo de monitoreo continuo"""
        if self._status.is_running:
            logger.warning("Orquestador ya está corriendo")
            return
        
        self._status.is_running = True
        self._interval_minutes = interval_minutes
        
        logger.info(f"Iniciando Orquestador de Agentes - ciclo cada {interval_minutes} minutos")
        
        await self.run_cycle()
        
        self._task = asyncio.create_task(self._run_loop())
    
    async def _run_loop(self):
        """Loop principal de monitoreo"""
        while self._status.is_running:
            try:
                await asyncio.sleep(self._interval_minutes * 60)
                if self._status.is_running:
                    await self.run_cycle()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error en ciclo de monitoreo: {e}")
                await self._self_heal(e)
    
    def stop(self):
        """Detiene el monitoreo"""
        self._status.is_running = False
        if self._task:
            self._task.cancel()
            self._task = None
        logger.info("Orquestador detenido")
    
    async def run_cycle(self) -> List[AgentReport]:
        """Ejecuta un ciclo completo de monitoreo y reparación"""
        cycle_start = datetime.utcnow()
        reports: List[AgentReport] = []
        
        logger.info(f"\n{'='*60}")
        logger.info(f"CICLO DE MANTENIMIENTO - {cycle_start.isoformat()}")
        logger.info(f"{'='*60}")
        
        try:
            logger.info("FASE 1: Monitoreo de Salud...")
            health_report = await self.health_monitor.check_all()
            
            report = AgentReport(
                agent_id="HEALTH_MONITOR",
                timestamp=cycle_start,
                status=health_report.status.value,
                issues=[{
                    "id": i.id,
                    "severity": i.severity.value,
                    "type": i.type,
                    "description": i.description,
                    "component": i.component
                } for i in health_report.issues]
            )
            reports.append(report)
            
            self._status.total_issues_found += len(health_report.issues)
            
            if health_report.issues:
                logger.info(f"FASE 2: Análisis de {len(health_report.issues)} issues...")
                
                for issue in health_report.issues:
                    logger.warning(f"  [{issue.severity.value.upper()}] {issue.component}: {issue.description}")
                    if issue.suggested_fix:
                        logger.info(f"    Sugerencia: {issue.suggested_fix}")
            else:
                logger.info("Sistema saludable - no se requieren reparaciones")
            
            self._status.last_cycle = datetime.utcnow()
            self._status.cycles_completed += 1
            
            self._reports_history.extend(reports)
            if len(self._reports_history) > self._max_history:
                self._reports_history = self._reports_history[-self._max_history:]
            
            duration = (datetime.utcnow() - cycle_start).total_seconds()
            logger.info(f"Ciclo completado en {duration:.2f}s")
            
        except Exception as e:
            logger.error(f"Error en ciclo de mantenimiento: {e}")
            await self._self_heal(e)
        
        return reports
    
    async def _self_heal(self, error: Exception):
        """Intenta auto-reparación del orquestador"""
        logger.info("Intentando auto-reparación del orquestador...")

        try:
            openai_key = os.getenv("OPENAI_API_KEY")
            if not openai_key:
                logger.warning("No hay API key de OpenAI para auto-diagnóstico")
                return

            from openai import OpenAI
            client = OpenAI(api_key=openai_key)

            response = client.chat.completions.create(
                model="gpt-4o",
                max_tokens=1000,
                messages=[{
                    "role": "user",
                    "content": f"""El orquestador de agentes de Revisar.IA falló con este error:
{str(error)}

Analiza el error y sugiere una solución breve en español."""
                }]
            )

            if response.choices:
                diagnosis = response.choices[0].message.content
                logger.info(f"Diagnóstico IA: {diagnosis[:500]}")

        except Exception as heal_error:
            logger.error(f"Fallo en auto-reparación: {heal_error}")
    
    def get_status(self) -> Dict[str, Any]:
        """Retorna el estado actual del orquestador"""
        return {
            "is_running": self._status.is_running,
            "last_cycle": self._status.last_cycle.isoformat() if self._status.last_cycle else None,
            "cycles_completed": self._status.cycles_completed,
            "total_issues_found": self._status.total_issues_found,
            "total_fixes_applied": self._status.total_fixes_applied,
            "interval_minutes": self._interval_minutes,
            "health_monitor": self.health_monitor.get_status()
        }
    
    def get_reports_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Retorna historial de reportes"""
        return [
            {
                "agent_id": r.agent_id,
                "timestamp": r.timestamp.isoformat(),
                "status": r.status,
                "issues_count": len(r.issues),
                "fixes_count": len(r.fixes)
            }
            for r in self._reports_history[-limit:]
        ]
    
    async def run_single_check(self) -> Dict[str, Any]:
        """Ejecuta un solo check de salud (on-demand)"""
        report = await self.health_monitor.check_all()
        return report.to_dict()


orchestrator = AgentOrchestrator()
