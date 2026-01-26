"""
Pruebas Unitarias: Umbrales de Revisión Humana - Revisar.IA
Verifica los criterios de cuándo se requiere revisión humana
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from context.umbrales_revision import (
    requiere_revision_humana,
    obtener_umbral_monto,
    obtener_umbral_risk_score,
    obtener_tipologias_siempre_humano,
    clasificar_por_risk_score
)


class TestUmbralesConfig:
    """Pruebas de configuración de umbrales"""
    
    def test_umbral_monto_5m(self):
        """Umbral de monto debe ser $5,000,000 MXN"""
        assert obtener_umbral_monto() == 5_000_000
    
    def test_umbral_risk_score_60(self):
        """Umbral de risk_score debe ser 60"""
        assert obtener_umbral_risk_score() == 60
    
    def test_tipologias_siempre_humano(self):
        """INTRAGRUPO y REESTRUCTURAS siempre requieren humano"""
        tipologias = obtener_tipologias_siempre_humano()
        assert "INTRAGRUPO_MANAGEMENT_FEE" in tipologias
        assert "REESTRUCTURAS" in tipologias


class TestRevisionHumana:
    """Pruebas para la función requiere_revision_humana"""
    
    def test_monto_mayor_5m_requiere_revision(self):
        """Proyecto > $5M MXN debe requerir revisión humana"""
        proyecto = {"monto": 8000000, "tipologia": "CONSULTORIA_ESTRATEGICA"}
        proveedor = {"tipo_relacion": "TERCERO_INDEPENDIENTE", "alerta_efos": False}
        
        resultado = requiere_revision_humana(proyecto, risk_score=30, proveedor=proveedor)
        
        assert resultado.requiere == True
        assert any("monto" in r.lower() or "5,000,000" in r for r in resultado.razones)
    
    def test_risk_score_60_requiere_revision(self):
        """Risk score >= 60 debe requerir revisión humana"""
        proyecto = {"monto": 1000000, "tipologia": "CONSULTORIA_ESTRATEGICA"}
        proveedor = {"tipo_relacion": "TERCERO_INDEPENDIENTE", "alerta_efos": False}
        
        resultado = requiere_revision_humana(proyecto, risk_score=65, proveedor=proveedor)
        
        assert resultado.requiere == True
        assert any("risk" in r.lower() or "score" in r.lower() or "60" in r for r in resultado.razones)
    
    def test_intragrupo_requiere_revision(self):
        """Tipología INTRAGRUPO siempre requiere revisión"""
        proyecto = {"monto": 500000, "tipologia": "INTRAGRUPO_MANAGEMENT_FEE"}
        proveedor = {"tipo_relacion": "PARTE_RELACIONADA", "alerta_efos": False}
        
        resultado = requiere_revision_humana(proyecto, risk_score=25, proveedor=proveedor)
        
        assert resultado.requiere == True
    
    def test_efos_requiere_revision(self):
        """Proveedor con alerta EFOS requiere revisión"""
        proyecto = {"monto": 500000, "tipologia": "CONSULTORIA_ESTRATEGICA"}
        proveedor = {"tipo_relacion": "TERCERO_INDEPENDIENTE", "alerta_efos": True}
        
        resultado = requiere_revision_humana(proyecto, risk_score=25, proveedor=proveedor)
        
        assert resultado.requiere == True
        assert any("efos" in r.lower() for r in resultado.razones)
    
    def test_parte_relacionada_requiere_revision(self):
        """Operación con parte relacionada requiere revisión"""
        proyecto = {"monto": 1000000, "tipologia": "CONSULTORIA_ESTRATEGICA"}
        proveedor = {"tipo_relacion": "PARTE_RELACIONADA_NACIONAL", "alerta_efos": False}
        
        resultado = requiere_revision_humana(proyecto, risk_score=25, proveedor=proveedor)
        
        assert resultado.requiere == True
        assert any("relacionada" in r.lower() for r in resultado.razones)
    
    def test_proyecto_normal_no_requiere_revision(self):
        """Proyecto normal bajo umbral no requiere revisión"""
        proyecto = {"monto": 1000000, "tipologia": "CONSULTORIA_ESTRATEGICA"}
        proveedor = {"tipo_relacion": "TERCERO_INDEPENDIENTE", "alerta_efos": False}
        
        resultado = requiere_revision_humana(proyecto, risk_score=30, proveedor=proveedor)
        
        assert resultado.requiere == False
        assert len(resultado.razones) == 0


class TestClasificacionRiskScore:
    """Pruebas para clasificación por risk_score"""
    
    def test_clasificar_bajo_automatizado(self):
        """Score < 40 debe clasificar como AUTOMATIZADO"""
        assert clasificar_por_risk_score(20) == "AUTOMATIZADO"
        assert clasificar_por_risk_score(39) == "AUTOMATIZADO"
    
    def test_clasificar_medio_discrecional(self):
        """Score 40-59 debe clasificar como DISCRECIONAL"""
        assert clasificar_por_risk_score(40) == "DISCRECIONAL"
        assert clasificar_por_risk_score(55) == "DISCRECIONAL"
        assert clasificar_por_risk_score(59) == "DISCRECIONAL"
    
    def test_clasificar_alto_obligatorio(self):
        """Score >= 60 debe clasificar como OBLIGATORIO"""
        assert clasificar_por_risk_score(60) == "OBLIGATORIO"
        assert clasificar_por_risk_score(85) == "OBLIGATORIO"
        assert clasificar_por_risk_score(100) == "OBLIGATORIO"
