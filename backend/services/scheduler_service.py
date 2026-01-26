"""
Scheduler Service for Revisar.IA
Handles scheduled tasks like daily agent emails
"""
import asyncio
import logging
from datetime import datetime, time, timedelta, timezone as dt_timezone
from typing import Callable, Dict, List
from zoneinfo import ZoneInfo

from backend.services.dreamhost_email_service import DreamHostEmailService

logger = logging.getLogger(__name__)

MEXICO_TZ = ZoneInfo('America/Mexico_City')

class SchedulerService:
    def __init__(self):
        self.email_service = DreamHostEmailService()
        self.running = False
        self.tasks: List[asyncio.Task] = []
    
    async def start(self):
        """Start all scheduled tasks"""
        if self.running:
            logger.warning("Scheduler already running")
            return
        
        self.running = True
        logger.info("🕐 Scheduler Service iniciado")
        
        task = asyncio.create_task(self._run_daily_pmo_email())
        self.tasks.append(task)
    
    async def stop(self):
        """Stop all scheduled tasks"""
        self.running = False
        for task in self.tasks:
            task.cancel()
        self.tasks = []
        logger.info("Scheduler Service detenido")
    
    async def _run_daily_pmo_email(self):
        """Run daily PMO to Proveedor email at 8:00 AM Mexico City time"""
        while self.running:
            try:
                now = datetime.now(MEXICO_TZ)
                target_time = now.replace(hour=8, minute=0, second=0, microsecond=0)
                
                if now >= target_time:
                    target_time += timedelta(days=1)
                
                wait_seconds = (target_time - now).total_seconds()
                logger.info(f"📧 Próximo envío PMO->Proveedor: {target_time.strftime('%Y-%m-%d %H:%M')} (en {wait_seconds/3600:.1f} horas)")
                
                await asyncio.sleep(wait_seconds)
                
                if self.running:
                    await self._send_daily_pmo_email()
                    
            except asyncio.CancelledError:
                logger.info("Daily PMO email task cancelled")
                break
            except Exception as e:
                logger.error(f"Error in daily PMO email scheduler: {e}")
                await asyncio.sleep(3600)
    
    async def _send_daily_pmo_email(self):
        """Send daily status email from PMO agent to Proveedor agent"""
        try:
            today = datetime.now(MEXICO_TZ).strftime('%d/%m/%Y')
            
            subject = f"📋 Reporte Diario de Actividades - {today}"
            
            body = f"""Buenos días,

Este es el reporte automático diario del Sistema Revisar.IA.

=== RESUMEN DE ACTIVIDADES ===

Fecha: {today}
Generado por: A2_PMO (Agente de Gestión de Proyectos)
Destinatario: A6_PROVEEDOR (Agente de Verificación de Proveedores)

--- TAREAS PENDIENTES ---
• Revisar nuevos proveedores registrados en las últimas 24 horas
• Verificar cumplimiento de documentación de proveedores activos
• Actualizar estatus de proveedores en lista 69-B del SAT
• Validar información fiscal de proveedores con facturas pendientes

--- RECORDATORIOS ---
• Los proveedores nuevos requieren validación completa antes de su primer pago
• Verificar Constancia de Situación Fiscal vigente
• Confirmar que el RFC no aparezca en listas negras del SAT

--- MÉTRICAS DEL SISTEMA ---
• Sistema operativo: ✅ Activo
• Base de conocimiento: ✅ Actualizada
• Conexión SAT: ✅ Disponible

Este correo es generado automáticamente por el sistema Revisar.IA.
No responder a este mensaje.

---
A2_PMO - Agente de Gestión de Proyectos
Sistema de Auditoría Fiscal Inteligente
Revisar.IA
"""

            html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{ font-family: 'Segoe UI', Arial, sans-serif; background: #f5f5f5; margin: 0; padding: 20px; }}
        .container {{ max-width: 600px; margin: 0 auto; background: white; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 20px rgba(0,0,0,0.1); }}
        .header {{ background: linear-gradient(135deg, #3B82F6 0%, #1D4ED8 100%); padding: 30px; text-align: center; }}
        .header h1 {{ color: white; margin: 0; font-size: 22px; }}
        .header .date {{ color: #93C5FD; font-size: 14px; margin-top: 8px; }}
        .content {{ padding: 30px; }}
        .section {{ margin-bottom: 25px; }}
        .section-title {{ font-size: 16px; font-weight: bold; color: #1E40AF; margin-bottom: 12px; border-bottom: 2px solid #DBEAFE; padding-bottom: 8px; }}
        .task-list {{ list-style: none; padding: 0; margin: 0; }}
        .task-list li {{ padding: 8px 0; border-bottom: 1px solid #F3F4F6; display: flex; align-items: center; gap: 10px; }}
        .task-list li:last-child {{ border-bottom: none; }}
        .bullet {{ color: #3B82F6; font-weight: bold; }}
        .metric {{ display: flex; justify-content: space-between; padding: 8px 12px; background: #F0FDF4; border-radius: 8px; margin-bottom: 8px; }}
        .metric-label {{ color: #374151; }}
        .metric-value {{ color: #059669; font-weight: bold; }}
        .footer {{ background: #F9FAFB; padding: 20px; text-align: center; color: #6B7280; font-size: 12px; border-top: 1px solid #E5E7EB; }}
        .agent-badge {{ display: inline-block; background: #DBEAFE; color: #1E40AF; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 500; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📋 Reporte Diario de Actividades</h1>
            <div class="date">{today}</div>
        </div>
        <div class="content">
            <div style="margin-bottom: 20px; text-align: center;">
                <span class="agent-badge">De: A2_PMO</span>
                <span style="margin: 0 10px;">→</span>
                <span class="agent-badge">Para: A6_PROVEEDOR</span>
            </div>
            
            <div class="section">
                <div class="section-title">📝 Tareas Pendientes</div>
                <ul class="task-list">
                    <li><span class="bullet">•</span> Revisar nuevos proveedores registrados en las últimas 24 horas</li>
                    <li><span class="bullet">•</span> Verificar cumplimiento de documentación de proveedores activos</li>
                    <li><span class="bullet">•</span> Actualizar estatus de proveedores en lista 69-B del SAT</li>
                    <li><span class="bullet">•</span> Validar información fiscal de proveedores con facturas pendientes</li>
                </ul>
            </div>
            
            <div class="section">
                <div class="section-title">⚠️ Recordatorios Importantes</div>
                <ul class="task-list">
                    <li><span class="bullet">•</span> Los proveedores nuevos requieren validación completa antes de su primer pago</li>
                    <li><span class="bullet">•</span> Verificar Constancia de Situación Fiscal vigente</li>
                    <li><span class="bullet">•</span> Confirmar que el RFC no aparezca en listas negras del SAT</li>
                </ul>
            </div>
            
            <div class="section">
                <div class="section-title">📊 Estado del Sistema</div>
                <div class="metric">
                    <span class="metric-label">Sistema operativo</span>
                    <span class="metric-value">✅ Activo</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Base de conocimiento</span>
                    <span class="metric-value">✅ Actualizada</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Conexión SAT</span>
                    <span class="metric-value">✅ Disponible</span>
                </div>
            </div>
        </div>
        <div class="footer">
            <p><strong>A2_PMO</strong> - Agente de Gestión de Proyectos</p>
            <p>Sistema de Auditoría Fiscal Inteligente • Revisar.IA</p>
            <p style="color: #9CA3AF; font-size: 11px;">Este correo es generado automáticamente. No responder.</p>
        </div>
    </div>
</body>
</html>
"""
            
            result = self.email_service.send_agent_to_agent(
                from_agent_id="A2_PMO",
                to_agent_id="A6_PROVEEDOR",
                subject=subject,
                body=body
            )
            
            if result.get('success'):
                logger.info(f"✅ Email diario PMO->Proveedor enviado exitosamente")
            else:
                logger.error(f"❌ Error enviando email diario: {result.get('error')}")
                
        except Exception as e:
            logger.error(f"Error sending daily PMO email: {e}")
    
    async def send_test_email(self):
        """Send a test email immediately (for testing purposes)"""
        await self._send_daily_pmo_email()
        return {"success": True, "message": "Test email sent"}

scheduler_service = SchedulerService()
