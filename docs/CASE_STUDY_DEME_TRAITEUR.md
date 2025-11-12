# Case Study: DéMé Traiteur - Production Workflow Automation

## Project Overview

**Domain**: Catering & Event Management
**Status**: Production (Active Client)
**Deployment**: Render.com (Free Tier Optimized)
**Architecture**: LangGraph Orchestration with Multi-API Integration

## Business Challenge

A catering service business was receiving event inquiries through a web form and manually processing each request across multiple systems:
- Manually creating client records in Notion
- Manually creating service records and linking relationships
- Manually generating quote spreadsheets from templates
- Manually creating calendar events
- Manually sending confirmation emails

This process was time-consuming (15-20 minutes per inquiry), error-prone, and did not scale with business growth.

## Technical Solution

### Architecture

Designed and implemented an end-to-end automation workflow using a modular pack architecture integrated into the Talaria platform. The solution orchestrates five external APIs in a single automated flow triggered by webhook.

**Technology Stack:**
- Backend: FastAPI (async) with LangGraph state machine
- Database: PostgreSQL 15 with pgvector
- Orchestration: LangGraph with checkpoint persistence
- APIs: Notion API, Google Calendar API, Google Drive API, Google Sheets API, Gmail API
- Deployment: Docker container on Render Free Tier

### Workflow Architecture

```
Web Form Submission (Webhook)
          ↓
    Data Validation
          ↓
    Client Handling (Notion)
    ├── Search existing client by email
    └── Create new client if not found
          ↓
    Prestation Creation (Notion)
    ├── Create service record
    ├── Link to client (relation)
    └── Generate service name
          ↓
    Quote Lines (Notion)
    ├── Match selected options to catalog
    ├── Create line items
    └── Link to prestation (relation)
          ↓
    Google Sheet Generation
    ├── Get template from pool
    ├── Rename with client info
    └── Fill with structured data
          ↓
    Calendar Event (Google Calendar)
    ├── Create event with date/time
    ├── Add client details
    └── Link to sheet and Notion
          ↓
    Email Notification (Gmail API)
    ├── Send to business email
    ├── Include all links
    └── Structured summary
```

## Technical Challenges & Solutions

### Challenge 1: Multi-Database Synchronization

**Problem**: Maintaining referential integrity across Notion databases (Clients, Prestations, Quote Lines) with complex many-to-many relationships.

**Solution**: Implemented transactional-style error handling in LangGraph nodes:
- Each node returns success/failure state
- Failed nodes append errors to state tracking list
- Downstream nodes check for upstream errors before proceeding
- State machine allows manual intervention if needed

**Code Pattern:**
```python
class DemeTraiteurState(TypedDict):
    # Data fields
    client_id: str
    prestation_id: str

    # Error tracking
    errors: Annotated[List[str], operator.add]
    current_step: str

async def handle_client(state: DemeTraiteurState) -> DemeTraiteurState:
    try:
        # API call logic
        state["client_id"] = result
        return state
    except Exception as e:
        state["errors"].append(f"Client creation failed: {str(e)}")
        return state
```

### Challenge 2: Google OAuth2 Token Refresh

**Problem**: Google API refresh tokens expire after inactivity, causing workflow failures in production.

**Solution**: Implemented automatic token refresh detection and persistence:
- Detect 401 Unauthorized responses
- Automatically refresh using refresh_token
- Persist new token to environment (Render env vars via API)
- Retry failed request with new token

**Implementation:**
```python
async def _ensure_valid_credentials(self):
    if self.creds and self.creds.expired and self.creds.refresh_token:
        self.creds.refresh(Request())
        # Persist updated token
        await self._persist_token(self.creds)
```

### Challenge 3: Google Drive API Rate Limits

**Problem**: Render Free Tier has limited CPU/memory. Creating Google Sheets copies on-demand hit rate limits and caused cold start delays.

**Solution**: Implemented a template pool system:
- Pre-create 10 Google Sheet copies during deployment
- Store sheet IDs in JSON file (template_pool.json)
- Mark sheets as "available" or "in_use"
- Workflow pulls from pool instead of creating copies
- GitHub Actions cron job replenishes pool every 6 hours

**Pool Structure:**
```json
{
  "available": ["sheet-id-1", "sheet-id-2", ...],
  "in_use": ["sheet-id-10"]
}
```

**Benefits:**
- Reduced execution time from 45s to 8s
- Eliminated Google Drive quota errors
- Improved UX (faster response)

### Challenge 4: Render Free Tier Optimization

**Problem**: Render Free Tier provides only 512MB RAM and no persistent workers.

**Solution**: Implemented dual execution mode with graceful degradation:
- Detect presence of CELERY_BROKER_URL environment variable
- **Celery Mode**: Use distributed task queue for scalability
- **Direct Mode**: Use FastAPI BackgroundTasks for free tier
- No code changes required, automatic detection

**Code:**
```python
CELERY_MODE = bool(os.getenv("CELERY_BROKER_URL", "").strip())

if CELERY_MODE:
    from core import tasks
    task = tasks.execute_pack.delay(pack_id, inputs)
else:
    background_tasks.add_task(execute_pack_direct, pack_id, inputs)
```

### Challenge 5: Structured Logging for Production Debugging

**Problem**: Debugging failures across 8 sequential steps with external API calls.

**Solution**: Implemented structured logging with request context propagation:
- structlog with contextvars for request ID tracking
- All logs tagged with request_id, step name, timestamps
- Errors captured with full context (client email, prestation ID, etc.)
- Render dashboard provides real-time log streaming

**Pattern:**
```python
structlog.contextvars.bind_contextvars(
    request_id=str(uuid.uuid4()),
    pack_id=pack_id,
    client_email=inputs["email"]
)
logger.info("starting workflow", step="process_data")
```

## Technical Achievements

### Code Quality
- **Type Safety**: Full Python type hints with Pydantic schemas
- **Async-First**: All API calls use httpx async client
- **Error Handling**: Comprehensive try-except with state tracking
- **Testing**: Unit tests with mocked external APIs (pytest-asyncio)
- **Documentation**: Docstrings, inline comments, manifest.json metadata

### Integration Complexity
- **5 External APIs**: Notion, Google Calendar, Google Drive, Google Sheets, Gmail
- **OAuth2 Management**: Automatic token refresh with persistence
- **Webhook Security**: Signature verification, rate limiting, CORS handling
- **Data Validation**: Pydantic models ensure type safety

### Performance Optimization
- **Cold Start Mitigation**: Template pool system
- **Memory Efficiency**: Streaming responses, lazy loading
- **Execution Time**: 8-15 seconds for complete workflow
- **Error Recovery**: Automatic retry with exponential backoff

## Production Deployment

### Infrastructure
- **Hosting**: Render.com Web Service (Free Tier)
- **Database**: PostgreSQL 15 with pgvector extension
- **Container**: Docker multi-stage build (Alpine Linux)
- **Environment**: 32 environment variables (API keys, credentials)
- **Monitoring**: Render log streaming, error email alerts

### Deployment Configuration (render.yaml)
```yaml
services:
  - type: web
    name: deme-api
    env: docker
    plan: free
    envVars:
      - key: CELERY_BROKER_URL
        value: ""  # Disabled for free tier
      - key: NOTION_API_TOKEN
        sync: false
      # ... 30 more environment variables
```

### CI/CD
- **GitHub Actions**: Template pool reload cron (every 6 hours)
- **Auto-Deploy**: Push to main triggers Render rebuild
- **Health Checks**: `/api/packs/deme-traiteur/health` endpoint

### Production Metrics
- **Uptime**: 99.5% (Render free tier cold starts)
- **Execution Time**: 8-15 seconds average
- **Error Rate**: <2% (mostly transient API errors)
- **Requests/Day**: 5-15 (catering inquiry volume)

## Business Impact

### Quantitative Results
- **Time Savings**: 15-20 minutes → 8-15 seconds (99% reduction)
- **Error Reduction**: Manual entry errors eliminated
- **Scalability**: System handles 100+ requests/day without changes
- **Cost**: $0/month (free tier deployment)

### Qualitative Benefits
- **Consistency**: All data follows standardized format
- **Auditability**: Complete workflow logging for debugging
- **Customer Experience**: Instant confirmation response
- **Business Agility**: Easy to modify workflow by updating graph nodes

## Technical Lessons Learned

### 1. LangGraph for Complex Workflows
LangGraph's StateGraph pattern proved excellent for multi-step orchestrations:
- **State Persistence**: Automatic checkpointing for resume/retry
- **Type Safety**: TypedDict enforces state schema
- **Visualizability**: Graph can be rendered for documentation
- **Testability**: Individual nodes can be unit tested

### 2. Graceful Degradation
Designing for dual execution modes (Celery vs Direct) enabled:
- Development on free tier without Redis
- Production scaling path without code changes
- Cost optimization for low-traffic scenarios

### 3. External API Integration Best Practices
- Always implement automatic token refresh
- Use exponential backoff for retries
- Cache responses when possible (template pool)
- Comprehensive error logging with context

### 4. Production-Ready Checklist
- Health check endpoints
- Structured logging with request tracing
- Environment-based configuration (no hardcoded secrets)
- Graceful error handling (don't crash on external API failures)
- Documentation (README, architecture diagrams, API docs)

## Code Highlights

### LangGraph State Machine
```python
def build_graph() -> StateGraph:
    workflow = StateGraph(DemeTraiteurState)

    workflow.add_node("process_data", process_data)
    workflow.add_node("handle_client", handle_client)
    workflow.add_node("create_prestation", create_prestation)
    # ... 6 more nodes

    workflow.set_entry_point("process_data")
    workflow.add_edge("process_data", "handle_client")
    # ... sequential edges
    workflow.add_edge("send_email_notification", END)

    return workflow.compile()
```

### Notion Client with Error Handling
```python
async def get_or_create_client(self, client_data: Dict[str, Any]) -> str:
    # Search by email
    results = await self._search_clients(client_data["email"])

    if results:
        return results[0]["id"]

    # Create new client
    response = await self._create_client_record(client_data)
    return response["id"]
```

### Template Pool Management
```python
async def get_template_from_pool(self) -> str:
    with open(self.pool_file, 'r') as f:
        pool = json.load(f)

    if not pool["available"]:
        raise Exception("Template pool exhausted")

    sheet_id = pool["available"].pop(0)
    pool["in_use"].append(sheet_id)

    with open(self.pool_file, 'w') as f:
        json.dump(pool, f, indent=2)

    return sheet_id
```

## Repository Structure

```
app/packs/deme_traiteur/
├── manifest.json                    # Pack metadata & API schema
├── router.py                        # FastAPI webhook endpoint
├── graph_modern.py                  # LangGraph orchestration
├── integrations/
│   ├── notion_client.py            # Notion API wrapper
│   ├── google_calendar_client.py   # Google Calendar API
│   ├── google_sheets_client.py     # Google Sheets + template pool
│   └── email_client.py             # Gmail API for notifications
├── template_pool.json               # Pre-created sheet IDs
└── tests/
    └── test_deme_traiteur_graph.py # Integration tests with mocks
```

## Skills Demonstrated

**Backend Development:**
- FastAPI async architecture
- SQLAlchemy 2.0 async ORM
- Pydantic schemas for validation
- Webhook implementation with security

**AI/ML Orchestration:**
- LangGraph StateGraph patterns
- Multi-step workflow design
- State persistence and checkpointing
- Error handling in distributed systems

**External API Integration:**
- Notion API (database operations, relations)
- Google Calendar API (event creation)
- Google Drive API (file operations, permissions)
- Google Sheets API (data manipulation)
- Gmail API (OAuth2, email sending)

**DevOps & Production:**
- Docker containerization
- Render.com deployment
- Environment-based configuration
- Structured logging (structlog)
- CI/CD with GitHub Actions
- Health checks and monitoring

**Software Engineering:**
- Modular architecture (pack system)
- Comprehensive error handling
- Unit testing with mocks (pytest)
- Type safety (Python type hints)
- Code documentation
- Git workflow

## Conclusion

The DéMé Traiteur pack demonstrates production-ready ML engineering capabilities including:
- Complex multi-API orchestration
- Robust error handling and logging
- Performance optimization for constrained environments
- Deployment and monitoring
- Real-world business problem solving

The system has been running in production since deployment, handling real customer inquiries with minimal intervention. The architecture is extensible and can be adapted to similar workflow automation problems in other domains.

---

**Technical Stack Summary:**
Python 3.11 | FastAPI | LangGraph | PostgreSQL | Notion API | Google Workspace APIs | Docker | Render.com
