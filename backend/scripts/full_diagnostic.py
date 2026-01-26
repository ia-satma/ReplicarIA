#!/usr/bin/env python3
"""
full_diagnostic.py - Diagnóstico Completo del Sistema REVISAR.IA
Ejecutar: python -m scripts.full_diagnostic desde el directorio backend
"""

import asyncio
import asyncpg
import os
import sys
import json
import time
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.ERROR)


class SystemDiagnostic:
    """Clase principal para diagnóstico completo del sistema REVISAR.IA."""

    def __init__(self):
        self.results: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat(),
            "sistema": "REVISAR.IA",
            "version": "1.0",
            "diagnosticos": {},
            "metricas": {},
            "errores": [],
            "recomendaciones": [],
            "estado_general": "desconocido",
        }
        self.db_conn: Optional[asyncpg.Connection] = None
        self.backend_dir = Path(__file__).parent.parent

    async def run_all(self) -> Dict[str, Any]:
        """Ejecuta todos los diagnósticos del sistema."""
        print("\n" + "=" * 70)
        print("🔬 DIAGNÓSTICO COMPLETO DEL SISTEMA - REVISAR.IA")
        print("=" * 70)
        print(f"Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        try:
            # Ejecutar diagnósticos
            await asyncio.wait_for(self.check_environment(), timeout=5)
            await asyncio.wait_for(self.check_database(), timeout=10)
            await asyncio.wait_for(self.check_pgvector(), timeout=10)
            await asyncio.wait_for(self.check_frontend_build(), timeout=5)
            await asyncio.wait_for(self.check_api_endpoints(), timeout=15)
            await asyncio.wait_for(self.check_agents(), timeout=5)
            await asyncio.wait_for(self.check_vector_search(), timeout=5)
            await asyncio.wait_for(self.check_cache(), timeout=5)
            await asyncio.wait_for(self.analyze_code_quality(), timeout=10)

            # Generar recomendaciones y resumen
            self.generate_recommendations()
            self.calculate_health_score()
            self.print_summary()
            await asyncio.wait_for(self.save_report(), timeout=5)

        except asyncio.TimeoutError:
            print("\n⏱️ Advertencia: Algunos diagnósticos fueron interrumpidos por timeout")
            self.generate_recommendations()
            self.calculate_health_score()
            self.print_summary()
            try:
                await asyncio.wait_for(self.save_report(), timeout=3)
            except:
                print("⚠️ No se pudo guardar el reporte")
        except Exception as e:
            print(f"\n❌ Error durante el diagnóstico: {e}")
            try:
                await asyncio.wait_for(self.save_report(), timeout=3)
            except:
                pass
        finally:
            # Asegurar que la conexión se cierre
            if self.db_conn:
                try:
                    await self.db_conn.close()
                except:
                    pass

        return self.results

    async def check_environment(self) -> bool:
        """Verifica variables de entorno requeridas y opcionales."""
        print("📋 Verificando variables de entorno...")
        env_check = {
            "requeridas": {},
            "opcionales": {},
            "variables_detectadas": 0,
        }

        # Variables requeridas
        required_vars = ["DATABASE_URL"]
        for var in required_vars:
            value = os.getenv(var)
            is_present = bool(value)
            env_check["requeridas"][var] = {
                "presente": is_present,
                "estado": "✅" if is_present else "❌",
            }
            if is_present:
                env_check["variables_detectadas"] += 1
            status = "✅" if is_present else "❌"
            print(f"   {status} {var}: {'presente' if is_present else 'FALTA'}")

        # Variables opcionales
        optional_vars = ["REDIS_URL", "ANTHROPIC_API_KEY", "OPENAI_API_KEY"]
        for var in optional_vars:
            value = os.getenv(var)
            is_present = bool(value)
            env_check["opcionales"][var] = {
                "presente": is_present,
                "estado": "✅" if is_present else "⚠️",
            }
            if is_present:
                env_check["variables_detectadas"] += 1
            status = "✅" if is_present else "⚠️"
            print(f"   {status} {var}: {'presente' if is_present else 'no configurada'}")

        # Verificar variables críticas
        database_ok = os.getenv("DATABASE_URL") is not None
        api_keys_ok = bool(
            os.getenv("ANTHROPIC_API_KEY") or os.getenv("OPENAI_API_KEY")
        )

        env_check["database_configurada"] = database_ok
        env_check["api_keys_configuradas"] = api_keys_ok

        success = database_ok
        self.results["diagnosticos"]["variables_entorno"] = env_check
        self.results["metricas"]["variables_entorno_detectadas"] = (
            env_check["variables_detectadas"]
        )

        print(f"   📊 Total detectadas: {env_check['variables_detectadas']}\n")
        return success

    async def check_database(self) -> bool:
        """Verifica conexión a base de datos y existencia de tablas."""
        print("💾 Verificando base de datos...")
        db_check = {
            "conexion_exitosa": False,
            "tablas": {},
            "indices": 0,
            "total_registros": 0,
        }

        try:
            self.db_conn = await asyncpg.connect(os.getenv("DATABASE_URL"))
            db_check["conexion_exitosa"] = True
            print("   ✅ Conexión a PostgreSQL: exitosa")

            # Tablas requeridas
            required_tables = [
                ("empresas", "Empresas/Tenants"),
                ("users", "Usuarios"),
                ("projects", "Proyectos"),
                ("deliberations", "Deliberaciones"),
                ("knowledge_chunks", "Chunks RAG"),
                ("usage_tracking", "Tracking de Uso"),
                ("planes", "Planes"),
            ]

            total_records = 0
            for table_name, description in required_tables:
                try:
                    count = await self.db_conn.fetchval(
                        f"SELECT COUNT(*) FROM {table_name}"
                    )
                    db_check["tablas"][table_name] = {
                        "existe": True,
                        "registros": count,
                        "descripcion": description,
                    }
                    total_records += count
                    status = "✅"
                    print(f"   {status} {description}: {count} registros")
                except Exception as e:
                    db_check["tablas"][table_name] = {
                        "existe": False,
                        "error": str(e),
                        "descripcion": description,
                    }
                    print(f"   ⚠️ {description}: no existe")

            # Contar índices
            try:
                indices = await self.db_conn.fetchval(
                    "SELECT COUNT(*) FROM pg_indexes WHERE schemaname = 'public'"
                )
                db_check["indices"] = indices
                print(f"   📊 Índices: {indices}\n")
            except:
                pass

            db_check["total_registros"] = total_records
            self.results["diagnosticos"]["base_datos"] = db_check
            self.results["metricas"]["registros_totales"] = total_records
            return True

        except Exception as e:
            db_check["error"] = str(e)
            db_check["conexion_exitosa"] = False
            print(f"   ❌ Error: {e}\n")
            self.results["diagnosticos"]["base_datos"] = db_check
            self.results["errores"].append(f"Base de datos: {e}")
            return False

    async def check_pgvector(self) -> bool:
        """Verifica extensión pgvector y cobertura de embeddings."""
        print("🔍 Verificando pgvector y embeddings...")
        pgvector_check = {
            "extension_instalada": False,
            "columna_embedding": False,
            "chunks_totales": 0,
            "chunks_con_embedding": 0,
            "cobertura_porcentaje": 0.0,
        }

        if not self.db_conn:
            print("   ⚠️ Sin conexión a base de datos\n")
            return False

        try:
            # Verificar extensión
            has_extension = await self.db_conn.fetchval(
                "SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'vector')"
            )
            pgvector_check["extension_instalada"] = has_extension
            status = "✅" if has_extension else "❌"
            print(f"   {status} Extensión pgvector: {'instalada' if has_extension else 'NO instalada'}")

            # Verificar columna embedding
            try:
                has_column = await self.db_conn.fetchval(
                    """
                    SELECT EXISTS(
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name = 'knowledge_chunks' 
                        AND column_name = 'embedding'
                    )
                    """
                )
                pgvector_check["columna_embedding"] = has_column
                status = "✅" if has_column else "⚠️"
                print(
                    f"   {status} Columna embedding: {'existe' if has_column else 'NO existe'}"
                )

                if has_column:
                    # Contar cobertura de embeddings
                    total = await self.db_conn.fetchval(
                        "SELECT COUNT(*) FROM knowledge_chunks"
                    )
                    with_embedding = await self.db_conn.fetchval(
                        "SELECT COUNT(*) FROM knowledge_chunks WHERE embedding IS NOT NULL"
                    )

                    pgvector_check["chunks_totales"] = total
                    pgvector_check["chunks_con_embedding"] = with_embedding

                    if total > 0:
                        coverage = (with_embedding / total) * 100
                        pgvector_check["cobertura_porcentaje"] = round(coverage, 1)

                        if coverage >= 80:
                            status = "✅"
                        elif coverage >= 50:
                            status = "⚠️"
                        else:
                            status = "❌"

                        print(
                            f"   {status} Cobertura embeddings: {coverage:.1f}% ({with_embedding}/{total})"
                        )
                    else:
                        print(f"   ℹ️ Sin chunks en la base de datos")

            except Exception as e:
                print(f"   ⚠️ Error verificando embeddings: {e}")

            print()
            self.results["diagnosticos"]["pgvector"] = pgvector_check
            return pgvector_check["extension_instalada"]

        except Exception as e:
            pgvector_check["error"] = str(e)
            print(f"   ❌ Error: {e}\n")
            self.results["diagnosticos"]["pgvector"] = pgvector_check
            return False

    async def check_frontend_build(self) -> bool:
        """Verifica existencia y archivos del build del frontend."""
        print("🎨 Verificando build del frontend...")
        frontend_check = {
            "build_existe": False,
            "archivos": {},
            "archivos_clave": [],
            "archivos_faltantes": [],
        }

        build_dir = self.backend_dir.parent / "frontend" / "build"
        frontend_check["build_path"] = str(build_dir)
        frontend_check["build_existe"] = build_dir.exists()

        status = "✅" if build_dir.exists() else "⚠️"
        print(f"   {status} Directorio build: {'existe' if build_dir.exists() else 'NO existe'}")

        if build_dir.exists():
            # Archivos clave que debe tener
            key_files = [
                "index.html",
                "manifest.json",
            ]

            for file_name in key_files:
                file_path = build_dir / file_name
                exists = file_path.exists()
                frontend_check["archivos"][file_name] = exists
                status = "✅" if exists else "❌"
                print(f"   {status} {file_name}: {'presente' if exists else 'falta'}")
                if not exists:
                    frontend_check["archivos_faltantes"].append(file_name)
                else:
                    frontend_check["archivos_clave"].append(file_name)

            # Contar archivos CSS y JS
            try:
                static_dir = build_dir / "static"
                if static_dir.exists():
                    css_files = list(static_dir.glob("**/*.css"))
                    js_files = list(static_dir.glob("**/*.js"))
                    frontend_check["archivos"]["css_count"] = len(css_files)
                    frontend_check["archivos"]["js_count"] = len(js_files)
                    print(f"   📊 Archivos CSS: {len(css_files)}")
                    print(f"   📊 Archivos JS: {len(js_files)}")
            except:
                pass
        else:
            print("   ℹ️ Build del frontend no encontrado\n")

        print()
        self.results["diagnosticos"]["frontend_build"] = frontend_check
        return frontend_check["build_existe"]

    async def check_api_endpoints(self) -> bool:
        """Verifica accesibilidad de endpoints API."""
        print("🌐 Verificando endpoints API...")
        api_check = {
            "endpoints_probados": [],
            "endpoints_accesibles": 0,
            "base_url": "http://localhost:5000",
            "servidor_disponible": False,
        }

        endpoints = [
            "/api/health",
            "/docs",
            "/api/usage/plans",
        ]

        try:
            import httpx

            async with httpx.AsyncClient(timeout=2) as client:
                for endpoint in endpoints:
                    try:
                        start = time.perf_counter()
                        response = await client.get(
                            f"http://localhost:5000{endpoint}", timeout=2
                        )
                        latency = (time.perf_counter() - start) * 1000
                        accessible = response.status_code < 500

                        api_check["endpoints_probados"].append(
                            {
                                "endpoint": endpoint,
                                "accesible": accessible,
                                "status_code": response.status_code,
                                "latencia_ms": round(latency, 1),
                            }
                        )

                        if accessible:
                            api_check["endpoints_accesibles"] += 1
                            api_check["servidor_disponible"] = True
                            status = "✅"
                        else:
                            status = "⚠️"

                        print(
                            f"   {status} {endpoint}: {response.status_code} ({latency:.0f}ms)"
                        )
                    except asyncio.TimeoutError:
                        api_check["endpoints_probados"].append(
                            {
                                "endpoint": endpoint,
                                "accesible": False,
                                "error": "timeout",
                            }
                        )
                        print(f"   ⏱️ {endpoint}: timeout (servidor no responde)")
                    except Exception as e:
                        api_check["endpoints_probados"].append(
                            {
                                "endpoint": endpoint,
                                "accesible": False,
                                "error": str(e),
                            }
                        )
                        error_msg = str(e)[:50]
                        if "Connection refused" in error_msg or "connection" in error_msg.lower():
                            print(f"   ⏱️ {endpoint}: servidor no disponible")
                        else:
                            print(f"   ❌ {endpoint}: {error_msg}")

        except ImportError:
            print("   ⚠️ httpx no disponible para pruebas de API")

        if not api_check["endpoints_probados"]:
            print("   ℹ️ Pruebas de API omitidas o servidor no disponible")

        print()
        self.results["diagnosticos"]["endpoints_api"] = api_check
        return api_check["endpoints_accesibles"] > 0

    async def check_agents(self) -> bool:
        """Verifica configuración del sistema de agentes."""
        print("🤖 Verificando sistema de agentes...")
        agents_check = {
            "agentes_configurados": 0,
            "agentes": {},
            "orquestador_disponible": False,
        }

        try:
            from services.agent_orchestrator import AGENTS_CONFIG, get_orchestrator

            agents_check["agentes_configurados"] = len(AGENTS_CONFIG)
            agents_check["orquestador_disponible"] = True

            for agent_id, config in AGENTS_CONFIG.items():
                agents_check["agentes"][agent_id] = {
                    "nombre": config.get("name", "desconocido"),
                    "rol": config.get("role", ""),
                    "capacidades": len(config.get("capabilities", [])),
                }
                print(f"   ✅ {agent_id}: {config.get('name', 'N/A')}")

            print(
                f"   📊 Total de agentes: {len(AGENTS_CONFIG)}\n"
            )
            self.results["diagnosticos"]["agentes"] = agents_check
            return True

        except Exception as e:
            agents_check["error"] = str(e)
            agents_check["orquestador_disponible"] = False
            print(f"   ❌ Error cargando agentes: {e}\n")
            self.results["diagnosticos"]["agentes"] = agents_check
            self.results["errores"].append(f"Agentes: {e}")
            return False

    async def check_vector_search(self) -> bool:
        """Verifica disponibilidad del servicio de búsqueda vectorial."""
        print("🔎 Verificando servicio de búsqueda vectorial...")
        vector_check = {
            "servicio_disponible": False,
            "embedder_disponible": False,
            "pgvector_funcional": False,
        }

        try:
            from services.vector_search_service import vector_search_service

            vector_check["servicio_disponible"] = True
            print("   ✅ Servicio de búsqueda vectorial: disponible")

            # Verificar embedder
            try:
                if vector_search_service.embedder:
                    vector_check["embedder_disponible"] = True
                    print("   ✅ Embedder: disponible")
            except:
                print("   ⚠️ Embedder: no disponible")

            # Verificar pgvector
            try:
                if self.db_conn:
                    pgvector_available = (
                        await vector_search_service.check_pgvector_available()
                    )
                    vector_check["pgvector_funcional"] = pgvector_available
                    status = "✅" if pgvector_available else "⚠️"
                    print(
                        f"   {status} pgvector funcional: {'sí' if pgvector_available else 'no'}"
                    )
            except Exception as e:
                print(f"   ⚠️ Error verificando pgvector: {e}")

            print()

        except ImportError as e:
            vector_check["error"] = f"No se puede importar: {e}"
            print(f"   ⚠️ Servicio no disponible: {e}\n")

        self.results["diagnosticos"]["busqueda_vectorial"] = vector_check
        return vector_check["servicio_disponible"]

    async def check_cache(self) -> bool:
        """Verifica disponibilidad del servicio de caché (Redis)."""
        print("⚡ Verificando servicio de caché (Redis)...")
        cache_check = {
            "redis_url_configurada": False,
            "conexion_exitosa": False,
            "tipo_cache": "desconocido",
        }

        redis_url = os.getenv("REDIS_URL")
        cache_check["redis_url_configurada"] = bool(redis_url)

        if redis_url:
            try:
                import redis

                client = redis.from_url(redis_url)
                # Intentar ping
                response = client.ping()
                cache_check["conexion_exitosa"] = response
                cache_check["tipo_cache"] = "Redis"
                status = "✅" if response else "❌"
                print(f"   {status} Redis: conectado")
            except Exception as e:
                cache_check["conexion_exitosa"] = False
                cache_check["error"] = str(e)
                print(f"   ❌ Redis: {str(e)[:50]}")
        else:
            print("   ⚠️ REDIS_URL no configurada (cache en memoria)")
            cache_check["tipo_cache"] = "En Memoria"

        print()
        self.results["diagnosticos"]["cache"] = cache_check
        return cache_check["conexion_exitosa"] or not redis_url

    async def analyze_code_quality(self) -> bool:
        """Analiza métricas de calidad del código."""
        print("📈 Analizando calidad del código...")
        code_quality = {
            "archivos_python": 0,
            "archivos_javascript": 0,
            "directorios_analizados": [],
        }

        # Analizar backend
        backend_path = self.backend_dir
        py_files = list(backend_path.glob("**/*.py"))
        code_quality["archivos_python"] = len(py_files)
        print(f"   📊 Archivos Python: {len(py_files)}")

        # Contar líneas de código Python
        total_lines = 0
        for py_file in py_files:
            try:
                with open(py_file, "r", encoding="utf-8", errors="ignore") as f:
                    total_lines += len(f.readlines())
            except:
                pass

        code_quality["lineas_python_totales"] = total_lines
        print(f"   📊 Líneas de código Python: {total_lines}")

        # Analizar frontend
        frontend_path = self.backend_dir.parent / "frontend"
        if frontend_path.exists():
            js_files = list(frontend_path.glob("**/*.js"))
            jsx_files = list(frontend_path.glob("**/*.jsx"))
            ts_files = list(frontend_path.glob("**/*.ts"))
            tsx_files = list(frontend_path.glob("**/*.tsx"))

            js_total = len(js_files) + len(jsx_files) + len(ts_files) + len(tsx_files)
            code_quality["archivos_javascript"] = js_total

            total_js_lines = 0
            for js_file in js_files + jsx_files + ts_files + tsx_files:
                try:
                    with open(
                        js_file, "r", encoding="utf-8", errors="ignore"
                    ) as f:
                        total_js_lines += len(f.readlines())
                except:
                    pass

            code_quality["lineas_javascript_totales"] = total_js_lines
            print(f"   📊 Archivos JavaScript/TypeScript: {js_total}")
            print(f"   📊 Líneas de código JS/TS: {total_js_lines}")

        print()
        self.results["diagnosticos"]["calidad_codigo"] = code_quality
        self.results["metricas"]["lineas_codigo_totales"] = (
            total_lines + code_quality.get("lineas_javascript_totales", 0)
        )
        return True

    def generate_recommendations(self) -> None:
        """Genera recomendaciones basadas en los diagnósticos."""
        print("💡 Generando recomendaciones...")
        recommendations = []

        # Verificar variables de entorno
        env_check = self.results["diagnosticos"].get("variables_entorno", {})
        if not env_check.get("api_keys_configuradas"):
            recommendations.append(
                {
                    "prioridad": "alta",
                    "area": "API Keys",
                    "problema": "No hay API keys configuradas",
                    "solucion": "Configura ANTHROPIC_API_KEY u OPENAI_API_KEY",
                }
            )

        # Verificar base de datos
        db_check = self.results["diagnosticos"].get("base_datos", {})
        if not db_check.get("conexion_exitosa"):
            recommendations.append(
                {
                    "prioridad": "crítica",
                    "area": "Base de Datos",
                    "problema": "No hay conexión a PostgreSQL",
                    "solucion": "Verifica DATABASE_URL y estado de la base de datos",
                }
            )

        # Verificar pgvector
        pgvector_check = self.results["diagnosticos"].get("pgvector", {})
        if not pgvector_check.get("extension_instalada"):
            recommendations.append(
                {
                    "prioridad": "media",
                    "area": "Búsqueda Vectorial",
                    "problema": "pgvector no está instalado",
                    "solucion": "Ejecuta: python backend/scripts/setup_pgvector.py",
                }
            )

        coverage = pgvector_check.get("cobertura_porcentaje", 0)
        if 0 < coverage < 50:
            recommendations.append(
                {
                    "prioridad": "media",
                    "area": "Embeddings",
                    "problema": f"Cobertura de embeddings baja ({coverage}%)",
                    "solucion": "Ejecuta: python backend/scripts/migrate_embeddings.py",
                }
            )

        # Verificar frontend build
        frontend_check = self.results["diagnosticos"].get("frontend_build", {})
        if not frontend_check.get("build_existe"):
            recommendations.append(
                {
                    "prioridad": "media",
                    "area": "Frontend",
                    "problema": "Build del frontend no encontrado",
                    "solucion": "Ejecuta: cd frontend && npm run build",
                }
            )

        if frontend_check.get("archivos_faltantes"):
            recommendations.append(
                {
                    "prioridad": "baja",
                    "area": "Frontend",
                    "problema": f"Archivos faltantes: {', '.join(frontend_check['archivos_faltantes'])}",
                    "solucion": "Reconstruye el frontend",
                }
            )

        # Verificar caché
        cache_check = self.results["diagnosticos"].get("cache", {})
        if not cache_check.get("conexion_exitosa") and cache_check.get(
            "redis_url_configurada"
        ):
            recommendations.append(
                {
                    "prioridad": "media",
                    "area": "Caché",
                    "problema": "Redis no está accesible",
                    "solucion": "Verifica la conexión a Redis o desactiva el uso de caché",
                }
            )

        # Verificar agentes
        agents_check = self.results["diagnosticos"].get("agentes", {})
        if not agents_check.get("orquestador_disponible"):
            recommendations.append(
                {
                    "prioridad": "alta",
                    "area": "Agentes IA",
                    "problema": "Orquestador de agentes no disponible",
                    "solucion": "Verifica la instalación de dependencias de Claude/IA",
                }
            )

        self.results["recomendaciones"] = recommendations
        print(f"   ℹ️ {len(recommendations)} recomendaciones generadas\n")

    def calculate_health_score(self) -> None:
        """Calcula una puntuación de salud del sistema."""
        diagnostics = self.results["diagnosticos"]
        score = 100.0
        max_points = 10
        points = 0

        # Verificaciones puntuables
        checks = [
            (diagnostics.get("variables_entorno", {}).get("database_configurada"), 10),
            (
                diagnostics.get("base_datos", {}).get("conexion_exitosa"),
                15,
            ),
            (
                diagnostics.get("pgvector", {}).get("extension_instalada"),
                5,
            ),
            (
                diagnostics.get("pgvector", {}).get("cobertura_porcentaje", 0)
                > 50,
                5,
            ),
            (diagnostics.get("frontend_build", {}).get("build_existe"), 10),
            (
                diagnostics.get("endpoints_api", {}).get("endpoints_accesibles", 0)
                > 0,
                10,
            ),
            (
                diagnostics.get("agentes", {}).get("orquestador_disponible"),
                15,
            ),
            (diagnostics.get("busqueda_vectorial", {}).get("servicio_disponible"), 10),
            (diagnostics.get("cache", {}).get("conexion_exitosa"), 10),
            (diagnostics.get("calidad_codigo", {}).get("archivos_python", 0) > 0, 10),
        ]

        total_points = 0
        for check, weight in checks:
            total_points += weight
            if check:
                points += weight

        health_percentage = (points / total_points * 100) if total_points > 0 else 0
        health_percentage = min(100, health_percentage)

        # Determinar estado general
        if health_percentage >= 80:
            status = "🟢 SALUDABLE"
        elif health_percentage >= 60:
            status = "🟡 DEGRADADO"
        elif health_percentage >= 40:
            status = "🟠 CRÍTICO"
        else:
            status = "🔴 INOPERABLE"

        self.results["puntuacion_salud"] = round(health_percentage, 1)
        self.results["estado_general"] = status
        self.results["puntos_diagnostico"] = f"{points}/{total_points}"

    def print_summary(self) -> None:
        """Imprime un resumen ejecutivo del diagnóstico."""
        print("=" * 70)
        print("📊 RESUMEN EJECUTIVO DEL DIAGNÓSTICO")
        print("=" * 70)

        # Estado general
        print(f"\n{self.results['estado_general']}")
        print(
            f"Puntuación de Salud: {self.results['puntuacion_salud']}% ({self.results['puntos_diagnostico']})"
        )

        # Verificaciones clave
        print("\n🔍 VERIFICACIONES CLAVE:")
        diagnostics = self.results["diagnosticos"]

        checks_summary = [
            (
                "Variables de Entorno",
                diagnostics.get("variables_entorno", {}).get(
                    "database_configurada", False
                ),
            ),
            (
                "Base de Datos",
                diagnostics.get("base_datos", {}).get("conexion_exitosa", False),
            ),
            (
                "pgvector Extension",
                diagnostics.get("pgvector", {}).get("extension_instalada", False),
            ),
            (
                "Cobertura de Embeddings",
                diagnostics.get("pgvector", {}).get("cobertura_porcentaje", 0) > 50,
            ),
            (
                "Frontend Build",
                diagnostics.get("frontend_build", {}).get("build_existe", False),
            ),
            (
                "Endpoints API",
                diagnostics.get("endpoints_api", {}).get("endpoints_accesibles", 0)
                > 0,
            ),
            (
                "Sistema de Agentes",
                diagnostics.get("agentes", {}).get("orquestador_disponible", False),
            ),
            (
                "Búsqueda Vectorial",
                diagnostics.get("busqueda_vectorial", {}).get(
                    "servicio_disponible", False
                ),
            ),
            (
                "Caché (Redis)",
                diagnostics.get("cache", {}).get("conexion_exitosa", False),
            ),
        ]

        for check_name, status in checks_summary:
            symbol = "✅" if status else "❌"
            print(f"   {symbol} {check_name}")

        # Métricas
        print("\n📈 MÉTRICAS:")
        metrics = self.results["metricas"]
        if "registros_totales" in metrics:
            print(f"   📊 Total de registros BD: {metrics['registros_totales']}")
        if "lineas_codigo_totales" in metrics:
            print(f"   📊 Líneas de código: {metrics['lineas_codigo_totales']}")
        if "variables_entorno_detectadas" in metrics:
            print(f"   📊 Variables de entorno: {metrics['variables_entorno_detectadas']}")

        # Recomendaciones
        if self.results["recomendaciones"]:
            print(f"\n💡 RECOMENDACIONES ({len(self.results['recomendaciones'])}):")
            for i, rec in enumerate(self.results["recomendaciones"][:5], 1):
                priority_icon = (
                    "🔴"
                    if rec["prioridad"] == "crítica"
                    else "🟠"
                    if rec["prioridad"] == "alta"
                    else "🟡"
                )
                print(f"   {priority_icon} [{rec['area']}] {rec['problema']}")
                print(f"      → {rec['solucion']}")

            if len(self.results["recomendaciones"]) > 5:
                print(
                    f"   ... y {len(self.results['recomendaciones']) - 5} recomendaciones más"
                )

        # Errores
        if self.results["errores"]:
            print(f"\n⚠️ ERRORES DETECTADOS ({len(self.results['errores'])}):")
            for error in self.results["errores"][:3]:
                print(f"   ❌ {error}")
            if len(self.results["errores"]) > 3:
                print(f"   ... y {len(self.results['errores']) - 3} errores más")

        print("\n" + "=" * 70)
        print(f"Fin del diagnóstico: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70 + "\n")

    async def save_report(self) -> None:
        """Guarda el reporte completo en formato JSON."""
        output_file = self.backend_dir / "full_diagnostic_report.json"

        try:
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(self.results, f, indent=2, ensure_ascii=False, default=str)

            print(f"✅ Reporte guardado: {output_file}")
        except Exception as e:
            print(f"⚠️ Error guardando reporte: {e}")
        finally:
            # Cerrar conexión si existe
            if self.db_conn:
                await self.db_conn.close()


async def main():
    """Función principal."""
    diagnostic = SystemDiagnostic()
    results = await diagnostic.run_all()
    return results


if __name__ == "__main__":
    asyncio.run(main())
