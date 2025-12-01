-- Insert test product for POC verification
-- This script tests the complete data pipeline

-- Generate a UUID for the product (using gen_random_uuid())
\set product_id `echo "'$(uuidgen | tr '[:upper:]' '[:lower:]')'"`

-- Insert test product
INSERT INTO stridematch_products (
    id, brand_id, model_name, primary_category, gender, release_year, created_at, updated_at
) VALUES (
    gen_random_uuid(),
    (SELECT id FROM stridematch_brands WHERE slug = 'nike'),
    'Test Pegasus 99 POC',
    'running_road',
    'male',
    2024,
    NOW(),
    NOW()
) RETURNING id as product_id \gset

-- Display inserted product
\echo 'Product inserted:'
SELECT id, model_name FROM stridematch_products WHERE model_name = 'Test Pegasus 99 POC';

-- Insert lab specs for the test product
INSERT INTO stridematch_product_specs_lab (
    product_id,
    drop_mm,
    stack_heel_mm,
    stack_forefoot_mm,
    cushioning_softness_ha,
    energy_return_pct,
    weight_g,
    data_source,
    last_updated
) VALUES (
    (SELECT id FROM stridematch_products WHERE model_name = 'Test Pegasus 99 POC' LIMIT 1),
    10.0,   -- drop: moderate (should generate SUITED_FOR_HEEL_STRIKER)
    32.0,   -- stack heel: maximal (should generate MAXIMAL_CUSHIONING)
    22.0,   -- stack forefoot
    55.0,   -- cushioning: balanced
    68.0,   -- energy return: good (should generate HIGH_ENERGY_RETURN)
    285.0,  -- weight: moderate for men
    'manual_test',
    NOW()
);

\echo 'Lab specs inserted'

-- Insert marketing specs
INSERT INTO stridematch_product_specs_marketing (
    product_id,
    stability_type,
    cushioning_level,
    terrain_type,
    distance_category,
    pace_category,
    waterproof,
    data_source,
    last_updated
) VALUES (
    (SELECT id FROM stridematch_products WHERE model_name = 'Test Pegasus 99 POC' LIMIT 1),
    'neutral',
    'moderate',
    'road',
    'middle',
    'tempo',
    false,
    'manual_test',
    NOW()
);

\echo 'Marketing specs inserted'

-- Display complete product
\echo ''
\echo '==================================================================='
\echo 'Test Product Summary:'
\echo '==================================================================='
SELECT
    b.name || ' ' || p.model_name as product,
    p.primary_category as category,
    p.gender,
    lab.drop_mm,
    lab.stack_heel_mm,
    lab.weight_g,
    lab.cushioning_softness_ha as cushioning_ha,
    mkt.stability_type,
    mkt.pace_category
FROM stridematch_products p
JOIN stridematch_brands b ON p.brand_id = b.id
LEFT JOIN stridematch_product_specs_lab lab ON p.id = lab.product_id
LEFT JOIN stridematch_product_specs_marketing mkt ON p.id = mkt.product_id
WHERE p.model_name = 'Test Pegasus 99 POC';

\echo ''
\echo 'Next step: Run ETL pipeline to generate tags'
\echo 'Command: docker-compose exec api python app/packs/stridematch/scraping/etl_pipeline.py --mode all'
