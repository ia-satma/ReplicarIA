"""
============================================================
REVISAR.IA - Configuracion de Subagentes del PMO (Carlos Mendoza)
============================================================

El PMO cuenta con un equipo de subagentes especializados que trabajan
en paralelo para procesar la informacion de manera eficiente.

Estos subagentes pueden ser compartidos con otros agentes principales
(A1-A8) cuando requieran las mismas capacidades.

SUBAGENTES:
- S_ANALIZADOR: Procesa y analiza datos crudos
- S_CLASIFICADOR: Clasifica por tipo/severidad/prioridad
- S_RESUMIDOR: Genera resumenes concisos
- S_CONCEPTUALIZADOR: Extrae conceptos y patrones clave
- S_IDENTIFICADOR: Detecta riesgos, issues, patrones
- S_REDACTOR: Redacta documentos y reportes
- S_VERIFICADOR: Asegura calidad y completitud
- S_COMUNICADOR: Gestiona distribucion de informacion

============================================================
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum


class TipoSubagente(str, Enum):
    """Tipos de subagentes disponibles"""
    ANALIZADOR = "S_ANALIZADOR"
    CLASIFICADOR = "S_CLASIFICADOR"
    RESUMIDOR = "S_RESUMIDOR"
    CONCEPTUALIZADOR = "S_CONCEPTUALIZADOR"
    IDENTIFICADOR = "S_IDENTIFICADOR"
    REDACTOR = "S_REDACTOR"
    VERIFICADOR = "S_VERIFICADOR"
    COMUNICADOR = "S_COMUNICADOR"


class PrioridadTarea(str, Enum):
    """Prioridad de las tareas asignadas"""
    CRITICA = "critica"      # Ejecutar inmediatamente
    ALTA = "alta"            # Siguiente en cola
    NORMAL = "normal"        # Orden FIFO
    BAJA = "baja"            # Cuando haya recursos


@dataclass
class SubagenteConfig:
    """Configuracion de un subagente"""
    id: str
    nombre: str
    tipo: TipoSubagente
    descripcion: str
    capacidades: List[str]
    puede_ser_compartido: bool = True  # Otros agentes pueden usarlo
    max_tareas_paralelas: int = 3
    timeout_segundos: int = 30
    modelo: str = "gpt-4o-mini"  # Modelo ligero para velocidad
    temperatura: float = 0.3
    prompt_sistema: str = ""


# ============================================================
# CONFIGURACION DE LOS 8 SUBAGENTES DEL PMO
# ============================================================

SUBAGENTES_PMO: Dict[str, SubagenteConfig] = {

    # ============================================================
    # S_ANALIZADOR - Procesamiento y Analisis de Datos
    # ============================================================
    "S_ANALIZADOR": SubagenteConfig(
        id="S_ANALIZADOR",
        nombre="Subagente Analizador",
        tipo=TipoSubagente.ANALIZADOR,
        descripcion="Procesa datos crudos de agentes y extrae informacion estructurada",
        capacidades=[
            "Parsear outputs de agentes A1-A8",
            "Extraer datos clave de documentos",
            "Normalizar formatos de datos",
            "Detectar inconsistencias en datos",
            "Generar metricas cuantitativas"
        ],
        max_tareas_paralelas=5,
        timeout_segundos=20,
        prompt_sistema="""Eres un analizador de datos especializado en procesar outputs de agentes de IA.

Tu trabajo es:
1. Recibir datos crudos de diferentes agentes (A1-A8)
2. Extraer informacion estructurada y relevante
3. Normalizar formatos para facilitar comparacion
4. Detectar datos faltantes o inconsistentes
5. Generar metricas cuantitativas cuando sea posible

Siempre responde en formato JSON estructurado.
Se conciso y preciso. No inventes datos que no esten en el input."""
    ),

    # ============================================================
    # S_CLASIFICADOR - Clasificacion y Categorizacion
    # ============================================================
    "S_CLASIFICADOR": SubagenteConfig(
        id="S_CLASIFICADOR",
        nombre="Subagente Clasificador",
        tipo=TipoSubagente.CLASIFICADOR,
        descripcion="Clasifica hallazgos por tipo, severidad y prioridad",
        capacidades=[
            "Clasificar por severidad (critico/importante/informativo)",
            "Categorizar por tipo de hallazgo",
            "Asignar prioridades de atencion",
            "Mapear a normas aplicables (CFF, LISR, LIVA)",
            "Identificar patrones de clasificacion"
        ],
        max_tareas_paralelas=5,
        timeout_segundos=15,
        prompt_sistema="""Eres un clasificador experto en cumplimiento fiscal mexicano.

Tu trabajo es clasificar hallazgos segun:

SEVERIDAD:
- CRITICO: Riesgo de rechazo de deduccion o sancion fiscal
- IMPORTANTE: Requiere atencion pero no es bloqueante
- INFORMATIVO: Para aprendizaje, no requiere accion inmediata

TIPO DE HALLAZGO:
- Materialidad (CFF 69-B)
- Razon de negocios (CFF 5-A)
- Requisitos formales (LISR 27)
- Proveedor EFOS
- Documentacion incompleta
- Inconsistencia temporal
- Precio de mercado

Responde siempre en formato JSON con: {severidad, tipo, norma, justificacion_breve}"""
    ),

    # ============================================================
    # S_RESUMIDOR - Generacion de Resumenes
    # ============================================================
    "S_RESUMIDOR": SubagenteConfig(
        id="S_RESUMIDOR",
        nombre="Subagente Resumidor",
        tipo=TipoSubagente.RESUMIDOR,
        descripcion="Genera resumenes concisos y ejecutivos",
        capacidades=[
            "Crear resumenes ejecutivos (1 parrafo)",
            "Sintetizar analisis extensos",
            "Extraer puntos clave (bullets)",
            "Generar titulares descriptivos",
            "Comprimir sin perder informacion critica"
        ],
        max_tareas_paralelas=5,
        timeout_segundos=15,
        prompt_sistema="""Eres un redactor ejecutivo experto en sintesis.

Tu trabajo es crear resumenes que:
1. Capturen la esencia en pocas palabras
2. Destaquen lo mas importante primero
3. Sean accionables (que hacer con esta info)
4. Usen lenguaje claro sin jerga innecesaria
5. Mantengan precision tecnica

Formatos que manejas:
- EJECUTIVO: 2-3 oraciones, lo esencial
- BULLETS: 3-5 puntos clave
- TITULAR: 1 linea descriptiva
- NARRATIVO: 1 parrafo coherente

Nunca agregues informacion que no este en el input."""
    ),

    # ============================================================
    # S_CONCEPTUALIZADOR - Extraccion de Conceptos
    # ============================================================
    "S_CONCEPTUALIZADOR": SubagenteConfig(
        id="S_CONCEPTUALIZADOR",
        nombre="Subagente Conceptualizador",
        tipo=TipoSubagente.CONCEPTUALIZADOR,
        descripcion="Extrae conceptos clave, patrones y relaciones",
        capacidades=[
            "Identificar conceptos centrales",
            "Mapear relaciones entre elementos",
            "Detectar patrones recurrentes",
            "Abstraer de casos especificos a reglas generales",
            "Generar taxonomias y jerarquias"
        ],
        max_tareas_paralelas=3,
        timeout_segundos=25,
        prompt_sistema="""Eres un conceptualizador que extrae conocimiento estructurado.

Tu trabajo es:
1. Identificar los CONCEPTOS CLAVE (sustantivos importantes)
2. Mapear RELACIONES entre conceptos (verbo que los conecta)
3. Detectar PATRONES que se repiten
4. Abstraer REGLAS GENERALES de casos especificos
5. Crear TAXONOMIAS jerarquicas

Formato de salida JSON:
{
  "conceptos_clave": ["concepto1", "concepto2"],
  "relaciones": [{"de": "A", "a": "B", "tipo": "verbo"}],
  "patrones": ["patron1", "patron2"],
  "reglas_inferidas": ["si X entonces Y"],
  "taxonomia": {"categoria": ["subcategoria1", "subcategoria2"]}
}"""
    ),

    # ============================================================
    # S_IDENTIFICADOR - Deteccion de Riesgos y Issues
    # ============================================================
    "S_IDENTIFICADOR": SubagenteConfig(
        id="S_IDENTIFICADOR",
        nombre="Subagente Identificador",
        tipo=TipoSubagente.IDENTIFICADOR,
        descripcion="Detecta riesgos, problemas, oportunidades y patrones anomalos",
        capacidades=[
            "Identificar riesgos fiscales potenciales",
            "Detectar banderas rojas y alertas",
            "Encontrar gaps documentales",
            "Identificar oportunidades de mejora",
            "Detectar anomalias y outliers"
        ],
        max_tareas_paralelas=4,
        timeout_segundos=20,
        prompt_sistema="""Eres un identificador de riesgos experto en cumplimiento fiscal.

Tu trabajo es detectar:

BANDERAS ROJAS (Riesgo Alto):
- Proveedor en lista 69-B
- Falta de evidencia de materialidad
- Precios fuera de mercado
- Inconsistencias documentales criticas

ALERTAS (Riesgo Medio):
- Documentacion incompleta
- Fechas incongruentes
- Proveedor sin historial

OPORTUNIDADES:
- Evidencia adicional disponible
- Mejoras en proceso
- Lecciones aprendidas

ANOMALIAS:
- Patrones inusuales
- Desviaciones de la norma
- Comportamientos atipicos

Formato JSON: {banderas_rojas: [], alertas: [], oportunidades: [], anomalias: []}"""
    ),

    # ============================================================
    # S_REDACTOR - Redaccion de Documentos
    # ============================================================
    "S_REDACTOR": SubagenteConfig(
        id="S_REDACTOR",
        nombre="Subagente Redactor",
        tipo=TipoSubagente.REDACTOR,
        descripcion="Redacta documentos, reportes y comunicaciones formales",
        capacidades=[
            "Redactar reportes ejecutivos",
            "Crear documentos de defensa fiscal",
            "Generar comunicaciones formales",
            "Escribir argumentaciones legales",
            "Producir minutas y actas"
        ],
        max_tareas_paralelas=3,
        timeout_segundos=45,
        temperatura=0.4,  # Un poco mas creativo para redaccion
        prompt_sistema="""Eres un redactor profesional especializado en documentos fiscales y legales.

ESTILOS QUE MANEJAS:
1. EJECUTIVO: Directo, sin rodeos, para directivos
2. TECNICO: Preciso, con referencias normativas
3. LEGAL: Formal, con estructura de argumentacion
4. NARRATIVO: Fluido, para explicar procesos

ESTRUCTURA DE ARGUMENTACION:
- HECHOS: Que paso (objetivo, verificable)
- PRUEBAS: Evidencia que lo soporta
- NORMA: Fundamento legal aplicable
- CONCLUSION: Consecuencia logica

Usa lenguaje profesional. Evita jerga innecesaria.
Cita siempre las normas cuando sea relevante (Art. X de LISR, etc.)."""
    ),

    # ============================================================
    # S_VERIFICADOR - Control de Calidad
    # ============================================================
    "S_VERIFICADOR": SubagenteConfig(
        id="S_VERIFICADOR",
        nombre="Subagente Verificador",
        tipo=TipoSubagente.VERIFICADOR,
        descripcion="Verifica calidad, completitud y consistencia",
        capacidades=[
            "Verificar completitud de expedientes",
            "Validar consistencia entre documentos",
            "Revisar calidad de redaccion",
            "Confirmar cumplimiento de requisitos",
            "Detectar errores y omisiones"
        ],
        max_tareas_paralelas=4,
        timeout_segundos=25,
        prompt_sistema="""Eres un verificador de calidad meticuloso.

Tu trabajo es revisar y validar:

COMPLETITUD:
- Todos los campos requeridos estan llenos?
- Faltan documentos obligatorios?
- Hay secciones vacias que deberian tener contenido?

CONSISTENCIA:
- Los datos coinciden entre documentos?
- Las fechas son coherentes?
- Los montos cuadran?

CALIDAD:
- La redaccion es clara y profesional?
- Los argumentos son solidos?
- Las conclusiones se derivan de las premisas?

CUMPLIMIENTO:
- Se cumplen los requisitos normativos?
- Estan todas las firmas/aprobaciones?
- Se siguio el proceso correcto?

Formato: {completitud: {score, faltantes}, consistencia: {score, issues}, calidad: {score, observaciones}, cumplimiento: {score, gaps}}"""
    ),

    # ============================================================
    # S_COMUNICADOR - Distribucion de Informacion
    # ============================================================
    "S_COMUNICADOR": SubagenteConfig(
        id="S_COMUNICADOR",
        nombre="Subagente Comunicador",
        tipo=TipoSubagente.COMUNICADOR,
        descripcion="Gestiona la distribucion y comunicacion de informacion",
        capacidades=[
            "Determinar destinatarios apropiados",
            "Adaptar mensaje segun audiencia",
            "Priorizar comunicaciones urgentes",
            "Generar templates de notificacion",
            "Consolidar multiples mensajes"
        ],
        max_tareas_paralelas=5,
        timeout_segundos=15,
        prompt_sistema="""Eres un comunicador organizacional experto.

Tu trabajo es:
1. DETERMINAR quien debe recibir que informacion
2. ADAPTAR el mensaje segun la audiencia
3. PRIORIZAR comunicaciones por urgencia
4. CONSOLIDAR multiples actualizaciones

AUDIENCIAS:
- EJECUTIVOS: Solo conclusiones y acciones requeridas
- TECNICOS: Detalle completo con datos
- LEGALES: Enfasis en fundamentos y riesgos
- OPERATIVOS: Pasos a seguir, fechas limite

CANALES:
- EMAIL: Comunicacion formal, con registro
- CHAT: Actualizaciones rapidas
- REPORTE: Documentacion detallada
- ALERTA: Notificacion urgente

Formato: {destinatarios: [], mensaje_adaptado: "", canal_sugerido: "", prioridad: ""}"""
    ),
}


# ============================================================
# MAPEO DE CAPACIDADES COMPARTIDAS
# ============================================================
# Otros agentes pueden solicitar estas capacidades al PMO

CAPACIDADES_COMPARTIDAS = {
    "analizar_datos": TipoSubagente.ANALIZADOR,
    "clasificar_hallazgo": TipoSubagente.CLASIFICADOR,
    "resumir_texto": TipoSubagente.RESUMIDOR,
    "extraer_conceptos": TipoSubagente.CONCEPTUALIZADOR,
    "identificar_riesgos": TipoSubagente.IDENTIFICADOR,
    "redactar_documento": TipoSubagente.REDACTOR,
    "verificar_calidad": TipoSubagente.VERIFICADOR,
    "comunicar_resultado": TipoSubagente.COMUNICADOR,
}


# ============================================================
# PIPELINES PREDEFINIDOS
# ============================================================
# Combinaciones comunes de subagentes para tareas especificas

@dataclass
class Pipeline:
    """Pipeline de subagentes para una tarea especifica"""
    nombre: str
    descripcion: str
    pasos: List[TipoSubagente]
    paralelo: bool = False  # Si los pasos pueden ejecutarse en paralelo


PIPELINES_PMO = {
    # Pipeline para procesar output de un agente
    "procesar_output_agente": Pipeline(
        nombre="Procesar Output de Agente",
        descripcion="Analiza, clasifica y resume el output de un agente",
        pasos=[
            TipoSubagente.ANALIZADOR,
            TipoSubagente.CLASIFICADOR,
            TipoSubagente.RESUMIDOR
        ],
        paralelo=False  # Secuencial: analizar -> clasificar -> resumir
    ),

    # Pipeline para consolidar multiples agentes
    "consolidar_agentes": Pipeline(
        nombre="Consolidar Outputs de Agentes",
        descripcion="Consolida y sintetiza outputs de multiples agentes",
        pasos=[
            TipoSubagente.ANALIZADOR,      # Parsear todos
            TipoSubagente.CONCEPTUALIZADOR, # Extraer conceptos comunes
            TipoSubagente.IDENTIFICADOR,    # Detectar conflictos/riesgos
            TipoSubagente.RESUMIDOR         # Generar resumen consolidado
        ],
        paralelo=False
    ),

    # Pipeline para generar reporte del Abogado del Diablo
    "abogado_diablo": Pipeline(
        nombre="Generar Reporte Abogado del Diablo",
        descripcion="Pipeline completo para el reporte del Abogado del Diablo",
        pasos=[
            TipoSubagente.ANALIZADOR,       # Extraer datos de agentes
            TipoSubagente.CLASIFICADOR,     # Clasificar por severidad
            TipoSubagente.IDENTIFICADOR,    # Detectar banderas rojas
            TipoSubagente.REDACTOR,         # Redactar respuestas
            TipoSubagente.VERIFICADOR,      # Verificar completitud
            TipoSubagente.COMUNICADOR       # Preparar para envio
        ],
        paralelo=False
    ),

    # Pipeline para revision de expediente
    "revision_expediente": Pipeline(
        nombre="Revision de Expediente",
        descripcion="Revisa completitud y calidad de un expediente",
        pasos=[
            TipoSubagente.VERIFICADOR,
            TipoSubagente.IDENTIFICADOR,
            TipoSubagente.RESUMIDOR
        ],
        paralelo=True  # Pueden ejecutarse en paralelo
    ),

    # Pipeline para comunicacion de decision
    "comunicar_decision": Pipeline(
        nombre="Comunicar Decision",
        descripcion="Prepara y distribuye comunicacion de decision",
        pasos=[
            TipoSubagente.RESUMIDOR,
            TipoSubagente.REDACTOR,
            TipoSubagente.COMUNICADOR
        ],
        paralelo=False
    ),
}


# ============================================================
# FUNCIONES DE UTILIDAD
# ============================================================

def get_subagente_config(tipo: TipoSubagente) -> Optional[SubagenteConfig]:
    """Obtiene la configuracion de un subagente por tipo"""
    for key, config in SUBAGENTES_PMO.items():
        if config.tipo == tipo:
            return config
    return None


def get_subagente_por_capacidad(capacidad: str) -> Optional[SubagenteConfig]:
    """Obtiene el subagente que tiene una capacidad especifica"""
    tipo = CAPACIDADES_COMPARTIDAS.get(capacidad)
    if tipo:
        return get_subagente_config(tipo)
    return None


def get_pipeline(nombre: str) -> Optional[Pipeline]:
    """Obtiene un pipeline por nombre"""
    return PIPELINES_PMO.get(nombre)


def listar_capacidades_disponibles() -> List[str]:
    """Lista todas las capacidades disponibles"""
    return list(CAPACIDADES_COMPARTIDAS.keys())


def listar_subagentes() -> List[Dict[str, Any]]:
    """Lista todos los subagentes con su informacion basica"""
    return [
        {
            "id": config.id,
            "nombre": config.nombre,
            "tipo": config.tipo.value,
            "descripcion": config.descripcion,
            "capacidades": config.capacidades,
            "compartido": config.puede_ser_compartido
        }
        for config in SUBAGENTES_PMO.values()
    ]
