"""
Event Streaming Service for Revisar.IA Multi-Agent Deliberation
Manages Server-Sent Events (SSE) for real-time analysis updates
WITH EVENT BUFFERING - Events are stored and replayed to late subscribers
"""
import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional, Any, List
from threading import Lock
from collections import deque

from config.agents_config import AGENT_CONFIGURATIONS

logger = logging.getLogger(__name__)

MAX_BUFFER_SIZE = 100
SESSION_TTL_MINUTES = 30


class EventEmitter:
    """
    Singleton class that manages Server-Sent Events for multi-agent deliberation.
    
    KEY FEATURE: Event Buffering
    - Events are stored in a buffer even when no subscribers exist
    - When a subscriber connects, they receive all buffered events first
    - This solves the timing problem where analysis starts before frontend connects
    """
    _instance = None
    _lock = Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._sessions: Dict[str, Dict[str, Any]] = {}
        self._session_lock = Lock()
        self._initialized = True
        logger.info("EventEmitter singleton inicializado con buffer de eventos")
    
    def _get_agent_name(self, agent_id: str) -> str:
        """Get agent display name from configuration"""
        config = AGENT_CONFIGURATIONS.get(agent_id, {})
        return config.get("name", agent_id)
    
    def _ensure_session(self, project_id: str) -> Dict[str, Any]:
        """
        Ensure a session exists for the project, creating one if needed.
        MUST be called with _session_lock held.
        """
        if project_id not in self._sessions:
            self._sessions[project_id] = {
                "queues": [],
                "buffer": deque(maxlen=MAX_BUFFER_SIZE),
                "created_at": datetime.now(timezone.utc),
                "event_count": 0,
                "is_complete": False,
                "final_event_time": None
            }
            logger.info(f"Sesión creada para proyecto {project_id} (con buffer)")
        return self._sessions[project_id]
    
    def create_session(self, project_id: str) -> bool:
        """
        Explicitly create a session for a project before analysis starts.
        This ensures the buffer is ready to receive events.
        """
        with self._session_lock:
            if project_id not in self._sessions:
                self._ensure_session(project_id)
                return True
            return False
    
    def subscribe(self, project_id: str) -> asyncio.Queue:
        """
        Subscribe to events for a specific project.
        Returns an asyncio Queue for receiving events.
        
        IMPORTANT: Buffered events are added to the queue immediately,
        so the subscriber receives all past events first.
        """
        queue: asyncio.Queue = asyncio.Queue()
        buffered_events: List[Dict] = []
        
        with self._session_lock:
            session = self._ensure_session(project_id)
            session["queues"].append(queue)
            buffered_events = list(session["buffer"])
            subscriber_count = len(session["queues"])
            buffer_count = len(buffered_events)
        
        logger.info(f"Nuevo suscriptor para proyecto {project_id}. Total: {subscriber_count}, Eventos en buffer: {buffer_count}")
        
        for event in buffered_events:
            try:
                queue.put_nowait(event)
            except asyncio.QueueFull:
                logger.warning(f"Cola llena al enviar eventos del buffer para {project_id}")
                break
        
        if buffer_count > 0:
            logger.info(f"Replay de {buffer_count} eventos del buffer para proyecto {project_id}")
        
        return queue
    
    def unsubscribe(self, project_id: str, queue: asyncio.Queue) -> bool:
        """
        Unsubscribe a queue from project events.
        Note: Session is NOT deleted when last subscriber leaves if buffer has events.
        """
        with self._session_lock:
            if project_id in self._sessions:
                session = self._sessions[project_id]
                try:
                    session["queues"].remove(queue)
                    subscriber_count = len(session["queues"])
                    logger.info(f"Suscriptor removido de proyecto {project_id}. Restantes: {subscriber_count}")
                    
                    if subscriber_count == 0 and session["is_complete"]:
                        del self._sessions[project_id]
                        logger.info(f"Sesión de proyecto {project_id} eliminada (completada y sin suscriptores)")
                    
                    return True
                except ValueError:
                    logger.warning(f"Cola no encontrada para proyecto {project_id}")
                    return False
            return False
    
    async def emit(
        self,
        project_id: str,
        agent_id: str,
        status: str,
        message: str,
        progress: Optional[int] = None,
        extra_data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Emit an event to all subscribers of a project AND store in buffer.
        
        Events are ALWAYS stored in the buffer, even if no subscribers exist.
        This ensures late-connecting subscribers receive all events.
        """
        event = {
            "agent_id": agent_id,
            "agent_name": self._get_agent_name(agent_id),
            "status": status,
            "message": message,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "project_id": project_id
        }
        
        if progress is not None:
            clamped_progress = min(max(int(progress), 0), 100)
            event["progress"] = clamped_progress
        
        if extra_data:
            event["data"] = dict(extra_data)
        
        is_final = extra_data and extra_data.get("final", False)
        
        with self._session_lock:
            session = self._ensure_session(project_id)
            
            session["buffer"].append(event)
            session["event_count"] += 1
            
            if is_final:
                session["is_complete"] = True
                session["final_event_time"] = datetime.now(timezone.utc)
                logger.info(f"Evento final recibido para proyecto {project_id}")
            
            queues = session["queues"].copy()
        
        sent_count = 0
        for queue in queues:
            try:
                await queue.put(event)
                sent_count += 1
            except Exception as e:
                logger.error(f"Error enviando evento a cola: {e}")
        
        buffer_note = f" (buffered, {len(queues)} suscriptores)" if len(queues) == 0 else f" ({sent_count} suscriptores)"
        logger.debug(f"Evento '{status}' para {project_id}{buffer_note}")
        
        return True
    
    def emit_sync(
        self,
        project_id: str,
        agent_id: str,
        status: str,
        message: str,
        progress: Optional[int] = None,
        extra_data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Synchronous wrapper for emit() - adds to buffer immediately,
        schedules queue delivery if event loop is running.
        Events are always buffered for late subscribers.
        """
        event = {
            "agent_id": agent_id,
            "agent_name": self._get_agent_name(agent_id),
            "status": status,
            "message": message,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "project_id": project_id
        }
        
        if progress is not None:
            event["progress"] = min(max(int(progress), 0), 100)
        
        if extra_data:
            event["data"] = dict(extra_data)
        
        is_final = extra_data and extra_data.get("final", False)
        
        with self._session_lock:
            session = self._ensure_session(project_id)
            session["buffer"].append(event)
            session["event_count"] += 1
            
            if is_final:
                session["is_complete"] = True
                session["final_event_time"] = datetime.now(timezone.utc)
            
            queues = session["queues"].copy()
        
        if queues:
            try:
                loop = asyncio.get_running_loop()
                for queue in queues:
                    try:
                        loop.call_soon_threadsafe(queue.put_nowait, event)
                    except Exception as e:
                        logger.warning(f"Failed to deliver event to queue: {e}")
            except RuntimeError:
                for queue in queues:
                    try:
                        queue.put_nowait(event)
                    except Exception:
                        pass
        
        return True
    
    async def emit_thinking(self, project_id: str, agent_id: str, message: str = None):
        """Emit a thinking status event"""
        agent_name = self._get_agent_name(agent_id)
        msg = message or f"{agent_name} está procesando la solicitud..."
        await self.emit(project_id, agent_id, "thinking", msg)
    
    async def emit_rag_search(self, project_id: str, agent_id: str, message: str = None):
        """Emit a RAG search status event"""
        agent_name = self._get_agent_name(agent_id)
        msg = message or f"{agent_name} consultando base de conocimiento..."
        await self.emit(project_id, agent_id, "rag_search", msg)
    
    async def emit_analyzing(self, project_id: str, agent_id: str, message: str = None, progress: int = None):
        """Emit an analyzing status event"""
        agent_name = self._get_agent_name(agent_id)
        msg = message or f"{agent_name} analizando información del proyecto..."
        await self.emit(project_id, agent_id, "analyzing", msg, progress)
    
    async def emit_sending(self, project_id: str, agent_id: str, to_agent_id: str = None):
        """Emit a sending status event"""
        agent_name = self._get_agent_name(agent_id)
        if to_agent_id:
            to_name = self._get_agent_name(to_agent_id)
            msg = f"{agent_name} enviando análisis a {to_name}..."
        else:
            msg = f"{agent_name} enviando análisis..."
        await self.emit(project_id, agent_id, "sending", msg)
    
    async def emit_auditing(self, project_id: str, agent_id: str, message: str = None):
        """Emit an auditing status event"""
        agent_name = self._get_agent_name(agent_id)
        msg = message or f"{agent_name} generando registro de auditoría..."
        await self.emit(project_id, agent_id, "auditing", msg)
    
    async def emit_complete(self, project_id: str, agent_id: str, decision: str = None, message: str = None, is_final: bool = False):
        """Emit a complete status event"""
        agent_name = self._get_agent_name(agent_id)
        if decision:
            decision_text = {
                "approve": "APROBADO",
                "reject": "RECHAZADO",
                "request_adjustment": "REQUIERE AJUSTES"
            }.get(decision, decision.upper())
            msg = message or f"{agent_name} completó análisis: {decision_text}"
        else:
            msg = message or f"{agent_name} completó su análisis"
        
        extra = {"decision": decision} if decision else {}
        if is_final:
            extra["final"] = True
        
        await self.emit(project_id, agent_id, "complete", msg, progress=100, extra_data=extra if extra else None)
    
    async def emit_final_complete(self, project_id: str, final_decision: str, message: str = None):
        """Emit the final completion event for the entire analysis"""
        decision_text = {
            "approve": "APROBADO",
            "reject": "RECHAZADO", 
            "request_adjustment": "REQUIERE AJUSTES"
        }.get(final_decision, final_decision.upper())
        
        msg = message or f"Análisis multi-agente completado: {decision_text}"
        
        await self.emit(
            project_id, 
            "SYSTEM", 
            "complete", 
            msg, 
            progress=100, 
            extra_data={"final": True, "final_decision": final_decision}
        )
    
    async def emit_error(self, project_id: str, agent_id: str, error_message: str):
        """Emit an error status event"""
        agent_name = self._get_agent_name(agent_id)
        msg = f"Error en {agent_name}: {error_message}"
        await self.emit(project_id, agent_id, "error", msg, extra_data={"error": error_message})
    
    def get_buffer_contents(self, project_id: str) -> List[Dict[str, Any]]:
        """Get the current buffer contents for a project"""
        with self._session_lock:
            if project_id in self._sessions:
                return list(self._sessions[project_id]["buffer"])
            return []
    
    def get_session_info(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a project's streaming session"""
        with self._session_lock:
            if project_id in self._sessions:
                session = self._sessions[project_id]
                return {
                    "project_id": project_id,
                    "subscriber_count": len(session["queues"]),
                    "created_at": session["created_at"].isoformat() if isinstance(session["created_at"], datetime) else session["created_at"],
                    "event_count": session["event_count"],
                    "buffer_size": len(session["buffer"]),
                    "is_complete": session["is_complete"]
                }
            return None
    
    def get_active_sessions(self) -> Dict[str, Dict[str, Any]]:
        """Get information about all active streaming sessions"""
        with self._session_lock:
            return {
                pid: {
                    "subscriber_count": len(session["queues"]),
                    "created_at": session["created_at"].isoformat() if isinstance(session["created_at"], datetime) else session["created_at"],
                    "event_count": session["event_count"],
                    "buffer_size": len(session["buffer"]),
                    "is_complete": session["is_complete"]
                }
                for pid, session in self._sessions.items()
            }
    
    def cleanup_session(self, project_id: str) -> bool:
        """Force cleanup of a project session"""
        with self._session_lock:
            if project_id in self._sessions:
                del self._sessions[project_id]
                logger.info(f"Sesión de proyecto {project_id} limpiada manualmente")
                return True
            return False
    
    def cleanup_old_sessions(self) -> int:
        """Clean up sessions that have been complete for more than SESSION_TTL_MINUTES"""
        now = datetime.now(timezone.utc)
        ttl = timedelta(minutes=SESSION_TTL_MINUTES)
        cleaned = 0
        
        with self._session_lock:
            to_delete = []
            for pid, session in self._sessions.items():
                if session["is_complete"] and session["final_event_time"]:
                    if now - session["final_event_time"] > ttl:
                        to_delete.append(pid)
            
            for pid in to_delete:
                del self._sessions[pid]
                cleaned += 1
                logger.info(f"Sesión expirada limpiada: {pid}")
        
        return cleaned


event_emitter = EventEmitter()
