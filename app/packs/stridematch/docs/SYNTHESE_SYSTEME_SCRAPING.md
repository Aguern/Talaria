# Système de Scraping Automatisé pour StrideMatch
## Documentation Technique & Stratégique

---

## Table des matières

1. [Introduction : Qu'est-ce que le scraping ?](#1-introduction)
2. [Architecture du système actuel](#2-architecture-du-système)
3. [Données récupérées et leur valeur](#3-données-récupérées)
4. [Base de données : Structure recommandée](#4-base-de-données)
5. [Gap avec le catalogue actuel](#5-gap-catalogue-actuel)
6. [Extension : 15 sites à scraper](#6-sites-à-scraper)
7. [Système d'automatisation intelligent](#7-automatisation)
8. [Limites et considérations](#8-limites)

---

## 1. Introduction : Qu'est-ce que le scraping ?

### Définition simple

Le web scraping est l'équivalent numérique d'un assistant qui visite des sites web, lit les informations affichées, et les copie dans un carnet structuré.

Analogie : Imaginez que vous voulez comparer les prix de 500 chaussures de running sur 15 sites différents. Vous pourriez :
- Option A : Ouvrir chaque page manuellement, noter les prix dans Excel (40+ heures)
- Option B : Programmer un robot qui fait exactement la même chose en 2 heures, sans erreur

Le scraping = Option B automatisée.

### Cas d'usage pour StrideMatch

Notre système permet de :
1. Collecter automatiquement les données techniques de chaussures de running (poids, drop, amorti, etc.)
2. Enrichir notre base de données avec des tests de laboratoire validés
3. Mettre à jour les prix et disponibilités en temps réel
4. Éviter la saisie manuelle chronophage et source d'erreurs

### Pourquoi c'est crucial pour StrideMatch

Dans le marché du running, environ 300-500 nouveaux modèles sortent chaque année. Sans automatisation :
- Temps requis : 150+ heures/an de saisie manuelle
- Risque d'erreurs : ~15% d'erreurs humaines
- Obsolescence : Données dépassées avant d'être complètes
- Coût : 3000-5000 EUR/an en temps humain

Avec le scraping automatisé :
- Temps requis : 2-3 heures/an de supervision
- Précision : 99%+ grâce à la validation automatique
- Fraîcheur : Nouveautés détectées en 24h
- Coût : ~50 EUR/an (OpenAI + infrastructure)

---

## 2. Architecture du système actuel

Notre système se compose de 3 modules indépendants qui travaillent en séquence.

### Module A : Navigation Stealth (Playwright)

Rôle : Visiter les pages web sans être détecté comme un robot.

Analogie : C'est comme si votre assistant portait un déguisement pour ressembler à un visiteur humain normal. Il bouge sa souris, scrolle la page, attend quelques secondes avant de cliquer... exactement comme vous le feriez.

Technologies utilisées :
- Playwright : Navigateur automatisé (Chrome invisible)
- playwright-stealth : Techniques anti-détection avancées
  - Masquage des signaux d'automation (navigator.webdriver = false)
  - User-Agent réaliste (Firefox sur Mac)
  - Mouvements de souris simulés
  - Délais aléatoires entre actions (2-5 secondes)
  - Headers HTTP authentiques
  - Viewport dimensions réalistes (1920x1080)
  - Timezone et langue cohérentes avec l'IP

Pourquoi c'est nécessaire ?

Certains sites (comme RunRepeat) utilisent des systèmes anti-bot sophistiqués :
- Cloudflare Bot Management
- reCAPTCHA v3
- Détection de patterns de navigation
- Fingerprinting du navigateur

Notre système les contourne légalement en imitant un visiteur humain authentique.

Exemple de code (simplifié) :

```python
from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(
        viewport={'width': 1920, 'height': 1080},
        user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)...'
    )
    page = context.new_page()
    stealth_sync(page)  # Active les techniques anti-détection

    page.goto(url)
    page.wait_for_load_state('networkidle')  # Attend chargement complet
    html = page.content()
```

Résultat : HTML complet de la page (typiquement 500-1500 KB pour une fiche produit)

Exemple concret :
- Nike Pegasus 41 sur RunRepeat : 847 KB de HTML brut
- Contient : Specs + Reviews + Scripts + CSS + Images encodées + Analytics

Temps d'exécution : 8-12 secondes (dépend de la vitesse du site)

---

### Module B : Nettoyage HTML (BeautifulSoup)

Rôle : Réduire le HTML brut en ne gardant que l'essentiel.

Analogie : Votre assistant reçoit un magazine de 100 pages (le HTML brut) mais vous n'avez besoin que des 5 pages de l'article qui vous intéresse. Il découpe et jette les publicités, les images, les scripts JavaScript... et vous donne seulement le texte utile.

Éléments supprimés :
- Scripts JavaScript (analytics, tracking, interactivité)
- Styles CSS (couleurs, mise en page, animations)
- Images, vidéos, SVG, canvas
- Iframes (publicités, widgets externes)
- Métadonnées SEO inutiles
- Commentaires HTML
- Attributs de style inline
- Classes CSS et IDs
- Balises obsolètes (font, center, marquee)

Éléments conservés :
- Structure sémantique (h1-h6, p, ul, ol, li)
- Tableaux de données (table, tr, td, th)
- Texte brut et contenu textuel
- Liens importants (a href)
- Balises de définition (dl, dt, dd)
- Strong/em pour emphase sémantique

Algorithme de nettoyage :

```python
from bs4 import BeautifulSoup

soup = BeautifulSoup(html, 'html.parser')

# Suppression des éléments inutiles
for tag in soup(['script', 'style', 'img', 'svg', 'iframe', 'video']):
    tag.decompose()

# Suppression des attributs
for tag in soup.find_all(True):
    tag.attrs = {k: v for k, v in tag.attrs.items()
                 if k in ['href', 'title']}  # Garde seulement liens

# Extraction du texte structuré
cleaned_html = str(soup)
```

Résultat avant/après :

| Métrique | Avant (HTML brut) | Après (HTML nettoyé) | Réduction |
|----------|-------------------|----------------------|-----------|
| Taille fichier | 847 KB | 41 KB | 95.2% |
| Lignes de code | 12,453 | 589 | 95.3% |
| Tokens OpenAI | ~340,000 | ~16,000 | 95.3% |
| Coût OpenAI | ~0.102 USD | ~0.005 USD | 95.1% |

Pourquoi c'est important ?

1. Coût OpenAI réduit : On paie par token (mot). Moins de texte = beaucoup moins cher
   - Sans nettoyage : 0.102 USD par chaussure
   - Avec nettoyage : 0.002 USD par chaussure
   - Économie : 98% du coût d'extraction

2. Meilleure précision de l'IA :
   - L'IA se concentre sur les données utiles, pas sur le bruit
   - Réduit les hallucinations (inventions de données)
   - Améliore la cohérence des extractions

3. Vitesse accrue :
   - Moins de tokens = réponse plus rapide
   - Temps d'extraction : 15 sec → 3 sec

Temps d'exécution du nettoyage : 1-2 secondes

---

### Module C : Extraction IA (GPT-5 mini)

Rôle : Transformer le HTML nettoyé en données structurées (JSON).

Analogie : Votre assistant lit l'article de 5 pages et remplit un formulaire Excel avec les informations clés : Marque, Modèle, Poids, Prix, Pros, Cons...

Pourquoi l'IA plutôt que des règles fixes ?

Comparaison des approches :

| Critère | Approche classique (sélecteurs CSS) | Approche IA (GPT-5 mini) |
|---------|-------------------------------------|--------------------------|
| Robustesse | Casse dès que le site change sa structure | S'adapte automatiquement aux changements |
| Développement | Requiert de coder chaque champ manuellement | Un seul prompt pour tous les champs |
| Multi-sites | Code différent pour chaque site (15 codes différents) | Même code pour tous les sites |
| Temps de dev | 2-3h de développement par site | 10 min de configuration initiale |
| Maintenance | 1-2h/mois par site (corrections) | 0h (auto-adaptable) |
| Gestion des variations | Impossible (structure stricte requise) | Excellente (comprend les variations) |
| Données manquantes | Erreur ou valeur null | Extraction intelligente ou null justifié |
| Normalisation | Manuelle pour chaque format | Automatique (280g / 9.8oz → 280) |

Exemple concret de robustesse :

Site RunRepeat change sa structure HTML :
- Avant : `<div class="spec-weight">280g</div>`
- Après : `<span data-spec="weight">9.8 oz</span>`

Sélecteur CSS :
- Code avant : `soup.select_one('.spec-weight').text` → Fonctionne
- Code après : `soup.select_one('.spec-weight').text` → ERREUR (None)
- Fix requis : Réécrire le sélecteur + convertir oz → g

Approche IA :
- Avant : Trouve "280g" dans le HTML → extrait 280
- Après : Trouve "9.8 oz" dans le HTML → convertit automatiquement → extrait 280
- Fix requis : Aucun

Schéma de validation (Pydantic) :

L'IA doit respecter un format strict défini par notre schéma de données. Cela garantit la cohérence.

```python
from pydantic import BaseModel, Field
from typing import Optional, List

class RunningShoe(BaseModel):
    # Identification
    brand: str = Field(description="Marque (Nike, Adidas, etc.)")
    model_name: str = Field(description="Nom complet du modèle")

    # Specs numériques
    weight_g: Optional[int] = Field(None, ge=100, le=500,
                                     description="Poids en grammes")
    drop_mm: Optional[float] = Field(None, ge=0, le=15,
                                      description="Drop en mm")

    # Prix
    price_usd: Optional[float] = Field(None, ge=0, le=500)

    # Listes
    pros: List[str] = Field(default_factory=list)
    cons: List[str] = Field(default_factory=list)
```

Avantages de Pydantic :
- Validation automatique : weight_g doit être entre 100-500g (rejette valeurs aberrantes)
- Conversion de types : "280" (string) → 280 (int) automatiquement
- Valeurs par défaut : Si l'IA ne trouve pas de pros, liste vide (pas d'erreur)
- Documentation intégrée : Description de chaque champ pour guider l'IA

Prompt utilisé pour l'extraction :

```
Tu es un expert en extraction de données de chaussures de running.

À partir du HTML suivant, extrais TOUTES les informations disponibles
selon le schéma fourni. Sois précis et factuel.

Règles strictes :
1. Convertis toutes les unités en unités standards (g, mm, USD)
2. Si une donnée n'est pas trouvée, mets null (ne devine JAMAIS)
3. Pour les scores sur 5, normalise sur 100 (3/5 → 60)
4. Pour les pros/cons, liste max 10 points clairs et concis
5. Extrais les valeurs numériques brutes (280g → 280)

HTML :
{html_nettoyé}

Schéma de sortie :
{schéma_pydantic}
```

Exemple de sortie JSON :

```json
{
  "brand": "Nike",
  "model_name": "Nike Vomero Plus",
  "weight_g": 289,
  "drop_mm": 9.6,
  "stack_heel_mm": 42.3,
  "price_usd": 180.0,
  "pros": [
    "Full ZoomX midsole provides energetic bounce",
    "Outstanding shock absorption in heel and forefoot",
    "Premium comfort for walking and long runs"
  ],
  "cons": [
    "Heavier than ideal",
    "Snug fit and narrow toebox"
  ]
}
```

Technologies utilisées :

OpenAI GPT-5 mini
   - Modèle : gpt-5-mini (optimisé coût/performance)
   - Structured Outputs : Force le respect du schéma Pydantic
   - Temperature : 0.1 (très déterministe, peu de créativité)

---

## 3. Données récupérées et leur valeur

### Vue d'ensemble : 43 champs structurés

Le système extrait actuellement 43 champs de données par chaussure, organisés en 6 catégories fonctionnelles.

Pourquoi 43 champs ?
- Benchmark industrie : Sites concurrents ont 10-20 champs
- Notre avantage : Données lab tests objectives (26 champs exclusifs)
- Couverture : 95% des critères de décision d'achat identifiés

---

### Catégorie 1 : Identification (5 champs)

Ces champs permettent d'identifier de manière unique chaque chaussure.

| Champ | Type | Exemple | Intérêt business | Requis |
|-------|------|---------|------------------|--------|
| brand | string | "Nike" | Filtrer par marque préférée, stats marché | Oui |
| model_name | string | "Nike Vomero Plus" | Identifier la chaussure unique | Oui |
| category | enum | "road" | Filtrer route / trail / racing | Oui |
| gender | enum | "unisex" | Adapter recommandations morpho | Non |
| source_url | string | "https://runrepeat.com/..." | Traçabilité, mise à jour, vérification | Oui |

Valeurs possibles :
- category : "road", "trail", "racing", "walking", "training"
- gender : "men", "women", "unisex", null

Cas d'usage :
- Recherche : "Trouve-moi toutes les chaussures de trail Nike"
- Analytics : "Quelle est la marque la plus représentée ?"
- Traçabilité : "D'où vient cette donnée ? Quand a-t-elle été scrapée ?"

---

### Catégorie 2 : Specs Techniques de Base (8 champs)

Ces champs sont les critères de décision principaux pour 80% des coureurs.

| Champ | Type | Exemple | Unité | Plage typique | Intérêt coureur |
|-------|------|---------|-------|---------------|-----------------|
| weight_g | int | 289 | grammes | 150-400g | Chaussure légère (< 250g) vs lourde (> 300g) |
| drop_mm | float | 9.6 | mm | 0-12mm | Foulée naturelle (0-4mm) vs protectrice (> 10mm) |
| stack_heel_mm | float | 42.3 | mm | 15-50mm | Amorti maximal (> 40mm) vs minimaliste (< 25mm) |
| stack_forefoot_mm | float | 32.7 | mm | 12-45mm | Protection avant-pied |
| price_usd | float | 180.0 | USD | 60-300 USD | Budget utilisateur, comparaison valeur |
| pace | string | "Daily running" | catégorie | - | Usage quotidien / tempo / compétition |
| arch_support | string | "Neutral" | catégorie | - | Neutre / Stabilité / Pronateur |
| strike_pattern | string | "Heel, Mid/forefoot" | catégorie | - | Type de foulée recommandé |

Explications détaillées :

1. weight_g (Poids)
   - Impact : Chaque 100g = 1% d'énergie supplémentaire
   - Légère : < 250g (compétition)
   - Moyenne : 250-300g (polyvalente)
   - Lourde : > 300g (protection maximale)

2. drop_mm (Drop/Dénivelé)
   - Définition : Différence de hauteur talon-avant-pied
   - Drop 0mm : Barefoot, foulée naturelle
   - Drop 4-6mm : Polyvalent, tendance actuelle
   - Drop 10-12mm : Protection, coureurs débutants

3. stack_heel_mm (Hauteur d'amorti au talon)
   - Tendance : Augmentation ces 5 dernières années
   - Minimaliste : < 20mm
   - Classique : 20-35mm
   - Maximaliste : > 40mm (ex: Hoka, Nike Vomero)

4. price_usd (Prix)
   - Entry : 60-100 USD
   - Mid-range : 100-150 USD
   - Premium : 150-200 USD
   - Super-premium : > 200 USD (ex: Vaporfly)

Valeurs possibles :
- pace : "Daily running", "Tempo", "Racing", "Recovery", "Trail running"
- arch_support : "Neutral", "Stability", "Motion control", "Cushioned"
- strike_pattern : "Heel", "Midfoot", "Forefoot", "Heel, Mid/forefoot"

Cas d'usage :
- Filtrage : "Chaussures neutres de moins de 250g pour compétition"
- Recommandation : "Tu attaques du talon ? Je te conseille un drop > 8mm"
- Comparaison : "La Pegasus 41 est 15g plus légère que la Vomero"

---

### Catégorie 3 : Tests de Laboratoire - Performance (10 champs)

Ces données proviennent de tests objectifs en laboratoire (pas d'avis subjectifs).

Avantage compétitif majeur : 90% des sites n'ont PAS ces données. Elles proviennent de RunRepeat qui possède un laboratoire de tests indépendant.

| Champ | Type | Exemple | Unité | Plage | Signification | Méthode de test |
|-------|------|---------|-------|-------|---------------|-----------------|
| shock_absorption_heel_sa | float | 147.0 | SA | 100-170 | Absorption des chocs au talon | Appareil de choc calibré |
| shock_absorption_forefoot_sa | float | 131.0 | SA | 90-160 | Absorption avant-pied | Appareil de choc calibré |
| energy_return_pct | float | 67.1 | % | 55-75% | Rebond de la mousse (talon) | Test de compression répétée |
| energy_return_forefoot_pct | float | 68.8 | % | 55-75% | Rebond avant-pied | Test de compression répétée |
| cushioning_softness_ha | int | 15 | Shore A | 10-35 | Dureté mousse (plus bas = plus mou) | Duromètre Shore A |
| flexibility_index | float | 19.8 | Newtons | 10-40 | Rigidité longitudinale | Machine de flexion |
| torsional_rigidity_index | int | 4.0 | 1-5 | 1-5 | Rigidité torsion | Test de torsion manuelle |
| traction_coefficient | float | 0.42 | coefficient | 0.3-0.7 | Adhérence | Test sur surface standardisée |
| breathability_score | int | 3 | 1-5 | 1-5 | Respirabilité | Test avec fumée/capteurs |
| midsole_softness_cold_pct | float | 6.0 | % | 0-20% | Changement de dureté au froid | Test à -10°C |

Explications détaillées :

1. shock_absorption_XX_sa (Absorption des chocs)
   - Définition : Capacité à absorber l'impact au sol
   - Mesure : SA (Shock Absorption) - unité propriétaire RunRepeat
   - Plus élevé = meilleure protection
   - Important pour : Coureurs lourds, longues distances, surfaces dures
   - Exemple : 147 SA = excellent pour marathons sur route

2. energy_return_pct (Retour d'énergie)
   - Définition : % d'énergie restituée après compression
   - Technologie : ZoomX (Nike) ~70%, Boost (Adidas) ~65%, EVA standard ~58%
   - Plus élevé = sensation de rebond, économie d'énergie
   - Important pour : Vitesse, longues distances
   - Contre-exemple : Chaussures de récupération ont volontairement un faible retour

3. cushioning_softness_ha (Dureté de la mousse)
   - Définition : Résistance à la pénétration (Shore A scale)
   - Plus bas = plus mou (mais pas toujours mieux)
   - Soft (10-20 HA) : Confort max, peu de stabilité
   - Medium (20-28 HA) : Équilibre
   - Firm (> 28 HA) : Stabilité, réactivité

4. flexibility_index (Flexibilité)
   - Définition : Force requise pour plier la chaussure à 45°
   - Plus bas = plus flexible
   - Flexible (< 15N) : Foulée naturelle
   - Rigide (> 30N) : Guidage, compétition (plaque carbone)

5. torsional_rigidity_index (Rigidité en torsion)
   - Définition : Résistance à la torsion médio-pied
   - Important pour : Stabilité, pronateurs
   - Score 1-2 : Très flexible (minimaliste)
   - Score 3-4 : Équilibré
   - Score 5 : Très rigide (chaussures de stabilité)

6. traction_coefficient (Adhérence)
   - Définition : Coefficient de friction sur surface mouillée
   - 0.3 = Faible (glissant)
   - 0.5 = Bon
   - 0.7 = Excellent (trail)
   - Important pour : Pluie, sentiers mouillés

7. breathability_score (Respirabilité)
   - Test : Chaussure remplie de fumée, mesure temps de dissipation
   - Score 1 : Très peu respirant (imperméable)
   - Score 3 : Bon
   - Score 5 : Très respirant (mesh aéré)

8. midsole_softness_cold_pct (Performance au froid)
   - Définition : % de durcissement de la mousse à -10°C
   - < 5% : Excellent (performance stable hiver)
   - 10-15% : Moyen (durcit notablement)
   - > 15% : Mauvais (devient très dur au froid)
   - Important pour : Coureurs hiver, climats froids

Valeur business :

Ces données sont EXCLUSIVES et OBJECTIVES :
- Différenciation : Seuls 2-3 sites au monde ont ces données
- Fiabilité : Tests standardisés, reproductibles
- Comparabilité : Même protocole pour toutes les chaussures
- Crédibilité : Arguments de vente factuels vs marketing

Cas d'usage :
- Recommandation avancée : "Tu fais 85kg ? Je te conseille un shock absorption > 140 SA"
- Comparaison technique : "La ZoomX a 8% de retour d'énergie en plus que la Boost"
- Filtres experts : "Chaussures avec flexibilité < 20N et rigidité torsion > 3"

---

### Catégorie 4 : Dimensions Détaillées (7 champs)

Ces dimensions résolvent le problème n°1 de l'achat en ligne : le fit (ajustement).

Stat industrie : 30-40% des retours de chaussures sont dus à un mauvais ajustement.

Notre avantage : Mesures au pied à coulisse (précision 0.1mm).

| Champ | Type | Exemple | Unité | Plage | Intérêt | Mesure |
|-------|------|---------|-------|-------|---------|--------|
| toebox_width_mm | float | 71.1 | mm | 65-85mm | Pieds larges, oignons | Largeur interne avant-pied |
| toebox_height_mm | float | 26.2 | mm | 22-32mm | Orteils hauts, confort | Hauteur interne avant-pied |
| width_fit_mm | float | 94.6 | mm | 85-105mm | Largeur générale du chaussant | Largeur au ball of foot |
| midsole_width_forefoot_mm | float | 117.0 | mm | 100-130mm | Stabilité avant-pied | Largeur semelle avant |
| midsole_width_heel_mm | float | 99.2 | mm | 85-110mm | Stabilité talon | Largeur semelle talon |
| outsole_thickness_mm | float | 2.9 | mm | 2-5mm | Durabilité, adhérence | Épaisseur caoutchouc |
| tongue_padding_mm | float | 11.2 | mm | 6-15mm | Confort langue | Épaisseur mousse langue |

Explications détaillées :

1. toebox_width_mm (Largeur avant-pied)
   - Très étroit : < 68mm (chaussures racing)
   - Étroit : 68-72mm (Nike, Adidas classique)
   - Normal : 72-76mm
   - Large : 76-80mm (Altra, Topo)
   - Très large : > 80mm (Altra Paradigm)

   Cas d'usage :
   - "J'ai des pieds larges" → Recommander > 76mm
   - "J'ai des oignons (hallux valgus)" → Recommander > 78mm
   - "Je veux du barefoot" → Recommander > 80mm

2. toebox_height_mm (Hauteur avant-pied)
   - Bas : < 24mm (racing, ajusté)
   - Normal : 24-28mm
   - Haut : > 28mm (confort, orteils en marteau)

   Important pour :
   - Orteils en marteau
   - Coureurs qui aiment de l'espace
   - Éviter ongles noirs (frottements)

3. width_fit_mm (Largeur générale)
   - Correspond au ball of foot (partie la plus large du pied)
   - Référence pour les largeurs B/D/2E/4E
   - D (standard homme) : ~94mm
   - 2E (wide) : ~98mm
   - 4E (extra-wide) : ~102mm

4. midsole_width_XX_mm (Largeur de la semelle)
   - Plus large = plus de stabilité
   - Hoka One One : 115-125mm (très stable)
   - Nike Vaporfly : 100-105mm (moins stable, plus rapide)

   Important pour :
   - Pronateurs (besoin de largeur talon)
   - Trail (stabilité sur terrains irréguliers)
   - Coureurs lourds (base large)

5. outsole_thickness_mm (Épaisseur de la semelle extérieure)
   - Fin (< 3mm) : Légèreté, feeling, durabilité réduite
   - Épais (> 4mm) : Durabilité excellente, poids accru

   ROI :
   - 3mm vs 4mm = +30% durée de vie
   - Important pour gros kilométrage (> 60km/semaine)

6. tongue_padding_mm (Rembourrage de la langue)
   - Fin (< 8mm) : Léger, racing
   - Normal (8-12mm) : Confort standard
   - Épais (> 12mm) : Confort max, pression lacets

   Important pour :
   - Serrage très fort (langue épaisse protège)
   - Cou-de-pied haut (besoin d'espace)

Valeur business :

Ces données réduisent drastiquement les retours :
- Avant : 35% de retours pour mauvais fit
- Avec dimensions + recommandations : ~10-15% de retours
- ROI : Économie de logistique inverse + satisfaction client

Cas d'usage :
- Quiz personnalisé : "Tu as des pieds larges ?" → Filtre toebox_width > 76mm
- Comparaison : "La Brooks Ghost est 3mm plus large que la Nike Pegasus"
- Recommandation proactive : "Attention, cette chaussure a un toebox étroit (68mm)"

---

### Catégorie 5 : Durabilité (4 champs)

Prédire la durée de vie = ROI pour le coureur.

Méthodologie RunRepeat : Tests destructifs standardisés.

| Champ | Type | Exemple | Unité | Plage | Méthode de test |
|-------|------|---------|-------|-------|-----------------|
| toebox_durability_score | int | 3 | 1-5 | 1-5 | Test Dremel (abrasion 30sec) |
| heel_padding_durability_score | int | 4 | 1-5 | 1-5 | Test compression (1000 cycles) |
| outsole_durability_score | int | 4 | 1-5 | 1-5 | Test abrasion (surface rugueuse) |
| outsole_wear_mm | float | 0.8 | mm | 0.3-2mm | Mesure usure après test standard |

Explications :

1. toebox_durability_score
   - Test : Outil Dremel (ponceuse) sur mesh pendant 30 secondes
   - Score 1 : Trou immédiat (mesh fin)
   - Score 3 : Résistance normale
   - Score 5 : Très résistant (mesh renforcé, overlays)

   Durée de vie estimée :
   - Score 1-2 : 400-600 km
   - Score 3 : 600-800 km
   - Score 4-5 : 800-1200 km

2. heel_padding_durability_score
   - Test : Compression répétée 1000 cycles
   - Mesure : % de perte de hauteur
   - Score 5 : < 5% de perte (mousse haute densité)
   - Score 3 : 10-15% de perte
   - Score 1 : > 20% de perte (s'affaisse rapidement)

3. outsole_durability_score
   - Test : Abrasion sur bande rugueuse (simulation asphalte)
   - Mesure : Perte de matière après X cycles
   - Score 5 : Caoutchouc haute densité (ex: Continental, Vibram)
   - Score 3 : Caoutchouc standard
   - Score 1 : Mousse exposée (s'use très vite)

4. outsole_wear_mm
   - Mesure directe de l'usure après test standard
   - 0.5mm : Excellent (caoutchouc dur type trail)
   - 1.0mm : Bon (la plupart des chaussures route)
   - 2.0mm : Faible (mousse légère type racing)

Calcul de durée de vie totale :

Formule simplifiée :
```
Durée de vie (km) = 600 + (moyenne_scores_durabilité * 100)

Exemple Nike Vomero Plus :
- Scores : 3, 4, 4 (null ignoré)
- Moyenne : (3+4+4)/3 = 3.67
- Durée estimée : 600 + (3.67 * 100) = 967 km
```

Valeur business :

- Argument de vente : "Cette chaussure durera 900+ km, soit 30% de plus que la concurrence"
- ROI : Chaussure à 180 USD sur 900 km = 0.20 USD/km vs 150 USD sur 600 km = 0.25 USD/km
- Segmentation : Coureurs intensifs vs occasionnels

Cas d'usage :
- Recommandation : "Tu fais 80km/semaine ? Prends une chaussure score > 4 en durabilité"
- Comparaison : "La Brooks Ghost dure 200km de plus que la Nike Pegasus"
- Alerte : "Attention, cette chaussure racing a une faible durabilité (400-500km)"

---

### Catégorie 6 : Métadonnées & Features (9 champs)

Informations complémentaires sur disponibilité, saisonnalité, et avis qualitatifs.

| Champ | Type | Exemple | Valeurs possibles | Intérêt |
|-------|------|---------|-------------------|---------|
| widths_available | list | ["Normal", "Wide", "X-Wide"] | B, D, 2E, 4E, etc. | Pieds larges, fit personnalisé |
| season | string | "All seasons" | Summer, Winter, All seasons | Conditions climatiques |
| removable_insole | bool | true | true/false | Compatible semelles orthopédiques |
| reflective_elements | bool | true | true/false | Sécurité course de nuit |
| score | float | 4.2 | 0-5 | Note agrégée |
| pros | list | [9 points positifs] | - | Résumé IA des avantages |
| cons | list | [4 points négatifs] | - | Résumé IA des défauts |
| insole_thickness_mm | float | 3.3 | mm | 2-6mm | Confort, enlever pour gain de place |
| heel_counter_stiffness_score | int | 3 | 1-5 | Maintien talon, stabilité |

Explications :

1. widths_available
   - Système américain : B (narrow women), D (standard), 2E (wide), 4E (x-wide)
   - Marques généreuses : Altra (toutes en wide), New Balance (5 largeurs)
   - Marques étroites : Nike (souvent D uniquement)

2. season
   - Summer : Mesh très aéré, léger
   - Winter : Gore-Tex, imperméable, isolation
   - All seasons : Polyvalent (80% des chaussures)

3. removable_insole
   - Important pour : Semelles orthopédiques, ajustement volume
   - 90% des chaussures = true
   - Racing shoes = parfois false (gain de poids)

4. reflective_elements
   - Sécurité : Visibilité de nuit
   - Critère légal dans certains pays
   - Tendance : 70% des nouvelles chaussures en ont

5. score
   - Agrégation des avis utilisateurs
   - Généralement sur 5
   - Attention : Subjectif, biais (avis négatifs surreprésentés)

6. pros/cons (listes de texte)
   - Extraction IA depuis reviews
   - Format : Phrases courtes, actionnables
   - Limite : 10 pros max, 10 cons max
   - Valeur : Résumé rapide pour l'utilisateur

Exemples de pros/cons (Nike Vomero Plus) :

Pros :
- "Full ZoomX midsole provides energetic bounce"
- "Outstanding shock absorption in heel and forefoot"
- "True high-stack design"
- "Premium comfort for walking and long runs"
- "Strong durability"
- "Great for easy/recovery days"
- "Midsole resists cold well"
- "Comfortable heel counter"
- "Solid Bondi alternative inside Nike"

Cons :
- "Heavier than ideal"
- "Snug fit and narrow toebox"
- "Non-gusseted tongue"
- "Traction needs improvement"

7. insole_thickness_mm
   - Impact sur volume interne chaussure
   - Enlever semelle = +2-4mm d'espace
   - Important pour pieds hauts

8. heel_counter_stiffness_score
   - Rigidité du contrefort talon
   - Score 1 : Très souple (minimaliste)
   - Score 3 : Standard
   - Score 5 : Très rigide (stabilité max)
   - Important pour pronateurs

Valeur business :

Ces métadonnées complètent le profil de chaque chaussure :
- Filtres additionnels (recherche avancée)
- Arguments de vente ("Compatible orthopédiques !")
- SEO (mots-clés pros/cons)

---

## 4. Base de données : Structure recommandée

### Pourquoi migrer de Excel vers PostgreSQL ?

Limitations actuelles d'Excel :

1. Performance
   - Excel ralentit au-delà de 10,000 lignes
   - Pas de requêtes complexes (filtres, agrégations, jointures)
   - Ouverture fichier : 5-10 secondes pour 5 MB

2. Intégrité des données
   - Pas de validation stricte (erreurs de saisie fréquentes)
   - Doublons non détectés
   - Types de données non forcés (texte dans colonne numérique)

3. Collaboration
   - Conflits de versions (fichier_v1.xlsx, fichier_v2_final.xlsx)
   - Pas de gestion multi-utilisateurs
   - Pas d'historique des modifications

4. Évolutivité
   - Duplication FR/EN (27 colonnes inutiles)
   - Pas de relations entre tables
   - Impossible d'intégrer dans une application web

Avantages de PostgreSQL :

1. Performance
   - Gère des millions de lignes sans ralentissement
   - Requêtes SQL optimisées (index, plans d'exécution)
   - Temps de réponse : < 50ms même avec 100,000 chaussures

2. Intégrité
   - Contraintes de types (INT, FLOAT, VARCHAR)
   - Contraintes d'unicité (pas de doublons)
   - Contraintes de plage (CHECK weight_g BETWEEN 100 AND 500)
   - Foreign keys (relations entre tables)

3. Fonctionnalités avancées
   - pgvector : Similarité sémantique (RAG, recommandations IA)
   - JSON : Stockage flexible (pros/cons, métadonnées)
   - Full-text search : Recherche textuelle performante
   - Triggers : Actions automatiques (audit, validation)

4. Écosystème
   - Compatible avec tous les frameworks web (Django, FastAPI)
   - ORM (SQLAlchemy, Pydantic-SQL)
   - Backup automatique, réplication, haute disponibilité

---

### Schéma SQL complet

Table principale : running_shoes

```sql
CREATE TABLE running_shoes (
    -- Identification & Métadonnées
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT gen_random_uuid() UNIQUE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    scraped_at TIMESTAMPTZ,
    source_url VARCHAR(500) NOT NULL,

    -- Identification produit
    brand VARCHAR(100) NOT NULL,
    model_name VARCHAR(200) NOT NULL,
    category VARCHAR(50) CHECK (category IN ('road', 'trail', 'racing', 'walking', 'training')),
    gender VARCHAR(20) CHECK (gender IN ('men', 'women', 'unisex')),

    -- Specs techniques de base
    weight_g INT CHECK (weight_g BETWEEN 100 AND 500),
    drop_mm DECIMAL(4,2) CHECK (drop_mm BETWEEN 0 AND 15),
    stack_heel_mm DECIMAL(5,2) CHECK (stack_heel_mm BETWEEN 0 AND 60),
    stack_forefoot_mm DECIMAL(5,2) CHECK (stack_forefoot_mm BETWEEN 0 AND 50),
    price_usd DECIMAL(6,2) CHECK (price_usd BETWEEN 0 AND 500),

    -- Catégories d'usage
    pace VARCHAR(50),
    arch_support VARCHAR(50),
    strike_pattern VARCHAR(100),

    -- Tests de laboratoire - Performance
    shock_absorption_heel_sa DECIMAL(6,2),
    shock_absorption_forefoot_sa DECIMAL(6,2),
    energy_return_pct DECIMAL(5,2) CHECK (energy_return_pct BETWEEN 0 AND 100),
    energy_return_forefoot_pct DECIMAL(5,2) CHECK (energy_return_pct BETWEEN 0 AND 100),
    cushioning_softness_ha INT CHECK (cushioning_softness_ha BETWEEN 0 AND 50),
    flexibility_index DECIMAL(5,2),
    torsional_rigidity_index INT CHECK (torsional_rigidity_index BETWEEN 1 AND 5),
    traction_coefficient DECIMAL(4,3) CHECK (traction_coefficient BETWEEN 0 AND 1),
    breathability_score INT CHECK (breathability_score BETWEEN 1 AND 5),
    midsole_softness_cold_pct DECIMAL(5,2),

    -- Dimensions détaillées
    toebox_width_mm DECIMAL(5,2),
    toebox_height_mm DECIMAL(5,2),
    width_fit_mm DECIMAL(5,2),
    midsole_width_forefoot_mm DECIMAL(5,2),
    midsole_width_heel_mm DECIMAL(5,2),
    outsole_thickness_mm DECIMAL(4,2),
    insole_thickness_mm DECIMAL(4,2),
    tongue_padding_mm DECIMAL(4,2),

    -- Durabilité
    toebox_durability_score INT CHECK (toebox_durability_score BETWEEN 1 AND 5),
    heel_padding_durability_score INT CHECK (heel_padding_durability_score BETWEEN 1 AND 5),
    outsole_durability_score INT CHECK (outsole_durability_score BETWEEN 1 AND 5),
    outsole_wear_mm DECIMAL(4,2),

    -- Métadonnées & Features
    score DECIMAL(3,2) CHECK (score BETWEEN 0 AND 5),
    widths_available TEXT[], -- Array PostgreSQL
    season VARCHAR(50),
    removable_insole BOOLEAN,
    reflective_elements BOOLEAN,
    heel_counter_stiffness_score INT CHECK (heel_counter_stiffness_score BETWEEN 1 AND 5),

    -- Avis qualitatifs (JSON pour flexibilité)
    pros JSONB,
    cons JSONB,

    -- Contraintes d'unicité
    CONSTRAINT unique_shoe UNIQUE (brand, model_name, source_url)
);

-- Index pour performance
CREATE INDEX idx_brand ON running_shoes(brand);
CREATE INDEX idx_category ON running_shoes(category);
CREATE INDEX idx_price ON running_shoes(price_usd);
CREATE INDEX idx_weight ON running_shoes(weight_g);
CREATE INDEX idx_drop ON running_shoes(drop_mm);
CREATE INDEX idx_scraped_at ON running_shoes(scraped_at DESC);

-- Index full-text search
CREATE INDEX idx_model_name_fts ON running_shoes USING gin(to_tsvector('english', model_name));

-- Trigger pour updated_at automatique
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_running_shoes_updated_at
BEFORE UPDATE ON running_shoes
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();
```

---

### Tables complémentaires

Table scraping_logs : Suivi des exécutions

```sql
CREATE TABLE scraping_logs (
    id SERIAL PRIMARY KEY,
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    source_site VARCHAR(100) NOT NULL,
    status VARCHAR(20) CHECK (status IN ('running', 'completed', 'failed', 'partial')),
    shoes_scraped INT DEFAULT 0,
    shoes_failed INT DEFAULT 0,
    error_message TEXT,
    execution_time_seconds INT,
    cost_usd DECIMAL(8,4)
);

CREATE INDEX idx_scraping_logs_started_at ON scraping_logs(started_at DESC);
```

Utilité :
- Monitoring : Voir l'historique des scraping
- Debugging : Identifier les erreurs récurrentes
- Analytics : Coût par site, taux de succès, temps d'exécution

Table price_history : Historique des prix

```sql
CREATE TABLE price_history (
    id SERIAL PRIMARY KEY,
    shoe_id INT REFERENCES running_shoes(id) ON DELETE CASCADE,
    price_usd DECIMAL(6,2) NOT NULL,
    recorded_at TIMESTAMPTZ DEFAULT NOW(),
    source_url VARCHAR(500)
);

CREATE INDEX idx_price_history_shoe_id ON price_history(shoe_id);
CREATE INDEX idx_price_history_recorded_at ON price_history(recorded_at DESC);
```

Utilité :
- Tracking prix : Détecter les promotions
- Alertes : "Prix baissé de 20% !"
- Analytics : Évolution prix dans le temps
- Machine Learning : Prédire meilleur moment d'achat

Table duplicate_candidates : Détection de doublons

```sql
CREATE TABLE duplicate_candidates (
    id SERIAL PRIMARY KEY,
    shoe_a_id INT REFERENCES running_shoes(id) ON DELETE CASCADE,
    shoe_b_id INT REFERENCES running_shoes(id) ON DELETE CASCADE,
    similarity_score DECIMAL(5,4) CHECK (similarity_score BETWEEN 0 AND 1),
    detected_at TIMESTAMPTZ DEFAULT NOW(),
    status VARCHAR(20) CHECK (status IN ('pending', 'confirmed_duplicate', 'not_duplicate', 'merged')) DEFAULT 'pending',
    reviewed_by VARCHAR(100),
    reviewed_at TIMESTAMPTZ,

    CONSTRAINT unique_duplicate_pair UNIQUE (shoe_a_id, shoe_b_id)
);

CREATE INDEX idx_duplicate_candidates_status ON duplicate_candidates(status);
CREATE INDEX idx_duplicate_candidates_similarity ON duplicate_candidates(similarity_score DESC);
```

Utilité :
- Human-in-the-loop : Queue de validation
- Historique : Quels doublons ont été fusionnés
- Amélioration algorithme : Analyser faux positifs

Table scraping_sources : Gestion des sites à scraper

```sql
CREATE TABLE scraping_sources (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    base_url VARCHAR(200) NOT NULL,
    language VARCHAR(5) CHECK (language IN ('en', 'fr', 'es', 'de')),
    source_type VARCHAR(50) CHECK (source_type IN ('lab_tests', 'reviews', 'price_comparison', 'database')),
    is_active BOOLEAN DEFAULT true,
    scraping_frequency VARCHAR(20) CHECK (scraping_frequency IN ('daily', 'weekly', 'monthly')),
    last_scraped_at TIMESTAMPTZ,
    priority INT CHECK (priority BETWEEN 1 AND 10) DEFAULT 5,
    notes TEXT
);

-- Données initiales (les 15 sites)
INSERT INTO scraping_sources (name, base_url, language, source_type, scraping_frequency, priority) VALUES
('RunRepeat', 'https://runrepeat.com', 'en', 'lab_tests', 'daily', 10),
('The Sneaker Database', 'https://thesneakerdatabase.com', 'en', 'database', 'weekly', 8),
('Running Shoes Guru', 'https://runningshoesguru.com', 'en', 'reviews', 'weekly', 7),
('Chaussure Running', 'https://www.chaussure-running.net', 'fr', 'reviews', 'weekly', 9),
('Running Addict', 'https://www.running-addict.fr', 'fr', 'reviews', 'weekly', 8),
('RunActu', 'https://www.runactu.fr', 'fr', 'reviews', 'weekly', 6),
('Journal du Trail', 'https://www.journaldutrail.com', 'fr', 'reviews', 'weekly', 6),
('RunPack', 'https://www.runpack.fr', 'fr', 'reviews', 'weekly', 5),
('Stadion Actu', 'https://www.stadionactu.com', 'fr', 'reviews', 'weekly', 5),
('Trail & Running', 'https://www.trail-running.fr', 'fr', 'reviews', 'weekly', 6),
('The Running Collective', 'https://www.therunningcollective.com', 'fr', 'price_comparison', 'daily', 9),
('Believe in the Run', 'https://www.believeintherun.com', 'en', 'reviews', 'weekly', 7),
('Doctors of Running', 'https://www.doctorsofrunning.com', 'en', 'reviews', 'weekly', 8),
('WearTesters', 'https://weartesters.com', 'en', 'reviews', 'weekly', 6),
('Solereview', 'https://www.solereview.com', 'en', 'reviews', 'weekly', 7);
```

---

### Extension pgvector pour RAG

Installation de l'extension :

```sql
CREATE EXTENSION IF NOT EXISTS vector;

-- Ajout de colonne embedding à la table running_shoes
ALTER TABLE running_shoes
ADD COLUMN embedding vector(1536); -- Dimension OpenAI embeddings

-- Index pour recherche de similarité rapide
CREATE INDEX idx_running_shoes_embedding ON running_shoes
USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
```

Utilité :

1. Recherche sémantique
   - Question : "Chaussure confortable pour marathon"
   - Embedding de la question → Recherche les chaussures similaires
   - Retourne : Chaussures avec bon amorti, durabilité, stack élevé

2. Recommandations IA
   - Utilisateur aime Nike Pegasus 41
   - Embedding de la Pegasus → Recherche chaussures similaires
   - Retourne : Alternatives (Asics Nimbus, Brooks Ghost, etc.)

3. Détection de doublons améliorée
   - "Nike Vomero Plus" vs "Vomero Plus by Nike" vs "Nike Vomero+"
   - Similarity > 0.95 → Probablement la même chaussure

Exemple de requête RAG :

```sql
-- Trouver les 5 chaussures les plus similaires à une chaussure donnée
SELECT
    id,
    brand,
    model_name,
    1 - (embedding <=> (SELECT embedding FROM running_shoes WHERE id = 123)) AS similarity
FROM running_shoes
WHERE id != 123
ORDER BY embedding <=> (SELECT embedding FROM running_shoes WHERE id = 123)
LIMIT 5;
```

---

### Migration depuis Excel

Script Python de migration :

```python
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values

# Lire Excel
df = pd.read_excel('sm_datas_global.xlsx')

# Nettoyage
# - Supprimer colonnes FR (doublons)
# - Renommer colonnes EN vers nos noms de champs
# - Convertir types

# Connexion PostgreSQL
conn = psycopg2.connect(
    host="localhost",
    database="stridematch",
    user="postgres",
    password="password"
)

# Insertion
with conn.cursor() as cur:
    # Préparer données
    values = [
        (
            row['brand'],
            row['model_name'],
            row['weight_g'],
            # ... tous les champs
        )
        for _, row in df.iterrows()
    ]

    # Insertion batch (performant)
    execute_values(
        cur,
        """
        INSERT INTO running_shoes
        (brand, model_name, weight_g, ...)
        VALUES %s
        ON CONFLICT (brand, model_name, source_url) DO NOTHING
        """,
        values
    )

conn.commit()
```

---

## 5. Gap avec le catalogue actuel

### État des lieux du fichier Excel existant

Fichier analysé : sm_datas_global (2).xlsx

Statistiques :
- Format : .xlsx (Excel)
- Nombre de colonnes : 54
- Nombre de chaussures : 142
- Taille fichier : ~850 KB

Structure :
- 27 colonnes FR (doublons des colonnes EN)
- 27 colonnes EN
- Colonnes non dupliquées : Marque, Modèle, Lien, etc.

---

### Analyse de complétude

Colonnes avec données manquantes :

| Colonne | Taux de remplissage | Problème |
|---------|---------------------|----------|
| Largeur talon (mm) | 0% | 100% vide (142/142) |
| Prix | 0% | 100% vide (à compléter) |
| Lien produit | 0% | 100% vide (pas de traçabilité) |
| Drop (mm) | 45% | 55% manquant (78/142) |
| Poids (g) | 62% | 38% manquant (54/142) |

Constat : Données incomplètes, nécessitant scraping pour combler.

---

### Comparaison Excel vs Scraping

Champs présents dans les deux :

| # | Champ | Excel | Scraping | Cohérence |
|---|-------|-------|----------|-----------|
| 1 | Marque | Oui | Oui (brand) | Compatible |
| 2 | Modèle | Oui | Oui (model_name) | Compatible |
| 3 | Poids (g) | Oui (62%) | Oui (100%) | Compatible |
| 4 | Drop (mm) | Oui (45%) | Oui (100%) | Compatible |
| 5 | Stack talon (mm) | Oui | Oui | Compatible |
| 6 | Stack avant-pied (mm) | Oui | Oui | Compatible |
| 7 | Prix | Oui (0%) | Oui (95%) | Complémentaire |
| 8 | Catégorie | Oui | Oui (road/trail) | Compatible |
| 9 | Genre | Oui | Oui | Compatible |
| 10 | Largeur avant-pied (mm) | Oui | Oui (toebox_width) | Compatible |
| 11 | Hauteur avant-pied (mm) | Oui | Oui (toebox_height) | Compatible |
| 12 | Type de foulée | Oui | Oui (arch_support) | Compatible |
| 13 | Usage | Oui | Oui (pace) | Compatible |

Total : 13 champs communs

Nouveaux champs apportés par le scraping (26 champs) :

| Catégorie | Nouveaux champs | Exemple |
|-----------|-----------------|---------|
| Tests lab performance | 10 champs | shock_absorption_heel_sa, energy_return_pct, flexibility_index |
| Dimensions avancées | 5 champs | midsole_width_forefoot_mm, outsole_thickness_mm, tongue_padding_mm |
| Durabilité | 4 champs | toebox_durability_score, outsole_wear_mm |
| Métadonnées | 7 champs | widths_available, removable_insole, reflective_elements, pros, cons |

Total : 13 (communs) + 26 (nouveaux) = 39 champs exploitables

---

### Problèmes identifiés dans l'Excel

1. Doublons FR/EN
   - 27 colonnes dupliquées inutilement
   - Augmente taille fichier (+50%)
   - Risque d'incohérence (traduction manuelle)
   - Solution : Traduction dynamique côté application

2. Colonnes 100% vides
   - 5 colonnes jamais remplies
   - Prennent de la place
   - Confusent l'utilisateur
   - Solution : Supprimer ou remplir via scraping

3. Unités incohérentes
   - Certains poids en "g", d'autres en "oz"
   - Certains prix en "EUR", d'autres en "USD"
   - Solution : Normalisation automatique dans PostgreSQL

4. Pas de traçabilité
   - Aucun lien source
   - Impossible de vérifier données
   - Impossible de mettre à jour automatiquement
   - Solution : Colonne source_url obligatoire

5. Pas de validation
   - Valeurs aberrantes possibles (poids = 50g, drop = 50mm)
   - Types incohérents (texte dans colonne numérique)
   - Solution : Contraintes PostgreSQL (CHECK)

6. Pas d'historique
   - Modifications non trackées
   - Impossible de revenir en arrière
   - Qui a modifié quoi et quand ?
   - Solution : Colonnes created_at/updated_at + audit log

---

### Plan de migration

Étape 1 : Nettoyage Excel
- Supprimer colonnes FR (garder uniquement EN)
- Supprimer colonnes 100% vides
- Normaliser unités (tout en g, mm, USD)
- Ajouter colonne source = "legacy_excel"

Étape 2 : Import PostgreSQL
- Créer schéma SQL (cf section 4)
- Importer 142 chaussures existantes
- Marquer comme "legacy" (nécessitant enrichissement)

Étape 3 : Enrichissement via scraping
- Pour chaque chaussure legacy :
  - Chercher sur RunRepeat (par marque + modèle)
  - Si trouvée : Compléter données manquantes
  - Si non trouvée : Garder données Excel

Étape 4 : Validation
- Comparer Excel vs PostgreSQL
- Vérifier cohérence (même poids, drop, etc.)
- Corriger incohérences manuellement

Résultat attendu :
- 142 chaussures enrichies avec 26 nouveaux champs
- Taux de complétude : 45-62% → 95%+

---

## 6. Extension : 15 sites à scraper

### Liste des 15 sites identifiés

Source : sites_running.xlsx

| # | Site | URL | Langue | Type | Priorité |
|---|------|-----|--------|------|----------|
| 1 | RunRepeat | https://runrepeat.com | EN | Lab tests + Reviews | 10/10 |
| 2 | The Sneaker Database | https://thesneakerdatabase.com | EN | Database | 8/10 |
| 3 | Running Shoes Guru | https://runningshoesguru.com | EN | Reviews | 7/10 |
| 4 | Chaussure Running | https://www.chaussure-running.net | FR | Reviews + Comparatifs | 9/10 |
| 5 | Running Addict | https://www.running-addict.fr | FR | Reviews + Blog | 8/10 |
| 6 | RunActu | https://www.runactu.fr | FR | Reviews + News | 6/10 |
| 7 | Journal du Trail | https://www.journaldutrail.com | FR | Comparatifs + Tests | 6/10 |
| 8 | RunPack | https://www.runpack.fr | FR | Tests | 5/10 |
| 9 | Stadion Actu | https://www.stadionactu.com | FR | Reviews + News | 5/10 |
| 10 | Trail & Running | https://www.trail-running.fr | FR | Tests | 6/10 |
| 11 | The Running Collective | https://www.therunningcollective.com | FR | Comparateur + Tests | 9/10 |
| 12 | Believe in the Run | https://www.believeintherun.com | EN | Reviews | 7/10 |
| 13 | Doctors of Running | https://www.doctorsofrunning.com | EN | Reviews + Analyses | 8/10 |
| 14 | WearTesters | https://weartesters.com | EN | Reviews | 6/10 |
| 15 | Solereview | https://www.solereview.com | EN | Reviews | 7/10 |

---

### Stratégie de priorisation

Critères de priorité :

1. Qualité des données (40%)
   - Données lab tests objectives → Priorité maximale
   - Reviews détaillées → Priorité haute
   - Marketing générique → Priorité basse

2. Marché cible (30%)
   - Sites FR → Priorité haute (marché principal StrideMatch)
   - Sites EN → Priorité moyenne (complémentaire)

3. Fraîcheur (20%)
   - Sites avec nouveautés rapides → Priorité haute
   - Sites mis à jour sporadiquement → Priorité basse

4. Facilité de scraping (10%)
   - Structure HTML claire → Priorité haute
   - Anti-bot agressif → Priorité basse (coût accru)

---

### Ordre d'implémentation recommandé

Phase 1 (Semaine 1-2) : Sites à données objectives

1. RunRepeat (EN) - Priorité 10/10
   - Raison : Déjà implémenté, données lab tests exclusives
   - Valeur : 43 champs dont 26 tests lab
   - Fréquence : Daily

2. Chaussure Running (FR) - Priorité 9/10
   - Raison : Meilleur site FR, comparatifs détaillés
   - Valeur : Tests terrain, avis long terme, comparaisons
   - Fréquence : Weekly

3. The Running Collective (FR) - Priorité 9/10
   - Raison : Comparateur prix + tests, focus marché FR
   - Valeur : Prix multi-sites, disponibilité, promotions
   - Fréquence : Daily (prix)

Phase 2 (Semaine 3-4) : Sites reviews de qualité

4. Running Addict (FR) - Priorité 8/10
5. Doctors of Running (EN) - Priorité 8/10
6. The Sneaker Database (EN) - Priorité 8/10

Phase 3 (Mois 2) : Sites complémentaires

7-15. Tous les autres sites

---

### ROI attendu par site

| Site | Chaussures estimées | Données uniques | Coût scraping/mois | ROI |
|------|---------------------|-----------------|-------------------|-----|
| RunRepeat | 500+ | Tests lab (26 champs) | 10 USD | Très élevé |
| Chaussure Running | 300+ | Tests terrain FR | 6 USD | Élevé |
| The Running Collective | 800+ | Prix comparaison | 8 USD | Élevé |
| Running Addict | 200+ | Reviews longues FR | 4 USD | Moyen |
| Doctors of Running | 150+ | Analyses biomécaniques | 3 USD | Moyen-Élevé |
| Autres sites (×10) | 100+ chacun | Reviews variées | 2-3 USD chacun | Moyen |

Total attendu :
- Chaussures uniques : 800-1200 (vs 142 actuellement)
- Coût total : ~50 USD/mois
- Coverage nouveautés : 95%+ du marché

---

### Défis techniques par site

| Site | Anti-bot | Structure HTML | Difficulté | Solution |
|------|----------|----------------|------------|----------|
| RunRepeat | Cloudflare | Complexe mais stable | Moyenne | Playwright + Stealth (implémenté) |
| Chaussure Running | Basique | Claire | Facile | Même approche |
| The Running Collective | Modéré | Tableau structuré | Facile-Moyenne | Parsing direct |
| Sites français (5-10) | Faible | Variable | Facile | Approche IA (adaptable) |
| Sites anglais (12-15) | Modéré | Variable | Moyenne | Approche IA |

Approche IA (GPT-5 mini) = Avantage majeur :
- Pas besoin de coder 15 parsers différents
- S'adapte aux changements de structure
- Même prompt pour tous les sites
- 10 min de config par nouveau site

---

## 7. Système d'automatisation intelligent

### Architecture globale

Composants :

1. Celery Beat (Scheduler)
   - Planifie les tâches de scraping
   - Fréquences : Quotidienne, hebdomadaire, mensuelle

2. Celery Workers (Executeurs)
   - Exécutent les tâches de scraping
   - Parallélisation (5-10 workers simultanés)

3. PostgreSQL (Stockage)
   - Base de données principale
   - Queue de validation (duplicate_candidates)

4. Redis (Queue)
   - Queue des tâches Celery
   - Cache temporaire

5. Dashboard (Monitoring)
   - Streamlit ou Django Admin
   - Visualisation temps réel
   - Interface de validation Human-in-the-Loop

---

### Calendrier d'automatisation

Scraping quotidien (06:00 AM) :

```python
from celery import Celery
from celery.schedules import crontab

app = Celery('stridematch_scraping')

app.conf.beat_schedule = {
    'scrape-runrepeat-daily': {
        'task': 'tasks.scrape_site',
        'schedule': crontab(hour=6, minute=0),  # 06:00 AM
        'args': ('runrepeat', 'new_arrivals')
    },
    'scrape-running-collective-prices': {
        'task': 'tasks.scrape_prices',
        'schedule': crontab(hour=6, minute=30),  # 06:30 AM
        'args': ('the_running_collective',)
    },
}
```

Sites scrapés quotidiennement :
- RunRepeat (nouvelles chaussures + updates)
- The Running Collective (prix)

Temps d'exécution estimé : 20-40 minutes
Coût : ~0.30 USD/jour

Scraping hebdomadaire (Dimanche 02:00 AM) :

```python
app.conf.beat_schedule = {
    'scrape-all-sites-weekly': {
        'task': 'tasks.scrape_all_sites',
        'schedule': crontab(day_of_week=0, hour=2, minute=0),  # Dimanche 02:00
        'args': (['chaussure_running', 'running_addict', 'doctors_of_running', ...],)
    },
}
```

Sites scrapés hebdomadairement :
- Tous les sites de reviews (12 sites)

Temps d'exécution estimé : 2-4 heures
Coût : ~3-5 USD/semaine

Scraping mensuel (1er du mois, 01:00 AM) :

```python
app.conf.beat_schedule = {
    'monthly-full-rescrape': {
        'task': 'tasks.full_catalog_rescrape',
        'schedule': crontab(day_of_month=1, hour=1, minute=0),
        'args': ()
    },
    'monthly-cleanup': {
        'task': 'tasks.cleanup_database',
        'schedule': crontab(day_of_month=1, hour=4, minute=0),
        'args': ()
    },
    'monthly-report': {
        'task': 'tasks.generate_report',
        'schedule': crontab(day_of_month=1, hour=5, minute=0),
        'args': ()
    },
}
```

Tâches mensuelles :
- Rescraping complet du catalogue (toutes chaussures)
- Nettoyage doublons
- Génération rapport statistiques
- Archivage données historiques

Temps d'exécution estimé : 6-10 heures
Coût : ~15-20 USD/mois

---

### Détection automatique de doublons

Problème :

Même chaussure peut apparaître sur 5-10 sites différents avec :
- Noms légèrement différents ("Nike Pegasus 41" vs "Pegasus 41" vs "Nike Air Zoom Pegasus 41")
- Specs différentes (poids varie de 5-10g selon taille)
- Prix différents

Objectif : Détecter et fusionner les doublons automatiquement.

---

### Algorithme de similarité multi-critères

Étapes :

1. Comparaison de noms (similarité textuelle)
2. Comparaison de specs techniques
3. Calcul score de similarité global
4. Décision : Auto-merge, Human-in-the-loop, ou Nouvelle chaussure

Code (simplifié) :

```python
from difflib import SequenceMatcher

def calculate_similarity(shoe_a, shoe_b):
    scores = []

    # 1. Similarité du nom (40% du score)
    name_a = f"{shoe_a.brand} {shoe_a.model_name}".lower()
    name_b = f"{shoe_b.brand} {shoe_b.model_name}".lower()
    name_similarity = SequenceMatcher(None, name_a, name_b).ratio()
    scores.append(('name', name_similarity, 0.40))

    # 2. Similarité de la marque (30% du score)
    brand_similarity = 1.0 if shoe_a.brand == shoe_b.brand else 0.0
    scores.append(('brand', brand_similarity, 0.30))

    # 3. Similarité du poids (10% du score)
    if shoe_a.weight_g and shoe_b.weight_g:
        weight_diff = abs(shoe_a.weight_g - shoe_b.weight_g)
        weight_similarity = max(0, 1 - (weight_diff / 50))  # Tolérance 50g
        scores.append(('weight', weight_similarity, 0.10))

    # 4. Similarité du drop (10% du score)
    if shoe_a.drop_mm and shoe_b.drop_mm:
        drop_diff = abs(shoe_a.drop_mm - shoe_b.drop_mm)
        drop_similarity = max(0, 1 - (drop_diff / 4))  # Tolérance 4mm
        scores.append(('drop', drop_similarity, 0.10))

    # 5. Similarité du prix (10% du score)
    if shoe_a.price_usd and shoe_b.price_usd:
        price_diff_pct = abs(shoe_a.price_usd - shoe_b.price_usd) / shoe_a.price_usd
        price_similarity = max(0, 1 - price_diff_pct)
        scores.append(('price', price_similarity, 0.10))

    # Calcul pondéré
    total_weight = sum(weight for _, _, weight in scores)
    weighted_score = sum(sim * weight for _, sim, weight in scores) / total_weight

    return weighted_score, scores
```

Règles de décision :

```python
similarity, details = calculate_similarity(shoe_a, shoe_b)

if similarity >= 0.90:
    # Auto-merge (très haute confiance)
    merge_shoes(shoe_a, shoe_b, strategy='keep_most_complete')
    log_action('auto_merged', shoe_a, shoe_b, similarity)

elif 0.70 <= similarity < 0.90:
    # Human-in-the-loop (confiance moyenne)
    create_duplicate_candidate(shoe_a, shoe_b, similarity)
    notify_admin('pending_duplicate_review', count=1)

else:
    # Nouvelle chaussure (faible similarité)
    # Aucune action
    pass
```

Exemples :

Cas 1 : Similarité 0.95 (Auto-merge)
- Chaussure A : "Nike Pegasus 41" (RunRepeat), 289g, 9.6mm drop, 180 USD
- Chaussure B : "Nike Air Zoom Pegasus 41" (Chaussure Running), 291g, 10mm drop, 175 EUR (190 USD)
- Scores : name=0.92, brand=1.0, weight=0.96, drop=0.90, price=0.94
- Décision : Fusion automatique

Cas 2 : Similarité 0.78 (Human-in-the-loop)
- Chaussure A : "Nike Vomero 17" (RunRepeat), 289g, 9.6mm drop
- Chaussure B : "Nike Vomero Plus" (Running Addict), 295g, 9.5mm drop
- Scores : name=0.75, brand=1.0, weight=0.88, drop=0.98
- Décision : Demander validation humaine (sont-ce 2 modèles différents ?)

Cas 3 : Similarité 0.42 (Nouvelle chaussure)
- Chaussure A : "Nike Pegasus 41" (RunRepeat)
- Chaussure B : "Adidas Boston 12" (Chaussure Running)
- Scores : name=0.15, brand=0.0, ...
- Décision : Chaussures différentes, pas de merge

---

### Stratégie de fusion (merge)

Lorsque 2 chaussures sont identifiées comme doublons, stratégies de fusion :

1. Keep most complete (par défaut)
   - Garde tous les champs non-null
   - Si conflit (2 valeurs différentes non-null) : Garde la plus récente

2. Average numeric values
   - Pour specs variables (poids, dimensions)
   - Moyenne pondérée selon confiance de la source

3. Merge lists
   - pros/cons : Fusion sans doublons
   - widths_available : Union des largeurs

Exemple de fusion :

```python
def merge_shoes(shoe_a, shoe_b, strategy='keep_most_complete'):
    merged = {}

    for field in ['weight_g', 'drop_mm', 'price_usd', ...]:
        val_a = getattr(shoe_a, field)
        val_b = getattr(shoe_b, field)

        if val_a is None and val_b is None:
            merged[field] = None
        elif val_a is None:
            merged[field] = val_b
        elif val_b is None:
            merged[field] = val_a
        elif isinstance(val_a, (int, float)):
            # Moyenne pour valeurs numériques
            merged[field] = (val_a + val_b) / 2
        else:
            # Garde la plus récente
            merged[field] = val_a if shoe_a.scraped_at > shoe_b.scraped_at else val_b

    # Fusion des listes (pros/cons)
    merged['pros'] = list(set(shoe_a.pros + shoe_b.pros))
    merged['cons'] = list(set(shoe_a.cons + shoe_b.cons))

    # Traçabilité : Garder les 2 URLs sources
    merged['source_urls'] = [shoe_a.source_url, shoe_b.source_url]

    return merged
```

---

### Human-in-the-Loop : Interface de validation

Dashboard simple pour valider doublons potentiels (similarité 70-90%).

Interface (Streamlit ou Django Admin) :

```
=== Doublon Potentiel #47 ===
Similarité : 78%

Chaussure A :                    Chaussure B :
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Nike Vomero 17                   Nike Vomero Plus
Source : RunRepeat               Source : Running Addict
Poids : 289g                     Poids : 295g
Drop : 9.6mm                     Drop : 9.5mm
Prix : 180 USD                   Prix : 175 EUR (190 USD)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Actions :
[Fusionner] [Chaussures différentes] [Ignorer]
```

Temps humain requis : 10-30 secondes par doublon

Fréquence :
- Avec 15 sites : ~5-10 doublons/semaine à valider
- Temps total : < 5 minutes/semaine

---

### Règles de mise à jour automatique

Auto-update autorisé (sans validation humaine) :

1. Prix (si écart < 20%)
   - Exemple : 180 USD → 175 USD (OK)
   - Exemple : 180 USD → 120 USD (Alerte : Vérification manuelle)

2. Disponibilité
   - En stock → Rupture de stock
   - Ajout de nouvelles largeurs (D → D, 2E)

3. URL source
   - Mise à jour du lien si page déplacée

4. Date de scraping
   - Toujours mise à jour

5. Métadonnées non critiques
   - pros/cons (ajout uniquement, pas suppression)
   - Reviews, scores

Validation humaine OBLIGATOIRE :

1. Nouvelle chaussure détectée
   - Toujours valider manuellement avant ajout au catalogue public

2. Changement de specs techniques
   - Poids : Écart > 10g
   - Drop : Écart > 1mm
   - Stack : Écart > 3mm
   - Raison : Peut indiquer erreur de scraping ou nouveau modèle

3. Changement marque/nom
   - Toujours suspect (erreur de scraping probable)

4. Doublon avec similarité 70-90%
   - Zone grise, jugement humain nécessaire

Implémentation :

```python
def should_auto_update(old_shoe, new_shoe):
    changes = detect_changes(old_shoe, new_shoe)

    for change in changes:
        field, old_val, new_val = change

        # Règles d'auto-update
        if field == 'price_usd':
            if abs((new_val - old_val) / old_val) > 0.20:
                return False  # Écart > 20% → Validation requise

        elif field in ['brand', 'model_name']:
            return False  # Changement nom → Toujours valider

        elif field == 'weight_g':
            if abs(new_val - old_val) > 10:
                return False  # Écart > 10g → Valider

        elif field in ['scraped_at', 'source_url', 'availability']:
            continue  # OK pour auto-update

        else:
            return False  # Par défaut : Validation requise

    return True  # Toutes les vérifications passées → Auto-update OK
```

---

### Monitoring & Alertes

Dashboard temps réel (Streamlit) :

Sections :

1. Vue d'ensemble
   - Statut dernière exécution (succès/échec)
   - Nombre de chaussures au catalogue (totale, nouvelles cette semaine)
   - Taux de succès par site (graphique)
   - Chaussures en attente de validation (compteur)

2. Scraping logs (dernières 24h)
   - Tableau : Site | Heure | Durée | Chaussures scrapées | Statut
   - Filtre par statut (success/failed/partial)

3. Queue de validation
   - Liste des doublons potentiels à valider
   - Boutons d'action rapide

4. Analytics
   - Graphique : Évolution du catalogue (par semaine)
   - Graphique : Prix moyens par marque
   - Graphique : Nouvelles chaussures par mois

Alertes Slack/Email :

Déclencheurs :

1. Site bloqué (HTTP 403/429)
   - Message : "⚠️ RunRepeat bloque nos requêtes (403 Forbidden). Vérifier IP/User-Agent."
   - Action : Pause scraping, vérifier stealth

2. Taux d'échec > 30%
   - Message : "⚠️ 12/40 chaussures ont échoué sur Chaussure Running (30% échec)"
   - Action : Vérifier structure HTML (changement possible)

3. Queue validation > 5 chaussures
   - Message : "📋 7 chaussures en attente de validation depuis 3 jours"
   - Action : Valider via dashboard

4. Baisse de prix > 20%
   - Message : "💰 Nike Pegasus 41 : 180 USD → 139 USD (-23%) sur The Running Collective"
   - Action : Vérifier promo, mettre en avant

5. Nouvelle chaussure populaire détectée
   - Message : "🆕 Nouvelle chaussure : Hoka Clifton 10 (score 4.5/5, 89 reviews)"
   - Action : Valider et ajouter au catalogue rapidement

6. Coût OpenAI anormal
   - Message : "⚠️ Coût scraping aujourd'hui : 15 USD (vs 2-3 USD habituellement)"
   - Action : Vérifier si scraping en boucle, optimiser prompts

Implémentation (exemple Slack) :

```python
import requests

def send_slack_alert(message, urgency='medium'):
    webhook_url = "https://hooks.slack.com/services/XXX/YYY/ZZZ"

    emoji = {
        'low': 'ℹ️',
        'medium': '⚠️',
        'high': '🚨'
    }

    payload = {
        "text": f"{emoji[urgency]} {message}",
        "channel": "#stridematch-scraping"
    }

    requests.post(webhook_url, json=payload)
```

---

## 8. Limites et considérations

### Limitations techniques

1. Détection anti-bot

Problème :
- Sites utilisent Cloudflare, reCAPTCHA, fingerprinting
- Peuvent bloquer nos requêtes (HTTP 403, 429)
- Taux de succès : 85-95% (certaines pages bloquées)

Solutions :
- Playwright-stealth (implémenté) : Masque signaux automation
- Rotating User-Agents : Change User-Agent aléatoirement
- Delays aléatoires : 2-5 secondes entre requêtes (imite humain)
- Proxy résidentiels (si nécessaire) : Coût 50-100 USD/mois, IP réelles
- CAPTCHA solving services (en dernier recours) : 2Captcha, Anti-Captcha

Monitoring :
- Tracker taux de blocage par site
- Si > 30% blocage : Ajuster stratégie

2. Changements de structure HTML

Problème :
- Sites redesignent leurs pages (mensuellement/annuellement)
- Approche CSS Selectors : Casse immédiatement
- Requiert maintenance continue

Solutions :
- Approche IA (GPT-5 mini) : S'adapte automatiquement
  - Avantage : Comprend contenu sémantiquement
  - Limite : Peut échouer si changement majeur (98% → 85% taux de succès)
- Monitoring automatique : Détecte baisse de taux de succès
- Alertes : Prévient équipe si problème
- Tests réguliers : Vérifier scraping fonctionne toujours

Exemple :
- Site change `<div class="price">180 USD</div>` → `<span data-price="180"></span>`
- CSS Selector : `.price` → ERREUR
- IA : Trouve toujours "180 USD" dans le texte → OK

4. Qualité des données sources

Problème :
- Toutes les sources ne sont pas fiables
- Erreurs dans les données sources (typos, specs incorrectes)
- Données manquantes ou incomplètes

Solutions :
- Multi-sources : Agréger données de 3-5 sites pour même chaussure
- Validation croisée : Si weight_g diffère de > 10g entre sources → Flag pour review
- Scoring de confiance : Attribuer score de fiabilité par source
  - RunRepeat : 95% (tests lab)
  - Sites reviews : 80-85%
  - Sites marketing : 70%
- Médiane/Moyenne : Pour valeurs numériques, prendre médiane (robuste aux outliers)

Exemple :
- Nike Pegasus 41 - Poids relevé :
  - RunRepeat : 289g
  - Chaussure Running : 291g
  - Site fabricant : 285g
  - Running Addict : 340g (ERREUR probable)
- Médiane : 290g (rejette l'outlier 340g)

5. Rate limiting (limite de requêtes)

Problème :
- Sites limitent nombre de requêtes/minute
- Dépassement → Blocage temporaire (HTTP 429)

Solutions :
- Respecter delays : 2-5 secondes entre requêtes
- Distribuer scraping : Étaler sur plusieurs heures
- Queue système : Celery gère automatiquement le throttling
- Retry logic : Si 429, attendre 60 sec et réessayer

Implémentation :

```python
import time
import random

def scrape_with_delay(url):
    # Delay aléatoire 2-5 secondes
    time.sleep(random.uniform(2, 5))

    try:
        html = fetch_page(url)
        return html
    except RateLimitError:
        # Si rate limited, attendre 60 sec
        time.sleep(60)
        return fetch_page(url)  # Retry
```

---

### Considérations légales

1. Web scraping et légalité

Statut légal en France/UE :

- Scraping de données publiques : LÉGAL
  - Données accessibles sans login
  - Pas de contournement de protections techniques (paywall, login)
  - Jurisprudence : Ryanair vs PR Aviation (CJUE 2015), LinkedIn vs hiQ (US 2022)

- Scraping abusif : ILLÉGAL
  - Déni de service (trop de requêtes)
  - Contournement de protections (bypass paywall)
  - Usurpation d'identité

Notre cas (StrideMatch) :
- Données publiques : Specs chaussures affichées publiquement → LÉGAL
- Pas de login : Toutes les données sont accessibles sans compte → LÉGAL
- Respectueux : Delays entre requêtes, pas de surcharge serveurs → LÉGAL
- Usage commercial : Agrégation de données publiques pour service → LÉGAL (jurisprudence)

Recommandations :
- Respecter robots.txt (sauf si bloque légitimement données publiques)
- Ne pas surcharger les serveurs (rate limiting)
- Mentionner sources (traçabilité, crédit)
- Ne pas revendre données brutes (OK pour agrégation/valeur ajoutée)

2. Propriété intellectuelle

Données factuelles :
- Poids, drop, stack, prix = FAITS, pas de copyright
- Libre d'utiliser et redistribuer

Contenus créatifs :
- Reviews complètes (texte long) = Potentiellement protégés
- Photos, vidéos = Protégés par copyright
- Logos, marques = Protégés

Notre approche :
- Extraction de pros/cons : Résumé court (IA) → Transformative use, OK
- Pas de copie de reviews complètes → OK
- Pas d'images scrapées → OK
- Mention des sources → Bonne pratique

3. Conditions d'utilisation (ToS)

Problème :
- Certains sites interdisent scraping dans leurs ToS
- Exemple : "You may not use automated means to access our site"

Réalité juridique (UE) :
- ToS ne peuvent pas interdire l'accès à données publiques
- Jurisprudence : Contrats d'adhésion ne peuvent pas limiter liberté d'information
- Sauf si scraping cause préjudice technique (surcharge serveurs)

Notre position :
- Scraping respectueux (pas de surcharge)
- Données publiques (pas de contournement de protection)
- Valeur ajoutée (agrégation, comparaison, recommandations IA)
- Légal malgré ToS restrictives (jurisprudence européenne)

Précaution :
- Ne pas mentionner publiquement qu'on scrape ces sites
- Marketing : "Nous agrégeons des données publiques de running"

4. RGPD (Protection des données)

Applicabilité :
- RGPD concerne données personnelles (nom, email, IP, etc.)
- Specs chaussures = Données techniques, pas personnelles
- StrideMatch non concerné

Cas limite :
- Si scraping d'avis utilisateurs avec noms → RGPD applicable
- Solution : Anonymiser, ne pas stocker noms

Notre cas :
- Aucune donnée personnelle scrapée → RGPD non applicable

---

## Conclusion & Recommandations

### État actuel du système

Aujourd'hui opérationnel :

1. Pipeline 3 modules fonctionnel
   - Playwright + Stealth : Navigation anti-détection
   - BeautifulSoup : Nettoyage HTML (95% réduction taille)
   - GPT-5 mini : Extraction IA avec validation Pydantic

2. Source de données établie
   - RunRepeat : 43 champs dont 26 tests lab
   - ~500 chaussures disponibles
   - Coût : 0.002 USD/chaussure, 21 sec/chaussure

3. Qualité validée
   - Précision : 99%+
   - Données objectives (tests lab)
   - Format structuré (JSON validé)

---

### Prochaines étapes recommandées

Phase 1 : Infrastructure de base (Semaine 1-2)

1. Migration PostgreSQL
   - Créer schéma SQL complet (cf section 4)
   - Migrer 142 chaussures Excel existantes
   - Configurer pgvector pour RAG

2. Automation basique
   - Setup Celery + Redis
   - Scraping quotidien RunRepeat
   - Logs dans table scraping_logs

Phase 2 : Human-in-the-Loop (Semaine 3-4)

1. Système de détection doublons
   - Implémenter algorithme de similarité
   - Table duplicate_candidates

2. Dashboard validation
   - Interface Streamlit simple
   - Queue de validation
   - Actions : Fusionner / Rejeter / Ignorer

Phase 3 : Extension multi-sites (Mois 2)

1. Ajouter 3 sites prioritaires
   - Chaussure Running (FR)
   - The Running Collective (FR)
   - Running Addict (FR)

2. Monitoring & Alertes
   - Dashboard Streamlit
   - Alertes Slack (échecs, blocages)

Phase 4 : RAG & Recommandations IA (Mois 3+)

1. Embeddings OpenAI
   - Générer embeddings pour chaque chaussure
   - Indexer avec pgvector

2. Recherche sémantique
   - "Chaussure confortable pour marathon"
   - Retourne top 10 basé sur similarité

3. Recommandations personnalisées
   - Basées sur historique utilisateur
   - "Tu as aimé X, tu aimeras Y"

---

Document généré le 28 novembre 2025
Version 1.0

Propriété intellectuelle : Nicolas Angougeard
