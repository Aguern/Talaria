# Lab Scraper - Phase 3

Scrapy project for extracting lab test data from RunRepeat.com and RunningShoesGuru.com.

## 📊 Data Extracted

### RunRepeat.com
- ✅ `drop_mm`: Heel-to-toe drop (mm)
- ✅ `stack_heel_mm`: Heel stack height
- ✅ `stack_forefoot_mm`: Forefoot stack height
- ✅ `cushioning_softness_ha`: Shore A hardness
- ✅ `energy_return_pct`: Energy return percentage
- ✅ `flexibility_index`: Flexibility score
- ✅ `torsional_rigidity_index`: Torsion resistance

### RunningShoesGuru.com
- ✅ `weight_g`: Weight in grams
- ✅ `median_lifespan_km`: Expected lifespan
- ✅ `midsole_material`: Midsole material (EVA, TPU, etc.)
- ✅ `outsole_material`: Outsole material
- ✅ `upper_material`: Upper material

## 🚀 Usage

### Prerequisites

1. Docker containers running (PostgreSQL)
2. Database initialized with schema from Phase 1
3. Brands seeded in `stridematch_brands` table

### Running Spiders

#### Scrape all brands from RunRepeat:
```bash
cd app/packs/stridematch/scraping/scrapy_projects/lab_scraper
scrapy crawl runrepeat
```

#### Scrape specific brand from RunRepeat:
```bash
scrapy crawl runrepeat -a brand=nike
```

#### Scrape all shoes from RunningShoesGuru:
```bash
scrapy crawl runningshoeguru
```

#### Scrape specific brand from RunningShoesGuru:
```bash
scrapy crawl runningshoeguru -a brand=hoka
```

### Export to JSON (for debugging):
```bash
scrapy crawl runrepeat -O output.json
```

### Run with custom settings:
```bash
scrapy crawl runrepeat -s DOWNLOAD_DELAY=5 -s CONCURRENT_REQUESTS=4
```

## 🏗️ Architecture

```
lab_scraper/
├── scrapy.cfg              # Scrapy project configuration
└── lab_scraper/
    ├── __init__.py
    ├── settings.py         # Ethical scraping config
    ├── items.py            # LabDataItem definition
    ├── middlewares.py      # Custom middlewares
    ├── pipelines.py        # Validation + PostgreSQL insertion
    ├── utils.py            # Brand/model matching functions
    └── spiders/
        ├── runrepeat_spider.py
        └── runningshoeguru_spider.py
```

## 🔄 Data Flow

1. **Spider** scrapes product page → extracts lab data
2. **ValidationPipeline** validates fields → normalizes gender → parses numeric values
3. **PostgreSQLPipeline** finds product_id using brand/model matching → inserts/updates `stridematch_product_specs_lab`

## 🛡️ Ethical Scraping

- ✅ `ROBOTSTXT_OBEY = True`: Respects robots.txt
- ✅ `DOWNLOAD_DELAY = 3-5s`: Polite delay between requests
- ✅ `CONCURRENT_REQUESTS_PER_DOMAIN = 2`: Limits concurrency
- ✅ `AUTOTHROTTLE_ENABLED = True`: Automatic rate limiting
- ✅ `HTTPCACHE_ENABLED = True`: Reduces server load

## ⚙️ Configuration

Environment variables (loaded from `.env`):
```bash
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=saas_nr_db
POSTGRES_USER=user
POSTGRES_PASSWORD=password
```

## 🧪 Testing

### Dry-run (scrape without database insertion):
Comment out PostgreSQLPipeline in `settings.py`:
```python
ITEM_PIPELINES = {
    'lab_scraper.pipelines.ValidationPipeline': 100,
    # 'lab_scraper.pipelines.PostgreSQLPipeline': 300,  # Commented
}
```

Then run with JSON export:
```bash
scrapy crawl runrepeat -O test_output.json
```

### Check scraped data:
```bash
PGPASSWORD="password" psql -h localhost -p 5432 -U user -d saas_nr_db \
  -c "SELECT p.model_name, s.drop_mm, s.stack_heel_mm, s.weight_g, s.data_source
      FROM stridematch_product_specs_lab s
      JOIN stridematch_products p ON s.product_id = p.id
      ORDER BY s.last_updated DESC
      LIMIT 10;"
```

## 🐛 Troubleshooting

### No products found in database
**Problem**: `Product not found in database: Nike Pegasus 41`

**Solution**: Ensure products exist in `stridematch_products` table:
```sql
SELECT id, brand_id, model_name FROM stridematch_products WHERE model_name LIKE '%Pegasus%';
```

If missing, you need to run the e-commerce scraper first (Phase 4) to populate products.

### Wrong CSS selectors
**Problem**: Spider extracts no data

**Solution**:
1. Visit target website manually
2. Inspect HTML structure using browser DevTools
3. Update XPath/CSS selectors in spider's `parse_product()` method
4. Test selectors in Scrapy shell:
```bash
scrapy shell "https://runrepeat.com/nike-pegasus-41"
>>> response.css('.spec-item::text').getall()
```

### Rate limiting / 429 errors
**Problem**: `HTTP 429 Too Many Requests`

**Solution**: Increase `DOWNLOAD_DELAY` in settings.py:
```python
DOWNLOAD_DELAY = 10  # Increase to 10 seconds
```

## 📝 Notes

- **Selectors are TEMPLATES**: XPath/CSS selectors in spiders are placeholders and must be adapted to the actual HTML structure of RunRepeat and RunningShoesGuru.
- **Brand/Model Matching**: Uses fuzzy matching (70% similarity threshold) to link scraped data with existing products.
- **Data Merging**: If lab specs already exist, pipeline only updates NULL fields, allowing data from multiple sources to be combined.

## 🔄 Next Steps

After Phase 3, proceed to:
- **Phase 4**: E-commerce scraper (i-run.fr, alltricks.fr) to populate products
- **Phase 5**: ETL pipeline for normalization and enrichment tags
- **Phase 6**: Webhook API for automation
