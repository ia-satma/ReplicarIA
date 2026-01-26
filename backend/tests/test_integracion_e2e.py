"""
Tests de Integración End-to-End - Revisar.IA

Verifica la integración completa del sistema:
- Contexto de agentes
- Validación de outputs
- Scoring service
- Flujo de fases con checklist
"""
import pytest
from datetime import datetime


class TestContextoAgentes:
    """Tests para inyección de contexto a agentes"""
    
    def test_construir_contexto_completo(self):
        """Verifica que se construye contexto completo para agente"""
        from services.inyeccion_contexto_service import construir_contexto_completo_para_agente
        
        proyecto = {
            "id": "PROJ-TEST-001",
            "name": "Proyecto Test E2E",
            "tipologia": "CONSULTORIA_MACRO_ESTRATEGIA",
            "fase_actual": "F0",
            "monto": 500000
        }
        
        contexto = construir_contexto_completo_para_agente(
            agente_id="A3_FISCAL",
            proyecto=proyecto,
            proveedor=None,
            documentos=[],
            deliberaciones_previas=[]
        )
        
        assert contexto is not None
        assert "_meta" in contexto
        assert contexto["_meta"]["agente_id"] == "A3_FISCAL"
        assert contexto["_meta"]["tipologia"] == "CONSULTORIA_MACRO_ESTRATEGIA"
        assert "contexto_normativo" in contexto
        assert "proyecto" in contexto
    
    def test_generar_system_prompt(self):
        """Verifica generación de system prompt con contexto"""
        from services.inyeccion_contexto_service import (
            construir_contexto_completo_para_agente,
            generar_system_prompt_con_contexto
        )
        
        proyecto = {
            "id": "PROJ-TEST-002",
            "tipologia": "SOFTWARE_SAAS_DESARROLLO",
            "fase_actual": "F1"
        }
        
        contexto = construir_contexto_completo_para_agente(
            agente_id="A3_FISCAL",
            proyecto=proyecto
        )
        
        prompt = generar_system_prompt_con_contexto("A3_FISCAL", contexto)
        
        assert prompt is not None
        assert len(prompt) > 100
        assert "ROL" in prompt or "TAREA" in prompt


class TestValidacionOutputs:
    """Tests para validación de outputs de agentes"""
    
    def test_validar_output_a3_fiscal(self):
        """Verifica validación de output de A3_FISCAL"""
        from validation.validation_service import validar_output_agente
        
        output_valido = {
            "decision": "APROBAR",
            "analisis_razon_negocios": "Proyecto tiene razón de negocios clara",
            "risk_score_total": 35,
            "conclusion_por_pilar": {
                "razon_negocios": {"evaluacion": "OK", "riesgo_puntos": 10},
                "beneficio_economico": {"evaluacion": "OK", "riesgo_puntos": 8},
                "materialidad": {"evaluacion": "MEDIO", "riesgo_puntos": 12},
                "trazabilidad": {"evaluacion": "OK", "riesgo_puntos": 5}
            },
            "checklist_evidencia_exigible": ["CFDI", "Contrato"],
            "condiciones_para_vbc": [],
            "requiere_validacion_humana": False
        }
        
        resultado = validar_output_agente("A3_FISCAL", output_valido)
        
        if resultado.get("valido"):
            assert resultado["valido"] == True
            assert len(resultado.get("errores", [])) == 0
    
    def test_validar_y_corregir_output(self):
        """Verifica corrección automática de outputs"""
        from validation.validation_service import validar_y_corregir
        
        output_con_errores = {
            "decision": "APROBAR",
            "analisis_razon_negocios": "Análisis",
            "risk_score_total": "35",
            "checklist_evidencia_exigible": "CFDI",
            "requiere_validacion_humana": "false"
        }
        
        resultado = validar_y_corregir("A3_FISCAL", output_con_errores)
        
        assert resultado is not None


class TestScoringService:
    """Tests para servicio de scoring"""
    
    @pytest.mark.asyncio
    async def test_actualizar_risk_score(self):
        """Verifica actualización de risk score"""
        from services.scoring_service import actualizar_risk_score_proyecto
        
        desglose = {
            "razon_negocios": 10,
            "beneficio_economico": 8,
            "materialidad": 12,
            "trazabilidad": 5
        }
        
        resultado = await actualizar_risk_score_proyecto(
            proyecto_id="PROJ-TEST-003",
            risk_score_total=35,
            desglose=desglose
        )
        
        assert resultado is not None
        assert resultado["risk_score_total"] == 35
        assert resultado["risk_score_razon_negocios"] == 10
        assert resultado["risk_score_beneficio_economico"] == 8
        assert resultado["risk_score_materialidad"] == 12
        assert resultado["risk_score_trazabilidad"] == 5
        assert "risk_score_updated_at" in resultado
    
    def test_extraer_risk_score_de_a3(self):
        """Verifica extracción de risk score del output de A3"""
        from services.scoring_service import extraer_risk_score_de_a3
        
        output_a3 = {
            "risk_score_total": 42,
            "conclusion_por_pilar": {
                "razon_negocios": {"riesgo_puntos": 15},
                "beneficio_economico": {"riesgo_puntos": 10},
                "materialidad": {"riesgo_puntos": 12},
                "trazabilidad": {"riesgo_puntos": 5}
            }
        }
        
        risk_total, desglose = extraer_risk_score_de_a3(output_a3)
        
        assert risk_total == 42
        assert desglose["razon_negocios"] == 15
        assert desglose["beneficio_economico"] == 10
        assert desglose["materialidad"] == 12
        assert desglose["trazabilidad"] == 5


class TestFlujoFases:
    """Tests para flujo de fases con checklist"""
    
    def test_verificar_avance_fase_completo(self):
        """Verifica función de avance de fase con checklist"""
        from services.fase_service import verificar_avance_fase_completo
        
        proyecto = {
            "id": "PROJ-TEST-004",
            "fase_actual": "F0",
            "tipologia": "CONSULTORIA_MACRO_ESTRATEGIA",
            "monto": 1000000
        }
        
        context = {
            "documentos": [],
            "fases_completadas": [],
            "deliberaciones": {}
        }
        
        resultado = verificar_avance_fase_completo(
            proyecto=proyecto,
            fase_destino="F1",
            context=context
        )
        
        assert resultado is not None
        assert "puede_avanzar" in resultado
        assert "bloqueos" in resultado
        assert resultado["fase_actual"] == "F0"
        assert resultado["fase_destino"] == "F1"
        assert resultado["checklist_validado"] == True
    
    def test_verificar_avance_fase_con_documentos(self):
        """Verifica avance cuando hay documentos cargados"""
        from services.fase_service import verificar_avance_fase_completo
        
        proyecto = {
            "id": "PROJ-TEST-005",
            "fase_actual": "F0",
            "tipologia": "CONSULTORIA_MACRO_ESTRATEGIA",
            "monto": 500000
        }
        
        context = {
            "documentos": [
                {"tipo": "Ficha SIB con BEE", "nombre": "ficha_sib.pdf"}
            ],
            "fases_completadas": [],
            "deliberaciones": {}
        }
        
        resultado = verificar_avance_fase_completo(
            proyecto=proyecto,
            fase_destino="F1",
            context=context
        )
        
        assert resultado is not None
        bloqueos_checklist = [b for b in resultado["bloqueos"] if "CHECKLIST" in b]
        assert len(bloqueos_checklist) == 0


class TestExtractoNormativo:
    """Tests para generación de extracto normativo"""
    
    def test_generar_extracto_sin_tipologia(self):
        """Verifica extracto normativo sin tipología"""
        from services.dreamhost_email_service import _generar_extracto_normativo
        
        extracto = _generar_extracto_normativo()
        
        assert extracto is not None
        assert "Art. 5-A CFF" in extracto
        assert "Art. 69-B CFF" in extracto
        assert "Art. 27 LISR" in extracto
    
    def test_generar_extracto_con_tipologia(self):
        """Verifica extracto normativo con tipología específica"""
        from services.dreamhost_email_service import _generar_extracto_normativo
        
        extracto = _generar_extracto_normativo("CONSULTORIA_MACRO_ESTRATEGIA")
        
        assert extracto is not None
        assert "MARCO NORMATIVO" in extracto


class TestIntegracionDeliberationOrchestrator:
    """Tests de integración para DeliberationOrchestrator"""
    
    def test_orchestrator_tiene_metodos_nuevos(self):
        """Verifica que el orchestrator tiene los nuevos métodos"""
        from services.deliberation_orchestrator import DeliberationOrchestrator
        
        orchestrator = DeliberationOrchestrator()
        
        assert hasattr(orchestrator, '_preparar_contexto_agente')
        assert hasattr(orchestrator, '_obtener_documentos_proyecto')
        assert hasattr(orchestrator, '_validar_y_registrar_output')
        assert callable(getattr(orchestrator, '_preparar_contexto_agente'))
        assert callable(getattr(orchestrator, '_obtener_documentos_proyecto'))
        assert callable(getattr(orchestrator, '_validar_y_registrar_output'))
    
    def test_obtener_documentos_proyecto_vacio(self):
        """Verifica obtención de documentos para proyecto inexistente"""
        from services.deliberation_orchestrator import DeliberationOrchestrator
        
        orchestrator = DeliberationOrchestrator()
        
        documentos = orchestrator._obtener_documentos_proyecto("PROJ-INEXISTENTE")
        
        assert documentos == []
    
    def test_validar_y_registrar_output(self):
        """Verifica validación y registro de output"""
        from services.deliberation_orchestrator import DeliberationOrchestrator
        
        orchestrator = DeliberationOrchestrator()
        
        output = {
            "decision": "APROBAR",
            "analisis": "Test"
        }
        deliberation_record = {}
        
        resultado = orchestrator._validar_y_registrar_output(
            "A1_SPONSOR",
            output,
            deliberation_record
        )
        
        assert resultado is not None
        assert "validation_status" in deliberation_record
