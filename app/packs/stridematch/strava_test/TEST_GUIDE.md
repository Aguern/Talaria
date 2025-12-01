# Guide de Test - Intégration Strava API

Ce guide explique comment tester l'intégration Strava API une fois déployé sur Render.

## 📋 Prérequis

1. ✅ Variables d'environnement configurées sur Render :
   - `STRAVA_CLIENT_ID`
   - `STRAVA_CLIENT_SECRET`
   - `STRAVA_REFRESH_TOKEN`
   - `STRAVA_ACCESS_TOKEN`
   - `STRAVA_CALLBACK_URL`
   - `STRAVA_WEBHOOK_VERIFY_TOKEN` (optionnel, défaut: "STRAVA")

2. ✅ Application déployée sur Render avec les derniers changements

3. ✅ Une activité Strava existante que vous souhaitez modifier pour le test

## 🧪 Tester la connexion Strava

### Option 1 : Via l'API Render (Recommandé)

Une fois votre application déployée sur Render, utilisez l'endpoint de test :

```bash
# Remplacez :
# - <VOTRE_URL_RENDER> par l'URL de votre service Render (ex: https://deme-api.onrender.com)
# - <ACTIVITY_ID> par l'ID de votre activité Strava

curl -X POST "https://<VOTRE_URL_RENDER>/api/stridematch/strava-test/test-connection/<ACTIVITY_ID>"
```

**Exemple concret** :
```bash
curl -X POST "https://deme-api.onrender.com/api/stridematch/strava-test/test-connection/16513661416"
```

**Réponse attendue en cas de succès** :
```json
{
  "status": "success",
  "message": "Test de connexion Strava réussi !",
  "activity_id": 16513661416,
  "activity_name": "Course du matin",
  "activity_type": "Run",
  "token_refreshed": true,
  "modifications_applied": {
    "description": "Signature StrideMatch ajoutée",
    "private_note": "Note de test ajoutée"
  },
  "strava_link": "https://www.strava.com/activities/16513661416"
}
```

**En cas d'erreur** :
```json
{
  "status": "error",
  "message": "Échec du test de connexion Strava",
  "error": "401 Unauthorized",
  "troubleshooting": [
    "Vérifiez que les variables d'environnement Strava sont configurées",
    "Vérifiez que le refresh token est valide",
    "Vérifiez que les permissions OAuth incluent 'activity:write'"
  ]
}
```

### Option 2 : Via le navigateur

Ouvrez simplement cette URL dans votre navigateur (remplacez les valeurs) :

```
https://<VOTRE_URL_RENDER>/api/docs
```

Puis :
1. Cherchez l'endpoint `POST /api/stridematch/strava-test/test-connection/{activity_id}`
2. Cliquez sur "Try it out"
3. Entrez l'ID de votre activité
4. Cliquez sur "Execute"

### Option 3 : Test local

Si vous voulez tester en local avant le déploiement :

```bash
# 1. Créer un fichier .env avec vos credentials Strava
cd /path/to/Talaria

# 2. Installer les dépendances
pip install pydantic httpx structlog

# 3. Lancer le script de test
PYTHONPATH=. python app/packs/stridematch/strava_test/test_connection.py 16513661416
```

**Note** : Le test local peut échouer à cause des restrictions réseau dans certains environnements. C'est normal - utilisez l'option 1 (API Render) dans ce cas.

## ✅ Vérification du résultat

Après avoir lancé le test, vérifiez sur Strava :

1. Allez sur votre activité : https://www.strava.com/activities/VOTRE_ACTIVITY_ID
2. Dans la **description**, vous devriez voir : `🧪 TEST StrideMatch • Connexion validée ✅`
3. Dans les **notes privées**, vous devriez voir le message de test

## 🔧 Dépannage

### Erreur 401 Unauthorized

**Cause** : Le refresh token est expiré ou invalide.

**Solution** :
1. Allez sur https://www.strava.com/settings/api
2. Créez une nouvelle autorisation OAuth avec les scopes : `activity:read_all,activity:write`
3. Obtenez un nouveau refresh token
4. Mettez à jour la variable `STRAVA_REFRESH_TOKEN` sur Render
5. Redémarrez le service

### Erreur 403 Forbidden

**Cause** : Permissions OAuth insuffisantes.

**Solution** :
1. Vérifiez que votre application Strava a le scope `activity:write`
2. Si non, créez une nouvelle autorisation avec ce scope
3. Mettez à jour les tokens sur Render

### Erreur 404 Not Found

**Cause** : L'activité n'existe pas ou vous n'y avez pas accès.

**Solution** :
1. Vérifiez l'ID de l'activité sur Strava
2. Vérifiez que l'activité appartient au compte connecté
3. Utilisez une activité récente et publique

### Erreur 500 Internal Server Error

**Cause** : Variables d'environnement manquantes ou mal configurées.

**Solution** :
1. Vérifiez que toutes les variables Strava sont configurées sur Render
2. Vérifiez les logs Render pour plus de détails
3. Redémarrez le service après avoir configuré les variables

## 📚 Documentation API complète

Pour voir tous les endpoints disponibles, consultez la documentation interactive :

```
https://<VOTRE_URL_RENDER>/api/docs
```

Sous la section **StrideMatch - Strava Testing**, vous trouverez :

- `POST /api/stridematch/strava-test/test-connection/{activity_id}` - Test de connexion
- `GET /api/stridematch/strava-test/subscription-info` - Info pour configurer le webhook
- `POST /api/stridematch/strava-test/webhook` - Endpoint webhook (pour production)
- `GET /api/stridematch/strava-test/jobs` - Liste des jobs de mise à jour
- `GET /api/stridematch/strava-test/jobs/{job_id}` - Statut d'un job

## 🎯 Prochaines étapes

Une fois le test réussi :

1. ✅ Votre intégration Strava est opérationnelle
2. 🔄 Vous pouvez configurer le webhook Strava pour les mises à jour automatiques
3. 🚀 Le pack StrideMatch peut enrichir automatiquement vos activités

Pour configurer le webhook automatique, appelez :
```bash
curl "https://<VOTRE_URL_RENDER>/api/stridematch/strava-test/subscription-info"
```

Cela vous donnera la commande curl complète pour enregistrer le webhook auprès de Strava.
