"""
Unit tests for ProductNormalizer.
"""

import pytest
from normalizer import ProductNormalizer


class TestProductNormalizer:
    """Test cases for ProductNormalizer class."""
    
    @pytest.fixture
    def sample_rules(self):
        """Sample normalization rules for testing."""
        return {
            'unit_mappings': {
                'kilogram': 'kg',
                'grams': 'g',
                'litre': 'liter',
                'pieces': 'piece'
            },
            'brand_aliases': {
                'farm2bag': ['farm2bag', 'farm 2 bag', 'farm2bag fresh'],
                'amul': ['amul', 'amul dairy']
            },
            'category_mappings': {
                'vegetables': 'vegetables',
                'fresh vegetables': 'vegetables',
                'fruits': 'fruits',
                'dairy products': 'dairy'
            },
            'name_cleaners': [
                {
                    'pattern': r'\b(fresh|organic|premium)\b',
                    'replacement': ''
                },
                {
                    'pattern': r'\s+',
                    'replacement': ' '
                }
            ],
            'size_patterns': [
                {
                    'pattern': r'(\d+(?:\.\d+)?)\s*g(?:rams?)?',
                    'unit_type': 'weight',
                    'conversion': 0.001
                },
                {
                    'pattern': r'(\d+(?:\.\d+)?)\s*kg',
                    'unit_type': 'weight',
                    'conversion': 1.0
                },
                {
                    'pattern': r'(\d+)\s*(?:piece|pcs?)',
                    'unit_type': 'count',
                    'conversion': 1.0
                }
            ]
        }
    
    @pytest.fixture
    def normalizer(self, sample_rules):
        """Create ProductNormalizer instance with sample rules."""
        return ProductNormalizer(sample_rules)
    
    def test_normalize_name_basic(self, normalizer):
        """Test basic name normalization."""
        # Test removing common promotional words
        result = normalizer.normalize_name("Fresh Organic Premium Tomatoes")
        assert result == "tomatoes"
        
        # Test whitespace normalization
        result = normalizer.normalize_name("Red   Onions    Fresh")
        assert result == "red onions"
        
        # Test case normalization
        result = normalizer.normalize_name("BASMATI RICE")
        assert result == "basmati rice"
    
    def test_normalize_name_empty_input(self, normalizer):
        """Test name normalization with empty input."""
        assert normalizer.normalize_name("") == ""
        assert normalizer.normalize_name(None) == ""
    
    def test_normalize_brand(self, normalizer):
        """Test brand normalization with aliases."""
        # Test exact match
        assert normalizer.normalize_brand("farm2bag") == "farm2bag"
        
        # Test alias mapping
        assert normalizer.normalize_brand("Farm 2 Bag") == "farm2bag"
        assert normalizer.normalize_brand("AMUL DAIRY") == "amul"
        
        # Test unknown brand
        assert normalizer.normalize_brand("Unknown Brand") == "unknown brand"
        
        # Test empty brand
        assert normalizer.normalize_brand("") == ""
    
    def test_normalize_category(self, normalizer):
        """Test category normalization."""
        # Test direct mapping
        assert normalizer.normalize_category("vegetables") == "vegetables"
        assert normalizer.normalize_category("fresh vegetables") == "vegetables"
        
        # Test case insensitive
        assert normalizer.normalize_category("FRUITS") == "fruits"
        
        # Test unknown category
        assert normalizer.normalize_category("unknown") == "unknown"
        
        # Test empty category
        assert normalizer.normalize_category("") == "general"
    
    def test_normalize_unit_and_size(self, normalizer):
        """Test unit and size normalization."""
        # Test weight units
        unit, size = normalizer.normalize_unit_and_size("kilogram", "2")
        assert unit == "kg"
        assert size == 2.0
        
        # Test volume units  
        unit, size = normalizer.normalize_unit_and_size("litre", "1.5")
        assert unit == "liter"
        assert size == 1.5
        
        # Test count units
        unit, size = normalizer.normalize_unit_and_size("pieces", "6")
        assert unit == "piece"
        assert size == 6.0
        
        # Test empty inputs
        unit, size = normalizer.normalize_unit_and_size("", "")
        assert unit == "piece"
        assert size == 1.0
    
    def test_extract_size_value(self, normalizer):
        """Test size value extraction from strings."""
        # Test gram extraction with conversion
        result = normalizer.extract_size_value("500g", "weight")
        assert result == 0.5  # 500g = 0.5kg
        
        # Test kilogram extraction
        result = normalizer.extract_size_value("2kg", "weight")
        assert result == 2.0
        
        # Test piece extraction
        result = normalizer.extract_size_value("6 pieces", "count")
        assert result == 6.0
        
        # Test complex size string
        result = normalizer.extract_size_value("Pack of 12 pcs", "count")
        assert result == 12.0
        
        # Test fallback for unparseable size
        result = normalizer.extract_size_value("large", "weight")
        assert result == 1.0
    
    def test_calculate_price_per_unit(self, normalizer):
        """Test price per unit calculation."""
        # Normal calculation
        result = normalizer.calculate_price_per_unit(100.0, "kg", 2.0)
        assert result == 50.0
        
        # Zero size handling
        result = normalizer.calculate_price_per_unit(100.0, "kg", 0.0)
        assert result == 0.0
        
        # Zero price handling
        result = normalizer.calculate_price_per_unit(0.0, "kg", 2.0)
        assert result == 0.0
    
    def test_normalize_product_complete(self, normalizer):
        """Test complete product normalization."""
        product = {
            'name': 'Fresh Organic Tomatoes Premium',
            'price': 100.0,
            'unit': 'kilogram',
            'size': '2',
            'category': 'fresh vegetables',
            'brand': 'Farm 2 Bag'
        }
        
        result = normalizer.normalize_product(product)
        
        # Check all normalized fields are present
        assert 'normalized_name' in result
        assert 'normalized_unit' in result
        assert 'normalized_size' in result
        assert 'normalized_brand' in result
        assert 'normalized_category' in result
        assert 'price_per_unit' in result
        
        # Check specific values
        assert result['normalized_name'] == 'tomatoes'
        assert result['normalized_unit'] == 'kg'
        assert result['normalized_size'] == 2.0
        assert result['normalized_brand'] == 'farm2bag'
        assert result['normalized_category'] == 'vegetables'
        assert result['price_per_unit'] == 50.0  # 100/2
    
    def test_normalize_batch(self, normalizer):
        """Test batch normalization of products."""
        products = [
            {
                'name': 'Fresh Tomatoes',
                'price': 50.0,
                'unit': 'kg',
                'size': '1',
                'category': 'vegetables',
                'brand': 'farm2bag'
            },
            {
                'name': 'Organic Bananas',
                'price': 60.0,
                'unit': 'pieces',
                'size': '12',
                'category': 'fruits', 
                'brand': 'amul'
            }
        ]
        
        result = normalizer.normalize_batch(products)
        
        assert len(result) == 2
        assert all('normalized_name' in product for product in result)
        assert result[0]['normalized_name'] == 'tomatoes'
        assert result[1]['normalized_name'] == 'bananas'
    
    def test_normalize_batch_with_errors(self, normalizer):
        """Test batch normalization with some products causing errors."""
        products = [
            {
                'name': 'Good Product',
                'price': 50.0,
                'unit': 'kg',
                'size': '1',
                'category': 'vegetables',
                'brand': 'farm2bag'
            },
            {
                # Missing required fields - should not crash
                'name': 'Incomplete Product'
            }
        ]
        
        result = normalizer.normalize_batch(products)
        
        # Should return 2 products (one good, one with minimal normalization)
        assert len(result) == 2
        assert result[0]['normalized_name'] == 'good product'
        assert result[1]['normalized_name'] == 'incomplete product'
    
    def test_price_parsing_edge_cases(self, normalizer):
        """Test price parsing with various formats."""
        # Test currency symbols
        assert normalizer._parse_price("₹45.50") == 45.50
        assert normalizer._parse_price("$25.99") == 25.99
        
        # Test with commas
        assert normalizer._parse_price("1,250.00") == 1250.0
        
        # Test with extra text
        assert normalizer._parse_price("Price: ₹99.99 only") == 99.99
        
        # Test invalid prices
        assert normalizer._parse_price("Invalid") == 0.0
        assert normalizer._parse_price("") == 0.0
        assert normalizer._parse_price(None) == 0.0


if __name__ == "__main__":
    pytest.main([__file__])