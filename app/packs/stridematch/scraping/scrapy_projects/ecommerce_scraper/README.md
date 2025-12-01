# E-commerce Scraper - Phase 4

Scrapy project for extracting product data from French running e-commerce sites:
- **i-run.fr**: Major French running specialist
- **alltricks.fr**: Outdoor & running equipment

## 📊 Data Extracted

### Products (stridematch_products)
- ✅ Brand, Model name, Full name
- ✅ Primary category (running_road, running_trail, etc.)
- ✅ Gender
- ✅ Release year

### Product Variants (stridematch_product_variants)
- ✅ Color, Size (EU)
- ✅ Price (EUR), Original price
- ✅ Stock status
- ✅ Retailer name & URL
- ✅ SKU

### Marketing Specs (stridematch_product_specs_marketing)
- ✅ Stability type (neutral, stability, etc.)
- ✅ Cushioning level (minimal, moderate, max)
- ✅ Terrain type (road, trail, mixed)
- ✅ Distance category (short, middle, long, ultra)
- ✅ Pace category (recovery, easy, tempo, speed)
- ✅ Waterproof status

## 🚀 Usage

### Prerequisites

1. Docker containers running (PostgreSQL)
2. Database initialized with schema (Phase 1)
3. Brands seeded in `stridematch_brands` table

### Running Spiders

#### Scrape all products from i-run.fr:
```bash
cd app/packs/stridematch/scraping/scrapy_projects/ecommerce_scraper
scrapy crawl irun
```

#### Scrape specific category from i-run.fr:
```bash
scrapy crawl irun -a category=road-men
```

Available categories:
- `road-men`: Men's road running shoes
- `road-women`: Women's road running shoes
- `trail-men`: Men's trail running shoes
- `trail-women`: Women's trail running shoes

#### Scrape specific brand from i-run.fr:
```bash
scrapy crawl irun -a brand=nike
```

#### Scrape all products from alltricks.fr:
```bash
scrapy crawl alltricks
```

#### Scrape specific category from alltricks.fr:
```bash
scrapy crawl alltricks -a category=running
```

Available categories:
- `running`: Road running shoes
- `trail`: Trail running shoes

### Export to JSON (for debugging):
```bash
scrapy crawl irun -O output.json
```

### Run with custom settings:
```bash
scrapy crawl irun -s DOWNLOAD_DELAY=5 -s CONCURRENT_REQUESTS=4
```

## 🏗️ Architecture

```
ecommerce_scraper/
├── scrapy.cfg              # Scrapy project configuration
└── ecommerce_scraper/
    ├── __init__.py
    ├── settings.py         # Ethical scraping config
    ├── items.py            # ProductItem, ProductVariantItem definitions
    ├── middlewares.py      # Custom middlewares
    ├── pipelines.py        # Validation + Classification + PostgreSQL
    ├── jsonld_parser.py    # schema.org/Product JSON-LD parser
    ├── utils.py            # Classification functions
    └── spiders/
        ├── irun_spider.py
        └── alltricks_spider.py
```

## 🔄 Data Flow

1. **Spider** scrapes product page
2. **JSON-LD Parser** extracts structured data (schema.org/Product)
3. **ValidationPipeline** validates required fields
4. **CategoryClassificationPipeline** classifies product:
   - Primary category (road/trail/racing)
   - Gender (male/female/unisex)
   - Marketing specs (stability, cushioning, terrain, etc.)
5. **PostgreSQLPipeline** inserts/updates:
   - Product (if not exists)
   - Variants (colors, sizes, prices)
   - Marketing specs

## 🤖 JSON-LD Extraction

Modern e-commerce sites embed structured data in JSON-LD format following schema.org standards.

Example from HTML:
```html
<script type="application/ld+json">
{
  "@context": "https://schema.org/",
  "@type": "Product",
  "name": "Nike Pegasus 41",
  "brand": {
    "@type": "Brand",
    "name": "Nike"
  },
  "offers": {
    "@type": "Offer",
    "price": "140.00",
    "priceCurrency": "EUR",
    "availability": "https://schema.org/InStock"
  }
}
</script>
```

Our `jsonld_parser.py` module automatically extracts this data, making scraping more robust than CSS selectors.

## 🏷️ Automatic Classification

The `CategoryClassificationPipeline` uses keyword matching to classify products:

### Primary Category
- **Trail**: Keywords like "trail", "sentier", "montagne"
- **Racing**: Keywords like "racing", "spike", "compétition"
- **Road**: Default

### Gender
- **Female**: Keywords like "femme", "women", "woman"
- **Male**: Keywords like "homme", "men", "man"
- **Unisex**: Default

### Stability Type
- **Motion Control**: "motion control", "max support"
- **Stability Strong**: "guide", "structure", "support"
- **Stability Mild**: "stability", "pronation"
- **Neutral**: Default

### Cushioning Level
- **Minimal**: "minimal", "barefoot", "race"
- **Max**: "max", "ultra", "plush", "bondi"
- **Moderate**: Default

## 🧪 Testing

### Dry-run (scrape without database insertion):
Comment out PostgreSQLPipeline in `settings.py`:
```python
ITEM_PIPELINES = {
    'ecommerce_scraper.pipelines.ValidationPipeline': 100,
    'ecommerce_scraper.pipelines.CategoryClassificationPipeline': 200,
    # 'ecommerce_scraper.pipelines.PostgreSQLPipeline': 300,  # Commented
}
```

Then run with JSON export:
```bash
scrapy crawl irun -O test_output.json
```

### Check scraped data:
```bash
PGPASSWORD="password" psql -h localhost -p 5432 -U user -d saas_nr_db \
  -c "SELECT p.model_name, p.primary_category, p.gender, COUNT(v.id) as variants
      FROM stridematch_products p
      LEFT JOIN stridematch_product_variants v ON p.id = v.product_id
      GROUP BY p.id, p.model_name, p.primary_category, p.gender
      ORDER BY p.created_at DESC
      LIMIT 10;"
```

### Check variants:
```bash
PGPASSWORD="password" psql -h localhost -p 5432 -U user -d saas_nr_db \
  -c "SELECT p.model_name, v.color, v.size_eu, v.price_eur, v.stock_status, v.retailer_name
      FROM stridematch_product_variants v
      JOIN stridematch_products p ON v.product_id = p.id
      ORDER BY v.created_at DESC
      LIMIT 20;"
```

## 🐛 Troubleshooting

### No JSON-LD data found
**Problem**: `No JSON-LD data found on [URL]`

**Solution**:
1. Visit the page manually in browser
2. View page source (Ctrl+U)
3. Search for `application/ld+json`
4. If missing, update spider to use fallback extraction (`_fallback_extraction()` method)

### Brand not found
**Problem**: `Brand not found: [Brand Name]`

**Solution**: Add brand to `stridematch_brands` table:
```sql
INSERT INTO stridematch_brands (name, slug, website_url, country_origin)
VALUES ('Salomon', 'salomon', 'https://www.salomon.com', 'FR');
```

### Wrong CSS selectors
**Problem**: Spider finds no product links

**Solution**:
1. Visit listing page manually
2. Inspect HTML structure using browser DevTools
3. Update selectors in spider's `parse()` method
4. Test selectors in Scrapy shell:
```bash
scrapy shell "https://www.i-run.fr/chaussures-running-route-homme/"
>>> response.css('.product-item a::attr(href)').getall()
```

### Rate limiting / 429 errors
**Problem**: `HTTP 429 Too Many Requests`

**Solution**: Increase `DOWNLOAD_DELAY` in settings.py:
```python
DOWNLOAD_DELAY = 10  # Increase to 10 seconds
```

## 🛡️ Ethical Scraping

- ✅ `ROBOTSTXT_OBEY = True`: Respects robots.txt
- ✅ `DOWNLOAD_DELAY = 3s`: Polite delay between requests
- ✅ `CONCURRENT_REQUESTS_PER_DOMAIN = 2`: Limits concurrency
- ✅ `AUTOTHROTTLE_ENABLED = True`: Automatic rate limiting
- ✅ `HTTPCACHE_ENABLED = True`: Reduces server load (24h cache)

## 📝 Notes

- **Selectors are TEMPLATES**: CSS/XPath selectors in spiders are placeholders and must be adapted to the actual HTML structure of i-run.fr and alltricks.fr.
- **JSON-LD First**: Spiders prioritize JSON-LD extraction, falling back to HTML parsing if needed.
- **Upsert Logic**: Pipeline updates existing products instead of creating duplicates (matched by brand + model + gender).
- **Variant Deduplication**: Variants are matched by product + retailer + color + size.

## 🔄 Next Steps

After Phase 4, proceed to:
- **Phase 5**: ETL pipeline for data normalization and enrichment tag generation
- **Phase 6**: Webhook API for automated scraping triggers
