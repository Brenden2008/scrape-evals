import os
import requests
from datetime import datetime
from dotenv import load_dotenv
from .base import Scraper, ScrapeResult

load_dotenv()

class ScraperAPIAPIScraper(Scraper):
    """
    Scraper implementation for ScraperAPI.
    """
    def __init__(self):
        self.api_key = os.getenv("SCRAPERAPI_API_KEY")
        if not self.api_key:
            raise RuntimeError("SCRAPERAPI_API_KEY environment variable not set.")
        self.base_url = "https://api.scraperapi.com/"

    def scrape(self, url: str, run_id: str) -> ScrapeResult:
        error = None
        status_code = 500
        content_size = 0
        try:
            payload = {
                "api_key": self.api_key,
                "url": url,
            }
            headers = {}
            headers["x-sapi-api_key"] = self.api_key
            resp = requests.get(self.base_url, headers=headers, params=payload, timeout=180)
            status_code = resp.status_code
            html = resp.text or ""
            
            # Try to parse JSON response to extract html if present
            try:
                if resp.headers.get("Content-Type", "").startswith("application/json"):
                    data = resp.json()
                    # Some JSON responses may include rendered html
                    html = data.get("html") or html
            except Exception:
                pass
            content_size = len(html.encode("utf-8")) if html else 0
        except Exception as e:
            html = ""
            content_size = 0
            status_code = 500
            error = str(e)
        
        return ScrapeResult(
            run_id=run_id,
            scraper="scraperapi_api",
            url=url,
            status_code=status_code or 500,
            error=error,
            content_size=content_size,
            format="html",
            created_at=datetime.now().isoformat(),
            content=html or None,
        )
