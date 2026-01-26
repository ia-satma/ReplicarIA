"""
Bibliotecar.IA Service
Interactive Knowledge Base Management Chatbot
Persona: Dra. Elena Vázquez
"""
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from models.kb_models import (
    DocumentType, ChangeType, KnowledgeState, AlertType, Priority,
    DocumentVersion, KBCategory, KBAlert, KBSolicitud, KBDashboard,
    IngestionRequest, IngestionResult, ChatMessage, BibliotecaContext
)
from services.kb_agent_service import KBAgentService, DocumentType as KBDocType


class BibliotecaService:
    """
    Bibliotecar.IA - Knowledge Base Chatbot Service
    
    Persona: Dra. Elena Vázquez Archivista
    - 20 años organizando información legal y fiscal
    - Curiosa, organizada, proactiva
    - Usa emojis: 📚 📖 🗂️ ✨ 🔍
    """
    
    GREETING = """¡Hola! Soy Bibliotecar.IA 📚 Tu aliada para mantener actualizado 
el conocimiento de Revisar.IA. ¿Qué traes para mí hoy?

Puedo ayudarte a:
• 📊 Ver el estado del acervo
• 📥 Cargar nuevos documentos
• 🔍 Buscar información específica
• 🔔 Ver solicitudes pendientes
• 📈 Revisar el historial de versiones"""
    
    CATEGORIES = [
        {"nombre": "Marco Legal", "icono": "⚖️", "path": "marco_legal/codigos"},
        {"nombre": "Jurisprudencias", "icono": "📜", "path": "marco_legal/jurisprudencias"},
        {"nombre": "Criterios SAT", "icono": "📋", "path": "marco_legal/criterios_sat"},
        {"nombre": "Catálogos SAT", "icono": "📁", "path": "catalogos_sat"},
        {"nombre": "Casos de Referencia", "icono": "📂", "path": "casos_referencia"},
        {"nombre": "Glosarios", "icono": "📖", "path": "glosarios"},
        {"nombre": "Plantillas", "icono": "📝", "path": "plantillas"},
    ]
    
    def __init__(self):
        self.kb_service = KBAgentService()
        self.sessions: Dict[str, BibliotecaContext] = {}
        self.document_versions: Dict[str, DocumentVersion] = {}
        self.alerts: List[KBAlert] = []
        self.solicitudes: List[KBSolicitud] = []
        self._init_sample_data()
    
    def _init_sample_data(self):
        """Initialize sample alerts and solicitudes"""
        self.alerts = [
            KBAlert(
                id="alert-001",
                tipo=AlertType.ACTUALIZACION,
                prioridad=Priority.MEDIA,
                mensaje="El RCFF podría tener actualizaciones de 2025",
                categoria="Marco Legal",
                accion="Verificar DOF para reformas recientes"
            ),
            KBAlert(
                id="alert-002",
                tipo=AlertType.FALTANTE,
                prioridad=Priority.ALTA,
                mensaje="Faltan jurisprudencias recientes sobre EFOS/69-B",
                categoria="Jurisprudencias",
                accion="Buscar tesis 2024-2025 en SCJN"
            ),
            KBAlert(
                id="alert-003",
                tipo=AlertType.CALIDAD,
                prioridad=Priority.BAJA,
                mensaje="Casos de referencia insuficientes",
                categoria="Casos de Referencia",
                accion="Agregar más ejemplos de defensa exitosa"
            ),
        ]
        
        self.solicitudes = [
            KBSolicitud(
                id="sol-001",
                documento="RMF 2025 - Reglas para servicios profesionales",
                razon="A3_FISCAL necesita verificar requisitos actualizados",
                solicitado_por=["A3_FISCAL", "A7_DEFENSA"],
                prioridad=Priority.ALTA
            ),
            KBSolicitud(
                id="sol-002",
                documento="Criterios PRODECON 2024 sobre razón de negocios",
                razon="A1_ESTRATEGIA requiere interpretaciones actuales",
                solicitado_por=["A1_ESTRATEGIA"],
                prioridad=Priority.MEDIA
            ),
        ]
    
    def get_or_create_session(self, session_id: str = None, empresa_id: str = None) -> BibliotecaContext:
        """Get or create a chat session"""
        if not session_id:
            session_id = str(uuid.uuid4())
        
        if session_id not in self.sessions:
            self.sessions[session_id] = BibliotecaContext(
                session_id=session_id,
                empresa_id=empresa_id,
                messages=[
                    ChatMessage(role="assistant", content=self.GREETING)
                ]
            )
        
        return self.sessions[session_id]
    
    def get_dashboard(self) -> KBDashboard:
        """Get knowledge base dashboard"""
        stats = self.kb_service.get_stats()
        
        categories = []
        for cat in self.CATEGORIES:
            state = self._calculate_category_state(cat["nombre"])
            completitud = self._calculate_completitud(cat["nombre"])
            alert_count = sum(1 for a in self.alerts if a.categoria == cat["nombre"])
            
            categories.append(KBCategory(
                nombre=cat["nombre"],
                icono=cat["icono"],
                documentos=stats.get("documents_by_type", {}).get(cat["path"], 0),
                estado=state,
                completitud=completitud,
                ultima_actualizacion=datetime.utcnow(),
                alertas=alert_count
            ))
        
        return KBDashboard(
            total_documentos=stats["total_documents"],
            total_chunks=stats["total_chunks"],
            ultima_actualizacion=datetime.utcnow(),
            score_promedio=0.85,
            completitud_general=0.78,
            categorias=categories,
            alertas=self.alerts[:5],
            solicitudes=self.solicitudes[:5]
        )
    
    def _calculate_category_state(self, categoria: str) -> KnowledgeState:
        """Calculate state for a category"""
        alert_count = sum(1 for a in self.alerts if a.categoria == categoria)
        critical = sum(1 for a in self.alerts if a.categoria == categoria and a.prioridad == Priority.ALTA)
        
        if critical > 0:
            return KnowledgeState.CRITICO
        elif alert_count > 1:
            return KnowledgeState.INCOMPLETO
        elif alert_count == 1:
            return KnowledgeState.ACTUALIZABLE
        else:
            return KnowledgeState.COMPLETO
    
    def _calculate_completitud(self, categoria: str) -> float:
        """Calculate completeness percentage for a category"""
        base_scores = {
            "Marco Legal": 0.90,
            "Jurisprudencias": 0.75,
            "Criterios SAT": 0.85,
            "Catálogos SAT": 0.95,
            "Casos de Referencia": 0.40,
            "Glosarios": 0.80,
            "Plantillas": 0.70,
        }
        return base_scores.get(categoria, 0.50)
    
    def process_message(self, session_id: str, user_message: str, empresa_id: str = None) -> str:
        """Process a user message and return Bibliotecar.IA response"""
        context = self.get_or_create_session(session_id, empresa_id)
        
        context.messages.append(ChatMessage(role="user", content=user_message))
        
        response = self._generate_response(user_message, context)
        
        context.messages.append(ChatMessage(role="assistant", content=response))
        
        return response
    
    def _generate_response(self, message: str, context: BibliotecaContext) -> str:
        """Generate response based on user intent"""
        message_lower = message.lower()
        
        if any(word in message_lower for word in ["estado", "dashboard", "acervo", "resumen"]):
            return self._format_dashboard_response()
        
        elif any(word in message_lower for word in ["cargar", "subir", "agregar", "nuevo documento"]):
            return self._format_ingestion_prompt()
        
        elif any(word in message_lower for word in ["buscar", "encontrar", "donde", "información"]):
            return self._format_search_response(message)
        
        elif any(word in message_lower for word in ["alertas", "pendiente", "falta", "solicitudes"]):
            return self._format_alerts_response()
        
        elif any(word in message_lower for word in ["versiones", "historial", "cambios"]):
            return self._format_versions_response()
        
        elif any(word in message_lower for word in ["hola", "ayuda", "qué puedes"]):
            return self.GREETING
        
        else:
            return self._format_general_response(message)
    
    def _format_dashboard_response(self) -> str:
        """Format dashboard as chat response"""
        dashboard = self.get_dashboard()
        
        response = """📊 **Estado Actual del Acervo**

"""
        for cat in dashboard.categorias:
            state_icon = {
                KnowledgeState.COMPLETO: "🟢",
                KnowledgeState.ACTUALIZABLE: "🟡",
                KnowledgeState.INCOMPLETO: "🟠",
                KnowledgeState.CRITICO: "🔴",
                KnowledgeState.EN_REVISION: "🔵",
            }.get(cat.estado, "⚪")
            
            response += f"{state_icon} **{cat.icono} {cat.nombre}**: {int(cat.completitud * 100)}% completo"
            if cat.alertas > 0:
                response += f" ({cat.alertas} alertas)"
            response += "\n"
        
        response += f"""
---
📈 **Resumen General**
• Documentos indexados: {dashboard.total_documentos}
• Chunks para RAG: {dashboard.total_chunks}
• Completitud general: {int(dashboard.completitud_general * 100)}%

¿Te gustaría ver las alertas pendientes o cargar un nuevo documento?"""
        
        return response
    
    def _format_ingestion_prompt(self) -> str:
        """Prompt for document ingestion"""
        return """📥 **Carga de Documentos**

¡Perfecto! Me encanta cuando llega información nueva ✨

Para cargar un documento, necesito que me digas:

1. **Tipo de documento:**
   • Ley / Código
   • Reglamento
   • RMF / Resolución Miscelánea
   • Criterio SAT
   • Jurisprudencia / Tesis
   • Otro

2. **Ordenamiento** (ej: CFF, LISR, LIVA)

3. **Versión/Año** (ej: 2025.01)

4. **Contenido** (puedes pegar el texto o subir el archivo)

¿Con qué tipo de documento empezamos?"""
    
    def _format_search_response(self, query: str) -> str:
        """Format search results"""
        results = self.kb_service.search(query, max_results=3)
        
        if not results:
            return f"""🔍 Busqué "{query}" pero no encontré resultados exactos.

💡 Sugerencias:
• Intenta con términos más específicos
• Busca por artículo (ej: "Artículo 27 LISR")
• Busca por concepto (ej: "razón de negocios")

¿Quieres que busque algo diferente?"""
        
        response = f"""🔍 **Resultados para "{query}"**

"""
        for i, result in enumerate(results, 1):
            source = result.chunk.metadata.source_document
            snippet = result.chunk.content[:200] + "..." if len(result.chunk.content) > 200 else result.chunk.content
            response += f"""**{i}. {source}**
{snippet}

"""
        
        response += "¿Necesitas más información sobre alguno de estos resultados?"
        return response
    
    def _format_alerts_response(self) -> str:
        """Format alerts and requests"""
        response = """🔔 **Alertas y Solicitudes Pendientes**

"""
        if self.alerts:
            response += "**Alertas Activas:**\n"
            for alert in self.alerts[:5]:
                icon = {"alta": "❗", "media": "⚠️", "baja": "ℹ️"}.get(alert.prioridad.value, "•")
                response += f"{icon} {alert.mensaje}\n   📁 {alert.categoria} | 🔧 {alert.accion}\n\n"
        
        if self.solicitudes:
            response += "\n**Documentos Solicitados por Agentes:**\n"
            for sol in self.solicitudes[:5]:
                agents = ", ".join(sol.solicitado_por)
                response += f"📄 {sol.documento}\n   Solicitado por: {agents}\n   Razón: {sol.razon}\n\n"
        
        response += "¿Tienes alguno de estos documentos para cargar?"
        return response
    
    def _format_versions_response(self) -> str:
        """Format version history"""
        return """📜 **Sistema de Versionamiento**

Mantengo un registro completo de versiones para cada ordenamiento:

**CFF - Código Fiscal de la Federación**
├── 📜 v2025.01 (Vigente) 🟢
│   └── DOF 13/11/2024 | Vigencia: 01/01/2025
├── 📜 v2024.01 (Histórico) ⚫
│   └── Vigencia: 01/01/2024 - 31/12/2024
└── 📜 v2022.01 (Histórico) ⚫

**LISR - Ley del Impuesto Sobre la Renta**
├── 📜 v2025.01 (Vigente) 🟢
└── 📜 v2024.01 (Histórico) ⚫

¿Quieres ver el historial detallado de algún artículo específico?
Por ejemplo: "historial artículo 27 LISR" """
    
    def _format_general_response(self, message: str) -> str:
        """General fallback response"""
        return f"""📚 Entiendo que quieres saber sobre "{message}".

Déjame buscar en mi acervo... 🔍

Mientras tanto, puedo ayudarte con:
• **estado** - Ver el dashboard del acervo
• **cargar** - Subir nuevos documentos
• **buscar [tema]** - Encontrar información específica
• **alertas** - Ver solicitudes pendientes
• **versiones** - Revisar historial de cambios

¿Qué te gustaría hacer?"""
    
    def ingest_document(self, request: IngestionRequest, usuario: str = None) -> IngestionResult:
        """Ingest a new document into the KB"""
        try:
            doc_type_map = {
                DocumentType.LEY: KBDocType.LEGAL_CODE,
                DocumentType.REGLAMENTO: KBDocType.LEGAL_CODE,
                DocumentType.RMF: KBDocType.LEGAL_CODE,
                DocumentType.CRITERIO: KBDocType.CRITERIA_SAT,
                DocumentType.JURISPRUDENCIA: KBDocType.JURISPRUDENCE,
                DocumentType.TESIS: KBDocType.JURISPRUDENCE,
                DocumentType.CONTRATO: KBDocType.CONTRACT,
            }
            
            kb_doc_type = doc_type_map.get(request.documento_tipo, KBDocType.GENERAL)
            
            if request.contenido:
                import tempfile
                import os
                with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
                    f.write(f"# {request.nombre}\n\n")
                    f.write(f"**Ordenamiento:** {request.ordenamiento}\n")
                    f.write(f"**Versión:** {request.version}\n")
                    f.write(f"**Fecha:** {request.fecha_publicacion}\n\n")
                    f.write(request.contenido)
                    temp_path = f.name
                
                doc = self.kb_service.ingest_document(
                    temp_path,
                    kb_doc_type,
                    request.metadata
                )
                
                os.unlink(temp_path)
                
                version = DocumentVersion(
                    document_id=doc.id,
                    version_id=f"{doc.id}_v{request.version}",
                    document_type=request.documento_tipo,
                    ordenamiento=request.ordenamiento,
                    nombre_completo=request.nombre,
                    version=request.version,
                    fecha_publicacion=request.fecha_publicacion,
                    fecha_inicio_vigencia=request.fecha_publicacion,
                    usuario_ingestion=usuario,
                    chunks_generados=doc.chunk_count,
                    score_calidad=0.85
                )
                self.document_versions[version.version_id] = version
                
                return IngestionResult(
                    success=True,
                    document_id=doc.id,
                    version_id=version.version_id,
                    chunks_generados=doc.chunk_count,
                    mensaje=f"¡Excelente! 📚 He indexado '{request.nombre}' exitosamente. "
                            f"Generé {doc.chunk_count} chunks para búsqueda RAG."
                )
            
            return IngestionResult(
                success=False,
                mensaje="No se proporcionó contenido para indexar.",
                errores=["Contenido vacío"]
            )
            
        except Exception as e:
            return IngestionResult(
                success=False,
                mensaje=f"Error al procesar el documento: {str(e)}",
                errores=[str(e)]
            )
    
    def get_version_tree(self, ordenamiento: str) -> Dict[str, Any]:
        """Get version tree for an ordenamiento"""
        versions = [v for v in self.document_versions.values() 
                   if v.ordenamiento.upper() == ordenamiento.upper()]
        
        versions.sort(key=lambda x: x.fecha_publicacion, reverse=True)
        
        return {
            "ordenamiento": ordenamiento,
            "versiones": [
                {
                    "version": v.version,
                    "vigente": v.es_vigente,
                    "fecha_publicacion": v.fecha_publicacion.isoformat() if v.fecha_publicacion else None,
                    "chunks": v.chunks_generados,
                    "calidad": v.score_calidad
                }
                for v in versions
            ]
        }
