"""
Defense Files - Agent Helper
Clase helper para que los agentes de IA documenten sus acciones en expedientes de defensa

Proporciona una interfaz unificada para registrar diferentes tipos de eventos
como conversaciones, análisis, documentos procesados, cálculos, consultas RAG, etc.
"""
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from enum import Enum

logger = logging.getLogger(__name__)


class TipoAnalisis(str, Enum):
    FISCAL = "fiscal"
    LEGAL = "legal"
    FINANCIERO = "financiero"
    RIESGO = "riesgo"
    CUMPLIMIENTO = "cumplimiento"
    MATERIALIDAD = "materialidad"
    RAZON_NEGOCIOS = "razon_negocios"


class TipoCalculo(str, Enum):
    ISR = "isr"
    IVA = "iva"
    RETENCION = "retencion"
    DEDUCCION = "deduccion"
    BASE_GRAVABLE = "base_gravable"
    ACTUALIZACION = "actualizacion"
    RECARGOS = "recargos"
    MULTA = "multa"


class SeveridadAlerta(str, Enum):
    BAJA = "baja"
    MEDIA = "media"
    ALTA = "alta"
    CRITICA = "critica"


class TipoDocumento(str, Enum):
    CFDI = "cfdi"
    CONTRATO = "contrato"
    ACTA = "acta"
    EVIDENCIA = "evidencia"
    DICTAMEN = "dictamen"
    CONSTANCIA = "constancia"
    OTRO = "otro"


class AgentDocumentor:
    """
    Clase base para documentar acciones de agentes en expedientes de defensa.
    
    Proporciona métodos para registrar diferentes tipos de eventos:
    - Conversaciones con usuarios
    - Análisis realizados
    - Documentos procesados
    - Cálculos fiscales
    - Consultas RAG
    - Verificaciones de proveedores
    - Alertas generadas
    
    Cada agente puede heredar de esta clase y agregar métodos especializados.
    
    Uso básico:
        documentor = AgentDocumentor(agente_id="A1", nombre_agente="Facturar.IA")
        await documentor.registrar_conversacion(
            defense_file_id=123,
            mensaje_usuario="¿Cómo deduzco esta factura?",
            respuesta_ia="Para deducir esta factura..."
        )
    """
    
    def __init__(self, agente_id: str, nombre_agente: str):
        """
        Inicializa el documentador de agente.
        
        Args:
            agente_id: Identificador del agente (A1, A2, A3, etc.)
            nombre_agente: Nombre descriptivo del agente
        """
        self.agente_id = agente_id
        self.nombre_agente = nombre_agente
        self._service = None
        logger.info(f"📁 [{agente_id}] {nombre_agente}: Documentador inicializado")
    
    @property
    def service(self):
        """Obtiene el servicio de defense files de forma lazy."""
        if self._service is None:
            from services.defense_file_pg_service import defense_file_pg_service
            self._service = defense_file_pg_service
        return self._service
    
    def _log(self, mensaje: str, nivel: str = "info"):
        """Registra un mensaje de log con el prefijo del agente."""
        prefijo = f"📁 [{self.agente_id}] {self.nombre_agente}:"
        log_msg = f"{prefijo} {mensaje}"
        if nivel == "error":
            logger.error(log_msg)
        elif nivel == "warning":
            logger.warning(log_msg)
        elif nivel == "debug":
            logger.debug(log_msg)
        else:
            logger.info(log_msg)
    
    async def registrar_conversacion(
        self,
        defense_file_id: int,
        mensaje_usuario: str,
        respuesta_ia: str,
        fuentes_consultadas: Optional[List[str]] = None,
        cfdis_mencionados: Optional[List[str]] = None,
        articulos_citados: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Registra una conversación entre el usuario y el agente de IA.
        
        Args:
            defense_file_id: ID del expediente de defensa
            mensaje_usuario: Mensaje enviado por el usuario
            respuesta_ia: Respuesta generada por la IA
            fuentes_consultadas: Lista de fuentes usadas para la respuesta
            cfdis_mencionados: Lista de UUIDs de CFDIs mencionados
            articulos_citados: Lista de artículos legales citados (ej: ["CFF-5A", "LISR-27"])
            metadata: Datos adicionales de la conversación
            
        Returns:
            Resultado del registro del evento
        """
        self._log(f"Registrando conversación en expediente {defense_file_id}")
        
        datos = {
            "mensaje_usuario": mensaje_usuario[:500],
            "respuesta_ia": respuesta_ia[:2000],
            "longitud_mensaje": len(mensaje_usuario),
            "longitud_respuesta": len(respuesta_ia),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if fuentes_consultadas:
            datos["fuentes_consultadas"] = fuentes_consultadas[:20]
        if cfdis_mencionados:
            datos["cfdis_mencionados"] = cfdis_mencionados[:50]
        if articulos_citados:
            datos["articulos_citados"] = articulos_citados[:30]
        if metadata:
            datos["metadata"] = metadata
        
        try:
            resultado = await self.service.registrar_evento(
                defense_file_id=defense_file_id,
                tipo="conversacion",
                agente=self.agente_id,
                titulo=f"Conversación: {mensaje_usuario[:80]}...",
                descripcion=f"El usuario consultó al agente {self.nombre_agente}",
                datos=datos
            )
            
            self._log(f"✅ Conversación registrada correctamente")
            return resultado
            
        except Exception as e:
            self._log(f"❌ Error registrando conversación: {e}", "error")
            return {"success": False, "error": str(e)}
    
    async def registrar_analisis(
        self,
        defense_file_id: int,
        tipo_analisis: Union[TipoAnalisis, str],
        objeto_analizado: str,
        resultado: str,
        hallazgos: Optional[List[str]] = None,
        recomendaciones: Optional[List[str]] = None,
        score: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Registra un análisis realizado por el agente.
        
        Args:
            defense_file_id: ID del expediente de defensa
            tipo_analisis: Tipo de análisis (fiscal, legal, financiero, etc.)
            objeto_analizado: Descripción de lo que se analizó
            resultado: Resultado del análisis
            hallazgos: Lista de hallazgos encontrados
            recomendaciones: Lista de recomendaciones
            score: Puntuación del análisis (0-100)
            metadata: Datos adicionales
            
        Returns:
            Resultado del registro del evento
        """
        if isinstance(tipo_analisis, TipoAnalisis):
            tipo_analisis = tipo_analisis.value
        
        self._log(f"Registrando análisis {tipo_analisis} en expediente {defense_file_id}")
        
        datos = {
            "tipo_analisis": tipo_analisis,
            "objeto_analizado": objeto_analizado[:500],
            "resultado": resultado[:2000],
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if hallazgos:
            datos["hallazgos"] = hallazgos[:20]
        if recomendaciones:
            datos["recomendaciones"] = recomendaciones[:20]
        if score is not None:
            datos["score"] = min(max(score, 0), 100)
        if metadata:
            datos["metadata"] = metadata
        
        try:
            resultado_registro = await self.service.registrar_evento(
                defense_file_id=defense_file_id,
                tipo="analisis_ia",
                agente=self.agente_id,
                titulo=f"Análisis {tipo_analisis}: {objeto_analizado[:60]}",
                descripcion=f"Análisis realizado por {self.nombre_agente}",
                datos=datos,
                subtipo=tipo_analisis
            )
            
            self._log(f"✅ Análisis {tipo_analisis} registrado correctamente")
            return resultado_registro
            
        except Exception as e:
            self._log(f"❌ Error registrando análisis: {e}", "error")
            return {"success": False, "error": str(e)}
    
    async def registrar_documento_procesado(
        self,
        defense_file_id: int,
        tipo_documento: Union[TipoDocumento, str],
        nombre: str,
        contenido: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        archivo_path: Optional[str] = None,
        hash_contenido: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Registra un documento procesado por el agente.
        
        Args:
            defense_file_id: ID del expediente de defensa
            tipo_documento: Tipo de documento (CFDI, contrato, acta, etc.)
            nombre: Nombre del documento
            contenido: Contenido o resumen del documento
            metadata: Metadatos del documento
            archivo_path: Ruta al archivo del documento
            hash_contenido: Hash SHA256 del contenido para verificación
            
        Returns:
            Resultado del registro del evento
        """
        if isinstance(tipo_documento, TipoDocumento):
            tipo_documento = tipo_documento.value
        
        self._log(f"Registrando documento {tipo_documento}: {nombre}")
        
        datos = {
            "tipo_documento": tipo_documento,
            "nombre": nombre,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if contenido:
            datos["contenido_preview"] = contenido[:1000]
            datos["longitud_contenido"] = len(contenido)
        if metadata:
            datos["metadata"] = metadata
        if archivo_path:
            datos["archivo_path"] = archivo_path
        if hash_contenido:
            datos["hash_contenido"] = hash_contenido
        
        try:
            resultado = await self.service.registrar_evento(
                defense_file_id=defense_file_id,
                tipo="documento_subido",
                agente=self.agente_id,
                titulo=f"Documento procesado: {nombre[:80]}",
                descripcion=f"Documento tipo {tipo_documento} procesado por {self.nombre_agente}",
                datos=datos,
                subtipo=tipo_documento
            )
            
            self._log(f"✅ Documento {nombre} registrado correctamente")
            return resultado
            
        except Exception as e:
            self._log(f"❌ Error registrando documento: {e}", "error")
            return {"success": False, "error": str(e)}
    
    async def registrar_calculo(
        self,
        defense_file_id: int,
        tipo_calculo: Union[TipoCalculo, str],
        concepto: str,
        resultado: float,
        formula: Optional[str] = None,
        fundamento: Optional[str] = None,
        datos_entrada: Optional[Dict[str, Any]] = None,
        periodo: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Registra un cálculo fiscal o financiero realizado.
        
        Args:
            defense_file_id: ID del expediente de defensa
            tipo_calculo: Tipo de cálculo (ISR, IVA, retención, etc.)
            concepto: Descripción del concepto calculado
            resultado: Resultado numérico del cálculo
            formula: Fórmula o método utilizado
            fundamento: Fundamento legal del cálculo
            datos_entrada: Datos utilizados para el cálculo
            periodo: Período fiscal del cálculo
            
        Returns:
            Resultado del registro del evento
        """
        if isinstance(tipo_calculo, TipoCalculo):
            tipo_calculo = tipo_calculo.value
        
        self._log(f"Registrando cálculo {tipo_calculo}: {concepto}")
        
        datos = {
            "tipo_calculo": tipo_calculo,
            "concepto": concepto,
            "resultado": resultado,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if formula:
            datos["formula"] = formula
        if fundamento:
            datos["fundamento"] = fundamento
        if datos_entrada:
            datos["datos_entrada"] = datos_entrada
        if periodo:
            datos["periodo"] = periodo
        
        try:
            resultado_db = await self.service.registrar_evento(
                defense_file_id=defense_file_id,
                tipo="calculo_realizado",
                agente=self.agente_id,
                titulo=f"Cálculo {tipo_calculo}: ${resultado:,.2f}",
                descripcion=f"Cálculo de {concepto} por {self.nombre_agente}",
                datos=datos,
                subtipo=tipo_calculo
            )
            
            self._log(f"✅ Cálculo {tipo_calculo} registrado: ${resultado:,.2f}")
            return resultado_db
            
        except Exception as e:
            self._log(f"❌ Error registrando cálculo: {e}", "error")
            return {"success": False, "error": str(e)}
    
    async def registrar_consulta_rag(
        self,
        defense_file_id: int,
        query: str,
        resultados: List[str],
        documentos_usados: Optional[List[str]] = None,
        chunks_ids: Optional[List[int]] = None,
        score_relevancia: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Registra una consulta al sistema RAG.
        
        Args:
            defense_file_id: ID del expediente de defensa
            query: Consulta realizada
            resultados: Lista de resultados obtenidos
            documentos_usados: Nombres de documentos consultados
            chunks_ids: IDs de los chunks recuperados
            score_relevancia: Puntuación de relevancia promedio
            metadata: Datos adicionales de la consulta
            
        Returns:
            Resultado del registro del evento
        """
        self._log(f"Registrando consulta RAG: {query[:50]}...")
        
        datos = {
            "query": query,
            "num_resultados": len(resultados),
            "resultados_preview": [r[:200] for r in resultados[:5]],
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if documentos_usados:
            datos["documentos_usados"] = documentos_usados[:20]
        if chunks_ids:
            datos["chunks_ids"] = chunks_ids[:50]
        if score_relevancia is not None:
            datos["score_relevancia"] = score_relevancia
        if metadata:
            datos["metadata"] = metadata
        
        try:
            resultado = await self.service.registrar_evento(
                defense_file_id=defense_file_id,
                tipo="consulta_rag",
                agente=self.agente_id,
                titulo=f"Consulta RAG: {query[:60]}...",
                descripcion=f"Consulta al knowledge base por {self.nombre_agente}",
                datos=datos
            )
            
            self._log(f"✅ Consulta RAG registrada ({len(resultados)} resultados)")
            return resultado
            
        except Exception as e:
            self._log(f"❌ Error registrando consulta RAG: {e}", "error")
            return {"success": False, "error": str(e)}
    
    async def registrar_verificacion_proveedor(
        self,
        defense_file_id: int,
        rfc: str,
        resultado_69b: Optional[str] = None,
        resultado_efos: Optional[str] = None,
        opinion_cumplimiento: Optional[str] = None,
        nivel_riesgo: Optional[str] = None,
        razon_social: Optional[str] = None,
        fecha_verificacion: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Registra una verificación de proveedor (69-B, EFOS, opinión de cumplimiento).
        
        Args:
            defense_file_id: ID del expediente de defensa
            rfc: RFC del proveedor verificado
            resultado_69b: Estado en lista 69-B (LISTADO, NO_LISTADO, DESVIRTUADO, etc.)
            resultado_efos: Estado EFOS (DEFINITIVO, PRESUNTO, DESVIRTUADO, NO_LISTADO)
            opinion_cumplimiento: Resultado de opinión de cumplimiento
            nivel_riesgo: Nivel de riesgo determinado (bajo, medio, alto, crítico)
            razon_social: Razón social del proveedor
            fecha_verificacion: Fecha de la verificación
            metadata: Datos adicionales
            
        Returns:
            Resultado del registro del evento
        """
        self._log(f"Registrando verificación de proveedor RFC: {rfc}")
        
        datos = {
            "rfc": rfc,
            "fecha_verificacion": (fecha_verificacion or datetime.utcnow()).isoformat()
        }
        
        if razon_social:
            datos["razon_social"] = razon_social
        if resultado_69b:
            datos["resultado_69b"] = resultado_69b
        if resultado_efos:
            datos["resultado_efos"] = resultado_efos
        if opinion_cumplimiento:
            datos["opinion_cumplimiento"] = opinion_cumplimiento
        if nivel_riesgo:
            datos["nivel_riesgo"] = nivel_riesgo
        if metadata:
            datos["metadata"] = metadata
        
        es_riesgoso = resultado_69b in ["LISTADO", "PRESUNTO"] or resultado_efos in ["DEFINITIVO", "PRESUNTO"]
        
        try:
            resultado = await self.service.registrar_evento(
                defense_file_id=defense_file_id,
                tipo="proveedor_verificado",
                agente=self.agente_id,
                titulo=f"Verificación proveedor: {rfc}",
                descripcion=f"Proveedor verificado por {self.nombre_agente}" + 
                           (f" - ⚠️ RIESGO DETECTADO" if es_riesgoso else " - Sin alertas"),
                datos=datos,
                tags=["riesgo_alto"] if es_riesgoso else None
            )
            
            status = "⚠️" if es_riesgoso else "✅"
            self._log(f"{status} Verificación de {rfc} registrada")
            return resultado
            
        except Exception as e:
            self._log(f"❌ Error registrando verificación: {e}", "error")
            return {"success": False, "error": str(e)}
    
    async def registrar_alerta(
        self,
        defense_file_id: int,
        tipo_alerta: str,
        titulo: str,
        descripcion: str,
        severidad: Union[SeveridadAlerta, str] = SeveridadAlerta.MEDIA,
        datos: Optional[Dict[str, Any]] = None,
        requiere_accion: bool = False,
        fecha_limite: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Registra una alerta generada por el agente.
        
        Args:
            defense_file_id: ID del expediente de defensa
            tipo_alerta: Tipo específico de alerta
            titulo: Título de la alerta
            descripcion: Descripción detallada
            severidad: Nivel de severidad (baja, media, alta, crítica)
            datos: Datos adicionales de la alerta
            requiere_accion: Si requiere acción del usuario
            fecha_limite: Fecha límite para atender la alerta
            
        Returns:
            Resultado del registro del evento
        """
        if isinstance(severidad, SeveridadAlerta):
            severidad = severidad.value
        
        self._log(f"Registrando alerta [{severidad.upper()}]: {titulo}")
        
        datos_alerta = {
            "tipo_alerta": tipo_alerta,
            "severidad": severidad,
            "requiere_accion": requiere_accion,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if datos:
            datos_alerta["datos"] = datos
        if fecha_limite:
            datos_alerta["fecha_limite"] = fecha_limite.isoformat()
        
        tags = [f"severidad_{severidad}"]
        if requiere_accion:
            tags.append("requiere_accion")
        if severidad in ["alta", "critica"]:
            tags.append("urgente")
        
        try:
            resultado = await self.service.registrar_evento(
                defense_file_id=defense_file_id,
                tipo="alerta_generada",
                agente=self.agente_id,
                titulo=f"🚨 {titulo}",
                descripcion=descripcion,
                datos=datos_alerta,
                subtipo=tipo_alerta,
                tags=tags
            )
            
            icono = "🔴" if severidad == "critica" else "🟠" if severidad == "alta" else "🟡" if severidad == "media" else "🟢"
            self._log(f"{icono} Alerta registrada: {titulo}")
            return resultado
            
        except Exception as e:
            self._log(f"❌ Error registrando alerta: {e}", "error")
            return {"success": False, "error": str(e)}
    
    async def registrar_fundamento_legal(
        self,
        defense_file_id: int,
        tipo: str,
        documento: str,
        articulo: str,
        texto_relevante: Optional[str] = None,
        fraccion: Optional[str] = None,
        parrafo: Optional[str] = None,
        aplicacion: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Registra un fundamento legal citado.
        
        Args:
            defense_file_id: ID del expediente de defensa
            tipo: Tipo de fundamento (ley, reglamento, jurisprudencia, etc.)
            documento: Nombre del documento (CFF, LISR, RMF 2024, etc.)
            articulo: Número de artículo
            texto_relevante: Texto del artículo o fracción relevante
            fraccion: Fracción específica (si aplica)
            parrafo: Párrafo específico (si aplica)
            aplicacion: Cómo se aplica este fundamento al caso
            
        Returns:
            Resultado del registro
        """
        self._log(f"Registrando fundamento legal: {documento} Art. {articulo}")
        
        try:
            resultado = await self.service.registrar_fundamento(
                defense_file_id=defense_file_id,
                tipo=tipo,
                documento=documento,
                articulo=articulo,
                texto_relevante=texto_relevante,
                fraccion=fraccion,
                parrafo=parrafo,
                aplicacion=aplicacion
            )
            
            self._log(f"✅ Fundamento {documento} Art. {articulo} registrado")
            return resultado
            
        except Exception as e:
            self._log(f"❌ Error registrando fundamento: {e}", "error")
            return {"success": False, "error": str(e)}
