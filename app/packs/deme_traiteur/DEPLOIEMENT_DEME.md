# 🚀 Guide de Déploiement DéMé Traiteur sur Render (Version 2.0 - Gratuite)

## 📋 Nouvelle Architecture (Gratuite sans Worker)

Cette version utilise **FastAPI BackgroundTasks** au lieu de Celery, permettant un déploiement **100% gratuit** sur Render Free.

### Workflow :
1. Prospect remplit le formulaire → envoie au webhook
2. API répond immédiatement (1-2s) : ✅ "Demande enregistrée"
3. Workflow s'exécute en arrière-plan (30-60s) :
   - Création client & prestation Notion
   - Génération devis Google Sheet
   - Création événement Google Calendar
   - **📧 Email automatique envoyé à DéMé**
4. DéMé reçoit l'email avec tous les liens

---

## ✅ Prérequis (Déjà fait)

- [x] `render.yaml` créé (sans worker)
- [x] `.dockerignore` créé
- [x] `.env` complété avec variables Notion + Email
- [x] `.gitignore` configuré pour ne pas commit les secrets
- [x] **Plus besoin d'Upstash Redis** ✅

---

## 📋 ÉTAPE 1 : Push le code sur GitHub

```bash
# Dans le dossier SaaS_NR

# Vérifier le statut
git status

# Ajouter tous les fichiers (sauf .env grâce au .gitignore)
git add .

# Commit
git commit -m "DéMé v2.0: Mode direct avec email notifications (Render Free)"

# Push
git push
```

**⚠️ IMPORTANT** : Vérifie que le `.env` n'a PAS été push :
```bash
git status
# .env ne doit PAS apparaître dans les fichiers trackés
```

---

## 📋 ÉTAPE 2 : Créer un compte Render

1. Va sur https://render.com
2. Clique sur "Get Started"
3. Connecte-toi avec GitHub
4. Autorise Render à accéder à tes repos

---

## 📋 ÉTAPE 3 : Déployer sur Render

### A. Créer le service depuis le Blueprint

1. Sur le dashboard Render, clique **"New +" → "Blueprint"**
2. Connecte ton repo GitHub `Talaria`
3. Render détecte automatiquement le fichier `render.yaml` ✅
4. Clique sur **"Apply"**

Render va créer automatiquement :
- ✅ Service Web : `deme-api`
- ✅ Database PostgreSQL : `deme-db`
- ❌ **Pas de worker** (plus nécessaire !)

### B. Configurer les variables d'environnement

Va dans : **Dashboard → deme-api → Environment**

Ajoute ces variables depuis ton `.env` :

```bash
# JWT & Encryption
SECRET_KEY=Ll4q145ur2nxncXmxyi28-Zj9kGb5Ju-qmMcvQ7B7HE
FERNET_KEY=vUNvO1IvfI_DtgV0dVn57pGS-27lLp3GJRHLscE-qk0=

# OpenAI
OPENAI_API_KEY=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
PPLX_API_KEY=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

# Notion
NOTION_API_TOKEN=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
NOTION_DATABASE_CLIENTS_ID=3805d502e86e474e83fa893197db4a80
NOTION_DATABASE_PRESTATIONS_ID=12ee0019fd5c48c6b18ce28be4151cf1
NOTION_DATABASE_CATALOGUE_ID=c9c12290234d4fbaa3198584c0117a5d
NOTION_DATABASE_LIGNES_DEVIS_ID=3bd15e699ed649c189bf437f8057e67e
NOTION_DATABASE_INGREDIENTS_ID=8b3362cec421486096c356e19c83a48b
NOTION_DATABASE_MATERIEL_ID=ae974d70b7f2431e9f19cc54bfda186c
NOTION_DATABASE_RH_ID=aa32b0204aa14be3915edd74cb5f5335

# Google Calendar (copie tout le JSON sur une ligne)
GOOGLE_CALENDAR_CREDENTIALS={"type": "service_account", "project_id": "deme-traiteur-automation", ...}
GOOGLE_CALENDAR_ID=a024e201cf5c0b79e93ec38be516841d5bb75497ad2b2d172b15d860ae8f4610@group.calendar.google.com

# Google Drive (copie tout le JSON sur une ligne)
GOOGLE_DRIVE_CREDENTIALS={"type": "service_account", "project_id": "deme-traiteur-automation", ...}
GOOGLE_DRIVE_TEMPLATE_FILE_ID=1bTaD-Usyfkr1v862I-5iiwJ6nvzG3p7RJbKbB26yuAE
GOOGLE_DRIVE_SHARED_FOLDER_ID=1ROU0zlIYM2gla_BnQjZ6xVC8Gd0DeQfx

# Email SMTP (Gmail - créer un mot de passe d'application)
SMTP_USER=your_email@gmail.com  # Ton email Gmail
SMTP_PASSWORD=your_app_password  # Mot de passe d'application Gmail
```

### C. Configurer Gmail SMTP (pour les notifications)

1. Va sur https://myaccount.google.com/apppasswords
2. Crée un mot de passe d'application :
   - App : "Mail"
   - Device : "DéMé Traiteur"
3. Copie le mot de passe généré (16 caractères)
4. Ajoute-le dans Render comme `SMTP_PASSWORD`
5. Ajoute ton email Gmail comme `SMTP_USER`

---

## 📋 ÉTAPE 4 : Vérifier le déploiement

### A. Vérifier les logs

**API** : Dashboard → deme-api → Logs
- Tu dois voir : `Application startup complete.`
- Tu dois voir : `DéMé Traiteur router: Direct execution mode enabled (Render Free)`

### B. Tester l'API

```bash
# Récupère l'URL de ton API (ex: https://deme-api.onrender.com)

# Test de santé
curl https://deme-api.onrender.com/api/packs/deme-traiteur/health

# Réponse attendue :
{
  "status": "healthy",
  "pack": "deme_traiteur",
  "version": "2.0.0",
  "mode": "direct"
}

# Test du webhook (attends 30-60s si cold start)
curl -X POST https://deme-api.onrender.com/api/packs/deme-traiteur/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "nom_complet": "Test Client",
    "email": "test@example.com",
    "telephone": "0612345678",
    "ville": "Lyon",
    "date": "2026-03-15",
    "pax": 30,
    "moment": "Midi",
    "options": ["Entrées (Charcuterie et Fromages)"]
  }'
```

**Réponse attendue** :
```json
{
  "success": true,
  "message": "Demande de prestation enregistrée avec succès. Nous vous recontacterons très prochainement."
}
```

### C. Vérifier le workflow complet

Après 30-60 secondes, vérifie :
- ✅ Client créé dans Notion
- ✅ Prestation créée
- ✅ Lignes de devis
- ✅ Événement Google Calendar
- ✅ Devis Google Sheet
- ✅ **Email reçu par DéMé** (demo.nouvellerive@gmail.com)

---

## 📋 ÉTAPE 5 : Livrer à DéMé

### A. Donner l'accès au workspace Notion

1. Transférer le compte `gestion.deme@proton.io` à DéMé
   - Lui donner email + mot de passe
   - Il aura accès à toutes les 7 bases Notion

### B. Fournir l'URL du webhook

```
URL : https://deme-api.onrender.com/api/packs/deme-traiteur/webhook
Method : POST
Content-Type : application/json
```

### C. Intégration sur son site web

Fournir le fichier `INTEGRATION_SITE.html` à DéMé.

Il doit remplacer l'URL du webhook :
```javascript
const WEBHOOK_URL = 'https://deme-api.onrender.com/api/packs/deme-traiteur/webhook';
```

---

## 🔧 MAINTENANCE

### Cold Start (15min d'inactivité)

Render Free met en veille après 15min. Premier appel = 30-60s de réveil.

**Solution** : Ajouter un cron job gratuit pour ping l'API toutes les 10 minutes.

**Option 1 : Cron-job.org (gratuit)**
1. Va sur https://cron-job.org
2. Crée un compte
3. Ajoute un job :
   - URL : `https://deme-api.onrender.com/api/packs/deme-traiteur/health`
   - Interval : Toutes les 10 minutes

**Option 2 : UptimeRobot (gratuit)**
1. Va sur https://uptimerobot.com
2. Crée un monitor HTTP(s)
3. URL : `https://deme-api.onrender.com/api/packs/deme-traiteur/health`
4. Interval : 5 minutes

### Logs et Monitoring

- **Logs** : Dashboard Render → Logs en temps réel
- **Erreurs** : Render envoie des emails si l'app crash
- **Email notifications** : Vérifier que les emails arrivent bien

### Mise à jour du code

```bash
# Faire tes modifications localement
git add .
git commit -m "Update: description"
git push

# Render redéploie automatiquement ✅
```

---

## 💰 COÛTS

- **Render** : 0€ (Free tier - API uniquement, pas de worker)
- **Gmail SMTP** : 0€ (gratuit)
- **Total** : **0€/mois** 🎉

---

## 🔄 PASSAGE EN MODE PRODUCTION (Si besoin de scaling)

Si DéMé a du succès et besoin de plus de capacité :

1. **Ajouter un worker Celery** (7$/mois) :
   - Ajouter Redis (Upstash ou Render Redis)
   - Activer le worker dans render.yaml
   - Ajouter CELERY_BROKER_URL dans les env vars
   - Le router détectera automatiquement et passera en mode Celery

2. **Upgrade plan Render** :
   - Starter : 7$/mois (plus de cold start)
   - Standard : 25$/mois (plus de ressources)

---

## ❓ TROUBLESHOOTING

### Erreur : "Service Unavailable"
→ L'app est en train de se réveiller (cold start), attends 60s

### Erreur : Connection to Notion failed
→ Vérifie que les variables d'env sont bien configurées
→ Vérifie que l'intégration Notion a accès aux bases

### Erreur : Email not sent
→ Vérifie les variables SMTP_USER et SMTP_PASSWORD
→ Vérifie que le mot de passe d'application Gmail est valide
→ Consulte les logs Render pour voir l'erreur exacte

### Mode Direct vs Celery

Le système détecte automatiquement le mode :
- **Mode Direct** : Si CELERY_BROKER_URL n'est pas défini (Render Free)
- **Mode Celery** : Si CELERY_BROKER_URL est défini (Production avec worker)

Pour vérifier le mode actif :
```bash
curl https://deme-api.onrender.com/api/packs/deme-traiteur/health
```

---

## 🎯 PROCHAINES ÉTAPES

1. [ ] Tester avec une vraie prestation
2. [ ] Vérifier que l'email arrive bien à DéMé
3. [ ] Setup cron job pour éviter le cold start
4. [ ] Documenter pour DéMé
5. [ ] Monitorer les premières semaines

---

**Félicitations ! DéMé Traiteur v2.0 est en production gratuitement ! 🚀**

**Changements vs v1.0 :**
- ❌ Plus besoin de Celery worker
- ❌ Plus besoin de Redis/Upstash
- ✅ 100% gratuit sur Render Free
- ✅ Email notifications automatiques
- ✅ Mode hybride (Celery si besoin plus tard)
