import scrapy
import re

from scrapy_playwright.page import PageMethod


class BaytSpider(scrapy.Spider):
    name = "bayt"
    allowed_domains = ["bayt.com"]

    # -------------------------------------------------------------------------
    # 1. SCRAPY-PLAYWRIGHT & OUTPUT SETTINGS
    # -------------------------------------------------------------------------
    custom_settings = {
        # Route requests through Playwright instead of Scrapy's default downloader
        "DOWNLOAD_HANDLERS": {
            "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
            "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
        },
        "TWISTED_REACTOR": "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
        "PLAYWRIGHT_BROWSER_TYPE": "chromium",
        "PLAYWRIGHT_LAUNCH_OPTIONS": {"headless": True},
        # save output to a JSON Lines file
        "FEEDS": {
            "raw_jobs.jsonl": {
                "format": "jsonlines",
                "encoding": "utf8",
                "overwrite": True,
            }
        },
    }

    # -------------------------------------------------------------------------
    # 2. THE PAGE LIMITER (Lab Requirement)
    # -------------------------------------------------------------------------
    def __init__(self, max_pages=3, *args, **kwargs):
        super(BaytSpider, self).__init__(*args, **kwargs)
        # Allows running: scrapy crawl bayt -a max_pages=5
        self.max_pages = int(max_pages)
        self.pages_crawled = 0

    def start_requests(self):
        url = "https://www.bayt.com/en/egypt/jobs/"
        yield scrapy.Request(
            url,
            callback=self.parse_search_page,
            meta={
                # <-- PLAYWRIGHT WAIT FOR JS TO FINISH -->
                "playwright_page_methods": [
                    PageMethod("wait_for_load_state", "networkidle")
                ],
            },
        )

    # -------------------------------------------------------------------------
    # 3. THE ROUTER (Finding Links & Pagination)
    # -------------------------------------------------------------------------
    # -------------------------------------------------------------------------
    # 3. THE ROUTER (Finding Links & Pagination)
    # -------------------------------------------------------------------------
    def parse_search_page(self, response):
        self.pages_crawled += 1
        self.logger.info(
            f"Crawling Search Page: {self.pages_crawled} / {self.max_pages}"
        )

        # --- A. Regex Link Filtering ---
        # Matches any href that contains "jobId=" followed by one or more digits
        job_links = response.css("a::attr(href)").re(r"/en/\w+/jobs/[\w-]+-\d+/")

        for link in set(job_links):
            absolute_url = response.urljoin(link)
            yield scrapy.Request(
                absolute_url,
                callback=self.parse_job_listing,
                meta={"playwright": True},
            )

        # --- B. Pagination (The BFS Engine) ---
        if self.pages_crawled < self.max_pages:
            # Look for the "Next" page button.
            next_page_link = (
                response.css("a[data-js='next-page']::attr(href)").get()
                or response.css(".pagination .next a::attr(href)").get()
            )

            if next_page_link:
                yield scrapy.Request(
                    response.urljoin(next_page_link),
                    callback=self.parse_search_page,
                    meta={"playwright": True},
                )
            else:
                self.logger.info("No more pagination links found.")
        else:
            self.logger.info(
                f"🛑 Reached max_pages limit ({self.max_pages}). Stopping."
            )

    # -------------------------------------------------------------------------
    # 4. THE EXTRACTOR (Grabbing Data for Week 2)
    # -------------------------------------------------------------------------
    def parse_job_listing(self, response):
        main_content = response.css("div.t-break").get() or response.css("body").get()

        yield {
            "url": response.url,
            "job_title": response.css("h1::text").get(default="Unknown").strip(),
            # stripping massive whitespace
            "raw_html_payload": re.sub(r"\s+", " ", main_content)[:5000],
        }
