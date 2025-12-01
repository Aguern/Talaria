"""
Scrapy Middlewares - Lab Scraper

Custom middlewares for handling requests and responses.
"""

from scrapy import signals
from scrapy.http import Request


# Playwright stealth script (inline)
STEALTH_JS = """
// Overwrite the `navigator.webdriver` property
Object.defineProperty(navigator, 'webdriver', {
    get: () => undefined,
});

// Overwrite the `plugins` property
Object.defineProperty(navigator, 'plugins', {
    get: () => [1, 2, 3, 4, 5],
});

// Overwrite the `languages` property
Object.defineProperty(navigator, 'languages', {
    get: () => ['en-US', 'en'],
});

// Remove Playwright-specific properties
delete window.playwright;
delete window._playwrightInstance;

// Chrome runtime
window.chrome = {
    runtime: {},
};

// Permissions
const originalQuery = window.navigator.permissions.query;
window.navigator.permissions.query = (parameters) => (
    parameters.name === 'notifications' ?
        Promise.resolve({ state: Notification.permission }) :
        originalQuery(parameters)
);
"""


class LabScraperSpiderMiddleware:
    """Spider middleware for processing spider input/output"""

    @classmethod
    def from_crawler(cls, crawler):
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        """Called for each response that goes through the spider middleware"""
        return None

    def process_spider_output(self, response, result, spider):
        """Called with the results returned from the Spider"""
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        """Called when a spider or process_spider_input() method raises an exception"""
        pass

    def process_start_requests(self, start_requests, spider):
        """Called with the start requests of the spider"""
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)


class LabScraperDownloaderMiddleware:
    """Downloader middleware for processing requests and responses"""

    @classmethod
    def from_crawler(cls, crawler):
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        """Called for each request that goes through the downloader middleware"""
        return None

    def process_response(self, request, response, spider):
        """Called with the response returned from the downloader"""
        return response

    def process_exception(self, request, exception, spider):
        """Called when a download handler or a process_request() raises an exception"""
        pass

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)


class PlaywrightStealthMiddleware:
    """Middleware to inject stealth scripts into Playwright requests"""

    @classmethod
    def from_crawler(cls, crawler):
        return cls()

    def process_request(self, request, spider):
        """Inject stealth script into Playwright requests"""
        if request.meta.get('playwright'):
            # Add stealth script to page initialization
            if 'playwright_page_init_callback' not in request.meta:
                request.meta['playwright_page_init_callback'] = self._stealth_init
        return None

    async def _stealth_init(self, page, request):
        """Initialize page with stealth scripts"""
        # Add init script that runs before page load
        await page.add_init_script(STEALTH_JS)

        # Additional stealth measures
        await page.evaluate("""
            // Add more realistic navigator properties
            Object.defineProperty(navigator, 'hardwareConcurrency', {
                get: () => 8,
            });

            Object.defineProperty(navigator, 'deviceMemory', {
                get: () => 8,
            });

            Object.defineProperty(navigator, 'platform', {
                get: () => 'MacIntel',
            });
        """)
