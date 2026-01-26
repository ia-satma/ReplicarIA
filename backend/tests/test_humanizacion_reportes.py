"""
Tests para el sistema de humanización de reportes
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.agents.personas import (
    PERSONA_VALIDADOR_DOCUMENTAL,
    PERSONA_AUDITOR_SAT,
    PERSONA_A1_ESTRATEGIA,
    PERSONA_A2_PMO,
    PERSONA_A3_FISCAL,
    obtener_persona
)
from services.agents.report_generator import humanizar_reporte


class TestPersonas:
    """Tests para las personas profesionales"""
    
    def test_persona_tiene_atributos_requeridos(self):
        """Cada persona debe tener todos los atributos necesarios"""
        persona = PERSONA_VALIDADOR_DOCUMENTAL
        
        assert persona.nombre is not None
        assert persona.titulo is not None
        assert persona.años_experiencia >= 0
        assert len(persona.frases_caracteristicas) > 0
    
    def test_obtener_persona_por_tipo(self):
        """Debe retornar persona correcta según tipo de agente"""
        persona_ocr = obtener_persona('ocr_validation')
        persona_rt = obtener_persona('red_team')
        
        assert persona_ocr.nombre == PERSONA_VALIDADOR_DOCUMENTAL.nombre
        assert persona_rt.nombre == PERSONA_AUDITOR_SAT.nombre
    
    def test_obtener_personas_agentes_principales(self):
        """Debe retornar personas correctas para A1-A8"""
        persona_a1 = obtener_persona('a1')
        persona_a2 = obtener_persona('a2')
        persona_a3 = obtener_persona('a3')
        
        assert persona_a1.nombre == PERSONA_A1_ESTRATEGIA.nombre
        assert persona_a2.nombre == PERSONA_A2_PMO.nombre
        assert persona_a3.nombre == PERSONA_A3_FISCAL.nombre
    
    def test_generar_introduccion(self):
        """La introducción debe ser coherente"""
        persona = PERSONA_AUDITOR_SAT
        intro = persona.generar_introduccion(
            tipo_reporte="simulación de auditoría fiscal",
            proyecto="Proyecto Test"
        )
        
        assert "Proyecto Test" in intro
        assert str(persona.años_experiencia) in intro
    
    def test_generar_cierre(self):
        """El cierre debe incluir nombre y título"""
        persona = PERSONA_A1_ESTRATEGIA
        cierre = persona.generar_cierre()
        
        assert persona.nombre in cierre
        assert persona.titulo in cierre


class TestHumanizacion:
    """Tests para la humanización de reportes"""
    
    @pytest.fixture
    def datos_ocr_exitoso(self):
        return {
            'document_name': 'Contrato_Servicios.pdf',
            'document_type': 'contrato',
            'status': 'VALIDATED',
            'confidence': 0.92,
            'iterations': 1,
            'keywords_found': ['CONTRATO', 'PARTES', 'OBJETO', 'FIRMA'],
            'keywords_missing': ['VIGENCIA'],
            'contradictions': []
        }
    
    @pytest.fixture
    def datos_red_team(self):
        return {
            'resumen': {
                'vectores_testeados': 6,
                'vectores_pasados': 4,
                'vulnerabilidades_encontradas': 2,
                'nivel_riesgo': 'MEDIUM'
            },
            'vulnerabilidades': [
                {
                    'severity': 'MEDIUM',
                    'message': 'Falta documentación de entregables tangibles',
                    'recommendation': 'Agregar evidencia fotográfica y actas de entrega'
                },
                {
                    'severity': 'LOW',
                    'message': 'Estudio de precios de transferencia no localizado',
                    'recommendation': 'Verificar si aplica por monto de operación'
                }
            ],
            'vectores_pasados': ['Razón de Negocios', 'Materialidad Básica', 'Documentación Contractual', 'Comprobación Fiscal'],
            'conclusion': 'DEFENDIBLE CON OBSERVACIONES',
            'score': 75
        }
    
    @pytest.fixture
    def datos_agente_principal(self):
        return {
            'decision': 'aprobado',
            'analisis': 'El proyecto cumple con los requisitos de alineación estratégica.',
            'recomendaciones': ['Documentar métricas de éxito', 'Establecer KPIs claros']
        }
    
    def test_humanizar_ocr_retorna_dict(self, datos_ocr_exitoso):
        """Debe retornar reporte en formato dict con todas las claves"""
        reporte = humanizar_reporte(
            tipo_agente='ocr_validation',
            datos_crudos=datos_ocr_exitoso,
            formato='dict'
        )
        
        assert isinstance(reporte, dict)
        assert 'reporte_markdown' in reporte
        assert 'reporte_html' in reporte
        assert 'metadata' in reporte
        assert 'resumen' in reporte
    
    def test_humanizar_ocr_contiene_documento(self, datos_ocr_exitoso):
        """Debe mencionar el documento analizado"""
        reporte = humanizar_reporte(
            tipo_agente='ocr_validation',
            datos_crudos=datos_ocr_exitoso,
            formato='dict'
        )
        
        markdown = reporte['reporte_markdown']
        assert 'Contrato_Servicios.pdf' in markdown
    
    def test_humanizar_ocr_retorna_html(self, datos_ocr_exitoso):
        """Debe retornar reporte en formato HTML"""
        reporte = humanizar_reporte(
            tipo_agente='ocr_validation',
            datos_crudos=datos_ocr_exitoso,
            formato='html'
        )
        
        assert '<div' in reporte['contenido']
        assert '</div>' in reporte['contenido']
    
    def test_humanizar_red_team_incluye_vulnerabilidades(self, datos_red_team):
        """El reporte Red Team debe mencionar las vulnerabilidades"""
        reporte = humanizar_reporte(
            tipo_agente='red_team',
            datos_crudos=datos_red_team,
            contexto={'proyecto': 'Proyecto Prueba'},
            formato='dict'
        )
        
        markdown = reporte['reporte_markdown']
        assert 'vulnerabilidad' in markdown.lower() or 'Vulnerabilidad' in markdown
    
    def test_humanizar_red_team_incluye_recomendaciones(self, datos_red_team):
        """El reporte debe incluir recomendaciones accionables"""
        reporte = humanizar_reporte(
            tipo_agente='red_team',
            datos_crudos=datos_red_team,
            contexto={'proyecto': 'Proyecto Prueba'},
            formato='dict'
        )
        
        markdown = reporte['reporte_markdown']
        assert 'recomend' in markdown.lower() or 'Recomend' in markdown
    
    def test_reporte_tiene_estructura_profesional(self, datos_red_team):
        """El reporte debe tener estructura de documento profesional"""
        resultado = humanizar_reporte(
            tipo_agente='red_team',
            datos_crudos=datos_red_team,
            contexto={'proyecto': 'Proyecto Prueba'},
            formato='dict'
        )
        
        markdown = resultado['reporte_markdown']
        
        assert '#' in markdown
        assert resultado['metadata']['persona'] is not None
        assert resultado['metadata']['titulo'] is not None
    
    def test_humanizar_agente_principal_a1(self, datos_agente_principal):
        """Debe generar reporte correcto para agente A1"""
        reporte = humanizar_reporte(
            tipo_agente='a1',
            datos_crudos=datos_agente_principal,
            contexto={'proyecto': 'Consultoría Estratégica 2024'},
            formato='dict'
        )
        
        assert reporte['metadata']['agente'] == 'a1'
        assert 'María' in reporte['metadata']['persona'] or 'Estrategia' in reporte['metadata']['titulo']
        assert 'aprobado' in reporte['reporte_markdown'].lower()
    
    def test_humanizar_agente_principal_a3(self, datos_agente_principal):
        """Debe generar reporte correcto para agente A3 Fiscal"""
        reporte = humanizar_reporte(
            tipo_agente='a3',
            datos_crudos=datos_agente_principal,
            contexto={'proyecto': 'Auditoría Fiscal 2024'},
            formato='dict'
        )
        
        assert reporte['metadata']['agente'] == 'a3'
        assert 'Laura' in reporte['metadata']['persona'] or 'Fiscal' in reporte['metadata']['titulo']
    
    def test_metadata_incluye_timestamp(self, datos_ocr_exitoso):
        """La metadata debe incluir timestamp de generación"""
        reporte = humanizar_reporte(
            tipo_agente='ocr_validation',
            datos_crudos=datos_ocr_exitoso,
            formato='dict'
        )
        
        assert 'generado' in reporte['metadata']
        assert reporte['metadata']['generado'] is not None
    
    def test_no_usa_palabras_prohibidas(self, datos_red_team):
        """El reporte no debe usar terminología inapropiada"""
        reporte = humanizar_reporte(
            tipo_agente='red_team',
            datos_crudos=datos_red_team,
            formato='dict'
        )
        
        markdown = reporte['reporte_markdown']
        palabras_prohibidas = ['FRAUDE', 'EVASIÓN', 'ILEGAL', 'DELITO']
        
        for palabra in palabras_prohibidas:
            assert palabra not in markdown.upper(), f"Encontrada palabra prohibida: {palabra}"
    
    def test_formato_markdown_retorna_contenido(self, datos_ocr_exitoso):
        """Formato markdown debe retornar contenido en clave 'contenido'"""
        reporte = humanizar_reporte(
            tipo_agente='ocr_validation',
            datos_crudos=datos_ocr_exitoso,
            formato='markdown'
        )
        
        assert 'contenido' in reporte
        assert isinstance(reporte['contenido'], str)


class TestPersonasCompletas:
    """Tests para verificar que todas las personas A1-A8 están configuradas"""
    
    def test_todos_los_agentes_principales_tienen_persona(self):
        """Cada agente A1-A8 debe tener una persona asignada"""
        agentes = ['a1', 'a2', 'a3', 'a4', 'a5', 'a6', 'a7', 'a8']
        
        for agente in agentes:
            persona = obtener_persona(agente)
            assert persona is not None, f"Agente {agente} no tiene persona asignada"
            assert persona.nombre is not None, f"Agente {agente} no tiene nombre"
            assert persona.titulo is not None, f"Agente {agente} no tiene título"
    
    def test_personas_tienen_frases_caracteristicas(self):
        """Cada persona debe tener frases características"""
        agentes = ['a1', 'a2', 'a3', 'a4', 'a5', 'a6', 'a7', 'a8']
        
        for agente in agentes:
            persona = obtener_persona(agente)
            assert len(persona.frases_caracteristicas) >= 3, \
                f"Agente {agente} tiene menos de 3 frases características"
    
    def test_personas_tienen_tono_comunicacion(self):
        """Cada persona debe tener un tono de comunicación definido"""
        agentes = ['a1', 'a2', 'a3', 'a4', 'a5', 'a6', 'a7', 'a8']
        
        for agente in agentes:
            persona = obtener_persona(agente)
            assert persona.tono is not None, f"Agente {agente} no tiene tono definido"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
