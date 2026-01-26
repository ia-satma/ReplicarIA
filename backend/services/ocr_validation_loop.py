"""
OCR VALIDATION LOOP
Valida que los documentos PDF contienen la información esperada
Itera hasta confirmar consistencia o agotar intentos
"""

import re
import logging
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from pathlib import Path

from services.loop_orchestrator import LoopOrchestrator, LoopResult

logger = logging.getLogger(__name__)

REQUIRED_KEYWORDS = {
    "contrato": ["CONTRATO", "PARTES", "OBJETO", "CLÁUSULA", "FIRMA"],
    "factura": ["CFDI", "RFC", "TOTAL", "FECHA", "FOLIO"],
    "comprobante_pago": ["PAGO", "MONTO", "FECHA", "REFERENCIA"],
    "evidencia_entrega": ["ENTREGA", "RECIBIDO", "FECHA", "FIRMA"],
    "sow": ["ALCANCE", "ENTREGABLES", "CRONOGRAMA", "PRECIO"],
    "cotizacion": ["COTIZACIÓN", "PRECIO", "VIGENCIA", "DESCRIPCIÓN"],
    "acta": ["ACTA", "ASISTENTES", "ACUERDOS", "FECHA"],
    "reporte": ["REPORTE", "ANÁLISIS", "RESULTADOS", "CONCLUSIONES"],
    "bee": ["BENEFICIO", "ECONÓMICO", "ESPERADO", "IMPACTO"],
    "defensa": ["DEFENSA", "EXPEDIENTE", "FUNDAMENTOS", "EVIDENCIA"]
}

CONFIDENCE_THRESHOLD = 0.7
MAX_OCR_ATTEMPTS = 3


@dataclass
class OCRValidationResult:
    status: str
    confidence: float
    extracted_data: Dict[str, Any]
    findings: List[Dict[str, Any]]
    contradictions: List[str]
    iterations: int
    requires_human_review: bool


class OCRValidationLoop:
    """
    Loop de validación OCR para documentos PDF
    Itera con diferentes estrategias hasta validar o requerir revisión humana
    """
    
    def __init__(self):
        self.orchestrator = LoopOrchestrator(
            max_iterations=MAX_OCR_ATTEMPTS,
            timeout_seconds=120,
            completion_marker="VALIDATED",
            delay_between_iterations=0.5
        )
        self.strategies = ["standard", "enhanced", "aggressive"]
    
    async def validate_document(
        self,
        document_path: str,
        document_type: str,
        expected_data: Optional[Dict[str, Any]] = None
    ) -> OCRValidationResult:
        """
        Valida un documento específico con OCR iterativo
        
        Args:
            document_path: Ruta al archivo PDF
            document_type: Tipo de documento (contrato, factura, etc.)
            expected_data: Datos esperados para cross-validation
        """
        expected_data = expected_data or {}
        
        context = {
            "document_path": document_path,
            "document_type": document_type,
            "expected_data": expected_data,
            "strategy": "standard",
            "findings": []
        }
        
        result = await self.orchestrator.execute_loop(
            self._ocr_validation_task,
            context,
            task_name=f"OCR Validation: {Path(document_path).name}"
        )
        
        final_result = result.result or {}
        
        return OCRValidationResult(
            status=final_result.get("status", "FAILED"),
            confidence=final_result.get("confidence", 0.0),
            extracted_data=final_result.get("extracted_data", {}),
            findings=final_result.get("findings", []),
            contradictions=final_result.get("contradictions", []),
            iterations=result.iterations,
            requires_human_review=final_result.get("status") == "REQUIRES_HUMAN_REVIEW"
        )
    
    async def _ocr_validation_task(self, context: Dict, iteration: int) -> Dict[str, Any]:
        """Tarea de validación OCR ejecutada en cada iteración"""
        document_path = context["document_path"]
        document_type = context["document_type"]
        expected_data = context["expected_data"]
        
        current_strategy = self.strategies[min(iteration - 1, len(self.strategies) - 1)]
        logger.info(f"[OCR] Iteración {iteration}: Estrategia {current_strategy}")
        
        extracted_text = await self._extract_text_from_pdf(document_path, current_strategy)
        
        if not extracted_text or len(extracted_text.strip()) < 50:
            return {
                "status": "RETRY",
                "reason": "Texto extraído insuficiente",
                "next_strategy": self.strategies[min(iteration, len(self.strategies) - 1)],
                "findings": [{
                    "type": "OCR_FAILURE",
                    "severity": "HIGH",
                    "message": f"No se pudo extraer texto legible (intento {iteration})"
                }]
            }
        
        required_keywords = REQUIRED_KEYWORDS.get(document_type, [])
        found_keywords = [kw for kw in required_keywords if kw.upper() in extracted_text.upper()]
        keyword_confidence = len(found_keywords) / len(required_keywords) if required_keywords else 1.0
        
        cross_validation = self._cross_validate_data(extracted_text, expected_data)
        
        all_checks = {
            "keywords_found": keyword_confidence >= CONFIDENCE_THRESHOLD,
            "data_matches": cross_validation["match_rate"] >= 0.8,
            "no_contradictions": len(cross_validation["contradictions"]) == 0
        }
        
        passed_checks = sum(1 for v in all_checks.values() if v)
        total_checks = len(all_checks)
        
        if passed_checks == total_checks:
            return {
                "status": "VALIDATED",
                "complete": True,
                "confidence": (keyword_confidence + cross_validation["match_rate"]) / 2,
                "extracted_data": cross_validation["extracted_data"],
                "keywords_found": found_keywords,
                "keyword_confidence": keyword_confidence,
                "findings": [{
                    "type": "VALIDATION_SUCCESS",
                    "severity": "INFO",
                    "message": f"Documento validado con {keyword_confidence * 100:.0f}% de keywords"
                }]
            }
        
        if iteration >= MAX_OCR_ATTEMPTS:
            failed_checks = [k for k, v in all_checks.items() if not v]
            return {
                "status": "REQUIRES_HUMAN_REVIEW",
                "complete": True,
                "confidence": (keyword_confidence + cross_validation["match_rate"]) / 2,
                "failed_checks": failed_checks,
                "contradictions": cross_validation["contradictions"],
                "extracted_data": cross_validation["extracted_data"],
                "findings": [{
                    "type": "VALIDATION_INCONCLUSIVE",
                    "severity": "MEDIUM",
                    "message": f"Requiere revisión humana: {', '.join(failed_checks)}"
                }]
            }
        
        return {
            "status": "RETRY",
            "partial_confidence": keyword_confidence,
            "keywords_found": found_keywords,
            "keywords_missing": [kw for kw in required_keywords if kw not in found_keywords],
            "findings": [
                {"type": "DATA_MISMATCH", "severity": "MEDIUM", "message": c}
                for c in cross_validation["contradictions"]
            ]
        }
    
    async def _extract_text_from_pdf(self, file_path: str, strategy: str) -> str:
        """Extrae texto de un PDF usando PyPDF2"""
        try:
            import PyPDF2
            
            text_content = []
            with open(file_path, 'rb') as pdf_file:
                reader = PyPDF2.PdfReader(pdf_file)
                for page in reader.pages:
                    page_text = page.extract_text() or ""
                    text_content.append(page_text)
            
            full_text = "\n".join(text_content)
            
            if strategy == "enhanced":
                full_text = self._clean_text(full_text)
            elif strategy == "aggressive":
                full_text = self._aggressive_clean(full_text)
            
            return full_text
            
        except Exception as e:
            logger.error(f"Error extrayendo texto de PDF: {e}")
            return ""
    
    def _clean_text(self, text: str) -> str:
        """Limpieza estándar de texto"""
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'[^\w\s$.,;:()/-]', '', text)
        return text.strip()
    
    def _aggressive_clean(self, text: str) -> str:
        """Limpieza agresiva para documentos problemáticos"""
        text = self._clean_text(text)
        text = text.upper()
        text = re.sub(r'\d{10,}', '', text)
        return text
    
    def _cross_validate_data(self, text: str, expected_data: Dict[str, Any]) -> Dict[str, Any]:
        """Cross-valida datos extraídos vs esperados"""
        results = {
            "extracted_data": {},
            "match_rate": 0.0,
            "contradictions": []
        }
        
        if not expected_data:
            results["match_rate"] = 1.0
            return results
        
        matches = 0
        total = 0
        
        if "monto" in expected_data and expected_data["monto"]:
            total += 1
            monto_regex = r'\$?\s*([\d,]+\.?\d*)'
            montos = [float(m.replace(',', '')) for m in re.findall(monto_regex, text) if m]
            
            try:
                expected_monto = float(expected_data["monto"])
                monto_found = any(abs(m - expected_monto) / max(expected_monto, 1) < 0.01 for m in montos if m > 0)
                
                if monto_found:
                    matches += 1
                    results["extracted_data"]["monto"] = expected_monto
                elif montos:
                    results["contradictions"].append(
                        f"Monto esperado: ${expected_monto:,.2f}, encontrado: ${', $'.join(f'{m:,.2f}' for m in montos[:3])}"
                    )
            except (ValueError, TypeError):
                pass
        
        if "rfc_proveedor" in expected_data and expected_data["rfc_proveedor"]:
            total += 1
            rfc_regex = r'[A-ZÑ&]{3,4}\d{6}[A-Z0-9]{3}'
            rfcs = re.findall(rfc_regex, text.upper())
            
            if expected_data["rfc_proveedor"].upper() in rfcs:
                matches += 1
                results["extracted_data"]["rfc_proveedor"] = expected_data["rfc_proveedor"]
            elif rfcs:
                results["contradictions"].append(
                    f"RFC esperado: {expected_data['rfc_proveedor']}, encontrado: {', '.join(rfcs[:3])}"
                )
        
        if "fecha" in expected_data and expected_data["fecha"]:
            total += 1
            try:
                from datetime import datetime
                if isinstance(expected_data["fecha"], str):
                    fecha = datetime.fromisoformat(expected_data["fecha"].replace('Z', '+00:00'))
                else:
                    fecha = expected_data["fecha"]
                
                year_str = str(fecha.year)
                if year_str in text or year_str[-2:] in text:
                    matches += 1
                    results["extracted_data"]["fecha"] = expected_data["fecha"]
            except Exception:
                pass
        
        if "uuid" in expected_data and expected_data["uuid"]:
            total += 1
            uuid_regex = r'[A-F0-9]{8}-[A-F0-9]{4}-[A-F0-9]{4}-[A-F0-9]{4}-[A-F0-9]{12}'
            uuids = re.findall(uuid_regex, text.upper())
            
            if expected_data["uuid"].upper() in uuids:
                matches += 1
                results["extracted_data"]["uuid"] = expected_data["uuid"]
        
        results["match_rate"] = matches / total if total > 0 else 1.0
        return results
    
    async def validate_project_documents(
        self,
        project_id: str,
        documents: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Valida todos los documentos de un proyecto
        
        Args:
            project_id: ID del proyecto
            documents: Lista de documentos a validar
        """
        results = {
            "project_id": project_id,
            "total_documents": len(documents),
            "validated": 0,
            "requires_review": 0,
            "failed": 0,
            "document_results": []
        }
        
        for doc in documents:
            try:
                result = await self.validate_document(
                    document_path=doc.get("path", ""),
                    document_type=doc.get("type", "evidencia"),
                    expected_data=doc.get("expected_data", {})
                )
                
                doc_result = {
                    "document_id": doc.get("id"),
                    "document_name": doc.get("name"),
                    "status": result.status,
                    "confidence": result.confidence,
                    "iterations": result.iterations,
                    "findings": result.findings
                }
                
                if result.status == "VALIDATED":
                    results["validated"] += 1
                elif result.requires_human_review:
                    results["requires_review"] += 1
                else:
                    results["failed"] += 1
                
                results["document_results"].append(doc_result)
                
            except Exception as e:
                logger.error(f"Error validating document {doc.get('id')}: {e}")
                results["failed"] += 1
                results["document_results"].append({
                    "document_id": doc.get("id"),
                    "status": "ERROR",
                    "error": str(e)
                })
        
        results["success_rate"] = results["validated"] / results["total_documents"] if results["total_documents"] > 0 else 0
        
        return results


ocr_validation_loop = OCRValidationLoop()
