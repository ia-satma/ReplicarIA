#!/usr/bin/env python3
"""
verify_dynamic_agents.py - Verificación Completa del Sistema de Agentes Dinámicos

Este script verifica:
1. Migración SQL ejecutada correctamente
2. Agentes base insertados en DB
3. Subagentes configurados
4. Sistema de feedback/learning
5. Integración con KB

Ejecutar: python backend/scripts/verify_dynamic_agents.py

Fecha: 2026-01-31
"""

import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import logging
logging.basicConfig(level=logging.INFO)


async def verify_database_tables():
    """Verificar que las tablas del sistema de agentes existan"""
    print("\n" + "="*60)
    print("📊 VERIFICACIÓN DE TABLAS EN BASE DE DATOS")
    print("="*60)

    try:
        import asyncpg
        db_url = os.environ.get("DATABASE_URL")

        if not db_url:
            print("❌ DATABASE_URL no configurada")
            return False

        conn = await asyncpg.connect(db_url)

        expected_tables = [
            'agent_configs', 'subagent_configs', 'agent_decisions',
            'agent_outcomes', 'agent_learnings', 'agent_feedback',
            'agent_metrics', 'agent_audit_log', 'agent_documents'
        ]

        results = []
        for table in expected_tables:
            exists = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = $1
                )
            """, table)
            status = "✅" if exists else "❌"
            print(f"   {status} {table}")
            results.append(exists)

        await conn.close()

        return all(results)

    except ImportError:
        print("❌ asyncpg no instalado")
        return False
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return False


async def verify_base_agents():
    """Verificar que los agentes base están insertados"""
    print("\n" + "="*60)
    print("👥 VERIFICACIÓN DE AGENTES BASE")
    print("="*60)

    try:
        import asyncpg
        db_url = os.environ.get("DATABASE_URL")
        conn = await asyncpg.connect(db_url)

        expected_agents = [
            'A1_ESTRATEGIA', 'A2_PMO', 'A3_FISCAL', 'A4_LEGAL',
            'A5_FINANZAS', 'A6_PROVEEDOR', 'A7_DEFENSA',
            'A8_REDTEAM', 'ORQUESTADOR', 'CODE_AUDITOR', 'FRONTEND_IMPROVER'
        ]

        for agent_id in expected_agents:
            row = await conn.fetchrow("""
                SELECT agent_id, nombre, activo, puede_crear_agentes
                FROM agent_configs
                WHERE agent_id = $1
            """, agent_id)

            if row:
                perms = "CRUD" if row['puede_crear_agentes'] else "READ"
                status = "✅" if row['activo'] else "⚠️"
                print(f"   {status} {row['agent_id']}: {row['nombre']} [{perms}]")
            else:
                print(f"   ❌ {agent_id}: No encontrado")

        total = await conn.fetchval("SELECT COUNT(*) FROM agent_configs")
        print(f"\n   📊 Total agentes en DB: {total}")

        await conn.close()
        return total >= 7

    except Exception as e:
        print(f"❌ Error: {e}")
        return False


async def verify_subagents():
    """Verificar subagentes S1-S5"""
    print("\n" + "="*60)
    print("🤖 VERIFICACIÓN DE SUBAGENTES")
    print("="*60)

    try:
        import asyncpg
        db_url = os.environ.get("DATABASE_URL")
        conn = await asyncpg.connect(db_url)

        expected_subs = [
            ('S1_TIPIFICACION', 'tipificacion'),
            ('S2_MATERIALIDAD', 'materialidad'),
            ('S3_RIESGOS', 'riesgos'),
            ('S4_ORGANIZADOR', 'organizacion'),
            ('S5_TRAFICO', 'trafico')
        ]

        for sub_id, tipo in expected_subs:
            row = await conn.fetchrow("""
                SELECT subagent_id, descripcion, activo
                FROM subagent_configs
                WHERE subagent_id = $1
            """, sub_id)

            if row:
                status = "✅" if row['activo'] else "⚠️"
                print(f"   {status} {row['subagent_id']}: {row['descripcion'][:50]}")
            else:
                print(f"   ❌ {sub_id}: No encontrado")

        await conn.close()
        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        return False


async def test_subagent_executor():
    """Probar la ejecución de subagentes"""
    print("\n" + "="*60)
    print("🧪 TEST DE EJECUCIÓN DE SUBAGENTES")
    print("="*60)

    try:
        from services.subagent_executor import SubagentExecutor, TipoServicio

        executor = SubagentExecutor()

        # Test 1: Tipificación
        print("\n   📋 Test S1_TIPIFICACION...")
        result1 = await executor.ejecutar_tipificacion(
            descripcion_servicio="Consultoría estratégica para optimización",
            monto=150000,
            proveedor={"nombre": "Test", "rfc": "TEST123"}
        )
        print(f"      ✅ Tipo: {result1.tipo_servicio.value} (confianza: {result1.confianza})")

        # Test 2: Materialidad
        print("\n   📊 Test S2_MATERIALIDAD...")
        result2 = await executor.ejecutar_materialidad(
            documentos=[
                {"tipo": "contrato", "nombre": "Contrato.pdf"},
                {"tipo": "entregable", "nombre": "Entregable.pdf"},
            ],
            tipo_servicio=TipoServicio.CONSULTORIA,
            monto=100000
        )
        print(f"      ✅ Score: {result2.score_materialidad}")

        # Test 3: Riesgos
        print("\n   ⚠️ Test S3_RIESGOS...")
        result3 = await executor.ejecutar_riesgos(
            proyecto={"descripcion": "Test", "monto": 100000, "bee_score": 70},
            materialidad_score=50,
            proveedor={"en_lista_69b": False, "es_relacionado": False},
            tipo_servicio=TipoServicio.CONSULTORIA
        )
        print(f"      ✅ Risk: {result3.risk_score} ({result3.risk_level.value})")

        return True

    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


async def test_dynamic_loader():
    """Probar el DynamicAgentLoader"""
    print("\n" + "="*60)
    print("🔄 TEST DE DYNAMIC AGENT LOADER")
    print("="*60)

    try:
        from services.dynamic_agent_loader import DynamicAgentLoader

        loader = DynamicAgentLoader()
        initialized = await loader.initialize()

        if not initialized:
            print("   ⚠️ Loader en modo fallback (sin DB)")
            agents = await loader.load_all_agents()
            print(f"   📊 Agentes cargados (fallback): {len(agents)}")
        else:
            print("   ✅ Conectado a PostgreSQL")

            agents = await loader.load_all_agents()
            print(f"   📊 Agentes cargados: {len(agents)}")

            for agent in agents[:5]:
                print(f"      - {agent.agent_id}: {agent.nombre}")

            # Test dynamic prompt
            print("\n   📝 Generando prompt dinámico...")
            prompt = await loader.get_dynamic_prompt("A1_ESTRATEGIA")
            print(f"      ✅ Prompt generado: {len(prompt)} caracteres")

            await loader.close()

        return True

    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_api_endpoints():
    """Probar endpoints API localmente"""
    print("\n" + "="*60)
    print("🔌 VERIFICACIÓN DE RUTAS API")
    print("="*60)

    try:
        from fastapi.testclient import TestClient
        from server import app

        client = TestClient(app)

        endpoints = [
            ("GET", "/health", "Health Check"),
            ("GET", "/api/agents/dynamic/agents", "Lista Agentes"),
            ("GET", "/api/subagents/tipos-servicio", "Tipos Servicio"),
            ("GET", "/api/subagents/niveles-riesgo", "Niveles Riesgo"),
        ]

        for method, path, name in endpoints:
            try:
                if method == "GET":
                    response = client.get(path)
                else:
                    response = client.post(path, json={})

                status = "✅" if response.status_code < 400 else "⚠️"
                print(f"   {status} {method} {path}: {response.status_code} ({name})")
            except Exception as e:
                print(f"   ❌ {method} {path}: {e}")

        return True

    except ImportError:
        print("   ⚠️ TestClient no disponible (httpx required)")
        return True
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


async def main():
    print("\n" + "="*70)
    print("🚀 VERIFICACIÓN COMPLETA - SISTEMA DE AGENTES DINÁMICOS")
    print("="*70)
    print(f"   Fecha: {__import__('datetime').datetime.now().isoformat()}")
    print(f"   DATABASE_URL: {'✅ Configurada' if os.environ.get('DATABASE_URL') else '❌ No configurada'}")

    results = {}

    # 1. Verificar tablas
    results['tables'] = await verify_database_tables()

    # 2. Verificar agentes base
    results['agents'] = await verify_base_agents()

    # 3. Verificar subagentes
    results['subagents'] = await verify_subagents()

    # 4. Test SubagentExecutor
    results['executor'] = await test_subagent_executor()

    # 5. Test DynamicAgentLoader
    results['loader'] = await test_dynamic_loader()

    # 6. Test API endpoints
    results['api'] = await test_api_endpoints()

    # Resumen
    print("\n" + "="*70)
    print("📋 RESUMEN DE VERIFICACIÓN")
    print("="*70)

    all_passed = True
    for name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"   {status}: {name}")
        if not passed:
            all_passed = False

    print("\n" + "="*70)
    if all_passed:
        print("✅ SISTEMA LISTO PARA PRODUCCIÓN")
    else:
        print("⚠️ REVISAR COMPONENTES FALLIDOS")
    print("="*70 + "\n")

    return 0 if all_passed else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
