"""
Farm2bag scraper - Example implementation that returns mock data.
Later can be replaced with actual scraping logic or CSV data loading.
"""

from typing import List, Dict, Any, Optional
from .base_scraper import ScraperBase
from datetime import datetime
import asyncio


class Farm2bagScraper(ScraperBase):
    """
    Farm2bag scraper implementation.
    Currently returns mock data for demonstration purposes.
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__('farm2bag', config)
        
    async def scrape_products(self, categories: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Scrape products from Farm2bag.
        Currently returns mock data.
        """
        # Mock data for demonstration
        mock_products = [
            {
                'name': 'Organic Tomatoes',
                'price': '45.00',
                'unit': 'kg',
                'size': '1',
                'category': 'vegetables',
                'brand': 'Farm2bag Fresh',
                'url': 'https://farm2bag.com/organic-tomatoes',
                'image_url': 'https://farm2bag.com/images/tomatoes.jpg',
                'availability': True
            },
            {
                'name': 'Fresh Bananas',
                'price': '35.00',
                'unit': 'dozen',
                'size': '1',
                'category': 'fruits',
                'brand': 'Farm2bag Fresh',
                'url': 'https://farm2bag.com/fresh-bananas',
                'image_url': 'https://farm2bag.com/images/bananas.jpg',
                'availability': True
            },
            {
                'name': 'Whole Wheat Bread',
                'price': '25.00',
                'unit': 'piece',
                'size': '400g',
                'category': 'bakery',
                'brand': 'Farm2bag Bakery',
                'url': 'https://farm2bag.com/wheat-bread',
                'image_url': 'https://farm2bag.com/images/bread.jpg',
                'availability': True
            },
            {
                'name': 'Fresh Milk',
                'price': '28.00',
                'unit': 'liter',
                'size': '1',
                'category': 'dairy',
                'brand': 'Farm2bag Dairy',
                'url': 'https://farm2bag.com/fresh-milk',
                'image_url': 'https://farm2bag.com/images/milk.jpg',
                'availability': True
            },
            {
                'name': 'Basmati Rice',
                'price': '120.00',
                'unit': 'kg',
                'size': '1',
                'category': 'grains',
                'brand': 'Farm2bag Premium',
                'url': 'https://farm2bag.com/basmati-rice',
                'image_url': 'https://farm2bag.com/images/rice.jpg',
                'availability': True
            },
            {
                'name': 'Red Onions',
                'price': '30.00',
                'unit': 'kg',
                'size': '1',
                'category': 'vegetables',
                'brand': 'Farm2bag Fresh',
                'url': 'https://farm2bag.com/red-onions',
                'image_url': 'https://farm2bag.com/images/onions.jpg',
                'availability': True
            }
        ]
        
        # Simulate async scraping delay
        await asyncio.sleep(0.5)
        
        # Convert mock data to standardized format
        products = []
        for mock_product in mock_products:
            if categories and mock_product['category'] not in categories:
                continue
            products.append(self.standardize_product_data(mock_product))
        
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
            'description': 'High quality product from Farm2bag',
            'ingredients': ['Natural ingredients'],
            'nutritional_info': {'calories': '100 per serving'},
            'reviews_count': 25,
            'average_rating': 4.5,
            'stock_quantity': 100
        }