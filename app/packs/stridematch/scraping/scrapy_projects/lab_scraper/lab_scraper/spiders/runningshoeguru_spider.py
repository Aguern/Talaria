"""
RunningShoesGuru Spider - Phase 3

Scrapes lab test data from RunningShoesGuru.com including:
- Weight (weight_g)
- Median lifespan (median_lifespan_km)
- Midsole material
- Outsole material
- Upper material

URL Structure:
- Listing: https://www.runningshoeguru.com/running-shoes/
- Product: https://www.runningshoeguru.com/[brand]/[model]/
"""

import scrapy
import re
from datetime import datetime
from lab_scraper.items import LabDataItem


class RunningShoesGuruSpider(scrapy.Spider):
    """Spider for scraping RunningShoesGuru.com lab data"""

    name = 'runningshoeguru'
    allowed_domains = ['runningshoeguru.com', 'www.runningshoeguru.com']

    # Start URLs - main listing page
    start_urls = [
        'https://www.runningshoeguru.com/running-shoes/',
    ]

    custom_settings = {
        'DOWNLOAD_DELAY': 4,
    }

    def __init__(self, brand=None, *args, **kwargs):
        """
        Initialize spider with optional brand filter.

        Args:
            brand: Optional brand name to filter (e.g., "nike")
        """
        super().__init__(*args, **kwargs)
        self.brand_filter = brand.lower() if brand else None

    def parse(self, response):
        """
        Parse listing page and extract product URLs.

        This method needs to be adapted based on RunningShoesGuru's actual HTML structure.
        """
        self.logger.info(f"📄 Parsing listing page: {response.url}")

        # TEMPLATE: Adjust selectors based on actual HTML structure
        # RunningShoesGuru may organize shoes by brand pages
        product_links = response.css('.shoe-listing a::attr(href)').getall()

        if not product_links:
            # Alternative selector patterns
            product_links = response.css('a[href*="/running-shoes/"]::attr(href)').getall()
            product_links = [link for link in product_links if self._is_product_url(link)]

        self.logger.info(f"Found {len(product_links)} product links")

        for link in product_links:
            full_url = response.urljoin(link)

            # Apply brand filter if specified
            if self.brand_filter and self.brand_filter not in full_url.lower():
                continue

            yield scrapy.Request(
                full_url,
                callback=self.parse_product,
                meta={'page_url': full_url}
            )

        # Handle pagination
        next_page = response.css('a.next::attr(href)').get()
        if next_page:
            yield response.follow(next_page, callback=self.parse)

    def parse_product(self, response):
        """
        Parse product page and extract lab data.

        This is a TEMPLATE - selectors must be adapted to RunningShoesGuru's HTML structure.
        """
        self.logger.info(f"🔬 Parsing product page: {response.url}")

        item = LabDataItem()

        # Extract brand and model
        # Method 1: From page title
        title = response.css('h1.product-title::text').get()
        if title:
            brand, model = self._parse_title(title)
        else:
            # Method 2: From URL
            brand, model = self._parse_url(response.url)

        item['brand_name'] = brand
        item['model_name'] = model

        # Extract gender
        gender_text = response.css('.gender-category::text').get()
        item['gender'] = self._extract_gender(gender_text or response.url)

        # === Lab Data Extraction ===
        # IMPORTANT: These selectors are TEMPLATES

        # Weight (usually in grams for men's size 9 US)
        weight_text = response.xpath(
            '//tr[contains(., "Weight")]/td[@class="spec-value"]/text() | '
            '//div[contains(@class, "spec")][contains(., "Weight")]/span[@class="value"]/text()'
        ).get()
        item['weight_g'] = self._extract_weight(weight_text)

        # Median lifespan (durability in km)
        lifespan_text = response.xpath(
            '//tr[contains(., "Durability") or contains(., "Lifespan")]/td[@class="spec-value"]/text() | '
            '//div[contains(., "Expected Lifespan")]/span[@class="value"]/text()'
        ).get()
        item['median_lifespan_km'] = self._extract_lifespan(lifespan_text)

        # Midsole material
        midsole_text = response.xpath(
            '//tr[contains(., "Midsole")]/td[@class="spec-value"]/text() | '
            '//div[contains(., "Midsole")]/span[@class="value"]/text()'
        ).get()
        item['midsole_material'] = self._clean_text(midsole_text)

        # Outsole material
        outsole_text = response.xpath(
            '//tr[contains(., "Outsole")]/td[@class="spec-value"]/text() | '
            '//div[contains(., "Outsole")]/span[@class="value"]/text()'
        ).get()
        item['outsole_material'] = self._clean_text(outsole_text)

        # Upper material
        upper_text = response.xpath(
            '//tr[contains(., "Upper")]/td[@class="spec-value"]/text() | '
            '//div[contains(., "Upper")]/span[@class="value"]/text()'
        ).get()
        item['upper_material'] = self._clean_text(upper_text)

        # Drop (if available)
        drop_text = response.xpath(
            '//tr[contains(., "Drop") or contains(., "Heel-Toe")]/td[@class="spec-value"]/text()'
        ).get()
        item['drop_mm'] = self._extract_numeric(drop_text)

        # Stack heights (if available)
        stack_heel = response.xpath(
            '//tr[contains(., "Heel Stack")]/td[@class="spec-value"]/text()'
        ).get()
        item['stack_heel_mm'] = self._extract_numeric(stack_heel)

        stack_forefoot = response.xpath(
            '//tr[contains(., "Forefoot Stack")]/td[@class="spec-value"]/text()'
        ).get()
        item['stack_forefoot_mm'] = self._extract_numeric(stack_forefoot)

        # Metadata
        item['source'] = 'runningshoeguru'
        item['source_url'] = response.url
        item['scrape_date'] = datetime.utcnow().isoformat()

        # Only yield if we have meaningful data
        if any([
            item.get('weight_g'),
            item.get('median_lifespan_km'),
            item.get('midsole_material'),
            item.get('drop_mm')
        ]):
            self.logger.info(f"✅ Extracted data: {brand} {model}")
            yield item
        else:
            self.logger.warning(f"⚠️  No data found for: {brand} {model}")

    def _is_product_url(self, url):
        """Check if URL is a product page (not category/listing)"""
        # Product URLs typically have more path segments
        path_segments = url.strip('/').split('/')
        return len(path_segments) >= 3 and 'category' not in url and 'page' not in url

    def _parse_title(self, title):
        """
        Parse brand and model from page title.

        Args:
            title: Page title (e.g., "Nike Pegasus 41 Review")

        Returns:
            Tuple of (brand, model)
        """
        # Remove common suffixes
        title = re.sub(r'\s+(Review|Test|Analysis).*$', '', title, flags=re.IGNORECASE)

        parts = title.split()
        if len(parts) >= 2:
            brand = parts[0]
            model = ' '.join(parts[1:])
            return brand, model

        return title, ''

    def _parse_url(self, url):
        """
        Parse brand and model from URL.

        Args:
            url: Product URL (e.g., "https://www.runningshoeguru.com/nike/pegasus-41/")

        Returns:
            Tuple of (brand, model)
        """
        path = url.rstrip('/').split('/')

        if len(path) >= 2:
            brand = path[-2].replace('-', ' ').title()
            model = path[-1].replace('-', ' ').title()
            return brand, model

        return 'Unknown', 'Unknown'

    def _extract_gender(self, text):
        """Extract gender from text or URL"""
        if not text:
            return 'unisex'

        text_lower = text.lower()
        if 'men' in text_lower or 'male' in text_lower:
            return 'male'
        elif 'women' in text_lower or 'female' in text_lower:
            return 'female'
        else:
            return 'unisex'

    def _extract_weight(self, text):
        """
        Extract weight in grams.

        Args:
            text: Weight string (e.g., "285g", "10.1 oz")

        Returns:
            Weight in grams or None
        """
        if not text:
            return None

        text = text.lower().strip()

        # If already in grams
        if 'g' in text and 'kg' not in text:
            match = re.search(r'(\d+\.?\d*)\s*g', text)
            if match:
                return float(match.group(1))

        # If in ounces, convert to grams (1 oz = 28.35g)
        if 'oz' in text:
            match = re.search(r'(\d+\.?\d*)\s*oz', text)
            if match:
                oz = float(match.group(1))
                return round(oz * 28.35, 1)

        # Try extracting any number
        return self._extract_numeric(text)

    def _extract_lifespan(self, text):
        """
        Extract lifespan in kilometers.

        Args:
            text: Lifespan string (e.g., "600-800 km", "400 miles")

        Returns:
            Median lifespan in km or None
        """
        if not text:
            return None

        text = text.lower().strip()

        # If in miles, convert to km (1 mile = 1.60934 km)
        if 'mile' in text or 'mi' in text:
            match = re.search(r'(\d+)', text)
            if match:
                miles = float(match.group(1))
                return round(miles * 1.60934, 0)

        # If range (e.g., "600-800 km"), take median
        range_match = re.search(r'(\d+)\s*-\s*(\d+)', text)
        if range_match:
            low = float(range_match.group(1))
            high = float(range_match.group(2))
            return round((low + high) / 2, 0)

        # Single number
        return self._extract_numeric(text)

    def _extract_numeric(self, text):
        """Extract numeric value from text"""
        if not text:
            return None

        try:
            match = re.search(r'[-+]?\d*\.?\d+', str(text))
            if match:
                return float(match.group())
        except (ValueError, AttributeError):
            pass

        return None

    def _clean_text(self, text):
        """Clean and normalize text fields"""
        if not text:
            return None

        # Remove extra whitespace
        text = ' '.join(text.split())
        # Remove special characters but keep hyphens
        text = re.sub(r'[^\w\s-]', '', text)

        return text.strip() or None
