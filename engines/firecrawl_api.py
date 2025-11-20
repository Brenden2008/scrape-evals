import os
import sys
from pathlib import Path
from datetime import datetime
import asyncio

# Add project root and src to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from dotenv import load_dotenv  # type: ignore
from .base import Scraper, ScrapeResult
from firecrawl import AsyncFirecrawl  # type: ignore

load_dotenv()

class FirecrawlAPIScraper(Scraper):
    """Scrapes web pages using the Firecrawl API with caching disabled (maxAge=0)."""
    def __init__(self):
        self.api_key = os.getenv("FIRECRAWL_API_KEY")
        if not self.api_key:
            raise ValueError("FIRECRAWL_API_KEY not set in environment.")
        self.firecrawl = AsyncFirecrawl(api_key=self.api_key)

    async def scrape(self, url: str, run_id: str) -> ScrapeResult:
        try:
            formats = ['markdown']
            result = await self.firecrawl.scrape(url, formats=formats)

            # Content selection
            markdown = (result.markdown or "") if result else ""
            content = markdown

            # Metadata (typed)
            metadata = result.metadata if result else None
            status_code = metadata.status_code if metadata else 200
            err_str = metadata.error if metadata else None

            content_size = len((markdown or "").encode('utf-8'))

            return ScrapeResult(
                run_id=run_id,
                scraper="firecrawl_api",
                url=url,
                status_code=status_code,
                error=err_str,
                content_size=content_size,
                format="markdown",
                created_at=datetime.now().isoformat(),
                content=content or None,
            )
        except asyncio.TimeoutError:
            return ScrapeResult(
                run_id=run_id,
                scraper="firecrawl_api",
                url=url,
                status_code=408,  # Timeout status code
                error="Timeout error",
                content_size=0,
                format="markdown",
                created_at=datetime.now().isoformat(),
                content=None,
            )
        except Exception as e:
            return ScrapeResult(
                run_id=run_id,
                scraper="firecrawl_api",
                url=url,
                status_code=500,
                error=f"{type(e).__name__}: {str(e)}",
                content_size=0,
                format="markdown",
                created_at=datetime.now().isoformat(),
                content=None,
            )
