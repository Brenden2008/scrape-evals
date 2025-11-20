# NOTE:
# ScrapyScraper uses a subprocess-per-URL approach because Scrapy (and Twisted) rely on a global reactor
# that can only be started once per process. After the reactor is stopped, it cannot be restarted in the same process.
# This makes it impossible to run multiple independent Scrapy crawls in the same process for benchmarking.
# By running each crawl in a separate subprocess (calling scrapers/scrapy_single.py), we ensure a fresh reactor
# for every URL, avoid all reactor restart errors, and maintain robust, isolated benchmarking.

import json
import os
import subprocess
import sys
from datetime import datetime

from .base import Scraper, ScrapeResult

class ScrapyScraper(Scraper):
    """Scrapes web pages using Scrapy."""

    def scrape(self, url: str, run_id: str) -> ScrapeResult:
        error = None
        status_code = 500
        html = ""
        content_size = 0
        
        try:
            script_path = os.path.join(os.path.dirname(__file__), "scripts/scrapy_single.py")
            result = subprocess.run(
                [sys.executable, script_path, url],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                try:
                    spider_result = json.loads(result.stdout.strip().split('\n')[-1])
                    status_code = spider_result.get("status_code")
                    error = spider_result.get("error")
                    html = spider_result.get("html") or ""
                    content_size = len(html.encode('utf-8')) if html else 0
                except (json.JSONDecodeError, IndexError):
                    status_code = 500
                    error = "Failed to parse Scrapy output"
                    html = ""
                    content_size = 0
            else:
                status_code = 500
                error = f"Scrapy process failed: {result.stderr}"
                html = ""
                content_size = 0
                
            if status_code is None and error is None:
                error = "No response received (possible network or DNS error)"
                status_code = 500
                
        except subprocess.TimeoutExpired:
            status_code = 500
            error = "Timeout: Scrapy process took longer than 60 seconds"
            html = ""
            content_size = 0
            
        except Exception as e:
            status_code = 500
            error = f"ScrapyError: {type(e).__name__}: {str(e)}"
            html = ""
            content_size = 0

        return ScrapeResult(
            run_id=run_id,
            scraper="scrapy_scraper",
            url=url,
            status_code=status_code or 500,
            error=error,
            content_size=content_size,
            format="html",
            created_at=datetime.now().isoformat(),
            content=html or None,
        )   
