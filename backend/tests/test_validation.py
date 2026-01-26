"""
Pruebas Unitarias: Validación de Outputs - Revisar.IA
Verifica los schemas de validación para outputs de agentes
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from pydantic import ValidationError
from validation.agent_schemas import (
    A3FiscalOutput,
    ChecklistEvidenciaItem,
    ConclusionPilar,
    ConclusionPorPilar,
    DecisionEnum,
    StatusPilarEnum,
    EstadoChecklistEnum
)
from validation.validation_service import (
    validar_output_agente,
    validar_y_corregir,
    calcular_completitud
)


class TestAgentSchemas:
    """Pruebas para schemas de agentes"""
    
    def test_conclusion_pilar_valida(self):
        """ConclusionPilar válida debe pasar"""
        pilar = ConclusionPilar(
            status=StatusPilarEnum.CONFORME,
            detalle="Este es un detalle suficientemente largo para pasar la validación mínima de 50 caracteres requerida por el schema.",
            riesgo_puntos=5
        )
        
        assert pilar.status == StatusPilarEnum.CONFORME
        assert pilar.riesgo_puntos == 5
    
    def test_conclusion_pilar_detalle_corto_falla(self):
        """ConclusionPilar con detalle < 50 chars debe fallar"""
        with pytest.raises(ValidationError) as excinfo:
            ConclusionPilar(
                status=StatusPilarEnum.CONFORME,
                detalle="Muy corto",  # < 50 chars
                riesgo_puntos=5
            )
        
        assert "detalle" in str(excinfo.value).lower()
    
    def test_conclusion_pilar_puntos_fuera_rango(self):
        """ConclusionPilar con puntos > 25 debe fallar"""
        with pytest.raises(ValidationError):
            ConclusionPilar(
                status=StatusPilarEnum.CONFORME,
                detalle="Este es un detalle suficientemente largo para la validación.",
                riesgo_puntos=30  # > 25
            )
    
    def test_checklist_item_valido(self):
        """ChecklistEvidenciaItem válido debe pasar"""
        item = ChecklistEvidenciaItem(
            item="Contrato firmado",
            obligatorio=True,
            estado=EstadoChecklistEnum.ENTREGADO,
            fase_requerida="F1"
        )
        
        assert item.obligatorio == True
        assert item.estado == EstadoChecklistEnum.ENTREGADO


class TestA3FiscalOutput:
    """Pruebas específicas para A3_FISCAL (el más crítico)"""
    
    def _crear_conclusion_pilar(self, status=StatusPilarEnum.CONFORME, puntos=5):
        """Helper para crear ConclusionPilar válida"""
        return {
            "status": status.value,
            "detalle": "Este es un detalle que supera los 50 caracteres requeridos por la validación del schema de Revisar.IA.",
            "riesgo_puntos": puntos
        }
    
    def _crear_checklist_item(self, item_name="Item Test"):
        """Helper para crear ChecklistEvidenciaItem válido"""
        return {
            "item": item_name,
            "obligatorio": True,
            "estado": "ENTREGADO",
            "fase_requerida": "F1"
        }
    
    def test_a3_fiscal_output_valido(self):
        """Output A3 válido debe pasar validación"""
        output = {
            "decision": "APROBAR",
            "conclusion_por_pilar": {
                "razon_negocios": self._crear_conclusion_pilar(),
                "beneficio_economico": self._crear_conclusion_pilar(),
                "materialidad": self._crear_conclusion_pilar(),
                "trazabilidad": self._crear_conclusion_pilar()
            },
            "risk_score_total": 20,
            "checklist_evidencia_exigible": [
                self._crear_checklist_item("SIB firmado"),
                self._crear_checklist_item("Contrato"),
                self._crear_checklist_item("Entregable")
            ],
            "alertas_riesgo_especial": [],
            "condiciones_para_vbc": [],
            "riesgos_subsistentes": [],
            "requiere_validacion_humana": False
        }
        
        resultado = A3FiscalOutput(**output)
        assert resultado.decision == DecisionEnum.APROBAR
        assert resultado.risk_score_total == 20
    
    def test_a3_fiscal_menos_de_3_checklist_falla(self):
        """Output A3 con menos de 3 items en checklist debe fallar"""
        output = {
            "decision": "APROBAR",
            "conclusion_por_pilar": {
                "razon_negocios": self._crear_conclusion_pilar(),
                "beneficio_economico": self._crear_conclusion_pilar(),
                "materialidad": self._crear_conclusion_pilar(),
                "trazabilidad": self._crear_conclusion_pilar()
            },
            "risk_score_total": 16,
            "checklist_evidencia_exigible": [
                self._crear_checklist_item("Item 1"),
                self._crear_checklist_item("Item 2")
                # Solo 2 items - debe fallar
            ],
            "requiere_validacion_humana": False
        }
        
        with pytest.raises(ValidationError) as excinfo:
            A3FiscalOutput(**output)
        
        assert "checklist_evidencia_exigible" in str(excinfo.value)
    
    def test_a3_fiscal_risk_score_fuera_rango(self):
        """Output A3 con risk_score > 100 debe fallar"""
        output = {
            "decision": "RECHAZAR",
            "conclusion_por_pilar": {
                "razon_negocios": self._crear_conclusion_pilar(),
                "beneficio_economico": self._crear_conclusion_pilar(),
                "materialidad": self._crear_conclusion_pilar(),
                "trazabilidad": self._crear_conclusion_pilar()
            },
            "risk_score_total": 150,  # > 100
            "checklist_evidencia_exigible": [
                self._crear_checklist_item("Item 1"),
                self._crear_checklist_item("Item 2"),
                self._crear_checklist_item("Item 3")
            ],
            "requiere_validacion_humana": True
        }
        
        with pytest.raises(ValidationError):
            A3FiscalOutput(**output)


class TestValidationService:
    """Pruebas para el servicio de validación"""
    
    def test_validar_y_corregir_string_a_numero(self):
        """validar_y_corregir debe convertir strings numéricos"""
        output = {
            "risk_score_total": "25",  # String en vez de int
            "requiere_validacion_humana": "true"  # String en vez de bool
        }
        
        resultado = validar_y_corregir("A3_FISCAL", output)
        
        # Verificar que se aplicaron correcciones
        assert "correcciones_aplicadas" in resultado
    
    def test_calcular_completitud_output_vacio(self):
        """Output vacío debe tener completitud baja"""
        output_vacio = {}
        
        resultado = calcular_completitud("A3_FISCAL", output_vacio)
        
        assert resultado["porcentaje_completitud"] == 0
    
    def test_calcular_completitud_output_completo(self):
        """Output completo debe tener completitud alta"""
        output_completo = {
            "decision": "APROBAR",
            "risk_score_total": 20,
            "conclusion_por_pilar": {"razon_negocios": {}, "beneficio_economico": {}, "materialidad": {}, "trazabilidad": {}},
            "checklist_evidencia_exigible": [1, 2, 3],
            "justificacion": "Proyecto cumple todos los criterios"
        }
        
        resultado = calcular_completitud("A3_FISCAL", output_completo)
        
        assert resultado["campos_llenos"] >= resultado["campos_totales"] // 2
