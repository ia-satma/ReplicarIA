#!/usr/bin/env python3
"""
Test Script: Agent Email Greeting Test
Sends a greeting email from each configured agent/subagent to verify email delivery.
"""
import os
import sys
import time
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.dreamhost_email_service import DreamHostEmailService, AGENT_EMAILS, AGENT_NAMES

# Target email for testing
TARGET_EMAIL = "santiago@satma.mx"

# Agent descriptions for personalized introductions
AGENT_DESCRIPTIONS = {
    "A1_SPONSOR": """Soy la Directora de Estrategia del equipo Revisar.IA. 
Mi función principal es:
- Validar la RAZÓN DE NEGOCIOS de cada servicio (Art. 5-A CFF)
- Evaluar el BENEFICIO ECONÓMICO ESPERADO (BEE)
- Emitir dictamen estratégico en las fases F0/F2
- Asegurar que los servicios contratados estén alineados con los objetivos de la empresa""",
    
    "A2_PMO": """Soy el Director de PMO (Project Management Office) de Revisar.IA.
Mi función principal es:
- Coordinar el flujo completo de fases F0-F9
- Gestionar los CANDADOS de control (F2, F6, F8)
- Consolidar dictámenes de todos los agentes
- Administrar excepciones y escalamientos""",
    
    "A3_FISCAL": """Soy la Especialista Fiscal de Revisar.IA.
Mi función principal es:
- Emitir el Dictamen de Deducibilidad (LISR Art. 27)
- Verificar cumplimiento de requisitos fiscales
- Evaluar riesgo de rechazo SAT
- Validar coherencia con razón de negocios (5-A CFF)""",
    
    "A5_FINANZAS": """Soy el Director de Finanzas de Revisar.IA.
Mi función principal es:
- Calcular ROI/NPV de los servicios
- Realizar el 3-Way Match (PO = Acta = CFDI)
- Verificar razonabilidad de precios
- Evaluar impacto presupuestal""",
    
    "LEGAL": """Soy la Directora Legal de Revisar.IA.
Mi función principal es:
- Validación contractual completa
- Verificar materialidad de servicios
- Emitir dictamen legal para F6
- Revisar cláusulas y obligaciones""",
    
    "A8_AUDITOR": """Soy el Auditor Interno de Revisar.IA.
Mi función principal es:
- Auditoría documental del expediente
- Verificar cumplimiento de POE
- Control de calidad (QA) en F7
- Identificar gaps en documentación""",
    
    "A7_DEFENSA": """Soy el Especialista en Defensa Fiscal de Revisar.IA.
Mi función principal es:
- Generar Defense Files completos
- Construir argumentación legal para defensa SAT
- Consolidar evidencia de materialidad
- Preparar expedientes para controversias""",
    
    "SUB_TIPIFICACION": """Soy la Subagente de Tipificación de Revisar.IA.
Mi función principal es:
- Clasificar servicios por tipología (consultoría, tecnología, marketing, etc.)
- Asignar nivel de riesgo inherente
- Activar checklists específicos por tipo de servicio
- Determinar agentes especializados requeridos""",
    
    "SUB_MATERIALIDAD": """Soy el Subagente de Materialidad de Revisar.IA.
Mi función principal es:
- Evaluar evidencia de prestación real del servicio
- Verificar entregables tangibles
- Calcular score de materialidad
- Identificar gaps en evidencia documental""",
    
    "SUB_RIESGOS": """Soy la Subagente de Riesgos Fiscales de Revisar.IA.
Mi función principal es:
- Calcular Risk Score global del servicio
- Evaluar probabilidad de rechazo SAT
- Identificar patrones de alerta EFOS
- Emitir recomendaciones de mitigación""",
    
    "PROVEEDOR": """Soy el Módulo de Comunicaciones con Proveedores de Revisar.IA.
Mi función principal es:
- Enviar notificaciones a proveedores externos
- Solicitar documentación adicional
- Comunicar ajustes requeridos
- Coordinar respuestas de proveedores""",
    
    "BIBLIOTECARIA": """Soy la Dra. Elena Vázquez, Knowledge Base Curator de Revisar.IA.
Mi función principal es:
- Gestionar la base de conocimiento normativo
- Mantener actualizados los criterios fiscales
- Proveer contexto regulatorio a otros agentes
- Curar precedentes y jurisprudencia relevante""",
    
    "TRAFICO": """Soy el Agente de Tráfico de Revisar.IA.
Mi función principal es:
- Enrutar consultas al agente correcto
- Orquestar comunicación entre agentes
- Priorizar tareas y solicitudes
- Monitorear tiempos de respuesta""",
    
    "SOPORTE": """Soy el Soporte Técnico de Revisar.IA.
Mi función principal es:
- Asistir con problemas técnicos de la plataforma
- Guiar en el uso del sistema
- Resolver incidencias de usuarios
- Escalar problemas críticos""",
    
    "SYSTEM": """Soy el Sistema Central de Revisar.IA.
Mi función principal es:
- Enviar notificaciones automáticas del sistema
- Alertar sobre eventos importantes
- Generar reportes automatizados
- Coordinar procesos en segundo plano"""
}


def send_greeting_emails():
    """Send greeting emails from all agents to the target email."""
    
    print("=" * 60)
    print("🚀 AGENT EMAIL GREETING TEST")
    print(f"📧 Target: {TARGET_EMAIL}")
    print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Initialize email service
    email_service = DreamHostEmailService()
    
    if not email_service.initialized:
        print("❌ ERROR: Email service not initialized!")
        print("   Make sure DREAMHOST_EMAIL_PASSWORD is set in your environment.")
        return
    
    print(f"✅ Email service initialized: SMTP={email_service.smtp_host}:{email_service.smtp_port}")
    print()
    
    # Results tracking
    success_count = 0
    failure_count = 0
    results = []
    
    # Send email from each agent
    for agent_id, agent_email in AGENT_EMAILS.items():
        agent_name = AGENT_NAMES.get(agent_id, "Agente")
        description = AGENT_DESCRIPTIONS.get(agent_id, "Soy un agente de Revisar.IA.")
        
        print(f"📤 Sending from {agent_name} ({agent_email})...")
        
        subject = f"[TEST] Saludo de {agent_name} - Revisar.IA"
        
        body = f"""¡Hola Santiago!

Este es un mensaje de prueba desde el sistema de agentes de Revisar.IA.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
👤 MI PRESENTACIÓN
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{description}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 DATOS TÉCNICOS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

• Agent ID: {agent_id}
• Email Sender: {agent_email}
• Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
• Test Type: Email Delivery Verification

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Este es un correo de prueba para verificar la conectividad del sistema de emails.

Saludos cordiales,
{agent_name}
{agent_email}

--
Revisar.IA - Sistema Multi-Agente de Trazabilidad Fiscal
"""
        
        html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #1a365d 0%, #2c5282 100%); color: white; padding: 30px; text-align: center; border-radius: 8px 8px 0 0; }}
        .header h1 {{ margin: 0; font-size: 24px; }}
        .header p {{ margin: 10px 0 0 0; opacity: 0.9; }}
        .content {{ background: #ffffff; padding: 30px; border: 1px solid #e2e8f0; border-top: none; }}
        .agent-badge {{ background: #48bb78; color: white; padding: 8px 16px; border-radius: 20px; display: inline-block; margin-bottom: 20px; font-weight: bold; }}
        .section {{ background: #f7fafc; padding: 15px; border-radius: 8px; margin: 15px 0; }}
        .section h3 {{ margin: 0 0 10px 0; color: #2c5282; }}
        .tech-data {{ font-family: monospace; font-size: 12px; color: #718096; }}
        .footer {{ background: #f7fafc; padding: 20px; text-align: center; border: 1px solid #e2e8f0; border-top: none; border-radius: 0 0 8px 8px; font-size: 12px; color: #718096; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Revisar.IA</h1>
            <p>Sistema Multi-Agente de Trazabilidad Fiscal</p>
        </div>
        <div class="content">
            <span class="agent-badge">🤖 {agent_name}</span>
            
            <p>¡Hola <strong>Santiago</strong>!</p>
            
            <p>Este es un mensaje de prueba desde el sistema de agentes de Revisar.IA.</p>
            
            <div class="section">
                <h3>👤 Mi Presentación</h3>
                <p>{description.replace(chr(10), '<br>')}</p>
            </div>
            
            <div class="section tech-data">
                <h3>📊 Datos Técnicos</h3>
                <p>
                    <strong>Agent ID:</strong> {agent_id}<br>
                    <strong>Email Sender:</strong> {agent_email}<br>
                    <strong>Timestamp:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br>
                    <strong>Test Type:</strong> Email Delivery Verification
                </p>
            </div>
            
            <p>Este es un correo de prueba para verificar la conectividad del sistema de emails.</p>
            
            <p>Saludos cordiales,<br>
            <strong>{agent_name}</strong><br>
            {agent_email}</p>
        </div>
        <div class="footer">
            <p>Revisar.IA | Sistema Multi-Agente de Trazabilidad Fiscal</p>
            <p>Este es un mensaje de prueba automático.</p>
        </div>
    </div>
</body>
</html>
"""
        
        try:
            result = email_service.send_email(
                from_agent_id=agent_id,
                to_email=TARGET_EMAIL,
                subject=subject,
                body=body,
                html_body=html_body
            )
            
            if result.get("success"):
                print(f"   ✅ SUCCESS - Message ID: {result.get('message_id', 'N/A')}")
                success_count += 1
            else:
                print(f"   ❌ FAILED - Error: {result.get('error', 'Unknown')}")
                failure_count += 1
            
            results.append({
                "agent_id": agent_id,
                "agent_name": agent_name,
                "email": agent_email,
                "success": result.get("success"),
                "error": result.get("error"),
                "message_id": result.get("message_id")
            })
            
            # Small delay between emails to avoid rate limiting
            time.sleep(1)
            
        except Exception as e:
            print(f"   ❌ EXCEPTION - {str(e)}")
            failure_count += 1
            results.append({
                "agent_id": agent_id,
                "agent_name": agent_name,
                "email": agent_email,
                "success": False,
                "error": str(e)
            })
    
    # Print summary
    print()
    print("=" * 60)
    print("📊 SUMMARY")
    print("=" * 60)
    print(f"✅ Successful: {success_count}")
    print(f"❌ Failed: {failure_count}")
    print(f"📧 Total: {len(AGENT_EMAILS)}")
    print()
    
    if failure_count > 0:
        print("❌ FAILED AGENTS:")
        for r in results:
            if not r.get("success"):
                print(f"   - {r['agent_name']} ({r['email']}): {r.get('error')}")
    
    print()
    print(f"📬 Check your inbox at {TARGET_EMAIL} for {success_count} emails!")
    print("=" * 60)
    
    return results


if __name__ == "__main__":
    send_greeting_emails()
