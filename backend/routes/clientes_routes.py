"""
Rutas de API para gestión de Clientes con soporte multi-tenant.
- Usuarios tenant: solo pueden ver/gestionar clientes de su empresa
- Administradores: pueden ver/gestionar clientes de cualquier empresa
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, List
import os
import logging
from jose import jwt, exceptions as jose_exceptions

from models.cliente import (
    Cliente, ClienteCreate, ClienteUpdate, ClienteResponse,
    TipoCliente, EstadoCliente
)
from services.cliente_service import cliente_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/clientes", tags=["clientes"])

security = HTTPBearer(auto_error=False)
SECRET_KEY = os.getenv("SESSION_SECRET") or os.getenv("JWT_SECRET_KEY", "dev-secret-key")
ALGORITHM = "HS256"


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Obtener usuario actual del token JWT"""
    if not credentials:
        raise HTTPException(status_code=401, detail="Autenticación requerida")
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jose_exceptions.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except jose_exceptions.JWTError:
        raise HTTPException(status_code=401, detail="Token inválido")


def get_empresa_id_from_user(user: dict) -> str:
    """Extraer empresa_id del usuario autenticado"""
    empresa_id = user.get("empresa_id") or user.get("company_id")
    if not empresa_id:
        raise HTTPException(status_code=403, detail="Usuario sin empresa asignada")
    return empresa_id


def is_admin(user: dict) -> bool:
    """Verificar si el usuario es administrador de plataforma"""
    role = user.get("role", "").lower()
    return role in ["admin", "superadmin", "platform_admin"]


@router.get("", response_model=List[ClienteResponse])
async def list_clientes(
    search: Optional[str] = Query(None, description="Buscar por razón social, RFC o nombre comercial"),
    status: Optional[str] = Query(None, description="Filtrar por estado"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    user: dict = Depends(get_current_user)
):
    """
    Listar clientes del tenant actual.
    Los usuarios solo ven clientes de su empresa.
    """
    empresa_id = get_empresa_id_from_user(user)
    
    clientes = await cliente_service.list_clientes(
        empresa_id=empresa_id,
        status=status,
        search=search,
        skip=skip,
        limit=limit
    )
    
    return clientes


@router.get("/count")
async def count_clientes(
    status: Optional[str] = Query(None),
    user: dict = Depends(get_current_user)
):
    """Contar clientes del tenant actual"""
    empresa_id = get_empresa_id_from_user(user)
    count = await cliente_service.count_clientes(empresa_id=empresa_id, status=status)
    return {"count": count, "empresa_id": empresa_id}


@router.get("/{cliente_id}")
async def get_cliente(
    cliente_id: str,
    user: dict = Depends(get_current_user)
):
    """Obtener un cliente específico (solo de la empresa del usuario)"""
    empresa_id = get_empresa_id_from_user(user)
    
    cliente = await cliente_service.get_cliente(cliente_id, empresa_id=empresa_id)
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    
    return cliente


@router.post("")
async def create_cliente(
    cliente_data: ClienteCreate,
    user: dict = Depends(get_current_user)
):
    """
    Crear un nuevo cliente para la empresa del usuario.
    """
    empresa_id = get_empresa_id_from_user(user)
    user_id = user.get("user_id") or user.get("sub")
    
    cliente = await cliente_service.create_cliente(
        cliente_data=cliente_data.dict(exclude_none=True),
        empresa_id=empresa_id,
        creado_por=user_id
    )
    
    return {
        "success": True,
        "cliente": cliente,
        "message": "Cliente creado exitosamente"
    }


@router.put("/{cliente_id}")
async def update_cliente(
    cliente_id: str,
    update_data: ClienteUpdate,
    user: dict = Depends(get_current_user)
):
    """Actualizar un cliente de la empresa del usuario"""
    empresa_id = get_empresa_id_from_user(user)
    
    cliente = await cliente_service.update_cliente(
        cliente_id=cliente_id,
        update_data=update_data.dict(exclude_none=True),
        empresa_id=empresa_id
    )
    
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    
    return {
        "success": True,
        "cliente": cliente,
        "message": "Cliente actualizado"
    }


@router.delete("/{cliente_id}")
async def delete_cliente(
    cliente_id: str,
    user: dict = Depends(get_current_user)
):
    """Eliminar (desactivar) un cliente"""
    empresa_id = get_empresa_id_from_user(user)
    
    success = await cliente_service.delete_cliente(cliente_id, empresa_id=empresa_id)
    if not success:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    
    return {"success": True, "message": "Cliente desactivado"}
