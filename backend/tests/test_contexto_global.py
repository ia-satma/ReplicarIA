"""
Pruebas para el sistema de contexto global y reglas por tipología
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from context.contexto_global import ContextoGlobalService
from context.poe_fases import es_candado_duro, get_candados_duros
from config.reglas_tipologia import (
    get_reglas_tipologia,
    get_checklist_obligatorio,
    validar_checklist_fase,
    get_reglas_auditoria,
    get_contexto_inyeccion,
    listar_tipologias,
    requiere_revision_humana
)
from services.inyeccion_contexto_service import (
    construir_contexto_completo_para_agente,
    generar_system_prompt_con_contexto
)


class TestContextoGlobal:
    
    def test_contexto_global_tiene_normativo(self):
        ctx = ContextoGlobalService.get_contexto_completo()
        assert "normativo" in ctx
    
    def test_contexto_global_tiene_tipologias(self):
        ctx = ContextoGlobalService.get_contexto_completo()
        assert "tipologias" in ctx
    
    def test_contexto_global_tiene_poe(self):
        ctx = ContextoGlobalService.get_contexto_completo()
        assert "poe" in ctx


class TestCandadosDuros:
    
    def test_candados_duros_correctos(self):
        assert es_candado_duro("F2") == True
        assert es_candado_duro("F6") == True
        assert es_candado_duro("F8") == True
        assert es_candado_duro("F3") == False
        assert es_candado_duro("F4") == False
    
    def test_get_candados_duros_lista(self):
        candados = get_candados_duros()
        assert "F2" in candados
        assert "F6" in candados
        assert "F8" in candados
        assert len(candados) == 3


class TestReglasTipologia:
    
    def test_consultoria_macro_tiene_reglas(self):
        reglas = get_reglas_tipologia("CONSULTORIA_MACRO_ESTRATEGIA")
        assert "checklist_obligatorio" in reglas
        assert "reglas_auditoria_fiscal" in reglas
    
    def test_checklist_f5_consultoria_tiene_modelo(self):
        checklist = get_checklist_obligatorio("CONSULTORIA_MACRO_ESTRATEGIA", "F5")
        nombres = [item["documento"] for item in checklist]
        assert "Herramienta/Modelo" in nombres
        assert "Manual Metodológico" in nombres
    
    def test_validar_checklist_detecta_faltantes(self):
        docs = [{"tipo": "Informe Final", "descripcion": "PDF"}]
        resultado = validar_checklist_fase(
            "CONSULTORIA_MACRO_ESTRATEGIA", 
            "F5", 
            docs
        )
        assert resultado["cumple"] == False
        assert len(resultado["faltantes"]) >= 2
    
    def test_validar_checklist_vacio_pasa(self):
        resultado = validar_checklist_fase(
            "CONSULTORIA_MACRO_ESTRATEGIA", 
            "F9",
            []
        )
        assert resultado["cumple"] == True
    
    def test_get_reglas_auditoria(self):
        reglas = get_reglas_auditoria("CONSULTORIA_MACRO_ESTRATEGIA")
        assert len(reglas) >= 2
        nombres = [r["regla"] for r in reglas]
        assert "REGLA_MODELO_OBLIGATORIO" in nombres
    
    def test_get_contexto_inyeccion(self):
        ctx = get_contexto_inyeccion("CONSULTORIA_MACRO_ESTRATEGIA", "A3_FISCAL")
        assert "contexto_rol" in ctx
        assert "alertas_tipologia" in ctx
    
    def test_listar_tipologias(self):
        tipologias = listar_tipologias()
        assert len(tipologias) >= 3
        assert "CONSULTORIA_MACRO_ESTRATEGIA" in tipologias
    
    def test_intragrupo_requiere_revision_humana(self):
        assert requiere_revision_humana("INTRAGRUPO_MANAGEMENT_FEE") == True
        assert requiere_revision_humana("CONSULTORIA_MACRO_ESTRATEGIA") == False


class TestInyeccionContexto:
    
    def test_contexto_completo_tiene_todos_bloques(self):
        proyecto = {
            "id": "test",
            "nombre": "Estudio Test",
            "tipologia": "CONSULTORIA_MACRO_ESTRATEGIA",
            "fase_actual": "F5"
        }
        
        contexto = construir_contexto_completo_para_agente(
            agente_id="A3_FISCAL",
            proyecto=proyecto
        )
        
        assert "contexto_normativo" in contexto
        assert "contexto_corporativo" in contexto
        assert "tipologia" in contexto
        assert "rol_agente" in contexto
        assert "checklist_fase_actual" in contexto
        assert "_meta" in contexto
    
    def test_contexto_meta_incluye_datos_correctos(self):
        proyecto = {
            "id": "test",
            "nombre": "Estudio Test",
            "tipologia": "CONSULTORIA_MACRO_ESTRATEGIA",
            "fase_actual": "F5"
        }
        
        contexto = construir_contexto_completo_para_agente(
            agente_id="A3_FISCAL",
            proyecto=proyecto
        )
        
        assert contexto["_meta"]["agente_id"] == "A3_FISCAL"
        assert contexto["_meta"]["tipologia"] == "CONSULTORIA_MACRO_ESTRATEGIA"
        assert contexto["_meta"]["fase_actual"] == "F5"
    
    def test_generar_system_prompt(self):
        proyecto = {
            "id": "test",
            "nombre": "Estudio Test",
            "tipologia": "CONSULTORIA_MACRO_ESTRATEGIA",
            "fase_actual": "F5"
        }
        
        contexto = construir_contexto_completo_para_agente(
            agente_id="A3_FISCAL",
            proyecto=proyecto
        )
        
        prompt = generar_system_prompt_con_contexto("A3_FISCAL", contexto)
        
        assert "ROL" in prompt
        assert "MARCO NORMATIVO" in prompt
        assert "TIPOLOGÍA" in prompt
        assert "CHECKLIST" in prompt


class TestIntegracionCompleta:
    
    def test_flujo_completo_consultoria(self):
        proyecto = {
            "id": "proj-001",
            "nombre": "Estudio de Mercado Nayarit",
            "tipologia": "CONSULTORIA_MACRO_ESTRATEGIA",
            "fase_actual": "F5",
            "monto": 2500000
        }
        
        proveedor = {
            "rfc": "ABC123456XYZ",
            "razon_social": "Consultora Estratégica SA",
            "alerta_efos": False
        }
        
        documentos = [
            {"tipo": "Informe Final", "nombre": "Estudio_Final.pdf"},
            {"tipo": "Herramienta/Modelo", "nombre": "Modelo_Parametrico.xlsx"}
        ]
        
        contexto = construir_contexto_completo_para_agente(
            agente_id="A3_FISCAL",
            proyecto=proyecto,
            proveedor=proveedor,
            documentos=documentos
        )
        
        assert contexto["proyecto"]["monto"] == 2500000
        assert contexto["proveedor"]["rfc"] == "ABC123456XYZ"
        assert len(contexto["documentos_cargados"]) == 2
        
        validacion = validar_checklist_fase(
            "CONSULTORIA_MACRO_ESTRATEGIA",
            "F5",
            documentos
        )
        assert len(validacion["faltantes"]) >= 1
