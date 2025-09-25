"""
Unit tests for PriceComparator.
"""

import pytest
from comparator import PriceComparator
from datetime import datetime


class TestPriceComparator:
    """Test cases for PriceComparator class."""
    
    @pytest.fixture
    def sample_config(self):
        """Sample configuration for testing."""
        return {
            'matching_threshold': 75,
            'weight_name': 0.7,
            'weight_brand': 0.2,
            'weight_category': 0.1,
            'exact_match_bonus': 10
        }
    
    @pytest.fixture
    def comparator(self, sample_config):
        """Create PriceComparator instance."""
        return PriceComparator(sample_config)
    
    @pytest.fixture
    def sample_farm2bag_products(self):
        """Sample Farm2bag products for testing."""
        return [
            {
                'name': 'Organic Tomatoes',
                'normalized_name': 'organic tomatoes',
                'price': 45.0,
                'price_per_unit': 45.0,
                'normalized_unit': 'kg',
                'normalized_size': 1.0,
                'normalized_brand': 'farm2bag',
                'normalized_category': 'vegetables'
            },
            {
                'name': 'Fresh Bananas',
                'normalized_name': 'fresh bananas',
                'price': 35.0,
                'price_per_unit': 2.92,  # 35/12
                'normalized_unit': 'piece',
                'normalized_size': 12.0,
                'normalized_brand': 'farm2bag',
                'normalized_category': 'fruits'
            }
        ]
    
    @pytest.fixture
    def sample_competitor_products(self):
        """Sample competitor products for testing."""
        return {
            'bigbasket': [
                {
                    'name': 'Premium Organic Tomatoes',
                    'normalized_name': 'premium organic tomatoes',
                    'price': 50.0,
                    'price_per_unit': 50.0,
                    'normalized_unit': 'kg',
                    'normalized_size': 1.0,
                    'normalized_brand': 'bigbasket',
                    'normalized_category': 'vegetables',
                    'comparison_site': 'bigbasket'
                },
                {
                    'name': 'Yellow Bananas Fresh',
                    'normalized_name': 'yellow bananas fresh',
                    'price': 40.0,
                    'price_per_unit': 3.33,  # 40/12
                    'normalized_unit': 'piece',
                    'normalized_size': 12.0,
                    'normalized_brand': 'bigbasket',
                    'normalized_category': 'fruits',
                    'comparison_site': 'bigbasket'
                }
            ],
            'jiomart': [
                {
                    'name': 'Tomatoes Red Fresh',
                    'normalized_name': 'tomatoes red fresh',
                    'price': 42.0,
                    'price_per_unit': 42.0,
                    'normalized_unit': 'kg',
                    'normalized_size': 1.0,
                    'normalized_brand': 'jiomart',
                    'normalized_category': 'vegetables',
                    'comparison_site': 'jiomart'
                }
            ]
        }
    
    def test_find_matches_exact_match(self, comparator, sample_competitor_products):
        """Test finding matches with exact name match."""
        target_product = {
            'normalized_name': 'organic tomatoes',
            'normalized_brand': 'farm2bag',
            'normalized_category': 'vegetables'
        }
        
        all_competitors = []
        for products in sample_competitor_products.values():
            all_competitors.extend(products)
        
        # Add exact match for testing
        exact_match = {
            'normalized_name': 'organic tomatoes',
            'normalized_brand': 'test_brand',
            'normalized_category': 'vegetables',
            'price': 48.0,
            'comparison_site': 'test_site'
        }
        all_competitors.append(exact_match)
        
        matches = comparator.find_matches(target_product, all_competitors)
        
        # Should find matches
        assert len(matches) > 0
        
        # Exact match should be first (highest score due to bonus)
        assert matches[0]['normalized_name'] == 'organic tomatoes'
        assert matches[0]['similarity_score'] > 90  # High score due to exact match bonus
    
    def test_find_matches_no_matches(self, comparator, sample_competitor_products):
        """Test finding matches when no good matches exist."""
        target_product = {
            'normalized_name': 'completely different product',
            'normalized_brand': 'unknown',
            'normalized_category': 'unknown'
        }
        
        all_competitors = []
        for products in sample_competitor_products.values():
            all_competitors.extend(products)
        
        matches = comparator.find_matches(target_product, all_competitors)
        
        # Should not find matches above threshold
        assert len(matches) == 0
    
    def test_calculate_price_difference(self, comparator):
        """Test price difference calculation."""
        farm2bag_product = {
            'name': 'Tomatoes',
            'price': 45.0,
            'price_per_unit': 45.0
        }
        
        competitor_product = {
            'name': 'Premium Tomatoes',
            'price': 50.0,
            'price_per_unit': 50.0,
            'comparison_site': 'bigbasket',
            'similarity_score': 85.0
        }
        
        result = comparator.calculate_price_difference(farm2bag_product, competitor_product)
        
        # Check structure
        assert 'farm2bag_product' in result
        assert 'competitor_product' in result
        assert 'price_comparison' in result
        assert 'unit_price_comparison' in result
        
        # Check price comparison values
        price_comp = result['price_comparison']
        assert price_comp['farm2bag_price'] == 45.0
        assert price_comp['competitor_price'] == 50.0
        assert price_comp['absolute_difference'] == -5.0  # Farm2bag is cheaper
        assert price_comp['percentage_difference'] == -10.0  # (45-50)/50*100
        assert price_comp['farm2bag_cheaper'] == True
        assert price_comp['price_advantage'] == 'Farm2bag'
        
        # Check unit price comparison
        unit_comp = result['unit_price_comparison']
        assert unit_comp['per_unit_difference'] == -5.0
        assert unit_comp['better_unit_price'] == 'Farm2bag'
    
    def test_calculate_price_difference_competitor_cheaper(self, comparator):
        """Test price difference when competitor is cheaper."""
        farm2bag_product = {
            'name': 'Tomatoes',
            'price': 55.0,
            'price_per_unit': 55.0
        }
        
        competitor_product = {
            'name': 'Premium Tomatoes',
            'price': 50.0,
            'price_per_unit': 50.0,
            'comparison_site': 'bigbasket',
            'similarity_score': 85.0
        }
        
        result = comparator.calculate_price_difference(farm2bag_product, competitor_product)
        
        price_comp = result['price_comparison']
        assert price_comp['absolute_difference'] == 5.0  # Farm2bag is more expensive
        assert price_comp['percentage_difference'] == 10.0  # (55-50)/50*100
        assert price_comp['farm2bag_cheaper'] == False
        assert price_comp['price_advantage'] == 'Competitor'
    
    def test_compare_products_complete(self, comparator, sample_farm2bag_products, sample_competitor_products):
        """Test complete product comparison."""
        results = comparator.compare_products(sample_farm2bag_products, sample_competitor_products)
        
        # Check structure
        assert 'matches' in results
        assert 'no_matches' in results
        assert 'statistics' in results
        assert 'price_analysis' in results
        
        # Should find some matches
        assert len(results['matches']) > 0
        
        # Check match structure
        match = results['matches'][0]
        assert 'farm2bag_product' in match
        assert 'competitor_product' in match
        assert 'price_comparison' in match
        assert 'all_matches' in match  # Top matches
    
    def test_calculate_statistics_empty(self, comparator):
        """Test statistics calculation with empty matches."""
        stats = comparator.calculate_statistics([])
        
        assert stats['total_matches'] == 0
        assert stats['farm2bag_cheaper_count'] == 0
        assert stats['competitor_cheaper_count'] == 0
        assert stats['average_price_difference_percentage'] == 0
    
    def test_calculate_statistics_with_matches(self, comparator):
        """Test statistics calculation with sample matches."""
        matches = [
            {
                'price_comparison': {
                    'percentage_difference': -10.0,  # Farm2bag cheaper
                    'farm2bag_cheaper': True
                }
            },
            {
                'price_comparison': {
                    'percentage_difference': 5.0,   # Competitor cheaper
                    'farm2bag_cheaper': False
                }
            },
            {
                'price_comparison': {
                    'percentage_difference': -2.0,  # Farm2bag cheaper
                    'farm2bag_cheaper': True
                }
            }
        ]
        
        stats = comparator.calculate_statistics(matches)
        
        assert stats['total_matches'] == 3
        assert stats['farm2bag_cheaper_count'] == 2
        assert stats['competitor_cheaper_count'] == 1
        assert stats['farm2bag_cheaper_percentage'] == (2/3) * 100
        assert stats['average_price_difference_percentage'] == (-10.0 + 5.0 + -2.0) / 3
        assert stats['max_savings_percentage'] == -10.0  # Most negative = biggest savings
        assert stats['min_savings_percentage'] == 5.0
        assert stats['median_price_difference'] == -2.0
    
    def test_analyze_pricing_empty(self, comparator):
        """Test pricing analysis with empty matches."""
        analysis = comparator.analyze_pricing([])
        
        assert analysis == {}
    
    def test_analyze_pricing_with_data(self, comparator):
        """Test pricing analysis with sample data."""
        matches = [
            {
                'farm2bag_product': {'normalized_category': 'vegetables'},
                'competitor_product': {'comparison_site': 'bigbasket'},
                'price_comparison': {'percentage_difference': -10.0, 'farm2bag_cheaper': True},
                'similarity_score': 85.0
            },
            {
                'farm2bag_product': {'normalized_category': 'fruits'},
                'competitor_product': {'comparison_site': 'jiomart'},
                'price_comparison': {'percentage_difference': 5.0, 'farm2bag_cheaper': False},
                'similarity_score': 80.0
            }
        ]
        
        analysis = comparator.analyze_pricing(matches)
        
        assert 'by_category' in analysis
        assert 'by_site' in analysis
        assert 'overall_competitiveness' in analysis
        
        # Check overall competitiveness
        overall = analysis['overall_competitiveness']
        assert 'avg_price_difference' in overall
        assert 'competitive_categories' in overall


if __name__ == "__main__":
    pytest.main([__file__])