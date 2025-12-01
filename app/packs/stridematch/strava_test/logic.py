"""Logique métier pour interagir avec l'API Strava"""

import httpx
from datetime import datetime
from typing import Dict, Optional
import structlog

from . import config

log = structlog.get_logger()

class StravaAPIClient:
    """Client pour interagir avec l'API Strava"""

    def __init__(self):
        self.client_id = config.STRAVA_CLIENT_ID
        self.client_secret = config.STRAVA_CLIENT_SECRET
        self.refresh_token = config.STRAVA_REFRESH_TOKEN
        self._access_token = config.STRAVA_ACCESS_TOKEN

    async def refresh_access_token(self) -> str:
        """
        Rafraîchit le token d'accès OAuth2 en utilisant le refresh token.

        Returns:
            str: Nouveau access token
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                config.STRAVA_OAUTH_TOKEN_URL,
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "grant_type": "refresh_token",
                    "refresh_token": self.refresh_token
                }
            )
            response.raise_for_status()
            data = response.json()

            self._access_token = data["access_token"]
            log.info("strava_token_refreshed",
                    expires_at=data["expires_at"],
                    expires_in=data["expires_in"])

            return self._access_token

    async def get_activity(self, activity_id: int) -> Dict:
        """
        Récupère les détails d'une activité Strava.

        Args:
            activity_id: ID de l'activité

        Returns:
            Dict contenant les détails de l'activité
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{config.STRAVA_ACTIVITIES_URL}/{activity_id}",
                headers={"Authorization": f"Bearer {self._access_token}"}
            )
            response.raise_for_status()
            activity = response.json()

            log.info("strava_activity_fetched",
                    activity_id=activity_id,
                    name=activity.get("name"),
                    type=activity.get("type"))

            return activity

    async def update_activity(
        self,
        activity_id: int,
        description: Optional[str] = None,
        private_note: Optional[str] = None
    ) -> Dict:
        """
        Met à jour une activité Strava (description et/ou private_note).

        Args:
            activity_id: ID de l'activité à mettre à jour
            description: Nouvelle description (optionnel)
            private_note: Nouvelle note privée (optionnel)

        Returns:
            Dict contenant la réponse de l'API
        """
        data = {}
        if description is not None:
            data["description"] = description
        if private_note is not None:
            data["private_note"] = private_note

        async with httpx.AsyncClient() as client:
            response = await client.put(
                f"{config.STRAVA_ACTIVITIES_URL}/{activity_id}",
                headers={"Authorization": f"Bearer {self._access_token}"},
                json=data
            )
            response.raise_for_status()
            result = response.json()

            log.info("strava_activity_updated",
                    activity_id=activity_id,
                    updated_fields=list(data.keys()))

            return result

    async def process_new_activity(self, activity_id: int, owner_id: int) -> Dict[str, str]:
        """
        Traitement complet d'une nouvelle activité :
        1. Rafraîchir le token
        2. Récupérer l'activité
        3. Mettre à jour description + private_note

        Args:
            activity_id: ID de l'activité
            owner_id: ID du propriétaire de l'activité

        Returns:
            Dict avec les mises à jour appliquées
        """
        try:
            # 1. Rafraîchir le token
            await self.refresh_access_token()

            # 2. Récupérer l'activité actuelle
            activity = await self.get_activity(activity_id)
            current_description = activity.get("description", "") or ""

            # 3. Préparer la nouvelle description (ajouter signature sans écraser)
            new_description = current_description + config.DESCRIPTION_SIGNATURE

            # 4. Mettre à jour l'activité
            await self.update_activity(
                activity_id=activity_id,
                description=new_description,
                private_note=config.PRIVATE_NOTE_COACHING
            )

            log.info("strava_activity_processing_completed",
                    activity_id=activity_id,
                    owner_id=owner_id)

            return {
                "description": new_description,
                "private_note": config.PRIVATE_NOTE_COACHING
            }

        except Exception as e:
            log.error("strava_activity_processing_failed",
                     activity_id=activity_id,
                     owner_id=owner_id,
                     error=str(e))
            raise
