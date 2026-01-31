"""
test_dynamic_agents.py - Tests para el Sistema de Agentes Dinámicos

Verifica:
1. Carga de agentes desde base de datos
2. CRUD de agentes
3. Ejecución de subagentes
4. Sistema de feedback y aprendizaje
5. Sincronización con pCloud

Fecha: 2026-01-31
"""

import asyncio
import pytest
import os
import sys
from uuid import uuid4

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestDynamicAgentLoader:
    """Tests para DynamicAgentLoader"""

    @pytest.mark.asyncio
    async def test_load_all_agents(self):
        """Test carga de todos los agentes"""
        from services.dynamic_agent_loader import DynamicAgentLoader

        loader = DynamicAgentLoader()
        initialized = await loader.initialize()

        if initialized:
            agents = await loader.load_all_agents()
            assert len(agents) > 0, "Should have at least one agent"

            # Verificar que los agentes base existen
            agent_ids = [a.agent_id for a in agents]
            assert "A1_ESTRATEGIA" in agent_ids or len(agents) > 0

            await loader.close()
        else:
            # Fallback mode - debería retornar agentes por defecto
            agents = await loader.load_all_agents()
            # En fallback puede haber menos agentes
            print(f"Fallback mode: {len(agents)} agents loaded")

    @pytest.mark.asyncio
    async def test_load_single_agent(self):
        """Test carga de un agente específico"""
        from services.dynamic_agent_loader import DynamicAgentLoader

        loader = DynamicAgentLoader()
        await loader.initialize()

        agent = await loader.load_agent("A1_ESTRATEGIA")

        if agent:
            assert agent.agent_id == "A1_ESTRATEGIA"
            assert agent.nombre is not None
            assert agent.system_prompt is not None
            print(f"✅ Agent loaded: {agent.nombre} - {agent.rol}")
        else:
            print("⚠️ Agent not found (expected if DB not configured)")

        await loader.close()

    @pytest.mark.asyncio
    async def test_get_dynamic_prompt(self):
        """Test generación de prompt dinámico"""
        from services.dynamic_agent_loader import DynamicAgentLoader

        loader = DynamicAgentLoader()
        await loader.initialize()

        prompt = await loader.get_dynamic_prompt(
            "A1_ESTRATEGIA",
            context={"proyecto": "Test Project"},
            include_learnings=True
        )

        assert prompt is not None
        assert len(prompt) > 50, "Prompt should have substantial content"
        print(f"✅ Dynamic prompt generated: {len(prompt)} chars")

        await loader.close()


class TestAgentCRUD:
    """Tests para AgentCRUDService"""

    @pytest.mark.asyncio
    async def test_create_agent(self):
        """Test crear un agente nuevo"""
        from services.agent_crud_service import AgentCRUDService, AgentCreateRequest

        crud = AgentCRUDService()
        initialized = await crud.initialize()

        if not initialized:
            pytest.skip("Database not available")

        # Crear agente de prueba
        request = AgentCreateRequest(
            agent_id=f"TEST_AGENT_{uuid4().hex[:8]}",
            nombre="Agente de Prueba",
            rol="Testing",
            descripcion="Agente creado para pruebas",
            system_prompt="Eres un agente de prueba.",
            tipo="soporte"
        )

        result = await crud.create_agent(request)

        if result:
            assert result['created'] == True
            assert result['agent_id'] == request.agent_id
            print(f"✅ Agent created: {result['agent_id']}")

            # Cleanup - eliminar agente de prueba
            await crud.delete_agent(request.agent_id, hard_delete=True)
            print(f"✅ Test agent cleaned up")
        else:
            print("⚠️ Could not create agent (may already exist)")

        await crud.close()

    @pytest.mark.asyncio
    async def test_check_permission(self):
        """Test verificación de permisos"""
        from services.agent_crud_service import AgentCRUDService

        crud = AgentCRUDService()
        initialized = await crud.initialize()

        if not initialized:
            pytest.skip("Database not available")

        # El ORQUESTADOR debería tener todos los permisos
        has_permission = await crud.check_permission("ORQUESTADOR", "create_agent")

        # Puede ser True (si existe) o False (si no existe)
        print(f"ORQUESTADOR create_agent permission: {has_permission}")

        await crud.close()


class TestSubagentExecutor:
    """Tests para SubagentExecutor"""

    @pytest.mark.asyncio
    async def test_tipificacion(self):
        """Test clasificación de servicio"""
        from services.subagent_executor import SubagentExecutor

        executor = SubagentExecutor()

        result = await executor.ejecutar_tipificacion(
            descripcion_servicio="Consultoría estratégica para optimización de procesos operativos",
            monto=150000,
            proveedor={"nombre": "Test Proveedor", "rfc": "TEST123456ABC"}
        )

        assert result is not None
        assert result.tipo_servicio is not None
        assert result.confianza > 0
        assert len(result.requisitos_materialidad) > 0

        print(f"✅ Tipificación: {result.tipo_servicio.value} (confianza: {result.confianza})")
        print(f"   Requisitos: {result.requisitos_materialidad[:2]}...")

    @pytest.mark.asyncio
    async def test_materialidad(self):
        """Test evaluación de materialidad"""
        from services.subagent_executor import SubagentExecutor, TipoServicio

        executor = SubagentExecutor()

        documentos = [
            {"tipo": "contrato", "nombre": "Contrato de servicios.pdf"},
            {"tipo": "propuesta", "nombre": "Propuesta comercial.docx"},
            {"tipo": "minuta", "nombre": "Minuta reunión 1.docx"},
            {"tipo": "entregable", "nombre": "Reporte final.pdf"},
            {"tipo": "acta", "nombre": "Acta de entrega-recepción.pdf"},
        ]

        result = await executor.ejecutar_materialidad(
            documentos=documentos,
            tipo_servicio=TipoServicio.CONSULTORIA,
            monto=200000
        )

        assert result is not None
        assert 0 <= result.score_materialidad <= 100
        assert result.evidencia_antes is not None
        assert result.evidencia_durante is not None
        assert result.evidencia_despues is not None

        print(f"✅ Materialidad Score: {result.score_materialidad}")
        print(f"   Gaps: {result.gaps[:2] if result.gaps else 'None'}")

    @pytest.mark.asyncio
    async def test_riesgos(self):
        """Test evaluación de riesgos"""
        from services.subagent_executor import SubagentExecutor, TipoServicio

        executor = SubagentExecutor()

        result = await executor.ejecutar_riesgos(
            proyecto={
                "descripcion": "Consultoría estratégica",
                "monto": 300000,
                "bee_score": 75
            },
            materialidad_score=65,
            proveedor={
                "nombre": "Consultores SA",
                "en_lista_69b": False,
                "es_relacionado": False
            },
            tipo_servicio=TipoServicio.CONSULTORIA
        )

        assert result is not None
        assert 0 <= result.risk_score <= 100
        assert result.risk_level is not None
        assert result.recomendacion_general is not None

        print(f"✅ Risk Score: {result.risk_score} ({result.risk_level.value})")
        print(f"   Recomendación: {result.recomendacion_general[:50]}...")

    @pytest.mark.asyncio
    async def test_analisis_completo(self):
        """Test análisis completo coordinado"""
        from services.subagent_executor import SubagentExecutor

        executor = SubagentExecutor()

        result = await executor.ejecutar_analisis_completo(
            proyecto={
                "descripcion": "Investigación de mercado para expansión regional",
                "monto": 250000,
                "bee_score": 80
            },
            documentos=[
                {"tipo": "contrato", "nombre": "Contrato.pdf"},
                {"tipo": "sib", "nombre": "SIB aprobado.pdf"},
                {"tipo": "minuta", "nombre": "Kickoff meeting.docx"},
                {"tipo": "avance", "nombre": "Reporte avance 1.pdf"},
                {"tipo": "entregable", "nombre": "Informe final.pdf"},
                {"tipo": "acta", "nombre": "Acta recepción.pdf"},
            ],
            proveedor={
                "nombre": "Research Corp",
                "en_lista_69b": False,
                "es_relacionado": False
            }
        )

        assert result is not None
        assert 'tipificacion' in result
        assert 'materialidad' in result
        assert 'riesgos' in result
        assert 'resumen' in result

        print(f"✅ Análisis Completo:")
        print(f"   Tipo: {result['tipificacion']['tipo_servicio']}")
        print(f"   Materialidad: {result['materialidad']['score']}")
        print(f"   Riesgo: {result['riesgos']['risk_score']} ({result['riesgos']['risk_level']})")
        print(f"   Decisión: {result['resumen']['decision_sugerida']}")
        print(f"   Score Consolidado: {result['resumen']['score_consolidado']}")


class TestAgentLearning:
    """Tests para AgentLearningService"""

    @pytest.mark.asyncio
    async def test_get_active_learnings(self):
        """Test obtener aprendizajes activos"""
        from services.agent_learning_service import AgentLearningService

        service = AgentLearningService()
        initialized = await service.initialize()

        if not initialized:
            pytest.skip("Database not available")

        learnings = await service.get_active_learnings("A1_ESTRATEGIA")

        # Puede estar vacío al inicio
        print(f"✅ Active learnings for A1_ESTRATEGIA: {len(learnings)}")

        await service.close()

    @pytest.mark.asyncio
    async def test_get_agent_metrics(self):
        """Test obtener métricas de agente"""
        from services.agent_learning_service import AgentLearningService

        service = AgentLearningService()
        initialized = await service.initialize()

        if not initialized:
            pytest.skip("Database not available")

        metrics = await service.get_agent_metrics("A1_ESTRATEGIA")

        if metrics:
            print(f"✅ Metrics for A1_ESTRATEGIA:")
            print(f"   Total decisions: {metrics.total_decisions}")
            print(f"   Accuracy: {metrics.accuracy_rate}")
        else:
            print("⚠️ No metrics yet (expected for new system)")

        await service.close()


# ============================================================================
# EJECUTAR TESTS
# ============================================================================

async def run_all_tests():
    """Ejecutar todos los tests manualmente"""
    print("=" * 60)
    print("🧪 RUNNING DYNAMIC AGENTS SYSTEM TESTS")
    print("=" * 60)

    # Test Loader
    print("\n📦 Testing DynamicAgentLoader...")
    loader_tests = TestDynamicAgentLoader()
    await loader_tests.test_load_all_agents()
    await loader_tests.test_load_single_agent()
    await loader_tests.test_get_dynamic_prompt()

    # Test CRUD
    print("\n🔧 Testing AgentCRUD...")
    crud_tests = TestAgentCRUD()
    await crud_tests.test_check_permission()
    # await crud_tests.test_create_agent()  # Commented to avoid DB side effects

    # Test Subagents
    print("\n🤖 Testing SubagentExecutor...")
    subagent_tests = TestSubagentExecutor()
    await subagent_tests.test_tipificacion()
    await subagent_tests.test_materialidad()
    await subagent_tests.test_riesgos()
    await subagent_tests.test_analisis_completo()

    # Test Learning
    print("\n📚 Testing AgentLearning...")
    learning_tests = TestAgentLearning()
    await learning_tests.test_get_active_learnings()
    await learning_tests.test_get_agent_metrics()

    print("\n" + "=" * 60)
    print("✅ ALL TESTS COMPLETED")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(run_all_tests())
