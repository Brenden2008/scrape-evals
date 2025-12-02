import os
import sys
from pathlib import Path
from datetime import datetime
import asyncio

# Add project root and src to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from dotenv import load_dotenv
from .base import Scraper, ScrapeResult

try:
    import httpx
except ImportError:
    httpx = None  # type: ignore

load_dotenv()


class TeracrawlAPIScraper(Scraper):
    """Scrapes web pages using the Teracrawl API (single page scrape endpoint)."""

    def __init__(self):
        if httpx is None:
            raise ImportError("httpx is required for TeracrawlAPIScraper. Install with: pip install httpx")
        
        # Default to localhost:8085 as per Teracrawl documentation
        self.api_url = os.getenv("TERACRAWL_API_URL", "http://localhost:8085")
        self.timeout = float(os.getenv("TERACRAWL_TIMEOUT", "600"))

    def check_environment(self) -> bool:
        """Check if the Teracrawl API is accessible."""
        if httpx is None:
            return False
        try:
            with httpx.Client(timeout=5.0) as client:
                response = client.get(f"{self.api_url}/health")
                return response.status_code == 200
        except Exception:
            return False

    async def scrape(self, url: str, run_id: str) -> ScrapeResult:
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.api_url}/scrape",
                    json={"url": url},
                    headers={"Content-Type": "application/json"},
                )

                if response.status_code != 200:
                    return ScrapeResult(
                        run_id=run_id,
                        scraper="teracrawl_api",
                        url=url,
                        status_code=response.status_code,
                        error=f"HTTP error: {response.status_code}",
                        content_size=0,
                        format="markdown",
                        created_at=datetime.now().isoformat(),
                        content=None,
                    )

                data = response.json()

                # Check status field from Teracrawl response
                status = data.get("status", "")
                if status == "error":
                    return ScrapeResult(
                        run_id=run_id,
                        scraper="teracrawl_api",
                        url=url,
                        status_code=500,
                        error=data.get("error", "Unknown error from Teracrawl"),
                        content_size=0,
                        format="markdown",
                        created_at=datetime.now().isoformat(),
                        content=None,
                    )

                # Extract markdown content
                markdown = data.get("markdown", "")
                content_size = len(markdown.encode("utf-8")) if markdown else 0

                return ScrapeResult(
                    run_id=run_id,
                    scraper="teracrawl_api",
                    url=url,
                    status_code=200,
                    error=None,
                    content_size=content_size,
                    format="markdown",
                    created_at=datetime.now().isoformat(),
                    content=markdown or None,
                )

        except asyncio.TimeoutError:
            return ScrapeResult(
                run_id=run_id,
                scraper="teracrawl_api",
                url=url,
                status_code=408,
                error="Timeout error",
                content_size=0,
                format="markdown",
                created_at=datetime.now().isoformat(),
                content=None,
            )
        except httpx.TimeoutException:
            return ScrapeResult(
                run_id=run_id,
                scraper="teracrawl_api",
                url=url,
                status_code=408,
                error="Timeout error",
                content_size=0,
                format="markdown",
                created_at=datetime.now().isoformat(),
                content=None,
            )
        except Exception as e:
            return ScrapeResult(
                run_id=run_id,
                scraper="teracrawl_api",
                url=url,
                status_code=500,
                error=f"{type(e).__name__}: {str(e)}",
                content_size=0,
                format="markdown",
                created_at=datetime.now().isoformat(),
                content=None,
            )
