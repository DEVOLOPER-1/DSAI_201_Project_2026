BOT_NAME = "crawler"

SPIDER_MODULES = ["crawler.spiders"]
NEWSPIDER_MODULE = "crawler.spiders"

# -----------------------------------------------------------------------------
# 1. THE BREADTH-FIRST SEARCH (BFS) ENGINE
# -----------------------------------------------------------------------------
# By default, Scrapy uses a Last-In, First-Out (LIFO) queue (Depth-First Search).


DEPTH_PRIORITY = 1
SCHEDULER_DISK_QUEUE = "scrapy.squeues.PickleFifoDiskQueue"
SCHEDULER_MEMORY_QUEUE = "scrapy.squeues.FifoMemoryQueue"

# -----------------------------------------------------------------------------
# 2. STEALTH & HUMAN DISGUISE MECHANISMS
# -----------------------------------------------------------------------------
# Bayt will block bots instantly. We must not declare ourselves as a Scrapy bot.
ROBOTSTXT_OBEY = False

# We provide a highly modern, standard browser User-Agent as a fallback.
# (Note: For a real production run, we will add a User-Agent rotation middleware).
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"

# Inject standard headers so the request looks like a real Chrome browser tab opening.
DEFAULT_REQUEST_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,ar;q=0.8",  # Support our bilingual requirement!
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
}

# Disable cookies! Job boards use tracking cookies to identify and ban scraping sessions.
# Keeping this False means every request looks like a fresh, incognito browser.
COOKIES_ENABLED = False

# -----------------------------------------------------------------------------
# 3. CONCURRENCY & THROTTLING (DON'T DDOS THE TARGET)
# -----------------------------------------------------------------------------
# Hitting Bayt with 16 concurrent requests will trigger their firewall.
# We slow it down to mimic human clicking speed.
CONCURRENT_REQUESTS = 4
CONCURRENT_REQUESTS_PER_DOMAIN = 2

# Scrapy will automatically randomize this
# between 1.0s and 3.0s (0.5x to 1.5x) to prevent predictable machine patterns.
DOWNLOAD_DELAY = 2

# slows down the spider if the Bayt server starts responding slowly.
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 2
AUTOTHROTTLE_MAX_DELAY = 10
AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0


HTTPCACHE_ENABLED = True
HTTPCACHE_EXPIRATION_SECS = 86400  # Cache expires after 24 hours
HTTPCACHE_DIR = "httpcache"
HTTPCACHE_IGNORE_HTTP_CODES = [403, 404, 500, 503]  # Don't cache error pages!
HTTPCACHE_STORAGE = "scrapy.extensions.httpcache.FilesystemCacheStorage"

# Set settings whose default value is deprecated to a future-proof value
REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
FEED_EXPORT_ENCODING = "utf-8"


DOWNLOADER_MIDDLEWARES = {
    # 1. Disable static User-Agent middleware
    "scrapy.downloadermiddlewares.useragent.UserAgentMiddleware": None,
    # Enable our custom rotating middleware (Lower number = executes earlier)
    "crawler.middlewares.RotateBrowserHeadersMiddleware": 400,
}
