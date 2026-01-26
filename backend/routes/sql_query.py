"""
SQL Query Route - Con validación de seguridad
"""
import re
import logging
from fastapi import APIRouter, Body, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
import os

from services.sql_engine_service import query as sql_query

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/sql", tags=["SQL"])
security = HTTPBearer()

# Palabras clave SQL peligrosas (case insensitive)
DANGEROUS_KEYWORDS = [
    r'\bDROP\b', r'\bDELETE\b', r'\bTRUNCATE\b', r'\bALTER\b',
    r'\bCREATE\b', r'\bINSERT\b', r'\bUPDATE\b', r'\bGRANT\b',
    r'\bREVOKE\b', r'\bEXEC\b', r'\bEXECUTE\b', r'\bMERGE\b',
    r'\bCALL\b', r'\bSET\b', r'--', r'/\*', r'\*/', r';.*SELECT',
    r'UNION\s+ALL', r'INTO\s+OUTFILE', r'LOAD_FILE', r'BENCHMARK',
    r'SLEEP\s*\(', r'WAITFOR', r'xp_', r'sp_'
]

# Compilar patrones para eficiencia
DANGEROUS_PATTERNS = [re.compile(kw, re.IGNORECASE) for kw in DANGEROUS_KEYWORDS]


def validate_sql(sql: str) -> tuple[bool, str]:
    """
    Valida que el SQL sea seguro para ejecutar.
    Returns: (is_valid, error_message)
    """
    if not sql or not sql.strip():
        return False, "SQL query cannot be empty"

    sql_upper = sql.upper().strip()

    # Solo permitir SELECT
    if not sql_upper.startswith('SELECT'):
        return False, "Only SELECT queries are allowed"

    # Buscar palabras peligrosas
    for pattern in DANGEROUS_PATTERNS:
        if pattern.search(sql):
            return False, f"Query contains prohibited keyword or pattern"

    # Limitar longitud
    if len(sql) > 5000:
        return False, "Query too long (max 5000 characters)"

    # Verificar paréntesis balanceados
    if sql.count('(') != sql.count(')'):
        return False, "Unbalanced parentheses in query"

    return True, ""


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verificar token JWT"""
    SECRET_KEY = os.environ.get('SECRET_KEY')
    if not SECRET_KEY:
        raise HTTPException(status_code=500, detail="Server configuration error")

    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload
    except JWTError as e:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


@router.post('/query')
def sql_run(
    payload: dict = Body(...),
    current_user: dict = Depends(get_current_user)
):
    """
    Ejecuta una query SQL de solo lectura (SELECT).

    Seguridad:
    - Requiere autenticación JWT
    - Solo permite SELECT
    - Bloquea palabras peligrosas
    - Limita resultados a 100 filas
    """
    try:
        sql = (payload or {}).get('sql', '')

        # Validar SQL
        is_valid, error_msg = validate_sql(sql)
        if not is_valid:
            logger.warning(f"SQL validation failed for user {current_user.get('sub', 'unknown')}: {error_msg}")
            raise HTTPException(status_code=400, detail=error_msg)

        # Log para auditoría
        logger.info(f"SQL query by {current_user.get('sub', 'unknown')}: {sql[:100]}...")

        # Ejecutar query
        df = sql_query(sql)

        # Limitar resultados
        max_rows = min(int(payload.get('limit', 100)), 100)

        return {
            "ok": True,
            "rows": len(df.index) if hasattr(df, 'index') else 0,
            "data": df.head(max_rows).to_dict(orient='records') if hasattr(df, 'to_dict') else [],
            "limited": len(df.index) > max_rows if hasattr(df, 'index') else False
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"SQL query error: {str(e)}")
        raise HTTPException(status_code=500, detail="Error executing query")
