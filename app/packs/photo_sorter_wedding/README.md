# Photo Sorter Wedding - Tri Intelligent de Photos de Mariage

Pack personnalisé pour trier automatiquement vos photos de mariage en utilisant l'IA (GPT-5) et des algorithmes de traitement d'image avancés.

## 🎯 Objectif

Trier automatiquement ~1680 photos de mariage pour ne conserver que les meilleures en se basant sur :
- ✅ Cadrage et composition
- ✅ Qualité de la lumière
- ✅ Arrière-plan
- ✅ Expression des personnes
- ✅ Netteté technique
- ✅ Détection et élimination des doublons

## 🔬 Approche Hybride Optimisée (2025)

Inspirée des meilleurs outils du marché (Aftershoot, Imagen, FilterPixel), cette solution utilise une approche en **4 passes** pour réduire les coûts d'API de **~69%** :

### Passe 1 : Détection de doublons (Sans API - Gratuit)
- Utilise le **hashing perceptuel** (pHash) pour détecter les photos similaires
- Robuste aux redimensionnements, compressions et petites modifications
- Garde automatiquement la photo avec le meilleur score
- **Économie : ~140 photos sur 1680**

### Passe 2 : Filtrage technique (Sans API - Gratuit)
- Analyse locale avec **OpenCV** et **Pillow**
- Seuils assouplis pour photos professionnelles de mariage :
  - Netteté minimale : 50 (permissif pour photos artistiques)
  - Luminosité : 10-250 (permissif pour photos créatives et high-key)
  - Résolution minimale : 500x500
- **Économie : Rejet seulement des photos vraiment problématiques**

### Passe 3a : Analyse IA low-detail (85 tokens/photo)
- **Toutes les photos qualifiées** sont analysées en mode rapide
- Utilise **GPT-5 Vision** en mode `detail: "low"`
- Évalue : composition, lumière, sujets, valeur émotionnelle
- **Coût : ~$0.37 pour 1450 photos**

### Passe 3b : Analyse IA high-detail (765 tokens/photo)
- **Seulement le top 40%** est ré-analysé en mode détaillé
- Mode `detail: "high"` pour analyse précise
- Scores finaux très précis sur les meilleures candidates
- **Coût : ~$3.99 pour 580 photos**

## 📋 Prérequis

### Dépendances Python

```bash
pip install opencv-python pillow imagehash openai
```

### Variables d'environnement

```bash
export OPENAI_API_KEY="votre-clé-api-openai"
```

## 🚀 Utilisation

### Via l'API REST

1. **Lancer un tri de photos :**

```bash
curl -X POST "http://localhost:8000/api/packs/photo-sorter-wedding/sort" \
  -H "Content-Type: application/json" \
  -d '{
    "photos_directory": "/chemin/vers/photos/mariage",
    "output_directory": "/chemin/vers/sortie",
    "selection_percentage": 30.0,
    "min_quality_score": 70.0,
    "duplicate_threshold": 0.95,
    "copy_files": true
  }'
```

**Réponse :**
```json
{
  "success": true,
  "message": "Tri de photos lancé avec succès...",
  "job_id": "sort_a3f9d2c8b1e4"
}
```

2. **Suivre la progression :**

```bash
curl "http://localhost:8000/api/packs/photo-sorter-wedding/status/sort_a3f9d2c8b1e4"
```

**Réponse :**
```json
{
  "job_id": "sort_a3f9d2c8b1e4",
  "status": "processing",
  "progress": 45.2,
  "total_photos": 1680,
  "processed_photos": 759,
  "selected_photos": 0,
  "duplicates_removed": 0
}
```

3. **Récupérer les résultats :**

Une fois terminé (`status: "completed"`), consultez :
- `output_directory/selected/` : Photos sélectionnées
- `output_directory/report_<job_id>.html` : Rapport détaillé HTML
- `output_directory/report_<job_id>.json` : Rapport JSON

### Paramètres configurables

| Paramètre | Type | Défaut | Description |
|-----------|------|--------|-------------|
| `photos_directory` | string | - | **Requis.** Dossier contenant les photos à trier |
| `output_directory` | string | - | **Requis.** Dossier de sortie pour les résultats |
| `selection_percentage` | float | 30.0 | Pourcentage de photos à conserver (1-100) |
| `min_quality_score` | float | 70.0 | Score de qualité minimum requis (0-100) |
| `duplicate_threshold` | float | 0.95 | Seuil de similarité pour doublons (0-1, 0.95 = très similaire) |
| `batch_size` | int | 10 | Nombre de photos à traiter en parallèle |
| `copy_files` | bool | true | Copier les photos sélectionnées dans output_directory/selected/ |

## 📊 Exemple de résultats

Pour 1680 photos de mariage :

```
📸 Rapport de Tri - Photos de Mariage

Photos analysées       : 1680
Photos sélectionnées   : 504 (30%)
Doublons retirés       : 143
Score moyen            : 84.2/100
Temps de traitement    : ~25 minutes
```

## 💰 Coût estimé

Avec l'approche hybride optimisée en 4 passes :

### Détail des coûts pour 1680 photos :

```
Passe 1 : Doublons          → 140 doublons détectés  (gratuit)
Passe 2 : Technique         → ~90 photos rejetées    (gratuit)
Passe 3a : Low-detail       → 1450 photos × 85 tokens  = $0.37
Passe 3b : High-detail      → 580 photos × 765 tokens = $3.99
                              ─────────────────────────────
                              TOTAL : ~$4.36
```

### Comparaison :
- **Sans optimisation** (high-detail sur toutes) : ~$14.21
- **Avec optimisation** (approche 4 passes) : ~$4.36
- **Économie : 69%** 💰

## 📁 Structure du rapport

Le rapport HTML généré inclut :

### ✅ Photos Sélectionnées
- Nom du fichier
- Score global de qualité (0-100)
- Scores détaillés : Composition, Lumière, Sujets, Netteté
- Description du moment capturé

### 🔄 Doublons Détectés
- Liste des doublons avec référence à l'original conservé

### ❌ Photos Rejetées
- Photos avec score insuffisant
- Raisons du rejet (flou, exposition, etc.)

## 🎨 Méthodologie de notation

### Score Global (0-100)
Combinaison pondérée :
- **70% IA** : Évaluation artistique et émotionnelle
- **30% Technique** : Qualité technique objective

### Scores IA (GPT-5.1 Vision)
- **Composition** (0-100) : Cadrage, règle des tiers, équilibre
- **Lumière** (0-100) : Exposition, contraste, rendu des couleurs
- **Arrière-plan** (0-100) : Propreté, absence d'éléments distrayants
- **Sujets** (0-100) : Expression, posture, émotion
- **Valeur émotionnelle** (0-100) : Authenticité, connexion, storytelling

### Scores Techniques (OpenCV/Pillow)
- **Netteté** (0-100) : Variance de Laplacian
- **Exposition** (0-100) : Histogramme de luminosité
- **Bruit** (0-100) : Écart-type des pixels

## 🛠️ Développement

### Structure du pack

```
app/packs/photo_sorter_wedding/
├── __init__.py          # Init du package
├── manifest.json        # Description du pack
├── schemas.py          # Schémas Pydantic
├── logic.py            # Logique métier (tri, analyse)
├── router.py           # Endpoints FastAPI
└── README.md           # Documentation
```

### Ajouter le pack au router principal

Dans `app/main.py`, ajouter :

```python
from app.packs.photo_sorter_wedding.router import router as photo_sorter_router

app.include_router(photo_sorter_router)
```

## 📝 Notes importantes

1. **Format des photos supportés** : JPG, JPEG, PNG, WebP, HEIC
2. **Traitement asynchrone** : Le tri se fait en arrière-plan
3. **Stockage temporaire** : Les statuts sont en mémoire (utiliser Redis en production)
4. **Rate limiting** : Pause de 1s entre chaque batch pour éviter les limites d'API

## 🔧 Troubleshooting

### Erreur "OPENAI_API_KEY not found"
```bash
export OPENAI_API_KEY="votre-clé"
```

### Photos non détectées
Vérifiez que les extensions sont supportées (.jpg, .jpeg, .png, .webp, .heic)

### Processus trop lent
Réduisez `min_quality_score` pour filtrer davantage avant l'analyse IA

### Trop de doublons non détectés
Augmentez `duplicate_threshold` (ex: 0.98)

## 📚 Références

- [Aftershoot](https://aftershoot.com/) - Inspiration pour l'approche hybride
- [Imagehash](https://github.com/JohannesBuchner/imagehash) - Hashing perceptuel
- [OpenCV](https://opencv.org/) - Analyse technique d'images
- [GPT-5 Vision](https://openai.com/) - Modèle IA utilisé

## 📄 Licence

Pack personnalisé créé pour un usage privé.

---

**Créé avec ❤️ pour optimiser le tri de vos plus beaux souvenirs de mariage**
