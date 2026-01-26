"""
Pruebas para el sistema de contexto requerido por agente
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config.contexto_requerido import (
    get_campos_obligatorios,
    get_campos_deseables,
    validar_contexto_completo,
    CONTEXTO_POR_AGENTE,
    get_contexto_requerido
)
from services.contexto_service import (
    preparar_contexto_para_agente,
    ContextoIncompleto,
    obtener_resumen_contexto_agente,
    listar_todos_agentes_contexto
)


class TestContextoRequerido:
    
    def test_todos_agentes_tienen_configuracion(self):
        """Todos los agentes deben tener configuración de contexto"""
        agentes_esperados = [
            "A1_SPONSOR", "A2_PMO", "A3_FISCAL", "A4_LEGAL", 
            "A5_FINANZAS", "A6_PROVEEDOR", "A7_DEFENSA", "A8_AUDITOR",
            "SUB_TIPIFICACION", "SUB_MATERIALIDAD", "SUB_RIESGOS_ESPECIALES"
        ]
        
        for agente in agentes_esperados:
            assert agente in CONTEXTO_POR_AGENTE
            assert "contexto_requerido" in CONTEXTO_POR_AGENTE[agente]
    
    def test_a3_fiscal_tiene_campos_criticos(self):
        """A3_FISCAL debe requerir campos fiscales críticos"""
        obligatorios = get_campos_obligatorios("A3_FISCAL")
        
        assert "proveedor.rfc" in obligatorios
        assert "proveedor.alerta_efos" in obligatorios
        assert "proyecto.tipologia" in obligatorios
    
    def test_a7_defensa_tiene_todos_risk_scores(self):
        """A7_DEFENSA debe requerir todos los risk scores por pilar"""
        obligatorios = get_campos_obligatorios("A7_DEFENSA")
        
        assert "proyecto.risk_score_total" in obligatorios
        assert "proyecto.risk_score_razon_negocios" in obligatorios
        assert "proyecto.risk_score_beneficio_economico" in obligatorios
        assert "proyecto.risk_score_materialidad" in obligatorios
        assert "proyecto.risk_score_trazabilidad" in obligatorios
    
    def test_validar_contexto_detecta_faltantes(self):
        """Debe detectar campos faltantes"""
        contexto_incompleto = {
            "proyecto": {"nombre": "Test"},
        }
        
        resultado = validar_contexto_completo("A3_FISCAL", contexto_incompleto)
        
        assert resultado["completo"] == False
        assert len(resultado["campos_faltantes"]) > 0
    
    def test_validar_contexto_completo_pasa(self):
        """Contexto completo debe pasar validación"""
        contexto_completo = {
            "proyecto": {
                "nombre": "Test",
                "descripcion": "Descripción",
                "monto": 1000000,
                "tipologia": "CONSULTORIA_ESTRATEGICA"
            },
            "proveedor": {
                "rfc": "TEST123456ABC",
                "tipo_relacion": "TERCERO_INDEPENDIENTE",
                "alerta_efos": False
            },
            "documentos": {
                "sib_bee": {"id": "doc1"},
                "contrato": {"id": "doc2"}
            }
        }
        
        resultado = validar_contexto_completo("A3_FISCAL", contexto_completo)
        
        assert resultado["completo"] == True
        assert resultado["porcentaje_completitud"] == 100
    
    def test_get_campos_deseables(self):
        """Debe retornar campos deseables"""
        deseables = get_campos_deseables("A3_FISCAL")
        
        assert len(deseables) > 0
        assert "proveedor.historial_operaciones" in deseables
    
    def test_get_contexto_requerido_agente_inexistente(self):
        """Debe retornar vacío para agente inexistente"""
        config = get_contexto_requerido("AGENTE_INEXISTENTE")
        
        assert config == {}


class TestContextoService:
    
    def test_obtener_resumen_contexto_agente(self):
        """Debe retornar resumen completo"""
        resumen = obtener_resumen_contexto_agente("A3_FISCAL")
        
        assert "agente_id" in resumen
        assert resumen["agente_id"] == "A3_FISCAL"
        assert "descripcion" in resumen
        assert "campos_obligatorios" in resumen
        assert "campos_deseables" in resumen
        assert "output_esperado" in resumen
    
    def test_listar_todos_agentes(self):
        """Debe listar todos los agentes con su contexto"""
        agentes = listar_todos_agentes_contexto()
        
        assert len(agentes) >= 10
        assert all("agente_id" in a for a in agentes)
    
    @pytest.mark.asyncio
    async def test_preparar_contexto_sin_validacion(self):
        """Debe preparar contexto sin validar obligatorios"""
        contexto = await preparar_contexto_para_agente(
            agente_id="A3_FISCAL",
            proyecto={"nombre": "Test"},
            validar_obligatorios=False
        )
        
        assert "_meta" in contexto
        assert contexto["_meta"]["agente_id"] == "A3_FISCAL"
    
    @pytest.mark.asyncio
    async def test_preparar_contexto_lanza_excepcion_si_incompleto(self):
        """Debe lanzar excepción si faltan campos obligatorios"""
        with pytest.raises(ContextoIncompleto) as excinfo:
            await preparar_contexto_para_agente(
                agente_id="A3_FISCAL",
                proyecto={"nombre": "Test"},
                validar_obligatorios=True
            )
        
        assert excinfo.value.agente_id == "A3_FISCAL"
        assert len(excinfo.value.campos_faltantes) > 0


class TestValidacionesEspeciales:
    
    def test_a3_fiscal_tiene_validaciones_especiales(self):
        """A3_FISCAL debe tener validaciones especiales definidas"""
        config = get_contexto_requerido("A3_FISCAL")
        
        assert "validaciones_especiales" in config
        assert "checklist_evidencia_exigible" in config["validaciones_especiales"]
    
    def test_cada_agente_tiene_output_esperado(self):
        """Cada agente debe tener output esperado definido"""
        for agente_id, config in CONTEXTO_POR_AGENTE.items():
            assert "output_esperado" in config, f"{agente_id} no tiene output_esperado"
            assert len(config["output_esperado"]) > 0, f"{agente_id} tiene output_esperado vacío"
