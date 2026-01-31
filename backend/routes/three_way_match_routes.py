"""
three_way_match_routes.py - API Routes para 3-Way Match REVISAR.IA

Validación de coherencia entre:
- Contrato/SOW
- CFDI
- Pago

Fecha: 2026-01-31
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import date, datetime
from decimal import Decimal
import logging
import os

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/3way-match", tags=["3-Way Match"])


# =============================================================================
# MODELOS PYDANTIC
# =============================================================================

class ContratoData(BaseModel):
    contrato_id: Optional[str] = None
    monto: float
    concepto: str
    fecha: date
    documento_id: Optional[str] = None


class CFDIData(BaseModel):
    uuid: str
    folio: Optional[str] = None
    monto: float
    concepto: str
    fecha: date
    rfc_emisor: str
    rfc_receptor: str
    documento_id: Optional[str] = None


class PagoData(BaseModel):
    pago_id: Optional[str] = None
    monto: float
    fecha: date
    referencia: str
    banco: Optional[str] = None
    documento_id: Optional[str] = None


class ThreeWayMatchCreate(BaseModel):
    proyecto_id: str
    empresa_id: str
    contrato: ContratoData
    cfdi: CFDIData
    pago: PagoData
    tolerancia_monto: float = Field(default=0.01, description="Tolerancia en porcentaje (0.01 = 1%)")


class ThreeWayMatchValidate(BaseModel):
    contrato_monto: float
    cfdi_monto: float
    pago_monto: float
    tolerancia_porcentaje: float = 0.01


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.get("", response_model=dict)
async def listar_matches(
    proyecto_id: Optional[str] = Query(None),
    empresa_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None, description="pendiente, parcial, completo, discrepancia"),
    limit: int = Query(50, le=200),
    offset: int = Query(0)
):
    """
    Lista los 3-way matches con filtros opcionales.
    """
    try:
        import asyncpg
        db_url = os.environ.get("DATABASE_URL")
        if not db_url:
            return {
                "items": get_demo_matches(),
                "total": 2,
                "stats": {"completo": 1, "parcial": 1, "discrepancia": 0}
            }

        conn = await asyncpg.connect(db_url)

        query = """
            SELECT id, match_id, proyecto_id, empresa_id,
                   contrato_monto, cfdi_monto, pago_monto,
                   match_status, discrepancia_monto, discrepancia_concepto,
                   excepcion_aprobada, created_at
            FROM three_way_match
            WHERE 1=1
        """
        params = []
        param_idx = 1

        if proyecto_id:
            query += f" AND proyecto_id = ${param_idx}"
            params.append(proyecto_id)
            param_idx += 1

        if empresa_id:
            query += f" AND empresa_id = ${param_idx}"
            params.append(empresa_id)
            param_idx += 1

        if status:
            query += f" AND match_status = ${param_idx}"
            params.append(status)
            param_idx += 1

        # Count
        count_query = query.replace(
            "SELECT id, match_id, proyecto_id, empresa_id, contrato_monto, cfdi_monto, pago_monto, match_status, discrepancia_monto, discrepancia_concepto, excepcion_aprobada, created_at",
            "SELECT COUNT(*)"
        )
        total = await conn.fetchval(count_query, *params)

        # Stats
        stats = await conn.fetchrow("""
            SELECT
                COUNT(*) FILTER (WHERE match_status = 'completo') as completo,
                COUNT(*) FILTER (WHERE match_status = 'parcial') as parcial,
                COUNT(*) FILTER (WHERE match_status = 'discrepancia') as discrepancia,
                COUNT(*) FILTER (WHERE match_status = 'pendiente') as pendiente
            FROM three_way_match
        """)

        # Pagination
        query += f" ORDER BY created_at DESC LIMIT ${param_idx} OFFSET ${param_idx + 1}"
        params.extend([limit, offset])

        rows = await conn.fetch(query, *params)
        await conn.close()

        items = []
        for row in rows:
            items.append({
                "id": str(row["id"]),
                "match_id": row["match_id"],
                "proyecto_id": str(row["proyecto_id"]) if row["proyecto_id"] else None,
                "montos": {
                    "contrato": float(row["contrato_monto"]) if row["contrato_monto"] else 0,
                    "cfdi": float(row["cfdi_monto"]) if row["cfdi_monto"] else 0,
                    "pago": float(row["pago_monto"]) if row["pago_monto"] else 0
                },
                "status": row["match_status"],
                "tiene_discrepancia": row["discrepancia_monto"] or row["discrepancia_concepto"],
                "excepcion_aprobada": row["excepcion_aprobada"],
                "created_at": row["created_at"].isoformat() if row["created_at"] else None
            })

        return {
            "items": items,
            "total": total,
            "stats": dict(stats) if stats else {}
        }

    except Exception as e:
        logger.error(f"Error listando matches: {e}")
        return {
            "items": get_demo_matches(),
            "total": 2,
            "stats": {}
        }


@router.post("/validar", response_model=dict)
async def validar_match(data: ThreeWayMatchValidate):
    """
    Valida si los montos coinciden dentro de la tolerancia especificada.
    No guarda en DB, solo calcula.
    """
    # Calcular diferencias
    diff_contrato_cfdi = abs(data.contrato_monto - data.cfdi_monto)
    diff_cfdi_pago = abs(data.cfdi_monto - data.pago_monto)
    diff_contrato_pago = abs(data.contrato_monto - data.pago_monto)

    # Calcular tolerancia absoluta
    monto_referencia = max(data.contrato_monto, data.cfdi_monto, data.pago_monto)
    tolerancia_absoluta = monto_referencia * data.tolerancia_porcentaje

    # Determinar status
    discrepancias = []

    if diff_contrato_cfdi > tolerancia_absoluta:
        discrepancias.append({
            "tipo": "contrato_vs_cfdi",
            "diferencia": diff_contrato_cfdi,
            "porcentaje": (diff_contrato_cfdi / data.contrato_monto * 100) if data.contrato_monto > 0 else 0
        })

    if diff_cfdi_pago > tolerancia_absoluta:
        discrepancias.append({
            "tipo": "cfdi_vs_pago",
            "diferencia": diff_cfdi_pago,
            "porcentaje": (diff_cfdi_pago / data.cfdi_monto * 100) if data.cfdi_monto > 0 else 0
        })

    if diff_contrato_pago > tolerancia_absoluta:
        discrepancias.append({
            "tipo": "contrato_vs_pago",
            "diferencia": diff_contrato_pago,
            "porcentaje": (diff_contrato_pago / data.contrato_monto * 100) if data.contrato_monto > 0 else 0
        })

    # Determinar status
    if not discrepancias:
        status = "completo"
        mensaje = "✅ Los tres montos coinciden dentro de la tolerancia"
    elif len(discrepancias) < 3:
        status = "parcial"
        mensaje = f"⚠️ Se encontraron {len(discrepancias)} discrepancia(s)"
    else:
        status = "discrepancia"
        mensaje = "❌ Los montos no coinciden"

    return {
        "status": status,
        "mensaje": mensaje,
        "montos": {
            "contrato": data.contrato_monto,
            "cfdi": data.cfdi_monto,
            "pago": data.pago_monto
        },
        "tolerancia_aplicada": {
            "porcentaje": data.tolerancia_porcentaje * 100,
            "absoluta": tolerancia_absoluta
        },
        "discrepancias": discrepancias,
        "es_valido": len(discrepancias) == 0
    }


@router.post("", response_model=dict)
async def crear_match(data: ThreeWayMatchCreate):
    """
    Crea un nuevo registro de 3-way match.
    """
    try:
        import asyncpg
        db_url = os.environ.get("DATABASE_URL")
        if not db_url:
            raise HTTPException(status_code=503, detail="Base de datos no disponible")

        # Validar primero
        validacion = await validar_match(ThreeWayMatchValidate(
            contrato_monto=data.contrato.monto,
            cfdi_monto=data.cfdi.monto,
            pago_monto=data.pago.monto,
            tolerancia_porcentaje=data.tolerancia_monto
        ))

        # Detectar si CFDI es genérico
        cfdi_es_generico = es_cfdi_generico(data.cfdi.concepto)

        conn = await asyncpg.connect(db_url)

        # El match_id se genera automáticamente por el trigger
        row = await conn.fetchrow("""
            INSERT INTO three_way_match (
                proyecto_id, empresa_id,
                contrato_id, contrato_monto, contrato_concepto, contrato_fecha, contrato_documento_id,
                cfdi_uuid, cfdi_folio, cfdi_monto, cfdi_concepto, cfdi_fecha,
                cfdi_rfc_emisor, cfdi_rfc_receptor, cfdi_documento_id, cfdi_es_generico,
                pago_id, pago_monto, pago_fecha, pago_referencia, pago_banco, pago_documento_id,
                match_status, discrepancia_monto, discrepancia_monto_detalle,
                tolerancia_porcentaje
            ) VALUES (
                $1, $2,
                $3, $4, $5, $6, $7,
                $8, $9, $10, $11, $12, $13, $14, $15, $16,
                $17, $18, $19, $20, $21, $22,
                $23, $24, $25, $26
            )
            RETURNING id, match_id
        """,
            data.proyecto_id, data.empresa_id,
            data.contrato.contrato_id, data.contrato.monto, data.contrato.concepto,
            data.contrato.fecha, data.contrato.documento_id,
            data.cfdi.uuid, data.cfdi.folio, data.cfdi.monto, data.cfdi.concepto,
            data.cfdi.fecha, data.cfdi.rfc_emisor, data.cfdi.rfc_receptor,
            data.cfdi.documento_id, cfdi_es_generico,
            data.pago.pago_id, data.pago.monto, data.pago.fecha,
            data.pago.referencia, data.pago.banco, data.pago.documento_id,
            validacion["status"],
            len(validacion["discrepancias"]) > 0,
            str(validacion["discrepancias"]) if validacion["discrepancias"] else None,
            data.tolerancia_monto * 100
        )

        await conn.close()

        return {
            "success": True,
            "id": str(row["id"]),
            "match_id": row["match_id"],
            "validacion": validacion,
            "cfdi_es_generico": cfdi_es_generico,
            "alerta": "⚠️ El CFDI parece tener una descripción genérica" if cfdi_es_generico else None
        }

    except Exception as e:
        logger.error(f"Error creando match: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{id}", response_model=dict)
async def obtener_match(id: str):
    """
    Obtiene el detalle de un 3-way match.
    """
    try:
        import asyncpg
        db_url = os.environ.get("DATABASE_URL")
        if not db_url:
            for m in get_demo_matches():
                if m["id"] == id:
                    return m
            raise HTTPException(status_code=404, detail="Match no encontrado")

        conn = await asyncpg.connect(db_url)
        row = await conn.fetchrow("SELECT * FROM three_way_match WHERE id = $1", id)
        await conn.close()

        if not row:
            raise HTTPException(status_code=404, detail="Match no encontrado")

        return {
            "id": str(row["id"]),
            "match_id": row["match_id"],
            "proyecto_id": str(row["proyecto_id"]) if row["proyecto_id"] else None,
            "contrato": {
                "id": row["contrato_id"],
                "monto": float(row["contrato_monto"]) if row["contrato_monto"] else 0,
                "concepto": row["contrato_concepto"],
                "fecha": row["contrato_fecha"].isoformat() if row["contrato_fecha"] else None
            },
            "cfdi": {
                "uuid": row["cfdi_uuid"],
                "folio": row["cfdi_folio"],
                "monto": float(row["cfdi_monto"]) if row["cfdi_monto"] else 0,
                "concepto": row["cfdi_concepto"],
                "fecha": row["cfdi_fecha"].isoformat() if row["cfdi_fecha"] else None,
                "es_generico": row["cfdi_es_generico"]
            },
            "pago": {
                "id": row["pago_id"],
                "monto": float(row["pago_monto"]) if row["pago_monto"] else 0,
                "fecha": row["pago_fecha"].isoformat() if row["pago_fecha"] else None,
                "referencia": row["pago_referencia"],
                "banco": row["pago_banco"]
            },
            "status": row["match_status"],
            "discrepancias": {
                "monto": row["discrepancia_monto"],
                "concepto": row["discrepancia_concepto"],
                "fecha": row["discrepancia_fecha"]
            },
            "excepcion": {
                "aprobada": row["excepcion_aprobada"],
                "motivo": row["excepcion_motivo"],
                "fecha": row["excepcion_fecha"].isoformat() if row["excepcion_fecha"] else None
            },
            "created_at": row["created_at"].isoformat() if row["created_at"] else None
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo match: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{id}/aprobar-excepcion", response_model=dict)
async def aprobar_excepcion(
    id: str,
    motivo: str,
    user_id: Optional[str] = Query(None)
):
    """
    Aprueba una excepción para un match con discrepancias.
    """
    try:
        import asyncpg
        db_url = os.environ.get("DATABASE_URL")
        if not db_url:
            raise HTTPException(status_code=503, detail="Base de datos no disponible")

        conn = await asyncpg.connect(db_url)

        await conn.execute("""
            UPDATE three_way_match
            SET excepcion_aprobada = TRUE,
                excepcion_motivo = $1,
                excepcion_aprobada_por = $2,
                excepcion_fecha = NOW(),
                match_status = 'excepcion_aprobada',
                updated_at = NOW()
            WHERE id = $3
        """, motivo, user_id, id)

        await conn.close()

        return {
            "success": True,
            "message": "Excepción aprobada. El match ahora puede continuar."
        }

    except Exception as e:
        logger.error(f"Error aprobando excepción: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/proyecto/{proyecto_id}", response_model=dict)
async def obtener_matches_proyecto(proyecto_id: str):
    """
    Obtiene todos los 3-way matches de un proyecto.
    """
    return await listar_matches(proyecto_id=proyecto_id)


# =============================================================================
# FUNCIONES AUXILIARES
# =============================================================================

def es_cfdi_generico(concepto: str) -> bool:
    """
    Detecta si un CFDI tiene una descripción genérica.
    """
    if not concepto:
        return True

    concepto_lower = concepto.lower().strip()

    # Patrones genéricos
    patrones_genericos = [
        "servicios",
        "servicio profesional",
        "servicios profesionales",
        "honorarios",
        "pago de servicios",
        "consultoria",
        "asesoria",
        "varios",
        "por servicios",
        "pago",
        "factura",
        "cobro"
    ]

    # Si el concepto es muy corto, probablemente es genérico
    if len(concepto_lower) < 20:
        for patron in patrones_genericos:
            if concepto_lower == patron or concepto_lower.startswith(patron + " "):
                return True

    return False


def get_demo_matches():
    """Retorna matches de demostración."""
    return [
        {
            "id": "demo-match-001",
            "match_id": "TWM-20260125-001",
            "proyecto_id": "demo-proj-001",
            "montos": {
                "contrato": 1250000.00,
                "cfdi": 1250000.00,
                "pago": 1250000.00
            },
            "status": "completo",
            "tiene_discrepancia": False,
            "excepcion_aprobada": False,
            "created_at": "2026-01-25T10:00:00Z"
        },
        {
            "id": "demo-match-002",
            "match_id": "TWM-20260130-001",
            "proyecto_id": "demo-proj-002",
            "montos": {
                "contrato": 500000.00,
                "cfdi": 498500.00,
                "pago": 498500.00
            },
            "status": "parcial",
            "tiene_discrepancia": True,
            "excepcion_aprobada": False,
            "created_at": "2026-01-30T14:30:00Z"
        }
    ]
