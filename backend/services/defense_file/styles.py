"""
ESTILOS Y CONSTANTES PARA EXPEDIENTE DE DEFENSA
Colores, fuentes y formatos consistentes con estándares legales mexicanos
"""

from reportlab.lib.colors import HexColor, black, white, gray
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.units import inch, cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY

# === COLORES CORPORATIVOS ===
COLORS = {
    'primary': HexColor('#1a365d'),      # Azul oscuro (confianza)
    'secondary': HexColor('#2c5282'),    # Azul medio
    'accent': HexColor('#3182ce'),       # Azul claro
    'success': HexColor('#276749'),      # Verde (validado)
    'warning': HexColor('#c05621'),      # Naranja (atención)
    'danger': HexColor('#c53030'),       # Rojo (crítico)
    'light_gray': HexColor('#e2e8f0'),   # Gris claro (fondos)
    'dark_gray': HexColor('#4a5568'),    # Gris oscuro (texto secundario)
    'text': HexColor('#1a202c'),         # Negro suave (texto principal)
    'white': white,
    'black': black,
}

# === CONFIGURACIÓN DE PÁGINA ===
PAGE_CONFIG = {
    'size': letter,  # 8.5 x 11 pulgadas (estándar México)
    'margin_top': 1 * inch,
    'margin_bottom': 0.75 * inch,
    'margin_left': 1 * inch,
    'margin_right': 1 * inch,
}

# === FUENTES ===
# Usamos Helvetica porque está disponible en todos los sistemas
FONTS = {
    'title': ('Helvetica-Bold', 24),
    'subtitle': ('Helvetica-Bold', 16),
    'heading': ('Helvetica-Bold', 14),
    'subheading': ('Helvetica-Bold', 12),
    'body': ('Helvetica', 11),
    'body_bold': ('Helvetica-Bold', 11),
    'small': ('Helvetica', 9),
    'tiny': ('Helvetica', 8),
    'monospace': ('Courier', 10),
}

# === ESTILOS DE PÁRRAFO ===
def get_styles():
    """Retorna diccionario de estilos de párrafo personalizados"""
    styles = getSampleStyleSheet()
    
    custom_styles = {
        'Title': ParagraphStyle(
            'CustomTitle',
            parent=styles['Title'],
            fontName='Helvetica-Bold',
            fontSize=24,
            textColor=COLORS['primary'],
            spaceAfter=20,
            alignment=TA_CENTER,
        ),
        'Subtitle': ParagraphStyle(
            'CustomSubtitle',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=16,
            textColor=COLORS['secondary'],
            spaceAfter=12,
            alignment=TA_CENTER,
        ),
        'Heading1': ParagraphStyle(
            'CustomHeading1',
            parent=styles['Heading1'],
            fontName='Helvetica-Bold',
            fontSize=14,
            textColor=COLORS['primary'],
            spaceBefore=16,
            spaceAfter=8,
            borderPadding=4,
        ),
        'Heading2': ParagraphStyle(
            'CustomHeading2',
            parent=styles['Heading2'],
            fontName='Helvetica-Bold',
            fontSize=12,
            textColor=COLORS['secondary'],
            spaceBefore=12,
            spaceAfter=6,
        ),
        'Body': ParagraphStyle(
            'CustomBody',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=11,
            textColor=COLORS['text'],
            spaceAfter=8,
            alignment=TA_JUSTIFY,
            leading=14,
        ),
        'BodyBold': ParagraphStyle(
            'CustomBodyBold',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=11,
            textColor=COLORS['text'],
            spaceAfter=8,
        ),
        'Small': ParagraphStyle(
            'CustomSmall',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=9,
            textColor=COLORS['dark_gray'],
            spaceAfter=4,
        ),
        'Footer': ParagraphStyle(
            'CustomFooter',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=8,
            textColor=COLORS['dark_gray'],
            alignment=TA_CENTER,
        ),
        'TableHeader': ParagraphStyle(
            'CustomTableHeader',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=10,
            textColor=COLORS['white'],
            alignment=TA_CENTER,
        ),
        'TableCell': ParagraphStyle(
            'CustomTableCell',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=9,
            textColor=COLORS['text'],
            alignment=TA_LEFT,
        ),
        'Legal': ParagraphStyle(
            'CustomLegal',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=8,
            textColor=COLORS['dark_gray'],
            alignment=TA_JUSTIFY,
            leading=10,
        ),
    }
    
    return custom_styles


# === MAPEO DE SEVERIDADES A COLORES ===
SEVERITY_COLORS = {
    'CRITICAL': COLORS['danger'],
    'HIGH': HexColor('#dd6b20'),  # Naranja oscuro
    'MEDIUM': COLORS['warning'],
    'LOW': HexColor('#d69e2e'),   # Amarillo
    'INFO': COLORS['accent'],
    'SUCCESS': COLORS['success'],
}

# === MAPEO DE ESTADOS A COLORES ===
STATUS_COLORS = {
    'VALIDATED': COLORS['success'],
    'PASSED': COLORS['success'],
    'COMPLETE': COLORS['success'],
    'PENDING': COLORS['warning'],
    'REQUIRES_REVIEW': COLORS['warning'],
    'FAILED': COLORS['danger'],
    'CRITICAL': COLORS['danger'],
    'MISSING': COLORS['danger'],
}

# === TEXTOS LEGALES ===
LEGAL_TEXTS = {
    'confidentiality': """
    AVISO DE CONFIDENCIALIDAD: Este documento contiene información privilegiada y 
    confidencial destinada únicamente para uso del destinatario. Cualquier revisión, 
    difusión, distribución u otro uso de esta información por personas o entidades 
    distintas al destinatario está prohibida. Si usted recibió este documento por 
    error, favor de notificar inmediatamente y destruir el original.
    """,
    
    'integrity': """
    DECLARACIÓN DE INTEGRIDAD: Este expediente fue generado automáticamente por el 
    sistema Revisar.IA. Los hashes de integridad y timestamps incluidos permiten 
    verificar que los documentos no han sido alterados desde su generación.
    """,
    
    'legal_basis': """
    FUNDAMENTO LEGAL: Este expediente se presenta conforme a los artículos 5-A y 69-B 
    del Código Fiscal de la Federación, artículo 27 de la Ley del Impuesto Sobre la 
    Renta, y la NOM-151-SCFI-2016 sobre conservación de mensajes de datos.
    """,
}

# === ESTRUCTURA DE CARPETAS PARA ZIP ===
ZIP_STRUCTURE = {
    '01_CARATULA': 'Carátula y resumen ejecutivo',
    '02_INDICE': 'Índice de documentos y checklist',
    '03_CONTRATOS': 'Contratos y anexos',
    '04_FACTURAS': 'CFDI y complementos de pago',
    '05_COMPROBANTES_PAGO': 'Comprobantes de transferencia/pago',
    '06_ENTREGABLES': 'Evidencia de entregables',
    '07_CORRESPONDENCIA': 'Correos y comunicaciones',
    '08_VALIDACIONES': 'Reportes de validación OCR',
    '09_RED_TEAM': 'Reporte de simulación SAT',
    '10_METADATOS': 'Hashes e información de integridad',
}
