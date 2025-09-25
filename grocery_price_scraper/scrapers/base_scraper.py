"""
Base scraper class that all site-specific scrapers should inherit from.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from loguru import logger
import time
import random


class ScraperBase(ABC):
    """
    Abstract base class for all scrapers.
    
    Provides common functionality like rate limiting, error handling,
    and standardized data structure for scraped products.
    """
    
    def __init__(self, site_name: str, config: Dict[str, Any]):
        """
        Initialize the scraper.
        
        Args:
            site_name: Name of the website being scraped
            config: Configuration dictionary from sites.yml
        """
        self.site_name = site_name
        self.config = config
        self.base_url = config.get('base_url', '')
        self.selectors = config.get('selectors', {})
        self.rate_limit = config.get('rate_limit', 1.0)  # seconds between requests
        
    @abstractmethod
    async def scrape_products(self, categories: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Scrape products from the website.
        
        Args:
            categories: List of product categories to scrape (optional)
            
        Returns:
            List of product dictionaries with standardized structure:
            {
                'name': str,
                'price': float,
                'unit': str,  # e.g., 'kg', 'liter', 'piece'
                'size': str,  # e.g., '1', '500g', '1L'
                'category': str,
                'brand': str,
                'url': str,
                'image_url': str,
                'availability': bool,
                'scraped_at': datetime,
                'site': str
            }
        """
        pass
    
    @abstractmethod
    async def scrape_product_details(self, product_url: str) -> Dict[str, Any]:
        """
        Scrape detailed information for a single product.
        
        Args:
            product_url: URL of the product page
            
        Returns:
            Dictionary with detailed product information
        """
        pass
    
    def apply_rate_limit(self):
        """Apply rate limiting between requests."""
        if self.rate_limit > 0:
            sleep_time = self.rate_limit + random.uniform(0, 0.5)  # Add some jitter
            time.sleep(sleep_time)
    
    def standardize_product_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Standardize raw scraped data into the expected format.
        
        Args:
            raw_data: Raw data from website
            
        Returns:
            Standardized product dictionary
        """
        from datetime import datetime
        
        return {
            'name': raw_data.get('name', '').strip(),
            'price': self._parse_price(raw_data.get('price', '')),
            'unit': raw_data.get('unit', 'piece').lower(),
            'size': raw_data.get('size', '1'),
            'category': raw_data.get('category', 'general'),
            'brand': raw_data.get('brand', '').strip(),
            'url': raw_data.get('url', ''),
            'image_url': raw_data.get('image_url', ''),
            'availability': raw_data.get('availability', True),
            'scraped_at': datetime.now(),
            'site': self.site_name
        }
    
    def _parse_price(self, price_text: str) -> float:
        """
        Parse price from text, handling different formats.
        
        Args:
            price_text: Price string from website
            
        Returns:
            Price as float, 0.0 if parsing fails
        """
        if not price_text:
            return 0.0
        
        try:
            # Remove common currency symbols and whitespace
            cleaned = price_text.replace('₹', '').replace('$', '').replace(',', '').strip()
            
            # Extract numbers (including decimals)
            import re
            match = re.search(r'\d+\.?\d*', cleaned)
            if match:
                return float(match.group())
        except Exception as e:
            logger.warning(f"Failed to parse price '{price_text}': {e}")
        
        return 0.0
    
    def log_scraping_stats(self, products_count: int, errors_count: int = 0):
        """Log scraping statistics."""
        logger.info(f"[{self.site_name}] Scraped {products_count} products, {errors_count} errors")