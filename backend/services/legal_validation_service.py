"""
============================================================
REVISAR.IA - Servicio de Validación Legal
============================================================
Framework de validación basado en:
- LISR 27 (Deducciones)
- CFF 69-B (Materialidad - EFOS/EDOS)
- CFF 5-A (Razón de negocios)
- LIVA 5 (Acreditamiento IVA)
- Anexo 20 (Estructura CFDI)

Tres capas de validación:
1. Formal-fiscal (CFDI, LISR 27, LIVA 5, CFF 28-29)
2. Materialidad (CFF 69-B + pruebas de existencia)
3. Razón de negocios (CFF 5-A + documentación interna)
============================================================
"""

from enum import Enum
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


# ============================================================
# ENUMS Y TIPOS
# ============================================================

class NivelRiesgo(str, Enum):
    """Semáforo de riesgo fiscal"""
    VERDE = "verde"      # Cumple formales + materialidad + razón de negocios
    AMARILLO = "amarillo"  # Formales OK, débil en materialidad o razón
    ROJO = "rojo"        # Proveedor en riesgo o sin evidencia mínima


class CapaValidacion(str, Enum):
    """Las tres capas de validación"""
    FORMAL_FISCAL = "formal_fiscal"
    MATERIALIDAD = "materialidad"
    RAZON_NEGOCIOS = "razon_negocios"


class TipoEvidencia(str, Enum):
    """Tipos de evidencia documental"""
    CONTRATO = "contrato"
    CFDI = "cfdi"
    ESTADO_CUENTA = "estado_cuenta"
    POLIZA_CONTABLE = "poliza_contable"
    ENTREGABLE = "entregable"
    ORDEN_SERVICIO = "orden_servicio"
    ACTA = "acta"
    CORREO = "correo"
    REPORTE = "reporte"
    CONSULTA_SAT = "consulta_sat"
    OPINION_32D = "opinion_32d"
    LISTA_69B = "lista_69b"
    ESTUDIO_PRECIOS_TRANSFERENCIA = "estudio_pt"
    MEMORANDO_INTERNO = "memorando"
    MINUTA = "minuta"
    ANALISIS_COSTO_BENEFICIO = "analisis_cb"


class TipoServicio(str, Enum):
    """Tipos de servicios para reglas específicas"""
    CONSULTORIA = "consultoria"
    TECNOLOGIA = "tecnologia"
    MARKETING = "marketing"
    LEGAL = "legal"
    CONTABLE = "contable"
    OUTSOURCING = "outsourcing"
    CAPACITACION = "capacitacion"
    TRANSPORTE = "transporte"
    MANTENIMIENTO = "mantenimiento"
    HONORARIOS = "honorarios"
    ARRENDAMIENTO = "arrendamiento"
    SERVICIOS_GENERALES = "servicios_generales"


class NivelRiesgoInherente(str, Enum):
    """Nivel de riesgo inherente por tipo de servicio según criterios SAT/TFJA"""
    BAJO = "bajo"
    MEDIO = "medio"
    ALTO = "alto"
    MUY_ALTO = "muy_alto"


class TipoActoAutoridad(str, Enum):
    """Tipos de actos de autoridad que activan modo defensa"""
    REVISION_ELECTRONICA = "revision_electronica"
    VISITA_DOMICILIARIA = "visita_domiciliaria"
    REVISION_GABINETE = "revision_gabinete"
    NEGATIVA_DEVOLUCION = "negativa_devolucion"
    OFICIO_OBSERVACIONES = "oficio_observaciones"
    CARTA_INVITACION = "carta_invitacion"
    RESOLUCION_PROVISIONAL = "resolucion_provisional"


class CategoriaGasto(str, Enum):
    """Categorías de gastos según LISR 27 con reglas específicas"""
    SERVICIOS_RECURRENTES = "servicios_recurrentes"  # mantenimiento, limpieza, seguridad
    CONSULTORIA_ESTRATEGICA = "consultoria_estrategica"  # coaching, dirección
    PUBLICIDAD_PROPAGANDA = "publicidad_propaganda"  # marketing, campañas
    PARTES_RELACIONADAS = "partes_relacionadas"  # intragrupo, extranjero
    VIATICOS_REPRESENTACION = "viaticos_representacion"  # viajes, gastos de representación
    TERCERIZACION = "tercerizacion"  # outsourcing, staffing


# ============================================================
# MODELOS DE DATOS
# ============================================================

@dataclass
class EvidenciaRequerida:
    """Evidencia requerida para una regla"""
    tipo: TipoEvidencia
    descripcion: str
    obligatoria: bool = True
    alternativas: List[TipoEvidencia] = field(default_factory=list)


@dataclass
class ElementoMatrizNHP:
    """Elemento de la Matriz Norma-Hecho-Prueba"""
    norma: str
    fundamento_legal: str
    hecho_a_acreditar: str
    pruebas_primarias: List[str]
    pruebas_secundarias: List[str] = field(default_factory=list)
    riesgo_si_falta: str = "ALTO"


@dataclass
class MatrizNormaHechoPrueba:
    """Matriz completa Norma-Hecho-Prueba para un tipo de servicio"""
    tipo_servicio: TipoServicio
    nivel_riesgo_inherente: NivelRiesgoInherente
    descripcion_riesgo: str
    elementos: List[ElementoMatrizNHP]
    consideraciones_especiales: List[str] = field(default_factory=list)


@dataclass
class PlantillaArgumentacion:
    """Plantilla de argumentación para Defense File"""
    seccion: str
    titulo: str
    template: str
    variables_requeridas: List[str]
    ejemplo: str = ""


@dataclass
class ExpedienteDefensa:
    """Estructura del expediente en modo defensa"""
    acto_autoridad: TipoActoAutoridad
    numero_oficio: str
    fecha_notificacion: datetime
    autoridad_emisora: str
    plazo_respuesta: int  # días hábiles
    fecha_limite: datetime
    conceptos_cuestionados: List[str]
    monto_total_cuestionado: float
    operaciones_impugnadas: List[Dict[str, Any]]
    narrativa_hechos: str
    argumentacion_juridica: str
    conclusion_operativa: str
    documentos_listos: List[str]
    documentos_faltantes: List[str]


@dataclass
class ReglaValidacion:
    """Regla de validación legal"""
    id: str
    nombre: str
    fundamento_legal: str
    capa: CapaValidacion
    descripcion: str
    condicion_logica: str
    evidencias_minimas: List[EvidenciaRequerida]
    aplica_a_servicios: List[TipoServicio] = field(default_factory=list)
    peso_validacion: float = 1.0  # Para calcular score


@dataclass
class ResultadoValidacion:
    """Resultado de validar una regla"""
    regla_id: str
    regla_nombre: str
    cumple: bool
    nivel_cumplimiento: float  # 0.0 a 1.0
    evidencias_presentes: List[str]
    evidencias_faltantes: List[str]
    observaciones: str
    recomendaciones: List[str]


@dataclass
class EvaluacionCompleta:
    """Evaluación completa de una operación"""
    operacion_id: str
    proveedor_rfc: str
    monto: float
    fecha_evaluacion: datetime
    nivel_riesgo: NivelRiesgo
    score_total: float  # 0-100
    score_formal: float
    score_materialidad: float
    score_razon_negocios: float
    resultados_por_regla: List[ResultadoValidacion]
    resumen: str
    acciones_correctivas: List[str]


# ============================================================
# MATRICES NORMA-HECHO-PRUEBA POR TIPO DE SERVICIO ALTO RIESGO
# ============================================================

MATRIZ_MARKETING = MatrizNormaHechoPrueba(
    tipo_servicio=TipoServicio.MARKETING,
    nivel_riesgo_inherente=NivelRiesgoInherente.ALTO,
    descripcion_riesgo="Servicios intangibles con alta dificultad de demostrar materialidad. SAT/TFJA son especialmente estrictos.",
    elementos=[
        ElementoMatrizNHP(
            norma="Deducción autorizada",
            fundamento_legal="LISR Art. 27 Fracción I - Estricta Indispensabilidad",
            hecho_a_acreditar="El servicio de marketing tiene vínculo directo con la actividad que genera ingresos (no es gasto personal o suntuario)",
            pruebas_primarias=[
                "Contrato/SOW con objetivo de campaña y KPIs definidos (ventas, leads, tráfico, posicionamiento)",
                "Brief de marketing aprobado internamente con firmas",
                "Minutas de kick-off y sesiones de seguimiento con asistentes identificados"
            ],
            pruebas_secundarias=[
                "Correos de aprobación de creativos",
                "Presentaciones a comité de marketing/dirección"
            ],
            riesgo_si_falta="ALTO - Sin vínculo demostrable, SAT puede rechazar deducción por suntuaria"
        ),
        ElementoMatrizNHP(
            norma="Gasto efectivamente erogado",
            fundamento_legal="LISR Art. 27 Fracción III + CFF Art. 28-29",
            hecho_a_acreditar="El pago se realizó al proveedor y se registró contablemente correctamente",
            pruebas_primarias=[
                "CFDI de servicios de marketing con descripción congruente y objetoImp gravado",
                "Estados de cuenta bancarios con pago rastreable al beneficiario",
                "Póliza contable con referencia a CFDI y proyecto/campaña específica"
            ],
            pruebas_secundarias=[
                "Complemento de pago si aplica",
                "Conciliación bancaria del período"
            ],
            riesgo_si_falta="CRÍTICO - Sin soporte de pago, no hay deducción"
        ),
        ElementoMatrizNHP(
            norma="Materialidad del servicio",
            fundamento_legal="CFF Art. 69-B - Criterios TFJA/SCJN sobre materialidad",
            hecho_a_acreditar="La campaña de marketing se ejecutó efectivamente y produjo resultados tangibles",
            pruebas_primarias=[
                "Capturas de anuncios publicados con fechas y URLs verificables",
                "Reportes de plataformas digitales (Google Ads, Meta, LinkedIn) con métricas",
                "Reportes de resultados: impresiones, clics, leads, conversiones con sellado de tiempo"
            ],
            pruebas_secundarias=[
                "Screenshots de redes sociales con publicaciones",
                "Analytics de tráfico web correlacionado con campaña",
                "Creatividades entregadas (diseños, videos, copys)",
                "Evidencia de optimizaciones realizadas durante campaña"
            ],
            riesgo_si_falta="MUY ALTO - Marketing sin evidencia de ejecución = operación simulada potencial"
        ),
        ElementoMatrizNHP(
            norma="Razón de negocios",
            fundamento_legal="CFF Art. 5-A",
            hecho_a_acreditar="La campaña tiene objetivo económico claro y razonable frente al costo, más allá del beneficio fiscal",
            pruebas_primarias=[
                "Memo interno/presentación a comité donde se aprueba campaña con objetivo y presupuesto",
                "Análisis ROI esperado vs real (aunque sea cualitativo)",
                "Matriz de escenarios 'sin campaña / con campaña' construida previamente"
            ],
            pruebas_secundarias=[
                "Acta de consejo o comité aprobando presupuesto",
                "Comparativo con campañas anteriores",
                "Benchmarks de industria para justificar inversión"
            ],
            riesgo_si_falta="ALTO - Sin razón de negocios, SAT puede invocar Art. 5-A"
        ),
        ElementoMatrizNHP(
            norma="IVA acreditable",
            fundamento_legal="LIVA Art. 5",
            hecho_a_acreditar="IVA trasladado, efectivamente pagado y relacionado con actividades gravadas",
            pruebas_primarias=[
                "CFDI con IVA trasladado expresamente desglosado",
                "Estado de cuenta o póliza demostrando pago efectivo del IVA",
                "Evidencia de que el servicio se vincula a actividades gravadas (no exentas)"
            ],
            pruebas_secundarias=[
                "Declaración mensual de IVA donde se acredita"
            ],
            riesgo_si_falta="MEDIO - IVA no acreditable si faltan requisitos"
        )
    ],
    consideraciones_especiales=[
        "Marketing digital deja más rastro probatorio que marketing tradicional - aprovecharlo",
        "Influencer marketing: exigir contratos específicos con entregables y métricas",
        "Evitar facturas globales 'servicios de marketing' - detallar por campaña/pieza",
        "SAT cuestiona frecuentemente montos elevados sin correlación con incremento de ventas"
    ]
)

MATRIZ_CONSULTORIA = MatrizNormaHechoPrueba(
    tipo_servicio=TipoServicio.CONSULTORIA,
    nivel_riesgo_inherente=NivelRiesgoInherente.MEDIO,
    descripcion_riesgo="Servicios intangibles donde la materialidad depende de entregables documentales. Riesgo aumenta si consultoría no genera cambios visibles.",
    elementos=[
        ElementoMatrizNHP(
            norma="Deducción autorizada",
            fundamento_legal="LISR Art. 27 Fracción I - Estricta Indispensabilidad",
            hecho_a_acreditar="La consultoría resuelve un problema o mejora directamente un proceso que impacta la operación o cumplimiento",
            pruebas_primarias=[
                "Términos de referencia / SOW con problema definido, alcance, entregables e hitos",
                "Aprobación interna del proyecto (correo de director, minuta de comité)",
                "Documento que evidencie el problema/necesidad que originó la consultoría"
            ],
            pruebas_secundarias=[
                "Cotizaciones comparativas de otros consultores",
                "Análisis de capacidades internas que justifique contratar externo"
            ],
            riesgo_si_falta="ALTO - Sin justificación, SAT puede cuestionar necesidad del gasto"
        ),
        ElementoMatrizNHP(
            norma="Materialidad del servicio",
            fundamento_legal="CFF Art. 69-B - Materialidad",
            hecho_a_acreditar="La consultoría se prestó efectivamente y generó entregables tangibles",
            pruebas_primarias=[
                "Informes de consultoría entregados (diagnósticos, matrices, presentaciones)",
                "Minutas de sesiones de trabajo con fechas, asistentes y temas tratados",
                "Modelos, herramientas o documentos de trabajo producidos"
            ],
            pruebas_secundarias=[
                "Grabaciones de sesiones (si existen y están autorizadas)",
                "Correos de coordinación con el consultor",
                "Listas de asistencia a talleres o sesiones",
                "Evidencia de implementación de recomendaciones"
            ],
            riesgo_si_falta="ALTO - Consultoría sin entregables = servicio inexistente potencial"
        ),
        ElementoMatrizNHP(
            norma="Razón de negocios",
            fundamento_legal="CFF Art. 5-A",
            hecho_a_acreditar="La consultoría tiene justificación económica/cualitativa real",
            pruebas_primarias=[
                "Análisis costo-beneficio (incluso cualitativo: evitar multa, cierre, incumplimiento)",
                "Vinculación a objetivos estratégicos documentados (planes anuales, OKR)",
                "Memo ejecutivo explicando por qué se contrata consultoría externa"
            ],
            pruebas_secundarias=[
                "Evidencia de decisiones tomadas derivadas de la consultoría",
                "Cambios implementados post-consultoría"
            ],
            riesgo_si_falta="MEDIO - Sin razón clara, mayor escrutinio de SAT"
        ),
        ElementoMatrizNHP(
            norma="Requisitos formales e IVA",
            fundamento_legal="LISR Art. 27 + LIVA Art. 5 + CFF 29-A",
            hecho_a_acreditar="CFDI válido, descripción correcta, proveedor en regla",
            pruebas_primarias=[
                "CFDI verificado en portal SAT (validación activa)",
                "Consulta de proveedor en lista 69-B (bitácora de verificación)",
                "Opinión de cumplimiento 32-D positiva del consultor"
            ],
            pruebas_secundarias=[
                "Constancia de situación fiscal del consultor",
                "Verificación de que descripción CFDI coincide con SOW"
            ],
            riesgo_si_falta="CRÍTICO si proveedor está en 69-B"
        )
    ],
    consideraciones_especiales=[
        "Consultoría estratégica/dirección tiene mayor escrutinio que consultoría técnica",
        "Honorarios elevados requieren justificación proporcional (expertise, resultados)",
        "Si el consultor es persona física, verificar que tenga capacidad real",
        "Documentar SIEMPRE las reuniones - las minutas son oro ante SAT"
    ]
)

MATRIZ_OUTSOURCING = MatrizNormaHechoPrueba(
    tipo_servicio=TipoServicio.OUTSOURCING,
    nivel_riesgo_inherente=NivelRiesgoInherente.MUY_ALTO,
    descripcion_riesgo="Máxima sensibilidad SAT/TFJA. Post-reforma outsourcing, cualquier tercerización de personal es vista con sospecha. Requiere demostrar que NO es simulación laboral.",
    elementos=[
        ElementoMatrizNHP(
            norma="No simulación laboral",
            fundamento_legal="LISR Art. 27 + LSS + LFT (contexto anti-outsourcing)",
            hecho_a_acreditar="No se trata de simulación de contratación para evitar obligaciones laborales/IMSS/ISR",
            pruebas_primarias=[
                "Contrato de servicios especializados (no subcontratación de personal)",
                "Registro REPSE del proveedor vigente (si aplica por tipo de servicio)",
                "Evidencia de que proveedor tiene plantilla propia, activos e infraestructura"
            ],
            pruebas_secundarias=[
                "Organigrama del proveedor",
                "Comprobantes de pago de nómina del proveedor a su personal",
                "Altas IMSS del personal del proveedor"
            ],
            riesgo_si_falta="CRÍTICO - Sin demostrar que no es outsourcing prohibido, rechazo total + multas"
        ),
        ElementoMatrizNHP(
            norma="Materialidad del servicio",
            fundamento_legal="CFF Art. 69-B",
            hecho_a_acreditar="El personal o servicio efectivamente se prestó y generó valor",
            pruebas_primarias=[
                "Listas de asistencia del personal tercerizado con firmas",
                "Bitácoras de trabajo con actividades específicas realizadas",
                "Reportes de horas trabajadas por proyecto/área",
                "Tickets de servicio o solicitudes atendidas"
            ],
            pruebas_secundarias=[
                "Comunicaciones entre personal tercerizado y cliente (correos, tickets)",
                "Accesos a sistemas del cliente (logs)",
                "Entregables específicos producidos por el personal"
            ],
            riesgo_si_falta="MUY ALTO - Sin evidencia de prestación real, operación simulada"
        ),
        ElementoMatrizNHP(
            norma="Razón de negocios",
            fundamento_legal="CFF Art. 5-A",
            hecho_a_acreditar="La tercerización responde a lógica de eficiencia/especialización, no solo ahorro fiscal",
            pruebas_primarias=[
                "Análisis interno 'make or buy': por qué se decide tercerizar",
                "Comparativo de costos internos vs externos (aunque sea simplificado)",
                "Justificación de expertise o flexibilidad que aporta el proveedor"
            ],
            pruebas_secundarias=[
                "Benchmarks de industria sobre tercerización",
                "Evidencia de capacidad limitada interna que justifica tercerizar"
            ],
            riesgo_si_falta="ALTO - Sin razón más allá de costo, SAT puede invocar Art. 5-A"
        ),
        ElementoMatrizNHP(
            norma="Proveedor no EFOS",
            fundamento_legal="CFF Art. 69-B",
            hecho_a_acreditar="El proveedor no está en listados de factureras y tiene sustancia real",
            pruebas_primarias=[
                "Consulta bitácora de lista 69-B con fecha de consulta",
                "Opinión de cumplimiento 32-D positiva vigente",
                "Constancia de situación fiscal del proveedor"
            ],
            pruebas_secundarias=[
                "Visita a instalaciones del proveedor documentada",
                "Verificación de domicilio fiscal activo",
                "Acta constitutiva y poderes del proveedor"
            ],
            riesgo_si_falta="CRÍTICO - Proveedor en 69-B = rechazo automático + contingencia"
        ),
        ElementoMatrizNHP(
            norma="Capacidad material del proveedor",
            fundamento_legal="CFF Art. 69-B - Criterios avanzados TFJA",
            hecho_a_acreditar="El proveedor tiene infraestructura, personal y activos congruentes con el servicio",
            pruebas_primarias=[
                "Evidencia de oficinas/instalaciones del proveedor",
                "Número de empleados registrados en IMSS del proveedor",
                "Activos fijos del proveedor congruentes con el servicio"
            ],
            pruebas_secundarias=[
                "Estados financieros del proveedor",
                "Historial de otros clientes del proveedor",
                "Referencias comerciales verificables"
            ],
            riesgo_si_falta="ALTO - Proveedor sin sustancia = EFOS potencial"
        )
    ],
    consideraciones_especiales=[
        "Post-reforma 2021: solo servicios especializados con REPSE son deducibles",
        "SAT tiene acceso cruzado a IMSS - puede detectar triangulaciones",
        "Documentar exhaustivamente la diferencia entre 'servicios' y 'personal'",
        "Si el personal tercerizado trabaja en instalaciones del cliente, mayor escrutinio",
        "Evitar contratos donde el cliente supervisa directamente al personal del proveedor"
    ]
)

# Diccionario de matrices por tipo de servicio
MATRICES_NHP: Dict[TipoServicio, MatrizNormaHechoPrueba] = {
    TipoServicio.MARKETING: MATRIZ_MARKETING,
    TipoServicio.CONSULTORIA: MATRIZ_CONSULTORIA,
    TipoServicio.OUTSOURCING: MATRIZ_OUTSOURCING,
}

# Riesgo inherente por tipo de servicio
RIESGO_POR_TIPO_SERVICIO: Dict[TipoServicio, NivelRiesgoInherente] = {
    TipoServicio.MARKETING: NivelRiesgoInherente.ALTO,
    TipoServicio.OUTSOURCING: NivelRiesgoInherente.MUY_ALTO,
    TipoServicio.CONSULTORIA: NivelRiesgoInherente.MEDIO,
    TipoServicio.TECNOLOGIA: NivelRiesgoInherente.MEDIO,
    TipoServicio.CAPACITACION: NivelRiesgoInherente.MEDIO,
    TipoServicio.HONORARIOS: NivelRiesgoInherente.MEDIO,
    TipoServicio.SERVICIOS_GENERALES: NivelRiesgoInherente.MEDIO,
    TipoServicio.LEGAL: NivelRiesgoInherente.BAJO,
    TipoServicio.CONTABLE: NivelRiesgoInherente.BAJO,
    TipoServicio.TRANSPORTE: NivelRiesgoInherente.BAJO,
    TipoServicio.MANTENIMIENTO: NivelRiesgoInherente.BAJO,
    TipoServicio.ARRENDAMIENTO: NivelRiesgoInherente.BAJO,
}


# ============================================================
# PLANTILLAS DE ARGUMENTACIÓN PARA DEFENSE FILE
# ============================================================

PLANTILLAS_ARGUMENTACION: List[PlantillaArgumentacion] = [
    PlantillaArgumentacion(
        seccion="hechos",
        titulo="Descripción de Hechos",
        template="""Durante el ejercicio fiscal {año}, la contribuyente {nombre_contribuyente} (RFC: {rfc_contribuyente})
contrató a {nombre_proveedor} (RFC: {rfc_proveedor}) para la prestación de servicios de {tipo_servicio}
consistentes en {descripcion_servicio}.

El propósito del proyecto fue {objetivo_negocio}, en el marco de {contexto_estrategico}.

El monto total del servicio ascendió a ${monto_total:,.2f} MXN más IVA, pagado mediante {forma_pago}
en {numero_pagos} exhibición(es), quedando debidamente registrado en la contabilidad de la contribuyente.""",
        variables_requeridas=["año", "nombre_contribuyente", "rfc_contribuyente", "nombre_proveedor",
                              "rfc_proveedor", "tipo_servicio", "descripcion_servicio", "objetivo_negocio",
                              "contexto_estrategico", "monto_total", "forma_pago", "numero_pagos"],
        ejemplo="Durante el ejercicio fiscal 2024, la contribuyente Empresa ABC SA de CV contrató a Consultores XYZ..."
    ),
    PlantillaArgumentacion(
        seccion="evidencia",
        titulo="Acreditación de Existencia y Ejecución",
        template="""La existencia y efectiva ejecución de los servicios contratados se acredita fehacientemente con la siguiente documentación:

DOCUMENTACIÓN CONTRACTUAL:
{lista_documentos_contractuales}

EVIDENCIA DE EJECUCIÓN:
{lista_evidencia_ejecucion}

SOPORTE DE PAGO:
{lista_soporte_pago}

VALIDACIONES SAT:
{lista_validaciones_sat}

Toda la documentación anterior obra en el expediente como Anexos {rango_anexos}, debidamente foliada
y con sellado de tiempo conforme a la NOM-151-SCFI-2016 donde aplica.""",
        variables_requeridas=["lista_documentos_contractuales", "lista_evidencia_ejecucion",
                              "lista_soporte_pago", "lista_validaciones_sat", "rango_anexos"],
        ejemplo="(i) Contrato de servicios de fecha 15 de enero de 2024..."
    ),
    PlantillaArgumentacion(
        seccion="deducibilidad",
        titulo="Cumplimiento de Requisitos de Deducibilidad (LISR 27)",
        template="""Los servicios contratados cumplen íntegramente con los requisitos de deducibilidad establecidos
en el Artículo 27 de la Ley del Impuesto sobre la Renta, conforme a lo siguiente:

FRACCIÓN I - ESTRICTA INDISPENSABILIDAD:
{argumentacion_indispensabilidad}

FRACCIÓN III - EFECTIVAMENTE EROGADO:
El gasto fue efectivamente erogado mediante {forma_pago} con fecha(s) {fechas_pago}, como consta en
los estados de cuenta bancarios y pólizas contables que obran en el expediente.

FRACCIÓN XVIII - COMPROBANTE FISCAL:
Se cuenta con CFDI(s) número(s) {folios_cfdi}, expedido(s) por {nombre_proveedor}, validado(s) ante
el SAT con estatus vigente a la fecha de la operación.""",
        variables_requeridas=["argumentacion_indispensabilidad", "forma_pago", "fechas_pago",
                              "folios_cfdi", "nombre_proveedor"],
        ejemplo="El servicio resulta estrictamente indispensable para la actividad de la contribuyente..."
    ),
    PlantillaArgumentacion(
        seccion="materialidad",
        titulo="Acreditación de Materialidad (CFF 69-B)",
        template="""Contrario a lo que pudiera presumirse en operaciones simuladas, la materialidad de los servicios
se encuentra plenamente demostrada, toda vez que:

EVIDENCIA DE PRESTACIÓN REAL:
{argumentacion_materialidad}

CAPACIDAD DEL PROVEEDOR:
El proveedor {nombre_proveedor} cuenta con la infraestructura, personal y capacidad técnica
necesarios para prestar los servicios contratados, como se acredita con {evidencia_capacidad_proveedor}.

VERIFICACIÓN 69-B:
Se realizó consulta a la lista de contribuyentes del Artículo 69-B del CFF con fecha {fecha_consulta_69b},
resultando que el proveedor NO se encuentra publicado en dicho listado. Constancia de la consulta
obra como Anexo {anexo_69b}.""",
        variables_requeridas=["argumentacion_materialidad", "nombre_proveedor",
                              "evidencia_capacidad_proveedor", "fecha_consulta_69b", "anexo_69b"],
        ejemplo="Los servicios de consultoría fueron efectivamente prestados mediante..."
    ),
    PlantillaArgumentacion(
        seccion="razon_negocios",
        titulo="Razón de Negocios (CFF 5-A)",
        template="""La operación cuenta con una razón de negocios válida y sustentable, conforme al Artículo 5-A
del Código Fiscal de la Federación, por las siguientes consideraciones:

JUSTIFICACIÓN ECONÓMICA:
{argumentacion_razon_negocios}

BENEFICIO ECONÓMICO ESPERADO VS OBTENIDO:
{analisis_beneficio_economico}

ALTERNATIVAS CONSIDERADAS:
Previo a la contratación, se evaluaron las siguientes alternativas: {alternativas_evaluadas},
eligiéndose la opción contratada por {motivos_eleccion}.

En consecuencia, la operación tiene efectos jurídicos y económicos razonables, independientemente
del posible ahorro o beneficio fiscal, cumpliendo con el estándar del Artículo 5-A del CFF.""",
        variables_requeridas=["argumentacion_razon_negocios", "analisis_beneficio_economico",
                              "alternativas_evaluadas", "motivos_eleccion"],
        ejemplo="El servicio responde a la necesidad de la contribuyente de..."
    ),
    PlantillaArgumentacion(
        seccion="conclusion",
        titulo="Conclusión",
        template="""Por todo lo anteriormente expuesto, la deducción reclamada por concepto de {tipo_servicio}
por un monto de ${monto_total:,.2f} MXN y el acreditamiento de IVA asociado por ${monto_iva:,.2f} MXN,
cumplen cabalmente con los requisitos legales establecidos en:

- Artículo 27 de la Ley del Impuesto sobre la Renta
- Artículo 5 de la Ley del Impuesto al Valor Agregado
- Artículos 5-A, 29-A y 69-B del Código Fiscal de la Federación
- Anexo 20 de la Resolución Miscelánea Fiscal

En consecuencia, la determinación de la autoridad fiscal resulta {calificacion_determinacion} en cuanto
desconoce {aspectos_desconocidos}, debiendo {peticion_concreta}.""",
        variables_requeridas=["tipo_servicio", "monto_total", "monto_iva", "calificacion_determinacion",
                              "aspectos_desconocidos", "peticion_concreta"],
        ejemplo="infundada e indebidamente motivada"
    )
]


# ============================================================
# REGLAS FINAS LISR 27 POR CATEGORÍA DE GASTO
# ============================================================

REGLAS_POR_CATEGORIA: Dict[CategoriaGasto, List[Dict[str, Any]]] = {
    CategoriaGasto.SERVICIOS_RECURRENTES: [
        {
            "id": "LISR27_RECURRENTE_01",
            "nombre": "Vinculación con operación diaria",
            "descripcion": "El servicio debe vincularse directamente con la operación rutinaria",
            "evidencia_minima": ["Contrato de servicios", "Órdenes de servicio mensuales", "Bitácora de servicios"],
            "nivel_exigencia": "MEDIO",
            "notas": "Servicios como limpieza, seguridad, mantenimiento tienen presunción favorable de indispensabilidad"
        },
        {
            "id": "LISR27_RECURRENTE_02",
            "nombre": "Periodicidad congruente",
            "descripcion": "La facturación debe corresponder a periodos de servicio verificables",
            "evidencia_minima": ["CFDI con periodo de servicio", "Reportes de servicio por periodo"],
            "nivel_exigencia": "BAJO",
            "notas": "SAT generalmente no cuestiona servicios recurrentes bien documentados"
        }
    ],
    CategoriaGasto.CONSULTORIA_ESTRATEGICA: [
        {
            "id": "LISR27_CONSULT_01",
            "nombre": "Justificación de expertise externo",
            "descripcion": "Debe explicarse por qué se requiere consultor externo vs capacidad interna",
            "evidencia_minima": ["Análisis de necesidad", "Perfil del consultor", "Comparativo de opciones"],
            "nivel_exigencia": "ALTO",
            "notas": "SAT cuestiona consultorías caras sin evidencia de valor agregado especializado"
        },
        {
            "id": "LISR27_CONSULT_02",
            "nombre": "Entregables tangibles",
            "descripcion": "La consultoría debe producir entregables documentales verificables",
            "evidencia_minima": ["Informes de consultoría", "Diagnósticos", "Recomendaciones documentadas"],
            "nivel_exigencia": "ALTO",
            "notas": "Consultoría sin papeles = operación cuestionable"
        },
        {
            "id": "LISR27_CONSULT_03",
            "nombre": "Implementación de recomendaciones",
            "descripcion": "Idealmente, evidenciar que las recomendaciones se implementaron",
            "evidencia_minima": ["Decisiones tomadas derivadas", "Cambios en procesos", "Políticas modificadas"],
            "nivel_exigencia": "MEDIO",
            "notas": "Consultoría que no genera cambios levanta sospechas"
        }
    ],
    CategoriaGasto.PUBLICIDAD_PROPAGANDA: [
        {
            "id": "LISR27_PUBLI_01",
            "nombre": "Evidencia de ejecución de campaña",
            "descripcion": "Debe demostrarse que la campaña efectivamente se ejecutó",
            "evidencia_minima": ["Screenshots de anuncios", "Reportes de plataformas", "URLs de publicaciones"],
            "nivel_exigencia": "MUY ALTO",
            "notas": "Publicidad sin evidencia de publicación = rechazada sistemáticamente"
        },
        {
            "id": "LISR27_PUBLI_02",
            "nombre": "Métricas de resultados",
            "descripcion": "Debe existir medición del impacto de la publicidad",
            "evidencia_minima": ["Reportes de métricas", "Analytics", "Leads/conversiones"],
            "nivel_exigencia": "ALTO",
            "notas": "SAT espera correlación entre gasto publicitario y resultados medibles"
        },
        {
            "id": "LISR27_PUBLI_03",
            "nombre": "Congruencia monto vs alcance",
            "descripcion": "El monto pagado debe ser congruente con el alcance de la campaña",
            "evidencia_minima": ["Comparativo de precios de mercado", "Propuesta con desglose"],
            "nivel_exigencia": "MEDIO",
            "notas": "Montos desproporcionados vs resultados = señal de EFOS"
        }
    ],
    CategoriaGasto.PARTES_RELACIONADAS: [
        {
            "id": "LISR27_PR_01",
            "nombre": "Estudio de precios de transferencia",
            "descripcion": "Operaciones con partes relacionadas requieren soporte de precios de mercado",
            "evidencia_minima": ["Estudio de PT", "Análisis de comparables", "Documentación master file"],
            "nivel_exigencia": "OBLIGATORIO",
            "notas": "Sin estudio de PT, deducciones con partes relacionadas son altamente cuestionables"
        },
        {
            "id": "LISR27_PR_02",
            "nombre": "Contrato intercompañía",
            "descripcion": "Debe existir contrato formal entre las partes relacionadas",
            "evidencia_minima": ["Contrato marco", "Anexos de servicios", "Precios acordados"],
            "nivel_exigencia": "OBLIGATORIO",
            "notas": "Operaciones sin contrato intragrupo = rechazo probable"
        },
        {
            "id": "LISR27_PR_03",
            "nombre": "Sustancia económica real",
            "descripcion": "La operación debe tener sustancia más allá del beneficio fiscal",
            "evidencia_minima": ["Justificación de negocio", "Análisis funcional", "Evidencia de servicios reales"],
            "nivel_exigencia": "MUY ALTO",
            "notas": "SAT presume artificialidad en operaciones intragrupo"
        }
    ],
    CategoriaGasto.VIATICOS_REPRESENTACION: [
        {
            "id": "LISR27_VIAT_01",
            "nombre": "Bitácora de viaje con propósito",
            "descripcion": "Cada viaje debe tener objetivo de negocio documentado",
            "evidencia_minima": ["Solicitud de viaje", "Objetivo del viaje", "Reporte post-viaje"],
            "nivel_exigencia": "ALTO",
            "notas": "Viajes sin justificación de negocio = gastos personales no deducibles"
        },
        {
            "id": "LISR27_VIAT_02",
            "nombre": "CFDI con requisitos específicos",
            "descripcion": "Viáticos tienen requisitos especiales de comprobación",
            "evidencia_minima": ["CFDI de hospedaje", "CFDI de transporte", "Topes de ley cumplidos"],
            "nivel_exigencia": "OBLIGATORIO",
            "notas": "Viáticos que exceden topes de ley no son deducibles"
        },
        {
            "id": "LISR27_VIAT_03",
            "nombre": "Correspondencia con agenda laboral",
            "descripcion": "El viaje debe corresponder a actividades de trabajo verificables",
            "evidencia_minima": ["Calendario de reuniones", "Minutas de reuniones en destino", "Correos de coordinación"],
            "nivel_exigencia": "MEDIO",
            "notas": "Viajes en fines de semana o periodos vacacionales son cuestionados"
        }
    ],
    CategoriaGasto.TERCERIZACION: [
        {
            "id": "LISR27_TERC_01",
            "nombre": "Registro REPSE vigente",
            "descripcion": "El proveedor debe tener registro REPSE si presta servicios especializados",
            "evidencia_minima": ["Constancia REPSE", "Verificación en portal STPS"],
            "nivel_exigencia": "OBLIGATORIO",
            "notas": "Sin REPSE, servicios especializados no son deducibles post-reforma 2021"
        },
        {
            "id": "LISR27_TERC_02",
            "nombre": "No subordinación del personal",
            "descripcion": "El personal del proveedor no debe estar subordinado al cliente",
            "evidencia_minima": ["Contrato de servicios (no de personal)", "Evidencia de supervisión por proveedor"],
            "nivel_exigencia": "MUY ALTO",
            "notas": "Subordinación = relación laboral encubierta = contingencia IMSS/ISR"
        },
        {
            "id": "LISR27_TERC_03",
            "nombre": "Servicio especializado real",
            "descripcion": "El servicio debe ser genuinamente especializado, no staffing genérico",
            "evidencia_minima": ["Descripción de especialización", "Certificaciones del proveedor", "Resultados especializados"],
            "nivel_exigencia": "ALTO",
            "notas": "Tercerizar 'recepcionistas' no es servicio especializado"
        }
    ]
}


# ============================================================
# CATÁLOGO DE REGLAS - LISR 27
# ============================================================

REGLAS_LISR_27: List[ReglaValidacion] = [
    ReglaValidacion(
        id="LISR_27_I",
        nombre="Estricta Indispensabilidad",
        fundamento_legal="LISR Art. 27 Fracción I",
        capa=CapaValidacion.FORMAL_FISCAL,
        descripcion="El gasto debe estar directamente vinculado con la actividad que genera ingresos",
        condicion_logica="gasto.vinculado_actividad_principal AND NOT gasto.es_personal AND NOT gasto.es_suntuario",
        evidencias_minimas=[
            EvidenciaRequerida(
                tipo=TipoEvidencia.CONTRATO,
                descripcion="Contrato/orden de servicio con descripción del objeto",
                obligatoria=True
            ),
            EvidenciaRequerida(
                tipo=TipoEvidencia.CFDI,
                descripcion="CFDI con descripción coherente con contrato y actividad",
                obligatoria=True
            ),
            EvidenciaRequerida(
                tipo=TipoEvidencia.ENTREGABLE,
                descripcion="Papeles de trabajo, reportes o entregables del servicio",
                obligatoria=True,
                alternativas=[TipoEvidencia.REPORTE, TipoEvidencia.ACTA]
            ),
        ],
        aplica_a_servicios=list(TipoServicio),
        peso_validacion=1.5  # Mayor peso por ser requisito fundamental
    ),

    ReglaValidacion(
        id="LISR_27_III",
        nombre="Efectivamente Erogado y Registrado",
        fundamento_legal="LISR Art. 27 Fracción III",
        capa=CapaValidacion.FORMAL_FISCAL,
        descripcion="El pago debe estar bancariamente soportado y registrado en contabilidad",
        condicion_logica="pago.tiene_soporte_bancario AND gasto.registrado_contabilidad AND gasto.cfdi_vinculado",
        evidencias_minimas=[
            EvidenciaRequerida(
                tipo=TipoEvidencia.ESTADO_CUENTA,
                descripcion="Estado de cuenta bancario con pago identificable",
                obligatoria=True
            ),
            EvidenciaRequerida(
                tipo=TipoEvidencia.POLIZA_CONTABLE,
                descripcion="Póliza contable con CFDI vinculado",
                obligatoria=True
            ),
        ],
        aplica_a_servicios=list(TipoServicio),
        peso_validacion=1.2
    ),

    ReglaValidacion(
        id="LISR_27_CFDI",
        nombre="CFDI Válido y Proveedor en Regla",
        fundamento_legal="LISR Art. 27 Fracciones relativas a CFDI",
        capa=CapaValidacion.FORMAL_FISCAL,
        descripcion="El proveedor debe tener RFC válido, no estar en 69-B y cumplir requisitos",
        condicion_logica="proveedor.rfc_valido AND NOT proveedor.en_lista_69b AND cfdi.validado_sat",
        evidencias_minimas=[
            EvidenciaRequerida(
                tipo=TipoEvidencia.CONSULTA_SAT,
                descripcion="Validación de CFDI en portal SAT",
                obligatoria=True
            ),
            EvidenciaRequerida(
                tipo=TipoEvidencia.LISTA_69B,
                descripcion="Consulta de proveedor en lista 69-B SAT",
                obligatoria=True
            ),
            EvidenciaRequerida(
                tipo=TipoEvidencia.OPINION_32D,
                descripcion="Opinión de cumplimiento 32-D del proveedor",
                obligatoria=False  # Solo en ciertos supuestos
            ),
        ],
        aplica_a_servicios=list(TipoServicio),
        peso_validacion=1.3
    ),

    ReglaValidacion(
        id="LISR_27_PARTES_REL",
        nombre="Operaciones con Partes Relacionadas",
        fundamento_legal="LISR Art. 27 y Art. 76 (Precios de Transferencia)",
        capa=CapaValidacion.FORMAL_FISCAL,
        descripcion="Servicios con partes relacionadas requieren documentación adicional",
        condicion_logica="IF operacion.es_parte_relacionada THEN existe.estudio_pt AND existe.contrato_intercompania",
        evidencias_minimas=[
            EvidenciaRequerida(
                tipo=TipoEvidencia.ESTUDIO_PRECIOS_TRANSFERENCIA,
                descripcion="Estudio de precios de transferencia o análisis soporte",
                obligatoria=True
            ),
            EvidenciaRequerida(
                tipo=TipoEvidencia.CONTRATO,
                descripcion="Contrato marco de servicios intragrupo",
                obligatoria=True
            ),
        ],
        aplica_a_servicios=list(TipoServicio),
        peso_validacion=1.0
    ),
]


# ============================================================
# CATÁLOGO DE REGLAS - CFF 69-B y 5-A (MATERIALIDAD)
# ============================================================

REGLAS_CFF_MATERIALIDAD: List[ReglaValidacion] = [
    ReglaValidacion(
        id="CFF_69B_PROVEEDOR",
        nombre="Verificación Lista 69-B",
        fundamento_legal="CFF Art. 69-B",
        capa=CapaValidacion.MATERIALIDAD,
        descripcion="El proveedor no debe estar en listados de presuntos/definitivos EFOS",
        condicion_logica="NOT proveedor.en_lista_presuntos_69b AND NOT proveedor.en_lista_definitivos_69b",
        evidencias_minimas=[
            EvidenciaRequerida(
                tipo=TipoEvidencia.LISTA_69B,
                descripcion="Consulta y bitácora de verificación en lista 69-B SAT",
                obligatoria=True
            ),
        ],
        aplica_a_servicios=list(TipoServicio),
        peso_validacion=2.0  # Muy alto peso - es crítico
    ),

    ReglaValidacion(
        id="CFF_69B_MATERIALIDAD",
        nombre="Acreditación de Materialidad del Servicio",
        fundamento_legal="CFF Art. 69-B (Materialidad)",
        capa=CapaValidacion.MATERIALIDAD,
        descripcion="Debe existir evidencia objetiva de la prestación real del servicio",
        condicion_logica="existe.contrato_detallado AND existe.entregables AND existe.comunicaciones_operacion",
        evidencias_minimas=[
            EvidenciaRequerida(
                tipo=TipoEvidencia.CONTRATO,
                descripcion="Contrato con descripción detallada de servicios, métricas y entregables",
                obligatoria=True
            ),
            EvidenciaRequerida(
                tipo=TipoEvidencia.ORDEN_SERVICIO,
                descripcion="Órdenes de trabajo, SOW o actas de servicio",
                obligatoria=True,
                alternativas=[TipoEvidencia.ACTA]
            ),
            EvidenciaRequerida(
                tipo=TipoEvidencia.ENTREGABLE,
                descripcion="Entregables: informes, reportes, productos digitales",
                obligatoria=True,
                alternativas=[TipoEvidencia.REPORTE]
            ),
            EvidenciaRequerida(
                tipo=TipoEvidencia.CORREO,
                descripcion="Medios electrónicos: correos, tickets, registros de uso",
                obligatoria=False
            ),
        ],
        aplica_a_servicios=list(TipoServicio),
        peso_validacion=1.8
    ),

    ReglaValidacion(
        id="CFF_69B_INFRAESTRUCTURA",
        nombre="Congruencia de Infraestructura del Proveedor",
        fundamento_legal="CFF Art. 69-B (Criterios de sustancia)",
        capa=CapaValidacion.MATERIALIDAD,
        descripcion="El proveedor debe tener infraestructura mínima congruente con el servicio",
        condicion_logica="proveedor.tiene_empleados OR proveedor.tiene_activos OR proveedor.tiene_domicilio_operativo",
        evidencias_minimas=[
            EvidenciaRequerida(
                tipo=TipoEvidencia.CONSULTA_SAT,
                descripcion="Constancia de situación fiscal del proveedor",
                obligatoria=True
            ),
        ],
        aplica_a_servicios=list(TipoServicio),
        peso_validacion=1.2
    ),

    ReglaValidacion(
        id="CFF_5A_RAZON",
        nombre="Razón de Negocios",
        fundamento_legal="CFF Art. 5-A",
        capa=CapaValidacion.RAZON_NEGOCIOS,
        descripcion="La operación debe tener razón económica válida más allá del beneficio fiscal",
        condicion_logica="existe.justificacion_negocio AND existe.analisis_necesidad AND operacion.resuelve_problema_real",
        evidencias_minimas=[
            EvidenciaRequerida(
                tipo=TipoEvidencia.MEMORANDO_INTERNO,
                descripcion="Memorandos internos o minutas donde se justifica el proyecto/servicio",
                obligatoria=True,
                alternativas=[TipoEvidencia.MINUTA]
            ),
            EvidenciaRequerida(
                tipo=TipoEvidencia.ANALISIS_COSTO_BENEFICIO,
                descripcion="Análisis de costos/beneficios o hipótesis de negocio",
                obligatoria=False
            ),
        ],
        aplica_a_servicios=list(TipoServicio),
        peso_validacion=1.5
    ),
]


# ============================================================
# CATÁLOGO DE REGLAS - LIVA 5 Y ANEXO 20
# ============================================================

REGLAS_IVA_CFDI: List[ReglaValidacion] = [
    ReglaValidacion(
        id="LIVA_5_ACREDITAMIENTO",
        nombre="Requisitos de Acreditamiento IVA",
        fundamento_legal="LIVA Art. 5",
        capa=CapaValidacion.FORMAL_FISCAL,
        descripcion="El IVA debe estar trasladado expresamente y efectivamente pagado",
        condicion_logica="cfdi.iva_trasladado_expreso AND pago.iva_efectivamente_pagado AND gasto.cumple_lisr27",
        evidencias_minimas=[
            EvidenciaRequerida(
                tipo=TipoEvidencia.CFDI,
                descripcion="CFDI con campos correctos de IVA trasladado",
                obligatoria=True
            ),
            EvidenciaRequerida(
                tipo=TipoEvidencia.ESTADO_CUENTA,
                descripcion="Estado de cuenta o póliza que demuestre pago",
                obligatoria=True,
                alternativas=[TipoEvidencia.POLIZA_CONTABLE]
            ),
        ],
        aplica_a_servicios=list(TipoServicio),
        peso_validacion=1.3
    ),

    ReglaValidacion(
        id="ANEXO20_ESTRUCTURA",
        nombre="Estructura CFDI Anexo 20",
        fundamento_legal="CFF Art. 29-A y Anexo 20 RMF",
        capa=CapaValidacion.FORMAL_FISCAL,
        descripcion="El CFDI debe cumplir con la estructura del Anexo 20",
        condicion_logica="cfdi.rfc_valido AND cfdi.regimen_congruente AND cfdi.clave_servicio_correcta AND cfdi.objeto_imp_correcto",
        evidencias_minimas=[
            EvidenciaRequerida(
                tipo=TipoEvidencia.CFDI,
                descripcion="CFDI con estructura completa según Anexo 20",
                obligatoria=True
            ),
            EvidenciaRequerida(
                tipo=TipoEvidencia.CONSULTA_SAT,
                descripcion="Validación de vigencia de CFDI en SAT",
                obligatoria=True
            ),
        ],
        aplica_a_servicios=list(TipoServicio),
        peso_validacion=1.0
    ),

    ReglaValidacion(
        id="ANEXO20_DESCRIPCION",
        nombre="Descripción Adecuada en CFDI",
        fundamento_legal="Anexo 20 RMF - Campo Descripción",
        capa=CapaValidacion.FORMAL_FISCAL,
        descripcion="La descripción del concepto debe ser suficientemente detallada",
        condicion_logica="cfdi.descripcion.longitud >= 20 AND cfdi.descripcion.no_es_generica",
        evidencias_minimas=[
            EvidenciaRequerida(
                tipo=TipoEvidencia.CFDI,
                descripcion="CFDI con descripción detallada (no solo 'servicios profesionales')",
                obligatoria=True
            ),
        ],
        aplica_a_servicios=list(TipoServicio),
        peso_validacion=0.8
    ),
]


# ============================================================
# EVIDENCIAS MÍNIMAS POR TIPO DE SERVICIO
# ============================================================

EVIDENCIAS_POR_TIPO_SERVICIO: Dict[TipoServicio, List[EvidenciaRequerida]] = {
    TipoServicio.CONSULTORIA: [
        EvidenciaRequerida(TipoEvidencia.CONTRATO, "Contrato de consultoría con alcance definido", True),
        EvidenciaRequerida(TipoEvidencia.REPORTE, "Informes de consultoría entregados", True),
        EvidenciaRequerida(TipoEvidencia.ACTA, "Actas de sesiones de trabajo", False),
        EvidenciaRequerida(TipoEvidencia.CORREO, "Comunicaciones con consultor", False),
    ],
    TipoServicio.TECNOLOGIA: [
        EvidenciaRequerida(TipoEvidencia.CONTRATO, "Contrato de servicios TI con SLAs", True),
        EvidenciaRequerida(TipoEvidencia.ENTREGABLE, "Código fuente, documentación técnica, licencias", True),
        EvidenciaRequerida(TipoEvidencia.REPORTE, "Reportes de avance o tickets cerrados", True),
        EvidenciaRequerida(TipoEvidencia.CORREO, "Logs de sistema o registros de uso", False),
    ],
    TipoServicio.MARKETING: [
        EvidenciaRequerida(TipoEvidencia.CONTRATO, "Contrato de servicios de marketing", True),
        EvidenciaRequerida(TipoEvidencia.ENTREGABLE, "Materiales creativos, campañas, métricas", True),
        EvidenciaRequerida(TipoEvidencia.REPORTE, "Reportes de resultados de campaña", True),
        EvidenciaRequerida(TipoEvidencia.ANALISIS_COSTO_BENEFICIO, "ROI de campañas", False),
    ],
    TipoServicio.LEGAL: [
        EvidenciaRequerida(TipoEvidencia.CONTRATO, "Contrato de servicios legales", True),
        EvidenciaRequerida(TipoEvidencia.ENTREGABLE, "Opiniones legales, contratos revisados", True),
        EvidenciaRequerida(TipoEvidencia.ACTA, "Actas de reuniones legales", False),
    ],
    TipoServicio.CONTABLE: [
        EvidenciaRequerida(TipoEvidencia.CONTRATO, "Contrato de servicios contables", True),
        EvidenciaRequerida(TipoEvidencia.ENTREGABLE, "Estados financieros, declaraciones", True),
        EvidenciaRequerida(TipoEvidencia.REPORTE, "Reportes de cierre contable", True),
    ],
    TipoServicio.OUTSOURCING: [
        EvidenciaRequerida(TipoEvidencia.CONTRATO, "Contrato de outsourcing con alcance", True),
        EvidenciaRequerida(TipoEvidencia.REPORTE, "Reportes de operación y KPIs", True),
        EvidenciaRequerida(TipoEvidencia.ACTA, "Actas de revisión de servicio", True),
        EvidenciaRequerida(TipoEvidencia.ORDEN_SERVICIO, "Órdenes de trabajo específicas", False),
    ],
    TipoServicio.CAPACITACION: [
        EvidenciaRequerida(TipoEvidencia.CONTRATO, "Contrato o cotización de capacitación", True),
        EvidenciaRequerida(TipoEvidencia.ENTREGABLE, "Materiales de capacitación, constancias DC-3", True),
        EvidenciaRequerida(TipoEvidencia.ACTA, "Listas de asistencia", True),
    ],
    TipoServicio.TRANSPORTE: [
        EvidenciaRequerida(TipoEvidencia.CONTRATO, "Contrato de transporte/logística", True),
        EvidenciaRequerida(TipoEvidencia.ENTREGABLE, "Cartas porte, guías de envío", True),
        EvidenciaRequerida(TipoEvidencia.REPORTE, "Reportes de entregas realizadas", False),
    ],
    TipoServicio.MANTENIMIENTO: [
        EvidenciaRequerida(TipoEvidencia.CONTRATO, "Contrato de mantenimiento", True),
        EvidenciaRequerida(TipoEvidencia.ORDEN_SERVICIO, "Órdenes de trabajo firmadas", True),
        EvidenciaRequerida(TipoEvidencia.REPORTE, "Bitácora de mantenimientos", False),
    ],
    TipoServicio.HONORARIOS: [
        EvidenciaRequerida(TipoEvidencia.CONTRATO, "Contrato de prestación de servicios", True),
        EvidenciaRequerida(TipoEvidencia.ENTREGABLE, "Evidencia del trabajo realizado", True),
        EvidenciaRequerida(TipoEvidencia.REPORTE, "Reportes de actividades", False),
    ],
    TipoServicio.ARRENDAMIENTO: [
        EvidenciaRequerida(TipoEvidencia.CONTRATO, "Contrato de arrendamiento", True),
        EvidenciaRequerida(TipoEvidencia.REPORTE, "Comprobante de uso del bien", False),
    ],
    TipoServicio.SERVICIOS_GENERALES: [
        EvidenciaRequerida(TipoEvidencia.CONTRATO, "Contrato o cotización del servicio", True),
        EvidenciaRequerida(TipoEvidencia.ENTREGABLE, "Evidencia de prestación del servicio", True),
    ],
}


# ============================================================
# SERVICIO DE VALIDACIÓN
# ============================================================

class LegalValidationService:
    """Servicio principal de validación legal"""

    def __init__(self):
        self.reglas_lisr = REGLAS_LISR_27
        self.reglas_cff = REGLAS_CFF_MATERIALIDAD
        self.reglas_iva = REGLAS_IVA_CFDI
        self.todas_las_reglas = self.reglas_lisr + self.reglas_cff + self.reglas_iva

    def obtener_reglas_por_capa(self, capa: CapaValidacion) -> List[ReglaValidacion]:
        """Obtiene todas las reglas de una capa específica"""
        return [r for r in self.todas_las_reglas if r.capa == capa]

    def obtener_reglas_por_servicio(self, tipo_servicio: TipoServicio) -> List[ReglaValidacion]:
        """Obtiene reglas aplicables a un tipo de servicio"""
        return [r for r in self.todas_las_reglas
                if not r.aplica_a_servicios or tipo_servicio in r.aplica_a_servicios]

    def obtener_evidencias_por_servicio(self, tipo_servicio: TipoServicio) -> List[EvidenciaRequerida]:
        """Obtiene lista de evidencias mínimas para un tipo de servicio"""
        return EVIDENCIAS_POR_TIPO_SERVICIO.get(tipo_servicio, [])

    def validar_operacion(
        self,
        operacion_id: str,
        proveedor_rfc: str,
        monto: float,
        tipo_servicio: TipoServicio,
        evidencias_presentadas: List[TipoEvidencia],
        es_parte_relacionada: bool = False,
        proveedor_en_69b: bool = False,
        cfdi_validado: bool = True,
        tiene_opinion_32d: bool = False
    ) -> EvaluacionCompleta:
        """
        Evalúa una operación contra todas las reglas aplicables.
        Retorna evaluación completa con semáforo de riesgo.
        """
        resultados: List[ResultadoValidacion] = []

        # Obtener reglas aplicables
        reglas = self.obtener_reglas_por_servicio(tipo_servicio)

        # Si es parte relacionada, incluir regla específica
        if not es_parte_relacionada:
            reglas = [r for r in reglas if r.id != "LISR_27_PARTES_REL"]

        # Evaluar cada regla
        for regla in reglas:
            resultado = self._evaluar_regla(
                regla,
                evidencias_presentadas,
                proveedor_en_69b,
                cfdi_validado,
                tiene_opinion_32d,
                es_parte_relacionada
            )
            resultados.append(resultado)

        # Calcular scores por capa
        score_formal = self._calcular_score_capa(resultados, CapaValidacion.FORMAL_FISCAL)
        score_materialidad = self._calcular_score_capa(resultados, CapaValidacion.MATERIALIDAD)
        score_razon = self._calcular_score_capa(resultados, CapaValidacion.RAZON_NEGOCIOS)

        # Score total ponderado
        score_total = (score_formal * 0.35 + score_materialidad * 0.40 + score_razon * 0.25)

        # Determinar nivel de riesgo
        nivel_riesgo = self._determinar_nivel_riesgo(
            score_total,
            proveedor_en_69b,
            resultados
        )

        # Generar resumen y acciones correctivas
        resumen, acciones = self._generar_resumen(resultados, nivel_riesgo)

        return EvaluacionCompleta(
            operacion_id=operacion_id,
            proveedor_rfc=proveedor_rfc,
            monto=monto,
            fecha_evaluacion=datetime.now(),
            nivel_riesgo=nivel_riesgo,
            score_total=round(score_total, 2),
            score_formal=round(score_formal, 2),
            score_materialidad=round(score_materialidad, 2),
            score_razon_negocios=round(score_razon, 2),
            resultados_por_regla=resultados,
            resumen=resumen,
            acciones_correctivas=acciones
        )

    def _evaluar_regla(
        self,
        regla: ReglaValidacion,
        evidencias_presentadas: List[TipoEvidencia],
        proveedor_en_69b: bool,
        cfdi_validado: bool,
        tiene_opinion_32d: bool,
        es_parte_relacionada: bool
    ) -> ResultadoValidacion:
        """Evalúa una regla específica"""

        evidencias_presentes = []
        evidencias_faltantes = []

        for ev_req in regla.evidencias_minimas:
            # Verificar si la evidencia está presente (o alguna alternativa)
            tipos_aceptados = [ev_req.tipo] + ev_req.alternativas
            encontrada = any(t in evidencias_presentadas for t in tipos_aceptados)

            if encontrada:
                evidencias_presentes.append(ev_req.descripcion)
            elif ev_req.obligatoria:
                evidencias_faltantes.append(ev_req.descripcion)

        # Casos especiales
        observaciones = []
        recomendaciones = []

        if regla.id == "CFF_69B_PROVEEDOR" and proveedor_en_69b:
            evidencias_faltantes.append("Proveedor en lista 69-B - CRÍTICO")
            observaciones.append("⚠️ ALERTA: Proveedor aparece en lista 69-B del SAT")
            recomendaciones.append("Suspender operaciones con este proveedor hasta aclarar situación")

        if regla.id == "LISR_27_CFDI" and not cfdi_validado:
            evidencias_faltantes.append("CFDI no validado en SAT")
            recomendaciones.append("Validar CFDI en portal del SAT inmediatamente")

        # Calcular nivel de cumplimiento
        total_obligatorias = len([e for e in regla.evidencias_minimas if e.obligatoria])
        obligatorias_presentes = len(evidencias_presentes)

        if total_obligatorias > 0:
            nivel_cumplimiento = obligatorias_presentes / total_obligatorias
        else:
            nivel_cumplimiento = 1.0 if not evidencias_faltantes else 0.0

        cumple = nivel_cumplimiento >= 0.8 and not proveedor_en_69b

        if not observaciones:
            if cumple:
                observaciones.append("Regla cumplida satisfactoriamente")
            else:
                observaciones.append(f"Cumplimiento parcial: {nivel_cumplimiento*100:.0f}%")

        if evidencias_faltantes and not recomendaciones:
            recomendaciones.append(f"Obtener evidencias faltantes: {', '.join(evidencias_faltantes[:3])}")

        return ResultadoValidacion(
            regla_id=regla.id,
            regla_nombre=regla.nombre,
            cumple=cumple,
            nivel_cumplimiento=nivel_cumplimiento,
            evidencias_presentes=evidencias_presentes,
            evidencias_faltantes=evidencias_faltantes,
            observaciones="; ".join(observaciones),
            recomendaciones=recomendaciones
        )

    def _calcular_score_capa(
        self,
        resultados: List[ResultadoValidacion],
        capa: CapaValidacion
    ) -> float:
        """Calcula score promedio de una capa"""
        reglas_capa = [r for r in self.todas_las_reglas if r.capa == capa]
        ids_capa = {r.id for r in reglas_capa}

        resultados_capa = [r for r in resultados if r.regla_id in ids_capa]

        if not resultados_capa:
            return 100.0

        # Ponderar por peso de cada regla
        total_peso = 0
        score_ponderado = 0

        for resultado in resultados_capa:
            regla = next((r for r in reglas_capa if r.id == resultado.regla_id), None)
            peso = regla.peso_validacion if regla else 1.0
            total_peso += peso
            score_ponderado += resultado.nivel_cumplimiento * 100 * peso

        return score_ponderado / total_peso if total_peso > 0 else 0

    def _determinar_nivel_riesgo(
        self,
        score_total: float,
        proveedor_en_69b: bool,
        resultados: List[ResultadoValidacion]
    ) -> NivelRiesgo:
        """Determina el nivel de riesgo (semáforo)"""

        # Rojo automático si proveedor en 69-B
        if proveedor_en_69b:
            return NivelRiesgo.ROJO

        # Rojo si alguna regla crítica no cumple
        reglas_criticas = {"CFF_69B_PROVEEDOR", "LISR_27_I", "CFF_69B_MATERIALIDAD"}
        for resultado in resultados:
            if resultado.regla_id in reglas_criticas and not resultado.cumple:
                return NivelRiesgo.ROJO

        # Semáforo por score
        if score_total >= 80:
            return NivelRiesgo.VERDE
        elif score_total >= 50:
            return NivelRiesgo.AMARILLO
        else:
            return NivelRiesgo.ROJO

    def _generar_resumen(
        self,
        resultados: List[ResultadoValidacion],
        nivel_riesgo: NivelRiesgo
    ) -> tuple[str, List[str]]:
        """Genera resumen y acciones correctivas"""

        reglas_cumplidas = sum(1 for r in resultados if r.cumple)
        total_reglas = len(resultados)

        if nivel_riesgo == NivelRiesgo.VERDE:
            resumen = f"✅ Operación con riesgo bajo. {reglas_cumplidas}/{total_reglas} reglas cumplidas."
            acciones = ["Mantener archivo documental actualizado", "Programar revisión periódica"]
        elif nivel_riesgo == NivelRiesgo.AMARILLO:
            resumen = f"⚠️ Operación con riesgo medio. {reglas_cumplidas}/{total_reglas} reglas cumplidas."
            acciones = [r.recomendaciones[0] for r in resultados if not r.cumple and r.recomendaciones][:5]
        else:
            resumen = f"🔴 Operación con riesgo alto. {reglas_cumplidas}/{total_reglas} reglas cumplidas."
            acciones = ["URGENTE: Revisar viabilidad de la deducción"]
            acciones.extend([r.recomendaciones[0] for r in resultados if not r.cumple and r.recomendaciones][:5])

        return resumen, acciones

    def obtener_checklist_completo(self, tipo_servicio: TipoServicio) -> Dict[str, Any]:
        """
        Genera un checklist completo para un tipo de servicio.
        Útil para UI de captura de documentos.
        """
        reglas = self.obtener_reglas_por_servicio(tipo_servicio)
        evidencias = self.obtener_evidencias_por_servicio(tipo_servicio)

        # Consolidar todas las evidencias requeridas
        evidencias_unicas = {}

        for regla in reglas:
            for ev in regla.evidencias_minimas:
                if ev.tipo.value not in evidencias_unicas:
                    evidencias_unicas[ev.tipo.value] = {
                        "tipo": ev.tipo.value,
                        "descripcion": ev.descripcion,
                        "obligatoria": ev.obligatoria,
                        "fundamentos": [regla.fundamento_legal],
                        "reglas_relacionadas": [regla.nombre]
                    }
                else:
                    evidencias_unicas[ev.tipo.value]["fundamentos"].append(regla.fundamento_legal)
                    evidencias_unicas[ev.tipo.value]["reglas_relacionadas"].append(regla.nombre)
                    if ev.obligatoria:
                        evidencias_unicas[ev.tipo.value]["obligatoria"] = True

        # Agregar evidencias específicas del tipo de servicio
        for ev in evidencias:
            if ev.tipo.value not in evidencias_unicas:
                evidencias_unicas[ev.tipo.value] = {
                    "tipo": ev.tipo.value,
                    "descripcion": ev.descripcion,
                    "obligatoria": ev.obligatoria,
                    "fundamentos": ["Mejor práctica por tipo de servicio"],
                    "reglas_relacionadas": []
                }

        return {
            "tipo_servicio": tipo_servicio.value,
            "total_reglas_aplicables": len(reglas),
            "evidencias_requeridas": list(evidencias_unicas.values()),
            "capas_validacion": [
                {
                    "capa": CapaValidacion.FORMAL_FISCAL.value,
                    "descripcion": "Requisitos formales de CFDI, LISR 27, LIVA 5",
                    "peso": "35%"
                },
                {
                    "capa": CapaValidacion.MATERIALIDAD.value,
                    "descripcion": "Existencia real del servicio (CFF 69-B)",
                    "peso": "40%"
                },
                {
                    "capa": CapaValidacion.RAZON_NEGOCIOS.value,
                    "descripcion": "Justificación económica (CFF 5-A)",
                    "peso": "25%"
                }
            ]
        }

    # ============================================================
    # MÉTODOS PARA MATRIZ NORMA-HECHO-PRUEBA
    # ============================================================

    def obtener_matriz_nhp(self, tipo_servicio: TipoServicio) -> Optional[MatrizNormaHechoPrueba]:
        """
        Obtiene la matriz Norma-Hecho-Prueba para un tipo de servicio de alto riesgo.
        Disponible para: marketing, consultoria, outsourcing
        """
        return MATRICES_NHP.get(tipo_servicio)

    def obtener_riesgo_inherente(self, tipo_servicio: TipoServicio) -> NivelRiesgoInherente:
        """Obtiene el nivel de riesgo inherente por tipo de servicio"""
        return RIESGO_POR_TIPO_SERVICIO.get(tipo_servicio, NivelRiesgoInherente.MEDIO)

    def generar_checklist_nhp(self, tipo_servicio: TipoServicio) -> Dict[str, Any]:
        """
        Genera un checklist basado en la matriz NHP para un tipo de servicio.
        Ideal para verificar completitud documental antes de cerrar expediente.
        """
        matriz = self.obtener_matriz_nhp(tipo_servicio)
        if not matriz:
            # Si no hay matriz específica, usar checklist genérico
            return self.obtener_checklist_completo(tipo_servicio)

        checklist = {
            "tipo_servicio": tipo_servicio.value,
            "nivel_riesgo_inherente": matriz.nivel_riesgo_inherente.value,
            "descripcion_riesgo": matriz.descripcion_riesgo,
            "consideraciones_especiales": matriz.consideraciones_especiales,
            "elementos_a_verificar": []
        }

        for elemento in matriz.elementos:
            item = {
                "norma": elemento.norma,
                "fundamento_legal": elemento.fundamento_legal,
                "hecho_a_acreditar": elemento.hecho_a_acreditar,
                "pruebas_primarias": elemento.pruebas_primarias,
                "pruebas_secundarias": elemento.pruebas_secundarias,
                "riesgo_si_falta": elemento.riesgo_si_falta,
                "completado": False  # Para UI
            }
            checklist["elementos_a_verificar"].append(item)

        return checklist

    # ============================================================
    # MÉTODOS PARA REGLAS FINAS POR CATEGORÍA
    # ============================================================

    def obtener_reglas_por_categoria(self, categoria: CategoriaGasto) -> List[Dict[str, Any]]:
        """Obtiene las reglas finas LISR 27 por categoría de gasto"""
        return REGLAS_POR_CATEGORIA.get(categoria, [])

    def mapear_servicio_a_categoria(self, tipo_servicio: TipoServicio) -> CategoriaGasto:
        """Mapea un tipo de servicio a su categoría de gasto LISR 27"""
        mapeo = {
            TipoServicio.MANTENIMIENTO: CategoriaGasto.SERVICIOS_RECURRENTES,
            TipoServicio.TRANSPORTE: CategoriaGasto.SERVICIOS_RECURRENTES,
            TipoServicio.CONSULTORIA: CategoriaGasto.CONSULTORIA_ESTRATEGICA,
            TipoServicio.LEGAL: CategoriaGasto.CONSULTORIA_ESTRATEGICA,
            TipoServicio.CONTABLE: CategoriaGasto.CONSULTORIA_ESTRATEGICA,
            TipoServicio.MARKETING: CategoriaGasto.PUBLICIDAD_PROPAGANDA,
            TipoServicio.OUTSOURCING: CategoriaGasto.TERCERIZACION,
            TipoServicio.CAPACITACION: CategoriaGasto.SERVICIOS_RECURRENTES,
            TipoServicio.HONORARIOS: CategoriaGasto.CONSULTORIA_ESTRATEGICA,
            TipoServicio.ARRENDAMIENTO: CategoriaGasto.SERVICIOS_RECURRENTES,
            TipoServicio.TECNOLOGIA: CategoriaGasto.CONSULTORIA_ESTRATEGICA,
            TipoServicio.SERVICIOS_GENERALES: CategoriaGasto.SERVICIOS_RECURRENTES,
        }
        return mapeo.get(tipo_servicio, CategoriaGasto.SERVICIOS_RECURRENTES)

    def obtener_reglas_finas_servicio(self, tipo_servicio: TipoServicio) -> Dict[str, Any]:
        """
        Obtiene las reglas finas LISR 27 aplicables a un tipo de servicio.
        Combina las reglas de la categoría con información específica del servicio.
        """
        categoria = self.mapear_servicio_a_categoria(tipo_servicio)
        reglas = self.obtener_reglas_por_categoria(categoria)
        riesgo = self.obtener_riesgo_inherente(tipo_servicio)

        return {
            "tipo_servicio": tipo_servicio.value,
            "categoria_gasto": categoria.value,
            "nivel_riesgo_inherente": riesgo.value,
            "reglas_aplicables": reglas,
            "total_reglas": len(reglas),
            "nota": f"Reglas específicas para {categoria.value} según criterios SAT/TFJA vigentes"
        }

    # ============================================================
    # MÉTODOS PARA PLANTILLAS DE ARGUMENTACIÓN
    # ============================================================

    def obtener_plantillas_argumentacion(self) -> List[PlantillaArgumentacion]:
        """Obtiene todas las plantillas de argumentación disponibles"""
        return PLANTILLAS_ARGUMENTACION

    def obtener_plantilla_por_seccion(self, seccion: str) -> Optional[PlantillaArgumentacion]:
        """Obtiene una plantilla específica por sección"""
        for plantilla in PLANTILLAS_ARGUMENTACION:
            if plantilla.seccion == seccion:
                return plantilla
        return None

    def generar_argumentacion(
        self,
        seccion: str,
        variables: Dict[str, Any]
    ) -> Optional[str]:
        """
        Genera texto de argumentación usando una plantilla.
        Retorna None si faltan variables requeridas.
        """
        plantilla = self.obtener_plantilla_por_seccion(seccion)
        if not plantilla:
            logger.warning(f"Plantilla no encontrada: {seccion}")
            return None

        # Verificar variables requeridas
        faltantes = [v for v in plantilla.variables_requeridas if v not in variables]
        if faltantes:
            logger.warning(f"Variables faltantes para plantilla {seccion}: {faltantes}")
            return None

        try:
            return plantilla.template.format(**variables)
        except KeyError as e:
            logger.error(f"Error al formatear plantilla {seccion}: {e}")
            return None

    def generar_defense_file_argumentacion(
        self,
        datos_operacion: Dict[str, Any]
    ) -> Dict[str, str]:
        """
        Genera todas las secciones de argumentación para un Defense File.
        Requiere un diccionario con todos los datos de la operación.
        """
        secciones = {}

        for plantilla in PLANTILLAS_ARGUMENTACION:
            texto = self.generar_argumentacion(plantilla.seccion, datos_operacion)
            if texto:
                secciones[plantilla.seccion] = texto
            else:
                secciones[plantilla.seccion] = f"[PENDIENTE: Completar sección '{plantilla.titulo}']"

        return secciones

    # ============================================================
    # MÉTODOS PARA MODO DEFENSA
    # ============================================================

    def activar_modo_defensa(
        self,
        acto_autoridad: TipoActoAutoridad,
        numero_oficio: str,
        fecha_notificacion: datetime,
        autoridad_emisora: str,
        operaciones_cuestionadas: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Activa el modo defensa para un conjunto de operaciones cuestionadas.
        Reorganiza la información en formato de expediente de defensa.
        """
        # Calcular fecha límite según tipo de acto
        plazos = {
            TipoActoAutoridad.REVISION_ELECTRONICA: 15,
            TipoActoAutoridad.VISITA_DOMICILIARIA: 20,
            TipoActoAutoridad.REVISION_GABINETE: 20,
            TipoActoAutoridad.NEGATIVA_DEVOLUCION: 15,
            TipoActoAutoridad.OFICIO_OBSERVACIONES: 20,
            TipoActoAutoridad.CARTA_INVITACION: 15,
            TipoActoAutoridad.RESOLUCION_PROVISIONAL: 15,
        }
        plazo_dias = plazos.get(acto_autoridad, 15)

        # Calcular fecha límite (simplificado - sin considerar días inhábiles)
        from datetime import timedelta
        fecha_limite = fecha_notificacion + timedelta(days=plazo_dias)

        # Calcular monto total cuestionado
        monto_total = sum(op.get("monto", 0) for op in operaciones_cuestionadas)

        # Organizar conceptos cuestionados
        conceptos = list(set(op.get("tipo_servicio", "No especificado") for op in operaciones_cuestionadas))

        # Generar checklist de documentos
        documentos_listos = []
        documentos_faltantes = []

        for op in operaciones_cuestionadas:
            tipo_servicio = op.get("tipo_servicio")
            if tipo_servicio:
                try:
                    ts = TipoServicio(tipo_servicio)
                    matriz = self.obtener_matriz_nhp(ts)
                    if matriz:
                        for elem in matriz.elementos:
                            for prueba in elem.pruebas_primarias:
                                if prueba not in documentos_faltantes:
                                    documentos_faltantes.append(prueba)
                except ValueError:
                    pass

        expediente = {
            "modo": "DEFENSA",
            "estado": "ACTIVO",
            "acto_autoridad": {
                "tipo": acto_autoridad.value,
                "numero_oficio": numero_oficio,
                "fecha_notificacion": fecha_notificacion.isoformat(),
                "autoridad_emisora": autoridad_emisora,
            },
            "plazos": {
                "dias_habiles": plazo_dias,
                "fecha_limite": fecha_limite.isoformat(),
                "dias_restantes": (fecha_limite - datetime.now()).days
            },
            "resumen_controversia": {
                "monto_total_cuestionado": monto_total,
                "numero_operaciones": len(operaciones_cuestionadas),
                "conceptos_cuestionados": conceptos,
            },
            "operaciones_impugnadas": operaciones_cuestionadas,
            "checklist_documentos": {
                "listos": documentos_listos,
                "faltantes": documentos_faltantes,
                "porcentaje_completitud": 0 if not documentos_faltantes else
                    len(documentos_listos) / (len(documentos_listos) + len(documentos_faltantes)) * 100
            },
            "estructura_defense_file": {
                "1_identificacion_acto": "Por completar",
                "2_mapa_controversia": "Por completar",
                "3_tabla_operaciones": "Generada automáticamente",
                "4_matriz_nhp": "Por generar según operaciones",
                "5_narrativa_hechos": "Por completar",
                "6_argumentacion_juridica": "Por generar con plantillas",
                "7_conclusion_operativa": "Por completar",
                "8_checklist_abogado": "Generado automáticamente"
            },
            "recomendaciones_inmediatas": [
                "Revisar plazo de respuesta y agendar fecha de entrega",
                "Recopilar todos los documentos listados en checklist",
                "Identificar documentos que requieren certificación NOM-151",
                "Preparar narrativa de hechos cronológica",
                "Consultar con abogado fiscalista sobre estrategia"
            ]
        }

        return expediente

    def generar_mapa_controversia(
        self,
        operaciones: List[Dict[str, Any]],
        observaciones_autoridad: List[str]
    ) -> Dict[str, Any]:
        """
        Genera el mapa de controversia para el expediente de defensa.
        Identifica qué está cuestionando la autoridad y por qué.
        """
        mapa = {
            "por_tipo_cuestionamiento": {},
            "por_operacion": [],
            "resumen_defensa": []
        }

        # Categorías típicas de cuestionamiento SAT
        categorias = {
            "forma": "Requisitos formales (CFDI, fechas, datos)",
            "materialidad": "Existencia real del servicio (69-B)",
            "razon_negocios": "Razón de negocios (5-A)",
            "proveedor": "Situación del proveedor (69-B, 32-D)",
            "precio": "Precio de mercado (partes relacionadas)"
        }

        for obs in observaciones_autoridad:
            obs_lower = obs.lower()
            if "cfdi" in obs_lower or "comprobante" in obs_lower or "fecha" in obs_lower:
                cat = "forma"
            elif "69-b" in obs_lower or "inexistente" in obs_lower or "simulad" in obs_lower:
                cat = "materialidad"
            elif "razón" in obs_lower or "5-a" in obs_lower or "negocio" in obs_lower:
                cat = "razon_negocios"
            elif "proveedor" in obs_lower or "rfc" in obs_lower:
                cat = "proveedor"
            elif "precio" in obs_lower or "valor" in obs_lower or "mercado" in obs_lower:
                cat = "precio"
            else:
                cat = "materialidad"  # Default

            if cat not in mapa["por_tipo_cuestionamiento"]:
                mapa["por_tipo_cuestionamiento"][cat] = {
                    "descripcion": categorias[cat],
                    "observaciones": [],
                    "estrategia_defensa": []
                }
            mapa["por_tipo_cuestionamiento"][cat]["observaciones"].append(obs)

        # Agregar estrategias de defensa por categoría
        estrategias = {
            "forma": [
                "Presentar CFDIs validados en portal SAT",
                "Demostrar que errores formales no afectan sustancia",
                "Solicitar corrección si es subsanable"
            ],
            "materialidad": [
                "Presentar matriz NHP completa por operación",
                "Anexar evidencia de ejecución (entregables, reportes, comunicaciones)",
                "Demostrar capacidad del proveedor"
            ],
            "razon_negocios": [
                "Presentar análisis costo-beneficio previo a contratación",
                "Demostrar objetivo económico independiente del fiscal",
                "Evidenciar resultados obtenidos del servicio"
            ],
            "proveedor": [
                "Consulta 69-B a fecha de operación",
                "Opinión 32-D positiva vigente",
                "Due diligence documental del proveedor"
            ],
            "precio": [
                "Estudio de precios de transferencia",
                "Comparables de mercado",
                "Justificación del precio pactado"
            ]
        }

        for cat in mapa["por_tipo_cuestionamiento"]:
            mapa["por_tipo_cuestionamiento"][cat]["estrategia_defensa"] = estrategias.get(cat, [])

        return mapa

    def calcular_probabilidad_exito(
        self,
        evaluaciones: List[EvaluacionCompleta],
        documentos_disponibles: List[str]
    ) -> Dict[str, Any]:
        """
        Calcula una estimación de probabilidad de éxito en la defensa
        basada en el score de las operaciones y la documentación disponible.
        NOTA: Esto es un indicador interno, NO una predicción legal.
        """
        if not evaluaciones:
            return {
                "probabilidad_estimada": 0,
                "nivel": "SIN_DATOS",
                "advertencia": "No hay evaluaciones para analizar"
            }

        # Promedio de scores
        score_promedio = sum(e.score_total for e in evaluaciones) / len(evaluaciones)

        # Contar operaciones por nivel de riesgo
        verdes = sum(1 for e in evaluaciones if e.nivel_riesgo == NivelRiesgo.VERDE)
        amarillas = sum(1 for e in evaluaciones if e.nivel_riesgo == NivelRiesgo.AMARILLO)
        rojas = sum(1 for e in evaluaciones if e.nivel_riesgo == NivelRiesgo.ROJO)

        total = len(evaluaciones)
        pct_verde = (verdes / total) * 100
        pct_roja = (rojas / total) * 100

        # Ajustar por documentación
        factor_docs = min(len(documentos_disponibles) / 20, 1.0)  # Máximo 20 docs esperados

        # Calcular probabilidad base
        prob_base = (score_promedio * 0.6) + (pct_verde * 0.3) + (factor_docs * 10)
        prob_ajustada = max(0, min(100, prob_base - (pct_roja * 0.5)))

        if prob_ajustada >= 70:
            nivel = "ALTA"
            recomendacion = "Expediente sólido. Proceder con defensa."
        elif prob_ajustada >= 50:
            nivel = "MEDIA"
            recomendacion = "Fortalecer documentación antes de proceder."
        elif prob_ajustada >= 30:
            nivel = "BAJA"
            recomendacion = "Considerar acuerdo conclusivo o autocorrección."
        else:
            nivel = "MUY_BAJA"
            recomendacion = "Evaluar seriamente autocorrección para reducir contingencia."

        return {
            "probabilidad_estimada": round(prob_ajustada, 1),
            "nivel": nivel,
            "score_promedio_operaciones": round(score_promedio, 1),
            "distribucion_riesgo": {
                "verde": verdes,
                "amarillo": amarillas,
                "rojo": rojas
            },
            "documentos_disponibles": len(documentos_disponibles),
            "recomendacion": recomendacion,
            "advertencia": "Este es un indicador interno de gestión de riesgo, NO una predicción legal. Consulte siempre con un abogado fiscalista."
        }


# ============================================================
# INSTANCIA GLOBAL
# ============================================================

legal_validation_service = LegalValidationService()


def get_legal_validation_service() -> LegalValidationService:
    """Obtiene la instancia del servicio de validación legal"""
    return legal_validation_service
