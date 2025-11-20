import sys
import json
import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy.spiders import Spider
from scrapy.utils.project import get_project_settings
from scrapy.utils.log import configure_logging
from typing import Optional, Dict, Union

class StatusSpider(Spider):
    name = "status_spider"
    custom_settings = {
        "LOG_ENABLED": False,
        "LOG_LEVEL": "CRITICAL",
        "DOWNLOAD_TIMEOUT": 30,
        "RETRY_ENABLED": False,
        "USER_AGENT": "Mozilla/5.0 (compatible; ScrapersBenchmark/1.0)",
        "HTTPERROR_ALLOW_ALL": True,
    }
    handle_httpstatus_all = True

    def __init__(self, url, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.start_urls = [url]
        self.result: Dict[str, Union[Optional[str], int]] = {"status_code": None, "error": None, "html": None}
        
    def start_requests(self):
        yield scrapy.Request(self.start_urls[0], callback=self.parse, errback=self.errback)

    def parse(self, response):
        self.result["status_code"] = response.status
        self.result["error"] = None
        self.result["html"] = response.text

    def errback(self, failure):
        self.result["status_code"] = None
        self.result["error"] = str(failure.value)
        self.result["html"] = None
        
    def closed(self, reason):
        print(json.dumps(self.result))

def main():
    url = sys.argv[1]
    configure_logging(install_root_handler=False)
    process = CrawlerProcess({
        **get_project_settings(),
        "LOG_ENABLED": False,
        "LOG_LEVEL": "CRITICAL",
        "DOWNLOAD_TIMEOUT": 30,
        "RETRY_ENABLED": False,
        "USER_AGENT": "Mozilla/5.0 (compatible; ScrapersBenchmark/1.0)",
        "HTTPERROR_ALLOW_ALL": True,
    })
    process.crawl(StatusSpider, url=url)
    process.start()

if __name__ == "__main__":
    main() 