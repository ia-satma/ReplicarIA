"""
API Routes para gestión de Empresas/Tenants (Multi-tenant).
"""
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import List, Optional
import os
import logging
import json

from models.empresa import (
    Empresa, EmpresaCreate, EmpresaUpdate,
    PilarEstrategico, OKR, ConfiguracionTipologia
)
from services.empresa_service import empresa_service
from services.auth_service import get_secret_key

logger = logging.getLogger(__name__)

# AI Provider - Try Anthropic first, then OpenAI
AI_PROVIDER = None
chat_completion_sync = None
AI_AVAILABLE = False

# Try Anthropic first
try:
    from services.anthropic_provider import chat_completion_sync as anthropic_chat, is_configured as anthropic_configured
    if anthropic_configured():
        AI_PROVIDER = "anthropic"
        chat_completion_sync = anthropic_chat
        AI_AVAILABLE = True
        logger.info("Empresas: Using Anthropic Claude")
except ImportError:
    pass

# Fallback to OpenAI
if not AI_AVAILABLE:
    try:
        from services.openai_provider import chat_completion_sync as openai_chat, is_configured as openai_configured
        if openai_configured():
            AI_PROVIDER = "openai"
            chat_completion_sync = openai_chat
            AI_AVAILABLE = True
            logger.info("Empresas: Using OpenAI GPT")
    except ImportError:
        pass

# Legacy compatibility
OPENAI_AVAILABLE = AI_AVAILABLE

# Model to use based on provider
AI_MODEL = "claude-sonnet-4-20250514" if AI_PROVIDER == "anthropic" else "gpt-4o"

# Deep Research Service for intelligent autofill
try:
    from services.deep_research_service import deep_research_service
    DEEP_RESEARCH_AVAILABLE = True
except ImportError:
    deep_research_service = None
    DEEP_RESEARCH_AVAILABLE = False

router = APIRouter(prefix="/empresas", tags=["empresas"])

security = HTTPBearer(auto_error=False)


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if not credentials:
        raise HTTPException(status_code=401, detail="No autorizado - Token requerido")

    from jose import jwt, exceptions as jose_exceptions

    try:
        SECRET_KEY = get_secret_key()
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=["HS256"])
        return payload
    except jose_exceptions.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except jose_exceptions.JWTError as e:
        logger.error(f"Error verificando token: {e}")
        raise HTTPException(status_code=401, detail="Token inválido")
    except RuntimeError as e:
        logger.error(f"Error de configuración: {e}")
        raise HTTPException(status_code=500, detail="Error de configuración del servidor")


class VisionMisionRequest(BaseModel):
    vision: Optional[str] = None
    mision: Optional[str] = None


class PilaresRequest(BaseModel):
    pilares: List[PilarEstrategico]


class OKRsRequest(BaseModel):
    okrs: List[OKR]


class TipologiasRequest(BaseModel):
    tipologias: List[ConfiguracionTipologia]


@router.post("", response_model=Empresa)
async def crear_empresa(data: EmpresaCreate):
    try:
        empresa = await empresa_service.crear_empresa(data)
        return empresa
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating empresa: {e}")
        raise HTTPException(status_code=500, detail="Error interno al crear empresa")


@router.get("", response_model=List[Empresa])
async def listar_empresas(only_active: bool = True):
    try:
        empresas = await empresa_service.get_all_empresas(only_active)
        return empresas
    except Exception as e:
        logger.error(f"Error listing empresas: {e}")
        raise HTTPException(status_code=500, detail="Error interno al listar empresas")


@router.get("/{empresa_id}", response_model=Empresa)
async def obtener_empresa(empresa_id: str):
    empresa = await empresa_service.get_empresa(empresa_id)
    if not empresa:
        raise HTTPException(status_code=404, detail=f"Empresa {empresa_id} no encontrada")
    return empresa


@router.patch("/{empresa_id}", response_model=Empresa)
async def actualizar_empresa(empresa_id: str, data: EmpresaUpdate):
    try:
        empresa = await empresa_service.update_empresa(empresa_id, data)
        if not empresa:
            raise HTTPException(status_code=404, detail=f"Empresa {empresa_id} no encontrada")
        return empresa
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating empresa: {e}")
        raise HTTPException(status_code=500, detail="Error interno al actualizar empresa")


@router.put("/{empresa_id}/vision-mision", response_model=Empresa)
async def actualizar_vision_mision(empresa_id: str, data: VisionMisionRequest):
    try:
        empresa = await empresa_service.actualizar_vision_mision(
            empresa_id, 
            data.vision, 
            data.mision
        )
        if not empresa:
            raise HTTPException(status_code=404, detail=f"Empresa {empresa_id} no encontrada")
        return empresa
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating vision/mision: {e}")
        raise HTTPException(status_code=500, detail="Error interno al actualizar visión/misión")


@router.put("/{empresa_id}/pilares", response_model=Empresa)
async def actualizar_pilares(empresa_id: str, data: PilaresRequest):
    try:
        empresa = await empresa_service.actualizar_pilares(empresa_id, data.pilares)
        if not empresa:
            raise HTTPException(status_code=404, detail=f"Empresa {empresa_id} no encontrada")
        return empresa
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating pilares: {e}")
        raise HTTPException(status_code=500, detail="Error interno al actualizar pilares")


@router.put("/{empresa_id}/okrs", response_model=Empresa)
async def actualizar_okrs(empresa_id: str, data: OKRsRequest):
    try:
        empresa = await empresa_service.actualizar_okrs(empresa_id, data.okrs)
        if not empresa:
            raise HTTPException(status_code=404, detail=f"Empresa {empresa_id} no encontrada")
        return empresa
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating OKRs: {e}")
        raise HTTPException(status_code=500, detail="Error interno al actualizar OKRs")


@router.get("/{empresa_id}/tipologias")
async def obtener_tipologias(empresa_id: str):
    try:
        tipologias = await empresa_service.get_tipologias_con_estado(empresa_id)
        return {"empresa_id": empresa_id, "tipologias": tipologias}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting tipologias: {e}")
        raise HTTPException(status_code=500, detail="Error interno al obtener tipologías")


@router.put("/{empresa_id}/tipologias", response_model=Empresa)
async def configurar_tipologias(empresa_id: str, data: TipologiasRequest):
    try:
        tipologias_dict = [t.model_dump() for t in data.tipologias]
        empresa = await empresa_service.configurar_tipologias(empresa_id, tipologias_dict)
        if not empresa:
            raise HTTPException(status_code=404, detail=f"Empresa {empresa_id} no encontrada")
        return empresa
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error configuring tipologias: {e}")
        raise HTTPException(status_code=500, detail="Error interno al configurar tipologías")


@router.delete("/{empresa_id}")
async def desactivar_empresa(empresa_id: str):
    try:
        empresa = await empresa_service.desactivar_empresa(empresa_id)
        if not empresa:
            raise HTTPException(status_code=404, detail=f"Empresa {empresa_id} no encontrada")
        return {"message": f"Empresa {empresa_id} desactivada", "empresa": empresa}
    except Exception as e:
        logger.error(f"Error deactivating empresa: {e}")
        raise HTTPException(status_code=500, detail="Error interno al desactivar empresa")


class AutofillRequest(BaseModel):
    nombre_comercial: str
    razon_social: Optional[str] = None
    rfc: Optional[str] = None
    industria: Optional[str] = None
    sitio_web: Optional[str] = None  # URL para deep research


# Templates por industria para fallback sin IA
TEMPLATES_POR_INDUSTRIA = {
    "tecnologia": {
        "vision": "Ser la empresa tecnologica lider en innovacion y transformacion digital en Mexico, reconocida por la calidad y el impacto de nuestras soluciones.",
        "mision": "Desarrollar soluciones tecnologicas que impulsen el crecimiento y la competitividad de nuestros clientes, generando valor a traves de la innovacion constante."
    },
    "servicios_profesionales": {
        "vision": "Ser el referente en servicios profesionales de excelencia, reconocidos por nuestra integridad, conocimiento y compromiso con el exito de nuestros clientes.",
        "mision": "Brindar servicios profesionales de alta calidad que superen las expectativas de nuestros clientes, contribuyendo a su crecimiento y desarrollo sostenible."
    },
    "manufactura": {
        "vision": "Ser lider en manufactura de clase mundial, reconocidos por la calidad, eficiencia y sustentabilidad de nuestros procesos productivos.",
        "mision": "Fabricar productos de la mas alta calidad que satisfagan las necesidades de nuestros clientes, optimizando recursos y cuidando el medio ambiente."
    },
    "comercio": {
        "vision": "Ser la empresa comercial preferida por nuestros clientes, destacando por nuestra variedad, servicio y precios competitivos.",
        "mision": "Ofrecer productos y servicios comerciales que cubran las necesidades de nuestros clientes, brindando una experiencia de compra excepcional."
    },
    "construccion": {
        "vision": "Ser la constructora lider en el mercado, reconocida por la calidad, seguridad e innovacion en cada uno de nuestros proyectos.",
        "mision": "Construir espacios que mejoren la calidad de vida de las personas, cumpliendo con los mas altos estandares de calidad y seguridad."
    },
    "salud": {
        "vision": "Ser referente en servicios de salud de excelencia, comprometidos con el bienestar integral de nuestros pacientes y comunidad.",
        "mision": "Brindar servicios de salud de calidad con calidez humana, utilizando tecnologia de vanguardia para el cuidado de nuestros pacientes."
    },
    "educacion": {
        "vision": "Ser institucion educativa lider, formando profesionales competentes y comprometidos con el desarrollo de Mexico.",
        "mision": "Formar personas integras con conocimientos, habilidades y valores que contribuyan al progreso de la sociedad."
    },
    "finanzas": {
        "vision": "Ser la institucion financiera mas confiable y solida, reconocida por nuestra integridad y servicios innovadores.",
        "mision": "Ofrecer soluciones financieras que impulsen el crecimiento de nuestros clientes, con transparencia, seguridad y servicio personalizado."
    },
    "inmobiliario": {
        "vision": "Ser la empresa inmobiliaria lider en desarrollo de proyectos que transformen comunidades y generen valor duradero.",
        "mision": "Desarrollar proyectos inmobiliarios que superen las expectativas de nuestros clientes, creando espacios que mejoren su calidad de vida."
    },
    "default": {
        "vision": "Ser la empresa lider en nuestro sector, reconocida por la excelencia, innovacion y compromiso con nuestros clientes y colaboradores.",
        "mision": "Ofrecer productos y servicios de la mas alta calidad que generen valor para nuestros clientes, colaboradores y la comunidad."
    }
}


@router.post("/autofill-ia")
async def autofill_empresa_con_ia(
    data: AutofillRequest,
    user: dict = Depends(get_current_user)  # REQUIRE AUTH to prevent bot abuse
):
    """
    Auto-rellena los campos de perfil de empresa usando Deep Research + IA.
    Investiga la empresa en internet y genera vision, mision, y datos adicionales.
    REQUIERE AUTENTICACIÓN para prevenir abuso de bots.
    """
    try:
        industria_key = data.industria or "default"
        industria_texto = data.industria.replace("_", " ") if data.industria else "general"

        # 1. Intentar Deep Research primero (más completo)
        if DEEP_RESEARCH_AVAILABLE and deep_research_service:
            try:
                logger.info(f"Iniciando Deep Research para: {data.nombre_comercial}")
                resultado = await deep_research_service.investigar_empresa(
                    nombre=data.nombre_comercial,
                    rfc=data.rfc,
                    sitio_web=data.sitio_web
                )

                if resultado and resultado.get("data"):
                    research_data = resultado["data"]
                    field_confidence = resultado.get("field_confidence", {})

                    # Generar vision/mision con IA basada en datos investigados
                    if OPENAI_AVAILABLE:
                        try:
                            context_info = f"""
Nombre: {research_data.get('nombre') or data.nombre_comercial}
Razon Social: {research_data.get('razon_social') or data.razon_social or 'No disponible'}
RFC: {research_data.get('rfc') or data.rfc or 'No disponible'}
Giro/Actividad: {research_data.get('giro') or research_data.get('actividad_economica') or industria_texto}
Direccion: {research_data.get('direccion') or 'No disponible'}
Sitio Web: {data.sitio_web or 'No disponible'}
"""
                            prompt = f"""Eres un experto en desarrollo empresarial en Mexico.
Con base en los siguientes datos investigados de una empresa real, genera su vision y mision:

{context_info}

Genera contenido profesional, especifico y realista para ESTA empresa en particular.
No uses frases genericas. Personaliza basandote en su giro y actividad.

Responde UNICAMENTE en formato JSON:
{{
    "vision": "Vision especifica para esta empresa (1-2 oraciones)...",
    "mision": "Mision especifica para esta empresa (1-2 oraciones)..."
}}"""

                            response_text = chat_completion_sync(
                                messages=[{"role": "user", "content": prompt}],
                                model=AI_MODEL,
                                max_tokens=512
                            ).strip()

                            if response_text.startswith("```"):
                                lines = response_text.split("\n")
                                response_text = "\n".join(lines[1:-1])

                            ai_result = json.loads(response_text)
                            # Check if AI returned an error
                            if "error" not in ai_result:
                                research_data["vision"] = ai_result.get("vision")
                                research_data["mision"] = ai_result.get("mision")
                            else:
                                logger.warning(f"AI returned error: {ai_result.get('error')}")
                        except Exception as ai_err:
                            logger.warning(f"Error generando vision/mision con IA: {ai_err}")

                    # If vision/mision are still empty, use templates
                    if not research_data.get("vision") or not research_data.get("mision"):
                        template = TEMPLATES_POR_INDUSTRIA.get(industria_key, TEMPLATES_POR_INDUSTRIA["default"])
                        if not research_data.get("vision"):
                            research_data["vision"] = template["vision"].replace("Ser la empresa", f"Ser {data.nombre_comercial} como la empresa")
                        if not research_data.get("mision"):
                            research_data["mision"] = template["mision"]

                    return {
                        "success": True,
                        "data": {
                            "vision": research_data.get("vision"),
                            "mision": research_data.get("mision"),
                            "razon_social": research_data.get("razon_social"),
                            "rfc": research_data.get("rfc"),
                            "direccion": research_data.get("direccion"),
                            "giro": research_data.get("giro") or research_data.get("actividad_economica"),
                            "regimen_fiscal": research_data.get("regimen_fiscal"),
                            "sitio_web": research_data.get("sitio_web") or data.sitio_web,
                            "telefono": research_data.get("telefono"),
                            "email": research_data.get("email")
                        },
                        "field_confidence": field_confidence,
                        "message": "Datos investigados con Deep Research + IA",
                        "source": "deep_research"
                    }

            except Exception as e:
                logger.warning(f"Error en Deep Research, intentando con IA basica: {e}")

        # 2. Fallback: IA basica sin investigacion
        if OPENAI_AVAILABLE:
            try:
                prompt = f"""Eres un experto en desarrollo empresarial y estrategia corporativa en Mexico.
Genera informacion de perfil empresarial para la siguiente empresa mexicana:

DATOS DE LA EMPRESA:
- Nombre Comercial: {data.nombre_comercial}
- Razon Social: {data.razon_social or 'No especificada'}
- RFC: {data.rfc or 'No especificado'}
- Industria: {industria_texto}
- Sitio Web: {data.sitio_web or 'No especificado'}

INSTRUCCIONES:
Genera contenido profesional, realista y especifico para esta empresa mexicana.
La vision y mision deben ser concisas (1-2 oraciones cada una).

Responde UNICAMENTE en este formato JSON exacto:
{{
    "vision": "La vision de la empresa en 1-2 oraciones...",
    "mision": "La mision de la empresa en 1-2 oraciones..."
}}"""

                response_text = chat_completion_sync(
                    messages=[{"role": "user", "content": prompt}],
                    model=AI_MODEL,
                    max_tokens=512
                ).strip()

                if response_text.startswith("```"):
                    lines = response_text.split("\n")
                    response_text = "\n".join(lines[1:-1])

                result = json.loads(response_text)

                # Check if AI returned an error
                if "error" in result:
                    logger.warning(f"AI returned error: {result.get('error')}")
                    raise ValueError(f"AI error: {result.get('error')}")

                return {
                    "success": True,
                    "data": result,
                    "message": "Perfil generado con IA",
                    "source": "ai"
                }

            except Exception as e:
                logger.warning(f"Error con IA, usando template: {e}")

        # 3. Fallback final: templates predefinidos
        template = TEMPLATES_POR_INDUSTRIA.get(industria_key, TEMPLATES_POR_INDUSTRIA["default"])
        vision = template["vision"].replace("Ser la empresa", f"Ser {data.nombre_comercial} como la empresa")
        mision = template["mision"]

        return {
            "success": True,
            "data": {
                "vision": vision,
                "mision": mision
            },
            "message": "Perfil generado con plantilla de industria",
            "source": "template"
        }

    except Exception as outer_error:
        # Ultimate fallback - if everything fails, return a basic template
        logger.error(f"Error crítico en autofill-ia: {outer_error}")
        default_template = TEMPLATES_POR_INDUSTRIA["default"]
        return {
            "success": True,
            "data": {
                "vision": default_template["vision"].replace("Ser la empresa", f"Ser {data.nombre_comercial} como la empresa"),
                "mision": default_template["mision"]
            },
            "message": "Perfil generado con plantilla por defecto",
            "source": "fallback_template"
        }
