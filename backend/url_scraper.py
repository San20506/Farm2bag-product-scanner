"""
URL-based product scraper.
Accepts raw product page URLs, visits them with Playwright,
and auto-extracts product info using multiple strategies:
  1. JSON-LD structured data  (most reliable)
  2. Open Graph / Twitter meta tags
  3. Site-specific CSS selectors  (BigBasket, Amazon, Flipkart, Jiomart, Zepto, Blinkit, Swiggy)
  4. Generic itemprop / data-* attributes
  5. Any text that looks like a price near a title
"""

import asyncio
import re
import logging
from typing import Any, Optional
from datetime import datetime
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

# ── Browser headers that look like a real Chrome request ─────────────
HEADERS = {
    "Accept-Language": "en-IN,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
}

# ── Site-specific selectors (highest priority after JSON-LD/OG) ───────
SITE_SELECTORS: dict[str, dict[str, list[str]]] = {
    "bigbasket.com": {
        "name":  ["h1.PDP__name", "h1[class*='product-name']", "h1.prd-name"],
        "price": [".Pricing__storePrice", ".pdp-price", ".discnt-price",
                  "[class*='sp']", "[class*='selling']", "[class*='offer']"],
        "image": [".product__img img", ".imgCnt img"],
    },
    "amazon.in": {
        "name":  ["#productTitle", "#title"],
        "price": ["#priceblock_ourprice", "#priceblock_dealprice",
                  ".a-price-whole", "#price_inside_buybox",
                  "#corePrice_feature_div .a-price-whole",
                  ".reinventPricePriceToPayMargin .a-price-whole"],
        "image": ["#imgTagWrapperId img", "#landingImage"],
    },
    "flipkart.com": {
        "name":  ["span.B_NuCI", "h1.yhB1nd", "h1[class*='title']"],
        "price": ["div._30jeq3", "div._16Jk6d", "div.dyC4hf",
                  "[class*='_30jeq3']", "[class*='price']"],
        "image": ["img._396cs4", "img._2r_T1I"],
    },
    "jiomart.com": {
        "name":  ["h1.product-title", "h1.product_title"],
        "price": ["span.final-price", ".product-price .price", "span#price"],
        "image": [".product-image img", ".product_image img"],
    },
    "zepto.app": {
        "name":  ["h1[class*='product']", "h1[class*='name']"],
        "price": ["[class*='price']", "[class*='amount']"],
        "image": ["img[class*='product']"],
    },
    "blinkit.com": {
        "name":  ["h1[class*='product']", "h1[class*='title']"],
        "price": ["[class*='price']", "[class*='amount']"],
        "image": ["img[class*='product']", "img[class*='item']"],
    },
    "swiggy.com": {
        "name":  ["h1[class*='name']", "h1[class*='title']"],
        "price": ["[class*='price']", "[class*='cost']"],
        "image": ["img[class*='product']"],
    },
    "nykaa.com": {
        "name":  ["h1[class*='product']", ".product-title"],
        "price": [".css-17x7n7h", "[class*='selling']", "[class*='price']"],
        "image": ["div.image-carousel img"],
    },
    "meesho.com": {
        "name":  ["h1[class*='ProductTitle']", "p[class*='title']"],
        "price": ["h4[class*='Price']", "[class*='price']"],
        "image": ["img[class*='ProductImage']"],
    },
}

# ── Generic price-looking selectors (applied to every site) ───────────
GENERIC_PRICE_SELECTORS = [
    "[itemprop='price']",
    "[class*='selling-price']", "[class*='sellingPrice']",
    "[class*='offer-price']",  "[class*='offerPrice']",
    "[class*='special-price']","[class*='specialPrice']",
    "[class*='discounted-price']",
    "[class*='current-price']", "[class*='sale-price']",
    "[class*='product-price']",
    "[data-price]",
    # broad fallbacks — catch anything with 'price' in class name
    "[class*='price']",
    "[class*='Price']",
    "[class*='amount']",
    "[class*='cost']",
]


# ── Generic name selectors ────────────────────────────────────────────
GENERIC_NAME_SELECTORS = [
    "[itemprop='name']",
    "h1[class*='product']", "h1[class*='title']", "h1[class*='name']",
    ".product-title", ".product-name",
]


# ─────────────────────────────────────────────────────────────────────
async def scrape_product_url(url: str) -> dict[str, Any]:
    """
    Visit a product page URL and extract name, price, image, description.
    Returns a result dict always — never raises.
    """
    from playwright.async_api import async_playwright

    result: dict[str, Any] = {
        "url": url,
        "site": urlparse(url).netloc.replace("www.", ""),
        "name": None,
        "price": None,
        "currency": "INR",
        "image": None,
        "description": None,
        "scraped_at": datetime.utcnow().isoformat(),
        "success": False,
        "error": None,
    }

    domain = result["site"]
    site_sel = _site_selectors_for(domain)

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            ctx = await browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/122.0.0.0 Safari/537.36"
                ),
                extra_http_headers=HEADERS,
                viewport={"width": 1280, "height": 800},
            )
            page = await ctx.new_page()

            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=35000)
            except Exception:
                await page.goto(url, wait_until="commit", timeout=35000)

            await page.wait_for_timeout(2500)

            # ── Strategy 1: JSON-LD ──────────────────────────────────
            jsonld = await page.evaluate(_JSONLD_JS)
            if jsonld:
                result["name"]        = jsonld.get("name")
                result["price"]       = _parse_price(str(jsonld.get("price", "")))
                result["currency"]    = jsonld.get("currency") or "INR"
                result["image"]       = jsonld.get("image")
                result["description"] = jsonld.get("description")

            # ── Strategy 2: Open Graph / meta tags ───────────────────
            if not result["name"]:
                result["name"] = await _first_meta(page, [
                    'meta[property="og:title"]',
                    'meta[name="twitter:title"]',
                    'meta[property="product:title"]',
                ])
            if not result["image"]:
                result["image"] = await _first_meta(page, [
                    'meta[property="og:image"]',
                    'meta[name="twitter:image"]',
                ])
            if not result["description"]:
                result["description"] = await _first_meta(page, [
                    'meta[property="og:description"]',
                    'meta[name="description"]',
                ])

            # price from meta tags
            if not result["price"]:
                price_str = await _first_meta(page, [
                    'meta[property="product:price:amount"]',
                    'meta[property="og:price:amount"]',
                    'meta[name="twitter:data1"]',
                ])
                if price_str:
                    result["price"] = _parse_price(price_str)

            # ── Strategy 3: site-specific selectors ──────────────────
            if not result["name"] and site_sel.get("name"):
                result["name"] = await _first_text(page, site_sel["name"])
            if not result["price"] and site_sel.get("price"):
                raw = await _first_text_or_attr(page, site_sel["price"])
                result["price"] = _parse_price(raw)
            if not result["image"] and site_sel.get("image"):
                result["image"] = await _first_img_src(page, site_sel["image"])

            # ── Strategy 4: generic selectors ────────────────────────
            if not result["name"]:
                result["name"] = await _first_text(page, GENERIC_NAME_SELECTORS)
            if not result["price"]:
                raw = await _first_text_or_attr(page, GENERIC_PRICE_SELECTORS)
                result["price"] = _parse_price(raw)

            # ── Strategy 5: page-title fallback for name ─────────────
            if not result["name"]:
                t = await page.title()
                result["name"] = t.split("|")[0].split("-")[0].split("–")[0].strip() or t

            result["success"] = bool(result["name"])
            await browser.close()

    except Exception as exc:
        logger.error("Failed to scrape %s: %s", url, exc)
        result["error"] = str(exc)

    return result


async def scrape_multiple_urls(urls: list[str]) -> list[dict[str, Any]]:
    """Scrape multiple product URLs concurrently (max 5 at a time)."""
    sem = asyncio.Semaphore(5)

    async def _bounded(url: str) -> dict[str, Any]:
        async with sem:
            return await scrape_product_url(url)

    return list(await asyncio.gather(*[_bounded(u) for u in urls]))


# ─── helpers ──────────────────────────────────────────────────────────

def _site_selectors_for(domain: str) -> dict[str, list[str]]:
    for key, sels in SITE_SELECTORS.items():
        if key in domain:
            return sels
    return {}


async def _first_meta(page, selectors: list[str]) -> Optional[str]:
    for sel in selectors:
        try:
            el = await page.query_selector(sel)
            if el:
                val = await el.get_attribute("content")
                if val and val.strip():
                    return val.strip()
        except Exception:
            pass
    return None


async def _first_text(page, selectors: list[str]) -> Optional[str]:
    for sel in selectors:
        try:
            el = await page.query_selector(sel)
            if el:
                txt = (await el.inner_text()).strip()
                if txt:
                    return txt
        except Exception:
            pass
    return None


async def _first_text_or_attr(page, selectors: list[str]) -> Optional[str]:
    """Try inner_text first, then content/data-price attribute."""
    for sel in selectors:
        try:
            el = await page.query_selector(sel)
            if el:
                for attr in ("content", "data-price", "value"):
                    val = await el.get_attribute(attr)
                    if val and re.search(r"\d", val):
                        return val.strip()
                txt = (await el.inner_text()).strip()
                if txt and re.search(r"\d", txt):
                    return txt
        except Exception:
            pass
    return None


async def _first_img_src(page, selectors: list[str]) -> Optional[str]:
    for sel in selectors:
        try:
            el = await page.query_selector(sel)
            if el:
                for attr in ("src", "data-src", "data-lazy-src"):
                    val = await el.get_attribute(attr)
                    if val and val.startswith("http"):
                        return val
        except Exception:
            pass
    return None


def _parse_price(text: Optional[str]) -> Optional[float]:
    """Extract a float price from a text fragment."""
    if not text:
        return None
    # Strip currency symbols, commas, whitespace
    cleaned = re.sub(r"[₹$€£¥₩\s,]", "", text)
    match = re.search(r"\d+\.?\d*", cleaned)
    if match:
        try:
            return float(match.group())
        except ValueError:
            pass
    return None


# ── JavaScript run inside the page to pull JSON-LD Product data ───────
_JSONLD_JS = """() => {
    const scripts = document.querySelectorAll('script[type="application/ld+json"]');
    for (const s of scripts) {
        try {
            const raw = s.textContent || '';
            const data = JSON.parse(raw);
            const items = Array.isArray(data) ? data : [data];
            for (const item of items) {
                let product = null;
                if (item['@type'] === 'Product') {
                    product = item;
                } else if (Array.isArray(item['@graph'])) {
                    product = item['@graph'].find(g => g['@type'] === 'Product');
                }
                if (product) {
                    const offer = product.offers
                        ? (Array.isArray(product.offers) ? product.offers[0] : product.offers)
                        : {};
                    let img = product.image;
                    if (Array.isArray(img)) img = img[0];
                    if (img && typeof img === 'object') img = img.url || img.contentUrl;
                    return {
                        name: product.name || null,
                        price: offer.price || offer.lowPrice || null,
                        currency: offer.priceCurrency || null,
                        image: img || null,
                        description: product.description || null,
                    };
                }
            }
        } catch(e) {}
    }
    return null;
}"""
