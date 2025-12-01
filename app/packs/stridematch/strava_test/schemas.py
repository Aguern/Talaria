"""Schémas Pydantic pour le module Strava"""

from pydantic import BaseModel, Field
from typing import Optional, Literal, Dict, Any
from datetime import datetime

# ===== Webhook Event Models =====

class StravaWebhookEvent(BaseModel):
    """Événement webhook reçu de Strava"""
    object_type: str  # "activity" ou "athlete"
    object_id: int
    aspect_type: str  # "create", "update", "delete"
    updates: Optional[Dict[str, Any]] = {}
    owner_id: int
    subscription_id: int
    event_time: int  # Unix timestamp

class WebhookValidationRequest(BaseModel):
    """Paramètres de validation GET du webhook"""
    hub_mode: str
    hub_verify_token: str
    hub_challenge: str

# ===== Job Tracking Models =====

class StravaJobStatus(BaseModel):
    """Statut d'un job de mise à jour Strava"""
    job_id: str
    status: Literal["queued", "processing", "completed", "failed"]
    activity_id: Optional[int] = None
    owner_id: Optional[int] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    updates_applied: Optional[Dict[str, str]] = None  # {description: "...", private_note: "..."}

# ===== Response Models =====

class WebhookResponse(BaseModel):
    """Réponse standard du webhook"""
    status: Literal["success", "error"]
    message: str
    job_id: Optional[str] = None

class SubscriptionInfo(BaseModel):
    """Info sur l'abonnement webhook"""
    curl_command: str
    callback_url: str
    verify_token: str
    instructions: str
