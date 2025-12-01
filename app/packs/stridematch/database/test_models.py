"""
Test StrideMatch SQLAlchemy Models

This script tests that the SQLAlchemy models are correctly defined and can
create/query data from the PostgreSQL database.

Usage:
    python test_models.py
"""

import os
import sys
from datetime import datetime
from uuid import uuid4

# Add parent directory to path to import models
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..')))

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from dotenv import load_dotenv

# Import StrideMatch models
from app.packs.stridematch.models import (
    Base,
    Brand,
    SizingNormalization,
    Product,
    ProductVariant,
    ProductSpecs_Lab,
    ProductSpecs_Marketing,
    Enrichment_Tag,
    Gender,
    ProductCategory,
    StabilityType,
    CushioningLevel,
    DropCategory
)

# Load environment variables
load_dotenv()

# ============================================================================
# Database Connection
# ============================================================================

def get_engine():
    """Create SQLAlchemy engine."""
    postgres_host = os.getenv('POSTGRES_HOST', 'localhost')
    postgres_port = os.getenv('POSTGRES_PORT', '5432')
    postgres_user = os.getenv('POSTGRES_USER', 'stridematch')
    postgres_password = os.getenv('POSTGRES_PASSWORD', '')
    postgres_db = os.getenv('POSTGRES_DB', 'stridematch')

    connection_string = f"postgresql://{postgres_user}:{postgres_password}@{postgres_host}:{postgres_port}/{postgres_db}"
    return create_engine(connection_string, echo=False)


# ============================================================================
# Test Functions
# ============================================================================

def test_connection(engine):
    """Test database connection."""
    print("📋 Test 1: Database Connection")
    try:
        with engine.connect() as conn:
            result = conn.execute(select(1))
            print("✅ Database connection successful")
            return True
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False


def test_brands(engine):
    """Test Brand model."""
    print("\n📋 Test 2: Brand Model")
    try:
        with Session(engine) as session:
            # Query all brands
            brands = session.execute(select(Brand)).scalars().all()
            print(f"   Found {len(brands)} brands:")
            for brand in brands[:5]:  # Show first 5
                print(f"   - {brand.name} (id={brand.id}, slug={brand.slug})")

            if len(brands) >= 10:
                print("✅ Brand model working correctly")
                return True
            else:
                print(f"⚠️  Expected 10+ brands, found {len(brands)}")
                return False
    except Exception as e:
        print(f"❌ Brand test failed: {e}")
        return False


def test_product_creation(engine):
    """Test creating a complete product with all relationships."""
    print("\n📋 Test 3: Product Creation (Full Relationship Test)")
    try:
        with Session(engine) as session:
            # Get Nike brand
            nike = session.execute(
                select(Brand).where(Brand.name == 'Nike')
            ).scalar_one_or_none()

            if not nike:
                print("⚠️  Nike brand not found, skipping product creation test")
                return False

            # Create test product
            product = Product(
                id=uuid4(),
                brand_id=nike.id,
                model_name="Test Pegasus 99",
                full_name="Nike Test Pegasus 99",
                primary_category=ProductCategory.RUNNING_ROAD,
                gender=Gender.MALE,
                description="Test product for infrastructure validation",
                release_year=2025,
                is_active=True
            )
            session.add(product)
            session.flush()  # Get product ID

            # Create lab specs
            lab_specs = ProductSpecs_Lab(
                product_id=product.id,
                drop_mm=10.0,
                stack_heel_mm=32.0,
                stack_forefoot_mm=22.0,
                cushioning_softness_ha=12.5,
                weight_g=285.0,
                median_lifespan_km=650.0,
                midsole_material="React X foam",
                source_lab="RunRepeat"
            )
            session.add(lab_specs)

            # Create marketing specs
            marketing_specs = ProductSpecs_Marketing(
                product_id=product.id,
                stability_type_brand="Neutral",
                cushioning_type_brand="Balanced",
                use_case_brand="Daily training",
                stability_normalized=StabilityType.NEUTRAL,
                cushioning_normalized=CushioningLevel.MEDIUM,
                drop_normalized=DropCategory.MEDIUM,
                marketing_tagline="Test product for the modern runner"
            )
            session.add(marketing_specs)

            # Create product variant
            variant = ProductVariant(
                sku="NIKE-PEGASUS-99-BLUE-42",
                product_id=product.id,
                color="Blue",
                color_hex="#0000FF",
                size_native="42",
                source_url="https://test.example.com/product",
                source_site="test.com",
                price_eur=150.00,
                is_available=True,
                stock_status="in_stock"
            )
            session.add(variant)

            # Create enrichment tags
            tags = [
                Enrichment_Tag(
                    product_id=product.id,
                    tag_name="SUITED_FOR_HEEL_STRIKER",
                    tag_category="biomechanics",
                    confidence_score=0.95,
                    rule_source="drop >= 8mm AND stability = neutral"
                ),
                Enrichment_Tag(
                    product_id=product.id,
                    tag_name="SUITED_FOR_NEUTRAL_RUNNER",
                    tag_category="biomechanics",
                    confidence_score=1.0,
                    rule_source="stability = neutral"
                )
            ]
            session.add_all(tags)

            # Commit all changes
            session.commit()

            print(f"   Created product: {product.model_name}")
            print(f"   - Brand: {nike.name}")
            print(f"   - Lab specs: drop={lab_specs.drop_mm}mm, weight={lab_specs.weight_g}g")
            print(f"   - Marketing specs: {marketing_specs.stability_normalized.value}")
            print(f"   - Variant SKU: {variant.sku}")
            print(f"   - Tags: {len(tags)} tags")
            print("✅ Product creation successful")
            return True

    except Exception as e:
        print(f"❌ Product creation failed: {e}")
        return False


def test_sizing_normalization(engine):
    """Test SizingNormalization model."""
    print("\n📋 Test 4: Sizing Normalization")
    try:
        with Session(engine) as session:
            # Get Nike brand
            nike = session.execute(
                select(Brand).where(Brand.name == 'Nike')
            ).scalar_one_or_none()

            if not nike:
                print("⚠️  Nike brand not found")
                return False

            # Create test sizing data
            sizing = SizingNormalization(
                brand_id=nike.id,
                gender=Gender.MALE,
                size_eu="42",
                size_us="8.5",
                size_uk="7.5",
                size_cm=26.5
            )
            session.add(sizing)
            session.commit()

            print(f"   Created sizing: Nike Men's EU:42 = {sizing.size_cm}cm")
            print("✅ Sizing normalization successful")
            return True

    except Exception as e:
        # May fail if sizing already exists (unique constraint)
        if "duplicate key" in str(e).lower():
            print("   Sizing data already exists (expected)")
            print("✅ Sizing normalization constraint working")
            return True
        else:
            print(f"❌ Sizing test failed: {e}")
            return False


def test_query_with_joins(engine):
    """Test complex query with joins."""
    print("\n📋 Test 5: Complex Query with Joins")
    try:
        with Session(engine) as session:
            # Query products with all relationships
            stmt = (
                select(Product, Brand, ProductSpecs_Lab)
                .join(Brand, Product.brand_id == Brand.id)
                .join(ProductSpecs_Lab, Product.id == ProductSpecs_Lab.product_id, isouter=True)
                .where(Product.model_name.like('%Test%'))
                .limit(5)
            )

            results = session.execute(stmt).all()

            print(f"   Found {len(results)} test products:")
            for product, brand, lab_specs in results:
                drop = lab_specs.drop_mm if lab_specs else "N/A"
                print(f"   - {brand.name} {product.model_name} (drop: {drop}mm)")

            print("✅ Complex query successful")
            return True

    except Exception as e:
        print(f"❌ Query test failed: {e}")
        return False


# ============================================================================
# Main Test Suite
# ============================================================================

def main():
    print("=" * 60)
    print("StrideMatch SQLAlchemy Models Test")
    print("=" * 60)
    print()

    # Create engine
    engine = get_engine()

    # Run tests
    results = []
    results.append(("Database Connection", test_connection(engine)))
    results.append(("Brand Model", test_brands(engine)))
    results.append(("Product Creation", test_product_creation(engine)))
    results.append(("Sizing Normalization", test_sizing_normalization(engine)))
    results.append(("Complex Queries", test_query_with_joins(engine)))

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")

    print()
    print(f"Results: {passed}/{total} tests passed")

    if passed == total:
        print("✅ All tests passed!")
        return 0
    else:
        print(f"⚠️  {total - passed} test(s) failed")
        return 1


if __name__ == '__main__':
    sys.exit(main())
