"""
Servicio de negocio para gestión de Empresas/Tenants.
"""
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

from models.empresa import (
    Empresa, EmpresaCreate, EmpresaUpdate,
    PilarEstrategico, OKR, ConfiguracionTipologia
)
from repositories.empresa_repository import empresa_repository

logger = logging.getLogger(__name__)

TIPOLOGIAS_BASE = [
    {
        "codigo": "CONSULTORIA_MACRO_ESTRATEGIA",
        "nombre": "Consultoría Macro / Estratégica",
        "descripcion": "Servicios de consultoría estratégica, estudios de mercado, análisis de inversión y asesoría en decisiones de alto nivel.",
        "checklist_documentos": [
            "Ficha SIB con BEE",
            "SOW / Propuesta",
            "Minutas (Kick-off/Avance)",
            "Borradores (V0/V1)",
            "Informe Final Integrado",
            "Herramienta/Modelo Excel",
            "Manual Metodológico",
            "VBC Fiscal y Legal",
            "CFDI",
            "Comprobante de pago"
        ]
    },
    {
        "codigo": "INTRAGRUPO_MANAGEMENT_FEE",
        "nombre": "Servicios Intragrupo / Management Fee",
        "descripcion": "Servicios entre empresas relacionadas, fees de administración, servicios compartidos corporativos.",
        "checklist_documentos": [
            "Análisis de no duplicidad",
            "Estudio de Precios de Transferencia",
            "Contrato de servicios intragrupo",
            "Análisis de beneficio real",
            "Evidencia de servicios prestados",
            "CFDI",
            "Comprobante de pago"
        ]
    },
    {
        "codigo": "SOFTWARE_SAAS_DESARROLLO",
        "nombre": "Software / SaaS / Desarrollo",
        "descripcion": "Desarrollo de software, licencias SaaS, implementación de sistemas tecnológicos.",
        "checklist_documentos": [
            "Especificación Técnica",
            "Contrato de desarrollo/licencia",
            "Evidencia de Desarrollo (commits, sprints)",
            "Sistema en Producción o Licencias activas",
            "Manual de Usuario",
            "CFDI",
            "Comprobante de pago"
        ]
    },
    {
        "codigo": "CAPACITACION_FORMACION",
        "nombre": "Capacitación / Formación",
        "descripcion": "Cursos, talleres, programas de formación, certificaciones para el personal.",
        "checklist_documentos": [
            "Programa de capacitación",
            "Lista de Asistencia firmada",
            "Evidencia de Capacitación (fotos, evaluaciones)",
            "Material Didáctico",
            "Constancias de participación",
            "CFDI",
            "Comprobante de pago"
        ]
    },
    {
        "codigo": "LEGAL_NOTARIAL",
        "nombre": "Servicios Legales / Notariales",
        "descripcion": "Asesoría legal, servicios notariales, constitución de sociedades, contratos.",
        "checklist_documentos": [
            "Contrato de servicios legales",
            "Escrituras/Actas notariales",
            "Opiniones legales",
            "Convenios/Contratos elaborados",
            "CFDI",
            "Comprobante de pago"
        ]
    },
    {
        "codigo": "MARKETING_PUBLICIDAD",
        "nombre": "Marketing / Publicidad",
        "descripcion": "Campañas publicitarias, diseño gráfico, marketing digital, branding.",
        "checklist_documentos": [
            "Brief de campaña",
            "Plan de medios",
            "Artes finales",
            "Métricas de campaña",
            "Evidencia de publicación",
            "CFDI",
            "Comprobante de pago"
        ]
    },
    {
        "codigo": "CONSTRUCCION_OBRA",
        "nombre": "Construcción / Obra Civil",
        "descripcion": "Servicios de construcción, supervisión de obra, proyectos de infraestructura.",
        "checklist_documentos": [
            "Contrato de obra",
            "Proyecto ejecutivo",
            "Bitácora de obra",
            "Estimaciones de avance",
            "Acta de entrega-recepción",
            "Finiquito de obra",
            "CFDI",
            "Comprobante de pago"
        ]
    },
    {
        "codigo": "AUDITORIA_CONTABLE",
        "nombre": "Auditoría / Servicios Contables",
        "descripcion": "Auditorías financieras, dictámenes fiscales, servicios de contabilidad externa.",
        "checklist_documentos": [
            "Carta de encargo",
            "Plan de auditoría",
            "Papeles de trabajo",
            "Informe de auditoría/Dictamen",
            "Carta de recomendaciones",
            "CFDI",
            "Comprobante de pago"
        ]
    }
]


class EmpresaService:
    def __init__(self):
        self.repository = empresa_repository
    
    async def crear_empresa(self, data: EmpresaCreate) -> Empresa:
        existing = await self.repository.get_by_rfc(data.rfc)
        if existing:
            raise ValueError(f"Ya existe una empresa con RFC {data.rfc}")
        
        tipologias_default = [
            ConfiguracionTipologia(
                codigo=t["codigo"],
                nombre=t["nombre"],
                descripcion=t["descripcion"],
                habilitada=True,
                checklist_documentos=t["checklist_documentos"]
            )
            for t in TIPOLOGIAS_BASE
        ]
        
        empresa = Empresa(
            nombre_comercial=data.nombre_comercial,
            razon_social=data.razon_social,
            rfc=data.rfc,
            industria=data.industria,
            sub_industria=data.sub_industria,
            tipologias_configuradas=tipologias_default
        )
        
        created = await self.repository.create(empresa)
        logger.info(f"Empresa creada: {created.id} - {created.nombre_comercial}")
        return created
    
    async def get_empresa(self, empresa_id: str) -> Optional[Empresa]:
        return await self.repository.get_by_id(empresa_id)
    
    async def get_all_empresas(self, only_active: bool = True) -> List[Empresa]:
        return await self.repository.get_all(only_active)
    
    async def update_empresa(self, empresa_id: str, data: EmpresaUpdate) -> Optional[Empresa]:
        update_dict = data.model_dump(exclude_unset=True)
        if not update_dict:
            return await self.repository.get_by_id(empresa_id)
        
        if 'pilares_estrategicos' in update_dict and update_dict['pilares_estrategicos']:
            update_dict['pilares_estrategicos'] = [
                p.model_dump() if hasattr(p, 'model_dump') else p 
                for p in update_dict['pilares_estrategicos']
            ]
        
        if 'okrs' in update_dict and update_dict['okrs']:
            update_dict['okrs'] = [
                o.model_dump() if hasattr(o, 'model_dump') else o 
                for o in update_dict['okrs']
            ]
        
        if 'tipologias_configuradas' in update_dict and update_dict['tipologias_configuradas']:
            update_dict['tipologias_configuradas'] = [
                t.model_dump() if hasattr(t, 'model_dump') else t 
                for t in update_dict['tipologias_configuradas']
            ]
        
        return await self.repository.update(empresa_id, update_dict)
    
    async def get_tipologias_con_estado(self, empresa_id: str) -> List[Dict[str, Any]]:
        empresa = await self.repository.get_by_id(empresa_id)
        if not empresa:
            raise ValueError(f"Empresa {empresa_id} no encontrada")
        
        tipologias_empresa = {t.codigo: t for t in empresa.tipologias_configuradas}
        
        result = []
        for base in TIPOLOGIAS_BASE:
            codigo = base["codigo"]
            if codigo in tipologias_empresa:
                tip = tipologias_empresa[codigo]
                result.append({
                    "codigo": codigo,
                    "nombre": tip.nombre,
                    "descripcion": tip.descripcion,
                    "habilitada": tip.habilitada,
                    "checklist_documentos": tip.checklist_documentos,
                    "criterios_adicionales": tip.criterios_adicionales,
                    "disponible": True
                })
            else:
                result.append({
                    "codigo": codigo,
                    "nombre": base["nombre"],
                    "descripcion": base["descripcion"],
                    "habilitada": False,
                    "checklist_documentos": base["checklist_documentos"],
                    "criterios_adicionales": None,
                    "disponible": True
                })
        
        return result
    
    async def configurar_tipologias(self, empresa_id: str, tipologias: List[Dict[str, Any]]) -> Optional[Empresa]:
        empresa = await self.repository.get_by_id(empresa_id)
        if not empresa:
            raise ValueError(f"Empresa {empresa_id} no encontrada")
        
        codigos_validos = {t["codigo"] for t in TIPOLOGIAS_BASE}
        
        tipologias_procesadas = []
        for tip in tipologias:
            if tip.get("codigo") not in codigos_validos:
                logger.warning(f"Tipología desconocida: {tip.get('codigo')}")
                continue
            
            tipologias_procesadas.append({
                "codigo": tip["codigo"],
                "nombre": tip.get("nombre", ""),
                "descripcion": tip.get("descripcion", ""),
                "habilitada": tip.get("habilitada", True),
                "checklist_documentos": tip.get("checklist_documentos", []),
                "criterios_adicionales": tip.get("criterios_adicionales")
            })
        
        return await self.repository.update_tipologias(empresa_id, tipologias_procesadas)
    
    async def actualizar_vision_mision(
        self, 
        empresa_id: str, 
        vision: Optional[str] = None, 
        mision: Optional[str] = None
    ) -> Optional[Empresa]:
        empresa = await self.repository.get_by_id(empresa_id)
        if not empresa:
            raise ValueError(f"Empresa {empresa_id} no encontrada")
        
        return await self.repository.update_vision_mision(empresa_id, vision, mision)
    
    async def actualizar_pilares(
        self, 
        empresa_id: str, 
        pilares: List[PilarEstrategico]
    ) -> Optional[Empresa]:
        empresa = await self.repository.get_by_id(empresa_id)
        if not empresa:
            raise ValueError(f"Empresa {empresa_id} no encontrada")
        
        total_peso = sum(p.peso for p in pilares)
        if abs(total_peso - 1.0) > 0.01:
            raise ValueError(f"La suma de pesos debe ser 1.0, actual: {total_peso}")
        
        pilares_dict = [p.model_dump() for p in pilares]
        return await self.repository.update_pilares(empresa_id, pilares_dict)
    
    async def actualizar_okrs(
        self, 
        empresa_id: str, 
        okrs: List[OKR]
    ) -> Optional[Empresa]:
        empresa = await self.repository.get_by_id(empresa_id)
        if not empresa:
            raise ValueError(f"Empresa {empresa_id} no encontrada")
        
        okrs_dict = [o.model_dump() for o in okrs]
        return await self.repository.update_okrs(empresa_id, okrs_dict)
    
    async def desactivar_empresa(self, empresa_id: str) -> Optional[Empresa]:
        return await self.repository.soft_delete(empresa_id)


empresa_service = EmpresaService()
