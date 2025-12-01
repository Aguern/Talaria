"""
Utility Functions - E-commerce Scraper

Helper functions for category classification, gender detection, and data normalization.
"""

import re
from typing import Optional, Tuple


# Brand name normalization (same as lab_scraper)
BRAND_ALIASES = {
    'nike': ['nike', 'nike running'],
    'adidas': ['adidas', 'adidas running'],
    'hoka': ['hoka', 'hoka one one'],
    'asics': ['asics', 'asics running'],
    'brooks': ['brooks', 'brooks running'],
    'new balance': ['new balance', 'newbalance', 'nb'],
    'saucony': ['saucony'],
    'mizuno': ['mizuno', 'mizuno running'],
    'on running': ['on', 'on running'],
    'altra': ['altra', 'altra running'],
}


def normalize_brand_name(brand: str) -> Optional[str]:
    """
    Normalize brand name to match database slugs.

    Args:
        brand: Raw brand name from scraping

    Returns:
        Normalized brand name or None if not found
    """
    brand_lower = brand.lower().strip()

    for canonical_brand, aliases in BRAND_ALIASES.items():
        if brand_lower in aliases:
            return canonical_brand

    return None


def classify_category(product_name: str, description: str = '') -> str:
    """
    Classify product into primary_category enum.

    Args:
        product_name: Product name
        description: Product description (optional)

    Returns:
        Category: "running_road", "running_trail", "running_racing", etc.

    Strategy:
        Use keyword matching to determine category.
    """
    text = (product_name + ' ' + description).lower()

    # Trail running
    if any(keyword in text for keyword in ['trail', 'sentier', 'montagne', 'mountain', 'ultra']):
        return 'running_trail'

    # Track/Racing
    if any(keyword in text for keyword in ['racing', 'spike', 'compétition', 'piste', 'track', 'marathon']):
        return 'running_racing'

    # Track and field
    if any(keyword in text for keyword in ['athletisme', 'field', 'throwing', 'jumping']):
        return 'track_field'

    # Triathlon
    if 'triathlon' in text or 'tri' in text:
        return 'triathlon'

    # Walking
    if any(keyword in text for keyword in ['walking', 'marche', 'walker']):
        return 'walking'

    # Default to road running
    return 'running_road'


def detect_gender(product_name: str, description: str = '', url: str = '') -> str:
    """
    Detect product gender from name, description, or URL.

    Args:
        product_name: Product name
        description: Product description
        url: Product URL

    Returns:
        Gender: "male", "female", or "unisex"
    """
    text = (product_name + ' ' + description + ' ' + url).lower()

    # Female keywords
    female_keywords = [
        'femme', 'women', 'woman', 'female', 'girl', 'lady',
        'ladies', "women's", 'dame'
    ]

    # Male keywords
    male_keywords = [
        'homme', 'men', 'man', 'male', 'boy',
        "men's", 'mens', 'garçon'
    ]

    female_score = sum(1 for kw in female_keywords if kw in text)
    male_score = sum(1 for kw in male_keywords if kw in text)

    if female_score > male_score:
        return 'female'
    elif male_score > female_score:
        return 'male'
    else:
        return 'unisex'


def extract_model_from_name(full_name: str, brand: str) -> str:
    """
    Extract model name from full product name.

    Args:
        full_name: Full product name (e.g., "Nike Pegasus 41")
        brand: Brand name (e.g., "Nike")

    Returns:
        Model name (e.g., "Pegasus 41")
    """
    if not brand:
        return full_name

    # Remove brand from name
    model = full_name.replace(brand, '').strip()

    # Remove "Running Shoe" and similar suffixes
    model = re.sub(r'\s+(Running\s+)?(Shoe|Chaussure|Chaussures)s?$', '', model, flags=re.IGNORECASE)

    # Clean up extra spaces
    model = ' '.join(model.split())

    return model


def extract_year_from_name(product_name: str) -> Optional[int]:
    """
    Extract release year from product name.

    Args:
        product_name: Product name (e.g., "Pegasus 41 (2024)")

    Returns:
        Year as integer or None
    """
    # Look for 4-digit year in parentheses or after dash
    match = re.search(r'[\(\-]\s*(\d{4})\s*[\)]?', product_name)
    if match:
        year = int(match.group(1))
        if 2015 <= year <= 2030:  # Sanity check
            return year

    return None


def classify_stability(product_name: str, description: str = '') -> str:
    """
    Classify stability type from product name and description.

    Args:
        product_name: Product name
        description: Product description

    Returns:
        Stability: "neutral", "stability_mild", "stability_strong", "motion_control"
    """
    text = (product_name + ' ' + description).lower()

    # Motion control (strongest support)
    if any(keyword in text for keyword in ['motion control', 'contrôle du mouvement', 'max support']):
        return 'motion_control'

    # Strong stability
    if any(keyword in text for keyword in ['guide', 'structure', 'support', 'stabilité forte']):
        return 'stability_strong'

    # Mild stability
    if any(keyword in text for keyword in ['stability', 'stabilité', 'pronation']):
        return 'stability_mild'

    # Neutral (default)
    return 'neutral'


def classify_cushioning(product_name: str, description: str = '') -> str:
    """
    Classify cushioning level from product name and description.

    Args:
        product_name: Product name
        description: Product description

    Returns:
        Cushioning: "minimal", "moderate", "max"
    """
    text = (product_name + ' ' + description).lower()

    # Minimal cushioning
    if any(keyword in text for keyword in ['minimal', 'barefoot', 'natural', 'race', 'racing']):
        return 'minimal'

    # Max cushioning
    if any(keyword in text for keyword in ['max', 'ultra', 'plush', 'maximum', 'bondi', 'clifton']):
        return 'max'

    # Moderate (default)
    return 'moderate'


def classify_terrain(category: str, product_name: str) -> str:
    """
    Classify terrain type.

    Args:
        category: Primary category
        product_name: Product name

    Returns:
        Terrain: "road", "trail", "track", "mixed"
    """
    if category == 'running_trail':
        return 'trail'
    elif category == 'running_racing':
        return 'track'
    elif 'trail' in product_name.lower():
        return 'trail'
    elif 'track' in product_name.lower():
        return 'track'
    else:
        return 'road'


def classify_distance(product_name: str, description: str = '') -> str:
    """
    Classify distance category.

    Args:
        product_name: Product name
        description: Product description

    Returns:
        Distance: "short", "middle", "long", "ultra"
    """
    text = (product_name + ' ' + description).lower()

    # Ultra distance
    if any(keyword in text for keyword in ['ultra', '100km', 'ultra-trail']):
        return 'ultra'

    # Long distance (marathon)
    if any(keyword in text for keyword in ['marathon', 'long', 'endurance', 'longue distance']):
        return 'long'

    # Short distance (5k, 10k)
    if any(keyword in text for keyword in ['5k', '10k', 'short', 'speed', 'vitesse']):
        return 'short'

    # Middle distance (default)
    return 'middle'


def classify_pace(product_name: str, description: str = '') -> str:
    """
    Classify pace category.

    Args:
        product_name: Product name
        description: Product description

    Returns:
        Pace: "recovery", "easy", "tempo", "speed"
    """
    text = (product_name + ' ' + description).lower()

    # Recovery
    if any(keyword in text for keyword in ['recovery', 'récupération', 'easy', 'confort']):
        return 'recovery'

    # Speed
    if any(keyword in text for keyword in ['speed', 'vitesse', 'racing', 'compétition', 'race']):
        return 'speed'

    # Tempo
    if any(keyword in text for keyword in ['tempo', 'training', 'entraînement', 'workout']):
        return 'tempo'

    # Easy (default)
    return 'easy'


def is_waterproof(product_name: str, description: str = '') -> bool:
    """
    Detect if product is waterproof.

    Args:
        product_name: Product name
        description: Product description

    Returns:
        True if waterproof, False otherwise
    """
    text = (product_name + ' ' + description).lower()

    waterproof_keywords = [
        'gtx', 'gore-tex', 'goretex', 'waterproof',
        'étanche', 'imperméable', 'water resistant'
    ]

    return any(keyword in text for keyword in waterproof_keywords)


def find_brand_id(cursor, brand_name: str) -> Optional[int]:
    """
    Find brand ID in database.

    Args:
        cursor: Database cursor
        brand_name: Brand name (e.g., "Nike")

    Returns:
        Brand ID or None
    """
    normalized_brand = normalize_brand_name(brand_name)
    if not normalized_brand:
        return None

    cursor.execute("""
        SELECT id FROM stridematch_brands
        WHERE slug = %s
    """, (normalized_brand,))

    result = cursor.fetchone()
    return result[0] if result else None
