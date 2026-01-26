"""
DEFENSE FILE GENERATOR
Servicio principal para generar expedientes de defensa fiscal completos
"""

import os
import io
import json
import hashlib
import zipfile
import shutil
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field, asdict

from PyPDF2 import PdfMerger, PdfReader

from .pdf_generator import PDFGenerator
from .styles import ZIP_STRUCTURE, LEGAL_TEXTS

HAS_MODELS = False
Project = None
Document = None


@dataclass
class DefenseFileConfig:
    """Configuración para generación de expediente"""
    include_cover: bool = True
    include_index: bool = True
    include_executive_summary: bool = True
    include_ocr_report: bool = True
    include_red_team_report: bool = True
    include_source_documents: bool = True
    include_integrity_section: bool = True
    generate_zip: bool = True
    output_format: str = 'both'


@dataclass
class DefenseFileResult:
    """Resultado de la generación"""
    success: bool
    pdf_path: Optional[str] = None
    zip_path: Optional[str] = None
    total_pages: int = 0
    total_documents: int = 0
    file_hashes: Dict[str, str] = field(default_factory=dict)
    generation_time_ms: int = 0
    errors: List[str] = field(default_factory=list)


class DefenseFileGenerator:
    """Generador de expedientes de defensa fiscal"""
    
    def __init__(self, output_dir: str = "static/generated_files"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    async def generate(
        self,
        project_data: Dict[str, Any],
        documents: List[Dict[str, Any]],
        ocr_results: List[Dict[str, Any]] = None,
        red_team_results: Dict[str, Any] = None,
        config: DefenseFileConfig = None
    ) -> DefenseFileResult:
        """
        Genera expediente de defensa completo.
        """
        start_time = datetime.now()
        config = config or DefenseFileConfig()
        errors = []
        file_hashes = {}
        
        folio = self._generate_folio(project_data)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        base_filename = f"expediente_{folio}_{timestamp}"
        pdf_path = os.path.join(self.output_dir, f"{base_filename}.pdf")
        zip_path = os.path.join(self.output_dir, f"{base_filename}.zip")
        
        try:
            if config.output_format in ['pdf', 'both']:
                pdf_path = await self._generate_main_pdf(
                    pdf_path=pdf_path,
                    project_data=project_data,
                    documents=documents,
                    ocr_results=ocr_results or [],
                    red_team_results=red_team_results or {},
                    config=config,
                    folio=folio
                )
                
                if os.path.exists(pdf_path):
                    file_hashes['expediente.pdf'] = self._calculate_hash(pdf_path)
            
            if config.generate_zip and config.output_format in ['zip', 'both']:
                zip_path, zip_hashes = await self._generate_zip_package(
                    zip_path=zip_path,
                    pdf_path=pdf_path if config.output_format in ['pdf', 'both'] else None,
                    project_data=project_data,
                    documents=documents,
                    ocr_results=ocr_results or [],
                    red_team_results=red_team_results or {},
                    folio=folio
                )
                file_hashes.update(zip_hashes)
            
        except Exception as e:
            errors.append(f"Error en generación: {str(e)}")
            import traceback
            traceback.print_exc()
        
        generation_time = int((datetime.now() - start_time).total_seconds() * 1000)
        
        return DefenseFileResult(
            success=len(errors) == 0,
            pdf_path=pdf_path if os.path.exists(pdf_path) else None,
            zip_path=zip_path if os.path.exists(zip_path) else None,
            total_pages=self._count_pdf_pages(pdf_path) if os.path.exists(pdf_path) else 0,
            total_documents=len(documents),
            file_hashes=file_hashes,
            generation_time_ms=generation_time,
            errors=errors
        )
    
    async def _generate_main_pdf(
        self,
        pdf_path: str,
        project_data: Dict,
        documents: List[Dict],
        ocr_results: List[Dict],
        red_team_results: Dict,
        config: DefenseFileConfig,
        folio: str
    ) -> str:
        """Genera el PDF principal del expediente"""
        
        pdf = PDFGenerator(
            output_path=pdf_path,
            title=f"Expediente de Defensa - {project_data.get('nombre', 'Proyecto')}"
        )
        
        if config.include_cover:
            pdf.add_title_page(
                project_name=project_data.get('nombre', 'Sin nombre'),
                client_name=project_data.get('cliente', project_data.get('contribuyente', 'N/A')),
                rfc=project_data.get('rfc', project_data.get('rfc_cliente', 'N/A')),
                periodo_fiscal=project_data.get('periodo_fiscal', str(datetime.now().year)),
                folio=folio,
                qr_data=f"REVISAR.IA:{folio}:{datetime.now().isoformat()}"
            )
        
        if config.include_executive_summary:
            risk_score = project_data.get('risk_score', 50)
            risk_level = self._get_risk_level(risk_score)
            total_docs = len(documents)
            validated_docs = len([d for d in documents if d.get('status') in ['VALIDATED', 'COMPLETE']])
            vuln_count = len(red_team_results.get('vulnerabilidades', []))
            
            key_findings = []
            if red_team_results.get('vulnerabilidades'):
                key_findings.extend([
                    v.get('message', v.get('description', ''))[:80]
                    for v in red_team_results['vulnerabilidades'][:3]
                ])
            
            if risk_level == 'LOW' and vuln_count == 0:
                recommendation = "EXPEDIENTE DEFENDIBLE - Listo para presentar ante autoridades fiscales."
            elif risk_level == 'MEDIUM' or vuln_count <= 2:
                recommendation = "EXPEDIENTE CON OBSERVACIONES - Corregir vulnerabilidades menores antes de presentar."
            else:
                recommendation = "EXPEDIENTE REQUIERE CORRECCIONES - No presentar hasta resolver vulnerabilidades críticas."
            
            pdf.add_executive_summary(
                risk_score=risk_score,
                risk_level=risk_level,
                total_documents=total_docs,
                validated_documents=validated_docs,
                vulnerabilities_found=vuln_count,
                key_findings=key_findings,
                recommendation=recommendation
            )
        
        if config.include_index:
            doc_index = []
            page_num = 5
            
            for doc in documents:
                doc_index.append({
                    'nombre': doc.get('nombre', doc.get('filename', 'Documento')),
                    'tipo': doc.get('tipo', doc.get('type', 'Otro')),
                    'status': doc.get('status', doc.get('validation_status', 'PENDING')),
                    'pagina': page_num
                })
                page_num += 1
            
            pdf.add_document_index(doc_index)
        
        if config.include_ocr_report and ocr_results:
            pdf.add_validation_report(ocr_results)
        
        if config.include_red_team_report and red_team_results:
            vulns = red_team_results.get('vulnerabilidades', [])
            score = red_team_results.get('score', 50)
            bulletproof = red_team_results.get('bulletproof', False)
            pdf.add_red_team_report(vulns, score, bulletproof)
        
        if config.include_integrity_section:
            source_hashes = {}
            for doc in documents:
                if doc.get('file_path') and os.path.exists(doc['file_path']):
                    source_hashes[doc.get('nombre', 'documento')] = self._calculate_hash(doc['file_path'])
            
            pdf.add_integrity_section(file_hashes=source_hashes)
        
        pdf.build()
        
        return pdf_path
    
    async def _generate_zip_package(
        self,
        zip_path: str,
        pdf_path: Optional[str],
        project_data: Dict,
        documents: List[Dict],
        ocr_results: List[Dict],
        red_team_results: Dict,
        folio: str
    ) -> tuple:
        """Genera paquete ZIP con estructura de carpetas"""
        
        file_hashes = {}
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            
            for folder, description in ZIP_STRUCTURE.items():
                readme_content = f"# {folder}\n\n{description}\n\nExpediente: {folio}\n"
                zf.writestr(f"{folder}/README.txt", readme_content)
            
            if pdf_path and os.path.exists(pdf_path):
                zf.write(pdf_path, "01_CARATULA/expediente_completo.pdf")
                file_hashes['expediente_completo.pdf'] = self._calculate_hash(pdf_path)
            
            index_data = {
                'folio': folio,
                'proyecto': project_data.get('nombre'),
                'fecha_generacion': datetime.now().isoformat(),
                'documentos': [
                    {
                        'nombre': d.get('nombre'),
                        'tipo': d.get('tipo'),
                        'status': d.get('status'),
                        'carpeta': self._get_folder_for_type(d.get('tipo'))
                    }
                    for d in documents
                ]
            }
            zf.writestr(
                "02_INDICE/indice_documentos.json",
                json.dumps(index_data, indent=2, ensure_ascii=False)
            )
            
            for doc in documents:
                if doc.get('file_path') and os.path.exists(doc['file_path']):
                    folder = self._get_folder_for_type(doc.get('tipo'))
                    filename = doc.get('nombre', os.path.basename(doc['file_path']))
                    
                    if not filename.endswith('.pdf'):
                        filename += '.pdf'
                    
                    zf.write(doc['file_path'], f"{folder}/{filename}")
                    file_hashes[filename] = self._calculate_hash(doc['file_path'])
            
            if ocr_results:
                ocr_report = {
                    'fecha': datetime.now().isoformat(),
                    'resultados': ocr_results
                }
                zf.writestr(
                    "08_VALIDACIONES/reporte_ocr.json",
                    json.dumps(ocr_report, indent=2, ensure_ascii=False)
                )
            
            if red_team_results:
                zf.writestr(
                    "09_RED_TEAM/reporte_simulacion.json",
                    json.dumps(red_team_results, indent=2, ensure_ascii=False)
                )
            
            integrity_data = {
                'folio': folio,
                'fecha_generacion': datetime.now().isoformat(),
                'algoritmo': 'SHA-256',
                'sistema': 'Revisar.IA',
                'hashes': file_hashes
            }
            zf.writestr(
                "10_METADATOS/integridad.json",
                json.dumps(integrity_data, indent=2, ensure_ascii=False)
            )
            
            zf.writestr(
                "10_METADATOS/legal.txt",
                LEGAL_TEXTS['legal_basis'].strip() + "\n\n" + LEGAL_TEXTS['integrity'].strip()
            )
        
        return zip_path, file_hashes
    
    def _generate_folio(self, project_data: Dict) -> str:
        """Genera folio único para el expediente"""
        project_id = project_data.get('id', project_data.get('project_id', 'UNKNOWN'))
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        hash_input = f"{project_id}{timestamp}"
        short_hash = hashlib.md5(hash_input.encode()).hexdigest()[:8].upper()
        return f"DEF-{short_hash}"
    
    def _get_risk_level(self, score: float) -> str:
        """Determina nivel de riesgo basado en score"""
        if score >= 70:
            return 'CRITICAL'
        elif score >= 50:
            return 'HIGH'
        elif score >= 30:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def _get_folder_for_type(self, doc_type: str) -> str:
        """Mapea tipo de documento a carpeta del ZIP"""
        type_mapping = {
            'contrato': '03_CONTRATOS',
            'sow': '03_CONTRATOS',
            'anexo': '03_CONTRATOS',
            'factura': '04_FACTURAS',
            'cfdi': '04_FACTURAS',
            'complemento': '04_FACTURAS',
            'comprobante': '05_COMPROBANTES_PAGO',
            'transferencia': '05_COMPROBANTES_PAGO',
            'pago': '05_COMPROBANTES_PAGO',
            'entregable': '06_ENTREGABLES',
            'evidencia': '06_ENTREGABLES',
            'reporte': '06_ENTREGABLES',
            'minuta': '07_CORRESPONDENCIA',
            'correo': '07_CORRESPONDENCIA',
            'email': '07_CORRESPONDENCIA',
        }
        
        if doc_type:
            doc_type_lower = doc_type.lower()
            for key, folder in type_mapping.items():
                if key in doc_type_lower:
                    return folder
        
        return '06_ENTREGABLES'
    
    def _calculate_hash(self, file_path: str) -> str:
        """Calcula hash SHA-256 de un archivo"""
        if not os.path.exists(file_path):
            return ""
        
        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                sha256.update(chunk)
        return sha256.hexdigest()
    
    def _count_pdf_pages(self, pdf_path: str) -> int:
        """Cuenta páginas de un PDF"""
        try:
            if os.path.exists(pdf_path):
                reader = PdfReader(pdf_path)
                return len(reader.pages)
        except Exception:
            pass
        return 0
    
    async def list_generated_files(self) -> List[Dict[str, Any]]:
        """Lista archivos generados"""
        files = []
        
        if not os.path.exists(self.output_dir):
            return files
        
        for filename in os.listdir(self.output_dir):
            if filename.startswith('expediente_'):
                filepath = os.path.join(self.output_dir, filename)
                files.append({
                    'filename': filename,
                    'path': filepath,
                    'size_bytes': os.path.getsize(filepath),
                    'created_at': datetime.fromtimestamp(os.path.getctime(filepath)).isoformat(),
                    'type': 'pdf' if filename.endswith('.pdf') else 'zip'
                })
        
        return sorted(files, key=lambda x: x['created_at'], reverse=True)
    
    async def delete_generated_file(self, filename: str) -> bool:
        """Elimina un archivo generado"""
        filepath = os.path.join(self.output_dir, filename)
        if os.path.exists(filepath):
            os.remove(filepath)
            return True
        return False


defense_file_generator = DefenseFileGenerator()
