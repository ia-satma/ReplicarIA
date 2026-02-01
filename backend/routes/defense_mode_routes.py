"""
============================================================
REVISAR.IA - API Routes: Modo Defensa
============================================================
Endpoints para gestionar expedientes cuando existe un acto
de autoridad fiscal.
============================================================
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime, date
from enum import Enum

from services.defense_mode_service import (
    get_defense_mode_service,
    TipoActoAutoridad,
    EstadoExpedienteDefensa,
    TipoMedioDefensa
)
from services.legal_validation_service import (
    get_legal_validation_service,
    TipoServicio,
    NivelRiesgoInherente,
    CategoriaGasto,
    MATRICES_NHP,
    PLANTILLAS_ARGUMENTACION,
    REGLAS_POR_CATEGORIA,
    RIESGO_POR_TIPO_SERVICIO
)
from services.normative_framework import (
    BLOQUES_NORMATIVOS,
    RECURSOS_SAT,
    obtener_fundamento,
    obtener_bloque,
    obtener_fundamentos_por_tipo_servicio,
    generar_fundamentacion_para_regla,
    generar_disclaimer_legal
)

router = APIRouter(prefix="/api/defense-mode", tags=["Modo Defensa"])


# ============================================================
# MODELOS PYDANTIC
# ============================================================

class OperacionInput(BaseModel):
    """Input para una operación cuestionada"""
    operacion_id: Optional[str] = None
    proveedor_rfc: str
    proveedor_nombre: str
    monto: float
    tipo_servicio: str
    cfdi_folio: Optional[str] = None
    fecha_operacion: Optional[date] = None
    motivo_cuestionamiento: str = "No especificado"


class CrearExpedienteInput(BaseModel):
    """Input para crear expediente de defensa"""
    empresa_id: str
    tipo_acto: str
    numero_oficio: str
    fecha_notificacion: date
    autoridad_emisora: str
    ejercicio_revisado: int
    operaciones: List[OperacionInput]


class ActualizarEstadoInput(BaseModel):
    """Input para actualizar estado del expediente"""
    estado: str
    notas: Optional[str] = None


class DocumentoUpdateInput(BaseModel):
    """Input para actualizar estado de documento"""
    disponible: bool
    archivo_url: Optional[str] = None
    notas: Optional[str] = None


class GenerarArgumentacionInput(BaseModel):
    """Input para generar argumentación"""
    nombre_contribuyente: str
    rfc_contribuyente: str
    forma_pago: str = "transferencia electrónica"
    numero_pagos: str = "una"
    datos_operaciones: Optional[Dict[str, Dict[str, str]]] = None


# ============================================================
# ENDPOINTS - EXPEDIENTES DE DEFENSA
# ============================================================

@router.post("/expedientes", response_model=Dict[str, Any])
async def crear_expediente_defensa(data: CrearExpedienteInput):
    """
    Crea un nuevo expediente de defensa.
    Se activa cuando hay un acto de autoridad fiscal.
    """
    service = get_defense_mode_service()

    try:
        tipo_acto = TipoActoAutoridad(data.tipo_acto)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Tipo de acto inválido: {data.tipo_acto}. Valores válidos: {[t.value for t in TipoActoAutoridad]}"
        )

    operaciones = [
        {
            "operacion_id": op.operacion_id,
            "proveedor_rfc": op.proveedor_rfc,
            "proveedor_nombre": op.proveedor_nombre,
            "monto": op.monto,
            "tipo_servicio": op.tipo_servicio,
            "cfdi_folio": op.cfdi_folio,
            "fecha_operacion": datetime.combine(op.fecha_operacion, datetime.min.time()) if op.fecha_operacion else None,
            "motivo_cuestionamiento": op.motivo_cuestionamiento
        }
        for op in data.operaciones
    ]

    expediente = service.crear_expediente_defensa(
        empresa_id=data.empresa_id,
        tipo_acto=tipo_acto,
        numero_oficio=data.numero_oficio,
        fecha_notificacion=datetime.combine(data.fecha_notificacion, datetime.min.time()),
        autoridad_emisora=data.autoridad_emisora,
        ejercicio_revisado=data.ejercicio_revisado,
        operaciones=operaciones
    )

    return service.obtener_resumen_expediente(expediente)


@router.get("/expedientes/{expediente_id}", response_model=Dict[str, Any])
async def obtener_expediente(expediente_id: str):
    """
    Obtiene los detalles de un expediente de defensa.
    NOTA: En producción, esto vendría de la base de datos.
    """
    # TODO: Implementar consulta a BD
    raise HTTPException(
        status_code=501,
        detail="Endpoint pendiente de implementación con BD. Use POST para crear expediente."
    )


@router.post("/expedientes/{expediente_id}/evaluar", response_model=Dict[str, Any])
async def evaluar_expediente(expediente_id: str):
    """
    Evalúa todas las operaciones de un expediente con el sistema de validación legal.
    """
    # TODO: Cargar expediente de BD y evaluar
    raise HTTPException(
        status_code=501,
        detail="Pendiente de implementación con BD"
    )


@router.post("/expedientes/{expediente_id}/generar-narrativa", response_model=Dict[str, str])
async def generar_narrativa(expediente_id: str):
    """
    Genera la narrativa de hechos para el expediente.
    """
    # TODO: Cargar expediente de BD y generar narrativa
    raise HTTPException(
        status_code=501,
        detail="Pendiente de implementación con BD"
    )


@router.post("/expedientes/{expediente_id}/generar-argumentacion", response_model=Dict[str, str])
async def generar_argumentacion(
    expediente_id: str,
    data: GenerarArgumentacionInput
):
    """
    Genera la argumentación jurídica completa para el expediente.
    """
    # TODO: Cargar expediente de BD y generar argumentación
    raise HTTPException(
        status_code=501,
        detail="Pendiente de implementación con BD"
    )


# ============================================================
# ENDPOINTS - MATRICES NORMA-HECHO-PRUEBA
# ============================================================

@router.get("/matrices-nhp", response_model=List[Dict[str, Any]])
async def listar_matrices_disponibles():
    """
    Lista todas las matrices Norma-Hecho-Prueba disponibles.
    """
    matrices = []
    for tipo, matriz in MATRICES_NHP.items():
        matrices.append({
            "tipo_servicio": tipo.value,
            "nivel_riesgo": matriz.nivel_riesgo_inherente.value,
            "descripcion_riesgo": matriz.descripcion_riesgo,
            "num_elementos": len(matriz.elementos),
            "consideraciones_especiales": matriz.consideraciones_especiales
        })
    return matrices


@router.get("/matrices-nhp/{tipo_servicio}", response_model=Dict[str, Any])
async def obtener_matriz_nhp(tipo_servicio: str):
    """
    Obtiene la matriz Norma-Hecho-Prueba completa para un tipo de servicio.
    Disponible para: marketing, consultoria, outsourcing
    """
    service = get_legal_validation_service()

    try:
        ts = TipoServicio(tipo_servicio)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Tipo de servicio inválido: {tipo_servicio}"
        )

    matriz = service.obtener_matriz_nhp(ts)
    if not matriz:
        raise HTTPException(
            status_code=404,
            detail=f"No hay matriz NHP disponible para {tipo_servicio}. Disponibles: marketing, consultoria, outsourcing"
        )

    return {
        "tipo_servicio": matriz.tipo_servicio.value,
        "nivel_riesgo_inherente": matriz.nivel_riesgo_inherente.value,
        "descripcion_riesgo": matriz.descripcion_riesgo,
        "consideraciones_especiales": matriz.consideraciones_especiales,
        "elementos": [
            {
                "norma": elem.norma,
                "fundamento_legal": elem.fundamento_legal,
                "hecho_a_acreditar": elem.hecho_a_acreditar,
                "pruebas_primarias": elem.pruebas_primarias,
                "pruebas_secundarias": elem.pruebas_secundarias,
                "riesgo_si_falta": elem.riesgo_si_falta
            }
            for elem in matriz.elementos
        ]
    }


@router.get("/checklist-nhp/{tipo_servicio}", response_model=Dict[str, Any])
async def obtener_checklist_nhp(tipo_servicio: str):
    """
    Genera un checklist basado en la matriz NHP para verificar completitud documental.
    """
    service = get_legal_validation_service()

    try:
        ts = TipoServicio(tipo_servicio)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Tipo de servicio inválido: {tipo_servicio}"
        )

    return service.generar_checklist_nhp(ts)


# ============================================================
# ENDPOINTS - REGLAS FINAS POR CATEGORÍA
# ============================================================

@router.get("/categorias-gasto", response_model=List[Dict[str, Any]])
async def listar_categorias_gasto():
    """
    Lista todas las categorías de gasto LISR 27 disponibles.
    """
    return [
        {
            "id": cat.value,
            "nombre": cat.value.replace("_", " ").title(),
            "num_reglas": len(REGLAS_POR_CATEGORIA.get(cat, []))
        }
        for cat in CategoriaGasto
    ]


@router.get("/reglas-categoria/{categoria}", response_model=Dict[str, Any])
async def obtener_reglas_categoria(categoria: str):
    """
    Obtiene las reglas finas LISR 27 para una categoría de gasto.
    """
    try:
        cat = CategoriaGasto(categoria)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Categoría inválida: {categoria}. Valores válidos: {[c.value for c in CategoriaGasto]}"
        )

    reglas = REGLAS_POR_CATEGORIA.get(cat, [])

    return {
        "categoria": cat.value,
        "descripcion": cat.value.replace("_", " ").title(),
        "reglas": reglas,
        "total_reglas": len(reglas)
    }


@router.get("/reglas-servicio/{tipo_servicio}", response_model=Dict[str, Any])
async def obtener_reglas_por_servicio(tipo_servicio: str):
    """
    Obtiene las reglas finas LISR 27 aplicables a un tipo de servicio.
    """
    service = get_legal_validation_service()

    try:
        ts = TipoServicio(tipo_servicio)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Tipo de servicio inválido: {tipo_servicio}"
        )

    return service.obtener_reglas_finas_servicio(ts)


@router.get("/riesgo-inherente", response_model=Dict[str, str])
async def obtener_riesgos_inherentes():
    """
    Obtiene el nivel de riesgo inherente por tipo de servicio.
    """
    return {
        ts.value: nivel.value
        for ts, nivel in RIESGO_POR_TIPO_SERVICIO.items()
    }


# ============================================================
# ENDPOINTS - PLANTILLAS DE ARGUMENTACIÓN
# ============================================================

@router.get("/plantillas-argumentacion", response_model=List[Dict[str, Any]])
async def listar_plantillas():
    """
    Lista todas las plantillas de argumentación disponibles.
    """
    return [
        {
            "seccion": p.seccion,
            "titulo": p.titulo,
            "variables_requeridas": p.variables_requeridas,
            "ejemplo": p.ejemplo[:200] + "..." if len(p.ejemplo) > 200 else p.ejemplo
        }
        for p in PLANTILLAS_ARGUMENTACION
    ]


@router.get("/plantillas-argumentacion/{seccion}", response_model=Dict[str, Any])
async def obtener_plantilla(seccion: str):
    """
    Obtiene una plantilla de argumentación específica con su template completo.
    """
    service = get_legal_validation_service()
    plantilla = service.obtener_plantilla_por_seccion(seccion)

    if not plantilla:
        raise HTTPException(
            status_code=404,
            detail=f"Plantilla no encontrada: {seccion}"
        )

    return {
        "seccion": plantilla.seccion,
        "titulo": plantilla.titulo,
        "template": plantilla.template,
        "variables_requeridas": plantilla.variables_requeridas,
        "ejemplo": plantilla.ejemplo
    }


@router.post("/generar-seccion/{seccion}", response_model=Dict[str, str])
async def generar_seccion_argumentacion(
    seccion: str,
    variables: Dict[str, Any]
):
    """
    Genera el texto de una sección de argumentación usando las variables proporcionadas.
    """
    service = get_legal_validation_service()

    texto = service.generar_argumentacion(seccion, variables)
    if not texto:
        plantilla = service.obtener_plantilla_por_seccion(seccion)
        if not plantilla:
            raise HTTPException(status_code=404, detail=f"Plantilla no encontrada: {seccion}")

        faltantes = [v for v in plantilla.variables_requeridas if v not in variables]
        raise HTTPException(
            status_code=400,
            detail=f"Variables faltantes: {faltantes}"
        )

    return {"seccion": seccion, "texto_generado": texto}


# ============================================================
# ENDPOINTS - PLAZOS PROCESALES
# ============================================================

@router.get("/plazos-procesales", response_model=Dict[str, Any])
async def obtener_plazos_procesales():
    """
    Obtiene el catálogo de plazos procesales por tipo de acto.
    """
    from services.defense_mode_service import PLAZOS_PROCESALES

    return {
        tipo.value: info
        for tipo, info in PLAZOS_PROCESALES.items()
    }


@router.get("/plazos-procesales/{tipo_acto}", response_model=Dict[str, Any])
async def obtener_plazo_especifico(tipo_acto: str):
    """
    Obtiene el plazo procesal para un tipo de acto específico.
    """
    from services.defense_mode_service import PLAZOS_PROCESALES

    try:
        tipo = TipoActoAutoridad(tipo_acto)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Tipo de acto inválido: {tipo_acto}"
        )

    plazo = PLAZOS_PROCESALES.get(tipo)
    if not plazo:
        raise HTTPException(status_code=404, detail="Plazo no encontrado")

    return {
        "tipo_acto": tipo.value,
        **plazo
    }


# ============================================================
# ENDPOINTS - UTILIDADES
# ============================================================

@router.get("/tipos-acto", response_model=List[Dict[str, str]])
async def listar_tipos_acto():
    """
    Lista todos los tipos de acto de autoridad soportados.
    """
    descripciones = {
        "revision_electronica": "Revisión electrónica de operaciones",
        "visita_domiciliaria": "Visita domiciliaria de auditoría",
        "revision_gabinete": "Revisión de gabinete (documentos)",
        "negativa_devolucion": "Negativa de devolución de saldo a favor",
        "oficio_observaciones": "Oficio de observaciones de auditoría",
        "carta_invitacion": "Carta invitación del SAT",
        "resolucion_provisional": "Resolución provisional de auditoría"
    }

    return [
        {"id": t.value, "nombre": t.value.replace("_", " ").title(), "descripcion": descripciones.get(t.value, "")}
        for t in TipoActoAutoridad
    ]


@router.get("/medios-defensa", response_model=List[Dict[str, str]])
async def listar_medios_defensa():
    """
    Lista todos los medios de defensa disponibles.
    """
    descripciones = {
        "respuesta_requerimiento": "Respuesta al requerimiento de información",
        "recurso_revocacion": "Recurso de revocación (CFF Art. 116-128)",
        "juicio_nulidad": "Juicio contencioso administrativo (TFJA)",
        "acuerdo_conclusivo": "Acuerdo conclusivo ante PRODECON",
        "autocorreccion": "Autocorrección fiscal"
    }

    return [
        {"id": m.value, "nombre": m.value.replace("_", " ").title(), "descripcion": descripciones.get(m.value, "")}
        for m in TipoMedioDefensa
    ]


@router.get("/estados-expediente", response_model=List[Dict[str, str]])
async def listar_estados_expediente():
    """
    Lista todos los estados posibles de un expediente de defensa.
    """
    descripciones = {
        "recibido": "Notificación recibida, pendiente de análisis",
        "en_analisis": "Analizando alcance y contenido del acto",
        "recopilando": "Recopilando documentación de soporte",
        "elaborando_respuesta": "Preparando escrito de respuesta",
        "listo_para_presentar": "Expediente completo, listo para presentar",
        "presentado": "Respuesta entregada a la autoridad",
        "en_espera_resolucion": "Esperando resolución de la autoridad",
        "resuelto_favorable": "Resuelto a favor del contribuyente",
        "resuelto_parcial": "Resolución parcialmente favorable",
        "resuelto_desfavorable": "Resuelto en contra, evaluar impugnación",
        "en_impugnacion": "Recurso o juicio en curso"
    }

    return [
        {"id": e.value, "nombre": e.value.replace("_", " ").title(), "descripcion": descripciones.get(e.value, "")}
        for e in EstadoExpedienteDefensa
    ]


# ============================================================
# ENDPOINTS - MARCO NORMATIVO
# ============================================================

@router.get("/marco-normativo/bloques", response_model=List[Dict[str, Any]])
async def listar_bloques_normativos():
    """
    Lista todos los bloques normativos disponibles.
    Cada bloque agrupa fundamentos relacionados temáticamente.
    """
    return [
        {
            "id": bloque.id,
            "nombre": bloque.nombre,
            "descripcion": bloque.descripcion,
            "aplicable_a": bloque.aplicable_a,
            "num_fundamentos": len(bloque.fundamentos),
            "notas_sistema": bloque.notas_sistema
        }
        for bloque in BLOQUES_NORMATIVOS.values()
    ]


@router.get("/marco-normativo/bloques/{bloque_id}", response_model=Dict[str, Any])
async def obtener_bloque_normativo(bloque_id: str):
    """
    Obtiene un bloque normativo completo con todos sus fundamentos.
    """
    bloque = obtener_bloque(bloque_id)
    if not bloque:
        raise HTTPException(
            status_code=404,
            detail=f"Bloque no encontrado: {bloque_id}. Disponibles: {list(BLOQUES_NORMATIVOS.keys())}"
        )

    return {
        "id": bloque.id,
        "nombre": bloque.nombre,
        "descripcion": bloque.descripcion,
        "aplicable_a": bloque.aplicable_a,
        "notas_sistema": bloque.notas_sistema,
        "fundamentos": [
            {
                "id": f.id,
                "nombre_corto": f.nombre_corto,
                "nombre_completo": f.nombre_completo,
                "tipo": f.tipo.value,
                "rama": f.rama.value,
                "articulos_relevantes": f.articulos_relevantes,
                "url_oficial": f.url_oficial,
                "fuente": f.fuente,
                "descripcion": f.descripcion,
                "aplicacion_practica": f.aplicacion_practica,
                "notas_interpretacion": f.notas_interpretacion,
                "vigente": f.vigente
            }
            for f in bloque.fundamentos
        ]
    }


@router.get("/marco-normativo/fundamentos/{fundamento_id}", response_model=Dict[str, Any])
async def obtener_fundamento_normativo(fundamento_id: str):
    """
    Obtiene un fundamento normativo específico con su URL oficial.
    """
    fundamento = obtener_fundamento(fundamento_id)
    if not fundamento:
        raise HTTPException(
            status_code=404,
            detail=f"Fundamento no encontrado: {fundamento_id}"
        )

    return {
        "id": fundamento.id,
        "nombre_corto": fundamento.nombre_corto,
        "nombre_completo": fundamento.nombre_completo,
        "tipo": fundamento.tipo.value,
        "rama": fundamento.rama.value,
        "articulos_relevantes": fundamento.articulos_relevantes,
        "url_oficial": fundamento.url_oficial,
        "fuente": fundamento.fuente,
        "descripcion": fundamento.descripcion,
        "aplicacion_practica": fundamento.aplicacion_practica,
        "notas_interpretacion": fundamento.notas_interpretacion,
        "vigente": fundamento.vigente,
        "ultima_reforma": fundamento.ultima_reforma
    }


@router.get("/marco-normativo/por-servicio/{tipo_servicio}", response_model=Dict[str, Any])
async def obtener_fundamentos_servicio(tipo_servicio: str):
    """
    Obtiene todos los fundamentos normativos aplicables a un tipo de servicio.
    """
    fundamentos = obtener_fundamentos_por_tipo_servicio(tipo_servicio)

    return {
        "tipo_servicio": tipo_servicio,
        "total_fundamentos": len(fundamentos),
        "fundamentos": [
            {
                "id": f.id,
                "nombre_corto": f.nombre_corto,
                "url_oficial": f.url_oficial,
                "fuente": f.fuente,
                "articulos": f.articulos_relevantes
            }
            for f in fundamentos
        ]
    }


@router.get("/marco-normativo/por-regla/{regla_id}", response_model=Dict[str, Any])
async def obtener_fundamentacion_regla(regla_id: str):
    """
    Obtiene la fundamentación normativa completa para una regla del sistema.
    Útil para generar la sección de fundamentos en el Defense File.
    """
    return generar_fundamentacion_para_regla(regla_id)


@router.get("/marco-normativo/recursos-sat", response_model=Dict[str, Any])
async def listar_recursos_sat():
    """
    Lista todos los recursos SAT disponibles para validación.
    Incluye URLs para consultas de 69-B, CFDI, 32-D, etc.
    """
    return RECURSOS_SAT


@router.get("/marco-normativo/disclaimer", response_model=Dict[str, str])
async def obtener_disclaimer_legal():
    """
    Obtiene el disclaimer legal para incluir en Defense Files.
    """
    return {
        "disclaimer": generar_disclaimer_legal()
    }
