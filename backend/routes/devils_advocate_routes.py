"""
============================================================
REVISAR.IA - API Routes: Abogado del Diablo
============================================================
Endpoints para el módulo de control interno y aprendizaje.
ACCESO: Solo administradores.

ADVERTENCIA: Este módulo genera información altamente sensible.
Debe tratarse como herramienta interna de compliance.
============================================================
"""

from fastapi import APIRouter, HTTPException, Query, Depends, Header
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime, date
from enum import Enum

from services.devils_advocate_service import (
    get_devils_advocate_service,
    CategoriaIndustria,
    NivelRiesgoResidual,
    FaseProyecto,
    TipoRegistro,
    BloquePregunta,
    NivelSeveridad,
    PREGUNTAS_INCOMODAS_BASE,
    PREGUNTAS_ESTRUCTURADAS,
    PREGUNTAS_POR_BLOQUE
)

router = APIRouter(prefix="/api/admin/abogado-diablo", tags=["Abogado del Diablo (Admin)"])


# ============================================================
# VERIFICACIÓN DE ADMIN (simplificada - implementar con auth real)
# ============================================================

async def verificar_admin(x_admin_token: Optional[str] = Header(None)):
    """
    Verifica que el request viene de un administrador.
    En producción, esto debe integrarse con el sistema de auth real.
    """
    # TODO: Implementar verificación real con JWT/sesiones
    # Por ahora, acepta cualquier token no vacío
    if not x_admin_token:
        raise HTTPException(
            status_code=403,
            detail="Acceso denegado. Este endpoint es solo para administradores."
        )
    return x_admin_token


# ============================================================
# MODELOS PYDANTIC
# ============================================================

class IniciarHuellaInput(BaseModel):
    """Input para iniciar huella de proyecto"""
    proyecto_id: str
    empresa_id: str
    industria: str
    tipo_servicio: str
    monto: float
    proveedor_rfc: str


class RegistrarCambioInput(BaseModel):
    """Input para registrar cambio de semáforo"""
    proyecto_id: str
    fase: str
    color_anterior: str
    color_nuevo: str
    score_anterior: float
    score_nuevo: float
    agente_responsable: str
    evidencia_que_cambio: List[str]
    justificacion: str
    version_entregable: str


class RegistrarPreguntaInput(BaseModel):
    """Input para registrar respuesta a pregunta incómoda"""
    proyecto_id: str
    categoria: str
    pregunta: str
    respuesta: str
    evidencia_soporte: List[str]
    norma_relacionada: str


class RegistrarRiesgoInput(BaseModel):
    """Input para registrar riesgo residual"""
    proyecto_id: str
    descripcion: str
    nivel: str
    justificacion: str
    mitigacion_propuesta: str
    monto_exposicion: float = 0.0


class CerrarHuellaInput(BaseModel):
    """Input para cerrar huella de proyecto"""
    proyecto_id: str
    resultado: str  # aprobado, rechazado
    notas_cierre: str = ""


class RegistrarLeccionInput(BaseModel):
    """Input para registrar lección aprendida manualmente"""
    titulo: str
    descripcion: str
    industria: str
    tipo_servicio: str
    categoria: str
    norma_relacionada: str
    contexto: str
    problema_detectado: str
    solucion_aplicada: str
    aplicable_cuando: List[str]


class RegistrarIncidenteInput(BaseModel):
    """Input para registrar incidente SAT"""
    proyecto_id: str
    descripcion: str
    tipo_acto: str
    monto_cuestionado: float
    fecha_incidente: date
    resultado: Optional[str] = None


class RespuestaEstructuradaInput(BaseModel):
    """Input para responder una pregunta estructurada"""
    pregunta_id: str = Field(..., description="ID de la pregunta (P01_DESCRIPCION_SERVICIO, etc.)")
    respuesta: str = Field(..., description="Respuesta proporcionada")
    indice_opcion: Optional[int] = Field(None, description="Índice de la opción seleccionada (para escala/selección)")
    evidencia_soporte: List[str] = Field(default_factory=list)


class EvaluacionCompletaInput(BaseModel):
    """Input para evaluar todas las respuestas de un proyecto"""
    proyecto_id: str
    respuestas: Dict[str, Dict[str, Any]] = Field(
        ...,
        description="Diccionario de respuestas: {pregunta_id: {respuesta, indice_opcion}}"
    )


# ============================================================
# ENDPOINTS - DOCUMENTACIÓN DEL MÓDULO
# ============================================================

@router.get("/", response_model=Dict[str, Any])
async def obtener_documentacion(admin_id: str = Depends(verificar_admin)):
    """
    Documentación del módulo Abogado del Diablo.
    Explica el propósito y uso de cada funcionalidad.
    """
    return {
        "modulo": "Abogado del Diablo",
        "version": "1.0.0",
        "acceso": "Solo administradores",
        "proposito": """
        Módulo interno de control y aprendizaje organizacional.
        NO es un agente que dictamina, sino que:
        - Cuestiona sistemáticamente las decisiones de aprobación
        - Registra el 'cómo' y 'cuándo' de cada decisión
        - Aprende patrones por industria y tipo de servicio
        - Genera estándares de prueba basados en experiencia real
        - Documenta riesgos residuales aceptados
        """,
        "advertencia": """
        Esta información es ALTAMENTE SENSIBLE.
        Debe tratarse como herramienta interna de compliance.
        NO compartir con terceros ni entregar a autoridades.
        """,
        "funcionalidades": {
            "huellas": "Registro completo del proceso de revisión de cada proyecto",
            "cambios_semaforo": "Documentación de qué evidencia cambió el color del semáforo",
            "preguntas_incomodas": "Cuestionamientos sistemáticos y sus respuestas",
            "riesgos_residuales": "Riesgos aceptados conscientemente con justificación",
            "perfiles_riesgo": "Aprendizaje dinámico por industria/servicio/monto",
            "lecciones_aprendidas": "Patrones de éxito y fracaso reutilizables",
            "incidentes_sat": "Problemas posteriores (evita sesgo de confirmación)"
        },
        "endpoints_disponibles": {
            "huellas": "/huellas",
            "preguntas": "/preguntas-incomodas",
            "perfiles": "/perfiles-riesgo",
            "lecciones": "/lecciones",
            "incidentes": "/incidentes-sat",
            "reportes": "/reportes",
            "estadisticas": "/estadisticas"
        }
    }


# ============================================================
# ENDPOINTS - HUELLAS DE REVISIÓN
# ============================================================

@router.post("/huellas/iniciar", response_model=Dict[str, Any])
async def iniciar_huella(
    data: IniciarHuellaInput,
    admin_id: str = Depends(verificar_admin)
):
    """
    Inicia el registro de huella para un proyecto.
    Debe llamarse cuando el proyecto entra a revisión.
    """
    service = get_devils_advocate_service()

    try:
        industria = CategoriaIndustria(data.industria)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Industria inválida: {data.industria}. Valores: {[i.value for i in CategoriaIndustria]}"
        )

    huella = service.registrar_huella_proyecto(
        proyecto_id=data.proyecto_id,
        empresa_id=data.empresa_id,
        industria=industria,
        tipo_servicio=data.tipo_servicio,
        monto=data.monto,
        proveedor_rfc=data.proveedor_rfc,
        admin_id=admin_id
    )

    return {
        "mensaje": "Huella iniciada correctamente",
        "proyecto_id": huella.proyecto_id,
        "industria": huella.industria.value,
        "tipo_servicio": huella.tipo_servicio,
        "fecha_inicio": huella.fecha_inicio.isoformat()
    }


@router.post("/huellas/cambio-semaforo", response_model=Dict[str, Any])
async def registrar_cambio_semaforo(
    data: RegistrarCambioInput,
    admin_id: str = Depends(verificar_admin)
):
    """
    Registra un cambio de color en el semáforo.
    Esto documenta qué evidencia hizo la diferencia.
    """
    service = get_devils_advocate_service()

    try:
        fase = FaseProyecto(data.fase)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Fase inválida: {data.fase}. Valores: F0-F9"
        )

    cambio = service.registrar_cambio_semaforo(
        proyecto_id=data.proyecto_id,
        fase=fase,
        color_anterior=data.color_anterior,
        color_nuevo=data.color_nuevo,
        score_anterior=data.score_anterior,
        score_nuevo=data.score_nuevo,
        agente_responsable=data.agente_responsable,
        evidencia_que_cambio=data.evidencia_que_cambio,
        justificacion=data.justificacion,
        version_entregable=data.version_entregable
    )

    if not cambio:
        raise HTTPException(
            status_code=404,
            detail=f"Proyecto {data.proyecto_id} no tiene huella registrada"
        )

    return {
        "mensaje": f"Cambio registrado: {data.color_anterior} → {data.color_nuevo}",
        "fase": data.fase,
        "evidencia_clave": data.evidencia_que_cambio
    }


@router.post("/huellas/cerrar", response_model=Dict[str, Any])
async def cerrar_huella(
    data: CerrarHuellaInput,
    admin_id: str = Depends(verificar_admin)
):
    """
    Cierra la huella de un proyecto y dispara el aprendizaje.
    """
    service = get_devils_advocate_service()

    huella = service.cerrar_huella_proyecto(
        proyecto_id=data.proyecto_id,
        resultado=data.resultado,
        notas_cierre=data.notas_cierre
    )

    if not huella:
        raise HTTPException(
            status_code=404,
            detail=f"Proyecto {data.proyecto_id} no tiene huella registrada"
        )

    return {
        "mensaje": f"Huella cerrada: {data.resultado}",
        "proyecto_id": data.proyecto_id,
        "duracion_dias": (huella.fecha_cierre - huella.fecha_inicio).days if huella.fecha_cierre else 0,
        "cambios_semaforo": len(huella.cambios_semaforo),
        "evidencias_clave": len(huella.evidencias_clave),
        "preguntas_respondidas": len(huella.preguntas_respondidas),
        "riesgos_documentados": len(huella.riesgos_residuales)
    }


# ============================================================
# ENDPOINTS - PREGUNTAS INCÓMODAS
# ============================================================

@router.get("/preguntas-incomodas", response_model=Dict[str, Any])
async def listar_preguntas_incomodas(
    tipo_servicio: Optional[str] = Query(None, description="Filtrar por tipo de servicio"),
    industria: Optional[str] = Query(None, description="Filtrar por industria"),
    admin_id: str = Depends(verificar_admin)
):
    """
    Lista las preguntas incómodas aplicables a un caso.
    Combina preguntas base con las aprendidas de casos anteriores.
    """
    service = get_devils_advocate_service()

    industria_enum = None
    if industria:
        try:
            industria_enum = CategoriaIndustria(industria)
        except ValueError:
            pass

    preguntas = service.obtener_preguntas_incomodas(
        tipo_servicio=tipo_servicio or "todos",
        industria=industria_enum
    )

    return {
        "tipo_servicio": tipo_servicio or "todos",
        "industria": industria or "todas",
        "total_preguntas": len(preguntas),
        "preguntas": preguntas,
        "categorias": list(PREGUNTAS_INCOMODAS_BASE.keys())
    }


@router.post("/preguntas-incomodas/responder", response_model=Dict[str, Any])
async def registrar_respuesta_pregunta(
    data: RegistrarPreguntaInput,
    admin_id: str = Depends(verificar_admin)
):
    """
    Registra la respuesta a una pregunta incómoda.
    Esto construye la biblioteca de argumentos de defensa.
    """
    service = get_devils_advocate_service()

    pregunta = service.registrar_respuesta_pregunta(
        proyecto_id=data.proyecto_id,
        categoria=data.categoria,
        pregunta=data.pregunta,
        respuesta=data.respuesta,
        evidencia_soporte=data.evidencia_soporte,
        norma_relacionada=data.norma_relacionada
    )

    if not pregunta:
        raise HTTPException(
            status_code=404,
            detail=f"Proyecto {data.proyecto_id} no tiene huella registrada"
        )

    return {
        "mensaje": "Respuesta registrada",
        "categoria": data.categoria,
        "norma": data.norma_relacionada,
        "evidencias_soporte": len(data.evidencia_soporte)
    }


# ============================================================
# ENDPOINTS - RIESGOS RESIDUALES
# ============================================================

@router.post("/riesgos/registrar", response_model=Dict[str, Any])
async def registrar_riesgo_residual(
    data: RegistrarRiesgoInput,
    admin_id: str = Depends(verificar_admin)
):
    """
    Registra un riesgo aceptado conscientemente.
    Esto documenta decisiones con información incompleta.
    """
    service = get_devils_advocate_service()

    try:
        nivel = NivelRiesgoResidual(data.nivel)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Nivel inválido: {data.nivel}. Valores: {[n.value for n in NivelRiesgoResidual]}"
        )

    riesgo = service.registrar_riesgo_residual(
        proyecto_id=data.proyecto_id,
        descripcion=data.descripcion,
        nivel=nivel,
        justificacion=data.justificacion,
        mitigacion_propuesta=data.mitigacion_propuesta,
        aprobado_por=admin_id,
        monto_exposicion=data.monto_exposicion
    )

    if not riesgo:
        raise HTTPException(
            status_code=404,
            detail=f"Proyecto {data.proyecto_id} no tiene huella registrada"
        )

    return {
        "mensaje": f"Riesgo {nivel.value} registrado",
        "descripcion": data.descripcion[:100] + "...",
        "monto_exposicion": data.monto_exposicion,
        "advertencia": "Este riesgo ha sido documentado y aprobado conscientemente."
    }


# ============================================================
# ENDPOINTS - PERFILES DE RIESGO DINÁMICO
# ============================================================

@router.get("/perfiles-riesgo", response_model=Dict[str, Any])
async def obtener_estandar_prueba(
    industria: str = Query(..., description="Industria"),
    tipo_servicio: str = Query(..., description="Tipo de servicio"),
    monto: float = Query(..., description="Monto de la operación"),
    admin_id: str = Depends(verificar_admin)
):
    """
    Obtiene el estándar de prueba aprendido para un tipo de caso.
    Este es el 'mínimo' basado en experiencia real.
    """
    service = get_devils_advocate_service()

    try:
        industria_enum = CategoriaIndustria(industria)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Industria inválida: {industria}"
        )

    return service.obtener_estandar_prueba(
        industria=industria_enum,
        tipo_servicio=tipo_servicio,
        monto=monto
    )


@router.get("/perfiles-riesgo/todos", response_model=List[Dict[str, Any]])
async def listar_perfiles_riesgo(
    admin_id: str = Depends(verificar_admin)
):
    """
    Lista todos los perfiles de riesgo generados.
    """
    service = get_devils_advocate_service()

    perfiles = []
    for clave, perfil in service._perfiles.items():
        perfiles.append({
            "clave": clave,
            "industria": perfil.industria.value,
            "tipo_servicio": perfil.tipo_servicio,
            "rango_monto": perfil.rango_monto,
            "total_casos": perfil.total_casos,
            "tasa_aprobacion": (perfil.casos_aprobados / perfil.total_casos * 100) if perfil.total_casos > 0 else 0,
            "evidencias_minimas": perfil.evidencias_minimas,
            "updated_at": perfil.updated_at.isoformat()
        })

    return perfiles


# ============================================================
# ENDPOINTS - LECCIONES APRENDIDAS
# ============================================================

@router.get("/lecciones", response_model=Dict[str, Any])
async def listar_lecciones(
    tipo_servicio: Optional[str] = Query(None),
    industria: Optional[str] = Query(None),
    admin_id: str = Depends(verificar_admin)
):
    """
    Lista las lecciones aprendidas aplicables a un caso.
    """
    service = get_devils_advocate_service()

    industria_enum = None
    if industria:
        try:
            industria_enum = CategoriaIndustria(industria)
        except ValueError:
            pass

    lecciones = service.obtener_lecciones_aplicables(
        tipo_servicio=tipo_servicio or "todos",
        industria=industria_enum
    )

    return {
        "filtros": {
            "tipo_servicio": tipo_servicio or "todos",
            "industria": industria or "todas"
        },
        "total_lecciones": len(lecciones),
        "lecciones": [
            {
                "id": l.id,
                "titulo": l.titulo,
                "descripcion": l.descripcion,
                "categoria": l.categoria,
                "norma": l.norma_relacionada,
                "problema": l.problema_detectado,
                "solucion": l.solucion_aplicada,
                "efectividad": (l.veces_exitosa / max(l.veces_aplicada, 1)) * 100
            }
            for l in lecciones
        ]
    }


@router.post("/lecciones/registrar", response_model=Dict[str, Any])
async def registrar_leccion_manual(
    data: RegistrarLeccionInput,
    admin_id: str = Depends(verificar_admin)
):
    """
    Registra una lección aprendida manualmente.
    """
    service = get_devils_advocate_service()

    try:
        industria = CategoriaIndustria(data.industria)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Industria inválida: {data.industria}"
        )

    leccion = service.registrar_leccion_manual(
        titulo=data.titulo,
        descripcion=data.descripcion,
        industria=industria,
        tipo_servicio=data.tipo_servicio,
        categoria=data.categoria,
        norma_relacionada=data.norma_relacionada,
        contexto=data.contexto,
        problema_detectado=data.problema_detectado,
        solucion_aplicada=data.solucion_aplicada,
        aplicable_cuando=data.aplicable_cuando,
        admin_id=admin_id
    )

    return {
        "mensaje": "Lección registrada",
        "id": leccion.id,
        "titulo": leccion.titulo
    }


# ============================================================
# ENDPOINTS - INCIDENTES SAT
# ============================================================

@router.post("/incidentes-sat/registrar", response_model=Dict[str, Any])
async def registrar_incidente_sat(
    data: RegistrarIncidenteInput,
    admin_id: str = Depends(verificar_admin)
):
    """
    Registra un incidente posterior con SAT sobre un proyecto aprobado.
    CRÍTICO para evitar sesgos de confirmación.
    """
    service = get_devils_advocate_service()

    incidente = service.registrar_incidente_sat(
        proyecto_id=data.proyecto_id,
        descripcion=data.descripcion,
        tipo_acto=data.tipo_acto,
        monto_cuestionado=data.monto_cuestionado,
        fecha_incidente=datetime.combine(data.fecha_incidente, datetime.min.time()),
        resultado=data.resultado,
        admin_id=admin_id
    )

    return {
        "mensaje": "Incidente SAT registrado",
        "advertencia": "Este registro es CRÍTICO para el aprendizaje del sistema",
        "incidente": incidente
    }


# ============================================================
# ENDPOINTS - REPORTES
# ============================================================

@router.get("/reportes/mejores-practicas", response_model=Dict[str, Any])
async def obtener_reporte_mejores_practicas(
    industria: Optional[str] = Query(None),
    tipo_servicio: Optional[str] = Query(None),
    admin_id: str = Depends(verificar_admin)
):
    """
    Genera un reporte de mejores prácticas basado en el aprendizaje.
    """
    service = get_devils_advocate_service()

    industria_enum = None
    if industria:
        try:
            industria_enum = CategoriaIndustria(industria)
        except ValueError:
            pass

    return service.generar_reporte_mejores_practicas(
        industria=industria_enum,
        tipo_servicio=tipo_servicio
    )


@router.get("/estadisticas", response_model=Dict[str, Any])
async def obtener_estadisticas_globales(
    admin_id: str = Depends(verificar_admin)
):
    """
    Obtiene estadísticas globales del módulo Abogado del Diablo.
    """
    service = get_devils_advocate_service()
    return service.obtener_estadisticas_globales()


# ============================================================
# ENDPOINTS - CATÁLOGOS
# ============================================================

@router.get("/catalogos/industrias", response_model=List[Dict[str, str]])
async def listar_industrias(admin_id: str = Depends(verificar_admin)):
    """Lista las industrias disponibles"""
    return [
        {"id": i.value, "nombre": i.value.replace("_", " ").title()}
        for i in CategoriaIndustria
    ]


@router.get("/catalogos/niveles-riesgo", response_model=List[Dict[str, str]])
async def listar_niveles_riesgo(admin_id: str = Depends(verificar_admin)):
    """Lista los niveles de riesgo residual"""
    descripciones = {
        "ninguno": "Sin riesgo residual identificado",
        "bajo": "Riesgo menor, documentado preventivamente",
        "medio": "Riesgo aceptable con justificación sólida",
        "alto": "Riesgo alto, requiere aprobación consciente",
        "critico": "Riesgo crítico, requiere aprobación especial"
    }
    return [
        {"id": n.value, "nombre": n.value.title(), "descripcion": descripciones.get(n.value, "")}
        for n in NivelRiesgoResidual
    ]


@router.get("/catalogos/fases", response_model=List[Dict[str, str]])
async def listar_fases(admin_id: str = Depends(verificar_admin)):
    """Lista las fases del flujo F0-F9"""
    descripciones = {
        "F0": "Intake - Captura inicial",
        "F1": "Proveedor - Datos y SOW",
        "F2": "Candado - Validación A1+A6",
        "F3": "Ejecución - Kick-off",
        "F4": "Revisión - Entregables",
        "F5": "Entrega - Aceptación técnica",
        "F6": "VBC - Candado Fiscal/Legal",
        "F7": "Auditoría - QA interno",
        "F8": "Pago - 3-Way Match",
        "F9": "Cierre - Defense File"
    }
    return [
        {"id": f.value, "nombre": f.value, "descripcion": descripciones.get(f.value, "")}
        for f in FaseProyecto
    ]


# ============================================================
# ENDPOINTS - PREGUNTAS ESTRUCTURADAS (25 PREGUNTAS CON SEVERIDAD)
# ============================================================

@router.get("/preguntas-estructuradas/bloques", response_model=List[Dict[str, Any]])
async def obtener_bloques_preguntas(admin_id: str = Depends(verificar_admin)):
    """
    Obtiene la estructura de los 6 bloques de preguntas.
    Cada bloque tiene un peso específico en el score final.
    """
    service = get_devils_advocate_service()
    return service.obtener_bloques_preguntas()


@router.get("/preguntas-estructuradas", response_model=Dict[str, Any])
async def listar_preguntas_estructuradas(
    bloque: Optional[str] = Query(None, description="Filtrar por bloque (B1_hechos_objeto, etc.)"),
    solo_obligatorias: bool = Query(False, description="Solo preguntas obligatorias"),
    solo_criticas: bool = Query(False, description="Solo preguntas con severidad crítica"),
    admin_id: str = Depends(verificar_admin)
):
    """
    Lista las 25 preguntas estructuradas con sus metadatos completos.

    Incluye:
    - Nivel de severidad (critico/importante/informativo)
    - Tipo de respuesta esperada
    - Acciones a disparar según respuesta
    - Umbrales de alerta
    """
    service = get_devils_advocate_service()

    bloque_enum = None
    if bloque:
        try:
            bloque_enum = BloquePregunta(bloque)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Bloque inválido: {bloque}. Valores: {[b.value for b in BloquePregunta]}"
            )

    preguntas = service.obtener_preguntas_estructuradas(
        bloque=bloque_enum,
        solo_obligatorias=solo_obligatorias,
        solo_criticas=solo_criticas
    )

    # Agrupar por bloque para mejor visualización
    por_bloque = {}
    for p in preguntas:
        bloque_key = p["bloque"]
        if bloque_key not in por_bloque:
            por_bloque[bloque_key] = []
        por_bloque[bloque_key].append(p)

    return {
        "total_preguntas": len(preguntas),
        "filtros": {
            "bloque": bloque,
            "solo_obligatorias": solo_obligatorias,
            "solo_criticas": solo_criticas
        },
        "resumen_severidad": {
            "critico": len([p for p in preguntas if p["severidad"] == "critico"]),
            "importante": len([p for p in preguntas if p["severidad"] == "importante"]),
            "informativo": len([p for p in preguntas if p["severidad"] == "informativo"])
        },
        "preguntas_por_bloque": por_bloque,
        "preguntas": preguntas
    }


@router.get("/preguntas-estructuradas/{pregunta_id}", response_model=Dict[str, Any])
async def obtener_pregunta_por_id(
    pregunta_id: str,
    admin_id: str = Depends(verificar_admin)
):
    """
    Obtiene una pregunta específica por su ID.
    Ejemplo: P01_DESCRIPCION_SERVICIO, P13_LISTA_69B
    """
    from services.devils_advocate_service import PREGUNTAS_POR_ID

    if pregunta_id not in PREGUNTAS_POR_ID:
        raise HTTPException(
            status_code=404,
            detail=f"Pregunta {pregunta_id} no encontrada"
        )

    p = PREGUNTAS_POR_ID[pregunta_id]

    return {
        "id": p.id,
        "numero": p.numero,
        "bloque": p.bloque.value,
        "pregunta": p.pregunta,
        "descripcion": p.descripcion,
        "severidad": p.severidad.value,
        "tipo_respuesta": p.tipo_respuesta.value,
        "norma_relacionada": p.norma_relacionada,
        "opciones": p.opciones,
        "obligatoria": p.obligatoria,
        "umbral_critico": p.umbral_critico,
        "umbral_alerta": p.umbral_alerta,
        "accion_si_negativo": p.accion_si_negativo.value,
        "accion_si_incompleto": p.accion_si_incompleto.value
    }


@router.post("/preguntas-estructuradas/evaluar", response_model=Dict[str, Any])
async def evaluar_respuesta_estructurada(
    data: RespuestaEstructuradaInput,
    admin_id: str = Depends(verificar_admin)
):
    """
    Evalúa una respuesta individual y determina la acción a tomar.

    Retorna:
    - accion: forzar_revision, bandera_roja, alerta, solo_aprendizaje
    - bandera_roja: Si la respuesta genera una bandera roja
    - requiere_revision_adicional: Si requiere revisión obligatoria
    - alertas: Lista de alertas generadas
    """
    service = get_devils_advocate_service()

    evaluacion = service.evaluar_respuesta_estructurada(
        pregunta_id=data.pregunta_id,
        respuesta=data.respuesta,
        indice_opcion=data.indice_opcion
    )

    return evaluacion


@router.post("/preguntas-estructuradas/evaluar-completo", response_model=Dict[str, Any])
async def evaluar_todas_respuestas(
    data: EvaluacionCompletaInput,
    admin_id: str = Depends(verificar_admin)
):
    """
    Genera un resumen consolidado de todas las respuestas de un proyecto.

    Retorna:
    - score_total: Score ponderado total (0-100)
    - score_por_bloque: Scores individuales por cada bloque
    - semaforo: verde/amarillo/rojo
    - banderas_rojas: Lista de banderas rojas detectadas
    - alertas: Lista de alertas generadas
    - recomendacion: Texto con recomendación de acción
    """
    service = get_devils_advocate_service()

    resumen = service.generar_resumen_evaluacion(data.respuestas)

    return {
        "proyecto_id": data.proyecto_id,
        "evaluacion": resumen,
        "fecha_evaluacion": datetime.now().isoformat()
    }


@router.get("/preguntas-estructuradas/criticas-pendientes/{proyecto_id}", response_model=Dict[str, Any])
async def obtener_criticas_pendientes(
    proyecto_id: str,
    admin_id: str = Depends(verificar_admin)
):
    """
    Obtiene las preguntas críticas que aún no han sido respondidas para un proyecto.
    Útil para verificar completitud antes de aprobar.
    """
    service = get_devils_advocate_service()

    # Obtener todas las preguntas críticas obligatorias
    criticas = service.obtener_preguntas_estructuradas(
        solo_obligatorias=True,
        solo_criticas=True
    )

    # TODO: Cruzar con respuestas almacenadas para el proyecto
    # Por ahora, devolver todas las críticas como pendientes

    return {
        "proyecto_id": proyecto_id,
        "total_criticas": len(criticas),
        "pendientes": criticas,
        "advertencia": "Todas las preguntas críticas deben ser respondidas antes de aprobar"
    }


@router.get("/catalogos/bloques-preguntas", response_model=List[Dict[str, Any]])
async def listar_bloques_preguntas(admin_id: str = Depends(verificar_admin)):
    """Lista los bloques de preguntas estructuradas"""
    return [
        {
            "id": b.value,
            "nombre": b.value.replace("_", " ").title(),
            "total_preguntas": len(PREGUNTAS_POR_BLOQUE.get(b, []))
        }
        for b in BloquePregunta
    ]


@router.get("/catalogos/severidades", response_model=List[Dict[str, str]])
async def listar_severidades(admin_id: str = Depends(verificar_admin)):
    """Lista los niveles de severidad de preguntas"""
    descripciones = {
        "critico": "Respuesta negativa genera bandera roja y fuerza revisión adicional",
        "importante": "Respuesta negativa genera alerta, revisión recomendada",
        "informativo": "Solo alimenta aprendizaje histórico, sin acciones inmediatas"
    }
    return [
        {"id": s.value, "nombre": s.value.title(), "descripcion": descripciones.get(s.value, "")}
        for s in NivelSeveridad
    ]
