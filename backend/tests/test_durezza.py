"""
Revisar.IA - Suite de Pruebas Unitarias
=========================================
Pruebas para el sistema de auditoría fiscal de servicios intangibles.

Ejecutar con: python -m pytest backend/tests/test_durezza.py -v
O directamente: python backend/tests/test_durezza.py
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from typing import Dict, Any

def print_header(title: str):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def print_test_result(test_name: str, passed: bool, details: str = ""):
    status = "PASS" if passed else "FAIL"
    symbol = "✓" if passed else "✗"
    print(f"  {symbol} {test_name}: {status}")
    if details:
        print(f"    {details}")

class DurezzaTestSuite:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.tests_run = 0
    
    def test_scoring_calcular_risk_score(self):
        """Test: Cálculo de risk score objetivo"""
        print_header("PRUEBAS DE RISK SCORING")
        
        try:
            from scoring import calcular_risk_score
            
            evaluacion_bajo = {
                "razon_negocios": {"vinculacion_giro": 2, "objetivo_economico": 3, "coherencia_monto": 2},
                "beneficio_economico": {"identificacion_beneficios": 2, "modelo_roi": 3, "horizonte_temporal": 2},
                "materialidad": {"formalizacion": 1, "evidencias_ejecucion": 2, "coherencia_documentos": 1},
                "trazabilidad": {"conservacion": 2, "integridad": 1, "timeline": 2}
            }
            
            resultado = calcular_risk_score(evaluacion_bajo)
            score = resultado.get("risk_score_total", 0)
            
            test1_pass = score < 40
            print_test_result(
                "Proyecto bajo riesgo (< 40)", 
                test1_pass, 
                f"Score: {score}/100"
            )
            self.record_result(test1_pass)
            
            evaluacion_alto = {
                "razon_negocios": {"vinculacion_giro": 8, "objetivo_economico": 8, "coherencia_monto": 9},
                "beneficio_economico": {"identificacion_beneficios": 8, "modelo_roi": 9, "horizonte_temporal": 8},
                "materialidad": {"formalizacion": 9, "evidencias_ejecucion": 8, "coherencia_documentos": 8},
                "trazabilidad": {"conservacion": 9, "integridad": 9, "timeline": 7}
            }
            
            resultado_alto = calcular_risk_score(evaluacion_alto)
            score_alto = resultado_alto.get("risk_score_total", 0)
            
            test2_pass = score_alto >= 60
            print_test_result(
                "Proyecto alto riesgo (>= 60)", 
                test2_pass, 
                f"Score: {score_alto}/100"
            )
            self.record_result(test2_pass)
            
            nivel = resultado_alto.get("nivel_riesgo", "")
            test3_pass = nivel in ["ALTO", "CRITICO"]
            print_test_result(
                "Nivel de riesgo clasificado correctamente",
                test3_pass,
                f"Nivel: {nivel}"
            )
            self.record_result(test3_pass)
            
        except ImportError as e:
            print_test_result("Importar módulo scoring", False, str(e))
            self.record_result(False)
    
    def test_subagente_tipificacion(self):
        """Test: SUB_TIPIFICACION - Clasificación de proyectos"""
        print_header("PRUEBAS DE SUB_TIPIFICACION")
        
        try:
            from agents import clasificar_proyecto
            
            proyecto = {
                "nombre": "Estudio de Mercado Regional",
                "descripcion": "Análisis macroeconómico del sector inmobiliario con proyecciones de demanda",
                "monto": 850000
            }
            proveedor = {"tipo_relacion": "TERCERO_INDEPENDIENTE", "alerta_efos": False}
            
            resultado = clasificar_proyecto(proyecto, proveedor)
            
            tipologia = resultado.get("tipologia_asignada", "")
            test1_pass = tipologia == "CONSULTORIA_MACRO_MERCADO"
            print_test_result(
                "Tipología asignada correctamente",
                test1_pass,
                f"Esperado: CONSULTORIA_MACRO_MERCADO, Obtenido: {tipologia}"
            )
            self.record_result(test1_pass)
            
            confianza = resultado.get("confianza_clasificacion", "")
            test2_pass = confianza in ["ALTA", "MEDIA", "BAJA"]
            print_test_result(
                "Nivel de confianza válido",
                test2_pass,
                f"Confianza: {confianza}"
            )
            self.record_result(test2_pass)
            
            checklist = resultado.get("checklist_aplicable", "")
            test3_pass = "checklist" in checklist.lower()
            print_test_result(
                "Checklist asignado",
                test3_pass,
                f"Checklist: {checklist}"
            )
            self.record_result(test3_pass)
            
        except ImportError as e:
            print_test_result("Importar clasificar_proyecto", False, str(e))
            self.record_result(False)
    
    def test_subagente_materialidad(self):
        """Test: SUB_MATERIALIDAD - Evaluación de matriz"""
        print_header("PRUEBAS DE SUB_MATERIALIDAD")
        
        try:
            from agents import evaluar_materialidad
            
            proyecto = {"nombre": "Proyecto Test", "monto": 500000}
            documentos = [
                {"tipo": "CONTRATO", "nombre": "contrato.pdf"},
                {"tipo": "SOW", "nombre": "sow.pdf"}
            ]
            
            resultado = evaluar_materialidad(proyecto, documentos, "F5")
            
            completitud = resultado.get("completitud_porcentaje", 0)
            test1_pass = 0 <= completitud <= 100
            print_test_result(
                "Completitud en rango válido (0-100%)",
                test1_pass,
                f"Completitud: {completitud}%"
            )
            self.record_result(test1_pass)
            
            puede_emitir = resultado.get("puede_emitir_vbc", None)
            expected_vbc = completitud >= 80
            test2_pass = puede_emitir == expected_vbc
            print_test_result(
                "VBC emitible solo si >= 80%",
                test2_pass,
                f"Completitud: {completitud}%, Puede emitir VBC: {puede_emitir}"
            )
            self.record_result(test2_pass)
            
        except ImportError as e:
            print_test_result("Importar evaluar_materialidad", False, str(e))
            self.record_result(False)
    
    def test_subagente_riesgos(self):
        """Test: SUB_RIESGOS_ESPECIALES - Detección de riesgos"""
        print_header("PRUEBAS DE SUB_RIESGOS_ESPECIALES")
        
        try:
            from agents import detectar_riesgos
            
            proyecto = {"nombre": "Management Fee", "monto": 8000000}
            proveedor = {
                "rfc": "ABC123",
                "tipo_relacion": "SUBSIDIARIA",
                "alerta_efos": False,
                "empleados": 0
            }
            contexto = {"estudio_tp_vigente": False}
            
            resultado = detectar_riesgos(proyecto, proveedor, contexto)
            
            alertas = resultado.get("alertas_detectadas", [])
            test1_pass = len(alertas) > 0
            print_test_result(
                "Detecta alertas para proyecto riesgoso",
                test1_pass,
                f"Alertas: {len(alertas)}"
            )
            self.record_result(test1_pass)
            
            puede_continuar = resultado.get("puede_continuar", True)
            test2_pass = puede_continuar == False
            print_test_result(
                "Bloquea proyecto con riesgos críticos",
                test2_pass,
                f"Puede continuar: {puede_continuar}"
            )
            self.record_result(test2_pass)
            
            tipos_riesgo = [a.get("tipo_riesgo", "") for a in alertas]
            test3_pass = any("PARTE_RELACIONADA" in t or "TP" in t for t in tipos_riesgo)
            print_test_result(
                "Detecta riesgo de parte relacionada/TP",
                test3_pass,
                f"Tipos detectados: {tipos_riesgo}"
            )
            self.record_result(test3_pass)
            
        except ImportError as e:
            print_test_result("Importar detectar_riesgos", False, str(e))
            self.record_result(False)
    
    def test_subagente_defensa(self):
        """Test: A7_DEFENSA - Generación de Defense File"""
        print_header("PRUEBAS DE A7_DEFENSA")
        
        try:
            from agents import evaluar_defendibilidad
            
            proyecto = {
                "nombre": "Proyecto Test",
                "tipologia": "CONSULTORIA_MACRO_MERCADO",
                "monto": 500000,
                "risk_score_total": 25
            }
            documentos = [
                {"tipo": "SIB", "nombre": "sib.pdf"},
                {"tipo": "CONTRATO", "nombre": "contrato.pdf"},
                {"tipo": "SOW", "nombre": "sow.pdf"}
            ]
            deliberaciones = {
                "A1_SPONSOR": {"decision": "APROBAR"},
                "A3_FISCAL": {"decision": "APROBAR"}
            }
            
            resultado = evaluar_defendibilidad(
                proyecto, documentos, deliberaciones, 
                {"completitud_porcentaje": 75}, None, None
            )
            
            indice = resultado.get("indice_defendibilidad", 0)
            test1_pass = 0 <= indice <= 100
            print_test_result(
                "Índice de defendibilidad en rango (0-100)",
                test1_pass,
                f"Índice: {indice}/100"
            )
            self.record_result(test1_pass)
            
            docs_clave = resultado.get("documentos_clave", [])
            test2_pass = len(docs_clave) > 0
            print_test_result(
                "Lista documentos clave",
                test2_pass,
                f"Documentos evaluados: {len(docs_clave)}"
            )
            self.record_result(test2_pass)
            
            argumentos = resultado.get("argumentos_defensa", [])
            test3_pass = len(argumentos) > 0
            print_test_result(
                "Genera argumentos de defensa",
                test3_pass,
                f"Argumentos: {len(argumentos)}"
            )
            self.record_result(test3_pass)
            
        except ImportError as e:
            print_test_result("Importar evaluar_defendibilidad", False, str(e))
            self.record_result(False)
    
    def test_validation_schemas(self):
        """Test: Validación de schemas de agentes"""
        print_header("PRUEBAS DE VALIDACIÓN DE OUTPUTS")
        
        try:
            from validation import validar_output_agente, A3FiscalOutput
            
            output_valido = {
                "decision": "APROBAR",
                "risk_score_calculado": 25,
                "risk_score_total": 25,
                "analisis_pilares": {
                    "razon_negocios": {"score": 5, "observaciones": "Coherente"},
                    "beneficio_economico": {"score": 8, "observaciones": "ROI claro"},
                    "materialidad": {"score": 5, "observaciones": "Documentado"},
                    "trazabilidad": {"score": 7, "observaciones": "Timeline completo"}
                },
                "conclusion_por_pilar": {
                    "razon_negocios": {"status": "CUMPLE", "observaciones": "OK"},
                    "beneficio_economico": {"status": "CUMPLE", "observaciones": "OK"},
                    "materialidad": {"status": "CUMPLE", "observaciones": "OK"},
                    "trazabilidad": {"status": "CUMPLE", "observaciones": "OK"}
                },
                "condiciones_aprobacion": [],
                "riesgos_identificados": [],
                "fundamento_legal": "CFF 5A, LISR 27",
                "checklist_evidencia_exigible": [],
                "requiere_validacion_humana": False
            }
            
            resultado = validar_output_agente("A3_FISCAL", output_valido)
            tiene_errores = len(resultado.get("errores", [])) > 0
            tiene_correciones = resultado.get("output_corregido") is not None
            test1_pass = tiene_errores or tiene_correciones
            print_test_result(
                "Valida/corrige output A3_FISCAL",
                test1_pass,
                f"Proceso validacion ejecutado. Errores: {len(resultado.get('errores', []))}"
            )
            self.record_result(test1_pass)
            
            output_invalido = {
                "decision": "INVALIDA",
                "risk_score_calculado": 150
            }
            
            resultado_inv = validar_output_agente("A3_FISCAL", output_invalido)
            test2_pass = resultado_inv.get("valido", True) == False
            print_test_result(
                "Rechaza output inválido",
                test2_pass,
                f"Errores detectados: {len(resultado_inv.get('errores', []))}"
            )
            self.record_result(test2_pass)
            
        except ImportError as e:
            print_test_result("Importar módulo validation", False, str(e))
            self.record_result(False)
    
    def test_checklists(self):
        """Test: Checklists por tipología y fase"""
        print_header("PRUEBAS DE CHECKLISTS")
        
        try:
            from checklists import CHECKLISTS_POR_TIPOLOGIA
            
            checklist = CHECKLISTS_POR_TIPOLOGIA.get("CONSULTORIA_MACRO_MERCADO", {})
            items = checklist.get("fases", {}).get("F5", {}).get("items", [])
            test1_pass = len(items) > 0 or len(checklist) > 0
            print_test_result(
                "Obtiene checklist para CONSULTORIA_MACRO_MERCADO",
                test1_pass,
                f"Items F5: {len(items)}, Fases: {list(checklist.get('fases', {}).keys())}"
            )
            self.record_result(test1_pass)
            
            tipologias = list(CHECKLISTS_POR_TIPOLOGIA.keys())
            test2_pass = len(tipologias) >= 3
            print_test_result(
                "Tipologías con checklist definido (min 3)",
                test2_pass,
                f"Tipologías: {len(tipologias)} ({', '.join(tipologias[:3])})"
            )
            self.record_result(test2_pass)
            
        except ImportError as e:
            print_test_result("Importar módulo checklists", False, str(e))
            self.record_result(False)
    
    def test_fases_candados(self):
        """Test: Fases y candados duros"""
        print_header("PRUEBAS DE FASES Y CANDADOS")
        
        try:
            from services.fase_service import es_candado_duro, ORDEN_FASES
            
            test1_pass = len(ORDEN_FASES) == 10
            print_test_result(
                "10 fases definidas (F0-F9)",
                test1_pass,
                f"Fases: {len(ORDEN_FASES)}"
            )
            self.record_result(test1_pass)
            
            candados = ["F2", "F6", "F8"]
            candados_correctos = all(es_candado_duro(f) for f in candados)
            test2_pass = candados_correctos
            print_test_result(
                "F2, F6, F8 son candados duros",
                test2_pass,
                f"F2={es_candado_duro('F2')}, F6={es_candado_duro('F6')}, F8={es_candado_duro('F8')}"
            )
            self.record_result(test2_pass)
            
            no_candados = ["F0", "F1", "F3", "F4", "F5", "F7", "F9"]
            no_candados_correctos = all(not es_candado_duro(f) for f in no_candados)
            test3_pass = no_candados_correctos
            print_test_result(
                "Otras fases NO son candados",
                test3_pass,
                ""
            )
            self.record_result(test3_pass)
            
        except ImportError as e:
            print_test_result("Importar fase_service", False, str(e))
            self.record_result(False)
    
    def test_contexto_global(self):
        """Test: Contexto global para agentes"""
        print_header("PRUEBAS DE CONTEXTO GLOBAL")
        
        try:
            from context.contexto_global import ContextoGlobalService
            
            servicio = ContextoGlobalService()
            contexto = servicio.get_contexto_para_agente("A3_FISCAL", "F0", "CONSULTORIA_MACRO_MERCADO")
            test1_pass = contexto is not None and len(contexto) > 0
            print_test_result(
                "Contexto para A3_FISCAL disponible",
                test1_pass,
                f"Claves: {list(contexto.keys()) if contexto else []}"
            )
            self.record_result(test1_pass)
            
            test2_pass = "normativa_aplicable" in contexto
            print_test_result(
                "Contexto incluye normativa aplicable",
                test2_pass,
                f"Contiene normativa: {test2_pass}"
            )
            self.record_result(test2_pass)
            
        except ImportError as e:
            print_test_result("Importar módulo context", False, str(e))
            self.record_result(False)
    
    def record_result(self, passed: bool):
        self.tests_run += 1
        if passed:
            self.passed += 1
        else:
            self.failed += 1
    
    def run_all_tests(self):
        print("\n" + "="*60)
        print("  REVISAR.IA - SUITE DE PRUEBAS UNITARIAS")
        print("="*60)
        
        self.test_scoring_calcular_risk_score()
        self.test_subagente_tipificacion()
        self.test_subagente_materialidad()
        self.test_subagente_riesgos()
        self.test_subagente_defensa()
        self.test_validation_schemas()
        self.test_checklists()
        self.test_fases_candados()
        self.test_contexto_global()
        
        print("\n" + "="*60)
        print("  RESUMEN DE RESULTADOS")
        print("="*60)
        print(f"  Total pruebas: {self.tests_run}")
        print(f"  Pasaron: {self.passed} ✓")
        print(f"  Fallaron: {self.failed} ✗")
        print(f"  Porcentaje: {(self.passed/self.tests_run*100):.1f}%")
        print("="*60 + "\n")
        
        return self.failed == 0


if __name__ == "__main__":
    suite = DurezzaTestSuite()
    success = suite.run_all_tests()
    sys.exit(0 if success else 1)
