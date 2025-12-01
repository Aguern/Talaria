"""
i-Run.fr Spider - Phase 4

Scrapes running shoe products from i-run.fr using JSON-LD structured data.

i-run.fr is a major French running e-commerce site with extensive product catalog.

URL Structure:
- Listing: https://www.i-run.fr/chaussures-running-route-homme/
- Product: https://www.i-run.fr/nike-pegasus-41-m/

Uses Playwright to bypass anti-bot detection.
"""

import scrapy
from datetime import datetime
from ecommerce_scraper.items import ProductItem
from ecommerce_scraper.jsonld_parser import extract_product_data


class IrunSpider(scrapy.Spider):
    """Spider for scraping i-run.fr product catalog using Playwright"""

    name = 'irun'
    allowed_domains = ['i-run.fr', 'www.i-run.fr']

    # Start URLs - main category pages
    start_urls = [
        # Men's road running shoes
        'https://www.i-run.fr/chaussures-running-route-homme/',

        # Women's road running shoes
        'https://www.i-run.fr/chaussures-running-route-femme/',

        # Men's trail running shoes
        'https://www.i-run.fr/chaussures-running-trail-homme/',

        # Women's trail running shoes
        'https://www.i-run.fr/chaussures-running-trail-femme/',
    ]

    custom_settings = {
        'DOWNLOAD_DELAY': 3,

        # Enable Playwright for HTTP/HTTPS requests
        'DOWNLOAD_HANDLERS': {
            "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
            "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
        },

        # Playwright browser configuration
        'PLAYWRIGHT_BROWSER_TYPE': 'chromium',
        'PLAYWRIGHT_LAUNCH_OPTIONS': {
            'headless': True,  # Run in headless mode
            'args': [
                '--disable-blink-features=AutomationControlled',  # Hide automation
            ],
        },

        # Respect robots.txt
        'ROBOTSTXT_OBEY': True,
    }

    def __init__(self, brand=None, category=None, *args, **kwargs):
        """
        Initialize spider with optional filters.

        Args:
            brand: Optional brand slug to filter (e.g., "nike")
            category: Optional category to scrape (e.g., "road-men")
        """
        super().__init__(*args, **kwargs)

        # Apply filters if provided
        if category:
            category_urls = {
                'road-men': 'https://www.i-run.fr/chaussures-running-route-homme/',
                'road-women': 'https://www.i-run.fr/chaussures-running-route-femme/',
                'trail-men': 'https://www.i-run.fr/chaussures-running-trail-homme/',
                'trail-women': 'https://www.i-run.fr/chaussures-running-trail-femme/',
            }
            if category in category_urls:
                self.start_urls = [category_urls[category]]

        self.brand_filter = brand.lower() if brand else None

    def start_requests(self):
        """
        Generate initial requests with Playwright enabled.
        """
        for url in self.start_urls:
            yield scrapy.Request(
                url,
                callback=self.parse,
                meta={
                    'playwright': True,
                    'playwright_page_methods': [
                        # Wait for network to be idle (page fully loaded)
                        ('wait_for_load_state', 'networkidle'),
                    ],
                },
                errback=self.errback_playwright,
            )

    def errback_playwright(self, failure):
        """
        Handle Playwright errors gracefully.
        """
        self.logger.error(f"❌ Playwright request failed: {failure.request.url}")
        self.logger.error(f"Error: {failure.value}")

    def parse(self, response):
        """
        Parse listing page and extract product URLs.

        This method needs to be adapted based on i-run.fr's actual HTML structure.
        """
        self.logger.info(f"📄 Parsing listing page: {response.url}")

        # TEMPLATE: Adjust selectors based on actual HTML structure
        # i-run.fr likely uses a grid of product cards

        product_links = response.css('.product-item a::attr(href)').getall()

        if not product_links:
            # Alternative selector patterns
            product_links = response.css('.product-card a.product-link::attr(href)').getall()

        if not product_links:
            # Another common pattern
            product_links = response.css('a[href*="/chaussures-"]::attr(href)').getall()
            # Filter to only product pages (not category pages)
            product_links = [
                link for link in product_links
                if link.count('/') >= 2 and not any(x in link for x in ['categorie', 'marque'])
            ]

        self.logger.info(f"Found {len(product_links)} product links")

        for link in product_links:
            full_url = response.urljoin(link)

            # Apply brand filter if specified
            if self.brand_filter and self.brand_filter not in full_url.lower():
                continue

            yield scrapy.Request(
                full_url,
                callback=self.parse_product,
                meta={
                    'page_url': full_url,
                    'playwright': True,
                    'playwright_page_methods': [
                        ('wait_for_load_state', 'networkidle'),
                    ],
                },
                errback=self.errback_playwright,
            )

        # Handle pagination
        next_page = response.css('a.next-page::attr(href)').get()
        if not next_page:
            # Alternative pagination selector
            next_page = response.css('link[rel="next"]::attr(href)').get()

        if next_page:
            yield scrapy.Request(
                response.urljoin(next_page),
                callback=self.parse,
                meta={
                    'playwright': True,
                    'playwright_page_methods': [
                        ('wait_for_load_state', 'networkidle'),
                    ],
                },
                errback=self.errback_playwright,
            )

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
        item['source'] = 'irun'
        item['source_url'] = response.url
        item['scrape_date'] = datetime.utcnow().isoformat()

        # Description (for classification)
        item['description'] = product_data.get('description', '')

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
        product_name = response.css('h1.product-title::text').get()
        if not product_name:
            product_name = response.css('h1::text').get()

        if not product_name:
            return None

        # Try to extract brand (usually first word or specific meta tag)
        brand = response.css('meta[property="product:brand"]::attr(content)').get()
        if not brand:
            # Extract from product name
            brand = product_name.split()[0]

        # Try to extract price
        price_text = response.css('.price::text, .product-price::text').get()
        price = self._parse_price(price_text) if price_text else None

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
            'full_name': product_name.strip(),
            'brand_name': brand,
            'model_name': product_name.replace(brand, '').strip(),
            'description': '',
            'offers': offers,
        }

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
