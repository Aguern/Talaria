# Webhook API - Phase 6

FastAPI endpoints for automated scraping triggers via webhooks.

Integrates with **changedetection.io** to automatically scrape when new products are detected on e-commerce sites.

## 🎯 Purpose

The Webhook API allows external services to trigger scraping and ETL pipelines automatically:

1. **changedetection.io** monitors product pages for changes
2. When a change is detected, it sends a webhook to our API
3. Our API triggers the appropriate scraper in the background
4. Optionally runs ETL pipeline to generate enrichment tags
5. Returns job status immediately (non-blocking)

## 🚀 Setup

### 1. Add router to main FastAPI app

Edit `app/main.py`:

```python
from app.packs.stridematch.api.webhook_handler import webhook_router

app = FastAPI(title="SaaS NR")

# Include StrideMatch webhook router
app.include_router(
    webhook_router,
    prefix="/api/stridematch",
    tags=["StrideMatch"]
)
```

### 2. Configure webhook secret

Add to `.env`:

```bash
WEBHOOK_SECRET=your-secure-random-secret-here
```

Generate a secure secret:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 3. Start FastAPI server

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

The webhook endpoints will be available at:
- `http://localhost:8000/api/stridematch/webhook/new-product`

## 📡 Webhook Endpoints

### POST /api/stridematch/webhook/new-product

Trigger a scraping job when a new product is detected.

**Authentication**: Requires `X-Webhook-Signature` header with HMAC-SHA256 signature.

**Request Body**:
```json
{
  "source": "changedetection",
  "target": "irun",
  "brand": "nike",
  "category": null,
  "run_etl": true,
  "url": "https://www.i-run.fr/nike-pegasus-42/"
}
```

**Parameters**:
- `source`: "changedetection" or "manual"
- `target`: Scraper to run:
  - `"runrepeat"`: Lab data from RunRepeat
  - `"runningshoeguru"`: Lab data from RunningShoesGuru
  - `"irun"`: E-commerce data from i-run.fr
  - `"alltricks"`: E-commerce data from alltricks.fr
  - `"all"`: Run all scrapers sequentially
- `brand` (optional): Filter by brand (e.g., "nike")
- `category` (optional): Filter by category (e.g., "road-men")
- `run_etl`: Run ETL pipeline after scraping (default: true)
- `url` (optional): URL that triggered the webhook (for logging)

**Response**:
```json
{
  "status": "success",
  "message": "Scraping job for irun queued successfully",
  "job_id": "irun_20251103_143022_a3f2b1c4",
  "timestamp": "2025-11-03T14:30:22.123456"
}
```

**Example using curl**:
```bash
# Generate signature
PAYLOAD='{"source":"manual","target":"irun","brand":"nike","run_etl":true}'
SIGNATURE=$(echo -n "$PAYLOAD" | openssl dgst -sha256 -hmac "your-webhook-secret" | cut -d' ' -f2)

curl -X POST http://localhost:8000/api/stridematch/webhook/new-product \
  -H "Content-Type: application/json" \
  -H "X-Webhook-Signature: $SIGNATURE" \
  -d "$PAYLOAD"
```

### GET /api/stridematch/webhook/jobs/{job_id}

Get status of a scraping job.

**Response**:
```json
{
  "job_id": "irun_20251103_143022_a3f2b1c4",
  "status": "completed",
  "target": "irun",
  "started_at": "2025-11-03T14:30:22",
  "completed_at": "2025-11-03T14:35:18",
  "error": null
}
```

**Status values**:
- `"queued"`: Job is waiting to start
- `"running"`: Job is currently executing
- `"completed"`: Job finished successfully
- `"failed"`: Job encountered an error

**Example**:
```bash
curl http://localhost:8000/api/stridematch/webhook/jobs/irun_20251103_143022_a3f2b1c4
```

### GET /api/stridematch/webhook/jobs

List recent scraping jobs.

**Parameters**:
- `limit` (optional): Maximum number of jobs to return (default: 50)

**Response**:
```json
[
  {
    "job_id": "irun_20251103_143022_a3f2b1c4",
    "status": "completed",
    "target": "irun",
    "started_at": "2025-11-03T14:30:22",
    "completed_at": "2025-11-03T14:35:18",
    "error": null
  },
  ...
]
```

**Example**:
```bash
curl http://localhost:8000/api/stridematch/webhook/jobs?limit=10
```

### POST /api/stridematch/webhook/test

Test endpoint to verify webhook is working (no scraping triggered).

**Response**:
```json
{
  "status": "success",
  "message": "Webhook test successful",
  "job_id": "test_20251103_143022_a3f2b1c4",
  "timestamp": "2025-11-03T14:30:22.123456"
}
```

## 🛠️ Manual Trigger Endpoints (Development)

These endpoints don't require authentication and are useful for testing.

### POST /api/stridematch/trigger/scrape/{target}

Manually trigger a scraping job.

**Parameters**:
- `target`: Scraper to run (runrepeat, irun, alltricks, all)
- `brand` (query): Optional brand filter
- `category` (query): Optional category filter
- `run_etl` (query): Run ETL after scraping (default: true)

**Example**:
```bash
curl -X POST "http://localhost:8000/api/stridematch/trigger/scrape/irun?brand=nike&run_etl=true"
```

### POST /api/stridematch/trigger/etl

Manually trigger ETL pipeline.

**Example**:
```bash
curl -X POST http://localhost:8000/api/stridematch/trigger/etl
```

## 🔧 Integration with changedetection.io

### 1. Install changedetection.io

```bash
docker run -d --name changedetection -p 5000:5000 \
  -v changedetection-data:/datastore \
  ghcr.io/dgtlmoon/changedetection.io
```

Access at: http://localhost:5000

### 2. Add product page to monitor

1. Go to changedetection.io dashboard
2. Click "Add new watch"
3. Enter product listing URL (e.g., `https://www.i-run.fr/chaussures-running-route-homme/`)
4. Configure change detection:
   - **Filters**: CSS selector for product grid (e.g., `.product-item`)
   - **Check frequency**: Every 6 hours
   - **Trigger text**: "New product" or similar

### 3. Configure webhook notification

In changedetection.io watch settings:

1. Go to "Notifications" tab
2. Select "Webhook" as notification type
3. Configure webhook:
   - **URL**: `http://your-api:8000/api/stridematch/webhook/new-product`
   - **Method**: POST
   - **Headers**:
     ```
     Content-Type: application/json
     X-Webhook-Signature: <computed-signature>
     ```
   - **Body**:
     ```json
     {
       "source": "changedetection",
       "target": "irun",
       "run_etl": true,
       "url": "{{ watch_url }}"
     }
     ```

### 4. Test webhook

1. Trigger manual check in changedetection.io
2. Verify job appears in `/api/stridematch/webhook/jobs`
3. Check job status until completion

## 🔒 Security

### HMAC-SHA256 Signature

Webhooks from changedetection.io must include a valid signature to prevent unauthorized access.

**Signature Generation**:
```python
import hmac
import hashlib

secret = "your-webhook-secret"
payload = '{"source":"changedetection","target":"irun"}'

signature = hmac.new(
    secret.encode(),
    payload.encode(),
    hashlib.sha256
).hexdigest()

# Send in header: X-Webhook-Signature: <signature>
```

**Signature Verification** (automatic in webhook handler):
```python
def verify_webhook_signature(payload: bytes, signature: str) -> bool:
    expected_signature = hmac.new(
        WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(signature, expected_signature)
```

### Best Practices

1. **Keep webhook secret confidential**: Store in `.env`, never commit to Git
2. **Use HTTPS in production**: Encrypt webhook traffic
3. **Rate limiting**: Consider adding rate limits to webhook endpoints
4. **IP allowlist**: Restrict webhook access to known IPs (changedetection.io)
5. **Logging**: Log all webhook calls with source IP and timestamp

## 📊 Job Queue System

### In-Memory Queue (MVP)

Current implementation uses in-memory dictionary for job tracking:
- ✅ Simple, no external dependencies
- ✅ Fast for development
- ❌ Jobs lost on server restart
- ❌ No distributed workers

**Job structure**:
```python
{
  "job_id": "irun_20251103_143022_a3f2b1c4",
  "status": "running",
  "target": "irun",
  "brand": "nike",
  "category": null,
  "started_at": "2025-11-03T14:30:22",
  "completed_at": null,
  "error": null
}
```

### Production Queue (Future Enhancement)

For production, consider using:

**Option 1: Celery + Redis**
```python
from celery import Celery

celery_app = Celery('stridematch', broker='redis://localhost:6379')

@celery_app.task
def run_scraper_task(job_id, target, brand, category):
    # Scraper logic here
    pass
```

**Option 2: RQ (Redis Queue)**
```python
from redis import Redis
from rq import Queue

redis_conn = Redis()
queue = Queue(connection=redis_conn)

job = queue.enqueue(run_scraper_task, job_id, target, brand, category)
```

## 🧪 Testing

### Test webhook endpoint:
```bash
curl -X POST http://localhost:8000/api/stridematch/webhook/test
```

### Trigger test scraping job:
```bash
curl -X POST "http://localhost:8000/api/stridematch/trigger/scrape/irun?brand=nike"
```

### Check job status:
```bash
JOB_ID="irun_20251103_143022_a3f2b1c4"
curl http://localhost:8000/api/stridematch/webhook/jobs/$JOB_ID
```

### List all jobs:
```bash
curl http://localhost:8000/api/stridematch/webhook/jobs
```

## 🐛 Troubleshooting

### Webhook returns 401 Unauthorized
**Problem**: Invalid or missing signature

**Solution**: Verify `WEBHOOK_SECRET` matches in `.env` and changedetection.io

### Job stuck in "running" status
**Problem**: Scraper crashed without updating job status

**Solution**:
1. Check scraper logs
2. Restart server (job will be lost with in-memory queue)
3. Consider implementing timeout mechanism

### Scraper not found error
**Problem**: `scrapy crawl` command fails

**Solution**:
1. Verify scraper paths in `run_scraper_task()`
2. Ensure Scrapy projects are in correct directories
3. Check that spider names match (runrepeat, irun, etc.)

### Database connection error during scraping
**Problem**: Scraper can't connect to PostgreSQL

**Solution**:
1. Ensure PostgreSQL is running: `docker-compose ps`
2. Verify `.env` has correct database credentials
3. Check network connectivity between API and database

## 📝 Example Automation Workflow

### Scenario: Automatically scrape when Nike releases new Pegasus model

1. **Setup changedetection.io**:
   - Monitor: `https://www.i-run.fr/nike-pegasus/`
   - Check frequency: Every 6 hours
   - Trigger: New product added to grid

2. **Configure webhook**:
   ```json
   {
     "source": "changedetection",
     "target": "irun",
     "brand": "nike",
     "run_etl": true,
     "url": "{{ watch_url }}"
   }
   ```

3. **When new product detected**:
   - changedetection.io sends webhook
   - API queues irun scraper with brand filter
   - Scraper extracts product data
   - ETL pipeline generates tags
   - Data available for recommendation engine

4. **Verify in database**:
   ```sql
   SELECT p.model_name, p.created_at, COUNT(t.id) as tags
   FROM stridematch_products p
   LEFT JOIN stridematch_enrichment_tags t ON p.id = t.product_id
   WHERE p.brand_id = (SELECT id FROM stridematch_brands WHERE slug = 'nike')
   ORDER BY p.created_at DESC
   LIMIT 5;
   ```

## 🔄 Next Steps

Phase 6 is the final phase of the Knowledge Core infrastructure! 🎉

**Infrastructure is now complete**:
- ✅ Phase 1: Database schema (PostgreSQL, MongoDB, Neo4j)
- ✅ Phase 2: Size normalization scraper
- ✅ Phase 3: Lab data scrapers (RunRepeat, RunningShoesGuru)
- ✅ Phase 4: E-commerce scrapers (i-run, alltricks)
- ✅ Phase 5: ETL pipeline (normalization + enrichment tags)
- ✅ Phase 6: Webhook API (automation)

**Ready for production MVP**:
- Deploy to cloud (Render, Railway, Fly.io)
- Configure changedetection.io monitors
- Set up automated scraping schedules
- Build recommendation engine on top of enriched data
