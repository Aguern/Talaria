"""
StrideMatch Sizing Scraper - Phase 2

This script scrapes size conversion tables from brand websites to populate
the SizingNormalization table in PostgreSQL.

Critical Mission:
    Solve the "42 Nike ≠ 42 Adidas" problem by creating a unified size database
    where all sizes are normalized to centimeters.

Target Brands:
    - Nike
    - Adidas
    - Asics
    - Hoka
    - Brooks

Architecture:
    - Uses requests + BeautifulSoup for simple HTML parsing
    - Falls back to Selenium for JavaScript-heavy pages
    - Inserts data into PostgreSQL stridematch_sizing_normalization table

Usage:
    python scrape_sizing.py --brand nike
    python scrape_sizing.py --brand all
    python scrape_sizing.py --brand nike --dry-run
"""

import os
import sys
import argparse
import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import psycopg2
from psycopg2.extras import execute_batch
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


# ============================================================================
# DATABASE CONNECTION
# ============================================================================

def get_db_connection():
    """Create PostgreSQL database connection."""
    conn = psycopg2.connect(
        host=os.getenv('POSTGRES_HOST', 'localhost'),
        port=int(os.getenv('POSTGRES_PORT', 5432)),
        user=os.getenv('POSTGRES_USER', 'stridematch'),
        password=os.getenv('POSTGRES_PASSWORD', ''),
        database=os.getenv('POSTGRES_DB', 'stridematch')
    )
    return conn


def get_brand_id(conn, brand_name: str) -> Optional[int]:
    """Get brand ID from database by brand name."""
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id FROM stridematch_brands WHERE LOWER(name) = LOWER(%s)",
            (brand_name,)
        )
        result = cur.fetchone()
        if result:
            return result[0]
        else:
            logger.warning(f"Brand '{brand_name}' not found in database. Skipping.")
            return None


def insert_sizing_data(conn, brand_id: int, sizing_data: List[Dict], dry_run: bool = False):
    """
    Insert sizing data into stridematch_sizing_normalization table.

    Args:
        conn: Database connection
        brand_id: Brand ID from stridematch_brands table
        sizing_data: List of sizing dictionaries
        dry_run: If True, only log data without inserting
    """
    if dry_run:
        logger.info(f"DRY RUN: Would insert {len(sizing_data)} sizing records for brand_id={brand_id}")
        for item in sizing_data[:5]:  # Show first 5 for preview
            logger.info(f"  Example: {item}")
        return

    insert_query = """
        INSERT INTO stridematch_sizing_normalization
        (brand_id, gender, size_eu, size_us, size_uk, size_cm)
        VALUES (%(brand_id)s, %(gender)s, %(size_eu)s, %(size_us)s, %(size_uk)s, %(size_cm)s)
        ON CONFLICT (brand_id, gender, size_cm) DO UPDATE
        SET size_eu = EXCLUDED.size_eu,
            size_us = EXCLUDED.size_us,
            size_uk = EXCLUDED.size_uk;
    """

    # Add brand_id to each record
    records = [{**item, 'brand_id': brand_id} for item in sizing_data]

    with conn.cursor() as cur:
        execute_batch(cur, insert_query, records)
        conn.commit()

    logger.info(f"✅ Inserted/Updated {len(sizing_data)} sizing records for brand_id={brand_id}")


# ============================================================================
# BRAND-SPECIFIC SCRAPING FUNCTIONS
# ============================================================================

def scrape_nike_sizing() -> List[Dict]:
    """
    Scrape Nike size guide.

    NOTE: This is a TEMPLATE. Nike's size guide page structure may change.
    You'll need to inspect the actual HTML and adjust selectors accordingly.

    Returns:
        List of sizing dictionaries with keys: gender, size_eu, size_us, size_uk, size_cm
    """
    logger.info("Scraping Nike size guide...")

    url = "https://www.nike.com/fr/size-fit/mens-footwear-sizing"  # Example URL (may change)
    sizing_data = []

    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        # EXAMPLE PARSING LOGIC (adjust based on actual HTML structure)
        # Look for sizing tables
        tables = soup.find_all('table', class_='size-table')  # Adjust selector

        for table in tables:
            # Determine gender from table context (adjust logic as needed)
            gender = 'male'  # Default, or extract from table headers

            rows = table.find_all('tr')[1:]  # Skip header row

            for row in rows:
                cols = row.find_all('td')
                if len(cols) >= 4:
                    size_eu = cols[0].text.strip()
                    size_us = cols[1].text.strip()
                    size_uk = cols[2].text.strip()
                    size_cm_text = cols[3].text.strip()

                    # Parse size_cm (remove "cm" suffix if present)
                    try:
                        size_cm = float(size_cm_text.replace('cm', '').replace(',', '.').strip())
                    except ValueError:
                        logger.warning(f"Could not parse size_cm: {size_cm_text}")
                        continue

                    sizing_data.append({
                        'gender': gender,
                        'size_eu': size_eu,
                        'size_us': size_us,
                        'size_uk': size_uk,
                        'size_cm': size_cm
                    })

        logger.info(f"✅ Scraped {len(sizing_data)} Nike sizing records")
        return sizing_data

    except Exception as e:
        logger.error(f"❌ Failed to scrape Nike sizing: {e}")
        return []


def scrape_adidas_sizing() -> List[Dict]:
    """
    Scrape Adidas size guide.

    NOTE: This is a TEMPLATE. Adidas may require Selenium due to JavaScript.
    """
    logger.info("Scraping Adidas size guide...")

    url = "https://www.adidas.fr/help/size_charts"  # Example URL
    sizing_data = []

    # OPTION 1: Try with requests first
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        # Parse tables (adjust selectors as needed)
        # Similar logic to Nike scraping...

        # If no tables found, try Selenium (OPTION 2)
        if not sizing_data:
            logger.info("No tables found with requests, trying Selenium...")
            sizing_data = scrape_with_selenium(url, brand='adidas')

        logger.info(f"✅ Scraped {len(sizing_data)} Adidas sizing records")
        return sizing_data

    except Exception as e:
        logger.error(f"❌ Failed to scrape Adidas sizing: {e}")
        return []


def scrape_asics_sizing() -> List[Dict]:
    """Scrape Asics size guide."""
    logger.info("Scraping Asics size guide...")
    url = "https://www.asics.com/fr/fr-fr/size-chart"
    # Similar implementation to Nike...
    logger.warning("Asics scraping not yet implemented (template)")
    return []


def scrape_hoka_sizing() -> List[Dict]:
    """Scrape Hoka size guide."""
    logger.info("Scraping Hoka size guide...")
    url = "https://www.hoka.com/fr/fr/size-guide.html"
    # Similar implementation to Nike...
    logger.warning("Hoka scraping not yet implemented (template)")
    return []


def scrape_brooks_sizing() -> List[Dict]:
    """Scrape Brooks size guide."""
    logger.info("Scraping Brooks size guide...")
    url = "https://www.brooksrunning.com/fr_fr/size-chart"
    # Similar implementation to Nike...
    logger.warning("Brooks scraping not yet implemented (template)")
    return []


def scrape_with_selenium(url: str, brand: str) -> List[Dict]:
    """
    Scrape sizing table using Selenium (for JavaScript-heavy pages).

    Args:
        url: URL of size guide page
        brand: Brand name (for logging)

    Returns:
        List of sizing dictionaries
    """
    logger.info(f"Using Selenium to scrape {brand} sizing...")
    sizing_data = []

    # Configure Selenium with headless Chrome
    chrome_options = ChromeOptions()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')

    driver = None
    try:
        driver = webdriver.Chrome(options=chrome_options)
        driver.get(url)

        # Wait for table to load (adjust selector as needed)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "table"))
        )

        # Parse page source with BeautifulSoup
        soup = BeautifulSoup(driver.page_source, 'html.parser')

        # Find and parse sizing tables
        tables = soup.find_all('table')

        for table in tables:
            # Parse rows (similar to requests-based scraping)
            # ...
            pass

        logger.info(f"✅ Scraped {len(sizing_data)} records with Selenium")
        return sizing_data

    except Exception as e:
        logger.error(f"❌ Selenium scraping failed: {e}")
        return []

    finally:
        if driver:
            driver.quit()


# ============================================================================
# BRAND SCRAPER REGISTRY
# ============================================================================

BRAND_SCRAPERS = {
    'nike': scrape_nike_sizing,
    'adidas': scrape_adidas_sizing,
    'asics': scrape_asics_sizing,
    'hoka': scrape_hoka_sizing,
    'brooks': scrape_brooks_sizing,
}


# ============================================================================
# MAIN SCRAPING LOGIC
# ============================================================================

def scrape_brand_sizing(brand_name: str, dry_run: bool = False) -> bool:
    """
    Scrape sizing data for a specific brand and insert into database.

    Args:
        brand_name: Brand name (e.g., 'nike', 'adidas')
        dry_run: If True, scrape but don't insert data

    Returns:
        True if successful, False otherwise
    """
    brand_name_lower = brand_name.lower()

    # Check if scraper exists
    if brand_name_lower not in BRAND_SCRAPERS:
        logger.error(f"No scraper defined for brand '{brand_name}'")
        logger.info(f"Available brands: {', '.join(BRAND_SCRAPERS.keys())}")
        return False

    # Get scraper function
    scraper_func = BRAND_SCRAPERS[brand_name_lower]

    # Scrape sizing data
    logger.info(f"Starting scraping for brand: {brand_name}")
    sizing_data = scraper_func()

    if not sizing_data:
        logger.warning(f"No sizing data scraped for {brand_name}")
        return False

    # Get database connection
    conn = get_db_connection()

    try:
        # Get brand ID
        brand_id = get_brand_id(conn, brand_name)
        if not brand_id:
            logger.error(f"Brand '{brand_name}' not found in database")
            return False

        # Insert data
        insert_sizing_data(conn, brand_id, sizing_data, dry_run=dry_run)

        logger.info(f"✅ Successfully processed sizing data for {brand_name}")
        return True

    except Exception as e:
        logger.error(f"❌ Database error: {e}")
        return False

    finally:
        conn.close()


def scrape_all_brands(dry_run: bool = False):
    """Scrape sizing data for all supported brands."""
    logger.info(f"Starting scraping for ALL brands ({len(BRAND_SCRAPERS)} brands)")

    results = {}
    for brand_name in BRAND_SCRAPERS.keys():
        success = scrape_brand_sizing(brand_name, dry_run=dry_run)
        results[brand_name] = 'SUCCESS' if success else 'FAILED'

    # Print summary
    logger.info("=" * 60)
    logger.info("SCRAPING SUMMARY")
    logger.info("=" * 60)
    for brand, status in results.items():
        emoji = '✅' if status == 'SUCCESS' else '❌'
        logger.info(f"{emoji} {brand.capitalize()}: {status}")
    logger.info("=" * 60)


# ============================================================================
# CLI INTERFACE
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='StrideMatch Sizing Scraper - Scrape brand size conversion tables'
    )

    parser.add_argument(
        '--brand',
        type=str,
        default='all',
        help=f'Brand to scrape (options: {", ".join(BRAND_SCRAPERS.keys())}, all)'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Scrape data but do not insert into database (preview mode)'
    )

    args = parser.parse_args()

    logger.info("=" * 60)
    logger.info("StrideMatch Sizing Scraper - Phase 2")
    logger.info("=" * 60)

    if args.dry_run:
        logger.info("🔍 DRY RUN MODE: Data will not be inserted into database")

    if args.brand.lower() == 'all':
        scrape_all_brands(dry_run=args.dry_run)
    else:
        scrape_brand_sizing(args.brand, dry_run=args.dry_run)


if __name__ == '__main__':
    main()


# ============================================================================
# IMPLEMENTATION NOTES
# ============================================================================

"""
IMPORTANT: This script is a TEMPLATE.

The scraping functions (scrape_nike_sizing, scrape_adidas_sizing, etc.) contain
placeholder logic and will need to be implemented by:

1. Inspecting the actual HTML structure of each brand's size guide page
2. Identifying the correct CSS selectors or XPath expressions
3. Extracting the size conversion data (EU, US, UK, CM)
4. Handling edge cases (JavaScript rendering, CAPTCHA, rate limiting)

TESTING WORKFLOW:

1. Test with --dry-run first:
   python scrape_sizing.py --brand nike --dry-run

2. Verify scraped data looks correct in logs

3. Run actual insert:
   python scrape_sizing.py --brand nike

4. Check database:
   psql -d stridematch -c "SELECT * FROM stridematch_sizing_normalization WHERE brand_id = (SELECT id FROM stridematch_brands WHERE name = 'Nike') LIMIT 10;"

ETHICAL CONSIDERATIONS:

- Respect robots.txt (checked automatically by requests library)
- Use appropriate delays between requests (DOWNLOAD_DELAY in settings.py)
- Identify your bot with proper USER_AGENT
- Only scrape publicly available size data (no personal data, no pricing)
- Comply with brand Terms of Service
- Consider contacting brands for official sizing data API access

ALTERNATIVE APPROACH:

Instead of scraping, consider:
1. Using official brand APIs (if available)
2. Purchasing sizing data from third-party providers
3. Manually entering data from PDF size guides (one-time effort)
4. Community-sourced sizing database (Reddit, RunRepeat forums)
"""
