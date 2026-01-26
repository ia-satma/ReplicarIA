#!/usr/bin/env python3
"""
Verificación de preparación para producción del sistema SATMA/Revisar.ia
Ejecutar: python backend/scripts/verify_production.py
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncio
from typing import Tuple, List

class ProductionVerifier:
    def __init__(self):
        self.results: List[Tuple[str, bool, str]] = []
        self.all_passed = True
    
    def add_result(self, check_name: str, passed: bool, detail: str = ""):
        self.results.append((check_name, passed, detail))
        if not passed:
            self.all_passed = False
    
    def check_env_vars(self):
        required_vars = {
            "DATABASE_URL": "PostgreSQL connection string",
            "MONGO_URL": "MongoDB connection string", 
            "JWT_SECRET": "JWT signing secret",
        }
        
        anthropic_vars = [
            "ANTHROPIC_API_KEY",
            "AI_INTEGRATIONS_ANTHROPIC_API_KEY"
        ]
        
        for var, desc in required_vars.items():
            value = os.environ.get(var)
            if value and len(value) > 5:
                self.add_result(f"ENV: {var}", True, desc)
            else:
                self.add_result(f"ENV: {var}", False, f"Missing or empty: {desc}")
        
        anthropic_found = any(os.environ.get(v) for v in anthropic_vars)
        if anthropic_found:
            found_var = next(v for v in anthropic_vars if os.environ.get(v))
            self.add_result("ENV: ANTHROPIC_API_KEY", True, f"Found as {found_var}")
        else:
            self.add_result("ENV: ANTHROPIC_API_KEY", False, "Missing Anthropic API key")
    
    def check_postgresql(self):
        database_url = os.environ.get("DATABASE_URL")
        if not database_url:
            self.add_result("PostgreSQL Connection", False, "DATABASE_URL not set")
            return
        
        async def test_connection():
            import asyncpg
            from urllib.parse import urlparse, parse_qs
            
            parsed = urlparse(database_url)
            query_params = parse_qs(parsed.query)
            ssl_mode = query_params.get('sslmode', ['require'])[0]
            
            conn = await asyncpg.connect(
                user=parsed.username,
                password=parsed.password,
                host=parsed.hostname,
                port=parsed.port or 5432,
                database=parsed.path.lstrip('/'),
                ssl='require' if ssl_mode != 'disable' else False
            )
            result = await conn.fetchval("SELECT 1")
            await conn.close()
            return result
        
        try:
            result = asyncio.get_event_loop().run_until_complete(test_connection())
            if result == 1:
                self.add_result("PostgreSQL Connection", True, "Query successful (asyncpg)")
            else:
                self.add_result("PostgreSQL Connection", False, "Query failed")
        except Exception as e:
            self.add_result("PostgreSQL Connection", False, str(e)[:60])
    
    def check_mongodb(self):
        try:
            from pymongo import MongoClient
            from urllib.parse import urlparse
            mongo_url = os.environ.get("MONGO_URL")
            
            if not mongo_url:
                self.add_result("MongoDB Connection", False, "MONGO_URL not set (demo mode)")
                return
            
            client = MongoClient(mongo_url, serverSelectionTimeoutMS=5000)
            client.admin.command('ping')
            
            parsed = urlparse(mongo_url)
            db_name = parsed.path.lstrip('/').split('?')[0] if parsed.path else 'satma'
            if not db_name:
                db_name = 'satma'
            
            db = client[db_name]
            collections = db.list_collection_names()
            
            client.close()
            self.add_result("MongoDB Connection", True, f"DB: {db_name}, Collections: {len(collections)}")
        except ImportError:
            self.add_result("MongoDB Connection", False, "pymongo not installed")
        except Exception as e:
            self.add_result("MongoDB Connection", False, str(e)[:60])
    
    def check_templates(self):
        templates_dir = Path(__file__).parent.parent / "templates"
        
        if not templates_dir.exists():
            self.add_result("Templates Directory", False, "Directory not found")
            return
        
        expected_agents = [
            "A1_ESTRATEGIA", "A2_PMO", "A3_FISCAL", "A4_LEGAL",
            "A5_FINANZAS", "A6_PROVEEDOR", "A7_DEFENSA", "KNOWLEDGE_BASE"
        ]
        
        missing_agents = []
        total_templates = 0
        
        for agent in expected_agents:
            agent_dir = templates_dir / agent
            if not agent_dir.exists():
                missing_agents.append(agent)
                continue
            
            docx_files = list(agent_dir.glob("*.docx"))
            manifest = agent_dir / "manifest.json"
            
            if not docx_files:
                missing_agents.append(f"{agent}(no .docx)")
            else:
                total_templates += len(docx_files)
        
        if missing_agents:
            self.add_result("Templates: Agent Folders", False, f"Missing: {', '.join(missing_agents)}")
        else:
            self.add_result("Templates: Agent Folders", True, f"{len(expected_agents)} agents found")
        
        if total_templates >= 42:
            self.add_result("Templates: DOCX Files", True, f"{total_templates} templates found")
        else:
            self.add_result("Templates: DOCX Files", False, f"Only {total_templates}/42 templates")
    
    def check_middleware(self):
        try:
            from middleware.tenant_context import TenantContextMiddleware, get_current_empresa_id
            self.add_result("Middleware: TenantContext", True, "Module imported successfully")
        except ImportError as e:
            self.add_result("Middleware: TenantContext", False, f"Import error: {str(e)[:40]}")
        
        try:
            from middleware.tenant_context import SKIP_TENANT_CHECK_PREFIXES
            if isinstance(SKIP_TENANT_CHECK_PREFIXES, (list, tuple, set)):
                self.add_result("Middleware: Skip Prefixes", True, f"{len(SKIP_TENANT_CHECK_PREFIXES)} public routes")
            else:
                self.add_result("Middleware: Skip Prefixes", False, "Invalid type")
        except ImportError:
            self.add_result("Middleware: Skip Prefixes", False, "Config not found")
    
    def check_project_routes(self):
        try:
            from routes.projects import router as projects_router
            
            empresa_filtered_methods = []
            for route in projects_router.routes:
                path = getattr(route, 'path', '')
                methods = getattr(route, 'methods', set())
                if path and methods:
                    empresa_filtered_methods.append(f"{list(methods)[0]} {path}")
            
            if empresa_filtered_methods:
                self.add_result("Routes: Projects API", True, f"{len(empresa_filtered_methods)} endpoints")
            else:
                self.add_result("Routes: Projects API", False, "No routes found")
        except Exception as e:
            self.add_result("Routes: Projects API", False, str(e)[:50])
        
        try:
            from services.durezza_database import DurezzaDatabaseService
            import inspect
            
            get_projects_sig = inspect.signature(DurezzaDatabaseService.get_projects)
            params = list(get_projects_sig.parameters.keys())
            
            if 'empresa_id' in params:
                self.add_result("Database: empresa_id Filter", True, "get_projects accepts empresa_id")
            else:
                self.add_result("Database: empresa_id Filter", False, "Missing empresa_id param")
        except Exception as e:
            self.add_result("Database: empresa_id Filter", False, str(e)[:50])
    
    def check_dashboard_routes(self):
        try:
            from routes.dashboard import router as dashboard_router
            
            route_count = len([r for r in dashboard_router.routes if hasattr(r, 'path')])
            self.add_result("Routes: Dashboard API", True, f"{route_count} endpoints")
        except Exception as e:
            self.add_result("Routes: Dashboard API", False, str(e)[:50])
    
    def print_report(self):
        print("\n" + "=" * 70)
        print("  VERIFICACIÓN DE PRODUCCIÓN - SATMA/Revisar.ia")
        print("=" * 70 + "\n")
        
        categories = {}
        for check, passed, detail in self.results:
            category = check.split(":")[0] if ":" in check else "General"
            if category not in categories:
                categories[category] = []
            categories[category].append((check, passed, detail))
        
        for category, checks in categories.items():
            print(f"  {category}")
            print("  " + "-" * 50)
            for check, passed, detail in checks:
                status = "✅" if passed else "❌"
                check_name = check.split(":", 1)[-1].strip() if ":" in check else check
                detail_str = f" - {detail}" if detail else ""
                print(f"    {status} {check_name}{detail_str}")
            print()
        
        print("=" * 70)
        passed_count = sum(1 for _, p, _ in self.results if p)
        total_count = len(self.results)
        
        if self.all_passed:
            print(f"  ✅ SISTEMA LISTO PARA PRODUCCIÓN ({passed_count}/{total_count} verificaciones)")
        else:
            failed_count = total_count - passed_count
            print(f"  ❌ SISTEMA NO LISTO - {failed_count} verificación(es) fallida(s)")
        print("=" * 70 + "\n")
    
    def run(self):
        print("\nEjecutando verificaciones de producción...\n")
        
        self.check_env_vars()
        self.check_postgresql()
        self.check_mongodb()
        self.check_templates()
        self.check_middleware()
        self.check_project_routes()
        self.check_dashboard_routes()
        
        self.print_report()
        
        return 0 if self.all_passed else 1


def main():
    verifier = ProductionVerifier()
    exit_code = verifier.run()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
