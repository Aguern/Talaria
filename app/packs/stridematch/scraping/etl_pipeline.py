"""
ETL Pipeline - Phase 5

Transforms raw scraped data into enriched, normalized data:
1. Normalize lab data (drop_mm → categories, cushioning_ha → soft/firm/balanced)
2. Generate biomechanical tags based on product specs
3. Insert enrichment tags into stridematch_enrichment_tags table

Usage:
    python etl_pipeline.py --mode normalize
    python etl_pipeline.py --mode generate-tags
    python etl_pipeline.py --mode all
"""

try:
    import psycopg2
except ImportError:
    import psycopg as psycopg2  # Use psycopg3 if psycopg2 not available
import argparse
import sys
from typing import List, Dict, Optional
from datetime import datetime


# ============================================================================
# Database Connection
# ============================================================================

def get_db_connection():
    """Create PostgreSQL connection from environment variables"""
    import os

    return psycopg2.connect(
        host=os.getenv('POSTGRES_HOST', 'localhost'),
        port=int(os.getenv('POSTGRES_PORT', 5432)),
        dbname=os.getenv('POSTGRES_DB', 'saas_nr_db'),
        user=os.getenv('POSTGRES_USER', 'user'),
        password=os.getenv('POSTGRES_PASSWORD', 'password'),
    )


# ============================================================================
# Normalization Functions
# ============================================================================

def normalize_drop(drop_mm: float) -> str:
    """
    Normalize heel-to-toe drop into categories.

    Args:
        drop_mm: Drop in millimeters

    Returns:
        Category: "zero_drop", "low_drop", "moderate_drop", "high_drop"

    Categories:
        - Zero drop: 0-2mm
        - Low drop: 3-6mm
        - Moderate drop: 7-10mm
        - High drop: 11mm+
    """
    if drop_mm <= 2:
        return 'zero_drop'
    elif drop_mm <= 6:
        return 'low_drop'
    elif drop_mm <= 10:
        return 'moderate_drop'
    else:
        return 'high_drop'


def normalize_cushioning(cushioning_ha: Optional[float]) -> str:
    """
    Normalize cushioning softness (Shore A hardness) into categories.

    Args:
        cushioning_ha: Shore A hardness (0-100)

    Returns:
        Category: "soft", "balanced", "firm"

    Categories:
        - Soft: ≤50 HA (softer midsole)
        - Balanced: 51-65 HA (moderate cushioning)
        - Firm: 66+ HA (firmer, more responsive)

    Note: Lower Shore A = softer material
    """
    if cushioning_ha is None:
        return 'balanced'  # Default

    if cushioning_ha <= 50:
        return 'soft'
    elif cushioning_ha <= 65:
        return 'balanced'
    else:
        return 'firm'


def normalize_stack_height(stack_heel_mm: float, stack_forefoot_mm: float) -> str:
    """
    Normalize stack height into categories.

    Args:
        stack_heel_mm: Heel stack height
        stack_forefoot_mm: Forefoot stack height

    Returns:
        Category: "minimal", "moderate", "maximal"

    Categories:
        - Minimal: heel ≤ 20mm
        - Moderate: heel 21-30mm
        - Maximal: heel 31mm+
    """
    if stack_heel_mm <= 20:
        return 'minimal'
    elif stack_heel_mm <= 30:
        return 'moderate'
    else:
        return 'maximal'


def normalize_weight(weight_g: float, gender: str) -> str:
    """
    Normalize weight into categories (gender-specific).

    Args:
        weight_g: Weight in grams (men's size 9 US / women's size 7 US)
        gender: "male" or "female"

    Returns:
        Category: "lightweight", "moderate", "heavy"

    Categories (Men):
        - Lightweight: ≤250g
        - Moderate: 251-320g
        - Heavy: 321g+

    Categories (Women):
        - Lightweight: ≤220g
        - Moderate: 221-280g
        - Heavy: 281g+
    """
    if gender == 'female':
        if weight_g <= 220:
            return 'lightweight'
        elif weight_g <= 280:
            return 'moderate'
        else:
            return 'heavy'
    else:  # male or unisex
        if weight_g <= 250:
            return 'lightweight'
        elif weight_g <= 320:
            return 'moderate'
        else:
            return 'heavy'


# ============================================================================
# Biomechanical Tag Generation
# ============================================================================

def generate_biomechanical_tags(product_specs: Dict) -> List[str]:
    """
    Generate biomechanical tags based on product specifications.

    Args:
        product_specs: Dictionary with lab and marketing specs

    Returns:
        List of tag names (e.g., ["SUITED_FOR_HEEL_STRIKER", "HIGH_CUSHIONING"])

    Rules are based on biomechanical research and industry standards.
    """
    tags = []

    # Extract specs
    drop_mm = product_specs.get('drop_mm')
    cushioning_ha = product_specs.get('cushioning_softness_ha')
    stack_heel = product_specs.get('stack_heel_mm')
    weight_g = product_specs.get('weight_g')
    stability_type = product_specs.get('stability_type')
    energy_return_pct = product_specs.get('energy_return_pct')

    # === Drop-based tags ===
    if drop_mm is not None:
        drop_category = normalize_drop(drop_mm)

        if drop_category == 'zero_drop':
            tags.append('SUITED_FOR_MIDFOOT_STRIKER')
            tags.append('SUITED_FOR_FOREFOOT_STRIKER')
            tags.append('ENCOURAGES_NATURAL_GAIT')
        elif drop_category in ['low_drop', 'moderate_drop']:
            tags.append('SUITED_FOR_MIDFOOT_STRIKER')
            tags.append('VERSATILE_STRIKE_PATTERN')
        elif drop_category == 'high_drop':
            tags.append('SUITED_FOR_HEEL_STRIKER')

    # === Cushioning-based tags ===
    if cushioning_ha is not None:
        cushioning_category = normalize_cushioning(cushioning_ha)

        if cushioning_category == 'soft':
            tags.append('HIGH_CUSHIONING')
            tags.append('SUITED_FOR_RECOVERY_RUNS')
        elif cushioning_category == 'firm':
            tags.append('RESPONSIVE_CUSHIONING')
            tags.append('SUITED_FOR_TEMPO_RUNS')

    # Stack height tags
    if stack_heel is not None:
        if stack_heel >= 30:
            tags.append('MAXIMAL_CUSHIONING')
            tags.append('HIGH_IMPACT_ABSORPTION')
        elif stack_heel <= 20:
            tags.append('GROUND_FEEL')
            tags.append('MINIMALIST_DESIGN')

    # === Weight-based tags ===
    if weight_g is not None:
        gender = product_specs.get('gender', 'male')
        weight_category = normalize_weight(weight_g, gender)

        if weight_category == 'lightweight':
            tags.append('LIGHTWEIGHT')
            tags.append('SUITED_FOR_RACING')
        elif weight_category == 'heavy':
            tags.append('DURABLE_CONSTRUCTION')

    # === Stability tags ===
    if stability_type:
        if stability_type in ['stability_mild', 'stability_strong', 'motion_control']:
            tags.append('SUITED_FOR_OVERPRONATION')
            tags.append('MEDIAL_SUPPORT')

        if stability_type == 'neutral':
            tags.append('SUITED_FOR_NEUTRAL_GAIT')

    # === Energy return tags ===
    if energy_return_pct is not None:
        if energy_return_pct >= 70:
            tags.append('HIGH_ENERGY_RETURN')
            tags.append('SUITED_FOR_TEMPO_RUNS')
        elif energy_return_pct <= 55:
            tags.append('STABLE_PLATFORM')

    # === Combined rules ===

    # Racing shoe profile: lightweight + firm + low drop + high energy return
    if (weight_g and weight_g <= 250 and
        cushioning_ha and cushioning_ha >= 60 and
        drop_mm and drop_mm <= 8 and
        energy_return_pct and energy_return_pct >= 70):
        tags.append('SUITED_FOR_RACING')
        tags.append('COMPETITIVE_EDGE')

    # Recovery shoe profile: heavy + soft + high stack
    if (weight_g and weight_g >= 300 and
        cushioning_ha and cushioning_ha <= 55 and
        stack_heel and stack_heel >= 30):
        tags.append('SUITED_FOR_RECOVERY_RUNS')
        tags.append('JOINT_PROTECTION')

    # Trail-specific tags (based on marketing specs)
    if product_specs.get('terrain_type') == 'trail':
        tags.append('TRAIL_OPTIMIZED')
        if weight_g and weight_g >= 300:
            tags.append('DURABLE_OUTSOLE')

    # Waterproof
    if product_specs.get('waterproof'):
        tags.append('WATERPROOF')
        tags.append('ALL_WEATHER')

    # Remove duplicates
    return list(set(tags))


# ============================================================================
# Database Operations
# ============================================================================

def fetch_products_for_enrichment(cursor):
    """
    Fetch all products with lab and marketing specs for enrichment.

    Returns:
        List of dictionaries with product data
    """
    query = """
        SELECT
            p.id as product_id,
            p.model_name,
            p.gender,
            p.primary_category,
            lab.drop_mm,
            lab.stack_heel_mm,
            lab.stack_forefoot_mm,
            lab.cushioning_softness_ha,
            lab.energy_return_pct,
            lab.weight_g,
            mkt.stability_normalized as stability_type,
            mkt.cushioning_normalized as cushioning_level,
            NULL as terrain_type,
            false as waterproof
        FROM stridematch_products p
        LEFT JOIN stridematch_product_specs_lab lab ON p.id = lab.product_id
        LEFT JOIN stridematch_product_specs_marketing mkt ON p.id = mkt.product_id
        WHERE lab.id IS NOT NULL OR mkt.id IS NOT NULL
    """

    cursor.execute(query)
    columns = [desc[0] for desc in cursor.description]

    products = []
    for row in cursor.fetchall():
        products.append(dict(zip(columns, row)))

    return products


def insert_enrichment_tags(cursor, product_id: str, tags: List[str]):
    """
    Insert enrichment tags for a product.

    Args:
        cursor: Database cursor
        product_id: Product UUID
        tags: List of tag names
    """
    # Delete existing tags for this product
    cursor.execute("""
        DELETE FROM stridematch_enrichment_tags
        WHERE product_id = %s
    """, (product_id,))

    # Insert new tags
    for tag in tags:
        cursor.execute("""
            INSERT INTO stridematch_enrichment_tags (
                product_id,
                tag_name,
                tag_category,
                confidence_score,
                created_at
            ) VALUES (
                %s, %s, %s, %s, NOW()
            )
        """, (
            product_id,
            tag,
            _categorize_tag(tag),
            1.0  # Rule-based tags have 100% confidence
        ))


def _categorize_tag(tag_name: str) -> str:
    """
    Categorize a tag into tag_category.

    Args:
        tag_name: Tag name (e.g., "SUITED_FOR_HEEL_STRIKER")

    Returns:
        Category: "biomechanics", "performance", "durability", "versatility"
    """
    biomechanics_keywords = [
        'STRIKER', 'GAIT', 'PRONATION', 'MIDFOOT', 'FOREFOOT', 'HEEL',
        'NATURAL', 'STRIKE_PATTERN'
    ]

    performance_keywords = [
        'RACING', 'TEMPO', 'SPEED', 'ENERGY', 'RESPONSIVE', 'COMPETITIVE',
        'LIGHTWEIGHT'
    ]

    durability_keywords = [
        'DURABLE', 'LIFESPAN', 'OUTSOLE', 'CONSTRUCTION'
    ]

    versatility_keywords = [
        'VERSATILE', 'ALL_WEATHER', 'TRAIL', 'WATERPROOF'
    ]

    recovery_keywords = [
        'RECOVERY', 'CUSHIONING', 'ABSORPTION', 'PROTECTION', 'JOINT'
    ]

    tag_upper = tag_name.upper()

    if any(kw in tag_upper for kw in biomechanics_keywords):
        return 'biomechanics'
    elif any(kw in tag_upper for kw in performance_keywords):
        return 'performance'
    elif any(kw in tag_upper for kw in durability_keywords):
        return 'durability'
    elif any(kw in tag_upper for kw in versatility_keywords):
        return 'versatility'
    elif any(kw in tag_upper for kw in recovery_keywords):
        return 'comfort'
    else:
        return 'general'


# ============================================================================
# Main ETL Functions
# ============================================================================

def run_normalization(cursor):
    """
    Run normalization on all products.

    This doesn't modify the database but logs normalized values.
    """
    print("=" * 60)
    print("ETL Pipeline - Normalization")
    print("=" * 60)
    print()

    products = fetch_products_for_enrichment(cursor)

    print(f"Found {len(products)} products to normalize")
    print()

    for product in products[:10]:  # Show first 10 for demo
        print(f"Product: {product['model_name']}")

        if product['drop_mm']:
            print(f"  Drop: {product['drop_mm']}mm → {normalize_drop(product['drop_mm'])}")

        if product['cushioning_softness_ha']:
            print(f"  Cushioning: {product['cushioning_softness_ha']} HA → {normalize_cushioning(product['cushioning_softness_ha'])}")

        if product['weight_g']:
            print(f"  Weight: {product['weight_g']}g → {normalize_weight(product['weight_g'], product['gender'])}")

        print()

    print(f"✅ Normalization complete (showed 10/{len(products)} products)")


def run_tag_generation(cursor, connection):
    """
    Generate and insert enrichment tags for all products.
    """
    print("=" * 60)
    print("ETL Pipeline - Tag Generation")
    print("=" * 60)
    print()

    products = fetch_products_for_enrichment(cursor)

    print(f"Generating tags for {len(products)} products...")
    print()

    tags_inserted = 0

    for i, product in enumerate(products, 1):
        # Generate tags
        tags = generate_biomechanical_tags(product)

        if tags:
            # Insert tags
            insert_enrichment_tags(cursor, product['product_id'], tags)
            tags_inserted += len(tags)

            print(f"{i}. {product['model_name']}: {len(tags)} tags")
            for tag in tags:
                print(f"   - {tag}")
            print()

        if i % 50 == 0:
            connection.commit()
            print(f"Committed {i} products...")

    connection.commit()

    print("=" * 60)
    print(f"✅ Generated {tags_inserted} tags for {len(products)} products")
    print("=" * 60)


# ============================================================================
# CLI Interface
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="StrideMatch ETL Pipeline - Data normalization and enrichment"
    )

    parser.add_argument(
        '--mode',
        choices=['normalize', 'generate-tags', 'all'],
        default='all',
        help='ETL operation to run'
    )

    args = parser.parse_args()

    # Connect to database
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        print("✅ Connected to PostgreSQL")
        print()
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        sys.exit(1)

    try:
        if args.mode in ['normalize', 'all']:
            run_normalization(cursor)
            print()

        if args.mode in ['generate-tags', 'all']:
            run_tag_generation(cursor, connection)

    except Exception as e:
        print(f"❌ ETL pipeline failed: {e}")
        connection.rollback()
        sys.exit(1)

    finally:
        cursor.close()
        connection.close()


if __name__ == '__main__':
    main()
