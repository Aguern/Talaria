"""
RunRepeat Spider - Phase 3

Scrapes lab test data from RunRepeat.com including:
- Heel-to-toe drop (drop_mm)
- Stack heights (heel and forefoot)
- Cushioning softness (Shore A hardness)
- Energy return percentage
- Flexibility and torsional rigidity indexes

URL Structure:
- Listing: https://runrepeat.com/running-shoes
- Product: https://runrepeat.com/nike-pegasus-41
"""

import scrapy
import re
from datetime import datetime
from lab_scraper.items import LabDataItem


class RunRepeatSpider(scrapy.Spider):
    """Spider for scraping RunRepeat.com lab data"""

    name = 'runrepeat'
    allowed_domains = ['runrepeat.com']

    # Start URLs - can be configured via command line
    # Example: scrapy crawl runrepeat -a brand=nike
    start_urls = [
        'https://runrepeat.com/running-shoes?brand=nike',
        'https://runrepeat.com/running-shoes?brand=adidas',
        'https://runrepeat.com/running-shoes?brand=hoka',
        'https://runrepeat.com/running-shoes?brand=asics',
        'https://runrepeat.com/running-shoes?brand=brooks',
        'https://runrepeat.com/running-shoes?brand=new-balance',
        'https://runrepeat.com/running-shoes?brand=saucony',
        'https://runrepeat.com/running-shoes?brand=mizuno',
        'https://runrepeat.com/running-shoes?brand=on',
        'https://runrepeat.com/running-shoes?brand=altra',
    ]

    custom_settings = {
        'DOWNLOAD_DELAY': 5,  # More conservative for RunRepeat
    }

    def __init__(self, brand=None, *args, **kwargs):
        """
        Initialize spider with optional brand filter.

        Args:
            brand: Optional brand slug to scrape only one brand
        """
        super().__init__(*args, **kwargs)
        if brand:
            self.start_urls = [f'https://runrepeat.com/running-shoes?brand={brand}']

    def parse(self, response):
        """
        Parse listing page and extract product URLs.

        This method needs to be adapted based on RunRepeat's actual HTML structure.
        """
        self.logger.info(f"📄 Parsing listing page: {response.url}")

        # TEMPLATE: Adjust selectors based on actual HTML structure
        # Example selectors (need verification):
        product_links = response.css('.product-card a::attr(href)').getall()

        if not product_links:
            # Alternative selector patterns
            product_links = response.css('a.shoe-link::attr(href)').getall()

        self.logger.info(f"Found {len(product_links)} product links")

        for link in product_links:
            full_url = response.urljoin(link)
            yield scrapy.Request(
                full_url,
                callback=self.parse_product,
                meta={'page_url': full_url}
            )

        # Handle pagination
        next_page = response.css('a.next-page::attr(href)').get()
        if next_page:
            yield response.follow(next_page, callback=self.parse)

    def parse_product(self, response):
        """
        Parse product page and extract lab data.

        This is a TEMPLATE - selectors must be adapted to RunRepeat's HTML structure.
        """
        self.logger.info(f"🔬 Parsing product page: {response.url}")

        item = LabDataItem()

        # Extract brand and model from URL or page
        # Example: https://runrepeat.com/nike-pegasus-41
        url_parts = response.url.rstrip('/').split('/')
        slug = url_parts[-1]  # "nike-pegasus-41"

        # Parse brand and model from slug
        brand, model = self._parse_slug(slug)
        item['brand_name'] = brand
        item['model_name'] = model

        # Extract gender (if available)
        gender_text = response.css('.gender-indicator::text').get()
        item['gender'] = self._extract_gender(gender_text)

        # === Lab Data Extraction ===
        # IMPORTANT: These selectors are TEMPLATES and must be adapted
        # based on RunRepeat's actual HTML structure

        # Drop (heel-to-toe)
        drop_text = response.xpath(
            '//div[contains(@class, "spec-item")][contains(., "Drop")]/span[@class="spec-value"]/text()'
        ).get()
        item['drop_mm'] = self._extract_numeric(drop_text)

        # Stack heights
        stack_heel_text = response.xpath(
            '//div[contains(@class, "spec-item")][contains(., "Heel Stack")]/span[@class="spec-value"]/text()'
        ).get()
        item['stack_heel_mm'] = self._extract_numeric(stack_heel_text)

        stack_forefoot_text = response.xpath(
            '//div[contains(@class, "spec-item")][contains(., "Forefoot Stack")]/span[@class="spec-value"]/text()'
        ).get()
        item['stack_forefoot_mm'] = self._extract_numeric(stack_forefoot_text)

        # Cushioning softness (Shore A hardness)
        cushioning_text = response.xpath(
            '//div[contains(@class, "lab-test")][contains(., "Cushioning")]/span[@class="value"]/text()'
        ).get()
        item['cushioning_softness_ha'] = self._extract_numeric(cushioning_text)

        # Energy return
        energy_text = response.xpath(
            '//div[contains(@class, "lab-test")][contains(., "Energy Return")]/span[@class="value"]/text()'
        ).get()
        item['energy_return_pct'] = self._extract_numeric(energy_text)

        # Flexibility index
        flex_text = response.xpath(
            '//div[contains(@class, "lab-test")][contains(., "Flexibility")]/span[@class="value"]/text()'
        ).get()
        item['flexibility_index'] = self._extract_numeric(flex_text)

        # Torsional rigidity
        torsion_text = response.xpath(
            '//div[contains(@class, "lab-test")][contains(., "Torsion")]/span[@class="value"]/text()'
        ).get()
        item['torsional_rigidity_index'] = self._extract_numeric(torsion_text)

        # Weight (if available)
        weight_text = response.xpath(
            '//div[contains(@class, "spec-item")][contains(., "Weight")]/span[@class="spec-value"]/text()'
        ).get()
        item['weight_g'] = self._extract_numeric(weight_text)

        # Metadata
        item['source'] = 'runrepeat'
        item['source_url'] = response.url
        item['scrape_date'] = datetime.utcnow().isoformat()

        # Only yield item if we have at least some lab data
        if any([
            item.get('drop_mm'),
            item.get('stack_heel_mm'),
            item.get('cushioning_softness_ha'),
            item.get('energy_return_pct')
        ]):
            self.logger.info(f"✅ Extracted lab data: {brand} {model}")
            yield item
        else:
            self.logger.warning(f"⚠️  No lab data found for: {brand} {model}")

    def _parse_slug(self, slug):
        """
        Parse brand and model from URL slug.

        Args:
            slug: URL slug (e.g., "nike-pegasus-41")

        Returns:
            Tuple of (brand, model)
        """
        parts = slug.split('-')

        # Brand is usually the first part
        brand = parts[0].capitalize()

        # Model is the rest
        model_parts = parts[1:]
        model = ' '.join(word.capitalize() for word in model_parts)

        return brand, model

    def _extract_gender(self, text):
        """Extract gender from text"""
        if not text:
            return 'unisex'

        text_lower = text.lower()
        if 'men' in text_lower or 'male' in text_lower:
            return 'male'
        elif 'women' in text_lower or 'female' in text_lower:
            return 'female'
        else:
            return 'unisex'

    def _extract_numeric(self, text):
        """
        Extract numeric value from text.

        Args:
            text: String containing a number (e.g., "10.5 mm", "75%")

        Returns:
            Float or None
        """
        if not text:
            return None

        # Remove common units and % signs
        text = text.replace('mm', '').replace('g', '').replace('%', '').strip()

        try:
            # Extract first number
            match = re.search(r'[-+]?\d*\.?\d+', text)
            if match:
                return float(match.group())
        except (ValueError, AttributeError):
            pass

        return None
