"""
Servicio de Notificación para Proveedores
Genera checklists detallados y envía emails a proveedores con requisitos pendientes.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from checklists import get_items_por_responsable, get_items_fase, get_checklist_tipologia
from services.dreamhost_email_service import DreamHostEmailService, AGENT_EMAILS, AGENT_NAMES

logger = logging.getLogger(__name__)


class NotificacionProveedorService:
    """Servicio para gestionar comunicaciones con proveedores"""
    
    def __init__(self):
        self.email_service = DreamHostEmailService()
    
    def generar_checklist_para_proveedor(
        self,
        tipologia: str,
        fase_actual: str,
        items_cumplidos: List[str] = None,
        incluir_fases_anteriores: bool = True
    ) -> Dict[str, Any]:
        """
        Genera un checklist completo para el proveedor con sus pendientes.
        
        Args:
            tipologia: ID de tipología del proyecto
            fase_actual: Fase actual del proyecto (F0, F1, etc.)
            items_cumplidos: Lista de IDs de items ya cumplidos
            incluir_fases_anteriores: Si incluir pendientes de fases anteriores
            
        Returns:
            Diccionario con checklist estructurado para el proveedor
        """
        items_cumplidos = items_cumplidos or []
        
        items_proveedor = get_items_por_responsable(tipologia, "PROVEEDOR")
        
        if not items_proveedor:
            return {
                "tipologia": tipologia,
                "fase_actual": fase_actual,
                "total_items": 0,
                "items_pendientes": [],
                "items_completados": [],
                "mensaje": "No se encontraron items para el proveedor en esta tipología"
            }
        
        fases_orden = ["F0", "F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "F9"]
        fase_idx = fases_orden.index(fase_actual.upper()) if fase_actual.upper() in fases_orden else 9
        
        items_relevantes = []
        for item in items_proveedor:
            item_fase = item.get("fase", "F9")
            if incluir_fases_anteriores:
                item_fase_idx = fases_orden.index(item_fase) if item_fase in fases_orden else 9
                if item_fase_idx <= fase_idx:
                    items_relevantes.append(item)
            else:
                if item_fase.upper() == fase_actual.upper():
                    items_relevantes.append(item)
        
        items_pendientes = []
        items_completados = []
        
        for item in items_relevantes:
            item_data = {
                "id": item["id"],
                "descripcion": item["descripcion"],
                "fase": item.get("fase", ""),
                "obligatorio": item.get("obligatorio", False),
                "criterio_aceptacion": item.get("criterio_aceptacion", ""),
                "ejemplo_bueno": item.get("ejemplo_bueno", ""),
                "ejemplo_malo": item.get("ejemplo_malo", "")
            }
            
            if item["id"] in items_cumplidos:
                items_completados.append(item_data)
            else:
                items_pendientes.append(item_data)
        
        obligatorios_pendientes = [i for i in items_pendientes if i["obligatorio"]]
        opcionales_pendientes = [i for i in items_pendientes if not i["obligatorio"]]
        
        progreso = 0
        total_obligatorios = len([i for i in items_relevantes if i.get("obligatorio")])
        if total_obligatorios > 0:
            completados_obligatorios = len([i for i in items_completados if i["obligatorio"]])
            progreso = round((completados_obligatorios / total_obligatorios) * 100)
        
        return {
            "tipologia": tipologia,
            "fase_actual": fase_actual,
            "total_items": len(items_relevantes),
            "items_pendientes": items_pendientes,
            "obligatorios_pendientes": obligatorios_pendientes,
            "opcionales_pendientes": opcionales_pendientes,
            "items_completados": items_completados,
            "progreso_porcentaje": progreso,
            "puede_avanzar": len(obligatorios_pendientes) == 0,
            "resumen": {
                "total": len(items_relevantes),
                "completados": len(items_completados),
                "pendientes": len(items_pendientes),
                "obligatorios_pendientes": len(obligatorios_pendientes)
            }
        }
    
    def _generar_mensaje_proveedor(
        self,
        proyecto_nombre: str,
        proyecto_folio: str,
        checklist: Dict[str, Any],
        tipo_mensaje: str = "pendientes"
    ) -> str:
        """
        Genera el mensaje humanizado para enviar al proveedor.
        
        Args:
            proyecto_nombre: Nombre del proyecto
            proyecto_folio: Folio del proyecto
            checklist: Datos del checklist generado
            tipo_mensaje: 'pendientes', 'rechazo', 'aprobacion'
            
        Returns:
            Mensaje formateado en HTML
        """
        fecha = datetime.now().strftime("%d de %B de %Y")
        
        obligatorios = checklist.get("obligatorios_pendientes", [])
        opcionales = checklist.get("opcionales_pendientes", [])
        progreso = checklist.get("progreso_porcentaje", 0)
        
        if tipo_mensaje == "rechazo":
            asunto_tipo = "ACCIÓN REQUERIDA"
            intro = f"""
            <p style="color: #c53030; font-weight: bold;">
                Se han identificado documentos faltantes que deben ser proporcionados 
                antes de poder continuar con la revisión del expediente.
            </p>
            """
        elif tipo_mensaje == "aprobacion":
            asunto_tipo = "CONFIRMACIÓN"
            intro = f"""
            <p style="color: #276749; font-weight: bold;">
                ¡Felicidades! Todos los documentos requeridos han sido recibidos y validados.
            </p>
            """
        else:
            asunto_tipo = "RECORDATORIO"
            intro = f"""
            <p>
                Le compartimos el estado actual de los documentos pendientes para el proyecto.
            </p>
            """
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #1a365d 0%, #2a4a6d 100%); color: white; padding: 20px; border-radius: 8px 8px 0 0; }}
                .content {{ background: #f7fafc; padding: 20px; border: 1px solid #e2e8f0; }}
                .footer {{ background: #edf2f7; padding: 15px; font-size: 12px; color: #718096; border-radius: 0 0 8px 8px; }}
                .item {{ background: white; padding: 15px; margin: 10px 0; border-radius: 6px; border-left: 4px solid #3182ce; }}
                .item.obligatorio {{ border-left-color: #e53e3e; }}
                .item-id {{ font-family: monospace; font-size: 11px; color: #718096; }}
                .badge {{ display: inline-block; padding: 2px 8px; border-radius: 12px; font-size: 11px; font-weight: bold; }}
                .badge.obligatorio {{ background: #fed7d7; color: #c53030; }}
                .badge.opcional {{ background: #bee3f8; color: #2b6cb0; }}
                .progress {{ background: #e2e8f0; border-radius: 10px; height: 20px; margin: 10px 0; overflow: hidden; }}
                .progress-bar {{ background: #48bb78; height: 100%; transition: width 0.3s; }}
                .criterio {{ font-size: 13px; color: #4a5568; margin-top: 8px; padding: 8px; background: #f0fff4; border-radius: 4px; }}
                .ejemplo {{ font-size: 12px; margin-top: 5px; }}
                .ejemplo.bueno {{ color: #276749; }}
                .ejemplo.malo {{ color: #c53030; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2 style="margin: 0;">📋 Checklist de Documentos - {asunto_tipo}</h2>
                    <p style="margin: 5px 0 0 0; opacity: 0.9;">Proyecto: {proyecto_nombre}</p>
                    <p style="margin: 5px 0 0 0; font-family: monospace; opacity: 0.8;">Folio: {proyecto_folio}</p>
                </div>
                
                <div class="content">
                    <p>Estimado Proveedor,</p>
                    <p>{fecha}</p>
                    
                    {intro}
                    
                    <h3>📊 Progreso Actual: {progreso}%</h3>
                    <div class="progress">
                        <div class="progress-bar" style="width: {progreso}%"></div>
                    </div>
        """
        
        if obligatorios:
            html += """
                    <h3 style="color: #c53030;">🔴 Documentos Obligatorios Pendientes</h3>
                    <p style="font-size: 13px; color: #718096;">
                        Estos documentos son indispensables para continuar el proceso.
                    </p>
            """
            
            for item in obligatorios:
                html += f"""
                    <div class="item obligatorio">
                        <div style="display: flex; justify-content: space-between; align-items: start;">
                            <strong>{item['descripcion']}</strong>
                            <span class="badge obligatorio">OBLIGATORIO</span>
                        </div>
                        <div class="item-id">ID: {item['id']} | Fase: {item['fase']}</div>
                """
                
                if item.get('criterio_aceptacion'):
                    html += f"""
                        <div class="criterio">
                            <strong>✓ Criterio de aceptación:</strong><br>
                            {item['criterio_aceptacion']}
                        </div>
                    """
                
                if item.get('ejemplo_bueno'):
                    html += f"""
                        <div class="ejemplo bueno">
                            ✅ <strong>Ejemplo válido:</strong> {item['ejemplo_bueno']}
                        </div>
                    """
                
                if item.get('ejemplo_malo'):
                    html += f"""
                        <div class="ejemplo malo">
                            ❌ <strong>Evitar:</strong> {item['ejemplo_malo']}
                        </div>
                    """
                
                html += "</div>"
        
        if opcionales:
            html += """
                    <h3 style="color: #2b6cb0; margin-top: 30px;">🔵 Documentos Opcionales</h3>
                    <p style="font-size: 13px; color: #718096;">
                        Estos documentos no son obligatorios pero fortalecen el expediente.
                    </p>
            """
            
            for item in opcionales:
                html += f"""
                    <div class="item">
                        <div style="display: flex; justify-content: space-between; align-items: start;">
                            <strong>{item['descripcion']}</strong>
                            <span class="badge opcional">OPCIONAL</span>
                        </div>
                        <div class="item-id">ID: {item['id']} | Fase: {item['fase']}</div>
                    </div>
                """
        
        html += f"""
                    <div style="margin-top: 30px; padding: 15px; background: #ebf8ff; border-radius: 6px;">
                        <h4 style="margin: 0 0 10px 0; color: #2b6cb0;">📬 ¿Cómo entregar los documentos?</h4>
                        <p style="margin: 0; font-size: 14px;">
                            Puede responder a este correo adjuntando los documentos solicitados,
                            o subirlos directamente al portal del proyecto usando el folio: <strong>{proyecto_folio}</strong>
                        </p>
                    </div>
                </div>
                
                <div class="footer">
                    <p style="margin: 0;">
                        Este mensaje fue generado automáticamente por el sistema Revisar.ia<br>
                        Para dudas o aclaraciones, contacte a su ejecutivo asignado.
                    </p>
                    <p style="margin: 10px 0 0 0; font-style: italic;">
                        Revisar.ia - Sistema de Trazabilidad de Servicios Intangibles
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html
    
    async def enviar_checklist_proveedor(
        self,
        email_proveedor: str,
        proyecto_id: str,
        proyecto_nombre: str,
        proyecto_folio: str,
        tipologia: str,
        fase_actual: str,
        items_cumplidos: List[str] = None,
        tipo_mensaje: str = "pendientes"
    ) -> Dict[str, Any]:
        """
        Envía el checklist de pendientes al proveedor por email.
        
        Args:
            email_proveedor: Email del proveedor
            proyecto_id: ID del proyecto
            proyecto_nombre: Nombre del proyecto
            proyecto_folio: Folio del proyecto
            tipologia: Tipología del servicio
            fase_actual: Fase actual
            items_cumplidos: Items ya entregados
            tipo_mensaje: Tipo de email (pendientes, rechazo, aprobacion)
            
        Returns:
            Resultado del envío
        """
        checklist = self.generar_checklist_para_proveedor(
            tipologia=tipologia,
            fase_actual=fase_actual,
            items_cumplidos=items_cumplidos
        )
        
        if len(checklist.get("items_pendientes", [])) == 0:
            return {
                "success": True,
                "enviado": False,
                "mensaje": "No hay items pendientes para notificar",
                "checklist": checklist
            }
        
        html_body = self._generar_mensaje_proveedor(
            proyecto_nombre=proyecto_nombre,
            proyecto_folio=proyecto_folio,
            checklist=checklist,
            tipo_mensaje=tipo_mensaje
        )
        
        asuntos = {
            "pendientes": f"📋 Checklist de Documentos Pendientes - {proyecto_folio}",
            "rechazo": f"⚠️ Documentos Requeridos - Acción Necesaria - {proyecto_folio}",
            "aprobacion": f"✅ Documentos Completos - {proyecto_folio}"
        }
        
        asunto = asuntos.get(tipo_mensaje, asuntos["pendientes"])
        
        resultado = self.email_service.send_email(
            from_agent_id="PROVEEDOR",
            to_email=email_proveedor,
            subject=asunto,
            body=f"Por favor vea el contenido HTML de este correo para ver el checklist completo.",
            html_body=html_body
        )
        
        return {
            "success": resultado.get("success", False),
            "enviado": resultado.get("success", False),
            "mensaje": "Checklist enviado exitosamente" if resultado.get("success") else "Error al enviar",
            "email_destino": email_proveedor,
            "items_notificados": len(checklist.get("items_pendientes", [])),
            "detalle_envio": resultado,
            "checklist": checklist
        }
    
    def generar_email_rechazo_con_checklist(
        self,
        proyecto_nombre: str,
        proyecto_folio: str,
        tipologia: str,
        fase_actual: str,
        motivo_rechazo: str,
        items_faltantes: List[str] = None
    ) -> Dict[str, Any]:
        """
        Genera un email de rechazo con el checklist de items faltantes.
        
        Args:
            proyecto_nombre: Nombre del proyecto
            proyecto_folio: Folio del proyecto
            tipologia: Tipología del servicio
            fase_actual: Fase actual
            motivo_rechazo: Motivo general del rechazo
            items_faltantes: Lista de IDs de items que faltan
            
        Returns:
            Diccionario con email generado listo para enviar
        """
        items_cumplidos = []
        if items_faltantes:
            todos_items = get_items_por_responsable(tipologia, "PROVEEDOR")
            todos_ids = [i["id"] for i in todos_items]
            items_cumplidos = [id for id in todos_ids if id not in items_faltantes]
        
        checklist = self.generar_checklist_para_proveedor(
            tipologia=tipologia,
            fase_actual=fase_actual,
            items_cumplidos=items_cumplidos
        )
        
        html_body = self._generar_mensaje_proveedor(
            proyecto_nombre=proyecto_nombre,
            proyecto_folio=proyecto_folio,
            checklist=checklist,
            tipo_mensaje="rechazo"
        )
        
        motivo_html = f"""
        <div style="background: #fff5f5; border: 1px solid #fc8181; border-radius: 6px; padding: 15px; margin: 15px 0;">
            <h4 style="color: #c53030; margin: 0 0 10px 0;">📌 Motivo del Rechazo</h4>
            <p style="margin: 0; color: #742a2a;">{motivo_rechazo}</p>
        </div>
        """
        
        html_body = html_body.replace("</h3>\n                    <div class=\"progress\">", 
                                      f"</h3>{motivo_html}\n                    <div class=\"progress\">")
        
        return {
            "asunto": f"⚠️ Solicitud de Ajustes - {proyecto_folio}",
            "html_body": html_body,
            "checklist": checklist,
            "motivo_rechazo": motivo_rechazo
        }


notificacion_proveedor_service = NotificacionProveedorService()
