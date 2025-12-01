"""
Scrapy Middlewares - E-commerce Scraper

Custom middlewares for handling requests and responses.
"""

from scrapy import signals


class EcommerceScraperSpiderMiddleware:
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


class EcommerceScraperDownloaderMiddleware:
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
