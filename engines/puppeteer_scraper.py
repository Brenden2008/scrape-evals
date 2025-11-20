import os
from datetime import datetime
import subprocess
from .base import Scraper, ScrapeResult

class PuppeteerScraper(Scraper):
    """
    Scrapes web pages using Puppeteer (Node.js headless browser).
    """
    def check_environment(self) -> bool:
        try:
            # Check Node.js
            subprocess.run(["node", "--version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            # Check Puppeteer (try to require it)
            scripts_dir = os.path.join(os.path.dirname(__file__), "scripts")
            subprocess.run(["node", "-e", "require('puppeteer')"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=scripts_dir)
            return True
        except Exception:
            return False

    def scrape(self, url: str, run_id: str) -> ScrapeResult:
        scripts_dir = os.path.join(os.path.dirname(__file__), "scripts")
        script_path = os.path.join(scripts_dir, "puppeteer_single.js")
        try:
            # Defaults to avoid UnboundLocalError on failures
            status_code = None
            error = None
            html = None
            content_size = 0
            result = subprocess.run(
                ["node", "puppeteer_single.js", url],
                capture_output=True,
                text=True,
                timeout=60,
                cwd=scripts_dir
            )
            created_at = datetime.now().isoformat()
            
            if result.returncode == 0:
                import json
                try:
                    data = json.loads(result.stdout.strip().split('\n')[-1])
                    status_code = data.get("status_code") or 200
                    error = data.get("error")
                    html = data.get("html")
                    if html:
                        content_size = len(html.encode('utf-8'))
                    content_text = html if html else ""
                except Exception:
                    status_code = 500
                    error = "Failed to parse Puppeteer output"
                    content_text = ""
            else:
                status_code = 500
                error = f"Puppeteer process failed: {result.stderr}"
                content_text = ""
            
            return ScrapeResult(
                run_id=run_id,
                scraper="puppeteer_scraper",
                url=url,
                status_code=status_code,
                error=error,
                content_size=content_size,
                format="html",
                created_at=created_at,
                content=content_text or None,
            )
        except subprocess.TimeoutExpired:
            created_at = datetime.now().isoformat()
            return ScrapeResult(
                run_id=run_id,
                scraper="puppeteer_scraper",
                url=url,
                status_code=408,
                error="Timeout: Puppeteer process took longer than 60 seconds",
                content_size=0,
                format="html",
                created_at=created_at,
                content=None,
            )
        except Exception as e:
            created_at = datetime.now().isoformat()
            return ScrapeResult(
                run_id=run_id,
                scraper="puppeteer_scraper",
                url=url,
                status_code=500,
                error=f"PuppeteerError: {type(e).__name__}: {str(e)}",
                content_size=0,
                format="html",
                created_at=created_at,
                content=None,
            ) 
