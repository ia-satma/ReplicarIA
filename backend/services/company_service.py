"""
Servicio de empresas usando PostgreSQL como fuente de verdad.
Tabla: companies (PostgreSQL)
"""
from typing import Optional, List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class CompanyService:
    """Servicio para gestionar empresas desde PostgreSQL."""
    
    async def get_company_by_id(self, company_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene una empresa por su ID."""
        try:
            from services.user_db import get_session
            from sqlalchemy import text
            
            async with get_session() as session:
                result = await session.execute(
                    text("SELECT * FROM companies WHERE id = :id"),
                    {"id": company_id}
                )
                row = result.fetchone()
                
                if row:
                    columns = result.keys()
                    return dict(zip(columns, row))
                return None
        except Exception as e:
            logger.error(f"Error obteniendo empresa por ID: {e}")
            return None
    
    async def get_company_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Obtiene una empresa por su nombre (búsqueda exacta o parcial)."""
        try:
            from services.user_db import get_session
            from sqlalchemy import text
            
            async with get_session() as session:
                result = await session.execute(
                    text("SELECT * FROM companies WHERE LOWER(TRIM(name)) = LOWER(TRIM(:name))"),
                    {"name": name}
                )
                row = result.fetchone()
                
                if row:
                    columns = result.keys()
                    return dict(zip(columns, row))
                return None
        except Exception as e:
            logger.error(f"Error obteniendo empresa por nombre: {e}")
            return None
    
    async def get_all_companies(self, only_active: bool = True) -> List[Dict[str, Any]]:
        """Obtiene todas las empresas."""
        try:
            from services.user_db import get_session
            from sqlalchemy import text
            
            async with get_session() as session:
                if only_active:
                    result = await session.execute(
                        text("SELECT * FROM companies WHERE is_active = true ORDER BY name")
                    )
                else:
                    result = await session.execute(
                        text("SELECT * FROM companies ORDER BY name")
                    )
                
                rows = result.fetchall()
                columns = result.keys()
                return [dict(zip(columns, row)) for row in rows]
        except Exception as e:
            logger.error(f"Error obteniendo empresas: {e}")
            return []
    
    async def get_company_id_for_user(self, company_name: str) -> Optional[str]:
        """
        Dado el nombre de empresa de un usuario, retorna el ID de la empresa.
        Usado para mapear users.company (texto) → companies.id (UUID)
        """
        if not company_name:
            return None
        
        company = await self.get_company_by_name(company_name)
        if company:
            return str(company.get('id'))
        return None


company_service = CompanyService()
