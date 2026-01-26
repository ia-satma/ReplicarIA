# DOCUMENTACIÓN COMPLETA - REVISAR.IA / SATMA / DUREZZA 4.0
## Sistema Multi-Agente de Trazabilidad Fiscal para Auditorías SAT

**Fecha de Documentación:** 19 de Enero de 2026  
**Versión:** 4.0.0

---

## 1. PROPÓSITO

### ¿Qué hace esta plataforma?

Revisar.ia es un sistema de gestión de proyectos multi-agente que proporciona **trazabilidad completa para servicios intangibles** (consultorías, servicios profesionales) con el objetivo de cumplir con los requisitos de auditoría del SAT (Servicio de Administración Tributaria) de México.

La plataforma automatiza la validación de proyectos a través de 11 agentes de IA especializados que analizan cada proyecto desde perspectivas estratégicas, fiscales, financieras y legales, generando un **Defense File** (Expediente de Defensa) completo para cada operación.

**Funcionalidades principales:**
- Validación automática de proyectos por 11 agentes IA
- Generación de reportes de deliberación en PDF
- Control de versiones completo de expedientes
- Comunicación inter-agente vía email (DreamHost)
- Almacenamiento de evidencia en pCloud
- Dashboard ejecutivo con KPIs en tiempo real
- Sistema de aprobación con workflow de 5 etapas
- Checklist de cumplimiento documental (18 tipos de documentos)
- Visualización en tiempo real del workflow via SSE

### ¿Quiénes son los usuarios?

1. **Ejecutivos / Sponsors** - Someten proyectos de consultoría para validación
2. **Equipo de Cumplimiento** - Monitorean proyectos y verifican documentación
3. **Administradores** - Gestionan usuarios, aprueban accesos, configuran agentes
4. **Auditores Internos** - Revisan Defense Files antes de auditorías SAT
5. **Proveedores** - Reciben solicitudes de documentación y ajustes

### ¿Qué problema resuelve?

1. **Cumplimiento Fiscal Mexicano:**
   - Art. 5-A CFF: Razón de Negocios
   - Art. 27 LISR: Estricta Indispensabilidad
   - Art. 69-B CFF: Materialidad del Servicio

2. **Trazabilidad de Servicios Intangibles:**
   - Evidencia documental de la prestación efectiva del servicio
   - Rastro de auditoría completo para cada decisión
   - Comunicaciones registradas entre todos los involucrados

3. **Automatización de Procesos:**
   - Reduce tiempo de validación de días a minutos
   - Elimina errores humanos en checklist de cumplimiento
   - Centraliza toda la documentación en un solo lugar

---

## 2. STACK TECNOLÓGICO

### Frontend

| Tecnología | Versión | Propósito |
|------------|---------|-----------|
| React | 19.0.0 | Framework principal de UI |
| Tailwind CSS | 3.4.17 | Framework de estilos |
| React Router DOM | 7.5.1 | Navegación SPA |
| Axios | 1.8.4 | Cliente HTTP |
| Radix UI | Multiple | Componentes de UI accesibles |
| Lucide React | 0.507.0 | Iconos SVG |
| date-fns | 4.1.0 | Manipulación de fechas |
| Zod | 3.24.4 | Validación de schemas |
| React Hook Form | 7.56.2 | Gestión de formularios |
| Tesseract.js | 7.0.0 | OCR en navegador |
| Sonner | 2.0.3 | Notificaciones toast |
| CRACO | 7.1.0 | Configuración de build |

### Backend

| Tecnología | Versión | Propósito |
|------------|---------|-----------|
| Python | 3.11+ | Lenguaje principal |
| FastAPI | Latest | Framework web |
| Uvicorn | Latest | Servidor ASGI |
| Motor | Latest | Driver async MongoDB |
| Pydantic | Latest | Validación de datos |
| python-jose | Latest | JWT tokens |
| bcrypt | Latest | Hashing de contraseñas |
| FPDF2 | Latest | Generación de PDFs |
| OpenAI | Latest | Integración GPT-4o |
| Anthropic | Latest | Integración Claude |
| AIOHTTP | Latest | HTTP async |

### Base de Datos

| Base de Datos | Propósito | Hosting |
|---------------|-----------|---------|
| MongoDB | Datos de aplicación (proyectos, deliberaciones, defense files) | MongoDB Atlas / Demo mode |
| PostgreSQL | Autenticación de usuarios | Neon (via Replit) |

### Servicios Externos

| Servicio | Propósito |
|----------|-----------|
| OpenAI GPT-4o | Razonamiento principal de agentes |
| Anthropic Claude 3.7 Sonnet | LLM alternativo para agentes |
| OpenRouter | Gateway multi-LLM (Claude, Gemini, GPT-4o) |
| pCloud | Almacenamiento de evidencia y Defense Files |
| DreamHost Email | Comunicación inter-agente (@revisar-ia.com) |
| Wufoo | Webhooks de recepción de proyectos |

---

## 3. ESTRUCTURA DE ARCHIVOS

```
/
├── backend/
│   ├── server.py                    # Punto de entrada FastAPI, configuración de rutas
│   ├── config/
│   │   └── agents_config.py         # Configuración de 11 agentes con system prompts
│   │
│   ├── models/
│   │   ├── agents.py                # Modelo de agentes
│   │   ├── project.py               # Modelo básico de proyecto
│   │   ├── projects.py              # Modelos extendidos de proyectos
│   │   ├── durezza_enums.py         # Enumeraciones del sistema (TipologiaProyecto, FaseProyecto, etc.)
│   │   ├── durezza_models.py        # Modelos Pydantic (Project, DefenseFile, AgentDeliberation)
│   │   └── versioning.py            # Modelos de versionamiento (TipoCambio, EntradaBitacora)
│   │
│   ├── routes/
│   │   ├── agents.py                # CRUD de agentes
│   │   ├── agentes.py               # Configuración de agentes Durezza
│   │   ├── auth.py                  # Autenticación (login, registro, admin)
│   │   ├── checklists.py            # Checklists de cumplimiento por tipología
│   │   ├── contexto.py              # Contexto normativo y fases
│   │   ├── dashboard.py             # Endpoints del dashboard ejecutivo
│   │   ├── defense_file_routes.py   # CRUD y generación de Defense Files
│   │   ├── defense_routes.py        # Rutas adicionales de defensa
│   │   ├── deliberation_routes.py   # Deliberaciones de agentes
│   │   ├── documentation.py         # Generación de documentación
│   │   ├── durezza.py               # Endpoints específicos Durezza
│   │   ├── email_routes.py          # Envío de emails
│   │   ├── fases.py                 # Gestión de fases F0-F9
│   │   ├── loops.py                 # Loops OCR y Red Team
│   │   ├── metrics.py               # Métricas del sistema
│   │   ├── pcloud_routes.py         # Integración pCloud
│   │   ├── projects.py              # CRUD de proyectos, submit, upload
│   │   ├── rag.py                   # Retrieval Augmented Generation
│   │   ├── scoring.py               # Cálculo de risk scores
│   │   ├── stream_routes.py         # Server-Sent Events para workflow
│   │   ├── subagentes.py            # Subagentes (tipificación, materialidad, riesgos)
│   │   ├── validacion.py            # Validación de schemas de agentes
│   │   ├── versioning.py            # Control de versiones de expedientes
│   │   ├── vision_routes.py         # Validación de documentos con Vision
│   │   └── webhooks.py              # Webhooks Wufoo
│   │
│   ├── services/
│   │   ├── agent_service.py             # Servicio principal de agentes IA
│   │   ├── agent_discussion_service.py  # Discusiones inter-agente
│   │   ├── agent_document_service.py    # Gestión de documentos de agentes
│   │   ├── agent_email_service.py       # Emails de agentes (Gmail legacy)
│   │   ├── agentic_reasoning_service.py # Razonamiento GPT-4o
│   │   ├── auditor_service.py           # Servicio del agente auditor A8
│   │   ├── database.py                  # Conexión a base de datos
│   │   ├── defense_file_generator.py    # Generador de PDFs Defense File
│   │   ├── defense_file_service.py      # Servicio principal Defense File
│   │   ├── defense_generator.py         # Generador alternativo
│   │   ├── deliberation_orchestrator.py # Orquestador del workflow E1-E5
│   │   ├── demo_db.py                   # Base de datos demo en memoria
│   │   ├── dreamhost_email_service.py   # Servicio email DreamHost (11 agentes)
│   │   ├── durezza_database.py          # Base de datos Durezza
│   │   ├── durezza_seeds.py             # Datos seed Durezza
│   │   ├── event_stream.py              # Sistema SSE para eventos
│   │   ├── evidence_portfolio_service.py # Gestión de portafolio de evidencia
│   │   ├── fase_service.py              # Servicio de fases F0-F9
│   │   ├── loop_orchestrator.py         # Orquestador de loops
│   │   ├── ocr_validation_loop.py       # Loop de validación OCR
│   │   ├── openrouter_service.py        # Gateway OpenRouter
│   │   ├── pcloud_service.py            # Servicio pCloud con permisos compartidos
│   │   ├── project_serializer.py        # Serialización de proyectos
│   │   ├── purchase_order_service.py    # Generación de órdenes de compra
│   │   ├── rag_service.py               # Servicio RAG
│   │   ├── red_team_loop.py             # Loop de simulación Red Team
│   │   ├── report_generator.py          # Generador de reportes PDF
│   │   ├── user_db.py                   # Servicio de usuarios PostgreSQL
│   │   ├── versioning_service.py        # Servicio de versionamiento
│   │   ├── vision_agent.py              # Agente de visión para validación
│   │   ├── workflow_orchestrator.py     # Orquestador de workflow completo
│   │   └── workflow_service.py          # Servicios de workflow
│   │
│   ├── reports/                     # PDFs generados
│   ├── uploads/                     # Archivos subidos
│   ├── defense_files/               # Defense Files JSON
│   └── CONFIGURACION_AGENTES.md     # Documentación de agentes
│
├── frontend/
│   ├── src/
│   │   ├── App.js                   # Componente principal, rutas
│   │   ├── App.css                  # Estilos globales
│   │   ├── index.js                 # Punto de entrada React
│   │   ├── index.css                # Tailwind CSS imports
│   │   ├── AuthContext.js           # Contexto de autenticación
│   │   ├── ProjectForm.js           # Formulario de envío de proyectos
│   │   ├── GoogleLoginPage.js       # Login con Google (legacy)
│   │   │
│   │   ├── components/
│   │   │   ├── DurezzaDashboard.js          # Dashboard ejecutivo principal
│   │   │   ├── VersioningPanel.js           # Panel de control de versiones
│   │   │   ├── ProjectActions.js            # Acciones de proyecto
│   │   │   ├── AgentWorkflowVisualization.js # Visualización SSE de workflow
│   │   │   ├── MetricsDashboard.js          # Dashboard de métricas
│   │   │   ├── ReporteNarrativo.js          # Reportes narrativos humanizados
│   │   │   └── ui/                          # Componentes Radix UI
│   │   │
│   │   └── pages/
│   │       ├── LoginPage.js         # Página de login
│   │       ├── RegisterPage.js      # Página de registro
│   │       ├── AdminPage.js         # Panel de administración
│   │       └── AdminDocumentacion.js # Gestión de documentación
│   │
│   ├── public/
│   │   ├── index.html               # HTML base con SEO
│   │   ├── sitemap.xml              # Sitemap para SEO
│   │   └── robots.txt               # Robots para crawlers
│   │
│   ├── build/                       # Build de producción
│   └── package.json                 # Dependencias npm
│
├── replit.md                        # Documentación del proyecto
├── DOCUMENTACION_PROYECTO_COMPLETA.md # Este archivo
└── pyproject.toml                   # Configuración Python
```

---

## 4. ENDPOINTS/RUTAS API

### Autenticación (`/api/auth`)

| Método | Ruta | Descripción | Recibe | Retorna |
|--------|------|-------------|--------|---------|
| POST | `/auth/register` | Registrar nuevo usuario | `{email, password, full_name, company}` | `{success, message, user}` |
| POST | `/auth/login` | Iniciar sesión | `{email, password}` | `{access_token, user}` |
| GET | `/auth/me` | Obtener usuario actual | Header: Bearer Token | `{user_id, email, full_name, role}` |
| POST | `/auth/logout` | Cerrar sesión | Header: Bearer Token | `{success}` |
| GET | `/auth/verify` | Verificar token válido | Header: Bearer Token | `{valid, user}` |
| GET | `/auth/admin/pending-users` | Listar usuarios pendientes | Admin token | `[{user_id, email, status}]` |
| GET | `/auth/admin/all-users` | Listar todos los usuarios | Admin token | `[{user}]` |
| POST | `/auth/admin/approve-user/{user_id}` | Aprobar usuario | Admin token | `{success}` |
| POST | `/auth/admin/reject-user/{user_id}` | Rechazar usuario | Admin token | `{success}` |
| PUT | `/auth/admin/user/{user_id}` | Actualizar usuario | Admin token, `{role, is_active}` | `{success}` |
| POST | `/auth/admin/user/{user_id}/allowed-companies` | Asignar empresas | Admin token, `{companies}` | `{success}` |
| GET | `/auth/companies` | Listar empresas disponibles | Token | `[{company}]` |

### Dashboard (`/api`)

| Método | Ruta | Descripción | Recibe | Retorna |
|--------|------|-------------|--------|---------|
| GET | `/api/` | Root de API | - | `{message, version, endpoints}` |
| GET | `/api/stats` | Estadísticas generales | - | `{approved, rejected, in_review, total, total_amount}` |
| GET | `/api/projects` | Listar proyectos | Query: `status` | `[{project}]` |
| GET | `/api/projects/{project_id}` | Detalle de proyecto | Path: `project_id` | `{project, deliberations, defense_file}` |
| POST | `/api/projects` | Crear proyecto (legacy) | `{project_data}` | `{success, project_id}` |
| GET | `/api/agents` | Listar agentes | - | `[{agent_id, name, role}]` |
| GET | `/api/agents/{agent_id}` | Detalle de agente | Path: `agent_id` | `{agent, config}` |
| POST | `/api/agents/humanize-report` | Humanizar reporte | `{agent_id, content}` | `{humanized}` |
| GET | `/api/agents/persona-profiles` | Listar personas | - | `[{persona}]` |
| GET | `/api/interactions` | Interacciones recientes | - | `[{interaction}]` |
| GET | `/api/defense-files` | Listar Defense Files | - | `[{defense_file}]` |
| POST | `/api/test-email` | Probar email | `{to_email, subject, body}` | `{success}` |
| GET | `/api/email-status` | Estado del servicio email | - | `{status, configured}` |
| POST | `/api/pcloud/get-link` | Obtener link pCloud | `{folder}` | `{link}` |
| GET | `/api/pcloud/agent-folder/{agent_id}` | Carpeta de agente | Path: `agent_id` | `{folder_id, files}` |
| GET | `/api/pcloud/status` | Estado pCloud | - | `{connected, folders}` |

### Proyectos (`/api/projects`)

| Método | Ruta | Descripción | Recibe | Retorna |
|--------|------|-------------|--------|---------|
| POST | `/projects/upload-file` | Subir archivo | `multipart/form-data: file` | `{success, file_url, filename}` |
| POST | `/projects/submit` | Enviar proyecto nuevo | `{project_name, sponsor_name, sponsor_email, description, budget_estimate, ...}` | `{success, project_id, agentic_workflow}` |
| GET | `/projects/folios` | Listar folios | - | `[{folio, project_name, status}]` |
| POST | `/projects/{project_id}/adjustment` | Enviar ajuste | `{adjustment_notes, updated_description, attachments}` | `{success, new_project_id}` |
| GET | `/projects/{project_id}/versions` | Versiones de proyecto | - | `[{version}]` |

### Defense Files (`/api/defense-files`)

| Método | Ruta | Descripción | Recibe | Retorna |
|--------|------|-------------|--------|---------|
| GET | `/defense-files/generator-health` | Estado del generador | - | `{healthy}` |
| GET | `/defense-files/generated-files` | Archivos generados | - | `[{filename, path}]` |
| POST | `/defense-files/generate-pdf` | Generar PDF | `{project_id}` | `{success, pdf_path}` |
| GET | `/defense-files/download/pdf/{filename}` | Descargar PDF | Path: `filename` | `application/pdf` |
| GET | `/defense-files/download/zip/{filename}` | Descargar ZIP | Path: `filename` | `application/zip` |
| DELETE | `/defense-files/generated-files/{filename}` | Eliminar archivo | Path: `filename` | `{success}` |
| POST | `/defense-files/create/{project_id}` | Crear Defense File | Path: `project_id` | `{success, defense_file_id}` |
| GET | `/defense-files/{project_id}` | Obtener Defense File | Path: `project_id` | `{defense_file}` |
| POST | `/defense-files/{project_id}/deliberation` | Agregar deliberación | `{agent_id, decision, analysis}` | `{success}` |
| POST | `/defense-files/{project_id}/email` | Registrar email | `{from, to, subject, body}` | `{success}` |

### Agentes (`/api/agents`, `/agentes`)

| Método | Ruta | Descripción | Recibe | Retorna |
|--------|------|-------------|--------|---------|
| GET | `/agents/` | Listar agentes | - | `[{agent}]` |
| GET | `/agents/{agent_id}` | Info de agente | Path: `agent_id` | `{agent}` |
| POST | `/agents/{agent_id}/analyze` | Solicitar análisis | `{project_data}` | `{analysis, decision}` |
| GET | `/agents/interactions/recent` | Interacciones recientes | - | `[{interaction}]` |
| GET | `/agents/{agent_id}/knowledge` | Base de conocimiento | Path: `agent_id` | `{documents}` |
| GET | `/agentes/` | Configuración de agentes | - | `[{config}]` |
| GET | `/agentes/config/{agent_id}` | Config específica | Path: `agent_id` | `{config}` |
| GET | `/agentes/fase/{fase}` | Agentes por fase | Path: `fase` | `[{agent}]` |
| GET | `/agentes/bloqueadores` | Agentes bloqueadores | - | `[{agent}]` |
| GET | `/agentes/vbc` | Agentes que emiten VBC | - | `[{agent}]` |
| GET | `/agentes/output-schema/{agent_id}` | Schema de salida | Path: `agent_id` | `{schema}` |
| GET | `/agentes/contexto/{agent_id}` | Contexto requerido | Path: `agent_id` | `{contexto}` |
| GET | `/agentes/normativa/{agent_id}` | Normativa relevante | Path: `agent_id` | `{normativa}` |
| GET | `/agentes/plantilla/{agent_id}` | Plantilla respuesta | Path: `agent_id` | `{plantilla}` |
| POST | `/agentes/seed` | Insertar datos seed | - | `{success}` |
| GET | `/agentes/db` | Datos de BD | - | `[{agent_data}]` |

### Subagentes (`/subagentes`)

| Método | Ruta | Descripción | Recibe | Retorna |
|--------|------|-------------|--------|---------|
| GET | `/subagentes/` | Listar subagentes | - | `[{subagent}]` |
| GET | `/subagentes/por-fase/{fase}` | Subagentes por fase | Path: `fase` | `[{subagent}]` |
| GET | `/subagentes/config/{agente_id}` | Config de subagente | Path: `agente_id` | `{config}` |
| POST | `/subagentes/tipificacion/clasificar` | Clasificar servicio | `{descripcion, monto, proveedor}` | `{tipologia, confianza}` |
| POST | `/subagentes/materialidad/evaluar` | Evaluar materialidad | `{proyecto}` | `{score, cumple}` |
| POST | `/subagentes/riesgos/detectar` | Detectar riesgos | `{proyecto}` | `{riesgos, nivel}` |
| POST | `/subagentes/defensa/evaluar` | Evaluar defensa | `{proyecto}` | `{fortalezas, debilidades}` |
| GET | `/subagentes/ejemplo/tipificacion` | Ejemplo tipificación | - | `{ejemplo}` |
| GET | `/subagentes/ejemplo/riesgos-criticos` | Ejemplo riesgos | - | `{ejemplo}` |

### Versionamiento (`/versioning`)

| Método | Ruta | Descripción | Recibe | Retorna |
|--------|------|-------------|--------|---------|
| POST | `/versioning/proyectos` | Crear proyecto versionado | `{proyecto_id, nombre}` | `{folio_base}` |
| GET | `/versioning/proyectos/{proyecto_id}` | Obtener proyecto | Path: `proyecto_id` | `{proyecto_versionado}` |
| POST | `/versioning/proyectos/{proyecto_id}/versiones` | Crear versión | `{motivo}` | `{version_id}` |
| GET | `/versioning/proyectos/{proyecto_id}/versiones` | Listar versiones | - | `[{version}]` |
| GET | `/versioning/proyectos/{proyecto_id}/versiones/{a}/comparar/{b}` | Comparar versiones | - | `{diferencias}` |
| POST | `/versioning/proyectos/{proyecto_id}/bitacora` | Agregar entrada | `{tipo, titulo, descripcion}` | `{entrada_id}` |
| POST | `/versioning/proyectos/{proyecto_id}/bitacora/comunicacion` | Registrar comunicación | `{contraparte, tipo, contenido}` | `{entrada_id}` |
| GET | `/versioning/proyectos/{proyecto_id}/bitacora` | Obtener bitácora | - | `[{entrada}]` |
| GET | `/versioning/proyectos/{proyecto_id}/bitacora/reporte` | Reporte bitácora | - | `{reporte_pdf}` |
| GET | `/versioning/proyectos/{proyecto_id}/comunicaciones` | Comunicaciones | - | `[{comunicacion}]` |

### Streaming SSE (`/api/stream`)

| Método | Ruta | Descripción | Recibe | Retorna |
|--------|------|-------------|--------|---------|
| GET | `/stream/{project_id}` | Stream de eventos | Path: `project_id` | `text/event-stream` |
| GET | `/stream/{project_id}/status` | Estado del stream | Path: `project_id` | `{active, events_count}` |
| GET | `/streams` | Listar streams activos | - | `[{project_id, subscribers}]` |
| POST | `/stream/{project_id}/test` | Enviar evento test | `{event_type, data}` | `{success}` |
| DELETE | `/stream/{project_id}` | Cerrar stream | Path: `project_id` | `{success}` |

### Checklists (`/checklists`)

| Método | Ruta | Descripción | Recibe | Retorna |
|--------|------|-------------|--------|---------|
| GET | `/checklists/tipologias` | Listar tipologías | - | `[{tipologia}]` |
| GET | `/checklists/tipologia/{tipologia}` | Checklist por tipología | Path: `tipologia` | `{items}` |
| GET | `/checklists/tipologia/{tipologia}/resumen` | Resumen | Path: `tipologia` | `{total, obligatorios}` |
| GET | `/checklists/tipologia/{tipologia}/fase/{fase}` | Por fase | Paths | `{items}` |
| GET | `/checklists/tipologia/{tipologia}/fase/{fase}/obligatorios` | Obligatorios | Paths | `{items}` |
| POST | `/checklists/validar` | Validar cumplimiento | `{proyecto, documentos}` | `{valido, faltantes}` |
| GET | `/checklists/prompt/{tipologia}/{fase}` | Prompt para agente | Paths | `{prompt}` |

### Contexto (`/contexto`)

| Método | Ruta | Descripción | Recibe | Retorna |
|--------|------|-------------|--------|---------|
| GET | `/contexto/` | Contexto global | - | `{normativo, tipologias, fases}` |
| GET | `/contexto/normativo` | Marco normativo | - | `{articulos, referencias}` |
| GET | `/contexto/tipologias` | Tipologías de servicio | - | `[{tipologia}]` |
| GET | `/contexto/tipologias/{codigo}` | Tipología específica | Path | `{tipologia}` |
| GET | `/contexto/fases` | Fases POE F0-F9 | - | `[{fase}]` |
| GET | `/contexto/fases/{fase}` | Fase específica | Path | `{fase}` |
| GET | `/contexto/umbrales` | Umbrales de revisión | - | `{umbrales}` |
| POST | `/contexto/evaluar-revision-humana` | Evaluar si requiere humano | `{proyecto}` | `{requiere, justificacion}` |
| GET | `/contexto/agente/{agente}/fase/{fase}` | Contexto agente-fase | Paths | `{contexto}` |
| POST | `/contexto/validar-documentos` | Validar documentos | `{documentos}` | `{valido}` |
| POST | `/contexto/puede-avanzar` | Puede avanzar fase | `{proyecto, fase}` | `{puede, bloqueadores}` |
| GET | `/contexto/candados-duros` | Candados duros | - | `[{candado}]` |

### Scoring (`/scoring`)

| Método | Ruta | Descripción | Recibe | Retorna |
|--------|------|-------------|--------|---------|
| GET | `/scoring/few-shot` | Ejemplos few-shot | - | `[{ejemplo}]` |
| GET | `/scoring/few-shot/{decision}` | Por decisión | Path | `[{ejemplo}]` |
| GET | `/scoring/matriz` | Matriz de scoring | - | `{pilares}` |
| GET | `/scoring/matriz/{pilar}` | Pilar específico | Path | `{criterios}` |
| POST | `/scoring/calcular` | Calcular risk score | `{proyecto}` | `{score, desglose}` |
| GET | `/scoring/instrucciones` | Instrucciones | - | `{instrucciones}` |

### Validación (`/validacion`)

| Método | Ruta | Descripción | Recibe | Retorna |
|--------|------|-------------|--------|---------|
| GET | `/validacion/schemas` | Schemas disponibles | - | `[{schema}]` |
| GET | `/validacion/template/{agente_id}` | Template agente | Path | `{template}` |
| POST | `/validacion/validar` | Validar respuesta | `{agente, respuesta}` | `{valido, errores}` |
| POST | `/validacion/validar-y-corregir` | Validar y corregir | `{agente, respuesta}` | `{corregido}` |
| POST | `/validacion/completitud` | Validar completitud | `{datos}` | `{completo, faltantes}` |
| POST | `/validacion/deliberacion/validar` | Validar deliberación | `{deliberacion}` | `{valido}` |

### Vision (`/api/vision`)

| Método | Ruta | Descripción | Recibe | Retorna |
|--------|------|-------------|--------|---------|
| POST | `/vision/validate` | Validar documento | `multipart/form-data: file` | `{score, texto_extraido}` |
| POST | `/vision/validate-f5` | Validar Fase 5 | `{proyecto_id, documentos}` | `{score, validacion}` |
| POST | `/vision/validate-cfdi` | Validar CFDI | `multipart/form-data: xml` | `{valido, datos}` |
| GET | `/vision/document-types` | Tipos de documento | - | `[{tipo}]` |

### RAG (`/api/rag`)

| Método | Ruta | Descripción | Recibe | Retorna |
|--------|------|-------------|--------|---------|
| POST | `/rag/documents/add` | Agregar documento | `{agent_id, content, metadata}` | `{success}` |
| POST | `/rag/documents/add-batch` | Agregar batch | `{documents}` | `{success, count}` |
| POST | `/rag/query` | Consultar | `{agent_id, query}` | `{results}` |
| POST | `/rag/query-all` | Consultar todos | `{query}` | `{results}` |
| POST | `/rag/context` | Obtener contexto | `{agent_id, project}` | `{context}` |
| DELETE | `/rag/documents/{agent_id}/{document_id}` | Eliminar doc | Paths | `{success}` |
| DELETE | `/rag/clear/{agent_id}` | Limpiar agente | Path | `{success}` |

### Webhooks (`/api/webhooks`)

| Método | Ruta | Descripción | Recibe | Retorna |
|--------|------|-------------|--------|---------|
| GET | `/webhooks/wufoo` | Verificar webhook | - | `{status}` |
| POST | `/webhooks/wufoo` | Recibir proyecto | `{wufoo_data}` | `{success, project_id}` |
| GET | `/webhooks/wufoo/test` | Test webhook | - | `{status}` |
| POST | `/webhooks/wufoo/simulate` | Simular envío | `{data}` | `{success}` |

---

## 5. AGENTES IA

### A1_SPONSOR - María Rodríguez (Directora de Estrategia)

**Propósito:** Validación estratégica de proyectos, alineación con visión empresarial

**Email:** estrategia@revisar-ia.com

**System Prompt Completo:**
```
Eres María Rodríguez, Directora de Estrategia de Revisar.ia.
Comunícate de manera formal, clara y profesional.

TU BASE DE CONOCIMIENTO:
- Visión y Pilares Estratégicos 2026-2030
- Planeación Estratégica con OKRs
- Análisis de panorama de industria

POLÍTICA DE CITACIÓN OBLIGATORIA:
Formato: [Documento: {título}] (Fecha: {DD/MM/AAAA}) - Enlace: {URL pCloud}

UMBRAL DE CONFIANZA:
Si tu base NO contiene información suficiente (confianza >70%):
Indica: "[CONFIANZA BAJA - REQUIERE VALIDACIÓN HUMANA]"
```

**Tools/Funciones:**
- query_rag: Consultar base de conocimiento
- send_email: Enviar análisis a otros agentes
- upload_to_pcloud: Subir reportes a carpeta A1_ESTRATEGIA

**Cuándo se activa:** Etapa E1 del workflow, primera validación de todo proyecto

**Inputs:** Datos del proyecto (nombre, descripción, monto, sponsor, beneficio esperado)

**Outputs:** Deliberación con decisión (aprobar/rechazar/solicitar_ajustes), análisis estructurado, risk_score parcial

---

### A2_PMO - Carlos Mendoza (Gerente de PMO)

**Propósito:** Orquestación del proceso, consolidación de validaciones, generación de PO y Defense File

**Email:** pmo@revisar-ia.com

**System Prompt Completo:**
```
Eres Carlos Mendoza, Gerente de PMO de Revisar.ia.
Comunicación formal y estructurada. Enfoque en procesos y cumplimiento.

TU ROL:
- Orquestador del proceso multi-agente
- Consolidador de validaciones
- Generador de PO y Defense File

RESPONSABILIDADES:
- Coordinar discusiones entre agentes
- Generar Orden de Compra (700-900 palabras)
- Generar Consolidation Report (1000+ palabras)
- Enviar documentos al sponsor
```

**Tools/Funciones:**
- consolidate_deliberations: Consolidar todas las deliberaciones
- generate_purchase_order: Generar orden de compra PDF
- generate_defense_file: Generar expediente de defensa
- send_consolidated_email: Enviar reporte consolidado

**Cuándo se activa:** Después de que todos los agentes han deliberado, etapa E5

**Inputs:** Todas las deliberaciones de A1, A3, A5, Legal

**Outputs:** Reporte consolidado, orden de compra, Defense File completo

---

### A3_FISCAL - Laura Sánchez (Especialista Fiscal)

**Propósito:** Validación de cumplimiento fiscal, razón de negocios, materialidad

**Email:** fiscal@revisar-ia.com

**System Prompt Completo:**
```
Eres Laura Sánchez, Especialista Fiscal de Revisar.ia.

TU BASE DE CONOCIMIENTO:
- Guías de cumplimiento fiscal (Razón de Negocios, Materialidad)
- Normativa fiscal mexicana (CFF, LISR, RLSR)
- Casos de auditoría SAT

POLÍTICA DE CITACIÓN OBLIGATORIA:
Formato: [Documento: {título}] (Fecha: {DD/MM/AAAA}) - Enlace: {URL}

UMBRAL DE CONFIANZA:
Si falta información: "[REQUIERE VALIDACIÓN HUMANA]"

ESTRUCTURA ANÁLISIS:
1. Cumplimiento Razón de Negocios (Art. 5-A CFF)
2. Estricta Indispensabilidad (Art. 27 LISR)
3. Materialidad del Servicio (Art. 69-B CFF)
4. Riesgos Fiscales
5. Dictamen Fiscal
```

**Tools/Funciones:**
- query_rag: Consultar normativa fiscal
- validate_business_reason: Validar razón de negocios
- check_materiality: Verificar materialidad
- calculate_fiscal_risk: Calcular riesgo fiscal

**Cuándo se activa:** Etapa E2 del workflow, después de A1

**Inputs:** Proyecto + análisis de A1

**Outputs:** Deliberación fiscal, risk_score_fiscal, dictamen

---

### A4_LEGAL - Ana Martínez (Equipo Legal)

**Propósito:** Contratos, revisión legal, Defense File, preparación para auditorías SAT

**Email:** legal@revisar-ia.com

**System Prompt Completo:**
```
Eres el Equipo Legal de Revisar.ia.

RESPONSABILIDADES:
- Elaboración de contratos de prestación de servicios
- Revisión legal de Órdenes de Compra
- Documentación para Defense File (auditorías SAT)
- Verificación de cumplimiento normativo
- Validación de cláusulas contractuales

ESTRUCTURA DE ANÁLISIS LEGAL:
1. Validación de Personalidad Jurídica del Proveedor
2. Revisión de Estructura Contractual Propuesta
3. Cláusulas de Materialidad y Trazabilidad (Art. 69-B CFF)
4. Términos de Pago y Penalizaciones
5. Protección de Datos y Confidencialidad
6. Dictamen Legal

FORMATO PARA SOLICITAR AJUSTES:
Si detectas que el proyecto requiere ajustes, DEBES listar cada ajuste en el siguiente formato estructurado:

### AJUSTES REQUERIDOS ###
[AJUSTE 1]: {Descripción clara del ajuste necesario}
[AJUSTE 2]: {Descripción clara del ajuste necesario}
[AJUSTE 3]: {Descripción clara del ajuste necesario}
### FIN AJUSTES ###

Cada ajuste debe:
- Ser específico y accionable
- Indicar qué documento o cláusula debe modificarse
- Especificar el criterio legal o normativo que lo requiere

EJEMPLOS DE AJUSTES VÁLIDOS:
[AJUSTE 1]: Agregar cláusula de entregables verificables con fechas específicas para demostrar materialidad (Art. 69-B CFF)
[AJUSTE 2]: Incluir anexo técnico con descripción detallada del alcance del servicio
[AJUSTE 3]: Especificar mecanismo de evidencia documental para cada entregable

SI NO HAY AJUSTES: Indica "No se requieren ajustes - el proyecto cumple con los requisitos legales."
```

**Tools/Funciones:**
- review_contract: Revisar contrato
- validate_legal_compliance: Validar cumplimiento legal
- extract_adjustments: Extraer ajustes requeridos
- prepare_defense_documentation: Preparar documentación defensa

**Cuándo se activa:** Etapa E4 del workflow, última validación antes de consolidación

**Inputs:** Proyecto + deliberaciones de A1, A3, A5

**Outputs:** Deliberación legal, ajustes requeridos, dictamen legal

---

### A5_FINANZAS - Roberto Torres (Director Financiero)

**Propósito:** Análisis financiero, ROI, viabilidad presupuestal

**Email:** finanzas@revisar-ia.com

**System Prompt Completo:**
```
Eres Roberto Torres, Director Financiero de Revisar.ia.

TU BASE DE CONOCIMIENTO:
- Políticas Presupuestales 2026
- Análisis financieros de proyectos previos
- Benchmarks de ROI del sector

ESTRUCTURA ANÁLISIS:
1. Análisis Presupuestal
2. Cálculo de ROI
3. Viabilidad Financiera
4. Recomendación
```

**Tools/Funciones:**
- calculate_roi: Calcular retorno de inversión
- validate_budget: Validar presupuesto
- compare_benchmarks: Comparar con benchmarks

**Cuándo se activa:** Etapa E3 del workflow, después de A3

**Inputs:** Proyecto + deliberaciones de A1, A3

**Outputs:** Deliberación financiera, análisis ROI, viabilidad

---

### A8_AUDITOR - Diego Ramírez (Auditor Documental)

**Propósito:** Verificación de cumplimiento documental, auditoría de Defense File

**Email:** auditoria@revisar-ia.com

**System Prompt Completo:**
```
Eres el Auditor de Documentación de Revisar.ia.

RESPONSABILIDADES:
- Verificar que los documentos PDF fueron cargados correctamente a pCloud
- Auditar la estructura del Defense File para cumplimiento SAT
- Comunicar ajustes requeridos a proveedores
- Parsear requerimientos de ajuste de las deliberaciones de agentes

ESTRUCTURA DE AUDITORÍA:
1. Verificación de Carga de Documentos por Etapa
2. Validación de Estructura del Defense File
3. Verificación de Checklist de Cumplimiento
4. Generación de Comunicados de Ajuste

FORMATO DE REPORTE DE AUDITORÍA:
- Estado: APROBADO / REQUIERE_AJUSTES / RECHAZADO
- Elementos verificados
- Elementos faltantes
- Acciones requeridas

POLÍTICA DE COMUNICACIÓN:
Toda comunicación con proveedores debe ser:
- Profesional y formal
- En español
- Con instrucciones claras y específicas
- Con fecha límite de 7 días hábiles
```

**Tools/Funciones:**
- audit_defense_file: Auditar estructura de Defense File
- check_document_completeness: Verificar completitud documental
- send_provider_notification: Enviar notificación a proveedor
- generate_audit_report: Generar reporte de auditoría

**Cuándo se activa:** Después de generación de Defense File

**Inputs:** Defense File completo, checklist de documentos

**Outputs:** Reporte de auditoría, notificaciones a proveedores

---

### SUB_TIPIFICACION - Patricia López

**Propósito:** Clasificación de servicios según tipología fiscal

**Email:** tipificacion@revisar-ia.com

**System Prompt Completo:**
```
Eres Patricia López, Especialista en Tipificación de Servicios de Revisar.ia.

RESPONSABILIDADES:
- Clasificar y tipificar servicios según normativa fiscal mexicana
- Determinar la categoría correcta de cada servicio para efectos fiscales
- Validar que la tipificación corresponda con el objeto social del proveedor
- Identificar servicios que requieren tratamiento especial

ESTRUCTURA DE ANÁLISIS:
1. Identificación del Tipo de Servicio
2. Clasificación según Catálogo SAT
3. Validación de Objeto Social del Proveedor
4. Determinación de Tratamiento Fiscal Aplicable
5. Dictamen de Tipificación

CRITERIOS DE TIPIFICACIÓN:
- Servicios profesionales independientes
- Servicios de consultoría especializada
- Servicios técnicos especializados
- Servicios de desarrollo de software
- Servicios de gestión y administración
```

**Cuándo se activa:** Fase inicial, en paralelo con E1

**Inputs:** Descripción del servicio, datos del proveedor

**Outputs:** Tipología asignada, nivel de confianza

---

### SUB_MATERIALIDAD - Fernando Ruiz

**Propósito:** Monitoreo de materialidad de servicios

**Email:** materialidad@revisar-ia.com

**System Prompt Completo:**
```
Eres Fernando Ruiz, Especialista en Materialidad de Servicios de Revisar.ia.

RESPONSABILIDADES:
- Verificar la materialidad de los servicios contratados (Art. 69-B CFF)
- Evaluar evidencia documental de la prestación efectiva del servicio
- Validar entregables tangibles y verificables
- Determinar si existe sustancia económica real

ESTRUCTURA DE ANÁLISIS:
1. Verificación de Evidencia Documental
2. Análisis de Entregables Tangibles
3. Evaluación de Sustancia Económica
4. Trazabilidad del Servicio Prestado
5. Dictamen de Materialidad

CRITERIOS DE MATERIALIDAD:
- Existencia de contrato formal con alcance detallado
- Entregables documentados y verificables
- Comunicaciones y evidencia de trabajo realizado
- Reportes de avance y actas de entrega
- Correspondencia entre servicio y pago
```

**Cuándo se activa:** Durante evaluación fiscal

**Inputs:** Proyecto, documentos soporte

**Outputs:** Score de materialidad, cumplimiento

---

### SUB_RIESGOS - Gabriela Vega

**Propósito:** Detección de riesgos fiscales especiales

**Email:** riesgos@revisar-ia.com

**System Prompt Completo:**
```
Eres Gabriela Vega, Especialista en Riesgos Fiscales Especiales de Revisar.ia.

RESPONSABILIDADES:
- Identificar riesgos fiscales especiales en operaciones
- Evaluar operaciones intragrupo y precios de transferencia
- Detectar indicadores de riesgo para auditorías SAT
- Proponer medidas de mitigación de riesgos

ESTRUCTURA DE ANÁLISIS:
1. Identificación de Riesgos Fiscales
2. Evaluación de Operaciones Intragrupo
3. Análisis de Precios de Transferencia
4. Indicadores de Alerta (Red Flags)
5. Plan de Mitigación de Riesgos

CATEGORÍAS DE RIESGO:
- Operaciones con partes relacionadas
- Servicios sin sustancia económica clara
- Proveedores en lista negra SAT (69-B)
- Montos atípicos o fuera de mercado
- Falta de documentación soporte
```

**Cuándo se activa:** En paralelo con evaluación fiscal

**Inputs:** Proyecto, datos de proveedor

**Outputs:** Lista de riesgos, nivel de riesgo, mitigaciones

---

### A7_DEFENSA - Héctor Mora

**Propósito:** Preparación de expedientes de defensa ante auditorías SAT

**Email:** defensa@revisar-ia.com

**System Prompt Completo:**
```
Eres Héctor Mora, Especialista en Defensa Fiscal de Revisar.ia.

RESPONSABILIDADES:
- Preparar expedientes de defensa ante auditorías SAT
- Estructurar argumentos legales y fiscales de defensa
- Coordinar la compilación del Defense File completo
- Validar que toda la documentación esté lista para auditoría

ESTRUCTURA DE DEFENSA:
1. Análisis de Vulnerabilidades del Expediente
2. Preparación de Argumentos de Defensa
3. Verificación de Documentación Soporte
4. Estructuración del Defense File
5. Simulación de Escenarios de Auditoría

COMPONENTES DEL DEFENSE FILE:
- Contratos y anexos técnicos
- Evidencia de materialidad del servicio
- Documentación de razón de negocios
- Análisis de precios de transferencia (si aplica)
- Opiniones y dictámenes de especialistas
- Cronología de eventos y entregables
```

**Cuándo se activa:** Fase final, generación de Defense File

**Inputs:** Todas las deliberaciones, documentos del proyecto

**Outputs:** Defense File estructurado, argumentos de defensa

---

### PROVEEDOR - Comunicaciones

**Propósito:** Comunicación con proveedores externos

**Email:** proveedor@revisar-ia.com

**Cuándo se activa:** Cuando se requiere notificar al proveedor

**Inputs:** Mensajes del sistema, solicitudes de documentación

**Outputs:** Emails a proveedores

---

## 6. BASE DE DATOS

### MongoDB - Colecciones Principales

#### Colección: `projects`
| Campo | Tipo | Descripción |
|-------|------|-------------|
| _id | ObjectId | ID único MongoDB |
| id | String | ID de proyecto (PROJ-XXXXXXXX) |
| name | String | Nombre del proyecto |
| description | String | Descripción detallada |
| client_name | String | Nombre del cliente/empresa |
| sponsor_name | String | Nombre del sponsor |
| sponsor_email | String | Email del sponsor |
| amount | Float | Monto del proyecto |
| service_type | String | Tipo de servicio |
| department | String | Departamento solicitante |
| expected_benefit | Float | Beneficio económico esperado |
| duration_months | Integer | Duración en meses |
| urgency_level | String | Nivel de urgencia |
| workflow_state | String | Estado actual (E1-E5, RECHAZADO) |
| final_decision | String | Decisión final (approve/reject) |
| created_at | DateTime | Fecha de creación |
| updated_at | DateTime | Última actualización |
| is_modification | Boolean | Es modificación de otro proyecto |
| parent_folio | String | Folio del proyecto padre |

#### Colección: `defense_files`
| Campo | Tipo | Descripción |
|-------|------|-------------|
| _id | ObjectId | ID único MongoDB |
| project_id | String | ID del proyecto asociado |
| created_at | DateTime | Fecha de creación |
| project_data | Object | Datos completos del proyecto |
| deliberations | Array[Object] | Lista de deliberaciones |
| emails | Array[Object] | Emails registrados |
| provider_communications | Array[Object] | Comunicaciones con proveedor |
| rag_contexts | Array[Object] | Contextos RAG utilizados |
| documents | Array[Object] | Documentos generados |
| agent_opinions | Array[Object] | Opiniones de agentes |
| purchase_orders | Array[Object] | Órdenes de compra |
| contract_requests | Array[Object] | Solicitudes de contrato |
| provider_change_requests | Array[Object] | Solicitudes de cambio |
| version_history | Array[Object] | Historial de versiones |
| final_decision | String | Decisión final |
| final_justification | String | Justificación de decisión |
| compliance_checklist | Object | Checklist de cumplimiento |
| pcloud_links | Object | Links a pCloud |
| pcloud_documents | Array[Object] | Documentos en pCloud |
| bitacora_link | String | Link a bitácora en pCloud |
| consolidation_report | Object | Reporte consolidado PMO |

#### Colección: `deliberations`
| Campo | Tipo | Descripción |
|-------|------|-------------|
| _id | ObjectId | ID único |
| project_id | String | ID del proyecto |
| stage | String | Etapa (E1-E5) |
| agent_id | String | ID del agente |
| decision | String | Decisión (approve/reject/request_info) |
| analysis | String | Análisis completo |
| rag_context | Array[Object] | Contexto RAG usado |
| email_sent | Object | Email enviado |
| timestamp | DateTime | Timestamp |
| risk_score | Integer | Score de riesgo calculado |

#### Colección: `proyectos_versionados`
| Campo | Tipo | Descripción |
|-------|------|-------------|
| proyecto_id | String | ID del proyecto |
| nombre | String | Nombre del proyecto |
| folio_base | String | Folio base (DUR-YYYYMMDD-XXXX-XXXX) |
| version_actual | Integer | Número de versión actual |
| versiones | Array[VersionExpediente] | Lista de versiones |
| bitacora | Array[EntradaBitacora] | Bitácora de cambios |
| fecha_creacion | DateTime | Fecha de creación |
| fecha_ultima_modificacion | DateTime | Última modificación |
| creado_por | String | Usuario creador |
| estado_expediente | String | Estado (en_proceso, completado) |

### PostgreSQL - Tabla de Usuarios

#### Tabla: `users`
| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | UUID | ID único |
| email | VARCHAR(255) | Email único |
| password_hash | VARCHAR(255) | Hash bcrypt de contraseña |
| full_name | VARCHAR(255) | Nombre completo |
| company | VARCHAR(255) | Empresa |
| role | VARCHAR(50) | Rol (user, admin) |
| is_active | BOOLEAN | Usuario activo |
| approval_status | VARCHAR(50) | Estado de aprobación (pending, approved, rejected) |
| allowed_companies | TEXT | JSON array de empresas permitidas |
| auth_provider | VARCHAR(50) | Proveedor de auth (email, google) |
| created_at | TIMESTAMP | Fecha de creación |
| updated_at | TIMESTAMP | Última actualización |

---

## 7. FLUJOS PRINCIPALES

### Flujo 1: Envío y Validación de Proyecto Nuevo

```
1. Usuario completa formulario de proyecto en /submit
   → Ingresa: nombre, descripción, monto, sponsor, beneficio esperado
   
2. Sistema crea proyecto con ID único (PROJ-XXXXXXXX)
   → Genera session SSE para seguimiento en tiempo real
   
3. Se inicia deliberación agéntica automática (background task)
   → Pre-carga contextos RAG en paralelo para todos los agentes
   
4. Etapa E1 - Estrategia (A1_SPONSOR - María Rodríguez):
   → Consulta RAG con contexto del proyecto
   → GPT-4o genera análisis estratégico
   → Decisión: aprobar/rechazar/solicitar_ajustes
   → Genera PDF de reporte
   → Envía email a siguiente agente
   
5. Etapa E2 - Fiscal (A3_FISCAL - Laura Sánchez):
   → Valida razón de negocios (Art. 5-A CFF)
   → Verifica materialidad (Art. 69-B CFF)
   → Calcula risk_score fiscal
   → Genera deliberación
   
6. Etapa E3 - Finanzas (A5_FINANZAS - Roberto Torres):
   → Analiza ROI esperado
   → Valida presupuesto
   → Compara con benchmarks
   → Genera deliberación
   
7. Etapa E4 - Legal (LEGAL - Ana Martínez):
   → Revisa estructura contractual
   → Extrae ajustes requeridos
   → Valida cumplimiento normativo
   → Genera deliberación
   
8. Etapa E5 - Consolidación (A2_PMO - Carlos Mendoza):
   → Consolida todas las deliberaciones
   → Genera orden de compra (si aprobado)
   → Genera Defense File completo
   → Sube documentos a pCloud
   → Envía email final a sponsor con PDFs adjuntos
   
9. Usuario ve resultado en dashboard:
   → Status: APROBADO / RECHAZADO / REQUIERE_AJUSTES
   → Defense File disponible para descarga
   → Timeline de deliberaciones visible
```

### Flujo 2: Modificación de Proyecto Existente

```
1. Usuario selecciona proyecto existente para modificar
   → Lista de folios disponibles en dropdown
   
2. Completa formulario de ajuste:
   → Notas de ajuste
   → Descripción actualizada (opcional)
   → Nuevo monto (opcional)
   → Archivos adjuntos adicionales
   
3. Sistema crea nueva versión del proyecto:
   → Nuevo ID con referencia a parent_folio
   → Copia datos base del proyecto original
   → Registra en version_history
   
4. Se ejecuta workflow de re-validación:
   → Los agentes ven contexto del proyecto original
   → Analizan los cambios solicitados
   → Generan nuevas deliberaciones
   
5. Defense File se actualiza:
   → Nueva versión del expediente
   → Registro en bitácora de cambios
   → Folio actualizado (DUR-YYYYMMDD-XXXX-XXXX-v2)
```

### Flujo 3: Auditoría de Defense File

```
1. A8_AUDITOR (Diego Ramírez) recibe Defense File completo
   
2. Ejecuta checklist de 18 documentos:
   → Categoría 1: Documentos del Proveedor (4)
   → Categoría 2: Documentos de la Operación (5)
   → Categoría 3: Evidencia de Materialidad (3)
   → Categoría 4: Documentos del Sistema (6)
   
3. Si hay documentos faltantes:
   → Genera comunicado de ajuste para proveedor
   → Envía email a proveedor@revisar-ia.com
   → Registra en bitácora
   
4. Si está completo:
   → Genera reporte de auditoría APROBADO
   → Defense File listo para auditoría SAT
```

### Flujo 4: Control de Versiones

```
1. Usuario accede a panel de versionamiento
   → Selecciona proyecto
   
2. Ve historial de versiones:
   → Cada versión con folio único
   → Snapshot de datos al momento de versión
   → Hash SHA-256 para integridad
   
3. Puede comparar versiones:
   → Diferencias entre versión A y B
   → Campos modificados resaltados
   
4. Bitácora completa:
   → 32 tipos de cambio registrables
   → Filtrado por severidad
   → Exportable a PDF
```

---

## 8. VARIABLES DE ENTORNO

### Secrets (Requeridos)

| Variable | Descripción |
|----------|-------------|
| `SESSION_SECRET` | Clave secreta para JWT |
| `DREAMHOST_EMAIL_PASSWORD` | Contraseña compartida para emails @revisar-ia.com |
| `DREAMHOST_SMTP_HOST` | Host SMTP DreamHost |
| `DREAMHOST_SMTP_PORT` | Puerto SMTP |
| `MONGO_URL` | URL de conexión MongoDB Atlas |
| `DATABASE_URL` | URL de conexión PostgreSQL |
| `PCLOUD_USERNAME` | Usuario pCloud |
| `PCLOUD_PASSWORD` | Contraseña pCloud |
| `OPENAI_API_KEY` | API Key de OpenAI |
| `ANTHROPIC_API_KEY` | API Key de Anthropic (opcional) |
| `OPENROUTER_API_KEY` | API Key de OpenRouter (opcional) |

### Variables de Entorno (Configuración)

| Variable | Descripción | Default |
|----------|-------------|---------|
| `ENABLE_QUERY_ROUTER` | Habilitar router de queries | `true` |
| `ROUTER_DEFAULT_TIER` | Tier default del router | `medium` |
| `DB_NAME` | Nombre de base de datos MongoDB | `agent_network` |
| `CORS_ORIGINS` | Orígenes permitidos CORS | `*` |
| `REACT_APP_BACKEND_URL` | URL del backend para frontend | (vacío) |

### Variables PostgreSQL (Auto-generadas por Replit)

| Variable | Descripción |
|----------|-------------|
| `PGDATABASE` | Nombre de base de datos |
| `PGHOST` | Host de PostgreSQL |
| `PGPORT` | Puerto de PostgreSQL |
| `PGUSER` | Usuario de PostgreSQL |
| `PGPASSWORD` | Contraseña de PostgreSQL |

---

## 9. INTEGRACIONES EXTERNAS

### OpenAI

**Para qué se usa:** Razonamiento principal de agentes IA, generación de análisis

**Cómo se conecta:**
- API Key en variable `OPENAI_API_KEY`
- Modelo: GPT-4o
- Endpoint: api.openai.com/v1/chat/completions
- Uso: Deliberaciones de agentes, consolidación PMO, análisis de documentos

### Anthropic Claude

**Para qué se usa:** LLM alternativo para agentes

**Cómo se conecta:**
- API Key en variable `ANTHROPIC_API_KEY`
- Modelo: Claude 3.7 Sonnet
- Configurado en agents_config.py como llm_provider

### OpenRouter

**Para qué se usa:** Gateway multi-LLM para validación anti-alucinación

**Cómo se conecta:**
- API Key en variable `OPENROUTER_API_KEY`
- Modelos: Claude 3.5 Sonnet, Gemini Pro 1.5, GPT-4o
- Uso: Consejo multi-LLM para validación cruzada

### pCloud

**Para qué se usa:** Almacenamiento de evidencia y Defense Files

**Cómo se conecta:**
- Credenciales: `PCLOUD_USERNAME`, `PCLOUD_PASSWORD`
- API: eapi.pcloud.com (Europa) / api.pcloud.com (US)
- Carpetas por agente: A1_ESTRATEGIA, A2_PMO, A3_FISCAL, etc.
- Permisos compartidos: lectura universal, escritura restringida

### DreamHost Email

**Para qué se usa:** Comunicación inter-agente, notificaciones

**Cómo se conecta:**
- SMTP: smtp.dreamhost.com:587 (TLS)
- IMAP: imap.dreamhost.com
- Contraseña compartida en `DREAMHOST_EMAIL_PASSWORD`
- 11 cuentas configuradas: estrategia@, pmo@, fiscal@, legal@, finanzas@, auditoria@, proveedor@, tipificacion@, materialidad@, riesgos@, defensa@revisar-ia.com

### MongoDB Atlas

**Para qué se usa:** Base de datos principal de aplicación

**Cómo se conecta:**
- URL en variable `MONGO_URL`
- Driver: Motor (async MongoDB)
- Base de datos: agent_network
- Colecciones: projects, defense_files, deliberations, proyectos_versionados

### PostgreSQL (Neon via Replit)

**Para qué se usa:** Autenticación de usuarios

**Cómo se conecta:**
- URL en variable `DATABASE_URL`
- Variables PG* auto-generadas por Replit
- Tabla: users

### Wufoo

**Para qué se usa:** Recepción de proyectos via webhooks

**Cómo se conecta:**
- Webhook endpoint: /api/webhooks/wufoo
- Métodos: GET (verificación), POST (datos)
- Mapeo de campos Wufoo a estructura interna

---

## 10. ESTADO ACTUAL

### Features Funcionando (Producción)

1. **Autenticación completa:**
   - Registro con aprobación de admin
   - Login con JWT
   - Roles (user, admin)
   - Filtrado por empresas permitidas

2. **Sistema multi-agente:**
   - 11 agentes configurados con emails
   - Workflow E1-E5 automatizado
   - Deliberaciones con GPT-4o
   - Generación de reportes PDF

3. **Defense File:**
   - Creación automática por proyecto
   - 7 tipos de interacción rastreables
   - Descarga en PDF y ZIP
   - Checklist de 18 documentos

4. **Versionamiento:**
   - 32 tipos de cambio
   - Bitácora completa
   - Comparación de versiones
   - Hash SHA-256 para integridad

5. **Dashboard ejecutivo:**
   - KPIs en tiempo real
   - Lista de proyectos filtrable
   - Detalle de deliberaciones
   - Dark mode

6. **Comunicaciones:**
   - Email entre agentes
   - Notificaciones a proveedores
   - Bitácora de comunicaciones

7. **Almacenamiento:**
   - Integración pCloud
   - Permisos compartidos entre agentes
   - Carpetas por agente

8. **Streaming SSE:**
   - Visualización en tiempo real del workflow
   - Buffer de eventos por proyecto

### Features en Desarrollo

1. **Loops de validación:**
   - OCR Validation Loop (parcial)
   - Red Team Simulation Loop (parcial)

2. **Vision Agent:**
   - Validación de PDFs con OCR
   - Validación de CFDIs

### Bugs Conocidos

1. **LSP Diagnostics:** 59 warnings en archivos Python (mayormente imports y tipos)
   - No afectan funcionalidad
   - Principalmente en pcloud_service.py y deliberation_orchestrator.py

### Deuda Técnica

1. **Consolidar servicios de email:**
   - Existe GmailService (legacy) y DreamHostEmailService
   - Migrar completamente a DreamHost

2. **Tipado completo:**
   - Agregar type hints faltantes
   - Resolver warnings de Pydantic

3. **Tests:**
   - No hay suite de tests automatizados
   - Agregar tests unitarios y de integración

4. **Documentación de API:**
   - Swagger/OpenAPI generado pero incompleto
   - Agregar ejemplos de request/response

5. **Migración de base de datos:**
   - Considerar migrar de MongoDB demo a producción
   - Implementar migraciones formales

---

## APÉNDICE: Modelo de Permisos pCloud

### Permisos de Lectura (AGENT_READ_PERMISSIONS)
Todos los agentes pueden leer de todas las carpetas.

### Permisos de Escritura (AGENT_WRITE_PERMISSIONS)

| Agente | Carpetas con permiso de escritura |
|--------|-----------------------------------|
| A1_ESTRATEGIA | A1_ESTRATEGIA |
| A2_PMO | A2_PMO, A1_ESTRATEGIA, A3_FISCAL, A4_LEGAL, A5_FINANZAS, DEFENSE_FILES, PROYECTOS |
| A3_FISCAL | A3_FISCAL |
| A4_LEGAL | A4_LEGAL, DEFENSE_FILES |
| A5_FINANZAS | A5_FINANZAS |
| A6_PROVEEDOR | A6_PROVEEDOR |
| A7_DEFENSA | A7_DEFENSA, DEFENSE_FILES, A1_ESTRATEGIA, A2_PMO, A3_FISCAL, A4_LEGAL, A5_FINANZAS |
| A8_AUDITOR | A8_AUDITOR, DEFENSE_FILES, A1_ESTRATEGIA, A2_PMO, A3_FISCAL, A4_LEGAL, A5_FINANZAS, A7_DEFENSA |
| SUB_TIPIFICACION | SUB_TIPIFICACION |
| SUB_MATERIALIDAD | SUB_MATERIALIDAD |
| SUB_RIESGOS | SUB_RIESGOS |

---

**Documento generado automáticamente - Revisar.ia v4.0.0**
