"""
Defense File API Routes - Rutas para el sistema de expedientes de defensa
Endpoints RESTful para gestión de expedientes, eventos, proveedores, CFDIs, fundamentos y cálculos
"""
import logging
import io
import hashlib
from datetime import date, datetime
from typing import Optional, List, Dict, Any
from decimal import Decimal

from fastapi import APIRouter, HTTPException, Query, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from services.defense_file_pg_service import defense_file_pg_service, TipoEvento, Agente, EstadoExpediente
from services.pcloud_service import pcloud_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/defense-files", tags=["Defense Files"])


class CreateDefenseFileRequest(BaseModel):
    cliente_id: int
    nombre: str
    anio_fiscal: int
    descripcion: Optional[str] = None
    entregable_id: Optional[int] = None
    periodo_inicio: Optional[date] = None
    periodo_fin: Optional[date] = None
    created_by: Optional[int] = None
    contribuyente_rfc: Optional[str] = None
    contribuyente_nombre: Optional[str] = None
    regimen_fiscal: Optional[str] = None
    tipo_revision: Optional[str] = None


class RegistrarEventoRequest(BaseModel):
    tipo: str
    agente: str
    titulo: str
    descripcion: Optional[str] = None
    datos: Optional[Dict[str, Any]] = None
    subtipo: Optional[str] = None
    usuario_id: Optional[int] = None
    usuario_email: Optional[str] = None
    archivos: Optional[List[Dict[str, Any]]] = None
    tags: Optional[List[str]] = None


class RegistrarProveedorRequest(BaseModel):
    rfc: str
    razon_social: Optional[str] = None
    nombre_comercial: Optional[str] = None
    lista_69b_status: Optional[str] = None
    lista_69b_fecha: Optional[date] = None
    efos_status: Optional[str] = None
    efos_fecha: Optional[date] = None
    opinion_cumplimiento: Optional[str] = None
    opinion_fecha: Optional[date] = None
    nivel_riesgo: Optional[str] = None
    notas_riesgo: Optional[str] = None


class RegistrarCFDIRequest(BaseModel):
    uuid: str
    proveedor_id: Optional[int] = None
    serie: Optional[str] = None
    folio: Optional[str] = None
    emisor_rfc: Optional[str] = None
    emisor_nombre: Optional[str] = None
    receptor_rfc: Optional[str] = None
    receptor_nombre: Optional[str] = None
    subtotal: Optional[float] = None
    descuento: Optional[float] = None
    iva: Optional[float] = None
    isr_retenido: Optional[float] = None
    iva_retenido: Optional[float] = None
    total: Optional[float] = None
    fecha_emision: Optional[datetime] = None
    fecha_timbrado: Optional[datetime] = None
    fecha_pago: Optional[date] = None
    tipo_comprobante: Optional[str] = None
    metodo_pago: Optional[str] = None
    forma_pago: Optional[str] = None
    uso_cfdi: Optional[str] = None
    status_sat: Optional[str] = None
    categoria_deduccion: Optional[str] = None
    es_deducible: Optional[bool] = None
    justificacion_deduccion: Optional[str] = None
    nivel_riesgo: Optional[str] = None
    xml_path: Optional[str] = None
    pdf_path: Optional[str] = None


class RegistrarFundamentoRequest(BaseModel):
    tipo: str
    documento: str
    articulo: str
    texto_relevante: Optional[str] = None
    fraccion: Optional[str] = None
    parrafo: Optional[str] = None
    titulo: Optional[str] = None
    aplicacion: Optional[str] = None
    usado_en_eventos: Optional[List[int]] = None
    kb_documento_id: Optional[int] = None
    kb_chunk_ids: Optional[List[int]] = None


class RegistrarCalculoRequest(BaseModel):
    tipo: str
    periodo: str
    concepto: Optional[str] = None
    base_gravable: Optional[float] = None
    tasa: Optional[float] = None
    impuesto_calculado: Optional[float] = None
    formula_aplicada: Optional[str] = None
    datos_entrada: Optional[Dict[str, Any]] = None
    resultado: Optional[Dict[str, Any]] = None
    fundamento_legal: Optional[str] = None
    notas: Optional[str] = None
    calculado_por: Optional[str] = None
    revisado_por: Optional[int] = None


class CerrarExpedienteRequest(BaseModel):
    usuario_id: Optional[int] = None


@router.get("/stats")
async def obtener_estadisticas_globales(
    cliente_id: Optional[int] = Query(None, description="Filtrar por cliente"),
    anio_fiscal: Optional[int] = Query(None, description="Filtrar por año fiscal")
):
    """Obtiene estadísticas globales de todos los expedientes."""
    try:
        result = await defense_file_pg_service.obtener_estadisticas_globales(
            cliente_id=cliente_id,
            anio_fiscal=anio_fiscal
        )
        if not result.get('success'):
            raise HTTPException(status_code=500, detail=result.get('error', 'Error desconocido'))
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"📁 Defense Files API: Error en estadísticas globales: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("")
async def listar_defense_files(
    cliente_id: Optional[int] = Query(None, description="Filtrar por cliente"),
    estado: Optional[str] = Query(None, description="Filtrar por estado"),
    anio_fiscal: Optional[int] = Query(None, description="Filtrar por año fiscal"),
    limit: int = Query(100, ge=1, le=1000, description="Límite de resultados"),
    offset: int = Query(0, ge=0, description="Offset para paginación")
):
    """Lista todos los expedientes de defensa con filtros opcionales."""
    try:
        result = await defense_file_pg_service.listar_defense_files(
            cliente_id=cliente_id,
            estado=estado,
            anio_fiscal=anio_fiscal,
            limit=limit,
            offset=offset
        )
        if not result.get('success'):
            raise HTTPException(status_code=500, detail=result.get('error', 'Error desconocido'))
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"📁 Defense Files API: Error al listar expedientes: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("")
async def crear_defense_file(request: CreateDefenseFileRequest):
    """Crea un nuevo expediente de defensa."""
    try:
        result = await defense_file_pg_service.crear_defense_file(
            cliente_id=request.cliente_id,
            nombre=request.nombre,
            anio_fiscal=request.anio_fiscal,
            descripcion=request.descripcion,
            entregable_id=request.entregable_id,
            periodo_inicio=request.periodo_inicio,
            periodo_fin=request.periodo_fin,
            created_by=request.created_by,
            contribuyente_rfc=request.contribuyente_rfc,
            contribuyente_nombre=request.contribuyente_nombre,
            regimen_fiscal=request.regimen_fiscal,
            tipo_revision=request.tipo_revision
        )
        if not result.get('success'):
            raise HTTPException(status_code=400, detail=result.get('error', 'Error al crear expediente'))
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"📁 Defense Files API: Error al crear expediente: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{defense_file_id}")
async def obtener_defense_file(defense_file_id: int):
    """Obtiene un expediente de defensa por su ID."""
    try:
        result = await defense_file_pg_service.obtener_defense_file(defense_file_id)
        if not result.get('success'):
            raise HTTPException(status_code=404, detail=result.get('error', 'Expediente no encontrado'))
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"📁 Defense Files API: Error al obtener expediente {defense_file_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{defense_file_id}/timeline")
async def obtener_timeline(defense_file_id: int):
    """Obtiene el timeline completo de eventos del expediente."""
    try:
        result = await defense_file_pg_service.obtener_timeline(defense_file_id)
        if not result.get('success'):
            raise HTTPException(status_code=500, detail=result.get('error', 'Error al obtener timeline'))
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"📁 Defense Files API: Error al obtener timeline {defense_file_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{defense_file_id}/eventos")
async def registrar_evento(defense_file_id: int, request: RegistrarEventoRequest):
    """Registra un nuevo evento en la bitácora del expediente."""
    try:
        result = await defense_file_pg_service.registrar_evento(
            defense_file_id=defense_file_id,
            tipo=request.tipo,
            agente=request.agente,
            titulo=request.titulo,
            descripcion=request.descripcion,
            datos=request.datos,
            subtipo=request.subtipo,
            usuario_id=request.usuario_id,
            usuario_email=request.usuario_email,
            archivos=request.archivos,
            tags=request.tags
        )
        if not result.get('success'):
            raise HTTPException(status_code=400, detail=result.get('error', 'Error al registrar evento'))
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"📁 Defense Files API: Error al registrar evento: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{defense_file_id}/proveedores")
async def listar_proveedores(defense_file_id: int):
    """Lista los proveedores asociados al expediente."""
    try:
        result = await defense_file_pg_service.listar_proveedores(defense_file_id)
        if not result.get('success'):
            raise HTTPException(status_code=500, detail=result.get('error', 'Error al listar proveedores'))
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"📁 Defense Files API: Error al listar proveedores: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{defense_file_id}/proveedores")
async def registrar_proveedor(defense_file_id: int, request: RegistrarProveedorRequest):
    """Registra un nuevo proveedor en el expediente."""
    try:
        result = await defense_file_pg_service.registrar_proveedor(
            defense_file_id=defense_file_id,
            rfc=request.rfc,
            razon_social=request.razon_social,
            nombre_comercial=request.nombre_comercial,
            lista_69b_status=request.lista_69b_status,
            lista_69b_fecha=request.lista_69b_fecha,
            efos_status=request.efos_status,
            efos_fecha=request.efos_fecha,
            opinion_cumplimiento=request.opinion_cumplimiento,
            opinion_fecha=request.opinion_fecha,
            nivel_riesgo=request.nivel_riesgo,
            notas_riesgo=request.notas_riesgo
        )
        if not result.get('success'):
            raise HTTPException(status_code=400, detail=result.get('error', 'Error al registrar proveedor'))
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"📁 Defense Files API: Error al registrar proveedor: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{defense_file_id}/cfdis")
async def listar_cfdis(
    defense_file_id: int,
    proveedor_id: Optional[int] = Query(None, description="Filtrar por proveedor")
):
    """Lista los CFDIs asociados al expediente."""
    try:
        result = await defense_file_pg_service.listar_cfdis(
            defense_file_id=defense_file_id,
            proveedor_id=proveedor_id
        )
        if not result.get('success'):
            raise HTTPException(status_code=500, detail=result.get('error', 'Error al listar CFDIs'))
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"📁 Defense Files API: Error al listar CFDIs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{defense_file_id}/cfdis")
async def registrar_cfdi(defense_file_id: int, request: RegistrarCFDIRequest):
    """Registra un nuevo CFDI en el expediente."""
    try:
        result = await defense_file_pg_service.registrar_cfdi(
            defense_file_id=defense_file_id,
            uuid=request.uuid,
            proveedor_id=request.proveedor_id,
            serie=request.serie,
            folio=request.folio,
            emisor_rfc=request.emisor_rfc,
            emisor_nombre=request.emisor_nombre,
            receptor_rfc=request.receptor_rfc,
            receptor_nombre=request.receptor_nombre,
            subtotal=Decimal(str(request.subtotal)) if request.subtotal else None,
            descuento=Decimal(str(request.descuento)) if request.descuento else None,
            iva=Decimal(str(request.iva)) if request.iva else None,
            isr_retenido=Decimal(str(request.isr_retenido)) if request.isr_retenido else None,
            iva_retenido=Decimal(str(request.iva_retenido)) if request.iva_retenido else None,
            total=Decimal(str(request.total)) if request.total else None,
            fecha_emision=request.fecha_emision,
            fecha_timbrado=request.fecha_timbrado,
            fecha_pago=request.fecha_pago,
            tipo_comprobante=request.tipo_comprobante,
            metodo_pago=request.metodo_pago,
            forma_pago=request.forma_pago,
            uso_cfdi=request.uso_cfdi,
            status_sat=request.status_sat,
            categoria_deduccion=request.categoria_deduccion,
            es_deducible=request.es_deducible,
            justificacion_deduccion=request.justificacion_deduccion,
            nivel_riesgo=request.nivel_riesgo,
            xml_path=request.xml_path,
            pdf_path=request.pdf_path
        )
        if not result.get('success'):
            raise HTTPException(status_code=400, detail=result.get('error', 'Error al registrar CFDI'))
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"📁 Defense Files API: Error al registrar CFDI: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{defense_file_id}/fundamentos")
async def listar_fundamentos(defense_file_id: int):
    """Lista los fundamentos legales asociados al expediente."""
    try:
        result = await defense_file_pg_service.listar_fundamentos(defense_file_id)
        if not result.get('success'):
            raise HTTPException(status_code=500, detail=result.get('error', 'Error al listar fundamentos'))
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"📁 Defense Files API: Error al listar fundamentos: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{defense_file_id}/fundamentos")
async def registrar_fundamento(defense_file_id: int, request: RegistrarFundamentoRequest):
    """Registra un nuevo fundamento legal en el expediente."""
    try:
        result = await defense_file_pg_service.registrar_fundamento(
            defense_file_id=defense_file_id,
            tipo=request.tipo,
            documento=request.documento,
            articulo=request.articulo,
            texto_relevante=request.texto_relevante,
            fraccion=request.fraccion,
            parrafo=request.parrafo,
            titulo=request.titulo,
            aplicacion=request.aplicacion,
            usado_en_eventos=request.usado_en_eventos,
            kb_documento_id=request.kb_documento_id,
            kb_chunk_ids=request.kb_chunk_ids
        )
        if not result.get('success'):
            raise HTTPException(status_code=400, detail=result.get('error', 'Error al registrar fundamento'))
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"📁 Defense Files API: Error al registrar fundamento: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{defense_file_id}/calculos")
async def listar_calculos(defense_file_id: int):
    """Lista los cálculos fiscales asociados al expediente."""
    try:
        result = await defense_file_pg_service.listar_calculos(defense_file_id)
        if not result.get('success'):
            raise HTTPException(status_code=500, detail=result.get('error', 'Error al listar cálculos'))
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"📁 Defense Files API: Error al listar cálculos: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{defense_file_id}/calculos")
async def registrar_calculo(defense_file_id: int, request: RegistrarCalculoRequest):
    """Registra un nuevo cálculo fiscal en el expediente."""
    try:
        result = await defense_file_pg_service.registrar_calculo(
            defense_file_id=defense_file_id,
            tipo=request.tipo,
            periodo=request.periodo,
            concepto=request.concepto,
            base_gravable=Decimal(str(request.base_gravable)) if request.base_gravable else None,
            tasa=Decimal(str(request.tasa)) if request.tasa else None,
            impuesto_calculado=Decimal(str(request.impuesto_calculado)) if request.impuesto_calculado else None,
            formula_aplicada=request.formula_aplicada,
            datos_entrada=request.datos_entrada,
            resultado=request.resultado,
            fundamento_legal=request.fundamento_legal,
            notas=request.notas,
            calculado_por=request.calculado_por,
            revisado_por=request.revisado_por
        )
        if not result.get('success'):
            raise HTTPException(status_code=400, detail=result.get('error', 'Error al registrar cálculo'))
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"📁 Defense Files API: Error al registrar cálculo: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{defense_file_id}/cerrar")
async def cerrar_defense_file(defense_file_id: int, request: CerrarExpedienteRequest = None):
    """Cierra el expediente y genera el hash de integridad final."""
    try:
        usuario_id = request.usuario_id if request else None
        result = await defense_file_pg_service.cerrar_defense_file(
            defense_file_id=defense_file_id,
            usuario_id=usuario_id
        )
        if not result.get('success'):
            raise HTTPException(status_code=400, detail=result.get('error', 'Error al cerrar expediente'))
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"📁 Defense Files API: Error al cerrar expediente {defense_file_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{defense_file_id}/resumen")
async def obtener_resumen_ejecutivo(defense_file_id: int):
    """Genera y retorna el resumen ejecutivo del expediente."""
    try:
        result = await defense_file_pg_service.generar_resumen_ejecutivo(defense_file_id)
        if not result.get('success'):
            raise HTTPException(status_code=500, detail=result.get('error', 'Error al generar resumen'))
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"📁 Defense Files API: Error al generar resumen {defense_file_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/enums/tipos-evento")
async def obtener_tipos_evento():
    """Retorna los tipos de evento disponibles."""
    return {
        "success": True,
        "tipos_evento": [e.value for e in TipoEvento]
    }


@router.get("/enums/agentes")
async def obtener_agentes():
    """Retorna los agentes disponibles."""
    return {
        "success": True,
        "agentes": [a.value for a in Agente]
    }


@router.get("/enums/estados")
async def obtener_estados():
    """Retorna los estados de expediente disponibles."""
    return {
        "success": True,
        "estados": [e.value for e in EstadoExpediente]
    }


class SubirDocumentoRequest(BaseModel):
    tipo_documento: str
    nombre: str
    descripcion: Optional[str] = None


@router.post("/{defense_file_id}/sincronizar-pcloud")
async def sincronizar_con_pcloud(defense_file_id: int):
    """Sincroniza el expediente completo con pCloud."""
    try:
        df_result = await defense_file_pg_service.obtener_defense_file(defense_file_id)
        if not df_result.get('success'):
            raise HTTPException(status_code=404, detail="Expediente no encontrado")
        
        defense_file = df_result.get('defense_file', {})
        
        cliente_id = defense_file.get('cliente_id')
        anio = defense_file.get('anio_fiscal')
        codigo = f"DEF-{defense_file_id:06d}"
        rfc = f"CLI{cliente_id:06d}"
        
        if not pcloud_service.is_available():
            return {
                "success": True,
                "simulado": True,
                "message": "pCloud no configurado - simulación",
                "defense_file_path": f"{rfc}/{anio}/{codigo}"
            }
        
        estructura_result = pcloud_service.crear_estructura_defense_file_v2(rfc, anio, codigo)
        if not estructura_result.get("success"):
            raise HTTPException(status_code=500, detail=estructura_result.get('error'))
        
        defense_file_path = f"{rfc}/{anio}/{codigo}"
        
        timeline_result = await defense_file_pg_service.obtener_timeline(defense_file_id)
        eventos_sincronizados = 0
        if timeline_result.get('success'):
            for evento in timeline_result.get('timeline', []):
                sync_result = pcloud_service.sincronizar_evento(
                    defense_file_path=defense_file_path,
                    agente_id=evento.get('agente', 'SYS'),
                    evento=evento
                )
                if sync_result.get('success'):
                    eventos_sincronizados += 1
        
        indice_result = pcloud_service.generar_indice(defense_file_path)
        
        await defense_file_pg_service.registrar_evento(
            defense_file_id=defense_file_id,
            tipo=TipoEvento.DOCUMENTO_SUBIDO.value,
            agente=Agente.SYS.value,
            titulo="Expediente sincronizado con pCloud",
            descripcion=f"Se sincronizaron {eventos_sincronizados} eventos",
            datos={
                "pcloud_path": defense_file_path,
                "eventos_sincronizados": eventos_sincronizados,
                "carpetas_creadas": estructura_result.get('carpetas_creadas', 0)
            }
        )
        
        logger.info(f"📁 Defense Files API: Expediente {defense_file_id} sincronizado con pCloud")
        
        return {
            "success": True,
            "defense_file_path": defense_file_path,
            "root_folder_id": estructura_result.get('root_folder_id'),
            "carpetas_creadas": estructura_result.get('carpetas_creadas'),
            "eventos_sincronizados": eventos_sincronizados,
            "indice": indice_result.get('success', False)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"📁 Defense Files API: Error sincronizando con pCloud: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{defense_file_id}/exportar-pdf")
async def exportar_pdf(defense_file_id: int):
    """Genera y retorna el PDF del expediente completo."""
    try:
        df_result = await defense_file_pg_service.obtener_defense_file(defense_file_id)
        if not df_result.get('success'):
            raise HTTPException(status_code=404, detail="Expediente no encontrado")
        
        defense_file = df_result.get('defense_file', {})
        
        resumen_result = await defense_file_pg_service.generar_resumen_ejecutivo(defense_file_id)
        resumen = resumen_result.get('resumen', {}) if resumen_result.get('success') else {}
        
        timeline_result = await defense_file_pg_service.obtener_timeline(defense_file_id)
        eventos = timeline_result.get('timeline', []) if timeline_result.get('success') else []
        
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.pdfgen import canvas
            from reportlab.lib.units import inch
            
            buffer = io.BytesIO()
            c = canvas.Canvas(buffer, pagesize=letter)
            width, height = letter
            
            c.setFont("Helvetica-Bold", 18)
            c.drawString(1*inch, height - 1*inch, f"Expediente de Defensa: {defense_file.get('nombre', '')}")
            
            c.setFont("Helvetica", 12)
            y = height - 1.5*inch
            c.drawString(1*inch, y, f"ID: {defense_file_id}")
            y -= 0.3*inch
            c.drawString(1*inch, y, f"Estado: {defense_file.get('estado', '')}")
            y -= 0.3*inch
            c.drawString(1*inch, y, f"Año Fiscal: {defense_file.get('anio_fiscal', '')}")
            y -= 0.3*inch
            c.drawString(1*inch, y, f"Creado: {defense_file.get('created_at', '')}")
            
            if defense_file.get('hash_integridad'):
                y -= 0.3*inch
                c.setFont("Helvetica-Bold", 10)
                c.drawString(1*inch, y, f"Hash Integridad: {defense_file.get('hash_integridad', '')[:32]}...")
            
            y -= 0.5*inch
            c.setFont("Helvetica-Bold", 14)
            c.drawString(1*inch, y, "Estadísticas")
            y -= 0.3*inch
            c.setFont("Helvetica", 11)
            stats = defense_file.get('estadisticas', {})
            c.drawString(1*inch, y, f"Total Eventos: {stats.get('total_eventos', 0)}")
            y -= 0.25*inch
            c.drawString(1*inch, y, f"Total Proveedores: {stats.get('total_proveedores', 0)}")
            y -= 0.25*inch
            c.drawString(1*inch, y, f"Total CFDIs: {stats.get('total_cfdis', 0)}")
            y -= 0.25*inch
            c.drawString(1*inch, y, f"Total Fundamentos: {stats.get('total_fundamentos', 0)}")
            y -= 0.25*inch
            c.drawString(1*inch, y, f"Total Cálculos: {stats.get('total_calculos', 0)}")
            y -= 0.25*inch
            c.drawString(1*inch, y, f"Monto Total CFDIs: ${stats.get('monto_total_cfdis', 0):,.2f}")
            
            if eventos:
                y -= 0.5*inch
                c.setFont("Helvetica-Bold", 14)
                c.drawString(1*inch, y, "Timeline de Eventos (últimos 10)")
                y -= 0.3*inch
                c.setFont("Helvetica", 9)
                
                for evento in eventos[:10]:
                    if y < 1*inch:
                        c.showPage()
                        y = height - 1*inch
                    
                    timestamp = evento.get('timestamp', '')[:19] if evento.get('timestamp') else ''
                    titulo = evento.get('titulo', '')[:60]
                    agente = evento.get('agente', '')
                    c.drawString(1*inch, y, f"[{timestamp}] [{agente}] {titulo}")
                    y -= 0.2*inch
            
            c.setFont("Helvetica-Oblique", 8)
            c.drawString(1*inch, 0.5*inch, f"Generado por REVISAR.IA - {datetime.utcnow().isoformat()}")
            
            c.save()
            buffer.seek(0)
            
            filename = f"expediente_{defense_file_id}_{datetime.utcnow().strftime('%Y%m%d')}.pdf"
            
            return StreamingResponse(
                buffer,
                media_type="application/pdf",
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )
            
        except ImportError:
            return {
                "success": True,
                "message": "ReportLab no disponible - retornando datos JSON",
                "defense_file": defense_file,
                "resumen": resumen,
                "eventos_count": len(eventos)
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"📁 Defense Files API: Error exportando PDF: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{defense_file_id}/documentos")
async def subir_documento(
    defense_file_id: int,
    tipo_documento: str = Form(...),
    nombre: str = Form(None),
    descripcion: str = Form(None),
    archivo: UploadFile = File(...)
):
    """Sube un documento al expediente y lo sincroniza con pCloud si está disponible."""
    try:
        df_result = await defense_file_pg_service.obtener_defense_file(defense_file_id)
        if not df_result.get('success'):
            raise HTTPException(status_code=404, detail="Expediente no encontrado")
        
        defense_file = df_result.get('defense_file', {})
        
        contenido = await archivo.read()
        nombre_archivo = nombre or archivo.filename
        
        cliente_id = defense_file.get('cliente_id')
        anio = defense_file.get('anio_fiscal')
        codigo = f"DEF-{defense_file_id:06d}"
        rfc = f"CLI{cliente_id:06d}"
        defense_file_path = f"{rfc}/{anio}/{codigo}"
        
        pcloud_result = None
        if pcloud_service.is_available():
            pcloud_result = pcloud_service.sincronizar_documento(
                defense_file_path=defense_file_path,
                tipo_documento=tipo_documento,
                nombre=nombre_archivo,
                contenido=contenido
            )
        
        await defense_file_pg_service.registrar_evento(
            defense_file_id=defense_file_id,
            tipo=TipoEvento.DOCUMENTO_SUBIDO.value,
            agente=Agente.USR.value,
            titulo=f"Documento subido: {nombre_archivo}",
            descripcion=descripcion or f"Tipo: {tipo_documento}",
            datos={
                "nombre": nombre_archivo,
                "tipo_documento": tipo_documento,
                "tamaño": len(contenido),
                "pcloud_sincronizado": pcloud_result.get('success', False) if pcloud_result else False,
                "pcloud_file_id": pcloud_result.get('file_id') if pcloud_result else None,
                "pcloud_link": pcloud_result.get('public_link') if pcloud_result else None
            },
            archivos=[{
                "nombre": nombre_archivo,
                "tipo": tipo_documento,
                "tamaño": len(contenido)
            }]
        )
        
        logger.info(f"📁 Defense Files API: Documento subido a expediente {defense_file_id}")
        
        return {
            "success": True,
            "nombre": nombre_archivo,
            "tipo_documento": tipo_documento,
            "tamaño": len(contenido),
            "pcloud_sincronizado": pcloud_result.get('success', False) if pcloud_result else False,
            "pcloud_link": pcloud_result.get('public_link') if pcloud_result else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"📁 Defense Files API: Error subiendo documento: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{defense_file_id}/documentos")
async def listar_documentos(defense_file_id: int):
    """Lista todos los documentos del expediente."""
    try:
        df_result = await defense_file_pg_service.obtener_defense_file(defense_file_id)
        if not df_result.get('success'):
            raise HTTPException(status_code=404, detail="Expediente no encontrado")
        
        defense_file = df_result.get('defense_file', {})
        
        documentos_db = []
        timeline_result = await defense_file_pg_service.obtener_timeline(defense_file_id)
        if timeline_result.get('success'):
            for evento in timeline_result.get('timeline', []):
                if evento.get('tipo') == TipoEvento.DOCUMENTO_SUBIDO.value:
                    archivos = evento.get('archivos', [])
                    datos = evento.get('datos', {})
                    if isinstance(datos, str):
                        import json
                        try:
                            datos = json.loads(datos)
                        except:
                            datos = {}
                    for archivo in (archivos if archivos else [datos] if datos.get('nombre') else []):
                        documentos_db.append({
                            "nombre": archivo.get('nombre') or datos.get('nombre'),
                            "tipo": archivo.get('tipo') or datos.get('tipo_documento'),
                            "tamaño": archivo.get('tamaño') or datos.get('tamaño', 0),
                            "fecha": evento.get('timestamp'),
                            "pcloud_link": datos.get('pcloud_link')
                        })
        
        documentos_pcloud = []
        if pcloud_service.is_available():
            cliente_id = defense_file.get('cliente_id')
            anio = defense_file.get('anio_fiscal')
            codigo = f"DEF-{defense_file_id:06d}"
            rfc = f"CLI{cliente_id:06d}"
            defense_file_path = f"{rfc}/{anio}/{codigo}"
            
            pcloud_result = pcloud_service.listar_documentos_expediente(defense_file_path)
            if pcloud_result.get('success'):
                documentos_pcloud = pcloud_result.get('documentos', [])
        
        return {
            "success": True,
            "documentos_registrados": documentos_db,
            "documentos_pcloud": documentos_pcloud,
            "total_registrados": len(documentos_db),
            "total_pcloud": len(documentos_pcloud)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"📁 Defense Files API: Error listando documentos: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{defense_file_id}/verificar-integridad")
async def verificar_integridad(defense_file_id: int):
    """Verifica la cadena de hashes del expediente."""
    try:
        df_result = await defense_file_pg_service.obtener_defense_file(defense_file_id)
        if not df_result.get('success'):
            raise HTTPException(status_code=404, detail="Expediente no encontrado")
        
        defense_file = df_result.get('defense_file', {})
        
        result = await defense_file_pg_service.verificar_integridad_cadena(defense_file_id)
        
        return {
            "success": True,
            "defense_file_id": defense_file_id,
            "estado": defense_file.get('estado'),
            "hash_integridad_expediente": defense_file.get('hash_integridad'),
            "integridad_valida": result.get('valida', False) if result.get('success') else None,
            "total_eventos": result.get('total_eventos', 0),
            "eventos_validos": result.get('eventos_validos', 0),
            "eventos_invalidos": result.get('eventos_invalidos', []),
            "mensaje": result.get('mensaje', 'Verificación completada')
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"📁 Defense Files API: Error verificando integridad: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class RegistrarBitacoraRequest(BaseModel):
    categoria: str
    tipo_registro: str
    origen: str
    titulo: str
    datos: Optional[Dict[str, Any]] = None
    contenido: Optional[str] = None
    usuario_id: Optional[int] = None
    agente: Optional[str] = None
    prioridad: Optional[str] = None
    proveedor_id: Optional[int] = None
    cfdi_id: Optional[int] = None
    es_critico: Optional[bool] = False


class RegistrarDeduccionRequest(BaseModel):
    concepto: str
    categoria: str
    subcategoria: Optional[str] = None
    monto_total: Optional[float] = None
    monto_deducible: Optional[float] = None
    monto_no_deducible: Optional[float] = None
    fundamento_legal: Optional[Dict[str, Any]] = None
    justificacion: Optional[str] = None
    es_deducible: Optional[bool] = None
    nivel_riesgo: Optional[str] = None


class RegistrarComunicacionRequest(BaseModel):
    tipo: str
    de_remitente: str
    para_destinatario: str
    asunto: str
    cuerpo: Optional[str] = None
    adjuntos: Optional[List[Dict[str, Any]]] = None
    fecha_envio: Optional[datetime] = None
    estado: Optional[str] = "enviado"
    cc: Optional[str] = None
    subtipo: Optional[str] = None
    numero_oficio: Optional[str] = None
    requiere_respuesta: Optional[bool] = False


class RegistrarDocumentoTablaRequest(BaseModel):
    tipo: str
    nombre: str
    archivo_hash: Optional[str] = None
    pcloud_path: Optional[str] = None
    pcloud_file_id: Optional[int] = None
    archivo_size: Optional[int] = None
    archivo_extension: Optional[str] = None
    descripcion: Optional[str] = None
    subtipo: Optional[str] = None
    categoria: Optional[str] = None


class RegistrarRetencionRequest(BaseModel):
    tipo_retencion: str
    base_gravable: Optional[float] = None
    tasa: Optional[float] = None
    monto_retenido: Optional[float] = None
    monto_enterado: Optional[float] = None
    periodo: Optional[str] = None
    fecha_calculo: Optional[date] = None
    fecha_entero: Optional[date] = None
    fundamento_legal: Optional[Dict[str, Any]] = None
    concepto: Optional[str] = None
    proveedor_id: Optional[int] = None
    proveedor_rfc: Optional[str] = None
    estado: Optional[str] = None


@router.get("/{defense_file_id}/bitacora")
async def obtener_bitacora(
    defense_file_id: int,
    categoria: Optional[str] = Query(None, description="Filtrar por categoría"),
    limit: int = Query(100, ge=1, le=1000, description="Límite de resultados")
):
    """Obtiene la bitácora maestra del expediente."""
    try:
        result = await defense_file_pg_service.obtener_bitacora(
            defense_file_id=defense_file_id,
            categoria=categoria,
            limit=limit
        )
        if not result.get('success'):
            raise HTTPException(status_code=500, detail=result.get('error', 'Error al obtener bitácora'))
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"📁 Defense Files API: Error al obtener bitácora: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{defense_file_id}/bitacora")
async def registrar_bitacora(defense_file_id: int, request: RegistrarBitacoraRequest):
    """Registra una entrada en la bitácora maestra del expediente."""
    try:
        result = await defense_file_pg_service.registrar_bitacora(
            defense_file_id=defense_file_id,
            categoria=request.categoria,
            tipo_registro=request.tipo_registro,
            origen=request.origen,
            titulo=request.titulo,
            datos=request.datos,
            contenido=request.contenido,
            usuario_id=request.usuario_id,
            agente=request.agente,
            prioridad=request.prioridad,
            proveedor_id=request.proveedor_id,
            cfdi_id=request.cfdi_id,
            es_critico=request.es_critico
        )
        if not result.get('success'):
            raise HTTPException(status_code=400, detail=result.get('error', 'Error al registrar bitácora'))
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"📁 Defense Files API: Error al registrar bitácora: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{defense_file_id}/deducciones")
async def listar_deducciones(defense_file_id: int):
    """Lista las deducciones analizadas del expediente."""
    try:
        result = await defense_file_pg_service.listar_deducciones(defense_file_id)
        if not result.get('success'):
            raise HTTPException(status_code=500, detail=result.get('error', 'Error al listar deducciones'))
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"📁 Defense Files API: Error al listar deducciones: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{defense_file_id}/deducciones")
async def registrar_deduccion(defense_file_id: int, request: RegistrarDeduccionRequest):
    """Registra una deducción analizada en el expediente."""
    try:
        result = await defense_file_pg_service.registrar_deduccion(
            defense_file_id=defense_file_id,
            concepto=request.concepto,
            categoria=request.categoria,
            subcategoria=request.subcategoria,
            monto_total=Decimal(str(request.monto_total)) if request.monto_total else None,
            monto_deducible=Decimal(str(request.monto_deducible)) if request.monto_deducible else None,
            monto_no_deducible=Decimal(str(request.monto_no_deducible)) if request.monto_no_deducible else None,
            fundamento_legal=request.fundamento_legal,
            justificacion=request.justificacion,
            es_deducible=request.es_deducible,
            nivel_riesgo=request.nivel_riesgo
        )
        if not result.get('success'):
            raise HTTPException(status_code=400, detail=result.get('error', 'Error al registrar deducción'))
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"📁 Defense Files API: Error al registrar deducción: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{defense_file_id}/comunicaciones")
async def listar_comunicaciones(defense_file_id: int):
    """Lista las comunicaciones del expediente."""
    try:
        result = await defense_file_pg_service.listar_comunicaciones(defense_file_id)
        if not result.get('success'):
            raise HTTPException(status_code=500, detail=result.get('error', 'Error al listar comunicaciones'))
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"📁 Defense Files API: Error al listar comunicaciones: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{defense_file_id}/comunicaciones")
async def registrar_comunicacion(defense_file_id: int, request: RegistrarComunicacionRequest):
    """Registra una comunicación en el expediente."""
    try:
        result = await defense_file_pg_service.registrar_comunicacion(
            defense_file_id=defense_file_id,
            tipo=request.tipo,
            de_remitente=request.de_remitente,
            para_destinatario=request.para_destinatario,
            asunto=request.asunto,
            cuerpo=request.cuerpo,
            adjuntos=request.adjuntos,
            fecha_envio=request.fecha_envio,
            estado=request.estado,
            cc=request.cc,
            subtipo=request.subtipo,
            numero_oficio=request.numero_oficio,
            requiere_respuesta=request.requiere_respuesta
        )
        if not result.get('success'):
            raise HTTPException(status_code=400, detail=result.get('error', 'Error al registrar comunicación'))
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"📁 Defense Files API: Error al registrar comunicación: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{defense_file_id}/documentos-tabla")
async def listar_documentos_tabla(defense_file_id: int):
    """Lista los documentos de la tabla df_documentos."""
    try:
        result = await defense_file_pg_service.listar_documentos_tabla(defense_file_id)
        if not result.get('success'):
            raise HTTPException(status_code=500, detail=result.get('error', 'Error al listar documentos'))
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"📁 Defense Files API: Error al listar documentos tabla: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{defense_file_id}/documentos-tabla")
async def registrar_documento_tabla(defense_file_id: int, request: RegistrarDocumentoTablaRequest):
    """Registra un documento en la tabla df_documentos."""
    try:
        result = await defense_file_pg_service.registrar_documento_tabla(
            defense_file_id=defense_file_id,
            tipo=request.tipo,
            nombre=request.nombre,
            archivo_hash=request.archivo_hash,
            pcloud_path=request.pcloud_path,
            pcloud_file_id=request.pcloud_file_id,
            archivo_size=request.archivo_size,
            archivo_extension=request.archivo_extension,
            descripcion=request.descripcion,
            subtipo=request.subtipo,
            categoria=request.categoria
        )
        if not result.get('success'):
            raise HTTPException(status_code=400, detail=result.get('error', 'Error al registrar documento'))
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"📁 Defense Files API: Error al registrar documento tabla: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{defense_file_id}/retenciones")
async def listar_retenciones(defense_file_id: int):
    """Lista las retenciones ISR/IVA del expediente."""
    try:
        result = await defense_file_pg_service.listar_retenciones(defense_file_id)
        if not result.get('success'):
            raise HTTPException(status_code=500, detail=result.get('error', 'Error al listar retenciones'))
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"📁 Defense Files API: Error al listar retenciones: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{defense_file_id}/retenciones")
async def registrar_retencion(defense_file_id: int, request: RegistrarRetencionRequest):
    """Registra una retención ISR/IVA en el expediente."""
    try:
        result = await defense_file_pg_service.registrar_retencion(
            defense_file_id=defense_file_id,
            tipo_retencion=request.tipo_retencion,
            base_gravable=Decimal(str(request.base_gravable)) if request.base_gravable else None,
            tasa=Decimal(str(request.tasa)) if request.tasa else None,
            monto_retenido=Decimal(str(request.monto_retenido)) if request.monto_retenido else None,
            monto_enterado=Decimal(str(request.monto_enterado)) if request.monto_enterado else None,
            periodo=request.periodo,
            fecha_calculo=request.fecha_calculo,
            fecha_entero=request.fecha_entero,
            fundamento_legal=request.fundamento_legal,
            concepto=request.concepto,
            proveedor_id=request.proveedor_id,
            proveedor_rfc=request.proveedor_rfc,
            estado=request.estado
        )
        if not result.get('success'):
            raise HTTPException(status_code=400, detail=result.get('error', 'Error al registrar retención'))
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"📁 Defense Files API: Error al registrar retención: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{defense_file_id}/resumen-completo")
async def obtener_resumen_completo(defense_file_id: int):
    """Obtiene el resumen completo del expediente con todas sus tablas relacionadas."""
    try:
        result = await defense_file_pg_service.obtener_resumen_completo(defense_file_id)
        if not result.get('success'):
            raise HTTPException(status_code=500, detail=result.get('error', 'Error al obtener resumen completo'))
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"📁 Defense Files API: Error al obtener resumen completo: {e}")
        raise HTTPException(status_code=500, detail=str(e))
