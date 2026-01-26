"""
Defense Files - Integración Específica por Agente
Clases especializadas para cada agente de IA de Revisar.IA

Cada documentador hereda de AgentDocumentor y agrega métodos específicos
para el tipo de trabajo que realiza cada agente.
"""
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Union

from .agent_helper import (
    AgentDocumentor,
    TipoAnalisis,
    TipoCalculo,
    TipoDocumento,
    SeveridadAlerta
)

logger = logging.getLogger(__name__)


class FacturarIADocumentor(AgentDocumentor):
    """
    Documentador especializado para Facturar.IA (A1)
    Agente de chat de facturación y asistencia con CFDIs.
    
    Funcionalidades principales:
    - Chat interactivo sobre facturación
    - Validación de CFDIs
    - Consultas sobre deducibilidad
    - Cálculos de impuestos
    """
    
    def __init__(self):
        super().__init__(agente_id="A1", nombre_agente="Facturar.IA")
    
    async def registrar_chat_facturacion(
        self,
        defense_file_id: int,
        pregunta: str,
        respuesta: str,
        cfdis_analizados: Optional[List[str]] = None,
        conceptos_fiscales: Optional[List[str]] = None,
        monto_involucrado: Optional[float] = None,
        es_deducible: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        Registra una interacción del chat de facturación.
        
        Args:
            defense_file_id: ID del expediente
            pregunta: Pregunta del usuario
            respuesta: Respuesta del agente
            cfdis_analizados: UUIDs de CFDIs mencionados
            conceptos_fiscales: Conceptos fiscales discutidos
            monto_involucrado: Monto total involucrado
            es_deducible: Si se determinó que es deducible
        """
        self._log(f"Registrando chat de facturación")
        
        metadata = {}
        if monto_involucrado:
            metadata["monto_involucrado"] = monto_involucrado
        if es_deducible is not None:
            metadata["es_deducible"] = es_deducible
        
        return await self.registrar_conversacion(
            defense_file_id=defense_file_id,
            mensaje_usuario=pregunta,
            respuesta_ia=respuesta,
            cfdis_mencionados=cfdis_analizados,
            articulos_citados=conceptos_fiscales,
            metadata=metadata
        )
    
    async def registrar_validacion_cfdi(
        self,
        defense_file_id: int,
        uuid: str,
        emisor_rfc: str,
        total: float,
        status_sat: str,
        es_valido: bool,
        errores: Optional[List[str]] = None,
        warnings: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Registra la validación de un CFDI.
        
        Args:
            defense_file_id: ID del expediente
            uuid: UUID del CFDI
            emisor_rfc: RFC del emisor
            total: Monto total del CFDI
            status_sat: Estado en el SAT
            es_valido: Si el CFDI es válido
            errores: Errores encontrados
            warnings: Advertencias encontradas
        """
        self._log(f"Registrando validación CFDI: {uuid[:8]}...")
        
        datos = {
            "uuid": uuid,
            "emisor_rfc": emisor_rfc,
            "total": total,
            "status_sat": status_sat,
            "es_valido": es_valido,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if errores:
            datos["errores"] = errores
        if warnings:
            datos["warnings"] = warnings
        
        titulo = f"CFDI {'✅ válido' if es_valido else '❌ inválido'}: ${total:,.2f}"
        
        try:
            resultado = await self.service.registrar_evento(
                defense_file_id=defense_file_id,
                tipo="cfdi_validado",
                agente=self.agente_id,
                titulo=titulo,
                descripcion=f"Validación de CFDI {uuid[:8]}... del emisor {emisor_rfc}",
                datos=datos,
                tags=["cfdi_invalido"] if not es_valido else None
            )
            
            self._log(f"{'✅' if es_valido else '❌'} Validación CFDI registrada: {uuid[:8]}")
            return resultado
            
        except Exception as e:
            self._log(f"❌ Error registrando validación CFDI: {e}", "error")
            return {"success": False, "error": str(e)}
    
    async def registrar_consulta_deducibilidad(
        self,
        defense_file_id: int,
        concepto: str,
        monto: float,
        es_deducible: bool,
        fundamento: str,
        requisitos_cumplidos: Optional[List[str]] = None,
        requisitos_faltantes: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Registra una consulta de deducibilidad.
        """
        self._log(f"Registrando consulta deducibilidad: {concepto}")
        
        hallazgos = requisitos_faltantes if requisitos_faltantes else None
        recomendaciones = None
        if requisitos_faltantes:
            recomendaciones = [f"Cumplir requisito: {req}" for req in requisitos_faltantes]
        
        return await self.registrar_analisis(
            defense_file_id=defense_file_id,
            tipo_analisis=TipoAnalisis.FISCAL,
            objeto_analizado=f"Deducibilidad: {concepto}",
            resultado=f"{'Deducible' if es_deducible else 'No deducible'} - Monto: ${monto:,.2f}",
            hallazgos=hallazgos,
            recomendaciones=recomendaciones,
            score=100 if es_deducible else 0,
            metadata={
                "monto": monto,
                "fundamento": fundamento,
                "requisitos_cumplidos": requisitos_cumplidos
            }
        )


class BibliotecaIADocumentor(AgentDocumentor):
    """
    Documentador especializado para Biblioteca.IA (A2)
    Agente de consultas RAG y gestión del knowledge base.
    
    Funcionalidades principales:
    - Consultas semánticas al knowledge base
    - Búsqueda de jurisprudencia
    - Consultas de normativa fiscal
    - Gestión de documentos
    """
    
    def __init__(self):
        super().__init__(agente_id="A2", nombre_agente="Biblioteca.IA")
    
    async def registrar_busqueda_conocimiento(
        self,
        defense_file_id: int,
        query: str,
        resultados: List[Dict[str, Any]],
        categoria: Optional[str] = None,
        tiempo_busqueda_ms: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Registra una búsqueda en el knowledge base.
        
        Args:
            defense_file_id: ID del expediente
            query: Consulta realizada
            resultados: Resultados obtenidos
            categoria: Categoría de búsqueda (normativa, jurisprudencia, etc.)
            tiempo_busqueda_ms: Tiempo de búsqueda en milisegundos
        """
        self._log(f"Registrando búsqueda: {query[:50]}...")
        
        documentos = [r.get("documento", r.get("source", "")) for r in resultados[:10]]
        chunks_ids = [r.get("chunk_id") for r in resultados if r.get("chunk_id")]
        scores = [r.get("score", 0) for r in resultados]
        score_promedio = sum(scores) / len(scores) if scores else 0
        
        metadata = {}
        if categoria:
            metadata["categoria"] = categoria
        if tiempo_busqueda_ms:
            metadata["tiempo_busqueda_ms"] = tiempo_busqueda_ms
        
        return await self.registrar_consulta_rag(
            defense_file_id=defense_file_id,
            query=query,
            resultados=[str(r) for r in resultados[:5]],
            documentos_usados=documentos,
            chunks_ids=chunks_ids[:20] if chunks_ids else None,
            score_relevancia=score_promedio,
            metadata=metadata
        )
    
    async def registrar_consulta_jurisprudencia(
        self,
        defense_file_id: int,
        tema: str,
        tesis_encontradas: List[Dict[str, Any]],
        tribunal: Optional[str] = None,
        epoca: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Registra una consulta de jurisprudencia.
        
        Args:
            defense_file_id: ID del expediente
            tema: Tema consultado
            tesis_encontradas: Tesis encontradas
            tribunal: Tribunal específico (SCJN, TFJA, TCC, etc.)
            epoca: Época jurisprudencial
        """
        self._log(f"Registrando consulta jurisprudencia: {tema}")
        
        datos = {
            "tema": tema,
            "num_tesis": len(tesis_encontradas),
            "tesis": [
                {
                    "clave": t.get("clave", ""),
                    "titulo": t.get("titulo", "")[:200],
                    "tribunal": t.get("tribunal", tribunal)
                }
                for t in tesis_encontradas[:10]
            ]
        }
        
        if tribunal:
            datos["tribunal_filtro"] = tribunal
        if epoca:
            datos["epoca"] = epoca
        
        try:
            resultado = await self.service.registrar_evento(
                defense_file_id=defense_file_id,
                tipo="consulta_rag",
                agente=self.agente_id,
                titulo=f"Consulta jurisprudencia: {tema[:60]}",
                descripcion=f"Búsqueda de jurisprudencia - {len(tesis_encontradas)} tesis encontradas",
                datos=datos,
                subtipo="jurisprudencia"
            )
            
            self._log(f"✅ Consulta jurisprudencia registrada ({len(tesis_encontradas)} tesis)")
            return resultado
            
        except Exception as e:
            self._log(f"❌ Error registrando consulta jurisprudencia: {e}", "error")
            return {"success": False, "error": str(e)}
    
    async def registrar_consulta_normativa(
        self,
        defense_file_id: int,
        ley: str,
        articulos: List[str],
        contexto: str,
        extractos: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Registra una consulta de normativa fiscal.
        
        Args:
            defense_file_id: ID del expediente
            ley: Ley consultada (CFF, LISR, LIVA, etc.)
            articulos: Artículos consultados
            contexto: Contexto de la consulta
            extractos: Extractos relevantes de los artículos
        """
        self._log(f"Registrando consulta normativa: {ley} Arts. {', '.join(articulos[:3])}")
        
        for articulo in articulos[:5]:
            extracto = None
            if extractos and len(extractos) > articulos.index(articulo):
                extracto = extractos[articulos.index(articulo)]
            
            await self.registrar_fundamento_legal(
                defense_file_id=defense_file_id,
                tipo="ley",
                documento=ley,
                articulo=articulo,
                texto_relevante=extracto,
                aplicacion=contexto
            )
        
        return {"success": True, "articulos_registrados": len(articulos)}


class RevisarIADocumentor(AgentDocumentor):
    """
    Documentador especializado para Revisar.IA (A3)
    Agente principal de revisiones fiscales y auditoría.
    
    Funcionalidades principales:
    - Revisiones fiscales completas
    - Análisis de riesgo
    - Verificación de cumplimiento
    - Detección de anomalías
    """
    
    def __init__(self):
        super().__init__(agente_id="A3", nombre_agente="Revisar.IA")
    
    async def registrar_revision_fiscal(
        self,
        defense_file_id: int,
        tipo_revision: str,
        periodo: str,
        hallazgos: List[Dict[str, Any]],
        score_riesgo: float,
        monto_observado: Optional[float] = None,
        recomendaciones: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Registra una revisión fiscal completa.
        
        Args:
            defense_file_id: ID del expediente
            tipo_revision: Tipo de revisión (deducciones, proveedores, etc.)
            periodo: Período fiscal revisado
            hallazgos: Lista de hallazgos
            score_riesgo: Score de riesgo (0-100)
            monto_observado: Monto total observado
            recomendaciones: Recomendaciones de la revisión
        """
        self._log(f"Registrando revisión fiscal: {tipo_revision} - {periodo}")
        
        hallazgos_str = [
            f"{h.get('tipo', 'Hallazgo')}: {h.get('descripcion', str(h))[:100]}"
            for h in hallazgos[:20]
        ]
        
        metadata = {
            "periodo": periodo,
            "tipo_revision": tipo_revision,
            "num_hallazgos": len(hallazgos),
            "hallazgos_detalle": hallazgos[:10]
        }
        
        if monto_observado:
            metadata["monto_observado"] = monto_observado
        
        return await self.registrar_analisis(
            defense_file_id=defense_file_id,
            tipo_analisis=TipoAnalisis.FISCAL,
            objeto_analizado=f"Revisión {tipo_revision} - Período {periodo}",
            resultado=f"Score de riesgo: {score_riesgo:.1f}/100 - {len(hallazgos)} hallazgos",
            hallazgos=hallazgos_str,
            recomendaciones=recomendaciones,
            score=100 - score_riesgo,
            metadata=metadata
        )
    
    async def registrar_analisis_proveedor(
        self,
        defense_file_id: int,
        rfc: str,
        razon_social: str,
        monto_operaciones: float,
        resultado_69b: str,
        resultado_efos: str,
        nivel_riesgo: str,
        operaciones_revisadas: int,
        alertas: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Registra un análisis completo de proveedor.
        """
        self._log(f"Registrando análisis proveedor: {rfc}")
        
        await self.registrar_verificacion_proveedor(
            defense_file_id=defense_file_id,
            rfc=rfc,
            razon_social=razon_social,
            resultado_69b=resultado_69b,
            resultado_efos=resultado_efos,
            nivel_riesgo=nivel_riesgo,
            metadata={
                "monto_operaciones": monto_operaciones,
                "operaciones_revisadas": operaciones_revisadas,
                "alertas": alertas
            }
        )
        
        if alertas and len(alertas) > 0:
            severidad = SeveridadAlerta.ALTA if nivel_riesgo in ["alto", "critico"] else SeveridadAlerta.MEDIA
            await self.registrar_alerta(
                defense_file_id=defense_file_id,
                tipo_alerta="proveedor_riesgoso",
                titulo=f"Proveedor con riesgo: {rfc}",
                descripcion=f"Se detectaron {len(alertas)} alertas para {razon_social}",
                severidad=severidad,
                datos={"rfc": rfc, "alertas": alertas},
                requiere_accion=True
            )
        
        return {"success": True}
    
    async def registrar_anomalia_detectada(
        self,
        defense_file_id: int,
        tipo_anomalia: str,
        descripcion: str,
        monto_afectado: float,
        evidencia: Dict[str, Any],
        severidad: Union[SeveridadAlerta, str] = SeveridadAlerta.MEDIA
    ) -> Dict[str, Any]:
        """
        Registra una anomalía detectada durante la revisión.
        """
        self._log(f"Registrando anomalía: {tipo_anomalia}")
        
        return await self.registrar_alerta(
            defense_file_id=defense_file_id,
            tipo_alerta=f"anomalia_{tipo_anomalia}",
            titulo=f"Anomalía detectada: {tipo_anomalia}",
            descripcion=descripcion,
            severidad=severidad,
            datos={
                "monto_afectado": monto_afectado,
                "evidencia": evidencia
            },
            requiere_accion=True
        )


class TraficoIADocumentor(AgentDocumentor):
    """
    Documentador especializado para Tráfico.IA (A4)
    Agente de monitoreo y alertas de proyectos.
    
    Funcionalidades principales:
    - Monitoreo de proyectos
    - Generación de alertas
    - Seguimiento de vencimientos
    - Notificaciones automáticas
    """
    
    def __init__(self):
        super().__init__(agente_id="A4", nombre_agente="Tráfico.IA")
    
    async def registrar_monitoreo_proyecto(
        self,
        defense_file_id: int,
        proyecto_id: str,
        nombre_proyecto: str,
        fase_actual: str,
        status: str,
        dias_sin_actividad: int,
        alertas_generadas: int
    ) -> Dict[str, Any]:
        """
        Registra el monitoreo de un proyecto.
        
        Args:
            defense_file_id: ID del expediente
            proyecto_id: ID del proyecto monitoreado
            nombre_proyecto: Nombre del proyecto
            fase_actual: Fase actual del proyecto
            status: Estado actual
            dias_sin_actividad: Días sin actividad
            alertas_generadas: Número de alertas generadas
        """
        self._log(f"Registrando monitoreo proyecto: {proyecto_id}")
        
        datos = {
            "proyecto_id": proyecto_id,
            "nombre_proyecto": nombre_proyecto,
            "fase_actual": fase_actual,
            "status": status,
            "dias_sin_actividad": dias_sin_actividad,
            "alertas_generadas": alertas_generadas,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        try:
            resultado = await self.service.registrar_evento(
                defense_file_id=defense_file_id,
                tipo="analisis_ia",
                agente=self.agente_id,
                titulo=f"Monitoreo: {nombre_proyecto[:50]}",
                descripcion=f"Proyecto en fase {fase_actual}, {dias_sin_actividad} días sin actividad",
                datos=datos,
                subtipo="monitoreo_proyecto"
            )
            
            self._log(f"✅ Monitoreo registrado: {proyecto_id}")
            return resultado
            
        except Exception as e:
            self._log(f"❌ Error registrando monitoreo: {e}", "error")
            return {"success": False, "error": str(e)}
    
    async def registrar_alerta_vencimiento(
        self,
        defense_file_id: int,
        tipo_vencimiento: str,
        fecha_vencimiento: datetime,
        dias_restantes: int,
        entidad_afectada: str,
        accion_requerida: str
    ) -> Dict[str, Any]:
        """
        Registra una alerta de vencimiento.
        """
        self._log(f"Registrando alerta vencimiento: {tipo_vencimiento}")
        
        if dias_restantes <= 0:
            severidad = SeveridadAlerta.CRITICA
        elif dias_restantes <= 3:
            severidad = SeveridadAlerta.ALTA
        elif dias_restantes <= 7:
            severidad = SeveridadAlerta.MEDIA
        else:
            severidad = SeveridadAlerta.BAJA
        
        return await self.registrar_alerta(
            defense_file_id=defense_file_id,
            tipo_alerta="vencimiento",
            titulo=f"Vencimiento próximo: {tipo_vencimiento}",
            descripcion=f"{entidad_afectada} - {dias_restantes} días restantes. Acción: {accion_requerida}",
            severidad=severidad,
            datos={
                "tipo_vencimiento": tipo_vencimiento,
                "fecha_vencimiento": fecha_vencimiento.isoformat(),
                "dias_restantes": dias_restantes,
                "entidad_afectada": entidad_afectada
            },
            requiere_accion=True,
            fecha_limite=fecha_vencimiento
        )
    
    async def registrar_notificacion_enviada(
        self,
        defense_file_id: int,
        tipo_notificacion: str,
        destinatarios: List[str],
        asunto: str,
        canal: str = "email",
        exitoso: bool = True
    ) -> Dict[str, Any]:
        """
        Registra una notificación enviada.
        """
        self._log(f"Registrando notificación: {asunto[:50]}")
        
        datos = {
            "tipo_notificacion": tipo_notificacion,
            "destinatarios": destinatarios,
            "asunto": asunto,
            "canal": canal,
            "exitoso": exitoso,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        try:
            resultado = await self.service.registrar_evento(
                defense_file_id=defense_file_id,
                tipo="email_enviado",
                agente=self.agente_id,
                titulo=f"Notificación {'✅' if exitoso else '❌'}: {asunto[:50]}",
                descripcion=f"Notificación por {canal} a {len(destinatarios)} destinatarios",
                datos=datos,
                subtipo=tipo_notificacion
            )
            
            self._log(f"{'✅' if exitoso else '❌'} Notificación registrada")
            return resultado
            
        except Exception as e:
            self._log(f"❌ Error registrando notificación: {e}", "error")
            return {"success": False, "error": str(e)}


class DisenarIADocumentor(AgentDocumentor):
    """
    Documentador especializado para Diseñar.IA (A5)
    Agente de auditorías UI y generación de reportes visuales.
    
    Funcionalidades principales:
    - Auditorías de interfaz
    - Generación de dashboards
    - Análisis de usabilidad
    - Reportes visuales
    """
    
    def __init__(self):
        super().__init__(agente_id="A5", nombre_agente="Diseñar.IA")
    
    async def registrar_auditoria_ui(
        self,
        defense_file_id: int,
        seccion: str,
        hallazgos_ux: List[Dict[str, Any]],
        score_usabilidad: float,
        capturas: Optional[List[str]] = None,
        recomendaciones: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Registra una auditoría de UI/UX.
        
        Args:
            defense_file_id: ID del expediente
            seccion: Sección auditada
            hallazgos_ux: Hallazgos de usabilidad
            score_usabilidad: Score de usabilidad (0-100)
            capturas: Rutas a capturas de pantalla
            recomendaciones: Mejoras recomendadas
        """
        self._log(f"Registrando auditoría UI: {seccion}")
        
        hallazgos_str = [
            f"{h.get('tipo', 'UX')}: {h.get('descripcion', str(h))[:80]}"
            for h in hallazgos_ux[:15]
        ]
        
        metadata = {
            "seccion": seccion,
            "num_hallazgos": len(hallazgos_ux),
            "hallazgos_detalle": hallazgos_ux[:10]
        }
        
        if capturas:
            metadata["capturas"] = capturas
        
        return await self.registrar_analisis(
            defense_file_id=defense_file_id,
            tipo_analisis="usabilidad",
            objeto_analizado=f"Auditoría UI: {seccion}",
            resultado=f"Score usabilidad: {score_usabilidad:.1f}/100",
            hallazgos=hallazgos_str,
            recomendaciones=recomendaciones,
            score=score_usabilidad,
            metadata=metadata
        )
    
    async def registrar_reporte_generado(
        self,
        defense_file_id: int,
        tipo_reporte: str,
        nombre: str,
        formato: str,
        ruta_archivo: str,
        datos_incluidos: Optional[Dict[str, Any]] = None,
        paginas: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Registra un reporte visual generado.
        
        Args:
            defense_file_id: ID del expediente
            tipo_reporte: Tipo de reporte (dashboard, pdf, excel, etc.)
            nombre: Nombre del reporte
            formato: Formato del archivo
            ruta_archivo: Ruta donde se guardó
            datos_incluidos: Resumen de datos incluidos
            paginas: Número de páginas (si aplica)
        """
        self._log(f"Registrando reporte: {nombre}")
        
        metadata = {
            "tipo_reporte": tipo_reporte,
            "formato": formato
        }
        
        if datos_incluidos:
            metadata["datos_incluidos"] = datos_incluidos
        if paginas:
            metadata["paginas"] = paginas
        
        return await self.registrar_documento_procesado(
            defense_file_id=defense_file_id,
            tipo_documento=TipoDocumento.OTRO,
            nombre=nombre,
            contenido=f"Reporte {tipo_reporte} en formato {formato}",
            metadata=metadata,
            archivo_path=ruta_archivo
        )
    
    async def registrar_dashboard_actualizado(
        self,
        defense_file_id: int,
        nombre_dashboard: str,
        widgets_actualizados: List[str],
        datos_frescos: bool,
        tiempo_carga_ms: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Registra la actualización de un dashboard.
        """
        self._log(f"Registrando actualización dashboard: {nombre_dashboard}")
        
        datos = {
            "nombre_dashboard": nombre_dashboard,
            "widgets_actualizados": widgets_actualizados,
            "num_widgets": len(widgets_actualizados),
            "datos_frescos": datos_frescos,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if tiempo_carga_ms:
            datos["tiempo_carga_ms"] = tiempo_carga_ms
        
        try:
            resultado = await self.service.registrar_evento(
                defense_file_id=defense_file_id,
                tipo="analisis_ia",
                agente=self.agente_id,
                titulo=f"Dashboard actualizado: {nombre_dashboard}",
                descripcion=f"Se actualizaron {len(widgets_actualizados)} widgets",
                datos=datos,
                subtipo="dashboard_update"
            )
            
            self._log(f"✅ Dashboard {nombre_dashboard} registrado")
            return resultado
            
        except Exception as e:
            self._log(f"❌ Error registrando dashboard: {e}", "error")
            return {"success": False, "error": str(e)}


facturar_ia_documentor = FacturarIADocumentor()
biblioteca_ia_documentor = BibliotecaIADocumentor()
revisar_ia_documentor = RevisarIADocumentor()
trafico_ia_documentor = TraficoIADocumentor()
disenar_ia_documentor = DisenarIADocumentor()
