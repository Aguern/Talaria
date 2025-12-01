"""
Webhook Handler - Phase 6

FastAPI endpoints for triggering scraping and ETL pipelines via webhooks.

Integrates with changedetection.io to automatically scrape when new products are detected.

Usage:
    Mount this router in your main FastAPI app:

    from app.packs.stridematch.api.webhook_handler import webhook_router
    app.include_router(webhook_router, prefix="/api/stridematch")
"""

from fastapi import APIRouter, BackgroundTasks, HTTPException, Header, Request
from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from datetime import datetime
import subprocess
import os
import hmac
import hashlib
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router
webhook_router = APIRouter(tags=["StrideMatch Webhooks"])


# ============================================================================
# Pydantic Models
# ============================================================================

class WebhookPayload(BaseModel):
    """Payload received from changedetection.io or manual trigger"""

    source: Literal["changedetection", "manual"] = Field(..., description="Webhook source")
    target: Literal["runrepeat", "runningshoeguru", "irun", "alltricks", "all"] = Field(
        ...,
        description="Target scraper to run"
    )
    brand: Optional[str] = Field(None, description="Optional brand filter")
    category: Optional[str] = Field(None, description="Optional category filter")
    run_etl: bool = Field(True, description="Run ETL pipeline after scraping")
    url: Optional[str] = Field(None, description="URL that triggered the webhook (from changedetection)")


class WebhookResponse(BaseModel):
    """Response returned to webhook caller"""

    status: Literal["success", "error"]
    message: str
    job_id: str
    timestamp: str


class JobStatus(BaseModel):
    """Status of a scraping job"""

    job_id: str
    status: Literal["queued", "running", "completed", "failed"]
    target: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error: Optional[str] = None


# ============================================================================
# Job Queue (In-Memory for MVP, use Redis/Celery for production)
# ============================================================================

# Simple in-memory job queue
job_queue = {}


def generate_job_id(target: str) -> str:
    """Generate unique job ID"""
    import uuid
    return f"{target}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}"


# ============================================================================
# Security
# ============================================================================

WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "your-webhook-secret-change-in-production")


def verify_webhook_signature(payload: bytes, signature: str) -> bool:
    """
    Verify webhook signature using HMAC-SHA256.

    Args:
        payload: Raw request body
        signature: Signature from X-Webhook-Signature header

    Returns:
        True if signature is valid
    """
    expected_signature = hmac.new(
        WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(signature, expected_signature)


# ============================================================================
# Background Task Runners
# ============================================================================

def run_scraper_task(job_id: str, target: str, brand: Optional[str], category: Optional[str]):
    """
    Run scraper in background.

    Args:
        job_id: Unique job identifier
        target: Scraper to run (runrepeat, irun, etc.)
        brand: Optional brand filter
        category: Optional category filter
    """
    try:
        job_queue[job_id]["status"] = "running"
        job_queue[job_id]["started_at"] = datetime.utcnow().isoformat()

        logger.info(f"Starting scraper: {target} (job_id: {job_id})")

        # Determine scraper path
        if target in ["runrepeat", "runningshoeguru"]:
            scraper_dir = "/app/packs/stridematch/scraping/scrapy_projects/lab_scraper"
        elif target in ["irun", "alltricks"]:
            scraper_dir = "/app/packs/stridematch/scraping/scrapy_projects/ecommerce_scraper"
        elif target == "all":
            # Run all scrapers sequentially
            run_all_scrapers(job_id)
            return
        else:
            raise ValueError(f"Unknown target: {target}")

        # Build scrapy command
        cmd = ["scrapy", "crawl", target]

        if brand:
            cmd.extend(["-a", f"brand={brand}"])

        if category:
            cmd.extend(["-a", f"category={category}"])

        # Run scraper
        result = subprocess.run(
            cmd,
            cwd=scraper_dir,
            capture_output=True,
            text=True,
            timeout=3600  # 1 hour timeout
        )

        if result.returncode == 0:
            logger.info(f"✅ Scraper {target} completed successfully")
            job_queue[job_id]["status"] = "completed"
        else:
            logger.error(f"❌ Scraper {target} failed: {result.stderr}")
            job_queue[job_id]["status"] = "failed"
            job_queue[job_id]["error"] = result.stderr

        job_queue[job_id]["completed_at"] = datetime.utcnow().isoformat()

    except Exception as e:
        logger.error(f"❌ Scraper task failed: {e}")
        job_queue[job_id]["status"] = "failed"
        job_queue[job_id]["error"] = str(e)
        job_queue[job_id]["completed_at"] = datetime.utcnow().isoformat()


def run_all_scrapers(job_id: str):
    """Run all scrapers sequentially"""
    scrapers = ["runrepeat", "runningshoeguru", "irun", "alltricks"]

    for scraper in scrapers:
        logger.info(f"Running {scraper}...")
        run_scraper_task(f"{job_id}_{scraper}", scraper, None, None)


def run_etl_task(job_id: str):
    """
    Run ETL pipeline in background.

    Args:
        job_id: Unique job identifier
    """
    try:
        job_queue[job_id]["status"] = "running"
        job_queue[job_id]["started_at"] = datetime.utcnow().isoformat()

        logger.info(f"Starting ETL pipeline (job_id: {job_id})")

        # Run ETL pipeline
        result = subprocess.run(
            ["python", "etl_pipeline.py", "--mode", "all"],
            cwd="/app/packs/stridematch/scraping",
            capture_output=True,
            text=True,
            timeout=600  # 10 minutes timeout
        )

        if result.returncode == 0:
            logger.info(f"✅ ETL pipeline completed successfully")
            job_queue[job_id]["status"] = "completed"
        else:
            logger.error(f"❌ ETL pipeline failed: {result.stderr}")
            job_queue[job_id]["status"] = "failed"
            job_queue[job_id]["error"] = result.stderr

        job_queue[job_id]["completed_at"] = datetime.utcnow().isoformat()

    except Exception as e:
        logger.error(f"❌ ETL task failed: {e}")
        job_queue[job_id]["status"] = "failed"
        job_queue[job_id]["error"] = str(e)
        job_queue[job_id]["completed_at"] = datetime.utcnow().isoformat()


# ============================================================================
# Webhook Endpoints
# ============================================================================

@webhook_router.post("/webhook/new-product", response_model=WebhookResponse)
async def webhook_new_product(
    payload: WebhookPayload,
    background_tasks: BackgroundTasks,
    request: Request,
    x_webhook_signature: Optional[str] = Header(None)
):
    """
    Webhook endpoint for triggering scraping when a new product is detected.

    This endpoint is called by changedetection.io when a product page changes.

    **Authentication**: Requires X-Webhook-Signature header with HMAC-SHA256 signature.

    **Payload Example**:
    ```json
    {
      "source": "changedetection",
      "target": "irun",
      "brand": "nike",
      "run_etl": true,
      "url": "https://www.i-run.fr/nike-pegasus-42/"
    }
    ```

    **Response Example**:
    ```json
    {
      "status": "success",
      "message": "Scraping job queued successfully",
      "job_id": "irun_20251103_143022_a3f2b1c4",
      "timestamp": "2025-11-03T14:30:22.123456"
    }
    ```
    """

    # Verify signature (skip if source is manual)
    if payload.source == "changedetection":
        if not x_webhook_signature:
            raise HTTPException(status_code=401, detail="Missing X-Webhook-Signature header")

        body = await request.body()
        if not verify_webhook_signature(body, x_webhook_signature):
            raise HTTPException(status_code=401, detail="Invalid webhook signature")

    # Generate job ID
    job_id = generate_job_id(payload.target)

    # Initialize job status
    job_queue[job_id] = {
        "job_id": job_id,
        "status": "queued",
        "target": payload.target,
        "brand": payload.brand,
        "category": payload.category,
        "started_at": None,
        "completed_at": None,
        "error": None,
    }

    # Queue scraping task
    background_tasks.add_task(
        run_scraper_task,
        job_id,
        payload.target,
        payload.brand,
        payload.category
    )

    # Queue ETL task if requested
    if payload.run_etl:
        etl_job_id = f"{job_id}_etl"
        job_queue[etl_job_id] = {
            "job_id": etl_job_id,
            "status": "queued",
            "target": "etl",
            "started_at": None,
            "completed_at": None,
            "error": None,
        }
        background_tasks.add_task(run_etl_task, etl_job_id)

    logger.info(f"✅ Webhook received: {payload.target} (job_id: {job_id})")

    return WebhookResponse(
        status="success",
        message=f"Scraping job for {payload.target} queued successfully",
        job_id=job_id,
        timestamp=datetime.utcnow().isoformat()
    )


@webhook_router.get("/webhook/jobs/{job_id}", response_model=JobStatus)
async def get_job_status(job_id: str):
    """
    Get status of a scraping job.

    **Parameters**:
    - `job_id`: Job identifier returned by webhook endpoint

    **Response Example**:
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
    """
    if job_id not in job_queue:
        raise HTTPException(status_code=404, detail="Job not found")

    return JobStatus(**job_queue[job_id])


@webhook_router.get("/webhook/jobs", response_model=List[JobStatus])
async def list_jobs(limit: int = 50):
    """
    List recent scraping jobs.

    **Parameters**:
    - `limit`: Maximum number of jobs to return (default: 50)

    **Response**: List of job statuses ordered by most recent first
    """
    # Sort jobs by job_id (which contains timestamp)
    sorted_jobs = sorted(
        job_queue.values(),
        key=lambda x: x["job_id"],
        reverse=True
    )

    return [JobStatus(**job) for job in sorted_jobs[:limit]]


@webhook_router.post("/webhook/test", response_model=WebhookResponse)
async def test_webhook():
    """
    Test endpoint to verify webhook is working.

    Does not trigger any scraping, just returns a success response.
    """
    job_id = generate_job_id("test")

    return WebhookResponse(
        status="success",
        message="Webhook test successful",
        job_id=job_id,
        timestamp=datetime.utcnow().isoformat()
    )


# ============================================================================
# Manual Trigger Endpoints (for development/testing)
# ============================================================================

@webhook_router.post("/trigger/scrape/{target}")
async def manual_trigger_scrape(
    target: Literal["runrepeat", "runningshoeguru", "irun", "alltricks", "all"],
    background_tasks: BackgroundTasks,
    brand: Optional[str] = None,
    category: Optional[str] = None,
    run_etl: bool = True
):
    """
    Manually trigger a scraping job (for development/testing).

    **No authentication required** - use only in development.

    **Parameters**:
    - `target`: Scraper to run
    - `brand`: Optional brand filter
    - `category`: Optional category filter
    - `run_etl`: Run ETL after scraping (default: true)

    **Example**:
    ```
    POST /api/stridematch/trigger/scrape/irun?brand=nike&run_etl=true
    ```
    """
    payload = WebhookPayload(
        source="manual",
        target=target,
        brand=brand,
        category=category,
        run_etl=run_etl
    )

    # Reuse webhook handler
    from fastapi import Request
    request = Request(scope={"type": "http", "method": "POST"})

    return await webhook_new_product(payload, background_tasks, request, None)


@webhook_router.post("/trigger/etl")
async def manual_trigger_etl(background_tasks: BackgroundTasks):
    """
    Manually trigger ETL pipeline (for development/testing).

    **Example**:
    ```
    POST /api/stridematch/trigger/etl
    ```
    """
    job_id = generate_job_id("etl")

    job_queue[job_id] = {
        "job_id": job_id,
        "status": "queued",
        "target": "etl",
        "started_at": None,
        "completed_at": None,
        "error": None,
    }

    background_tasks.add_task(run_etl_task, job_id)

    return WebhookResponse(
        status="success",
        message="ETL job queued successfully",
        job_id=job_id,
        timestamp=datetime.utcnow().isoformat()
    )
