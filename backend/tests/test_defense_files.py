#!/usr/bin/env python3
"""
Test Script - Defense Files API
Sistema de pruebas completo para expedientes de defensa Revisar.IA

Ejecutar: python backend/tests/test_defense_files.py
"""
import sys
import os
import json
import time
import random
import string
from datetime import datetime
from typing import Dict, Any, Tuple, List

try:
    import requests
except ImportError:
    print("❌ Error: requests library not installed. Run: pip install requests")
    sys.exit(1)

BASE_URL = os.environ.get("TEST_BASE_URL", "http://localhost:5000")
API_URL = f"{BASE_URL}/api/defense-files"

CLIENTE_ID = 5


class TestResult:
    """Resultado de un test individual."""
    def __init__(self, name: str, passed: bool, message: str, details: Any = None):
        self.name = name
        self.passed = passed
        self.message = message
        self.details = details

    def __str__(self):
        emoji = "✅" if self.passed else "❌"
        return f"{emoji} {self.name}: {self.message}"


class DefenseFilesTestSuite:
    """Suite de pruebas para Defense Files API."""

    def __init__(self, base_url: str = API_URL, cliente_id: int = CLIENTE_ID):
        self.base_url = base_url
        self.cliente_id = cliente_id
        self.results: List[TestResult] = []
        self.created_defense_file_id: int = None
        self.created_proveedor_id: int = None
        self.created_fundamento_id: int = None
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json"
        })

    def _generate_unique_name(self, prefix: str) -> str:
        """Genera un nombre único para tests."""
        suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        return f"{prefix}_{suffix}_{int(time.time())}"

    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Dict = None,
        params: Dict = None
    ) -> Tuple[bool, Dict]:
        """Realiza una petición HTTP y retorna (success, response_data)."""
        url = f"{self.base_url}{endpoint}"
        try:
            if method.upper() == "GET":
                response = self.session.get(url, params=params, timeout=30)
            elif method.upper() == "POST":
                response = self.session.post(url, json=data, timeout=30)
            elif method.upper() == "PUT":
                response = self.session.put(url, json=data, timeout=30)
            elif method.upper() == "DELETE":
                response = self.session.delete(url, timeout=30)
            else:
                return False, {"error": f"Método HTTP no soportado: {method}"}

            if response.status_code >= 200 and response.status_code < 300:
                return True, response.json()
            else:
                try:
                    error_data = response.json()
                except:
                    error_data = {"error": response.text}
                return False, error_data

        except requests.exceptions.ConnectionError:
            return False, {"error": "No se pudo conectar al servidor"}
        except requests.exceptions.Timeout:
            return False, {"error": "Timeout en la petición"}
        except Exception as e:
            return False, {"error": str(e)}

    def test_01_crear_defense_file(self) -> TestResult:
        """Test 1: Crear Defense File (POST /api/defense-files)."""
        test_name = "Test 01: Crear Defense File"
        
        nombre = self._generate_unique_name("ExpedientePrueba")
        data = {
            "cliente_id": self.cliente_id,
            "nombre": nombre,
            "anio_fiscal": 2025,
            "descripcion": "Expediente creado durante pruebas automatizadas"
        }

        success, response = self._make_request("POST", "", data=data)

        if success and response.get("success"):
            defense_file = response.get("defense_file", {})
            self.created_defense_file_id = defense_file.get("id")
            
            if self.created_defense_file_id:
                result = TestResult(
                    test_name,
                    True,
                    f"Expediente creado correctamente (ID: {self.created_defense_file_id})",
                    defense_file
                )
            else:
                result = TestResult(test_name, False, "No se retornó ID del expediente", response)
        else:
            error = response.get("error", "Error desconocido")
            result = TestResult(test_name, False, f"Error al crear expediente: {error}", response)

        self.results.append(result)
        return result

    def test_02_listar_defense_files(self) -> TestResult:
        """Test 2: Listar Defense Files (GET /api/defense-files)."""
        test_name = "Test 02: Listar Defense Files"

        success, response = self._make_request("GET", "", params={"limit": 10})

        if success and response.get("success"):
            defense_files = response.get("defense_files", [])
            total = response.get("total", 0)
            
            has_created = any(
                df.get("id") == self.created_defense_file_id 
                for df in defense_files
            ) if self.created_defense_file_id else True

            if has_created:
                result = TestResult(
                    test_name,
                    True,
                    f"Listado correcto: {len(defense_files)} expedientes (total: {total})",
                    {"count": len(defense_files), "total": total}
                )
            else:
                result = TestResult(
                    test_name,
                    False,
                    "El expediente creado no aparece en el listado",
                    response
                )
        else:
            error = response.get("error", "Error desconocido")
            result = TestResult(test_name, False, f"Error al listar: {error}", response)

        self.results.append(result)
        return result

    def test_03_obtener_defense_file(self) -> TestResult:
        """Test 3: Obtener Defense File específico (GET /api/defense-files/{id})."""
        test_name = "Test 03: Obtener Defense File"

        if not self.created_defense_file_id:
            result = TestResult(test_name, False, "No hay expediente de prueba creado", None)
            self.results.append(result)
            return result

        success, response = self._make_request("GET", f"/{self.created_defense_file_id}")

        if success and response.get("success"):
            defense_file = response.get("defense_file", {})
            estadisticas = defense_file.get("estadisticas", {})
            
            if defense_file.get("id") == self.created_defense_file_id:
                result = TestResult(
                    test_name,
                    True,
                    f"Expediente obtenido correctamente con estadísticas",
                    {
                        "id": defense_file.get("id"),
                        "nombre": defense_file.get("nombre"),
                        "estado": defense_file.get("estado"),
                        "estadisticas": estadisticas
                    }
                )
            else:
                result = TestResult(test_name, False, "ID no coincide", response)
        else:
            error = response.get("error", "Error desconocido")
            result = TestResult(test_name, False, f"Error al obtener: {error}", response)

        self.results.append(result)
        return result

    def test_04_registrar_evento(self) -> TestResult:
        """Test 4: Registrar evento (POST /api/defense-files/{id}/eventos)."""
        test_name = "Test 04: Registrar Evento"

        if not self.created_defense_file_id:
            result = TestResult(test_name, False, "No hay expediente de prueba creado", None)
            self.results.append(result)
            return result

        data = {
            "tipo": "analisis_ia",
            "agente": "A3",
            "titulo": "Análisis fiscal automatizado",
            "descripcion": "Evento de prueba para verificar registro en bitácora",
            "datos": {
                "fuente": "test_suite",
                "timestamp": datetime.now().isoformat()
            },
            "tags": ["test", "automatico"]
        }

        success, response = self._make_request(
            "POST",
            f"/{self.created_defense_file_id}/eventos",
            data=data
        )

        if success and response.get("success"):
            evento = response.get("evento", {})
            hash_evento = evento.get("hash_evento")
            
            if evento.get("id") and hash_evento:
                result = TestResult(
                    test_name,
                    True,
                    f"Evento registrado con hash de integridad",
                    {
                        "evento_id": evento.get("id"),
                        "tipo": evento.get("tipo"),
                        "hash_length": len(hash_evento) if hash_evento else 0
                    }
                )
            else:
                result = TestResult(test_name, False, "Evento sin ID o hash", response)
        else:
            error = response.get("error", "Error desconocido")
            result = TestResult(test_name, False, f"Error al registrar: {error}", response)

        self.results.append(result)
        return result

    def test_05_obtener_timeline(self) -> TestResult:
        """Test 5: Obtener timeline (GET /api/defense-files/{id}/timeline)."""
        test_name = "Test 05: Obtener Timeline"

        if not self.created_defense_file_id:
            result = TestResult(test_name, False, "No hay expediente de prueba creado", None)
            self.results.append(result)
            return result

        success, response = self._make_request(
            "GET",
            f"/{self.created_defense_file_id}/timeline"
        )

        if success and response.get("success"):
            timeline = response.get("timeline", [])
            total = response.get("total", 0)
            
            if total > 0:
                result = TestResult(
                    test_name,
                    True,
                    f"Timeline obtenido con {total} eventos",
                    {
                        "total_eventos": total,
                        "primer_evento": timeline[0].get("titulo") if timeline else None
                    }
                )
            else:
                result = TestResult(test_name, False, "Timeline vacío", response)
        else:
            error = response.get("error", "Error desconocido")
            result = TestResult(test_name, False, f"Error al obtener timeline: {error}", response)

        self.results.append(result)
        return result

    def test_06_registrar_proveedor(self) -> TestResult:
        """Test 6: Registrar proveedor (POST /api/defense-files/{id}/proveedores)."""
        test_name = "Test 06: Registrar Proveedor"

        if not self.created_defense_file_id:
            result = TestResult(test_name, False, "No hay expediente de prueba creado", None)
            self.results.append(result)
            return result

        rfc_suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
        data = {
            "rfc": f"TEST{rfc_suffix}001",
            "razon_social": "Proveedor de Prueba SA de CV",
            "nombre_comercial": "Proveedor Test",
            "lista_69b_status": "no_listado",
            "efos_status": "no_efos",
            "opinion_cumplimiento": "positiva",
            "nivel_riesgo": "bajo",
            "notas_riesgo": "Proveedor registrado durante pruebas automatizadas"
        }

        success, response = self._make_request(
            "POST",
            f"/{self.created_defense_file_id}/proveedores",
            data=data
        )

        if success and response.get("success"):
            proveedor = response.get("proveedor", {})
            self.created_proveedor_id = proveedor.get("id")
            
            if self.created_proveedor_id:
                result = TestResult(
                    test_name,
                    True,
                    f"Proveedor registrado (ID: {self.created_proveedor_id})",
                    {
                        "proveedor_id": self.created_proveedor_id,
                        "rfc": proveedor.get("rfc"),
                        "nivel_riesgo": proveedor.get("nivel_riesgo")
                    }
                )
            else:
                result = TestResult(test_name, False, "No se retornó ID del proveedor", response)
        else:
            error = response.get("error", "Error desconocido")
            result = TestResult(test_name, False, f"Error al registrar: {error}", response)

        self.results.append(result)
        return result

    def test_07_listar_proveedores(self) -> TestResult:
        """Test 7: Listar proveedores (GET /api/defense-files/{id}/proveedores)."""
        test_name = "Test 07: Listar Proveedores"

        if not self.created_defense_file_id:
            result = TestResult(test_name, False, "No hay expediente de prueba creado", None)
            self.results.append(result)
            return result

        success, response = self._make_request(
            "GET",
            f"/{self.created_defense_file_id}/proveedores"
        )

        if success and response.get("success"):
            proveedores = response.get("proveedores", [])
            total = response.get("total", len(proveedores))
            
            has_created = any(
                p.get("id") == self.created_proveedor_id 
                for p in proveedores
            ) if self.created_proveedor_id else True

            if has_created and total > 0:
                result = TestResult(
                    test_name,
                    True,
                    f"Listado correcto: {total} proveedores",
                    {"count": total, "proveedores": [p.get("rfc") for p in proveedores]}
                )
            else:
                result = TestResult(
                    test_name,
                    False,
                    "Proveedor creado no encontrado en listado",
                    response
                )
        else:
            error = response.get("error", "Error desconocido")
            result = TestResult(test_name, False, f"Error al listar: {error}", response)

        self.results.append(result)
        return result

    def test_08_registrar_fundamento(self) -> TestResult:
        """Test 8: Registrar fundamento (POST /api/defense-files/{id}/fundamentos)."""
        test_name = "Test 08: Registrar Fundamento"

        if not self.created_defense_file_id:
            result = TestResult(test_name, False, "No hay expediente de prueba creado", None)
            self.results.append(result)
            return result

        data = {
            "tipo": "legal",
            "documento": "CFF",
            "articulo": "5-A",
            "texto_relevante": "Los actos jurídicos que carezcan de una razón de negocios...",
            "fraccion": "I",
            "titulo": "Razón de Negocios",
            "aplicacion": "Fundamento para defensa de operaciones con sustancia económica"
        }

        success, response = self._make_request(
            "POST",
            f"/{self.created_defense_file_id}/fundamentos",
            data=data
        )

        if success and response.get("success"):
            fundamento = response.get("fundamento", {})
            self.created_fundamento_id = fundamento.get("id")
            
            if self.created_fundamento_id:
                result = TestResult(
                    test_name,
                    True,
                    f"Fundamento registrado (ID: {self.created_fundamento_id})",
                    {
                        "fundamento_id": self.created_fundamento_id,
                        "documento": fundamento.get("documento"),
                        "articulo": fundamento.get("articulo")
                    }
                )
            else:
                result = TestResult(test_name, False, "No se retornó ID del fundamento", response)
        else:
            error = response.get("error", "Error desconocido")
            result = TestResult(test_name, False, f"Error al registrar: {error}", response)

        self.results.append(result)
        return result

    def test_09_verificar_integridad(self) -> TestResult:
        """Test 9: Verificar integridad (GET /api/defense-files/{id}/verificar-integridad)."""
        test_name = "Test 09: Verificar Integridad Cadena Hashes"

        if not self.created_defense_file_id:
            result = TestResult(test_name, False, "No hay expediente de prueba creado", None)
            self.results.append(result)
            return result

        success, response = self._make_request(
            "GET",
            f"/{self.created_defense_file_id}/verificar-integridad"
        )

        if success and response.get("success"):
            integridad_valida = response.get("integridad_valida", False)
            total_eventos = response.get("total_eventos", 0)
            eventos_validos = response.get("eventos_validos", 0)
            mensaje = response.get("mensaje", "")
            
            if integridad_valida and total_eventos == eventos_validos:
                result = TestResult(
                    test_name,
                    True,
                    f"Cadena de hashes válida ({eventos_validos}/{total_eventos} eventos)",
                    {
                        "integridad_valida": integridad_valida,
                        "total_eventos": total_eventos,
                        "eventos_validos": eventos_validos,
                        "mensaje": mensaje
                    }
                )
            else:
                result = TestResult(
                    test_name,
                    False,
                    f"Integridad comprometida: {mensaje}",
                    response
                )
        else:
            error = response.get("error", "Error desconocido")
            result = TestResult(test_name, False, f"Error al verificar: {error}", response)

        self.results.append(result)
        return result

    def test_10_estadisticas_globales(self) -> TestResult:
        """Test 10: Estadísticas globales (GET /api/defense-files/stats)."""
        test_name = "Test 10: Estadísticas Globales"

        success, response = self._make_request("GET", "/stats")

        if success and response.get("success"):
            estadisticas = response.get("estadisticas", {})
            total_expedientes = estadisticas.get("total_expedientes", 0)
            
            if total_expedientes > 0:
                result = TestResult(
                    test_name,
                    True,
                    f"Estadísticas obtenidas: {total_expedientes} expedientes totales",
                    estadisticas
                )
            else:
                result = TestResult(
                    test_name,
                    True,
                    "Estadísticas obtenidas (sin expedientes)",
                    estadisticas
                )
        else:
            error = response.get("error", "Error desconocido")
            result = TestResult(test_name, False, f"Error al obtener stats: {error}", response)

        self.results.append(result)
        return result

    def run_all_tests(self) -> Dict[str, Any]:
        """Ejecuta todos los tests y retorna resumen."""
        print("\n" + "="*70)
        print("🧪 DEFENSE FILES API - SUITE DE PRUEBAS")
        print("="*70)
        print(f"📍 Base URL: {self.base_url}")
        print(f"👤 Cliente ID: {self.cliente_id}")
        print(f"🕐 Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*70 + "\n")

        tests = [
            self.test_01_crear_defense_file,
            self.test_02_listar_defense_files,
            self.test_03_obtener_defense_file,
            self.test_04_registrar_evento,
            self.test_05_obtener_timeline,
            self.test_06_registrar_proveedor,
            self.test_07_listar_proveedores,
            self.test_08_registrar_fundamento,
            self.test_09_verificar_integridad,
            self.test_10_estadisticas_globales,
        ]

        for test_func in tests:
            try:
                result = test_func()
                print(result)
            except Exception as e:
                result = TestResult(test_func.__name__, False, f"Excepción: {str(e)}")
                self.results.append(result)
                print(result)

        return self._generate_summary()

    def _generate_summary(self) -> Dict[str, Any]:
        """Genera resumen de resultados."""
        total = len(self.results)
        passed = sum(1 for r in self.results if r.passed)
        failed = total - passed
        percentage = (passed / total * 100) if total > 0 else 0

        print("\n" + "="*70)
        print("📊 RESUMEN DE RESULTADOS")
        print("="*70)
        print(f"   Total de tests:    {total}")
        print(f"   ✅ Pasados:         {passed}")
        print(f"   ❌ Fallidos:        {failed}")
        print(f"   📈 Porcentaje:      {percentage:.1f}%")
        print("="*70)

        status_emoji = "✅" if percentage >= 80 else "⚠️" if percentage >= 60 else "❌"
        status_msg = "EXITOSO" if percentage >= 80 else "PARCIAL" if percentage >= 60 else "FALLIDO"
        
        print(f"\n{status_emoji} RESULTADO FINAL: {status_msg} ({percentage:.1f}%)")
        
        if percentage >= 80:
            print("   El sistema de Defense Files está funcionando correctamente.")
        else:
            print("   Se requiere revisión de los componentes fallidos.")

        print("\n" + "="*70)
        print(f"🕐 Fin: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*70 + "\n")

        return {
            "total": total,
            "passed": passed,
            "failed": failed,
            "percentage": percentage,
            "status": status_msg,
            "created_defense_file_id": self.created_defense_file_id,
            "results": [
                {
                    "name": r.name,
                    "passed": r.passed,
                    "message": r.message
                }
                for r in self.results
            ]
        }


def main():
    """Punto de entrada principal."""
    print("\n🚀 Iniciando pruebas de Defense Files API...")
    
    test_url = os.environ.get("TEST_BASE_URL", "http://localhost:5000")
    print(f"🔗 Verificando conectividad con {test_url}...")
    
    try:
        response = requests.get(f"{test_url}/api/defense-files/stats", timeout=10)
        if response.status_code != 200:
            print(f"❌ Error: Servidor respondió con código {response.status_code}")
            sys.exit(1)
        print("✅ Servidor disponible")
    except requests.exceptions.ConnectionError:
        print(f"❌ Error: No se pudo conectar a {test_url}")
        print("   Asegúrate de que el backend esté ejecutándose.")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        sys.exit(1)

    suite = DefenseFilesTestSuite()
    summary = suite.run_all_tests()

    if summary["percentage"] >= 80:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
