from datetime import datetime
from typing import List
from backend.models.proyecto_sib import (
    FormularioSIB, ScoreDetalleA1, DictamenA1, 
    EstadoA1, RecomendacionF2, RedFlagA1, TipoBeneficio
)

class A1ScoringService:
    """Service for A1_ESTRATEGIA scoring logic"""
    
    RED_FLAGS = [
        ("OBJETIVO_VAGO", "Objetivo demasiado vago o genérico", "GRAVE"),
        ("SIN_KPIS", "Sin KPIs medibles definidos", "MODERADO"),
        ("SIN_VINCULACION_ESTRATEGICA", "Sin conexión con pilares/OKRs", "MODERADO"),
        ("TIMING_SOSPECHOSO", "Contratación en fechas atípicas (diciembre)", "MODERADO"),
        ("REPETICION_SIN_APRENDIZAJE", "Servicio similar previo sin implementación", "GRAVE"),
        ("DESACOPLE_ACTIVIDAD", "Sin relación con actividad preponderante", "GRAVE"),
        ("SOLO_BENEFICIO_FISCAL", "Único beneficio identificable es fiscal", "GRAVE"),
        ("BEE_NO_CUANTIFICABLE", "Beneficio no cuantificable ni describible", "GRAVE"),
    ]
    
    def evaluar_sib(self, sib: FormularioSIB) -> DictamenA1:
        """Evalúa un formulario SIB y genera dictamen A1"""
        
        score = self._calcular_score(sib)
        
        red_flags = self._detectar_red_flags(sib)
        
        estado = self._determinar_estado(score.total, red_flags)
        recomendacion = self._determinar_recomendacion(estado, red_flags)
        
        rn_solidez = self._evaluar_solidez_rn(sib, score)
        
        observaciones, areas_mejora = self._generar_observaciones(sib, score, red_flags)
        
        return DictamenA1(
            proyecto_id=sib.nombre_proyecto,
            razon_negocios_identificada=sib.objetivo_principal,
            razon_negocios_solidez=rn_solidez,
            bee_tipo=sib.tipo_beneficio,
            bee_descripcion=sib.descripcion_beneficio,
            bee_mecanismo=sib.mecanismo_causa_efecto,
            bee_horizonte_meses=sib.horizonte_meses,
            score=score,
            red_flags=red_flags,
            estado=estado,
            recomendacion_f2=recomendacion,
            observaciones=observaciones,
            areas_mejora=areas_mejora
        )
    
    def _calcular_score(self, sib: FormularioSIB) -> ScoreDetalleA1:
        """Calculate detailed A1 score"""
        
        sustancia = 0
        if sib.tipo_beneficio != TipoBeneficio.CUMPLIMIENTO:
            sustancia += 2
        if sib.mecanismo_causa_efecto and len(sib.mecanismo_causa_efecto) > 50:
            sustancia += 2
        if sib.monto_estimado > 0:
            sustancia += 1
        
        proposito = 0
        if sib.objetivo_principal and len(sib.objetivo_principal) > 20:
            proposito += 2
        if sib.problema_a_resolver and len(sib.problema_a_resolver) > 20:
            proposito += 2
        if sib.objetivos_secundarios:
            proposito += 1
        
        coherencia = 0
        if sib.vinculacion.pilar_estrategico:
            coherencia += 2
        if sib.vinculacion.okr_relacionado:
            coherencia += 2
        if sib.vinculacion.iniciativa_origen:
            coherencia += 1
        
        bee = 0
        if sib.descripcion_beneficio and len(sib.descripcion_beneficio) > 30:
            bee += 2
        if sib.mecanismo_causa_efecto and len(sib.mecanismo_causa_efecto) > 30:
            bee += 2
        if sib.kpis and len(sib.kpis) >= 1:
            bee += 1
        
        doc = 0
        if sib.fecha_solicitud:
            doc += 2
        if sib.solicitante:
            doc += 1
        if sib.area_solicitante:
            doc += 1
        if sib.supuestos:
            doc += 1
        
        total = sustancia + proposito + coherencia + bee + doc
        
        return ScoreDetalleA1(
            sustancia_economica=min(sustancia, 5),
            proposito_concreto=min(proposito, 5),
            coherencia_estrategica=min(coherencia, 5),
            bee_describible=min(bee, 5),
            documentacion_contemporanea=min(doc, 5),
            total=min(total, 25)
        )
    
    def _detectar_red_flags(self, sib: FormularioSIB) -> List[RedFlagA1]:
        """Detect red flags in SIB"""
        flags = []
        
        vague_words = ["mejorar", "optimizar", "general", "varios", "apoyar"]
        if any(w in sib.objetivo_principal.lower() for w in vague_words):
            if len(sib.objetivo_principal) < 50:
                flags.append(RedFlagA1(
                    codigo="OBJETIVO_VAGO",
                    descripcion="Objetivo demasiado vago o genérico",
                    severidad="GRAVE",
                    detectado=True
                ))
        
        if not sib.kpis or len(sib.kpis) == 0:
            flags.append(RedFlagA1(
                codigo="SIN_KPIS",
                descripcion="Sin KPIs medibles definidos",
                severidad="MODERADO",
                detectado=True
            ))
        
        if not sib.vinculacion.pilar_estrategico and not sib.vinculacion.okr_relacionado:
            flags.append(RedFlagA1(
                codigo="SIN_VINCULACION_ESTRATEGICA",
                descripcion="Sin conexión con pilares/OKRs",
                severidad="MODERADO",
                detectado=True
            ))
        
        if sib.fecha_solicitud and sib.fecha_solicitud.month == 12:
            flags.append(RedFlagA1(
                codigo="TIMING_SOSPECHOSO",
                descripcion="Contratación en fechas atípicas (diciembre)",
                severidad="MODERADO",
                detectado=True
            ))
        
        return flags
    
    def _determinar_estado(self, score: int, flags: List[RedFlagA1]) -> EstadoA1:
        """Determine A1 state from score and flags"""
        grave_flags = [f for f in flags if f.severidad == "GRAVE" and f.detectado]
        
        if grave_flags or score < 12:
            return EstadoA1.NO_CONFORME
        elif score >= 18:
            return EstadoA1.CONFORME
        else:
            return EstadoA1.CONDICIONADA
    
    def _determinar_recomendacion(self, estado: EstadoA1, flags: List[RedFlagA1]) -> RecomendacionF2:
        """Determine F2 recommendation"""
        if estado == EstadoA1.NO_CONFORME:
            return RecomendacionF2.NO_AVANZAR
        elif estado == EstadoA1.CONFORME:
            return RecomendacionF2.AVANZAR
        else:
            return RecomendacionF2.REPLANTEAR
    
    def _evaluar_solidez_rn(self, sib: FormularioSIB, score: ScoreDetalleA1) -> str:
        """Evaluate business reason strength"""
        if score.total >= 20:
            return "FUERTE"
        elif score.total >= 15:
            return "MODERADA"
        elif score.total >= 10:
            return "DEBIL"
        else:
            return "INEXISTENTE"
    
    def _generar_observaciones(self, sib: FormularioSIB, score: ScoreDetalleA1, 
                                flags: List[RedFlagA1]) -> tuple:
        """Generate observations and improvement areas"""
        obs_parts = []
        areas = []
        
        if score.sustancia_economica < 3:
            obs_parts.append("La sustancia económica del proyecto requiere mayor clarificación.")
            areas.append("Detallar el beneficio económico esperado más allá del cumplimiento")
        
        if score.proposito_concreto < 3:
            obs_parts.append("El propósito del proyecto no está suficientemente definido.")
            areas.append("Reformular objetivos con métricas específicas")
        
        if score.coherencia_estrategica < 3:
            obs_parts.append("No se identifica clara alineación estratégica.")
            areas.append("Vincular con OKRs o pilares estratégicos de la empresa")
        
        if score.bee_describible < 3:
            obs_parts.append("El mecanismo de generación de valor no es claro.")
            areas.append("Describir cómo el servicio genera el beneficio esperado")
        
        detected_flags = [f for f in flags if f.detectado]
        if detected_flags:
            obs_parts.append(f"Se detectaron {len(detected_flags)} señales de alerta.")
        
        observaciones = " ".join(obs_parts) if obs_parts else "Proyecto con documentación adecuada."
        
        return observaciones, areas
