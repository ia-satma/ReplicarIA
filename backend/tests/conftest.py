"""
Configuración de Pytest para Revisar.IA
Fixtures compartidos para todas las pruebas
"""

import pytest
import sys
from pathlib import Path

backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))


@pytest.fixture
def proyecto_bajo_riesgo():
    """Fixture: proyecto de bajo riesgo para tests"""
    return {
        "id": "test-001",
        "nombre": "Estudio de Mercado Test",
        "tipologia": "CONSULTORIA_MACRO_MERCADO",
        "monto": 1500000,
        "risk_score_total": 16,
        "fase_actual": "F0",
        "fases_completadas": []
    }


@pytest.fixture
def proyecto_alto_riesgo():
    """Fixture: proyecto de alto riesgo para tests"""
    return {
        "id": "test-002",
        "nombre": "Management Fee Intragrupo Test",
        "tipologia": "INTRAGRUPO_MANAGEMENT_FEE",
        "monto": 8000000,
        "risk_score_total": 85,
        "fase_actual": "F0",
        "fases_completadas": []
    }


@pytest.fixture
def proveedor_independiente():
    """Fixture: proveedor tercero independiente"""
    return {
        "rfc": "TEST123456ABC",
        "tipo_relacion": "TERCERO_INDEPENDIENTE",
        "alerta_efos": False
    }


@pytest.fixture
def proveedor_relacionado_efos():
    """Fixture: proveedor parte relacionada con alerta EFOS"""
    return {
        "rfc": "EFOS987654XYZ",
        "tipo_relacion": "PARTE_RELACIONADA",
        "alerta_efos": True
    }


@pytest.fixture
def evaluacion_bajo_riesgo():
    """Fixture: evaluación que resulta en ~16 puntos"""
    return {
        "razon_negocios": {
            "vinculacion_giro": 0,
            "objetivo_economico": 0,
            "coherencia_monto": 3
        },
        "beneficio_economico": {
            "identificacion_beneficios": 0,
            "modelo_roi": 5,
            "horizonte_temporal": 0
        },
        "materialidad": {
            "formalizacion": 0,
            "evidencias_ejecucion": 0,
            "coherencia_documentos": 5
        },
        "trazabilidad": {
            "conservacion": 0,
            "integridad": 0,
            "timeline": 3
        }
    }


@pytest.fixture
def evaluacion_alto_riesgo():
    """Fixture: evaluación que resulta en ~92 puntos"""
    return {
        "razon_negocios": {
            "vinculacion_giro": 5,
            "objetivo_economico": 10,
            "coherencia_monto": 10
        },
        "beneficio_economico": {
            "identificacion_beneficios": 10,
            "modelo_roi": 10,
            "horizonte_temporal": 5
        },
        "materialidad": {
            "formalizacion": 5,
            "evidencias_ejecucion": 10,
            "coherencia_documentos": 10
        },
        "trazabilidad": {
            "conservacion": 10,
            "integridad": 10,
            "timeline": 5
        }
    }


@pytest.fixture
def context_f2_completo():
    """Fixture: contexto completo para pasar candado F2"""
    return {
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


@pytest.fixture
def context_f6_completo():
    """Fixture: contexto completo para pasar candado F6"""
    return {
        "fases_completadas": ["F0", "F1", "F2", "F3", "F4", "F5"],
        "deliberaciones": {
            "F6": {
                "A3_FISCAL": {"decision": "APROBAR"},
                "A4_LEGAL": {"decision": "APROBAR"}
            }
        },
        "defense_file": {
            "matriz_materialidad_completitud": 85,
            "vbc_fiscal_emitido": True,
            "vbc_legal_emitido": True
        },
        "proveedor": {"tipo_relacion": "TERCERO_INDEPENDIENTE"},
        "documentos": []
    }


@pytest.fixture
def context_f8_completo():
    """Fixture: contexto completo para pasar candado F8"""
    return {
        "fases_completadas": ["F0", "F1", "F2", "F3", "F4", "F5", "F6", "F7"],
        "deliberaciones": {
            "F8": {
                "A5_FINANZAS": {"decision": "APROBAR"}
            }
        },
        "documentos": [
            {
                "tipo": "CFDI",
                "metadata": {
                    "descripcion": "Estudio de Mercado Inmobiliario NL 2026",
                    "monto": 1500000
                }
            },
            {
                "tipo": "CONTRATO",
                "metadata": {
                    "monto": 1500000
                }
            }
        ]
    }
