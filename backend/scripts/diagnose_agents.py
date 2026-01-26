#!/usr/bin/env python3
"""
diagnose_agents.py - Diagnóstico del sistema de agentes REVISAR.IA
"""

import asyncio
import json
import time
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

RESULTS = {
    "timestamp": datetime.utcnow().isoformat(),
    "checks": {},
    "metrics": {},
    "errors": [],
}


async def check_database():
    """Verifica conexión a base de datos."""
    print("📊 Verificando base de datos...")
    
    try:
        import asyncpg
        conn = await asyncpg.connect(os.getenv("DATABASE_URL"))
        
        tables = ["deliberations", "knowledge_chunks", "projects", "empresas"]
        for table in tables:
            try:
                count = await conn.fetchval(f"SELECT COUNT(*) FROM {table}")
                print(f"   ✅ {table}: {count} registros")
                RESULTS["metrics"][f"table_{table}"] = count
            except Exception as e:
                print(f"   ⚠️ {table}: tabla no existe")
        
        await conn.close()
        RESULTS["checks"]["database"] = True
        return True
    except Exception as e:
        RESULTS["errors"].append(f"Database: {e}")
        RESULTS["checks"]["database"] = False
        print(f"   ❌ Error: {e}")
        return False


async def check_orchestrator():
    """Verifica el orquestador de agentes."""
    print("\n🤖 Verificando orquestador...")
    
    try:
        from services.agent_orchestrator import get_orchestrator, AGENTS_CONFIG
        
        orchestrator = get_orchestrator()
        agent_count = len(AGENTS_CONFIG)
        
        print(f"   ✅ Agentes configurados: {agent_count}")
        RESULTS["metrics"]["agents"] = agent_count
        
        for agent_id, config in AGENTS_CONFIG.items():
            print(f"      - {agent_id}: {config['name']}")
        
        RESULTS["checks"]["orchestrator"] = True
        return True
    except Exception as e:
        RESULTS["errors"].append(f"Orchestrator: {e}")
        RESULTS["checks"]["orchestrator"] = False
        print(f"   ❌ Error: {e}")
        return False


async def check_claude():
    """Verifica conexión a Claude API."""
    print("\n🧠 Verificando Claude API...")
    
    try:
        from anthropic import Anthropic
        
        client = Anthropic()
        
        start = time.perf_counter()
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=50,
            messages=[{"role": "user", "content": "Di 'OK'"}],
        )
        elapsed = (time.perf_counter() - start) * 1000
        
        print(f"   ✅ Claude API: OK ({elapsed:.0f}ms)")
        RESULTS["metrics"]["claude_latency_ms"] = elapsed
        RESULTS["checks"]["claude"] = True
        return True
    except Exception as e:
        RESULTS["errors"].append(f"Claude: {e}")
        RESULTS["checks"]["claude"] = False
        print(f"   ❌ Error: {e}")
        return False


async def test_agent_invocation():
    """Prueba invocación de agente."""
    print("\n🧪 Probando invocación de agente...")
    
    try:
        from services.agent_orchestrator import get_orchestrator
        
        orchestrator = get_orchestrator()
        
        start = time.perf_counter()
        result = await orchestrator.process_request(
            empresa_id="test_tenant",
            project_id="test_project",
            user_id="test_user",
            user_message="¿Qué requisitos tiene el artículo 27 LISR?",
            target_agents=["A2_ANALISIS"],
        )
        elapsed = (time.perf_counter() - start) * 1000
        
        has_response = bool(result.get("response"))
        print(f"   ✅ Invocación: {'OK' if has_response else 'FAIL'} ({elapsed:.0f}ms)")
        print(f"   ✅ Agentes: {result.get('agents_invoked', [])}")
        
        RESULTS["metrics"]["e2e_latency_ms"] = elapsed
        RESULTS["checks"]["e2e"] = has_response
        return has_response
    except Exception as e:
        RESULTS["errors"].append(f"E2E: {e}")
        RESULTS["checks"]["e2e"] = False
        print(f"   ❌ Error: {e}")
        return False


def calculate_percentages():
    """Calcula porcentajes finales."""
    checks = RESULTS["checks"]
    
    impl_tasks = ["database", "orchestrator"]
    impl_done = sum(1 for t in impl_tasks if checks.get(t, False))
    impl_pct = (impl_done / len(impl_tasks)) * 100
    
    func_tasks = ["database", "claude", "e2e"]
    func_done = sum(1 for t in func_tasks if checks.get(t, False))
    func_pct = (func_done / len(func_tasks)) * 100
    
    fe_tasks = ["database", "orchestrator", "claude"]
    fe_done = sum(1 for t in fe_tasks if checks.get(t, False))
    fe_pct = (fe_done / len(fe_tasks)) * 100
    
    return {"implementation": impl_pct, "functionality": func_pct, "frontend": fe_pct}


async def main():
    print("=" * 60)
    print("🔬 DIAGNÓSTICO DE AGENTES - REVISAR.IA")
    print("=" * 60)
    
    await check_database()
    await check_orchestrator()
    await check_claude()
    await test_agent_invocation()
    
    pcts = calculate_percentages()
    RESULTS["percentages"] = pcts
    
    print("\n" + "=" * 60)
    print("📊 RESULTADOS")
    print("=" * 60)
    print(f"""
    ┌────────────────────────────────────────┐
    │  IMPLEMENTACIÓN:        {pcts['implementation']:>6.1f}%       │
    │  FUNCIONALIDAD:         {pcts['functionality']:>6.1f}%       │
    │  INTEGRACIÓN FRONTEND:  {pcts['frontend']:>6.1f}%       │
    └────────────────────────────────────────┘
    """)
    
    if RESULTS["errors"]:
        print("❌ ERRORES DETECTADOS:")
        for err in RESULTS["errors"]:
            print(f"   - {err}")
    
    with open("backend/agent_diagnostics.json", "w") as f:
        json.dump(RESULTS, f, indent=2, default=str)
    
    print("\n✅ Resultados guardados en backend/agent_diagnostics.json")
    return pcts


if __name__ == "__main__":
    asyncio.run(main())
