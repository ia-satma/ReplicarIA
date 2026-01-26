"""
DEBUGGER.IA - Agente que analiza y diagnostica bugs

Este agente:
1. Analiza bugs detectados por Guardian
2. Diagnostica causa raíz usando IA (Anthropic Claude)
3. Propone soluciones
4. Identifica archivos a modificar
5. Puede aplicar arreglos (con supervisión)

Uso:
    debugger = DebuggerAgent()
    await debugger.iniciar()  # Inicia el loop de análisis
    await debugger.detener()  # Detiene el análisis
    
    # O manualmente:
    diagnostico = await debugger.analizar_bug(bug_id)
"""

import asyncio
import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

import asyncpg
from anthropic import Anthropic

logger = logging.getLogger(__name__)

# Anthropic client usando Replit AI Integrations
AI_INTEGRATIONS_ANTHROPIC_API_KEY = os.environ.get("AI_INTEGRATIONS_ANTHROPIC_API_KEY")
AI_INTEGRATIONS_ANTHROPIC_BASE_URL = os.environ.get("AI_INTEGRATIONS_ANTHROPIC_BASE_URL")


@dataclass
class BugInfo:
    """Información de un bug detectado"""
    id: int
    codigo: str
    health_check_id: Optional[int]
    categoria: Optional[str]
    componente: Optional[str]
    titulo: str
    descripcion: Optional[str]
    error_message: Optional[str]
    stack_trace: Optional[str]
    severidad: str
    estado: str
    es_regresion: bool = False
    veces_detectado: int = 1
    detectado_at: Optional[datetime] = None


@dataclass
class Diagnostico:
    """Resultado del diagnóstico de un bug"""
    bug_id: int
    causa_raiz: str
    explicacion: str
    archivos_afectados: List[Dict[str, str]] = field(default_factory=list)
    confianza: float = 0.0


@dataclass
class Solucion:
    """Solución propuesta para un bug"""
    bug_id: int
    descripcion: str
    pasos: List[str] = field(default_factory=list)
    archivos_modificar: List[Dict[str, Any]] = field(default_factory=list)
    riesgo: str = "medio"
    requiere_supervision: bool = True


class DebuggerAgent:
    """
    Agente debugger que analiza y diagnostica bugs usando IA.
    
    Uso:
        debugger = DebuggerAgent()
        await debugger.iniciar()  # Inicia el loop de análisis automático
        await debugger.detener()  # Detiene el análisis
        
        # O manualmente:
        diagnostico = await debugger.analizar_bug(bug_id)
    """
    
    def __init__(self, database_url: Optional[str] = None):
        """
        Inicializa el agente debugger.
        
        Args:
            database_url: URL de PostgreSQL. Por defecto usa DATABASE_URL del environment
        """
        self.database_url = database_url or os.environ.get("DATABASE_URL")
        
        self.running = False
        self.db_pool: Optional[asyncpg.Pool] = None
        self._task: Optional[asyncio.Task] = None
        self._check_interval = 120  # segundos entre ciclos de análisis
        
        # Cliente Anthropic usando Replit AI Integrations
        self.anthropic_client: Optional[Anthropic] = None
        self._init_anthropic_client()
    
    def _init_anthropic_client(self) -> None:
        """Inicializa el cliente de Anthropic"""
        if AI_INTEGRATIONS_ANTHROPIC_API_KEY and AI_INTEGRATIONS_ANTHROPIC_BASE_URL:
            try:
                self.anthropic_client = Anthropic(
                    api_key=AI_INTEGRATIONS_ANTHROPIC_API_KEY,
                    base_url=AI_INTEGRATIONS_ANTHROPIC_BASE_URL
                )
                logger.info("🔧 Debugger: Cliente Anthropic inicializado")
            except Exception as e:
                logger.error(f"Error inicializando cliente Anthropic: {e}")
                self.anthropic_client = None
        else:
            logger.warning("🔧 Debugger: Variables de Anthropic no configuradas")
    
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
            logger.info("🔧 Debugger: Pool de PostgreSQL inicializado")
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
        Inicia el loop de análisis de bugs.
        El agente analizará bugs continuamente hasta que se llame detener().
        """
        if self.running:
            logger.warning("Debugger ya está corriendo")
            return
        
        logger.info("🔧 DEBUGGER.IA iniciando - Analizando bugs...")
        
        self.running = True
        await self._init_db_pool()
        
        self._task = asyncio.create_task(self._loop_analisis())
        logger.info("🔧 DEBUGGER.IA activo")
    
    async def detener(self) -> None:
        """Detiene el loop de análisis"""
        logger.info("🔧 DEBUGGER.IA deteniendo...")
        
        self.running = False
        
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        
        await self._close_db_pool()
        
        logger.info("🔧 DEBUGGER.IA detenido")
    
    async def _loop_analisis(self) -> None:
        """Loop principal de análisis de bugs"""
        while self.running:
            try:
                bugs = await self.get_bugs_pendientes()
                
                for bug in bugs:
                    if not self.running:
                        break
                    
                    logger.info(f"🔧 Analizando bug: {bug.codigo}")
                    
                    # Marcar como analizando
                    await self._actualizar_estado_bug(bug.id, "analizando")
                    
                    # Diagnosticar causa raíz
                    diagnostico = await self.diagnosticar_causa_raiz(bug)
                    
                    if diagnostico:
                        # Proponer solución
                        solucion = await self.proponer_solucion(bug, diagnostico)
                        
                        if solucion:
                            await self._guardar_diagnostico_y_solucion(
                                bug.id, diagnostico, solucion
                            )
                            logger.info(f"✅ Bug {bug.codigo} diagnosticado y solución propuesta")
                        else:
                            logger.warning(f"⚠️ Bug {bug.codigo} diagnosticado pero sin solución")
                    else:
                        logger.warning(f"⚠️ No se pudo diagnosticar bug {bug.codigo}")
                        await self._actualizar_estado_bug(bug.id, "detectado")
                    
            except Exception as e:
                logger.error(f"⚠️ Debugger error en ciclo: {e}")
            
            await asyncio.sleep(self._check_interval)
    
    async def get_bugs_pendientes(self, limite: int = 5) -> List[BugInfo]:
        """
        Obtiene bugs que aún no han sido diagnosticados.
        
        Args:
            limite: Número máximo de bugs a obtener
            
        Returns:
            Lista de bugs pendientes de análisis
        """
        if not self.db_pool:
            logger.warning("Sin conexión a BD - no se pueden obtener bugs")
            return []
        
        try:
            async with self.db_pool.acquire() as conn:
                rows = await conn.fetch("""
                    SELECT 
                        id, codigo, health_check_id, categoria, componente,
                        titulo, descripcion, error_message, stack_trace,
                        severidad, estado, es_regresion, veces_detectado,
                        detectado_at
                    FROM detected_bugs
                    WHERE estado = 'detectado'
                    AND diagnostico IS NULL
                    ORDER BY 
                        CASE severidad 
                            WHEN 'critical' THEN 1 
                            WHEN 'high' THEN 2 
                            WHEN 'medium' THEN 3 
                            ELSE 4 
                        END,
                        veces_detectado DESC,
                        detectado_at ASC
                    LIMIT $1
                """, limite)
                
                bugs = []
                for row in rows:
                    bugs.append(BugInfo(
                        id=row['id'],
                        codigo=row['codigo'],
                        health_check_id=row['health_check_id'],
                        categoria=row['categoria'],
                        componente=row['componente'],
                        titulo=row['titulo'],
                        descripcion=row['descripcion'],
                        error_message=row['error_message'],
                        stack_trace=row['stack_trace'],
                        severidad=row['severidad'],
                        estado=row['estado'],
                        es_regresion=row['es_regresion'] or False,
                        veces_detectado=row['veces_detectado'] or 1,
                        detectado_at=row['detectado_at']
                    ))
                
                return bugs
                
        except Exception as e:
            logger.error(f"Error obteniendo bugs pendientes: {e}")
            return []
    
    async def analizar_bug(self, bug_id: int) -> Optional[Dict[str, Any]]:
        """
        Analiza un bug específico: diagnostica y propone solución.
        
        Args:
            bug_id: ID del bug a analizar
            
        Returns:
            Diccionario con diagnóstico y solución, o None si falla
        """
        if not self.db_pool:
            await self._init_db_pool()
            if not self.db_pool:
                return None
        
        try:
            async with self.db_pool.acquire() as conn:
                row = await conn.fetchrow("""
                    SELECT 
                        id, codigo, health_check_id, categoria, componente,
                        titulo, descripcion, error_message, stack_trace,
                        severidad, estado, es_regresion, veces_detectado,
                        detectado_at
                    FROM detected_bugs
                    WHERE id = $1
                """, bug_id)
                
                if not row:
                    logger.warning(f"Bug {bug_id} no encontrado")
                    return None
                
                bug = BugInfo(
                    id=row['id'],
                    codigo=row['codigo'],
                    health_check_id=row['health_check_id'],
                    categoria=row['categoria'],
                    componente=row['componente'],
                    titulo=row['titulo'],
                    descripcion=row['descripcion'],
                    error_message=row['error_message'],
                    stack_trace=row['stack_trace'],
                    severidad=row['severidad'],
                    estado=row['estado'],
                    es_regresion=row['es_regresion'] or False,
                    veces_detectado=row['veces_detectado'] or 1,
                    detectado_at=row['detectado_at']
                )
            
            # Marcar como analizando
            await self._actualizar_estado_bug(bug.id, "analizando")
            
            # Diagnosticar
            diagnostico = await self.diagnosticar_causa_raiz(bug)
            
            if not diagnostico:
                await self._actualizar_estado_bug(bug.id, "detectado")
                return None
            
            # Proponer solución
            solucion = await self.proponer_solucion(bug, diagnostico)
            
            if solucion:
                await self._guardar_diagnostico_y_solucion(bug.id, diagnostico, solucion)
            
            return {
                "bug": {
                    "id": bug.id,
                    "codigo": bug.codigo,
                    "titulo": bug.titulo,
                    "severidad": bug.severidad
                },
                "diagnostico": {
                    "causa_raiz": diagnostico.causa_raiz,
                    "explicacion": diagnostico.explicacion,
                    "archivos_afectados": diagnostico.archivos_afectados,
                    "confianza": diagnostico.confianza
                },
                "solucion": {
                    "descripcion": solucion.descripcion,
                    "pasos": solucion.pasos,
                    "archivos_modificar": solucion.archivos_modificar,
                    "riesgo": solucion.riesgo,
                    "requiere_supervision": solucion.requiere_supervision
                } if solucion else None
            }
            
        except Exception as e:
            logger.error(f"Error analizando bug {bug_id}: {e}")
            return None
    
    async def diagnosticar_causa_raiz(self, bug: BugInfo) -> Optional[Diagnostico]:
        """
        Usa IA para diagnosticar la causa raíz de un bug.
        
        Args:
            bug: Información del bug a diagnosticar
            
        Returns:
            Diagnóstico con causa raíz y archivos afectados
        """
        if not self.anthropic_client:
            logger.error("Cliente Anthropic no disponible")
            return None
        
        # Construir prompt para diagnóstico
        prompt = self._construir_prompt_diagnostico(bug)
        
        try:
            message = self.anthropic_client.messages.create(
                model="claude-sonnet-4-5",
                max_tokens=2048,
                system="""Eres DEBUGGER.IA, un experto en diagnóstico de bugs y análisis de errores.
Tu trabajo es analizar bugs detectados en un sistema y diagnosticar su causa raíz.

IMPORTANTE: Responde SIEMPRE en formato JSON válido con la siguiente estructura:
{
    "causa_raiz": "Descripción breve de la causa principal del bug",
    "explicacion": "Explicación detallada de por qué ocurre el error",
    "archivos_afectados": [
        {"archivo": "ruta/al/archivo.py", "razon": "Por qué este archivo está involucrado"}
    ],
    "confianza": 0.85
}

Donde "confianza" es un número entre 0 y 1 indicando tu nivel de certeza.""",
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )
            
            response_text = message.content[0].text
            
            # Parsear respuesta JSON
            try:
                # Limpiar respuesta si tiene markdown
                if "```json" in response_text:
                    response_text = response_text.split("```json")[1].split("```")[0]
                elif "```" in response_text:
                    response_text = response_text.split("```")[1].split("```")[0]
                
                data = json.loads(response_text.strip())
                
                return Diagnostico(
                    bug_id=bug.id,
                    causa_raiz=data.get("causa_raiz", "No determinada"),
                    explicacion=data.get("explicacion", ""),
                    archivos_afectados=data.get("archivos_afectados", []),
                    confianza=float(data.get("confianza", 0.5))
                )
                
            except json.JSONDecodeError as e:
                logger.error(f"Error parseando respuesta de IA: {e}")
                # Intentar extraer información básica
                return Diagnostico(
                    bug_id=bug.id,
                    causa_raiz=response_text[:500] if response_text else "Error en diagnóstico",
                    explicacion="No se pudo parsear la respuesta de IA",
                    archivos_afectados=[],
                    confianza=0.3
                )
                
        except Exception as e:
            logger.error(f"Error en diagnóstico con IA: {e}")
            return None
    
    async def proponer_solucion(
        self, 
        bug: BugInfo, 
        diagnostico: Diagnostico
    ) -> Optional[Solucion]:
        """
        Propone una solución basada en el diagnóstico.
        
        Args:
            bug: Información del bug
            diagnostico: Diagnóstico del bug
            
        Returns:
            Solución propuesta con pasos y archivos a modificar
        """
        if not self.anthropic_client:
            logger.error("Cliente Anthropic no disponible")
            return None
        
        prompt = self._construir_prompt_solucion(bug, diagnostico)
        
        try:
            message = self.anthropic_client.messages.create(
                model="claude-sonnet-4-5",
                max_tokens=2048,
                system="""Eres DEBUGGER.IA, un experto en resolver bugs y proponer soluciones.
Basándote en el diagnóstico proporcionado, propón una solución clara y ejecutable.

IMPORTANTE: Responde SIEMPRE en formato JSON válido con la siguiente estructura:
{
    "descripcion": "Descripción breve de la solución",
    "pasos": [
        "Paso 1: Descripción del primer paso",
        "Paso 2: Descripción del segundo paso"
    ],
    "archivos_modificar": [
        {
            "archivo": "ruta/al/archivo.py",
            "cambios": "Descripción de los cambios necesarios",
            "codigo_sugerido": "código a agregar o modificar (opcional)"
        }
    ],
    "riesgo": "bajo|medio|alto",
    "requiere_supervision": true
}

Sé específico en los pasos y cambios necesarios.""",
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )
            
            response_text = message.content[0].text
            
            try:
                # Limpiar respuesta si tiene markdown
                if "```json" in response_text:
                    response_text = response_text.split("```json")[1].split("```")[0]
                elif "```" in response_text:
                    response_text = response_text.split("```")[1].split("```")[0]
                
                data = json.loads(response_text.strip())
                
                return Solucion(
                    bug_id=bug.id,
                    descripcion=data.get("descripcion", "Sin descripción"),
                    pasos=data.get("pasos", []),
                    archivos_modificar=data.get("archivos_modificar", []),
                    riesgo=data.get("riesgo", "medio"),
                    requiere_supervision=data.get("requiere_supervision", True)
                )
                
            except json.JSONDecodeError as e:
                logger.error(f"Error parseando solución de IA: {e}")
                return Solucion(
                    bug_id=bug.id,
                    descripcion=response_text[:500] if response_text else "Error generando solución",
                    pasos=["Revisar manualmente el error"],
                    archivos_modificar=[],
                    riesgo="alto",
                    requiere_supervision=True
                )
                
        except Exception as e:
            logger.error(f"Error proponiendo solución con IA: {e}")
            return None
    
    def _construir_prompt_diagnostico(self, bug: BugInfo) -> str:
        """Construye el prompt para diagnóstico"""
        prompt = f"""Analiza el siguiente bug y diagnostica su causa raíz:

## Bug Detectado
- **Código**: {bug.codigo}
- **Título**: {bug.titulo}
- **Categoría**: {bug.categoria or 'No especificada'}
- **Componente**: {bug.componente or 'No especificado'}
- **Severidad**: {bug.severidad}
- **Es regresión**: {'Sí' if bug.es_regresion else 'No'}
- **Veces detectado**: {bug.veces_detectado}

## Descripción
{bug.descripcion or 'Sin descripción'}

## Mensaje de Error
{bug.error_message or 'No disponible'}

## Stack Trace
{bug.stack_trace or 'No disponible'}

Por favor, diagnostica:
1. ¿Cuál es la causa raíz más probable?
2. ¿Por qué ocurre este error?
3. ¿Qué archivos podrían estar involucrados?
4. ¿Qué tan seguro estás del diagnóstico?"""
        
        return prompt
    
    def _construir_prompt_solucion(
        self, 
        bug: BugInfo, 
        diagnostico: Diagnostico
    ) -> str:
        """Construye el prompt para proponer solución"""
        archivos_str = "\n".join([
            f"  - {a['archivo']}: {a.get('razon', '')}"
            for a in diagnostico.archivos_afectados
        ]) if diagnostico.archivos_afectados else "No identificados"
        
        prompt = f"""Propón una solución para el siguiente bug diagnosticado:

## Bug
- **Código**: {bug.codigo}
- **Título**: {bug.titulo}
- **Severidad**: {bug.severidad}
- **Error**: {bug.error_message or 'No disponible'}

## Diagnóstico
- **Causa Raíz**: {diagnostico.causa_raiz}
- **Explicación**: {diagnostico.explicacion}
- **Confianza**: {diagnostico.confianza * 100:.0f}%
- **Archivos Afectados**:
{archivos_str}

Por favor, proporciona:
1. Una descripción clara de la solución
2. Pasos específicos para implementarla
3. Qué archivos necesitan modificarse y cómo
4. El nivel de riesgo de la solución
5. Si requiere supervisión humana para aplicarse"""
        
        return prompt
    
    async def _actualizar_estado_bug(self, bug_id: int, estado: str) -> None:
        """Actualiza el estado de un bug"""
        if not self.db_pool:
            return
        
        try:
            async with self.db_pool.acquire() as conn:
                await conn.execute("""
                    UPDATE detected_bugs
                    SET estado = $1, updated_at = NOW()
                    WHERE id = $2
                """, estado, bug_id)
        except Exception as e:
            logger.error(f"Error actualizando estado de bug {bug_id}: {e}")
    
    async def _guardar_diagnostico_y_solucion(
        self,
        bug_id: int,
        diagnostico: Diagnostico,
        solucion: Solucion
    ) -> None:
        """Guarda el diagnóstico y solución en la base de datos"""
        if not self.db_pool:
            return
        
        try:
            async with self.db_pool.acquire() as conn:
                archivos_json = json.dumps(solucion.archivos_modificar)
                
                await conn.execute("""
                    UPDATE detected_bugs
                    SET 
                        estado = 'diagnosticado',
                        diagnostico = $1,
                        solucion_propuesta = $2,
                        archivos_modificar = $3,
                        diagnosticado_at = NOW(),
                        updated_at = NOW()
                    WHERE id = $4
                """, 
                    diagnostico.explicacion,
                    solucion.descripcion,
                    archivos_json,
                    bug_id
                )
                
                logger.info(f"✅ Diagnóstico guardado para bug {bug_id}")
                
        except Exception as e:
            logger.error(f"Error guardando diagnóstico de bug {bug_id}: {e}")
    
    async def obtener_estado(self) -> Dict[str, Any]:
        """
        Obtiene el estado actual del debugger.
        
        Returns:
            Diccionario con métricas del debugger
        """
        if not self.db_pool:
            return {
                "activo": self.running,
                "anthropic_disponible": self.anthropic_client is not None,
                "database_conectada": False
            }
        
        try:
            async with self.db_pool.acquire() as conn:
                stats = await conn.fetchrow("""
                    SELECT 
                        COUNT(*) as total_bugs,
                        COUNT(*) FILTER (WHERE estado = 'detectado') as pendientes,
                        COUNT(*) FILTER (WHERE estado = 'analizando') as analizando,
                        COUNT(*) FILTER (WHERE estado = 'diagnosticado') as diagnosticados,
                        COUNT(*) FILTER (WHERE estado = 'resuelto') as resueltos,
                        COUNT(*) FILTER (WHERE severidad = 'critical') as criticos,
                        COUNT(*) FILTER (WHERE es_regresion = TRUE) as regresiones
                    FROM detected_bugs
                """)
                
                return {
                    "activo": self.running,
                    "anthropic_disponible": self.anthropic_client is not None,
                    "database_conectada": True,
                    "bugs": {
                        "total": stats['total_bugs'] or 0,
                        "pendientes": stats['pendientes'] or 0,
                        "analizando": stats['analizando'] or 0,
                        "diagnosticados": stats['diagnosticados'] or 0,
                        "resueltos": stats['resueltos'] or 0,
                        "criticos": stats['criticos'] or 0,
                        "regresiones": stats['regresiones'] or 0
                    }
                }
                
        except Exception as e:
            logger.error(f"Error obteniendo estado: {e}")
            return {
                "activo": self.running,
                "anthropic_disponible": self.anthropic_client is not None,
                "database_conectada": False,
                "error": str(e)
            }


# Singleton para acceso global
_debugger_instance: Optional[DebuggerAgent] = None


def get_debugger() -> DebuggerAgent:
    """Obtiene la instancia singleton del debugger"""
    global _debugger_instance
    if _debugger_instance is None:
        _debugger_instance = DebuggerAgent()
    return _debugger_instance


async def iniciar_debugger() -> DebuggerAgent:
    """Inicia el debugger y retorna la instancia"""
    debugger = get_debugger()
    await debugger.iniciar()
    return debugger


async def detener_debugger() -> None:
    """Detiene el debugger"""
    global _debugger_instance
    if _debugger_instance:
        await _debugger_instance.detener()
