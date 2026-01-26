import os
import logging
import time
from typing import List, Dict, Optional
from pathlib import Path
from docx import Document

logger = logging.getLogger(__name__)

try:
    import fitz  # PyMuPDF - más rápido
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False
    import PyPDF2

class FileAnalysisService:
    """Servicio para analizar documentos adjuntos"""
    
    def __init__(self):
        ROOT_DIR = Path(__file__).parent.parent
        self.upload_dir = ROOT_DIR / "uploads"
    
    def extract_text_from_pdf(self, file_path: str) -> str:
        """Extrae texto de un archivo PDF con feedback de progreso"""
        inicio = time.time()
        
        if HAS_PYMUPDF:
            return self._extract_with_pymupdf(file_path, inicio)
        else:
            return self._extract_with_pypdf2(file_path, inicio)
    
    def _extract_with_pymupdf(self, file_path: str, inicio: float) -> str:
        """Extracción usando PyMuPDF (fitz) - más rápido"""
        try:
            doc = fitz.open(file_path)
            total_pages = len(doc)
            logger.info(f"📄 PDF tiene {total_pages} páginas (usando PyMuPDF)")
            
            texto_partes = []
            for i, page in enumerate(doc):
                try:
                    texto = page.get_text()
                    texto_partes.append(texto)
                    
                    if i % 20 == 0 and i > 0:
                        progreso = int((i / total_pages) * 100)
                        elapsed = time.time() - inicio
                        logger.info(f"  📖 Procesando... {progreso}% ({i}/{total_pages}) - {elapsed:.1f}s")
                except Exception as e:
                    logger.warning(f"  ⚠️ Error en página {i}: {e}")
                    continue
            
            doc.close()
            elapsed = time.time() - inicio
            texto_final = '\n'.join(texto_partes)
            logger.info(f"✅ Extracción completa: {len(texto_final)} caracteres en {elapsed:.1f}s")
            return texto_final.strip()
            
        except Exception as e:
            logger.error(f"Error extracting PDF with PyMuPDF: {str(e)}")
            return f"[No se pudo leer el PDF: {str(e)}]"
    
    def _extract_with_pypdf2(self, file_path: str, inicio: float) -> str:
        """Extracción usando PyPDF2 (fallback)"""
        try:
            import PyPDF2
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                total_pages = len(pdf_reader.pages)
                logger.info(f"📄 PDF tiene {total_pages} páginas (usando PyPDF2)")
                
                texto_partes = []
                for i, page in enumerate(pdf_reader.pages):
                    try:
                        texto = page.extract_text() or ''
                        texto_partes.append(texto)
                        
                        if i % 20 == 0 and i > 0:
                            progreso = int((i / total_pages) * 100)
                            elapsed = time.time() - inicio
                            logger.info(f"  📖 Procesando... {progreso}% ({i}/{total_pages}) - {elapsed:.1f}s")
                    except Exception as e:
                        logger.warning(f"  ⚠️ Error en página {i}: {e}")
                        continue
                
                elapsed = time.time() - inicio
                texto_final = '\n'.join(texto_partes)
                logger.info(f"✅ Extracción completa: {len(texto_final)} caracteres en {elapsed:.1f}s")
                return texto_final.strip()
                
        except Exception as e:
            logger.error(f"Error extracting PDF with PyPDF2: {str(e)}")
            return f"[No se pudo leer el PDF: {str(e)}]"
    
    def extract_text_from_docx(self, file_path: str) -> str:
        """Extrae texto de un archivo DOCX"""
        try:
            doc = Document(file_path)
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            return text.strip()
        except Exception as e:
            logger.error(f"Error extracting DOCX text: {str(e)}")
            return f"[No se pudo leer el DOCX: {str(e)}]"
    
    def extract_text_from_file(self, file_url: str) -> str:
        """Extrae texto de un archivo según su extensión"""
        try:
            # Convertir URL relativa a path
            if file_url.startswith('/uploads/'):
                filename = file_url.replace('/uploads/', '')
                file_path = self.upload_dir / filename
            else:
                return "[URL externa - no se puede analizar localmente]"
            
            if not file_path.exists():
                return f"[Archivo no encontrado: {file_url}]"
            
            extension = file_path.suffix.lower()
            
            if extension == '.pdf':
                return self.extract_text_from_pdf(str(file_path))
            elif extension in ['.docx', '.doc']:
                return self.extract_text_from_docx(str(file_path))
            elif extension == '.txt':
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            else:
                return f"[Archivo {extension} - formato no soportado para análisis de texto]"
        
        except Exception as e:
            logger.error(f"Error extracting text from file: {str(e)}")
            return f"[Error al analizar archivo: {str(e)}]"
    
    def analyze_attachments(self, attachment_urls: List[str]) -> Dict:
        """Analiza todos los archivos adjuntos y retorna un resumen"""
        if not attachment_urls:
            return {
                "total_files": 0,
                "files_analyzed": [],
                "combined_text": ""
            }
        
        files_analyzed = []
        combined_text = "\n\n=== ANÁLISIS DE DOCUMENTOS ADJUNTOS ===\n\n"
        
        for i, url in enumerate(attachment_urls, 1):
            filename = url.split('/')[-1]
            text = self.extract_text_from_file(url)
            
            files_analyzed.append({
                "url": url,
                "filename": filename,
                "text_length": len(text),
                "preview": text[:500] if len(text) > 500 else text
            })
            
            combined_text += f"--- DOCUMENTO {i}: {filename} ---\n"
            combined_text += text[:2000]  # Limitar a 2000 caracteres por documento
            combined_text += "\n" + ("="*80) + "\n\n"
        
        combined_text += f"=== FIN ANÁLISIS DOCUMENTOS ({len(files_analyzed)} archivos) ===\n"
        
        return {
            "total_files": len(attachment_urls),
            "files_analyzed": files_analyzed,
            "combined_text": combined_text
        }