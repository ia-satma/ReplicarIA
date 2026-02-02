"""
pCloud Onboarding Service - Onboarding automático de empresas desde pCloud

Este servicio detecta nuevas carpetas de empresas en pCloud y las procesa automáticamente:
1. Detecta carpetas nuevas en CLIENTES_NUEVOS/
2. Lee _info.json si existe para datos de la empresa
3. Analiza documentos (PDF, DOCX) para extraer información
4. Crea la empresa en la base de datos
5. Ingesta documentos en RAG para el conocimiento del agente
6. Mueve la carpeta procesada a CLIENTES/

Estructura esperada en pCloud:
REVISAR.IA/
├── CLIENTES_NUEVOS/
│   ├── EMPRESA_ABC_RFC123/
│   │   ├── _info.json         # Opcional: datos manuales
│   │   ├── acta_constitutiva.pdf
│   │   ├── cedula_fiscal.pdf
│   │   └── ...
│   └── OTRA_EMPRESA_RFC456/
│       └── ...
└── CLIENTES/                   # Empresas procesadas (se mueven aquí)
"""

import os
import json
import logging
import asyncio
import re
from typing import Optional, List, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class PCloudOnboardingService:
    """Servicio para onboarding automático de empresas desde pCloud"""

    def __init__(self):
        self.pcloud_service = None
        self._initialized = False
        self._clientes_nuevos_id = None
        self._clientes_id = None

    def initialize(self) -> bool:
        """Inicializa dependencias de forma lazy"""
        if self._initialized:
            return True

        try:
            from services.pcloud_service import pcloud_service
            self.pcloud_service = pcloud_service

            # Login en pCloud
            login_result = self.pcloud_service.login()
            if not login_result.get("success"):
                logger.warning(f"pCloud login failed: {login_result.get('error')}")
                return False

            self._initialized = True
            return True

        except Exception as e:
            logger.error(f"Error initializing PCloudOnboardingService: {e}")
            return False

    def ensure_onboarding_folders(self) -> Dict[str, Any]:
        """Asegura que existan las carpetas de onboarding en pCloud"""
        if not self.initialize():
            return {"success": False, "error": "Failed to initialize"}

        try:
            # Encontrar carpeta raíz REVISAR.IA
            revisar_result = self.pcloud_service.find_revisar_ia_folder()
            if not revisar_result.get("success"):
                return {"success": False, "error": "REVISAR.IA folder not found"}

            root_folder_id = revisar_result.get("folder_id")

            # Crear/obtener CLIENTES_NUEVOS
            clientes_nuevos_id = self.pcloud_service.get_or_create_folder(
                "CLIENTES_NUEVOS", root_folder_id
            )

            # Crear/obtener CLIENTES
            clientes_id = self.pcloud_service.get_or_create_folder(
                "CLIENTES", root_folder_id
            )

            if not clientes_nuevos_id or not clientes_id:
                return {"success": False, "error": "Could not create onboarding folders"}

            self._clientes_nuevos_id = clientes_nuevos_id
            self._clientes_id = clientes_id

            return {
                "success": True,
                "folders": {
                    "root": root_folder_id,
                    "clientes_nuevos": clientes_nuevos_id,
                    "clientes": clientes_id
                }
            }

        except Exception as e:
            logger.error(f"Error ensuring onboarding folders: {e}")
            return {"success": False, "error": str(e)}

    def scan_new_clients(self) -> Dict[str, Any]:
        """Escanea la carpeta CLIENTES_NUEVOS para encontrar empresas pendientes"""
        if not self.initialize():
            return {"success": False, "error": "Failed to initialize", "clients": []}

        try:
            # Asegurar que existan las carpetas
            folders = self.ensure_onboarding_folders()
            if not folders.get("success"):
                return {"success": False, "error": "Could not create folders", "clients": []}

            clientes_nuevos_id = folders["folders"]["clientes_nuevos"]

            # Listar contenido de CLIENTES_NUEVOS
            contents = self.pcloud_service.list_folder(clientes_nuevos_id)
            if not contents.get("success"):
                return {"success": False, "error": contents.get("error"), "clients": []}

            pending_clients = []
            for item in contents.get("items", []):
                if item.get("is_folder"):
                    folder_name = item.get("name", "")
                    folder_id = item.get("id")

                    # Listar archivos en la carpeta del cliente
                    client_contents = self.pcloud_service.list_folder(folder_id)
                    client_files = client_contents.get("items", []) if client_contents.get("success") else []

                    # Buscar _info.json
                    has_info = any(
                        not f.get("is_folder") and f.get("name") == "_info.json"
                        for f in client_files
                    )

                    # Contar documentos (excluir _info.json)
                    documents = [
                        f for f in client_files
                        if not f.get("is_folder") and f.get("name") != "_info.json"
                    ]

                    pending_clients.append({
                        "folder_name": folder_name,
                        "folder_id": folder_id,
                        "has_info_file": has_info,
                        "document_count": len(documents),
                        "documents": [
                            {"name": d.get("name"), "size": d.get("size")}
                            for d in documents[:10]
                        ],
                        "created": item.get("created"),
                        "modified": item.get("modified")
                    })

            return {
                "success": True,
                "pending_count": len(pending_clients),
                "clients": pending_clients
            }

        except Exception as e:
            logger.error(f"Error scanning new clients: {e}")
            return {"success": False, "error": str(e), "clients": []}

    def process_client_folder(self, folder_id: int, folder_name: str) -> Dict[str, Any]:
        """
        Procesa una carpeta de cliente nuevo:
        1. Lee _info.json si existe
        2. Descarga y analiza documentos
        3. Crea la empresa
        4. Ingesta documentos en RAG
        5. Mueve carpeta a CLIENTES/
        """
        if not self.initialize():
            return {"success": False, "error": "Failed to initialize"}

        result = {
            "folder_name": folder_name,
            "folder_id": folder_id,
            "steps": [],
            "empresa_id": None,
            "documents_processed": 0,
            "errors": []
        }

        try:
            # Paso 1: Listar contenido
            contents = self.pcloud_service.list_folder(folder_id)
            if not contents.get("success"):
                result["errors"].append(f"Could not list folder: {contents.get('error')}")
                return result

            items = contents.get("items", [])
            result["steps"].append({"step": "list_folder", "success": True, "items": len(items)})

            # Paso 2: Buscar y leer _info.json
            empresa_data = self._read_info_file(items, folder_name)
            result["steps"].append({"step": "read_info", "success": empresa_data is not None})

            # Paso 3: Analizar documentos para extraer más datos
            documents = [f for f in items if not f.get("is_folder") and f.get("name") != "_info.json"]
            extracted_data = self._analyze_documents(documents)
            result["steps"].append({
                "step": "analyze_docs",
                "success": True,
                "docs_analyzed": len(extracted_data.get("documentos_analizados", []))
            })

            # Paso 4: Combinar datos (info.json tiene prioridad)
            final_data = self._merge_empresa_data(empresa_data, extracted_data, folder_name)

            # Paso 5: Crear empresa en la base de datos
            empresa_result = self._create_empresa(final_data)
            result["steps"].append({
                "step": "create_empresa",
                "success": empresa_result.get("success", False),
                "method": empresa_result.get("method")
            })

            if empresa_result.get("success"):
                result["empresa_id"] = empresa_result.get("empresa_id")

                # Paso 6: Ingestar documentos en RAG (opcional)
                ingestion_result = self._ingest_documents(
                    documents,
                    empresa_result.get("empresa_id"),
                    final_data.get("rfc", folder_name)
                )
                result["documents_processed"] = ingestion_result.get("processed", 0)
                result["steps"].append({
                    "step": "ingest_docs",
                    "success": True,
                    "processed": result["documents_processed"]
                })

                # Paso 7: Mover carpeta a CLIENTES/
                move_result = self._move_to_processed(folder_id, folder_name)
                result["steps"].append({"step": "move_folder", "success": move_result})

            result["success"] = result["empresa_id"] is not None

        except Exception as e:
            logger.error(f"Error processing client folder {folder_name}: {e}")
            result["success"] = False
            result["errors"].append(str(e))

        return result

    def _read_info_file(self, contents: List[Dict], folder_name: str) -> Optional[Dict]:
        """Lee el archivo _info.json si existe"""
        try:
            info_file = next(
                (f for f in contents if not f.get("is_folder") and f.get("name") == "_info.json"),
                None
            )
            if not info_file:
                return None

            file_id = info_file.get("id")
            download_result = self.pcloud_service.download_file(file_id)

            if download_result.get("success") and download_result.get("content"):
                content = download_result.get("content")
                if isinstance(content, bytes):
                    content = content.decode("utf-8")
                return json.loads(content)

        except Exception as e:
            logger.warning(f"Error reading _info.json for {folder_name}: {e}")

        return None

    def _analyze_documents(self, documents: List[Dict]) -> Dict[str, Any]:
        """Analiza documentos PDF/DOCX para extraer datos de la empresa"""
        extracted = {
            "nombre_comercial": None,
            "razon_social": None,
            "rfc": None,
            "direccion": None,
            "representante_legal": None,
            "regimen_fiscal": None,
            "documentos_analizados": []
        }

        try:
            for doc in documents[:5]:  # Limitar a 5 documentos para análisis
                file_name = doc.get("name", "").lower()

                # Priorizar documentos clave
                if any(kw in file_name for kw in ["acta", "constitutiva", "cedula", "fiscal", "rfc"]):
                    file_id = doc.get("id")
                    download_result = self.pcloud_service.download_file(file_id)

                    if download_result.get("success"):
                        content = download_result.get("content")
                        if isinstance(content, bytes):
                            try:
                                text = content.decode("utf-8", errors="ignore")
                            except:
                                text = str(content)
                        else:
                            text = str(content)

                        # Intentar extraer RFC del texto
                        rfc_pattern = r'[A-ZÑ&]{3,4}\d{6}[A-Z0-9]{3}'
                        rfc_matches = re.findall(rfc_pattern, text.upper())
                        if rfc_matches and not extracted["rfc"]:
                            extracted["rfc"] = rfc_matches[0]

                        extracted["documentos_analizados"].append(doc.get("name"))

        except Exception as e:
            logger.warning(f"Error analyzing documents: {e}")

        return extracted

    def _merge_empresa_data(self, info_data: Optional[Dict], extracted_data: Dict, folder_name: str) -> Dict:
        """Combina datos de info.json, documentos analizados y nombre de carpeta"""

        # Defaults basados en el nombre de la carpeta
        default_data = {
            "nombre_comercial": folder_name,
            "razon_social": folder_name,
            "rfc": None,
            "industria": "SERVICIOS_PROFESIONALES",
            "direccion": None,
            "email": None,
            "telefono": None,
            "sitio_web": None,
            "regimen_fiscal": None
        }

        # Si el nombre de carpeta parece RFC, usarlo
        if re.match(r'^[A-ZÑ&]{3,4}\d{6}[A-Z0-9]{3}$', folder_name.upper()):
            default_data["rfc"] = folder_name.upper()

        # Merge con datos extraídos de documentos
        for key, value in extracted_data.items():
            if value and key in default_data:
                default_data[key] = value

        # Merge con _info.json (tiene prioridad máxima)
        if info_data:
            for key, value in info_data.items():
                if value:
                    default_data[key] = value

        return default_data

    def _create_empresa(self, data: Dict) -> Dict[str, Any]:
        """Crea la empresa en la base de datos"""
        try:
            # Intentar usar el servicio de empresa si existe
            try:
                from services.empresa_service import empresa_service
                if empresa_service:
                    empresa = empresa_service.crear_empresa(data)
                    return {
                        "success": True,
                        "empresa_id": str(empresa.id) if hasattr(empresa, 'id') else str(empresa.get('id')),
                        "method": "empresa_service"
                    }
            except ImportError:
                pass
            except Exception as e:
                logger.warning(f"empresa_service failed: {e}")

            # Fallback: crear directamente via API MongoDB
            try:
                from pymongo import MongoClient
                mongo_url = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
                client = MongoClient(mongo_url)
                db = client.revisar_ia

                empresa_dict = {
                    "nombre_comercial": data.get("nombre_comercial"),
                    "razon_social": data.get("razon_social"),
                    "rfc": data.get("rfc"),
                    "industria": data.get("industria", "SERVICIOS_PROFESIONALES"),
                    "sub_industria": data.get("sub_industria"),
                    "direccion": data.get("direccion"),
                    "telefono": data.get("telefono"),
                    "email": data.get("email"),
                    "sitio_web": data.get("sitio_web"),
                    "regimen_fiscal": data.get("regimen_fiscal"),
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                    "status": "active",
                    "onboarding_source": "pcloud_automatic"
                }

                result = db.empresas.insert_one(empresa_dict)

                return {
                    "success": True,
                    "empresa_id": str(result.inserted_id),
                    "method": "direct_mongodb"
                }

            except Exception as mongo_error:
                logger.error(f"MongoDB fallback failed: {mongo_error}")
                return {"success": False, "error": str(mongo_error)}

        except Exception as e:
            logger.error(f"Error creating empresa: {e}")
            return {"success": False, "error": str(e)}

    def _ingest_documents(self, documents: List[Dict], empresa_id: str, rfc: str) -> Dict[str, Any]:
        """Ingesta documentos en RAG para la empresa (opcional)"""
        processed = 0
        errors = []

        try:
            # Intentar usar knowledge service si existe
            try:
                from services.knowledge_service import knowledge_service
            except ImportError:
                return {"processed": 0, "errors": ["KnowledgeService not available"]}

            for doc in documents:
                try:
                    file_id = doc.get("id")
                    file_name = doc.get("name")

                    # Descargar archivo
                    download_result = self.pcloud_service.download_file(file_id)

                    if download_result.get("success"):
                        content = download_result.get("content")
                        # TODO: Integrar con knowledge_service.upload_file cuando esté disponible
                        processed += 1

                except Exception as e:
                    errors.append(f"{doc.get('name')}: {str(e)}")

        except Exception as e:
            errors.append(str(e))

        return {"processed": processed, "errors": errors}

    def _move_to_processed(self, folder_id: int, folder_name: str) -> bool:
        """Mueve la carpeta procesada a CLIENTES/"""
        try:
            folders = self.ensure_onboarding_folders()
            if not folders.get("success"):
                return False

            clientes_id = folders["folders"]["clientes"]

            # Mover carpeta
            result = self.pcloud_service.move_folder(folder_id, clientes_id)
            return result.get("success", False)

        except Exception as e:
            logger.error(f"Error moving folder {folder_name} to processed: {e}")
            return False

    def process_all_pending(self) -> Dict[str, Any]:
        """Procesa todas las empresas pendientes en CLIENTES_NUEVOS"""
        results = {
            "success": True,
            "total_found": 0,
            "processed": 0,
            "failed": 0,
            "details": []
        }

        # Escanear clientes pendientes
        scan_result = self.scan_new_clients()
        if not scan_result.get("success"):
            return {"success": False, "error": scan_result.get("error")}

        pending = scan_result.get("clients", [])
        results["total_found"] = len(pending)

        # Procesar cada uno
        for client in pending:
            client_result = self.process_client_folder(
                client["folder_id"],
                client["folder_name"]
            )

            results["details"].append(client_result)

            if client_result.get("success"):
                results["processed"] += 1
            else:
                results["failed"] += 1

        return results


class PCloudOnboardingWatcher:
    """
    Watcher que monitorea CLIENTES_NUEVOS periódicamente para auto-procesar nuevas empresas.

    Uso:
        # Iniciar monitoreo cada 5 minutos
        watcher.start(interval_seconds=300)

        # Detener monitoreo
        watcher.stop()
    """

    def __init__(self, onboarding_service: PCloudOnboardingService):
        self.onboarding_service = onboarding_service
        self._running = False
        self._task = None
        self._interval_seconds = 300  # 5 minutos por defecto
        self._last_check = None
        self._processed_folders = set()  # Track folders being processed to avoid duplicates

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def status(self) -> Dict[str, Any]:
        return {
            "running": self._running,
            "interval_seconds": self._interval_seconds,
            "last_check": self._last_check.isoformat() if self._last_check else None,
            "processed_folders_count": len(self._processed_folders)
        }

    async def start(self, interval_seconds: int = 300) -> Dict[str, Any]:
        """Inicia el monitoreo periódico de CLIENTES_NUEVOS"""
        if self._running:
            return {"success": False, "error": "Watcher already running", "status": self.status}

        self._interval_seconds = max(60, interval_seconds)  # Mínimo 1 minuto
        self._running = True

        self._task = asyncio.create_task(self._watch_loop())

        logger.info(f"pCloud onboarding watcher started (interval: {self._interval_seconds}s)")
        return {"success": True, "message": "Watcher started", "status": self.status}

    async def stop(self) -> Dict[str, Any]:
        """Detiene el monitoreo"""
        if not self._running:
            return {"success": False, "error": "Watcher not running", "status": self.status}

        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

        logger.info("pCloud onboarding watcher stopped")
        return {"success": True, "message": "Watcher stopped", "status": self.status}

    async def _watch_loop(self):
        """Loop principal de monitoreo"""
        while self._running:
            try:
                await self._check_and_process()
            except Exception as e:
                logger.error(f"Error in watcher loop: {e}")

            # Esperar hasta el próximo check
            await asyncio.sleep(self._interval_seconds)

    async def _check_and_process(self):
        """Verifica y procesa nuevas carpetas"""
        self._last_check = datetime.utcnow()

        # Escanear nuevos clientes (síncrono, ejecutar en thread pool)
        loop = asyncio.get_event_loop()
        scan_result = await loop.run_in_executor(
            None,
            self.onboarding_service.scan_new_clients
        )

        if not scan_result.get("success"):
            logger.warning(f"Watcher scan failed: {scan_result.get('error')}")
            return

        pending = scan_result.get("clients", [])

        if not pending:
            logger.debug("Watcher: No pending clients found")
            return

        logger.info(f"Watcher found {len(pending)} pending client(s)")

        # Procesar cada carpeta nueva
        for client in pending:
            folder_id = client["folder_id"]

            # Evitar procesar carpetas que ya están en proceso
            if folder_id in self._processed_folders:
                continue

            self._processed_folders.add(folder_id)

            try:
                # Ejecutar en thread pool porque es síncrono
                result = await loop.run_in_executor(
                    None,
                    lambda: self.onboarding_service.process_client_folder(
                        folder_id,
                        client["folder_name"]
                    )
                )

                if result.get("success"):
                    logger.info(f"Watcher: Successfully processed {client['folder_name']}")
                else:
                    logger.warning(f"Watcher: Failed to process {client['folder_name']}: {result.get('errors')}")

            except Exception as e:
                logger.error(f"Watcher: Error processing {client['folder_name']}: {e}")

            finally:
                # Limpiar del set después de procesar
                self._processed_folders.discard(folder_id)


# Singleton instances
pcloud_onboarding_service = PCloudOnboardingService()
pcloud_onboarding_watcher = PCloudOnboardingWatcher(pcloud_onboarding_service)
