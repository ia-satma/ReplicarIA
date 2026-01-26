"""
Defense Files - Decoradores para Documentación Automática
Decoradores que registran automáticamente las acciones de los agentes en expedientes de defensa

Para FastAPI con funciones async
"""
import logging
import functools
import time
import traceback
from typing import Optional, Any, Dict, Callable
from datetime import datetime

from fastapi import Request

logger = logging.getLogger(__name__)


async def obtener_defense_file_id(request: Request) -> Optional[int]:
    """
    Obtiene el defense_file_id del contexto de la petición.
    Busca en el siguiente orden:
    1. Header X-Defense-File-ID
    2. Query parameter defense_file_id
    3. Body JSON campo defense_file_id
    
    Args:
        request: Objeto Request de FastAPI
        
    Returns:
        defense_file_id si se encuentra, None en caso contrario
    """
    defense_file_id = None
    
    header_value = request.headers.get("X-Defense-File-ID")
    if header_value:
        try:
            defense_file_id = int(header_value)
            logger.debug(f"📁 Defense Files: Obtenido defense_file_id={defense_file_id} desde header")
            return defense_file_id
        except (ValueError, TypeError):
            logger.warning(f"📁 Defense Files: Header X-Defense-File-ID inválido: {header_value}")
    
    query_value = request.query_params.get("defense_file_id")
    if query_value:
        try:
            defense_file_id = int(query_value)
            logger.debug(f"📁 Defense Files: Obtenido defense_file_id={defense_file_id} desde query param")
            return defense_file_id
        except (ValueError, TypeError):
            logger.warning(f"📁 Defense Files: Query param defense_file_id inválido: {query_value}")
    
    try:
        content_type = request.headers.get("content-type", "")
        if "application/json" in content_type:
            body = await request.json()
            if isinstance(body, dict) and "defense_file_id" in body:
                defense_file_id = int(body["defense_file_id"])
                logger.debug(f"📁 Defense Files: Obtenido defense_file_id={defense_file_id} desde body JSON")
                return defense_file_id
    except Exception as e:
        logger.debug(f"📁 Defense Files: No se pudo obtener defense_file_id del body: {e}")
    
    return None


async def _registrar_evento_accion(
    defense_file_id: int,
    agente_id: str,
    tipo_evento: str,
    titulo: str,
    descripcion: str,
    datos: Dict[str, Any],
    duracion_ms: float,
    exito: bool,
    error_msg: Optional[str] = None
) -> Dict[str, Any]:
    """
    Registra un evento de acción de agente en el expediente de defensa.
    
    Args:
        defense_file_id: ID del expediente de defensa
        agente_id: Identificador del agente (A1, A2, etc.)
        tipo_evento: Tipo de evento a registrar
        titulo: Título descriptivo del evento
        descripcion: Descripción detallada de la acción
        datos: Datos adicionales del evento
        duracion_ms: Duración de la acción en milisegundos
        exito: Si la acción fue exitosa
        error_msg: Mensaje de error si hubo fallo
        
    Returns:
        Resultado del registro del evento
    """
    from services.defense_file_pg_service import defense_file_pg_service
    
    datos_completos = {
        **datos,
        "duracion_ms": duracion_ms,
        "exito": exito,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    if error_msg:
        datos_completos["error"] = error_msg
    
    try:
        resultado = await defense_file_pg_service.registrar_evento(
            defense_file_id=defense_file_id,
            tipo=tipo_evento,
            agente=agente_id,
            titulo=titulo,
            descripcion=descripcion,
            datos=datos_completos
        )
        
        status = "✅" if exito else "❌"
        logger.info(f"📁 [{agente_id}] {status} Evento registrado: {titulo} ({duracion_ms:.0f}ms)")
        
        return resultado
        
    except Exception as e:
        logger.error(f"📁 [{agente_id}] Error registrando evento: {e}")
        return {"success": False, "error": str(e)}


def documentar_accion(
    agente_id: str,
    tipo_evento: str,
    titulo_template: str,
    descripcion_template: Optional[str] = None,
    extraer_datos: Optional[Callable] = None
):
    """
    Decorador para documentar automáticamente acciones de agentes en expedientes de defensa.
    
    El decorador:
    1. Obtiene el defense_file_id del contexto de la petición
    2. Ejecuta la función decorada midiendo el tiempo
    3. Registra el evento con el resultado (éxito o error)
    
    Args:
        agente_id: Identificador del agente (A1, A2, A3, etc.)
        tipo_evento: Tipo de evento para clasificar la acción
        titulo_template: Template para el título (puede usar {nombre} para valores del request)
        descripcion_template: Template opcional para la descripción
        extraer_datos: Función opcional para extraer datos adicionales del request/response
        
    Returns:
        Decorador que envuelve funciones async
        
    Ejemplo:
        @documentar_accion(
            agente_id="A1",
            tipo_evento="conversacion",
            titulo_template="Chat de facturación: {mensaje[:50]}..."
        )
        async def procesar_chat(request: Request, mensaje: str):
            return await generar_respuesta(mensaje)
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            request: Optional[Request] = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            if not request:
                request = kwargs.get("request")
            
            defense_file_id: Optional[int] = None
            if request:
                defense_file_id = await obtener_defense_file_id(request)
            
            defense_file_id = defense_file_id or kwargs.get("defense_file_id")
            
            inicio = time.time()
            error_msg: Optional[str] = None
            resultado = None
            exito = True
            
            try:
                resultado = await func(*args, **kwargs)
                return resultado
                
            except Exception as e:
                exito = False
                error_msg = f"{type(e).__name__}: {str(e)}"
                logger.error(f"📁 [{agente_id}] Error en {func.__name__}: {error_msg}")
                raise
                
            finally:
                duracion_ms = (time.time() - inicio) * 1000
                
                if defense_file_id:
                    try:
                        titulo = titulo_template
                        try:
                            format_data = {**kwargs}
                            if resultado and isinstance(resultado, dict):
                                format_data.update(resultado)
                            titulo = titulo_template.format(**format_data)
                        except (KeyError, IndexError, ValueError):
                            pass
                        
                        descripcion = descripcion_template or f"Acción ejecutada por {agente_id}"
                        try:
                            if descripcion_template:
                                descripcion = descripcion_template.format(**format_data)
                        except (KeyError, IndexError, ValueError):
                            pass
                        
                        datos = {}
                        if extraer_datos:
                            try:
                                datos = extraer_datos(kwargs, resultado) or {}
                            except Exception as extract_err:
                                logger.warning(f"📁 [{agente_id}] Error extrayendo datos: {extract_err}")
                        
                        if kwargs:
                            datos["parametros"] = {
                                k: str(v)[:200] if isinstance(v, str) else v
                                for k, v in kwargs.items()
                                if k not in ["request", "db", "session"]
                            }
                        
                        await _registrar_evento_accion(
                            defense_file_id=defense_file_id,
                            agente_id=agente_id,
                            tipo_evento=tipo_evento,
                            titulo=titulo[:255],
                            descripcion=descripcion[:1000],
                            datos=datos,
                            duracion_ms=duracion_ms,
                            exito=exito,
                            error_msg=error_msg
                        )
                        
                    except Exception as reg_error:
                        logger.error(f"📁 [{agente_id}] Error en registro de evento: {reg_error}")
                else:
                    logger.debug(f"📁 [{agente_id}] Sin defense_file_id, evento no registrado para {func.__name__}")
        
        return wrapper
    return decorator


class DefenseFileContext:
    """
    Clase auxiliar para manejar el contexto del defense_file en peticiones.
    Puede usarse con FastAPI Depends para inyectar el defense_file_id.
    
    Ejemplo:
        async def get_defense_file_context(request: Request) -> DefenseFileContext:
            return DefenseFileContext(request)
            
        @router.post("/chat")
        async def chat(
            mensaje: str,
            df_ctx: DefenseFileContext = Depends(get_defense_file_context)
        ):
            if df_ctx.defense_file_id:
                await df_ctx.registrar_conversacion(...)
    """
    
    def __init__(self, request: Request):
        self.request = request
        self._defense_file_id: Optional[int] = None
        self._initialized = False
    
    async def _init(self):
        """Inicializa el contexto obteniendo el defense_file_id."""
        if not self._initialized:
            self._defense_file_id = await obtener_defense_file_id(self.request)
            self._initialized = True
    
    @property
    async def defense_file_id(self) -> Optional[int]:
        """Obtiene el defense_file_id del contexto."""
        await self._init()
        return self._defense_file_id
    
    async def tiene_expediente(self) -> bool:
        """Verifica si hay un expediente asociado a la petición."""
        await self._init()
        return self._defense_file_id is not None


async def get_defense_file_context(request: Request) -> DefenseFileContext:
    """
    Dependency para FastAPI que proporciona el contexto del defense_file.
    
    Uso:
        from fastapi import Depends
        from services.defense_files.decorators import get_defense_file_context, DefenseFileContext
        
        @router.post("/endpoint")
        async def mi_endpoint(
            df_ctx: DefenseFileContext = Depends(get_defense_file_context)
        ):
            df_id = await df_ctx.defense_file_id
            if df_id:
                # Registrar evento...
    """
    return DefenseFileContext(request)
