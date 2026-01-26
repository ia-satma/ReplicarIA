#!/usr/bin/env python3
"""
verify.py - Script de verificación integral del sistema REVISAR.IA

Ejecuta diagnósticos de:
- Base de datos PostgreSQL
- Frontend build
- Sistema de agentes
- Endpoints de API
- Knowledge Base
- Integración completa

Uso: cd backend && python scripts/verify.py
"""

import asyncio
import os
import sys
import json
from datetime import datetime
from typing import Dict, Any, List

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def print_status(success: bool, message: str):
    icon = f"{Colors.GREEN}✅{Colors.RESET}" if success else f"{Colors.RED}❌{Colors.RESET}"
    print(f"{icon} {message}")


def print_header(title: str):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*50}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}  {title}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*50}{Colors.RESET}\n")


async def check_database() -> Dict[str, Any]:
    """Verifica conexión y tablas de PostgreSQL"""
    result = {"success": False, "tables": 0, "details": {}}
    
    try:
        import asyncpg
        database_url = os.getenv("DATABASE_URL")
        
        if not database_url:
            result["error"] = "DATABASE_URL no configurado"
            return result
        
        conn = await asyncpg.connect(database_url)
        
        tables = await conn.fetch("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        
        result["tables"] = len(tables)
        result["table_names"] = [t["table_name"] for t in tables]
        
        critical_tables = ["projects", "deliberations", "empresas", "users"]
        missing = [t for t in critical_tables if t not in result["table_names"]]
        result["missing_critical"] = missing
        
        projects_count = await conn.fetchval("SELECT COUNT(*) FROM projects") or 0
        deliberations_count = await conn.fetchval("SELECT COUNT(*) FROM deliberations") or 0
        empresas_count = await conn.fetchval("SELECT COUNT(*) FROM empresas") or 0
        
        result["details"] = {
            "projects": projects_count,
            "deliberations": deliberations_count,
            "empresas": empresas_count
        }
        
        await conn.close()
        result["success"] = len(missing) == 0
        
    except Exception as e:
        result["error"] = str(e)
    
    return result


def check_frontend() -> Dict[str, Any]:
    """Verifica el build del frontend"""
    result = {"success": False, "files": {}}
    
    build_paths = [
        os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "build"),
        "/home/runner/workspace/frontend/build",
        "./frontend/build",
    ]
    
    build_path = None
    for p in build_paths:
        abs_path = os.path.abspath(p)
        if os.path.exists(os.path.join(abs_path, "index.html")):
            build_path = abs_path
            break
    
    if not build_path:
        result["error"] = "Frontend build no encontrado"
        return result
    
    result["build_path"] = build_path
    
    index_html = os.path.join(build_path, "index.html")
    static_js = os.path.join(build_path, "static", "js")
    static_css = os.path.join(build_path, "static", "css")
    
    result["files"]["index.html"] = os.path.exists(index_html)
    result["files"]["static/js"] = os.path.exists(static_js)
    result["files"]["static/css"] = os.path.exists(static_css)
    
    if os.path.exists(static_js):
        js_files = [f for f in os.listdir(static_js) if f.endswith('.js')]
        result["js_files"] = len(js_files)
    
    if os.path.exists(static_css):
        css_files = [f for f in os.listdir(static_css) if f.endswith('.css')]
        result["css_files"] = len(css_files)
    
    result["success"] = all(result["files"].values())
    return result


def check_agents() -> Dict[str, Any]:
    """Verifica el sistema de agentes"""
    result = {"success": False, "agents": [], "count": 0}
    
    try:
        from services.agent_prompts import OPTIMIZED_PROMPTS, list_available_agents
        
        agents = list_available_agents()
        result["agents"] = agents
        result["count"] = len(agents)
        
        expected_agents = [
            "A1_RECEPCION", "A2_ANALISIS", "A3_NORMATIVO", "A4_CONTABLE",
            "A5_OPERATIVO", "A6_FINANCIERO", "A7_LEGAL", "A8_REDTEAM",
            "A9_SINTESIS", "A10_ARCHIVO"
        ]
        
        missing = [a for a in expected_agents if a not in agents]
        result["missing"] = missing
        result["success"] = len(missing) == 0 and len(agents) >= 10
        
    except Exception as e:
        result["error"] = str(e)
    
    return result


async def check_api_endpoints() -> Dict[str, Any]:
    """Verifica endpoints de API críticos"""
    result = {"success": False, "endpoints": {}}
    
    try:
        import aiohttp
        
        base_url = "http://localhost:5000"
        
        endpoints = [
            ("/api/health", "GET"),
            ("/api/agents/stats", "GET"),
            ("/api/agents/available", "GET"),
        ]
        
        async with aiohttp.ClientSession() as session:
            for endpoint, method in endpoints:
                try:
                    url = f"{base_url}{endpoint}"
                    async with session.request(method, url, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                        result["endpoints"][endpoint] = {
                            "status": resp.status,
                            "ok": resp.status == 200
                        }
                except Exception as e:
                    result["endpoints"][endpoint] = {
                        "status": 0,
                        "ok": False,
                        "error": str(e)
                    }
        
        successful = sum(1 for e in result["endpoints"].values() if e.get("ok"))
        result["success"] = successful == len(endpoints)
        result["healthy_endpoints"] = successful
        result["total_endpoints"] = len(endpoints)
        
    except ImportError:
        result["error"] = "aiohttp no instalado - instalando..."
        result["note"] = "Ejecuta: pip install aiohttp"
    except Exception as e:
        result["error"] = str(e)
    
    return result


def check_environment() -> Dict[str, Any]:
    """Verifica variables de entorno críticas"""
    result = {"success": False, "variables": {}}
    
    required_vars = [
        "DATABASE_URL",
    ]
    
    optional_vars = [
        "ANTHROPIC_API_KEY",
        "OPENAI_API_KEY",
        "PCLOUD_USERNAME",
        "PCLOUD_PASSWORD",
    ]
    
    for var in required_vars:
        value = os.getenv(var)
        result["variables"][var] = {
            "set": value is not None and len(value) > 0,
            "required": True
        }
    
    for var in optional_vars:
        value = os.getenv(var)
        result["variables"][var] = {
            "set": value is not None and len(value) > 0,
            "required": False
        }
    
    required_set = all(
        result["variables"][v]["set"] 
        for v in required_vars
    )
    
    result["success"] = required_set
    return result


def calculate_implementation_score(results: Dict[str, Dict]) -> float:
    """Calcula el porcentaje de implementación"""
    weights = {
        "database": 25,
        "frontend": 20,
        "agents": 25,
        "api": 20,
        "environment": 10
    }
    
    total_weight = sum(weights.values())
    achieved = 0
    
    for key, weight in weights.items():
        if key in results and results[key].get("success"):
            achieved += weight
    
    return (achieved / total_weight) * 100


async def main():
    print_header("VERIFICACIÓN DEL SISTEMA REVISAR.IA")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Directorio: {os.getcwd()}")
    
    results = {}
    
    print_header("1. BASE DE DATOS")
    db_result = await check_database()
    results["database"] = db_result
    print_status(db_result["success"], f"PostgreSQL: {db_result.get('tables', 0)} tablas")
    if db_result.get("details"):
        for table, count in db_result["details"].items():
            print(f"   - {table}: {count} registros")
    if db_result.get("error"):
        print(f"   {Colors.RED}Error: {db_result['error']}{Colors.RESET}")
    
    print_header("2. FRONTEND BUILD")
    frontend_result = check_frontend()
    results["frontend"] = frontend_result
    print_status(frontend_result["success"], f"Build: {frontend_result.get('build_path', 'No encontrado')}")
    if frontend_result.get("js_files"):
        print(f"   - JS files: {frontend_result['js_files']}")
    if frontend_result.get("css_files"):
        print(f"   - CSS files: {frontend_result['css_files']}")
    
    print_header("3. SISTEMA DE AGENTES")
    agents_result = check_agents()
    results["agents"] = agents_result
    print_status(agents_result["success"], f"Agentes: {agents_result.get('count', 0)}/10 configurados")
    if agents_result.get("agents"):
        print(f"   Disponibles: {', '.join(agents_result['agents'][:5])}...")
    if agents_result.get("missing"):
        print(f"   {Colors.YELLOW}Faltantes: {agents_result['missing']}{Colors.RESET}")
    
    print_header("4. ENDPOINTS API")
    api_result = await check_api_endpoints()
    results["api"] = api_result
    healthy = api_result.get("healthy_endpoints", 0)
    total = api_result.get("total_endpoints", 0)
    print_status(api_result["success"], f"API: {healthy}/{total} endpoints funcionando")
    for endpoint, status in api_result.get("endpoints", {}).items():
        icon = "✓" if status.get("ok") else "✗"
        print(f"   {icon} {endpoint}: {status.get('status', 'error')}")
    
    print_header("5. VARIABLES DE ENTORNO")
    env_result = check_environment()
    results["environment"] = env_result
    set_vars = sum(1 for v in env_result["variables"].values() if v["set"])
    total_vars = len(env_result["variables"])
    print_status(env_result["success"], f"Variables: {set_vars}/{total_vars} configuradas")
    for var, status in env_result["variables"].items():
        icon = "✓" if status["set"] else ("✗" if status["required"] else "○")
        req = "(requerida)" if status["required"] else "(opcional)"
        print(f"   {icon} {var} {req}")
    
    print_header("RESUMEN")
    score = calculate_implementation_score(results)
    
    if score >= 90:
        color = Colors.GREEN
        status_text = "EXCELENTE"
    elif score >= 70:
        color = Colors.YELLOW
        status_text = "BUENO"
    elif score >= 50:
        color = Colors.YELLOW
        status_text = "PARCIAL"
    else:
        color = Colors.RED
        status_text = "INCOMPLETO"
    
    print(f"\n{Colors.BOLD}IMPLEMENTACIÓN: {color}{score:.0f}% - {status_text}{Colors.RESET}")
    
    checks_passed = sum(1 for r in results.values() if r.get("success"))
    print(f"Verificaciones pasadas: {checks_passed}/{len(results)}")
    
    output_file = "/tmp/verify_results.json"
    with open(output_file, "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "score": score,
            "results": results
        }, f, indent=2, default=str)
    
    print(f"\nResultados guardados en: {output_file}")
    
    return score >= 70


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
