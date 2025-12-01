"""
Utility Functions - Lab Scraper

Helper functions for brand/model matching and data normalization.
"""

import re
from typing import Optional, Tuple
from difflib import SequenceMatcher


# Brand name normalization mapping
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

    Examples:
        >>> normalize_brand_name("NIKE Running")
        "nike"
        >>> normalize_brand_name("Hoka One One")
        "hoka"
    """
    brand_lower = brand.lower().strip()

    for canonical_brand, aliases in BRAND_ALIASES.items():
        if brand_lower in aliases:
            return canonical_brand

    return None


def normalize_model_name(model: str) -> str:
    """
    Normalize model name by removing version numbers and special characters.

    Args:
        model: Raw model name

    Returns:
        Normalized model name

    Examples:
        >>> normalize_model_name("Pegasus 41")
        "Pegasus"
        >>> normalize_model_name("Clifton 9 (2024)")
        "Clifton"
    """
    # Remove version numbers (e.g., "41", "9")
    model = re.sub(r'\s+\d+(\.\d+)?$', '', model)
    # Remove year indicators
    model = re.sub(r'\s*\(?\d{4}\)?', '', model)
    # Remove special characters
    model = re.sub(r'[^\w\s-]', '', model)
    # Normalize whitespace
    model = ' '.join(model.split())

    return model.strip()


def similarity_score(s1: str, s2: str) -> float:
    """
    Calculate similarity score between two strings.

    Args:
        s1: First string
        s2: Second string

    Returns:
        Similarity score between 0.0 and 1.0

    Examples:
        >>> similarity_score("Pegasus 41", "Pegasus 40")
        0.9
    """
    return SequenceMatcher(None, s1.lower(), s2.lower()).ratio()


def find_product_id(cursor, brand_name: str, model_name: str, gender: Optional[str] = None) -> Optional[str]:
    """
    Find product ID in database by matching brand and model name.

    Args:
        cursor: Database cursor
        brand_name: Brand name (e.g., "Nike")
        model_name: Model name (e.g., "Pegasus 41")
        gender: Optional gender filter

    Returns:
        Product UUID if found, None otherwise

    Strategy:
        1. Get brand_id from stridematch_brands
        2. Query stridematch_products with normalized model name
        3. Use fuzzy matching if exact match fails
    """
    normalized_brand = normalize_brand_name(brand_name)
    if not normalized_brand:
        return None

    # Get brand_id
    cursor.execute("""
        SELECT id FROM stridematch_brands
        WHERE slug = %s
    """, (normalized_brand,))

    result = cursor.fetchone()
    if not result:
        return None

    brand_id = result[0]

    # Normalize model name for matching
    normalized_model = normalize_model_name(model_name)

    # Try exact match first
    query = """
        SELECT id FROM stridematch_products
        WHERE brand_id = %s
        AND LOWER(model_name) LIKE %s
    """
    params = [brand_id, f'%{normalized_model.lower()}%']

    if gender:
        query += " AND gender = %s"
        params.append(gender)

    cursor.execute(query, params)
    result = cursor.fetchone()

    if result:
        return str(result[0])

    # If no exact match, try fuzzy matching
    cursor.execute("""
        SELECT id, model_name FROM stridematch_products
        WHERE brand_id = %s
    """, (brand_id,))

    products = cursor.fetchall()
    best_match = None
    best_score = 0.0

    for product_id, db_model_name in products:
        score = similarity_score(normalized_model, normalize_model_name(db_model_name))
        if score > best_score and score >= 0.7:  # 70% similarity threshold
            best_score = score
            best_match = str(product_id)

    return best_match


def parse_float(value: str) -> Optional[float]:
    """
    Safely parse float from string.

    Args:
        value: String containing a number

    Returns:
        Float value or None if parsing fails

    Examples:
        >>> parse_float("10.5 mm")
        10.5
        >>> parse_float("N/A")
        None
    """
    if not value or value.lower() in ['n/a', 'na', 'unknown', '-']:
        return None

    try:
        # Extract first number from string
        match = re.search(r'[-+]?\d*\.?\d+', str(value))
        if match:
            return float(match.group())
    except (ValueError, AttributeError):
        pass

    return None


def parse_gender(gender: str) -> str:
    """
    Normalize gender string to database enum values.

    Args:
        gender: Raw gender string

    Returns:
        "male", "female", or "unisex"

    Examples:
        >>> parse_gender("Men's")
        "male"
        >>> parse_gender("Women")
        "female"
    """
    gender_lower = gender.lower().strip()

    if any(term in gender_lower for term in ['men', 'male', "men's", 'homme']):
        return 'male'
    elif any(term in gender_lower for term in ['women', 'female', "women's", 'femme']):
        return 'female'
    else:
        return 'unisex'
