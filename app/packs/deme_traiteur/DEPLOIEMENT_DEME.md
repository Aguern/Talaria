# 🚀 Guide de Déploiement DéMé Traiteur sur Render

## ✅ Prérequis (Déjà fait)

- [x] `render.yaml` créé
- [x] `.dockerignore` créé
- [x] `.env` complété avec toutes les variables Notion
- [x] `.gitignore` configure pour ne pas commit les secrets

---

## 📋 ÉTAPE 1 : Créer un compte Redis gratuit (Upstash)

Render Free ne fournit pas Redis, mais Upstash a un plan gratuit parfait pour DéMé.

1. Va sur https://upstash.com
2. Crée un compte gratuit
3. Clique sur "Create Database"
   - Name: `deme-redis`
   - Type: **Regional**
   - Region: **EU-West-1** (Ireland - proche de Frankfurt)
   - Primary: Activé
4. Copie l'URL de connexion :
   - Format: `rediss://default:xxxxx@xxxxx.upstash.io:6379`

---

## 📋 ÉTAPE 2 : Push le code sur GitHub

```bash
# Dans le dossier SaaS_NR

# Initialiser Git si pas déjà fait
git init

# Ajouter tous les fichiers (sauf .env grâce au .gitignore)
git add .

# Commit
git commit -m "Setup DéMé Traiteur deployment for Render"

# Créer un repo sur GitHub (via interface web)
# Puis linker le repo local

git remote add origin https://github.com/TON_USERNAME/saas-deme-traiteur.git
git branch -M main
git push -u origin main
```

**⚠️ IMPORTANT** : Vérifie que le `.env` n'a PAS été push :
```bash
git status
# .env ne doit PAS apparaître dans les fichiers trackés
```

---

## 📋 ÉTAPE 3 : Créer un compte Render

1. Va sur https://render.com
2. Clique sur "Get Started"
3. Connecte-toi avec GitHub
4. Autorise Render à accéder à tes repos

---

## 📋 ÉTAPE 4 : Déployer sur Render

### A. Créer le service depuis le Blueprint

1. Sur le dashboard Render, clique **"New +" → "Blueprint"**
2. Connecte ton repo GitHub `saas-deme-traiteur`
3. Render détecte automatiquement le fichier `render.yaml` ✅
4. Clique sur **"Apply"**

Render va créer automatiquement :
- ✅ Service Web : `deme-api`
- ✅ Service Worker : `deme-worker`
- ✅ Database PostgreSQL : `deme-db`

### B. Configurer les variables d'environnement

Pour chaque service (API et Worker), tu dois ajouter les variables avec `sync: false`.

#### 1. Service `deme-api`

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

# Redis Upstash (URL d'Upstash créée à l'étape 1)
CELERY_BROKER_URL=rediss://default:xxxxx@xxxxx.upstash.io:6379
CELERY_RESULT_BACKEND=rediss://default:xxxxx@xxxxx.upstash.io:6379
```

#### 2. Service `deme-worker`

Va dans : **Dashboard → deme-worker → Environment**

**Ajoute EXACTEMENT les mêmes variables** que pour `deme-api`.

---

## 📋 ÉTAPE 5 : Vérifier le déploiement

### A. Vérifier les logs

1. **API** : Dashboard → deme-api → Logs
   - Tu dois voir : `Application startup complete.`

2. **Worker** : Dashboard → deme-worker → Logs
   - Tu dois voir : `celery@... ready.`

### B. Tester l'API

```bash
# Récupère l'URL de ton API (ex: https://deme-api.onrender.com)

# Test de santé
curl https://deme-api.onrender.com/

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
  "task_id": "xxx-xxx-xxx",
  "message": "Demande de prestation enregistrée avec succès."
}
```

### C. Vérifier dans Notion / Calendar / Sheets

- ✅ Client créé dans Notion
- ✅ Prestation créée
- ✅ Lignes de devis
- ✅ Événement Google Calendar
- ✅ Devis Google Sheet

---

## 📋 ÉTAPE 6 : Livrer à DéMé

### A. Donner l'accès au workspace Notion

1. Transfert de propriété du compte `gestion.deme@proton.io`
   - OU partager toutes les bases avec son compte Notion personnel

### B. Fournir l'URL du webhook

```
URL : https://deme-api.onrender.com/api/packs/deme-traiteur/webhook
Method : POST
Content-Type : application/json
```

### C. Intégration sur son site web

Code à fournir à DéMé (voir fichier INTEGRATION_SITE.html créé séparément)

---

## 🔧 MAINTENANCE

### Cold Start (15min d'inactivité)

Render Free met en veille après 15min. Premier appel = 30-60s de réveil.

**Solution** : Ajouter un cron job gratuit pour ping l'API toutes les 10 minutes.

**Option 1 : Cron-job.org (gratuit)**
1. Va sur https://cron-job.org
2. Crée un compte
3. Ajoute un job :
   - URL : `https://deme-api.onrender.com/`
   - Interval : Toutes les 10 minutes
   - ✅ L'API reste toujours réveillée

**Option 2 : UptimeRobot (gratuit)**
1. Va sur https://uptimerobot.com
2. Crée un monitor HTTP(s)
3. URL : `https://deme-api.onrender.com/`
4. Interval : 5 minutes

### Logs et Monitoring

- **Logs** : Dashboard Render → Logs en temps réel
- **Erreurs** : Render envoie des emails si l'app crash

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

- **Render** : 0€ (Free tier)
- **Upstash Redis** : 0€ (Free tier - 10k commandes/jour)
- **Total** : **0€/mois** 🎉

---

## ❓ TROUBLESHOOTING

### Erreur : "Service Unavailable"
→ L'app est en train de se réveiller (cold start), attends 60s

### Erreur : Connection to Notion failed
→ Vérifie que les variables d'env sont bien configurées
→ Vérifie que l'intégration Notion a accès aux bases

### Erreur : Redis connection refused
→ Vérifie l'URL Redis Upstash dans les variables d'env
→ Format : `rediss://` (avec double 's')

### Worker ne démarre pas
→ Check les logs : Dashboard → deme-worker → Logs
→ Vérifie que toutes les variables d'env sont identiques à l'API

---

## 🎯 PROCHAINES ÉTAPES

1. [ ] Tester avec une vraie prestation
2. [ ] Documenter pour DéMé
3. [ ] Setup cron job pour éviter le cold start
4. [ ] Monitorer les premières semaines

---

**Félicitations ! DéMé Traiteur est en production ! 🚀**
