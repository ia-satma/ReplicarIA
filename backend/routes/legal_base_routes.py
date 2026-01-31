"""
legal_base_routes.py - API Routes para Base Jurídica REVISAR.IA

Endpoints para gestión de:
- Artículos CFF/LISR
- Jurisprudencia SCJN/TFJA
- Normas Oficiales (NOM-151)
- Criterios internos

Fecha: 2026-01-31
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime
from uuid import UUID
import logging
import os

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/legal-base", tags=["Legal Base"])


# =============================================================================
# MODELOS PYDANTIC
# =============================================================================

class LegalBaseCreate(BaseModel):
    tipo: str = Field(..., description="Tipo: articulo_cff, articulo_lisr, jurisprudencia, norma_oficial, criterio_interno")
    categoria: Optional[str] = Field(None, description="Categoría: razon_negocios, materialidad, bee, trazabilidad, efos")
    titulo: str = Field(..., min_length=5, max_length=500)
    subtitulo: Optional[str] = None
    numero_referencia: Optional[str] = Field(None, description="Ej: Art. 5-A CFF, II.2o.C. J/1 K")
    registro_digital: Optional[str] = None
    contenido_completo: str = Field(..., min_length=10)
    resumen_ejecutivo: Optional[str] = None
    aplica_a_tipologias: List[str] = []
    aplica_a_fases: List[str] = []
    aplica_a_pilares: List[str] = []
    fecha_publicacion: Optional[date] = None
    fecha_vigencia_inicio: Optional[date] = None
    fecha_vigencia_fin: Optional[date] = None
    fuente: Optional[str] = None
    keywords: List[str] = []


class LegalBaseUpdate(BaseModel):
    titulo: Optional[str] = None
    subtitulo: Optional[str] = None
    contenido_completo: Optional[str] = None
    resumen_ejecutivo: Optional[str] = None
    aplica_a_tipologias: Optional[List[str]] = None
    aplica_a_fases: Optional[List[str]] = None
    aplica_a_pilares: Optional[List[str]] = None
    es_vigente: Optional[bool] = None
    fecha_vigencia_fin: Optional[date] = None
    keywords: Optional[List[str]] = None


class LegalBaseResponse(BaseModel):
    id: str
    tipo: str
    categoria: Optional[str]
    titulo: str
    subtitulo: Optional[str]
    numero_referencia: Optional[str]
    registro_digital: Optional[str]
    contenido_completo: str
    resumen_ejecutivo: Optional[str]
    aplica_a_tipologias: List[str]
    aplica_a_fases: List[str]
    aplica_a_pilares: List[str]
    fecha_publicacion: Optional[date]
    es_vigente: bool
    fuente: Optional[str]
    keywords: List[str]
    created_at: datetime


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.get("", response_model=dict)
async def listar_base_legal(
    tipo: Optional[str] = Query(None, description="Filtrar por tipo"),
    categoria: Optional[str] = Query(None, description="Filtrar por categoría"),
    pilar: Optional[str] = Query(None, description="Filtrar por pilar (razon_negocios, bee, materialidad, trazabilidad)"),
    fase: Optional[str] = Query(None, description="Filtrar por fase (F0-F9)"),
    solo_vigentes: bool = Query(True, description="Solo mostrar vigentes"),
    busqueda: Optional[str] = Query(None, description="Búsqueda en título y contenido"),
    limit: int = Query(50, le=200),
    offset: int = Query(0)
):
    """
    Lista artículos, jurisprudencia y normas de la base jurídica.
    """
    try:
        import asyncpg
        db_url = os.environ.get("DATABASE_URL")
        if not db_url:
            # Datos de demostración
            return {
                "items": get_demo_legal_base(tipo, categoria),
                "total": 5,
                "limit": limit,
                "offset": offset
            }

        conn = await asyncpg.connect(db_url)

        # Construir query
        query = """
            SELECT id, tipo, categoria, titulo, subtitulo, numero_referencia,
                   registro_digital, contenido_completo, resumen_ejecutivo,
                   aplica_a_tipologias, aplica_a_fases, aplica_a_pilares,
                   fecha_publicacion, es_vigente, fuente, keywords, created_at
            FROM legal_base
            WHERE 1=1
        """
        params = []
        param_idx = 1

        if tipo:
            query += f" AND tipo = ${param_idx}"
            params.append(tipo)
            param_idx += 1

        if categoria:
            query += f" AND categoria = ${param_idx}"
            params.append(categoria)
            param_idx += 1

        if pilar:
            query += f" AND aplica_a_pilares ? ${param_idx}"
            params.append(pilar)
            param_idx += 1

        if fase:
            query += f" AND aplica_a_fases ? ${param_idx}"
            params.append(fase)
            param_idx += 1

        if solo_vigentes:
            query += " AND es_vigente = TRUE"

        if busqueda:
            query += f" AND (titulo ILIKE ${param_idx} OR contenido_completo ILIKE ${param_idx})"
            params.append(f"%{busqueda}%")
            param_idx += 1

        # Count total
        count_query = query.replace(
            "SELECT id, tipo, categoria, titulo, subtitulo, numero_referencia, registro_digital, contenido_completo, resumen_ejecutivo, aplica_a_tipologias, aplica_a_fases, aplica_a_pilares, fecha_publicacion, es_vigente, fuente, keywords, created_at",
            "SELECT COUNT(*)"
        )
        total = await conn.fetchval(count_query, *params)

        # Add pagination
        query += f" ORDER BY orden_display, created_at DESC LIMIT ${param_idx} OFFSET ${param_idx + 1}"
        params.extend([limit, offset])

        rows = await conn.fetch(query, *params)
        await conn.close()

        items = []
        for row in rows:
            items.append({
                "id": str(row["id"]),
                "tipo": row["tipo"],
                "categoria": row["categoria"],
                "titulo": row["titulo"],
                "subtitulo": row["subtitulo"],
                "numero_referencia": row["numero_referencia"],
                "registro_digital": row["registro_digital"],
                "contenido_completo": row["contenido_completo"],
                "resumen_ejecutivo": row["resumen_ejecutivo"],
                "aplica_a_tipologias": row["aplica_a_tipologias"] or [],
                "aplica_a_fases": row["aplica_a_fases"] or [],
                "aplica_a_pilares": row["aplica_a_pilares"] or [],
                "fecha_publicacion": row["fecha_publicacion"].isoformat() if row["fecha_publicacion"] else None,
                "es_vigente": row["es_vigente"],
                "fuente": row["fuente"],
                "keywords": row["keywords"] or [],
                "created_at": row["created_at"].isoformat()
            })

        return {
            "items": items,
            "total": total,
            "limit": limit,
            "offset": offset
        }

    except Exception as e:
        logger.error(f"Error listando base legal: {e}")
        return {
            "items": get_demo_legal_base(tipo, categoria),
            "total": 5,
            "limit": limit,
            "offset": offset
        }


@router.get("/tipos", response_model=List[dict])
async def obtener_tipos():
    """
    Obtiene los tipos de contenido legal disponibles.
    """
    return [
        {"codigo": "articulo_cff", "nombre": "Artículos CFF", "descripcion": "Código Fiscal de la Federación"},
        {"codigo": "articulo_lisr", "nombre": "Artículos LISR", "descripcion": "Ley del Impuesto sobre la Renta"},
        {"codigo": "jurisprudencia", "nombre": "Jurisprudencia", "descripcion": "Tesis SCJN/TFJA"},
        {"codigo": "norma_oficial", "nombre": "Normas Oficiales", "descripcion": "NOM y estándares"},
        {"codigo": "criterio_sat", "nombre": "Criterios SAT", "descripcion": "Criterios normativos del SAT"},
        {"codigo": "resolucion_tfja", "nombre": "Resoluciones TFJA", "descripcion": "Resoluciones del Tribunal"},
        {"codigo": "criterio_interno", "nombre": "Criterios Internos", "descripcion": "Políticas de la plataforma"}
    ]


@router.get("/categorias", response_model=List[dict])
async def obtener_categorias():
    """
    Obtiene las categorías de clasificación.
    """
    return [
        {"codigo": "razon_negocios", "nombre": "Razón de Negocios", "pilar": "razon_negocios", "articulo_principal": "Art. 5-A CFF"},
        {"codigo": "bee", "nombre": "Beneficio Económico Esperado", "pilar": "bee", "articulo_principal": "Art. 5-A CFF"},
        {"codigo": "materialidad", "nombre": "Materialidad", "pilar": "materialidad", "articulo_principal": "Art. 69-B CFF"},
        {"codigo": "trazabilidad", "nombre": "Trazabilidad Documental", "pilar": "trazabilidad", "articulo_principal": "NOM-151"},
        {"codigo": "efos", "nombre": "EFOS / Operaciones Inexistentes", "pilar": "materialidad", "articulo_principal": "Art. 69-B CFF"},
        {"codigo": "uso_ia", "nombre": "Uso de IA", "pilar": None, "articulo_principal": "Jurisprudencia SCJN"},
        {"codigo": "deducciones", "nombre": "Requisitos de Deducciones", "pilar": "razon_negocios", "articulo_principal": "Art. 27 LISR"}
    ]


@router.get("/por-pilar/{pilar}", response_model=dict)
async def obtener_por_pilar(pilar: str):
    """
    Obtiene toda la fundamentación legal para un pilar específico.
    """
    pilares_validos = ["razon_negocios", "bee", "materialidad", "trazabilidad"]
    if pilar not in pilares_validos:
        raise HTTPException(status_code=400, detail=f"Pilar inválido. Válidos: {pilares_validos}")

    try:
        import asyncpg
        db_url = os.environ.get("DATABASE_URL")
        if not db_url:
            return {
                "pilar": pilar,
                "items": [item for item in get_demo_legal_base() if pilar in item.get("aplica_a_pilares", [])]
            }

        conn = await asyncpg.connect(db_url)
        rows = await conn.fetch("""
            SELECT id, tipo, titulo, numero_referencia, resumen_ejecutivo
            FROM legal_base
            WHERE es_vigente = TRUE
            AND aplica_a_pilares ? $1
            ORDER BY tipo, orden_display
        """, pilar)
        await conn.close()

        return {
            "pilar": pilar,
            "items": [dict(row) for row in rows]
        }

    except Exception as e:
        logger.error(f"Error obteniendo por pilar: {e}")
        return {
            "pilar": pilar,
            "items": []
        }


@router.get("/por-fase/{fase}", response_model=dict)
async def obtener_por_fase(fase: str):
    """
    Obtiene la fundamentación legal aplicable a una fase específica del flujo.
    """
    fases_validas = ["F0", "F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "F9"]
    if fase not in fases_validas:
        raise HTTPException(status_code=400, detail=f"Fase inválida. Válidas: {fases_validas}")

    try:
        import asyncpg
        db_url = os.environ.get("DATABASE_URL")
        if not db_url:
            return {"fase": fase, "items": []}

        conn = await asyncpg.connect(db_url)
        rows = await conn.fetch("""
            SELECT id, tipo, titulo, numero_referencia, resumen_ejecutivo, aplica_a_pilares
            FROM legal_base
            WHERE es_vigente = TRUE
            AND aplica_a_fases ? $1
            ORDER BY tipo, orden_display
        """, fase)
        await conn.close()

        return {
            "fase": fase,
            "items": [dict(row) for row in rows]
        }

    except Exception as e:
        logger.error(f"Error obteniendo por fase: {e}")
        return {"fase": fase, "items": []}


@router.get("/{id}", response_model=dict)
async def obtener_articulo(id: str):
    """
    Obtiene el detalle completo de un artículo/jurisprudencia.
    """
    try:
        import asyncpg
        db_url = os.environ.get("DATABASE_URL")
        if not db_url:
            demo_items = get_demo_legal_base()
            for item in demo_items:
                if item["id"] == id:
                    return item
            raise HTTPException(status_code=404, detail="Artículo no encontrado")

        conn = await asyncpg.connect(db_url)
        row = await conn.fetchrow("""
            SELECT *
            FROM legal_base
            WHERE id = $1
        """, id)
        await conn.close()

        if not row:
            raise HTTPException(status_code=404, detail="Artículo no encontrado")

        return dict(row)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo artículo: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("", response_model=dict)
async def crear_articulo(data: LegalBaseCreate):
    """
    Crea un nuevo artículo en la base jurídica (solo admin).
    """
    try:
        import asyncpg
        import json
        db_url = os.environ.get("DATABASE_URL")
        if not db_url:
            raise HTTPException(status_code=503, detail="Base de datos no disponible")

        conn = await asyncpg.connect(db_url)
        row = await conn.fetchrow("""
            INSERT INTO legal_base (
                tipo, categoria, titulo, subtitulo, numero_referencia,
                registro_digital, contenido_completo, resumen_ejecutivo,
                aplica_a_tipologias, aplica_a_fases, aplica_a_pilares,
                fecha_publicacion, fecha_vigencia_inicio, fecha_vigencia_fin,
                fuente, keywords
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16
            )
            RETURNING id, created_at
        """,
            data.tipo, data.categoria, data.titulo, data.subtitulo,
            data.numero_referencia, data.registro_digital,
            data.contenido_completo, data.resumen_ejecutivo,
            json.dumps(data.aplica_a_tipologias),
            json.dumps(data.aplica_a_fases),
            json.dumps(data.aplica_a_pilares),
            data.fecha_publicacion, data.fecha_vigencia_inicio,
            data.fecha_vigencia_fin, data.fuente,
            json.dumps(data.keywords)
        )
        await conn.close()

        return {
            "success": True,
            "id": str(row["id"]),
            "message": "Artículo creado exitosamente"
        }

    except Exception as e:
        logger.error(f"Error creando artículo: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{id}", response_model=dict)
async def actualizar_articulo(id: str, data: LegalBaseUpdate):
    """
    Actualiza un artículo existente (solo admin).
    """
    try:
        import asyncpg
        import json
        db_url = os.environ.get("DATABASE_URL")
        if not db_url:
            raise HTTPException(status_code=503, detail="Base de datos no disponible")

        conn = await asyncpg.connect(db_url)

        # Construir update dinámico
        updates = []
        params = []
        param_idx = 1

        if data.titulo is not None:
            updates.append(f"titulo = ${param_idx}")
            params.append(data.titulo)
            param_idx += 1

        if data.contenido_completo is not None:
            updates.append(f"contenido_completo = ${param_idx}")
            params.append(data.contenido_completo)
            param_idx += 1

        if data.resumen_ejecutivo is not None:
            updates.append(f"resumen_ejecutivo = ${param_idx}")
            params.append(data.resumen_ejecutivo)
            param_idx += 1

        if data.es_vigente is not None:
            updates.append(f"es_vigente = ${param_idx}")
            params.append(data.es_vigente)
            param_idx += 1

        if data.aplica_a_pilares is not None:
            updates.append(f"aplica_a_pilares = ${param_idx}")
            params.append(json.dumps(data.aplica_a_pilares))
            param_idx += 1

        if data.keywords is not None:
            updates.append(f"keywords = ${param_idx}")
            params.append(json.dumps(data.keywords))
            param_idx += 1

        updates.append("updated_at = NOW()")

        if not updates:
            return {"success": True, "message": "Nada que actualizar"}

        query = f"UPDATE legal_base SET {', '.join(updates)} WHERE id = ${param_idx}"
        params.append(id)

        await conn.execute(query, *params)
        await conn.close()

        return {"success": True, "message": "Artículo actualizado"}

    except Exception as e:
        logger.error(f"Error actualizando artículo: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# DATOS DE DEMOSTRACIÓN
# =============================================================================

def get_demo_legal_base(tipo=None, categoria=None):
    """Retorna datos de demostración para la base jurídica."""
    items = [
        {
            "id": "demo-5a-cff",
            "tipo": "articulo_cff",
            "categoria": "razon_negocios",
            "titulo": "Artículo 5-A CFF - Razón de Negocios",
            "numero_referencia": "Art. 5-A CFF",
            "contenido_completo": """Los actos jurídicos que carezcan de una razón de negocios y que generen un beneficio fiscal directo o indirecto, tendrán los efectos fiscales que correspondan a los que se habrían realizado para la obtención del beneficio económico razonablemente esperado por el contribuyente.

Se considera que no existe una razón de negocios, cuando el beneficio económico cuantificable razonablemente esperado, sea menor al beneficio fiscal.""",
            "resumen_ejecutivo": "Establece el principio de razón de negocios: los actos jurídicos deben tener un propósito económico real más allá del beneficio fiscal.",
            "aplica_a_pilares": ["razon_negocios", "bee"],
            "aplica_a_fases": ["F0", "F6"],
            "es_vigente": True,
            "keywords": ["razon de negocios", "beneficio economico", "5-A"]
        },
        {
            "id": "demo-27-lisr",
            "tipo": "articulo_lisr",
            "categoria": "razon_negocios",
            "titulo": "Artículo 27 LISR - Requisitos de Deducciones",
            "numero_referencia": "Art. 27 LISR",
            "contenido_completo": """Las deducciones autorizadas en este Título deberán reunir los siguientes requisitos:

I. Ser estrictamente indispensables para los fines de la actividad del contribuyente.""",
            "resumen_ejecutivo": "Los gastos deducibles deben ser ESTRICTAMENTE INDISPENSABLES para la actividad del contribuyente.",
            "aplica_a_pilares": ["razon_negocios"],
            "aplica_a_fases": ["F0", "F6"],
            "es_vigente": True,
            "keywords": ["deducciones", "estricta indispensabilidad", "27 LISR"]
        },
        {
            "id": "demo-69b-cff",
            "tipo": "articulo_cff",
            "categoria": "materialidad",
            "titulo": "Artículo 69-B CFF - Operaciones Inexistentes (EFOS)",
            "numero_referencia": "Art. 69-B CFF",
            "contenido_completo": """Cuando la autoridad fiscal detecte que un contribuyente ha estado emitiendo comprobantes sin contar con los activos, personal, infraestructura o capacidad material, directa o indirectamente, para prestar los servicios o producir, comercializar o entregar los bienes que amparan tales comprobantes...""",
            "resumen_ejecutivo": "Establece el procedimiento para detectar EFOS. Requiere demostrar MATERIALIDAD de las operaciones.",
            "aplica_a_pilares": ["materialidad"],
            "aplica_a_fases": ["F2", "F5", "F6"],
            "es_vigente": True,
            "keywords": ["EFOS", "operaciones inexistentes", "materialidad", "69-B"]
        },
        {
            "id": "demo-nom-151",
            "tipo": "norma_oficial",
            "categoria": "trazabilidad",
            "titulo": "NOM-151-SCFI-2016 - Conservación de Mensajes de Datos",
            "numero_referencia": "NOM-151-SCFI-2016",
            "contenido_completo": """Esta Norma Oficial Mexicana establece los requisitos que deben observarse para la conservación de mensajes de datos y digitalización de documentos, garantizando: Integridad, Autenticidad, Fecha cierta, No repudio.""",
            "resumen_ejecutivo": "Establece requisitos para conservación de documentos digitales con valor probatorio.",
            "aplica_a_pilares": ["trazabilidad"],
            "aplica_a_fases": ["F5", "F6", "F7", "F8"],
            "es_vigente": True,
            "keywords": ["NOM-151", "conservación", "mensajes de datos", "trazabilidad"]
        },
        {
            "id": "demo-scjn-ia",
            "tipo": "jurisprudencia",
            "categoria": "uso_ia",
            "titulo": "Jurisprudencia SCJN - Uso de Inteligencia Artificial",
            "numero_referencia": "II.2o.C. J/1 K (12a.)",
            "registro_digital": "2031639",
            "contenido_completo": """INTELIGENCIA ARTIFICIAL. SU USO COMO HERRAMIENTA EN EL CÁLCULO DE GARANTÍAS EN EL JUICIO DE AMPARO.

El uso de herramientas de inteligencia artificial es válido y recomendable, siempre que se utilice como herramienta auxiliar y no sustituya la función jurisdiccional.

La IA aporta beneficios como:
- Reducción de errores humanos
- Transparencia y trazabilidad
- Consistencia y estandarización
- Eficiencia

El núcleo decisorio permanece siempre en la persona juzgadora.""",
            "resumen_ejecutivo": "La SCJN avala el uso de IA como herramienta auxiliar. Reduce errores, aporta transparencia, sin sustituir decisión humana.",
            "aplica_a_pilares": ["uso_ia"],
            "aplica_a_fases": [],
            "es_vigente": True,
            "keywords": ["inteligencia artificial", "SCJN", "herramienta auxiliar", "validez"]
        }
    ]

    if tipo:
        items = [i for i in items if i["tipo"] == tipo]
    if categoria:
        items = [i for i in items if i["categoria"] == categoria]

    return items
