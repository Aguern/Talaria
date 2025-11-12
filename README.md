# Talaria

Plateforme iPaaS (Integration Platform as a Service) modulaire pour la construction et le déploiement de solutions d'automatisation de workflows personnalisés. Talaria propose une architecture basée sur des plugins où des "packs" spécialisés gèrent la logique métier spécifique à chaque domaine, tandis que le système central assure l'authentification, le multi-tenancy, l'orchestration et l'exécution.

## Vue d'ensemble

Talaria est conçue comme une plateforme d'automatisation flexible qui peut s'adapter à divers domaines métier grâce à son système modulaire de packs. Chaque pack est autonome avec sa propre logique, ses routes API et sa configuration, ce qui rend la plateforme facilement extensible pour de nouveaux cas d'usage.

Fonctionnalités principales :
- Architecture plugin avec découverte automatique des packs via manifests JSON
- Isolation des données multi-tenant
- Workflows IA conversationnels avec support human-in-the-loop
- Orchestration basée sur LangGraph pour des machines à états complexes
- API RESTful avec support streaming (Server-Sent Events)
- Architecture async-first (FastAPI + SQLAlchemy async)
- PostgreSQL avec pgvector pour la recherche sémantique
- Interface web moderne construite avec Next.js 15 et React 19

## Stack technique

### Backend
- Framework : FastAPI avec uvicorn
- Base de données : PostgreSQL 15 avec extension pgvector
- ORM : SQLAlchemy 2.0 (mode async avec driver asyncpg)
- Orchestration IA : LangGraph avec persistence des checkpoints
- Intégration LLM : OpenAI GPT-4o via langchain-openai
- Tâches background : Celery avec Redis (optionnel, fallback vers FastAPI BackgroundTasks)
- Authentification : Tokens JWT avec hashing Argon2
- Logging : structlog avec contextvars pour le traçage des requêtes
- Recherche vectorielle : sentence-transformers avec stockage pgvector

### Frontend
- Framework : Next.js 15.4 (App Router)
- UI Library : React 19.1
- Composants UI : Radix UI primitives (shadcn/ui)
- Styling : TailwindCSS 4
- Gestion d'état : Zustand + TanStack Query v5
- Formulaires : React Hook Form avec validation Zod
- Type Safety : TypeScript 5 (strict mode)

### DevOps
- Conteneurisation : Docker avec builds multi-stages
- Déploiement : Render.com (configuré via render.yaml)
- CI/CD : GitHub Actions
- Gestion environnement : pydantic-settings avec support .env

## Structure du projet

```
/
├── app/                          # Application backend Python
│   ├── core/                     # Modules système centraux
│   │   ├── auth.py              # Authentification JWT & hashing Argon2
│   │   ├── database.py          # Configuration SQLAlchemy async
│   │   ├── models.py            # Modèles de base (Users, Tenants, Documents)
│   │   ├── orchestrator.py      # Découverte et moteur d'exécution des packs
│   │   ├── engine.py            # Modèles ML & client embedding
│   │   └── logging_config.py    # Configuration logging structuré
│   ├── packs/                   # Packs de logique métier modulaire
│   │   ├── deme_traiteur/       # Automatisation workflow traiteur (production)
│   │   ├── form_3916/           # Traitement formulaire fiscal français
│   │   └── bofip/               # Système RAG code fiscal français
│   ├── tools/                   # Outils IA réutilisables
│   │   ├── document_classifier.py
│   │   ├── document_parser.py
│   │   ├── data_extractor.py
│   │   ├── pdf_filler.py
│   │   └── pdf_generator.py
│   ├── api/                     # Endpoints API
│   │   ├── recipes.py           # API d'exécution des packs
│   │   └── chat.py              # Interface conversationnelle
│   ├── tests/                   # Suite de tests
│   │   ├── core/
│   │   ├── packs/
│   │   └── tools/
│   ├── mcp_server/              # Serveur Model Context Protocol
│   └── main.py                  # Point d'entrée application FastAPI
│
├── frontend/                     # Interface web Next.js
│   └── src/
│       ├── app/                 # Pages Next.js (App Router)
│       ├── components/          # Composants React
│       │   ├── ui/             # Composants shadcn/ui
│       │   ├── recipes/        # Composants liés aux packs
│       │   ├── tasks/          # Statut et résultats des tâches
│       │   ├── chat/           # Interface conversationnelle
│       │   └── forms/          # Génération dynamique de formulaires
│       └── hooks/              # Hooks React personnalisés
│
├── docker-compose.yml           # Orchestration développement local
├── Dockerfile                   # Image container production
├── render.yaml                  # Configuration déploiement Render
├── requirements.txt             # Dépendances Python
└── requirements-render.txt      # Dépendances optimisées pour déploiement
```

## Packs disponibles

### 1. DéMé Traiteur (Production)
Domaine : Gestion traiteur et événementiel
Statut : Déploiement production avec client réel

Automatisation end-to-end pour les demandes de prestation traiteur :
- Intégration webhook pour soumissions de formulaire web
- Synchronisation base de données Notion (Clients, Prestations, Lignes de devis)
- Création d'événements Google Calendar avec descriptions enrichies
- Génération de devis Google Sheets avec système de pooling de templates
- Notifications email via Gmail API avec refresh automatique des tokens OAuth2
- Mode d'exécution dual (worker Celery ou FastAPI BackgroundTasks)

Intégrations : Notion API, Google Calendar API, Google Drive API, Google Sheets API, Gmail API

### 2. Form 3916 Processor
Domaine : Traitement de documents fiscaux (formulaire fiscal français)

Workflow LangGraph avec human-in-the-loop pour le remplissage de formulaire fiscal multi-documents :
- Classification de documents (cartes d'identité, relevés bancaires, RIB, etc.)
- Parsing de documents multi-pages avec PyMuPDF
- Extraction de données structurées via GPT-5-mini avec schémas Pydantic
- Consolidation des champs et détection des données manquantes
- Complétion de formulaire interactive via interface conversationnelle
- Génération PDF avec ReportLab (sortie multi-pages coordonnée)

Technologies : LangGraph StateGraph, OpenAI structured outputs, PyMuPDF, ReportLab

### 3. BOFIP RAG System
Domaine : Base de connaissances code fiscal français

Système de recherche hybride pour questions-réponses sur la législation fiscale française :
- Recherche full-text avec indexes PostgreSQL tsvector
- Recherche sémantique via pgvector et embeddings multilingues
- Fusion des résultats avec Reciprocal Rank Fusion (RRF)
- Re-ranking avec CrossEncoder (BAAI/bge-reranker-base)
- Génération de réponses GPT-5-mini avec citations des sources

Technologies : pgvector, sentence-transformers, CrossEncoder, patterns RAG LangChain

## Installation

### Prérequis
- Python 3.11+
- Node.js 20+
- PostgreSQL 15+ avec extension pgvector
- Docker & Docker Compose (pour développement local)
- Redis (optionnel, pour mode Celery)

### Configuration développement local

1. Cloner le repository
```bash
git clone <repository-url>
cd Talaria
```

2. Configuration Backend
```bash
# Créer environnement virtuel
python -m venv venv
source venv/bin/activate  # Sur Windows: venv\Scripts\activate

# Installer dépendances
pip install -r requirements.txt

# Configurer variables d'environnement
cp .env.example .env
# Éditer .env avec vos credentials (clé API OpenAI, URL base de données, etc.)
```

3. Configuration Base de données
```bash
# Démarrer PostgreSQL avec pgvector via Docker
docker-compose up -d db

# Les tables sont créées automatiquement au premier lancement
```

4. Configuration Frontend
```bash
cd frontend
npm install
npm run dev
```

5. Lancer l'application
```bash
# Backend (depuis le répertoire racine)
uvicorn app.main:app --reload --port 8000

# Frontend (déjà lancé à l'étape 4)
# Accessible sur http://localhost:3000
```

### Docker Compose (Full Stack)
```bash
# Démarrer tous les services (API, DB, Redis, Worker, Service Embedding)
docker-compose up -d

# Voir les logs
docker-compose logs -f api

# Arrêter tous les services
docker-compose down
```

## Configuration

### Variables d'environnement

Variables clés (voir .env.example pour la liste complète) :

```bash
# Base de données
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/talaria

# Authentification
SECRET_KEY=your-secret-key-here
FERNET_KEY=your-fernet-encryption-key

# OpenAI
OPENAI_API_KEY=sk-...

# Celery (optionnel)
CELERY_BROKER_URL=redis://localhost:6379/0

# Variables spécifiques aux packs (Notion, Google APIs, etc.)
```

### Configuration des packs

Chaque pack inclut un fichier manifest.json définissant :
- Schémas input/output
- Credentials API requises
- Métadonnées du pack (nom, description, version)

Les packs sont automatiquement découverts au démarrage en scannant app/packs/*/manifest.json.

## Utilisation

### Endpoints API

Authentification :
- POST /users - Créer un compte utilisateur
- POST /token - Login et obtention token JWT
- GET /users/me - Récupérer informations utilisateur courant

Exécution de packs :
- GET /api/recipes/ - Lister les packs disponibles
- POST /api/recipes/{id}/execute - Exécuter un pack avec upload de fichiers
- GET /api/recipes/tasks/{task_id} - Interroger le statut d'une tâche
- POST /api/recipes/tasks/{task_id}/human-input - Soumettre une entrée human-in-the-loop

Interface conversationnelle :
- POST /api/chat/message - Envoyer un message (streaming Server-Sent Events)
- GET /api/conversations - Lister les conversations utilisateur
- POST /api/conversations - Créer une nouvelle conversation

Endpoints spécifiques aux packs :
- /api/packs/deme-traiteur/webhook - Webhook pour soumissions formulaire traiteur
- /api/packs/form-3916/* - Endpoints traitement Form 3916
- /api/packs/bofip/query - Endpoint requête RAG pour questions code fiscal

### Exemple : Exécuter un pack

```bash
# Authentification
curl -X POST http://localhost:8000/token \
  -d "username=user@example.com&password=yourpassword"

# Exécuter le pack DéMé Traiteur
curl -X POST http://localhost:8000/api/recipes/deme_traiteur/execute \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "nom_complet": "Jean Dupont",
    "email": "jean@example.com",
    "telephone": "0612345678",
    "date": "2025-12-25",
    "pax": 30,
    "moment": "Déjeuner",
    "options": ["Entrées", "Plats chauds"]
  }'
```

## Tests

### Tests Backend
```bash
# Lancer tous les tests
pytest

# Lancer un module de test spécifique
pytest app/tests/packs/test_form_3916_graph.py

# Avec couverture
pytest --cov=app --cov-report=html
```

### Tests Frontend
```bash
cd frontend

# Lancer tests unitaires (Vitest)
npm run test:unit

# Lancer tests E2E (Playwright)
npm run test:e2e

# Lancer tous les tests
npm run test:all
```

## Déploiement

### Render.com (Production)

Le projet inclut un blueprint render.yaml pour déploiement en un clic :

1. Push le code sur GitHub
2. Connecter le repository à Render
3. Configurer les variables d'environnement dans le dashboard Render
4. Déployer via Render Blueprint

Services créés :
- Web Service : API FastAPI (deme-api)
- PostgreSQL Database : 15 avec pgvector (deme-db)

Optimisation pour Render Free Tier :
- Mode Celery désactivé (utilise FastAPI BackgroundTasks)
- Service embedding désactivé si non requis
- Template pooling pour opérations Google Drive pour éviter les limites de quota

### Déploiement Docker manuel
```bash
# Construire image production
docker build -t talaria-api -f Dockerfile .

# Lancer avec fichier environnement
docker run -d -p 8000:8000 --env-file .env talaria-api
```

## Patterns d'architecture

### Système plugin
Les packs sont découverts automatiquement via fichiers manifest.json. L'orchestrateur charge les métadonnées des packs et route les requêtes dynamiquement.

### Human-in-the-loop
Les workflows LangGraph peuvent interrompre l'exécution et attendre une entrée utilisateur via l'interface conversationnelle. L'état est persisté via les checkpoints LangGraph.

### Multi-tenancy
Toutes les opérations de données sont filtrées par tenant_id. Les utilisateurs appartiennent à des tenants, et les requêtes de base de données sont automatiquement scopées au tenant de l'utilisateur courant.

### Mode d'exécution dual
Le système détecte la présence de CELERY_BROKER_URL et bascule entre :
- Mode Celery : Tâches background exécutées par des processus worker séparés
- Mode Direct : Tâches exécutées inline via FastAPI BackgroundTasks (adapté aux tiers gratuits d'hébergement)

## Model Context Protocol (MCP)

Le projet inclut une implémentation serveur MCP (app/mcp_server/) pour intégration avec Claude Desktop. Cela permet un accès direct aux packs Talaria depuis l'interface Claude.

## Documentation technique

Des case studies techniques détaillées sont disponibles pour chaque pack :
- docs/CASE_STUDY_DEME_TRAITEUR.md - Workflow production avec intégrations multi-API
- docs/CASE_STUDY_FORM_3916.md - Traitement documents conversationnel avec LangGraph
- docs/CASE_STUDY_BOFIP_RAG.md - Système RAG hybride avec re-ranking

## Licence

Copyright (c) 2025 [Nicolas Angougeard]. Tous droits réservés.

Ce projet est un portfolio technique personnel. Le code source est fourni à titre de démonstration uniquement et n'est pas destiné à une utilisation commerciale par des tiers sans autorisation expresse.
