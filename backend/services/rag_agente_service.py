# backend/services/rag_agente_service.py
"""
Servicio para cargar documentos RAG específicos por agente y tenant.
Implementa lógica de fallback: tenant -> templates -> KNOWLEDGE_BASE
"""

import os
import logging
from typing import List, Dict, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class RAGAgenteService:
    """Servicio para cargar documentos RAG específicos por agente y tenant"""
    
    def __init__(self):
        self.templates_base = Path(__file__).parent.parent / "rag" / "templates"
        self.tenants_base = Path(__file__).parent.parent / "rag" / "tenants"
    
    async def cargar_documentos_para_agente(
        self,
        agente_id: str,
        empresa_id: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Carga los documentos RAG para un agente específico.
        
        Prioridad:
        1. Documentos personalizados del tenant (si existen)
        2. Plantillas base (fallback)
        
        Para KNOWLEDGE_BASE, siempre usa las plantillas (son universales).
        """
        if agente_id == "KNOWLEDGE_BASE":
            return await self.cargar_knowledge_base()
        
        from config.agentes_config import get_agente_config
        
        config = get_agente_config(agente_id)
        documentos_ids = config.documentos_rag
        
        resultado = {}
        
        for doc_id in documentos_ids:
            contenido = await self._cargar_documento(
                agente_id=agente_id,
                doc_id=doc_id,
                empresa_id=empresa_id
            )
            if contenido:
                resultado[doc_id] = contenido
            else:
                logger.warning(f"Documento {doc_id} no encontrado para agente {agente_id}")
        
        return resultado
    
    async def _cargar_documento(
        self,
        agente_id: str,
        doc_id: str,
        empresa_id: Optional[str] = None
    ) -> Optional[str]:
        """Carga un documento individual con lógica de fallback"""
        
        # 1. Si hay empresa_id, buscar primero en tenant
        if empresa_id:
            tenant_path = self.tenants_base / empresa_id / agente_id / f"{doc_id}.md"
            if tenant_path.exists():
                logger.debug(f"Cargando documento tenant: {tenant_path}")
                return tenant_path.read_text(encoding='utf-8')
        
        # 2. Buscar en plantillas base del agente
        template_path = self.templates_base / agente_id / f"{doc_id}.md"
        if template_path.exists():
            logger.debug(f"Cargando documento template: {template_path}")
            return template_path.read_text(encoding='utf-8')
        
        # 3. Buscar con patrón más flexible (doc_id puede ser parcial)
        agente_dir = self.templates_base / agente_id
        if agente_dir.exists():
            for archivo in agente_dir.glob("*.md"):
                if doc_id in archivo.stem:
                    logger.debug(f"Cargando documento por patrón: {archivo}")
                    return archivo.read_text(encoding='utf-8')
        
        # 4. Si el doc_id es de KNOWLEDGE_BASE, buscar ahí
        kb_path = self.templates_base / "KNOWLEDGE_BASE" / f"{doc_id}.md"
        if kb_path.exists():
            logger.debug(f"Cargando documento KNOWLEDGE_BASE: {kb_path}")
            return kb_path.read_text(encoding='utf-8')
        
        # 5. Buscar en KNOWLEDGE_BASE con patrón flexible
        kb_dir = self.templates_base / "KNOWLEDGE_BASE"
        if kb_dir.exists():
            for archivo in kb_dir.glob("*.md"):
                if doc_id in archivo.stem:
                    logger.debug(f"Cargando documento KB por patrón: {archivo}")
                    return archivo.read_text(encoding='utf-8')
        
        return None
    
    async def verificar_documentos_tenant(
        self,
        empresa_id: str,
        agente_id: str
    ) -> Dict[str, bool]:
        """Verifica qué documentos tiene configurados un tenant"""
        from config.agentes_config import get_agente_config
        
        config = get_agente_config(agente_id)
        
        resultado = {}
        for doc_id in config.documentos_rag:
            tenant_path = self.tenants_base / empresa_id / agente_id / f"{doc_id}.md"
            resultado[doc_id] = tenant_path.exists()
        
        return resultado
    
    async def obtener_documentos_faltantes(
        self,
        empresa_id: str,
        agente_id: str
    ) -> List[str]:
        """Retorna lista de documentos que el tenant no ha personalizado"""
        verificacion = await self.verificar_documentos_tenant(empresa_id, agente_id)
        return [doc_id for doc_id, existe in verificacion.items() if not existe]
    
    async def cargar_contexto_completo_agente(
        self,
        agente_id: str,
        empresa_id: Optional[str] = None,
        incluir_knowledge_base: bool = True
    ) -> Dict[str, str]:
        """
        Carga el contexto completo para un agente, incluyendo:
        - Documentos específicos del agente
        - Documentos de KNOWLEDGE_BASE (opcional)
        """
        documentos = await self.cargar_documentos_para_agente(agente_id, empresa_id)
        
        if incluir_knowledge_base:
            kb_docs = await self._cargar_knowledge_base()
            for doc_id, contenido in kb_docs.items():
                if doc_id not in documentos:
                    documentos[f"KB_{doc_id}"] = contenido
        
        return documentos
    
    async def cargar_knowledge_base(self) -> Dict[str, str]:
        """Carga todos los documentos de KNOWLEDGE_BASE (universales)"""
        resultado = {}
        kb_dir = self.templates_base / "KNOWLEDGE_BASE"
        
        if not kb_dir.exists():
            return resultado
        
        for archivo in kb_dir.glob("*.md"):
            doc_id = archivo.stem
            try:
                resultado[doc_id] = archivo.read_text(encoding='utf-8')
            except Exception as e:
                logger.error(f"Error cargando {archivo}: {e}")
        
        return resultado
    
    async def _cargar_knowledge_base(self) -> Dict[str, str]:
        """Alias para compatibilidad"""
        return await self.cargar_knowledge_base()
    
    def listar_agentes_disponibles(self) -> List[str]:
        """Lista los agentes que tienen documentos RAG disponibles"""
        agentes = []
        if self.templates_base.exists():
            for carpeta in self.templates_base.iterdir():
                if carpeta.is_dir() and not carpeta.name.startswith("_"):
                    agentes.append(carpeta.name)
        return sorted(agentes)
    
    async def guardar_documento_tenant(
        self,
        empresa_id: str,
        agente_id: str,
        doc_id: str,
        contenido: str
    ) -> bool:
        """Guarda un documento personalizado para un tenant"""
        try:
            tenant_dir = self.tenants_base / empresa_id / agente_id
            tenant_dir.mkdir(parents=True, exist_ok=True)
            
            doc_path = tenant_dir / f"{doc_id}.md"
            doc_path.write_text(contenido, encoding='utf-8')
            
            logger.info(f"Documento guardado: {doc_path}")
            return True
        except Exception as e:
            logger.error(f"Error guardando documento: {e}")
            return False


rag_agente_service = RAGAgenteService()
