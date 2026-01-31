"""
subagent_executor.py - Servicio de Ejecución de Subagentes

Este servicio ejecuta los subagentes especializados:
- S1_TIPIFICACION: Clasificar tipo de servicio intangible
- S2_MATERIALIDAD: Evaluar evidencia de materialidad
- S3_RIESGOS: Calcular score de riesgo fiscal
- S4_ORGANIZADOR: Organizar documentos por fase
- S5_TRAFICO: Monitorear y alertar sobre proyectos

Fecha: 2026-01-31
"""

import asyncio
import os
import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID
from enum import Enum

logger = logging.getLogger(__name__)


class TipoServicio(str, Enum):
    """Tipos de servicios intangibles según criterios SAT."""
    INVESTIGACION = "INVESTIGACION"
    DESARROLLO = "DESARROLLO"
    CONSULTORIA = "CONSULTORIA"
    AUDITORIA = "AUDITORIA"
    CAPACITACION = "CAPACITACION"
    ASESORIA_LEGAL = "ASESORIA_LEGAL"
    ASESORIA_FISCAL = "ASESORIA_FISCAL"
    SOFTWARE = "SOFTWARE"
    MARKETING = "MARKETING"
    TECNOLOGIA = "TECNOLOGIA"
    OTRO = "OTRO"


class NivelRiesgo(str, Enum):
    """Niveles de riesgo fiscal."""
    BAJO = "BAJO"       # 0-30
    MEDIO = "MEDIO"     # 31-60
    ALTO = "ALTO"       # 61-80
    CRITICO = "CRITICO" # 81-100


@dataclass
class TipificacionResult:
    """Resultado de tipificación de servicio."""
    tipo_servicio: TipoServicio
    subtipo: Optional[str]
    confianza: float
    requisitos_materialidad: List[str]
    documentos_esperados: List[str]
    risk_level: NivelRiesgo
    justificacion: str


@dataclass
class MaterialidadResult:
    """Resultado de evaluación de materialidad."""
    score_materialidad: float  # 0-100
    evidencia_antes: Dict[str, Any]
    evidencia_durante: Dict[str, Any]
    evidencia_despues: Dict[str, Any]
    gaps: List[str]
    fortalezas: List[str]
    recomendaciones: List[str]
    nivel_confianza: float


@dataclass
class RiesgosResult:
    """Resultado de evaluación de riesgos."""
    risk_score: float  # 0-100
    risk_level: NivelRiesgo
    factores_riesgo: List[Dict[str, Any]]
    mitigaciones: List[str]
    probabilidad_rechazo: float
    impacto_fiscal: Optional[float]
    recomendacion_general: str


class SubagentExecutor:
    """
    Ejecutor de subagentes especializados.
    """

    def __init__(self):
        self._llm_client = None
        self._vector_search = None

    async def initialize(self):
        """Inicializar conexiones."""
        # Lazy import para evitar dependencias circulares
        pass

    @property
    def llm_client(self):
        """Obtener cliente LLM."""
        if self._llm_client is None:
            try:
                from anthropic import AsyncAnthropic
                self._llm_client = AsyncAnthropic(
                    api_key=os.environ.get('ANTHROPIC_API_KEY', '')
                )
            except Exception:
                pass
        return self._llm_client

    # =========================================================================
    # S1_TIPIFICACION - Clasificar tipo de servicio
    # =========================================================================

    async def ejecutar_tipificacion(
        self,
        descripcion_servicio: str,
        monto: float,
        proveedor: Dict[str, Any],
        contexto_adicional: Dict = None
    ) -> TipificacionResult:
        """
        Ejecutar subagente S1_TIPIFICACION.

        Clasifica el servicio según su naturaleza y determina los requisitos
        de materialidad correspondientes.
        """
        # Matriz de requisitos por tipo de servicio
        requisitos_por_tipo = {
            TipoServicio.INVESTIGACION: {
                "requisitos": [
                    "Metodología de investigación documentada",
                    "Fuentes primarias y secundarias",
                    "Análisis de datos",
                    "Conclusiones y recomendaciones"
                ],
                "documentos": [
                    "Propuesta de investigación",
                    "Plan de trabajo",
                    "Reportes de avance",
                    "Informe final con hallazgos"
                ],
                "risk_base": 30
            },
            TipoServicio.CONSULTORIA: {
                "requisitos": [
                    "Diagnóstico inicial",
                    "Análisis de situación",
                    "Recomendaciones específicas",
                    "Plan de implementación"
                ],
                "documentos": [
                    "Propuesta de servicios",
                    "Minutas de reuniones",
                    "Entregables intermedios",
                    "Reporte final"
                ],
                "risk_base": 40
            },
            TipoServicio.ASESORIA_FISCAL: {
                "requisitos": [
                    "Análisis de situación fiscal",
                    "Fundamentación legal",
                    "Estrategias recomendadas",
                    "Documentación de soporte"
                ],
                "documentos": [
                    "Carta de encomienda",
                    "Opiniones legales",
                    "Cálculos y proyecciones",
                    "Dictamen o reporte"
                ],
                "risk_base": 50
            },
            TipoServicio.SOFTWARE: {
                "requisitos": [
                    "Especificaciones funcionales",
                    "Código fuente o configuración",
                    "Pruebas documentadas",
                    "Manual de usuario"
                ],
                "documentos": [
                    "Documento de requerimientos",
                    "Diseño técnico",
                    "Repositorio de código",
                    "Documentación técnica"
                ],
                "risk_base": 25
            },
            TipoServicio.MARKETING: {
                "requisitos": [
                    "Estrategia de marketing",
                    "Plan de medios",
                    "Creativos y materiales",
                    "Métricas de resultados"
                ],
                "documentos": [
                    "Brief creativo",
                    "Plan de campaña",
                    "Artes finales",
                    "Reporte de resultados"
                ],
                "risk_base": 45
            }
        }

        # Clasificar usando LLM o heurísticas
        tipo_detectado = await self._clasificar_servicio(descripcion_servicio)

        # Obtener requisitos
        config = requisitos_por_tipo.get(tipo_detectado, {
            "requisitos": ["Documentación general del servicio"],
            "documentos": ["Contrato", "Entregables", "Factura"],
            "risk_base": 50
        })

        # Ajustar riesgo base según monto
        risk_adjustment = 0
        if monto > 500000:
            risk_adjustment += 15
        elif monto > 100000:
            risk_adjustment += 5

        # Verificar proveedor
        if proveedor.get('es_relacionado'):
            risk_adjustment += 20
        if proveedor.get('en_lista_69b'):
            risk_adjustment += 50

        risk_score = min(100, config["risk_base"] + risk_adjustment)
        risk_level = self._score_to_level(risk_score)

        return TipificacionResult(
            tipo_servicio=tipo_detectado,
            subtipo=self._detectar_subtipo(descripcion_servicio, tipo_detectado),
            confianza=0.85,
            requisitos_materialidad=config["requisitos"],
            documentos_esperados=config["documentos"],
            risk_level=risk_level,
            justificacion=f"Servicio clasificado como {tipo_detectado.value} basado en análisis de descripción. "
                         f"Monto: ${monto:,.2f}. Riesgo base ajustado por factores específicos."
        )

    async def _clasificar_servicio(self, descripcion: str) -> TipoServicio:
        """Clasificar servicio usando keywords y/o LLM."""
        descripcion_lower = descripcion.lower()

        # Keywords por tipo
        keywords = {
            TipoServicio.INVESTIGACION: ['investigación', 'estudio', 'análisis de mercado', 'research'],
            TipoServicio.DESARROLLO: ['desarrollo', 'desarrollo de producto', 'innovación', 'prototipo'],
            TipoServicio.CONSULTORIA: ['consultoría', 'asesoría', 'diagnóstico', 'estrategia'],
            TipoServicio.AUDITORIA: ['auditoría', 'revisión', 'dictamen', 'verificación'],
            TipoServicio.CAPACITACION: ['capacitación', 'entrenamiento', 'curso', 'taller', 'formación'],
            TipoServicio.ASESORIA_LEGAL: ['legal', 'jurídico', 'abogado', 'contrato', 'litigio'],
            TipoServicio.ASESORIA_FISCAL: ['fiscal', 'impuestos', 'sat', 'tributario', 'contable'],
            TipoServicio.SOFTWARE: ['software', 'sistema', 'aplicación', 'plataforma', 'desarrollo web'],
            TipoServicio.MARKETING: ['marketing', 'publicidad', 'campaña', 'branding', 'digital'],
            TipoServicio.TECNOLOGIA: ['tecnología', 'it', 'infraestructura', 'cloud', 'implementación']
        }

        # Contar matches
        scores = {}
        for tipo, kws in keywords.items():
            score = sum(1 for kw in kws if kw in descripcion_lower)
            if score > 0:
                scores[tipo] = score

        if scores:
            return max(scores.keys(), key=lambda k: scores[k])

        return TipoServicio.OTRO

    def _detectar_subtipo(self, descripcion: str, tipo: TipoServicio) -> Optional[str]:
        """Detectar subtipo específico."""
        subtipos = {
            TipoServicio.CONSULTORIA: {
                'estratégica': ['estrategia', 'estratégica', 'planeación'],
                'operativa': ['operativa', 'procesos', 'eficiencia'],
                'financiera': ['financiera', 'finanzas', 'inversión']
            },
            TipoServicio.SOFTWARE: {
                'desarrollo a medida': ['medida', 'custom', 'personalizado'],
                'implementación ERP': ['erp', 'sap', 'oracle'],
                'desarrollo web': ['web', 'sitio', 'portal']
            }
        }

        if tipo in subtipos:
            for subtipo, keywords in subtipos[tipo].items():
                if any(kw in descripcion.lower() for kw in keywords):
                    return subtipo

        return None

    # =========================================================================
    # S2_MATERIALIDAD - Evaluar evidencia de materialidad
    # =========================================================================

    async def ejecutar_materialidad(
        self,
        documentos: List[Dict[str, Any]],
        tipo_servicio: TipoServicio,
        monto: float,
        fechas: Dict[str, str] = None
    ) -> MaterialidadResult:
        """
        Ejecutar subagente S2_MATERIALIDAD.

        Evalúa la evidencia de materialidad según el criterio del SAT:
        - ANTES: Evidencia previa a la ejecución
        - DURANTE: Evidencia de ejecución
        - DESPUÉS: Evidencia de conclusión y entrega
        """
        # Clasificar documentos por fase
        evidencia_antes = self._evaluar_fase_antes(documentos)
        evidencia_durante = self._evaluar_fase_durante(documentos)
        evidencia_despues = self._evaluar_fase_despues(documentos)

        # Calcular scores por fase
        score_antes = evidencia_antes.get('score', 0)
        score_durante = evidencia_durante.get('score', 0)
        score_despues = evidencia_despues.get('score', 0)

        # Ponderación: antes 25%, durante 40%, después 35%
        score_materialidad = (score_antes * 0.25) + (score_durante * 0.40) + (score_despues * 0.35)

        # Identificar gaps
        gaps = []
        fortalezas = []
        recomendaciones = []

        if score_antes < 60:
            gaps.append("Evidencia ANTES insuficiente: falta documentación previa al inicio")
            recomendaciones.append("Incluir contrato con fecha cierta, SIB, y aprobación de presupuesto")
        else:
            fortalezas.append("Documentación previa al inicio completa")

        if score_durante < 60:
            gaps.append("Evidencia DURANTE insuficiente: falta documentación de ejecución")
            recomendaciones.append("Incluir minutas de reuniones, correos de seguimiento, entregables parciales")
        else:
            fortalezas.append("Documentación de ejecución completa")

        if score_despues < 60:
            gaps.append("Evidencia DESPUÉS insuficiente: falta documentación de conclusión")
            recomendaciones.append("Incluir acta de entrega-recepción firmada, entregables finales, CFDI")
        else:
            fortalezas.append("Documentación de conclusión completa")

        # Ajustar por monto (montos altos requieren más evidencia)
        if monto > 500000 and score_materialidad < 80:
            gaps.append(f"Monto alto (${monto:,.2f}) requiere evidencia más robusta")
            recomendaciones.append("Aumentar nivel de detalle en documentación para montos mayores a $500,000")

        return MaterialidadResult(
            score_materialidad=round(score_materialidad, 2),
            evidencia_antes=evidencia_antes,
            evidencia_durante=evidencia_durante,
            evidencia_despues=evidencia_despues,
            gaps=gaps,
            fortalezas=fortalezas,
            recomendaciones=recomendaciones,
            nivel_confianza=0.9
        )

    def _evaluar_fase_antes(self, documentos: List[Dict]) -> Dict[str, Any]:
        """Evaluar documentos de la fase ANTES."""
        docs_antes = ['contrato', 'sow', 'propuesta', 'sib', 'presupuesto', 'aprobacion', 'orden_compra']
        encontrados = []
        score = 0

        for doc in documentos:
            doc_type = doc.get('tipo', '').lower()
            doc_name = doc.get('nombre', '').lower()

            for tipo_esperado in docs_antes:
                if tipo_esperado in doc_type or tipo_esperado in doc_name:
                    encontrados.append(doc.get('nombre', tipo_esperado))
                    score += 20
                    break

        return {
            'documentos_encontrados': encontrados,
            'score': min(100, score),
            'completitud': f"{len(encontrados)}/{len(docs_antes)} documentos esperados"
        }

    def _evaluar_fase_durante(self, documentos: List[Dict]) -> Dict[str, Any]:
        """Evaluar documentos de la fase DURANTE."""
        docs_durante = ['minuta', 'correo', 'avance', 'borrador', 'reporte_parcial', 'log', 'seguimiento']
        encontrados = []
        score = 0

        for doc in documentos:
            doc_type = doc.get('tipo', '').lower()
            doc_name = doc.get('nombre', '').lower()

            for tipo_esperado in docs_durante:
                if tipo_esperado in doc_type or tipo_esperado in doc_name:
                    encontrados.append(doc.get('nombre', tipo_esperado))
                    score += 15
                    break

        return {
            'documentos_encontrados': encontrados,
            'score': min(100, score),
            'completitud': f"{len(encontrados)} documentos de ejecución"
        }

    def _evaluar_fase_despues(self, documentos: List[Dict]) -> Dict[str, Any]:
        """Evaluar documentos de la fase DESPUÉS."""
        docs_despues = ['entregable', 'acta', 'recepcion', 'cfdi', 'factura', 'reporte_final', 'cierre']
        encontrados = []
        score = 0

        for doc in documentos:
            doc_type = doc.get('tipo', '').lower()
            doc_name = doc.get('nombre', '').lower()

            for tipo_esperado in docs_despues:
                if tipo_esperado in doc_type or tipo_esperado in doc_name:
                    encontrados.append(doc.get('nombre', tipo_esperado))
                    score += 25
                    break

        return {
            'documentos_encontrados': encontrados,
            'score': min(100, score),
            'completitud': f"{len(encontrados)}/{len(docs_despues)} documentos esperados"
        }

    # =========================================================================
    # S3_RIESGOS - Calcular score de riesgo
    # =========================================================================

    async def ejecutar_riesgos(
        self,
        proyecto: Dict[str, Any],
        materialidad_score: float,
        proveedor: Dict[str, Any],
        tipo_servicio: TipoServicio = None
    ) -> RiesgosResult:
        """
        Ejecutar subagente S3_RIESGOS.

        Calcula el score de riesgo fiscal considerando múltiples factores.
        """
        factores_riesgo = []
        risk_score = 0

        # Factor 1: Proveedor en lista 69-B
        if proveedor.get('en_lista_69b'):
            factores_riesgo.append({
                'factor': 'Lista 69-B',
                'impacto': 50,
                'descripcion': 'Proveedor en lista negra del SAT',
                'severidad': 'CRITICO'
            })
            risk_score += 50
        elif proveedor.get('alertas_69b'):
            factores_riesgo.append({
                'factor': 'Alerta 69-B',
                'impacto': 20,
                'descripcion': 'Proveedor con alertas en proceso de revisión',
                'severidad': 'ALTO'
            })
            risk_score += 20

        # Factor 2: Materialidad insuficiente
        if materialidad_score < 50:
            impacto = int((50 - materialidad_score) * 0.6)
            factores_riesgo.append({
                'factor': 'Materialidad baja',
                'impacto': impacto,
                'descripcion': f'Score de materialidad: {materialidad_score}%',
                'severidad': 'ALTO' if materialidad_score < 30 else 'MEDIO'
            })
            risk_score += impacto
        elif materialidad_score < 70:
            impacto = int((70 - materialidad_score) * 0.3)
            factores_riesgo.append({
                'factor': 'Materialidad media',
                'impacto': impacto,
                'descripcion': f'Score de materialidad: {materialidad_score}%',
                'severidad': 'MEDIO'
            })
            risk_score += impacto

        # Factor 3: Proveedor relacionado
        if proveedor.get('es_relacionado'):
            factores_riesgo.append({
                'factor': 'Parte relacionada',
                'impacto': 15,
                'descripcion': 'Operación entre partes relacionadas requiere precio de mercado',
                'severidad': 'MEDIO'
            })
            risk_score += 15

        # Factor 4: Monto elevado
        monto = proyecto.get('monto', 0)
        if monto > 1000000:
            factores_riesgo.append({
                'factor': 'Monto significativo',
                'impacto': 10,
                'descripcion': f'Monto > $1M aumenta escrutinio del SAT',
                'severidad': 'MEDIO'
            })
            risk_score += 10
        elif monto > 500000:
            factores_riesgo.append({
                'factor': 'Monto considerable',
                'impacto': 5,
                'descripcion': f'Monto > $500K requiere documentación robusta',
                'severidad': 'BAJO'
            })
            risk_score += 5

        # Factor 5: Razón de negocios débil
        if proyecto.get('bee_score', 100) < 60:
            factores_riesgo.append({
                'factor': 'Razón de negocios débil',
                'impacto': 15,
                'descripcion': 'BEE no claramente documentado',
                'severidad': 'ALTO'
            })
            risk_score += 15

        # Factor 6: Tipo de servicio de alto riesgo
        tipos_alto_riesgo = [TipoServicio.ASESORIA_FISCAL, TipoServicio.MARKETING, TipoServicio.CONSULTORIA]
        if tipo_servicio in tipos_alto_riesgo:
            factores_riesgo.append({
                'factor': 'Tipo de servicio sensible',
                'impacto': 10,
                'descripcion': f'{tipo_servicio.value} es un servicio con mayor escrutinio',
                'severidad': 'MEDIO'
            })
            risk_score += 10

        # Calcular nivel de riesgo
        risk_score = min(100, risk_score)
        risk_level = self._score_to_level(risk_score)

        # Generar mitigaciones
        mitigaciones = self._generar_mitigaciones(factores_riesgo)

        # Calcular probabilidad de rechazo
        probabilidad_rechazo = min(0.95, risk_score / 100)

        # Impacto fiscal estimado
        impacto_fiscal = None
        if monto > 0:
            # ISR 30% + multas potenciales 50%
            impacto_fiscal = monto * 0.30 * (1 + probabilidad_rechazo * 0.5)

        # Recomendación general
        if risk_level == NivelRiesgo.CRITICO:
            recomendacion = "NO PROCEDER con la deducción hasta resolver factores críticos"
        elif risk_level == NivelRiesgo.ALTO:
            recomendacion = "Fortalecer documentación antes de deducir. Considerar consulta fiscal"
        elif risk_level == NivelRiesgo.MEDIO:
            recomendacion = "Deducción viable con mejoras en documentación"
        else:
            recomendacion = "Deducción segura. Mantener expediente actualizado"

        return RiesgosResult(
            risk_score=risk_score,
            risk_level=risk_level,
            factores_riesgo=factores_riesgo,
            mitigaciones=mitigaciones,
            probabilidad_rechazo=round(probabilidad_rechazo, 2),
            impacto_fiscal=round(impacto_fiscal, 2) if impacto_fiscal else None,
            recomendacion_general=recomendacion
        )

    def _score_to_level(self, score: float) -> NivelRiesgo:
        """Convertir score a nivel de riesgo."""
        if score <= 30:
            return NivelRiesgo.BAJO
        elif score <= 60:
            return NivelRiesgo.MEDIO
        elif score <= 80:
            return NivelRiesgo.ALTO
        else:
            return NivelRiesgo.CRITICO

    def _generar_mitigaciones(self, factores: List[Dict]) -> List[str]:
        """Generar recomendaciones de mitigación."""
        mitigaciones = []

        for factor in factores:
            nombre = factor['factor']

            if 'Lista 69-B' in nombre:
                mitigaciones.append("Cambiar proveedor o esperar resolución favorable del SAT")
            elif 'Materialidad' in nombre:
                mitigaciones.append("Recabar documentación adicional de ejecución del servicio")
            elif 'relacionada' in nombre:
                mitigaciones.append("Obtener estudio de precios de transferencia")
            elif 'Monto' in nombre:
                mitigaciones.append("Documentar exhaustivamente la razón de negocios")
            elif 'Razón de negocios' in nombre:
                mitigaciones.append("Elaborar SIB detallado con BEE cuantificado")
            elif 'servicio sensible' in nombre:
                mitigaciones.append("Obtener entregables tangibles y verificables")

        return mitigaciones

    # =========================================================================
    # EJECUCIÓN COORDINADA DE TODOS LOS SUBAGENTES
    # =========================================================================

    async def ejecutar_analisis_completo(
        self,
        proyecto: Dict[str, Any],
        documentos: List[Dict[str, Any]],
        proveedor: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Ejecutar análisis completo con todos los subagentes.

        Returns:
            Dict con resultados de tipificación, materialidad y riesgos
        """
        # S1: Tipificación
        tipificacion = await self.ejecutar_tipificacion(
            descripcion_servicio=proyecto.get('descripcion', ''),
            monto=proyecto.get('monto', 0),
            proveedor=proveedor
        )

        # S2: Materialidad
        materialidad = await self.ejecutar_materialidad(
            documentos=documentos,
            tipo_servicio=tipificacion.tipo_servicio,
            monto=proyecto.get('monto', 0)
        )

        # S3: Riesgos
        riesgos = await self.ejecutar_riesgos(
            proyecto=proyecto,
            materialidad_score=materialidad.score_materialidad,
            proveedor=proveedor,
            tipo_servicio=tipificacion.tipo_servicio
        )

        return {
            'tipificacion': {
                'tipo_servicio': tipificacion.tipo_servicio.value,
                'subtipo': tipificacion.subtipo,
                'confianza': tipificacion.confianza,
                'requisitos_materialidad': tipificacion.requisitos_materialidad,
                'documentos_esperados': tipificacion.documentos_esperados,
                'risk_level': tipificacion.risk_level.value,
                'justificacion': tipificacion.justificacion
            },
            'materialidad': {
                'score': materialidad.score_materialidad,
                'evidencia_antes': materialidad.evidencia_antes,
                'evidencia_durante': materialidad.evidencia_durante,
                'evidencia_despues': materialidad.evidencia_despues,
                'gaps': materialidad.gaps,
                'fortalezas': materialidad.fortalezas,
                'recomendaciones': materialidad.recomendaciones
            },
            'riesgos': {
                'risk_score': riesgos.risk_score,
                'risk_level': riesgos.risk_level.value,
                'factores': riesgos.factores_riesgo,
                'mitigaciones': riesgos.mitigaciones,
                'probabilidad_rechazo': riesgos.probabilidad_rechazo,
                'impacto_fiscal': riesgos.impacto_fiscal,
                'recomendacion': riesgos.recomendacion_general
            },
            'resumen': {
                'decision_sugerida': self._determinar_decision(
                    tipificacion, materialidad, riesgos
                ),
                'score_consolidado': round(
                    (materialidad.score_materialidad * 0.4) +
                    ((100 - riesgos.risk_score) * 0.4) +
                    (tipificacion.confianza * 100 * 0.2),
                    2
                ),
                'timestamp': datetime.now().isoformat()
            }
        }

    def _determinar_decision(
        self,
        tipificacion: TipificacionResult,
        materialidad: MaterialidadResult,
        riesgos: RiesgosResult
    ) -> str:
        """Determinar decisión sugerida basada en análisis de subagentes."""
        if riesgos.risk_level == NivelRiesgo.CRITICO:
            return "RECHAZAR"
        elif riesgos.risk_level == NivelRiesgo.ALTO and materialidad.score_materialidad < 50:
            return "RECHAZAR"
        elif riesgos.risk_level == NivelRiesgo.ALTO or materialidad.score_materialidad < 70:
            return "APROBAR_CON_CONDICIONES"
        else:
            return "APROBAR"


# Singleton
_executor_instance: Optional[SubagentExecutor] = None


async def get_subagent_executor() -> SubagentExecutor:
    """Obtener instancia singleton del ejecutor."""
    global _executor_instance
    if _executor_instance is None:
        _executor_instance = SubagentExecutor()
        await _executor_instance.initialize()
    return _executor_instance
