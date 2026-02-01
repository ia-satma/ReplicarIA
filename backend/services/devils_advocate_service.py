"""
============================================================
REVISAR.IA - Servicio "Abogado del Diablo"
============================================================
Módulo interno de control y aprendizaje organizacional.
Acceso exclusivo para administradores.

PROPÓSITO:
- Cuestionar sistemáticamente decisiones de aprobación
- Registrar el "cómo" y "cuándo" de cada decisión
- Aprender patrones por industria y tipo de servicio
- Generar estándares de prueba basados en experiencia real
- Documentar riesgos residuales aceptados

NOTA IMPORTANTE:
Este módulo genera información altamente sensible (diario interno
de decisiones). Debe tratarse como herramienta interna de compliance,
NO como documentación a entregar a autoridades.

============================================================
"""

from enum import Enum
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import logging
import json

logger = logging.getLogger(__name__)


# ============================================================
# ENUMS
# ============================================================

class TipoRegistro(str, Enum):
    """Tipos de registro del Abogado del Diablo"""
    APROBACION = "aprobacion"  # Proyecto aprobado
    RECHAZO = "rechazo"  # Proyecto rechazado
    CAMBIO_COLOR = "cambio_color"  # Cambio de semáforo
    PREGUNTA_INCOMODA = "pregunta_incomoda"  # Cuestionamiento registrado
    RIESGO_ACEPTADO = "riesgo_aceptado"  # Riesgo residual documentado
    LECCION_APRENDIDA = "leccion_aprendida"  # Patrón identificado
    INCIDENTE_SAT = "incidente_sat"  # Problema posterior con SAT


class CategoriaIndustria(str, Enum):
    """Categorías de industria para perfiles de riesgo"""
    RETAIL = "retail"
    MANUFACTURA = "manufactura"
    SERVICIOS_FINANCIEROS = "servicios_financieros"
    TECNOLOGIA = "tecnologia"
    SALUD = "salud"
    CONSTRUCCION = "construccion"
    ALIMENTOS = "alimentos"
    ENERGIA = "energia"
    TRANSPORTE = "transporte"
    EDUCACION = "educacion"
    COMERCIO_EXTERIOR = "comercio_exterior"
    INMOBILIARIO = "inmobiliario"
    OTRO = "otro"


class NivelRiesgoResidual(str, Enum):
    """Nivel de riesgo residual aceptado"""
    NINGUNO = "ninguno"  # Sin riesgo residual
    BAJO = "bajo"  # Riesgo menor documentado
    MEDIO = "medio"  # Riesgo aceptable con justificación
    ALTO = "alto"  # Riesgo alto aceptado conscientemente
    CRITICO = "critico"  # Riesgo crítico (requiere aprobación especial)


class NivelSeveridad(str, Enum):
    """Nivel de severidad de las preguntas"""
    CRITICO = "critico"  # Respuesta negativa = bandera roja, forzar revisión adicional
    IMPORTANTE = "importante"  # Respuesta negativa = alerta, revisión recomendada
    INFORMATIVO = "informativo"  # Solo alimenta aprendizaje histórico


class TipoRespuesta(str, Enum):
    """Tipo de respuesta esperada para la pregunta"""
    TEXTO_CORTO = "texto_corto"  # Respuesta breve
    TEXTO_LARGO = "texto_largo"  # Descripción detallada
    SELECCION_SIMPLE = "seleccion_simple"  # Sí/No
    SELECCION_MULTIPLE = "seleccion_multiple"  # Varias opciones
    ESCALA = "escala"  # Bajo/Medio/Alto
    PORCENTAJE = "porcentaje"  # 0-100%
    MONTO = "monto"  # Valor numérico


class AccionRespuesta(str, Enum):
    """Acción a disparar según la respuesta"""
    FORZAR_REVISION = "forzar_revision"  # Requiere revisión adicional obligatoria
    BANDERA_ROJA = "bandera_roja"  # Marca alerta crítica
    ALERTA = "alerta"  # Genera alerta (no crítica)
    SOLO_APRENDIZAJE = "solo_aprendizaje"  # Solo alimenta historial


class BloquePregunta(str, Enum):
    """Bloque temático de la pregunta"""
    B1_HECHOS_OBJETO = "B1_hechos_objeto"  # Hechos y Objeto del Servicio
    B2_MATERIALIDAD = "B2_materialidad"  # Materialidad / CFF 69-B
    B3_RAZON_NEGOCIOS = "B3_razon_negocios"  # Razón de Negocios / CFF 5-A
    B4_PROVEEDOR_EFOS = "B4_proveedor_efos"  # Proveedor y EFOS
    B5_FORMAL_FISCAL = "B5_formal_fiscal"  # Requisitos Fiscales Formales
    B6_RIESGO_RESIDUAL = "B6_riesgo_residual"  # Riesgo Residual y Lecciones


class FaseProyecto(str, Enum):
    """Fases del flujo F0-F9"""
    F0_INTAKE = "F0"
    F1_PROVEEDOR = "F1"
    F2_CANDADO = "F2"
    F3_EJECUCION = "F3"
    F4_REVISION = "F4"
    F5_ENTREGA = "F5"
    F6_VBC = "F6"
    F7_AUDITORIA = "F7"
    F8_PAGO = "F8"
    F9_CIERRE = "F9"


# ============================================================
# MODELOS DE DATOS
# ============================================================

@dataclass
class CambioSemaforo:
    """Registro de cambio de color en el semáforo"""
    fase: FaseProyecto
    fecha: datetime
    color_anterior: str
    color_nuevo: str
    score_anterior: float
    score_nuevo: float
    agente_responsable: str
    evidencia_que_cambio: List[str]
    justificacion: str
    version_entregable: str


@dataclass
class PreguntaIncomoda:
    """Pregunta de cuestionamiento y su respuesta"""
    categoria: str  # materialidad, razon_negocios, formal, proveedor
    pregunta: str
    respuesta: str
    evidencia_soporte: List[str]
    norma_relacionada: str  # LISR_27, CFF_69B, etc.
    efectiva: bool = True  # Si funcionó como argumento
    fecha_registro: datetime = field(default_factory=datetime.now)


@dataclass
class RiesgoResidual:
    """Riesgo aceptado conscientemente"""
    descripcion: str
    nivel: NivelRiesgoResidual
    justificacion: str
    mitigacion_propuesta: str
    aprobado_por: str
    fecha_aprobacion: datetime
    monto_exposicion: float = 0.0


@dataclass
class EvidenciaClave:
    """Evidencia que hizo la diferencia en una decisión"""
    tipo_evidencia: str
    descripcion: str
    norma_acreditada: str  # LISR_27, CFF_69B, CFF_5A, LIVA_5, NOM_151
    impacto: str  # amarillo_a_verde, rechazo_a_aprobado, etc.
    reusable: bool = True
    notas: str = ""


@dataclass
class HuellaRevision:
    """Huella completa de revisión de un proyecto"""
    proyecto_id: str
    empresa_id: str
    industria: CategoriaIndustria
    tipo_servicio: str
    monto: float
    proveedor_rfc: str

    # Timeline
    fecha_inicio: datetime
    fecha_cierre: Optional[datetime]
    resultado_final: str  # aprobado, rechazado, en_proceso

    # Scores por fase
    scores_por_fase: Dict[str, Dict[str, float]]  # {F2: {formal: 80, materialidad: 75, razon: 85}}

    # Cambios de color
    cambios_semaforo: List[CambioSemaforo]

    # Evidencias clave
    evidencias_clave: List[EvidenciaClave]

    # Preguntas incómodas
    preguntas_respondidas: List[PreguntaIncomoda]

    # Riesgos aceptados
    riesgos_residuales: List[RiesgoResidual]

    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    created_by: str = ""


@dataclass
class PerfilRiesgoDinamico:
    """Perfil de riesgo aprendido por industria/servicio"""
    industria: CategoriaIndustria
    tipo_servicio: str
    rango_monto: str  # "<500k", "500k-2M", ">2M"

    # Estadísticas
    total_casos: int
    casos_aprobados: int
    casos_rechazados: int
    score_promedio_aprobados: float

    # Evidencias mínimas requeridas (aprendidas)
    evidencias_minimas: List[str]

    # Objeciones frecuentes
    objeciones_frecuentes: List[Dict[str, str]]

    # Patrones de éxito
    patrones_exito: List[str]

    # Alertas especiales
    alertas: List[str]

    # Última actualización
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class LeccionAprendida:
    """Lección aprendida de casos anteriores"""
    id: str
    titulo: str
    descripcion: str
    industria: CategoriaIndustria
    tipo_servicio: str
    categoria: str  # materialidad, razon_negocios, formal, proveedor
    norma_relacionada: str

    # Contexto
    contexto: str
    problema_detectado: str
    solucion_aplicada: str

    # Aplicabilidad
    aplicable_cuando: List[str]
    no_aplicable_cuando: List[str]

    # Efectividad
    veces_aplicada: int = 0
    veces_exitosa: int = 0

    created_at: datetime = field(default_factory=datetime.now)


# ============================================================
# MODELO DE PREGUNTA ESTRUCTURADA
# ============================================================

@dataclass
class PreguntaEstructurada:
    """Pregunta del Abogado del Diablo con metadatos completos"""
    id: str
    bloque: BloquePregunta
    numero: int
    pregunta: str
    descripcion: str  # Contexto adicional
    severidad: NivelSeveridad
    tipo_respuesta: TipoRespuesta
    norma_relacionada: str

    # Acciones según respuesta
    accion_si_negativo: AccionRespuesta
    accion_si_incompleto: AccionRespuesta

    # Opciones (si aplica)
    opciones: Optional[List[str]] = None

    # Umbral de alerta (para escalas y porcentajes)
    umbral_critico: Optional[float] = None
    umbral_alerta: Optional[float] = None

    # Aplicabilidad
    aplica_a_servicios: List[str] = field(default_factory=lambda: ["todos"])
    obligatoria: bool = True


# ============================================================
# 25 PREGUNTAS ESTRUCTURADAS EN 6 BLOQUES
# ============================================================

PREGUNTAS_ESTRUCTURADAS: List[PreguntaEstructurada] = [
    # ============================================================
    # BLOQUE 1: HECHOS Y OBJETO DEL SERVICIO (Preguntas 1-4)
    # ============================================================
    PreguntaEstructurada(
        id="P01_DESCRIPCION_SERVICIO",
        bloque=BloquePregunta.B1_HECHOS_OBJETO,
        numero=1,
        pregunta="¿Puedes describir el servicio exactamente como lo entendería un auditor que no sabe nada del negocio?",
        descripcion="Verificar que la descripción del servicio sea clara, específica y comprensible para un tercero sin contexto previo.",
        severidad=NivelSeveridad.IMPORTANTE,
        tipo_respuesta=TipoRespuesta.TEXTO_LARGO,
        norma_relacionada="CFF_69B",
        accion_si_negativo=AccionRespuesta.ALERTA,
        accion_si_incompleto=AccionRespuesta.FORZAR_REVISION,
        aplica_a_servicios=["todos"],
        obligatoria=True
    ),
    PreguntaEstructurada(
        id="P02_ENTREGABLE_CONCRETO",
        bloque=BloquePregunta.B1_HECHOS_OBJETO,
        numero=2,
        pregunta="¿Cuál es el entregable físico o digital concreto que generó este servicio?",
        descripcion="Identificar evidencia tangible del resultado del servicio.",
        severidad=NivelSeveridad.CRITICO,
        tipo_respuesta=TipoRespuesta.TEXTO_CORTO,
        norma_relacionada="CFF_69B",
        accion_si_negativo=AccionRespuesta.BANDERA_ROJA,
        accion_si_incompleto=AccionRespuesta.FORZAR_REVISION,
        aplica_a_servicios=["todos"],
        obligatoria=True
    ),
    PreguntaEstructurada(
        id="P03_EVIDENCIA_EJECUCION",
        bloque=BloquePregunta.B1_HECHOS_OBJETO,
        numero=3,
        pregunta="¿Cómo demostrarías que el servicio se prestó entre las fechas del contrato y la factura?",
        descripcion="Verificar correspondencia temporal entre documentos y ejecución real.",
        severidad=NivelSeveridad.CRITICO,
        tipo_respuesta=TipoRespuesta.TEXTO_LARGO,
        norma_relacionada="CFF_28_30",
        accion_si_negativo=AccionRespuesta.BANDERA_ROJA,
        accion_si_incompleto=AccionRespuesta.FORZAR_REVISION,
        aplica_a_servicios=["todos"],
        obligatoria=True
    ),
    PreguntaEstructurada(
        id="P04_TESTIGO_INDEPENDIENTE",
        bloque=BloquePregunta.B1_HECHOS_OBJETO,
        numero=4,
        pregunta="¿Hay algún testigo, correo o registro de terceros que corrobore la ejecución?",
        descripcion="Buscar evidencia independiente que refuerce la materialidad.",
        severidad=NivelSeveridad.IMPORTANTE,
        tipo_respuesta=TipoRespuesta.SELECCION_SIMPLE,
        norma_relacionada="CFF_69B",
        accion_si_negativo=AccionRespuesta.ALERTA,
        accion_si_incompleto=AccionRespuesta.SOLO_APRENDIZAJE,
        opciones=["Sí, existe evidencia de terceros", "No, solo evidencia bilateral", "Parcialmente"],
        aplica_a_servicios=["todos"],
        obligatoria=True
    ),

    # ============================================================
    # BLOQUE 2: MATERIALIDAD / CFF 69-B - EVIDENCIA DURA (Preguntas 5-8)
    # ============================================================
    PreguntaEstructurada(
        id="P05_CAPACIDAD_PROVEEDOR",
        bloque=BloquePregunta.B2_MATERIALIDAD,
        numero=5,
        pregunta="¿El proveedor tiene la capacidad material, humana y técnica demostrable para prestar este servicio?",
        descripcion="Evaluar si el proveedor podría razonablemente haber prestado el servicio según su estructura.",
        severidad=NivelSeveridad.CRITICO,
        tipo_respuesta=TipoRespuesta.ESCALA,
        norma_relacionada="CFF_69B",
        accion_si_negativo=AccionRespuesta.BANDERA_ROJA,
        accion_si_incompleto=AccionRespuesta.FORZAR_REVISION,
        opciones=["Alta capacidad demostrada", "Capacidad parcial/inferida", "Capacidad dudosa", "Sin evidencia de capacidad"],
        umbral_critico=2,  # "Capacidad dudosa" o peor
        aplica_a_servicios=["todos"],
        obligatoria=True
    ),
    PreguntaEstructurada(
        id="P06_DOMICILIO_VERIFICABLE",
        bloque=BloquePregunta.B2_MATERIALIDAD,
        numero=6,
        pregunta="¿El domicilio fiscal del proveedor es verificable y congruente con su actividad?",
        descripcion="Verificar que el domicilio fiscal exista y sea apropiado para la operación declarada.",
        severidad=NivelSeveridad.CRITICO,
        tipo_respuesta=TipoRespuesta.SELECCION_SIMPLE,
        norma_relacionada="CFF_69B",
        accion_si_negativo=AccionRespuesta.BANDERA_ROJA,
        accion_si_incompleto=AccionRespuesta.FORZAR_REVISION,
        opciones=["Verificado y congruente", "Verificado pero cuestionable", "No verificable", "No localizable"],
        aplica_a_servicios=["todos"],
        obligatoria=True
    ),
    PreguntaEstructurada(
        id="P07_RASTRO_DIGITAL",
        bloque=BloquePregunta.B2_MATERIALIDAD,
        numero=7,
        pregunta="¿Existe un rastro digital independiente y verificable de la prestación del servicio?",
        descripcion="Identificar evidencia digital que no pueda ser fabricada unilateralmente.",
        severidad=NivelSeveridad.IMPORTANTE,
        tipo_respuesta=TipoRespuesta.SELECCION_MULTIPLE,
        norma_relacionada="NOM_151",
        accion_si_negativo=AccionRespuesta.ALERTA,
        accion_si_incompleto=AccionRespuesta.SOLO_APRENDIZAJE,
        opciones=["Correos con timestamps", "Plataformas de gestión de proyectos", "Métricas de terceros", "Logs de sistemas", "Ninguno de los anteriores"],
        aplica_a_servicios=["todos"],
        obligatoria=True
    ),
    PreguntaEstructurada(
        id="P08_FABRICACION_POSTERIOR",
        bloque=BloquePregunta.B2_MATERIALIDAD,
        numero=8,
        pregunta="¿La evidencia presentada podría haber sido fabricada o generada después de los hechos?",
        descripcion="Evaluar el riesgo de que la documentación haya sido creada ex post facto.",
        severidad=NivelSeveridad.CRITICO,
        tipo_respuesta=TipoRespuesta.ESCALA,
        norma_relacionada="CFF_69B",
        accion_si_negativo=AccionRespuesta.BANDERA_ROJA,
        accion_si_incompleto=AccionRespuesta.FORZAR_REVISION,
        opciones=["Imposible de fabricar (sellos/terceros)", "Difícil de fabricar", "Posible fabricación", "Alta probabilidad de fabricación"],
        umbral_critico=2,  # "Posible fabricación" o peor
        aplica_a_servicios=["todos"],
        obligatoria=True
    ),

    # ============================================================
    # BLOQUE 3: RAZÓN DE NEGOCIOS / CFF 5-A (Preguntas 9-12)
    # ============================================================
    PreguntaEstructurada(
        id="P09_BENEFICIO_SIN_FISCAL",
        bloque=BloquePregunta.B3_RAZON_NEGOCIOS,
        numero=9,
        pregunta="¿Qué beneficio económico concreto obtuvo la empresa, independientemente del efecto fiscal?",
        descripcion="Identificar el valor real del servicio más allá de la deducción.",
        severidad=NivelSeveridad.CRITICO,
        tipo_respuesta=TipoRespuesta.TEXTO_LARGO,
        norma_relacionada="CFF_5A",
        accion_si_negativo=AccionRespuesta.BANDERA_ROJA,
        accion_si_incompleto=AccionRespuesta.FORZAR_REVISION,
        aplica_a_servicios=["todos"],
        obligatoria=True
    ),
    PreguntaEstructurada(
        id="P10_ALTERNATIVA_INTERNA",
        bloque=BloquePregunta.B3_RAZON_NEGOCIOS,
        numero=10,
        pregunta="¿Por qué no se hizo internamente si la empresa tiene o podría tener la capacidad?",
        descripcion="Justificar la necesidad de externalizar vs. desarrollar internamente.",
        severidad=NivelSeveridad.IMPORTANTE,
        tipo_respuesta=TipoRespuesta.SELECCION_SIMPLE,
        norma_relacionada="CFF_5A",
        accion_si_negativo=AccionRespuesta.ALERTA,
        accion_si_incompleto=AccionRespuesta.SOLO_APRENDIZAJE,
        opciones=[
            "Especialización técnica no disponible internamente",
            "Capacidad insuficiente (tiempo/recursos)",
            "Costo-beneficio favorable a tercerizar",
            "No se evaluó la alternativa interna"
        ],
        aplica_a_servicios=["todos"],
        obligatoria=True
    ),
    PreguntaEstructurada(
        id="P11_PRECIO_MERCADO",
        bloque=BloquePregunta.B3_RAZON_NEGOCIOS,
        numero=11,
        pregunta="¿El precio pagado es congruente con referencias de mercado para servicios similares?",
        descripcion="Verificar que el precio no sea artificialmente alto o bajo.",
        severidad=NivelSeveridad.IMPORTANTE,
        tipo_respuesta=TipoRespuesta.ESCALA,
        norma_relacionada="LISR_27",
        accion_si_negativo=AccionRespuesta.ALERTA,
        accion_si_incompleto=AccionRespuesta.FORZAR_REVISION,
        opciones=["Dentro de rango de mercado", "Ligeramente por arriba", "Significativamente elevado", "Sin referencia comparable"],
        umbral_critico=2,  # "Significativamente elevado"
        aplica_a_servicios=["todos"],
        obligatoria=True
    ),
    PreguntaEstructurada(
        id="P12_RESULTADO_MEDIBLE",
        bloque=BloquePregunta.B3_RAZON_NEGOCIOS,
        numero=12,
        pregunta="¿Se midió o evaluó el resultado del servicio? ¿Existe evidencia de la medición?",
        descripcion="Verificar que el servicio tuvo un impacto evaluable.",
        severidad=NivelSeveridad.INFORMATIVO,
        tipo_respuesta=TipoRespuesta.SELECCION_SIMPLE,
        norma_relacionada="CFF_5A",
        accion_si_negativo=AccionRespuesta.SOLO_APRENDIZAJE,
        accion_si_incompleto=AccionRespuesta.SOLO_APRENDIZAJE,
        opciones=["Sí, con métricas documentadas", "Sí, evaluación informal", "No se midió", "No aplica medición"],
        aplica_a_servicios=["todos"],
        obligatoria=False
    ),

    # ============================================================
    # BLOQUE 4: PROVEEDOR Y EFOS (Preguntas 13-16)
    # ============================================================
    PreguntaEstructurada(
        id="P13_LISTA_69B",
        bloque=BloquePregunta.B4_PROVEEDOR_EFOS,
        numero=13,
        pregunta="¿Se verificó que el proveedor NO esté en lista 69-B antes de contratar y al momento de pagar?",
        descripcion="Verificación obligatoria en lista de operaciones simuladas del SAT.",
        severidad=NivelSeveridad.CRITICO,
        tipo_respuesta=TipoRespuesta.SELECCION_SIMPLE,
        norma_relacionada="CFF_69B",
        accion_si_negativo=AccionRespuesta.BANDERA_ROJA,
        accion_si_incompleto=AccionRespuesta.BANDERA_ROJA,
        opciones=["Verificado limpio en ambas fechas", "Solo verificado al contratar", "En lista 69-B", "No se verificó"],
        aplica_a_servicios=["todos"],
        obligatoria=True
    ),
    PreguntaEstructurada(
        id="P14_OPINION_32D",
        bloque=BloquePregunta.B4_PROVEEDOR_EFOS,
        numero=14,
        pregunta="¿Se cuenta con opinión de cumplimiento 32-D positiva y vigente del proveedor?",
        descripcion="Verificar cumplimiento fiscal del proveedor mediante constancia oficial.",
        severidad=NivelSeveridad.IMPORTANTE,
        tipo_respuesta=TipoRespuesta.SELECCION_SIMPLE,
        norma_relacionada="CFF_32D",
        accion_si_negativo=AccionRespuesta.ALERTA,
        accion_si_incompleto=AccionRespuesta.ALERTA,
        opciones=["Opinión positiva vigente", "Opinión vencida", "Opinión negativa", "No se solicitó"],
        aplica_a_servicios=["todos"],
        obligatoria=True
    ),
    PreguntaEstructurada(
        id="P15_HISTORIAL_PROVEEDOR",
        bloque=BloquePregunta.B4_PROVEEDOR_EFOS,
        numero=15,
        pregunta="¿El proveedor tiene historial verificable de operaciones reales con otros clientes?",
        descripcion="Evaluar si el proveedor tiene trayectoria comercial legítima.",
        severidad=NivelSeveridad.IMPORTANTE,
        tipo_respuesta=TipoRespuesta.ESCALA,
        norma_relacionada="CFF_69B",
        accion_si_negativo=AccionRespuesta.ALERTA,
        accion_si_incompleto=AccionRespuesta.SOLO_APRENDIZAJE,
        opciones=["Historial amplio verificable", "Historial limitado pero real", "Historial no verificable", "Proveedor nuevo/desconocido"],
        umbral_alerta=2,  # "Historial no verificable"
        aplica_a_servicios=["todos"],
        obligatoria=True
    ),
    PreguntaEstructurada(
        id="P16_EMPLEADOS_IMSS",
        bloque=BloquePregunta.B4_PROVEEDOR_EFOS,
        numero=16,
        pregunta="¿El proveedor tiene empleados registrados en IMSS congruentes con su operación?",
        descripcion="Verificar que el proveedor tenga estructura laboral real.",
        severidad=NivelSeveridad.IMPORTANTE,
        tipo_respuesta=TipoRespuesta.SELECCION_SIMPLE,
        norma_relacionada="CFF_69B",
        accion_si_negativo=AccionRespuesta.ALERTA,
        accion_si_incompleto=AccionRespuesta.SOLO_APRENDIZAJE,
        opciones=["Plantilla congruente verificada", "Plantilla mínima pero existente", "Sin empleados registrados", "No verificable"],
        aplica_a_servicios=["todos"],
        obligatoria=True
    ),

    # ============================================================
    # BLOQUE 5: REQUISITOS FISCALES FORMALES (Preguntas 17-21)
    # ============================================================
    PreguntaEstructurada(
        id="P17_CFDI_DETALLE",
        bloque=BloquePregunta.B5_FORMAL_FISCAL,
        numero=17,
        pregunta="¿El CFDI tiene descripción suficientemente detallada del servicio prestado?",
        descripcion="Verificar que el concepto del CFDI identifique claramente el servicio.",
        severidad=NivelSeveridad.CRITICO,
        tipo_respuesta=TipoRespuesta.ESCALA,
        norma_relacionada="CFF_29_29A",
        accion_si_negativo=AccionRespuesta.BANDERA_ROJA,
        accion_si_incompleto=AccionRespuesta.FORZAR_REVISION,
        opciones=["Descripción detallada y específica", "Descripción adecuada", "Descripción genérica", "Descripción insuficiente"],
        umbral_critico=2,  # "Descripción genérica" o peor
        aplica_a_servicios=["todos"],
        obligatoria=True
    ),
    PreguntaEstructurada(
        id="P18_COINCIDENCIA_CONTRATO_CFDI",
        bloque=BloquePregunta.B5_FORMAL_FISCAL,
        numero=18,
        pregunta="¿Los datos del contrato coinciden exactamente con lo facturado en el CFDI?",
        descripcion="Verificar consistencia entre documentos contractuales y fiscales.",
        severidad=NivelSeveridad.CRITICO,
        tipo_respuesta=TipoRespuesta.SELECCION_SIMPLE,
        norma_relacionada="CFF_29_29A",
        accion_si_negativo=AccionRespuesta.BANDERA_ROJA,
        accion_si_incompleto=AccionRespuesta.FORZAR_REVISION,
        opciones=["Coincidencia exacta", "Diferencias menores explicables", "Diferencias significativas", "No hay contrato"],
        aplica_a_servicios=["todos"],
        obligatoria=True
    ),
    PreguntaEstructurada(
        id="P19_PAGO_BANCARIZADO",
        bloque=BloquePregunta.B5_FORMAL_FISCAL,
        numero=19,
        pregunta="¿El pago se realizó por transferencia bancaria a cuenta del proveedor y está debidamente documentado?",
        descripcion="Verificar trazabilidad bancaria del pago.",
        severidad=NivelSeveridad.CRITICO,
        tipo_respuesta=TipoRespuesta.SELECCION_SIMPLE,
        norma_relacionada="LISR_27",
        accion_si_negativo=AccionRespuesta.BANDERA_ROJA,
        accion_si_incompleto=AccionRespuesta.FORZAR_REVISION,
        opciones=["Transferencia a cuenta del proveedor verificada", "Otro medio bancarizado documentado", "Pago en efectivo parcial", "Sin trazabilidad bancaria"],
        aplica_a_servicios=["todos"],
        obligatoria=True
    ),
    PreguntaEstructurada(
        id="P20_CONGRUENCIA_FECHAS",
        bloque=BloquePregunta.B5_FORMAL_FISCAL,
        numero=20,
        pregunta="¿Hay congruencia lógica entre las fechas de contrato, servicio, factura y pago?",
        descripcion="Verificar que la secuencia temporal sea lógica y no presente inconsistencias.",
        severidad=NivelSeveridad.IMPORTANTE,
        tipo_respuesta=TipoRespuesta.SELECCION_SIMPLE,
        norma_relacionada="CFF_28_30",
        accion_si_negativo=AccionRespuesta.ALERTA,
        accion_si_incompleto=AccionRespuesta.FORZAR_REVISION,
        opciones=["Secuencia lógica perfecta", "Pequeñas inconsistencias explicables", "Inconsistencias notables", "Secuencia ilógica"],
        aplica_a_servicios=["todos"],
        obligatoria=True
    ),
    PreguntaEstructurada(
        id="P21_REGIMEN_CONGRUENTE",
        bloque=BloquePregunta.B5_FORMAL_FISCAL,
        numero=21,
        pregunta="¿El régimen fiscal del proveedor es congruente con el tipo de servicio prestado?",
        descripcion="Verificar que el proveedor pueda legalmente prestar el servicio según su régimen.",
        severidad=NivelSeveridad.IMPORTANTE,
        tipo_respuesta=TipoRespuesta.SELECCION_SIMPLE,
        norma_relacionada="LISR_27",
        accion_si_negativo=AccionRespuesta.ALERTA,
        accion_si_incompleto=AccionRespuesta.SOLO_APRENDIZAJE,
        opciones=["Régimen plenamente congruente", "Régimen aceptable", "Régimen cuestionable", "Régimen incompatible"],
        aplica_a_servicios=["todos"],
        obligatoria=True
    ),

    # ============================================================
    # BLOQUE 6: RIESGO RESIDUAL Y LECCIONES APRENDIDAS (Preguntas 22-25)
    # ============================================================
    PreguntaEstructurada(
        id="P22_DEBILIDAD_PRINCIPAL",
        bloque=BloquePregunta.B6_RIESGO_RESIDUAL,
        numero=22,
        pregunta="¿Cuál es la debilidad más importante del expediente que podría explotar un auditor fiscal?",
        descripcion="Identificar el punto más vulnerable del caso para documentar el riesgo residual.",
        severidad=NivelSeveridad.INFORMATIVO,
        tipo_respuesta=TipoRespuesta.TEXTO_LARGO,
        norma_relacionada="general",
        accion_si_negativo=AccionRespuesta.SOLO_APRENDIZAJE,
        accion_si_incompleto=AccionRespuesta.SOLO_APRENDIZAJE,
        aplica_a_servicios=["todos"],
        obligatoria=True
    ),
    PreguntaEstructurada(
        id="P23_MITIGACION_DEBILIDAD",
        bloque=BloquePregunta.B6_RIESGO_RESIDUAL,
        numero=23,
        pregunta="¿Qué se puede hacer para mitigar esta debilidad antes del cierre del expediente?",
        descripcion="Proponer acciones concretas para reducir el riesgo identificado.",
        severidad=NivelSeveridad.INFORMATIVO,
        tipo_respuesta=TipoRespuesta.TEXTO_LARGO,
        norma_relacionada="general",
        accion_si_negativo=AccionRespuesta.SOLO_APRENDIZAJE,
        accion_si_incompleto=AccionRespuesta.SOLO_APRENDIZAJE,
        aplica_a_servicios=["todos"],
        obligatoria=True
    ),
    PreguntaEstructurada(
        id="P24_LECCION_PREVENCION",
        bloque=BloquePregunta.B6_RIESGO_RESIDUAL,
        numero=24,
        pregunta="¿Qué lección aprendida debería aplicarse en futuros casos similares?",
        descripcion="Capturar conocimiento para mejorar procesos futuros.",
        severidad=NivelSeveridad.INFORMATIVO,
        tipo_respuesta=TipoRespuesta.TEXTO_LARGO,
        norma_relacionada="general",
        accion_si_negativo=AccionRespuesta.SOLO_APRENDIZAJE,
        accion_si_incompleto=AccionRespuesta.SOLO_APRENDIZAJE,
        aplica_a_servicios=["todos"],
        obligatoria=False
    ),
    PreguntaEstructurada(
        id="P25_RIESGO_ACEPTADO",
        bloque=BloquePregunta.B6_RIESGO_RESIDUAL,
        numero=25,
        pregunta="Si se aprueba con debilidades, ¿cuál es el nivel de riesgo residual que se está aceptando conscientemente?",
        descripcion="Documentar formalmente el riesgo residual aceptado y su justificación.",
        severidad=NivelSeveridad.IMPORTANTE,
        tipo_respuesta=TipoRespuesta.ESCALA,
        norma_relacionada="general",
        accion_si_negativo=AccionRespuesta.ALERTA,
        accion_si_incompleto=AccionRespuesta.FORZAR_REVISION,
        opciones=["Ninguno - expediente sólido", "Bajo - riesgo menor documentado", "Medio - riesgo aceptable con justificación", "Alto - requiere aprobación especial"],
        umbral_alerta=2,  # "Medio" o superior
        aplica_a_servicios=["todos"],
        obligatoria=True
    ),
]

# Índice por ID para acceso rápido
PREGUNTAS_POR_ID: Dict[str, PreguntaEstructurada] = {p.id: p for p in PREGUNTAS_ESTRUCTURADAS}

# Índice por bloque
PREGUNTAS_POR_BLOQUE: Dict[BloquePregunta, List[PreguntaEstructurada]] = {}
for p in PREGUNTAS_ESTRUCTURADAS:
    if p.bloque not in PREGUNTAS_POR_BLOQUE:
        PREGUNTAS_POR_BLOQUE[p.bloque] = []
    PREGUNTAS_POR_BLOQUE[p.bloque].append(p)


# ============================================================
# PREGUNTAS INCÓMODAS LEGACY (para compatibilidad)
# ============================================================

PREGUNTAS_INCOMODAS_BASE: Dict[str, List[str]] = {
    "materialidad": [
        "¿Qué pasa si el SAT dice que el proveedor no tenía capacidad para prestar el servicio?",
        "¿Cómo demostrarías que el servicio se prestó si el proveedor niega la operación?",
        "¿La evidencia documental es suficiente sin testigos o registros independientes?",
        "¿El proveedor tiene la infraestructura física/humana para prestar este servicio?",
        "¿Hay rastro digital verificable de la ejecución del servicio?",
        "¿Los entregables son genéricos o claramente vinculados a este proyecto específico?",
        "¿Podría esta evidencia haber sido fabricada posteriormente?",
    ],
    "razon_negocios": [
        "¿Qué beneficio económico habría sin considerar el efecto fiscal?",
        "¿Por qué no se hizo internamente si la empresa tiene capacidad?",
        "¿El precio pagado es congruente con el mercado para este servicio?",
        "¿Cuál era el problema de negocio que este servicio resolvía?",
        "¿Se evaluaron alternativas antes de contratar?",
        "¿Hay evidencia de que la decisión se tomó por razones de negocio, no fiscales?",
        "¿El resultado del servicio se midió o evaluó?",
    ],
    "formal": [
        "¿El CFDI tiene la descripción suficientemente detallada?",
        "¿Los datos del contrato coinciden exactamente con el CFDI?",
        "¿El pago se realizó por los canales y fechas correctos?",
        "¿Hay inconsistencias entre fechas de servicio, factura y pago?",
        "¿El régimen fiscal del proveedor es congruente con el servicio?",
    ],
    "proveedor": [
        "¿Se verificó que el proveedor no esté en lista 69-B antes de contratar?",
        "¿El proveedor tiene historial de operaciones reales?",
        "¿Hay indicios de que sea empresa de fachada o facturera?",
        "¿El domicilio fiscal del proveedor es verificable?",
        "¿Se tiene la opinión de cumplimiento 32-D vigente?",
        "¿El proveedor tiene empleados registrados en IMSS?",
    ],
    "marketing": [
        "¿Se puede demostrar que la campaña se publicó efectivamente?",
        "¿Hay métricas de terceros (Google, Meta) que validen los resultados?",
        "¿El alcance reportado es congruente con el monto pagado?",
        "¿Se pueden correlacionar los resultados con incremento real de ventas?",
        "¿Los creativos existen y pueden mostrarse como evidencia?",
    ],
    "outsourcing": [
        "¿El proveedor tiene registro REPSE vigente?",
        "¿El personal tercerizado reporta al proveedor o al cliente?",
        "¿Hay evidencia de que no es simulación de relación laboral?",
        "¿El servicio es genuinamente especializado o es staffing genérico?",
        "¿El proveedor paga las cuotas IMSS de su personal?",
    ],
}


# ============================================================
# SERVICIO ABOGADO DEL DIABLO
# ============================================================

class DevilsAdvocateService:
    """
    Servicio del Abogado del Diablo.
    Módulo de control interno y aprendizaje organizacional.

    ACCESO: Solo administradores.
    """

    def __init__(self):
        # En producción, esto vendría de la BD
        self._huellas: Dict[str, HuellaRevision] = {}
        self._perfiles: Dict[str, PerfilRiesgoDinamico] = {}
        self._lecciones: Dict[str, LeccionAprendida] = {}
        self._estadisticas_globales: Dict[str, Any] = {}

    # ============================================================
    # REGISTRO DE HUELLAS
    # ============================================================

    def registrar_huella_proyecto(
        self,
        proyecto_id: str,
        empresa_id: str,
        industria: CategoriaIndustria,
        tipo_servicio: str,
        monto: float,
        proveedor_rfc: str,
        admin_id: str
    ) -> HuellaRevision:
        """
        Inicia el registro de huella para un proyecto.
        Debe llamarse cuando el proyecto entra a revisión.
        """
        huella = HuellaRevision(
            proyecto_id=proyecto_id,
            empresa_id=empresa_id,
            industria=industria,
            tipo_servicio=tipo_servicio,
            monto=monto,
            proveedor_rfc=proveedor_rfc,
            fecha_inicio=datetime.now(),
            fecha_cierre=None,
            resultado_final="en_proceso",
            scores_por_fase={},
            cambios_semaforo=[],
            evidencias_clave=[],
            preguntas_respondidas=[],
            riesgos_residuales=[],
            created_by=admin_id
        )

        self._huellas[proyecto_id] = huella
        logger.info(f"[ABOGADO_DIABLO] Huella iniciada para proyecto {proyecto_id}")

        return huella

    def registrar_cambio_semaforo(
        self,
        proyecto_id: str,
        fase: FaseProyecto,
        color_anterior: str,
        color_nuevo: str,
        score_anterior: float,
        score_nuevo: float,
        agente_responsable: str,
        evidencia_que_cambio: List[str],
        justificacion: str,
        version_entregable: str
    ) -> Optional[CambioSemaforo]:
        """
        Registra un cambio de color en el semáforo.
        Esto es clave para entender qué evidencia hace la diferencia.
        """
        if proyecto_id not in self._huellas:
            logger.warning(f"[ABOGADO_DIABLO] Proyecto {proyecto_id} no tiene huella registrada")
            return None

        cambio = CambioSemaforo(
            fase=fase,
            fecha=datetime.now(),
            color_anterior=color_anterior,
            color_nuevo=color_nuevo,
            score_anterior=score_anterior,
            score_nuevo=score_nuevo,
            agente_responsable=agente_responsable,
            evidencia_que_cambio=evidencia_que_cambio,
            justificacion=justificacion,
            version_entregable=version_entregable
        )

        self._huellas[proyecto_id].cambios_semaforo.append(cambio)

        # Si pasó de amarillo/rojo a verde, marcar las evidencias como clave
        if color_nuevo == "verde" and color_anterior in ["amarillo", "rojo"]:
            for ev in evidencia_que_cambio:
                self._registrar_evidencia_clave(
                    proyecto_id=proyecto_id,
                    tipo_evidencia=ev,
                    descripcion=f"Cambió de {color_anterior} a verde en {fase.value}",
                    impacto=f"{color_anterior}_a_verde"
                )

        logger.info(f"[ABOGADO_DIABLO] Cambio {color_anterior}->{color_nuevo} en {proyecto_id}/{fase.value}")

        return cambio

    def _registrar_evidencia_clave(
        self,
        proyecto_id: str,
        tipo_evidencia: str,
        descripcion: str,
        impacto: str,
        norma_acreditada: str = "general"
    ):
        """Registra una evidencia como clave para el caso"""
        if proyecto_id not in self._huellas:
            return

        evidencia = EvidenciaClave(
            tipo_evidencia=tipo_evidencia,
            descripcion=descripcion,
            norma_acreditada=norma_acreditada,
            impacto=impacto
        )

        self._huellas[proyecto_id].evidencias_clave.append(evidencia)

    def registrar_scores_fase(
        self,
        proyecto_id: str,
        fase: FaseProyecto,
        score_formal: float,
        score_materialidad: float,
        score_razon: float,
        score_total: float
    ):
        """Registra los scores de una fase específica"""
        if proyecto_id not in self._huellas:
            return

        self._huellas[proyecto_id].scores_por_fase[fase.value] = {
            "formal": score_formal,
            "materialidad": score_materialidad,
            "razon_negocios": score_razon,
            "total": score_total,
            "fecha": datetime.now().isoformat()
        }

    # ============================================================
    # PREGUNTAS ESTRUCTURADAS (25 PREGUNTAS CON SEVERIDAD)
    # ============================================================

    def obtener_preguntas_estructuradas(
        self,
        bloque: Optional[BloquePregunta] = None,
        solo_obligatorias: bool = False,
        solo_criticas: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Obtiene las 25 preguntas estructuradas con sus metadatos.

        Args:
            bloque: Filtrar por bloque específico
            solo_obligatorias: Solo preguntas marcadas como obligatorias
            solo_criticas: Solo preguntas con severidad CRITICO

        Returns:
            Lista de preguntas con todos sus metadatos
        """
        preguntas = PREGUNTAS_ESTRUCTURADAS

        if bloque:
            preguntas = [p for p in preguntas if p.bloque == bloque]

        if solo_obligatorias:
            preguntas = [p for p in preguntas if p.obligatoria]

        if solo_criticas:
            preguntas = [p for p in preguntas if p.severidad == NivelSeveridad.CRITICO]

        return [
            {
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
                "umbral_alerta": p.umbral_alerta
            }
            for p in preguntas
        ]

    def evaluar_respuesta_estructurada(
        self,
        pregunta_id: str,
        respuesta: Any,
        indice_opcion: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Evalúa una respuesta y determina la acción a tomar.

        Args:
            pregunta_id: ID de la pregunta (P01_DESCRIPCION_SERVICIO, etc.)
            respuesta: La respuesta proporcionada
            indice_opcion: Si es selección/escala, el índice de la opción elegida

        Returns:
            Evaluación con acción recomendada y alertas
        """
        if pregunta_id not in PREGUNTAS_POR_ID:
            return {
                "error": f"Pregunta {pregunta_id} no encontrada",
                "accion": AccionRespuesta.SOLO_APRENDIZAJE.value
            }

        pregunta = PREGUNTAS_POR_ID[pregunta_id]
        resultado = {
            "pregunta_id": pregunta_id,
            "severidad": pregunta.severidad.value,
            "respuesta_recibida": respuesta,
            "accion": AccionRespuesta.SOLO_APRENDIZAJE.value,
            "alertas": [],
            "requiere_revision_adicional": False,
            "bandera_roja": False
        }

        # Evaluar respuestas vacías o incompletas
        if not respuesta or (isinstance(respuesta, str) and len(respuesta.strip()) < 10):
            resultado["accion"] = pregunta.accion_si_incompleto.value
            resultado["alertas"].append("Respuesta incompleta o vacía")

            if pregunta.accion_si_incompleto == AccionRespuesta.FORZAR_REVISION:
                resultado["requiere_revision_adicional"] = True
            elif pregunta.accion_si_incompleto == AccionRespuesta.BANDERA_ROJA:
                resultado["bandera_roja"] = True
                resultado["requiere_revision_adicional"] = True

            return resultado

        # Evaluar respuestas de tipo escala/selección
        if pregunta.tipo_respuesta in [TipoRespuesta.ESCALA, TipoRespuesta.SELECCION_SIMPLE] and indice_opcion is not None:
            # Verificar umbrales
            if pregunta.umbral_critico is not None and indice_opcion >= pregunta.umbral_critico:
                resultado["accion"] = AccionRespuesta.BANDERA_ROJA.value
                resultado["bandera_roja"] = True
                resultado["requiere_revision_adicional"] = True
                resultado["alertas"].append(f"Respuesta por debajo del umbral crítico: {pregunta.opciones[indice_opcion]}")

            elif pregunta.umbral_alerta is not None and indice_opcion >= pregunta.umbral_alerta:
                resultado["accion"] = AccionRespuesta.ALERTA.value
                resultado["alertas"].append(f"Respuesta en zona de alerta: {pregunta.opciones[indice_opcion]}")

            # Evaluar opciones negativas específicas
            elif pregunta.opciones and indice_opcion == len(pregunta.opciones) - 1:
                # Última opción generalmente es la más negativa
                resultado["accion"] = pregunta.accion_si_negativo.value
                if pregunta.accion_si_negativo == AccionRespuesta.BANDERA_ROJA:
                    resultado["bandera_roja"] = True
                    resultado["requiere_revision_adicional"] = True
                elif pregunta.accion_si_negativo == AccionRespuesta.FORZAR_REVISION:
                    resultado["requiere_revision_adicional"] = True

        return resultado

    def generar_resumen_evaluacion(
        self,
        respuestas: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Genera un resumen consolidado de todas las respuestas.

        Args:
            respuestas: Diccionario {pregunta_id: {respuesta, indice_opcion}}

        Returns:
            Resumen con score, banderas rojas, y recomendaciones
        """
        evaluaciones = []
        banderas_rojas = []
        alertas = []
        requieren_revision = []
        score_por_bloque = {}

        for pregunta_id, datos in respuestas.items():
            evaluacion = self.evaluar_respuesta_estructurada(
                pregunta_id,
                datos.get("respuesta"),
                datos.get("indice_opcion")
            )
            evaluaciones.append(evaluacion)

            if evaluacion.get("bandera_roja"):
                banderas_rojas.append({
                    "pregunta_id": pregunta_id,
                    "pregunta": PREGUNTAS_POR_ID.get(pregunta_id, {}).pregunta if pregunta_id in PREGUNTAS_POR_ID else pregunta_id,
                    "alertas": evaluacion.get("alertas", [])
                })

            if evaluacion.get("alertas"):
                alertas.extend(evaluacion["alertas"])

            if evaluacion.get("requiere_revision_adicional"):
                requieren_revision.append(pregunta_id)

        # Calcular score por bloque
        for bloque in BloquePregunta:
            preguntas_bloque = [p.id for p in PREGUNTAS_POR_BLOQUE.get(bloque, [])]
            respondidas = [r for r in evaluaciones if r["pregunta_id"] in preguntas_bloque]

            if respondidas:
                score = 100
                for r in respondidas:
                    if r.get("bandera_roja"):
                        score -= 30
                    elif r.get("requiere_revision_adicional"):
                        score -= 15
                    elif r.get("alertas"):
                        score -= 5
                score_por_bloque[bloque.value] = max(0, score)

        # Score total ponderado
        pesos = {
            BloquePregunta.B1_HECHOS_OBJETO.value: 0.15,
            BloquePregunta.B2_MATERIALIDAD.value: 0.25,
            BloquePregunta.B3_RAZON_NEGOCIOS.value: 0.20,
            BloquePregunta.B4_PROVEEDOR_EFOS.value: 0.20,
            BloquePregunta.B5_FORMAL_FISCAL.value: 0.15,
            BloquePregunta.B6_RIESGO_RESIDUAL.value: 0.05,
        }

        score_total = sum(
            score_por_bloque.get(bloque, 100) * peso
            for bloque, peso in pesos.items()
        )

        # Determinar semáforo
        if banderas_rojas or score_total < 50:
            semaforo = "rojo"
        elif score_total < 80 or len(alertas) > 3:
            semaforo = "amarillo"
        else:
            semaforo = "verde"

        return {
            "score_total": round(score_total, 2),
            "score_por_bloque": score_por_bloque,
            "semaforo": semaforo,
            "banderas_rojas": banderas_rojas,
            "total_banderas_rojas": len(banderas_rojas),
            "alertas": list(set(alertas)),
            "total_alertas": len(alertas),
            "requieren_revision": requieren_revision,
            "preguntas_respondidas": len(respuestas),
            "preguntas_totales": len(PREGUNTAS_ESTRUCTURADAS),
            "completitud": round(len(respuestas) / len(PREGUNTAS_ESTRUCTURADAS) * 100, 1),
            "recomendacion": self._generar_recomendacion(semaforo, banderas_rojas, alertas)
        }

    def _generar_recomendacion(
        self,
        semaforo: str,
        banderas_rojas: List[Dict],
        alertas: List[str]
    ) -> str:
        """Genera recomendación textual basada en la evaluación"""
        if semaforo == "rojo":
            if banderas_rojas:
                return f"ALTO RIESGO: Se detectaron {len(banderas_rojas)} bandera(s) roja(s). El expediente NO debe aprobarse sin resolver los problemas críticos identificados."
            return "ALTO RIESGO: El score general es insuficiente. Revisar evidencia en todos los bloques."

        if semaforo == "amarillo":
            return f"PRECAUCIÓN: Se detectaron {len(alertas)} alerta(s). Evaluar si los riesgos son aceptables y documentar justificación."

        return "VIABLE: El expediente cumple con los estándares mínimos. Proceder con revisión final."

    def obtener_bloques_preguntas(self) -> List[Dict[str, Any]]:
        """Obtiene la estructura de bloques con su descripción"""
        return [
            {
                "id": BloquePregunta.B1_HECHOS_OBJETO.value,
                "nombre": "Hechos y Objeto del Servicio",
                "descripcion": "Verificar que el servicio está claramente definido y documentado",
                "preguntas_count": len(PREGUNTAS_POR_BLOQUE.get(BloquePregunta.B1_HECHOS_OBJETO, [])),
                "peso_score": 0.15
            },
            {
                "id": BloquePregunta.B2_MATERIALIDAD.value,
                "nombre": "Materialidad / CFF 69-B",
                "descripcion": "Evidencia dura de que el servicio se prestó realmente",
                "preguntas_count": len(PREGUNTAS_POR_BLOQUE.get(BloquePregunta.B2_MATERIALIDAD, [])),
                "peso_score": 0.25
            },
            {
                "id": BloquePregunta.B3_RAZON_NEGOCIOS.value,
                "nombre": "Razón de Negocios / CFF 5-A",
                "descripcion": "Justificación económica más allá del beneficio fiscal",
                "preguntas_count": len(PREGUNTAS_POR_BLOQUE.get(BloquePregunta.B3_RAZON_NEGOCIOS, [])),
                "peso_score": 0.20
            },
            {
                "id": BloquePregunta.B4_PROVEEDOR_EFOS.value,
                "nombre": "Proveedor y EFOS",
                "descripcion": "Verificación de legitimidad del proveedor",
                "preguntas_count": len(PREGUNTAS_POR_BLOQUE.get(BloquePregunta.B4_PROVEEDOR_EFOS, [])),
                "peso_score": 0.20
            },
            {
                "id": BloquePregunta.B5_FORMAL_FISCAL.value,
                "nombre": "Requisitos Fiscales Formales",
                "descripcion": "Cumplimiento de requisitos formales de deducibilidad",
                "preguntas_count": len(PREGUNTAS_POR_BLOQUE.get(BloquePregunta.B5_FORMAL_FISCAL, [])),
                "peso_score": 0.15
            },
            {
                "id": BloquePregunta.B6_RIESGO_RESIDUAL.value,
                "nombre": "Riesgo Residual y Lecciones",
                "descripcion": "Documentación de debilidades y aprendizaje organizacional",
                "preguntas_count": len(PREGUNTAS_POR_BLOQUE.get(BloquePregunta.B6_RIESGO_RESIDUAL, [])),
                "peso_score": 0.05
            },
        ]

    # ============================================================
    # PREGUNTAS INCÓMODAS (LEGACY)
    # ============================================================

    def obtener_preguntas_incomodas(
        self,
        tipo_servicio: str,
        industria: Optional[CategoriaIndustria] = None
    ) -> List[Dict[str, Any]]:
        """
        Obtiene las preguntas incómodas aplicables a un caso.
        Combina preguntas base con las específicas del tipo de servicio.
        """
        preguntas = []

        # Preguntas base siempre aplicables
        for categoria in ["materialidad", "razon_negocios", "formal", "proveedor"]:
            for p in PREGUNTAS_INCOMODAS_BASE.get(categoria, []):
                preguntas.append({
                    "categoria": categoria,
                    "pregunta": p,
                    "tipo_servicio": "todos"
                })

        # Preguntas específicas por tipo de servicio
        if tipo_servicio.lower() == "marketing":
            for p in PREGUNTAS_INCOMODAS_BASE.get("marketing", []):
                preguntas.append({
                    "categoria": "marketing_especifica",
                    "pregunta": p,
                    "tipo_servicio": "marketing"
                })

        if tipo_servicio.lower() == "outsourcing":
            for p in PREGUNTAS_INCOMODAS_BASE.get("outsourcing", []):
                preguntas.append({
                    "categoria": "outsourcing_especifica",
                    "pregunta": p,
                    "tipo_servicio": "outsourcing"
                })

        # Agregar preguntas aprendidas de lecciones anteriores
        for leccion in self._lecciones.values():
            if leccion.tipo_servicio == tipo_servicio or leccion.tipo_servicio == "todos":
                if industria and leccion.industria == industria:
                    preguntas.append({
                        "categoria": leccion.categoria,
                        "pregunta": f"[Aprendida] {leccion.problema_detectado}",
                        "tipo_servicio": tipo_servicio,
                        "fuente": "leccion_aprendida",
                        "leccion_id": leccion.id
                    })

        return preguntas

    def registrar_respuesta_pregunta(
        self,
        proyecto_id: str,
        categoria: str,
        pregunta: str,
        respuesta: str,
        evidencia_soporte: List[str],
        norma_relacionada: str
    ) -> Optional[PreguntaIncomoda]:
        """
        Registra la respuesta a una pregunta incómoda.
        Esto construye la biblioteca de argumentos de defensa.
        """
        if proyecto_id not in self._huellas:
            logger.warning(f"[ABOGADO_DIABLO] Proyecto {proyecto_id} no tiene huella")
            return None

        pregunta_obj = PreguntaIncomoda(
            categoria=categoria,
            pregunta=pregunta,
            respuesta=respuesta,
            evidencia_soporte=evidencia_soporte,
            norma_relacionada=norma_relacionada
        )

        self._huellas[proyecto_id].preguntas_respondidas.append(pregunta_obj)

        logger.info(f"[ABOGADO_DIABLO] Pregunta respondida en {proyecto_id}: {pregunta[:50]}...")

        return pregunta_obj

    # ============================================================
    # RIESGOS RESIDUALES
    # ============================================================

    def registrar_riesgo_residual(
        self,
        proyecto_id: str,
        descripcion: str,
        nivel: NivelRiesgoResidual,
        justificacion: str,
        mitigacion_propuesta: str,
        aprobado_por: str,
        monto_exposicion: float = 0.0
    ) -> Optional[RiesgoResidual]:
        """
        Registra un riesgo aceptado conscientemente.
        Esto es crítico para documentar decisiones con información incompleta.
        """
        if proyecto_id not in self._huellas:
            return None

        riesgo = RiesgoResidual(
            descripcion=descripcion,
            nivel=nivel,
            justificacion=justificacion,
            mitigacion_propuesta=mitigacion_propuesta,
            aprobado_por=aprobado_por,
            fecha_aprobacion=datetime.now(),
            monto_exposicion=monto_exposicion
        )

        self._huellas[proyecto_id].riesgos_residuales.append(riesgo)

        logger.warning(f"[ABOGADO_DIABLO] Riesgo {nivel.value} registrado en {proyecto_id}: {descripcion[:50]}...")

        return riesgo

    # ============================================================
    # CIERRE DE PROYECTO
    # ============================================================

    def cerrar_huella_proyecto(
        self,
        proyecto_id: str,
        resultado: str,  # aprobado, rechazado
        notas_cierre: str = ""
    ) -> Optional[HuellaRevision]:
        """
        Cierra la huella de un proyecto y dispara el aprendizaje.
        """
        if proyecto_id not in self._huellas:
            return None

        huella = self._huellas[proyecto_id]
        huella.fecha_cierre = datetime.now()
        huella.resultado_final = resultado

        # Actualizar perfil de riesgo dinámico
        self._actualizar_perfil_riesgo(huella)

        # Extraer lecciones si hay patrones nuevos
        self._extraer_lecciones(huella)

        logger.info(f"[ABOGADO_DIABLO] Huella cerrada para {proyecto_id}: {resultado}")

        return huella

    # ============================================================
    # PERFILES DE RIESGO DINÁMICO
    # ============================================================

    def _obtener_clave_perfil(
        self,
        industria: CategoriaIndustria,
        tipo_servicio: str,
        monto: float
    ) -> str:
        """Genera la clave única para un perfil de riesgo"""
        if monto < 500000:
            rango = "<500k"
        elif monto < 2000000:
            rango = "500k-2M"
        else:
            rango = ">2M"

        return f"{industria.value}|{tipo_servicio}|{rango}"

    def _actualizar_perfil_riesgo(self, huella: HuellaRevision):
        """
        Actualiza el perfil de riesgo dinámico con la información del proyecto.
        """
        clave = self._obtener_clave_perfil(
            huella.industria,
            huella.tipo_servicio,
            huella.monto
        )

        if clave not in self._perfiles:
            self._perfiles[clave] = PerfilRiesgoDinamico(
                industria=huella.industria,
                tipo_servicio=huella.tipo_servicio,
                rango_monto=clave.split("|")[2],
                total_casos=0,
                casos_aprobados=0,
                casos_rechazados=0,
                score_promedio_aprobados=0,
                evidencias_minimas=[],
                objeciones_frecuentes=[],
                patrones_exito=[],
                alertas=[]
            )

        perfil = self._perfiles[clave]
        perfil.total_casos += 1

        if huella.resultado_final == "aprobado":
            perfil.casos_aprobados += 1

            # Actualizar score promedio
            if huella.scores_por_fase:
                ultimo_score = list(huella.scores_por_fase.values())[-1].get("total", 0)
                perfil.score_promedio_aprobados = (
                    (perfil.score_promedio_aprobados * (perfil.casos_aprobados - 1) + ultimo_score)
                    / perfil.casos_aprobados
                )

            # Extraer evidencias que funcionaron
            for ev in huella.evidencias_clave:
                if ev.tipo_evidencia not in perfil.evidencias_minimas:
                    perfil.evidencias_minimas.append(ev.tipo_evidencia)

        else:
            perfil.casos_rechazados += 1

        perfil.updated_at = datetime.now()

    def obtener_perfil_riesgo(
        self,
        industria: CategoriaIndustria,
        tipo_servicio: str,
        monto: float
    ) -> Optional[PerfilRiesgoDinamico]:
        """
        Obtiene el perfil de riesgo dinámico para una combinación industria/servicio/monto.
        """
        clave = self._obtener_clave_perfil(industria, tipo_servicio, monto)
        return self._perfiles.get(clave)

    def obtener_estandar_prueba(
        self,
        industria: CategoriaIndustria,
        tipo_servicio: str,
        monto: float
    ) -> Dict[str, Any]:
        """
        Genera el estándar de prueba aprendido para un tipo de caso.
        Este es el "mínimo" basado en experiencia real.
        """
        perfil = self.obtener_perfil_riesgo(industria, tipo_servicio, monto)

        if not perfil:
            # Si no hay perfil, devolver estándar base
            return {
                "industria": industria.value,
                "tipo_servicio": tipo_servicio,
                "monto_rango": "sin_datos",
                "evidencias_minimas_sugeridas": [
                    "contrato_detallado",
                    "cfdi_validado",
                    "estado_cuenta_pago",
                    "entregables_especificos"
                ],
                "alertas": ["Sin historial suficiente para este tipo de caso"],
                "fuente": "estandar_base"
            }

        return {
            "industria": industria.value,
            "tipo_servicio": tipo_servicio,
            "monto_rango": perfil.rango_monto,
            "estadisticas": {
                "total_casos": perfil.total_casos,
                "tasa_aprobacion": (perfil.casos_aprobados / perfil.total_casos * 100) if perfil.total_casos > 0 else 0,
                "score_promedio": perfil.score_promedio_aprobados
            },
            "evidencias_minimas_sugeridas": perfil.evidencias_minimas,
            "objeciones_frecuentes": perfil.objeciones_frecuentes,
            "patrones_exito": perfil.patrones_exito,
            "alertas": perfil.alertas,
            "fuente": "aprendizaje_historico",
            "ultima_actualizacion": perfil.updated_at.isoformat()
        }

    # ============================================================
    # LECCIONES APRENDIDAS
    # ============================================================

    def _extraer_lecciones(self, huella: HuellaRevision):
        """
        Extrae lecciones aprendidas de un caso cerrado.
        """
        # Si hubo cambio de rojo/amarillo a verde, hay una lección
        for cambio in huella.cambios_semaforo:
            if cambio.color_nuevo == "verde" and cambio.color_anterior in ["rojo", "amarillo"]:
                leccion_id = f"LECCION_{huella.proyecto_id}_{cambio.fase.value}"

                if leccion_id not in self._lecciones:
                    self._lecciones[leccion_id] = LeccionAprendida(
                        id=leccion_id,
                        titulo=f"Cambio {cambio.color_anterior}→verde en {cambio.fase.value}",
                        descripcion=cambio.justificacion,
                        industria=huella.industria,
                        tipo_servicio=huella.tipo_servicio,
                        categoria="evidencia_efectiva",
                        norma_relacionada="general",
                        contexto=f"Proyecto de {huella.tipo_servicio} en {huella.industria.value}",
                        problema_detectado=f"Score en {cambio.color_anterior}",
                        solucion_aplicada=f"Evidencia: {', '.join(cambio.evidencia_que_cambio)}",
                        aplicable_cuando=[f"Tipo: {huella.tipo_servicio}", f"Industria: {huella.industria.value}"],
                        no_aplicable_cuando=[]
                    )

    def registrar_leccion_manual(
        self,
        titulo: str,
        descripcion: str,
        industria: CategoriaIndustria,
        tipo_servicio: str,
        categoria: str,
        norma_relacionada: str,
        contexto: str,
        problema_detectado: str,
        solucion_aplicada: str,
        aplicable_cuando: List[str],
        admin_id: str
    ) -> LeccionAprendida:
        """
        Registra una lección aprendida manualmente por un administrador.
        """
        import uuid
        leccion_id = f"LECCION_MANUAL_{uuid.uuid4().hex[:8]}"

        leccion = LeccionAprendida(
            id=leccion_id,
            titulo=titulo,
            descripcion=descripcion,
            industria=industria,
            tipo_servicio=tipo_servicio,
            categoria=categoria,
            norma_relacionada=norma_relacionada,
            contexto=contexto,
            problema_detectado=problema_detectado,
            solucion_aplicada=solucion_aplicada,
            aplicable_cuando=aplicable_cuando,
            no_aplicable_cuando=[]
        )

        self._lecciones[leccion_id] = leccion

        logger.info(f"[ABOGADO_DIABLO] Lección manual registrada: {titulo}")

        return leccion

    def obtener_lecciones_aplicables(
        self,
        tipo_servicio: str,
        industria: Optional[CategoriaIndustria] = None
    ) -> List[LeccionAprendida]:
        """
        Obtiene las lecciones aprendidas aplicables a un caso.
        """
        lecciones = []

        for leccion in self._lecciones.values():
            # Filtrar por tipo de servicio
            if leccion.tipo_servicio not in [tipo_servicio, "todos"]:
                continue

            # Filtrar por industria si se especifica
            if industria and leccion.industria != industria and leccion.industria != CategoriaIndustria.OTRO:
                continue

            lecciones.append(leccion)

        # Ordenar por efectividad
        lecciones.sort(key=lambda x: x.veces_exitosa / max(x.veces_aplicada, 1), reverse=True)

        return lecciones

    # ============================================================
    # INCIDENTES SAT
    # ============================================================

    def registrar_incidente_sat(
        self,
        proyecto_id: str,
        descripcion: str,
        tipo_acto: str,
        monto_cuestionado: float,
        fecha_incidente: datetime,
        resultado: Optional[str] = None,
        admin_id: str = ""
    ) -> Dict[str, Any]:
        """
        Registra un incidente posterior con SAT sobre un proyecto aprobado.
        Esto es CRÍTICO para evitar sesgos de confirmación.
        """
        incidente = {
            "proyecto_id": proyecto_id,
            "descripcion": descripcion,
            "tipo_acto": tipo_acto,
            "monto_cuestionado": monto_cuestionado,
            "fecha_incidente": fecha_incidente.isoformat(),
            "resultado": resultado,
            "registrado_por": admin_id,
            "fecha_registro": datetime.now().isoformat()
        }

        # Marcar la huella si existe
        if proyecto_id in self._huellas:
            # Agregar nota de incidente
            self._huellas[proyecto_id].riesgos_residuales.append(
                RiesgoResidual(
                    descripcion=f"INCIDENTE SAT: {descripcion}",
                    nivel=NivelRiesgoResidual.CRITICO,
                    justificacion="Incidente registrado post-aprobación",
                    mitigacion_propuesta="Revisar criterios de aprobación",
                    aprobado_por="SISTEMA",
                    fecha_aprobacion=datetime.now(),
                    monto_exposicion=monto_cuestionado
                )
            )

        logger.warning(f"[ABOGADO_DIABLO] INCIDENTE SAT registrado para {proyecto_id}: {tipo_acto}")

        return incidente

    # ============================================================
    # REPORTES PARA ADMINISTRADORES
    # ============================================================

    def generar_reporte_mejores_practicas(
        self,
        industria: Optional[CategoriaIndustria] = None,
        tipo_servicio: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Genera un reporte de mejores prácticas basado en el aprendizaje.
        Solo para administradores.
        """
        perfiles_filtrados = []

        for perfil in self._perfiles.values():
            if industria and perfil.industria != industria:
                continue
            if tipo_servicio and perfil.tipo_servicio != tipo_servicio:
                continue
            perfiles_filtrados.append(perfil)

        if not perfiles_filtrados:
            return {
                "mensaje": "No hay suficientes datos para generar reporte",
                "filtros": {
                    "industria": industria.value if industria else "todas",
                    "tipo_servicio": tipo_servicio or "todos"
                }
            }

        # Agregar estadísticas
        total_casos = sum(p.total_casos for p in perfiles_filtrados)
        total_aprobados = sum(p.casos_aprobados for p in perfiles_filtrados)
        total_rechazados = sum(p.casos_rechazados for p in perfiles_filtrados)

        # Extraer evidencias más comunes
        evidencias_frecuentes: Dict[str, int] = {}
        for perfil in perfiles_filtrados:
            for ev in perfil.evidencias_minimas:
                evidencias_frecuentes[ev] = evidencias_frecuentes.get(ev, 0) + 1

        evidencias_ordenadas = sorted(evidencias_frecuentes.items(), key=lambda x: x[1], reverse=True)

        return {
            "titulo": "Reporte de Mejores Prácticas",
            "generado": datetime.now().isoformat(),
            "filtros": {
                "industria": industria.value if industria else "todas",
                "tipo_servicio": tipo_servicio or "todos"
            },
            "estadisticas": {
                "total_casos_analizados": total_casos,
                "casos_aprobados": total_aprobados,
                "casos_rechazados": total_rechazados,
                "tasa_aprobacion": (total_aprobados / total_casos * 100) if total_casos > 0 else 0
            },
            "evidencias_mas_efectivas": [
                {"tipo": ev, "frecuencia": freq}
                for ev, freq in evidencias_ordenadas[:10]
            ],
            "perfiles_detallados": [
                {
                    "industria": p.industria.value,
                    "tipo_servicio": p.tipo_servicio,
                    "rango_monto": p.rango_monto,
                    "casos": p.total_casos,
                    "tasa_aprobacion": (p.casos_aprobados / p.total_casos * 100) if p.total_casos > 0 else 0,
                    "evidencias_minimas": p.evidencias_minimas
                }
                for p in perfiles_filtrados
            ],
            "lecciones_aplicables": [
                {
                    "id": l.id,
                    "titulo": l.titulo,
                    "solucion": l.solucion_aplicada,
                    "efectividad": (l.veces_exitosa / max(l.veces_aplicada, 1)) * 100
                }
                for l in self.obtener_lecciones_aplicables(
                    tipo_servicio or "todos",
                    industria
                )[:5]
            ],
            "advertencia": "Este reporte es de uso interno exclusivo. No compartir con terceros."
        }

    def obtener_estadisticas_globales(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas globales del módulo Abogado del Diablo.
        """
        total_huellas = len(self._huellas)
        huellas_cerradas = sum(1 for h in self._huellas.values() if h.fecha_cierre)
        huellas_aprobadas = sum(1 for h in self._huellas.values() if h.resultado_final == "aprobado")
        huellas_rechazadas = sum(1 for h in self._huellas.values() if h.resultado_final == "rechazado")

        total_preguntas = sum(len(h.preguntas_respondidas) for h in self._huellas.values())
        total_riesgos = sum(len(h.riesgos_residuales) for h in self._huellas.values())
        riesgos_criticos = sum(
            1 for h in self._huellas.values()
            for r in h.riesgos_residuales
            if r.nivel in [NivelRiesgoResidual.ALTO, NivelRiesgoResidual.CRITICO]
        )

        return {
            "resumen": {
                "total_proyectos_monitoreados": total_huellas,
                "proyectos_cerrados": huellas_cerradas,
                "proyectos_aprobados": huellas_aprobadas,
                "proyectos_rechazados": huellas_rechazadas,
                "tasa_aprobacion": (huellas_aprobadas / max(huellas_cerradas, 1)) * 100
            },
            "cuestionamientos": {
                "preguntas_respondidas": total_preguntas,
                "riesgos_documentados": total_riesgos,
                "riesgos_criticos": riesgos_criticos
            },
            "aprendizaje": {
                "perfiles_generados": len(self._perfiles),
                "lecciones_registradas": len(self._lecciones)
            },
            "ultima_actualizacion": datetime.now().isoformat()
        }


# ============================================================
# INSTANCIA GLOBAL
# ============================================================

devils_advocate_service = DevilsAdvocateService()


def get_devils_advocate_service() -> DevilsAdvocateService:
    """Obtiene la instancia del servicio Abogado del Diablo"""
    return devils_advocate_service
