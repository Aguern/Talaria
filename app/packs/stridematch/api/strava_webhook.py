"""
Webhook Handler pour Strava API

Endpoints FastAPI pour recevoir et traiter les événements webhook de Strava.
"""

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, Request
from typing import Dict, Optional
from datetime import datetime
import structlog
import uuid

from packs.stridematch.strava_test import schemas, config
from packs.stridematch.strava_test.logic import StravaAPIClient

log = structlog.get_logger()

# Créer le router
strava_router = APIRouter(
    prefix="/api/stridematch/strava-test",
    tags=["StrideMatch - Strava Testing"]
)

# Job queue en mémoire (même pattern que webhook_handler.py)
strava_jobs: Dict[str, schemas.StravaJobStatus] = {}

# Client API Strava (singleton)
strava_client = StravaAPIClient()


# ============================================================================
# Background Task Runner
# ============================================================================

async def process_strava_activity_task(
    job_id: str,
    activity_id: int,
    owner_id: int
):
    """
    Tâche background pour traiter une activité Strava.

    Args:
        job_id: Identifiant unique du job
        activity_id: ID de l'activité Strava
        owner_id: ID du propriétaire
    """
    try:
        strava_jobs[job_id].status = "processing"
        strava_jobs[job_id].started_at = datetime.utcnow()

        log.info("strava_job_started",
                job_id=job_id,
                activity_id=activity_id,
                owner_id=owner_id)

        # Traiter l'activité
        updates = await strava_client.process_new_activity(activity_id, owner_id)

        # Marquer comme complété
        strava_jobs[job_id].status = "completed"
        strava_jobs[job_id].completed_at = datetime.utcnow()
        strava_jobs[job_id].updates_applied = updates

        log.info("strava_job_completed",
                job_id=job_id,
                activity_id=activity_id)

    except Exception as e:
        strava_jobs[job_id].status = "failed"
        strava_jobs[job_id].completed_at = datetime.utcnow()
        strava_jobs[job_id].error = str(e)

        log.error("strava_job_failed",
                 job_id=job_id,
                 activity_id=activity_id,
                 error=str(e))


# ============================================================================
# Webhook Endpoints
# ============================================================================

@strava_router.get("/webhook")
async def strava_webhook_validation(
    hub_mode: str = Query(..., alias="hub.mode"),
    hub_challenge: str = Query(..., alias="hub.challenge"),
    hub_verify_token: str = Query(..., alias="hub.verify_token")
):
    """
    Endpoint de validation pour l'abonnement webhook Strava (GET).

    Strava envoie une requête GET pour vérifier que le callback URL est valide.
    On doit renvoyer hub.challenge si hub.verify_token correspond.

    **Paramètres** (query string):
    - hub.mode: Toujours "subscribe"
    - hub.verify_token: Token de vérification (doit matcher "STRAVA")
    - hub.challenge: Challenge à renvoyer pour validation

    **Réponse**: JSON avec {"hub.challenge": "..."}
    """
    log.info("strava_webhook_validation_request",
            mode=hub_mode,
            verify_token=hub_verify_token)

    # Vérifier que le mode est "subscribe"
    if hub_mode != "subscribe":
        log.warning("strava_webhook_invalid_mode", mode=hub_mode)
        raise HTTPException(status_code=400, detail="Invalid hub.mode")

    # Vérifier le token
    if hub_verify_token != config.WEBHOOK_VERIFY_TOKEN:
        log.warning("strava_webhook_invalid_token", token=hub_verify_token)
        raise HTTPException(status_code=403, detail="Invalid verify token")

    log.info("strava_webhook_validated", challenge=hub_challenge)

    # Renvoyer le challenge
    return {"hub.challenge": hub_challenge}


@strava_router.post("/webhook", response_model=schemas.WebhookResponse)
async def strava_webhook_event(
    event: schemas.StravaWebhookEvent,
    background_tasks: BackgroundTasks
):
    """
    Endpoint pour recevoir les événements webhook Strava (POST).

    **IMPORTANT**: Doit répondre 200 OK dans les 2 secondes, sinon Strava
    considère le webhook comme échoué.

    Le traitement réel est fait en background pour éviter les timeouts.

    **Événements supportés**:
    - object_type: "activity"
    - aspect_type: "create"

    **Payload exemple**:
    ```json
    {
      "object_type": "activity",
      "object_id": 123456789,
      "aspect_type": "create",
      "owner_id": 134815,
      "subscription_id": 120475,
      "event_time": 1516126040
    }
    ```
    """
    log.info("strava_webhook_event_received",
            object_type=event.object_type,
            object_id=event.object_id,
            aspect_type=event.aspect_type,
            owner_id=event.owner_id)

    # Filtrer uniquement les créations d'activité
    if event.object_type != "activity" or event.aspect_type != "create":
        log.info("strava_webhook_event_ignored",
                object_type=event.object_type,
                aspect_type=event.aspect_type)
        return schemas.WebhookResponse(
            status="success",
            message="Event ignored (not activity.create)"
        )

    # Générer job ID unique
    job_id = f"strava_{event.object_id}_{uuid.uuid4().hex[:8]}"

    # Créer le job status
    strava_jobs[job_id] = schemas.StravaJobStatus(
        job_id=job_id,
        status="queued",
        activity_id=event.object_id,
        owner_id=event.owner_id
    )

    # Lancer le traitement en background
    background_tasks.add_task(
        process_strava_activity_task,
        job_id=job_id,
        activity_id=event.object_id,
        owner_id=event.owner_id
    )

    log.info("strava_job_queued",
            job_id=job_id,
            activity_id=event.object_id)

    # Répondre immédiatement (critique pour Strava)
    return schemas.WebhookResponse(
        status="success",
        message="Activity update queued",
        job_id=job_id
    )


@strava_router.get("/jobs/{job_id}", response_model=schemas.StravaJobStatus)
async def get_strava_job_status(job_id: str):
    """
    Récupère le statut d'un job de mise à jour Strava.

    **Paramètres**:
    - job_id: Identifiant du job (retourné par le webhook)

    **Exemple**:
    ```
    GET /api/stridematch/strava-test/jobs/strava_123456789_a3f2b1c4
    ```
    """
    if job_id not in strava_jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    return strava_jobs[job_id]


@strava_router.get("/jobs", response_model=list[schemas.StravaJobStatus])
async def list_strava_jobs(limit: int = 50):
    """
    Liste les jobs récents de mise à jour Strava.

    **Paramètres**:
    - limit: Nombre max de jobs à retourner (défaut: 50)
    """
    sorted_jobs = sorted(
        strava_jobs.values(),
        key=lambda x: x.started_at or datetime.min,
        reverse=True
    )
    return sorted_jobs[:limit]


@strava_router.get("/subscription-info", response_model=schemas.SubscriptionInfo)
async def get_subscription_info():
    """
    Retourne la commande cURL pour enregistrer le webhook auprès de Strava.

    **À EXÉCUTER MANUELLEMENT** après le déploiement pour activer les webhooks.
    """
    curl_command = f"""curl -X POST https://www.strava.com/api/v3/push_subscriptions \\
  -F client_id={config.STRAVA_CLIENT_ID} \\
  -F client_secret={config.STRAVA_CLIENT_SECRET} \\
  -F callback_url={config.CALLBACK_URL}/api/stridematch/strava-test/webhook \\
  -F verify_token={config.WEBHOOK_VERIFY_TOKEN}"""

    instructions = """
1. Assurez-vous que le serveur est déployé et accessible publiquement
2. Exécutez la commande cURL ci-dessus dans votre terminal
3. Strava enverra une requête GET de validation au callback_url
4. Si la validation réussit, vous recevrez un subscription_id
5. Créez une activité Strava pour tester le webhook
    """

    return schemas.SubscriptionInfo(
        curl_command=curl_command,
        callback_url=f"{config.CALLBACK_URL}/api/stridematch/strava-test/webhook",
        verify_token=config.WEBHOOK_VERIFY_TOKEN,
        instructions=instructions.strip()
    )
