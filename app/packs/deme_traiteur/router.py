"""
DéMé Traiteur Pack - Hybrid API Router

Provides webhook endpoint for receiving form submissions from demefontainebleau.com

This router supports two execution modes:
1. Celery mode (when CELERY_BROKER_URL is set): For local dev and full production with workers
2. Direct mode (when CELERY_BROKER_URL is not set): For Render Free deployment without workers
"""

import os
from enum import Enum
from fastapi import APIRouter, BackgroundTasks, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional
import structlog

from .graph_modern import build_graph

log = structlog.get_logger()

# Detect execution mode: Celery (if CELERY_BROKER_URL exists AND not empty) or Direct (FastAPI BackgroundTasks)
CELERY_MODE = bool(os.getenv("CELERY_BROKER_URL", "").strip())

if CELERY_MODE:
    log.info("DéMé Traiteur router: Celery mode enabled (dev/full production)")
    # Import Celery task only if in Celery mode
    try:
        from core.tasks import execute_recipe_task
    except ImportError:
        log.warning("Celery task import failed, falling back to direct mode")
        CELERY_MODE = False
else:
    log.info("DéMé Traiteur router: Direct execution mode enabled (Render Free)")

router = APIRouter(
    prefix="/api/packs/deme-traiteur",
    tags=["DéMé Traiteur"],
    responses={404: {"description": "Not found"}},
)


# Menu options validation
class MenuOption(str, Enum):
    """Valid menu options for the catalogue"""
    ANTIPASTI_FROIDS = "Antipasti froids (burrata, salade, carapaccio, etc.)"
    ANTIPASTI_CHAUDS = "Antipasti chauds (fritures, arancini, crispy mozza, etc.)"
    PIZZA = "Pizza (sur-mesure)"
    PATES = "Pâtes (Truffes, Carbonara, Ragù, etc.)"
    RISOTTO = "Risotto (champignon, fruits de mer, 4 fromages, etc.)"
    DESSERTS = "Desserts (Tiramisù, Panna cotta, crème pistache)"
    PLANCHES = "Planches (charcuterie, fromage)"
    BOISSONS = "Boissons (soft, vin, cocktail)"


# Request/Response schemas
class WebhookRequest(BaseModel):
    """Schema for webhook form submission"""
    nom_complet: str
    email: str
    telephone: Optional[str] = ""
    adresse: Optional[str] = ""
    ville: Optional[str] = ""
    type_client: Optional[str] = "Particulier"
    date: str  # Format: YYYY-MM-DD
    pax: int
    moment: Optional[str] = "Midi"
    options: List[MenuOption] = []
    message: Optional[str] = ""


class WebhookResponse(BaseModel):
    """Response schema for webhook"""
    success: bool
    message: str
    task_id: Optional[str] = None


async def run_workflow_direct(data: dict):
    """
    Execute the workflow directly in background (no Celery).
    Used when CELERY_BROKER_URL is not set (Render Free mode).

    This function runs the entire LangGraph workflow asynchronously in the background.
    The client has already received a response, so we can't communicate errors back.
    Errors are logged for monitoring.
    """
    try:
        log.info("Starting DéMé workflow in direct execution mode",
                client=data.get("nom_complet"),
                email=data.get("email"))

        # Build and execute the graph
        graph = build_graph()

        # Initialize state with form data
        initial_state = {
            "nom_complet": data["nom_complet"],
            "email": data["email"],
            "telephone": data.get("telephone", ""),
            "adresse": data.get("adresse", ""),
            "ville": data.get("ville", ""),
            "type_client": data.get("type_client", "Particulier"),
            "date": data["date"],
            "pax": data["pax"],
            "moment": data.get("moment", "Midi"),
            "nom_prestation": f"{data['nom_complet']} - {data['pax']}",  # Will be set in process_data
            "options": data.get("options", []),
            "message": data.get("message", ""),
            "errors": [],
            "current_step": "init"
        }

        # Execute the workflow
        result = await graph.ainvoke(initial_state)

        log.info("DéMé workflow completed successfully",
                client=data.get("nom_complet"),
                prestation_id=result.get("prestation_id"),
                email_sent=result.get("email_sent", False),
                errors_count=len(result.get("errors", [])))

        if result.get("errors"):
            log.warning("Workflow completed with errors",
                       errors=result.get("errors"),
                       client=data.get("nom_complet"))

    except Exception as e:
        log.error("Error executing DéMé workflow in direct mode",
                 error=str(e),
                 error_type=type(e).__name__,
                 client=data.get("nom_complet"))
        # In direct mode, we can't notify the user of errors since we already responded
        # Errors are logged and should be monitored via Render logs


@router.post("/webhook", response_model=WebhookResponse)
async def webhook_form_submission(
    submission: WebhookRequest,
    background_tasks: BackgroundTasks
):
    """
    Webhook endpoint for receiving form submissions from demefontainebleau.com

    This endpoint supports two execution modes:

    **Celery Mode** (when CELERY_BROKER_URL is set):
    - Creates a Celery task for async processing
    - Returns a task_id for tracking
    - Requires Redis and Celery worker
    - Used in local development and full production deployments

    **Direct Mode** (when CELERY_BROKER_URL is not set):
    - Executes the workflow in background using FastAPI BackgroundTasks
    - No task_id returned (fire-and-forget)
    - No Redis or Celery worker needed
    - Used in Render Free deployment

    In both modes:
    - The endpoint responds immediately (~1-2 seconds)
    - The workflow executes in the background (~30-60 seconds)
    - DéMé receives an email notification when complete

    Note: This endpoint does NOT require authentication as it's a public webhook.
    """
    try:
        data = submission.model_dump()

        log.info("Webhook form submission received",
                email=submission.email,
                date=submission.date,
                pax=submission.pax,
                mode="celery" if CELERY_MODE else "direct")

        if CELERY_MODE:
            # Mode Celery: Create async task via Celery
            task = execute_recipe_task.apply_async(
                args=["deme_traiteur", None, data],
                queue="default"
            )

            log.info("DéMé prestation request queued in Celery",
                    client=submission.nom_complet,
                    task_id=task.id)

            return WebhookResponse(
                success=True,
                message="Demande de prestation enregistrée avec succès. Nous vous recontacterons très prochainement.",
                task_id=task.id
            )
        else:
            # Mode Direct: Execute in background using FastAPI BackgroundTasks
            background_tasks.add_task(run_workflow_direct, data)

            log.info("DéMé prestation request queued in BackgroundTasks",
                    client=submission.nom_complet)

            return WebhookResponse(
                success=True,
                message="Demande de prestation enregistrée avec succès. Nous vous recontacterons très prochainement."
            )

    except Exception as e:
        log.error("Error processing webhook request",
                 error=str(e),
                 error_type=type(e).__name__,
                 email=submission.email if submission else None)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Une erreur est survenue lors du traitement de votre demande. Veuillez réessayer."
        )


@router.get("/admin/pool-status")
async def pool_status():
    """
    Get the current status of the Google Sheets template pool

    Returns pool statistics (available templates, in-use templates, etc.)
    """
    try:
        from .integrations.google_sheets_client import GoogleSheetsClient
        import json
        from pathlib import Path

        # Read pool file directly
        pool_file = Path(__file__).parent / "template_pool.json"
        with open(pool_file, 'r') as f:
            pool = json.load(f)

        return {
            "status": "ok",
            "pool": {
                "available": len(pool.get("available", [])),
                "in_use": len(pool.get("in_use", [])),
                "total": len(pool.get("available", [])) + len(pool.get("in_use", [])),
                "needs_reload": len(pool.get("available", [])) < 5
            },
            "available_ids": pool.get("available", [])[:3]  # Show first 3 IDs
        }

    except Exception as e:
        log.error("Error getting pool status", error=str(e))
        return {
            "status": "error",
            "message": str(e)
        }


@router.post("/admin/reload-pool")
async def reload_pool(secret: str, count: int = 10):
    """
    Reload the template pool by creating new copies

    This endpoint should be called periodically (e.g., via cron) to keep the pool full.

    Args:
        secret: Admin secret key (from env: ADMIN_SECRET or hardcoded for now)
        count: Number of templates to create (default: 10, max: 20)

    Returns:
        Pool reload status and statistics
    """
    # Simple secret validation
    expected_secret = os.getenv("ADMIN_SECRET", "reload_pool_secret_2024")

    if secret != expected_secret:
        log.warning("Unauthorized pool reload attempt")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid secret"
        )

    try:
        from .integrations.google_sheets_client import GoogleSheetsClient

        # Limit count to prevent abuse
        count = min(count, 20)

        log.info(f"Starting pool reload: {count} templates")

        sheets = GoogleSheetsClient()
        result = await sheets.reload_pool(count)

        return {
            "status": "success",
            "result": result
        }

    except Exception as e:
        log.error("Error reloading pool", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reload pool: {str(e)}"
        )


@router.get("/health")
async def health_check():
    """
    Health check endpoint to verify the service is running.
    Also indicates which execution mode is active.
    """
    return {
        "status": "healthy",
        "pack": "deme_traiteur",
        "version": "2.0.0",
        "mode": "celery" if CELERY_MODE else "direct",
        "description": "Celery mode" if CELERY_MODE else "Direct execution (Render Free)"
    }
