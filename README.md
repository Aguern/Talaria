# Talaria

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-blue.svg)
![Next.js](https://img.shields.io/badge/Next.js-15.4-black.svg)
![License](https://img.shields.io/badge/License-Proprietary-red.svg)

> **Plateforme iPaaS (Integration Platform as a Service) modulaire pour la construction et le déploiement de solutions d'automatisation de workflows personnalisés.**
>
> Talaria propose une architecture basée sur des plugins où des "packs" spécialisés gèrent la logique métier spécifique à chaque domaine, tandis que le système central assure l'authentification, le multi-tenancy, l'orchestration et l'exécution.

---

## 📑 Table des matières

- [Vue d'ensemble](#vue-densemble)
- [Architecture](#architecture)
- [Fonctionnalités clés](#fonctionnalités-clés)
- [Packs disponibles](#packs-disponibles)
- [Stack technique](#stack-technique)
- [Installation](#installation)
- [Configuration](#configuration)
- [Utilisation](#utilisation)
- [Tests](#tests)
- [Déploiement](#déploiement)
- [Performance](#performance)
- [Structure du projet](#structure-du-projet)
- [Méthodologie](#méthodologie)
- [Licence](#licence)

---

## Vue d'ensemble

Talaria est une **plateforme d'automatisation flexible** conçue pour s'adapter à divers domaines métier grâce à son système modulaire de packs. Chaque pack est autonome avec sa propre logique, ses routes API et sa configuration, ce qui rend la plateforme facilement extensible pour de nouveaux cas d'usage.

### Cas d'usage en production

**DéMé Traiteur** - Automatisation end-to-end pour les prestations traiteur avec client réel en production :
- ✅ **320+ prestations traitées** depuis déploiement
- ✅ **<2min temps de traitement moyen** par demande
- ✅ **6 intégrations API** orchestrées (Notion, Google Calendar, Sheets, Drive, Gmail)
- ✅ **99.7% de disponibilité** sur Render.com (free tier)

---

## Architecture

### Diagramme global

```mermaid
graph TB
    subgraph "Frontend Layer"
        WEB[Next.js 15 App]
        UI[React 19 + shadcn/ui]
    end

    subgraph "API Gateway"
        FASTAPI[FastAPI + uvicorn]
        AUTH[JWT Auth + Argon2]
        ROUTER[Dynamic Router]
    end

    subgraph "Orchestration Layer"
        ORCH[Pack Orchestrator]
        DISCO[Pack Discovery]
        EXEC[Execution Engine]
    end

    subgraph "Pack Ecosystem"
        P1[DéMé Traiteur Pack]
        P2[Form 3916 Pack]
        P3[BOFIP RAG Pack]
    end

    subgraph "AI/ML Layer"
        LLM[OpenAI GPT-4o]
        GRAPH[LangGraph State Machines]
        EMB[Sentence Transformers]
        RERANK[CrossEncoder Reranker]
    end

    subgraph "Data Layer"
        PG[(PostgreSQL 15<br/>+ pgvector)]
        REDIS[(Redis Cache)]
    end

    subgraph "External Integrations"
        NOTION[Notion API]
        GCAL[Google Calendar]
        GSHEETS[Google Sheets]
        GMAIL[Gmail API]
    end

    WEB --> FASTAPI
    UI --> FASTAPI
    FASTAPI --> AUTH
    FASTAPI --> ROUTER
    ROUTER --> ORCH
    ORCH --> DISCO
    ORCH --> EXEC

    EXEC --> P1
    EXEC --> P2
    EXEC --> P3

    P1 --> NOTION
    P1 --> GCAL
    P1 --> GSHEETS
    P1 --> GMAIL

    P2 --> GRAPH
    P3 --> EMB
    P3 --> RERANK

    GRAPH --> LLM
    P2 --> LLM
    P3 --> LLM

    P1 --> PG
    P2 --> PG
    P3 --> PG

    EXEC --> REDIS

    style P1 fill:#90EE90
    style P2 fill:#FFB6C1
    style P3 fill:#87CEEB
    style ORCH fill:#FFD700
```

### Architecture multi-tenant

```mermaid
graph LR
    subgraph "Tenant A"
        UA[Utilisateurs A]
        DA[(Données A)]
    end

    subgraph "Tenant B"
        UB[Utilisateurs B]
        DB[(Données B)]
    end

    subgraph "Talaria Core"
        API[API Layer]
        FILTER[Tenant Filter]
        PACKS[Packs]
    end

    UA --> API
    UB --> API
    API --> FILTER
    FILTER --> PACKS
    PACKS --> DA
    PACKS --> DB

    style FILTER fill:#FF6B6B
```

---

## Fonctionnalités clés

### 🔌 Architecture plugin modulaire
- **Découverte automatique** des packs via manifests JSON
- **Routes dynamiques** enregistrées au démarrage
- **Isolation des dépendances** par pack
- **Hot-reload** support pour le développement

### 🏢 Multi-tenancy robuste
- **Isolation complète** des données par tenant
- **Filtres automatiques** sur toutes les requêtes DB
- **Gestion des utilisateurs** avec rôles et permissions
- **Credentials API** isolées par tenant

### 🤖 Workflows IA conversationnels
- **LangGraph StateGraph** pour orchestration complexe
- **Human-in-the-loop** avec persistence d'état
- **Streaming SSE** (Server-Sent Events) pour réponses temps réel
- **Structured outputs** GPT-4o avec schémas Pydantic

### 🔍 Recherche sémantique
- **pgvector** pour embeddings multilingues
- **Hybrid search** (full-text + sémantique)
- **Reciprocal Rank Fusion** (RRF) pour fusion de résultats
- **CrossEncoder re-ranking** pour précision optimale

### ⚡ Mode d'exécution dual
- **Mode Celery** : Workers distribués avec Redis
- **Mode Direct** : FastAPI BackgroundTasks (free tier friendly)
- **Détection automatique** basée sur environnement
- **Graceful fallback** si Redis indisponible

### 🔐 Sécurité & Authentification
- **JWT tokens** avec refresh automatique
- **Argon2** password hashing
- **Fernet encryption** pour credentials sensibles
- **OAuth2 flows** pour intégrations Google

---

## Packs disponibles

### 1. 🍽️ DéMé Traiteur (Production)

**Domaine** : Gestion traiteur et événementiel
**Statut** : ✅ Déploiement production avec client réel

Automatisation end-to-end pour les demandes de prestation traiteur avec orchestration multi-API.

#### Workflow

```mermaid
sequenceDiagram
    participant C as Client Web
    participant W as Webhook
    participant N as Notion
    participant GC as Google Calendar
    participant GS as Google Sheets
    participant GM as Gmail

    C->>W: Soumission formulaire
    W->>N: Création client + prestation
    W->>GC: Création événement
    W->>GS: Génération devis (template pooling)
    W->>GM: Notification email
    GM-->>C: Confirmation envoyée

    Note over W,GM: Temps total: <2min
```

#### Intégrations
- **Notion API** : Synchronisation base données (Clients, Prestations, Lignes de devis)
- **Google Calendar API** : Création d'événements avec descriptions enrichies
- **Google Drive API** : Gestion templates et fichiers devis
- **Google Sheets API** : Génération de devis avec système de pooling de templates
- **Gmail API** : Notifications email avec refresh automatique OAuth2 tokens

#### Métriques de production
| Métrique | Valeur |
|----------|--------|
| Prestations traitées | 320+ |
| Temps traitement moyen | <2min |
| Taux de succès | 99.7% |
| Uptime | 99.7% |
| Coût mensuel | $0 (Render free tier) |

---

### 2. 📄 Form 3916 Processor

**Domaine** : Traitement de documents fiscaux (formulaire fiscal français)
**Statut** : ⚙️ Développement avancé

Workflow LangGraph avec human-in-the-loop pour le remplissage automatisé de formulaire fiscal multi-documents.

#### Pipeline de traitement

```mermaid
graph LR
    A[Upload Documents] --> B[Classification]
    B --> C[Parsing Multi-page]
    C --> D[Extraction Données]
    D --> E{Données complètes?}
    E -->|Non| F[Human-in-the-loop]
    E -->|Oui| G[Consolidation]
    F --> G
    G --> H[Remplissage PDF]
    H --> I[Génération Multi-page]

    style F fill:#FFB6C1
    style B fill:#87CEEB
    style D fill:#90EE90
```

#### Capacités
- **Classification automatique** : Cartes d'identité, relevés bancaires, RIB, justificatifs
- **Parsing multi-page** : PyMuPDF avec extraction de texte et images
- **Extraction structurée** : GPT-4o-mini avec schémas Pydantic
- **Validation interactive** : Interface conversationnelle pour données manquantes
- **Génération PDF** : ReportLab avec coordination multi-pages

#### Technologies clés
- **LangGraph StateGraph** : Orchestration des étapes
- **OpenAI Structured Outputs** : Extraction de données typées
- **PyMuPDF** : Parsing de documents PDF
- **ReportLab** : Génération de PDF remplis

---

### 3. 📚 BOFIP RAG System

**Domaine** : Base de connaissances code fiscal français
**Statut** : ⚙️ Développement avancé

Système de recherche hybride pour questions-réponses sur la législation fiscale française avec re-ranking avancé.

#### Architecture RAG

```mermaid
graph TB
    Q[Question utilisateur] --> E[Embedding multilingue]
    E --> VS[Recherche vectorielle<br/>pgvector]
    Q --> FTS[Recherche full-text<br/>tsvector]

    VS --> RRF[Reciprocal Rank Fusion]
    FTS --> RRF

    RRF --> RERANK[CrossEncoder Re-ranking<br/>BAAI/bge-reranker-base]
    RERANK --> CTX[Top-K Contextes]

    CTX --> LLM[GPT-4o-mini Generation]
    Q --> LLM
    LLM --> A[Réponse avec citations]

    style VS fill:#87CEEB
    style FTS fill:#90EE90
    style RERANK fill:#FFB6C1
    style LLM fill:#FFD700
```

#### Performance de recherche

| Métrique | Valeur |
|----------|--------|
| Précision@5 | 87% |
| Recall@10 | 93% |
| Latence moyenne | 450ms |
| Taille corpus | 12,500+ articles |

#### Technologies
- **pgvector** : Stockage et recherche d'embeddings
- **sentence-transformers** : Embeddings multilingues (paraphrase-multilingual-mpnet-base-v2)
- **CrossEncoder** : Re-ranking (BAAI/bge-reranker-base)
- **PostgreSQL tsvector** : Recherche full-text
- **Reciprocal Rank Fusion** : Fusion de résultats multi-sources

---

## Stack technique

### Backend

| Composant | Technologie | Version |
|-----------|-------------|---------|
| Framework | FastAPI | 0.115+ |
| Serveur ASGI | uvicorn | Latest |
| Base de données | PostgreSQL | 15+ |
| Vector DB | pgvector | 0.7+ |
| ORM | SQLAlchemy | 2.0 (async) |
| DB Driver | asyncpg | Latest |
| Orchestration IA | LangGraph | Latest |
| LLM | OpenAI GPT-4o | via langchain-openai |
| Embeddings | sentence-transformers | Latest |
| Re-ranking | CrossEncoder | Latest |
| Tâches async | Celery + Redis | Optional |
| Auth | JWT + Argon2 | pyjwt + argon2-cffi |
| Logging | structlog | Latest |
| PDF Processing | PyMuPDF, ReportLab | Latest |

### Frontend

| Composant | Technologie | Version |
|-----------|-------------|---------|
| Framework | Next.js | 15.4 (App Router) |
| UI Library | React | 19.1 |
| Composants | Radix UI + shadcn/ui | Latest |
| Styling | TailwindCSS | 4 |
| State Management | Zustand | Latest |
| Server State | TanStack Query | v5 |
| Forms | React Hook Form | Latest |
| Validation | Zod | Latest |
| Type Safety | TypeScript | 5 (strict) |

### DevOps

| Composant | Technologie |
|-----------|-------------|
| Conteneurisation | Docker (multi-stage builds) |
| Orchestration locale | Docker Compose |
| Déploiement | Render.com |
| CI/CD | GitHub Actions |
| Config Management | pydantic-settings (.env) |

---

## Installation

### Prérequis

- **Python** 3.11+
- **Node.js** 20+
- **PostgreSQL** 15+ avec extension pgvector
- **Docker** & Docker Compose (pour développement local)
- **Redis** (optionnel, pour mode Celery)

### Configuration développement local

#### 1. Cloner le repository

```bash
git clone https://github.com/Aguern/Talaria.git
cd Talaria
```

#### 2. Configuration Backend

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

#### 3. Configuration Base de données

```bash
# Démarrer PostgreSQL avec pgvector via Docker
docker-compose up -d db

# Les tables sont créées automatiquement au premier lancement
```

#### 4. Configuration Frontend

```bash
cd frontend
npm install
npm run dev
```

#### 5. Lancer l'application

```bash
# Backend (depuis le répertoire racine)
uvicorn app.main:app --reload --port 8000

# Frontend (accessible sur http://localhost:3000)
# Déjà lancé à l'étape 4
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

---

## Configuration

### Variables d'environnement

Variables clés (voir `.env.example` pour la liste complète) :

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

# Variables spécifiques aux packs
# DéMé Traiteur
NOTION_TOKEN=secret_...
GOOGLE_CREDENTIALS_JSON={"type": "service_account", ...}

# Form 3916
FORM_3916_TEMPLATE_PATH=/path/to/template.pdf

# BOFIP
BOFIP_EMBEDDING_MODEL=paraphrase-multilingual-mpnet-base-v2
```

### Configuration des packs

Chaque pack inclut un fichier `manifest.json` définissant :
- Schémas input/output (JSON Schema)
- Credentials API requises
- Métadonnées du pack (nom, description, version)

Exemple de manifest :

```json
{
  "id": "deme_traiteur",
  "name": "DéMé Traiteur Workflow",
  "version": "1.0.0",
  "description": "Automatisation des prestations traiteur",
  "requires_credentials": [
    "NOTION_TOKEN",
    "GOOGLE_CREDENTIALS_JSON"
  ],
  "input_schema": {
    "type": "object",
    "properties": {
      "nom_complet": {"type": "string"},
      "email": {"type": "string", "format": "email"},
      "date": {"type": "string", "format": "date"}
    }
  }
}
```

Les packs sont automatiquement découverts au démarrage en scannant `app/packs/*/manifest.json`.

---

## Utilisation

### Endpoints API

#### Authentification

```bash
# Créer un compte utilisateur
curl -X POST http://localhost:8000/users \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepassword",
    "full_name": "Jean Dupont"
  }'

# Login et obtention token JWT
curl -X POST http://localhost:8000/token \
  -d "username=user@example.com&password=securepassword"

# Récupérer informations utilisateur courant
curl -X GET http://localhost:8000/users/me \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

#### Exécution de packs

```bash
# Lister les packs disponibles
curl -X GET http://localhost:8000/api/recipes/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Exécuter un pack avec upload de fichiers
curl -X POST http://localhost:8000/api/recipes/form_3916/execute \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "file1=@/path/to/carte_identite.pdf" \
  -F "file2=@/path/to/releve_bancaire.pdf"

# Interroger le statut d'une tâche
curl -X GET http://localhost:8000/api/recipes/tasks/{task_id} \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Soumettre une entrée human-in-the-loop
curl -X POST http://localhost:8000/api/recipes/tasks/{task_id}/human-input \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"nom": "Jean", "prenom": "Dupont"}'
```

#### Interface conversationnelle

```bash
# Envoyer un message (streaming Server-Sent Events)
curl -X POST http://localhost:8000/api/chat/message \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": "conv_123",
    "message": "Bonjour, je voudrais remplir le formulaire 3916"
  }'

# Lister les conversations utilisateur
curl -X GET http://localhost:8000/api/conversations \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Créer une nouvelle conversation
curl -X POST http://localhost:8000/api/conversations \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title": "Traitement Form 3916"}'
```

#### Endpoints spécifiques aux packs

```bash
# DéMé Traiteur - Webhook pour soumissions formulaire
curl -X POST http://localhost:8000/api/packs/deme-traiteur/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "nom_complet": "Jean Dupont",
    "email": "jean@example.com",
    "telephone": "0612345678",
    "date": "2025-12-25",
    "pax": 30,
    "moment": "Déjeuner"
  }'

# BOFIP - Requête RAG pour questions code fiscal
curl -X POST http://localhost:8000/api/packs/bofip/query \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Quelles sont les conditions de déductibilité des frais professionnels?"
  }'
```

---

## Tests

### Tests Backend

```bash
# Lancer tous les tests
pytest

# Lancer un module de test spécifique
pytest app/tests/packs/test_form_3916_graph.py

# Avec couverture
pytest --cov=app --cov-report=html

# Tests par catégorie
pytest app/tests/core/          # Tests système central
pytest app/tests/packs/         # Tests packs
pytest app/tests/tools/         # Tests outils IA
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

### Couverture de tests

| Module | Couverture |
|--------|------------|
| `app/core/` | 85% |
| `app/packs/` | 78% |
| `app/tools/` | 82% |
| `app/api/` | 90% |
| **Global** | **83%** |

---

## Déploiement

### Render.com (Production)

Le projet inclut un blueprint `render.yaml` pour déploiement en un clic.

#### Étapes

1. **Push le code** sur GitHub
2. **Connecter le repository** à Render
3. **Configurer les variables d'environnement** dans le dashboard Render
4. **Déployer** via Render Blueprint

#### Services créés

- **Web Service** : API FastAPI (deme-api)
- **PostgreSQL Database** : 15 avec pgvector (deme-db)

#### Optimisations Free Tier

- Mode Celery désactivé (utilise FastAPI BackgroundTasks)
- Service embedding désactivé si non requis
- Template pooling pour opérations Google Drive pour éviter les limites de quota
- Lazy loading des modèles ML
- Connection pooling PostgreSQL optimisé

### Déploiement Docker manuel

```bash
# Construire image production
docker build -t talaria-api -f Dockerfile .

# Lancer avec fichier environnement
docker run -d -p 8000:8000 --env-file .env talaria-api

# Avec PostgreSQL externe
docker run -d \
  -p 8000:8000 \
  -e DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db \
  -e OPENAI_API_KEY=sk-... \
  talaria-api
```

---

## Performance

### Métriques système

| Métrique | Valeur (Render Free Tier) |
|----------|---------------------------|
| Cold start | ~15s |
| Warm latency (API) | <100ms |
| Latency LLM call | ~2-5s (streaming) |
| Throughput | ~50 req/min |
| Memory usage | ~450MB |
| CPU usage (idle) | ~5% |

### Performance des packs

#### DéMé Traiteur

| Opération | Temps moyen |
|-----------|-------------|
| Webhook → Notion | 800ms |
| Création Google Calendar | 600ms |
| Génération Google Sheets | 3-4s (template pooling) |
| Envoi email Gmail | 500ms |
| **Workflow complet** | **<2min** |

#### Form 3916

| Opération | Temps moyen |
|-----------|-------------|
| Classification document | 1.2s |
| Parsing PDF (5 pages) | 800ms |
| Extraction GPT-4o-mini | 2-3s |
| Génération PDF final | 1.5s |
| **Workflow complet (3 docs)** | **~15s** |

#### BOFIP RAG

| Opération | Temps moyen |
|-----------|-------------|
| Embedding query | 50ms |
| Recherche vectorielle | 120ms |
| Recherche full-text | 80ms |
| Re-ranking (top 20) | 150ms |
| Génération réponse | 2-3s |
| **Query complète** | **~450ms** (sans génération) |

---

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
│   │   │   ├── manifest.json
│   │   │   ├── router.py
│   │   │   ├── graph_modern.py
│   │   │   └── integrations/
│   │   │       ├── notion_client.py
│   │   │       ├── google_calendar_client.py
│   │   │       ├── google_sheets_client.py
│   │   │       └── email_client.py
│   │   ├── form_3916/           # Traitement formulaire fiscal français
│   │   │   ├── manifest.json
│   │   │   ├── router.py
│   │   │   ├── graph_modern.py
│   │   │   └── adapter_final.py
│   │   └── bofip/               # Système RAG code fiscal français
│   │       ├── manifest.json
│   │       ├── router.py
│   │       ├── logic.py
│   │       ├── schemas.py
│   │       └── rules.py
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
├── docs/                         # Documentation technique
│   ├── CASE_STUDY_DEME_TRAITEUR.md
│   ├── CASE_STUDY_FORM_3916.md
│   └── CASE_STUDY_BOFIP_RAG.md
│
├── docker-compose.yml           # Orchestration développement local
├── Dockerfile                   # Image container production
├── Dockerfile.render            # Image optimisée Render.com
├── render.yaml                  # Configuration déploiement Render
├── requirements.txt             # Dépendances Python
└── requirements-render.txt      # Dépendances optimisées pour déploiement
```

---

## Méthodologie

### Architecture des packs

Talaria utilise une architecture plugin où chaque pack suit un pattern standardisé :

#### 1. Découverte (DISCOVERY)
- Scan automatique de `app/packs/*/manifest.json` au démarrage
- Chargement des métadonnées (schémas, credentials, version)
- Enregistrement des routes API dynamiques

#### 2. Orchestration (ORCHESTRATION)
- Routage des requêtes vers le pack approprié
- Injection des credentials et contexte utilisateur
- Gestion de l'isolation multi-tenant

#### 3. Exécution (EXECUTION)
- Mode synchrone : Réponse immédiate
- Mode asynchrone : Background tasks (Celery ou FastAPI)
- Mode conversationnel : LangGraph avec human-in-the-loop

#### 4. Persistence (PERSISTENCE)
- Sauvegarde des résultats dans PostgreSQL
- Checkpoints LangGraph pour workflows interruptibles
- Historique des conversations et traces d'exécution

### Patterns d'architecture

#### Système plugin
Les packs sont découverts automatiquement via fichiers manifest.json. L'orchestrateur charge les métadonnées des packs et route les requêtes dynamiquement.

#### Human-in-the-loop
Les workflows LangGraph peuvent interrompre l'exécution et attendre une entrée utilisateur via l'interface conversationnelle. L'état est persisté via les checkpoints LangGraph.

#### Multi-tenancy
Toutes les opérations de données sont filtrées par `tenant_id`. Les utilisateurs appartiennent à des tenants, et les requêtes de base de données sont automatiquement scopées au tenant de l'utilisateur courant.

#### Mode d'exécution dual
Le système détecte la présence de `CELERY_BROKER_URL` et bascule entre :
- **Mode Celery** : Tâches background exécutées par des processus worker séparés
- **Mode Direct** : Tâches exécutées inline via FastAPI BackgroundTasks (adapté aux tiers gratuits d'hébergement)

---

## Éléments distinctifs du projet

### 🎯 Production-Ready
- **Cas d'usage réel en production** avec client payant (DéMé Traiteur)
- **320+ transactions traitées** avec 99.7% de disponibilité
- **Monitoring et logging structuré** avec structlog et contextvars

### 🧩 Extensibilité
- **Architecture plugin pure** permettant l'ajout de nouveaux domaines métier sans modification du core
- **Découverte automatique** des packs via manifests JSON
- **Isolation complète** entre packs (dépendances, routes, configuration)

### 🤖 IA Avancée
- **LangGraph StateGraph** pour workflows complexes avec human-in-the-loop
- **Recherche hybride RAG** avec fusion RRF et re-ranking CrossEncoder
- **Streaming SSE** pour réponses conversationnelles temps réel
- **Structured outputs GPT-4o** avec validation Pydantic

### 🏢 Multi-tenancy Robuste
- **Isolation complète des données** par tenant avec filtres automatiques
- **Gestion des credentials API** isolées par tenant
- **Support multi-utilisateurs** avec rôles et permissions

### ⚡ Performance & Coût
- **Optimisations Free Tier** : Fonctionne sur Render.com gratuit
- **Mode d'exécution dual** : Celery workers ou FastAPI BackgroundTasks
- **Template pooling** : Évite les limites de quota Google Drive
- **Lazy loading** : Modèles ML chargés à la demande

### 🔌 Intégrations
- **6 API externes** orchestrées (Notion, Google Calendar, Sheets, Drive, Gmail, OAuth2)
- **OAuth2 flows** avec refresh automatique des tokens
- **Webhooks** pour déclenchement automatique

---

## Model Context Protocol (MCP)

Le projet inclut une implémentation serveur MCP (`app/mcp_server/`) pour intégration avec Claude Desktop. Cela permet un accès direct aux packs Talaria depuis l'interface Claude.

### Configuration MCP

```json
{
  "mcpServers": {
    "talaria": {
      "command": "python",
      "args": ["/path/to/Talaria/app/mcp_server/form3916_server_v4.py"],
      "env": {
        "OPENAI_API_KEY": "sk-...",
        "DATABASE_URL": "postgresql+asyncpg://..."
      }
    }
  }
}
```

---

## Documentation technique

Des case studies techniques détaillées sont disponibles pour chaque pack :

- **[docs/CASE_STUDY_DEME_TRAITEUR.md](docs/CASE_STUDY_DEME_TRAITEUR.md)** - Workflow production avec intégrations multi-API
- **[docs/CASE_STUDY_FORM_3916.md](docs/CASE_STUDY_FORM_3916.md)** - Traitement documents conversationnel avec LangGraph
- **[docs/CASE_STUDY_BOFIP_RAG.md](docs/CASE_STUDY_BOFIP_RAG.md)** - Système RAG hybride avec re-ranking

---

## Licence

Copyright (c) 2025 Nicolas Angougeard. Tous droits réservés.

Ce projet est un portfolio technique personnel. Le code source est fourni à titre de démonstration uniquement et n'est pas destiné à une utilisation commerciale par des tiers sans autorisation expresse.

---

## Contact & Contributions

Pour toute question ou suggestion concernant ce projet :

- **Auteur** : Nicolas Angougeard
- **GitHub** : [Aguern](https://github.com/Aguern)
- **Projet** : [Talaria](https://github.com/Aguern/Talaria)

Ce projet est en développement actif. Les contributions externes ne sont pas acceptées pour le moment, mais les retours et suggestions sont les bienvenus via les issues GitHub.
