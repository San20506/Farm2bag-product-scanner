"""
Playwright fetcher for JavaScript-heavy websites.
"""

from playwright.async_api import async_playwright, Browser, Page
from typing import Dict, Any, Optional, List
from loguru import logger
import asyncio


class PlaywrightFetcher:
    """
    Browser-based fetcher using Playwright for JavaScript-heavy websites.
    Good for sites that require interaction or JavaScript execution.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize Playwright fetcher.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.browser: Optional[Browser] = None
        self.playwright = None
        
        # Configuration
        self.headless = self.config.get('headless', True)
        self.timeout = self.config.get('timeout', 30000)  # 30 seconds
        self.user_agent = self.config.get('user_agent',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        self.viewport = self.config.get('viewport', {'width': 1920, 'height': 1080})
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
    
    async def start(self):
        """Start the browser."""
        if not self.playwright:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=self.headless,
                args=['--no-sandbox', '--disable-setuid-sandbox']
            )
            logger.info("Playwright browser started")
    
    async def close(self):
        """Close the browser and cleanup."""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        logger.info("Playwright browser closed")
    
    async def create_page(self, **kwargs) -> Page:
        """
        Create a new page with default configuration.
        
        Returns:
            Page object
        """
        if not self.browser:
            await self.start()
        
        context = await self.browser.new_context(
            user_agent=self.user_agent,
            viewport=self.viewport,
            **kwargs
        )
        
        page = await context.new_page()
        page.set_default_timeout(self.timeout)
        
        return page
    
    async def fetch_page(self, url: str, wait_for: Optional[str] = None, **kwargs) -> Page:
        """
        Navigate to a URL and return the page.
        
        Args:
            url: URL to navigate to
            wait_for: CSS selector to wait for before returning
            **kwargs: Additional arguments for page.goto()
            
        Returns:
            Page object after navigation
        """
        page = await self.create_page()
        
        try:
            logger.debug(f"Navigating to: {url}")
            await page.goto(url, **kwargs)
            
            if wait_for:
                await page.wait_for_selector(wait_for, timeout=self.timeout)
            
            logger.debug(f"Successfully loaded: {url}")
            return page
            
        except Exception as e:
            await page.close()
            logger.error(f"Failed to load {url}: {e}")
            raise
    
    async def fetch_content(self, url: str, wait_for: Optional[str] = None) -> str:
        """
        Fetch page content as HTML.
        
        Args:
            url: URL to fetch
            wait_for: CSS selector to wait for
            
        Returns:
            HTML content
        """
        page = await self.fetch_page(url, wait_for)
        try:
            content = await page.content()
            return content
        finally:
            await page.close()
    
    async def fetch_json_from_api(self, page: Page, api_url: str) -> Dict[str, Any]:
        """
        Intercept and return JSON response from an API call.
        
        Args:
            page: Page object to use for interception
            api_url: URL pattern to intercept
            
        Returns:
            JSON response data
        """
        json_response = {}
        
        async def handle_response(response):
            if api_url in response.url:
                json_response.update(await response.json())
        
        page.on("response", handle_response)
        
        # Wait for the API call
        await asyncio.sleep(2)
        
        return json_response
    
    async def scroll_to_bottom(self, page: Page, delay: float = 1.0):
        """
        Scroll to bottom of page to trigger lazy loading.
        
        Args:
            page: Page object
            delay: Delay between scroll steps
        """
        last_height = await page.evaluate("document.body.scrollHeight")
        
        while True:
            # Scroll to bottom
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(delay)
            
            # Check if new content loaded
            new_height = await page.evaluate("document.body.scrollHeight")
            if new_height == last_height:
                break
            
            last_height = new_height
            logger.debug("Scrolled and waiting for more content...")
    
    async def extract_products_from_page(self, page: Page, selectors: Dict[str, str]) -> List[Dict[str, str]]:
        """
        Extract product information using CSS selectors.
        
        Args:
            page: Page object
            selectors: Dictionary of CSS selectors for product fields
            
        Returns:
            List of product data dictionaries
        """
        products = []
        
        try:
            # Wait for products to load
            await page.wait_for_selector(selectors.get('product_container', '.product'), timeout=10000)
            
            # Get all product containers
            product_elements = await page.query_selector_all(selectors.get('product_container', '.product'))
            
            for element in product_elements:
                product_data = {}
                
                for field, selector in selectors.items():
                    if field == 'product_container':
                        continue
                    
                    try:
                        if field.endswith('_attribute'):
                            # Handle attributes like data-price
                            attr_name = field.replace('_attribute', '')
                            value = await element.get_attribute(selector)
                            if value:
                                product_data[attr_name] = value
                        else:
                            # Handle text content
                            field_element = await element.query_selector(selector)
                            if field_element:
                                text = await field_element.inner_text()
                                product_data[field] = text.strip()
                    except Exception as e:
                        logger.debug(f"Failed to extract {field}: {e}")
                
                if product_data:
                    products.append(product_data)
            
            logger.info(f"Extracted {len(products)} products from page")
            
        except Exception as e:
            logger.error(f"Failed to extract products: {e}")
        
        return products