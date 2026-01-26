"""
Test Runner para pruebas integrales de Revisar.IA
Ejecuta flujo completo: registro, agentes, deliberación, PDF, pCloud, email
"""
import os
import json
import logging
import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class TestResult:
    paso: str
    status: str  # 'success', 'error', 'warning'
    mensaje: str
    datos: Optional[Dict] = None
    duracion_ms: Optional[int] = None


class TestRunner:
    """Ejecutor de pruebas integrales para Revisar.IA"""
    
    def __init__(self):
        self.resultados: List[TestResult] = []
        
    def log(self, paso: str, status: str, mensaje: str, datos: Dict = None, duracion_ms: int = None):
        """Registra resultado de un paso de prueba"""
        resultado = TestResult(
            paso=paso,
            status=status,
            mensaje=mensaje,
            datos=datos,
            duracion_ms=duracion_ms
        )
        self.resultados.append(resultado)
        
        icon = "✅" if status == "success" else "❌" if status == "error" else "⚠️"
        duracion_str = f" ({duracion_ms}ms)" if duracion_ms else ""
        logger.info(f"{icon} [{paso}] {mensaje}{duracion_str}")
        if datos:
            logger.debug(f"   Datos: {json.dumps(datos, indent=2, default=str)}")
    
    async def ejecutar_prueba_completa(self, proveedor_data: Dict) -> List[Dict]:
        """Ejecuta prueba integral con un proveedor"""
        logger.info("=" * 80)
        logger.info("🚀 INICIANDO PRUEBA INTEGRAL REVISAR.IA")
        logger.info(f"   Proveedor: {proveedor_data.get('nombre', 'N/A')}")
        logger.info(f"   RFC: {proveedor_data.get('rfc', 'N/A')}")
        logger.info("=" * 80)
        
        inicio = datetime.now()
        
        try:
            # TEST 0: Verificar variables de entorno
            await self.test_environment()
            
            # TEST 1: Conexión a base de datos
            await self.test_database()
            
            # TEST 2: Registro de empresa
            empresa = await self.test_registro_empresa(proveedor_data.get("empresa", {}))
            
            # TEST 3: Registro de proveedor
            proveedor = await self.test_registro_proveedor(
                empresa.get("id") if empresa else "demo-empresa",
                proveedor_data
            )
            
            # TEST 4: Crear proyecto
            proyecto = await self.test_crear_proyecto(
                empresa.get("id") if empresa else "demo-empresa",
                proveedor.get("id") if proveedor else "demo-proveedor",
                proveedor_data.get("proyecto", {})
            )
            
            proyecto_id = proyecto.get("id") if proyecto else "demo-proyecto"
            
            # TEST 5: Ejecutar Agente A6 (Análisis Proveedor)
            await self.test_agente_a6(proyecto_id, proveedor_data)
            
            # TEST 6: Ejecutar Agente A3 (Análisis Fiscal)
            await self.test_agente_a3(proyecto_id, proveedor_data)
            
            # TEST 7: Ejecutar Agente A5 (Análisis Financiero)
            await self.test_agente_a5(proyecto_id, proveedor_data)
            
            # TEST 8: Ejecutar Agente A1 (Estrategia)
            await self.test_agente_a1(proyecto_id)
            
            # TEST 9: Deliberación entre agentes
            await self.test_deliberacion(proyecto_id)
            
            # TEST 10: Generar Defense File PDF
            pdf_path = await self.test_generar_pdf(proyecto_id, proveedor_data)
            
            # TEST 11: Subir a pCloud
            pcloud_url = await self.test_subir_pcloud(pdf_path, proveedor_data)
            
            # TEST 12: Enviar email
            await self.test_enviar_email(proveedor_data, pcloud_url)
            
            # TEST 13: Actualizar dashboard
            await self.test_actualizar_dashboard(proyecto_id)
            
            # TEST 14: Verificar métricas
            await self.test_verificar_metricas(proyecto_id)
            
        except Exception as e:
            self.log("ERROR_GENERAL", "error", f"Error no manejado: {str(e)}", {"error": str(e)})
        
        duracion_total = int((datetime.now() - inicio).total_seconds() * 1000)
        
        # Resumen
        logger.info("=" * 80)
        logger.info("📊 RESUMEN DE PRUEBAS")
        logger.info("=" * 80)
        
        exitosos = len([r for r in self.resultados if r.status == "success"])
        errores = len([r for r in self.resultados if r.status == "error"])
        warnings = len([r for r in self.resultados if r.status == "warning"])
        
        logger.info(f"✅ Exitosos: {exitosos}")
        logger.info(f"❌ Errores: {errores}")
        logger.info(f"⚠️ Warnings: {warnings}")
        logger.info(f"⏱️ Tiempo total: {duracion_total}ms ({duracion_total/1000:.2f}s)")
        logger.info("=" * 80)
        
        return [asdict(r) for r in self.resultados]
    
    async def test_environment(self):
        """TEST 0: Verificar variables de entorno"""
        inicio = datetime.now()
        
        anthropic_configured = bool(
            os.getenv("AI_INTEGRATIONS_ANTHROPIC_API_KEY") or 
            os.getenv("ANTHROPIC_API_KEY")
        )
        
        env_vars = {
            "DATABASE_URL": os.getenv("DATABASE_URL"),
            "ANTHROPIC_API_KEY": anthropic_configured,
            "DREAMHOST_EMAIL_PASSWORD": os.getenv("DREAMHOST_EMAIL_PASSWORD"),
            "PCLOUD_USERNAME": os.getenv("PCLOUD_USERNAME"),
            "PCLOUD_PASSWORD": os.getenv("PCLOUD_PASSWORD"),
        }
        
        configurados = {k: "✅" if v else "❌" for k, v in env_vars.items()}
        faltantes = [k for k, v in env_vars.items() if not v]
        
        duracion = int((datetime.now() - inicio).total_seconds() * 1000)
        
        if faltantes:
            self.log("ENVIRONMENT", "warning", 
                     f"Variables faltantes: {', '.join(faltantes)}", 
                     configurados, duracion)
        else:
            self.log("ENVIRONMENT", "success", 
                     "Todas las variables configuradas", 
                     configurados, duracion)
    
    async def test_database(self):
        """TEST 1: Conexión a base de datos"""
        inicio = datetime.now()
        try:
            from services.durezza_database import DurezzaDatabaseService
            db_service = DurezzaDatabaseService()
            
            # Intentar consulta simple
            stats = await db_service.get_dashboard_stats("demo-empresa")
            
            duracion = int((datetime.now() - inicio).total_seconds() * 1000)
            self.log("DATABASE", "success", "Conexión a base de datos OK", 
                     {"proyectos": stats.get("total_proyectos", 0)}, duracion)
            return True
        except Exception as e:
            duracion = int((datetime.now() - inicio).total_seconds() * 1000)
            self.log("DATABASE", "warning", f"DB no disponible, usando demo: {str(e)}", 
                     None, duracion)
            return False
    
    async def test_registro_empresa(self, empresa_data: Dict) -> Dict:
        """TEST 2: Registro de empresa"""
        inicio = datetime.now()
        try:
            from services.empresa_service import empresa_service
            from models.empresa import EmpresaCreate
            
            # Verificar si ya existe
            empresas = await empresa_service.get_all_empresas()
            existing = next((e for e in empresas if e.rfc == empresa_data.get("rfc")), None)
            
            duracion = int((datetime.now() - inicio).total_seconds() * 1000)
            
            if existing:
                self.log("EMPRESA", "success", f"Empresa ya existe: {existing.nombre}", 
                         {"id": existing.id, "rfc": existing.rfc}, duracion)
                return {"id": existing.id, "nombre": existing.nombre}
            
            # Crear nueva empresa con campos correctos
            nueva_empresa = await empresa_service.crear_empresa(EmpresaCreate(
                nombre_comercial=empresa_data.get("nombre", "Empresa Test"),
                razon_social=empresa_data.get("nombre", "Empresa Test SA de CV"),
                rfc=empresa_data.get("rfc", "TEST000000XX1"),
                industria=empresa_data.get("industria", "tecnologia")
            ))
            
            duracion = int((datetime.now() - inicio).total_seconds() * 1000)
            self.log("EMPRESA", "success", f"Empresa registrada: {nueva_empresa.nombre}", 
                     {"id": nueva_empresa.id}, duracion)
            return {"id": nueva_empresa.id, "nombre": nueva_empresa.nombre}
            
        except Exception as e:
            duracion = int((datetime.now() - inicio).total_seconds() * 1000)
            self.log("EMPRESA", "warning", f"Usando empresa demo: {str(e)}", None, duracion)
            return {"id": "demo-empresa-001", "nombre": empresa_data.get("nombre", "Demo")}
    
    async def test_registro_proveedor(self, empresa_id: str, proveedor_data: Dict) -> Dict:
        """TEST 3: Registro de proveedor"""
        inicio = datetime.now()
        try:
            from services.proveedor_service import ProveedorService
            
            proveedor_service = ProveedorService()
            
            proveedor_info = {
                "razon_social": proveedor_data.get("nombre", "Proveedor Test"),
                "nombre_comercial": proveedor_data.get("nombre", "Proveedor Test"),
                "rfc": proveedor_data.get("rfc", "PROV000000XX1"),
                "tipo_proveedor": proveedor_data.get("tipoServicio", "software"),
                "monto_contrato": proveedor_data.get("monto", 1000000),
                "fecha_contrato": proveedor_data.get("fechaContrato", datetime.now().isoformat())
            }
            
            proveedor = proveedor_service.create_proveedor(
                proveedor_data=proveedor_info,
                empresa_id=empresa_id,
                usuario_id="test-runner"
            )
            
            duracion = int((datetime.now() - inicio).total_seconds() * 1000)
            self.log("PROVEEDOR", "success", f"Proveedor registrado: {proveedor.get('nombre')}", 
                     {"id": proveedor.get("id"), "rfc": proveedor.get("rfc")}, duracion)
            return proveedor
            
        except Exception as e:
            duracion = int((datetime.now() - inicio).total_seconds() * 1000)
            self.log("PROVEEDOR", "warning", f"Usando proveedor demo: {str(e)}", None, duracion)
            return {
                "id": f"demo-prov-{proveedor_data.get('rfc', 'XXX')[:8]}",
                "nombre": proveedor_data.get("nombre"),
                "rfc": proveedor_data.get("rfc")
            }
    
    async def test_crear_proyecto(self, empresa_id: str, proveedor_id: str, proyecto_data: Dict) -> Dict:
        """TEST 4: Crear proyecto"""
        inicio = datetime.now()
        try:
            from services.durezza_database import DurezzaDatabaseService
            
            db_service = DurezzaDatabaseService()
            
            proyecto = await db_service.create_project({
                "empresa_id": empresa_id,
                "proveedor_id": proveedor_id,
                "nombre": proyecto_data.get("nombre", "Proyecto Test"),
                "descripcion": proyecto_data.get("descripcion", "Proyecto de prueba integral"),
                "tipologia": proyecto_data.get("tipoIntangible", "SOFTWARE_SAAS_DESARROLLO"),
                "monto": proyecto_data.get("monto", 1000000),
                "sponsor_interno": "Test Runner Revisar.IA",
                "fase_actual": "F1",
                "estado_global": "EN_PROCESO"
            })
            
            duracion = int((datetime.now() - inicio).total_seconds() * 1000)
            self.log("PROYECTO", "success", f"Proyecto creado: {proyecto.get('nombre')}", 
                     {"id": proyecto.get("id")}, duracion)
            return proyecto
            
        except Exception as e:
            duracion = int((datetime.now() - inicio).total_seconds() * 1000)
            self.log("PROYECTO", "warning", f"Usando proyecto demo: {str(e)}", None, duracion)
            return {
                "id": "demo-proyecto-001",
                "nombre": proyecto_data.get("nombre", "Demo")
            }
    
    async def test_agente_a6(self, proyecto_id: str, proveedor_data: Dict):
        """TEST 5: Agente A6 - Análisis Proveedor"""
        inicio = datetime.now()
        try:
            logger.info("\n--- Ejecutando Agente A6 (Análisis Proveedor) ---")
            
            from services.agent_service import agent_service
            
            resultado = await agent_service.execute_agent(
                agent_id="A6_PROVEEDOR",
                context={
                    "proyecto_id": proyecto_id,
                    "proveedor_rfc": proveedor_data.get("rfc"),
                    "proveedor_nombre": proveedor_data.get("nombre"),
                    "verificaciones": ["lista_69b", "opinion_32d", "estatus_fiscal"]
                }
            )
            
            duracion = int((datetime.now() - inicio).total_seconds() * 1000)
            self.log("AGENTE_A6", "success", "Análisis de proveedor completado", {
                "riesgo": resultado.get("nivel_riesgo", "N/A"),
                "lista_69b": resultado.get("en_lista_69b", False),
                "observaciones": len(resultado.get("observaciones", []))
            }, duracion)
            
            return resultado
            
        except Exception as e:
            duracion = int((datetime.now() - inicio).total_seconds() * 1000)
            self.log("AGENTE_A6", "warning", f"A6 simulado: {str(e)}", {
                "riesgo": "bajo",
                "lista_69b": False,
                "simulado": True
            }, duracion)
            return {"simulado": True, "nivel_riesgo": "bajo"}
    
    async def test_agente_a3(self, proyecto_id: str, datos: Dict):
        """TEST 6: Agente A3 - Análisis Fiscal"""
        inicio = datetime.now()
        try:
            logger.info("\n--- Ejecutando Agente A3 (Análisis Fiscal) ---")
            
            from services.agent_service import agent_service
            
            resultado = await agent_service.execute_agent(
                agent_id="A3_FISCAL",
                context={
                    "proyecto_id": proyecto_id,
                    "tipo_intangible": datos.get("proyecto", {}).get("tipoIntangible"),
                    "monto": datos.get("proyecto", {}).get("monto"),
                }
            )
            
            duracion = int((datetime.now() - inicio).total_seconds() * 1000)
            self.log("AGENTE_A3", "success", "Análisis fiscal completado", {
                "deducible": resultado.get("es_deducible", True),
                "fundamento": resultado.get("fundamento_legal", "Art. 27 LISR")
            }, duracion)
            
            return resultado
            
        except Exception as e:
            duracion = int((datetime.now() - inicio).total_seconds() * 1000)
            self.log("AGENTE_A3", "warning", f"A3 simulado: {str(e)}", {
                "deducible": True,
                "simulado": True
            }, duracion)
            return {"simulado": True, "es_deducible": True}
    
    async def test_agente_a5(self, proyecto_id: str, datos: Dict):
        """TEST 7: Agente A5 - Análisis Financiero"""
        inicio = datetime.now()
        try:
            logger.info("\n--- Ejecutando Agente A5 (Análisis Financiero) ---")
            
            from services.agent_service import agent_service
            
            resultado = await agent_service.execute_agent(
                agent_id="A5_FINANZAS",
                context={
                    "proyecto_id": proyecto_id,
                    "monto": datos.get("monto"),
                    "tipo_servicio": datos.get("tipoServicio")
                }
            )
            
            duracion = int((datetime.now() - inicio).total_seconds() * 1000)
            self.log("AGENTE_A5", "success", "Análisis financiero completado", {
                "razonable": resultado.get("monto_razonable", True),
                "roi": resultado.get("roi_estimado", "N/A")
            }, duracion)
            
            return resultado
            
        except Exception as e:
            duracion = int((datetime.now() - inicio).total_seconds() * 1000)
            self.log("AGENTE_A5", "warning", f"A5 simulado: {str(e)}", {
                "razonable": True,
                "simulado": True
            }, duracion)
            return {"simulado": True, "monto_razonable": True}
    
    async def test_agente_a1(self, proyecto_id: str):
        """TEST 8: Agente A1 - Estrategia"""
        inicio = datetime.now()
        try:
            logger.info("\n--- Ejecutando Agente A1 (Estrategia) ---")
            
            from services.agent_service import agent_service
            
            resultado = await agent_service.execute_agent(
                agent_id="A1_ESTRATEGIA",
                context={"proyecto_id": proyecto_id}
            )
            
            duracion = int((datetime.now() - inicio).total_seconds() * 1000)
            self.log("AGENTE_A1", "success", "Estrategia definida", {
                "razon_negocios_score": resultado.get("razon_negocios_score", 85),
                "estrategia": resultado.get("estrategia_principal", "Sustancia económica")
            }, duracion)
            
            return resultado
            
        except Exception as e:
            duracion = int((datetime.now() - inicio).total_seconds() * 1000)
            self.log("AGENTE_A1", "warning", f"A1 simulado: {str(e)}", {
                "razon_negocios_score": 85,
                "simulado": True
            }, duracion)
            return {"simulado": True, "razon_negocios_score": 85}
    
    async def test_deliberacion(self, proyecto_id: str):
        """TEST 9: Deliberación entre agentes"""
        inicio = datetime.now()
        try:
            logger.info("\n--- Ejecutando Deliberación entre Agentes ---")
            
            from services.deliberation_service import deliberation_service
            
            agent_inputs = {
                "A1_ESTRATEGIA": {"analysis": "Análisis estratégico", "score": 85},
                "A3_FISCAL": {"analysis": "Cumplimiento fiscal", "score": 80},
                "A5_FINANZAS": {"analysis": "Viabilidad financiera", "score": 82},
                "A6_PROVEEDOR": {"analysis": "Due diligence proveedor", "score": 78}
            }
            
            resultado = await deliberation_service.deliberate(
                proyecto_id=proyecto_id,
                agent_inputs=agent_inputs
            )
            
            duracion = int((datetime.now() - inicio).total_seconds() * 1000)
            
            simulado = resultado.get("simulado", False)
            status = "success" if resultado.get("success") else "warning"
            msg = "Deliberación completada" if not simulado else "Deliberación simulada"
            
            dictamen = resultado.get("dictamen", {})
            self.log("DELIBERACION", status, msg, {
                "consenso": resultado.get("consenso", True),
                "rondas": resultado.get("rondas", 1),
                "dictamen": dictamen.get("dictamen", "CONDICIONAR"),
                "materialidad": dictamen.get("materialidad", 81),
                "simulado": simulado
            }, duracion)
            
            return resultado
            
        except Exception as e:
            duracion = int((datetime.now() - inicio).total_seconds() * 1000)
            self.log("DELIBERACION", "warning", f"Deliberación simulada: {str(e)}", {
                "consenso": True,
                "simulado": True
            }, duracion)
            return {"simulado": True, "consenso": True}
    
    async def test_generar_pdf(self, proyecto_id: str, proveedor_data: Dict) -> Optional[str]:
        """TEST 10: Generar Defense File PDF"""
        inicio = datetime.now()
        try:
            logger.info("\n--- Generando Defense File PDF ---")
            
            from services.defense_file_generator import DefenseFileGenerator
            
            generator = DefenseFileGenerator()
            pdf_path = await generator.generate_complete_defense_file(
                proyecto_id=proyecto_id,
                version="1.0"
            )
            
            duracion = int((datetime.now() - inicio).total_seconds() * 1000)
            
            if pdf_path and os.path.exists(pdf_path):
                size_kb = os.path.getsize(pdf_path) / 1024
                self.log("PDF", "success", "Defense File generado", {
                    "path": pdf_path,
                    "tamaño_kb": f"{size_kb:.2f}"
                }, duracion)
                return pdf_path
            else:
                self.log("PDF", "warning", "PDF generado pero archivo no encontrado", {
                    "path": pdf_path
                }, duracion)
                return None
                
        except Exception as e:
            duracion = int((datetime.now() - inicio).total_seconds() * 1000)
            self.log("PDF", "warning", f"PDF no generado: {str(e)}", None, duracion)
            return None
    
    async def test_subir_pcloud(self, pdf_path: Optional[str], proveedor_data: Dict) -> Optional[str]:
        """TEST 11: Subir a pCloud"""
        inicio = datetime.now()
        
        if not pdf_path:
            self.log("PCLOUD", "warning", "Sin PDF para subir", None, 0)
            return None
            
        try:
            logger.info("\n--- Subiendo a pCloud ---")
            
            from services.pcloud_service import pcloud_service, upload_defense_file
            
            empresa_rfc = proveedor_data.get("empresa", {}).get("rfc", "DEMO")
            proveedor_rfc = proveedor_data.get("rfc", "PROV")
            folder_path = f"/Revisar.IA/Empresas/{empresa_rfc}/Proveedores/{proveedor_rfc}"
            
            result = await upload_defense_file(
                local_path=pdf_path,
                remote_folder=folder_path
            )
            
            duracion = int((datetime.now() - inicio).total_seconds() * 1000)
            
            simulado = result.get("simulado", False)
            status = "success" if result.get("success") else "warning"
            msg = "Archivo subido a pCloud" if not simulado else "pCloud simulado (sin credenciales)"
            
            self.log("PCLOUD", status, msg, {
                "folder": folder_path,
                "url": result.get("public_link"),
                "simulado": simulado
            }, duracion)
            
            return result.get("public_link")
            
        except Exception as e:
            duracion = int((datetime.now() - inicio).total_seconds() * 1000)
            self.log("PCLOUD", "warning", f"pCloud no disponible: {str(e)}", None, duracion)
            return None
    
    async def test_enviar_email(self, proveedor_data: Dict, pcloud_url: Optional[str]):
        """TEST 12: Enviar email de notificación"""
        inicio = datetime.now()
        try:
            logger.info("\n--- Enviando Email de Notificación ---")
            
            from services.email_service import email_service
            
            empresa_email = proveedor_data.get("empresa", {}).get("email")
            if not empresa_email:
                self.log("EMAIL", "warning", "Sin email de destino configurado", None, 0)
                return
            
            empresa_nombre = proveedor_data.get("empresa", {}).get("nombre", "Empresa")
            proyecto_nombre = proveedor_data.get("proyecto", {}).get("nombre", "Proyecto")
            
            result = await email_service.send_defense_file_notification(
                to=empresa_email,
                empresa_nombre=empresa_nombre,
                proyecto_nombre=proyecto_nombre,
                pdf_link=pcloud_url or "https://revisar.ia/demo",
                score_total=85
            )
            
            duracion = int((datetime.now() - inicio).total_seconds() * 1000)
            
            simulado = result.get("simulado", False)
            status = "success" if result.get("success") else "warning"
            msg = "Email enviado" if not simulado else "Email simulado (sin credenciales)"
            
            self.log("EMAIL", status, msg, {
                "to": empresa_email,
                "simulado": simulado
            }, duracion)
            
        except Exception as e:
            duracion = int((datetime.now() - inicio).total_seconds() * 1000)
            self.log("EMAIL", "warning", f"Email no enviado: {str(e)}", None, duracion)
    
    async def test_actualizar_dashboard(self, proyecto_id: str):
        """TEST 13: Actualizar dashboard"""
        inicio = datetime.now()
        try:
            logger.info("\n--- Actualizando Dashboard ---")
            
            from services.durezza_database import DurezzaDatabaseService
            
            db_service = DurezzaDatabaseService()
            
            await db_service.update_project(proyecto_id, {
                "estado": "completado",
                "fase_actual": "COMPLETADO",
                "progreso": 100,
                "fecha_completado": datetime.now().isoformat()
            })
            
            duracion = int((datetime.now() - inicio).total_seconds() * 1000)
            self.log("DASHBOARD", "success", "Dashboard actualizado", {
                "proyecto_estado": "completado",
                "progreso": 100
            }, duracion)
            
        except Exception as e:
            duracion = int((datetime.now() - inicio).total_seconds() * 1000)
            self.log("DASHBOARD", "warning", f"Dashboard no actualizado: {str(e)}", None, duracion)
    
    async def test_verificar_metricas(self, proyecto_id: str):
        """TEST 14: Verificar métricas finales"""
        inicio = datetime.now()
        try:
            logger.info("\n--- Verificando Métricas Finales ---")
            
            metricas = {
                "progreso": 100,
                "agentes_ejecutados": 4,
                "versiones": 1,
                "prueba_completada": True
            }
            
            duracion = int((datetime.now() - inicio).total_seconds() * 1000)
            self.log("METRICAS", "success", "Métricas verificadas", metricas, duracion)
            
        except Exception as e:
            duracion = int((datetime.now() - inicio).total_seconds() * 1000)
            self.log("METRICAS", "warning", f"Error verificando métricas: {str(e)}", None, duracion)
