from .base import Scraper, ScrapeResult
from datetime import datetime
import sys
import os
from contextlib import contextmanager
from crawl4ai import AsyncWebCrawler
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig

class Crawl4AIScraper(Scraper):
    """
    Scrapes web pages using the local Crawl4AI library (headless browser).
    """
    def check_environment(self) -> bool:
        try:
            # Try to instantiate the crawler (will fail if setup is missing)
            _ = AsyncWebCrawler()
            return True
        except Exception:
            return False

    @contextmanager
    def suppress_output(self):
        with open(os.devnull, 'w') as devnull:
            old_stdout = sys.stdout
            old_stderr = sys.stderr
            sys.stdout = devnull
            sys.stderr = devnull
            try:
                yield
            finally:
                sys.stdout = old_stdout
                sys.stderr = old_stderr

    async def scrape(self, url: str, run_id: str) -> ScrapeResult:
        try:

            browser_config = BrowserConfig(verbose=False)
            with self.suppress_output():
                async with AsyncWebCrawler(config=browser_config) as crawler:
                    result = await crawler.arun(url=url, config=CrawlerRunConfig())
            content_size = len(result.html.encode('utf-8')) if result.html else 0

            return ScrapeResult(
                run_id=run_id,
                scraper="crawl4ai_scraper",
                url=url,
                status_code=result.status_code or 200,
                error=None if result.success else result.error_message,
                content_size=content_size,
                format="html",
                created_at=datetime.now().isoformat(),
                content=result.html,
            )
        except Exception as e:
            return ScrapeResult(
                run_id=run_id,
                scraper="crawl4ai_scraper",
                url=url,
                status_code=500,
                error=f"{type(e).__name__}: {str(e)}",
                format="html",
                content=None,
                content_size=0,
                created_at=datetime.now().isoformat(),
            )
