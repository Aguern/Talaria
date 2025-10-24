"""
Google Calendar API Client for DéMé Traiteur Pack

Handles event creation in Google Calendar
"""

import os
import json
import httpx
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class GoogleCalendarClient:
    """Client for Google Calendar API operations"""

    def __init__(self):
        credentials_str = os.getenv("GOOGLE_CALENDAR_CREDENTIALS")
        self.credentials = json.loads(credentials_str) if credentials_str else {}
        self.calendar_id = os.getenv("GOOGLE_CALENDAR_ID")
        self.access_token: Optional[str] = None

    async def _get_access_token(self) -> str:
        """
        Get OAuth2 access token using service account credentials

        Returns:
            Access token string
        """
        # Always regenerate token to avoid stale token issues
        # (removing the cache check)

        # For service accounts, we need to use JWT
        try:
            from google.oauth2 import service_account
            from google.auth.transport.requests import Request

            credentials = service_account.Credentials.from_service_account_info(
                self.credentials,
                scopes=['https://www.googleapis.com/auth/calendar']
            )

            # Refresh to get the token
            credentials.refresh(Request())
            self.access_token = credentials.token
            logger.info("Google Calendar access token obtained")
            return self.access_token

        except Exception as e:
            logger.error(f"Error getting access token: {str(e)}")
            raise

    async def create_event(
        self,
        summary: str,
        start_datetime: str,
        end_datetime: str,
        description: str = "",
        location: str = "",
        attendees: Optional[List[str]] = None
    ) -> Dict[str, str]:
        """
        Create an event in Google Calendar

        Args:
            summary: Event title
            start_datetime: Start datetime in ISO format (e.g., "2025-01-15T12:00:00")
            end_datetime: End datetime in ISO format
            description: Event description (can include links)
            location: Event location
            attendees: List of attendee email addresses

        Returns:
            Dictionary with 'id' and 'htmlLink' of the created event
        """
        token = await self._get_access_token()

        url = f"https://www.googleapis.com/calendar/v3/calendars/{self.calendar_id}/events"

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        # Prepare attendees list
        attendees_list = []
        if attendees:
            attendees_list = [{"email": email} for email in attendees]

        # Prepare event payload
        event = {
            "summary": summary,
            "description": description,
            "location": location,
            "start": {
                "dateTime": start_datetime,
                "timeZone": "Europe/Paris"
            },
            "end": {
                "dateTime": end_datetime,
                "timeZone": "Europe/Paris"
            },
            "attendees": attendees_list,
            "reminders": {
                "useDefault": True
            }
        }

        try:
            async with httpx.AsyncClient() as client:
                # DEBUG: Log request details
                logger.info(f"DEBUG: Sending POST to {url}")
                logger.info(f"DEBUG: Calendar ID: {self.calendar_id}")
                logger.info(f"DEBUG: Event summary: {summary}")
                logger.info(f"DEBUG: Token length: {len(token)}")

                response = await client.post(url, headers=headers, json=event)

                # DEBUG: Log response details
                logger.info(f"DEBUG: Response status: {response.status_code}")
                logger.info(f"DEBUG: Response headers: {dict(response.headers)}")

                response.raise_for_status()
                data = response.json()

                event_id = data["id"]
                event_link = data.get("htmlLink", "")
                logger.info(f"Google Calendar event created: {event_id}")
                return {"id": event_id, "htmlLink": event_link}

        except httpx.HTTPStatusError as e:
            logger.error(f"ERROR: HTTP {e.response.status_code}")
            logger.error(f"ERROR: Response body: {e.response.text}")
            logger.error(f"ERROR: Request URL: {e.request.url}")
            logger.error(f"ERROR: Request headers: {dict(e.request.headers)}")
            raise
        except Exception as e:
            logger.error(f"Error creating calendar event: {str(e)}")
            raise

    async def create_event_from_prestation(
        self,
        prestation_data: Dict[str, Any],
        prestation_url: str,
        client_data: Dict[str, Any],
        devis_sheet_link: str
    ) -> Dict[str, str]:
        """
        Create a calendar event from prestation data with enriched client information

        Args:
            prestation_data: Dictionary with keys: nom_prestation, date, moment, pax, ville
            prestation_url: URL to the Notion prestation page
            client_data: Dictionary with keys: nom_complet, email, telephone, adresse, ville
            devis_sheet_link: URL to the Google Sheet devis

        Returns:
            Dictionary with 'id' and 'htmlLink' of the created event
        """
        # Build event summary
        summary = f"DéMé - {prestation_data.get('nom_prestation', 'Prestation')}"

        # Build enriched description with Client, Prestation, Message, and Links sections
        message_section = f"""
💬 MESSAGE DU PROSPECT
{prestation_data.get('message', 'Aucun message')}
""" if prestation_data.get('message') else ""

        description = f"""📋 INFORMATIONS CLIENT
Nom: {client_data.get('nom_complet', '')}
Email: {client_data.get('email', '')}
Téléphone: {client_data.get('telephone', '')}
Adresse: {client_data.get('adresse', '')}
Ville: {client_data.get('ville', '')}

🍽️ PRESTATION
Date: {prestation_data.get('date', '')}
PAX: {prestation_data.get('pax', 0)} personnes
Moment: {prestation_data.get('moment', 'Midi')}
{message_section}
🔗 LIENS
Fiche Notion: {prestation_url}
Devis Google Sheet: {devis_sheet_link}
"""

        # Parse date and create start/end datetimes
        date_str = prestation_data.get('date', '')
        moment = prestation_data.get('moment', 'Déjeuner')

        # Set default times based on moment
        # Handle both "Déjeuner"/"Midi" and "Dîner"/"Soir"
        if moment in ["Déjeuner", "Midi"]:
            start_time = "12:00:00"
            end_time = "14:00:00"
        elif moment in ["Dîner", "Soir"]:
            start_time = "19:00:00"
            end_time = "21:00:00"
        else:
            start_time = "10:00:00"
            end_time = "12:00:00"

        start_datetime = f"{date_str}T{start_time}"
        end_datetime = f"{date_str}T{end_time}"

        location = prestation_data.get('ville', '')

        # Note: Service accounts cannot invite attendees without Domain-Wide Delegation
        # So we create the event without attendees
        attendees = []

        return await self.create_event(
            summary=summary,
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            description=description,
            location=location,
            attendees=attendees
        )
