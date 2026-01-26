# SATMA/Revisar.ia - Multi-Agent Consulting Project Management System

## Overview
SATMA/Revisar.ia is a multi-agent consulting project management system designed for complete traceability of intangible services. It enhances decision-making with AI-driven insights and ensures compliance for SAT audits. The system includes an Executive Dashboard and specialized AI agents, integrating LLM reasoning, pCloud evidence management, and email attachments to maintain comprehensive audit trails, streamlining project management and improving regulatory adherence. Key features include multi-tenant data isolation, a comprehensive supplier management module, and an AI-powered onboarding assistant.

## User Preferences
- Spanish language interface (es-MX)
- Automatic setup without manual configuration
- Revisar.ia branding
- Demo mode for testing without external credentials

## System Architecture

### Frontend
The frontend is built with React 19 and styled with Tailwind CSS, featuring a premium dark theme, Glassmorphism effects, custom SVG icons, and dynamic animations. Key components include an AI onboarding chatbot, agent workflow visualizations, version history timelines, and detailed views for projects and providers.

#### Modular Chatbot Architecture (Refactored)
The ChatbotArchivo component has been refactored into a modular architecture with custom hooks and reusable components:

**Custom Hooks** (`frontend/src/hooks/`):
- `useChatMessages.js`: Message management (add, update, stream, history)
- `useFileUpload.js`: File validation, analysis, upload to cloud
- `useOnboardingSteps.js`: Step navigation, data collection, validation
- `useChatAPI.js`: Claude API communication, streaming, web search

**Chatbot Components** (`frontend/src/components/chatbot/`):
- `MessageBubble.jsx`: Individual message with agent avatar, suggestions
- `MessageList.jsx`: Scrollable message list with typing indicator
- `TypingIndicator.jsx`: Animated typing dots
- `ChatInput.jsx`: Textarea with attach button, Enter to send
- `FileUploadArea.jsx`: Drag-drop with status icons, AI analysis results
- `ProgressIndicator.jsx`: Step progress sidebar
- `ConfirmationCard.jsx`: Data confirmation modal

**Shared Components** (`frontend/src/components/shared/`):
- `Modal.jsx`: Reusable modal with backdrop, ESC to close
- `ErrorMessage.jsx`: Error alert with retry/dismiss
- `LoadingSpinner.jsx`: Animated spinner

**Constants** (`frontend/src/constants/onboarding.js`):
- AGENTS, ENTITY_TYPES, FILE_STATUS, ONBOARDING_STEPS, SYSTEM_MESSAGES

#### Agent Visualization Components (New)
- `AgentVisualization.jsx`: Canvas-based circular visualization of 10 AI agents with animated connections, click to select, communication simulation
- `DeliberationTimeline.jsx`: Vertical timeline of agent deliberations with color-coded badges, score progress bars, expandable details, field normalization for English/Spanish APIs

### Backend
The backend uses FastAPI, implementing a multi-tenant architecture for data isolation. It provides API routes for projects, dashboards, authentication, company management, RAG templates, versioning, agent deliberations, defense file generation, and streaming. Key services include agent orchestration, deliberation logic, PDF defense file generation, auditor compliance verification, and a robust supplier management system with OCR capabilities.

### Database Consolidation (PostgreSQL)
The system is consolidating from MongoDB to PostgreSQL for core project data:

**New PostgreSQL Tables** (consolidated schema):
- `projects`: Main project data with empresa_id isolation, fase tracking, risk scores
- `deliberations`: Agent opinions and decisions per project/fase
- `agent_interactions`: Chat history and agent interactions
- `project_phases`: 10-phase workflow status (POE phases 0-9)
- `proveedores_scoring`: Supplier verification with EFOS status, scoring metrics

**New Services** (`backend/services/`):
- `project_service.py`: CRUD operations for projects using asyncpg
- `deliberation_pg_service.py`: Deliberation persistence and retrieval
- `database_pg.py`: Connection pool management (asyncpg)

**New API Routes** (`/api/projects/pg/`):
- GET/POST `/api/projects/pg` - List/create projects
- GET/PATCH/DELETE `/api/projects/pg/{id}` - Project operations
- GET/PATCH `/api/projects/pg/{id}/phases/{fase}` - Phase management
- GET/POST `/api/projects/pg/{id}/deliberations` - Deliberation management
- GET `/api/projects/pg/search/{query}` - Search projects
- GET `/api/projects/pg/stats/summary` - Project statistics

**Migration Script**: `backend/scripts/migrate_mongo_to_postgres.py`
- Supports dry-run mode: `python -m scripts.migrate_mongo_to_postgres --dry-run`
- Migrates: projects, deliberations, agent_interactions, durezza_suppliers

### AI Agents
The system leverages 10 specialized AI agents for strategic vision, project management, tax compliance, legal review, financial analysis, provider verification, defense file generation, compliance verification, knowledge base management, and document onboarding.

#### Agent Prompts System (`backend/services/agent_prompts.py`)
Complete prompt system for all 10 agents with:
- **ResponseFormat Enum**: JSON, MARKDOWN, TEXT, STRUCTURED
- **AgentPrompt Dataclass**: system, context_template, output_format, examples, required_sections, response_format
- **Agents with Full Prompts**:
  - A1_RECEPCION: Document reception, classification, data extraction
  - A2_ANALISIS: Fiscal analysis, LISR Art. 27 deducibility, IVA acreditamiento
  - A3_NORMATIVO: Tax regulations (NIF, RMF, LISR, LIVA, CFF)
  - A4_CONTABLE: Accounting verification (NIF A-1 to D-4, journal entries)
  - A5_OPERATIVO: Supplier capabilities, materiality verification
  - A6_FINANCIERO: Cash flow, pricing, ROI, financial impact
  - A7_LEGAL: Contracts, legal clauses, dispute resolution
  - A8_REDTEAM: SAT audit simulation, weakness identification
  - A9_SINTESIS: Final dictamen, score consolidation (80%+ approved)
  - A10_ARCHIVO: Document filing, indexing, NOM-151 compliance
- **Response Validation**: `validate_agent_response()` checks sections, legal references, scores
- **Helper Functions**: `get_agent_required_sections()`, `get_agent_response_format()`, `requires_legal_references()`

### Knowledge Base System
A RAG-powered knowledge base uses specialized chunking strategies for legal documents, jurisprudence, contracts, SAT criteria, and glossaries. It is managed by an interactive chatbot, Bibliotecar.IA, which handles ingestion, semantic search, versioning, alerts, and agent-initiated document requests.

### Knowledge Repository System (Nuevo)
A corporate knowledge repository with file explorer functionality:
- **Database Tables**: knowledge_documents, knowledge_folders, knowledge_versions, knowledge_tags, knowledge_document_tags, knowledge_audit, knowledge_document_text, knowledge_chunks, knowledge_jobs, knowledge_pcloud_refs
- **Services**:
  - `knowledge_service.py`: File explorer operations (browse, upload, delete, search)
  - `ingestion_service.py`: Text extraction from PDF/DOCX/XLSX/TXT with OCR fallback
  - `classification_service.py`: AI-powered classification with fiscal taxonomy, chunking for RAG
  - `embedding_service.py`: OpenAI text-embedding-3-small (1536 dimensions) for vector generation
  - `vector_search_service.py`: Semantic search with pgvector, hybrid search with RRF (Reciprocal Rank Fusion)
- **API Endpoints**: /api/knowledge/browse, /upload, /init, /stats, /search, /query_rag, /hybrid_search, /semantic_search, /vector_status, /ingest, /reindex, /jobs
- **Vector Search**: Uses pgvector extension with HNSW indexing for semantic similarity search, combines with keyword search using RRF for optimal results
- **Frontend**: KnowledgeRepository.jsx with drag-drop upload, folder navigation, search, stats bar
- **Folder Structure**: /empresa, /fiscal, /clientes, /proveedores, /pcloud (with A1-A7 agent subfolders)

### Estado del Acervo (Document Collection Status)
The Estado del Acervo system tracks document lifecycle with versioning, processing status, re-ingestion endpoints, and document statistics.

### Client Management System
The multi-tenant client management system supports client creation, retrieval, updating, and deletion. It includes an admin interface, a Client 360° system with an admin approval workflow, versioned documents with hash detection, agent interaction logs, and AI-generated evolutionary context.

### Agent Scoring Services
Each core agent has a dedicated scoring service to evaluate specific aspects of project compliance and performance.

### Project Flow with Candados
The project follows a phased flow with "candados" (checkpoints) that require specific agent approvals or conditions to be met before proceeding to the next phase, ensuring compliance and quality.

### Intelligent Onboarding System
The ARCHIVO chatbot provides an intelligent onboarding mode for clients and suppliers, featuring document analysis for data extraction, simulated web search for missing data, and a confirmation flow.

### Facturar.IA - SAT Billing Assistant
An AI-powered voice and text billing assistant helps users find correct SAT codes for invoicing, integrates with ElevenLabs for voice chat, analyzes documents for suggestions, and offers deductibility tips.

### RAG Template System
A RAG template system utilizes 42 `.docx` files with placeholders for dynamic data, organized by agent and managed via `manifest.json` files for metadata.

### Databases
MongoDB is used for application data including projects, agent interactions, and deliberation states, supporting multi-tenancy. PostgreSQL manages user authentication, company data, user roles, and client-related data, including historical changes, documents, interactions, and AI-generated evolutionary context.

### Autonomous Agents System
A self-healing agent network, orchestrated by a principal agent, monitors and maintains the platform 24/7, checking database connectivity, API endpoint availability, authentication systems, and critical services.

### Tráfico.IA - Project Monitoring System
An intelligent monitoring system tracks project status and sends automatic alerts via email, with configurable scheduling, various alert types, and priority levels.

### Diseñar.IA - Autonomous UI Design Guardian
An AI-powered design auditor analyzes UI components for consistency and best practices, covering Accessibility (WCAG 2.1), Visual Consistency, Responsive Design, Usability, Visual Performance, and Branding. It uses Anthropic Claude for intelligent code analysis and screenshot interpretation and provides actionable recommendations.

### Defense Files System - Expedientes de Defensa Fiscal
A comprehensive fiscal defense file management system for SAT audit compliance with full traceability. It uses 11 PostgreSQL tables for master files, events, providers, CFDIs, legal foundations, calculations, audit logs, deductions, communications, documents, and retentions. Key features include automatic code generation, entity extractors, hash chain integrity for audit trails, and agent integration for automatic event logging.
- **PDF Export Service**: `defense_file_export_service.py` - Professional PDF generation with ReportLab including:
  - Cover page with project summary and risk classification
  - Executive summary with phase status
  - Taxpayer data section
  - Service description and provider details
  - Legal foundations (CFF Art. 5-A, 69-B, LISR Art. 27)
  - Agent analyses with deliberation history
  - Materiality evidence checklist
  - Risk matrix with compliance pillars
  - Conclusions and final dictamen
  - Integrity chain with SHA-256 hash verification
- **API Endpoint**: GET /api/defense-files/projects/{project_id}/pdf for authenticated PDF downloads
- **Frontend Component**: `DefenseFileDownload.jsx` - Download button with loading state and error handling

### Rate Limiting System
Per-empresa rate limiting based on subscription plans with usage tracking:
- **Plans**: free (50 req/100K tokens), starter (500 req/1M tokens), pro (5K req/10M tokens), enterprise (50K req/100M tokens)
- **Database Tables**: 
  - `usage_tracking`: Daily usage counters (requests_count, tokens_input, tokens_output, chat_requests, rag_queries, document_uploads, costo_estimado_cents)
  - `planes`: Subscription plan definitions with limits and pricing
  - `request_logs`: Request audit trail for debugging
  - `empresas`: Company data with plan_id assignment
- **PostgreSQL Views**: 
  - `v_usage_monthly`: Aggregated monthly usage for billing
  - `v_usage_dashboard`: Real-time usage dashboard data
- **PostgreSQL Function**: `increment_usage()` - Atomic rate limit check and increment
- **Services**: `rate_limiter_service.py` with RateLimiterService class
- **API Endpoints** (`/api/usage/`):
  - GET `/api/usage/dashboard` - Current usage stats
  - GET `/api/usage/monthly` - Historical monthly usage
  - GET `/api/usage/limits` - Current plan limits
  - GET `/api/usage/plans` - Available plans
  - POST `/api/usage/check` - Pre-check rate limits
- **Frontend Component**: `UsageDashboard.jsx` - Visual usage progress bars with plan info

### KB Legal - Sistema de Artículos Legales Indexados
A structured legal knowledge base with 18 critical articles for agent-assisted fiscal analysis, stored in a PostgreSQL table with tags, law references, text norms, interpretations, and agent assignments. It includes legal documents from CFF, LISR, and LIVA, with a tag system used by agents for legal citations.

## External Dependencies
-   **AI Providers**: Replit AI Integrations (Anthropic Claude), OpenAI GPT-4o, and OpenRouter.
-   **Cloud Storage**: pCloud for Defense Files and Evidence Portfolios.
-   **Email Service**: DreamHost @revisar-ia.com.
-   **Project Submission**: Wufoo webhooks.
-   **Voice AI**: ElevenLabs for conversational AI.