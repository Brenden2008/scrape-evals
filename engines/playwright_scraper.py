import os
from datetime import datetime
from .base import Scraper, ScrapeResult

class PlaywrightScraper(Scraper):
    """
    Scrapes web pages using Playwright (headless browser).
    """
    def check_environment(self) -> bool:
        try:
            import playwright.async_api
            return True
        except ImportError:
            return False

    async def scrape(self, url: str, run_id: str) -> ScrapeResult:
        try:
            from playwright.async_api import async_playwright

            async with async_playwright() as p:
                headful_env = os.getenv("PLAYWRIGHT_HEADFUL", "0")
                is_headful = headful_env in ["1", "true", "True"]
                browser = await p.chromium.launch(headless=not is_headful, devtools=is_headful, slow_mo=100 if is_headful else 0)
                page = await browser.new_page()
                response = await page.goto(url, wait_until="networkidle", timeout=30000)
                status_code = response.status if response else None
                html = await page.content()
                content_size = len(html.encode('utf-8')) if html else 0
                await browser.close()

                return ScrapeResult(
                    run_id=run_id,
                    scraper="playwright_scraper",
                    url=url,
                    status_code=status_code or 200,
                    error=None if status_code and status_code < 400 else f"HTTP error: {status_code}",
                    content_size=content_size,
                    format="html",
                    created_at=datetime.now().isoformat(),
                    content=html or None,
                )
        except Exception as e:
            return ScrapeResult(
                run_id=run_id,
                scraper="playwright_scraper",
                url=url,
                status_code=500,
                error=f"{type(e).__name__}: {str(e)}",
                content_size=0,
                format="html",
                created_at=datetime.now().isoformat(),
                content=None,
            ) 
