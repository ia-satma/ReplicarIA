from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum

class CumplimientoLISR27(str, Enum):
    CUMPLE = "CUMPLE"
    CUMPLE_CON_OBSERVACIONES = "CUMPLE_CON_OBSERVACIONES"
    NO_CUMPLE = "NO_CUMPLE"

class RecomendacionA3(str, Enum):
    APROBAR = "APROBAR"
    APROBAR_CON_EXCEPCION = "APROBAR_CON_EXCEPCION"
    NO_APROBAR = "NO_APROBAR"

class ScoreDetalleA3(BaseModel):
    estricta_indispensabilidad: int = Field(ge=0, le=25)  # LISR 27-I
    documentacion_cfdi: int = Field(ge=0, le=25)          # LISR 27-III
    bancarizacion: int = Field(ge=0, le=15)               # LISR 27-III
    registro_contable: int = Field(ge=0, le=10)           # LISR 27-IV
    riesgo_efos: int = Field(ge=0, le=25)                 # CFF 69-B
    total: int = Field(ge=0, le=100)

class ObservacionFiscal(BaseModel):
    codigo: str
    descripcion: str
    severidad: str  # BLOQUEANTE, ALTA, MEDIA, BAJA
    recomendacion: str

class DictamenA3(BaseModel):
    proyecto_id: str
    
    # Análisis LISR 27
    cumplimiento_lisr27: CumplimientoLISR27
    fracciones_evaluadas: List[str] = []  # I, III, IV, V, XVIII, XIX
    
    # Análisis CFDI
    cfdi_concepto_especifico: bool = False
    cfdi_uso_correcto: bool = False
    cfdi_monto_coincide: bool = False
    
    # Análisis 69-B
    proveedor_limpio_69b: bool = True
    riesgo_efos: str = "BAJO"  # BAJO, MEDIO, ALTO, CRITICO
    
    # Materialidad
    materialidad_suficiente: bool = False
    porcentaje_materialidad: int = Field(ge=0, le=100, default=0)
    
    # Scoring
    score: ScoreDetalleA3
    
    # Observaciones
    observaciones: List[ObservacionFiscal] = []
    
    # Estado y recomendación
    recomendacion_f6: RecomendacionA3
    dictamen_deducibilidad: str
    
    # Metadata
    fecha_dictamen: datetime = Field(default_factory=datetime.utcnow)


class A3FiscalService:
    """Service for A3_FISCAL deducibility analysis"""
    
    def evaluar_proyecto(
        self,
        proyecto_id: str,
        dictamen_a1: Optional[Dict[str, Any]] = None,
        dictamen_a6: Optional[Dict[str, Any]] = None,
        cfdi_data: Optional[Dict[str, Any]] = None,
        evidencias: Optional[List[Dict[str, Any]]] = None
    ) -> DictamenA3:
        """Complete fiscal evaluation for F6"""
        
        # Calculate score
        score = self._calcular_score(dictamen_a1, dictamen_a6, cfdi_data, evidencias)
        
        # Evaluate LISR 27 compliance
        cumplimiento = self._evaluar_lisr27(score)
        
        # Generate observations
        observaciones = self._generar_observaciones(dictamen_a1, dictamen_a6, cfdi_data, evidencias)
        
        # Determine recommendation
        recomendacion = self._determinar_recomendacion(score.total, observaciones)
        
        # Generate deducibility dictamen
        dictamen_ded = self._generar_dictamen_deducibilidad(score, observaciones, recomendacion)
        
        # Check 69-B risk from A6
        riesgo_efos = "BAJO"
        proveedor_limpio = True
        if dictamen_a6:
            nivel_riesgo = dictamen_a6.get('nivel_riesgo', 'BAJO')
            if nivel_riesgo in ['ALTO', 'CRITICO']:
                riesgo_efos = nivel_riesgo
                proveedor_limpio = False
        
        # Calculate materiality percentage
        pct_materialidad = 0
        if evidencias:
            requeridas = 5  # Minimum required evidences
            presentes = len([e for e in evidencias if e.get('verificado', False)])
            pct_materialidad = min(100, int((presentes / requeridas) * 100))
        
        return DictamenA3(
            proyecto_id=proyecto_id,
            cumplimiento_lisr27=cumplimiento,
            fracciones_evaluadas=["I", "III", "IV"],
            cfdi_concepto_especifico=cfdi_data.get('concepto_especifico', False) if cfdi_data else False,
            cfdi_uso_correcto=cfdi_data.get('uso_correcto', False) if cfdi_data else False,
            cfdi_monto_coincide=cfdi_data.get('monto_coincide', False) if cfdi_data else False,
            proveedor_limpio_69b=proveedor_limpio,
            riesgo_efos=riesgo_efos,
            materialidad_suficiente=pct_materialidad >= 70,
            porcentaje_materialidad=pct_materialidad,
            score=score,
            observaciones=observaciones,
            recomendacion_f6=recomendacion,
            dictamen_deducibilidad=dictamen_ded
        )
    
    def _calcular_score(
        self,
        dictamen_a1: Optional[Dict[str, Any]],
        dictamen_a6: Optional[Dict[str, Any]],
        cfdi_data: Optional[Dict[str, Any]],
        evidencias: Optional[List[Dict[str, Any]]]
    ) -> ScoreDetalleA3:
        """Calculate detailed fiscal score"""
        
        # Estricta indispensabilidad (0-25) - from A1
        indispensabilidad = 0
        if dictamen_a1:
            estado_a1 = dictamen_a1.get('estado', '')
            if estado_a1 == 'CONFORME':
                indispensabilidad = 25
            elif estado_a1 == 'CONDICIONADA':
                indispensabilidad = 15
            else:
                indispensabilidad = 5
        
        # CFDI documentation (0-25)
        cfdi_score = 0
        if cfdi_data:
            if cfdi_data.get('concepto_especifico', False):
                cfdi_score += 10
            if cfdi_data.get('uso_correcto', False):
                cfdi_score += 8
            if cfdi_data.get('monto_coincide', False):
                cfdi_score += 7
        
        # Bancarización (0-15)
        bancarizacion = 0
        if cfdi_data and cfdi_data.get('pago_bancarizado', False):
            bancarizacion = 15
        
        # Registro contable (0-10)
        registro = 0
        if evidencias:
            tiene_poliza = any(e.get('tipo') == 'POLIZA_CONTABLE' for e in evidencias)
            if tiene_poliza:
                registro = 10
        
        # Riesgo EFOS (0-25) - from A6
        efos_score = 25  # Default: clean
        if dictamen_a6:
            nivel = dictamen_a6.get('nivel_riesgo', 'BAJO')
            if nivel == 'BAJO':
                efos_score = 25
            elif nivel in ['MEDIO_BAJO', 'MEDIO']:
                efos_score = 15
            elif nivel == 'MEDIO_ALTO':
                efos_score = 10
            elif nivel == 'ALTO':
                efos_score = 5
            else:  # CRITICO
                efos_score = 0
        
        total = indispensabilidad + cfdi_score + bancarizacion + registro + efos_score
        
        return ScoreDetalleA3(
            estricta_indispensabilidad=indispensabilidad,
            documentacion_cfdi=cfdi_score,
            bancarizacion=bancarizacion,
            registro_contable=registro,
            riesgo_efos=efos_score,
            total=min(total, 100)
        )
    
    def _evaluar_lisr27(self, score: ScoreDetalleA3) -> CumplimientoLISR27:
        """Evaluate LISR 27 compliance"""
        if score.total >= 80:
            return CumplimientoLISR27.CUMPLE
        elif score.total >= 60:
            return CumplimientoLISR27.CUMPLE_CON_OBSERVACIONES
        else:
            return CumplimientoLISR27.NO_CUMPLE
    
    def _generar_observaciones(
        self,
        dictamen_a1: Optional[Dict[str, Any]],
        dictamen_a6: Optional[Dict[str, Any]],
        cfdi_data: Optional[Dict[str, Any]],
        evidencias: Optional[List[Dict[str, Any]]]
    ) -> List[ObservacionFiscal]:
        """Generate fiscal observations"""
        obs = []
        
        # Check A1 state
        if dictamen_a1 and dictamen_a1.get('estado') == 'NO_CONFORME':
            obs.append(ObservacionFiscal(
                codigo="A1_NO_CONFORME",
                descripcion="Razón de negocios no conforme según A1",
                severidad="BLOQUEANTE",
                recomendacion="Replantear proyecto o documentar excepción"
            ))
        
        # Check CFDI
        if cfdi_data:
            if not cfdi_data.get('concepto_especifico', False):
                obs.append(ObservacionFiscal(
                    codigo="CFDI_GENERICO",
                    descripcion="Concepto en CFDI es genérico",
                    severidad="ALTA",
                    recomendacion="Solicitar CFDI con concepto específico que refleje el servicio"
                ))
        
        # Check 69-B
        if dictamen_a6:
            if dictamen_a6.get('estatus_69b') == 'DEFINITIVO':
                obs.append(ObservacionFiscal(
                    codigo="PROVEEDOR_EFOS_DEFINITIVO",
                    descripcion="Proveedor en lista 69-B definitiva",
                    severidad="BLOQUEANTE",
                    recomendacion="No procede la deducción. Evaluar autocorrección."
                ))
        
        return obs
    
    def _determinar_recomendacion(self, score: int, observaciones: List[ObservacionFiscal]) -> RecomendacionA3:
        """Determine F6 recommendation"""
        bloqueantes = [o for o in observaciones if o.severidad == "BLOQUEANTE"]
        
        if bloqueantes:
            return RecomendacionA3.NO_APROBAR
        elif score >= 80:
            return RecomendacionA3.APROBAR
        elif score >= 60:
            return RecomendacionA3.APROBAR_CON_EXCEPCION
        else:
            return RecomendacionA3.NO_APROBAR
    
    def _generar_dictamen_deducibilidad(
        self, 
        score: ScoreDetalleA3, 
        observaciones: List[ObservacionFiscal],
        recomendacion: RecomendacionA3
    ) -> str:
        """Generate deducibility dictamen text"""
        if recomendacion == RecomendacionA3.APROBAR:
            return f"Deducción procedente. Score {score.total}/100. Cumple requisitos LISR 27."
        elif recomendacion == RecomendacionA3.APROBAR_CON_EXCEPCION:
            obs_text = ", ".join([o.codigo for o in observaciones])
            return f"Deducción condicionada. Score {score.total}/100. Observaciones: {obs_text}"
        else:
            obs_text = ", ".join([o.codigo for o in observaciones if o.severidad == "BLOQUEANTE"])
            return f"Deducción NO procedente. Score {score.total}/100. Bloqueantes: {obs_text}"
