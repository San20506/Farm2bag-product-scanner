"""Config-driven scraper that performs live network scraping using sites.yml."""

from typing import List, Dict, Any, Optional, Tuple
from urllib.parse import urljoin, quote_plus
import asyncio
import re

import requests
from bs4 import BeautifulSoup

from .base_scraper import ScraperBase


class GenericScraper(ScraperBase):
    """
    Generic scraper implementation driven by site configuration.
    Reads selectors and category paths from sites.yml and performs live scraping.
    """
    
    def __init__(self, site_name: str, config: Dict[str, Any]):
        super().__init__(site_name, config)
        self.categories_config = config.get('categories', [])
        self.use_playwright = config.get('use_playwright', False)
        
    async def scrape_products(
        self,
        categories: Optional[List[str]] = None,
        product_query: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Scrape products from configured category pages.
        If product_query is provided, returns only the best match from live scraped products.
        """
        raw_products: List[Dict[str, Any]] = []

        if product_query:
            query_url = self._build_search_url(product_query)
            html = await self._fetch_html(query_url)
            if html:
                raw_products.extend(
                    self._extract_products_from_html(
                        html,
                        query_url,
                        "general",
                        product_query=product_query,
                    )
                )
            self.apply_rate_limit()
        else:
            category_paths = self._category_paths()
            target_categories = categories or list(category_paths.keys())

            if not target_categories:
                # Fall back to a single request at base URL when categories are not configured.
                target_categories = ["general"]
                category_paths["general"] = "/"

            for category in target_categories:
                rel_path = category_paths.get(category)
                if rel_path is None:
                    continue

                page_url = urljoin(self.base_url, rel_path)
                html = await self._fetch_html(page_url)
                if not html:
                    continue

                page_products = self._extract_products_from_html(
                    html,
                    page_url,
                    category,
                    product_query=product_query,
                )
                raw_products.extend(page_products)
                self.apply_rate_limit()

        standardized = [self.standardize_product_data(p) for p in raw_products if p.get("name")]

        if product_query:
            best_match = self._best_match(standardized, product_query)
            products = [best_match] if best_match else []
        else:
            products = standardized

        self.log_scraping_stats(len(products))
        return products
    
    async def scrape_product_details(self, product_url: str) -> Dict[str, Any]:
        """
        Scrape detailed information for a single product.
        Returns mock detailed data.
        """
        # Simulate async request delay
        await asyncio.sleep(0.2)
        
        # Mock detailed product data
        return {
            'description': f'High quality product from {self.site_name}',
            'ingredients': ['Natural ingredients'],
            'nutritional_info': {'calories': '100 per serving'},
            'reviews_count': 25,
            'average_rating': 4.5,
            'stock_quantity': 100
        }

    def _category_paths(self) -> Dict[str, str]:
        paths: Dict[str, str] = {}
        for entry in self.categories_config:
            if isinstance(entry, dict):
                for key, value in entry.items():
                    if isinstance(key, str) and isinstance(value, str):
                        paths[key] = value
        return paths

    def _build_search_url(self, query: str) -> str:
        encoded = quote_plus(query.strip())
        template = self.config.get("search_url_template")
        if isinstance(template, str) and "{query}" in template:
            return template.format(query=encoded)

        domain = self.base_url.lower()
        if "amazon." in domain:
            return urljoin(self.base_url, f"/s?k={encoded}")
        if "flipkart." in domain:
            return urljoin(self.base_url, f"/search?q={encoded}")
        if "ebay." in domain:
            return urljoin(self.base_url, f"/sch/i.html?_nkw={encoded}")
        if "meesho." in domain:
            return urljoin(self.base_url, f"/search?q={encoded}")

        return urljoin(self.base_url, f"/search?q={encoded}")

    async def _fetch_html(self, url: str) -> Optional[str]:
        if self.use_playwright:
            return await self._fetch_with_playwright(url)
        return await self._fetch_with_requests(url)

    async def _fetch_with_requests(self, url: str) -> Optional[str]:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9",
        }
        headers.update(self.config.get("headers", {}))

        timeout = int(self.config.get("request_timeout", 20))

        def _request() -> Optional[str]:
            try:
                response = requests.get(url, headers=headers, timeout=timeout)
                response.raise_for_status()
                return response.text
            except Exception:
                return None

        return await asyncio.to_thread(_request)

    async def _fetch_with_playwright(self, url: str) -> Optional[str]:
        try:
            from playwright.async_api import async_playwright
        except Exception:
            return await self._fetch_with_requests(url)

        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                await page.wait_for_timeout(1500)
                html = await page.content()
                await browser.close()
                return html
        except Exception:
            return await self._fetch_with_requests(url)

    def _extract_products_from_html(
        self,
        html: str,
        page_url: str,
        category: str,
        product_query: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        soup = BeautifulSoup(html, "html.parser")
        containers = []

        container_selector = self.selectors.get("product_container")
        if container_selector:
            containers = soup.select(container_selector)

        # If container selector fails, parse at page scope as a fallback.
        if not containers:
            containers = [soup]

        products: List[Dict[str, Any]] = []
        for container in containers[:60]:
            name = self._select_text(container, self.selectors.get("name"))
            price = self._select_text(container, self.selectors.get("price"))
            if not name or not price:
                continue

            unit = self._select_text(container, self.selectors.get("unit")) or "piece"
            brand = self._select_text(container, self.selectors.get("brand")) or ""
            image_url = self._select_image(container, self.selectors.get("image")) or ""
            product_url = self._select_link(container) or page_url
            availability_selector = self.selectors.get("availability")
            availability = bool(container.select_one(availability_selector)) if availability_selector else True

            products.append({
                "name": name,
                "price": price,
                "unit": unit,
                "size": "1",
                "category": category,
                "brand": brand,
                "url": urljoin(self.base_url, product_url),
                "image_url": urljoin(self.base_url, image_url) if image_url else "",
                "availability": availability,
            })

        if not products:
            # Fallback: pair global name and price selector matches even without product container mapping.
            name_selector = self.selectors.get("name")
            price_selector = self.selectors.get("price")
            if name_selector and price_selector:
                name_nodes = soup.select(name_selector)[:80]
                price_nodes = soup.select(price_selector)[:80]
                for name_node, price_node in zip(name_nodes, price_nodes):
                    name = re.sub(r"\s+", " ", name_node.get_text(strip=True))
                    price = re.sub(r"\s+", " ", price_node.get_text(strip=True))
                    if not name or not price:
                        continue

                    context = name_node.parent or soup
                    image_url = self._select_image(context, self.selectors.get("image")) or ""
                    link = self._select_link(context) or page_url

                    products.append({
                        "name": name,
                        "price": price,
                        "unit": "piece",
                        "size": "1",
                        "category": category,
                        "brand": "",
                        "url": urljoin(self.base_url, link),
                        "image_url": urljoin(self.base_url, image_url) if image_url else "",
                        "availability": True,
                    })

        if not products and product_query:
            fallback = self._extract_with_query_fallback(soup, page_url, category, product_query)
            if fallback:
                products.append(fallback)

        if not products:
            products = self._extract_with_generic_selectors(soup, page_url, category)

        return products

    def _select_text(self, root: Any, selector: Optional[str]) -> str:
        if not selector:
            return ""
        el = root.select_one(selector)
        if not el:
            return ""
        return re.sub(r"\s+", " ", el.get_text(strip=True))

    def _select_image(self, root: Any, selector: Optional[str]) -> str:
        if not selector:
            return ""
        el = root.select_one(selector)
        if not el:
            return ""
        return el.get("src") or el.get("data-src") or ""

    def _select_link(self, root: Any) -> str:
        link = root.select_one("a[href]")
        if not link:
            return ""
        return link.get("href") or ""

    def _best_match(self, products: List[Dict[str, Any]], product_query: str) -> Optional[Dict[str, Any]]:
        if not products:
            return None

        query = product_query.strip().lower()
        query_tokens = [t for t in re.split(r"\s+", query) if t]

        scored: List[Tuple[int, Dict[str, Any]]] = []
        for product in products:
            name = str(product.get("name", "")).lower()
            if not name:
                continue

            score = 0
            if query in name:
                score += 100

            for token in query_tokens:
                if token in name:
                    score += 20

            if score > 0:
                scored.append((score, product))

        if not scored:
            return None

        scored.sort(key=lambda item: item[0], reverse=True)
        return scored[0][1]

    def _extract_with_query_fallback(
        self,
        soup: BeautifulSoup,
        page_url: str,
        category: str,
        product_query: str,
    ) -> Optional[Dict[str, Any]]:
        query = product_query.strip().lower()
        if not query:
            return None

        candidates = soup.find_all(["div", "li", "article"], limit=1500)
        price_regex = re.compile(r"(?:₹|\$|Rs\.?|USD|EUR|£)\s*(\d{1,6}(?:[.,]\d{1,2})?)", re.IGNORECASE)
        blocked_phrases = [
            "results for",
            "sort by",
            "save this search",
            "related:",
            "filter",
            "shop by",
        ]

        for node in candidates:
            text = re.sub(r"\s+", " ", node.get_text(" ", strip=True))
            low = text.lower()
            if query not in low:
                continue

            if any(phrase in low for phrase in blocked_phrases):
                continue

            if len(text) < 4 or len(text) > 240:
                continue

            explicit_price_node = node.select_one("[class*='price'], [data-testid*='price']")
            if not explicit_price_node:
                continue

            price_source = re.sub(r"\s+", " ", explicit_price_node.get_text(" ", strip=True))

            price_match = price_regex.search(price_source)
            if not price_match:
                continue

            anchor = node.select_one("a[href]")
            image = node.select_one("img[src], img[data-src]")

            name_node = node.select_one("h2, h3, h4, a[title], [class*='title'], [class*='name']")
            name = re.sub(r"\s+", " ", name_node.get_text(" ", strip=True)) if name_node else text
            if "|" in name:
                name = name.split("|")[0].strip()
            if len(name) > 90:
                name = name[:90].strip()

            if any(phrase in name.lower() for phrase in blocked_phrases):
                continue

            return {
                "name": name,
                "price": price_match.group(0),
                "unit": "piece",
                "size": "1",
                "category": category,
                "brand": "",
                "url": urljoin(self.base_url, anchor.get("href")) if anchor else page_url,
                "image_url": (
                    urljoin(self.base_url, image.get("src") or image.get("data-src"))
                    if image else ""
                ),
                "availability": True,
            }

        return None

    def _extract_with_generic_selectors(self, soup: BeautifulSoup, page_url: str, category: str) -> List[Dict[str, Any]]:
        name_selectors = [
            "h2 a span",
            "h3 a",
            "a.s-item__link .s-item__title",
            "div.KzDlHZ",
            "a[title]",
            "[data-testid='x-item-title']",
        ]
        price_selectors = [
            ".a-price-whole",
            ".Nx9bqj",
            ".s-item__price",
            "[data-testid='x-price-primary']",
            "[class*='price']",
        ]

        names: List[str] = []
        prices: List[str] = []

        for selector in name_selectors:
            nodes = soup.select(selector)
            if nodes:
                names = [re.sub(r"\s+", " ", n.get_text(strip=True)) for n in nodes[:80] if n.get_text(strip=True)]
                if names:
                    break

        for selector in price_selectors:
            nodes = soup.select(selector)
            if nodes:
                prices = [re.sub(r"\s+", " ", n.get_text(strip=True)) for n in nodes[:80] if n.get_text(strip=True)]
                if prices:
                    break

        products: List[Dict[str, Any]] = []
        for name, price in zip(names, prices):
            if not name or not price:
                continue
            products.append({
                "name": name,
                "price": price,
                "unit": "piece",
                "size": "1",
                "category": category,
                "brand": "",
                "url": page_url,
                "image_url": "",
                "availability": True,
            })

        return products
