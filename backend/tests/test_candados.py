"""
Pruebas Unitarias: Candados Duros - Revisar.IA
Verifica los 3 candados duros F2, F6, F8
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from services.fase_service import (
    verificar_candado_f2,
    verificar_candado_f6,
    verificar_candado_f8,
    es_candado_duro,
    CANDADOS_DUROS
)


class TestCandadosConfig:
    """Pruebas de configuración de candados"""
    
    def test_candados_duros_definidos(self):
        """Deben existir exactamente 3 candados duros"""
        assert len(CANDADOS_DUROS) == 3
        assert "F2" in CANDADOS_DUROS
        assert "F6" in CANDADOS_DUROS
        assert "F8" in CANDADOS_DUROS
    
    def test_es_candado_duro_true(self):
        """F2, F6, F8 son candados duros"""
        assert es_candado_duro("F2") == True
        assert es_candado_duro("F6") == True
        assert es_candado_duro("F8") == True
    
    def test_es_candado_duro_false(self):
        """F0, F1, F3-F5, F7, F9 no son candados duros"""
        assert es_candado_duro("F0") == False
        assert es_candado_duro("F1") == False
        assert es_candado_duro("F3") == False
        assert es_candado_duro("F9") == False


class TestCandadoF2:
    """Pruebas para CANDADO F2: No iniciar ejecución sin aprobación"""
    
    def test_f2_bloquea_sin_f0(self):
        """F2 debe bloquear si F0 no está completa"""
        proyecto = {"monto": 1000000, "risk_score_total": 20}
        context = {
            "fases_completadas": ["F1"],  # Falta F0
            "deliberaciones": {}
        }
        
        resultado = verificar_candado_f2(proyecto, context)
        
        assert resultado["liberado"] == False
        assert any("F0" in b for b in resultado["bloqueos"])
    
    def test_f2_bloquea_sin_f1(self):
        """F2 debe bloquear si F1 no está completa"""
        proyecto = {"monto": 1000000, "risk_score_total": 20}
        context = {
            "fases_completadas": ["F0"],  # Falta F1
            "deliberaciones": {}
        }
        
        resultado = verificar_candado_f2(proyecto, context)
        
        assert resultado["liberado"] == False
        assert any("F1" in b for b in resultado["bloqueos"])
    
    def test_f2_bloquea_sin_presupuesto(self):
        """F2 debe bloquear sin confirmación de presupuesto"""
        proyecto = {"monto": 1000000, "risk_score_total": 20}
        context = {
            "fases_completadas": ["F0", "F1"],
            "deliberaciones": {
                "F0": {
                    "A1_SPONSOR": {"decision": "APROBAR"},
                    "A3_FISCAL": {"decision": "APROBAR"}
                },
                "F2": {}  # Falta A5_FINANZAS
            }
        }
        
        resultado = verificar_candado_f2(proyecto, context)
        
        assert resultado["liberado"] == False
        assert any("Finanzas" in b or "presupuesto" in b for b in resultado["bloqueos"])
    
    def test_f2_bloquea_revision_humana_requerida(self):
        """F2 debe bloquear si requiere revisión humana y no se obtuvo"""
        proyecto = {"monto": 8000000, "risk_score_total": 25, "revision_humana_obtenida": False}
        context = {
            "fases_completadas": ["F0", "F1"],
            "deliberaciones": {
                "F0": {
                    "A1_SPONSOR": {"decision": "APROBAR"},
                    "A3_FISCAL": {"decision": "APROBAR"}
                },
                "F2": {
                    "A5_FINANZAS": {"decision": "APROBAR"}
                }
            }
        }
        
        resultado = verificar_candado_f2(proyecto, context)
        
        assert resultado["liberado"] == False
        assert any("revisión humana" in b.lower() for b in resultado["bloqueos"])
    
    def test_f2_pasa_con_todo_completo(self, context_f2_completo):
        """F2 debe pasar con todo completo"""
        proyecto = {"monto": 1000000, "risk_score_total": 20}
        
        resultado = verificar_candado_f2(proyecto, context_f2_completo)
        
        assert resultado["liberado"] == True
        assert len(resultado["bloqueos"]) == 0


class TestCandadoF6:
    """Pruebas para CANDADO F6: No emitir VBC sin evidencia"""
    
    def test_f6_bloquea_sin_f5(self):
        """F6 debe bloquear si F5 no está completa"""
        proyecto = {"monto": 1000000}
        context = {
            "fases_completadas": ["F0", "F1", "F2", "F3", "F4"],  # Falta F5
            "deliberaciones": {},
            "defense_file": {},
            "proveedor": {},
            "documentos": []
        }
        
        resultado = verificar_candado_f6(proyecto, context)
        
        assert resultado["liberado"] == False
        assert any("F5" in b for b in resultado["bloqueos"])
    
    def test_f6_bloquea_sin_vbc_fiscal(self):
        """F6 debe bloquear sin VBC Fiscal"""
        proyecto = {"monto": 1000000}
        context = {
            "fases_completadas": ["F0", "F1", "F2", "F3", "F4", "F5"],
            "deliberaciones": {"F6": {"A3_FISCAL": {"decision": "APROBAR"}, "A4_LEGAL": {"decision": "APROBAR"}}},
            "defense_file": {
                "matriz_materialidad_completitud": 85,
                "vbc_fiscal_emitido": False,  # Falta VBC Fiscal
                "vbc_legal_emitido": True
            },
            "proveedor": {"tipo_relacion": "TERCERO_INDEPENDIENTE"},
            "documentos": []
        }
        
        resultado = verificar_candado_f6(proyecto, context)
        
        assert resultado["liberado"] == False
        assert any("VBC Fiscal" in b for b in resultado["bloqueos"])
    
    def test_f6_bloquea_materialidad_baja(self):
        """F6 debe bloquear si materialidad < 80%"""
        proyecto = {"monto": 1000000}
        context = {
            "fases_completadas": ["F0", "F1", "F2", "F3", "F4", "F5"],
            "deliberaciones": {"F6": {"A3_FISCAL": {"decision": "APROBAR"}, "A4_LEGAL": {"decision": "APROBAR"}}},
            "defense_file": {
                "matriz_materialidad_completitud": 75,  # < 80%
                "vbc_fiscal_emitido": True,
                "vbc_legal_emitido": True
            },
            "proveedor": {"tipo_relacion": "TERCERO_INDEPENDIENTE"},
            "documentos": []
        }
        
        resultado = verificar_candado_f6(proyecto, context)
        
        assert resultado["liberado"] == False
        assert any("materialidad" in b.lower() for b in resultado["bloqueos"])
    
    def test_f6_bloquea_intragrupo_sin_tp(self):
        """F6 debe bloquear operación intra-grupo sin estudio TP"""
        proyecto = {"monto": 5000000}
        context = {
            "fases_completadas": ["F0", "F1", "F2", "F3", "F4", "F5"],
            "deliberaciones": {"F6": {"A3_FISCAL": {"decision": "APROBAR"}, "A4_LEGAL": {"decision": "APROBAR"}}},
            "defense_file": {
                "matriz_materialidad_completitud": 90,
                "vbc_fiscal_emitido": True,
                "vbc_legal_emitido": True
            },
            "proveedor": {"tipo_relacion": "PARTE_RELACIONADA"},  # Intra-grupo
            "documentos": []  # Sin ESTUDIO_TP
        }
        
        resultado = verificar_candado_f6(proyecto, context)
        
        assert resultado["liberado"] == False
        assert any("TP" in b or "parte relacionada" in b.lower() for b in resultado["bloqueos"])
    
    def test_f6_pasa_con_todo_completo(self, context_f6_completo):
        """F6 debe pasar con todo completo"""
        proyecto = {"monto": 1500000}
        
        resultado = verificar_candado_f6(proyecto, context_f6_completo)
        
        assert resultado["liberado"] == True
        assert len(resultado["bloqueos"]) == 0


class TestCandadoF8:
    """Pruebas para CANDADO F8: No liberar pago sin 3-way match"""
    
    def test_f8_bloquea_sin_f6(self):
        """F8 debe bloquear si F6 no está completa"""
        proyecto = {"monto": 1500000}
        context = {
            "fases_completadas": ["F0", "F1", "F2", "F3", "F4", "F5", "F7"],  # Falta F6
            "deliberaciones": {},
            "documentos": []
        }
        
        resultado = verificar_candado_f8(proyecto, context)
        
        assert resultado["liberado"] == False
        assert any("F6" in b for b in resultado["bloqueos"])
    
    def test_f8_bloquea_cfdi_generico(self):
        """F8 debe bloquear si CFDI tiene descripción genérica"""
        proyecto = {"monto": 1500000}
        context = {
            "fases_completadas": ["F0", "F1", "F2", "F3", "F4", "F5", "F6", "F7"],
            "deliberaciones": {"F8": {"A5_FINANZAS": {"decision": "APROBAR"}}},
            "documentos": [
                {
                    "tipo": "CFDI",
                    "metadata": {
                        "descripcion": "Servicios profesionales varios",  # Genérico
                        "monto": 1500000
                    }
                },
                {"tipo": "CONTRATO", "metadata": {"monto": 1500000}}
            ]
        }
        
        resultado = verificar_candado_f8(proyecto, context)
        
        assert resultado["liberado"] == False
        assert any("genéric" in b.lower() or "CFDI" in b for b in resultado["bloqueos"])
    
    def test_f8_bloquea_three_way_match_alto(self):
        """F8 debe bloquear si diferencia 3-way match > 5%"""
        proyecto = {"monto": 1500000}
        context = {
            "fases_completadas": ["F0", "F1", "F2", "F3", "F4", "F5", "F6", "F7"],
            "deliberaciones": {"F8": {"A5_FINANZAS": {"decision": "APROBAR"}}},
            "documentos": [
                {
                    "tipo": "CFDI",
                    "metadata": {
                        "descripcion": "Estudio de Mercado Inmobiliario NL 2026",
                        "monto": 1700000  # 13% más que contrato
                    }
                },
                {"tipo": "CONTRATO", "metadata": {"monto": 1500000}}
            ]
        }
        
        resultado = verificar_candado_f8(proyecto, context)
        
        assert resultado["liberado"] == False
        assert any("3-way" in b.lower() or "match" in b.lower() for b in resultado["bloqueos"])
    
    def test_f8_pasa_con_todo_completo(self, context_f8_completo):
        """F8 debe pasar con todo completo y montos coinciden"""
        proyecto = {"monto": 1500000}
        
        resultado = verificar_candado_f8(proyecto, context_f8_completo)
        
        assert resultado["liberado"] == True
        assert len(resultado["bloqueos"]) == 0


class TestMiddlewareCandados:
    """Pruebas para el middleware de candados"""
    
    @pytest.mark.asyncio
    async def test_middleware_bloquea_f2_sin_requisitos(self):
        """Middleware debe lanzar excepción si F2 no tiene requisitos"""
        from middleware.candados_middleware import (
            verificar_candado_antes_de_avanzar,
            CandadoBlockedException
        )
        
        proyecto = {
            "id": "test-001",
            "monto": 1000000,
            "risk_score_total": 20
        }
        context = {
            "fases_completadas": ["F0"],  # Falta F1
            "deliberaciones": {}
        }
        
        with pytest.raises(CandadoBlockedException) as excinfo:
            await verificar_candado_antes_de_avanzar(proyecto, "F2", context)
        
        assert excinfo.value.fase == "F2"
        assert len(excinfo.value.bloqueos) > 0
    
    @pytest.mark.asyncio
    async def test_middleware_permite_f2_con_requisitos(self, context_f2_completo):
        """Middleware debe permitir F2 si tiene todos los requisitos"""
        from middleware.candados_middleware import verificar_candado_antes_de_avanzar
        
        proyecto = {
            "id": "test-002",
            "monto": 1000000,
            "risk_score_total": 20
        }
        
        resultado = await verificar_candado_antes_de_avanzar(proyecto, "F2", context_f2_completo)
        
        assert resultado["puede_avanzar"] == True
    
    @pytest.mark.asyncio
    async def test_middleware_no_verifica_fases_sin_candado(self):
        """Middleware debe permitir fases sin candado (F3, F4, F5, etc.)"""
        from middleware.candados_middleware import verificar_candado_antes_de_avanzar
        
        proyecto = {
            "id": "test-003",
            "monto": 1000000
        }
        context = {}
        
        # F3 no tiene candado, debe pasar
        resultado = await verificar_candado_antes_de_avanzar(proyecto, "F3", context)
        
        assert resultado["puede_avanzar"] == True
    
    @pytest.mark.asyncio
    async def test_middleware_bloquea_f6_sin_materialidad(self):
        """Middleware debe bloquear F6 si materialidad < 80%"""
        from middleware.candados_middleware import (
            verificar_candado_antes_de_avanzar,
            CandadoBlockedException
        )
        
        proyecto = {"id": "test-004", "monto": 1000000}
        context = {
            "fases_completadas": ["F0", "F1", "F2", "F3", "F4", "F5"],
            "deliberaciones": {"F6": {}},
            "defense_file": {"matriz_materialidad_completitud": 60},
            "proveedor": {},
            "documentos": []
        }
        
        with pytest.raises(CandadoBlockedException) as excinfo:
            await verificar_candado_antes_de_avanzar(proyecto, "F6", context)
        
        assert excinfo.value.fase == "F6"
    
    @pytest.mark.asyncio
    async def test_middleware_bloquea_f8_sin_f7(self):
        """Middleware debe bloquear F8 si F7 no está completa"""
        from middleware.candados_middleware import (
            verificar_candado_antes_de_avanzar,
            CandadoBlockedException
        )
        
        proyecto = {"id": "test-005", "monto": 1500000}
        context = {
            "fases_completadas": ["F0", "F1", "F2", "F3", "F4", "F5", "F6"],
            "deliberaciones": {},
            "documentos": []
        }
        
        with pytest.raises(CandadoBlockedException) as excinfo:
            await verificar_candado_antes_de_avanzar(proyecto, "F8", context)
        
        assert excinfo.value.fase == "F8"


class TestObtenerAcciones:
    """Pruebas para la función obtener_acciones_para_bloqueos"""
    
    def test_acciones_para_presupuesto(self):
        """Debe mapear bloqueo de presupuesto a acción correcta"""
        from middleware.candados_middleware import obtener_acciones_para_bloqueos
        
        bloqueos = ["Sin presupuesto confirmado"]
        acciones = obtener_acciones_para_bloqueos(bloqueos)
        
        assert any("Finanzas" in a for a in acciones)
    
    def test_acciones_para_revision_humana(self):
        """Debe mapear bloqueo de revisión humana a acción correcta"""
        from middleware.candados_middleware import obtener_acciones_para_bloqueos
        
        bloqueos = ["Requiere revisión humana no obtenida"]
        acciones = obtener_acciones_para_bloqueos(bloqueos)
        
        assert any("revisión humana" in a.lower() for a in acciones)
    
    def test_acciones_para_materialidad(self):
        """Debe mapear bloqueo de materialidad a acción correcta"""
        from middleware.candados_middleware import obtener_acciones_para_bloqueos
        
        bloqueos = ["Materialidad incompleta < 80%"]
        acciones = obtener_acciones_para_bloqueos(bloqueos)
        
        assert any("materialidad" in a.lower() for a in acciones)
    
    def test_acciones_para_3way_match(self):
        """Debe mapear bloqueo de 3-way match a acción correcta"""
        from middleware.candados_middleware import obtener_acciones_para_bloqueos
        
        bloqueos = ["Diferencia 3-way match mayor a 5%"]
        acciones = obtener_acciones_para_bloqueos(bloqueos)
        
        assert any("3-way" in a or "5%" in a for a in acciones)
