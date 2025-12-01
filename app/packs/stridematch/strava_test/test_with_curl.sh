#!/bin/bash
# Script de test Strava API avec curl (contourne les problèmes de proxy Python)

set -e

echo "======================================================================"
echo "TEST GRANDEUR NATURE - INTÉGRATION STRAVA API (avec curl)"
echo "======================================================================"
echo ""

# Configuration
ACTIVITY_ID="${1:-16513661416}"
CLIENT_ID="${STRAVA_CLIENT_ID:-187964}"
CLIENT_SECRET="${STRAVA_CLIENT_SECRET:-f7a1a1e4777fb5201bdc2e81f57615632a711bd6}"
REFRESH_TOKEN="${STRAVA_REFRESH_TOKEN:-ccfca9deb206102e5d6a15b108e6efe779557201}"

echo "📡 Configuration:"
echo "   ✓ Client ID: $CLIENT_ID"
echo "   ✓ Activity ID: $ACTIVITY_ID"
echo ""

# Étape 1: Rafraîchir le token
echo "🔄 Étape 1/3 : Rafraîchissement du token OAuth2..."
REFRESH_RESPONSE=$(curl -s -X POST https://www.strava.com/api/v3/oauth/token \
  -d "client_id=$CLIENT_ID" \
  -d "client_secret=$CLIENT_SECRET" \
  -d "grant_type=refresh_token" \
  -d "refresh_token=$REFRESH_TOKEN")

# Vérifier si la réponse contient une erreur
if echo "$REFRESH_RESPONSE" | grep -q "error"; then
    echo "❌ Erreur lors du rafraîchissement du token:"
    echo "$REFRESH_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$REFRESH_RESPONSE"
    exit 1
fi

ACCESS_TOKEN=$(echo "$REFRESH_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")
echo "   ✓ Nouveau token obtenu : ${ACCESS_TOKEN:0:20}..."
echo ""

# Étape 2: Récupérer l'activité
echo "🔍 Étape 2/3 : Récupération de l'activité $ACTIVITY_ID..."
ACTIVITY_RESPONSE=$(curl -s -X GET "https://www.strava.com/api/v3/activities/$ACTIVITY_ID" \
  -H "Authorization: Bearer $ACCESS_TOKEN")

# Vérifier si la réponse contient une erreur
if echo "$ACTIVITY_RESPONSE" | grep -q "errors"; then
    echo "❌ Erreur lors de la récupération de l'activité:"
    echo "$ACTIVITY_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$ACTIVITY_RESPONSE"
    exit 1
fi

ACTIVITY_NAME=$(echo "$ACTIVITY_RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('name', 'Sans nom'))")
ACTIVITY_TYPE=$(echo "$ACTIVITY_RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('type', 'Inconnu'))")
CURRENT_DESCRIPTION=$(echo "$ACTIVITY_RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('description') or '')")

echo "   ✓ Activité récupérée : $ACTIVITY_NAME"
echo "   ✓ Type : $ACTIVITY_TYPE"
echo ""

# Étape 3: Modifier l'activité
echo "✏️  Étape 3/3 : Modification de l'activité..."
echo "   → Ajout de la signature StrideMatch dans la description"
echo "   → Ajout d'une note privée avec analyse"

# Préparer les nouvelles données
TEST_SIGNATURE=$'\n\n🧪 TEST StrideMatch • Connexion validée ✅'
NEW_DESCRIPTION="${CURRENT_DESCRIPTION}${TEST_SIGNATURE}"

TEST_NOTE="Test StrideMatch - Connexion API réussie :
✅ Token OAuth2 rafraîchi
✅ Activité récupérée
✅ Modification appliquée

Ce test valide l'intégration Strava pour le pack StrideMatch."

# Échapper les guillemets pour JSON
NEW_DESCRIPTION_ESCAPED=$(echo "$NEW_DESCRIPTION" | python3 -c "import sys, json; print(json.dumps(sys.stdin.read()))")
TEST_NOTE_ESCAPED=$(echo "$TEST_NOTE" | python3 -c "import sys, json; print(json.dumps(sys.stdin.read()))")

# Créer le payload JSON
PAYLOAD="{\"description\": $NEW_DESCRIPTION_ESCAPED, \"private_note\": $TEST_NOTE_ESCAPED}"

# Envoyer la mise à jour
UPDATE_RESPONSE=$(curl -s -X PUT "https://www.strava.com/api/v3/activities/$ACTIVITY_ID" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d "$PAYLOAD")

# Vérifier si la réponse contient une erreur
if echo "$UPDATE_RESPONSE" | grep -q "errors"; then
    echo "❌ Erreur lors de la modification de l'activité:"
    echo "$UPDATE_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$UPDATE_RESPONSE"
    exit 1
fi

echo "   ✓ Description mise à jour"
echo "   ✓ Note privée ajoutée"
echo ""

# Résumé
echo "======================================================================"
echo "✅ SUCCÈS - TOUS LES TESTS SONT PASSÉS !"
echo "======================================================================"
echo ""
echo "Résumé des opérations :"
echo "  • Token rafraîchi : ✅"
echo "  • Activité $ACTIVITY_ID récupérée : ✅"
echo "  • Modifications appliquées : ✅"
echo ""
echo "🎉 Votre compte Strava est correctement connecté !"
echo "🔗 Voir l'activité : https://www.strava.com/activities/$ACTIVITY_ID"
echo ""
