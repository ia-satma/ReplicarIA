"""
Vision Agent - Validación de documentos PDF
PROPÓSITO: Leer contenido real de PDFs y validar coherencia
con metadata de la base de datos para Revisar.IA
"""

import re
import io
import logging
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, field
from datetime import datetime
import PyPDF2

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Resultado de validación de documento"""
    score: int = 100
    keywords_found: Dict[str, bool] = field(default_factory=dict)
    keywords_missing: List[str] = field(default_factory=list)
    inconsistencies: List[str] = field(default_factory=list)
    raw_text: str = ""
    page_count: int = 0
    extraction_method: str = "PyPDF2"
    validated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "score": self.score,
            "keywords_found": self.keywords_found,
            "keywords_missing": self.keywords_missing,
            "inconsistencies": self.inconsistencies,
            "raw_text": self.raw_text,
            "page_count": self.page_count,
            "extraction_method": self.extraction_method,
            "validated_at": self.validated_at
        }


class VisionAgent:
    """
    Agente de visión para validación de documentos PDF.
    Extrae texto, verifica keywords obligatorias y cruza datos con BD.
    """
    
    REQUIRED_KEYWORDS = {
        "contrato": ["CLÁUSULA", "OBJETO", "PARTES", "VIGENCIA", "FIRMA"],
        "factura": ["RFC", "TOTAL", "FECHA", "UUID", "CFDI"],
        "comprobante": ["TRANSFERENCIA", "CUENTA", "IMPORTE", "BANCO"],
        "sow": ["ALCANCE", "ENTREGABLES", "CRONOGRAMA", "PRECIO"],
        "cotizacion": ["COTIZACIÓN", "PRECIO", "CONCEPTO", "VIGENCIA"],
        "acta": ["ACTA", "REUNIÓN", "ACUERDOS", "FECHA", "ASISTENTES"],
        "reporte": ["REPORTE", "ANÁLISIS", "CONCLUSIONES", "RECOMENDACIONES"],
        "evidencia": ["EVIDENCIA", "FECHA", "DESCRIPCIÓN"],
        "bee": ["BENEFICIO", "ECONÓMICO", "EMPRESA", "ROI", "AHORRO"],
        "defensa": ["DEFENSA", "MATERIALIDAD", "TRAZABILIDAD", "FISCAL"]
    }
    
    AMOUNT_PATTERNS = [
        r'\$[\d,]+(?:\.\d{2})?',
        r'MXN[\s:]*[\d,]+(?:\.\d{2})?',
        r'TOTAL[\s:]*\$?[\d,]+(?:\.\d{2})?',
        r'MONTO[\s:]*\$?[\d,]+(?:\.\d{2})?',
        r'IMPORTE[\s:]*\$?[\d,]+(?:\.\d{2})?'
    ]
    
    DATE_PATTERNS = [
        r'\d{1,2}/\d{1,2}/\d{4}',
        r'\d{1,2}-\d{1,2}-\d{4}',
        r'\d{4}-\d{2}-\d{2}',
        r'\d{1,2}\s+de\s+\w+\s+de\s+\d{4}'
    ]
    
    RFC_PATTERN = r'[A-ZÑ&]{3,4}\d{6}[A-Z0-9]{3}'
    UUID_PATTERN = r'[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}'
    
    def __init__(self):
        self.extraction_method = "PyPDF2"
        logger.info("VisionAgent inicializado con PyPDF2")
    
    def _extract_text_from_pdf(self, file_content: bytes) -> tuple[str, int]:
        """Extrae texto de PDF usando PyPDF2"""
        try:
            pdf_file = io.BytesIO(file_content)
            reader = PyPDF2.PdfReader(pdf_file)
            page_count = len(reader.pages)
            
            text_parts = []
            for page in reader.pages:
                page_text = page.extract_text() or ""
                text_parts.append(page_text)
            
            full_text = "\n".join(text_parts)
            logger.info(f"Extraído texto de {page_count} páginas ({len(full_text)} caracteres)")
            return full_text, page_count
            
        except Exception as e:
            logger.error(f"Error extrayendo texto de PDF: {e}")
            return "", 0
    
    def _extract_text_from_path(self, file_path: str) -> tuple[str, int]:
        """Extrae texto de un archivo PDF por ruta"""
        try:
            with open(file_path, 'rb') as f:
                return self._extract_text_from_pdf(f.read())
        except Exception as e:
            logger.error(f"Error leyendo archivo {file_path}: {e}")
            return "", 0
    
    def _check_keywords(self, text: str, doc_type: str) -> Dict[str, bool]:
        """Verifica presencia de keywords obligatorias"""
        text_upper = text.upper()
        keywords = self.REQUIRED_KEYWORDS.get(doc_type.lower(), [])
        
        results = {}
        for keyword in keywords:
            found = keyword.upper() in text_upper
            results[keyword] = found
            
        return results
    
    def _normalize_amount(self, amount_str: str) -> float:
        """Normaliza un string de monto a float"""
        cleaned = re.sub(r'[^\d.]', '', amount_str.replace(',', ''))
        try:
            return float(cleaned) if cleaned else 0.0
        except ValueError:
            return 0.0
    
    def _find_amounts(self, text: str) -> List[float]:
        """Encuentra todos los montos en el texto"""
        amounts = []
        for pattern in self.AMOUNT_PATTERNS:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                amount = self._normalize_amount(match)
                if amount > 0:
                    amounts.append(amount)
        return amounts
    
    def _find_amount(self, text: str, expected_amount: float, tolerance: float = 0.05) -> bool:
        """Busca un monto específico en el texto con tolerancia del 5%"""
        amounts = self._find_amounts(text)
        for amount in amounts:
            if abs(amount - expected_amount) / max(expected_amount, 1) <= tolerance:
                return True
        return False
    
    def _find_dates(self, text: str) -> List[str]:
        """Encuentra todas las fechas en el texto"""
        dates = []
        for pattern in self.DATE_PATTERNS:
            matches = re.findall(pattern, text, re.IGNORECASE)
            dates.extend(matches)
        return dates
    
    def _normalize_date(self, date_str: str) -> Optional[str]:
        """Normaliza fecha a formato YYYY-MM-DD"""
        date_formats = [
            "%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d",
            "%m/%d/%Y", "%Y/%m/%d"
        ]
        
        for fmt in date_formats:
            try:
                dt = datetime.strptime(date_str.strip(), fmt)
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                continue
        return None
    
    def _find_date(self, text: str, expected_date: str) -> bool:
        """Busca una fecha específica en el texto"""
        expected_normalized = self._normalize_date(expected_date)
        if not expected_normalized:
            return False
            
        dates_found = self._find_dates(text)
        for date_str in dates_found:
            normalized = self._normalize_date(date_str)
            if normalized == expected_normalized:
                return True
        return False
    
    def _find_rfc(self, text: str, expected_rfc: Optional[str] = None) -> tuple[List[str], bool]:
        """Encuentra RFCs en el texto"""
        rfcs = re.findall(self.RFC_PATTERN, text.upper())
        if expected_rfc:
            return rfcs, expected_rfc.upper() in [r.upper() for r in rfcs]
        return rfcs, len(rfcs) > 0
    
    def _find_uuid(self, text: str, expected_uuid: Optional[str] = None) -> tuple[List[str], bool]:
        """Encuentra UUIDs en el texto"""
        uuids = re.findall(self.UUID_PATTERN, text, re.IGNORECASE)
        if expected_uuid:
            return uuids, expected_uuid.lower() in [u.lower() for u in uuids]
        return uuids, len(uuids) > 0
    
    def validate_document(
        self,
        file_content: Optional[bytes] = None,
        file_path: Optional[str] = None,
        doc_type: str = "contrato",
        expected_data: Optional[Dict[str, Any]] = None
    ) -> ValidationResult:
        """
        Valida un documento PDF completo.
        
        Args:
            file_content: Contenido binario del PDF
            file_path: Ruta al archivo PDF (alternativa a file_content)
            doc_type: Tipo de documento (contrato, factura, sow, etc.)
            expected_data: Datos esperados para validación cruzada
                - monto: Monto esperado
                - fecha: Fecha esperada
                - proveedor: Nombre del proveedor
                - rfc: RFC esperado
                - uuid: UUID de CFDI esperado
        
        Returns:
            ValidationResult con score, keywords encontradas e inconsistencias
        """
        expected_data = expected_data or {}
        inconsistencies = []
        
        if file_content:
            text, page_count = self._extract_text_from_pdf(file_content)
        elif file_path:
            text, page_count = self._extract_text_from_path(file_path)
        else:
            return ValidationResult(
                score=0,
                inconsistencies=["❌ No se proporcionó contenido de documento"]
            )
        
        if not text.strip():
            return ValidationResult(
                score=20,
                page_count=page_count,
                inconsistencies=["⚠️ No se pudo extraer texto del PDF (puede ser imagen/escaneado)"],
                extraction_method=self.extraction_method
            )
        
        keywords_found = self._check_keywords(text, doc_type)
        keywords_missing = [k for k, v in keywords_found.items() if not v]
        
        if keywords_missing:
            missing_pct = len(keywords_missing) / max(len(keywords_found), 1)
            if missing_pct > 0.5:
                inconsistencies.append(
                    f"⚠️ Faltan {len(keywords_missing)} keywords obligatorias: {', '.join(keywords_missing)}"
                )
        
        if "monto" in expected_data and expected_data["monto"]:
            expected_amount = float(expected_data["monto"])
            if not self._find_amount(text, expected_amount):
                amounts_found = self._find_amounts(text)
                inconsistencies.append(
                    f"⚠️ Monto esperado ${expected_amount:,.2f} no encontrado. "
                    f"Montos detectados: {', '.join(f'${a:,.2f}' for a in amounts_found[:5])}"
                )
        
        if "fecha" in expected_data and expected_data["fecha"]:
            if not self._find_date(text, expected_data["fecha"]):
                dates_found = self._find_dates(text)
                inconsistencies.append(
                    f"⚠️ Fecha esperada {expected_data['fecha']} no coincide. "
                    f"Fechas detectadas: {', '.join(dates_found[:5])}"
                )
        
        if "rfc" in expected_data and expected_data["rfc"]:
            rfcs, found = self._find_rfc(text, expected_data["rfc"])
            if not found:
                inconsistencies.append(
                    f"⚠️ RFC esperado {expected_data['rfc']} no encontrado. "
                    f"RFCs detectados: {', '.join(rfcs[:3])}"
                )
        
        if "uuid" in expected_data and expected_data["uuid"]:
            uuids, found = self._find_uuid(text, expected_data["uuid"])
            if not found:
                inconsistencies.append(
                    f"⚠️ UUID CFDI esperado no encontrado en documento."
                )
        
        if "proveedor" in expected_data and expected_data["proveedor"]:
            proveedor = expected_data["proveedor"].upper()
            if proveedor not in text.upper():
                words = proveedor.split()
                words_found = sum(1 for w in words if w in text.upper())
                if words_found < len(words) * 0.5:
                    inconsistencies.append(
                        f"⚠️ Nombre de proveedor '{expected_data['proveedor']}' no encontrado claramente"
                    )
        
        base_score = 100
        base_score -= len(inconsistencies) * 15
        base_score -= len(keywords_missing) * 5
        score = max(0, min(100, base_score))
        
        return ValidationResult(
            score=score,
            keywords_found=keywords_found,
            keywords_missing=keywords_missing,
            inconsistencies=inconsistencies,
            raw_text=text[:1000],
            page_count=page_count,
            extraction_method=self.extraction_method
        )
    
    def validate_f5_document(
        self,
        file_content: bytes,
        project_data: Dict[str, Any]
    ) -> ValidationResult:
        """
        Validación específica para Fase F5 (Entrega Final).
        Integra validación de contrato con datos del proyecto.
        
        Args:
            file_content: Contenido del documento subido
            project_data: Datos del proyecto para validación cruzada
        
        Returns:
            ValidationResult con evaluación completa
        """
        expected_data = {
            "monto": project_data.get("budget") or project_data.get("presupuesto"),
            "fecha": project_data.get("start_date") or project_data.get("fecha_inicio"),
            "proveedor": project_data.get("vendor_name") or project_data.get("proveedor"),
            "rfc": project_data.get("vendor_rfc") or project_data.get("rfc_proveedor")
        }
        
        expected_data = {k: v for k, v in expected_data.items() if v}
        
        doc_type = project_data.get("document_type", "contrato")
        
        result = self.validate_document(
            file_content=file_content,
            doc_type=doc_type,
            expected_data=expected_data
        )
        
        if result.score < 70:
            result.inconsistencies.insert(0, 
                f"🚨 Documento sospechoso (score: {result.score}/100) - Requiere revisión manual"
            )
        
        return result
    
    def validate_cfdi(self, file_content: bytes, expected_data: Dict[str, Any]) -> ValidationResult:
        """Validación específica para facturas CFDI"""
        return self.validate_document(
            file_content=file_content,
            doc_type="factura",
            expected_data=expected_data
        )
    
    def validate_sow(self, file_content: bytes, expected_data: Dict[str, Any]) -> ValidationResult:
        """Validación específica para SOW (Statement of Work)"""
        return self.validate_document(
            file_content=file_content,
            doc_type="sow",
            expected_data=expected_data
        )
    
    def validate_bee(self, file_content: bytes, expected_data: Dict[str, Any]) -> ValidationResult:
        """Validación específica para documentos BEE (Beneficio Económico Empresa)"""
        return self.validate_document(
            file_content=file_content,
            doc_type="bee",
            expected_data=expected_data
        )


vision_agent = VisionAgent()


def check_f5_completion(uploaded_file_content: bytes, project_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Función helper para integración en Fase F5.
    Valida documento subido contra datos del proyecto.
    
    Raises:
        ValueError si el documento no pasa validación (score < 70)
    """
    result = vision_agent.validate_f5_document(uploaded_file_content, project_data)
    
    if result.score < 70:
        raise ValueError(
            f"Documento sospechoso (score: {result.score}/100)\n"
            f"Inconsistencias: {chr(10).join(result.inconsistencies)}"
        )
    
    return result.to_dict()
