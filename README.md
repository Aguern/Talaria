# Talaria

A modular iPaaS (Integration Platform as a Service) for building and deploying custom workflow automation solutions. Talaria provides a plugin-based architecture where specialized "packs" handle domain-specific business logic while the core system manages authentication, multi-tenancy, orchestration, and execution.

## Overview

Talaria is designed as a flexible automation platform that can adapt to various business domains through its modular pack system. Each pack is self-contained with its own logic, API routes, and configuration, making the platform easily extensible for new use cases.

**Key Features:**
- Plugin architecture with automatic pack discovery via JSON manifests
- Multi-tenant data isolation (tenant-based data segregation)
- Conversational AI workflows with human-in-the-loop support
- LangGraph-based orchestration for complex state machines
- RESTful API with streaming support (Server-Sent Events)
- Async-first architecture (FastAPI + SQLAlchemy async)
- PostgreSQL with pgvector for semantic search capabilities
- Modern web interface built with Next.js 15 and React 19

## Technology Stack

### Backend
- **Framework**: FastAPI with uvicorn
- **Database**: PostgreSQL 15 with pgvector extension
- **ORM**: SQLAlchemy 2.0 (async mode with asyncpg driver)
- **AI Orchestration**: LangGraph with checkpoint persistence
- **LLM Integration**: OpenAI GPT-4o via langchain-openai
- **Background Tasks**: Celery with Redis (optional, graceful fallback to FastAPI BackgroundTasks)
- **Authentication**: JWT tokens with Argon2 password hashing
- **Logging**: structlog with contextvars for request tracing
- **Vector Search**: sentence-transformers with pgvector storage

### Frontend
- **Framework**: Next.js 15.4 (App Router)
- **UI Library**: React 19.1
- **UI Components**: Radix UI primitives (shadcn/ui)
- **Styling**: TailwindCSS 4
- **State Management**: Zustand + TanStack Query v5
- **Forms**: React Hook Form with Zod validation
- **Type Safety**: TypeScript 5 (strict mode)

### DevOps
- **Containerization**: Docker with multi-stage builds
- **Deployment**: Render.com (configured via render.yaml)
- **CI/CD**: GitHub Actions
- **Environment Management**: pydantic-settings with .env support

## Project Structure

```
/
├── app/                          # Backend Python application
│   ├── core/                     # Core system modules
│   │   ├── auth.py              # JWT authentication & Argon2 hashing
│   │   ├── database.py          # Async SQLAlchemy setup
│   │   ├── models.py            # Database models (Users, Tenants, Documents)
│   │   ├── orchestrator.py      # Pack discovery & execution engine
│   │   ├── engine.py            # ML models & embedding client
│   │   └── logging_config.py    # Structured logging configuration
│   ├── packs/                   # Modular business logic packs
│   │   ├── deme_traiteur/       # Catering workflow automation (production)
│   │   ├── form_3916/           # French tax form processing
│   │   └── bofip/               # French tax code RAG system
│   ├── tools/                   # Reusable AI tools
│   │   ├── document_classifier.py
│   │   ├── document_parser.py
│   │   ├── data_extractor.py
│   │   ├── pdf_filler.py
│   │   └── pdf_generator.py
│   ├── api/                     # API endpoints
│   │   ├── recipes.py           # Pack execution API
│   │   └── chat.py              # Conversational interface
│   ├── tests/                   # Test suite
│   │   ├── core/
│   │   ├── packs/
│   │   └── tools/
│   ├── mcp_server/              # Model Context Protocol server
│   └── main.py                  # FastAPI application entry point
│
├── frontend/                     # Next.js web interface
│   └── src/
│       ├── app/                 # Next.js pages (App Router)
│       ├── components/          # React components
│       │   ├── ui/             # shadcn/ui components
│       │   ├── recipes/        # Pack-related components
│       │   ├── tasks/          # Task status & results
│       │   ├── chat/           # Conversational interface
│       │   └── forms/          # Dynamic form generation
│       └── hooks/              # Custom React hooks
│
├── docker-compose.yml           # Local development orchestration
├── Dockerfile                   # Production container image
├── render.yaml                  # Render deployment configuration
├── requirements.txt             # Python dependencies
└── requirements-render.txt      # Optimized dependencies for deployment
```

## Available Packs

### 1. DéMé Traiteur (Production)
**Domain**: Catering & Event Management
**Status**: Production deployment with real client

End-to-end automation for catering service requests:
- Webhook integration for web form submissions
- Notion database synchronization (Clients, Services, Quote Lines)
- Google Calendar event creation with enriched descriptions
- Google Sheets quote generation with template pooling system
- Email notifications via Gmail API with OAuth2 token refresh
- Dual execution mode (Celery worker or FastAPI BackgroundTasks)

**Integrations**: Notion API, Google Calendar API, Google Drive API, Google Sheets API, Gmail API

### 2. Form 3916 Processor
**Domain**: Tax Document Processing (French fiscal form)

LangGraph workflow with human-in-the-loop for multi-document tax form completion:
- Document classification (ID cards, bank statements, RIB, etc.)
- Multi-page document parsing with PyMuPDF
- Structured data extraction using GPT-4o with Pydantic schemas
- Field consolidation and missing data detection
- Interactive form completion via conversational UI
- PDF generation with ReportLab (multi-page coordinated output)

**Technologies**: LangGraph StateGraph, OpenAI structured outputs, PyMuPDF, ReportLab

### 3. BOFIP RAG System
**Domain**: French Tax Code Knowledge Base

Hybrid retrieval system for question-answering on French tax legislation:
- Full-text search with PostgreSQL tsvector indexes
- Semantic search using pgvector and multilingual embeddings
- Result fusion with Reciprocal Rank Fusion (RRF)
- Re-ranking with CrossEncoder (BAAI/bge-reranker-base)
- GPT-4 answer generation with source citations

**Technologies**: pgvector, sentence-transformers, CrossEncoder, LangChain RAG patterns

## Installation

### Prerequisites
- Python 3.11+
- Node.js 20+
- PostgreSQL 15+ with pgvector extension
- Docker & Docker Compose (for local development)
- Redis (optional, for Celery mode)

### Local Development Setup

1. **Clone the repository**
```bash
git clone <repository-url>
cd Talaria
```

2. **Backend Setup**
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env with your credentials (OpenAI API key, database URL, etc.)
```

3. **Database Setup**
```bash
# Start PostgreSQL with pgvector using Docker
docker-compose up -d db

# Database tables are created automatically on first run
```

4. **Frontend Setup**
```bash
cd frontend
npm install
npm run dev
```

5. **Run the Application**
```bash
# Backend (from root directory)
uvicorn app.main:app --reload --port 8000

# Frontend (already running from step 4)
# Access at http://localhost:3000
```

### Docker Compose (Full Stack)
```bash
# Start all services (API, DB, Redis, Worker, Embedding Service)
docker-compose up -d

# View logs
docker-compose logs -f api

# Stop all services
docker-compose down
```

## Configuration

### Environment Variables

Key environment variables (see `.env.example` for complete list):

```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/talaria

# Authentication
SECRET_KEY=your-secret-key-here
FERNET_KEY=your-fernet-encryption-key

# OpenAI
OPENAI_API_KEY=sk-...

# Celery (optional)
CELERY_BROKER_URL=redis://localhost:6379/0

# Pack-specific variables (Notion, Google APIs, etc.)
```

### Pack Configuration

Each pack includes a `manifest.json` file defining:
- Input/output schemas
- Required API credentials
- Pack metadata (name, description, version)

Packs are automatically discovered at startup by scanning `app/packs/*/manifest.json`.

## Usage

### API Endpoints

**Core Authentication**
- `POST /users` - Create new user account
- `POST /token` - Login and obtain JWT token
- `GET /users/me` - Get current user information

**Pack Execution**
- `GET /api/recipes/` - List available packs
- `POST /api/recipes/{id}/execute` - Execute a pack with file uploads
- `GET /api/recipes/tasks/{task_id}` - Poll task status
- `POST /api/recipes/tasks/{task_id}/human-input` - Submit human-in-the-loop input

**Conversational Interface**
- `POST /api/chat/message` - Send message (Server-Sent Events streaming)
- `GET /api/conversations` - List user conversations
- `POST /api/conversations` - Create new conversation

**Pack-Specific Endpoints**
- `/api/packs/deme-traiteur/webhook` - Webhook for catering form submissions
- `/api/packs/form-3916/*` - Form 3916 processing endpoints
- `/api/packs/bofip/query` - RAG query endpoint for tax code questions

### Example: Execute a Pack

```bash
# Authenticate
curl -X POST http://localhost:8000/token \
  -d "username=user@example.com&password=yourpassword"

# Execute DéMé Traiteur pack
curl -X POST http://localhost:8000/api/recipes/deme_traiteur/execute \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "nom_complet": "Jean Dupont",
    "email": "jean@example.com",
    "telephone": "0612345678",
    "date": "2025-12-25",
    "pax": 30,
    "moment": "Déjeuner",
    "options": ["Entrées", "Plats chauds"]
  }'
```

## Testing

### Backend Tests
```bash
# Run all tests
pytest

# Run specific test module
pytest app/tests/packs/test_form_3916_graph.py

# Run with coverage
pytest --cov=app --cov-report=html
```

### Frontend Tests
```bash
cd frontend

# Run unit tests (Vitest)
npm run test:unit

# Run E2E tests (Playwright)
npm run test:e2e

# Run all tests
npm run test:all
```

## Deployment

### Render.com (Production)

The project includes a `render.yaml` blueprint for one-click deployment:

1. Push code to GitHub
2. Connect repository to Render
3. Configure environment variables in Render dashboard
4. Deploy via Render Blueprint

**Services Created:**
- Web Service: FastAPI API (`deme-api`)
- PostgreSQL Database: 15 with pgvector (`deme-db`)

**Optimization for Render Free Tier:**
- Celery mode disabled (uses FastAPI BackgroundTasks)
- Embedding service disabled if not required
- Template pooling for Google Drive operations to avoid quota limits

### Manual Docker Deployment
```bash
# Build production image
docker build -t talaria-api -f Dockerfile .

# Run with environment file
docker run -d -p 8000:8000 --env-file .env talaria-api
```

## Architecture Patterns

### Plugin System
Packs are discovered automatically via `manifest.json` files. The orchestrator loads pack metadata and routes requests dynamically.

### Human-in-the-Loop
LangGraph workflows can interrupt execution and wait for user input via the conversational interface. State is persisted using LangGraph checkpoints.

### Multi-Tenancy
All data operations are filtered by `tenant_id`. Users belong to tenants, and database queries automatically scope to the current user's tenant.

### Dual Execution Mode
The system detects the presence of `CELERY_BROKER_URL` and switches between:
- **Celery Mode**: Background tasks executed by separate worker processes
- **Direct Mode**: Tasks executed inline using FastAPI BackgroundTasks (suitable for free hosting tiers)

## Model Context Protocol (MCP)

The project includes an MCP server implementation (`app/mcp_server/`) for integration with Claude Desktop. This enables direct access to Talaria packs from the Claude interface.

## License

[Specify your license here]

## Contact

[Your contact information or contribution guidelines]
