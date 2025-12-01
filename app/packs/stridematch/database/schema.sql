-- ============================================================================
-- StrideMatch Knowledge Core - PostgreSQL Database Schema
-- ============================================================================
--
-- This script creates all tables for the StrideMatch product catalog.
--
-- Architecture:
--   - PostgreSQL → Product catalog (this file)
--   - MongoDB → User profiles (see mongodb_schemas.py)
--   - Neo4j → Recommendation graph (see neo4j_init.cypher)
--
-- Usage:
--   psql -U stridematch -d stridematch -f schema.sql
--
-- Dependencies:
--   - PostgreSQL 15+
--   - pgvector extension (already installed via pgvector/pgvector Docker image)
--   - UUID extension
-- ============================================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";


-- ============================================================================
-- ENUMS - Product Classification Types
-- ============================================================================

CREATE TYPE gender_type AS ENUM ('male', 'female', 'unisex');

CREATE TYPE product_category_type AS ENUM (
    'running_road',
    'running_trail',
    'running_track',
    'walking',
    'training',
    'other'
);

CREATE TYPE stability_type AS ENUM (
    'neutral',
    'stability_mild',
    'stability_high',
    'motion_control'
);

CREATE TYPE cushioning_level AS ENUM (
    'low',
    'medium',
    'high',
    'ultra'
);

CREATE TYPE drop_category AS ENUM (
    'zero',    -- 0mm
    'low',     -- 1-4mm
    'medium',  -- 5-8mm
    'high'     -- 9mm+
);


-- ============================================================================
-- TABLE 1: stridematch_brands
-- Shoe brands (Nike, Adidas, Hoka, etc.)
-- GLOBAL TABLE (no tenant_id)
-- ============================================================================

CREATE TABLE stridematch_brands (
    -- Primary key
    id SERIAL PRIMARY KEY,

    -- Brand information
    name VARCHAR(100) UNIQUE NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,  -- URL-friendly name (e.g., "nike", "hoka-one-one")

    -- Metadata
    logo_url TEXT,
    website_url TEXT,
    country_origin CHAR(2),  -- ISO 3166-1 alpha-2 country code

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Indexes
CREATE INDEX ix_brands_name ON stridematch_brands(name);
CREATE INDEX ix_brands_slug ON stridematch_brands(slug);

-- Comments
COMMENT ON TABLE stridematch_brands IS 'Global table of shoe brands (Nike, Adidas, etc.)';
COMMENT ON COLUMN stridematch_brands.slug IS 'URL-friendly identifier (e.g., "nike", "hoka-one-one")';


-- ============================================================================
-- TABLE 2: stridematch_sizing_normalization
-- Size conversion tables: Maps native brand sizes to standard CM
-- Solves "42 Nike ≠ 42 Adidas" problem
-- GLOBAL TABLE (no tenant_id)
-- ============================================================================

CREATE TABLE stridematch_sizing_normalization (
    -- Primary key
    id SERIAL PRIMARY KEY,

    -- Foreign key to Brand
    brand_id INTEGER NOT NULL REFERENCES stridematch_brands(id) ON DELETE CASCADE,

    -- Gender
    gender gender_type NOT NULL,

    -- Native sizes (as displayed by brand)
    size_eu VARCHAR(10),   -- European size (e.g., "42", "42.5")
    size_us VARCHAR(10),   -- US size (e.g., "8.5", "9")
    size_uk VARCHAR(10),   -- UK size (e.g., "7.5", "8")

    -- Normalized size (SOURCE OF TRUTH)
    size_cm NUMERIC(4, 1) NOT NULL,  -- Size in centimeters (e.g., 26.5)

    -- Timestamp
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CONSTRAINT uq_brand_gender_size_cm UNIQUE (brand_id, gender, size_cm)
);

-- Indexes
CREATE INDEX ix_sizing_brand_id ON stridematch_sizing_normalization(brand_id);
CREATE INDEX ix_sizing_gender ON stridematch_sizing_normalization(gender);
CREATE INDEX ix_sizing_size_cm ON stridematch_sizing_normalization(size_cm);
CREATE INDEX ix_sizing_lookup ON stridematch_sizing_normalization(brand_id, gender, size_eu);

-- Comments
COMMENT ON TABLE stridematch_sizing_normalization IS 'Size conversion table: Maps brand-specific sizes (EU/US/UK) to standardized CM';
COMMENT ON COLUMN stridematch_sizing_normalization.size_cm IS 'Normalized foot length in centimeters (SOURCE OF TRUTH)';


-- ============================================================================
-- TABLE 3: stridematch_products
-- Product models (e.g., "Nike Pegasus 40", "Hoka Clifton 9")
-- GLOBAL TABLE (no tenant_id)
-- ============================================================================

CREATE TABLE stridematch_products (
    -- Primary key (UUID for scalability)
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Foreign key to Brand
    brand_id INTEGER NOT NULL REFERENCES stridematch_brands(id) ON DELETE CASCADE,

    -- Product information
    model_name VARCHAR(200) NOT NULL,  -- e.g., "Pegasus 40"
    full_name VARCHAR(300),            -- e.g., "Nike Air Zoom Pegasus 40"

    -- Category
    primary_category product_category_type NOT NULL,
    gender gender_type NOT NULL,

    -- Description
    description TEXT,

    -- Release info
    release_year INTEGER,
    is_active BOOLEAN DEFAULT TRUE,  -- Still in production?

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Indexes
CREATE INDEX ix_products_brand_id ON stridematch_products(brand_id);
CREATE INDEX ix_products_model_name ON stridematch_products(model_name);
CREATE INDEX ix_products_category ON stridematch_products(primary_category);
CREATE INDEX ix_products_gender ON stridematch_products(gender);
CREATE INDEX ix_products_is_active ON stridematch_products(is_active);
CREATE INDEX ix_products_release_year ON stridematch_products(release_year);
CREATE INDEX ix_product_brand_model ON stridematch_products(brand_id, model_name);

-- Comments
COMMENT ON TABLE stridematch_products IS 'Shoe product models (e.g., Nike Pegasus 40, Hoka Clifton 9)';
COMMENT ON COLUMN stridematch_products.is_active IS 'Indicates if product is still in production';


-- ============================================================================
-- TABLE 4: stridematch_product_variants
-- Product variants: Specific SKUs (color + size combinations)
-- GLOBAL TABLE (no tenant_id)
-- ============================================================================

CREATE TABLE stridematch_product_variants (
    -- Primary key (SKU = Stock Keeping Unit)
    sku VARCHAR(100) PRIMARY KEY,

    -- Foreign key to Product
    product_id UUID NOT NULL REFERENCES stridematch_products(id) ON DELETE CASCADE,

    -- Variant attributes
    color VARCHAR(100),
    color_hex CHAR(7),          -- Hex color code (e.g., "#FF5733")
    size_native VARCHAR(10),    -- Native size as displayed (e.g., "42", "9 US")

    -- E-commerce data
    source_url TEXT,            -- Product page URL
    source_site VARCHAR(100),   -- e.g., "i-run.fr", "alltricks.fr"
    price_eur NUMERIC(8, 2),    -- Current price in EUR
    price_updated_at TIMESTAMP WITH TIME ZONE,

    -- Media
    image_url TEXT,

    -- Availability
    is_available BOOLEAN DEFAULT TRUE,
    stock_status VARCHAR(50),   -- "in_stock", "low_stock", "out_of_stock"

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Indexes
CREATE INDEX ix_variants_product_id ON stridematch_product_variants(product_id);
CREATE INDEX ix_variants_color ON stridematch_product_variants(color);
CREATE INDEX ix_variants_size_native ON stridematch_product_variants(size_native);
CREATE INDEX ix_variants_source_site ON stridematch_product_variants(source_site);
CREATE INDEX ix_variants_is_available ON stridematch_product_variants(is_available);
CREATE INDEX ix_variant_product_color ON stridematch_product_variants(product_id, color);

-- Comments
COMMENT ON TABLE stridematch_product_variants IS 'Product variants (SKUs): specific color + size combinations with pricing';
COMMENT ON COLUMN stridematch_product_variants.sku IS 'Stock Keeping Unit: unique identifier for this specific variant';


-- ============================================================================
-- TABLE 5: stridematch_product_specs_lab
-- Laboratory/Technical Specifications (objective data from lab tests)
-- Source: RunRepeat, Solereview, RunningShoesGuru
-- One-to-one relationship with Product
-- GLOBAL TABLE (no tenant_id)
-- ============================================================================

CREATE TABLE stridematch_product_specs_lab (
    -- Primary key
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Foreign key to Product (one-to-one)
    product_id UUID UNIQUE NOT NULL REFERENCES stridematch_products(id) ON DELETE CASCADE,

    -- Geometry (Critical for biomechanical matching)
    drop_mm NUMERIC(4, 1),             -- Heel-to-toe drop in mm (e.g., 8.0)
    stack_heel_mm NUMERIC(5, 1),       -- Heel stack height in mm
    stack_forefoot_mm NUMERIC(5, 1),   -- Forefoot stack height in mm

    -- Cushioning (Objective measurement)
    cushioning_softness_ha NUMERIC(4, 1),  -- Shore Hardness A (e.g., 11.9)
    energy_return_pct NUMERIC(4, 1),       -- Energy return percentage (e.g., 65.0)

    -- Weight
    weight_g NUMERIC(6, 1),  -- Weight in grams (e.g., 285.0)

    -- Durability
    median_lifespan_km NUMERIC(6, 1),  -- Median lifespan in km (e.g., 650.0)

    -- Midsole Technology
    midsole_material VARCHAR(200),  -- e.g., "React X foam", "EVA + TPU plate"

    -- Data source tracking
    source_lab VARCHAR(100),  -- e.g., "RunRepeat", "Solereview", "RunningShoesGuru"
    test_date TIMESTAMP WITH TIME ZONE,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Indexes
CREATE INDEX ix_lab_specs_product_id ON stridematch_product_specs_lab(product_id);
CREATE INDEX ix_lab_specs_drop_mm ON stridematch_product_specs_lab(drop_mm);
CREATE INDEX ix_lab_specs_cushioning ON stridematch_product_specs_lab(cushioning_softness_ha);
CREATE INDEX ix_lab_specs_weight_g ON stridematch_product_specs_lab(weight_g);

-- Comments
COMMENT ON TABLE stridematch_product_specs_lab IS 'Laboratory-tested technical specifications (OBJECTIVE FACTS)';
COMMENT ON COLUMN stridematch_product_specs_lab.cushioning_softness_ha IS 'Shore Hardness A scale: lower = softer cushioning';


-- ============================================================================
-- TABLE 6: stridematch_product_specs_marketing
-- Marketing/Brand Specifications (subjective claims by manufacturers)
-- Source: Brand websites, e-commerce descriptions
-- One-to-one relationship with Product
-- GLOBAL TABLE (no tenant_id)
-- ============================================================================

CREATE TABLE stridematch_product_specs_marketing (
    -- Primary key
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Foreign key to Product (one-to-one)
    product_id UUID UNIQUE NOT NULL REFERENCES stridematch_products(id) ON DELETE CASCADE,

    -- Brand claims (raw text)
    stability_type_brand VARCHAR(100),    -- e.g., "Neutral", "Stability", "Motion Control"
    cushioning_type_brand VARCHAR(100),   -- e.g., "Soft", "Balanced", "Responsive"
    use_case_brand VARCHAR(200),          -- e.g., "Daily training", "Racing", "Long distance"

    -- Normalized values (mapped to StrideMatch scale via ETL)
    stability_normalized stability_type,
    cushioning_normalized cushioning_level,
    drop_normalized drop_category,

    -- Marketing description
    marketing_tagline VARCHAR(500),  -- e.g., "Fly like never before"

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Indexes
CREATE INDEX ix_marketing_specs_product_id ON stridematch_product_specs_marketing(product_id);
CREATE INDEX ix_marketing_specs_stability ON stridematch_product_specs_marketing(stability_normalized);
CREATE INDEX ix_marketing_specs_cushioning ON stridematch_product_specs_marketing(cushioning_normalized);
CREATE INDEX ix_marketing_specs_drop ON stridematch_product_specs_marketing(drop_normalized);

-- Comments
COMMENT ON TABLE stridematch_product_specs_marketing IS 'Marketing claims by brands (SUBJECTIVE, not lab-verified)';
COMMENT ON COLUMN stridematch_product_specs_marketing.stability_normalized IS 'Normalized stability type (mapped from brand claim)';


-- ============================================================================
-- TABLE 7: stridematch_enrichment_tags
-- AI-generated tags based on expert rules (Biomechanical Matching Matrix)
-- Created by ETL pipeline (Phase 5)
-- Many-to-one relationship with Product
-- GLOBAL TABLE (no tenant_id)
-- ============================================================================

CREATE TABLE stridematch_enrichment_tags (
    -- Primary key
    id SERIAL PRIMARY KEY,

    -- Foreign key to Product
    product_id UUID NOT NULL REFERENCES stridematch_products(id) ON DELETE CASCADE,

    -- Tag information
    tag_name VARCHAR(100) NOT NULL,      -- e.g., "SUITED_FOR_HEEL_STRIKER"
    tag_category VARCHAR(50),            -- e.g., "biomechanics", "durability", "terrain"

    -- Tag metadata
    confidence_score NUMERIC(3, 2),      -- Confidence 0.00-1.00 (if probabilistic)
    rule_source VARCHAR(200),            -- Which rule generated this tag

    -- Timestamp
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CONSTRAINT uq_product_tag UNIQUE (product_id, tag_name)
);

-- Indexes
CREATE INDEX ix_enrichment_tags_product_id ON stridematch_enrichment_tags(product_id);
CREATE INDEX ix_enrichment_tags_tag_name ON stridematch_enrichment_tags(tag_name);
CREATE INDEX ix_enrichment_tags_tag_category ON stridematch_enrichment_tags(tag_category);
CREATE INDEX ix_tag_lookup ON stridematch_enrichment_tags(tag_name, tag_category);

-- Comments
COMMENT ON TABLE stridematch_enrichment_tags IS 'AI-generated tags based on expert biomechanical matching rules';
COMMENT ON COLUMN stridematch_enrichment_tags.tag_name IS 'Tag name (e.g., SUITED_FOR_HEEL_STRIKER, HIGH_DURABILITY)';


-- ============================================================================
-- SEED DATA - Initial Brands (Optional)
-- ============================================================================

-- Insert major running shoe brands
INSERT INTO stridematch_brands (name, slug, website_url, country_origin) VALUES
    ('Nike', 'nike', 'https://www.nike.com', 'US'),
    ('Adidas', 'adidas', 'https://www.adidas.com', 'DE'),
    ('Hoka', 'hoka', 'https://www.hoka.com', 'FR'),
    ('Asics', 'asics', 'https://www.asics.com', 'JP'),
    ('Brooks', 'brooks', 'https://www.brooksrunning.com', 'US'),
    ('New Balance', 'new-balance', 'https://www.newbalance.com', 'US'),
    ('Saucony', 'saucony', 'https://www.saucony.com', 'US'),
    ('Mizuno', 'mizuno', 'https://www.mizuno.com', 'JP'),
    ('On Running', 'on-running', 'https://www.on-running.com', 'CH'),
    ('Altra', 'altra', 'https://www.altrarunning.com', 'US')
ON CONFLICT (name) DO NOTHING;


-- ============================================================================
-- DATABASE STATISTICS & MAINTENANCE
-- ============================================================================

-- Analyze tables for query optimization
ANALYZE stridematch_brands;
ANALYZE stridematch_sizing_normalization;
ANALYZE stridematch_products;
ANALYZE stridematch_product_variants;
ANALYZE stridematch_product_specs_lab;
ANALYZE stridematch_product_specs_marketing;
ANALYZE stridematch_enrichment_tags;


-- ============================================================================
-- GRANTS & PERMISSIONS (Adjust based on your security requirements)
-- ============================================================================

-- Grant appropriate permissions to your application user
-- Example (adjust as needed):
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO stridematch_app;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO stridematch_app;


-- ============================================================================
-- SCHEMA SUMMARY
-- ============================================================================

/*
Database Schema Summary:

TABLES:
1. stridematch_brands (10 seed brands inserted)
2. stridematch_sizing_normalization (to be populated by scrape_sizing.py)
3. stridematch_products (to be populated by ecommerce_scraper)
4. stridematch_product_variants (to be populated by ecommerce_scraper)
5. stridematch_product_specs_lab (to be populated by lab_scraper)
6. stridematch_product_specs_marketing (to be populated by ecommerce_scraper)
7. stridematch_enrichment_tags (to be populated by etl_pipeline.py)

RELATIONSHIPS:
- Brand → Products (1-to-many)
- Brand → SizingNormalization (1-to-many)
- Product → ProductVariants (1-to-many)
- Product → ProductSpecs_Lab (1-to-1)
- Product → ProductSpecs_Marketing (1-to-1)
- Product → Enrichment_Tags (1-to-many)

NEXT STEPS:
1. Run Phase 2: scrape_sizing.py to populate sizing tables
2. Run Phase 3: lab_scraper to populate ProductSpecs_Lab
3. Run Phase 4: ecommerce_scraper to populate Products, Variants, Marketing Specs
4. Run Phase 5: etl_pipeline.py to generate Enrichment_Tags

For MongoDB schema (user profiles), see: database/mongodb_schemas.py
For Neo4j schema (recommendation graph), see: database/neo4j_init.cypher
*/
