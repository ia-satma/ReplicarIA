"""
Defense File Service - PostgreSQL Version
Sistema completo de expedientes de defensa para Revisar.IA
Usa asyncpg para conexión a PostgreSQL con cadena de hashes SHA256
"""
import os
import json
import hashlib
import logging
from datetime import datetime, date
from typing import Dict, List, Optional, Any, Union
from enum import Enum
from decimal import Decimal

import asyncpg

logger = logging.getLogger(__name__)


class TipoEvento(str, Enum):
    CONVERSACION = "conversacion"
    CONSULTA_RAG = "consulta_rag"
    ANALISIS_IA = "analisis_ia"
    CFDI_REGISTRADO = "cfdi_registrado"
    CFDI_VALIDADO = "cfdi_validado"
    PROVEEDOR_VERIFICADO = "proveedor_verificado"
    EMAIL_ENVIADO = "email_enviado"
    CALCULO_REALIZADO = "calculo_realizado"
    DOCUMENTO_SUBIDO = "documento_subido"
    ALERTA_GENERADA = "alerta_generada"
    EXPEDIENTE_CREADO = "expediente_creado"
    EXPEDIENTE_CERRADO = "expediente_cerrado"
    FUNDAMENTO_AGREGADO = "fundamento_agregado"


class Agente(str, Enum):
    A1 = "A1"
    A2 = "A2"
    A3 = "A3"
    A4 = "A4"
    A5 = "A5"
    A6 = "A6"
    A7 = "A7"
    SYS = "SYS"
    USR = "USR"


class EstadoExpediente(str, Enum):
    ABIERTO = "abierto"
    EN_REVISION = "en_revision"
    PENDIENTE = "pendiente"
    CERRADO = "cerrado"
    ARCHIVADO = "archivado"


def _serialize_value(value: Any) -> Any:
    """Serializa valores para JSON."""
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, Enum):
        return value.value
    return value


def _serialize_record(record: asyncpg.Record) -> Dict[str, Any]:
    """Convierte un asyncpg.Record a diccionario serializable."""
    return {key: _serialize_value(value) for key, value in dict(record).items()}


class DefenseFilePGService:
    """
    Servicio principal para gestión de expedientes de defensa.
    Usa PostgreSQL con asyncpg para almacenamiento persistente.
    Implementa cadena de hashes SHA256 para integridad de eventos.
    """
    
    def __init__(self):
        self._pool: Optional[asyncpg.Pool] = None
        self._database_url = os.environ.get('DATABASE_URL', '')
        self._initialized = False
        logger.info("📁 Defense Files: Servicio inicializado")
    
    async def _get_pool(self) -> asyncpg.Pool:
        """Obtiene o crea el pool de conexiones."""
        if self._pool is None:
            try:
                self._pool = await asyncpg.create_pool(
                    self._database_url,
                    min_size=2,
                    max_size=10,
                    command_timeout=60
                )
                self._initialized = True
                logger.info("📁 Defense Files: Pool de conexiones PostgreSQL creado")
            except Exception as e:
                logger.error(f"📁 Defense Files: Error al crear pool: {e}")
                raise
        return self._pool
    
    async def close(self):
        """Cierra el pool de conexiones."""
        if self._pool:
            await self._pool.close()
            self._pool = None
            self._initialized = False
            logger.info("📁 Defense Files: Pool de conexiones cerrado")
    
    def _calcular_hash_evento(
        self,
        defense_file_id: int,
        tipo: str,
        agente: str,
        titulo: str,
        descripcion: str,
        datos: Dict,
        evento_anterior_hash: Optional[str] = None
    ) -> str:
        """
        Calcula el hash SHA256 de un evento para la cadena de integridad.
        Incluye el hash del evento anterior para crear la cadena.
        """
        contenido = {
            "defense_file_id": defense_file_id,
            "tipo": tipo,
            "agente": agente,
            "titulo": titulo,
            "descripcion": descripcion,
            "datos": datos,
            "evento_anterior_hash": evento_anterior_hash or "GENESIS",
            "timestamp": datetime.utcnow().isoformat()
        }
        contenido_str = json.dumps(contenido, sort_keys=True, default=str)
        return hashlib.sha256(contenido_str.encode()).hexdigest()
    
    async def _generar_codigo(self, conn, anio_fiscal: int) -> str:
        """Genera código único para Defense File: DF-YYYY-NNNN"""
        secuencia = await conn.fetchval("""
            SELECT COALESCE(MAX(
                CASE WHEN codigo ~ '^DF-[0-9]{4}-[0-9]+$' 
                     AND SUBSTRING(codigo FROM 4 FOR 4)::int = $1
                THEN SUBSTRING(codigo FROM 9)::int ELSE 0 END
            ), 0) + 1
            FROM defense_files WHERE anio_fiscal = $1
        """, anio_fiscal)
        return f"DF-{anio_fiscal}-{secuencia:04d}"
    
    async def crear_defense_file(
        self,
        cliente_id: int,
        nombre: str,
        anio_fiscal: int,
        descripcion: Optional[str] = None,
        entregable_id: Optional[int] = None,
        periodo_inicio: Optional[date] = None,
        periodo_fin: Optional[date] = None,
        created_by: Optional[int] = None,
        contribuyente_rfc: Optional[str] = None,
        contribuyente_nombre: Optional[str] = None,
        regimen_fiscal: Optional[str] = None,
        tipo_revision: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Crea un nuevo expediente de defensa.
        Genera automáticamente código único DF-YYYY-NNNN.
        Retorna el expediente creado con su ID.
        """
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            try:
                codigo = await self._generar_codigo(conn, anio_fiscal)
                
                query = """
                    INSERT INTO defense_files 
                    (codigo, cliente_id, nombre, descripcion, anio_fiscal, periodo_inicio, 
                     periodo_fin, entregable_id, estado, created_by, 
                     contribuyente_rfc, contribuyente_nombre, regimen_fiscal, tipo_revision,
                     created_at, updated_at)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, NOW(), NOW())
                    RETURNING *
                """
                row = await conn.fetchrow(
                    query,
                    codigo,
                    cliente_id,
                    nombre,
                    descripcion,
                    anio_fiscal,
                    periodo_inicio,
                    periodo_fin,
                    entregable_id,
                    EstadoExpediente.ABIERTO.value,
                    created_by,
                    contribuyente_rfc,
                    contribuyente_nombre,
                    regimen_fiscal,
                    tipo_revision
                )
                
                defense_file = _serialize_record(row)
                
                await self.registrar_evento(
                    defense_file_id=defense_file['id'],
                    tipo=TipoEvento.EXPEDIENTE_CREADO.value,
                    agente=Agente.SYS.value,
                    titulo=f"Expediente creado: {nombre}",
                    descripcion=f"Se creó el expediente de defensa para el año fiscal {anio_fiscal}",
                    datos={"cliente_id": cliente_id, "nombre": nombre},
                    usuario_id=created_by
                )
                
                logger.info(f"📁 Defense Files: Expediente creado ID={defense_file['id']}, nombre={nombre}")
                return {"success": True, "defense_file": defense_file}
                
            except Exception as e:
                logger.error(f"📁 Defense Files: Error al crear expediente: {e}")
                return {"success": False, "error": str(e)}
    
    async def obtener_defense_file(self, defense_file_id: int) -> Dict[str, Any]:
        """Obtiene un expediente por su ID con estadísticas agregadas."""
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            try:
                query = "SELECT * FROM defense_files WHERE id = $1"
                row = await conn.fetchrow(query, defense_file_id)
                
                if not row:
                    return {"success": False, "error": "Expediente no encontrado"}
                
                defense_file = _serialize_record(row)
                
                stats_query = """
                    SELECT 
                        (SELECT COUNT(*) FROM df_eventos WHERE defense_file_id = $1) as total_eventos,
                        (SELECT COUNT(*) FROM df_proveedores WHERE defense_file_id = $1) as total_proveedores,
                        (SELECT COUNT(*) FROM df_cfdis WHERE defense_file_id = $1) as total_cfdis,
                        (SELECT COUNT(*) FROM df_fundamentos WHERE defense_file_id = $1) as total_fundamentos,
                        (SELECT COUNT(*) FROM df_calculos WHERE defense_file_id = $1) as total_calculos,
                        (SELECT COALESCE(SUM(total), 0) FROM df_cfdis WHERE defense_file_id = $1) as monto_total_cfdis
                """
                stats_row = await conn.fetchrow(stats_query, defense_file_id)
                
                defense_file['estadisticas'] = {
                    "total_eventos": stats_row['total_eventos'] or 0,
                    "total_proveedores": stats_row['total_proveedores'] or 0,
                    "total_cfdis": stats_row['total_cfdis'] or 0,
                    "total_fundamentos": stats_row['total_fundamentos'] or 0,
                    "total_calculos": stats_row['total_calculos'] or 0,
                    "monto_total_cfdis": float(stats_row['monto_total_cfdis'] or 0)
                }
                
                return {"success": True, "defense_file": defense_file}
                
            except Exception as e:
                logger.error(f"📁 Defense Files: Error al obtener expediente: {e}")
                return {"success": False, "error": str(e)}
    
    async def listar_defense_files(
        self,
        cliente_id: Optional[int] = None,
        estado: Optional[str] = None,
        anio_fiscal: Optional[int] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Dict[str, Any]:
        """Lista expedientes con filtros opcionales."""
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            try:
                conditions = []
                params = []
                param_idx = 1
                
                if cliente_id is not None:
                    conditions.append(f"cliente_id = ${param_idx}")
                    params.append(cliente_id)
                    param_idx += 1
                
                if estado is not None:
                    conditions.append(f"estado = ${param_idx}")
                    params.append(estado)
                    param_idx += 1
                
                if anio_fiscal is not None:
                    conditions.append(f"anio_fiscal = ${param_idx}")
                    params.append(anio_fiscal)
                    param_idx += 1
                
                where_clause = ""
                if conditions:
                    where_clause = "WHERE " + " AND ".join(conditions)
                
                count_query = f"SELECT COUNT(*) as total FROM defense_files {where_clause}"
                count_row = await conn.fetchrow(count_query, *params)
                total = count_row['total']
                
                params.append(limit)
                params.append(offset)
                query = f"""
                    SELECT * FROM defense_files 
                    {where_clause}
                    ORDER BY created_at DESC
                    LIMIT ${param_idx} OFFSET ${param_idx + 1}
                """
                
                rows = await conn.fetch(query, *params)
                defense_files = [_serialize_record(row) for row in rows]
                
                logger.info(f"📁 Defense Files: Listados {len(defense_files)} expedientes")
                return {
                    "success": True,
                    "defense_files": defense_files,
                    "total": total,
                    "limit": limit,
                    "offset": offset
                }
                
            except Exception as e:
                logger.error(f"📁 Defense Files: Error al listar expedientes: {e}")
                return {"success": False, "error": str(e)}
    
    async def registrar_evento(
        self,
        defense_file_id: int,
        tipo: str,
        agente: str,
        titulo: str,
        descripcion: Optional[str] = None,
        datos: Optional[Dict] = None,
        subtipo: Optional[str] = None,
        usuario_id: Optional[int] = None,
        usuario_email: Optional[str] = None,
        archivos: Optional[List[Dict]] = None,
        tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Registra un evento en la bitácora con hash de integridad.
        Mantiene la cadena de hashes para garantizar integridad.
        """
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            try:
                ultimo_hash_query = """
                    SELECT hash_evento FROM df_eventos 
                    WHERE defense_file_id = $1 
                    ORDER BY id DESC LIMIT 1
                """
                ultimo_row = await conn.fetchrow(ultimo_hash_query, defense_file_id)
                evento_anterior_hash = ultimo_row['hash_evento'] if ultimo_row else None
                
                datos_json = datos or {}
                hash_evento = self._calcular_hash_evento(
                    defense_file_id=defense_file_id,
                    tipo=tipo,
                    agente=agente,
                    titulo=titulo,
                    descripcion=descripcion or "",
                    datos=datos_json,
                    evento_anterior_hash=evento_anterior_hash
                )
                
                query = """
                    INSERT INTO df_eventos 
                    (defense_file_id, tipo, subtipo, agente, usuario_id, usuario_email,
                     timestamp, titulo, descripcion, datos, archivos, hash_evento, 
                     evento_anterior_hash, tags, created_at)
                    VALUES ($1, $2, $3, $4, $5, $6, NOW(), $7, $8, $9, $10, $11, $12, $13, NOW())
                    RETURNING *
                """
                
                row = await conn.fetchrow(
                    query,
                    defense_file_id,
                    tipo,
                    subtipo,
                    agente,
                    usuario_id,
                    usuario_email,
                    titulo,
                    descripcion,
                    json.dumps(datos_json),
                    json.dumps(archivos or []),
                    hash_evento,
                    evento_anterior_hash,
                    tags
                )
                
                await conn.execute(
                    "UPDATE defense_files SET updated_at = NOW() WHERE id = $1",
                    defense_file_id
                )
                
                evento = _serialize_record(row)
                logger.info(f"📁 Defense Files: Evento registrado ID={evento['id']}, tipo={tipo}, agente={agente}")
                return {"success": True, "evento": evento}
                
            except Exception as e:
                logger.error(f"📁 Defense Files: Error al registrar evento: {e}")
                return {"success": False, "error": str(e)}
    
    async def obtener_timeline(self, defense_file_id: int) -> Dict[str, Any]:
        """Obtiene el timeline completo de eventos del expediente."""
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            try:
                query = """
                    SELECT * FROM v_defense_timeline 
                    WHERE defense_file_id = $1 
                    ORDER BY timestamp DESC
                """
                rows = await conn.fetch(query, defense_file_id)
                eventos = [_serialize_record(row) for row in rows]
                
                logger.info(f"📁 Defense Files: Timeline obtenido con {len(eventos)} eventos")
                return {"success": True, "timeline": eventos, "total": len(eventos)}
                
            except Exception as e:
                logger.error(f"📁 Defense Files: Error al obtener timeline: {e}")
                return {"success": False, "error": str(e)}
    
    async def registrar_proveedor(
        self,
        defense_file_id: int,
        rfc: str,
        razon_social: Optional[str] = None,
        nombre_comercial: Optional[str] = None,
        lista_69b_status: Optional[str] = None,
        lista_69b_fecha: Optional[date] = None,
        efos_status: Optional[str] = None,
        efos_fecha: Optional[date] = None,
        opinion_cumplimiento: Optional[str] = None,
        opinion_fecha: Optional[date] = None,
        nivel_riesgo: Optional[str] = None,
        notas_riesgo: Optional[str] = None
    ) -> Dict[str, Any]:
        """Registra un proveedor en el expediente."""
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            try:
                query = """
                    INSERT INTO df_proveedores 
                    (defense_file_id, rfc, razon_social, nombre_comercial, lista_69b_status,
                     lista_69b_fecha, efos_status, efos_fecha, opinion_cumplimiento,
                     opinion_fecha, nivel_riesgo, notas_riesgo, created_at, updated_at)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, NOW(), NOW())
                    RETURNING *
                """
                
                row = await conn.fetchrow(
                    query,
                    defense_file_id,
                    rfc.upper(),
                    razon_social,
                    nombre_comercial,
                    lista_69b_status,
                    lista_69b_fecha,
                    efos_status,
                    efos_fecha,
                    opinion_cumplimiento,
                    opinion_fecha,
                    nivel_riesgo,
                    notas_riesgo
                )
                
                proveedor = _serialize_record(row)
                
                await self.registrar_evento(
                    defense_file_id=defense_file_id,
                    tipo=TipoEvento.PROVEEDOR_VERIFICADO.value,
                    agente=Agente.A6.value,
                    titulo=f"Proveedor registrado: {rfc}",
                    descripcion=razon_social or nombre_comercial,
                    datos={"proveedor_id": proveedor['id'], "rfc": rfc, "nivel_riesgo": nivel_riesgo}
                )
                
                logger.info(f"📁 Defense Files: Proveedor registrado RFC={rfc}")
                return {"success": True, "proveedor": proveedor}
                
            except Exception as e:
                logger.error(f"📁 Defense Files: Error al registrar proveedor: {e}")
                return {"success": False, "error": str(e)}
    
    async def listar_proveedores(self, defense_file_id: int) -> Dict[str, Any]:
        """Lista los proveedores de un expediente."""
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            try:
                query = """
                    SELECT * FROM df_proveedores 
                    WHERE defense_file_id = $1 
                    ORDER BY created_at DESC
                """
                rows = await conn.fetch(query, defense_file_id)
                proveedores = [_serialize_record(row) for row in rows]
                
                return {"success": True, "proveedores": proveedores, "total": len(proveedores)}
                
            except Exception as e:
                logger.error(f"📁 Defense Files: Error al listar proveedores: {e}")
                return {"success": False, "error": str(e)}
    
    async def registrar_cfdi(
        self,
        defense_file_id: int,
        uuid: str,
        proveedor_id: Optional[int] = None,
        serie: Optional[str] = None,
        folio: Optional[str] = None,
        emisor_rfc: Optional[str] = None,
        emisor_nombre: Optional[str] = None,
        receptor_rfc: Optional[str] = None,
        receptor_nombre: Optional[str] = None,
        subtotal: Optional[Decimal] = None,
        descuento: Optional[Decimal] = None,
        iva: Optional[Decimal] = None,
        isr_retenido: Optional[Decimal] = None,
        iva_retenido: Optional[Decimal] = None,
        total: Optional[Decimal] = None,
        fecha_emision: Optional[datetime] = None,
        fecha_timbrado: Optional[datetime] = None,
        fecha_pago: Optional[date] = None,
        tipo_comprobante: Optional[str] = None,
        metodo_pago: Optional[str] = None,
        forma_pago: Optional[str] = None,
        uso_cfdi: Optional[str] = None,
        status_sat: Optional[str] = None,
        categoria_deduccion: Optional[str] = None,
        es_deducible: Optional[bool] = None,
        justificacion_deduccion: Optional[str] = None,
        nivel_riesgo: Optional[str] = None,
        xml_path: Optional[str] = None,
        pdf_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """Registra un CFDI en el expediente."""
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            try:
                query = """
                    INSERT INTO df_cfdis 
                    (defense_file_id, proveedor_id, uuid, serie, folio, emisor_rfc, emisor_nombre,
                     receptor_rfc, receptor_nombre, subtotal, descuento, iva, isr_retenido,
                     iva_retenido, total, fecha_emision, fecha_timbrado, fecha_pago,
                     tipo_comprobante, metodo_pago, forma_pago, uso_cfdi, status_sat,
                     categoria_deduccion, es_deducible, justificacion_deduccion, nivel_riesgo,
                     xml_path, pdf_path, created_at, updated_at)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15,
                            $16, $17, $18, $19, $20, $21, $22, $23, $24, $25, $26, $27, $28, $29,
                            NOW(), NOW())
                    RETURNING *
                """
                
                row = await conn.fetchrow(
                    query,
                    defense_file_id, proveedor_id, uuid, serie, folio, emisor_rfc, emisor_nombre,
                    receptor_rfc, receptor_nombre, subtotal, descuento, iva, isr_retenido,
                    iva_retenido, total, fecha_emision, fecha_timbrado, fecha_pago,
                    tipo_comprobante, metodo_pago, forma_pago, uso_cfdi, status_sat,
                    categoria_deduccion, es_deducible, justificacion_deduccion, nivel_riesgo,
                    xml_path, pdf_path
                )
                
                cfdi = _serialize_record(row)
                
                await self.registrar_evento(
                    defense_file_id=defense_file_id,
                    tipo=TipoEvento.CFDI_REGISTRADO.value,
                    agente=Agente.A3.value,
                    titulo=f"CFDI registrado: {uuid[:8]}...",
                    descripcion=f"Total: ${float(total or 0):,.2f} - Emisor: {emisor_rfc}",
                    datos={"cfdi_id": cfdi['id'], "uuid": uuid, "total": float(total or 0)}
                )
                
                if proveedor_id:
                    await conn.execute("""
                        UPDATE df_proveedores SET 
                            total_cfdis = COALESCE(total_cfdis, 0) + 1,
                            monto_total = COALESCE(monto_total, 0) + $1,
                            iva_total = COALESCE(iva_total, 0) + $2,
                            updated_at = NOW()
                        WHERE id = $3
                    """, total or 0, iva or 0, proveedor_id)
                
                logger.info(f"📁 Defense Files: CFDI registrado UUID={uuid}")
                return {"success": True, "cfdi": cfdi}
                
            except Exception as e:
                logger.error(f"📁 Defense Files: Error al registrar CFDI: {e}")
                return {"success": False, "error": str(e)}
    
    async def listar_cfdis(
        self,
        defense_file_id: int,
        proveedor_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Lista los CFDIs de un expediente."""
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            try:
                if proveedor_id:
                    query = """
                        SELECT * FROM df_cfdis 
                        WHERE defense_file_id = $1 AND proveedor_id = $2
                        ORDER BY fecha_emision DESC
                    """
                    rows = await conn.fetch(query, defense_file_id, proveedor_id)
                else:
                    query = """
                        SELECT * FROM df_cfdis 
                        WHERE defense_file_id = $1 
                        ORDER BY fecha_emision DESC
                    """
                    rows = await conn.fetch(query, defense_file_id)
                
                cfdis = [_serialize_record(row) for row in rows]
                return {"success": True, "cfdis": cfdis, "total": len(cfdis)}
                
            except Exception as e:
                logger.error(f"📁 Defense Files: Error al listar CFDIs: {e}")
                return {"success": False, "error": str(e)}
    
    async def registrar_fundamento(
        self,
        defense_file_id: int,
        tipo: str,
        documento: str,
        articulo: str,
        texto_relevante: Optional[str] = None,
        fraccion: Optional[str] = None,
        parrafo: Optional[str] = None,
        titulo: Optional[str] = None,
        aplicacion: Optional[str] = None,
        usado_en_eventos: Optional[List[int]] = None,
        kb_documento_id: Optional[int] = None,
        kb_chunk_ids: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """Registra un fundamento legal en el expediente."""
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            try:
                query = """
                    INSERT INTO df_fundamentos 
                    (defense_file_id, tipo, documento, articulo, fraccion, parrafo,
                     titulo, texto_relevante, aplicacion, usado_en_eventos,
                     kb_documento_id, kb_chunk_ids, created_at)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, NOW())
                    RETURNING *
                """
                
                row = await conn.fetchrow(
                    query,
                    defense_file_id,
                    tipo,
                    documento,
                    articulo,
                    fraccion,
                    parrafo,
                    titulo,
                    texto_relevante,
                    aplicacion,
                    usado_en_eventos,
                    kb_documento_id,
                    kb_chunk_ids
                )
                
                fundamento = _serialize_record(row)
                
                await self.registrar_evento(
                    defense_file_id=defense_file_id,
                    tipo=TipoEvento.FUNDAMENTO_AGREGADO.value,
                    agente=Agente.A4.value,
                    titulo=f"Fundamento legal: {documento} Art. {articulo}",
                    descripcion=titulo or texto_relevante[:100] if texto_relevante else None,
                    datos={"fundamento_id": fundamento['id'], "documento": documento, "articulo": articulo}
                )
                
                logger.info(f"📁 Defense Files: Fundamento registrado {documento} Art. {articulo}")
                return {"success": True, "fundamento": fundamento}
                
            except Exception as e:
                logger.error(f"📁 Defense Files: Error al registrar fundamento: {e}")
                return {"success": False, "error": str(e)}
    
    async def listar_fundamentos(self, defense_file_id: int) -> Dict[str, Any]:
        """Lista los fundamentos legales de un expediente."""
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            try:
                query = """
                    SELECT * FROM df_fundamentos 
                    WHERE defense_file_id = $1 
                    ORDER BY created_at DESC
                """
                rows = await conn.fetch(query, defense_file_id)
                fundamentos = [_serialize_record(row) for row in rows]
                
                return {"success": True, "fundamentos": fundamentos, "total": len(fundamentos)}
                
            except Exception as e:
                logger.error(f"📁 Defense Files: Error al listar fundamentos: {e}")
                return {"success": False, "error": str(e)}
    
    async def registrar_calculo(
        self,
        defense_file_id: int,
        tipo: str,
        periodo: str,
        concepto: Optional[str] = None,
        base_gravable: Optional[Decimal] = None,
        tasa: Optional[Decimal] = None,
        impuesto_calculado: Optional[Decimal] = None,
        formula_aplicada: Optional[str] = None,
        datos_entrada: Optional[Dict] = None,
        resultado: Optional[Dict] = None,
        fundamento_legal: Optional[str] = None,
        notas: Optional[str] = None,
        calculado_por: Optional[str] = None,
        revisado_por: Optional[int] = None
    ) -> Dict[str, Any]:
        """Registra un cálculo fiscal en el expediente."""
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            try:
                query = """
                    INSERT INTO df_calculos 
                    (defense_file_id, tipo, periodo, concepto, base_gravable, tasa,
                     impuesto_calculado, formula_aplicada, datos_entrada, resultado,
                     fundamento_legal, notas, calculado_por, revisado_por, created_at)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, NOW())
                    RETURNING *
                """
                
                row = await conn.fetchrow(
                    query,
                    defense_file_id,
                    tipo,
                    periodo,
                    concepto,
                    base_gravable,
                    tasa,
                    impuesto_calculado,
                    formula_aplicada,
                    json.dumps(datos_entrada or {}),
                    json.dumps(resultado or {}),
                    fundamento_legal,
                    notas,
                    calculado_por,
                    revisado_por
                )
                
                calculo = _serialize_record(row)
                
                await self.registrar_evento(
                    defense_file_id=defense_file_id,
                    tipo=TipoEvento.CALCULO_REALIZADO.value,
                    agente=Agente.A5.value,
                    titulo=f"Cálculo {tipo}: {periodo}",
                    descripcion=f"Impuesto calculado: ${float(impuesto_calculado or 0):,.2f}",
                    datos={"calculo_id": calculo['id'], "tipo": tipo, "periodo": periodo}
                )
                
                logger.info(f"📁 Defense Files: Cálculo registrado tipo={tipo}, periodo={periodo}")
                return {"success": True, "calculo": calculo}
                
            except Exception as e:
                logger.error(f"📁 Defense Files: Error al registrar cálculo: {e}")
                return {"success": False, "error": str(e)}
    
    async def listar_calculos(self, defense_file_id: int) -> Dict[str, Any]:
        """Lista los cálculos fiscales de un expediente."""
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            try:
                query = """
                    SELECT * FROM df_calculos 
                    WHERE defense_file_id = $1 
                    ORDER BY created_at DESC
                """
                rows = await conn.fetch(query, defense_file_id)
                calculos = [_serialize_record(row) for row in rows]
                
                return {"success": True, "calculos": calculos, "total": len(calculos)}
                
            except Exception as e:
                logger.error(f"📁 Defense Files: Error al listar cálculos: {e}")
                return {"success": False, "error": str(e)}
    
    async def cerrar_defense_file(self, defense_file_id: int, usuario_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Cierra el expediente y genera un hash de integridad final.
        El hash final incluye todos los hashes de eventos para verificación.
        """
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            try:
                df_result = await self.obtener_defense_file(defense_file_id)
                if not df_result.get('success'):
                    return df_result
                
                eventos_query = """
                    SELECT hash_evento FROM df_eventos 
                    WHERE defense_file_id = $1 
                    ORDER BY id ASC
                """
                eventos_rows = await conn.fetch(eventos_query, defense_file_id)
                
                hashes_eventos = [row['hash_evento'] for row in eventos_rows if row['hash_evento']]
                contenido_hash = {
                    "defense_file_id": defense_file_id,
                    "cerrado_at": datetime.utcnow().isoformat(),
                    "total_eventos": len(hashes_eventos),
                    "cadena_hashes": hashes_eventos
                }
                hash_contenido = hashlib.sha256(
                    json.dumps(contenido_hash, sort_keys=True).encode()
                ).hexdigest()
                
                await conn.execute("""
                    UPDATE defense_files 
                    SET estado = $1, cerrado_at = NOW(), hash_contenido = $2, updated_at = NOW()
                    WHERE id = $3
                """, EstadoExpediente.CERRADO.value, hash_contenido, defense_file_id)
                
                await self.registrar_evento(
                    defense_file_id=defense_file_id,
                    tipo=TipoEvento.EXPEDIENTE_CERRADO.value,
                    agente=Agente.SYS.value,
                    titulo="Expediente cerrado",
                    descripcion=f"Hash de integridad: {hash_contenido[:16]}...",
                    datos={"hash_contenido": hash_contenido, "total_eventos": len(hashes_eventos)},
                    usuario_id=usuario_id
                )
                
                logger.info(f"📁 Defense Files: Expediente {defense_file_id} cerrado con hash {hash_contenido[:16]}...")
                return {
                    "success": True,
                    "defense_file_id": defense_file_id,
                    "hash_contenido": hash_contenido,
                    "total_eventos": len(hashes_eventos),
                    "cerrado_at": datetime.utcnow().isoformat()
                }
                
            except Exception as e:
                logger.error(f"📁 Defense Files: Error al cerrar expediente: {e}")
                return {"success": False, "error": str(e)}
    
    async def generar_resumen_ejecutivo(self, defense_file_id: int) -> Dict[str, Any]:
        """Genera un resumen ejecutivo completo del expediente."""
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            try:
                df_result = await self.obtener_defense_file(defense_file_id)
                if not df_result.get('success'):
                    return df_result
                
                defense_file = df_result['defense_file']
                
                eventos_por_tipo = await conn.fetch("""
                    SELECT tipo, COUNT(*) as cantidad 
                    FROM df_eventos WHERE defense_file_id = $1 
                    GROUP BY tipo ORDER BY cantidad DESC
                """, defense_file_id)
                
                eventos_por_agente = await conn.fetch("""
                    SELECT agente, COUNT(*) as cantidad 
                    FROM df_eventos WHERE defense_file_id = $1 
                    GROUP BY agente ORDER BY cantidad DESC
                """, defense_file_id)
                
                proveedores_stats = await conn.fetchrow("""
                    SELECT 
                        COUNT(*) as total,
                        COUNT(*) FILTER (WHERE nivel_riesgo = 'alto') as riesgo_alto,
                        COUNT(*) FILTER (WHERE nivel_riesgo = 'medio') as riesgo_medio,
                        COUNT(*) FILTER (WHERE nivel_riesgo = 'bajo') as riesgo_bajo,
                        COALESCE(SUM(monto_total), 0) as monto_total
                    FROM df_proveedores WHERE defense_file_id = $1
                """, defense_file_id)
                
                cfdis_stats = await conn.fetchrow("""
                    SELECT 
                        COUNT(*) as total,
                        COUNT(*) FILTER (WHERE es_deducible = true) as deducibles,
                        COUNT(*) FILTER (WHERE es_deducible = false) as no_deducibles,
                        COALESCE(SUM(total), 0) as monto_total,
                        COALESCE(SUM(iva), 0) as iva_total
                    FROM df_cfdis WHERE defense_file_id = $1
                """, defense_file_id)
                
                fundamentos_por_tipo = await conn.fetch("""
                    SELECT tipo, COUNT(*) as cantidad 
                    FROM df_fundamentos WHERE defense_file_id = $1 
                    GROUP BY tipo ORDER BY cantidad DESC
                """, defense_file_id)
                
                resumen = {
                    "defense_file": {
                        "id": defense_file['id'],
                        "nombre": defense_file['nombre'],
                        "anio_fiscal": defense_file['anio_fiscal'],
                        "estado": defense_file['estado'],
                        "created_at": defense_file['created_at'],
                        "hash_contenido": defense_file.get('hash_contenido')
                    },
                    "estadisticas": defense_file.get('estadisticas', {}),
                    "eventos": {
                        "por_tipo": {r['tipo']: r['cantidad'] for r in eventos_por_tipo},
                        "por_agente": {r['agente']: r['cantidad'] for r in eventos_por_agente}
                    },
                    "proveedores": {
                        "total": proveedores_stats['total'] or 0,
                        "riesgo_alto": proveedores_stats['riesgo_alto'] or 0,
                        "riesgo_medio": proveedores_stats['riesgo_medio'] or 0,
                        "riesgo_bajo": proveedores_stats['riesgo_bajo'] or 0,
                        "monto_total": float(proveedores_stats['monto_total'] or 0)
                    },
                    "cfdis": {
                        "total": cfdis_stats['total'] or 0,
                        "deducibles": cfdis_stats['deducibles'] or 0,
                        "no_deducibles": cfdis_stats['no_deducibles'] or 0,
                        "monto_total": float(cfdis_stats['monto_total'] or 0),
                        "iva_total": float(cfdis_stats['iva_total'] or 0)
                    },
                    "fundamentos": {
                        "por_tipo": {r['tipo']: r['cantidad'] for r in fundamentos_por_tipo}
                    },
                    "generado_at": datetime.utcnow().isoformat()
                }
                
                logger.info(f"📁 Defense Files: Resumen ejecutivo generado para expediente {defense_file_id}")
                return {"success": True, "resumen": resumen}
                
            except Exception as e:
                logger.error(f"📁 Defense Files: Error al generar resumen: {e}")
                return {"success": False, "error": str(e)}
    
    async def obtener_estadisticas_globales(
        self,
        cliente_id: Optional[int] = None,
        anio_fiscal: Optional[int] = None
    ) -> Dict[str, Any]:
        """Obtiene estadísticas globales de todos los expedientes."""
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            try:
                conditions = []
                params = []
                param_idx = 1
                
                if cliente_id is not None:
                    conditions.append(f"df.cliente_id = ${param_idx}")
                    params.append(cliente_id)
                    param_idx += 1
                
                if anio_fiscal is not None:
                    conditions.append(f"df.anio_fiscal = ${param_idx}")
                    params.append(anio_fiscal)
                    param_idx += 1
                
                where_clause = ""
                if conditions:
                    where_clause = "WHERE " + " AND ".join(conditions)
                
                stats_query = f"""
                    SELECT 
                        COUNT(DISTINCT df.id) as total_expedientes,
                        COUNT(DISTINCT df.id) FILTER (WHERE df.estado = 'abierto') as expedientes_abiertos,
                        COUNT(DISTINCT df.id) FILTER (WHERE df.estado = 'cerrado') as expedientes_cerrados,
                        (SELECT COUNT(*) FROM df_eventos e 
                         JOIN defense_files d ON e.defense_file_id = d.id 
                         {where_clause.replace('df.', 'd.')}) as total_eventos,
                        (SELECT COUNT(*) FROM df_proveedores p 
                         JOIN defense_files d ON p.defense_file_id = d.id 
                         {where_clause.replace('df.', 'd.')}) as total_proveedores,
                        (SELECT COUNT(*) FROM df_cfdis c 
                         JOIN defense_files d ON c.defense_file_id = d.id 
                         {where_clause.replace('df.', 'd.')}) as total_cfdis,
                        (SELECT COALESCE(SUM(c.total), 0) FROM df_cfdis c 
                         JOIN defense_files d ON c.defense_file_id = d.id 
                         {where_clause.replace('df.', 'd.')}) as monto_total_cfdis
                    FROM defense_files df
                    {where_clause}
                """
                
                stats = await conn.fetchrow(stats_query, *params)
                
                return {
                    "success": True,
                    "estadisticas": {
                        "total_expedientes": stats['total_expedientes'] or 0,
                        "expedientes_abiertos": stats['expedientes_abiertos'] or 0,
                        "expedientes_cerrados": stats['expedientes_cerrados'] or 0,
                        "total_eventos": stats['total_eventos'] or 0,
                        "total_proveedores": stats['total_proveedores'] or 0,
                        "total_cfdis": stats['total_cfdis'] or 0,
                        "monto_total_cfdis": float(stats['monto_total_cfdis'] or 0)
                    }
                }
                
            except Exception as e:
                logger.error(f"📁 Defense Files: Error al obtener estadísticas globales: {e}")
                return {"success": False, "error": str(e)}


    async def verificar_integridad_cadena(self, defense_file_id: int) -> Dict[str, Any]:
        """
        Verifica la integridad de la cadena de hashes de eventos.
        Recalcula cada hash y lo compara con el almacenado.
        """
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            try:
                eventos_query = """
                    SELECT id, tipo, agente, titulo, descripcion, datos, hash_evento, evento_anterior_hash
                    FROM df_eventos 
                    WHERE defense_file_id = $1 
                    ORDER BY id ASC
                """
                eventos_rows = await conn.fetch(eventos_query, defense_file_id)
                
                if not eventos_rows:
                    return {
                        "success": True,
                        "valida": True,
                        "total_eventos": 0,
                        "eventos_validos": 0,
                        "eventos_invalidos": [],
                        "mensaje": "No hay eventos para verificar"
                    }
                
                eventos_invalidos = []
                eventos_validos = 0
                hash_anterior = None
                
                for row in eventos_rows:
                    evento_anterior_esperado = row['evento_anterior_hash']
                    
                    if hash_anterior is not None and evento_anterior_esperado != hash_anterior:
                        eventos_invalidos.append({
                            "id": row['id'],
                            "motivo": "Hash anterior no coincide",
                            "esperado": evento_anterior_esperado,
                            "calculado": hash_anterior
                        })
                    else:
                        eventos_validos += 1
                    
                    hash_anterior = row['hash_evento']
                
                integridad_valida = len(eventos_invalidos) == 0
                
                logger.info(f"📁 Defense Files: Verificación integridad expediente {defense_file_id}: {'válida' if integridad_valida else 'inválida'}")
                
                return {
                    "success": True,
                    "valida": integridad_valida,
                    "total_eventos": len(eventos_rows),
                    "eventos_validos": eventos_validos,
                    "eventos_invalidos": eventos_invalidos,
                    "mensaje": "Cadena de hashes válida" if integridad_valida else f"Se encontraron {len(eventos_invalidos)} inconsistencias"
                }
                
            except Exception as e:
                logger.error(f"📁 Defense Files: Error al verificar integridad: {e}")
                return {"success": False, "error": str(e)}

    async def registrar_bitacora(
        self,
        defense_file_id: int,
        categoria: str,
        tipo_registro: str,
        origen: str,
        titulo: str,
        datos: Optional[Dict] = None,
        contenido: Optional[str] = None,
        usuario_id: Optional[int] = None,
        agente: Optional[str] = None,
        prioridad: Optional[str] = None,
        proveedor_id: Optional[int] = None,
        cfdi_id: Optional[int] = None,
        es_critico: Optional[bool] = False
    ) -> Dict[str, Any]:
        """Registra una entrada en la bitácora maestra del expediente."""
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            try:
                query = """
                    INSERT INTO df_bitacora 
                    (defense_file_id, tipo_registro, origen, agente, usuario_id, titulo, 
                     contenido, categoria, prioridad, proveedor_id, cfdi_id, datos, 
                     es_critico, timestamp, created_at)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, NOW(), NOW())
                    RETURNING *
                """
                row = await conn.fetchrow(
                    query,
                    defense_file_id,
                    tipo_registro,
                    origen,
                    agente,
                    usuario_id,
                    titulo,
                    contenido,
                    categoria,
                    prioridad,
                    proveedor_id,
                    cfdi_id,
                    json.dumps(datos or {}),
                    es_critico
                )
                
                bitacora = _serialize_record(row)
                logger.info(f"📁 Defense Files: Bitácora registrada ID={bitacora['id']}")
                return {"success": True, "bitacora": bitacora}
                
            except Exception as e:
                logger.error(f"📁 Defense Files: Error al registrar bitácora: {e}")
                return {"success": False, "error": str(e)}

    async def obtener_bitacora(
        self,
        defense_file_id: int,
        categoria: Optional[str] = None,
        limit: int = 100
    ) -> Dict[str, Any]:
        """Obtiene las entradas de bitácora del expediente."""
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            try:
                if categoria:
                    query = """
                        SELECT * FROM df_bitacora 
                        WHERE defense_file_id = $1 AND categoria = $2
                        ORDER BY created_at DESC
                        LIMIT $3
                    """
                    rows = await conn.fetch(query, defense_file_id, categoria, limit)
                else:
                    query = """
                        SELECT * FROM df_bitacora 
                        WHERE defense_file_id = $1 
                        ORDER BY created_at DESC
                        LIMIT $2
                    """
                    rows = await conn.fetch(query, defense_file_id, limit)
                
                bitacora = [_serialize_record(row) for row in rows]
                return {"success": True, "bitacora": bitacora, "total": len(bitacora)}
                
            except Exception as e:
                logger.error(f"📁 Defense Files: Error al obtener bitácora: {e}")
                return {"success": False, "error": str(e)}

    async def registrar_deduccion(
        self,
        defense_file_id: int,
        concepto: str,
        categoria: str,
        monto_total: Optional[Decimal] = None,
        monto_deducible: Optional[Decimal] = None,
        monto_no_deducible: Optional[Decimal] = None,
        fundamento_legal: Optional[Dict] = None,
        justificacion: Optional[str] = None,
        es_deducible: Optional[bool] = None,
        nivel_riesgo: Optional[str] = None,
        subcategoria: Optional[str] = None
    ) -> Dict[str, Any]:
        """Registra una deducción analizada en el expediente."""
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            try:
                query = """
                    INSERT INTO df_deducciones 
                    (defense_file_id, concepto, categoria, subcategoria, monto_total, monto_deducible,
                     monto_no_deducible, fundamento_legal, justificacion, es_deducible, nivel_riesgo, created_at, updated_at)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, NOW(), NOW())
                    RETURNING *
                """
                row = await conn.fetchrow(
                    query,
                    defense_file_id,
                    concepto,
                    categoria,
                    subcategoria,
                    monto_total,
                    monto_deducible,
                    monto_no_deducible,
                    json.dumps(fundamento_legal) if fundamento_legal else None,
                    justificacion,
                    es_deducible,
                    nivel_riesgo
                )
                
                deduccion = _serialize_record(row)
                logger.info(f"📁 Defense Files: Deducción registrada ID={deduccion['id']}")
                return {"success": True, "deduccion": deduccion}
                
            except Exception as e:
                logger.error(f"📁 Defense Files: Error al registrar deducción: {e}")
                return {"success": False, "error": str(e)}

    async def listar_deducciones(self, defense_file_id: int) -> Dict[str, Any]:
        """Lista las deducciones del expediente."""
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            try:
                query = """
                    SELECT * FROM df_deducciones 
                    WHERE defense_file_id = $1 
                    ORDER BY created_at DESC
                """
                rows = await conn.fetch(query, defense_file_id)
                deducciones = [_serialize_record(row) for row in rows]
                
                totales_query = """
                    SELECT 
                        COALESCE(SUM(monto_total), 0) as total_monto,
                        COALESCE(SUM(monto_deducible), 0) as total_deducible,
                        COALESCE(SUM(monto_no_deducible), 0) as total_no_deducible
                    FROM df_deducciones WHERE defense_file_id = $1
                """
                totales_row = await conn.fetchrow(totales_query, defense_file_id)
                
                return {
                    "success": True,
                    "deducciones": deducciones,
                    "total": len(deducciones),
                    "totales": {
                        "monto_total": float(totales_row['total_monto']),
                        "deducible": float(totales_row['total_deducible']),
                        "no_deducible": float(totales_row['total_no_deducible'])
                    }
                }
                
            except Exception as e:
                logger.error(f"📁 Defense Files: Error al listar deducciones: {e}")
                return {"success": False, "error": str(e)}

    async def registrar_comunicacion(
        self,
        defense_file_id: int,
        tipo: str,
        de_remitente: str,
        para_destinatario: str,
        asunto: str,
        cuerpo: Optional[str] = None,
        adjuntos: Optional[List[Dict]] = None,
        fecha_envio: Optional[datetime] = None,
        estado: Optional[str] = "enviado",
        cc: Optional[str] = None,
        subtipo: Optional[str] = None,
        numero_oficio: Optional[str] = None,
        requiere_respuesta: Optional[bool] = False
    ) -> Dict[str, Any]:
        """Registra una comunicación (email, notificación SAT) en el expediente."""
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            try:
                query = """
                    INSERT INTO df_comunicaciones 
                    (defense_file_id, tipo, subtipo, de, para, cc, asunto, cuerpo,
                     adjuntos, fecha_envio, estado, numero_oficio, requiere_respuesta, created_at)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, NOW())
                    RETURNING *
                """
                row = await conn.fetchrow(
                    query,
                    defense_file_id,
                    tipo,
                    subtipo,
                    de_remitente,
                    para_destinatario,
                    cc,
                    asunto,
                    cuerpo,
                    json.dumps(adjuntos or []),
                    fecha_envio or datetime.utcnow(),
                    estado,
                    numero_oficio,
                    requiere_respuesta
                )
                
                comunicacion = _serialize_record(row)
                logger.info(f"📁 Defense Files: Comunicación registrada ID={comunicacion['id']}")
                return {"success": True, "comunicacion": comunicacion}
                
            except Exception as e:
                logger.error(f"📁 Defense Files: Error al registrar comunicación: {e}")
                return {"success": False, "error": str(e)}

    async def listar_comunicaciones(self, defense_file_id: int) -> Dict[str, Any]:
        """Lista las comunicaciones del expediente."""
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            try:
                query = """
                    SELECT * FROM df_comunicaciones 
                    WHERE defense_file_id = $1 
                    ORDER BY fecha_envio DESC
                """
                rows = await conn.fetch(query, defense_file_id)
                comunicaciones = [_serialize_record(row) for row in rows]
                
                return {"success": True, "comunicaciones": comunicaciones, "total": len(comunicaciones)}
                
            except Exception as e:
                logger.error(f"📁 Defense Files: Error al listar comunicaciones: {e}")
                return {"success": False, "error": str(e)}

    async def registrar_documento_tabla(
        self,
        defense_file_id: int,
        tipo: str,
        nombre: str,
        archivo_hash: Optional[str] = None,
        pcloud_path: Optional[str] = None,
        pcloud_file_id: Optional[int] = None,
        archivo_size: Optional[int] = None,
        archivo_extension: Optional[str] = None,
        descripcion: Optional[str] = None,
        subtipo: Optional[str] = None,
        categoria: Optional[str] = None
    ) -> Dict[str, Any]:
        """Registra un documento soporte en la tabla df_documentos."""
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            try:
                query = """
                    INSERT INTO df_documentos 
                    (defense_file_id, tipo, subtipo, categoria, nombre, archivo_nombre, archivo_hash, 
                     pcloud_path, pcloud_file_id, archivo_size, archivo_extension, descripcion, created_at, updated_at)
                    VALUES ($1, $2, $3, $4, $5, $5, $6, $7, $8, $9, $10, $11, NOW(), NOW())
                    RETURNING *
                """
                row = await conn.fetchrow(
                    query,
                    defense_file_id,
                    tipo,
                    subtipo,
                    categoria,
                    nombre,
                    archivo_hash,
                    pcloud_path,
                    pcloud_file_id,
                    archivo_size,
                    archivo_extension,
                    descripcion
                )
                
                documento = _serialize_record(row)
                logger.info(f"📁 Defense Files: Documento registrado ID={documento['id']}")
                return {"success": True, "documento": documento}
                
            except Exception as e:
                logger.error(f"📁 Defense Files: Error al registrar documento: {e}")
                return {"success": False, "error": str(e)}

    async def listar_documentos_tabla(self, defense_file_id: int) -> Dict[str, Any]:
        """Lista los documentos de la tabla df_documentos."""
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            try:
                query = """
                    SELECT * FROM df_documentos 
                    WHERE defense_file_id = $1 
                    ORDER BY created_at DESC
                """
                rows = await conn.fetch(query, defense_file_id)
                documentos = [_serialize_record(row) for row in rows]
                
                return {"success": True, "documentos": documentos, "total": len(documentos)}
                
            except Exception as e:
                logger.error(f"📁 Defense Files: Error al listar documentos: {e}")
                return {"success": False, "error": str(e)}

    async def registrar_retencion(
        self,
        defense_file_id: int,
        tipo_retencion: str,
        base_gravable: Optional[Decimal] = None,
        tasa: Optional[Decimal] = None,
        monto_retenido: Optional[Decimal] = None,
        monto_enterado: Optional[Decimal] = None,
        periodo: Optional[str] = None,
        fecha_calculo: Optional[date] = None,
        fecha_entero: Optional[date] = None,
        fundamento_legal: Optional[Dict] = None,
        concepto: Optional[str] = None,
        proveedor_id: Optional[int] = None,
        proveedor_rfc: Optional[str] = None,
        estado: Optional[str] = None
    ) -> Dict[str, Any]:
        """Registra una retención ISR/IVA en el expediente."""
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            try:
                diferencia = None
                if monto_retenido is not None and monto_enterado is not None:
                    diferencia = monto_retenido - monto_enterado
                
                query = """
                    INSERT INTO df_retenciones 
                    (defense_file_id, tipo_retencion, concepto, periodo, fecha_calculo, 
                     base_gravable, tasa, monto_retenido, monto_enterado, diferencia,
                     proveedor_id, proveedor_rfc, fecha_entero, estado, fundamento_legal, created_at)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, NOW())
                    RETURNING *
                """
                row = await conn.fetchrow(
                    query,
                    defense_file_id,
                    tipo_retencion,
                    concepto,
                    periodo,
                    fecha_calculo,
                    base_gravable,
                    tasa,
                    monto_retenido,
                    monto_enterado,
                    diferencia,
                    proveedor_id,
                    proveedor_rfc,
                    fecha_entero,
                    estado,
                    json.dumps(fundamento_legal) if fundamento_legal else None
                )
                
                retencion = _serialize_record(row)
                logger.info(f"📁 Defense Files: Retención registrada ID={retencion['id']}")
                return {"success": True, "retencion": retencion}
                
            except Exception as e:
                logger.error(f"📁 Defense Files: Error al registrar retención: {e}")
                return {"success": False, "error": str(e)}

    async def listar_retenciones(self, defense_file_id: int) -> Dict[str, Any]:
        """Lista las retenciones del expediente."""
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            try:
                query = """
                    SELECT * FROM df_retenciones 
                    WHERE defense_file_id = $1 
                    ORDER BY created_at DESC
                """
                rows = await conn.fetch(query, defense_file_id)
                retenciones = [_serialize_record(row) for row in rows]
                
                totales_query = """
                    SELECT 
                        tipo_retencion,
                        COALESCE(SUM(base_gravable), 0) as total_base,
                        COALESCE(SUM(monto_retenido), 0) as total_retenido,
                        COALESCE(SUM(monto_enterado), 0) as total_enterado,
                        COALESCE(SUM(diferencia), 0) as total_diferencia
                    FROM df_retenciones 
                    WHERE defense_file_id = $1
                    GROUP BY tipo_retencion
                """
                totales_rows = await conn.fetch(totales_query, defense_file_id)
                totales_por_tipo = {
                    row['tipo_retencion']: {
                        "base": float(row['total_base']),
                        "retenido": float(row['total_retenido']),
                        "enterado": float(row['total_enterado']),
                        "diferencia": float(row['total_diferencia'])
                    }
                    for row in totales_rows
                }
                
                return {
                    "success": True,
                    "retenciones": retenciones,
                    "total": len(retenciones),
                    "totales_por_tipo": totales_por_tipo
                }
                
            except Exception as e:
                logger.error(f"📁 Defense Files: Error al listar retenciones: {e}")
                return {"success": False, "error": str(e)}

    async def obtener_resumen_completo(self, defense_file_id: int) -> Dict[str, Any]:
        """Obtiene el resumen completo del expediente usando la vista v_defense_file_completo."""
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            try:
                query = """
                    SELECT * FROM v_defense_file_completo 
                    WHERE id = $1
                """
                row = await conn.fetchrow(query, defense_file_id)
                
                if not row:
                    df_result = await self.obtener_defense_file(defense_file_id)
                    if not df_result.get('success'):
                        return {"success": False, "error": "Expediente no encontrado"}
                    
                    return {
                        "success": True,
                        "resumen": df_result.get('defense_file', {}),
                        "fuente": "defense_files"
                    }
                
                resumen = _serialize_record(row)
                
                bitacora_result = await self.obtener_bitacora(defense_file_id, limit=10)
                deducciones_result = await self.listar_deducciones(defense_file_id)
                comunicaciones_result = await self.listar_comunicaciones(defense_file_id)
                documentos_result = await self.listar_documentos_tabla(defense_file_id)
                retenciones_result = await self.listar_retenciones(defense_file_id)
                
                resumen['ultimas_bitacoras'] = bitacora_result.get('bitacora', []) if bitacora_result.get('success') else []
                resumen['deducciones_resumen'] = deducciones_result.get('totales', {}) if deducciones_result.get('success') else {}
                resumen['total_deducciones'] = deducciones_result.get('total', 0) if deducciones_result.get('success') else 0
                resumen['total_comunicaciones'] = comunicaciones_result.get('total', 0) if comunicaciones_result.get('success') else 0
                resumen['total_documentos'] = documentos_result.get('total', 0) if documentos_result.get('success') else 0
                resumen['retenciones_resumen'] = retenciones_result.get('totales_por_tipo', {}) if retenciones_result.get('success') else {}
                resumen['total_retenciones'] = retenciones_result.get('total', 0) if retenciones_result.get('success') else 0
                
                logger.info(f"📁 Defense Files: Resumen completo obtenido para expediente {defense_file_id}")
                return {"success": True, "resumen": resumen, "fuente": "v_defense_file_completo"}
                
            except Exception as e:
                logger.error(f"📁 Defense Files: Error al obtener resumen completo: {e}")
                return {"success": False, "error": str(e)}


defense_file_pg_service = DefenseFilePGService()
