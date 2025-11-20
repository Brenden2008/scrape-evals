import os
import sys
from pathlib import Path
from datetime import datetime

# Add project root and src to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from dotenv import load_dotenv
from .base import Scraper, ScrapeResult
from exa_py import Exa

load_dotenv()

class ExaAPIScraper(Scraper):
    """Scrapes web pages using the Exa API."""
    
    def __init__(self):
        self.api_key = os.getenv("EXA_API_KEY")
        if not self.api_key:
            raise ValueError("EXA_API_KEY not set in environment.")
        self.exa = Exa(api_key=self.api_key)

    def scrape(self, url: str, run_id: str) -> ScrapeResult:
        content_size = 0
        
        try:
            result = self.exa.get_contents(
                [url],
                text={
                    "include_html_tags": True
                }
            )
            
            # Extract the first result since we're only scraping one URL
            if result and hasattr(result, 'results') and len(result.results) > 0:
                first_result = result.results[0]
                html_content = getattr(first_result, 'text', '') or ''
                
                content_size = len(html_content.encode('utf-8')) if html_content else 0
                
                # Try to get status code from result
                status_code = 200  # Default success
                if hasattr(result, 'statuses') and result.statuses and len(result.statuses) > 0:
                    status_obj = result.statuses[0]
                    # Try common status code attribute names
                    if hasattr(status_obj, 'status'):
                        status_code = 200 if status_obj.status == 'success' else 500
                
                return ScrapeResult(
                    run_id=run_id,
                    scraper="exa_api",
                    url=url,
                    status_code=status_code,
                    error=None,
                    content_size=content_size,
                    format="html",
                    created_at=datetime.now().isoformat(),
                    content=html_content or None,
                )
            else:
                return ScrapeResult(
                    run_id=run_id,
                    scraper="exa_api",
                    url=url,
                    status_code=404,
                    error="No content returned from Exa API",
                    content_size=0,
                    format="html",
                    created_at=datetime.now().isoformat(),
                    content=None,
                )
                
        except Exception as e:
            return ScrapeResult(
                run_id=run_id,
                scraper="exa_api",
                url=url,
                status_code=500,
                error=f"{type(e).__name__}: {str(e)}",
                content_size=0,
                format="html",
                created_at=datetime.now().isoformat(),
                content=None,
            )
