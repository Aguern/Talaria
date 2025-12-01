"""
Scrapy Pipelines - Lab Scraper

Pipelines for validating and inserting lab data into PostgreSQL.
"""

import psycopg2
from datetime import datetime
from typing import Optional
from scrapy.exceptions import DropItem

from .utils import find_product_id, parse_float, parse_gender


class ValidationPipeline:
    """
    Validate scraped items before database insertion.

    Drop items that are missing critical fields or have invalid data.
    """

    def process_item(self, item, spider):
        """Validate item fields"""

        # Check required fields
        required_fields = ['brand_name', 'model_name', 'source']
        for field in required_fields:
            if not item.get(field):
                raise DropItem(f"Missing required field: {field} in {item}")

        # Validate numeric fields
        numeric_fields = [
            'drop_mm', 'stack_heel_mm', 'stack_forefoot_mm',
            'cushioning_softness_ha', 'energy_return_pct',
            'weight_g', 'median_lifespan_km'
        ]

        for field in numeric_fields:
            if field in item and item[field] is not None:
                try:
                    parsed_value = parse_float(item[field])
                    item[field] = parsed_value
                except ValueError:
                    spider.logger.warning(f"Invalid {field} value: {item[field]}")
                    item[field] = None

        # Normalize gender
        if 'gender' in item:
            item['gender'] = parse_gender(item['gender'])
        else:
            item['gender'] = 'unisex'

        # Add scrape timestamp
        item['scrape_date'] = datetime.utcnow().isoformat()

        spider.logger.info(f"✅ Validated: {item['brand_name']} {item['model_name']}")
        return item


class PostgreSQLPipeline:
    """
    Insert lab data into PostgreSQL stridematch_product_specs_lab table.

    Handles connection pooling and automatic product matching.
    """

    def __init__(self, db_config):
        self.db_config = db_config
        self.connection = None
        self.cursor = None
        self.items_inserted = 0
        self.items_updated = 0
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
        spider.logger.info("Lab Scraper Statistics:")
        spider.logger.info(f"  ✅ Inserted: {self.items_inserted}")
        spider.logger.info(f"  🔄 Updated: {self.items_updated}")
        spider.logger.info(f"  ❌ Failed: {self.items_failed}")
        spider.logger.info("=" * 60)

    def process_item(self, item, spider):
        """
        Insert or update lab data in database.

        Strategy:
        1. Find product_id using brand/model matching
        2. Check if lab specs already exist
        3. Insert or update accordingly
        """
        try:
            # Find product_id
            product_id = find_product_id(
                self.cursor,
                item['brand_name'],
                item['model_name'],
                item.get('gender')
            )

            if not product_id:
                spider.logger.warning(
                    f"⚠️  Product not found in database: {item['brand_name']} {item['model_name']}"
                )
                self.items_failed += 1
                raise DropItem(f"Product not found: {item['brand_name']} {item['model_name']}")

            # Check if lab specs already exist
            self.cursor.execute("""
                SELECT id FROM stridematch_product_specs_lab
                WHERE product_id = %s
            """, (product_id,))

            existing = self.cursor.fetchone()

            if existing:
                # Update existing record
                self._update_lab_specs(existing[0], product_id, item, spider)
                self.items_updated += 1
            else:
                # Insert new record
                self._insert_lab_specs(product_id, item, spider)
                self.items_inserted += 1

            self.connection.commit()
            return item

        except Exception as e:
            self.connection.rollback()
            self.items_failed += 1
            spider.logger.error(f"❌ Failed to insert item: {e}")
            raise DropItem(f"Database error: {e}")

    def _insert_lab_specs(self, product_id: str, item: dict, spider):
        """Insert new lab specs record"""
        query = """
            INSERT INTO stridematch_product_specs_lab (
                product_id,
                drop_mm,
                stack_heel_mm,
                stack_forefoot_mm,
                cushioning_softness_ha,
                energy_return_pct,
                flexibility_index,
                torsional_rigidity_index,
                weight_g,
                median_lifespan_km,
                midsole_material,
                outsole_material,
                upper_material,
                data_source,
                last_updated
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW()
            )
        """

        self.cursor.execute(query, (
            product_id,
            item.get('drop_mm'),
            item.get('stack_heel_mm'),
            item.get('stack_forefoot_mm'),
            item.get('cushioning_softness_ha'),
            item.get('energy_return_pct'),
            item.get('flexibility_index'),
            item.get('torsional_rigidity_index'),
            item.get('weight_g'),
            item.get('median_lifespan_km'),
            item.get('midsole_material'),
            item.get('outsole_material'),
            item.get('upper_material'),
            item.get('source'),
        ))

        spider.logger.info(f"✅ Inserted: {item['brand_name']} {item['model_name']} (ID: {product_id})")

    def _update_lab_specs(self, spec_id: int, product_id: str, item: dict, spider):
        """
        Update existing lab specs record.

        Only update fields that are not NULL in the new item.
        This allows combining data from multiple sources.
        """
        updates = []
        params = []

        # Fields that can be updated
        updatable_fields = {
            'drop_mm': item.get('drop_mm'),
            'stack_heel_mm': item.get('stack_heel_mm'),
            'stack_forefoot_mm': item.get('stack_forefoot_mm'),
            'cushioning_softness_ha': item.get('cushioning_softness_ha'),
            'energy_return_pct': item.get('energy_return_pct'),
            'flexibility_index': item.get('flexibility_index'),
            'torsional_rigidity_index': item.get('torsional_rigidity_index'),
            'weight_g': item.get('weight_g'),
            'median_lifespan_km': item.get('median_lifespan_km'),
            'midsole_material': item.get('midsole_material'),
            'outsole_material': item.get('outsole_material'),
            'upper_material': item.get('upper_material'),
        }

        for field, value in updatable_fields.items():
            if value is not None:
                updates.append(f"{field} = %s")
                params.append(value)

        if not updates:
            spider.logger.info(f"⏭️  No new data to update for {item['brand_name']} {item['model_name']}")
            return

        # Add data_source and last_updated
        updates.append("data_source = %s")
        params.append(item.get('source'))
        updates.append("last_updated = NOW()")

        params.append(spec_id)

        query = f"""
            UPDATE stridematch_product_specs_lab
            SET {', '.join(updates)}
            WHERE id = %s
        """

        self.cursor.execute(query, params)
        spider.logger.info(f"🔄 Updated: {item['brand_name']} {item['model_name']} (ID: {product_id})")
