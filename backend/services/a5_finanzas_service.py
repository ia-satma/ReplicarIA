from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum

class CalidadModelo(str, Enum):
    ALTA = "ALTA"
    MEDIA = "MEDIA"
    BAJA = "BAJA"

class RecomendacionA5(str, Enum):
    APROBAR = "APROBAR"
    APROBAR_CON_RESERVAS = "APROBAR_CON_RESERVAS"
    NO_APROBAR = "NO_APROBAR"

class ScoreDetalleA5(BaseModel):
    roi_razonabilidad: int = Field(ge=0, le=5)
    npv_positivo: int = Field(ge=0, le=5)
    payback_aceptable: int = Field(ge=0, le=5)
    bee_cuantificable: int = Field(ge=0, le=5)
    precio_mercado: int = Field(ge=0, le=5)
    total: int = Field(ge=0, le=25)

class AnalisisFinanciero(BaseModel):
    inversion: float
    beneficios_esperados: float
    horizonte_meses: int
    wacc: float = 0.10  # Default 10%

class MetricasCalculadas(BaseModel):
    roi: float
    npv: float
    payback_meses: float
    beneficio_neto: float

class DictamenA5(BaseModel):
    proyecto_id: str
    
    # Input data
    analisis: AnalisisFinanciero
    
    # Calculated metrics
    metricas: MetricasCalculadas
    
    # Evaluation
    roi_razonable: bool
    npv_positivo: bool
    payback_aceptable: bool
    precio_de_mercado: bool
    
    # Score
    score: ScoreDetalleA5
    
    # Quality and recommendation
    calidad_modelo: CalidadModelo
    recomendacion: RecomendacionA5
    justificacion: str
    
    # Metadata
    fecha_dictamen: datetime = Field(default_factory=datetime.utcnow)


class A5FinanzasService:
    """Service for A5_FINANZAS financial analysis"""
    
    # Thresholds
    ROI_MINIMO = 0.15  # 15% minimum acceptable ROI
    PAYBACK_MAXIMO_MESES = 24  # 2 years max payback
    
    def evaluar_proyecto(
        self,
        proyecto_id: str,
        inversion: float,
        beneficios_esperados: float,
        horizonte_meses: int,
        dictamen_a1: Optional[Dict[str, Any]] = None,
        wacc: float = 0.10
    ) -> DictamenA5:
        """Complete financial evaluation"""
        
        analisis = AnalisisFinanciero(
            inversion=inversion,
            beneficios_esperados=beneficios_esperados,
            horizonte_meses=horizonte_meses,
            wacc=wacc
        )
        
        # Calculate metrics
        metricas = self._calcular_metricas(analisis)
        
        # Evaluate against thresholds
        roi_razonable = metricas.roi >= self.ROI_MINIMO
        npv_positivo = metricas.npv > 0
        payback_aceptable = metricas.payback_meses <= self.PAYBACK_MAXIMO_MESES
        
        # Check price reasonability (simplified - would need market data)
        precio_de_mercado = True  # Default assumption
        
        # Calculate score
        score = self._calcular_score(
            roi_razonable, npv_positivo, payback_aceptable, 
            precio_de_mercado, dictamen_a1
        )
        
        # Determine quality and recommendation
        calidad = self._evaluar_calidad_modelo(dictamen_a1, analisis)
        recomendacion = self._determinar_recomendacion(score.total, calidad)
        justificacion = self._generar_justificacion(metricas, score, recomendacion)
        
        return DictamenA5(
            proyecto_id=proyecto_id,
            analisis=analisis,
            metricas=metricas,
            roi_razonable=roi_razonable,
            npv_positivo=npv_positivo,
            payback_aceptable=payback_aceptable,
            precio_de_mercado=precio_de_mercado,
            score=score,
            calidad_modelo=calidad,
            recomendacion=recomendacion,
            justificacion=justificacion
        )
    
    def _calcular_metricas(self, analisis: AnalisisFinanciero) -> MetricasCalculadas:
        """Calculate financial metrics"""
        
        # ROI = (Beneficios - Inversión) / Inversión
        beneficio_neto = analisis.beneficios_esperados - analisis.inversion
        roi = beneficio_neto / analisis.inversion if analisis.inversion > 0 else 0
        
        # NPV simplified (single cash flow at end of horizon)
        # NPV = -Inversión + Beneficios / (1 + WACC)^(horizonte/12)
        years = analisis.horizonte_meses / 12
        discount_factor = (1 + analisis.wacc) ** years
        npv = -analisis.inversion + (analisis.beneficios_esperados / discount_factor)
        
        # Payback simplified
        if beneficio_neto > 0:
            monthly_benefit = beneficio_neto / analisis.horizonte_meses
            if monthly_benefit > 0:
                payback_meses = analisis.inversion / (analisis.beneficios_esperados / analisis.horizonte_meses)
            else:
                payback_meses = float('inf')
        else:
            payback_meses = float('inf')
        
        return MetricasCalculadas(
            roi=round(roi, 4),
            npv=round(npv, 2),
            payback_meses=round(min(payback_meses, 999), 1),
            beneficio_neto=round(beneficio_neto, 2)
        )
    
    def _calcular_score(
        self,
        roi_ok: bool,
        npv_ok: bool,
        payback_ok: bool,
        precio_ok: bool,
        dictamen_a1: Optional[Dict[str, Any]]
    ) -> ScoreDetalleA5:
        """Calculate A5 score"""
        
        roi_score = 5 if roi_ok else 2
        npv_score = 5 if npv_ok else 0
        payback_score = 5 if payback_ok else 2
        precio_score = 5 if precio_ok else 3
        
        # BEE cuantificable - from A1
        bee_score = 3  # Default
        if dictamen_a1:
            bee_describible = dictamen_a1.get('score', {}).get('bee_describible', 0)
            if bee_describible >= 4:
                bee_score = 5
            elif bee_describible >= 2:
                bee_score = 3
            else:
                bee_score = 1
        
        total = roi_score + npv_score + payback_score + precio_score + bee_score
        
        return ScoreDetalleA5(
            roi_razonabilidad=roi_score,
            npv_positivo=npv_score,
            payback_aceptable=payback_score,
            bee_cuantificable=bee_score,
            precio_mercado=precio_score,
            total=min(total, 25)
        )
    
    def _evaluar_calidad_modelo(
        self, 
        dictamen_a1: Optional[Dict[str, Any]],
        analisis: AnalisisFinanciero
    ) -> CalidadModelo:
        """Evaluate quality of financial model inputs"""
        
        # Check if A1 provided good BEE description
        if dictamen_a1:
            bee_score = dictamen_a1.get('score', {}).get('bee_describible', 0)
            if bee_score >= 4:
                return CalidadModelo.ALTA
            elif bee_score >= 2:
                return CalidadModelo.MEDIA
        
        # Check if numbers make sense
        if analisis.beneficios_esperados > analisis.inversion * 0.5:
            return CalidadModelo.MEDIA
        
        return CalidadModelo.BAJA
    
    def _determinar_recomendacion(self, score: int, calidad: CalidadModelo) -> RecomendacionA5:
        """Determine recommendation"""
        if score >= 20 and calidad in [CalidadModelo.ALTA, CalidadModelo.MEDIA]:
            return RecomendacionA5.APROBAR
        elif score >= 15:
            return RecomendacionA5.APROBAR_CON_RESERVAS
        else:
            return RecomendacionA5.NO_APROBAR
    
    def _generar_justificacion(
        self, 
        metricas: MetricasCalculadas, 
        score: ScoreDetalleA5,
        recomendacion: RecomendacionA5
    ) -> str:
        """Generate justification text"""
        return f"""
Score A5: {score.total}/25
ROI: {metricas.roi:.1%} {'✓' if score.roi_razonabilidad >= 4 else '⚠'}
NPV: ${metricas.npv:,.0f} MXN {'✓' if metricas.npv > 0 else '✗'}
Payback: {metricas.payback_meses:.1f} meses {'✓' if score.payback_aceptable >= 4 else '⚠'}
Beneficio neto: ${metricas.beneficio_neto:,.0f} MXN

Recomendación: {recomendacion.value}
"""
