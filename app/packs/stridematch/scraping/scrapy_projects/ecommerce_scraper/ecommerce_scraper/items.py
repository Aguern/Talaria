"""
E-commerce Items - Phase 4

Defines Scrapy items for product data extracted from:
- i-run.fr
- alltricks.fr

Data structure matches schema.org/Product JSON-LD format.
"""

import scrapy


class ProductItem(scrapy.Item):
    """
    Item for product data (inserts into stridematch_products table).
    """

    # Product identification
    brand_name = scrapy.Field()  # e.g., "Nike"
    model_name = scrapy.Field()  # e.g., "Pegasus 41"
    full_name = scrapy.Field()  # e.g., "Nike Pegasus 41"

    # Categories
    primary_category = scrapy.Field()  # "running_road", "running_trail", etc.
    gender = scrapy.Field()  # "male", "female", "unisex"

    # Release info
    release_year = scrapy.Field()  # e.g., 2024

    # Marketing specs (will be split into ProductSpecs_Marketing)
    target_use = scrapy.Field()  # "training", "racing", "recovery"
    terrain_type = scrapy.Field()  # "road", "trail", "mixed"
    distance_category = scrapy.Field()  # "short", "middle", "long", "ultra"
    stability_type = scrapy.Field()  # "neutral", "stability_mild", "stability_strong", "motion_control"
    cushioning_level = scrapy.Field()  # "minimal", "moderate", "max"
    pace_category = scrapy.Field()  # "recovery", "easy", "tempo", "speed"
    waterproof = scrapy.Field()  # Boolean

    # Variants (will be split into ProductVariant items)
    variants = scrapy.Field()  # List of dicts with color, size, sku, price, stock, url

    # Metadata
    source_url = scrapy.Field()  # Product page URL
    scrape_date = scrapy.Field()  # Timestamp
    source = scrapy.Field()  # "irun" or "alltricks"


class ProductVariantItem(scrapy.Item):
    """
    Item for product variants (inserts into stridematch_product_variants table).
    """

    # Link to parent product
    parent_product_id = scrapy.Field()  # UUID of parent product

    # Variant identification
    color = scrapy.Field()  # e.g., "Black/White"
    size_eu = scrapy.Field()  # e.g., "42"
    sku = scrapy.Field()  # Retailer SKU

    # Pricing
    price_eur = scrapy.Field()  # Current price
    original_price_eur = scrapy.Field()  # MSRP
    is_on_sale = scrapy.Field()  # Boolean

    # Availability
    stock_status = scrapy.Field()  # "in_stock", "out_of_stock", "preorder"
    retailer_name = scrapy.Field()  # "irun" or "alltricks"
    retailer_url = scrapy.Field()  # Direct link to buy

    # Metadata
    scrape_date = scrapy.Field()


class ProductSpecsMarketingItem(scrapy.Item):
    """
    Item for marketing specs (inserts into stridematch_product_specs_marketing table).
    """

    # Link to parent product
    product_id = scrapy.Field()  # UUID of product

    # Marketing claims
    target_use = scrapy.Field()
    terrain_type = scrapy.Field()
    distance_category = scrapy.Field()
    stability_type = scrapy.Field()
    cushioning_level = scrapy.Field()
    pace_category = scrapy.Field()
    waterproof = scrapy.Field()

    # Metadata
    data_source = scrapy.Field()
    scrape_date = scrapy.Field()
