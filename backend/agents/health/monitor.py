"""
Health Monitor Agent - Monitorea la salud del sistema Revisar.IA
"""
import os
import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field, asdict
from enum import Enum
import httpx
from motor.motor_asyncio import AsyncIOMotorClient

logger = logging.getLogger(__name__)


class HealthStatus(str, Enum):
    OK = "ok"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class IssueSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class HealthCheck:
    name: str
    status: HealthStatus
    message: str
    latency_ms: Optional[float] = None
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Issue:
    id: str
    severity: IssueSeverity
    type: str
    description: str
    component: str
    file: Optional[str] = None
    line: Optional[int] = None
    suggested_fix: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class HealthReport:
    agent_id: str = "HEALTH_MONITOR"
    timestamp: datetime = field(default_factory=datetime.utcnow)
    status: HealthStatus = HealthStatus.OK
    checks: List[HealthCheck] = field(default_factory=list)
    issues: List[Issue] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "timestamp": self.timestamp.isoformat(),
            "status": self.status.value,
            "checks": [asdict(c) for c in self.checks],
            "issues": [asdict(i) for i in self.issues],
            "summary": {
                "total_checks": len(self.checks),
                "passed": sum(1 for c in self.checks if c.status == HealthStatus.OK),
                "warnings": sum(1 for c in self.checks if c.status == HealthStatus.WARNING),
                "errors": sum(1 for c in self.checks if c.status in [HealthStatus.ERROR, HealthStatus.CRITICAL]),
                "total_issues": len(self.issues)
            }
        }


class HealthMonitor:
    """Agente de monitoreo de salud del sistema"""
    
    def __init__(self):
        self.mongo_uri = os.getenv("MONGODB_URI", os.getenv("MONGO_URL", ""))
        self.database_url = os.getenv("DATABASE_URL", "")
        self.base_url = os.getenv("REPLIT_DEV_DOMAIN", "localhost:5000")
        self._last_report: Optional[HealthReport] = None
        self._is_running = False
    
    async def check_all(self) -> HealthReport:
        """Ejecuta todos los health checks"""
        report = HealthReport()
        
        checks = await asyncio.gather(
            self._check_mongodb(),
            self._check_postgresql(),
            self._check_api_endpoints(),
            self._check_auth_system(),
            self._check_critical_services(),
            return_exceptions=True
        )
        
        for check in checks:
            if isinstance(check, Exception):
                report.checks.append(HealthCheck(
                    name="unknown",
                    status=HealthStatus.ERROR,
                    message=str(check)
                ))
            elif isinstance(check, list):
                report.checks.extend(check)
            else:
                report.checks.append(check)
        
        for check in report.checks:
            if check.status in [HealthStatus.ERROR, HealthStatus.CRITICAL]:
                report.issues.append(Issue(
                    id=f"issue_{check.name}_{datetime.utcnow().timestamp()}",
                    severity=IssueSeverity.HIGH if check.status == HealthStatus.ERROR else IssueSeverity.CRITICAL,
                    type="health_check_failed",
                    description=check.message,
                    component=check.name,
                    suggested_fix=self._get_suggested_fix(check.name, check.message)
                ))
        
        if any(c.status == HealthStatus.CRITICAL for c in report.checks):
            report.status = HealthStatus.CRITICAL
        elif any(c.status == HealthStatus.ERROR for c in report.checks):
            report.status = HealthStatus.ERROR
        elif any(c.status == HealthStatus.WARNING for c in report.checks):
            report.status = HealthStatus.WARNING
        else:
            report.status = HealthStatus.OK
        
        self._last_report = report
        return report
    
    async def _check_mongodb(self) -> HealthCheck:
        """Verifica conexión a MongoDB"""
        start = datetime.utcnow()
        try:
            if not self.mongo_uri:
                return HealthCheck(
                    name="mongodb",
                    status=HealthStatus.WARNING,
                    message="MONGODB_URI no configurada"
                )
            
            client = AsyncIOMotorClient(self.mongo_uri, serverSelectionTimeoutMS=5000)
            await client.admin.command('ping')
            
            db = client.get_default_database()
            collections = await db.list_collection_names()
            
            latency = (datetime.utcnow() - start).total_seconds() * 1000
            client.close()
            
            status = HealthStatus.OK if latency < 100 else HealthStatus.WARNING if latency < 500 else HealthStatus.ERROR
            
            return HealthCheck(
                name="mongodb",
                status=status,
                message=f"Conectado. {len(collections)} colecciones",
                latency_ms=latency,
                details={"collections_count": len(collections)}
            )
        except Exception as e:
            return HealthCheck(
                name="mongodb",
                status=HealthStatus.ERROR,
                message=f"Error de conexión: {str(e)}"
            )
    
    async def _check_postgresql(self) -> HealthCheck:
        """Verifica conexión a PostgreSQL"""
        start = datetime.utcnow()
        try:
            if not self.database_url:
                return HealthCheck(
                    name="postgresql",
                    status=HealthStatus.WARNING,
                    message="DATABASE_URL no configurada"
                )
            
            import asyncpg
            conn = await asyncpg.connect(self.database_url, timeout=5)
            
            result = await conn.fetchval('SELECT 1')
            
            tables = await conn.fetch("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'public' LIMIT 50
            """)
            
            latency = (datetime.utcnow() - start).total_seconds() * 1000
            await conn.close()
            
            status = HealthStatus.OK if latency < 100 else HealthStatus.WARNING if latency < 500 else HealthStatus.ERROR
            
            return HealthCheck(
                name="postgresql",
                status=status,
                message=f"Conectado. {len(tables)} tablas",
                latency_ms=latency,
                details={"tables_count": len(tables), "tables": [t['table_name'] for t in tables[:10]]}
            )
        except Exception as e:
            return HealthCheck(
                name="postgresql",
                status=HealthStatus.ERROR,
                message=f"Error de conexión: {str(e)}"
            )
    
    async def _check_api_endpoints(self) -> List[HealthCheck]:
        """Verifica endpoints críticos de la API"""
        checks = []
        endpoints = [
            ("/api/health", "GET", "health"),
            ("/api/status", "GET", "status"),
            ("/api/auth/otp/request-code", "POST", "auth_otp"),
        ]
        
        port = os.getenv("PORT", "5000")
        base = f"http://localhost:{port}"
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            for path, method, name in endpoints:
                start = datetime.utcnow()
                try:
                    url = f"{base}{path}"
                    if method == "GET":
                        response = await client.get(url)
                    else:
                        response = await client.post(url, json={})
                    
                    latency = (datetime.utcnow() - start).total_seconds() * 1000
                    
                    if response.status_code < 500:
                        status = HealthStatus.OK if latency < 200 else HealthStatus.WARNING
                        message = f"Status {response.status_code}, {latency:.0f}ms"
                    else:
                        status = HealthStatus.ERROR
                        message = f"Error {response.status_code}"
                    
                    checks.append(HealthCheck(
                        name=f"endpoint_{name}",
                        status=status,
                        message=message,
                        latency_ms=latency
                    ))
                except Exception as e:
                    checks.append(HealthCheck(
                        name=f"endpoint_{name}",
                        status=HealthStatus.ERROR,
                        message=f"No responde: {str(e)}"
                    ))
        
        return checks
    
    async def _check_auth_system(self) -> HealthCheck:
        """Verifica el sistema de autenticación"""
        try:
            import asyncpg
            conn = await asyncpg.connect(self.database_url, timeout=5)
            
            users_count = await conn.fetchval("SELECT COUNT(*) FROM users")
            otp_users = await conn.fetchval("SELECT COUNT(*) FROM usuarios_autorizados")
            
            await conn.close()
            
            if users_count == 0 and otp_users == 0:
                return HealthCheck(
                    name="auth_system",
                    status=HealthStatus.WARNING,
                    message="No hay usuarios registrados",
                    details={"users": users_count, "otp_users": otp_users}
                )
            
            return HealthCheck(
                name="auth_system",
                status=HealthStatus.OK,
                message=f"{users_count} usuarios, {otp_users} usuarios OTP",
                details={"users": users_count, "otp_users": otp_users}
            )
        except Exception as e:
            return HealthCheck(
                name="auth_system",
                status=HealthStatus.ERROR,
                message=f"Error verificando auth: {str(e)}"
            )
    
    async def _check_critical_services(self) -> HealthCheck:
        """Verifica servicios críticos"""
        services_status = []
        
        anthropic_key = os.getenv("ANTHROPIC_API_KEY") or os.getenv("AI_INTEGRATIONS_ANTHROPIC_API_KEY")
        if anthropic_key:
            services_status.append(("anthropic", True))
        else:
            services_status.append(("anthropic", False))
        
        sendgrid_key = os.getenv("SENDGRID_API_KEY")
        if sendgrid_key:
            services_status.append(("sendgrid", True))
        else:
            services_status.append(("sendgrid", False))
        
        active = [s[0] for s in services_status if s[1]]
        inactive = [s[0] for s in services_status if not s[1]]
        
        if len(inactive) > len(active):
            status = HealthStatus.WARNING
        else:
            status = HealthStatus.OK
        
        return HealthCheck(
            name="critical_services",
            status=status,
            message=f"Activos: {', '.join(active) if active else 'ninguno'}",
            details={"active": active, "inactive": inactive}
        )
    
    def _get_suggested_fix(self, component: str, message: str) -> str:
        """Genera sugerencia de fix basada en el componente y mensaje"""
        fixes = {
            "mongodb": "Verificar MONGODB_URI en variables de entorno y conectividad de red",
            "postgresql": "Verificar DATABASE_URL y que el servicio PostgreSQL esté activo",
            "auth_system": "Ejecutar script de seeding de usuarios: python -c 'from db.seed import seed_users; seed_users()'",
            "endpoint": "Reiniciar el servidor backend: pkill -f uvicorn && uvicorn server:app --reload",
            "critical_services": "Configurar API keys faltantes en variables de entorno"
        }
        
        for key, fix in fixes.items():
            if key in component.lower():
                return fix
        
        return "Revisar logs del servidor para más detalles"
    
    def get_status(self) -> Dict[str, Any]:
        """Retorna el estado actual del monitor"""
        return {
            "is_running": self._is_running,
            "last_check": self._last_report.timestamp.isoformat() if self._last_report else None,
            "last_status": self._last_report.status.value if self._last_report else None,
            "issues_count": len(self._last_report.issues) if self._last_report else 0
        }
    
    def get_last_report(self) -> Optional[Dict[str, Any]]:
        """Retorna el último reporte"""
        if self._last_report:
            return self._last_report.to_dict()
        return None


health_monitor = HealthMonitor()
