from fastapi import FastAPI, APIRouter
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List
import uuid
from datetime import datetime, timezone

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# ============================================================
# RAILWAY AUTO-CONFIGURATION
# ============================================================
# Railway sets RAILWAY_PUBLIC_DOMAIN automatically
RAILWAY_DOMAIN = os.environ.get('RAILWAY_PUBLIC_DOMAIN', '')
if RAILWAY_DOMAIN:
    # Auto-configure APP_URL and BACKEND_URL from Railway's domain
    if not os.environ.get('APP_URL'):
        os.environ['APP_URL'] = f"https://{RAILWAY_DOMAIN}"
    if not os.environ.get('BACKEND_URL'):
        os.environ['BACKEND_URL'] = f"https://{RAILWAY_DOMAIN}"
    logging.info(f"✅ Railway domain detected: {RAILWAY_DOMAIN}")

# ============================================================
# PRODUCTION STARTUP WARNINGS - Missing Environment Variables
# ============================================================
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')
MONGO_URL_ENV = os.environ.get('MONGO_URL', '')
DREAMHOST_PASSWORD = os.environ.get('DREAMHOST_EMAIL_PASSWORD', '')

missing_keys = []
if not OPENAI_API_KEY:
    missing_keys.append("OPENAI_API_KEY")
if not MONGO_URL_ENV:
    missing_keys.append("MONGO_URL")
if not DREAMHOST_PASSWORD:
    missing_keys.append("DREAMHOST_EMAIL_PASSWORD")

if missing_keys:
    logging.warning("=" * 60)
    logging.warning("⚠️  PRODUCTION WARNING: MISSING ENVIRONMENT VARIABLES")
    logging.warning("=" * 60)
    for key in missing_keys:
        logging.warning(f"   ❌ {key} is NOT SET")
    logging.warning("=" * 60)
    logging.warning("System will run in DEGRADED mode with fallback behavior.")
    logging.warning("=" * 60)

# Database connection - Demo mode or MongoDB
DEMO_MODE = False
mongo_url = os.environ.get('MONGO_URL', '')
db_name = os.environ.get('DB_NAME', 'revisar_agent_network')

if mongo_url and mongo_url.strip():
    try:
        from motor.motor_asyncio import AsyncIOMotorClient
        client = AsyncIOMotorClient(mongo_url)
        db = client[db_name]
        logging.info("Connected to MongoDB")
    except Exception as e:
        logging.warning(f"Could not connect to MongoDB: {e}. Using demo mode.")
        from services.demo_db import get_demo_database
        client, db = get_demo_database()
        DEMO_MODE = True
else:
    logging.info("MONGO_URL not set. Running in DEMO MODE with sample data.")
    from services.demo_db import get_demo_database
    client, db = get_demo_database()
    DEMO_MODE = True

# Import core routes (minimal dependencies)
from routes import projects, projects_pg, agents, dashboard, deliberation_routes, defense_file_routes, stream_routes, metrics

# Import optional routes - fail gracefully if dependencies are missing
try:
    from routes import google_services
except ImportError:
    google_services = None

try:
    from routes import rag, sql_tools, sql_query, kg_routes, analyze, health_v4
except ImportError:
    rag = sql_tools = sql_query = kg_routes = analyze = health_v4 = None

try:
    from routes import email_routes, webhooks, pcloud_routes
except ImportError:
    email_routes = webhooks = pcloud_routes = None

try:
    from routes import workflow_routes
except ImportError as e:
    logging.warning(f"Workflow routes not available: {e}")
    workflow_routes = None

try:
    from routes import proveedores
except ImportError as e:
    logging.warning(f"Proveedores routes not available: {e}")
    proveedores = None

try:
    from routes import auth
except ImportError as e:
    logging.warning(f"Auth routes not available: {e}")
    auth = None

try:
    from routes import knowledge
except ImportError as e:
    logging.warning(f"Knowledge routes not available: {e}")
    knowledge = None

try:
    from routes import kb_routes
except ImportError as e:
    logging.warning(f"KB routes not available: {e}")
    kb_routes = None

try:
    from routes import durezza
except ImportError as e:
    logging.warning(f"Revisar.IA routes not available: {e}")
    durezza = None

try:
    from routes import contexto
except ImportError as e:
    logging.warning(f"Contexto routes not available: {e}")
    contexto = None

try:
    from routes import agentes
except ImportError as e:
    logging.warning(f"Agentes routes not available: {e}")
    agentes = None

try:
    from routes import scoring
except ImportError as e:
    logging.warning(f"Scoring routes not available: {e}")
    scoring = None

try:
    from routes import versioning
except ImportError as e:
    logging.warning(f"Versioning routes not available: {e}")
    versioning = None

try:
    from routes import checklists
except ImportError as e:
    logging.warning(f"Checklists routes not available: {e}")
    checklists = None

try:
    from routes import fases
except ImportError as e:
    logging.warning(f"Fases routes not available: {e}")
    fases = None

try:
    from routes import validacion
except ImportError as e:
    logging.warning(f"Validacion routes not available: {e}")
    validacion = None

try:
    from routes import subagentes
except ImportError as e:
    logging.warning(f"Subagentes routes not available: {e}")
    subagentes = None

try:
    from routes import documentation
except ImportError as e:
    logging.warning(f"Documentation routes not available: {e}")
    documentation = None

try:
    from routes import vision_routes
except ImportError as e:
    logging.warning(f"Vision routes not available: {e}")
    vision_routes = None

try:
    from routes import defense_routes
except ImportError as e:
    logging.warning(f"Defense routes not available: {e}")
    defense_routes = None

try:
    from routes import loops
except ImportError as e:
    logging.warning(f"Loops routes not available: {e}")
    loops = None

try:
    from routes import documentos
except ImportError as e:
    logging.warning(f"Documentos routes not available: {e}")
    documentos = None

try:
    from routes import empresas
except ImportError as e:
    logging.warning(f"Empresas routes not available: {e}")
    empresas = None

try:
    from routes import templates
    logging.info("✅ Templates routes loaded successfully")
except ImportError as e:
    logging.error(f"❌ Templates routes FAILED to load: {e}")
    import traceback
    traceback.print_exc()
    templates = None

try:
    from routes import archivo_routes
except ImportError as e:
    logging.warning(f"Archivo routes not available: {e}")
    archivo_routes = None

try:
    from routes import protected_files
except ImportError as e:
    logging.warning(f"Protected files routes not available: {e}")
    protected_files = None

try:
    from routes import lista_69b
except ImportError as e:
    logging.warning(f"Lista 69B routes not available: {e}")
    lista_69b = None

try:
    from routes import upload_routes
except ImportError as e:
    logging.warning(f"Upload routes not available: {e}")
    upload_routes = None

try:
    from routes import test_routes
except ImportError as e:
    logging.warning(f"Test routes not available: {e}")
    test_routes = None

try:
    from routes import otp_auth_routes
except ImportError as e:
    logging.warning(f"OTP Auth routes not available: {e}")
    otp_auth_routes = None

try:
    from routes import support_routes
except ImportError as e:
    logging.warning(f"Support routes not available: {e}")
    support_routes = None

try:
    from routes import asistente_facturacion_routes
except ImportError as e:
    logging.warning(f"Asistente Facturacion routes not available: {e}")
    asistente_facturacion_routes = None

try:
    from routes import agents_routes
except ImportError as e:
    logging.warning(f"Agents routes not available: {e}")
    agents_routes = None

try:
    from routes import agents_stats_routes
except ImportError as e:
    logging.warning(f"Agents stats routes not available: {e}")
    agents_stats_routes = None

try:
    from routes import admin
except ImportError as e:
    logging.warning(f"Admin routes not available: {e}")
    admin = None

try:
    from routes import onboarding_routes
except ImportError as e:
    logging.warning(f"Onboarding routes not available: {e}")
    onboarding_routes = None

try:
    from routes import biblioteca_routes
except ImportError as e:
    logging.warning(f"Biblioteca routes not available: {e}")
    biblioteca_routes = None

try:
    from routes import clientes_routes
except ImportError as e:
    logging.warning(f"Clientes routes not available: {e}")
    clientes_routes = None

try:
    from routes import admin_clientes_routes
except ImportError as e:
    logging.warning(f"Admin clientes routes not available: {e}")
    admin_clientes_routes = None

try:
    from routes import disenar_routes
except ImportError as e:
    logging.warning(f"Disenar routes not available: {e}")
    disenar_routes = None

try:
    from routes import defense_files_routes
except ImportError as e:
    logging.warning(f"Defense files routes not available: {e}")
    defense_files_routes = None

try:
    from routes import trafico_routes
except ImportError as e:
    logging.warning(f"Trafico routes not available: {e}")
    trafico_routes = None

try:
    from routes import defense_file_api_routes
except ImportError as e:
    logging.warning(f"Defense file API routes not available: {e}")
    defense_file_api_routes = None

try:
    from routes import guardian_routes
except ImportError as e:
    logging.warning(f"Guardian routes not available: {e}")
    guardian_routes = None

try:
    from routes import knowledge_routes
except ImportError as e:
    logging.warning(f"Knowledge repository routes not available: {e}")
    knowledge_routes = None

try:
    from routes import usage_routes
except ImportError as e:
    logging.warning(f"Usage routes not available: {e}")
    usage_routes = None

try:
    from routes import articulos_legales_routes
except ImportError as e:
    logging.warning(f"Articulos legales routes not available: {e}")
    articulos_legales_routes = None

try:
    from routes import agent_comms
    logging.info("✅ Agent Communications routes loaded successfully")
except ImportError as e:
    logging.warning(f"Agent Communications routes not available: {e}")
    agent_comms = None

# Import middleware exception handlers
try:
    from middleware.candados_middleware import CandadoBlockedException
    from middleware.exception_handlers import candado_exception_handler
except ImportError as e:
    logging.warning(f"Candados middleware not available: {e}")
    CandadoBlockedException = None
    candado_exception_handler = None

# Import tenant context middleware for multi-tenant isolation
try:
    from middleware.tenant_context import TenantContextMiddleware
except ImportError as e:
    logging.warning(f"TenantContextMiddleware not available: {e}")
    TenantContextMiddleware = None

# Middleware para normalizar trailing slashes (redirige /api/clientes/ a /api/clientes)
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import RedirectResponse

class TrailingSlashMiddleware(BaseHTTPMiddleware):
    """Middleware que normaliza URLs removiendo trailing slash excepto para la raíz."""
    async def dispatch(self, request, call_next):
        path = request.scope.get("path", "")
        if path != "/" and path.endswith("/") and path.startswith("/api"):
            new_path = path.rstrip("/")
            query_string = request.scope.get("query_string", b"").decode()
            redirect_url = new_path + ("?" + query_string if query_string else "")
            return RedirectResponse(url=redirect_url, status_code=307)
        return await call_next(request)

# Create the main app without a prefix
app = FastAPI(
    title="Agent Network System - Trazabilidad de Servicios",
    description="Sistema de red de agentes IA para trazabilidad de servicios intangibles y consultorías especializadas",
    version="1.0.0",
    redirect_slashes=False  # Prevent redirect loops with TrailingSlashMiddleware
)

# Add trailing slash normalization middleware
app.add_middleware(TrailingSlashMiddleware)
logging.info("TrailingSlashMiddleware registered for URL normalization")

# Register exception handlers
if CandadoBlockedException and candado_exception_handler:
    app.add_exception_handler(CandadoBlockedException, candado_exception_handler)
    logging.info("Candados exception handler registered")

# Add TenantContextMiddleware for multi-tenant isolation
if TenantContextMiddleware:
    app.add_middleware(TenantContextMiddleware)
    logging.info("TenantContextMiddleware registered for multi-tenant isolation")

# Create uploads and reports directories (accessed via protected API endpoints)
uploads_path = ROOT_DIR / "uploads"
uploads_path.mkdir(exist_ok=True)
reports_path = ROOT_DIR / "reports"
reports_path.mkdir(exist_ok=True)

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")


# Root-level health check for Railway/deployment platforms
@app.get("/health")
async def root_health():
    """Simple health check at root level for deployment platforms"""
    return {"status": "ok", "service": "replicaria"}

# ============================================================
# FRONTEND BUILD PATH CONFIGURATION
# Static files are mounted AFTER routers at the end of the file
# ============================================================
FRONTEND_BUILD_PATH = ROOT_DIR.parent / "frontend" / "build"
logging.info(f"Frontend build path: {FRONTEND_BUILD_PATH}")
logging.info(f"Frontend build exists: {FRONTEND_BUILD_PATH.exists()}")


# Define Models
class StatusCheck(BaseModel):
    model_config = ConfigDict(extra="ignore")  # Ignore MongoDB's _id field
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class StatusCheckCreate(BaseModel):
    client_name: str

# Add your routes to the router instead of directly to app
@api_router.get("/")
async def root():
    return {
        "message": "Agent Network System API",
        "version": "4.0.0",
        "description": "Sistema de red de agentes IA con trazabilidad completa de 5 etapas",
        "demo_mode": DEMO_MODE,
        "endpoints": {
            "projects": "/api/projects",
            "agents": "/api/agents",
            "health": "/api/health",
            "sql": "/api/sql/query",
            "docs": "/docs"
        }
    }

@api_router.get("/health")
async def health_check():
    """
    Production Health Check Endpoint
    Returns actual connectivity status for all critical services.
    Note: Error details are hidden in production for security.
    """
    services = {}
    overall_healthy = True
    is_production = os.environ.get('ENVIRONMENT', '').lower() == 'production'

    # 1. Check MongoDB connectivity
    if DEMO_MODE:
        from services.demo_db import is_local_persistence, STORAGE_FILE
        if is_local_persistence():
            services["database"] = "local_persistence"
            if not is_production:
                services["storage_file"] = str(STORAGE_FILE)
        else:
            services["database"] = "local_persistence_new"
    else:
        try:
            await db.command("ping")
            services["database"] = "connected"
        except Exception as e:
            # Don't expose error details in production
            services["database"] = "disconnected" if is_production else f"disconnected: {str(e)[:50]}"
            logging.error(f"MongoDB health check failed: {e}")
            overall_healthy = False

    # 2. Check PostgreSQL connectivity
    db_url = os.environ.get('DATABASE_URL', '')
    if db_url:
        try:
            import asyncpg
            conn = await asyncpg.connect(db_url)
            await conn.close()
            services["postgres"] = "connected"
        except Exception as e:
            services["postgres"] = "disconnected" if is_production else f"disconnected: {str(e)[:30]}"
            logging.error(f"PostgreSQL health check failed: {e}")
            overall_healthy = False
    else:
        services["postgres"] = "not_configured"

    # 3. Check OpenAI API Key
    openai_key = os.environ.get('OPENAI_API_KEY', '')
    if openai_key and len(openai_key) > 10:
        services["llm"] = "ready"
    else:
        services["llm"] = "missing_key"
        overall_healthy = False

    # 4. Check SECRET_KEY configuration
    secret_key = os.environ.get('SECRET_KEY', '') or os.environ.get('JWT_SECRET_KEY', '')
    if secret_key and len(secret_key) >= 16:
        services["auth"] = "configured"
    else:
        services["auth"] = "insecure_default"
        if is_production:
            overall_healthy = False

    # 5. Check Email Service
    email_password = os.environ.get('DREAMHOST_EMAIL_PASSWORD', '')
    if email_password and len(email_password) > 0:
        services["email"] = "configured"
    else:
        services["email"] = "not_configured"

    # 6. Check pCloud credentials
    pcloud_user = os.environ.get('PCLOUD_USERNAME', '')
    pcloud_pass = os.environ.get('PCLOUD_PASSWORD', '')
    if pcloud_user and pcloud_pass:
        services["pcloud"] = "configured"
    else:
        services["pcloud"] = "not_configured"

    return {
        "status": "healthy" if overall_healthy else "degraded",
        "demo_mode": DEMO_MODE,
        "environment": "production" if is_production else "development",
        "services": services,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "4.0.0"
    }

@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_dict = input.model_dump()
    status_obj = StatusCheck(**status_dict)
    
    # Convert to dict and serialize datetime to ISO string for MongoDB
    doc = status_obj.model_dump()
    doc['timestamp'] = doc['timestamp'].isoformat()
    
    _ = await db.status_checks.insert_one(doc)
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    # Exclude MongoDB's _id field from the query results
    status_checks = await db.status_checks.find({}, {"_id": 0}).to_list(1000)
    
    # Convert ISO string timestamps back to datetime objects
    for check in status_checks:
        if isinstance(check['timestamp'], str):
            check['timestamp'] = datetime.fromisoformat(check['timestamp'])
    
    return status_checks

# Include core routers (always available)
api_router.include_router(projects.router)
api_router.include_router(projects_pg.router)
api_router.include_router(agents.router)
api_router.include_router(deliberation_routes.router)
api_router.include_router(defense_file_routes.router)
api_router.include_router(stream_routes.router)
api_router.include_router(metrics.router)

# Include optional routers - only if dependencies available
if auth:
    api_router.include_router(auth.router)
if rag:
    api_router.include_router(rag.router)
if kg_routes:
    api_router.include_router(kg_routes.router)
if analyze:
    api_router.include_router(analyze.router)
if health_v4:
    api_router.include_router(health_v4.router)
if sql_tools:
    api_router.include_router(sql_tools.router)
if sql_query:
    api_router.include_router(sql_query.router)
if webhooks:
    api_router.include_router(webhooks.router)
if workflow_routes:
    app.include_router(workflow_routes.router)
if google_services:
    api_router.include_router(google_services.router, prefix="/google", tags=["Google Services"])
if email_routes:
    api_router.include_router(email_routes.router)
if pcloud_routes:
    api_router.include_router(pcloud_routes.router)
if knowledge:
    api_router.include_router(knowledge.router)
if kb_routes:
    app.include_router(kb_routes.router)
if articulos_legales_routes:
    app.include_router(articulos_legales_routes.router)
if durezza:
    app.include_router(durezza.router)
if contexto:
    app.include_router(contexto.router)
if agentes:
    app.include_router(agentes.router)
if scoring:
    app.include_router(scoring.router)
if checklists:
    app.include_router(checklists.router)
    if hasattr(checklists, 'projects_router'):
        app.include_router(checklists.projects_router, prefix="/api/proyectos")
if fases:
    app.include_router(fases.router)
if validacion:
    app.include_router(validacion.router)
if subagentes:
    app.include_router(subagentes.router)
if documentation:
    api_router.include_router(documentation.router)
if otp_auth_routes:
    api_router.include_router(otp_auth_routes.router)
if vision_routes:
    api_router.include_router(vision_routes.router)
if defense_routes:
    api_router.include_router(defense_routes.router)
if loops:
    app.include_router(loops.router)
if versioning:
    app.include_router(versioning.router)
if documentos:
    app.include_router(documentos.router)
if empresas:
    api_router.include_router(empresas.router)
if templates:
    api_router.include_router(templates.router)
if archivo_routes:
    app.include_router(archivo_routes.router)
    if hasattr(archivo_routes, 'onboarding_router'):
        app.include_router(archivo_routes.onboarding_router)
if protected_files:
    app.include_router(protected_files.router)
if upload_routes:
    app.include_router(upload_routes.router)
if proveedores:
    app.include_router(proveedores.router)
if test_routes:
    api_router.include_router(test_routes.router)
if support_routes:
    api_router.include_router(support_routes.router)
if asistente_facturacion_routes:
    app.include_router(asistente_facturacion_routes.router)
if admin:
    api_router.include_router(admin.router)
if onboarding_routes:
    app.include_router(onboarding_routes.router)
if biblioteca_routes:
    app.include_router(biblioteca_routes.router)
if clientes_routes:
    app.include_router(clientes_routes.router)
if admin_clientes_routes:
    app.include_router(admin_clientes_routes.router)
if agents_routes:
    app.include_router(agents_routes.router)
if agents_stats_routes:
    app.include_router(agents_stats_routes.router)
if disenar_routes:
    app.include_router(disenar_routes.router, prefix="/api/disenar", tags=["Diseñar.IA"])
if defense_files_routes:
    app.include_router(defense_files_routes.router)
if lista_69b:
    app.include_router(lista_69b.router)
if trafico_routes:
    app.include_router(trafico_routes.router, prefix="/api/trafico", tags=["Tráfico.IA"])
if defense_file_api_routes:
    app.include_router(defense_file_api_routes.router, tags=["Defense Files"])
if guardian_routes:
    app.include_router(guardian_routes.router, tags=["Guardian.IA"])
if knowledge_routes:
    app.include_router(knowledge_routes.router, prefix="/api", tags=["Knowledge Repository"])
if usage_routes:
    app.include_router(usage_routes.router, tags=["Usage & Rate Limiting"])
if agent_comms:
    api_router.include_router(agent_comms.router)
    logging.info("✅ Agent Communications routes registered at /api/agent-comms")

# ============================================================
# RESET DEMO DATA ENDPOINT - Direct on app for reliability
# ============================================================
RESET_SECRET = os.environ.get('RESET_SECRET_KEY', 'satma-reset-2024-confirmado')

@app.post("/reset-demo")
async def reset_demo_data_direct(secret_key: str = ""):
    """Reset all demo data. Requires secret_key as query param."""
    if secret_key != RESET_SECRET:
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Invalid secret key")

    import asyncpg
    import re
    db_url = os.environ.get('DATABASE_URL', '')
    if db_url.startswith('postgres://'):
        db_url = db_url.replace('postgres://', 'postgresql://', 1)
    db_url = re.sub(r'[?&]sslmode=[^&]*', '', db_url)

    if not db_url:
        return {"error": "DATABASE_URL not configured"}

    try:
        conn = await asyncpg.connect(db_url, ssl='require')
        results = {"cleaned": [], "errors": []}

        tables = [
            'clientes_historial', 'clientes_interacciones', 'clientes_contexto',
            'clientes_documentos', 'proveedores_scoring', 'df_proveedores',
            'df_documents', 'df_metadata', 'kb_chunk_agente', 'kb_chunks',
            'kb_documentos', 'kb_metricas', 'projects', 'clientes', 'proveedores'
        ]

        for table in tables:
            try:
                exists = await conn.fetchval(
                    "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = $1)", table
                )
                if exists:
                    count = await conn.fetchval(f'SELECT COUNT(*) FROM {table}')
                    await conn.execute(f'DELETE FROM {table}')
                    results["cleaned"].append({"table": table, "deleted": count})
            except Exception as e:
                results["errors"].append({"table": table, "error": str(e)[:50]})

        # Clean non-admin users
        try:
            await conn.execute('''
                DELETE FROM auth_users
                WHERE email NOT IN ('ia@satma.mx', 'admin@revisar-ia.com')
                AND role NOT IN ('super_admin', 'admin')
            ''')
        except:
            pass

        await conn.close()

        # Also clean MongoDB - ALL collections including durezza_*
        mongo_results = {"cleaned": [], "errors": []}
        try:
            if db is not None:
                # Clean standard collections
                for coll_name in ['projects', 'agents', 'deliberations', 'agent_interactions']:
                    try:
                        count = await db[coll_name].count_documents({})
                        await db[coll_name].delete_many({})
                        mongo_results["cleaned"].append({"collection": coll_name, "deleted": count})
                    except:
                        pass

                # Clean durezza_* collections (Revisar.ia dashboard data)
                durezza_collections = [
                    'durezza_projects', 'durezza_suppliers', 'durezza_project_phases',
                    'durezza_deliberations', 'durezza_defense_files', 'durezza_checklist_templates',
                    'durezza_agent_configs', 'durezza_documents', 'durezza_audit_logs'
                ]
                for coll_name in durezza_collections:
                    try:
                        count = await db[coll_name].count_documents({})
                        await db[coll_name].delete_many({})
                        mongo_results["cleaned"].append({"collection": coll_name, "deleted": count})
                    except:
                        pass
        except Exception as e:
            mongo_results["errors"].append({"error": str(e)[:100]})

        # Clean in-memory demo data
        demo_results = {"cleaned": []}
        try:
            from services.durezza_database import (
                DEMO_PROJECTS, DEMO_SUPPLIERS, DEMO_PROJECT_PHASES,
                DEMO_DELIBERATIONS, DEMO_DEFENSE_FILES, DEMO_DOCUMENTS
            )
            demo_lists = [
                ('DEMO_PROJECTS', DEMO_PROJECTS),
                ('DEMO_SUPPLIERS', DEMO_SUPPLIERS),
                ('DEMO_PROJECT_PHASES', DEMO_PROJECT_PHASES),
                ('DEMO_DELIBERATIONS', DEMO_DELIBERATIONS),
                ('DEMO_DEFENSE_FILES', DEMO_DEFENSE_FILES),
                ('DEMO_DOCUMENTS', DEMO_DOCUMENTS)
            ]
            for name, lst in demo_lists:
                count = len(lst)
                lst.clear()
                demo_results["cleaned"].append({"list": name, "cleared": count})
        except Exception as e:
            demo_results["error"] = str(e)[:100]

        results["demo_memory"] = demo_results

        results["mongodb"] = mongo_results
        return {"success": True, "results": results}

    except Exception as e:
        return {"success": False, "error": str(e)}

# Include the router in the main app - api_router MUST be included first
# to ensure /api/projects/folios is matched before dashboard's /projects/{project_id}
app.include_router(api_router)
app.include_router(dashboard.router)
app.include_router(dashboard.dashboard_router)

# ============================================================
# SERVE FRONTEND IN PRODUCTION - CORRECTED STATIC FILE HANDLING
# ============================================================
# FRONTEND_BUILD_PATH is defined earlier in the file
if FRONTEND_BUILD_PATH.exists():
    # Mount static files AFTER all routers are included
    static_dir = FRONTEND_BUILD_PATH / "static"
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static_files")
        logging.info(f"✅ Mounted /static from {static_dir}")
    
    @app.get("/")
    async def serve_frontend():
        """Serve frontend index.html"""
        return FileResponse(str(FRONTEND_BUILD_PATH / "index.html"))
    
    @app.get("/{full_path:path}")
    async def serve_frontend_routes(full_path: str):
        """Serve frontend for all non-API routes (SPA routing)"""
        from fastapi import HTTPException
        
        # Skip API routes and docs - let them 404 properly
        if full_path.startswith("api/") or full_path.startswith("docs") or full_path.startswith("openapi"):
            raise HTTPException(status_code=404, detail="Not found")
        
        # CRITICAL: Serve static files directly from build/static/
        if full_path.startswith("static/"):
            static_file = FRONTEND_BUILD_PATH / full_path
            if static_file.exists() and static_file.is_file():
                return FileResponse(str(static_file))
            raise HTTPException(status_code=404, detail="Static file not found")
        
        # Check if it's a static file in build root (favicon, logo, manifest.json, etc)
        root_file = FRONTEND_BUILD_PATH / full_path
        if root_file.exists() and root_file.is_file():
            return FileResponse(str(root_file))
        
        # Return index.html for SPA routing (React Router)
        return FileResponse(str(FRONTEND_BUILD_PATH / "index.html"))
else:
    # Development mode - API only
    @app.get("/")
    async def app_root():
        """API root endpoint"""
        return {
            "name": "Revisar.IA Multi-Agent System API",
            "version": "2.0",
            "status": "running",
            "docs": "/docs",
            "endpoints": {
                "stats": "/api/stats",
                "projects": "/api/projects",
                "agents": "/api/agents",
                "defense_files": "/api/defense-files"
            }
        }

# CORS configuration with secure defaults
CORS_DEFAULT_ORIGINS = "https://replicar-ia.vercel.app,http://localhost:3000,http://localhost:5173"
cors_origins_str = os.environ.get('CORS_ORIGINS', '')
if not cors_origins_str or cors_origins_str.strip() == '*':
    # Use secure defaults instead of wildcard
    cors_origins = CORS_DEFAULT_ORIGINS.split(',')
    logging.info(f"CORS: Using default origins (no wildcard): {cors_origins}")
else:
    cors_origins = [origin.strip() for origin in cors_origins_str.split(',') if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=cors_origins,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Empresa-ID", "X-Request-ID"],
    expose_headers=["Content-Type", "X-Request-ID"]
)

# Add middleware to prevent caching
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

class NoCacheMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        # Add no-cache headers to all API responses
        if request.url.path.startswith('/api/'):
            response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'
        return response

app.add_middleware(NoCacheMiddleware)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def seed_usuarios_autorizados():
    """Create default authorized users if they don't exist - seeds BOTH tables"""
    import asyncpg
    import os
    import bcrypt
    import uuid
    
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        logger.warning("DATABASE_URL not set, skipping user seeding")
        return
    
    try:
        conn = await asyncpg.connect(db_url)
        
        # Seed usuarios_autorizados table (for OTP login)
        count_otp = await conn.fetchval("SELECT COUNT(*) FROM usuarios_autorizados")
        if count_otp == 0:
            logger.info("Seeding usuarios_autorizados table...")
            default_otp_users = [
                ('usr-001', 'admin@revisar-ia.com', 'Administrador Sistema', 'Revisar.IA', 'admin', True),
                ('usr-002', 'demo@revisar-ia.com', 'Usuario Demo', 'Demo Corp', 'user', True),
            ]
            await conn.executemany(
                """INSERT INTO usuarios_autorizados (id, email, nombre, empresa, rol, activo) 
                   VALUES ($1, $2, $3, $4, $5, $6) ON CONFLICT (id) DO NOTHING""",
                default_otp_users
            )
            logger.info(f"Seeded {len(default_otp_users)} OTP users")
        else:
            logger.info(f"Found {count_otp} existing OTP users")
        
        # Seed users table (for password login - admin)
        # Support multiple admin users via ADMIN_EMAIL, ADMIN_EMAIL_2, ADMIN_EMAIL_3, etc.
        admin_configs = []

        # Primary admin
        admin_password = os.environ.get('ADMIN_PASSWORD')
        admin_email = os.environ.get('ADMIN_EMAIL')
        if admin_email and admin_password:
            admin_configs.append({
                'email': admin_email,
                'password': admin_password,
                'name': os.environ.get('ADMIN_NAME', 'Administrator'),
                'company': os.environ.get('ADMIN_COMPANY', 'Default')
            })

        # Additional admins (ADMIN_EMAIL_2, ADMIN_EMAIL_3, etc.)
        for i in range(2, 10):
            admin_email_n = os.environ.get(f'ADMIN_EMAIL_{i}')
            admin_password_n = os.environ.get(f'ADMIN_PASSWORD_{i}')
            if admin_email_n and admin_password_n:
                admin_configs.append({
                    'email': admin_email_n,
                    'password': admin_password_n,
                    'name': os.environ.get(f'ADMIN_NAME_{i}', f'Administrator {i}'),
                    'company': os.environ.get(f'ADMIN_COMPANY_{i}', 'Default')
                })

        if not admin_configs:
            logger.warning("⚠️ No ADMIN_EMAIL/ADMIN_PASSWORD configured - skipping admin user seeding")
        else:
            logger.info(f"Seeding {len(admin_configs)} admin users in users table...")
            for admin_config in admin_configs:
                password_hash = bcrypt.hashpw(admin_config['password'].encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                admin_id = str(uuid.uuid4())

                await conn.execute(
                    """INSERT INTO users (id, email, full_name, password_hash, role, is_active, approval_status, company, auth_provider)
                       VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                       ON CONFLICT (email) DO UPDATE SET password_hash = $4, is_active = $6, approval_status = $7""",
                    admin_id, admin_config['email'], admin_config['name'], password_hash, 'admin', True, 'approved', admin_config['company'], 'email'
                )
                logger.info(f"Admin user seeded/updated: {admin_config['email']}")
        
        await conn.close()
        logger.info("User seeding completed successfully")
    except Exception as e:
        logger.warning(f"Could not seed users: {e}")


async def start_guardian_agent():
    """Initialize and start the Guardian Agent for system monitoring"""
    try:
        from services.agents.guardian_agent import GuardianAgent
        from routes import guardian_routes
        
        if guardian_routes:
            guardian = GuardianAgent()
            await guardian.iniciar()
            guardian_routes._guardian_instance = guardian
            logger.info("🛡️ Guardian Agent started automatically on server startup")
            return True
    except Exception as e:
        logger.warning(f"Could not start Guardian Agent: {e}")
    return False


async def start_trafico_ia():
    """Initialize and start Tráfico.IA monitoring service"""
    try:
        from routes import trafico_routes
        
        if trafico_routes:
            trafico_service = trafico_routes.init_trafico_service(db=db)
            await trafico_service.iniciar()
            await trafico_service.ejecutar_monitoreo()
            logger.info("🚦 Tráfico.IA started automatically on server startup")
            return True
    except Exception as e:
        logger.warning(f"Could not start Tráfico.IA: {e}")
    return False


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    import asyncio
    from services.event_stream import event_emitter
    from services.database import create_multi_tenant_indexes

    # ============================================================
    # INICIALIZACIÓN DE BASE DE DATOS
    # ============================================================
    # Por ahora usar sistema legacy hasta que el unificado esté completamente probado
    try:
        from services.user_db import init_db
        await init_db()
        await seed_usuarios_autorizados()
        logger.info("✅ Sistema de autenticación inicializado")
    except Exception as e:
        logger.error(f"Error inicializando autenticación: {e}")
    
    # Start Guardian Agent for system monitoring
    await start_guardian_agent()
    
    # Start Tráfico.IA monitoring service
    await start_trafico_ia()
    
    from services import user_db
    if user_db.async_session_factory:
        try:
            if biblioteca_routes:
                biblioteca_routes.init_biblioteca_services(user_db.async_session_factory)
                logger.info("Biblioteca RAG services initialized")
            if kb_routes:
                kb_routes.init_kb_rag_services(user_db.async_session_factory)
                logger.info("KB routes RAG services initialized")
        except Exception as e:
            logger.warning(f"Could not initialize RAG services: {e}")
    
    try:
        await create_multi_tenant_indexes()
        logger.info("Multi-tenant MongoDB indexes initialized")
    except Exception as e:
        logger.warning(f"Could not create multi-tenant indexes: {e}")
    
    async def cleanup_old_sessions():
        """Background task to clean up old SSE sessions every 5 minutes"""
        while True:
            try:
                await asyncio.sleep(300)
                cleaned = event_emitter.cleanup_old_sessions()
                if cleaned > 0:
                    logger.info(f"SSE cleanup: removed {cleaned} expired sessions")
            except asyncio.CancelledError:
                logger.info("SSE cleanup task cancelled")
                break
            except Exception as e:
                logger.error(f"SSE cleanup error: {e}", exc_info=True)
                await asyncio.sleep(60)
    
    cleanup_task = asyncio.create_task(cleanup_old_sessions())
    cleanup_task.add_done_callback(
        lambda t: logger.warning(f"SSE cleanup task ended unexpectedly: {t.exception()}") if t.exception() else None
    )
    
    from services.scheduler_service import scheduler_service
    await scheduler_service.start()
    logger.info("Application startup complete - SSE cleanup and scheduler tasks started")

@app.on_event("shutdown")
async def shutdown_db_client():
    from services.scheduler_service import scheduler_service
    await scheduler_service.stop()
    
    # Stop Guardian Agent
    try:
        from routes import guardian_routes
        if guardian_routes and guardian_routes._guardian_instance:
            await guardian_routes._guardian_instance.detener()
            guardian_routes._guardian_instance = None
            logger.info("🛡️ Guardian Agent stopped on server shutdown")
    except Exception as e:
        logger.warning(f"Error stopping Guardian Agent: {e}")
    
    # Stop Tráfico.IA service
    try:
        from routes import trafico_routes
        if trafico_routes and trafico_routes.trafico_service:
            await trafico_routes.trafico_service.detener()
            logger.info("🚦 Tráfico.IA stopped on server shutdown")
    except Exception as e:
        logger.warning(f"Error stopping Tráfico.IA: {e}")
    
    client.close()
