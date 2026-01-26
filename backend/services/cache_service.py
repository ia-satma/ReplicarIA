"""
Servicio de Cache con Redis.
Optimiza consultas frecuentes y reduce carga en la base de datos.
"""
import redis
import json
import os
from typing import Optional, Any
from functools import wraps
import hashlib

REDIS_URL = os.getenv("REDIS_URL")

class CacheService:
    """Servicio de cache con Redis para optimizar consultas frecuentes."""
    
    def __init__(self):
        if REDIS_URL:
            try:
                self.client = redis.from_url(REDIS_URL, decode_responses=True)
                self.client.ping()
                self.enabled = True
                print("✅ Redis cache conectado")
            except Exception as e:
                self.client = None
                self.enabled = False
                print(f"⚠️ Redis no disponible: {e}")
        else:
            self.client = None
            self.enabled = False
            print("⚠️ REDIS_URL no configurada - cache deshabilitado")
    
    def _make_key(self, prefix: str, *args, **kwargs) -> str:
        """Genera una key única basada en los argumentos."""
        key_data = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True, default=str)
        hash_val = hashlib.md5(key_data.encode()).hexdigest()[:12]
        return f"revisar:{prefix}:{hash_val}"
    
    def get(self, key: str) -> Optional[Any]:
        """Obtiene un valor del cache."""
        if not self.enabled:
            return None
        try:
            value = self.client.get(key)
            return json.loads(value) if value else None
        except Exception as e:
            print(f"Cache get error: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        """Guarda un valor en cache con TTL en segundos (default 5 min)."""
        if not self.enabled:
            return False
        try:
            self.client.setex(key, ttl, json.dumps(value, default=str))
            return True
        except Exception as e:
            print(f"Cache set error: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Elimina una key del cache."""
        if not self.enabled:
            return False
        try:
            self.client.delete(key)
            return True
        except Exception as e:
            print(f"Cache delete error: {e}")
            return False
    
    def delete_pattern(self, pattern: str) -> int:
        """Elimina todas las keys que coincidan con el patrón."""
        if not self.enabled:
            return 0
        try:
            keys = self.client.keys(f"revisar:{pattern}*")
            if keys:
                return self.client.delete(*keys)
            return 0
        except Exception as e:
            print(f"Cache delete_pattern error: {e}")
            return 0
    
    def invalidate_empresa(self, empresa_id: str) -> int:
        """Invalida todo el cache de una empresa específica."""
        return self.delete_pattern(f"*:{empresa_id}:*")
    
    def get_stats(self) -> dict:
        """Obtiene estadísticas del cache."""
        if not self.enabled:
            return {"enabled": False}
        try:
            info = self.client.info("stats")
            return {
                "enabled": True,
                "hits": info.get("keyspace_hits", 0),
                "misses": info.get("keyspace_misses", 0),
                "keys": self.client.dbsize()
            }
        except Exception as e:
            return {"enabled": True, "error": str(e)}


_cache_service: Optional[CacheService] = None

def get_cache() -> CacheService:
    """Obtiene la instancia singleton del servicio de cache."""
    global _cache_service
    if _cache_service is None:
        _cache_service = CacheService()
    return _cache_service


def cached(prefix: str, ttl: int = 300):
    """
    Decorator para cachear resultados de funciones async.
    
    Uso:
        @cached("search_results", ttl=600)
        async def search_documents(query: str, empresa_id: str):
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache = get_cache()
            cache_args = args[1:] if args and hasattr(args[0], '__class__') else args
            key = cache._make_key(prefix, *cache_args, **kwargs)
            
            cached_value = cache.get(key)
            if cached_value is not None:
                return cached_value
            
            result = await func(*args, **kwargs)
            cache.set(key, result, ttl)
            return result
        return wrapper
    return decorator


def cached_sync(prefix: str, ttl: int = 300):
    """Decorator para cachear resultados de funciones síncronas."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache = get_cache()
            cache_args = args[1:] if args and hasattr(args[0], '__class__') else args
            key = cache._make_key(prefix, *cache_args, **kwargs)
            
            cached_value = cache.get(key)
            if cached_value is not None:
                return cached_value
            
            result = func(*args, **kwargs)
            cache.set(key, result, ttl)
            return result
        return wrapper
    return decorator
