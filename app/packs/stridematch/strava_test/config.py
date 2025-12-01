"""Configuration pour le module de test Strava API"""

import os

# Strava OAuth Credentials (lues depuis variables d'environnement)
STRAVA_CLIENT_ID = os.getenv("STRAVA_CLIENT_ID", "187964")
STRAVA_CLIENT_SECRET = os.getenv("STRAVA_CLIENT_SECRET", "f7a1a1e4777fb5201bdc2e81f57615632a711bd6")
STRAVA_REFRESH_TOKEN = os.getenv("STRAVA_REFRESH_TOKEN", "ccfca9deb206102e5d6a15b108e6efe779557201")
STRAVA_ACCESS_TOKEN = os.getenv("STRAVA_ACCESS_TOKEN", "5cf9669e408d7e5928be68638171fe1b49f857bf")

# Webhook Configuration
WEBHOOK_VERIFY_TOKEN = os.getenv("STRAVA_WEBHOOK_VERIFY_TOKEN", "STRAVA")
CALLBACK_URL = os.getenv("STRAVA_CALLBACK_URL", "https://nouvelle-rive.com")

# Strava API Endpoints
STRAVA_OAUTH_TOKEN_URL = "https://www.strava.com/api/v3/oauth/token"
STRAVA_ACTIVITIES_URL = "https://www.strava.com/api/v3/activities"

# Update Templates
DESCRIPTION_SIGNATURE = "\n\n👟 Test Shoe • 65% Life 🔋"
PRIVATE_NOTE_COACHING = """Analyse StrideMatch :
🏃 Repos conseillé après cette séance
📊 Metrics: Distance optimale atteinte
💡 Suggestion: Vérifier l'usure de vos chaussures"""
