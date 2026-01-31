"""
defense_file_v2_routes.py - API Routes para Defense File Mejorado REVISAR.IA

Sistema de expedientes de defensa estructurados con:
- 5 secciones según metodología
- Índice de Defendibilidad (0-100)
- Integración con 3-Way Match
- Generación automática de documentos

Fecha: 2026-01-31
"""

from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from uuid import UUID
import logging
import os
import json
import hashlib

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/defense-v2", tags=["Defense File V2"])


# =============================================================================
# MODELOS PYDANTIC
# =============================================================================

class SeccionContexto(BaseModel):
    """Sección 1: Contexto Estratégico y Razón de Negocios"""
    razon_negocios_descripcion: str = ""
    objetivo_negocio: str = ""
    pilares_estrategicos: List[str] = []
    okrs_vinculados: List[str] = []
    alternativas_consideradas: str = ""
    riesgos_de_no_hacer: str = ""


class SeccionContractual(BaseModel):
    """Sección 2: Marco Contractual"""
    contrato_id: Optional[str] = None
    sow_id: Optional[str] = None
    objeto_servicio: str = ""
    alcance_detallado: str = ""
    entregables_pactados: List[Dict[str, Any]] = []
    cronograma: Dict[str, Any] = {}
    monto_total: float = 0
    forma_pago: str = ""


class SeccionEjecucion(BaseModel):
    """Sección 3: Evidencia de Ejecución"""
    minutas: List[Dict[str, Any]] = []
    versiones_entregables: List[Dict[str, Any]] = []
    comunicaciones: List[Dict[str, Any]] = []
    evidencia_trabajo: List[Dict[str, Any]] = []
    acta_aceptacion_id: Optional[str] = None
    fecha_aceptacion: Optional[date] = None


class SeccionFinanciero(BaseModel):
    """Sección 4: Aspecto Financiero"""
    cfdi_uuid: Optional[str] = None
    cfdi_folio: Optional[str] = None
    cfdi_monto: float = 0
    cfdi_concepto: str = ""
    cfdi_es_especifico: bool = False
    pago_referencia: Optional[str] = None
    pago_fecha: Optional[date] = None
    pago_monto: float = 0
    three_way_match_id: Optional[str] = None
    three_way_match_status: str = "pendiente"


class SeccionCierre(BaseModel):
    """Sección 5: Cierre y BEE Post-Implementación"""
    bee_original: Dict[str, Any] = {}
    bee_alcanzado: Dict[str, Any] = {}
    kpis_medidos: List[Dict[str, Any]] = []
    uso_real_servicio: str = ""
    lecciones_aprendidas: str = ""
    recomendaciones_futuras: str = ""


class DefenseFileCreate(BaseModel):
    proyecto_id: str
    empresa_id: str
    titulo: str
    descripcion: Optional[str] = None


class DefenseFileUpdate(BaseModel):
    titulo: Optional[str] = None
    descripcion: Optional[str] = None
    estado: Optional[str] = None
    seccion_1_contexto: Optional[SeccionContexto] = None
    seccion_2_contractual: Optional[SeccionContractual] = None
    seccion_3_ejecucion: Optional[SeccionEjecucion] = None
    seccion_4_financiero: Optional[SeccionFinanciero] = None
    seccion_5_cierre: Optional[SeccionCierre] = None


class AprobacionRequest(BaseModel):
    tipo: str = Field(..., description="fiscal, legal, finanzas")
    aprobado: bool
    notas: Optional[str] = None


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.get("", response_model=dict)
async def listar_defense_files(
    empresa_id: Optional[str] = Query(None),
    proyecto_id: Optional[str] = Query(None),
    estado: Optional[str] = Query(None),
    min_defendibilidad: Optional[float] = Query(None, ge=0, le=100),
    limit: int = Query(50, le=200),
    offset: int = Query(0)
):
    """
    Lista los expedientes de defensa con filtros opcionales.
    """
    try:
        import asyncpg
        db_url = os.environ.get("DATABASE_URL")
        if not db_url:
            return {
                "items": get_demo_defense_files(),
                "total": 2,
                "stats": get_defense_stats([])
            }

        conn = await asyncpg.connect(db_url)

        query = """
            SELECT id, folio_defensa, proyecto_id, empresa_id, titulo, descripcion,
                   estado, indice_defendibilidad, score_razon_negocios, score_bee,
                   score_materialidad, score_trazabilidad, score_coherencia_documental,
                   aprobacion_fiscal, aprobacion_legal, aprobacion_finanzas,
                   created_at, updated_at
            FROM defense_files_v2
            WHERE 1=1
        """
        params = []
        param_idx = 1

        if empresa_id:
            query += f" AND empresa_id = ${param_idx}"
            params.append(empresa_id)
            param_idx += 1

        if proyecto_id:
            query += f" AND proyecto_id = ${param_idx}"
            params.append(proyecto_id)
            param_idx += 1

        if estado:
            query += f" AND estado = ${param_idx}"
            params.append(estado)
            param_idx += 1

        if min_defendibilidad is not None:
            query += f" AND indice_defendibilidad >= ${param_idx}"
            params.append(min_defendibilidad)
            param_idx += 1

        # Count
        count_query = query.replace(
            "SELECT id, folio_defensa, proyecto_id, empresa_id, titulo, descripcion, estado, indice_defendibilidad, score_razon_negocios, score_bee, score_materialidad, score_trazabilidad, score_coherencia_documental, aprobacion_fiscal, aprobacion_legal, aprobacion_finanzas, created_at, updated_at",
            "SELECT COUNT(*)"
        )
        total = await conn.fetchval(count_query, *params)

        # Pagination
        query += f" ORDER BY created_at DESC LIMIT ${param_idx} OFFSET ${param_idx + 1}"
        params.extend([limit, offset])

        rows = await conn.fetch(query, *params)
        await conn.close()

        items = []
        for row in rows:
            items.append({
                "id": str(row["id"]),
                "folio_defensa": row["folio_defensa"],
                "proyecto_id": str(row["proyecto_id"]) if row["proyecto_id"] else None,
                "titulo": row["titulo"],
                "estado": row["estado"],
                "indice_defendibilidad": float(row["indice_defendibilidad"]) if row["indice_defendibilidad"] else 0,
                "scores": {
                    "razon_negocios": float(row["score_razon_negocios"]) if row["score_razon_negocios"] else 0,
                    "bee": float(row["score_bee"]) if row["score_bee"] else 0,
                    "materialidad": float(row["score_materialidad"]) if row["score_materialidad"] else 0,
                    "trazabilidad": float(row["score_trazabilidad"]) if row["score_trazabilidad"] else 0,
                    "coherencia": float(row["score_coherencia_documental"]) if row["score_coherencia_documental"] else 0
                },
                "aprobaciones": {
                    "fiscal": row["aprobacion_fiscal"],
                    "legal": row["aprobacion_legal"],
                    "finanzas": row["aprobacion_finanzas"]
                },
                "created_at": row["created_at"].isoformat() if row["created_at"] else None
            })

        return {
            "items": items,
            "total": total,
            "stats": get_defense_stats(items)
        }

    except Exception as e:
        logger.error(f"Error listando defense files: {e}")
        return {
            "items": get_demo_defense_files(),
            "total": 2,
            "stats": {}
        }


@router.get("/estados", response_model=List[dict])
async def obtener_estados():
    """
    Obtiene los estados posibles de un Defense File.
    """
    return [
        {"codigo": "borrador", "nombre": "Borrador", "descripcion": "En construcción inicial", "color": "gray"},
        {"codigo": "en_construccion", "nombre": "En Construcción", "descripcion": "Recopilando evidencia", "color": "blue"},
        {"codigo": "revision_interna", "nombre": "Revisión Interna", "descripcion": "Pendiente de aprobaciones", "color": "yellow"},
        {"codigo": "aprobado", "nombre": "Aprobado", "descripcion": "Listo para defensa", "color": "green"},
        {"codigo": "presentado", "nombre": "Presentado", "descripcion": "Usado en auditoría/litigio", "color": "purple"},
        {"codigo": "archivado", "nombre": "Archivado", "descripcion": "Caso cerrado", "color": "gray"}
    ]


@router.get("/{id}", response_model=dict)
async def obtener_defense_file(id: str):
    """
    Obtiene el detalle completo de un Defense File con todas sus secciones.
    """
    try:
        import asyncpg
        db_url = os.environ.get("DATABASE_URL")
        if not db_url:
            demo = get_demo_defense_files()
            for item in demo:
                if item["id"] == id:
                    return item
            raise HTTPException(status_code=404, detail="Defense File no encontrado")

        conn = await asyncpg.connect(db_url)
        row = await conn.fetchrow("SELECT * FROM defense_files_v2 WHERE id = $1", id)
        await conn.close()

        if not row:
            raise HTTPException(status_code=404, detail="Defense File no encontrado")

        return {
            "id": str(row["id"]),
            "folio_defensa": row["folio_defensa"],
            "proyecto_id": str(row["proyecto_id"]) if row["proyecto_id"] else None,
            "empresa_id": str(row["empresa_id"]) if row["empresa_id"] else None,
            "titulo": row["titulo"],
            "descripcion": row["descripcion"],
            "estado": row["estado"],
            "indice_defendibilidad": float(row["indice_defendibilidad"]) if row["indice_defendibilidad"] else 0,
            "scores": {
                "razon_negocios": float(row["score_razon_negocios"]) if row["score_razon_negocios"] else 0,
                "bee": float(row["score_bee"]) if row["score_bee"] else 0,
                "materialidad": float(row["score_materialidad"]) if row["score_materialidad"] else 0,
                "trazabilidad": float(row["score_trazabilidad"]) if row["score_trazabilidad"] else 0,
                "coherencia": float(row["score_coherencia_documental"]) if row["score_coherencia_documental"] else 0
            },
            "secciones": {
                "contexto": row["seccion_1_contexto"] or {},
                "contractual": row["seccion_2_contractual"] or {},
                "ejecucion": row["seccion_3_ejecucion"] or {},
                "financiero": row["seccion_4_financiero"] or {},
                "cierre": row["seccion_5_cierre"] or {}
            },
            "aprobaciones": {
                "fiscal": {
                    "aprobado": row["aprobacion_fiscal"],
                    "fecha": row["aprobacion_fiscal_fecha"].isoformat() if row["aprobacion_fiscal_fecha"] else None
                },
                "legal": {
                    "aprobado": row["aprobacion_legal"],
                    "fecha": row["aprobacion_legal_fecha"].isoformat() if row["aprobacion_legal_fecha"] else None
                },
                "finanzas": {
                    "aprobado": row["aprobacion_finanzas"],
                    "fecha": row["aprobacion_finanzas_fecha"].isoformat() if row["aprobacion_finanzas_fecha"] else None
                }
            },
            "documentos_ids": row["documentos_ids"] or [],
            "deliberaciones_ids": row["deliberaciones_ids"] or [],
            "hash_contenido": row["hash_contenido"],
            "created_at": row["created_at"].isoformat() if row["created_at"] else None,
            "updated_at": row["updated_at"].isoformat() if row["updated_at"] else None
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo defense file: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("", response_model=dict)
async def crear_defense_file(data: DefenseFileCreate):
    """
    Crea un nuevo Defense File para un proyecto.
    """
    try:
        import asyncpg
        db_url = os.environ.get("DATABASE_URL")
        if not db_url:
            raise HTTPException(status_code=503, detail="Base de datos no disponible")

        conn = await asyncpg.connect(db_url)

        # El folio se genera automáticamente por el trigger
        row = await conn.fetchrow("""
            INSERT INTO defense_files_v2 (
                proyecto_id, empresa_id, titulo, descripcion, estado
            ) VALUES ($1, $2, $3, $4, 'borrador')
            RETURNING id, folio_defensa, created_at
        """, data.proyecto_id, data.empresa_id, data.titulo, data.descripcion)
        await conn.close()

        return {
            "success": True,
            "id": str(row["id"]),
            "folio_defensa": row["folio_defensa"],
            "message": "Defense File creado exitosamente"
        }

    except Exception as e:
        logger.error(f"Error creando defense file: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{id}", response_model=dict)
async def actualizar_defense_file(id: str, data: DefenseFileUpdate):
    """
    Actualiza un Defense File y recalcula el índice de defendibilidad.
    """
    try:
        import asyncpg
        db_url = os.environ.get("DATABASE_URL")
        if not db_url:
            raise HTTPException(status_code=503, detail="Base de datos no disponible")

        conn = await asyncpg.connect(db_url)

        updates = []
        params = []
        param_idx = 1

        if data.titulo is not None:
            updates.append(f"titulo = ${param_idx}")
            params.append(data.titulo)
            param_idx += 1

        if data.descripcion is not None:
            updates.append(f"descripcion = ${param_idx}")
            params.append(data.descripcion)
            param_idx += 1

        if data.estado is not None:
            updates.append(f"estado = ${param_idx}")
            params.append(data.estado)
            param_idx += 1

        if data.seccion_1_contexto is not None:
            updates.append(f"seccion_1_contexto = ${param_idx}")
            params.append(json.dumps(data.seccion_1_contexto.dict()))
            param_idx += 1

        if data.seccion_2_contractual is not None:
            updates.append(f"seccion_2_contractual = ${param_idx}")
            params.append(json.dumps(data.seccion_2_contractual.dict()))
            param_idx += 1

        if data.seccion_3_ejecucion is not None:
            updates.append(f"seccion_3_ejecucion = ${param_idx}")
            params.append(json.dumps(data.seccion_3_ejecucion.dict()))
            param_idx += 1

        if data.seccion_4_financiero is not None:
            updates.append(f"seccion_4_financiero = ${param_idx}")
            params.append(json.dumps(data.seccion_4_financiero.dict()))
            param_idx += 1

        if data.seccion_5_cierre is not None:
            updates.append(f"seccion_5_cierre = ${param_idx}")
            params.append(json.dumps(data.seccion_5_cierre.dict()))
            param_idx += 1

        updates.append("updated_at = NOW()")

        query = f"UPDATE defense_files_v2 SET {', '.join(updates)} WHERE id = ${param_idx}"
        params.append(id)

        await conn.execute(query, *params)

        # Recalcular índice de defendibilidad
        await recalcular_indice_defendibilidad(conn, id)

        await conn.close()

        return {"success": True, "message": "Defense File actualizado"}

    except Exception as e:
        logger.error(f"Error actualizando defense file: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{id}/aprobar", response_model=dict)
async def registrar_aprobacion(id: str, data: AprobacionRequest, user_id: Optional[str] = Query(None)):
    """
    Registra la aprobación de Fiscal, Legal o Finanzas.
    """
    tipos_validos = ["fiscal", "legal", "finanzas"]
    if data.tipo not in tipos_validos:
        raise HTTPException(status_code=400, detail=f"Tipo inválido. Válidos: {tipos_validos}")

    try:
        import asyncpg
        db_url = os.environ.get("DATABASE_URL")
        if not db_url:
            raise HTTPException(status_code=503, detail="Base de datos no disponible")

        conn = await asyncpg.connect(db_url)

        campo_aprobacion = f"aprobacion_{data.tipo}"
        campo_fecha = f"aprobacion_{data.tipo}_fecha"
        campo_por = f"aprobacion_{data.tipo}_por"

        await conn.execute(f"""
            UPDATE defense_files_v2
            SET {campo_aprobacion} = $1,
                {campo_fecha} = NOW(),
                {campo_por} = $2,
                updated_at = NOW()
            WHERE id = $3
        """, data.aprobado, user_id, id)

        # Verificar si todas las aprobaciones están completas
        row = await conn.fetchrow("""
            SELECT aprobacion_fiscal, aprobacion_legal, aprobacion_finanzas
            FROM defense_files_v2 WHERE id = $1
        """, id)

        if row and all([row["aprobacion_fiscal"], row["aprobacion_legal"], row["aprobacion_finanzas"]]):
            await conn.execute("""
                UPDATE defense_files_v2
                SET estado = 'aprobado', updated_at = NOW()
                WHERE id = $1
            """, id)

        await conn.close()

        return {
            "success": True,
            "message": f"Aprobación de {data.tipo} registrada"
        }

    except Exception as e:
        logger.error(f"Error registrando aprobación: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{id}/calcular-indice", response_model=dict)
async def calcular_indice(id: str):
    """
    Recalcula manualmente el índice de defendibilidad.
    """
    try:
        import asyncpg
        db_url = os.environ.get("DATABASE_URL")
        if not db_url:
            return {"indice_defendibilidad": 75.5, "message": "Demo mode"}

        conn = await asyncpg.connect(db_url)
        indice = await recalcular_indice_defendibilidad(conn, id)
        await conn.close()

        return {
            "success": True,
            "indice_defendibilidad": indice,
            "message": "Índice recalculado"
        }

    except Exception as e:
        logger.error(f"Error calculando índice: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{id}/generar-hash", response_model=dict)
async def generar_hash_integridad(id: str):
    """
    Genera y registra el hash de integridad del Defense File.
    """
    try:
        import asyncpg
        db_url = os.environ.get("DATABASE_URL")
        if not db_url:
            return {"hash": "demo_hash_abc123", "message": "Demo mode"}

        conn = await asyncpg.connect(db_url)

        row = await conn.fetchrow("""
            SELECT seccion_1_contexto, seccion_2_contractual, seccion_3_ejecucion,
                   seccion_4_financiero, seccion_5_cierre, documentos_ids
            FROM defense_files_v2 WHERE id = $1
        """, id)

        if not row:
            raise HTTPException(status_code=404, detail="Defense File no encontrado")

        # Construir contenido para hash
        contenido = json.dumps({
            "s1": row["seccion_1_contexto"],
            "s2": row["seccion_2_contractual"],
            "s3": row["seccion_3_ejecucion"],
            "s4": row["seccion_4_financiero"],
            "s5": row["seccion_5_cierre"],
            "docs": row["documentos_ids"]
        }, sort_keys=True)

        hash_contenido = hashlib.sha256(contenido.encode()).hexdigest()

        await conn.execute("""
            UPDATE defense_files_v2
            SET hash_contenido = $1, fecha_hash = NOW(), updated_at = NOW()
            WHERE id = $2
        """, hash_contenido, id)

        await conn.close()

        return {
            "success": True,
            "hash": hash_contenido,
            "message": "Hash de integridad generado"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generando hash: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{id}/exportar", response_model=dict)
async def exportar_defense_file(id: str, formato: str = Query("json", description="json, pdf")):
    """
    Exporta el Defense File en el formato especificado.
    """
    # TODO: Implementar exportación a PDF
    if formato == "pdf":
        raise HTTPException(status_code=501, detail="Exportación a PDF en desarrollo")

    return await obtener_defense_file(id)


# =============================================================================
# FUNCIONES AUXILIARES
# =============================================================================

async def recalcular_indice_defendibilidad(conn, defense_file_id: str) -> float:
    """
    Recalcula el índice de defendibilidad basado en las 5 secciones.
    """
    row = await conn.fetchrow("""
        SELECT seccion_1_contexto, seccion_2_contractual, seccion_3_ejecucion,
               seccion_4_financiero, seccion_5_cierre
        FROM defense_files_v2 WHERE id = $1
    """, defense_file_id)

    if not row:
        return 0

    # Calcular scores por sección
    s1 = row["seccion_1_contexto"] or {}
    s2 = row["seccion_2_contractual"] or {}
    s3 = row["seccion_3_ejecucion"] or {}
    s4 = row["seccion_4_financiero"] or {}
    s5 = row["seccion_5_cierre"] or {}

    # Score Razón de Negocios (Sección 1)
    score_rn = 0
    if s1.get("razon_negocios_descripcion"):
        score_rn += 30
    if s1.get("objetivo_negocio"):
        score_rn += 25
    if s1.get("pilares_estrategicos"):
        score_rn += 25
    if s1.get("alternativas_consideradas"):
        score_rn += 20

    # Score BEE (Secciones 1 y 5)
    score_bee = 0
    if s1.get("okrs_vinculados"):
        score_bee += 30
    if s5.get("bee_original"):
        score_bee += 35
    if s5.get("kpis_medidos"):
        score_bee += 35

    # Score Materialidad (Secciones 2 y 3)
    score_mat = 0
    if s2.get("contrato_id") or s2.get("sow_id"):
        score_mat += 25
    if s2.get("entregables_pactados"):
        score_mat += 25
    if s3.get("versiones_entregables"):
        score_mat += 25
    if s3.get("acta_aceptacion_id"):
        score_mat += 25

    # Score Trazabilidad (Sección 3)
    score_traz = 0
    if s3.get("minutas"):
        score_traz += 35
    if s3.get("comunicaciones"):
        score_traz += 30
    if s3.get("evidencia_trabajo"):
        score_traz += 35

    # Score Coherencia (Sección 4 - 3-way match)
    score_coh = 0
    if s4.get("cfdi_uuid"):
        score_coh += 25
    if s4.get("cfdi_es_especifico"):
        score_coh += 25
    if s4.get("three_way_match_status") == "completo":
        score_coh += 50
    elif s4.get("three_way_match_status") == "parcial":
        score_coh += 25

    # Calcular índice total (promedio ponderado)
    indice = (
        score_rn * 0.20 +
        score_bee * 0.20 +
        score_mat * 0.25 +
        score_traz * 0.20 +
        score_coh * 0.15
    )

    # Actualizar en DB
    await conn.execute("""
        UPDATE defense_files_v2
        SET indice_defendibilidad = $1,
            score_razon_negocios = $2,
            score_bee = $3,
            score_materialidad = $4,
            score_trazabilidad = $5,
            score_coherencia_documental = $6,
            updated_at = NOW()
        WHERE id = $7
    """, indice, score_rn, score_bee, score_mat, score_traz, score_coh, defense_file_id)

    return indice


def get_defense_stats(items: List[dict]) -> dict:
    """Calcula estadísticas de los Defense Files."""
    if not items:
        return {
            "total": 0,
            "por_estado": {},
            "promedio_defendibilidad": 0
        }

    por_estado = {}
    total_def = 0

    for item in items:
        estado = item.get("estado", "borrador")
        por_estado[estado] = por_estado.get(estado, 0) + 1
        total_def += item.get("indice_defendibilidad", 0)

    return {
        "total": len(items),
        "por_estado": por_estado,
        "promedio_defendibilidad": round(total_def / len(items), 2) if items else 0
    }


def get_demo_defense_files():
    """Retorna Defense Files de demostración."""
    return [
        {
            "id": "demo-df-001",
            "folio_defensa": "DF-2026-00001",
            "proyecto_id": "demo-proj-001",
            "titulo": "Estudio Prospectivo Macroeconómico 2026",
            "estado": "aprobado",
            "indice_defendibilidad": 85.5,
            "scores": {
                "razon_negocios": 90,
                "bee": 80,
                "materialidad": 85,
                "trazabilidad": 88,
                "coherencia": 80
            },
            "aprobaciones": {
                "fiscal": True,
                "legal": True,
                "finanzas": True
            },
            "created_at": "2026-01-15T10:30:00Z"
        },
        {
            "id": "demo-df-002",
            "folio_defensa": "DF-2026-00002",
            "proyecto_id": "demo-proj-002",
            "titulo": "Consultoría Estratégica Q1 2026",
            "estado": "en_construccion",
            "indice_defendibilidad": 62.0,
            "scores": {
                "razon_negocios": 75,
                "bee": 60,
                "materialidad": 55,
                "trazabilidad": 70,
                "coherencia": 50
            },
            "aprobaciones": {
                "fiscal": False,
                "legal": False,
                "finanzas": False
            },
            "created_at": "2026-01-25T14:00:00Z"
        }
    ]
