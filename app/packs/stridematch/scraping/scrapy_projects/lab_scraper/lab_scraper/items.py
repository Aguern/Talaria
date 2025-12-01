"""
Lab Data Items - Phase 3

Defines Scrapy items for lab test data extracted from:
- RunRepeat.com: drop, stack heights, cushioning, energy return
- RunningShoesGuru.com: weight, lifespan, midsole material
"""

import scrapy


class LabDataItem(scrapy.Item):
    """Item for lab test specifications"""

    # Product identification
    brand_name = scrapy.Field()  # e.g., "Nike"
    model_name = scrapy.Field()  # e.g., "Pegasus 41"
    gender = scrapy.Field()  # "male", "female", "unisex"

    # RunRepeat data
    drop_mm = scrapy.Field()  # Heel-to-toe drop in mm
    stack_heel_mm = scrapy.Field()  # Heel stack height
    stack_forefoot_mm = scrapy.Field()  # Forefoot stack height
    cushioning_softness_ha = scrapy.Field()  # Shore A hardness
    energy_return_pct = scrapy.Field()  # Energy return percentage
    flexibility_index = scrapy.Field()  # Flexibility score
    torsional_rigidity_index = scrapy.Field()  # Torsion resistance

    # RunningShoesGuru data
    weight_g = scrapy.Field()  # Weight in grams (men's size 9 US)
    median_lifespan_km = scrapy.Field()  # Expected lifespan
    midsole_material = scrapy.Field()  # e.g., "EVA", "TPU"
    outsole_material = scrapy.Field()  # e.g., "Carbon rubber"
    upper_material = scrapy.Field()  # e.g., "Engineered mesh"

    # Metadata
    source_url = scrapy.Field()  # URL where data was scraped
    scrape_date = scrapy.Field()  # Timestamp of scraping
    source = scrapy.Field()  # "runrepeat" or "runningshoeguru"
