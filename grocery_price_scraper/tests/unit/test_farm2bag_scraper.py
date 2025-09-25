"""
Unit tests for Farm2bagScraper.
"""

import pytest
import asyncio
from scrapers import Farm2bagScraper


class TestFarm2bagScraper:
    """Test cases for Farm2bagScraper class."""
    
    @pytest.fixture
    def scraper_config(self):
        """Sample configuration for Farm2bag scraper."""
        return {
            'base_url': 'https://farm2bag.com',
            'rate_limit': 0.1,  # Fast for testing
            'selectors': {
                'product_container': '.product',
                'name': '.product-name',
                'price': '.price'
            }
        }
    
    @pytest.fixture
    def scraper(self, scraper_config):
        """Create Farm2bagScraper instance."""
        return Farm2bagScraper(scraper_config)
    
    @pytest.mark.asyncio
    async def test_scraper_initialization(self, scraper):
        """Test scraper initialization."""
        assert scraper.site_name == 'farm2bag'
        assert scraper.base_url == 'https://farm2bag.com'
        assert scraper.rate_limit == 0.1
    
    @pytest.mark.asyncio
    async def test_scrape_products_no_categories(self, scraper):
        """Test scraping products without category filter."""
        products = await scraper.scrape_products()
        
        # Should return mock products
        assert len(products) > 0
        
        # Check product structure
        for product in products:
            assert 'name' in product
            assert 'price' in product
            assert 'site' in product
            assert 'scraped_at' in product
            assert product['site'] == 'farm2bag'
            assert isinstance(product['price'], float)
    
    @pytest.mark.asyncio
    async def test_scrape_products_with_categories(self, scraper):
        """Test scraping products with category filter."""
        products = await scraper.scrape_products(['vegetables'])
        
        # Should return only vegetables
        vegetable_products = [p for p in products if p['category'] == 'vegetables']
        assert len(vegetable_products) > 0
        
        # Should not contain fruits
        fruit_products = [p for p in products if p['category'] == 'fruits']
        assert len(fruit_products) == 0
    
    @pytest.mark.asyncio
    async def test_scrape_multiple_categories(self, scraper):
        """Test scraping multiple categories."""
        products = await scraper.scrape_products(['vegetables', 'fruits'])
        
        # Should return products from both categories
        categories = {p['category'] for p in products}
        assert 'vegetables' in categories
        assert 'fruits' in categories
    
    @pytest.mark.asyncio
    async def test_scrape_product_details(self, scraper):
        """Test scraping individual product details."""
        details = await scraper.scrape_product_details('https://farm2bag.com/test-product')
        
        # Should return mock detailed data
        assert 'description' in details
        assert 'reviews_count' in details
        assert 'average_rating' in details
        assert isinstance(details['reviews_count'], int)
        assert isinstance(details['average_rating'], (int, float))
    
    @pytest.mark.asyncio
    async def test_product_data_standardization(self, scraper):
        """Test that scraped data is properly standardized."""
        products = await scraper.scrape_products()
        
        for product in products:
            # Check required fields are present
            required_fields = ['name', 'price', 'unit', 'size', 'category', 
                             'brand', 'url', 'availability', 'scraped_at', 'site']
            for field in required_fields:
                assert field in product, f"Missing field: {field}"
            
            # Check data types
            assert isinstance(product['price'], float)
            assert isinstance(product['availability'], bool)
            assert product['site'] == 'farm2bag'
    
    def test_price_parsing(self, scraper):
        """Test price parsing functionality."""
        # Test various price formats
        assert scraper._parse_price('₹45.50') == 45.50
        assert scraper._parse_price('45') == 45.0
        assert scraper._parse_price('₹1,250.00') == 1250.0
        assert scraper._parse_price('') == 0.0
        assert scraper._parse_price('invalid') == 0.0
    
    def test_standardize_product_data(self, scraper):
        """Test product data standardization."""
        raw_data = {
            'name': '  Fresh Tomatoes  ',
            'price': '₹45.50',
            'unit': 'KG',
            'size': '1',
            'category': 'Vegetables',
            'brand': '  Farm2bag  ',
            'url': 'https://farm2bag.com/tomatoes',
            'availability': 'true'
        }
        
        standardized = scraper.standardize_product_data(raw_data)
        
        assert standardized['name'] == 'Fresh Tomatoes'
        assert standardized['price'] == 45.50
        assert standardized['unit'] == 'kg'  # Lowercase
        assert standardized['category'] == 'Vegetables'
        assert standardized['brand'] == 'Farm2bag'
        assert standardized['site'] == 'farm2bag'
        assert 'scraped_at' in standardized
    
    @pytest.mark.asyncio
    async def test_rate_limiting(self, scraper):
        """Test that rate limiting is applied."""
        # This test checks that rate limiting doesn't crash
        # Actual timing would be hard to test reliably
        scraper.apply_rate_limit()
        # Should complete without error
        assert True


if __name__ == "__main__":
    pytest.main([__file__])