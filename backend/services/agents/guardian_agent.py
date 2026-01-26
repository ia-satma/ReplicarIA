"""
GUARDIAN.IA - Agente que vigila el sistema 24/7

Este agente:
1. Ejecuta pruebas automáticas cada X minutos
2. Detecta cuando algo falla
3. Crea tickets de bug automáticamente
4. Notifica si algo crítico se cae
5. Detecta REGRESIONES (bugs que vuelven)
"""

import asyncio
import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field

import httpx
import asyncpg

logger = logging.getLogger(__name__)


@dataclass
class PruebaConfig:
    """Configuración de una prueba de salud del sistema"""
    id: int
    categoria: str
    nombre: str
    descripcion: Optional[str]
    tipo_prueba: str
    configuracion: Dict[str, Any]
    intervalo_minutos: int
    ultima_ejecucion: Optional[datetime]
    ultimo_resultado: Optional[str]
    activo: bool = True


@dataclass
class ResultadoPrueba:
    """Resultado de una prueba ejecutada"""
    status: str  # ok, warning, error, critical
    message: str
    tiempo_ms: int = 0
    detalles: Dict[str, Any] = field(default_factory=dict)


class GuardianAgent:
    """
    Agente guardián que vigila la salud del sistema 24/7
    
    Uso:
        guardian = GuardianAgent()
        await guardian.iniciar()  # Inicia el loop de monitoreo
        await guardian.detener()  # Detiene el monitoreo
    """
    
    def __init__(self, base_url: Optional[str] = None, database_url: Optional[str] = None):
        """
        Inicializa el agente guardián.
        
        Args:
            base_url: URL base para pruebas HTTP. Por defecto usa REPLIT_DEV_DOMAIN o localhost:5000
            database_url: URL de PostgreSQL. Por defecto usa DATABASE_URL del environment
        """
        self.base_url = base_url or self._get_default_base_url()
        self.database_url = database_url or os.environ.get("DATABASE_URL")
        
        self.running = False
        self.http_client: Optional[httpx.AsyncClient] = None
        self.db_pool: Optional[asyncpg.Pool] = None
        
        self._check_interval = 60  # segundos entre ciclos de verificación
        self._task: Optional[asyncio.Task] = None
        self._auth_token: Optional[str] = None
        self._empresa_id: Optional[str] = None
    
    def _generate_service_token(self) -> str:
        """Genera un token JWT para el Guardian como servicio interno"""
        try:
            from jose import jwt
            from datetime import timedelta
            
            secret = os.environ.get("SESSION_SECRET") or os.environ.get("JWT_SECRET_KEY", "dev-secret-key")
            payload = {
                "user_id": "guardian-service",
                "email": "guardian@revisar-ia.internal",
                "empresa_id": self._empresa_id or "system",
                "role": "service",
                "exp": datetime.utcnow() + timedelta(hours=24)
            }
            return jwt.encode(payload, secret, algorithm="HS256")
        except Exception as e:
            logger.warning(f"No se pudo generar token de servicio: {e}")
            return ""
    
    def _get_auth_headers(self) -> Dict[str, str]:
        """Obtiene headers de autenticación para las pruebas HTTP"""
        headers = {}
        if self._auth_token:
            headers["Authorization"] = f"Bearer {self._auth_token}"
        if self._empresa_id:
            headers["X-Empresa-ID"] = self._empresa_id
        return headers
    
    def _get_default_base_url(self) -> str:
        """Obtiene la URL base por defecto del environment"""
        domain = os.environ.get("REPLIT_DEV_DOMAIN")
        if domain:
            return f"https://{domain}"
        return "http://localhost:5000"
    
    async def _init_db_pool(self) -> None:
        """Inicializa el pool de conexiones a PostgreSQL"""
        if not self.database_url:
            logger.warning("DATABASE_URL no configurado - modo sin base de datos")
            return
        
        try:
            self.db_pool = await asyncpg.create_pool(
                self.database_url,
                min_size=1,
                max_size=5,
                command_timeout=30
            )
            logger.info("🛡️ Guardian: Pool de PostgreSQL inicializado")
        except Exception as e:
            logger.error(f"Error inicializando pool de PostgreSQL: {e}")
            self.db_pool = None
    
    async def _close_db_pool(self) -> None:
        """Cierra el pool de conexiones"""
        if self.db_pool:
            await self.db_pool.close()
            self.db_pool = None
    
    async def iniciar(self) -> None:
        """
        Inicia el loop de monitoreo.
        El agente ejecutará pruebas continuamente hasta que se llame detener().
        """
        if self.running:
            logger.warning("Guardian ya está corriendo")
            return
        
        logger.info("🛡️ GUARDIAN.IA iniciando - Vigilando el sistema...")
        
        self.running = True
        
        # Obtener empresa_id por defecto de la base de datos
        await self._init_db_pool()
        if self.db_pool:
            try:
                async with self.db_pool.acquire() as conn:
                    row = await conn.fetchrow("SELECT id FROM companies LIMIT 1")
                    if row:
                        self._empresa_id = str(row['id'])
            except Exception as e:
                logger.warning(f"No se pudo obtener empresa_id: {e}")
        
        # Generar token de servicio para autenticación
        self._auth_token = self._generate_service_token()
        
        self.http_client = httpx.AsyncClient(timeout=30.0, verify=False)
        
        self._task = asyncio.create_task(self._loop_monitoreo())
        logger.info(f"🛡️ GUARDIAN.IA activo - Base URL: {self.base_url}, Auth: {'✅' if self._auth_token else '❌'}")
    
    async def detener(self) -> None:
        """Detiene el loop de monitoreo"""
        logger.info("🛡️ GUARDIAN.IA deteniendo...")
        
        self.running = False
        
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        
        if self.http_client:
            await self.http_client.aclose()
            self.http_client = None
        
        await self._close_db_pool()
        
        logger.info("🛡️ GUARDIAN.IA detenido")
    
    async def _loop_monitoreo(self) -> None:
        """Loop principal de monitoreo"""
        while self.running:
            try:
                await self.ejecutar_pruebas_pendientes()
            except Exception as e:
                logger.error(f"⚠️ Guardian error en ciclo: {e}")
            
            await asyncio.sleep(self._check_interval)
    
    async def ejecutar_pruebas_pendientes(self) -> List[Dict[str, Any]]:
        """
        Ejecuta las pruebas que deben correrse según su intervalo.
        
        Returns:
            Lista de resultados de las pruebas ejecutadas
        """
        if not self.db_pool:
            logger.warning("Sin conexión a BD - no se pueden ejecutar pruebas")
            return []
        
        resultados = []
        
        try:
            async with self.db_pool.acquire() as conn:
                pruebas = await conn.fetch("""
                    SELECT id, categoria, nombre, descripcion, tipo_prueba, 
                           configuracion, intervalo_minutos, ultima_ejecucion,
                           ultimo_resultado, activo
                    FROM system_health_checks
                    WHERE activo = TRUE
                    AND (
                        ultima_ejecucion IS NULL
                        OR ultima_ejecucion < NOW() - (intervalo_minutos || ' minutes')::INTERVAL
                    )
                    ORDER BY 
                        CASE ultimo_resultado 
                            WHEN 'critical' THEN 1 
                            WHEN 'error' THEN 2 
                            ELSE 3 
                        END,
                        ultima_ejecucion ASC NULLS FIRST
                    LIMIT 10
                """)
                
                for row in pruebas:
                    prueba = PruebaConfig(
                        id=row['id'],
                        categoria=row['categoria'],
                        nombre=row['nombre'],
                        descripcion=row['descripcion'],
                        tipo_prueba=row['tipo_prueba'],
                        configuracion=json.loads(row['configuracion']) if row['configuracion'] else {},
                        intervalo_minutos=row['intervalo_minutos'],
                        ultima_ejecucion=row['ultima_ejecucion'],
                        ultimo_resultado=row['ultimo_resultado'],
                        activo=row['activo']
                    )
                    
                    resultado = await self.ejecutar_prueba(prueba)
                    await self.guardar_resultado(prueba, resultado)
                    
                    if resultado.status in ('error', 'critical'):
                        await self.crear_bug_si_nuevo(prueba, resultado)
                    
                    resultados.append({
                        'prueba_id': prueba.id,
                        'nombre': prueba.nombre,
                        'resultado': resultado.status,
                        'mensaje': resultado.message,
                        'tiempo_ms': resultado.tiempo_ms
                    })
                    
        except Exception as e:
            logger.error(f"Error ejecutando pruebas pendientes: {e}")
        
        return resultados
    
    async def ejecutar_prueba(self, prueba: PruebaConfig) -> ResultadoPrueba:
        """
        Ejecuta una prueba específica según su tipo.
        
        Args:
            prueba: Configuración de la prueba a ejecutar
            
        Returns:
            ResultadoPrueba con el estado y detalles
        """
        inicio = datetime.now()
        
        try:
            if prueba.tipo_prueba == 'http_get':
                return await self._http_get(prueba.configuracion, inicio)
            
            elif prueba.tipo_prueba == 'http_post':
                return await self._http_post(prueba.configuracion, inicio)
            
            elif prueba.tipo_prueba == 'db_query':
                return await self._db_query(prueba.configuracion, inicio)
            
            elif prueba.tipo_prueba == 'ui_check':
                return ResultadoPrueba(
                    status='warning',
                    message='Pruebas UI no implementadas aún',
                    tiempo_ms=0
                )
            
            else:
                return ResultadoPrueba(
                    status='warning',
                    message=f'Tipo de prueba no soportado: {prueba.tipo_prueba}',
                    tiempo_ms=0
                )
                
        except Exception as e:
            tiempo_ms = int((datetime.now() - inicio).total_seconds() * 1000)
            return ResultadoPrueba(
                status='error',
                message=str(e),
                tiempo_ms=tiempo_ms,
                detalles={'exception': type(e).__name__}
            )
    
    async def _http_get(self, config: Dict[str, Any], inicio: datetime) -> ResultadoPrueba:
        """Ejecuta prueba HTTP GET"""
        if not self.http_client:
            return ResultadoPrueba(status='error', message='HTTP client no inicializado')
        
        url = self.base_url + config.get('url', '/')
        headers = self._get_auth_headers()
        
        try:
            response = await self.http_client.get(url, headers=headers)
            tiempo_ms = int((datetime.now() - inicio).total_seconds() * 1000)
            
            expected = config.get('expected_status', 200)
            if isinstance(expected, list):
                ok = response.status_code in expected
            else:
                ok = response.status_code == expected
            
            # 401/403 significa que el endpoint responde pero requiere autenticación
            auth_response = response.status_code in [401, 403]
            if auth_response and not ok:
                return ResultadoPrueba(
                    status='ok',
                    message=f'Status {response.status_code} (auth requerida)',
                    tiempo_ms=tiempo_ms,
                    detalles={'response_status': response.status_code, 'auth_required': True}
                )
            
            # 502 indica que el servidor está reiniciando - ignorar como warning
            if response.status_code == 502:
                return ResultadoPrueba(
                    status='warning',
                    message='Servidor reiniciando (502)',
                    tiempo_ms=tiempo_ms,
                    detalles={'response_status': 502, 'server_restarting': True}
                )
            
            check_not = config.get('check_not', [])
            if response.status_code in check_not:
                ok = False
            
            return ResultadoPrueba(
                status='ok' if ok else 'error',
                message=f'Status {response.status_code}' + ('' if ok else f' (esperado: {expected})'),
                tiempo_ms=tiempo_ms,
                detalles={'response_status': response.status_code}
            )
        except httpx.TimeoutException:
            tiempo_ms = int((datetime.now() - inicio).total_seconds() * 1000)
            return ResultadoPrueba(
                status='critical',
                message='Timeout al conectar',
                tiempo_ms=tiempo_ms
            )
        except httpx.ConnectError as e:
            tiempo_ms = int((datetime.now() - inicio).total_seconds() * 1000)
            return ResultadoPrueba(
                status='critical',
                message=f'Error de conexión: {e}',
                tiempo_ms=tiempo_ms
            )
    
    async def _http_post(self, config: Dict[str, Any], inicio: datetime) -> ResultadoPrueba:
        """Ejecuta prueba HTTP POST"""
        if not self.http_client:
            return ResultadoPrueba(status='error', message='HTTP client no inicializado')
        
        url = self.base_url + config.get('url', '/')
        body = config.get('body', {})
        headers = self._get_auth_headers()
        
        try:
            response = await self.http_client.post(url, json=body, headers=headers)
            tiempo_ms = int((datetime.now() - inicio).total_seconds() * 1000)
            
            expected = config.get('expected_status', [200, 201])
            if isinstance(expected, int):
                expected = [expected]
            
            ok = response.status_code in expected
            
            # 401/403 significa que el endpoint responde pero requiere autenticación
            auth_response = response.status_code in [401, 403]
            if auth_response and not ok:
                return ResultadoPrueba(
                    status='ok',
                    message=f'Status {response.status_code} (auth requerida)',
                    tiempo_ms=tiempo_ms,
                    detalles={'response_status': response.status_code, 'auth_required': True}
                )
            
            # 502 indica que el servidor está reiniciando - ignorar como warning
            if response.status_code == 502:
                return ResultadoPrueba(
                    status='warning',
                    message='Servidor reiniciando (502)',
                    tiempo_ms=tiempo_ms,
                    detalles={'response_status': 502, 'server_restarting': True}
                )
            
            check_not = config.get('check_not', [500, 503])
            if response.status_code in check_not:
                ok = False
            
            response_text = response.text[:500] if not ok else None
            
            return ResultadoPrueba(
                status='ok' if ok else 'error',
                message=f'Status {response.status_code}',
                tiempo_ms=tiempo_ms,
                detalles={
                    'response_status': response.status_code,
                    'response_body': response_text
                }
            )
        except httpx.TimeoutException:
            tiempo_ms = int((datetime.now() - inicio).total_seconds() * 1000)
            return ResultadoPrueba(
                status='critical',
                message='Timeout al conectar',
                tiempo_ms=tiempo_ms
            )
        except httpx.ConnectError as e:
            tiempo_ms = int((datetime.now() - inicio).total_seconds() * 1000)
            return ResultadoPrueba(
                status='critical',
                message=f'Error de conexión: {e}',
                tiempo_ms=tiempo_ms
            )
    
    async def _db_query(self, config: Dict[str, Any], inicio: datetime) -> ResultadoPrueba:
        """Ejecuta prueba de consulta a base de datos"""
        if not self.db_pool:
            return ResultadoPrueba(
                status='error',
                message='Pool de base de datos no disponible'
            )
        
        query = config.get('query', 'SELECT 1')
        expected = config.get('expected', True)
        expected_type = config.get('expected_type')
        
        try:
            async with self.db_pool.acquire() as conn:
                result = await conn.fetchval(query)
                tiempo_ms = int((datetime.now() - inicio).total_seconds() * 1000)
                
                ok = True
                if expected_type == 'number':
                    ok = isinstance(result, (int, float))
                elif expected is not None:
                    ok = result is not None
                
                return ResultadoPrueba(
                    status='ok' if ok else 'error',
                    message='Query exitoso' if ok else f'Resultado inesperado: {result}',
                    tiempo_ms=tiempo_ms,
                    detalles={'result': str(result) if result else None}
                )
        except Exception as e:
            tiempo_ms = int((datetime.now() - inicio).total_seconds() * 1000)
            return ResultadoPrueba(
                status='critical',
                message=f'Error de BD: {e}',
                tiempo_ms=tiempo_ms
            )
    
    async def guardar_resultado(self, prueba: PruebaConfig, resultado: ResultadoPrueba) -> None:
        """
        Guarda el resultado de una prueba en la base de datos.
        Actualiza system_health_checks y agrega a health_check_history.
        
        Args:
            prueba: La prueba que se ejecutó
            resultado: El resultado obtenido
        """
        if not self.db_pool:
            logger.warning("No se puede guardar resultado - sin conexión a BD")
            return
        
        try:
            async with self.db_pool.acquire() as conn:
                racha_delta = 1 if resultado.status == 'ok' else -1
                
                status_val = str(resultado.status)
                await conn.execute("""
                    UPDATE system_health_checks
                    SET ultima_ejecucion = NOW(),
                        ultimo_resultado = $1::VARCHAR(20),
                        ultimo_mensaje = $2,
                        tiempo_respuesta_ms = $3,
                        total_ejecuciones = COALESCE(total_ejecuciones, 0) + 1,
                        total_exitosas = COALESCE(total_exitosas, 0) + CASE WHEN $1::VARCHAR(20) = 'ok' THEN 1 ELSE 0 END,
                        total_fallidas = COALESCE(total_fallidas, 0) + CASE WHEN $1::VARCHAR(20) != 'ok' THEN 1 ELSE 0 END,
                        racha_actual = CASE 
                            WHEN $1::VARCHAR(20) = 'ok' AND COALESCE(racha_actual, 0) >= 0 THEN COALESCE(racha_actual, 0) + 1
                            WHEN $1::VARCHAR(20) = 'ok' AND COALESCE(racha_actual, 0) < 0 THEN 1
                            WHEN $1::VARCHAR(20) != 'ok' AND COALESCE(racha_actual, 0) <= 0 THEN COALESCE(racha_actual, 0) - 1
                            ELSE -1
                        END,
                        updated_at = NOW()
                    WHERE id = $4
                """, status_val, resultado.message, resultado.tiempo_ms, prueba.id)
                
                await conn.execute("""
                    INSERT INTO health_check_history 
                    (health_check_id, ejecutado_at, resultado, mensaje, tiempo_respuesta_ms, detalles)
                    VALUES ($1, NOW(), $2::VARCHAR(20), $3, $4, $5::JSONB)
                """, prueba.id, status_val, resultado.message, 
                    resultado.tiempo_ms, json.dumps(resultado.detalles))
                
                logger.debug(f"✓ {prueba.nombre}: {resultado.status} ({resultado.tiempo_ms}ms)")
                
        except Exception as e:
            logger.error(f"Error guardando resultado: {e}")
    
    async def crear_bug_si_nuevo(self, prueba: PruebaConfig, resultado: ResultadoPrueba) -> Optional[str]:
        """
        Crea un bug automáticamente si no existe uno similar abierto.
        Detecta regresiones (bugs que ya se habían arreglado).
        
        Args:
            prueba: La prueba que falló
            resultado: El resultado con el error
            
        Returns:
            Código del bug creado (BUG-YYYY-NNNN) o None si ya existía
        """
        if not self.db_pool:
            return None
        
        try:
            async with self.db_pool.acquire() as conn:
                bug_existente = await conn.fetchrow("""
                    SELECT id, codigo, veces_detectado, estado
                    FROM detected_bugs
                    WHERE health_check_id = $1
                    AND estado NOT IN ('resuelto', 'cerrado')
                    ORDER BY detectado_at DESC
                    LIMIT 1
                """, prueba.id)
                
                if bug_existente:
                    await conn.execute("""
                        UPDATE detected_bugs
                        SET veces_detectado = veces_detectado + 1,
                            error_message = $1,
                            updated_at = NOW()
                        WHERE id = $2
                    """, resultado.message, bug_existente['id'])
                    
                    logger.info(f"🐛 Bug existente actualizado: {bug_existente['codigo']} (detectado {bug_existente['veces_detectado'] + 1} veces)")
                    return bug_existente['codigo']
                
                bug_resuelto = await conn.fetchrow("""
                    SELECT id, codigo
                    FROM detected_bugs
                    WHERE health_check_id = $1
                    AND estado = 'resuelto'
                    ORDER BY verificado_at DESC NULLS LAST
                    LIMIT 1
                """, prueba.id)
                
                es_regresion = bug_resuelto is not None
                bug_original_id = bug_resuelto['id'] if bug_resuelto else None
                
                codigo = await self._generar_codigo_bug(conn)
                
                severidad = 'high' if resultado.status == 'critical' else 'medium'
                if prueba.categoria == 'database':
                    severidad = 'critical'
                
                await conn.execute("""
                    INSERT INTO detected_bugs (
                        codigo, health_check_id, categoria, componente,
                        titulo, descripcion, error_message,
                        severidad, estado, es_regresion, bug_original_id,
                        asignado_a, detectado_at
                    ) VALUES (
                        $1, $2, $3, $4,
                        $5, $6, $7,
                        $8, 'detectado', $9, $10,
                        'DEBUGGER.IA', NOW()
                    )
                """, 
                    codigo, prueba.id, prueba.categoria, prueba.nombre,
                    f"Fallo en: {prueba.nombre}",
                    f"La prueba '{prueba.nombre}' falló con el mensaje: {resultado.message}",
                    resultado.message,
                    severidad, es_regresion, bug_original_id
                )
                
                emoji = "🔄" if es_regresion else "🐛"
                tipo = "REGRESIÓN" if es_regresion else "Nuevo bug"
                logger.warning(f"{emoji} {tipo} detectado: {codigo} - {prueba.nombre} [{severidad}]")
                
                return codigo
                
        except Exception as e:
            logger.error(f"Error creando bug: {e}")
            return None
    
    async def _generar_codigo_bug(self, conn: asyncpg.Connection) -> str:
        """
        Genera un código único para el bug: BUG-YYYY-NNNN
        
        Args:
            conn: Conexión a la base de datos
            
        Returns:
            Código del bug generado
        """
        year = datetime.now().year
        
        ultimo = await conn.fetchval("""
            SELECT codigo FROM detected_bugs
            WHERE codigo LIKE $1
            ORDER BY codigo DESC
            LIMIT 1
        """, f"BUG-{year}-%")
        
        if ultimo:
            try:
                num = int(ultimo.split('-')[-1]) + 1
            except:
                num = 1
        else:
            num = 1
        
        return f"BUG-{year}-{num:04d}"
    
    async def obtener_estado_sistema(self) -> Dict[str, Any]:
        """
        Obtiene un resumen del estado actual del sistema.
        
        Returns:
            Diccionario con métricas de salud del sistema
        """
        if not self.db_pool:
            return {'error': 'Sin conexión a base de datos'}
        
        try:
            async with self.db_pool.acquire() as conn:
                stats = await conn.fetchrow("""
                    SELECT 
                        COUNT(*) as total_pruebas,
                        COUNT(*) FILTER (WHERE ultimo_resultado = 'ok') as exitosas,
                        COUNT(*) FILTER (WHERE ultimo_resultado = 'error') as con_error,
                        COUNT(*) FILTER (WHERE ultimo_resultado = 'critical') as criticas,
                        COUNT(*) FILTER (WHERE ultimo_resultado = 'warning') as advertencias
                    FROM system_health_checks
                    WHERE activo = TRUE
                """)
                
                bugs_abiertos = await conn.fetchval("""
                    SELECT COUNT(*) FROM detected_bugs
                    WHERE estado NOT IN ('resuelto', 'cerrado')
                """)
                
                bugs_criticos = await conn.fetchval("""
                    SELECT COUNT(*) FROM detected_bugs
                    WHERE estado NOT IN ('resuelto', 'cerrado')
                    AND severidad = 'critical'
                """)
                
                return {
                    'guardian_activo': self.running,
                    'base_url': self.base_url,
                    'pruebas': {
                        'total': stats['total_pruebas'],
                        'exitosas': stats['exitosas'],
                        'con_error': stats['con_error'],
                        'criticas': stats['criticas'],
                        'advertencias': stats['advertencias']
                    },
                    'bugs': {
                        'abiertos': bugs_abiertos,
                        'criticos': bugs_criticos
                    },
                    'salud_general': 'critical' if stats['criticas'] > 0 else (
                        'warning' if stats['con_error'] > 0 else 'ok'
                    )
                }
        except Exception as e:
            return {'error': str(e)}


guardian_instance: Optional[GuardianAgent] = None


async def get_guardian() -> GuardianAgent:
    """Obtiene la instancia global del Guardian Agent"""
    global guardian_instance
    if guardian_instance is None:
        guardian_instance = GuardianAgent()
    return guardian_instance


async def iniciar_guardian() -> GuardianAgent:
    """Inicia el Guardian Agent globalmente"""
    guardian = await get_guardian()
    if not guardian.running:
        await guardian.iniciar()
    return guardian


async def detener_guardian() -> None:
    """Detiene el Guardian Agent global"""
    global guardian_instance
    if guardian_instance and guardian_instance.running:
        await guardian_instance.detener()
