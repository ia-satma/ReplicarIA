"""
Tráfico.IA - Sistema de Monitoreo de Proyectos con Emails Automáticos
Servicio principal para detección de eventos críticos y notificaciones
"""
import os
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum
from zoneinfo import ZoneInfo
import httpx

logger = logging.getLogger(__name__)

MEXICO_TZ = ZoneInfo('America/Mexico_City')


class TipoAlerta(str, Enum):
    PROYECTO_INACTIVO = "proyecto_inactivo"
    ENTREGABLE_PROXIMO = "entregable_proximo"
    CANDADO_PENDIENTE = "candado_pendiente"
    CAMBIO_CALIFICACION = "cambio_calificacion"
    VENCIMIENTO_CRITICO = "vencimiento_critico"
    FASE_BLOQUEADA = "fase_bloqueada"


class PrioridadAlerta(str, Enum):
    BAJA = "baja"
    MEDIA = "media"
    ALTA = "alta"
    CRITICA = "critica"


class Alerta:
    def __init__(
        self,
        tipo: TipoAlerta,
        proyecto_id: str,
        titulo: str,
        descripcion: str,
        prioridad: PrioridadAlerta = PrioridadAlerta.MEDIA,
        datos_extra: Dict = None
    ):
        self.id = f"ALR-{datetime.now().strftime('%Y%m%d%H%M%S')}-{proyecto_id[:8]}"
        self.tipo = tipo
        self.proyecto_id = proyecto_id
        self.titulo = titulo
        self.descripcion = descripcion
        self.prioridad = prioridad
        self.datos_extra = datos_extra or {}
        self.creada_en = datetime.now(MEXICO_TZ)
        self.leida = False
        self.resuelta = False

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "tipo": self.tipo.value,
            "proyecto_id": self.proyecto_id,
            "titulo": self.titulo,
            "descripcion": self.descripcion,
            "prioridad": self.prioridad.value,
            "datos_extra": self.datos_extra,
            "creada_en": self.creada_en.isoformat(),
            "leida": self.leida,
            "resuelta": self.resuelta
        }


async def get_sendgrid_credentials() -> Optional[Dict[str, str]]:
    """Obtiene credenciales de SendGrid via Replit Connectors."""
    hostname = os.environ.get('REPLIT_CONNECTORS_HOSTNAME')
    token = None
    
    if os.environ.get('REPL_IDENTITY'):
        token = f"repl {os.environ.get('REPL_IDENTITY')}"
    elif os.environ.get('WEB_REPL_RENEWAL'):
        token = f"depl {os.environ.get('WEB_REPL_RENEWAL')}"
    
    if not token or not hostname:
        logger.warning("⚠️ Tráfico.IA: Credenciales de Replit Connectors no disponibles")
        return None
    
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"https://{hostname}/api/v2/connection?include_secrets=true&connector_names=sendgrid",
                headers={"Accept": "application/json", "X_REPLIT_TOKEN": token},
                timeout=30.0
            )
            data = resp.json()
            item = data.get('items', [{}])[0] if data.get('items') else {}
            settings = item.get('settings', {})
            
            api_key = settings.get('api_key')
            from_email = settings.get('from_email')
            
            if api_key and from_email:
                return {"api_key": api_key, "from_email": from_email}
            
            logger.warning("⚠️ Tráfico.IA: SendGrid no configurado correctamente")
            return None
    except Exception as e:
        logger.error(f"❌ Tráfico.IA: Error obteniendo credenciales SendGrid: {e}")
        return None


class TraficoIAService:
    """Servicio principal de Tráfico.IA para monitoreo y alertas."""
    
    def __init__(self, db=None):
        self.db = db
        self.running = False
        self.scheduler_task: Optional[asyncio.Task] = None
        self.alertas: List[Alerta] = []
        self.metricas: Dict[str, Any] = {
            "proyectos_monitoreados": 0,
            "alertas_generadas_hoy": 0,
            "emails_enviados_hoy": 0,
            "ultima_ejecucion": None,
            "errores_hoy": 0
        }
        self.configuracion = {
            "frecuencia_monitoreo_minutos": 60,
            "dias_inactividad_alerta": 3,
            "dias_vencimiento_alerta": 5,
            "emails_habilitados": True,
            "destinatarios_alertas": [],
            "horario_inicio": "08:00",
            "horario_fin": "20:00"
        }
        logger.info("🚦 Tráfico.IA: Servicio inicializado")
    
    async def iniciar(self):
        """Inicia el scheduler de monitoreo."""
        if self.running:
            logger.warning("🚦 Tráfico.IA: Scheduler ya está corriendo")
            return
        
        self.running = True
        self.scheduler_task = asyncio.create_task(self._loop_monitoreo())
        logger.info("🚦 Tráfico.IA: Scheduler iniciado")
    
    async def detener(self):
        """Detiene el scheduler de monitoreo."""
        self.running = False
        if self.scheduler_task:
            self.scheduler_task.cancel()
            self.scheduler_task = None
        logger.info("🚦 Tráfico.IA: Scheduler detenido")
    
    async def _loop_monitoreo(self):
        """Loop principal de monitoreo programado."""
        while self.running:
            try:
                ahora = datetime.now(MEXICO_TZ)
                hora_actual = ahora.strftime("%H:%M")
                
                inicio = self.configuracion["horario_inicio"]
                fin = self.configuracion["horario_fin"]
                
                if inicio <= hora_actual <= fin:
                    logger.info(f"🚦 Tráfico.IA: Ejecutando monitoreo programado [{hora_actual}]")
                    await self.ejecutar_monitoreo()
                else:
                    logger.debug(f"🚦 Tráfico.IA: Fuera de horario de monitoreo ({inicio}-{fin})")
                
                frecuencia = self.configuracion["frecuencia_monitoreo_minutos"] * 60
                await asyncio.sleep(frecuencia)
                
            except asyncio.CancelledError:
                logger.info("🚦 Tráfico.IA: Loop de monitoreo cancelado")
                break
            except Exception as e:
                logger.error(f"❌ Tráfico.IA: Error en loop de monitoreo: {e}")
                self.metricas["errores_hoy"] += 1
                await asyncio.sleep(300)
    
    async def ejecutar_monitoreo(self) -> Dict[str, Any]:
        """Ejecuta un ciclo completo de monitoreo."""
        resultado = {
            "ejecutado_en": datetime.now(MEXICO_TZ).isoformat(),
            "alertas_nuevas": 0,
            "proyectos_revisados": 0,
            "emails_enviados": 0,
            "errores": []
        }
        
        try:
            proyectos = await self._obtener_proyectos_activos()
            resultado["proyectos_revisados"] = len(proyectos)
            self.metricas["proyectos_monitoreados"] = len(proyectos)
            
            for proyecto in proyectos:
                alertas_proyecto = await self._analizar_proyecto(proyecto)
                for alerta in alertas_proyecto:
                    self.alertas.append(alerta)
                    resultado["alertas_nuevas"] += 1
                    self.metricas["alertas_generadas_hoy"] += 1
                    
                    if alerta.prioridad in [PrioridadAlerta.ALTA, PrioridadAlerta.CRITICA]:
                        if self.configuracion["emails_habilitados"]:
                            email_result = await self._enviar_alerta_email(alerta, proyecto)
                            if email_result.get("success"):
                                resultado["emails_enviados"] += 1
                                self.metricas["emails_enviados_hoy"] += 1
            
            self.metricas["ultima_ejecucion"] = resultado["ejecutado_en"]
            logger.info(f"🚦 Tráfico.IA: Monitoreo completado - {resultado['alertas_nuevas']} alertas, {resultado['emails_enviados']} emails")
            
        except Exception as e:
            error_msg = f"Error en monitoreo: {str(e)}"
            resultado["errores"].append(error_msg)
            self.metricas["errores_hoy"] += 1
            logger.error(f"❌ Tráfico.IA: {error_msg}")
        
        return resultado
    
    async def _obtener_proyectos_activos(self) -> List[Dict]:
        """Obtiene proyectos activos de la base de datos."""
        if self.db is None:
            logger.debug("🚦 Tráfico.IA: Sin conexión a DB, usando datos de ejemplo")
            return self._generar_proyectos_ejemplo()
        
        try:
            proyectos = await self.db.projects.find({
                "current_status": {"$nin": ["closed", "rejected", "completed"]}
            }).to_list(length=100)
            return proyectos
        except Exception as e:
            logger.error(f"❌ Tráfico.IA: Error obteniendo proyectos: {e}")
            return []
    
    def _generar_proyectos_ejemplo(self) -> List[Dict]:
        """Genera proyectos de ejemplo para demostración."""
        ahora = datetime.now(MEXICO_TZ)
        return [
            {
                "project_id": "PROJ-001",
                "project_name": "Consultoría Marketing Digital",
                "current_phase": "phase_3_execution",
                "current_status": "in_execution",
                "sponsor_email": "sponsor@empresa.com",
                "ultima_actividad": (ahora - timedelta(days=5)).isoformat(),
                "fecha_vencimiento": (ahora + timedelta(days=3)).isoformat(),
                "candados_pendientes": ["candado_legal", "candado_fiscal"],
                "calificacion_actual": 75
            },
            {
                "project_id": "PROJ-002",
                "project_name": "Servicios de Software SaaS",
                "current_phase": "phase_2_contractual",
                "current_status": "in_validation",
                "sponsor_email": "sponsor2@empresa.com",
                "ultima_actividad": ahora.isoformat(),
                "fecha_vencimiento": (ahora + timedelta(days=15)).isoformat(),
                "candados_pendientes": [],
                "calificacion_actual": 88
            }
        ]
    
    async def _analizar_proyecto(self, proyecto: Dict) -> List[Alerta]:
        """Analiza un proyecto y genera alertas si es necesario."""
        alertas = []
        ahora = datetime.now(MEXICO_TZ)
        proyecto_id = proyecto.get("project_id", "UNKNOWN")
        proyecto_nombre = proyecto.get("project_name", "Sin nombre")
        
        ultima_actividad_str = proyecto.get("ultima_actividad")
        if ultima_actividad_str:
            try:
                ultima_actividad = datetime.fromisoformat(ultima_actividad_str.replace('Z', '+00:00'))
                if ultima_actividad.tzinfo is None:
                    ultima_actividad = ultima_actividad.replace(tzinfo=MEXICO_TZ)
                dias_inactivo = (ahora - ultima_actividad).days
                
                umbral = self.configuracion["dias_inactividad_alerta"]
                if dias_inactivo >= umbral:
                    prioridad = PrioridadAlerta.ALTA if dias_inactivo >= umbral * 2 else PrioridadAlerta.MEDIA
                    alertas.append(Alerta(
                        tipo=TipoAlerta.PROYECTO_INACTIVO,
                        proyecto_id=proyecto_id,
                        titulo=f"Proyecto sin actividad: {proyecto_nombre}",
                        descripcion=f"El proyecto lleva {dias_inactivo} días sin actividad registrada.",
                        prioridad=prioridad,
                        datos_extra={"dias_inactivo": dias_inactivo}
                    ))
            except Exception as e:
                logger.warning(f"⚠️ Error parseando fecha de actividad: {e}")
        
        fecha_vencimiento_str = proyecto.get("fecha_vencimiento")
        if fecha_vencimiento_str:
            try:
                fecha_vencimiento = datetime.fromisoformat(fecha_vencimiento_str.replace('Z', '+00:00'))
                if fecha_vencimiento.tzinfo is None:
                    fecha_vencimiento = fecha_vencimiento.replace(tzinfo=MEXICO_TZ)
                dias_para_vencer = (fecha_vencimiento - ahora).days
                
                umbral = self.configuracion["dias_vencimiento_alerta"]
                if 0 < dias_para_vencer <= umbral:
                    prioridad = PrioridadAlerta.CRITICA if dias_para_vencer <= 2 else PrioridadAlerta.ALTA
                    alertas.append(Alerta(
                        tipo=TipoAlerta.ENTREGABLE_PROXIMO,
                        proyecto_id=proyecto_id,
                        titulo=f"Entregable próximo a vencer: {proyecto_nombre}",
                        descripcion=f"El proyecto vence en {dias_para_vencer} días.",
                        prioridad=prioridad,
                        datos_extra={"dias_para_vencer": dias_para_vencer, "fecha_vencimiento": fecha_vencimiento_str}
                    ))
                elif dias_para_vencer <= 0:
                    alertas.append(Alerta(
                        tipo=TipoAlerta.VENCIMIENTO_CRITICO,
                        proyecto_id=proyecto_id,
                        titulo=f"¡VENCIDO! Proyecto: {proyecto_nombre}",
                        descripcion=f"El proyecto venció hace {abs(dias_para_vencer)} días.",
                        prioridad=PrioridadAlerta.CRITICA,
                        datos_extra={"dias_vencido": abs(dias_para_vencer)}
                    ))
            except Exception as e:
                logger.warning(f"⚠️ Error parseando fecha de vencimiento: {e}")
        
        candados = proyecto.get("candados_pendientes", [])
        if candados:
            alertas.append(Alerta(
                tipo=TipoAlerta.CANDADO_PENDIENTE,
                proyecto_id=proyecto_id,
                titulo=f"Candados pendientes: {proyecto_nombre}",
                descripcion=f"Hay {len(candados)} candados pendientes de aprobación: {', '.join(candados)}",
                prioridad=PrioridadAlerta.ALTA,
                datos_extra={"candados": candados}
            ))
        
        return alertas
    
    async def _enviar_alerta_email(self, alerta: Alerta, proyecto: Dict) -> Dict[str, Any]:
        """Envía una alerta por email usando SendGrid."""
        credenciales = await get_sendgrid_credentials()
        
        if not credenciales:
            logger.warning("⚠️ Tráfico.IA: No se puede enviar email, SendGrid no configurado")
            return {"success": False, "error": "SendGrid no configurado"}
        
        destinatario = proyecto.get("sponsor_email", "")
        if not destinatario and self.configuracion["destinatarios_alertas"]:
            destinatario = self.configuracion["destinatarios_alertas"][0]
        
        if not destinatario:
            return {"success": False, "error": "Sin destinatario"}
        
        color_prioridad = {
            PrioridadAlerta.BAJA: "#10B981",
            PrioridadAlerta.MEDIA: "#F59E0B",
            PrioridadAlerta.ALTA: "#EF4444",
            PrioridadAlerta.CRITICA: "#DC2626"
        }
        
        color = color_prioridad.get(alerta.prioridad, "#6B7280")
        
        subject = f"🚦 [{alerta.prioridad.value.upper()}] {alerta.titulo}"
        
        html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{ font-family: 'Segoe UI', Arial, sans-serif; background: #f5f5f5; margin: 0; padding: 20px; }}
        .container {{ max-width: 600px; margin: 0 auto; background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 20px rgba(0,0,0,0.1); }}
        .header {{ background: {color}; padding: 25px; text-align: center; }}
        .header h1 {{ color: white; margin: 0; font-size: 20px; }}
        .header .tipo {{ color: rgba(255,255,255,0.8); font-size: 12px; margin-top: 5px; text-transform: uppercase; }}
        .content {{ padding: 30px; }}
        .proyecto-info {{ background: #F3F4F6; padding: 15px; border-radius: 8px; margin-bottom: 20px; }}
        .proyecto-info strong {{ color: #1F2937; }}
        .descripcion {{ color: #4B5563; line-height: 1.6; margin-bottom: 20px; }}
        .prioridad {{ display: inline-block; background: {color}; color: white; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 500; }}
        .footer {{ background: #F9FAFB; padding: 20px; text-align: center; color: #6B7280; font-size: 12px; }}
        .datos-extra {{ background: #EFF6FF; padding: 15px; border-radius: 8px; margin-top: 15px; }}
        .datos-extra h4 {{ margin: 0 0 10px 0; color: #1E40AF; font-size: 14px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚦 Alerta de Tráfico.IA</h1>
            <div class="tipo">{alerta.tipo.value.replace('_', ' ')}</div>
        </div>
        <div class="content">
            <div class="proyecto-info">
                <strong>Proyecto:</strong> {proyecto.get('project_name', 'N/A')}<br>
                <strong>ID:</strong> {alerta.proyecto_id}<br>
                <strong>Fase:</strong> {proyecto.get('current_phase', 'N/A')}
            </div>
            
            <h3 style="color: #1F2937; margin-top: 0;">{alerta.titulo}</h3>
            <p class="descripcion">{alerta.descripcion}</p>
            
            <p><span class="prioridad">Prioridad: {alerta.prioridad.value.upper()}</span></p>
            
            {self._generar_html_datos_extra(alerta.datos_extra)}
            
        </div>
        <div class="footer">
            <p><strong>Tráfico.IA</strong> - Sistema de Monitoreo de Proyectos</p>
            <p>Revisar.IA • {datetime.now(MEXICO_TZ).strftime('%d/%m/%Y %H:%M')}</p>
            <p style="color: #9CA3AF; font-size: 11px;">Este correo es generado automáticamente.</p>
        </div>
    </div>
</body>
</html>
"""
        
        try:
            api_key = credenciales["api_key"]
            from_email = credenciales["from_email"]
            
            payload = {
                "personalizations": [{"to": [{"email": destinatario}]}],
                "from": {"email": from_email, "name": "Tráfico.IA - Revisar.IA"},
                "subject": subject,
                "content": [{"type": "text/html", "value": html_body}]
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.sendgrid.com/v3/mail/send",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json"
                    },
                    json=payload,
                    timeout=30.0
                )
                
                if response.status_code in (200, 201, 202):
                    logger.info(f"✅ Tráfico.IA: Email enviado a {destinatario}")
                    return {"success": True, "destinatario": destinatario}
                else:
                    error_msg = response.text
                    logger.error(f"❌ Tráfico.IA: Error SendGrid {response.status_code}: {error_msg}")
                    return {"success": False, "error": error_msg}
                    
        except Exception as e:
            logger.error(f"❌ Tráfico.IA: Error enviando email: {e}")
            return {"success": False, "error": str(e)}
    
    def _generar_html_datos_extra(self, datos: Dict) -> str:
        """Genera HTML para datos extra de la alerta."""
        if not datos:
            return ""
        
        items = []
        for key, value in datos.items():
            key_display = key.replace('_', ' ').title()
            if isinstance(value, list):
                value = ", ".join(str(v) for v in value)
            items.append(f"<li><strong>{key_display}:</strong> {value}</li>")
        
        return f"""
            <div class="datos-extra">
                <h4>📊 Detalles adicionales</h4>
                <ul style="margin: 0; padding-left: 20px;">
                    {''.join(items)}
                </ul>
            </div>
        """
    
    async def enviar_resumen_diario(self, destinatario: str = None) -> Dict[str, Any]:
        """Envía un resumen diario de alertas y métricas."""
        if not destinatario and self.configuracion["destinatarios_alertas"]:
            destinatario = self.configuracion["destinatarios_alertas"][0]
        
        if not destinatario:
            return {"success": False, "error": "Sin destinatario configurado"}
        
        credenciales = await get_sendgrid_credentials()
        if not credenciales:
            return {"success": False, "error": "SendGrid no configurado"}
        
        alertas_activas = [a for a in self.alertas if not a.resuelta]
        alertas_criticas = len([a for a in alertas_activas if a.prioridad == PrioridadAlerta.CRITICA])
        alertas_altas = len([a for a in alertas_activas if a.prioridad == PrioridadAlerta.ALTA])
        
        fecha_hoy = datetime.now(MEXICO_TZ).strftime('%d/%m/%Y')
        
        html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{ font-family: 'Segoe UI', Arial, sans-serif; background: #f5f5f5; margin: 0; padding: 20px; }}
        .container {{ max-width: 600px; margin: 0 auto; background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 20px rgba(0,0,0,0.1); }}
        .header {{ background: linear-gradient(135deg, #3B82F6 0%, #1D4ED8 100%); padding: 30px; text-align: center; }}
        .header h1 {{ color: white; margin: 0; font-size: 22px; }}
        .header .date {{ color: #93C5FD; font-size: 14px; margin-top: 8px; }}
        .content {{ padding: 30px; }}
        .metric-grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px; margin-bottom: 25px; }}
        .metric {{ background: #F3F4F6; padding: 20px; border-radius: 10px; text-align: center; }}
        .metric .number {{ font-size: 32px; font-weight: bold; color: #1F2937; }}
        .metric .label {{ color: #6B7280; font-size: 12px; margin-top: 5px; }}
        .metric.critica .number {{ color: #DC2626; }}
        .metric.alta .number {{ color: #EF4444; }}
        .section {{ margin-bottom: 25px; }}
        .section-title {{ font-size: 16px; font-weight: bold; color: #1E40AF; margin-bottom: 12px; border-bottom: 2px solid #DBEAFE; padding-bottom: 8px; }}
        .alerta-item {{ padding: 12px; background: #FEF3C7; border-radius: 8px; margin-bottom: 10px; border-left: 4px solid #F59E0B; }}
        .alerta-item.critica {{ background: #FEE2E2; border-left-color: #DC2626; }}
        .footer {{ background: #F9FAFB; padding: 20px; text-align: center; color: #6B7280; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 Resumen Diario Tráfico.IA</h1>
            <div class="date">{fecha_hoy}</div>
        </div>
        <div class="content">
            <div class="metric-grid">
                <div class="metric">
                    <div class="number">{self.metricas['proyectos_monitoreados']}</div>
                    <div class="label">Proyectos Monitoreados</div>
                </div>
                <div class="metric">
                    <div class="number">{len(alertas_activas)}</div>
                    <div class="label">Alertas Activas</div>
                </div>
                <div class="metric critica">
                    <div class="number">{alertas_criticas}</div>
                    <div class="label">Alertas Críticas</div>
                </div>
                <div class="metric alta">
                    <div class="number">{alertas_altas}</div>
                    <div class="label">Alertas Altas</div>
                </div>
            </div>
            
            <div class="section">
                <div class="section-title">⚡ Actividad del Día</div>
                <ul>
                    <li>Alertas generadas hoy: <strong>{self.metricas['alertas_generadas_hoy']}</strong></li>
                    <li>Emails enviados hoy: <strong>{self.metricas['emails_enviados_hoy']}</strong></li>
                    <li>Errores registrados: <strong>{self.metricas['errores_hoy']}</strong></li>
                </ul>
            </div>
            
            {self._generar_html_alertas_recientes(alertas_activas[:5])}
            
        </div>
        <div class="footer">
            <p><strong>Tráfico.IA</strong> - Sistema de Monitoreo de Proyectos</p>
            <p>Revisar.IA • Generado automáticamente</p>
        </div>
    </div>
</body>
</html>
"""
        
        try:
            api_key = credenciales["api_key"]
            from_email = credenciales["from_email"]
            
            payload = {
                "personalizations": [{"to": [{"email": destinatario}]}],
                "from": {"email": from_email, "name": "Tráfico.IA - Revisar.IA"},
                "subject": f"📊 Resumen Diario Tráfico.IA - {fecha_hoy}",
                "content": [{"type": "text/html", "value": html_body}]
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.sendgrid.com/v3/mail/send",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json"
                    },
                    json=payload,
                    timeout=30.0
                )
                
                if response.status_code in (200, 201, 202):
                    logger.info(f"✅ Tráfico.IA: Resumen diario enviado a {destinatario}")
                    return {"success": True, "destinatario": destinatario}
                else:
                    return {"success": False, "error": response.text}
                    
        except Exception as e:
            logger.error(f"❌ Tráfico.IA: Error enviando resumen: {e}")
            return {"success": False, "error": str(e)}
    
    def _generar_html_alertas_recientes(self, alertas: List[Alerta]) -> str:
        """Genera HTML para lista de alertas recientes."""
        if not alertas:
            return """
            <div class="section">
                <div class="section-title">📋 Alertas Recientes</div>
                <p style="color: #10B981;">✅ No hay alertas activas. ¡Todo en orden!</p>
            </div>
            """
        
        items = []
        for alerta in alertas:
            clase = "critica" if alerta.prioridad == PrioridadAlerta.CRITICA else ""
            items.append(f"""
                <div class="alerta-item {clase}">
                    <strong>{alerta.titulo}</strong><br>
                    <small style="color: #6B7280;">{alerta.descripcion}</small>
                </div>
            """)
        
        return f"""
            <div class="section">
                <div class="section-title">📋 Alertas Recientes (Top 5)</div>
                {''.join(items)}
            </div>
        """
    
    def obtener_status(self) -> Dict[str, Any]:
        """Obtiene el estado actual del sistema de monitoreo."""
        alertas_activas = len([a for a in self.alertas if not a.resuelta])
        return {
            "servicio": "Tráfico.IA",
            "version": "1.0.0",
            "activo": self.running,
            "scheduler_running": self.running,
            "pending_alerts": alertas_activas,
            "ultima_ejecucion": self.metricas.get("ultima_ejecucion"),
            "configuracion": self.configuracion,
            "metricas": self.metricas,
            "timestamp": datetime.now(MEXICO_TZ).isoformat()
        }
    
    def obtener_alertas(self, solo_activas: bool = True, limite: int = 50) -> List[Dict]:
        """Obtiene la lista de alertas."""
        alertas = self.alertas
        if solo_activas:
            alertas = [a for a in alertas if not a.resuelta]
        
        alertas_ordenadas = sorted(alertas, key=lambda x: x.creada_en, reverse=True)
        return [a.to_dict() for a in alertas_ordenadas[:limite]]
    
    def obtener_metricas(self) -> Dict[str, Any]:
        """Obtiene métricas detalladas del sistema."""
        alertas_por_tipo = {}
        alertas_por_prioridad = {}
        
        for alerta in self.alertas:
            tipo = alerta.tipo.value
            prioridad = alerta.prioridad.value
            alertas_por_tipo[tipo] = alertas_por_tipo.get(tipo, 0) + 1
            alertas_por_prioridad[prioridad] = alertas_por_prioridad.get(prioridad, 0) + 1
        
        return {
            "resumen": self.metricas,
            "alertas_totales": len(self.alertas),
            "alertas_activas": len([a for a in self.alertas if not a.resuelta]),
            "alertas_por_tipo": alertas_por_tipo,
            "alertas_por_prioridad": alertas_por_prioridad,
            "timestamp": datetime.now(MEXICO_TZ).isoformat()
        }
    
    def configurar(self, nueva_config: Dict[str, Any]) -> Dict[str, Any]:
        """Actualiza la configuración del servicio."""
        campos_validos = [
            "frecuencia_monitoreo_minutos",
            "dias_inactividad_alerta",
            "dias_vencimiento_alerta",
            "emails_habilitados",
            "destinatarios_alertas",
            "horario_inicio",
            "horario_fin"
        ]
        
        for campo in campos_validos:
            if campo in nueva_config:
                self.configuracion[campo] = nueva_config[campo]
                logger.info(f"🚦 Tráfico.IA: Configuración '{campo}' actualizada a '{nueva_config[campo]}'")
        
        return {
            "success": True,
            "configuracion_actual": self.configuracion
        }
    
    def marcar_alerta_leida(self, alerta_id: str) -> bool:
        """Marca una alerta como leída."""
        for alerta in self.alertas:
            if alerta.id == alerta_id:
                alerta.leida = True
                return True
        return False
    
    def resolver_alerta(self, alerta_id: str) -> bool:
        """Marca una alerta como resuelta."""
        for alerta in self.alertas:
            if alerta.id == alerta_id:
                alerta.resuelta = True
                logger.info(f"🚦 Tráfico.IA: Alerta {alerta_id} marcada como resuelta")
                return True
        return False
    
    def reiniciar_metricas_diarias(self):
        """Reinicia las métricas diarias (llamar a medianoche)."""
        self.metricas["alertas_generadas_hoy"] = 0
        self.metricas["emails_enviados_hoy"] = 0
        self.metricas["errores_hoy"] = 0
        logger.info("🚦 Tráfico.IA: Métricas diarias reiniciadas")


trafico_ia_service = TraficoIAService()
