"""
AgriScraper — Real-world Zimbabwe agricultural data engine.
Scrapes live prices from GMB/AMA/ZAMACE and news from Zimbabwe media RSS feeds.
No hardcoded prices or fake random fluctuations.
"""
import logging
import xml.etree.ElementTree as ET
from datetime import datetime

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}

# ---------------------------------------------------------------------------
# NEWS SOURCES  (RSS feeds — most reliable, structured data)
# ---------------------------------------------------------------------------
NEWS_RSS_SOURCES = [
    ("The Herald",   "https://www.herald.co.zw/feed/"),
    ("NewsDay",      "https://www.newsday.co.zw/feed/"),
    ("Chronicle",    "https://www.chronicle.co.zw/feed/"),
    ("ZBC News",     "https://www.zbcnews.co.zw/feed/"),
    ("Sunday Mail",  "https://www.sundaymail.co.zw/feed/"),
    ("FinGazette",   "https://www.financialgazette.co.zw/feed/"),
]

# Fallback HTML scrape sources when RSS fails
NEWS_HTML_SOURCES = [
    ("The Herald",   "https://www.herald.co.zw/category/business/agriculture/"),
    ("Chronicle",    "https://www.chronicle.co.zw/category/business/agriculture/"),
    ("NewsDay",      "https://www.newsday.co.zw/category/15/business"),
    ("Agriculture",  "https://agriculture.co.zw"),
    ("AfriAgri",     "https://africanagribusiness.com"),
]

AGRI_KEYWORDS = {
    "maize", "wheat", "soybean", "tobacco", "cotton", "harvest", "crop",
    "farm", "agri", "grain", "livestock", "drought", "rain", "fertilizer",
    "subsidy", "export", "import", "gmb", "zamace", "ama", "food",
    "price", "market", "commodity", "seed", "irrigation", "cattle",
    "horticulture", "groundnut", "sorghum", "sugar", "bean",
}

# ---------------------------------------------------------------------------
# PRICE SOURCES  (structured pages with actual price tables)
# ---------------------------------------------------------------------------
PRICE_SOURCES = [
    # GMB official floor prices page
    "https://gmbdura.co.zw/pricing/",
    # AMA market bulletins
    "https://ama.co.zw/",
    # ZimPriceCheck market prices
    "https://zimpricecheck.com/market-prices/",
    # FarmnPort aggregator
    "https://farmnport.com/prices",
    # Ministry of Agriculture
    "https://www.agric.gov.zw/",
]

# ---------------------------------------------------------------------------
# In-memory cache
# ---------------------------------------------------------------------------
_news_cache: list[dict] | None = None
_news_cache_time: datetime | None = None
_NEWS_TTL = 3600  # 1 hour

_price_cache: list[dict] | None = None
_price_cache_time: datetime | None = None
_PRICE_TTL = 3600  # 1 hour


class AgriScraper:

    # ------------------------------------------------------------------ #
    #  NEWS                                                                #
    # ------------------------------------------------------------------ #

    @classmethod
    def scrape_latest_news(cls) -> list[dict]:
        """
        Returns real agriculture news from Zimbabwe RSS feeds.
        Falls back to HTML scraping if RSS is unavailable.
        Returns empty list (never fake data) if all sources fail.
        """
        global _news_cache, _news_cache_time

        now = datetime.utcnow()
        if _news_cache is not None and _news_cache_time is not None:
            if (now - _news_cache_time).total_seconds() < _NEWS_TTL:
                return _news_cache

        articles: list[dict] = []

        # 1. Try RSS feeds first (structured, reliable)
        for source, url in NEWS_RSS_SOURCES:
            articles.extend(cls._parse_rss(url, source))
            if len(articles) >= 10:
                break

        # 2. Fall back to HTML scraping
        if not articles:
            for source, url in NEWS_HTML_SOURCES:
                articles.extend(cls._scrape_html_headlines(url, source))
                if len(articles) >= 10:
                    break

        _news_cache = articles[:10]
        _news_cache_time = now
        return _news_cache

    @staticmethod
    def _parse_rss(url: str, source: str) -> list[dict]:
        try:
            resp = requests.get(url, timeout=6, headers=_HEADERS)
            if resp.status_code != 200:
                return []
            root = ET.fromstring(resp.content)
            results = []
            for item in root.findall(".//item")[:8]:
                title = (item.findtext("title") or "").strip()
                link  = (item.findtext("link")  or url).strip()
                pub   = (item.findtext("pubDate") or "").strip()
                if not title:
                    continue
                if any(kw in title.lower() for kw in AGRI_KEYWORDS):
                    results.append({
                        "title":     title,
                        "url":       link,
                        "source":    source,
                        "published": pub,
                        "live":      True,
                    })
            return results
        except Exception as e:
            logger.debug("RSS parse failed for %s: %s", url, e)
            return []

    @staticmethod
    def _scrape_html_headlines(url: str, source: str) -> list[dict]:
        try:
            resp = requests.get(url, timeout=6, headers=_HEADERS)
            if resp.status_code != 200:
                return []
            soup = BeautifulSoup(resp.content, "html.parser")
            results = []
            for tag in soup.find_all(["h1", "h2", "h3", "a"], limit=20):
                title = tag.get_text(strip=True)
                href  = tag.get("href", url)
                if not href.startswith("http"):
                    href = url
                if 30 < len(title) < 160 and any(kw in title.lower() for kw in AGRI_KEYWORDS):
                    results.append({
                        "title":     title,
                        "url":       href,
                        "source":    source,
                        "published": "",
                        "live":      True,
                    })
                if len(results) >= 3:
                    break
            return results
        except Exception as e:
            logger.debug("HTML scrape failed for %s: %s", url, e)
            return []

    # ------------------------------------------------------------------ #
    #  PRICES                                                              #
    # ------------------------------------------------------------------ #

    @classmethod
    def scrape_market_prices(cls) -> list[dict]:
        """
        Scrapes real commodity prices from GMB/AMA/ZimPriceCheck.
        Returns only prices that were actually found on the page.
        Returns empty list if all sources fail — never fake data.
        """
        global _price_cache, _price_cache_time

        now = datetime.utcnow()
        if _price_cache is not None and _price_cache_time is not None:
            if (now - _price_cache_time).total_seconds() < _PRICE_TTL:
                return _price_cache

        prices: list[dict] = []

        for url in PRICE_SOURCES:
            found = cls._extract_prices_from_page(url)
            prices.extend(found)
            if len(prices) >= 5:
                break

        _price_cache = prices
        _price_cache_time = now
        return prices

    @staticmethod
    def _extract_prices_from_page(url: str) -> list[dict]:
        """
        Attempts to extract commodity name + price pairs from a page.
        Looks for table rows and elements containing known crop names + numbers.
        """
        CROP_NAMES = [
            "maize", "wheat", "soybeans", "soybean", "sorghum", "groundnut",
            "tobacco", "cotton", "sugar bean", "sunflower", "barley",
        ]
        import re
        results = []
        try:
            resp = requests.get(url, timeout=7, headers=_HEADERS)
            if resp.status_code != 200:
                return []
            soup = BeautifulSoup(resp.content, "html.parser")

            # Strategy 1: look for <table> rows with price data
            for row in soup.find_all("tr"):
                cells = [td.get_text(strip=True) for td in row.find_all(["td", "th"])]
                if len(cells) < 2:
                    continue
                row_text = " ".join(cells).lower()
                matched_crop = next((c for c in CROP_NAMES if c in row_text), None)
                if not matched_crop:
                    continue
                # Find a number that looks like a price
                numbers = re.findall(r"\d[\d,]*\.?\d*", " ".join(cells))
                if not numbers:
                    continue
                price_str = numbers[0].replace(",", "")
                try:
                    price = float(price_str)
                except ValueError:
                    continue
                # Determine unit from context
                unit = "t"
                if any(u in row_text for u in ["/kg", "per kg", "kg"]):
                    unit = "kg"
                elif any(u in row_text for u in ["/t", "per tonne", "tonne", "ton"]):
                    unit = "t"
                results.append({
                    "commodity": matched_crop.title(),
                    "price":     price,
                    "unit":      unit,
                    "source":    url,
                    "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M"),
                })

            # Strategy 2: look for paragraphs/divs mentioning crop + price
            if not results:
                for elem in soup.find_all(["p", "li", "div", "span"], limit=200):
                    text = elem.get_text(strip=True)
                    text_lower = text.lower()
                    matched_crop = next((c for c in CROP_NAMES if c in text_lower), None)
                    if not matched_crop:
                        continue
                    numbers = re.findall(r"\$?\d[\d,]*\.?\d*", text)
                    if not numbers:
                        continue
                    price_str = numbers[0].replace("$", "").replace(",", "")
                    try:
                        price = float(price_str)
                    except ValueError:
                        continue
                    unit = "kg" if "/kg" in text_lower else "t"
                    results.append({
                        "commodity": matched_crop.title(),
                        "price":     price,
                        "unit":      unit,
                        "source":    url,
                        "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M"),
                    })
                    if len(results) >= 5:
                        break

        except Exception as e:
            logger.debug("Price scrape failed for %s: %s", url, e)

        return results
