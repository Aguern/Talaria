# RunRepeat AI Scraper
## Architecture Modulaire Stealth + IA

Ce système de scraping utilise une approche moderne qui combine :
- **Playwright** avec mesures stealth maximales pour éviter les 403
- **BeautifulSoup** pour nettoyer le HTML et réduire les coûts
- **OpenAI GPT-4o-mini** pour extraire les données (fini les sélecteurs CSS fragiles !)

---

## 📦 Architecture

```
scraping/
├── stealth_browser.py      # Module A: Navigation furtive (Playwright + Stealth)
├── html_cleaner.py          # Module B: Nettoyage HTML (BeautifulSoup)
├── ai_extractor.py          # Module C: Extraction IA (OpenAI)
├── runrepeat_scraper.py     # Pipeline complet
└── README_AI_SCRAPER.md     # Ce fichier
```

### Module A: Stealth Browser
- Playwright avec User-Agent réaliste
- Désactive tous les flags d'automation
- Mouvements de souris et scrolling simulés
- Délais aléatoires entre actions
- Fingerprint navigateur réaliste

### Module B: HTML Cleaner
- Supprime scripts, styles, images, SVG
- Garde seulement la structure sémantique (h1-h6, p, div, table)
- Réduit le HTML de ~90% (économise tokens OpenAI)
- Fonctions: `clean_html()`, `extract_text_only()`, `get_structured_content()`

### Module C: AI Extractor
- Utilise OpenAI Structured Outputs (garantit JSON valide)
- Schéma Pydantic pour validation
- Extrait: nom, poids, drop, score, pros/cons, specs techniques
- Mode batch pour scraper plusieurs chaussures en parallèle

---

## 🚀 Installation

### 1. Installer les dépendances Python

```bash
cd app/packs/stridematch/scraping

# Installer les packages
pip install playwright playwright-stealth beautifulsoup4 lxml openai pydantic
```

### 2. Installer Playwright browsers

```bash
# Installer Chromium (headless)
playwright install chromium
```

### 3. Configurer l'API OpenAI

Ajouter dans votre `.env` :

```bash
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxx
```

---

## 🧪 Tests

### Test 1: Vérifier l'accès à RunRepeat

```bash
python runrepeat_scraper.py --test
```

**Résultat attendu:**
```
✅ ACCESS OK - Fetched 250000 characters
Stealth configuration appears to be working!
```

**Si vous voyez `❌ BLOCKED`:**
- Vous êtes sur un serveur cloud (AWS, GCP, DigitalOcean, etc.)
- RunRepeat détecte l'IP de datacenter
- **Solution:** Lancer depuis votre PC local (IP résidentielle)

---

### Test 2: Tester chaque module indépendamment

#### Module A (Stealth Browser)
```bash
cd app/packs/stridematch/scraping
python stealth_browser.py
```

#### Module B (HTML Cleaner)
```bash
python html_cleaner.py
```

#### Module C (AI Extractor)
```bash
# Nécessite OPENAI_API_KEY dans .env
python ai_extractor.py
```

---

## 📖 Utilisation

### Scraper une seule chaussure

```bash
python runrepeat_scraper.py https://runrepeat.com/nike-pegasus-41
```

**Sortie:**
```json
[
  {
    "model_name": "Nike Pegasus 41",
    "score": 87.0,
    "weight_g": 280,
    "drop_mm": 10.0,
    "stack_heel_mm": 37.0,
    "stack_forefoot_mm": 27.0,
    "pros": [
      "Comfortable and responsive cushioning",
      "Durable outsole with excellent traction",
      "Great value for daily training"
    ],
    "cons": [
      "Too heavy for racing (280g)",
      "Limited color options"
    ],
    "source_url": "https://runrepeat.com/nike-pegasus-41"
  }
]
```

---

### Scraper plusieurs chaussures

Créer un fichier `urls.txt` :

```
https://runrepeat.com/nike-pegasus-41
https://runrepeat.com/adidas-ultraboost-23
https://runrepeat.com/hoka-clifton-9
https://runrepeat.com/asics-gel-nimbus-26
```

Lancer le scraping batch :

```bash
python runrepeat_scraper.py --urls urls.txt --output results.json
```

**Comportement:**
- Scrape chaque URL séquentiellement
- Délai de 10 secondes entre chaque requête (politesse)
- Sauvegarde dans `results.json`

---

### Options avancées

#### Sauvegarder le HTML brut et nettoyé (debug)

```bash
python runrepeat_scraper.py https://runrepeat.com/nike-pegasus-41 --save-raw
```

Génère :
- `raw_nike-pegasus-41.html` - HTML brut après Playwright
- `cleaned_nike-pegasus-41.html` - HTML après nettoyage

#### Personnaliser le fichier de sortie

```bash
python runrepeat_scraper.py --urls urls.txt --output my_data.json
```

---

## 💰 Coûts OpenAI

Le module utilise **GPT-4o-mini** (le modèle le moins cher d'OpenAI).

**Estimation:**
- HTML nettoyé: ~2000-4000 tokens (input)
- Réponse JSON: ~500 tokens (output)
- **Coût par chaussure:** ~$0.001 - $0.002 USD (0.1 à 0.2 centime)

**Pour 100 chaussures:** ~$0.10 - $0.20 USD

👉 Bien moins cher que de maintenir des sélecteurs CSS qui cassent constamment !

---

## ⚠️ Important: Question de l'IP

### ❌ Ne fonctionnera PAS depuis :
- Serveurs cloud (AWS, GCP, Azure, DigitalOcean, Hetzner, etc.)
- VPS / machines virtuelles
- **Raison:** RunRepeat détecte les IPs de datacenter et retourne 403

### ✅ Fonctionnera depuis :
- **Votre PC/Mac personnel** (connexion Wifi/fibre maison)
- Serveur avec IP résidentielle (proxy résidentiel)

### Solutions si vous êtes bloqué :

1. **Recommandé:** Lancer depuis votre ordinateur local
   ```bash
   # Sur votre Mac/PC
   cd ~/Desktop/SaaS_NR/app/packs/stridematch/scraping
   python runrepeat_scraper.py --test
   ```

2. **Alternative:** Utiliser un proxy résidentiel
   - Services: Bright Data, Oxylabs, SmartProxy
   - Coût: ~$5-10 / Go de data
   - Configuration: ajouter proxy dans `stealth_browser.py`

3. **Alternative:** Scraper depuis GitHub Actions
   - Les runners GitHub ont parfois des IPs non-bloquées
   - Gratuit pour repos publics

---

## 🔧 Personnalisation

### Modifier les champs extraits

Éditer `ai_extractor.py`, classe `ShoeData` :

```python
class ShoeData(BaseModel):
    model_name: str
    weight_g: Optional[int]
    # Ajouter vos champs ici
    heel_counter_stiffness: Optional[str] = None
    breathability_score: Optional[int] = None
```

### Ajuster les mesures stealth

Éditer `stealth_browser.py`, fonction `get_page_content()` :

```python
# Augmenter le délai de simulation humaine
await asyncio.sleep(random.uniform(2.0, 5.0))  # Au lieu de 1.0-2.5

# Augmenter le wait_time
wait_time=10  # Au lieu de 5
```

### Changer le modèle OpenAI

```python
# Utiliser GPT-4o (plus cher mais plus précis)
data = await extract_shoe_data(cleaned, model="gpt-4o")

# Ou Claude 3.5 Sonnet (Anthropic)
# Modifier ai_extractor.py pour utiliser l'API Anthropic
```

---

## 🐛 Dépannage

### Erreur: `403 Forbidden`

**Cause:** IP de datacenter détectée

**Solution:**
1. Lancer depuis votre PC local
2. Vérifier avec `python runrepeat_scraper.py --test`
3. Si toujours bloqué, essayer un proxy résidentiel

### Erreur: `OPENAI_API_KEY not found`

**Solution:**
```bash
# Dans votre .env
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxx
```

### Erreur: `playwright install chromium`

**Solution:**
```bash
playwright install chromium
playwright install-deps chromium  # Sur Linux
```

### Extraction incomplète (champs manquants)

**Cause:** L'IA n'a pas trouvé les données dans le HTML

**Solution:**
1. Vérifier le HTML nettoyé : `--save-raw`
2. Ajuster le prompt dans `ai_extractor.py`
3. Augmenter `max_tokens` si la réponse est tronquée

---

## 📊 Workflow complet

```
1. get_page_content(url)
   ↓
   HTML brut (250KB)
   ↓
2. clean_html(html)
   ↓
   HTML nettoyé (25KB, -90%)
   ↓
3. extract_shoe_data(cleaned)
   ↓
   JSON structuré
   ↓
4. Sauvegarder en base de données
```

---

## 🎯 Next Steps

Une fois le scraping fonctionnel :

1. **Intégrer à la base de données PostgreSQL**
   - Adapter le pipeline pour insérer dans `stridematch_products`
   - Mapper les champs AI → schéma DB

2. **Automatiser avec Celery**
   - Créer une tâche Celery pour scraping nocturne
   - Scheduler avec `celery beat`

3. **Ajouter d'autres sources**
   - Dupliquer la structure pour RunningShoesGuru
   - Adapter le schéma `ShoeData` pour chaque source

4. **Monitoring & Logs**
   - Logger dans PostgreSQL les succès/échecs
   - Dashboard Grafana pour suivre le scraping

---

## 📝 Licence

Utilisation interne uniquement. Respecter les robots.txt et les ToS de RunRepeat.

---

## 🙏 Crédits

- **Playwright** : https://playwright.dev/
- **OpenAI** : https://openai.com/
- **BeautifulSoup** : https://www.crummy.com/software/BeautifulSoup/
