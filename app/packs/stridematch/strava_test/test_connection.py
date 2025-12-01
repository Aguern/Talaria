#!/usr/bin/env python3
"""
Script de test grandeur nature pour l'intégration Strava API.

Ce script teste :
1. Le rafraîchissement du token OAuth2
2. La récupération de la dernière activité
3. La modification d'une activité (ajout description + note privée)

Usage:
    python test_connection.py [activity_id]

Si activity_id n'est pas fourni, le script récupère automatiquement
la dernière activité de l'utilisateur connecté.
"""

import asyncio
import sys
from pathlib import Path

# Ajouter le répertoire parent au PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from app.packs.stridematch.strava_test.logic import StravaAPIClient
from app.packs.stridematch.strava_test import config


async def get_latest_activity(client: StravaAPIClient) -> dict:
    """Récupère la dernière activité de l'utilisateur."""
    import httpx

    async with httpx.AsyncClient() as http_client:
        response = await http_client.get(
            config.STRAVA_ACTIVITIES_URL,
            headers={"Authorization": f"Bearer {client._access_token}"},
            params={"per_page": 1}  # Seulement la dernière
        )
        response.raise_for_status()
        activities = response.json()

        if not activities:
            raise Exception("Aucune activité trouvée pour cet utilisateur")

        return activities[0]


async def test_strava_integration(activity_id: int = None):
    """
    Test complet de l'intégration Strava.

    Args:
        activity_id: ID de l'activité à modifier (optionnel)
    """
    print("=" * 70)
    print("TEST GRANDEUR NATURE - INTÉGRATION STRAVA API")
    print("=" * 70)
    print()

    # Initialisation du client
    print("📡 Initialisation du client Strava...")
    client = StravaAPIClient()
    print(f"   ✓ Client ID: {client.client_id}")
    print(f"   ✓ Callback URL: {config.CALLBACK_URL}")
    print()

    try:
        # Étape 1 : Rafraîchir le token
        print("🔄 Étape 1/3 : Rafraîchissement du token OAuth2...")
        new_token = await client.refresh_access_token()
        print(f"   ✓ Nouveau token obtenu : {new_token[:20]}...")
        print()

        # Étape 2 : Récupérer l'activité
        if activity_id is None:
            print("🔍 Étape 2/3 : Récupération de la dernière activité...")
            latest = await get_latest_activity(client)
            activity_id = latest["id"]
            print(f"   ✓ Dernière activité trouvée : ID {activity_id}")
            print(f"   ✓ Nom : {latest.get('name', 'Sans nom')}")
            print(f"   ✓ Type : {latest.get('type', 'Inconnu')}")
            print(f"   ✓ Date : {latest.get('start_date', 'Inconnue')}")
        else:
            print(f"🔍 Étape 2/3 : Récupération de l'activité {activity_id}...")
            activity = await client.get_activity(activity_id)
            print(f"   ✓ Activité récupérée : {activity.get('name', 'Sans nom')}")
            print(f"   ✓ Type : {activity.get('type', 'Inconnu')}")

        print()

        # Étape 3 : Modifier l'activité
        print("✏️  Étape 3/3 : Modification de l'activité...")
        print("   → Ajout de la signature StrideMatch dans la description")
        print("   → Ajout d'une note privée avec analyse")

        # Récupérer la description actuelle
        activity = await client.get_activity(activity_id)
        current_description = activity.get("description", "") or ""

        # Préparer les nouvelles données
        test_signature = "\n\n🧪 TEST StrideMatch • Connexion validée ✅"
        test_note = """Test StrideMatch - Connexion API réussie :
✅ Token OAuth2 rafraîchi
✅ Activité récupérée
✅ Modification appliquée

Ce test valide l'intégration Strava pour le pack StrideMatch."""

        new_description = current_description + test_signature

        # Appliquer les modifications
        result = await client.update_activity(
            activity_id=activity_id,
            description=new_description,
            private_note=test_note
        )

        print(f"   ✓ Description mise à jour")
        print(f"   ✓ Note privée ajoutée")
        print()

        # Résumé
        print("=" * 70)
        print("✅ SUCCÈS - TOUS LES TESTS SONT PASSÉS !")
        print("=" * 70)
        print()
        print("Résumé des opérations :")
        print(f"  • Token rafraîchi : ✅")
        print(f"  • Activité {activity_id} récupérée : ✅")
        print(f"  • Modifications appliquées : ✅")
        print()
        print("🎉 Votre compte Strava est correctement connecté !")
        print(f"🔗 Voir l'activité : https://www.strava.com/activities/{activity_id}")
        print()

    except Exception as e:
        print()
        print("=" * 70)
        print("❌ ÉCHEC DU TEST")
        print("=" * 70)
        print()
        print(f"Erreur : {str(e)}")
        print()
        print("Vérifiez que :")
        print("  1. Les variables d'environnement Strava sont correctement configurées")
        print("  2. Le refresh token est toujours valide")
        print("  3. Les permissions OAuth incluent 'activity:write'")
        print()
        raise


def main():
    """Point d'entrée du script."""
    activity_id = None

    # Récupérer l'activity_id depuis les arguments si fourni
    if len(sys.argv) > 1:
        try:
            activity_id = int(sys.argv[1])
        except ValueError:
            print("❌ Erreur : l'activity_id doit être un nombre entier")
            sys.exit(1)

    # Lancer le test
    asyncio.run(test_strava_integration(activity_id))


if __name__ == "__main__":
    main()
