"""
Tests para arquitectura multi-tenant de Revisar.ia.
"""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from models.empresa import (
    Empresa, EmpresaCreate, EmpresaUpdate,
    PilarEstrategico, OKR, ConfiguracionTipologia,
    IndustriaEnum
)
from services.empresa_service import empresa_service, TIPOLOGIAS_BASE
from repositories.empresa_repository import EmpresaRepository


class TestEmpresaModel:
    def test_empresa_create_model(self):
        data = EmpresaCreate(
            nombre_comercial="Test Corp",
            razon_social="Test Corporation S.A. de C.V.",
            rfc="TCO123456ABC",
            industria=IndustriaEnum.TECNOLOGIA
        )
        assert data.nombre_comercial == "Test Corp"
        assert data.rfc == "TCO123456ABC"
        assert data.industria == IndustriaEnum.TECNOLOGIA
    
    def test_empresa_full_model(self):
        empresa = Empresa(
            nombre_comercial="Full Corp",
            razon_social="Full Corporation S.A. de C.V.",
            rfc="FCO987654XYZ",
            industria=IndustriaEnum.CONSTRUCCION,
            vision="Ser líderes en construcción sustentable",
            mision="Construir con calidad y responsabilidad"
        )
        assert empresa.id is not None
        assert empresa.nombre_comercial == "Full Corp"
        assert empresa.vision == "Ser líderes en construcción sustentable"
        assert empresa.activa == True
        assert empresa.plan == "basico"
    
    def test_pilar_estrategico(self):
        pilar = PilarEstrategico(
            nombre="Innovación",
            descripcion="Impulsar la innovación en todos los procesos",
            peso=0.25
        )
        assert pilar.nombre == "Innovación"
        assert pilar.peso == 0.25
    
    def test_okr_model(self):
        okr = OKR(
            objetivo="Aumentar ingresos en 20%",
            key_results=["Cerrar 10 nuevos clientes", "Aumentar ticket promedio 15%"],
            periodo="2026-Q1",
            responsable="Director Comercial"
        )
        assert okr.objetivo == "Aumentar ingresos en 20%"
        assert len(okr.key_results) == 2
    
    def test_configuracion_tipologia(self):
        config = ConfiguracionTipologia(
            codigo="CONSULTORIA_MACRO_ESTRATEGIA",
            nombre="Consultoría Estratégica",
            descripcion="Servicios de consultoría",
            habilitada=True,
            checklist_documentos=["SOW", "Informe Final"]
        )
        assert config.codigo == "CONSULTORIA_MACRO_ESTRATEGIA"
        assert config.habilitada == True
        assert len(config.checklist_documentos) == 2


class TestTipologiasBase:
    def test_tipologias_base_count(self):
        assert len(TIPOLOGIAS_BASE) == 8
    
    def test_tipologias_have_required_fields(self):
        for tip in TIPOLOGIAS_BASE:
            assert "codigo" in tip
            assert "nombre" in tip
            assert "descripcion" in tip
            assert "checklist_documentos" in tip
            assert len(tip["checklist_documentos"]) > 0
    
    def test_tipologias_codigos_unicos(self):
        codigos = [t["codigo"] for t in TIPOLOGIAS_BASE]
        assert len(codigos) == len(set(codigos))
    
    def test_tipologia_consultoria_existe(self):
        codigos = [t["codigo"] for t in TIPOLOGIAS_BASE]
        assert "CONSULTORIA_MACRO_ESTRATEGIA" in codigos
    
    def test_tipologia_intragrupo_existe(self):
        codigos = [t["codigo"] for t in TIPOLOGIAS_BASE]
        assert "INTRAGRUPO_MANAGEMENT_FEE" in codigos


class TestEmpresaRepository:
    @pytest.fixture
    def repo(self):
        repo = EmpresaRepository()
        repo.demo_mode = True
        repo._demo_empresas = []
        return repo
    
    @pytest.mark.asyncio
    async def test_create_empresa(self, repo):
        empresa = Empresa(
            nombre_comercial="Repo Test",
            razon_social="Repo Test S.A.",
            rfc="RTE123456ABC",
            industria=IndustriaEnum.SERVICIOS_PROFESIONALES
        )
        created = await repo.create(empresa)
        assert created.nombre_comercial == "Repo Test"
        assert len(repo._demo_empresas) == 1
    
    @pytest.mark.asyncio
    async def test_get_by_id(self, repo):
        empresa = Empresa(
            nombre_comercial="Find Test",
            razon_social="Find Test S.A.",
            rfc="FTE123456ABC",
            industria=IndustriaEnum.COMERCIO
        )
        await repo.create(empresa)
        
        found = await repo.get_by_id(empresa.id)
        assert found is not None
        assert found.nombre_comercial == "Find Test"
    
    @pytest.mark.asyncio
    async def test_get_by_rfc(self, repo):
        empresa = Empresa(
            nombre_comercial="RFC Test",
            razon_social="RFC Test S.A.",
            rfc="RFC123456XYZ",
            industria=IndustriaEnum.MANUFACTURA
        )
        await repo.create(empresa)
        
        found = await repo.get_by_rfc("RFC123456XYZ")
        assert found is not None
        assert found.nombre_comercial == "RFC Test"
    
    @pytest.mark.asyncio
    async def test_update_empresa(self, repo):
        empresa = Empresa(
            nombre_comercial="Update Test",
            razon_social="Update Test S.A.",
            rfc="UPD123456ABC",
            industria=IndustriaEnum.SALUD
        )
        await repo.create(empresa)
        
        updated = await repo.update(empresa.id, {"vision": "Nueva visión"})
        assert updated is not None
        assert updated.vision == "Nueva visión"
    
    @pytest.mark.asyncio
    async def test_soft_delete(self, repo):
        empresa = Empresa(
            nombre_comercial="Delete Test",
            razon_social="Delete Test S.A.",
            rfc="DEL123456ABC",
            industria=IndustriaEnum.EDUCACION
        )
        await repo.create(empresa)
        
        deleted = await repo.soft_delete(empresa.id)
        assert deleted is not None
        assert deleted.activa == False


class TestEmpresaService:
    @pytest.fixture
    def clean_service(self):
        empresa_service.repository.demo_mode = True
        empresa_service.repository._demo_empresas = []
        return empresa_service
    
    @pytest.mark.asyncio
    async def test_crear_empresa(self, clean_service):
        data = EmpresaCreate(
            nombre_comercial="Service Test",
            razon_social="Service Test S.A. de C.V.",
            rfc="STE123456ABC",
            industria=IndustriaEnum.TECNOLOGIA
        )
        empresa = await clean_service.crear_empresa(data)
        
        assert empresa.nombre_comercial == "Service Test"
        assert len(empresa.tipologias_configuradas) == 8
    
    @pytest.mark.asyncio
    async def test_crear_empresa_duplicado(self, clean_service):
        data = EmpresaCreate(
            nombre_comercial="Duplicate Test",
            razon_social="Duplicate Test S.A.",
            rfc="DUP123456ABC",
            industria=IndustriaEnum.COMERCIO
        )
        await clean_service.crear_empresa(data)
        
        with pytest.raises(ValueError, match="Ya existe una empresa"):
            await clean_service.crear_empresa(data)
    
    @pytest.mark.asyncio
    async def test_get_tipologias_con_estado(self, clean_service):
        data = EmpresaCreate(
            nombre_comercial="Tipologias Test",
            razon_social="Tipologias Test S.A.",
            rfc="TIP123456ABC",
            industria=IndustriaEnum.CONSTRUCCION
        )
        empresa = await clean_service.crear_empresa(data)
        
        tipologias = await clean_service.get_tipologias_con_estado(empresa.id)
        
        assert len(tipologias) == 8
        for tip in tipologias:
            assert tip["disponible"] == True
            assert "checklist_documentos" in tip
    
    @pytest.mark.asyncio
    async def test_actualizar_vision_mision(self, clean_service):
        data = EmpresaCreate(
            nombre_comercial="Vision Test",
            razon_social="Vision Test S.A.",
            rfc="VIS123456ABC",
            industria=IndustriaEnum.INMOBILIARIO
        )
        empresa = await clean_service.crear_empresa(data)
        
        updated = await clean_service.actualizar_vision_mision(
            empresa.id,
            vision="Nuestra visión",
            mision="Nuestra misión"
        )
        
        assert updated.vision == "Nuestra visión"
        assert updated.mision == "Nuestra misión"
    
    @pytest.mark.asyncio
    async def test_actualizar_pilares(self, clean_service):
        data = EmpresaCreate(
            nombre_comercial="Pilares Test",
            razon_social="Pilares Test S.A.",
            rfc="PIL123456ABC",
            industria=IndustriaEnum.SERVICIOS_PROFESIONALES
        )
        empresa = await clean_service.crear_empresa(data)
        
        pilares = [
            PilarEstrategico(nombre="Innovación", descripcion="Innovar siempre", peso=0.4),
            PilarEstrategico(nombre="Calidad", descripcion="Calidad total", peso=0.3),
            PilarEstrategico(nombre="Sostenibilidad", descripcion="Ser sostenibles", peso=0.3)
        ]
        
        updated = await clean_service.actualizar_pilares(empresa.id, pilares)
        
        assert len(updated.pilares_estrategicos) == 3
    
    @pytest.mark.asyncio
    async def test_actualizar_pilares_peso_invalido(self, clean_service):
        data = EmpresaCreate(
            nombre_comercial="Peso Test",
            razon_social="Peso Test S.A.",
            rfc="PES123456ABC",
            industria=IndustriaEnum.HOTELERIA_RESTAURANTES
        )
        empresa = await clean_service.crear_empresa(data)
        
        pilares = [
            PilarEstrategico(nombre="Pilar 1", descripcion="Desc 1", peso=0.5),
            PilarEstrategico(nombre="Pilar 2", descripcion="Desc 2", peso=0.3)
        ]
        
        with pytest.raises(ValueError, match="suma de pesos"):
            await clean_service.actualizar_pilares(empresa.id, pilares)
    
    @pytest.mark.asyncio
    async def test_actualizar_okrs(self, clean_service):
        data = EmpresaCreate(
            nombre_comercial="OKR Test",
            razon_social="OKR Test S.A.",
            rfc="OKR123456ABC",
            industria=IndustriaEnum.TRANSPORTE_LOGISTICA
        )
        empresa = await clean_service.crear_empresa(data)
        
        okrs = [
            OKR(
                objetivo="Crecer 25%",
                key_results=["Abrir 5 rutas nuevas", "Reducir costos 10%"],
                periodo="2026-Q1"
            )
        ]
        
        updated = await clean_service.actualizar_okrs(empresa.id, okrs)
        
        assert len(updated.okrs) == 1
        assert updated.okrs[0].objetivo == "Crecer 25%"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
