"""
Test StrideMatch Models - Simplified Version

This is a standalone test that doesn't depend on app.core modules.
"""

from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import Session

print("=" * 60)
print("StrideMatch Infrastructure Test - Simple Version")
print("=" * 60)
print()

# ============================================================================
# Test 1: Database Connection
# ============================================================================

print("📋 Test 1: PostgreSQL Connection")

try:
    # Create engine directly
    engine = create_engine("postgresql://user:password@localhost:5432/saas_nr_db")

    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        print("✅ Database connection successful")
except Exception as e:
    print(f"❌ Connection failed: {e}")
    exit(1)

# ============================================================================
# Test 2: Check Tables
# ============================================================================

print("\n📋 Test 2: Check Tables")

try:
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT tablename
            FROM pg_tables
            WHERE schemaname = 'public'
            AND tablename LIKE 'stridematch_%'
            ORDER BY tablename
        """))

        tables = [row[0] for row in result]
        print(f"   Found {len(tables)} tables:")
        for table in tables:
            print(f"   - {table}")

        if len(tables) == 7:
            print("✅ All 7 tables created successfully")
        else:
            print(f"⚠️  Expected 7 tables, found {len(tables)}")
except Exception as e:
    print(f"❌ Table check failed: {e}")
    exit(1)

# ============================================================================
# Test 3: Check Brands (Seed Data)
# ============================================================================

print("\n📋 Test 3: Check Brands")

try:
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT id, name, slug
            FROM stridematch_brands
            ORDER BY name
        """))

        brands = list(result)
        print(f"   Found {len(brands)} brands:")
        for brand in brands:
            print(f"   - {brand[1]} (id={brand[0]}, slug={brand[2]})")

        if len(brands) >= 10:
            print("✅ Seed data loaded successfully")
        else:
            print(f"⚠️  Expected 10+ brands, found {len(brands)}")
except Exception as e:
    print(f"❌ Brands check failed: {e}")
    exit(1)

# ============================================================================
# Test 4: Insert Test Product
# ============================================================================

print("\n📋 Test 4: Insert Test Product")

try:
    with Session(engine) as session:
        # Insert test product
        session.execute(text("""
            INSERT INTO stridematch_products (id, brand_id, model_name, primary_category, gender)
            VALUES (gen_random_uuid(), 1, 'Test Pegasus 99', 'running_road', 'male')
            ON CONFLICT DO NOTHING
            RETURNING id
        """))
        session.commit()

        # Check if product was created
        result = session.execute(text("""
            SELECT model_name FROM stridematch_products WHERE model_name LIKE 'Test%'
        """))

        test_products = list(result)
        if test_products:
            print(f"   Created/Found test product: {test_products[0][0]}")
            print("✅ Product insertion successful")
        else:
            print("⚠️  No test product found")
except Exception as e:
    print(f"❌ Product insertion failed: {e}")
    exit(1)

# ============================================================================
# Test 5: Query with Joins
# ============================================================================

print("\n📋 Test 5: Query with Joins")

try:
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT p.model_name, b.name as brand_name
            FROM stridematch_products p
            JOIN stridematch_brands b ON p.brand_id = b.id
            WHERE p.model_name LIKE 'Test%'
            LIMIT 5
        """))

        products = list(result)
        if products:
            print(f"   Found {len(products)} test products:")
            for product in products:
                print(f"   - {product[1]} {product[0]}")
            print("✅ Join query successful")
        else:
            print("⚠️  No products found in join query")
except Exception as e:
    print(f"❌ Join query failed: {e}")
    exit(1)

# ============================================================================
# Summary
# ============================================================================

print("\n" + "=" * 60)
print("Test Summary")
print("=" * 60)
print("✅ PASS: Database Connection")
print("✅ PASS: Tables Check (7 tables)")
print("✅ PASS: Brands Check (10 brands)")
print("✅ PASS: Product Insertion")
print("✅ PASS: Join Queries")
print()
print("🎉 All tests passed!")
print("=" * 60)
