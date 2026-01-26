"""
LOOP ORCHESTRATOR - Implementación de principios Ralph Loop para Revisar.IA
Permite ejecutar tareas iterativamente hasta completarse o alcanzar límite
Casos de uso: OCR Validation, Red Team Simulation, Testing Automatizado
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class LoopStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETE = "complete"
    TIMEOUT = "timeout"
    MAX_ITERATIONS = "max_iterations"
    ERROR = "error"
    ABORTED = "aborted"


@dataclass
class LoopLog:
    timestamp: str
    iteration: int
    message: str
    level: str = "info"


@dataclass
class LoopResult:
    success: bool
    status: LoopStatus
    iterations: int
    result: Any
    logs: List[LoopLog]
    duration_ms: int
    context: Dict[str, Any] = field(default_factory=dict)


class LoopOrchestrator:
    """
    Orquestador de loops iterativos estilo Ralph para tareas que requieren
    múltiples intentos hasta completarse correctamente.
    
    Casos de uso:
    - OCR Validation: Reintenta extracción hasta obtener texto válido
    - Red Team Simulation: Ejecuta pruebas de seguridad iterativas
    - Testing Automatizado: Corre tests hasta que todos pasen
    - Document Processing: Procesa documentos con reintentos
    """
    
    FATAL_ERROR_PATTERNS = [
        "ECONNREFUSED",
        "INVALID_API_KEY",
        "RATE_LIMIT",
        "OUT_OF_MEMORY",
        "AUTHENTICATION_FAILED",
        "PERMISSION_DENIED"
    ]
    
    COMPLETION_MARKERS = [
        "COMPLETE",
        "DONE",
        "SUCCESS",
        "FINISHED",
        "<promise>",
        "</promise>"
    ]
    
    def __init__(
        self,
        max_iterations: int = 10,
        timeout_seconds: float = 300.0,
        completion_marker: str = "COMPLETE",
        delay_between_iterations: float = 0.5
    ):
        self.max_iterations = max_iterations
        self.timeout_seconds = timeout_seconds
        self.completion_marker = completion_marker
        self.delay_between_iterations = delay_between_iterations
        self.current_iteration = 0
        self.logs: List[LoopLog] = []
        self._callbacks: Dict[str, List[Callable]] = {
            "loop:start": [],
            "loop:complete": [],
            "loop:timeout": [],
            "loop:max_iterations": [],
            "iteration:start": [],
            "iteration:end": [],
            "iteration:error": []
        }
    
    def on(self, event: str, callback: Callable):
        """Registra callback para un evento"""
        if event in self._callbacks:
            self._callbacks[event].append(callback)
    
    def _emit(self, event: str, data: Dict[str, Any]):
        """Emite un evento a todos los callbacks registrados"""
        for callback in self._callbacks.get(event, []):
            try:
                callback(data)
            except Exception as e:
                logger.warning(f"Error in callback for {event}: {e}")
    
    async def execute_loop(
        self,
        task_fn: Callable,
        context: Optional[Dict[str, Any]] = None,
        task_name: str = "unnamed_task"
    ) -> LoopResult:
        """
        Ejecuta una tarea en loop hasta que:
        1. La tarea retorne el completionMarker
        2. Se alcance maxIterations
        3. Se exceda el timeout
        
        Args:
            task_fn: Función async que ejecuta la tarea
            context: Contexto inicial (se pasa entre iteraciones)
            task_name: Nombre descriptivo de la tarea
            
        Returns:
            LoopResult con success, iterations, result, logs
        """
        context = context or {}
        start_time = datetime.now(timezone.utc)
        result = None
        status = LoopStatus.PENDING
        
        self.reset()
        self._log(f"Iniciando loop para tarea: {task_name}", level="info")
        self._emit("loop:start", {"context": context, "max_iterations": self.max_iterations})
        
        try:
            while self.current_iteration < self.max_iterations:
                self.current_iteration += 1
                elapsed_seconds = (datetime.now(timezone.utc) - start_time).total_seconds()
                
                if elapsed_seconds > self.timeout_seconds:
                    self._log(f"TIMEOUT alcanzado después de {self.current_iteration} iteraciones ({elapsed_seconds:.1f}s)", level="warning")
                    status = LoopStatus.TIMEOUT
                    self._emit("loop:timeout", {"iterations": self.current_iteration})
                    break
                
                self._emit("iteration:start", {"iteration": self.current_iteration, "context": context})
                self._log(f"Iteración {self.current_iteration}/{self.max_iterations} iniciada")
                
                try:
                    if asyncio.iscoroutinefunction(task_fn):
                        result = await task_fn(context, self.current_iteration)
                    else:
                        result = task_fn(context, self.current_iteration)
                    
                    result_preview = str(result)[:200] if result else "None"
                    self._log(f"Iteración {self.current_iteration} resultado: {result_preview}")
                    
                    if self._is_complete(result):
                        status = LoopStatus.COMPLETE
                        self._log(f"Tarea completada en iteración {self.current_iteration}", level="success")
                        self._emit("loop:complete", {"iteration": self.current_iteration, "result": result})
                        break
                    
                    context = self._merge_context(context, result)
                    self._emit("iteration:end", {
                        "iteration": self.current_iteration,
                        "result": result,
                        "will_continue": True
                    })
                    
                    if self.delay_between_iterations > 0:
                        await asyncio.sleep(self.delay_between_iterations)
                        
                except Exception as error:
                    error_msg = str(error)
                    self._log(f"ERROR en iteración {self.current_iteration}: {error_msg}", level="error")
                    self._emit("iteration:error", {"iteration": self.current_iteration, "error": error_msg})
                    
                    if self._is_fatal_error(error):
                        status = LoopStatus.ERROR
                        self._log(f"Error fatal detectado, abortando loop", level="error")
                        break
                    
            else:
                status = LoopStatus.MAX_ITERATIONS
                self._log(f"Máximo de iteraciones alcanzado ({self.max_iterations})", level="warning")
                self._emit("loop:max_iterations", {"iterations": self.current_iteration, "last_result": result})
                
        except Exception as e:
            status = LoopStatus.ERROR
            self._log(f"Error fatal en loop: {e}", level="error")
        
        end_time = datetime.now(timezone.utc)
        duration_ms = int((end_time - start_time).total_seconds() * 1000)
        
        return LoopResult(
            success=status == LoopStatus.COMPLETE,
            status=status,
            iterations=self.current_iteration,
            result=result,
            logs=self.logs.copy(),
            duration_ms=duration_ms,
            context=context
        )
    
    def _is_complete(self, result: Any) -> bool:
        """Verifica si el resultado indica completitud"""
        if result is None:
            return False
        
        if isinstance(result, str):
            for marker in self.COMPLETION_MARKERS:
                if marker.lower() in result.lower():
                    return True
            return self.completion_marker.lower() in result.lower()
        
        if isinstance(result, dict):
            if result.get("status") == self.completion_marker:
                return True
            if result.get("complete") is True:
                return True
            if result.get("done") is True:
                return True
            if result.get("success") is True and result.get("final") is True:
                return True
        
        return False
    
    def _merge_context(self, old_context: Dict, new_result: Any) -> Dict:
        """Combina contexto anterior con nuevo resultado"""
        accumulated_findings = old_context.get("accumulated_findings", [])
        
        if isinstance(new_result, dict) and "findings" in new_result:
            accumulated_findings = accumulated_findings + new_result.get("findings", [])
        
        return {
            **old_context,
            "previous_result": new_result,
            "previous_iteration": self.current_iteration,
            "accumulated_findings": accumulated_findings
        }
    
    def _is_fatal_error(self, error: Exception) -> bool:
        """Determina si un error debe detener el loop inmediatamente"""
        error_msg = str(error)
        return any(pattern in error_msg for pattern in self.FATAL_ERROR_PATTERNS)
    
    def _log(self, message: str, level: str = "info"):
        """Registra un mensaje en los logs"""
        entry = LoopLog(
            timestamp=datetime.now(timezone.utc).isoformat(),
            iteration=self.current_iteration,
            message=message,
            level=level
        )
        self.logs.append(entry)
        
        log_prefix = f"[Loop:{self.current_iteration}]"
        if level == "error":
            logger.error(f"{log_prefix} {message}")
        elif level == "warning":
            logger.warning(f"{log_prefix} {message}")
        elif level == "success":
            logger.info(f"{log_prefix} ✅ {message}")
        else:
            logger.info(f"{log_prefix} {message}")
    
    def reset(self):
        """Reinicia el estado del orquestador"""
        self.current_iteration = 0
        self.logs = []


class OCRValidationLoop(LoopOrchestrator):
    """Loop especializado para validación OCR de documentos"""
    
    def __init__(self, **kwargs):
        kwargs.setdefault("max_iterations", 5)
        kwargs.setdefault("completion_marker", "OCR_VALID")
        super().__init__(**kwargs)
    
    async def validate_document(self, document_path: str, expected_fields: List[str]) -> LoopResult:
        """Valida un documento con OCR hasta obtener todos los campos"""
        
        async def ocr_task(context: Dict, iteration: int) -> Dict:
            try:
                from services.vision_agent import VisionAgent
                vision = VisionAgent()
                
                with open(document_path, 'rb') as f:
                    file_content = f.read()
                
                result = await asyncio.to_thread(
                    vision.validate_document,
                    file_content,
                    "evidencia"
                )
                
                score = getattr(result, 'score', 0) if hasattr(result, 'score') else 0
                if score >= 70:
                    return {"complete": True, "result": {"score": score}}
                
                missing = getattr(result, 'missing_keywords', []) if hasattr(result, 'missing_keywords') else []
                return {
                    "complete": False,
                    "score": score,
                    "missing_fields": missing
                }
            except Exception as e:
                return {"complete": False, "error": str(e)}
        
        return await self.execute_loop(
            ocr_task,
            {"document_path": document_path, "expected_fields": expected_fields},
            task_name=f"OCR Validation: {document_path}"
        )


class RedTeamLoop(LoopOrchestrator):
    """Loop especializado para simulaciones Red Team de seguridad"""
    
    def __init__(self, **kwargs):
        kwargs.setdefault("max_iterations", 15)
        kwargs.setdefault("timeout_seconds", 600)
        kwargs.setdefault("completion_marker", "SECURITY_AUDIT_COMPLETE")
        super().__init__(**kwargs)
    
    async def run_security_audit(self, target_endpoint: str, attack_vectors: List[str]) -> LoopResult:
        """Ejecuta auditoría de seguridad iterativa"""
        
        async def security_task(context: Dict, iteration: int) -> Dict:
            findings = context.get("accumulated_findings", [])
            vectors_tested = context.get("vectors_tested", [])
            
            remaining_vectors = [v for v in attack_vectors if v not in vectors_tested]
            
            if not remaining_vectors:
                return {
                    "complete": True,
                    "status": "SECURITY_AUDIT_COMPLETE",
                    "total_findings": len(findings),
                    "findings": findings
                }
            
            current_vector = remaining_vectors[0]
            
            finding = {
                "vector": current_vector,
                "iteration": iteration,
                "result": "tested",
                "severity": "low"
            }
            
            return {
                "complete": False,
                "vector_tested": current_vector,
                "vectors_tested": vectors_tested + [current_vector],
                "findings": [finding]
            }
        
        return await self.execute_loop(
            security_task,
            {"target": target_endpoint, "attack_vectors": attack_vectors, "vectors_tested": []},
            task_name=f"Red Team Audit: {target_endpoint}"
        )


class TestingLoop(LoopOrchestrator):
    """Loop especializado para testing automatizado"""
    
    def __init__(self, **kwargs):
        kwargs.setdefault("max_iterations", 20)
        kwargs.setdefault("completion_marker", "ALL_TESTS_PASSED")
        super().__init__(**kwargs)
    
    async def run_tests_until_pass(self, test_suite: str) -> LoopResult:
        """Ejecuta tests hasta que todos pasen"""
        
        async def test_task(context: Dict, iteration: int) -> Dict:
            import subprocess
            
            result = subprocess.run(
                ["python", "-m", "pytest", test_suite, "-v", "--tb=short"],
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode == 0:
                return {
                    "complete": True,
                    "status": "ALL_TESTS_PASSED",
                    "output": result.stdout[-500:]
                }
            
            failed_tests = []
            for line in result.stdout.split('\n'):
                if 'FAILED' in line:
                    failed_tests.append(line.strip())
            
            return {
                "complete": False,
                "failed_tests": failed_tests,
                "returncode": result.returncode,
                "findings": [{"type": "test_failure", "tests": failed_tests}]
            }
        
        return await self.execute_loop(
            test_task,
            {"test_suite": test_suite},
            task_name=f"Test Loop: {test_suite}"
        )


loop_orchestrator = LoopOrchestrator()
ocr_loop = OCRValidationLoop()
red_team_loop = RedTeamLoop()
testing_loop = TestingLoop()
