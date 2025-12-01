"""
Alltricks.fr Spider - Phase 4

Scrapes running shoe products from alltricks.fr using JSON-LD structured data.

Alltricks.fr is a major French outdoor/running e-commerce site.

URL Structure:
- Listing: https://www.alltricks.fr/C-41419-chaussures_running
- Product: https://www.alltricks.fr/F-11949-chaussures_running/P-[product-id]-[product-slug]
"""

import scrapy
from datetime import datetime
from ecommerce_scraper.items import ProductItem
from ecommerce_scraper.jsonld_parser import extract_product_data


class AlltricksSpider(scrapy.Spider):
    """Spider for scraping alltricks.fr product catalog"""

    name = 'alltricks'
    allowed_domains = ['alltricks.fr', 'www.alltricks.fr']

    # Start URLs - main category pages
    start_urls = [
        # Running shoes main category
        'https://www.alltricks.fr/C-41419-chaussures_running',

        # Trail running shoes
        'https://www.alltricks.fr/C-41418-chaussures_trail',
    ]

    custom_settings = {
        'DOWNLOAD_DELAY': 3,
    }

    def __init__(self, brand=None, category=None, *args, **kwargs):
        """
        Initialize spider with optional filters.

        Args:
            brand: Optional brand slug to filter (e.g., "nike")
            category: Optional category to scrape (e.g., "running", "trail")
        """
        super().__init__(*args, **kwargs)

        # Apply filters if provided
        if category:
            category_urls = {
                'running': 'https://www.alltricks.fr/C-41419-chaussures_running',
                'trail': 'https://www.alltricks.fr/C-41418-chaussures_trail',
            }
            if category in category_urls:
                self.start_urls = [category_urls[category]]

        self.brand_filter = brand.lower() if brand else None

    def parse(self, response):
        """
        Parse listing page and extract product URLs.

        This method needs to be adapted based on alltricks.fr's actual HTML structure.
        """
        self.logger.info(f"📄 Parsing listing page: {response.url}")

        # TEMPLATE: Adjust selectors based on actual HTML structure
        # Alltricks likely uses a product grid

        product_links = response.css('.product-item a::attr(href)').getall()

        if not product_links:
            # Alternative selector patterns
            product_links = response.css('.product-card a::attr(href)').getall()

        if not product_links:
            # Alltricks might use specific URL pattern
            product_links = response.css('a[href*="/P-"]::attr(href)').getall()

        # Deduplicate links
        product_links = list(set(product_links))

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
        # Alltricks might use numbered pagination or infinite scroll
        next_page = response.css('a.pagination-next::attr(href)').get()

        if not next_page:
            # Alternative pagination selector
            next_page = response.css('link[rel="next"]::attr(href)').get()

        if not next_page:
            # Try numbered pagination
            current_page = response.url
            # Check if there's a page parameter
            if 'page=' in current_page:
                import re
                match = re.search(r'page=(\d+)', current_page)
                if match:
                    page_num = int(match.group(1))
                    next_page = re.sub(r'page=\d+', f'page={page_num + 1}', current_page)
            else:
                # First pagination
                separator = '&' if '?' in current_page else '?'
                next_page = f"{current_page}{separator}page=2"

            # Verify next page exists
            # (Scrapy will handle 404s automatically)

        if next_page:
            yield response.follow(next_page, callback=self.parse)

    def parse_product(self, response):
        """
        Parse product page and extract data using JSON-LD.

        Modern e-commerce sites embed structured data in JSON-LD format.
        """
        self.logger.info(f"🛒 Parsing product page: {response.url}")

        # Extract product data from JSON-LD
        product_data = extract_product_data(response)

        if not product_data:
            self.logger.warning(f"⚠️  No JSON-LD data found on {response.url}")
            # Fallback to manual extraction if needed
            product_data = self._fallback_extraction(response)

        if not product_data:
            self.logger.error(f"❌ Failed to extract product data from {response.url}")
            return

        # Create ProductItem
        item = ProductItem()

        # Basic product info
        item['brand_name'] = product_data.get('brand_name', '')
        item['model_name'] = product_data.get('model_name', '')
        item['full_name'] = product_data.get('full_name', '')

        # Variants (colors, sizes, prices)
        item['variants'] = product_data.get('offers', [])

        # Metadata
        item['source'] = 'alltricks'
        item['source_url'] = response.url
        item['scrape_date'] = datetime.utcnow().isoformat()

        # Description (for classification)
        item['description'] = product_data.get('description', '')

        # Extract additional info from HTML if needed
        self._enrich_from_html(item, response)

        # Validate item
        if not item['brand_name'] or not item['full_name']:
            self.logger.warning(f"⚠️  Missing brand or name: {response.url}")
            return

        self.logger.info(f"✅ Extracted: {item['brand_name']} {item['model_name']}")
        yield item

    def _fallback_extraction(self, response):
        """
        Fallback extraction if JSON-LD is not available.

        This method manually extracts data from HTML using CSS/XPath selectors.
        """
        self.logger.info("🔄 Attempting fallback extraction...")

        # Try to extract product name
        product_name = response.css('h1.product-name::text, h1::text').get()

        if not product_name:
            return None

        product_name = product_name.strip()

        # Try to extract brand
        brand = response.css('.product-brand::text, meta[property="product:brand"]::attr(content)').get()

        if not brand:
            # Extract from product name (first word is often the brand)
            brand = product_name.split()[0]

        # Try to extract price
        price_text = response.css('.price::text, .product-price::text').get()
        price = self._parse_price(price_text) if price_text else None

        # Try to extract description
        description = response.css('.product-description::text').get()
        if not description:
            description = response.css('meta[name="description"]::attr(content)').get()

        # Create minimal offer
        offers = []
        if price:
            offers.append({
                'price': price,
                'currency': 'EUR',
                'availability': 'InStock',
                'url': response.url,
                'sku': '',
                'color': 'Standard',
                'size': 'Standard',
            })

        return {
            'full_name': product_name,
            'brand_name': brand,
            'model_name': product_name.replace(brand, '').strip(),
            'description': description or '',
            'offers': offers,
        }

    def _enrich_from_html(self, item, response):
        """
        Enrich item with additional data from HTML.

        Some information might not be in JSON-LD and needs to be scraped from HTML.
        """
        # Try to extract more detailed description
        if not item.get('description'):
            description = response.css('.product-description::text').get()
            if description:
                item['description'] = description.strip()

        # Try to extract technical specifications
        tech_specs = response.css('.tech-specs li::text').getall()
        if tech_specs:
            item['description'] = (item.get('description', '') + ' ' + ' '.join(tech_specs)).strip()

    def _parse_price(self, price_text):
        """Parse price from text"""
        import re
        if not price_text:
            return None

        # Remove currency symbols and extract number
        price_clean = price_text.replace('€', '').replace(',', '.').strip()
        match = re.search(r'\d+\.?\d*', price_clean)

        if match:
            return float(match.group())

        return None
