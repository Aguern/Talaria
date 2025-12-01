"""
Scrapy Settings for StrideMatch - Ethical Web Scraping Configuration

This configuration file implements best practices for responsible web scraping,
respecting robots.txt, rate limiting, and server resources.

Compliance: CNIL (France), GDPR, and general web scraping ethics.
"""

# ============================================================================
# BOT IDENTIFICATION & TRANSPARENCY
# ============================================================================

BOT_NAME = 'stridematch_scraper'

# User-Agent: Transparent identification of our bot
# Format recommandé: 'BotName/Version (+URL with contact info)'
USER_AGENT = 'StrideMatch-Bot/1.0 (+https://stridematch.com/bot; contact@stridematch.com)'

# Respect robots.txt directives (CRITICAL for legal compliance)
ROBOTSTXT_OBEY = True

# ============================================================================
# RATE LIMITING & SERVER COURTESY (Anti-DDoS, Anti-Ban)
# ============================================================================

# Download delay: 3 seconds between requests to the same domain
# This prevents server overload and reduces risk of IP blocking
DOWNLOAD_DELAY = 3

# Randomize delay to simulate human behavior (between 0.5*DELAY and 1.5*DELAY)
RANDOMIZE_DOWNLOAD_DELAY = True

# Concurrent requests settings
CONCURRENT_REQUESTS = 8  # Max concurrent requests across all domains
CONCURRENT_REQUESTS_PER_DOMAIN = 2  # Max concurrent requests per domain
CONCURRENT_REQUESTS_PER_IP = 2  # Max concurrent requests per IP

# Auto-throttle: Dynamic adjustment based on server response time
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 3  # Initial download delay
AUTOTHROTTLE_MAX_DELAY = 10  # Maximum delay in case of high latency
AUTOTHROTTLE_TARGET_CONCURRENCY = 1.5  # Target concurrency level
AUTOTHROTTLE_DEBUG = False  # Enable to see throttling stats

# ============================================================================
# RETRY & ERROR HANDLING
# ============================================================================

# Retry settings
RETRY_ENABLED = True
RETRY_TIMES = 3  # Number of retries for failed requests
RETRY_HTTP_CODES = [500, 502, 503, 504, 408, 429]  # HTTP codes to retry

# Timeout settings
DOWNLOAD_TIMEOUT = 30  # Request timeout in seconds

# ============================================================================
# SPIDER MIDDLEWARES & EXTENSIONS
# ============================================================================

SPIDER_MODULES = ['stridematch_scraper.spiders']
NEWSPIDER_MODULE = 'stridematch_scraper.spiders'

# Downloader Middlewares
DOWNLOADER_MIDDLEWARES = {
    'scrapy.downloadermiddlewares.robotstxt.RobotsTxtMiddleware': 100,
    'scrapy.downloadermiddlewares.httpauth.HttpAuthMiddleware': 300,
    'scrapy.downloadermiddlewares.downloadtimeout.DownloadTimeoutMiddleware': 350,
    'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': 400,
    'scrapy.downloadermiddlewares.retry.RetryMiddleware': 500,
    'scrapy.downloadermiddlewares.redirect.RedirectMiddleware': 600,
    'scrapy.downloadermiddlewares.cookies.CookiesMiddleware': 700,
    'scrapy.downloadermiddlewares.httpcompression.HttpCompressionMiddleware': 810,
}

# Item Pipelines (pour sauvegarder les données scrapées)
ITEM_PIPELINES = {
    # Will be populated in Phase 3-4 with custom pipelines
}

# ============================================================================
# CACHE & PERSISTENCE (Development/Debug)
# ============================================================================

# HTTP Cache (useful for development to avoid re-scraping)
HTTPCACHE_ENABLED = False  # Enable in development mode
HTTPCACHE_EXPIRATION_SECS = 86400  # 24 hours
HTTPCACHE_DIR = 'httpcache'
HTTPCACHE_IGNORE_HTTP_CODES = [500, 502, 503, 504]

# ============================================================================
# LOGGING
# ============================================================================

LOG_LEVEL = 'INFO'  # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FORMAT = '%(asctime)s [%(name)s] %(levelname)s: %(message)s'
LOG_DATEFORMAT = '%Y-%m-%d %H:%M:%S'

# ============================================================================
# COOKIES & HEADERS
# ============================================================================

# Accept cookies (some sites require this)
COOKIES_ENABLED = True

# Default request headers (simulate real browser)
DEFAULT_REQUEST_HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
    'Accept-Encoding': 'gzip, deflate, br',
    'DNT': '1',  # Do Not Track
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
}

# ============================================================================
# SECURITY & PRIVACY
# ============================================================================

# Disable telemetry (respect user privacy)
TELNETCONSOLE_ENABLED = False

# Disable cookies debug (avoid logging sensitive data)
COOKIES_DEBUG = False

# ============================================================================
# CUSTOM SETTINGS (StrideMatch specific)
# ============================================================================

# Database connection settings (will be loaded from .env)
# These will be used in custom pipelines (Phase 3-4)
import os
from dotenv import load_dotenv

load_dotenv()

POSTGRES_HOST = os.getenv('POSTGRES_HOST', 'localhost')
POSTGRES_PORT = int(os.getenv('POSTGRES_PORT', 5432))
POSTGRES_USER = os.getenv('POSTGRES_USER', 'stridematch')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD', '')
POSTGRES_DB = os.getenv('POSTGRES_DB', 'stridematch')

MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://stridematch:stridematch_password@localhost:27017/')
MONGODB_DB = os.getenv('MONGO_DB', 'stridematch')

# ============================================================================
# NOTES FOR DEVELOPERS
# ============================================================================

# IMPORTANT REMINDERS:
# 1. Always test spiders on a small sample before full crawl
# 2. Monitor server response times and adjust DOWNLOAD_DELAY if needed
# 3. Check robots.txt of target sites before scraping
# 4. Keep USER_AGENT updated with current contact information
# 5. Never scrape personal data without consent (GDPR compliance)
# 6. Respect copyright: only scrape publicly available product specs
# 7. Consider using Scrapy Cloud or Scrapyd for production deployment

# Legal Disclaimer:
# This scraper is designed to collect publicly available product specifications
# for the purpose of providing a product recommendation service.
# It does not collect personal data, pricing information, or copyrighted content.
# Always verify that your scraping activities comply with the target site's
# Terms of Service and applicable laws (GDPR, CNIL, etc.).
