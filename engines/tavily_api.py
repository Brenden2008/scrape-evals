import os
import sys
from pathlib import Path
from datetime import datetime

# Add project root and src to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from tavily import TavilyClient
from dotenv import load_dotenv
from .base import Scraper, ScrapeResult

load_dotenv()

class TavilyAPIScraper(Scraper):
    """Scrapes web pages using the Tavily API."""
    
    def __init__(self):
        self.api_key = os.getenv("TAVILY_API_KEY")
        if not self.api_key:
            raise ValueError("TAVILY_API_KEY not set in environment.")
        self.tavily_client = TavilyClient(api_key=self.api_key)

    def scrape(self, url: str, run_id: str) -> ScrapeResult:
        error = None
        status_code = None
        html = ""
        content_size = 0
        
        try:
            response = self.tavily_client.extract(url)

            # Tavily SDK returns a dict; handle defensively
            results = None
            status_code = 200
            if isinstance(response, dict):
                status_code = response.get("status_code", 200)
                # try common keys just in case their schema changes
                results = response.get("results") or response.get("data") or response.get("extractions")
            else:
                # Fallback if SDK returns an object
                status_code = getattr(response, "status_code", 200)
                results = getattr(response, "results", None)

            # Extract content
            html_content = None
            markdown_or_text = None
            if results and len(results) > 0:
                first_item = results[0] if isinstance(results, list) else results
                if isinstance(first_item, dict):
                    html_content = (
                        first_item.get("raw_html")
                        or first_item.get("raw_content")
                        or first_item.get("html")
                        or first_item.get("content")
                    )
                    markdown_or_text = first_item.get("markdown") or first_item.get("text")
                else:
                    html_content = getattr(first_item, "raw_content", None)
            else:
                # Some responses may put content at the top level
                if isinstance(response, dict):
                    html_content = (
                        response.get("raw_html")
                        or response.get("raw_content")
                        or response.get("html")
                        or response.get("content")
                        or response.get("text")
                    )
                    markdown_or_text = response.get("markdown") or response.get("text")

            # Choose what to use: prefer HTML, else markdown/text if available
            html = html_content or markdown_or_text or ""
            content_size = len(html.encode('utf-8')) if html else 0

            if not html:
                status_code = 500
                error = "No content found in Tavily response"
            elif status_code and status_code >= 400:
                error = f"HTTP error: {status_code}"
                
        except Exception as e:
            html = ""
            content_size = 0
            status_code = 500
            error = f"{type(e).__name__}: {str(e)}"

        return ScrapeResult(
            run_id=run_id,
            scraper="tavily_api",
            url=url,
            status_code=status_code or 500,
            error=error,
            content_size=content_size,
            format="html",
            created_at=datetime.now().isoformat(),
            content=html or None,
        )
