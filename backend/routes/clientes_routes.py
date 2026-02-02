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
from services.auth_service import get_secret_key

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/clientes", tags=["clientes"])

security = HTTPBearer(auto_error=False)
ALGORITHM = "HS256"


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Obtener usuario actual del token JWT"""
    if not credentials:
        raise HTTPException(status_code=401, detail="Autenticación requerida")
    try:
        SECRET_KEY = get_secret_key()
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
    try:
        empresa_id = get_empresa_id_from_user(user)

        # Null checks
        if not empresa_id or not empresa_id.strip():
            raise HTTPException(status_code=403, detail="No empresa assigned to user")

        clientes = await cliente_service.list_clientes(
            empresa_id=empresa_id,
            status=status,
            search=search,
            skip=skip,
            limit=limit
        )

        return clientes or []
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing clientes for empresa {user.get('empresa_id')}: {e}")
        raise HTTPException(status_code=503, detail="Unable to retrieve clients. Service temporarily unavailable.")


@router.get("/count")
async def count_clientes(
    status: Optional[str] = Query(None),
    user: dict = Depends(get_current_user)
):
    """Contar clientes del tenant actual"""
    try:
        empresa_id = get_empresa_id_from_user(user)

        # Null check
        if not empresa_id or not empresa_id.strip():
            raise HTTPException(status_code=403, detail="No empresa assigned to user")

        count = await cliente_service.count_clientes(empresa_id=empresa_id, status=status)
        return {"count": count if count else 0, "empresa_id": empresa_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error counting clientes for empresa {user.get('empresa_id')}: {e}")
        raise HTTPException(status_code=503, detail="Unable to count clients. Service temporarily unavailable.")


@router.get("/{cliente_id}")
async def get_cliente(
    cliente_id: str,
    user: dict = Depends(get_current_user)
):
    """Obtener un cliente específico (solo de la empresa del usuario)"""
    try:
        # Null check
        if not cliente_id or not cliente_id.strip():
            raise HTTPException(status_code=400, detail="Cliente ID is required")

        empresa_id = get_empresa_id_from_user(user)

        if not empresa_id or not empresa_id.strip():
            raise HTTPException(status_code=403, detail="No empresa assigned to user")

        cliente = await cliente_service.get_cliente(cliente_id, empresa_id=empresa_id)
        if not cliente:
            raise HTTPException(status_code=404, detail="Cliente no encontrado")

        return cliente
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting cliente {cliente_id}: {e}")
        raise HTTPException(status_code=503, detail="Unable to retrieve client. Service temporarily unavailable.")


@router.post("")
async def create_cliente(
    cliente_data: ClienteCreate,
    user: dict = Depends(get_current_user)
):
    """
    Crear un nuevo cliente para la empresa del usuario.
    """
    try:
        # Null checks
        if not cliente_data:
            raise HTTPException(status_code=400, detail="Cliente data is required")

        empresa_id = get_empresa_id_from_user(user)

        if not empresa_id or not empresa_id.strip():
            raise HTTPException(status_code=403, detail="No empresa assigned to user")

        user_id = user.get("user_id") or user.get("sub")

        cliente = await cliente_service.create_cliente(
            cliente_data=cliente_data.dict(exclude_none=True),
            empresa_id=empresa_id,
            creado_por=user_id
        )

        if not cliente:
            raise HTTPException(status_code=500, detail="Failed to create cliente")

        return {
            "success": True,
            "cliente": cliente,
            "message": "Cliente creado exitosamente"
        }
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Validation error creating cliente: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating cliente: {e}")
        raise HTTPException(status_code=503, detail="Unable to create client. Service temporarily unavailable.")


@router.put("/{cliente_id}")
async def update_cliente(
    cliente_id: str,
    update_data: ClienteUpdate,
    user: dict = Depends(get_current_user)
):
    """Actualizar un cliente de la empresa del usuario"""
    try:
        # Null checks
        if not cliente_id or not cliente_id.strip():
            raise HTTPException(status_code=400, detail="Cliente ID is required")

        if not update_data:
            raise HTTPException(status_code=400, detail="Update data is required")

        empresa_id = get_empresa_id_from_user(user)

        if not empresa_id or not empresa_id.strip():
            raise HTTPException(status_code=403, detail="No empresa assigned to user")

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
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Validation error updating cliente {cliente_id}: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating cliente {cliente_id}: {e}")
        raise HTTPException(status_code=503, detail="Unable to update client. Service temporarily unavailable.")


@router.delete("/{cliente_id}")
async def delete_cliente(
    cliente_id: str,
    user: dict = Depends(get_current_user)
):
    """Eliminar (desactivar) un cliente"""
    try:
        # Null check
        if not cliente_id or not cliente_id.strip():
            raise HTTPException(status_code=400, detail="Cliente ID is required")

        empresa_id = get_empresa_id_from_user(user)

        if not empresa_id or not empresa_id.strip():
            raise HTTPException(status_code=403, detail="No empresa assigned to user")

        success = await cliente_service.delete_cliente(cliente_id, empresa_id=empresa_id)
        if not success:
            raise HTTPException(status_code=404, detail="Cliente no encontrado")

        return {"success": True, "message": "Cliente desactivado"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting cliente {cliente_id}: {e}")
        raise HTTPException(status_code=503, detail="Unable to delete client. Service temporarily unavailable.")
