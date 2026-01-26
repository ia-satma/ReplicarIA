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
    
    anthropic_configured = bool(
        os.getenv("AI_INTEGRATIONS_ANTHROPIC_API_KEY") or 
        os.getenv("ANTHROPIC_API_KEY")
    )
    
    return {
        "servicios": {
            "database": bool(os.getenv("DATABASE_URL")),
            "anthropic": anthropic_configured,
            "email": bool(os.getenv("DREAMHOST_EMAIL_PASSWORD")),
            "pcloud": bool(os.getenv("PCLOUD_USERNAME") and os.getenv("PCLOUD_PASSWORD"))
        },
        "proveedores_test": [
            {"nombre": "Software Solutions Test SA", "endpoint": "/api/test/software"},
            {"nombre": "Consultores Fiscales Test", "endpoint": "/api/test/consultoria"}
        ]
    }
