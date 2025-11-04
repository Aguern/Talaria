# Fichier: app/packs/deme_traiteur/integrations/email_client.py

import os
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any
import structlog

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

log = structlog.get_logger()


class EmailClient:
    """
    Client Gmail API pour envoyer des notifications email à DéMé.
    Utilise token.json pour l'authentification OAuth2.
    """

    def __init__(self):
        self.notification_email = os.getenv("DEME_NOTIFICATION_EMAIL", "demo.nouvellerive@gmail.com")
        self.gmail_service = None

        # Initialize Gmail API with auto-refresh from environment variable
        try:
            import json
            token_json = os.getenv("GOOGLE_TOKEN_JSON")

            if not token_json:
                # Fallback to token.json file if env var not set (for local dev)
                token_path = "token.json"
                if not os.path.exists(token_path):
                    log.error("GOOGLE_TOKEN_JSON env var not set and token.json not found")
                    return

                with open(token_path, 'r') as f:
                    token_data = json.load(f)
            else:
                token_data = json.loads(token_json)

            # Create credentials from token data
            creds = Credentials(
                token=token_data.get("token"),
                refresh_token=token_data.get("refresh_token"),
                token_uri=token_data.get("token_uri"),
                client_id=token_data.get("client_id"),
                client_secret=token_data.get("client_secret"),
                scopes=token_data.get("scopes")
            )

            # Always refresh token at startup to ensure validity
            # This avoids expiration issues on Render where filesystem is not persistent
            if creds.refresh_token:
                from google.auth.transport.requests import Request
                creds.refresh(Request())
                log.info("Gmail token refreshed successfully at startup")
            else:
                log.warning("No refresh_token available, using existing token (may expire)")

            self.gmail_service = build('gmail', 'v1', credentials=creds)
            log.info("Gmail API initialized successfully")
        except Exception as e:
            log.error("Failed to initialize Gmail API", error=str(e))

    async def send_prestation_notification(
        self,
        client_data: Dict[str, Any],
        prestation_data: Dict[str, Any],
        links: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Envoie un email de notification à DéMé avec les détails de la nouvelle prestation.

        Args:
            client_data: Informations du client (nom, email, téléphone, etc.)
            prestation_data: Informations de la prestation (date, pax, moment, options)
            links: Dictionnaire contenant les liens (notion_url, sheet_url, calendar_url)

        Returns:
            Dict avec le statut de l'envoi
        """
        if not self.gmail_service:
            log.warning("Cannot send email: Gmail API not initialized")
            return {
                "success": False,
                "message": "Gmail API not initialized"
            }

        try:
            # Créer le message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"📋 Nouvelle demande de prestation - {client_data.get('nom_complet', 'Client')}"
            msg['From'] = 'assistant.nouvellerive@gmail.com'
            msg['To'] = self.notification_email

            # Créer le contenu HTML
            html_content = self._build_email_html(client_data, prestation_data, links)

            # Créer le contenu texte (fallback)
            text_content = self._build_email_text(client_data, prestation_data, links)

            # Attacher les deux versions
            part1 = MIMEText(text_content, 'plain', 'utf-8')
            part2 = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(part1)
            msg.attach(part2)

            # Envoyer via Gmail API
            raw_message = base64.urlsafe_b64encode(msg.as_bytes()).decode('utf-8')
            send_result = self.gmail_service.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()

            log.info("Email notification sent successfully via Gmail API",
                    recipient=self.notification_email,
                    client=client_data.get('nom_complet'),
                    message_id=send_result.get('id'))

            return {
                "success": True,
                "message": "Email sent successfully",
                "recipient": self.notification_email,
                "message_id": send_result.get('id')
            }

        except Exception as e:
            log.error("Failed to send email notification", error=str(e))
            return {
                "success": False,
                "message": f"Failed to send email: {str(e)}"
            }

    def _build_email_html(
        self,
        client_data: Dict[str, Any],
        prestation_data: Dict[str, Any],
        links: Dict[str, str]
    ) -> str:
        """Construit le contenu HTML de l'email."""

        # Formater les options
        options_list = prestation_data.get('options', [])
        options_html = "<br>".join([f"        • {opt}" for opt in options_list]) if options_list else "        Aucune option spécifiée"

        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
        }}
        .container {{
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
        }}
        .header {{
            background-color: #4CAF50;
            color: white;
            padding: 20px;
            text-align: center;
            border-radius: 5px 5px 0 0;
        }}
        .content {{
            background-color: #f9f9f9;
            padding: 20px;
            border: 1px solid #ddd;
        }}
        .section {{
            margin-bottom: 20px;
        }}
        .section-title {{
            font-size: 18px;
            font-weight: bold;
            color: #4CAF50;
            margin-bottom: 10px;
        }}
        .info-row {{
            margin: 5px 0;
        }}
        .label {{
            font-weight: bold;
            color: #555;
        }}
        .link-button {{
            display: inline-block;
            background-color: #4CAF50;
            color: white !important;
            padding: 10px 20px;
            text-decoration: none;
            border-radius: 5px;
            margin: 5px;
        }}
        .footer {{
            background-color: #f1f1f1;
            padding: 15px;
            text-align: center;
            font-size: 12px;
            color: #777;
            border-radius: 0 0 5px 5px;
        }}
        .checklist {{
            background-color: #e8f5e9;
            padding: 15px;
            border-left: 4px solid #4CAF50;
            margin-top: 15px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📋 Nouvelle Demande de Prestation</h1>
        </div>

        <div class="content">
            <div class="section">
                <div class="section-title">👤 INFORMATIONS CLIENT</div>
                <div class="info-row"><span class="label">Nom :</span> {client_data.get('nom_complet', 'N/A')}</div>
                <div class="info-row"><span class="label">Email :</span> {client_data.get('email', 'N/A')}</div>
                <div class="info-row"><span class="label">Téléphone :</span> {client_data.get('telephone', 'N/A')}</div>
                <div class="info-row"><span class="label">Adresse :</span> {client_data.get('adresse', 'N/A')}</div>
                <div class="info-row"><span class="label">Ville :</span> {client_data.get('ville', 'N/A')}</div>
                <div class="info-row"><span class="label">Type de client :</span> {client_data.get('type_client', 'Particulier')}</div>
            </div>

            <div class="section">
                <div class="section-title">🍽️ DÉTAILS DE LA PRESTATION</div>
                <div class="info-row"><span class="label">Date :</span> {prestation_data.get('date', 'N/A')}</div>
                <div class="info-row"><span class="label">Moment :</span> {prestation_data.get('moment', 'N/A')}</div>
                <div class="info-row"><span class="label">Nombre de personnes :</span> {prestation_data.get('pax', 'N/A')}</div>
                <div class="info-row"><span class="label">Options de menu :</span></div>
                {options_html}
            </div>

            {f'''
            <div class="section">
                <div class="section-title">💬 MESSAGE DU PROSPECT</div>
                <div style="background-color: #fff3cd; padding: 15px; border-left: 4px solid #ffc107; border-radius: 4px;">
                    <p style="margin: 0; white-space: pre-wrap;">{prestation_data.get('message', 'Aucun message')}</p>
                </div>
            </div>
            ''' if prestation_data.get('message') else ''}

            <div class="section">
                <div class="section-title">🔗 LIENS RAPIDES</div>
                <div style="text-align: center; margin-top: 15px;">
                    <a href="{links.get('notion_url', '#')}" class="link-button">📋 Fiche Notion</a>
                    <a href="{links.get('sheet_url', '#')}" class="link-button">📊 Devis Google Sheet</a>
                    <a href="{links.get('calendar_url', '#')}" class="link-button">📅 Événement Calendar</a>
                </div>
            </div>
        </div>

        <div class="footer">
            <p>🤖 Notification automatique générée par le système DéMé Traiteur</p>
            <p>Pour toute question, consultez la fiche Notion de la prestation.</p>
        </div>
    </div>
</body>
</html>
"""
        return html

    def _build_email_text(
        self,
        client_data: Dict[str, Any],
        prestation_data: Dict[str, Any],
        links: Dict[str, str]
    ) -> str:
        """Construit le contenu texte brut de l'email (fallback)."""

        options_list = prestation_data.get('options', [])
        options_text = "\n".join([f"  • {opt}" for opt in options_list]) if options_list else "  Aucune option spécifiée"

        text = f"""
Bonjour DéMé,

Une nouvelle demande de prestation a été enregistrée avec succès !

👤 INFORMATIONS CLIENT
━━━━━━━━━━━━━━━━━━━━
Nom : {client_data.get('nom_complet', 'N/A')}
Email : {client_data.get('email', 'N/A')}
Téléphone : {client_data.get('telephone', 'N/A')}
Adresse : {client_data.get('adresse', 'N/A')}
Ville : {client_data.get('ville', 'N/A')}
Type de client : {client_data.get('type_client', 'Particulier')}

🍽️ DÉTAILS DE LA PRESTATION
━━━━━━━━━━━━━━━━━━━━━━━━━
Date : {prestation_data.get('date', 'N/A')}
Moment : {prestation_data.get('moment', 'N/A')}
Nombre de personnes : {prestation_data.get('pax', 'N/A')}

Options de menu :
{options_text}

{f'''
💬 MESSAGE DU PROSPECT
━━━━━━━━━━━━━━━━━━━━
{prestation_data.get('message', 'Aucun message')}

''' if prestation_data.get('message') else ''}
🔗 LIENS RAPIDES
━━━━━━━━━━━━━━━
• Fiche Notion : {links.get('notion_url', 'N/A')}
• Devis Google Sheet : {links.get('sheet_url', 'N/A')}
• Événement Calendar : {links.get('calendar_url', 'N/A')}

Bonne journée !

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🤖 Notification automatique
Système DéMé Traiteur
"""
        return text
