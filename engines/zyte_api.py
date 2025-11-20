import os
from datetime import datetime
from base64 import b64decode

import requests
from dotenv import load_dotenv
from .base import Scraper, ScrapeResult

load_dotenv()

class ZyteAPIScraper(Scraper):
    """Scrapes web pages using the Zyte API."""
    
    def __init__(self):
        self.api_key = os.getenv("ZYTE_API_KEY")
        if not self.api_key:
            raise ValueError("ZYTE_API_KEY not set in environment.")
        self.api_url = "https://api.zyte.com/v1/extract"

    def scrape(self, url: str, run_id: str) -> ScrapeResult:
        error = None
        status_code = 500
        html = ""
        content_size = 0

        try:
            payload: dict = {
                "url": url,
            }
            
            payload["httpResponseBody"] = True
            payload["followRedirect"] = True
            
            response = requests.post(
                self.api_url,
                auth=(self.api_key or "", ""),
                json=payload,
                timeout=90
            )
            status_code = response.status_code

            if response.status_code == 200:
                try:
                    response_data = response.json()
                    
                    http_response_body = b64decode(response_data["httpResponseBody"])
                    html = http_response_body.decode('utf-8', errors='ignore')
                    
                    content_size = len(html.encode('utf-8')) if html else 0
                except (KeyError, ValueError) as e:
                    error = f"Failed to decode response: {str(e)}"
            
        except Exception as e:
            html = ""
            content_size = 0
            status_code = 500
            error = f"{type(e).__name__}: {str(e)}"

        return ScrapeResult(
            run_id=run_id,
            scraper="zyte_api",
            url=url,
            status_code=status_code or 500,
            error=error,
            content_size=content_size,
            format="html",
            created_at=datetime.now().isoformat(),
            content=html or None,
        ) 
