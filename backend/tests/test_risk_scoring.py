"""
Pruebas Unitarias: Risk Scoring - Revisar.IA
Verifica el cálculo objetivo del risk_score basado en 12 criterios
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from scoring.risk_scoring import calcular_risk_score
from scoring.few_shot_examples import FEW_SHOT_EXAMPLES


class TestRiskScoring:
    """Pruebas para el cálculo objetivo de risk_score"""
    
    def test_proyecto_bajo_riesgo_aprobar(self, evaluacion_bajo_riesgo):
        """Caso APROBAR: score ~16 puntos"""
        resultado = calcular_risk_score(evaluacion_bajo_riesgo)
        
        assert resultado["risk_score_total"] == 16
        assert resultado["risk_score_total"] < 40, "Proyecto bajo riesgo debe ser < 40"
        assert resultado["nivel_riesgo"] == "BAJO"
        assert resultado["requiere_revision_humana"] == False
    
    def test_proyecto_medio_riesgo_ajustes(self):
        """Caso SOLICITAR_AJUSTES: score ~58 puntos"""
        evaluacion = {
            "razon_negocios": {
                "vinculacion_giro": 3,
                "objetivo_economico": 5,
                "coherencia_monto": 5
            },
            "beneficio_economico": {
                "identificacion_beneficios": 5,
                "modelo_roi": 5,
                "horizonte_temporal": 3
            },
            "materialidad": {
                "formalizacion": 3,
                "evidencias_ejecucion": 10,
                "coherencia_documentos": 5
            },
            "trazabilidad": {
                "conservacion": 5,
                "integridad": 5,
                "timeline": 4
            }
        }
        
        resultado = calcular_risk_score(evaluacion)
        
        assert 40 <= resultado["risk_score_total"] < 70
        assert resultado["nivel_riesgo"] in ["MEDIO", "ALTO"]
    
    def test_proyecto_alto_riesgo_rechazar(self, evaluacion_alto_riesgo):
        """Caso RECHAZAR: score ~92 puntos"""
        resultado = calcular_risk_score(evaluacion_alto_riesgo)
        
        assert resultado["risk_score_total"] >= 80
        assert resultado["nivel_riesgo"] == "CRITICO"
        assert resultado["requiere_revision_humana"] == True
    
    def test_risk_score_por_pilar_max_25(self, evaluacion_alto_riesgo):
        """Cada pilar debe tener máximo 25 puntos"""
        resultado = calcular_risk_score(evaluacion_alto_riesgo)
        
        assert resultado["risk_score_razon_negocios"] <= 25
        assert resultado["risk_score_beneficio_economico"] <= 25
        assert resultado["risk_score_materialidad"] <= 25
        assert resultado["risk_score_trazabilidad"] <= 25
        assert resultado["risk_score_total"] <= 100
    
    def test_risk_score_minimo_cero(self):
        """Evaluación perfecta debe dar score 0"""
        evaluacion_perfecta = {
            "razon_negocios": {
                "vinculacion_giro": 0,
                "objetivo_economico": 0,
                "coherencia_monto": 0
            },
            "beneficio_economico": {
                "identificacion_beneficios": 0,
                "modelo_roi": 0,
                "horizonte_temporal": 0
            },
            "materialidad": {
                "formalizacion": 0,
                "evidencias_ejecucion": 0,
                "coherencia_documentos": 0
            },
            "trazabilidad": {
                "conservacion": 0,
                "integridad": 0,
                "timeline": 0
            }
        }
        
        resultado = calcular_risk_score(evaluacion_perfecta)
        
        assert resultado["risk_score_total"] == 0
        assert resultado["nivel_riesgo"] == "BAJO"
        assert resultado["requiere_revision_humana"] == False
    
    def test_umbral_revision_humana_60(self):
        """Score >= 60 debe requerir revisión humana"""
        evaluacion_limite = {
            "razon_negocios": {"vinculacion_giro": 5, "objetivo_economico": 5, "coherencia_monto": 5},
            "beneficio_economico": {"identificacion_beneficios": 5, "modelo_roi": 5, "horizonte_temporal": 5},
            "materialidad": {"formalizacion": 5, "evidencias_ejecucion": 5, "coherencia_documentos": 5},
            "trazabilidad": {"conservacion": 5, "integridad": 5, "timeline": 5}
        }
        
        resultado = calcular_risk_score(evaluacion_limite)
        
        assert resultado["risk_score_total"] == 60
        assert resultado["requiere_revision_humana"] == True
    
    def test_few_shot_examples_existen(self):
        """Verificar que existen los 3 casos modelo"""
        assert "APROBAR" in FEW_SHOT_EXAMPLES
        assert "SOLICITAR_AJUSTES" in FEW_SHOT_EXAMPLES
        assert "RECHAZAR" in FEW_SHOT_EXAMPLES
    
    def test_few_shot_aprobar_score_bajo(self):
        """Caso APROBAR debe tener score bajo"""
        caso = FEW_SHOT_EXAMPLES["APROBAR"]
        score = caso.get("risk_score", {}).get("total", 0)
        assert score < 40, f"Caso APROBAR debe tener score < 40, tiene {score}"
    
    def test_few_shot_rechazar_score_alto(self):
        """Caso RECHAZAR debe tener score alto"""
        caso = FEW_SHOT_EXAMPLES["RECHAZAR"]
        score = caso.get("risk_score", {}).get("total", 0)
        assert score >= 80, f"Caso RECHAZAR debe tener score >= 80, tiene {score}"
