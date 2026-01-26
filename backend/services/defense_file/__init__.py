"""
Defense File Generator Package
Generación de expedientes de defensa fiscal profesionales
"""

from .styles import (
    COLORS,
    PAGE_CONFIG,
    FONTS,
    get_styles,
    SEVERITY_COLORS,
    STATUS_COLORS,
    LEGAL_TEXTS,
    ZIP_STRUCTURE
)

from .pdf_generator import PDFGenerator
from .generator import DefenseFileGenerator, DefenseFileConfig, DefenseFileResult, defense_file_generator

__all__ = [
    'COLORS',
    'PAGE_CONFIG', 
    'FONTS',
    'get_styles',
    'SEVERITY_COLORS',
    'STATUS_COLORS',
    'LEGAL_TEXTS',
    'ZIP_STRUCTURE',
    'PDFGenerator',
    'DefenseFileGenerator',
    'DefenseFileConfig',
    'DefenseFileResult',
    'defense_file_generator'
]
