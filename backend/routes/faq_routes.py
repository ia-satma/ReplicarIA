"""
faq_routes.py - API Routes para FAQ Fiscal/Legal REVISAR.IA

Endpoints para preguntas frecuentes organizadas por categoría:
- Uso de IA
- Materialidad
- Razón de Negocios
- Defensa Fiscal
- Flujo F0-F9

Fecha: 2026-01-31
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
import logging
import os

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/faqs", tags=["FAQ"])


# =============================================================================
# MODELOS PYDANTIC
# =============================================================================

class FAQCreate(BaseModel):
    categoria: str = Field(..., description="Categoría: uso_ia, materialidad, razon_negocios, defensa, flujo")
    subcategoria: Optional[str] = None
    pregunta: str = Field(..., min_length=10)
    respuesta: str = Field(..., min_length=20)
    respuesta_corta: Optional[str] = Field(None, max_length=500)
    referencias_legales: List[str] = []
    keywords: List[str] = []
    es_destacada: bool = False


class FAQUpdate(BaseModel):
    pregunta: Optional[str] = None
    respuesta: Optional[str] = None
    respuesta_corta: Optional[str] = None
    keywords: Optional[List[str]] = None
    es_activa: Optional[bool] = None
    es_destacada: Optional[bool] = None


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.get("", response_model=dict)
async def listar_faqs(
    categoria: Optional[str] = Query(None, description="Filtrar por categoría"),
    busqueda: Optional[str] = Query(None, description="Buscar en pregunta/respuesta"),
    solo_destacadas: bool = Query(False),
    limit: int = Query(50, le=100),
    offset: int = Query(0)
):
    """
    Lista las preguntas frecuentes, opcionalmente filtradas por categoría.
    """
    try:
        import asyncpg
        db_url = os.environ.get("DATABASE_URL")
        if not db_url:
            return {
                "items": get_demo_faqs(categoria, solo_destacadas),
                "total": 10,
                "categorias": get_categorias_faq()
            }

        conn = await asyncpg.connect(db_url)

        # Construir query
        query = """
            SELECT id, categoria, subcategoria, pregunta, respuesta,
                   respuesta_corta, referencias_legales, keywords,
                   es_destacada, visitas, created_at
            FROM faqs
            WHERE es_activa = TRUE
        """
        params = []
        param_idx = 1

        if categoria:
            query += f" AND categoria = ${param_idx}"
            params.append(categoria)
            param_idx += 1

        if solo_destacadas:
            query += " AND es_destacada = TRUE"

        if busqueda:
            query += f" AND (pregunta ILIKE ${param_idx} OR respuesta ILIKE ${param_idx})"
            params.append(f"%{busqueda}%")
            param_idx += 1

        # Count
        count_query = query.replace(
            "SELECT id, categoria, subcategoria, pregunta, respuesta, respuesta_corta, referencias_legales, keywords, es_destacada, visitas, created_at",
            "SELECT COUNT(*)"
        )
        total = await conn.fetchval(count_query, *params)

        # Pagination
        query += f" ORDER BY es_destacada DESC, orden, created_at DESC LIMIT ${param_idx} OFFSET ${param_idx + 1}"
        params.extend([limit, offset])

        rows = await conn.fetch(query, *params)

        # Get categorías con conteo
        cat_rows = await conn.fetch("""
            SELECT categoria, COUNT(*) as count
            FROM faqs WHERE es_activa = TRUE
            GROUP BY categoria
        """)

        await conn.close()

        return {
            "items": [dict(row) for row in rows],
            "total": total,
            "categorias": [{"codigo": r["categoria"], "count": r["count"]} for r in cat_rows]
        }

    except Exception as e:
        logger.error(f"Error listando FAQs: {e}")
        return {
            "items": get_demo_faqs(categoria, solo_destacadas),
            "total": 10,
            "categorias": get_categorias_faq()
        }


@router.get("/categorias", response_model=List[dict])
async def obtener_categorias():
    """
    Obtiene las categorías de FAQ disponibles.
    """
    return get_categorias_faq()


@router.get("/destacadas", response_model=List[dict])
async def obtener_destacadas(limit: int = Query(5, le=20)):
    """
    Obtiene las preguntas más destacadas/frecuentes.
    """
    try:
        import asyncpg
        db_url = os.environ.get("DATABASE_URL")
        if not db_url:
            return [f for f in get_demo_faqs() if f.get("es_destacada")][:limit]

        conn = await asyncpg.connect(db_url)
        rows = await conn.fetch("""
            SELECT id, categoria, pregunta, respuesta_corta, visitas
            FROM faqs
            WHERE es_activa = TRUE AND es_destacada = TRUE
            ORDER BY visitas DESC, orden
            LIMIT $1
        """, limit)
        await conn.close()

        return [dict(row) for row in rows]

    except Exception as e:
        logger.error(f"Error obteniendo destacadas: {e}")
        return [f for f in get_demo_faqs() if f.get("es_destacada")][:limit]


@router.get("/por-categoria/{categoria}", response_model=dict)
async def obtener_por_categoria(categoria: str):
    """
    Obtiene todas las FAQ de una categoría específica.
    """
    categorias_validas = ["uso_ia", "materialidad", "razon_negocios", "defensa", "flujo", "fiscal", "legal"]
    if categoria not in categorias_validas:
        raise HTTPException(status_code=400, detail=f"Categoría inválida. Válidas: {categorias_validas}")

    try:
        import asyncpg
        db_url = os.environ.get("DATABASE_URL")
        if not db_url:
            return {
                "categoria": categoria,
                "nombre": get_categoria_nombre(categoria),
                "items": get_demo_faqs(categoria)
            }

        conn = await asyncpg.connect(db_url)
        rows = await conn.fetch("""
            SELECT id, pregunta, respuesta, respuesta_corta, subcategoria,
                   referencias_legales, es_destacada
            FROM faqs
            WHERE es_activa = TRUE AND categoria = $1
            ORDER BY es_destacada DESC, orden
        """, categoria)
        await conn.close()

        return {
            "categoria": categoria,
            "nombre": get_categoria_nombre(categoria),
            "items": [dict(row) for row in rows]
        }

    except Exception as e:
        logger.error(f"Error obteniendo por categoría: {e}")
        return {
            "categoria": categoria,
            "nombre": get_categoria_nombre(categoria),
            "items": get_demo_faqs(categoria)
        }


@router.get("/{id}", response_model=dict)
async def obtener_faq(id: str):
    """
    Obtiene el detalle de una FAQ específica e incrementa contador de visitas.
    """
    try:
        import asyncpg
        db_url = os.environ.get("DATABASE_URL")
        if not db_url:
            demo = get_demo_faqs()
            for item in demo:
                if item["id"] == id:
                    return item
            raise HTTPException(status_code=404, detail="FAQ no encontrada")

        conn = await asyncpg.connect(db_url)

        # Incrementar visitas
        await conn.execute("""
            UPDATE faqs SET visitas = visitas + 1 WHERE id = $1
        """, id)

        row = await conn.fetchrow("""
            SELECT * FROM faqs WHERE id = $1
        """, id)
        await conn.close()

        if not row:
            raise HTTPException(status_code=404, detail="FAQ no encontrada")

        return dict(row)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo FAQ: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("", response_model=dict)
async def crear_faq(data: FAQCreate):
    """
    Crea una nueva FAQ (solo admin).
    """
    try:
        import asyncpg
        import json
        db_url = os.environ.get("DATABASE_URL")
        if not db_url:
            raise HTTPException(status_code=503, detail="Base de datos no disponible")

        conn = await asyncpg.connect(db_url)

        # Obtener siguiente orden
        max_orden = await conn.fetchval("""
            SELECT COALESCE(MAX(orden), 0) + 1 FROM faqs WHERE categoria = $1
        """, data.categoria)

        row = await conn.fetchrow("""
            INSERT INTO faqs (
                categoria, subcategoria, pregunta, respuesta,
                respuesta_corta, referencias_legales, keywords,
                es_destacada, orden
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            RETURNING id
        """,
            data.categoria, data.subcategoria, data.pregunta,
            data.respuesta, data.respuesta_corta,
            json.dumps(data.referencias_legales),
            json.dumps(data.keywords),
            data.es_destacada, max_orden
        )
        await conn.close()

        return {
            "success": True,
            "id": str(row["id"]),
            "message": "FAQ creada exitosamente"
        }

    except Exception as e:
        logger.error(f"Error creando FAQ: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{id}", response_model=dict)
async def actualizar_faq(id: str, data: FAQUpdate):
    """
    Actualiza una FAQ existente (solo admin).
    """
    try:
        import asyncpg
        import json
        db_url = os.environ.get("DATABASE_URL")
        if not db_url:
            raise HTTPException(status_code=503, detail="Base de datos no disponible")

        conn = await asyncpg.connect(db_url)

        updates = []
        params = []
        param_idx = 1

        if data.pregunta is not None:
            updates.append(f"pregunta = ${param_idx}")
            params.append(data.pregunta)
            param_idx += 1

        if data.respuesta is not None:
            updates.append(f"respuesta = ${param_idx}")
            params.append(data.respuesta)
            param_idx += 1

        if data.respuesta_corta is not None:
            updates.append(f"respuesta_corta = ${param_idx}")
            params.append(data.respuesta_corta)
            param_idx += 1

        if data.es_activa is not None:
            updates.append(f"es_activa = ${param_idx}")
            params.append(data.es_activa)
            param_idx += 1

        if data.es_destacada is not None:
            updates.append(f"es_destacada = ${param_idx}")
            params.append(data.es_destacada)
            param_idx += 1

        updates.append("updated_at = NOW()")

        query = f"UPDATE faqs SET {', '.join(updates)} WHERE id = ${param_idx}"
        params.append(id)

        await conn.execute(query, *params)
        await conn.close()

        return {"success": True, "message": "FAQ actualizada"}

    except Exception as e:
        logger.error(f"Error actualizando FAQ: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{id}", response_model=dict)
async def eliminar_faq(id: str):
    """
    Desactiva una FAQ (soft delete, solo admin).
    """
    try:
        import asyncpg
        db_url = os.environ.get("DATABASE_URL")
        if not db_url:
            raise HTTPException(status_code=503, detail="Base de datos no disponible")

        conn = await asyncpg.connect(db_url)
        await conn.execute("""
            UPDATE faqs SET es_activa = FALSE, updated_at = NOW() WHERE id = $1
        """, id)
        await conn.close()

        return {"success": True, "message": "FAQ desactivada"}

    except Exception as e:
        logger.error(f"Error eliminando FAQ: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# DATOS DE DEMOSTRACIÓN
# =============================================================================

def get_categorias_faq():
    """Retorna las categorías de FAQ."""
    return [
        {"codigo": "uso_ia", "nombre": "Uso de Inteligencia Artificial", "icono": "🤖", "descripcion": "Preguntas sobre cómo la IA apoya el proceso"},
        {"codigo": "materialidad", "nombre": "Materialidad (Art. 69-B)", "icono": "📋", "descripcion": "Evidencia y sustancia de operaciones"},
        {"codigo": "razon_negocios", "nombre": "Razón de Negocios (Art. 5-A)", "icono": "💼", "descripcion": "Justificación económica de los gastos"},
        {"codigo": "defensa", "nombre": "Defensa Fiscal", "icono": "🛡️", "descripcion": "Preparación ante auditorías SAT/TFJA"},
        {"codigo": "flujo", "nombre": "Flujo F0-F9", "icono": "📊", "descripcion": "Fases del proceso de validación"},
        {"codigo": "fiscal", "nombre": "Aspectos Fiscales", "icono": "📑", "descripcion": "Requisitos de deducción y cumplimiento"},
        {"codigo": "legal", "nombre": "Aspectos Legales", "icono": "⚖️", "descripcion": "Contratos, firmas y validez jurídica"}
    ]


def get_categoria_nombre(codigo: str) -> str:
    """Obtiene el nombre de una categoría por su código."""
    for cat in get_categorias_faq():
        if cat["codigo"] == codigo:
            return cat["nombre"]
    return codigo.replace("_", " ").title()


def get_demo_faqs(categoria=None, solo_destacadas=False):
    """Retorna FAQs de demostración."""
    faqs = [
        {
            "id": "faq-ia-1",
            "categoria": "uso_ia",
            "pregunta": "¿Revisar-IA sustituye al abogado fiscal o al contador?",
            "respuesta": """No. La plataforma utiliza inteligencia artificial como herramienta de apoyo, pero las decisiones con consecuencias jurídicas y fiscales (celebrar contratos, autorizar pagos, determinar deducciones, definir postura ante SAT/TFJA) las toman siempre personas: Dirección, Fiscal, Legal, Finanzas.

Revisar-IA se encarga de:
• Aplicar checklists objetivos (5-A CFF, 27 LISR, 69-B CFF, NOM-151)
• Calcular risk_scores reproducibles
• Organizar Defense Files
• Señalar brechas (falta contrato, falta evidencia, CFDI genérico, riesgo EFOS, etc.)

La función de Fiscal/Legal no desaparece; se fortalece con mejor información y mejor documentación.""",
            "respuesta_corta": "No. La IA auxilia, pero las decisiones legales/fiscales siempre las toman personas.",
            "es_destacada": True,
            "visitas": 1250
        },
        {
            "id": "faq-ia-2",
            "categoria": "uso_ia",
            "pregunta": "¿El SAT puede rechazar un gasto 'porque lo revisó una IA'?",
            "respuesta": """No hay base legal para eso. El SAT puede rechazar deducciones si:
• No hubo servicio real
• No hay contrato/SOW adecuado
• No hay entregables ni evidencia de ejecución
• El CFDI es genérico o no corresponde a la realidad
• No hay razón de negocios ni estricta indispensabilidad
• Se detecta que el proveedor es EFOS (69-B CFF) o la operación es simulada

Lo que la autoridad NO hace es calificar el gasto por el software utilizado, sino por la realidad de los hechos y la calidad de las pruebas.

Revisar-IA está diseñada justamente para detectar esos problemas ANTES de que ocurran.""",
            "respuesta_corta": "No. El SAT evalúa hechos y pruebas, no el software usado para documentarlos.",
            "es_destacada": True,
            "visitas": 980
        },
        {
            "id": "faq-ia-3",
            "categoria": "uso_ia",
            "pregunta": "¿Qué aval jurídico tiene el uso de IA?",
            "respuesta": """Hay dos planos importantes:

1. La ley fiscal mexicana NO PROHÍBE el uso de sistemas automatizados o IA para control interno, checklists, cálculos o preparación de expedientes.

2. Existe jurisprudencia federal (Registro 2031639, Tesis II.2o.C. J/1 K) que reconoce que la inteligencia artificial puede utilizarse válidamente en procesos judiciales para tareas auxiliares, siempre que no sustituya la función de la persona juzgadora.

La jurisprudencia destaca que la IA:
• Reduce errores humanos en cálculos complejos
• Aporta transparencia y trazabilidad
• Genera consistencia y estandarización
• Mejora la eficiencia

Revisar-IA aplica exactamente esta lógica: la IA no dicta sentencias ni firma contratos; se usa para calcular, organizar y documentar.""",
            "respuesta_corta": "La ley no lo prohíbe y existe jurisprudencia SCJN que avala el uso de IA como herramienta auxiliar.",
            "es_destacada": True,
            "visitas": 850
        },
        {
            "id": "faq-mat-1",
            "categoria": "materialidad",
            "pregunta": "¿Qué hace Revisar-IA respecto de la materialidad (Art. 69-B CFF)?",
            "respuesta": """La plataforma obliga a construir una Matriz de Materialidad por proyecto, donde cada HECHO (contratación, ejecución, entrega, pago) se liga a EVIDENCIAS concretas:
• Contrato / SOW
• Minutas de seguimiento
• Borradores y versiones intermedias
• Informes y modelos
• Logs de actividad
• CFDI específico
• Transferencias bancarias

Además:
• Mide el porcentaje de completitud de materialidad
• No permite declarar F6 como completada sin umbral mínimo de evidencia
• Bloquea avance si faltan documentos críticos

El objetivo es obligar internamente a que no se considere "cerrado" un servicio sin soporte suficiente.""",
            "respuesta_corta": "Construye matriz de materialidad con evidencias específicas y bloquea avance sin documentación suficiente.",
            "es_destacada": True,
            "visitas": 720
        },
        {
            "id": "faq-mat-2",
            "categoria": "materialidad",
            "pregunta": "¿Qué pasa con servicios intra-grupo y management fees?",
            "respuesta": """En esas tipologías (INTRAGRUPO_MANAGEMENT_FEE), Revisar-IA:

• Marca riesgo inherente MUY ALTO
• Exige como mínimos:
  - Estudio de precios de transferencia vigente
  - Contrato con desglose de servicios
  - Base clara de asignación del fee
  - Reportes periódicos de servicios prestados
  - Evidencia de capacidad operativa del prestador

En estas operaciones, la revisión humana de Fiscal y Legal es SIEMPRE obligatoria, sin depender solo del análisis automatizado.""",
            "respuesta_corta": "Riesgo MUY ALTO. Requiere estudio PT, contratos detallados, reportes periódicos y revisión humana obligatoria.",
            "es_destacada": True,
            "visitas": 650
        },
        {
            "id": "faq-def-1",
            "categoria": "defensa",
            "pregunta": "¿Revisar-IA garantiza que nunca habrá ajustes del SAT?",
            "respuesta": """No. Ninguna herramienta puede garantizar eso.

Lo que hace es:
1. Reducir la probabilidad de ajustes por errores evitables:
   • Falta de contrato
   • CFDI genéricos
   • Ausencia de entregables
   • Inexistencia de BEE
   • Mala documentación de servicios intra-grupo o marketing

2. Si aún así hubiera un ajuste, te permite tener:
   • Un Defense File ordenado y completo
   • Mejores argumentos de defensa
   • Mayor claridad de qué se hizo bien o mal
   • Base para ajustar políticas futuras""",
            "respuesta_corta": "No garantiza cero ajustes, pero reduce riesgos evitables y mejora capacidad de defensa.",
            "es_destacada": False,
            "visitas": 420
        },
        {
            "id": "faq-rn-1",
            "categoria": "razon_negocios",
            "pregunta": "¿Qué hace Revisar-IA en materia de razón de negocios (Art. 5-A CFF)?",
            "respuesta": """La plataforma exige que cada servicio relevante tenga:

1. Un SIB/BEE (Service Initiation Brief) donde se explique:
   • El objetivo de negocio del servicio
   • El tipo de beneficio económico esperado (ingresos, ahorros, mitigación de riesgo, cumplimiento)
   • El horizonte de tiempo
   • Los KPIs con los que se evaluará el resultado

2. Una vinculación explícita con:
   • Los pilares estratégicos de la empresa
   • Los OKRs del año

Los agentes Fiscal (A3) y Estrategia (A1) utilizan esa información para determinar si hay una razón de negocios real, si el BEE es razonable, y que no se trate solo de una operación "para deducir".""",
            "respuesta_corta": "Exige documentar objetivo, BEE, horizonte y KPIs, vinculándolos con estrategia empresarial.",
            "es_destacada": False,
            "visitas": 380
        },
        {
            "id": "faq-flujo-1",
            "categoria": "flujo",
            "pregunta": "¿Qué son los 'candados' F2, F6 y F8?",
            "respuesta": """Los candados son puntos de control obligatorio donde se requiere validación humana antes de continuar:

• **Candado F2 (Inicio)**: Valida que exista:
  - Ficha de proyecto completa
  - Justificación de razón de negocios
  - Presupuesto aprobado
  - Contrato/SOW base

• **Candado F6 (Visto Bueno Fiscal/Legal)**: Valida que exista:
  - Matriz de materialidad completa (>70%)
  - Entregables recibidos y aceptados
  - VBC Fiscal aprobado
  - VBC Legal aprobado
  - Sin alertas de EFOS pendientes

• **Candado F8 (Pago)**: Valida que exista:
  - 3-way match (Contrato = CFDI = Pago)
  - CFDI específico (no genérico)
  - Auditoría interna completada
  - Todas las aprobaciones previas

Sin estos candados liberados, el sistema no permite avanzar a la siguiente fase.""",
            "respuesta_corta": "Puntos de control obligatorio (F2=inicio, F6=fiscal/legal, F8=pago) que requieren validación humana.",
            "es_destacada": False,
            "visitas": 310
        }
    ]

    if categoria:
        faqs = [f for f in faqs if f["categoria"] == categoria]
    if solo_destacadas:
        faqs = [f for f in faqs if f.get("es_destacada")]

    return faqs
