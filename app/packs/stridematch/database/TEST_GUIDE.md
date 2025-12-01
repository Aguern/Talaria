# 🧪 Guide de Test de l'Infrastructure StrideMatch

Ce guide vous accompagne pour tester l'infrastructure complète de StrideMatch (PostgreSQL + MongoDB + Neo4j).

---

## Prérequis

✅ Docker Desktop installé et **démarré**
✅ PostgreSQL client installé (`psql`) - Optionnel mais recommandé
✅ Python 3.10+ avec dépendances installées

---

## Méthode 1 : Script Automatique (Recommandé)

### Étape 1 : Vérifier que Docker est démarré

```bash
docker --version
```

**Résultat attendu :** `Docker version 24.x.x` (ou similaire)

### Étape 2 : Lancer le script de test

```bash
cd /Users/nicolasangougeard/Desktop/SaaS_NR
./app/packs/stridematch/database/test_infrastructure.sh
```

**Ce script va automatiquement :**
1. ✅ Vérifier que Docker est démarré
2. ✅ Lancer PostgreSQL, MongoDB, Neo4j
3. ✅ Initialiser le schéma PostgreSQL (7 tables + 10 marques)
4. ✅ Tester MongoDB et créer un profil utilisateur test
5. ✅ Initialiser Neo4j avec contraintes et index
6. ✅ Afficher un résumé complet

**Durée estimée :** ~2 minutes

---

## Méthode 2 : Tests Manuels (Détaillé)

Si tu préfères tester manuellement étape par étape :

### Test 1 : Lancer les Services

```bash
docker-compose up -d db mongodb neo4j
```

**Vérifier que les services sont démarrés :**
```bash
docker-compose ps
```

**Résultat attendu :**
```
NAME                STATUS
db                  Up
mongodb             Up
neo4j               Up
```

---

### Test 2 : PostgreSQL

#### 2.1 Initialiser le schéma

```bash
# Charger les variables d'environnement
source .env

# Exécuter le script SQL
PGPASSWORD="${POSTGRES_PASSWORD}" psql \
    -h localhost \
    -p 5432 \
    -U "${POSTGRES_USER}" \
    -d "${POSTGRES_DB}" \
    -f app/packs/stridematch/database/schema.sql
```

**Résultat attendu :**
```
CREATE EXTENSION
CREATE TYPE
CREATE TYPE
...
CREATE TABLE
...
INSERT 0 10  (10 brands inserted)
✅ Schema initialized successfully
```

#### 2.2 Vérifier les tables créées

```bash
PGPASSWORD="${POSTGRES_PASSWORD}" psql \
    -h localhost \
    -p 5432 \
    -U "${POSTGRES_USER}" \
    -d "${POSTGRES_DB}" \
    -c "\dt stridematch_*"
```

**Résultat attendu :** 7 tables listées
- `stridematch_brands`
- `stridematch_sizing_normalization`
- `stridematch_products`
- `stridematch_product_variants`
- `stridematch_product_specs_lab`
- `stridematch_product_specs_marketing`
- `stridematch_enrichment_tags`

#### 2.3 Vérifier les marques

```bash
PGPASSWORD="${POSTGRES_PASSWORD}" psql \
    -h localhost \
    -p 5432 \
    -U "${POSTGRES_USER}" \
    -d "${POSTGRES_DB}" \
    -c "SELECT id, name, slug FROM stridematch_brands ORDER BY name;"
```

**Résultat attendu :** 10 marques (Nike, Adidas, Hoka, etc.)

---

### Test 3 : MongoDB

#### 3.1 Tester la connexion

```bash
docker exec $(docker-compose ps -q mongodb) mongosh \
    --username stridematch \
    --password stridematch_password \
    --authenticationDatabase admin \
    --eval "db.adminCommand('ping')"
```

**Résultat attendu :**
```json
{ "ok": 1 }
```

#### 3.2 Créer un profil utilisateur test

```bash
docker exec $(docker-compose ps -q mongodb) mongosh \
    stridematch \
    --username stridematch \
    --password stridematch_password \
    --authenticationDatabase admin \
    --eval '
db.users.insertOne({
  user_id: 1,
  tenant_id: 1,
  email: "test@stridematch.com",
  demographics: {
    age: 35,
    weight_kg: 75.0,
    height_cm: 175.0,
    gender: "male"
  },
  biomechanics: {
    foot_strike: "heel_strike",
    pronation_type: "overpronation",
    avg_cadence_spm: 172
  },
  created_at: new Date()
})'
```

#### 3.3 Vérifier le document créé

```bash
docker exec $(docker-compose ps -q mongodb) mongosh \
    stridematch \
    --username stridematch \
    --password stridematch_password \
    --authenticationDatabase admin \
    --eval "db.users.find().pretty()"
```

---

### Test 4 : Neo4j

#### 4.1 Accéder à Neo4j Browser

Ouvre ton navigateur : **http://localhost:7474**

**Credentials :**
- Username: `neo4j`
- Password: `stridematch_neo4j`

#### 4.2 Initialiser le schéma (via Browser)

Copie-colle le contenu du fichier :
```
app/packs/stridematch/database/neo4j_init.cypher
```

Dans le Neo4j Browser et exécute-le.

**Résultat attendu :**
```
✅ StrideMatch Neo4j graph schema initialized successfully!
   Constraints: 5, Indexes: 11, Sample nodes created
```

#### 4.3 Vérifier les contraintes

Dans Neo4j Browser, exécute :
```cypher
SHOW CONSTRAINTS;
```

**Résultat attendu :** 5 contraintes listées

#### 4.4 Vérifier les index

```cypher
SHOW INDEXES;
```

**Résultat attendu :** 11+ index listés

#### 4.5 Vérifier les nœuds de test

```cypher
MATCH (c:Category) RETURN c.name AS category;
```

**Résultat attendu :** 5 catégories (Running Road, Running Trail, etc.)

```cypher
MATCH (t:Tag) RETURN t.tag_name AS tag LIMIT 10;
```

**Résultat attendu :** 10 tags biomécaniques

---

## Test 5 : Modèles SQLAlchemy

Teste que les modèles Python fonctionnent correctement :

```bash
cd /Users/nicolasangougeard/Desktop/SaaS_NR
python app/packs/stridematch/database/test_models.py
```

**Ce script va :**
1. Tester la connexion à PostgreSQL
2. Lire les marques (Brand model)
3. Créer un produit complet avec specs (Product + ProductSpecs_Lab + ProductSpecs_Marketing + ProductVariant + Enrichment_Tag)
4. Créer une entrée de sizing (SizingNormalization)
5. Exécuter une requête complexe avec joins

**Résultat attendu :**
```
============================================================
StrideMatch SQLAlchemy Models Test
============================================================

📋 Test 1: Database Connection
✅ Database connection successful

📋 Test 2: Brand Model
   Found 10 brands:
   - Adidas (id=2, slug=adidas)
   - Altra (id=10, slug=altra)
   ...
✅ Brand model working correctly

📋 Test 3: Product Creation (Full Relationship Test)
   Created product: Test Pegasus 99
   - Brand: Nike
   - Lab specs: drop=10.0mm, weight=285.0g
   - Marketing specs: neutral
   - Variant SKU: NIKE-PEGASUS-99-BLUE-42
   - Tags: 2 tags
✅ Product creation successful

📋 Test 4: Sizing Normalization
   Created sizing: Nike Men's EU:42 = 26.5cm
✅ Sizing normalization successful

📋 Test 5: Complex Query with Joins
   Found 1 test products:
   - Nike Test Pegasus 99 (drop: 10.0mm)
✅ Complex query successful

============================================================
Test Summary
============================================================
✅ PASS: Database Connection
✅ PASS: Brand Model
✅ PASS: Product Creation
✅ PASS: Sizing Normalization
✅ PASS: Complex Queries

Results: 5/5 tests passed
✅ All tests passed!
```

---

## Test 6 : Script de Scraping (Dry-Run)

Teste le script de scraping des guides de tailles en mode dry-run :

```bash
cd app/packs/stridematch/scraping
python scrape_sizing.py --brand nike --dry-run
```

**Résultat attendu :**
```
============================================================
StrideMatch Sizing Scraper - Phase 2
============================================================
🔍 DRY RUN MODE: Data will not be inserted into database
Scraping Nike size guide...
⚠️ Nike scraping not yet implemented (template)
```

---

## Accès aux Services

Une fois les tests passés, tu peux accéder aux services :

### PostgreSQL
```bash
PGPASSWORD="${POSTGRES_PASSWORD}" psql \
    -h localhost \
    -p 5432 \
    -U "${POSTGRES_USER}" \
    -d "${POSTGRES_DB}"
```

### MongoDB
```bash
docker exec -it $(docker-compose ps -q mongodb) mongosh \
    stridematch \
    --username stridematch \
    --password stridematch_password
```

### Neo4j Browser
**URL :** http://localhost:7474
**Username :** neo4j
**Password :** stridematch_neo4j

---

## Arrêter les Services

Quand tu as fini de tester :

```bash
docker-compose down
```

**Pour supprimer les données (ATTENTION : destructif) :**
```bash
docker-compose down -v
```

---

## Dépannage

### Erreur : "Cannot connect to Docker daemon"
**Solution :** Démarre Docker Desktop et attends qu'il soit prêt

### Erreur : "Port 5432 already in use"
**Solution :** Un autre service PostgreSQL utilise déjà le port. Arrête-le ou change le port dans `docker-compose.yml`

### Erreur : "FATAL: password authentication failed"
**Solution :** Vérifie que le fichier `.env` contient les bonnes credentials

### Neo4j n'est pas accessible
**Solution :** Attends 30-60 secondes après `docker-compose up`. Neo4j met du temps à démarrer.

---

## Checklist de Validation

- [ ] ✅ Docker Desktop démarré
- [ ] ✅ Services lancés (`docker-compose ps` montre 3 services "Up")
- [ ] ✅ PostgreSQL : 7 tables créées + 10 marques
- [ ] ✅ MongoDB : Profil utilisateur test créé
- [ ] ✅ Neo4j : Contraintes et index initialisés
- [ ] ✅ Modèles SQLAlchemy : 5/5 tests passés
- [ ] ✅ Script scraping fonctionne en dry-run

**Si toute la checklist est validée, l'infrastructure est prête pour les Phases 3-6 ! 🎉**
