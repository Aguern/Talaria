"""
DéMé Traiteur Pack - API Router

Provides webhook endpoint for receiving form submissions from demefontainebleau.com
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional, List
import structlog

from core.orchestrator import get_orchestrator, OrchestratorService

log = structlog.get_logger()

router = APIRouter(
    prefix="/api/packs/deme-traiteur",
    tags=["DéMé Traiteur"],
    responses={404: {"description": "Not found"}},
)


class FormSubmission(BaseModel):
    """Schema for webhook form submission"""
    nom_complet: str
    email: str
    telephone: Optional[str] = None
    adresse: Optional[str] = None
    ville: Optional[str] = None
    type_client: Optional[str] = "Particulier"
    date: str  # Format: YYYY-MM-DD
    pax: int
    moment: Optional[str] = "Déjeuner"
    nom_prestation: Optional[str] = None
    options: Optional[List[str]] = []


class WebhookResponse(BaseModel):
    """Response schema for webhook"""
    success: bool
    task_id: str
    message: str


@router.post("/webhook", response_model=WebhookResponse)
async def webhook_form_submission(
    submission: FormSubmission,
    orchestrator: OrchestratorService = Depends(get_orchestrator)
):
    """
    Webhook endpoint for receiving form submissions from demefontainebleau.com

    This endpoint:
    1. Receives form data as JSON
    2. Validates the data
    3. Launches the deme_traiteur recipe asynchronously
    4. Returns a task_id for tracking

    The client can then poll GET /api/recipes/tasks/{task_id} to track progress.

    Note: This endpoint does NOT require authentication as it's a public webhook.
    If you need authentication, add:
    current_user: CurrentUser = Depends(get_current_active_user)
    """
    try:
        log.info("Webhook form submission received",
                email=submission.email,
                date=submission.date,
                pax=submission.pax)

        # Prepare inputs for the recipe
        inputs = {
            "nom_complet": submission.nom_complet,
            "email": submission.email,
            "telephone": submission.telephone or "",
            "adresse": submission.adresse or "",
            "ville": submission.ville or "",
            "type_client": submission.type_client or "Particulier",
            "date": submission.date,
            "pax": submission.pax,
            "moment": submission.moment or "Déjeuner",
            "nom_prestation": submission.nom_prestation or f"{submission.nom_complet} - {submission.date}",
            "options": submission.options or []
        }

        # Launch the recipe via orchestrator
        task_id = await orchestrator.run_recipe("deme_traiteur", inputs)

        log.info("DéMé Traiteur workflow launched",
                task_id=task_id,
                email=submission.email)

        return WebhookResponse(
            success=True,
            task_id=task_id,
            message=f"Demande de prestation enregistrée avec succès. ID de suivi: {task_id}"
        )

    except Exception as e:
        log.error("Error processing webhook submission",
                 error=str(e),
                 email=submission.email if submission else None)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors du traitement de la demande: {str(e)}"
        )


@router.get("/health")
async def health_check():
    """
    Health check endpoint for the DéMé Traiteur pack
    """
    return {
        "status": "healthy",
        "pack": "deme_traiteur",
        "version": "1.0.0"
    }
