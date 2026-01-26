"""
Módulo de Agentes - Personas Profesionales y Reportes Narrativos
"""

from .personas import (
    TonoComunicacion,
    PersonaProfesional,
    PERSONA_VALIDADOR_DOCUMENTAL,
    PERSONA_AUDITOR_SAT,
    PERSONA_ANALISTA_RIESGO,
    PERSONA_ESPECIALISTA_MATERIALIDAD,
    PERSONA_DEFENSOR_FISCAL,
    PERSONA_A1_ESTRATEGIA,
    PERSONA_A2_PMO,
    PERSONA_A3_FISCAL,
    PERSONA_A4_LEGAL,
    PERSONA_A5_FINANZAS,
    PERSONA_A6_PROVEEDOR,
    PERSONA_A7_DEFENSA,
    PERSONA_A8_AUDITOR,
    PERSONAS_POR_AGENTE,
    obtener_persona
)

from .reporte_narrativo import (
    NivelSeveridad,
    SeccionReporte,
    ReporteNarrativo,
    generar_reporte_ocr,
    generar_reporte_red_team,
    generar_reporte_riesgo,
    generar_reporte_defensa
)

from .report_generator import humanizar_reporte
from .guardian_agent import (
    GuardianAgent,
    PruebaConfig,
    ResultadoPrueba,
    get_guardian,
    iniciar_guardian,
    detener_guardian
)

from .debugger_agent import (
    DebuggerAgent,
    BugInfo,
    Diagnostico,
    Solucion,
    get_debugger,
    iniciar_debugger,
    detener_debugger
)

__all__ = [
    'TonoComunicacion',
    'PersonaProfesional',
    'humanizar_reporte',
    'PERSONA_VALIDADOR_DOCUMENTAL',
    'PERSONA_AUDITOR_SAT',
    'PERSONA_ANALISTA_RIESGO',
    'PERSONA_ESPECIALISTA_MATERIALIDAD',
    'PERSONA_DEFENSOR_FISCAL',
    'PERSONAS_POR_AGENTE',
    'obtener_persona',
    'NivelSeveridad',
    'SeccionReporte',
    'ReporteNarrativo',
    'generar_reporte_ocr',
    'generar_reporte_red_team',
    'generar_reporte_riesgo',
    'generar_reporte_defensa',
    'GuardianAgent',
    'PruebaConfig',
    'ResultadoPrueba',
    'get_guardian',
    'iniciar_guardian',
    'detener_guardian',
    'DebuggerAgent',
    'BugInfo',
    'Diagnostico',
    'Solucion',
    'get_debugger',
    'iniciar_debugger',
    'detener_debugger'
]
