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
import anthropic

from models.empresa import (
    Empresa, EmpresaCreate, EmpresaUpdate,
    PilarEstrategico, OKR, ConfiguracionTipologia
)
from services.empresa_service import empresa_service

logger = logging.getLogger(__name__)

# Initialize Anthropic client
anthropic_client = None
ai_api_key = os.environ.get('AI_INTEGRATIONS_ANTHROPIC_API_KEY')
ai_base_url = os.environ.get('AI_INTEGRATIONS_ANTHROPIC_BASE_URL')
if ai_api_key and ai_base_url:
    anthropic_client = anthropic.Anthropic(api_key=ai_api_key, base_url=ai_base_url)
elif os.environ.get('ANTHROPIC_API_KEY'):
    anthropic_client = anthropic.Anthropic(api_key=os.environ.get('ANTHROPIC_API_KEY'))

router = APIRouter(prefix="/empresas", tags=["empresas"])

security = HTTPBearer(auto_error=False)


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if not credentials:
        raise HTTPException(status_code=401, detail="No autorizado - Token requerido")
    
    from jose import jwt, exceptions as jose_exceptions
    SECRET_KEY = os.getenv("SESSION_SECRET") or os.getenv("JWT_SECRET_KEY", "dev-secret-key-change-in-production")
    
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=["HS256"])
        return payload
    except jose_exceptions.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except jose_exceptions.JWTError:
        raise HTTPException(status_code=401, detail="Token inválido")


class VisionMisionRequest(BaseModel):
    vision: Optional[str] = None
    mision: Optional[str] = None


class PilaresRequest(BaseModel):
    pilares: List[PilarEstrategico]


class OKRsRequest(BaseModel):
    okrs: List[OKR]


class TipologiasRequest(BaseModel):
    tipologias: List[ConfiguracionTipologia]


@router.post("/", response_model=Empresa)
async def crear_empresa(data: EmpresaCreate):
    try:
        empresa = await empresa_service.crear_empresa(data)
        return empresa
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating empresa: {e}")
        raise HTTPException(status_code=500, detail="Error interno al crear empresa")


@router.get("/", response_model=List[Empresa])
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


@router.post("/autofill-ia")
async def autofill_empresa_con_ia(data: AutofillRequest):
    """
    Auto-rellena los campos de perfil de empresa usando IA.
    Genera vision, mision, valores y sugerencias basadas en el nombre/RFC.
    """
    if not anthropic_client:
        raise HTTPException(
            status_code=503, 
            detail="Servicio de IA no disponible. Configure las credenciales de Anthropic."
        )
    
    try:
        industria_texto = data.industria.replace("_", " ") if data.industria else "no especificada"
        
        prompt = f"""Eres un experto en desarrollo empresarial y estrategia corporativa en Mexico.
Genera informacion de perfil empresarial para la siguiente empresa mexicana:

DATOS DE LA EMPRESA:
- Nombre Comercial: {data.nombre_comercial}
- Razon Social: {data.razon_social or 'No especificada'}
- RFC: {data.rfc or 'No especificado'}
- Industria: {industria_texto}

INSTRUCCIONES:
Genera contenido profesional, realista y especifico para esta empresa mexicana.
La vision y mision deben ser concisas (1-2 oraciones cada una).
Los valores deben reflejar la industria y cultura empresarial mexicana.

Responde UNICAMENTE en este formato JSON exacto, sin explicaciones adicionales:
{{
    "vision": "La vision de la empresa en 1-2 oraciones...",
    "mision": "La mision de la empresa en 1-2 oraciones...",
    "valores": ["Valor 1", "Valor 2", "Valor 3", "Valor 4", "Valor 5"],
    "modelo_negocio": "Descripcion breve del modelo de negocio sugerido...",
    "mercados_objetivo": ["Mercado 1", "Mercado 2", "Mercado 3"],
    "ventajas_competitivas": ["Ventaja 1", "Ventaja 2", "Ventaja 3"]
}}"""

        response = anthropic_client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        )
        
        response_text = response.content[0].text.strip()
        
        # Clean up response if wrapped in markdown code blocks
        if response_text.startswith("```"):
            lines = response_text.split("\n")
            response_text = "\n".join(lines[1:-1])
        
        result = json.loads(response_text)
        
        return {
            "success": True,
            "data": result,
            "message": "Perfil generado exitosamente con IA"
        }
        
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing AI response: {e}")
        raise HTTPException(status_code=500, detail="Error al procesar respuesta de IA")
    except Exception as e:
        logger.error(f"Error in autofill: {e}")
        raise HTTPException(status_code=500, detail=f"Error al generar perfil: {str(e)}")
