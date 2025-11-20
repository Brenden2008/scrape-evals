import os
from datetime import datetime
from scrapingbee import ScrapingBeeClient
from dotenv import load_dotenv
from .base import Scraper, ScrapeResult

load_dotenv()

class ScrapingBeeAPIScraper(Scraper):
    """
    Scraper implementation for ScrapingBee API.
    """
    def __init__(self):
        self.api_key = os.getenv("SCRAPINGBEE_API_KEY")
        if not self.api_key:
            raise RuntimeError("SCRAPINGBEE_API_KEY environment variable not set.")
        self.client = ScrapingBeeClient(api_key=self.api_key)

    def scrape(self, url: str, run_id: str) -> ScrapeResult:
        error = None
        status_code = 500
        html = ""
        content_size = 0

        params: dict[str, str | list | dict[str, list]]  = { "transparent_status_code": "True" }
        try:
            response = self.client.get(url, params=params)
            status_code = response.status_code
            html = response.content.decode("utf-8", errors="replace") if response.content else ""
            
            content_size = len(response.content) if response.content else 0
        except Exception as e:
            html = ""
            content_size = 0
            status_code = 500
            error = str(e)
        
        return ScrapeResult(
            run_id=run_id,
            scraper="scrapingbee_api",
            url=url,
            status_code=status_code or 500,
            error=error,
            content_size=content_size,
            format="html",
            created_at=datetime.now().isoformat(),
            content=html or None,
        ) 
