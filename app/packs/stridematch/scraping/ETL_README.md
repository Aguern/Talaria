# ETL Pipeline - Phase 5

Transforms raw scraped data into enriched, normalized data with biomechanical tags.

## 🎯 Purpose

The ETL (Extract-Transform-Load) pipeline processes product data in two stages:

1. **Normalization**: Convert continuous values into categorical classifications
   - Drop (mm) → zero_drop, low_drop, moderate_drop, high_drop
   - Cushioning (Shore A) → soft, balanced, firm
   - Weight (g) → lightweight, moderate, heavy

2. **Enrichment**: Generate biomechanical tags based on product specs
   - SUITED_FOR_HEEL_STRIKER
   - HIGH_CUSHIONING
   - LIGHTWEIGHT
   - ... (30+ tags)

## 🚀 Usage

### Run full pipeline (normalization + tag generation):
```bash
cd app/packs/stridematch/scraping
python etl_pipeline.py --mode all
```

### Run only normalization (no database changes):
```bash
python etl_pipeline.py --mode normalize
```

### Run only tag generation:
```bash
python etl_pipeline.py --mode generate-tags
```

## 📊 Normalization Rules

### Drop Categories

| Drop (mm) | Category | Use Case |
|-----------|----------|----------|
| 0-2mm | Zero Drop | Forefoot/midfoot strikers, natural gait |
| 3-6mm | Low Drop | Midfoot strikers, versatile |
| 7-10mm | Moderate Drop | Most runners, heel-to-midfoot |
| 11mm+ | High Drop | Heel strikers, traditional cushioning |

### Cushioning Categories (Shore A Hardness)

| Shore A | Category | Feel | Use Case |
|---------|----------|------|----------|
| ≤50 | Soft | Plush, high cushioning | Recovery runs, long distances |
| 51-65 | Balanced | Moderate cushioning | Daily training |
| 66+ | Firm | Responsive, road feel | Tempo, racing |

**Note**: Lower Shore A = softer material

### Weight Categories

**Men's Shoes** (size 9 US):
| Weight (g) | Category |
|------------|----------|
| ≤250g | Lightweight |
| 251-320g | Moderate |
| 321g+ | Heavy |

**Women's Shoes** (size 7 US):
| Weight (g) | Category |
|------------|----------|
| ≤220g | Lightweight |
| 221-280g | Moderate |
| 281g+ | Heavy |

### Stack Height Categories

| Heel Stack (mm) | Category |
|-----------------|----------|
| ≤20mm | Minimal |
| 21-30mm | Moderate |
| 31mm+ | Maximal |

## 🏷️ Biomechanical Tags

### Tag Generation Rules

The pipeline generates tags based on product specifications using research-backed rules:

#### Drop-Based Tags
- **Zero Drop (0-2mm)**:
  - `SUITED_FOR_MIDFOOT_STRIKER`
  - `SUITED_FOR_FOREFOOT_STRIKER`
  - `ENCOURAGES_NATURAL_GAIT`

- **High Drop (11mm+)**:
  - `SUITED_FOR_HEEL_STRIKER`

#### Cushioning-Based Tags
- **Soft (≤50 HA)**:
  - `HIGH_CUSHIONING`
  - `SUITED_FOR_RECOVERY_RUNS`

- **Firm (66+ HA)**:
  - `RESPONSIVE_CUSHIONING`
  - `SUITED_FOR_TEMPO_RUNS`

#### Stack Height Tags
- **Maximal (31mm+)**:
  - `MAXIMAL_CUSHIONING`
  - `HIGH_IMPACT_ABSORPTION`

- **Minimal (≤20mm)**:
  - `GROUND_FEEL`
  - `MINIMALIST_DESIGN`

#### Weight-Based Tags
- **Lightweight**:
  - `LIGHTWEIGHT`
  - `SUITED_FOR_RACING`

- **Heavy**:
  - `DURABLE_CONSTRUCTION`

#### Stability Tags
- **Stability/Motion Control**:
  - `SUITED_FOR_OVERPRONATION`
  - `MEDIAL_SUPPORT`

- **Neutral**:
  - `SUITED_FOR_NEUTRAL_GAIT`

#### Energy Return Tags
- **High (70%+)**:
  - `HIGH_ENERGY_RETURN`
  - `SUITED_FOR_TEMPO_RUNS`

#### Combined Rules (Multi-Spec)

**Racing Shoe Profile**:
- Lightweight (≤250g) + Firm (≥60 HA) + Low Drop (≤8mm) + High Energy Return (≥70%)
- → `SUITED_FOR_RACING`, `COMPETITIVE_EDGE`

**Recovery Shoe Profile**:
- Heavy (≥300g) + Soft (≤55 HA) + High Stack (≥30mm)
- → `SUITED_FOR_RECOVERY_RUNS`, `JOINT_PROTECTION`

**Trail Shoe**:
- Terrain = Trail + Heavy (≥300g)
- → `TRAIL_OPTIMIZED`, `DURABLE_OUTSOLE`

### Tag Categories

Tags are automatically categorized:

| Category | Examples |
|----------|----------|
| `biomechanics` | SUITED_FOR_HEEL_STRIKER, NATURAL_GAIT |
| `performance` | RACING, TEMPO_RUNS, LIGHTWEIGHT |
| `durability` | DURABLE_CONSTRUCTION, DURABLE_OUTSOLE |
| `comfort` | RECOVERY, HIGH_CUSHIONING, JOINT_PROTECTION |
| `versatility` | ALL_WEATHER, WATERPROOF, TRAIL_OPTIMIZED |

## 🔄 Data Flow

```
1. Fetch products with specs
   ↓
2. For each product:
   a. Normalize continuous values → categories
   b. Apply tag generation rules
   c. Delete existing tags
   d. Insert new tags
   ↓
3. Commit to database (batch of 50)
```

## 🧪 Testing

### Check normalized values (dry-run):
```bash
python etl_pipeline.py --mode normalize
```

This shows normalized values without modifying the database.

### Generate tags for all products:
```bash
python etl_pipeline.py --mode generate-tags
```

### Verify tags in database:
```bash
PGPASSWORD="password" psql -h localhost -p 5432 -U user -d saas_nr_db \
  -c "SELECT p.model_name, COUNT(t.id) as tag_count
      FROM stridematch_products p
      LEFT JOIN stridematch_enrichment_tags t ON p.id = t.product_id
      GROUP BY p.id, p.model_name
      ORDER BY tag_count DESC
      LIMIT 10;"
```

### View tags for specific product:
```bash
PGPASSWORD="password" psql -h localhost -p 5432 -U user -d saas_nr_db \
  -c "SELECT p.model_name, t.tag_name, t.tag_category, t.confidence_score
      FROM stridematch_enrichment_tags t
      JOIN stridematch_products p ON t.product_id = p.id
      WHERE p.model_name LIKE '%Pegasus%'
      ORDER BY t.tag_category, t.tag_name;"
```

## 📊 Example Output

```
============================================================
ETL Pipeline - Tag Generation
============================================================

Generating tags for 127 products...

1. Pegasus 41: 8 tags
   - SUITED_FOR_HEEL_STRIKER
   - HIGH_CUSHIONING
   - VERSATILE_STRIKE_PATTERN
   - MODERATE_WEIGHT
   - SUITED_FOR_TEMPO_RUNS
   - RESPONSIVE_CUSHIONING
   - HIGH_ENERGY_RETURN
   - SUITED_FOR_NEUTRAL_GAIT

2. Clifton 9: 9 tags
   - SUITED_FOR_HEEL_STRIKER
   - MAXIMAL_CUSHIONING
   - HIGH_IMPACT_ABSORPTION
   - LIGHTWEIGHT
   - SUITED_FOR_RECOVERY_RUNS
   - JOINT_PROTECTION
   - HIGH_CUSHIONING
   - SUITED_FOR_NEUTRAL_GAIT
   - DURABLE_CONSTRUCTION

...

============================================================
✅ Generated 847 tags for 127 products
============================================================
```

## 🐛 Troubleshooting

### No products found
**Problem**: `Found 0 products to normalize`

**Solution**: Ensure you've run the scrapers (Phase 3 & 4) to populate products and specs:
```bash
cd app/packs/stridematch/scraping/scrapy_projects/lab_scraper
scrapy crawl runrepeat

cd ../ecommerce_scraper
scrapy crawl irun
```

### Database connection error
**Problem**: `Database connection failed`

**Solution**: Ensure PostgreSQL is running and `.env` is configured:
```bash
docker-compose ps  # Check if db is running
docker-compose up -d db  # Start if needed
```

### Tags not appearing
**Problem**: Tags generated but not visible in database

**Solution**: Check if enrichment_tags table exists:
```bash
PGPASSWORD="password" psql -h localhost -p 5432 -U user -d saas_nr_db \
  -c "\\dt stridematch_enrichment_tags"
```

If missing, run schema initialization from Phase 1.

## 🔄 Re-running the Pipeline

The pipeline is **idempotent**: running it multiple times produces the same result.

- Existing tags are deleted before inserting new ones
- Safe to run after updating tag generation rules
- Recommended frequency: After each scraping session

## 📝 Notes

- **Confidence Score**: All rule-based tags have 100% confidence (1.0)
- **Future Enhancement**: ML-based tags could have variable confidence
- **Tag Versioning**: Consider adding `rule_version` field to track changes
- **Performance**: Processes ~100 products/second

## 🔄 Next Steps

After Phase 5, proceed to:
- **Phase 6**: Webhook API for automated pipeline triggers
