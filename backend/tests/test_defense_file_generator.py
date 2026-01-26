"""
Tests para Defense File Generator
"""

import pytest
import asyncio
import os
import json
from datetime import datetime

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.defense_file import (
    DefenseFileGenerator,
    DefenseFileConfig,
    defense_file_generator
)


class TestDefenseFileGenerator:
    """Tests para el generador de expedientes"""
    
    @pytest.fixture
    def sample_project_data(self):
        return {
            'id': 'TEST001',
            'nombre': 'Proyecto de Prueba',
            'cliente': 'Empresa Test S.A. de C.V.',
            'rfc': 'ETE123456ABC',
            'periodo_fiscal': '2024',
            'risk_score': 35,
            'usuario': 'test_user'
        }
    
    @pytest.fixture
    def sample_documents(self):
        return [
            {
                'nombre': 'Contrato de Servicios',
                'tipo': 'contrato',
                'status': 'VALIDATED',
                'file_path': None
            },
            {
                'nombre': 'Factura CFDI',
                'tipo': 'factura',
                'status': 'VALIDATED',
                'file_path': None
            },
            {
                'nombre': 'Comprobante de Pago',
                'tipo': 'comprobante_pago',
                'status': 'PENDING',
                'file_path': None
            }
        ]
    
    @pytest.fixture
    def sample_ocr_results(self):
        return [
            {
                'document_name': 'Contrato de Servicios',
                'status': 'VALIDATED',
                'confidence': 0.95,
                'iterations': 1,
                'keywords_found': ['CONTRATO', 'PARTES', 'OBJETO']
            },
            {
                'document_name': 'Factura CFDI',
                'status': 'VALIDATED',
                'confidence': 0.88,
                'iterations': 2,
                'keywords_found': ['CFDI', 'RFC', 'TOTAL']
            }
        ]
    
    @pytest.fixture
    def sample_red_team_results(self):
        return {
            'resumen': {
                'vectores_testeados': 5,
                'vectores_pasados': 4,
                'vulnerabilidades_encontradas': 1,
                'nivel_riesgo': 'LOW'
            },
            'vulnerabilidades': [
                {
                    'severity': 'LOW',
                    'message': 'Falta estudio de precios de transferencia',
                    'recommendation': 'Considerar elaborar EPT si aplica'
                }
            ],
            'conclusion': 'DEFENDIBLE'
        }
    
    @pytest.mark.asyncio
    async def test_generator_initialization(self):
        """El generador debe inicializarse correctamente"""
        generator = DefenseFileGenerator()
        assert generator.output_dir is not None
        assert os.path.exists(generator.output_dir)
    
    @pytest.mark.asyncio
    async def test_generate_pdf_only(
        self,
        sample_project_data,
        sample_documents,
        sample_ocr_results,
        sample_red_team_results
    ):
        """Debe generar solo PDF cuando se configura así"""
        config = DefenseFileConfig(
            output_format='pdf',
            generate_zip=False
        )
        
        generator = DefenseFileGenerator()
        result = await generator.generate(
            project_data=sample_project_data,
            documents=sample_documents,
            ocr_results=sample_ocr_results,
            red_team_results=sample_red_team_results,
            config=config
        )
        
        assert result.success is True
        assert result.pdf_path is not None
        assert os.path.exists(result.pdf_path)
        assert result.total_pages > 0
        
        if result.pdf_path and os.path.exists(result.pdf_path):
            os.remove(result.pdf_path)
    
    @pytest.mark.asyncio
    async def test_generate_full_package(
        self,
        sample_project_data,
        sample_documents,
        sample_ocr_results,
        sample_red_team_results
    ):
        """Debe generar PDF y ZIP completos"""
        generator = DefenseFileGenerator()
        result = await generator.generate(
            project_data=sample_project_data,
            documents=sample_documents,
            ocr_results=sample_ocr_results,
            red_team_results=sample_red_team_results
        )
        
        assert result.success is True
        assert result.pdf_path is not None
        assert result.zip_path is not None
        assert len(result.file_hashes) > 0
        
        if result.zip_path and os.path.exists(result.zip_path):
            import zipfile
            with zipfile.ZipFile(result.zip_path, 'r') as zf:
                names = zf.namelist()
                assert any('01_CARATULA' in n for n in names)
                assert any('02_INDICE' in n for n in names)
                assert any('10_METADATOS' in n for n in names)
        
        for path in [result.pdf_path, result.zip_path]:
            if path and os.path.exists(path):
                os.remove(path)
    
    @pytest.mark.asyncio
    async def test_folio_generation(self, sample_project_data):
        """El folio debe generarse con formato correcto"""
        generator = DefenseFileGenerator()
        folio = generator._generate_folio(sample_project_data)
        
        assert folio.startswith('DEF-')
        assert len(folio) == 12  # DEF- + 8 chars
    
    @pytest.mark.asyncio
    async def test_risk_level_calculation(self):
        """Los niveles de riesgo deben calcularse correctamente"""
        generator = DefenseFileGenerator()
        
        assert generator._get_risk_level(85) == 'CRITICAL'
        assert generator._get_risk_level(65) == 'HIGH'
        assert generator._get_risk_level(45) == 'MEDIUM'
        assert generator._get_risk_level(25) == 'LOW'
    
    @pytest.mark.asyncio
    async def test_folder_mapping(self):
        """Los tipos de documento deben mapearse a carpetas correctas"""
        generator = DefenseFileGenerator()
        
        assert generator._get_folder_for_type('contrato') == '03_CONTRATOS'
        assert generator._get_folder_for_type('factura') == '04_FACTURAS'
        assert generator._get_folder_for_type('cfdi') == '04_FACTURAS'
        assert generator._get_folder_for_type('comprobante') == '05_COMPROBANTES_PAGO'
        assert generator._get_folder_for_type('entregable') == '06_ENTREGABLES'
        assert generator._get_folder_for_type('correo') == '07_CORRESPONDENCIA'


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
