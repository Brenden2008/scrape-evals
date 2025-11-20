from __future__ import annotations
from .base import ScrapeResult, Scraper
import requests
from datetime import datetime

class RestScraper(Scraper):
    def scrape(self, url: str, run_id: str) -> ScrapeResult:
        try:
            response = requests.get(url, timeout=30)
            created_at = datetime.now().isoformat()
            status_code = response.status_code
            error = None
            content = response.text or ""
            if response.status_code >= 400:
                error = f"HTTP {response.status_code}: {response.reason}"
            content_size = len(content.encode('utf-8')) if content else 0
            return ScrapeResult(
                run_id=run_id,
                scraper="rest_scraper",
                url=url,
                status_code=status_code,
                error=error,
                content_size=content_size,
                format="html",
                created_at=created_at,
                content=content or None,
            )
        except requests.exceptions.Timeout:
            created_at = datetime.now().isoformat()
            return ScrapeResult(
                run_id=run_id,
                scraper="rest_scraper",
                url=url,
                status_code=408,
                error="Timeout: Request took longer than 30 seconds",
                content_size=0,
                format="html",
                created_at=created_at,
                content=None,
            )
        except requests.exceptions.ConnectionError as e:
            created_at = datetime.now().isoformat()
            return ScrapeResult(
                run_id=run_id,
                scraper="rest_scraper",
                url=url,
                status_code=503,
                error=f"ConnectionError: {str(e)}",
                content_size=0,
                format="html",
                created_at=created_at,
                content=None,
            )
        except requests.exceptions.RequestException as e:
            created_at = datetime.now().isoformat()
            return ScrapeResult(
                run_id=run_id,
                scraper="rest_scraper",
                url=url,
                status_code=500,
                error=f"RequestError: {type(e).__name__}: {str(e)}",
                content_size=0,
                format="html",
                created_at=created_at,
                content=None,
            )
        except Exception as e:
            created_at = datetime.now().isoformat()
            return ScrapeResult(
                run_id=run_id,
                scraper="rest_scraper",
                url=url,
                status_code=500,
                error=f"RestError: {type(e).__name__}: {str(e)}",
                content_size=0,
                format="html",
                created_at=created_at,
                content=None,
            )


