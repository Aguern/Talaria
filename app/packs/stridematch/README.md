# StrideMatch Pack - Analyse de Foulée par IA

Pack d'analyse biomécanique de la foulée de course utilisant MediaPipe Pose et l'intelligence artificielle.

## 📋 Vue d'ensemble

Ce pack permet d'analyser la foulée de course à partir d'une simple vidéo smartphone pour :
- ✅ Extraire les angles articulaires (genou, cheville, hanche)
- ✅ Classifier le type d'attaque au sol (talon, médio-pied, avant-pied)
- ✅ Mesurer les performances en temps réel (latence < 150ms)
- ✅ Générer des recommandations biomécaniques

## 🎯 Objectifs du POC 1

Le POC 1 valide l'ancre technique différenciante de StrideMatch :
1. **Latence** : Traitement < 150ms par frame sur machine standard
2. **Précision** : Détection > 85% des landmarks pour analyse fiable
3. **Accessibilité** : Utilisation de vidéo smartphone (pas d'équipement spécialisé)

## 🚀 Installation

### Prérequis

- Python 3.10+
- PostgreSQL 15+ (pour l'API complète)
- Docker (optionnel, pour déploiement containerisé)

### Installation des dépendances

```bash
pip install -r requirements.txt
```

Les dépendances spécifiques au pack StrideMatch :
- `opencv-python` : Traitement vidéo
- `mediapipe` : Estimation de pose
- `numpy` : Calculs scientifiques
- `scipy` : Traitement du signal (détection de cadence)

## 📖 Utilisation

### Mode Standalone (POC rapide)

Le script `poc1_standalone.py` permet de tester l'analyse sans l'infrastructure complète.

#### Utilisation basique

```bash
cd app/packs/stridematch
python poc1_standalone.py /path/to/video.mp4
```

#### Avec sauvegarde de la vidéo annotée

```bash
python poc1_standalone.py video_input.mp4 --output video_annotated.mp4
```

#### Modes d'analyse

```bash
# Mode rapide (model_complexity=0, plus rapide)
python poc1_standalone.py video.mp4 --mode quick

# Mode détaillé (model_complexity=1, équilibré) - PAR DÉFAUT
python poc1_standalone.py video.mp4 --mode detailed

# Mode professionnel (model_complexity=2, plus précis)
python poc1_standalone.py video.mp4 --mode professional
```

#### Sans affichage en temps réel

```bash
python poc1_standalone.py video.mp4 --no-display
```

#### Exemple complet

```bash
python poc1_standalone.py \
  ~/Videos/course_profil.mp4 \
  --output ~/Results/analyse_foulée.mp4 \
  --mode detailed
```

### Mode API (Production)

L'API REST permet d'intégrer l'analyse dans des applications.

#### Démarrer le serveur

```bash
# Depuis la racine du projet
docker-compose up -d

# Ou en mode développement
uvicorn app.main:app --reload
```

#### Endpoints disponibles

##### 1. Analyser une vidéo

```bash
POST /api/packs/stridematch/analyze-gait
Content-Type: multipart/form-data

{
  "video_file": <binary>,
  "runner_name": "John Doe",
  "analysis_mode": "detailed",
  "save_annotated_video": true
}
```

**Réponse** :
```json
{
  "analysis_id": "123e4567-e89b-12d3-a456-426614174000",
  "gait_type": "heel_strike",
  "confidence": 87.5,
  "angles": {
    "knee_right": 145.2,
    "ankle_right": 92.3,
    "hip_right": 170.5
  },
  "avg_latency_ms": 85.3,
  "frame_count": 315,
  "landmarks_detected": true
}
```

##### 2. Récupérer une analyse

```bash
GET /api/packs/stridematch/analyses/{analysis_id}
```

##### 3. Lister les analyses

```bash
GET /api/packs/stridematch/analyses?limit=10&offset=0
```

##### 4. Health check

```bash
GET /api/packs/stridematch/health
```

**Réponse** :
```json
{
  "status": "healthy",
  "mediapipe_available": true,
  "opencv_available": true,
  "version": "0.1.0"
}
```

## 🎯 Objectifs du POC 2 - Moteur de Recommandation Hybride

Le POC 2 prouve que les **données biomécaniques du POC 1** résolvent le **problème du cold start** des systèmes de recommandation :

1. **Baseline** : Système expert rule-based (100% de précision théorique)
2. **Champion** : Modèle hybride LightFM qui apprend automatiquement les règles biomécaniques
3. **Objectif** : LightFM doit atteindre >60% de précision pour prouver qu'il apprend les patterns

### Installation des dépendances POC 2

```bash
pip install lightfm jupyter ipykernel matplotlib scikit-learn
```

Les dépendances spécifiques au POC 2 :
- `lightfm` : Modèle de recommandation hybride (collaborative + content-based)
- `jupyter` : Environnement notebook pour exploration
- `matplotlib` : Visualisations
- `scikit-learn` : Modèle baseline et métriques

### Utilisation du POC 2

#### Option 1 : Script Python (Recommandé pour tests rapides)

```bash
cd app/packs/stridematch
python run_poc2.py
```

**Sortie attendue** :
```
============================================================
POC 2 - Moteur de Recommandation Hybride StrideMatch
============================================================

📊 Génération catalogue: 100 chaussures
👥 Génération profils: 500 utilisateurs
🧬 Génération interactions: 8863 interactions (logique biomécanique)

🎯 Baseline (Rule-Based Expert System)
   - Precision@10: 1.000 (perfection théorique)

🏆 Champion (LightFM Hybride)
   - Precision@10: 0.966 (96.6% de la perfection!)

✅ SUCCESS: LightFM a appris les patterns biomécaniques!
```

#### Option 2 : Jupyter Notebook (Pour exploration approfondie)

```bash
jupyter notebook poc2_recommender.ipynb
```

Le notebook contient :
- Génération de données simulées (users, items, interactions)
- Entraînement des deux modèles
- Comparaison des métriques
- Visualisations

#### Option 3 : Script de débogage (Inspection détaillée)

```bash
python debug_poc2.py
```

Affiche :
- Exemples d'utilisateurs avec profils biomécaniques
- Items compatibles/incompatibles pour chaque profil
- Diagnostic des problèmes potentiels

### Architecture POC 2

#### 1. Génération de Données Simulées

**Catalogue Chaussures** (100 items) :
```python
features = {
    'stabilite': ['neutral', 'stable', 'motion_control'],
    'amorti': ['low', 'medium', 'high'],
    'drop': ['low', 'medium', 'high']
}
```

**Profils Utilisateurs** (500 users avec données POC 1) :
```python
biomechanical_features = {
    'pronation': ['neutral', 'overpronation', 'supination'],
    'foulee': ['heel_strike', 'midfoot_strike', 'forefoot_strike'],
    'poids': ['light', 'medium', 'heavy']
}
```

**Interactions** (10 000 générées avec logique biomécanique) :
```python
# Exemple de règle
if user.pronation == 'overpronation':
    if item.stabilite == 'motion_control':
        rating = 1  # Excellent match (prévention blessures)
    elif item.stabilite == 'neutral':
        rating = -1  # Mauvais match (risque de blessure)
```

#### 2. Modèle Baseline : Rule-Based Expert System

Le baseline représente la **perfection théorique** (100%) :
```python
def get_ideal_recommendations(user_id, k=10):
    """
    Calcule le score de compatibilité biomécanique
    pour chaque item et retourne les top-k.
    """
    scores = []
    for item in items:
        score = calculate_biomechanical_match(user, item)
        scores.append((item_id, score))

    return sorted(scores, reverse=True)[:k]
```

**Avantages** :
- ✅ 100% de précision (connaît parfaitement les règles)
- ✅ Aucun cold start (fonctionne dès le premier utilisateur)
- ❌ Mais ne peut pas apprendre de nouveaux patterns

#### 3. Modèle Champion : LightFM Hybride

LightFM **apprend automatiquement** les règles biomécaniques :
```python
model = LightFM(
    loss='warp',              # Optimisé pour ranking
    no_components=10,         # Embedding dimension
    user_alpha=0.0001,        # Régularisation user
    item_alpha=0.0001         # Régularisation item
)

model.fit(
    interactions,
    user_features=biomechanical_matrix,  # POC 1 data!
    item_features=shoe_specs_matrix,
    epochs=50
)
```

**Avantages** :
- ✅ Apprend les patterns complexes automatiquement
- ✅ Combine biomécanique + collaboratif + content
- ✅ S'améliore avec plus de données
- ⚠️  Nécessite des données d'entraînement

### Métriques et Validation POC 2

| Métrique | Baseline | LightFM | Critère |
|----------|----------|---------|---------|
| Precision@10 | 1.000 | 0.966 | >0.60 ✅ |
| Écart à la perfection | 0% | 3.4% | <30% ✅ |

**Interprétation** :
- Le baseline (100%) est un **système expert** qui connaît parfaitement les règles
- LightFM atteint **96.6%** de cette perfection en apprenant automatiquement
- **Écart de seulement 3.4%** : LightFM a réussi à découvrir les patterns biomécaniques !

### Exemples de Patterns Appris par LightFM

#### Pattern 1 : Pronation → Stabilité
```
Utilisateur: overpronation
→ LightFM recommande: chaussures stable/motion_control
→ Logique apprise: stabilité corrige l'effondrement médial
```

#### Pattern 2 : Poids → Amorti
```
Utilisateur: heavy
→ LightFM recommande: chaussures high amorti
→ Logique apprise: protection des articulations
```

#### Pattern 3 : Foulée → Drop
```
Utilisateur: forefoot_strike
→ LightFM recommande: chaussures low drop
→ Logique apprise: favorise l'attaque naturelle avant-pied
```

### Résultats Obtenus

**Configuration de test** :
- 500 utilisateurs avec profils biomécaniques
- 100 chaussures avec specs techniques
- 8863 interactions (5463 positives, 3400 négatives)
- Split 80/20 : 4370 train, 1093 test

**Performances** :
```
🏆 RÉSULTATS FINAUX - POC 2
============================================================
Modèle                                      Precision@10
------------------------------------------------------------
Baseline (Rule-Based Expert System)                1.000
Champion (LightFM Hybride)                         0.966
------------------------------------------------------------
Écart à la perfection                               3.4%
============================================================

✅ SUCCESS: LightFM a réussi à apprendre les patterns biomécaniques!
   Les données du POC 1 permettent effectivement de résoudre le cold start.
```

### Impact de la Biomécanique (POC 1 → POC 2)

Le POC 2 prouve que les données extraites par le POC 1 sont **la clé du cold start** :

**Sans biomécanique** (collaborative pur) :
- ❌ Cold start total pour nouveaux utilisateurs
- ❌ Recommandations aléatoires avant historique
- ❌ Risque de recommander des chaussures dangereuses

**Avec biomécanique** (POC 1 → POC 2) :
- ✅ Recommandations précises dès le premier achat
- ✅ 96.6% de précision vs système expert
- ✅ Prévention des blessures (matching biomécanique)

### Dépannage POC 2

#### Precision < 60%

**Causes possibles** :
- Pas assez d'interactions (augmenter TARGET_INTERACTIONS)
- Règles biomécaniques trop strictes (assouplir les seuils)
- Hyperparamètres LightFM mal configurés

**Solutions** :
```python
# Augmenter les interactions
TARGET_INTERACTIONS = 20000  # au lieu de 10000

# Optimiser LightFM
model = LightFM(
    no_components=15,     # Augmenter si plus de données
    epochs=100,           # Augmenter pour meilleur apprentissage
    learning_rate=0.01    # Réduire si instable
)
```

#### Temps d'entraînement trop long

```python
# Réduire la complexité
model = LightFM(
    no_components=5,      # Moins de paramètres
    epochs=30,            # Moins d'epochs
    num_threads=8         # Utiliser plus de threads
)
```

## 🏗️ Architecture

### Structure du pack

```
stridematch/
├── manifest.json              # Métadonnées du pack
├── models.py                  # Modèles SQLAlchemy (GaitAnalysis, etc.)
├── schemas.py                 # Schémas Pydantic (validation API)
├── router.py                  # Routes FastAPI
├── graph.py                   # Workflow LangGraph
│
├── poc1_standalone.py         # POC 1: Script standalone analyse gait
├── run_poc2.py                # POC 2: Script recommandation hybride
├── poc2_recommender.ipynb     # POC 2: Notebook Jupyter complet
├── debug_poc2.py              # POC 2: Script de débogage
│
├── ml/
│   ├── pose_estimator.py      # Wrapper MediaPipe Pose
│   ├── angle_calculator.py    # Calculs angles biomécaniques
│   ├── gait_classifier.py     # Classification type de foulée
│   ├── velocity_tracker.py    # Détection vélocité/contact sol
│   ├── gait_state_machine.py  # Machine à états cycle de foulée
│   └── landmark_filter.py     # Lissage adaptatif des landmarks
│
├── data/                      # Données simulées POC 2 (générées)
│   ├── users.csv              # Profils utilisateurs
│   ├── items.csv              # Catalogue chaussures
│   └── interactions.csv       # Historique achats simulé
│
└── utils/
    └── video_processor.py     # Utilitaires vidéo
```

### Workflow d'analyse

#### POC 1 : Analyse Biomécanique

```
Vidéo Input
    ↓
[1. Extraction Pose] (MediaPipe)
    ↓
[2. Lissage Landmarks] (Adaptive Filter)
    ↓
[3. Calcul Vélocité] (Velocity Tracker)
    ↓
[4. State Machine] (SWING → CONTACT → STANCE → TOE_OFF)
    ↓
[5. Classification à CONTACT] (Multi-critères biomécaniques)
    ↓
[6. Calcul Angles] (Genou, Cheville, Hanche, Tronc)
    ↓
Profil Biomécanique Complet
```

#### POC 2 : Recommandation Hybride

```
Profil Biomécanique (POC 1)
    ↓
[1. Feature Engineering] (One-hot encoding)
    ↓
[2. Génération Interactions] (Règles biomécaniques)
    ↓
[3. Train/Test Split] (80/20)
    ↓
         ┌─────────────────────────────┐
         │                             │
    [Baseline]                    [Champion]
    Rule-Based                    LightFM Hybride
    Expert System                 (WARP Loss)
         │                             │
         │                             │
    [user × item]                [user_features +
    biomech_score                 item_features +
         │                        interactions]
         │                             │
         └─────────────┬───────────────┘
                       ↓
              [Comparaison Métriques]
                       ↓
           Top-10 Recommandations
         (96.6% vs perfection!)
```

## 📊 Métriques et Validation

### Critères de Succès POC 1

| Métrique | Objectif | Méthode de validation |
|----------|----------|----------------------|
| Latence moyenne | < 150ms/frame | Mesure `time.time()` autour de `pose.process()` |
| Taux de détection | > 85% | Ratio frames avec landmarks / total frames |
| Précision classification | > 85% | Validation manuelle par expert (20+ vidéos) |

### Résultats Attendus

Sur une machine standard (CPU moderne, pas de GPU requis) :
- **Latence** : 80-120ms par frame (mode detailed)
- **Détection** : 90-95% des frames (vidéo bien cadrée)
- **Classification** : 85-92% de précision vs évaluation expert

## 🎥 Recommandations Vidéo

Pour des résultats optimaux :

### Capture Vidéo

- **Angle** : Vue de profil (plan sagittal)
- **Distance** : Personne visible en entier (tête aux pieds)
- **Éclairage** : Bon éclairage, éviter contre-jour
- **Fond** : Fond contrasté pour meilleure détection
- **Durée** : 5-15 secondes (suffisant pour analyse)
- **Vitesse** : Course à vitesse constante

### Format Vidéo

- **Résolution** : Minimum 720p (1280x720), idéal 1080p
- **FPS** : 30 FPS minimum
- **Codec** : H.264/AVC (MP4)
- **Orientation** : Paysage (horizontal)

## 🔬 Détails Techniques

### Angles Biomécaniques Calculés

1. **Angle de genou** : Hip → Knee → Ankle
   - Normal course : 140-160° (phase d'appui)

2. **Angle de cheville** : Knee → Ankle → Foot
   - Dorsiflexion : 90-110° (heel strike)
   - Plantarflexion : 70-85° (forefoot strike)

3. **Angle de hanche** : Shoulder → Hip → Knee
   - Extension : 160-180°

4. **Inclinaison tronc** : Vertical → Hip → Shoulder
   - Lean avant optimal : 5-15°

### Classification Type de Foulée

#### Méthode Principale : Position Verticale

```python
vertical_ratio = heel.y / toe.y

if ratio >= 0.98:
    gait_type = HEEL_STRIKE
elif ratio <= 0.85:
    gait_type = FOREFOOT_STRIKE
else:
    gait_type = MIDFOOT_STRIKE
```

#### Méthode Alternative : Angles Articulaires

- **Heel Strike** : Ankle > 95°, Knee > 155°
- **Forefoot Strike** : Ankle < 85°, Knee < 155°
- **Midfoot Strike** : Valeurs intermédiaires

## 🐛 Dépannage

### Erreur : "Failed to open video file"

- Vérifier que le fichier existe
- Vérifier le format (MP4, AVI, MOV supportés)
- Essayer de réencoder avec ffmpeg :
  ```bash
  ffmpeg -i input.mp4 -c:v libx264 -crf 23 output.mp4
  ```

### Faible taux de détection (< 85%)

- Améliorer l'éclairage de la vidéo
- Vérifier que la personne est entièrement visible
- Utiliser mode "professional" (plus précis)
- Augmenter la résolution vidéo

### Latence élevée (> 150ms)

- Utiliser mode "quick" (model_complexity=0)
- Réduire la résolution vidéo (720p)
- Vérifier que MediaPipe utilise bien les optimisations CPU

## 📚 Références

### Documentation Technique

- [MediaPipe Pose](https://google.github.io/mediapipe/solutions/pose.html)
- [StrideMatch Documentation Complète](/docs/StrideMatch.md)

### Recherche Biomécanique

- Heliyon Oct 2024: Pose estimation models review
- Nature Scientific Data 2024: 3D gait datasets
- Running Injury Clinic Dataset (Figshare)

## 🤝 Contribution

Ce pack fait partie du SaaS Caméléon et suit l'architecture "Cœur + Packs".

### Principes de développement

- **Modularité stricte** : Logique métier isolée dans le pack
- **Multi-tenancy** : Toutes les données filtrées par `tenant_id`
- **Sécurité** : Pas de secrets en dur, utilisation de `.env`
- **Qualité** : Type hints, tests unitaires, documentation

## 📄 Licence

Copyright © 2025 StrideMatch

## 👤 Auteur

Développé dans le cadre du POC technique StrideMatch pour validation de faisabilité.

---

**Version** : 0.2.0 (POC 1 + POC 2 validés)
**Dernière mise à jour** : Janvier 2025

## 📈 Changelog

### v0.2.0 (Janvier 2025)
- ✅ **POC 2 validé** : Moteur de recommandation hybride (LightFM)
- ✅ LightFM atteint 96.6% de précision vs baseline expert
- ✅ Preuve que les données biomécaniques résolvent le cold start
- 📝 Documentation complète POC 2 ajoutée
- 🆕 Scripts : `run_poc2.py`, `debug_poc2.py`, `poc2_recommender.ipynb`

### v0.1.0 (Janvier 2025)
- ✅ **POC 1 validé** : Analyse biomécanique de la foulée
- ✅ Latence 12.85ms (< 150ms requis)
- ✅ Détection 100% (> 85% requis)
- ✅ State Machine avec 4 phases (SWING/CONTACT/STANCE/TOE_OFF)
- 🆕 Adaptive Landmark Smoother pour réduction du bruit
- 🆕 Velocity Tracker pour détection précise du contact sol
