"""
Diseñar.IA - Guardián Autónomo de Diseño UI
Rutas API para auditoría de diseño, detección de inconsistencias
y sugerencias de mejora basadas en mejores prácticas de UX/UI.
"""

from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import base64
import logging

from services.disenar_ia_service import disenar_service
from config.design_system import COLORES, TIPOGRAFIAS, BREAKPOINTS, COMPONENTES

logger = logging.getLogger(__name__)

router = APIRouter()


class ChatMessage(BaseModel):
    """Modelo para mensajes de chat con Diseñar.IA."""
    message: str = Field(..., description="Mensaje del usuario")
    history: Optional[List[dict]] = Field(default=[], description="Historial de conversación")


class AuditarComponenteRequest(BaseModel):
    """Request para auditar un componente específico."""
    ruta_componente: str = Field(..., description="Ruta relativa del componente (ej: components/Button.jsx)")
    contenido: Optional[str] = Field(None, description="Contenido del componente (opcional, se lee del archivo si no se proporciona)")


class AuditarPaginaRequest(BaseModel):
    """Request para auditar una página completa."""
    ruta_pagina: str = Field(..., description="Ruta relativa de la página (ej: pages/Dashboard.jsx)")
    incluir_componentes: bool = Field(True, description="Si incluir análisis de componentes importados")


class AnalizarScreenshotRequest(BaseModel):
    """Request para analizar un screenshot con IA."""
    imagen_base64: str = Field(..., description="Imagen en formato base64")
    contexto: Optional[str] = Field(None, description="Contexto adicional sobre la pantalla (ej: 'página de login', 'dashboard móvil')")


@router.get("/status")
async def obtener_status():
    """
    Obtiene el estado actual del servicio Diseñar.IA.
    
    Retorna:
    - Estado del servicio (activo/degradado)
    - Disponibilidad de IA
    - Métricas generales
    - Categorías y niveles de severidad disponibles
    """
    try:
        status = disenar_service.obtener_status()
        logger.info("🎨 Diseñar.IA: Status consultado")
        return {
            "success": True,
            **status
        }
    except Exception as e:
        logger.error(f"❌ Diseñar.IA: Error obteniendo status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/auditar-componente")
async def auditar_componente(request: AuditarComponenteRequest):
    """
    Audita un componente específico de la UI.
    
    Analiza:
    - Uso de colores del design system
    - Accesibilidad (alt en imágenes, labels en inputs)
    - Patrones responsive
    - Estilos inline
    - Estados de carga y error
    
    Retorna un reporte con score, problemas detectados y sugerencias.
    """
    try:
        logger.info(f"🎨 Diseñar.IA: Auditando componente {request.ruta_componente}")
        
        resultado = await disenar_service.auditar_componente(
            ruta_componente=request.ruta_componente,
            contenido=request.contenido
        )
        
        return {
            "success": True,
            **resultado
        }
    except Exception as e:
        logger.error(f"❌ Diseñar.IA: Error auditando componente: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/auditar-pagina")
async def auditar_pagina(request: AuditarPaginaRequest):
    """
    Audita una página completa incluyendo sus componentes importados.
    
    Analiza:
    - Código de la página principal
    - Componentes importados (opcional)
    - Hooks y estados utilizados
    - Patrones de manejo de errores y loading
    
    Retorna un reporte integral con métricas y problemas.
    """
    try:
        logger.info(f"🎨 Diseñar.IA: Auditando página {request.ruta_pagina}")
        
        resultado = await disenar_service.auditar_pagina(
            ruta_pagina=request.ruta_pagina,
            incluir_componentes=request.incluir_componentes
        )
        
        return {
            "success": True,
            **resultado
        }
    except Exception as e:
        logger.error(f"❌ Diseñar.IA: Error auditando página: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/reportes")
async def obtener_reportes(limite: int = 20):
    """
    Obtiene el historial de reportes de auditoría.
    
    Parámetros:
    - limite: Número máximo de reportes a retornar (default: 20)
    
    Retorna lista de reportes ordenados por fecha (más recientes primero).
    """
    try:
        reportes = disenar_service.obtener_reportes(limite=limite)
        logger.info(f"🎨 Diseñar.IA: {len(reportes)} reportes consultados")
        return {
            "success": True,
            "reportes": reportes,
            "total": len(reportes)
        }
    except Exception as e:
        logger.error(f"❌ Diseñar.IA: Error obteniendo reportes: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recomendaciones")
async def obtener_recomendaciones(solo_pendientes: bool = True):
    """
    Obtiene las recomendaciones activas de mejora de diseño.
    
    Parámetros:
    - solo_pendientes: Si solo retornar recomendaciones no aplicadas (default: True)
    
    Las recomendaciones incluyen:
    - Título y descripción del problema
    - Prioridad (alta/media/baja)
    - Ejemplos de código cuando aplica
    - Categoría de auditoría
    """
    try:
        recomendaciones = disenar_service.obtener_recomendaciones(solo_pendientes=solo_pendientes)
        logger.info(f"🎨 Diseñar.IA: {len(recomendaciones)} recomendaciones consultadas")
        return {
            "success": True,
            "recomendaciones": recomendaciones,
            "total": len(recomendaciones),
            "solo_pendientes": solo_pendientes
        }
    except Exception as e:
        logger.error(f"❌ Diseñar.IA: Error obteniendo recomendaciones: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analizar-screenshot")
async def analizar_screenshot(request: AnalizarScreenshotRequest):
    """
    Analiza un screenshot de la UI usando visión de IA.
    
    Detecta problemas de:
    - Accesibilidad (contraste, tamaños de fuente)
    - Consistencia visual
    - Responsive design
    - Usabilidad y UX
    - Branding
    
    Requiere que Anthropic API esté configurada.
    """
    try:
        logger.info("🎨 Diseñar.IA: Analizando screenshot con IA")
        
        imagen_base64 = request.imagen_base64
        if imagen_base64.startswith('data:image'):
            imagen_base64 = imagen_base64.split(',')[1]
        
        resultado = await disenar_service.analizar_screenshot(
            imagen_base64=imagen_base64,
            contexto=request.contexto
        )
        
        if not resultado.get('success'):
            raise HTTPException(status_code=500, detail=resultado.get('error', 'Error desconocido'))
        
        return resultado
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Diseñar.IA: Error analizando screenshot: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analizar-screenshot-upload")
async def analizar_screenshot_upload(
    file: UploadFile = File(...),
    contexto: Optional[str] = None
):
    """
    Analiza un screenshot subido como archivo.
    
    Alternativa a analizar-screenshot para subir imágenes directamente.
    Soporta PNG, JPG, JPEG, WEBP.
    """
    try:
        if not file.content_type or not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="El archivo debe ser una imagen")
        
        contenido = await file.read()
        imagen_base64 = base64.b64encode(contenido).decode('utf-8')
        
        resultado = await disenar_service.analizar_screenshot(
            imagen_base64=imagen_base64,
            contexto=contexto
        )
        
        if not resultado.get('success'):
            raise HTTPException(status_code=500, detail=resultado.get('error', 'Error desconocido'))
        
        return resultado
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Diseñar.IA: Error procesando screenshot: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metricas-ui")
async def obtener_metricas_ui():
    """
    Obtiene métricas detalladas de calidad UI.
    
    Retorna:
    - Resumen de auditorías realizadas
    - Problemas por categoría y severidad
    - Tendencia de scores
    - Áreas críticas que requieren atención
    """
    try:
        metricas = disenar_service.obtener_metricas_ui()
        logger.info("🎨 Diseñar.IA: Métricas UI consultadas")
        return {
            "success": True,
            **metricas
        }
    except Exception as e:
        logger.error(f"❌ Diseñar.IA: Error obteniendo métricas UI: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/auditoria")
async def ejecutar_auditoria():
    """Ejecuta auditoría completa del diseño frontend."""
    try:
        resultado = disenar_service.auditar_todo()
        logger.info(f"🎨 Diseñar.IA: Auditoría completa - Score: {resultado.get('score_general', 0)}")
        return {
            'success': True,
            **resultado
        }
    except Exception as e:
        logger.error(f"❌ Diseñar.IA: Error en auditoría: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/auditoria")
async def ejecutar_auditoria_post():
    """Ejecuta auditoría completa del diseño (POST)."""
    return await ejecutar_auditoria()


@router.get("/design-system")
async def obtener_design_system():
    """Retorna el design system completo de la plataforma."""
    return {
        'success': True,
        'colores': COLORES,
        'tipografias': TIPOGRAFIAS,
        'breakpoints': BREAKPOINTS,
        'componentes': COMPONENTES
    }


@router.get("/sugerencias")
async def obtener_sugerencias():
    """Retorna sugerencias de nuevas tecnologías a implementar."""
    return {
        'success': True,
        'sugerencias': disenar_service.generar_sugerencias_tecnologias()
    }


@router.get("/auditoria/colores")
async def auditar_colores():
    """Audita solo colorimetría del frontend."""
    try:
        return {
            'success': True,
            'resultado': disenar_service.auditar_colores()
        }
    except Exception as e:
        logger.error(f"❌ Diseñar.IA: Error en auditoría de colores: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/auditoria/responsive")
async def auditar_responsive():
    """Audita solo responsive/móvil del frontend."""
    try:
        return {
            'success': True,
            'resultado': disenar_service.auditar_responsive()
        }
    except Exception as e:
        logger.error(f"❌ Diseñar.IA: Error en auditoría responsive: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/auditoria/tipografia")
async def auditar_tipografia():
    """Audita solo tipografías del frontend."""
    try:
        return {
            'success': True,
            'resultado': disenar_service.auditar_tipografias()
        }
    except Exception as e:
        logger.error(f"❌ Diseñar.IA: Error en auditoría de tipografía: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/auditoria/accesibilidad")
async def auditar_accesibilidad():
    """Audita accesibilidad (WCAG 2.1) del frontend."""
    try:
        return {
            'success': True,
            'resultado': disenar_service.auditar_accesibilidad()
        }
    except Exception as e:
        logger.error(f"❌ Diseñar.IA: Error en auditoría de accesibilidad: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/auditoria/rendimiento")
async def auditar_rendimiento():
    """Audita rendimiento CSS y patrones de React."""
    try:
        return {
            'success': True,
            'resultado': disenar_service.auditar_rendimiento()
        }
    except Exception as e:
        logger.error(f"❌ Diseñar.IA: Error en auditoría de rendimiento: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/auditoria/componentes")
async def auditar_componentes():
    """Audita consistencia de componentes UI."""
    try:
        return {
            'success': True,
            'resultado': disenar_service.auditar_componentes()
        }
    except Exception as e:
        logger.error(f"❌ Diseñar.IA: Error en auditoría de componentes: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat")
async def chat_disenar(data: ChatMessage):
    """
    Chat interactivo con el agente Diseñar.IA.
    
    Permite hacer preguntas sobre:
    - Mejores prácticas de diseño
    - Problemas específicos de UI/UX
    - Sugerencias de mejora
    - Uso del design system
    """
    try:
        if not data.message:
            raise HTTPException(status_code=400, detail="Mensaje requerido")
        
        resultado = await disenar_service.chat(
            mensaje=data.message,
            history=data.history
        )
        
        if not resultado.get('success'):
            raise HTTPException(status_code=500, detail=resultado.get('error', 'Error desconocido'))
        
        return resultado
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Diseñar.IA: Error en chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))
