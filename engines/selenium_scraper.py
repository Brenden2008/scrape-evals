from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from .base import Scraper, ScrapeResult

class SeleniumScraper(Scraper):
    """
    Scrapes web pages using Selenium (headless Chrome browser).
    """
    def check_environment(self) -> bool:
        try:
            opts = Options()
            opts.add_argument("--headless")
            driver = webdriver.Chrome(options=opts)
            driver.quit()
            return True
        except Exception:
            return False

    def scrape(self, url: str, run_id: str) -> ScrapeResult:
        error = None
        status_code = 500
        html = ""
        content_size = 0
        driver = None
        
        try:
            opts = Options()
            opts.add_argument("--headless")
            driver = webdriver.Chrome(options=opts)
            driver.set_page_load_timeout(30)
            driver.get(url)
            html = driver.page_source
            
            # Get the actual HTTP status code from the browser
            status_code = driver.execute_script("return window.performance.getEntriesByType('navigation')[0].responseStatus;")
            if status_code is None:
                status_code = 200 if html else 500
            
            content_size = len(html.encode('utf-8')) if html else 0
            
            driver.quit()
            
        except Exception as e:
            html = ""
            content_size = 0
            status_code = 500
            error = f"{type(e).__name__}: {str(e)}"

        return ScrapeResult(
            run_id=run_id,
            scraper="selenium_scraper",
            url=url,
            status_code=status_code or 500,
            error=error,
            content_size=content_size,
            format="html",
            created_at=datetime.now().isoformat(),
            content=html or None,
        ) 
