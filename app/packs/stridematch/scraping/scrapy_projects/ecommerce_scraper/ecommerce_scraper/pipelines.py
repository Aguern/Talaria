"""
Scrapy Pipelines - E-commerce Scraper

Pipelines for validating, classifying, and inserting product data into PostgreSQL.
"""

import psycopg2
import uuid
from datetime import datetime
from typing import Optional
from scrapy.exceptions import DropItem

from .utils import (
    classify_category,
    detect_gender,
    extract_model_from_name,
    extract_year_from_name,
    classify_stability,
    classify_cushioning,
    classify_terrain,
    classify_distance,
    classify_pace,
    is_waterproof,
    find_brand_id,
)
from .jsonld_parser import parse_availability


class ValidationPipeline:
    """
    Validate scraped product items before processing.
    """

    def process_item(self, item, spider):
        """Validate item fields"""

        # Check required fields
        required_fields = ['brand_name', 'full_name', 'source']
        for field in required_fields:
            if not item.get(field):
                raise DropItem(f"Missing required field: {field} in {item}")

        # Extract model name if not present
        if not item.get('model_name'):
            item['model_name'] = extract_model_from_name(
                item['full_name'],
                item['brand_name']
            )

        # Add scrape timestamp
        if 'scrape_date' not in item:
            item['scrape_date'] = datetime.utcnow().isoformat()

        spider.logger.info(f"✅ Validated: {item['brand_name']} {item['model_name']}")
        return item


class CategoryClassificationPipeline:
    """
    Automatically classify products into categories based on name and description.
    """

    def process_item(self, item, spider):
        """Classify product into categories"""

        product_name = item.get('full_name', '')
        description = item.get('description', '')

        # Classify primary category
        if not item.get('primary_category'):
            item['primary_category'] = classify_category(product_name, description)

        # Detect gender
        if not item.get('gender'):
            item['gender'] = detect_gender(
                product_name,
                description,
                item.get('source_url', '')
            )

        # Extract release year
        if not item.get('release_year'):
            item['release_year'] = extract_year_from_name(product_name)

        # Marketing specs classification
        item['stability_type'] = classify_stability(product_name, description)
        item['cushioning_level'] = classify_cushioning(product_name, description)
        item['terrain_type'] = classify_terrain(item['primary_category'], product_name)
        item['distance_category'] = classify_distance(product_name, description)
        item['pace_category'] = classify_pace(product_name, description)
        item['waterproof'] = is_waterproof(product_name, description)

        spider.logger.info(
            f"🏷️  Classified: {item['brand_name']} {item['model_name']} "
            f"→ {item['primary_category']} / {item['gender']}"
        )

        return item


class PostgreSQLPipeline:
    """
    Insert product data into PostgreSQL.

    Handles insertion of:
    - stridematch_products
    - stridematch_product_variants
    - stridematch_product_specs_marketing
    """

    def __init__(self, db_config):
        self.db_config = db_config
        self.connection = None
        self.cursor = None

        # Statistics
        self.products_inserted = 0
        self.products_updated = 0
        self.variants_inserted = 0
        self.specs_inserted = 0
        self.items_failed = 0

    @classmethod
    def from_crawler(cls, crawler):
        """Load database configuration from settings"""
        return cls(
            db_config={
                'host': crawler.settings.get('POSTGRES_HOST'),
                'port': crawler.settings.get('POSTGRES_PORT'),
                'database': crawler.settings.get('POSTGRES_DB'),
                'user': crawler.settings.get('POSTGRES_USER'),
                'password': crawler.settings.get('POSTGRES_PASSWORD'),
            }
        )

    def open_spider(self, spider):
        """Open database connection when spider starts"""
        try:
            self.connection = psycopg2.connect(**self.db_config)
            self.cursor = self.connection.cursor()
            spider.logger.info("✅ PostgreSQL connection established")
        except psycopg2.Error as e:
            spider.logger.error(f"❌ Database connection failed: {e}")
            raise

    def close_spider(self, spider):
        """Close database connection and log statistics"""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()

        spider.logger.info("=" * 60)
        spider.logger.info("E-commerce Scraper Statistics:")
        spider.logger.info(f"  ✅ Products Inserted: {self.products_inserted}")
        spider.logger.info(f"  🔄 Products Updated: {self.products_updated}")
        spider.logger.info(f"  📦 Variants Inserted: {self.variants_inserted}")
        spider.logger.info(f"  📝 Specs Inserted: {self.specs_inserted}")
        spider.logger.info(f"  ❌ Failed: {self.items_failed}")
        spider.logger.info("=" * 60)

    def process_item(self, item, spider):
        """
        Insert or update product, variants, and specs.

        Strategy:
        1. Find or insert product
        2. Insert product variants
        3. Insert marketing specs
        """
        try:
            # Find brand_id
            brand_id = find_brand_id(self.cursor, item['brand_name'])

            if not brand_id:
                spider.logger.warning(
                    f"⚠️  Brand not found: {item['brand_name']}"
                )
                self.items_failed += 1
                raise DropItem(f"Brand not found: {item['brand_name']}")

            # Insert or update product
            product_id = self._upsert_product(item, brand_id, spider)

            # Insert variants
            if item.get('variants'):
                for variant_data in item['variants']:
                    self._insert_variant(product_id, variant_data, item, spider)

            # Insert marketing specs
            self._upsert_marketing_specs(product_id, item, spider)

            self.connection.commit()
            return item

        except Exception as e:
            self.connection.rollback()
            self.items_failed += 1
            spider.logger.error(f"❌ Failed to insert item: {e}")
            raise DropItem(f"Database error: {e}")

    def _upsert_product(self, item: dict, brand_id: int, spider) -> str:
        """
        Insert or update product in stridematch_products table.

        Returns:
            Product UUID
        """
        # Check if product already exists
        self.cursor.execute("""
            SELECT id FROM stridematch_products
            WHERE brand_id = %s
            AND LOWER(model_name) = LOWER(%s)
            AND gender = %s
        """, (brand_id, item['model_name'], item['gender']))

        existing = self.cursor.fetchone()

        if existing:
            # Update existing product
            product_id = str(existing[0])
            self._update_product(product_id, item, spider)
            self.products_updated += 1
        else:
            # Insert new product
            product_id = str(uuid.uuid4())
            self._insert_product(product_id, item, brand_id, spider)
            self.products_inserted += 1

        return product_id

    def _insert_product(self, product_id: str, item: dict, brand_id: int, spider):
        """Insert new product"""
        query = """
            INSERT INTO stridematch_products (
                id,
                brand_id,
                model_name,
                primary_category,
                gender,
                release_year,
                created_at,
                updated_at
            ) VALUES (
                %s, %s, %s, %s, %s, %s, NOW(), NOW()
            )
        """

        self.cursor.execute(query, (
            product_id,
            brand_id,
            item['model_name'],
            item['primary_category'],
            item['gender'],
            item.get('release_year'),
        ))

        spider.logger.info(
            f"✅ Inserted product: {item['brand_name']} {item['model_name']} (ID: {product_id})"
        )

    def _update_product(self, product_id: str, item: dict, spider):
        """Update existing product"""
        query = """
            UPDATE stridematch_products
            SET
                release_year = COALESCE(%s, release_year),
                updated_at = NOW()
            WHERE id = %s
        """

        self.cursor.execute(query, (
            item.get('release_year'),
            product_id,
        ))

        spider.logger.info(
            f"🔄 Updated product: {item['brand_name']} {item['model_name']} (ID: {product_id})"
        )

    def _insert_variant(self, product_id: str, variant_data: dict, item: dict, spider):
        """Insert product variant"""

        # Parse availability
        stock_status = parse_availability(variant_data.get('availability', ''))

        # Check if variant already exists (same product + color + size)
        self.cursor.execute("""
            SELECT id FROM stridematch_product_variants
            WHERE product_id = %s
            AND retailer_name = %s
            AND color = %s
            AND size_eu = %s
        """, (
            product_id,
            item['source'],
            variant_data.get('color', 'Standard'),
            variant_data.get('size', 'Standard')
        ))

        existing = self.cursor.fetchone()

        if existing:
            # Update existing variant (price might have changed)
            self.cursor.execute("""
                UPDATE stridematch_product_variants
                SET
                    price_eur = %s,
                    stock_status = %s,
                    retailer_url = %s,
                    updated_at = NOW()
                WHERE id = %s
            """, (
                variant_data.get('price'),
                stock_status,
                variant_data.get('url'),
                existing[0]
            ))
        else:
            # Insert new variant
            query = """
                INSERT INTO stridematch_product_variants (
                    product_id,
                    color,
                    size_eu,
                    sku,
                    price_eur,
                    stock_status,
                    retailer_name,
                    retailer_url,
                    created_at,
                    updated_at
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW()
                )
            """

            self.cursor.execute(query, (
                product_id,
                variant_data.get('color', 'Standard'),
                variant_data.get('size', 'Standard'),
                variant_data.get('sku'),
                variant_data.get('price'),
                stock_status,
                item['source'],
                variant_data.get('url'),
            ))

            self.variants_inserted += 1

    def _upsert_marketing_specs(self, product_id: str, item: dict, spider):
        """Insert or update marketing specs"""

        # Check if specs already exist
        self.cursor.execute("""
            SELECT id FROM stridematch_product_specs_marketing
            WHERE product_id = %s
        """, (product_id,))

        existing = self.cursor.fetchone()

        if existing:
            # Update existing specs
            query = """
                UPDATE stridematch_product_specs_marketing
                SET
                    target_use = COALESCE(%s, target_use),
                    terrain_type = COALESCE(%s, terrain_type),
                    distance_category = COALESCE(%s, distance_category),
                    stability_type = COALESCE(%s, stability_type),
                    cushioning_level = COALESCE(%s, cushioning_level),
                    pace_category = COALESCE(%s, pace_category),
                    waterproof = COALESCE(%s, waterproof),
                    data_source = %s,
                    last_updated = NOW()
                WHERE id = %s
            """

            self.cursor.execute(query, (
                item.get('target_use'),
                item.get('terrain_type'),
                item.get('distance_category'),
                item.get('stability_type'),
                item.get('cushioning_level'),
                item.get('pace_category'),
                item.get('waterproof'),
                item['source'],
                existing[0]
            ))
        else:
            # Insert new specs
            query = """
                INSERT INTO stridematch_product_specs_marketing (
                    product_id,
                    target_use,
                    terrain_type,
                    distance_category,
                    stability_type,
                    cushioning_level,
                    pace_category,
                    waterproof,
                    data_source,
                    last_updated
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW()
                )
            """

            self.cursor.execute(query, (
                product_id,
                item.get('target_use'),
                item.get('terrain_type'),
                item.get('distance_category'),
                item.get('stability_type'),
                item.get('cushioning_level'),
                item.get('pace_category'),
                item.get('waterproof'),
                item['source'],
            ))

            self.specs_inserted += 1
