"""
Scrapy Settings - E-commerce Scraper

Ethical scraping configuration for i-run.fr and alltricks.fr.
"""

# Scrapy project settings
BOT_NAME = 'ecommerce_scraper'
SPIDER_MODULES = ['ecommerce_scraper.spiders']
NEWSPIDER_MODULE = 'ecommerce_scraper.spiders'

# User-Agent (identify ourselves)
USER_AGENT = 'StrideMatch-EcomBot/1.0 (+https://stridematch.com/bot; contact@stridematch.com)'

# Obey robots.txt rules
ROBOTSTXT_OBEY = True

# Configure maximum concurrent requests (be polite)
CONCURRENT_REQUESTS = 8
CONCURRENT_REQUESTS_PER_DOMAIN = 2
CONCURRENT_REQUESTS_PER_IP = 0

# Configure a delay for requests (in seconds)
# Critical for ethical scraping
DOWNLOAD_DELAY = 3
RANDOMIZE_DOWNLOAD_DELAY = True

# Disable cookies (unless needed for authentication)
COOKIES_ENABLED = True  # Enable for e-commerce sites (session tracking)

# Disable Telemetry
TELNETCONSOLE_ENABLED = False

# Override the default request headers
DEFAULT_REQUEST_HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'fr-FR,fr;q=0.9,en;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
}

# Enable or disable spider middlewares
SPIDER_MIDDLEWARES = {
    'ecommerce_scraper.middlewares.EcommerceScraperSpiderMiddleware': 543,
}

# Enable or disable downloader middlewares
DOWNLOADER_MIDDLEWARES = {
    'ecommerce_scraper.middlewares.EcommerceScraperDownloaderMiddleware': 543,
}

# Configure item pipelines
ITEM_PIPELINES = {
    'ecommerce_scraper.pipelines.ValidationPipeline': 100,
    'ecommerce_scraper.pipelines.CategoryClassificationPipeline': 200,
    'ecommerce_scraper.pipelines.PostgreSQLPipeline': 300,
}

# Enable AutoThrottle extension (automatically adjust delays)
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 3
AUTOTHROTTLE_MAX_DELAY = 10
AUTOTHROTTLE_TARGET_CONCURRENCY = 2.0
AUTOTHROTTLE_DEBUG = False

# Enable and configure HTTP caching (reduces server load)
HTTPCACHE_ENABLED = True
HTTPCACHE_EXPIRATION_SECS = 86400  # 24 hours
HTTPCACHE_DIR = 'httpcache'
HTTPCACHE_IGNORE_HTTP_CODES = [500, 502, 503, 504, 408, 429]
HTTPCACHE_STORAGE = 'scrapy.extensions.httpcache.FilesystemCacheStorage'

# Retry settings
RETRY_ENABLED = True
RETRY_TIMES = 3
RETRY_HTTP_CODES = [500, 502, 503, 504, 408, 429]

# Timeout settings
DOWNLOAD_TIMEOUT = 30

# Database configuration (loaded from environment)
import os
POSTGRES_HOST = os.getenv('POSTGRES_HOST', 'localhost')
POSTGRES_PORT = int(os.getenv('POSTGRES_PORT', 5432))
POSTGRES_DB = os.getenv('POSTGRES_DB', 'saas_nr_db')
POSTGRES_USER = os.getenv('POSTGRES_USER', 'user')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD', 'password')

# Logging
LOG_LEVEL = 'INFO'
LOG_FORMAT = '%(asctime)s [%(name)s] %(levelname)s: %(message)s'
LOG_DATEFORMAT = '%Y-%m-%d %H:%M:%S'

# Set settings whose default value is deprecated to a future-proof value
REQUEST_FINGERPRINTER_IMPLEMENTATION = '2.7'
TWISTED_REACTOR = 'twisted.internet.asyncioreactor.AsyncioSelectorReactor'
FEED_EXPORT_ENCODING = 'utf-8'
