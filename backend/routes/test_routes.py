"""
API Routes para pruebas integrales de Revisar.IA
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import logging

from services.test_runner import TestRunner

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/test", tags=["tests"])


class ProveedorTestData(BaseModel):
    empresa: Dict[str, Any]
    nombre: str
    rfc: str
    tipoServicio: str
    monto: float
    fechaContrato: Optional[str] = None
    proyecto: Dict[str, Any]
    documentos: Optional[List[Dict]] = None


class TestRequest(BaseModel):
    proveedor: ProveedorTestData


class TestResponse(BaseModel):
    success: bool
    resumen: Dict[str, int]
    resultados: List[Dict[str, Any]]


# Datos de prueba predefinidos
PROVEEDOR_SOFTWARE_TEST = {
    "empresa": {
        "nombre": "Corporativo Prueba SA de CV",
        "rfc": "CPR240120XX1",
        "email": "test@revisar-ia.com",
        "telefono": "8112345678",
        "direccion": "Monterrey, NL",
        "industria": "tecnologia"
    },
    "nombre": "Software Solutions Test SA",
    "rfc": "SST200115AA1",
    "tipoServicio": "licencias_software",
    "monto": 1500000,
    "fechaContrato": "2024-01-15",
    "proyecto": {
        "nombre": "Licencias ERP Test",
        "descripcion": "Licenciamiento de sistema ERP para operaciones",
        "tipoIntangible": "software",
        "monto": 1500000
    },
    "documentos": [
        {"tipo": "contrato", "nombre": "Contrato de licenciamiento"},
        {"tipo": "factura", "nombre": "CFDI A-001"}
    ]
}

PROVEEDOR_CONSULTORIA_TEST = {
    "empresa": {
        "nombre": "Corporativo Prueba SA de CV",
        "rfc": "CPR240120XX1",
        "email": "test@revisar-ia.com",
        "telefono": "8112345678",
        "direccion": "Monterrey, NL",
        "industria": "tecnologia"
    },
    "nombre": "Consultores Fiscales Test",
    "rfc": "CFT190820BB2",
    "tipoServicio": "consultoria_fiscal",
    "monto": 3200000,
    "fechaContrato": "2024-03-01",
    "proyecto": {
        "nombre": "Asesoría Fiscal Especial Test",
        "descripcion": "Servicios de consultoría fiscal especializada",
        "tipoIntangible": "servicios_profesionales",
        "monto": 3200000
    },
    "documentos": [
        {"tipo": "contrato", "nombre": "Contrato de servicios"},
        {"tipo": "entregable", "nombre": "Informe de diagnóstico"}
    ]
}


@router.post("/full", response_model=TestResponse)
async def ejecutar_prueba_completa(request: TestRequest):
    """
    Ejecuta prueba integral completa con un proveedor.
    
    Pruebas incluidas:
    - Conexión a base de datos
    - Registro de empresa y proveedor
    - Ejecución de agentes (A1, A3, A5, A6)
    - Deliberación entre agentes
    - Generación de PDF Defense File
    - Subida a pCloud
    - Envío de email
    - Actualización de dashboard
    """
    try:
        proveedor_data = request.proveedor.model_dump()
        
        runner = TestRunner()
        resultados = await runner.ejecutar_prueba_completa(proveedor_data)
        
        exitosos = len([r for r in resultados if r["status"] == "success"])
        errores = len([r for r in resultados if r["status"] == "error"])
        warnings = len([r for r in resultados if r["status"] == "warning"])
        
        return TestResponse(
            success=errores == 0,
            resumen={
                "total": len(resultados),
                "exitosos": exitosos,
                "errores": errores,
                "warnings": warnings
            },
            resultados=resultados
        )
        
    except Exception as e:
        logger.error(f"Error en prueba integral: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/software")
async def ejecutar_prueba_software():
    """Ejecuta prueba con proveedor de software predefinido"""
    runner = TestRunner()
    resultados = await runner.ejecutar_prueba_completa(PROVEEDOR_SOFTWARE_TEST)
    
    exitosos = len([r for r in resultados if r["status"] == "success"])
    errores = len([r for r in resultados if r["status"] == "error"])
    warnings = len([r for r in resultados if r["status"] == "warning"])
    
    return {
        "success": errores == 0,
        "proveedor": "Software Solutions Test SA",
        "resumen": {
            "total": len(resultados),
            "exitosos": exitosos,
            "errores": errores,
            "warnings": warnings
        },
        "resultados": resultados
    }


@router.post("/consultoria")
async def ejecutar_prueba_consultoria():
    """Ejecuta prueba con proveedor de consultoría predefinido"""
    runner = TestRunner()
    resultados = await runner.ejecutar_prueba_completa(PROVEEDOR_CONSULTORIA_TEST)
    
    exitosos = len([r for r in resultados if r["status"] == "success"])
    errores = len([r for r in resultados if r["status"] == "error"])
    warnings = len([r for r in resultados if r["status"] == "warning"])
    
    return {
        "success": errores == 0,
        "proveedor": "Consultores Fiscales Test",
        "resumen": {
            "total": len(resultados),
            "exitosos": exitosos,
            "errores": errores,
            "warnings": warnings
        },
        "resultados": resultados
    }


@router.get("/status")
async def get_test_status():
    """Verifica el estado de los servicios para pruebas"""
    import os
    
    openai_configured = bool(os.getenv("OPENAI_API_KEY"))

    return {
        "servicios": {
            "database": bool(os.getenv("DATABASE_URL")),
            "openai": openai_configured,
            "email": bool(os.getenv("DREAMHOST_EMAIL_PASSWORD")),
            "sendgrid": bool(os.getenv("SENDGRID_API_KEY")),
            "pcloud": bool(os.getenv("PCLOUD_USERNAME") and os.getenv("PCLOUD_PASSWORD"))
        },
        "proveedores_test": [
            {"nombre": "Software Solutions Test SA", "endpoint": "/api/test/software"},
            {"nombre": "Consultores Fiscales Test", "endpoint": "/api/test/consultoria"}
        ]
    }


@router.post("/email-agents")
async def test_email_between_agents():
    """
    Prueba de emails entre agentes usando SendGrid.
    Envía emails de prueba simulando comunicación entre todos los agentes.
    """
    import os
    import httpx

    api_key = os.getenv("SENDGRID_API_KEY")
    from_email = os.getenv("SENDGRID_FROM_EMAIL", "pmo@revisar-ia.com")

    if not api_key:
        return {"success": False, "error": "SENDGRID_API_KEY no configurada"}

    # Definir los agentes y sus emails
    agents = {
        "A1_SPONSOR": {"name": "María Rodríguez", "email": "estrategia@revisar-ia.com", "role": "Dirección Estratégica"},
        "A2_PMO": {"name": "Carlos Mendoza", "email": "pmo@revisar-ia.com", "role": "Project Manager"},
        "A3_FISCAL": {"name": "Laura Sánchez", "email": "fiscal@revisar-ia.com", "role": "Especialista Fiscal"},
        "A5_FINANZAS": {"name": "Roberto Torres", "email": "finanzas@revisar-ia.com", "role": "Director Financiero"},
        "A4_LEGAL": {"name": "Ana Martínez", "email": "legal@revisar-ia.com", "role": "Directora Legal"},
        "A7_DEFENSA": {"name": "Héctor Mora", "email": "defensa@revisar-ia.com", "role": "Director Defensa Fiscal"},
        "A8_AUDITOR": {"name": "Diego Ramírez", "email": "auditoria@revisar-ia.com", "role": "Auditor"},
        "BIBLIOTECARIA": {"name": "Dra. Elena Vázquez", "email": "kb@revisar-ia.com", "role": "Gestión Conocimiento"},
    }

    # Emails de prueba a enviar
    test_emails = [
        {"from": "A2_PMO", "to": "A3_FISCAL", "subject": "[TEST] Solicitud revisión fiscal - Proyecto Fortezza"},
        {"from": "A3_FISCAL", "to": "A5_FINANZAS", "subject": "[TEST] Análisis deducibilidad completado"},
        {"from": "A5_FINANZAS", "to": "A4_LEGAL", "subject": "[TEST] Aprobación financiera - revisar contrato"},
        {"from": "A4_LEGAL", "to": "A7_DEFENSA", "subject": "[TEST] Contrato validado - preparar defense file"},
        {"from": "A7_DEFENSA", "to": "A2_PMO", "subject": "[TEST] Defense file listo para revisión"},
        {"from": "A2_PMO", "to": "BIBLIOTECARIA", "subject": "[TEST] Solicitud documentos CFF Art. 69-B"},
    ]

    results = []

    async with httpx.AsyncClient() as client:
        for email_data in test_emails:
            from_agent = agents[email_data["from"]]
            to_agent = agents[email_data["to"]]

            body_html = f"""
            <html>
            <body style="font-family: Arial, sans-serif; padding: 20px;">
                <h2 style="color: #2c5282;">📧 Email de Prueba - Revisar.IA</h2>
                <p><strong>De:</strong> {from_agent['name']} ({from_agent['role']})</p>
                <p><strong>Para:</strong> {to_agent['name']} ({to_agent['role']})</p>
                <hr style="border: 1px solid #e2e8f0;">
                <p>Este es un email de prueba del sistema multi-agente de Revisar.IA.</p>
                <p>El sistema de comunicación entre agentes está funcionando correctamente.</p>
                <br>
                <p style="color: #718096; font-size: 12px;">
                    Enviado desde: {from_agent['email']}<br>
                    Sistema: Revisar.IA Multi-Agent Platform<br>
                    Fecha: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                </p>
            </body>
            </html>
            """

            payload = {
                "personalizations": [{"to": [{"email": to_agent["email"]}]}],
                "from": {"email": from_email, "name": f"{from_agent['name']} via Revisar.IA"},
                "subject": email_data["subject"],
                "content": [{"type": "text/html", "value": body_html}]
            }

            try:
                response = await client.post(
                    "https://api.sendgrid.com/v3/mail/send",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json"
                    },
                    json=payload,
                    timeout=30.0
                )

                success = response.status_code in [200, 202]
                results.append({
                    "from": f"{from_agent['name']} <{from_agent['email']}>",
                    "to": f"{to_agent['name']} <{to_agent['email']}>",
                    "subject": email_data["subject"],
                    "status": "sent" if success else "failed",
                    "status_code": response.status_code
                })

                if success:
                    logger.info(f"✅ Email enviado: {email_data['from']} → {email_data['to']}")
                else:
                    logger.error(f"❌ Error enviando email: {response.text}")

            except Exception as e:
                results.append({
                    "from": f"{from_agent['name']} <{from_agent['email']}>",
                    "to": f"{to_agent['name']} <{to_agent['email']}>",
                    "subject": email_data["subject"],
                    "status": "error",
                    "error": str(e)
                })
                logger.error(f"❌ Error: {e}")

    sent = len([r for r in results if r["status"] == "sent"])
    failed = len([r for r in results if r["status"] != "sent"])

    return {
        "success": failed == 0,
        "summary": {
            "total": len(results),
            "sent": sent,
            "failed": failed
        },
        "results": results
    }
