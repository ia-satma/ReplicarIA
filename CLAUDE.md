# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ReplicarIA is a multi-agent AI system for traceability of intangible services and specialized consulting in Mexican regulatory context. It implements a 5-stage workflow with 7+ specialized AI agents that collaborate on compliance analysis, fiscal validation, and defense file generation.

## Development Commands

### Quick Start
```bash
./start.sh              # Start everything (Docker DBs + Backend + Frontend)
./start.sh db           # Start databases only (MongoDB, PostgreSQL, Redis)
./start.sh backend      # Start backend only (requires DBs running)
./start.sh frontend     # Start frontend only
./start.sh stop         # Stop all services
./start.sh status       # Show running services
```

### Manual Commands
```bash
# Backend (runs on port 5000)
cd backend
source venv/bin/activate  # or create: python3 -m venv venv
pip install -r requirements.txt
uvicorn server:app --host 0.0.0.0 --port 5000 --reload

# Frontend (runs on port 3000)
cd frontend
npm install --legacy-peer-deps
npm start

# Build frontend for production
cd frontend && npm run build
```

### Testing
```bash
# Backend tests
cd backend
python run_tests.py                    # Run all tests
pytest tests/ -v                       # Verbose output
pytest tests/test_validation.py -v     # Run specific test file
pytest -x                              # Stop on first failure

# Frontend tests
cd frontend && npm test
```

### Docker (databases only)
```bash
docker-compose up -d mongodb postgres redis   # Start databases
docker-compose down                            # Stop databases
```

## Architecture

### Backend (`backend/`)
- **Framework**: FastAPI with async support
- **Databases**: MongoDB (projects/agents), PostgreSQL (auth/users)
- **Entry Point**: `main.py` imports from `server.py`
- **Key Structure**:
  - `routes/` - API endpoints (60+ route files, loaded dynamically with graceful fallback)
  - `services/` - Business logic (100+ service files)
  - `services/agents/` - Specialized agent implementations
  - `middleware/` - Request processing (tenant isolation, candados)
  - `models/` - Pydantic models
  - `kb/` and `kb_legal/` - Knowledge base with Mexican tax law (CFF, LISR, LIVA)

### Frontend (`frontend/`)
- **Framework**: React 19 with CRACO
- **Styling**: TailwindCSS with Radix UI components
- **API Client**: `src/services/api.js` - centralized axios client with interceptors
- **Key Structure**:
  - `src/components/` - UI components
  - `src/pages/` - Route pages
  - `src/context/` - React context (AuthContext)
  - `src/hooks/` - Custom hooks

### Multi-Agent System
Seven specialized agents with unique personalities collaborate on projects:
- **A1-Sponsor**: Strategic validation (GPT-5)
- **A2-PMO**: Document consolidation (Claude Sonnet)
- **A3-Fiscal**: Mexican tax compliance (Claude Sonnet)
- **A5-Finanzas**: Budget verification, 3-Way Match (GPT-5)
- **A4-Legal**: Contract review
- **A6-Proveedor**: Service execution
- **A7-Defensa**: Defense file generation

### 5-Stage Workflow
1. **Intake**: Strategic Initiative Brief (SIB) validation
2. **Formalization**: Vendor selection, PO generation, contracts
3. **Execution**: Service delivery, materiality monitoring
4. **Audit**: Deliverable validation, compliance audit
5. **Close**: 3-Way Match, impact measurement

## Environment Setup

Copy `.env.example` to `.env` and configure:
- `OPENAI_API_KEY` - Required for LLM calls
- `ANTHROPIC_API_KEY` - For Claude-based agents
- `MONGO_URL` - MongoDB connection string
- `DATABASE_URL` - PostgreSQL connection string
- `SECRET_KEY` - JWT signing key
- `ADMIN_EMAIL` / `ADMIN_PASSWORD` - Initial admin user

## API Documentation

- **Swagger UI**: http://localhost:5000/docs
- **Health Check**: GET `/health` or GET `/api/health`
- **Key Endpoints**:
  - `/api/projects` - Project CRUD and stage execution
  - `/api/agents` - Agent info and analysis
  - `/api/defense-files` - Defense file generation
  - `/auth/*` - Authentication (login, register)

## Deployment

- **Backend**: Railway (uses `main.py` as entry point)
- **Frontend**: Vercel (uses `frontend/vercel.json` config)
- Frontend production build served by backend when `frontend/build` exists

## Key Patterns

### Route Loading
Routes in `server.py` are loaded with try/except to gracefully handle missing dependencies:
```python
try:
    from routes import some_route
except ImportError:
    some_route = None

if some_route:
    app.include_router(some_route.router)
```

### Multi-Tenant Isolation
Uses `X-Empresa-ID` header for tenant isolation. TenantContextMiddleware handles context.

### API Client Usage (Frontend)
```javascript
import api from './services/api';

// Auth token and empresa_id are automatically added
const projects = await api.get('/api/projects/');
await api.post('/api/projects/submit', data);
```
