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
    def sample_products_by_site(self):
        """Sample products organized by site for testing."""
        return {
            'site_a': [
                {
                    'name': 'Organic Tomatoes',
                    'normalized_name': 'organic tomatoes',
                    'price': 45.0,
                    'price_per_unit': 45.0,
                    'normalized_unit': 'kg',
                    'normalized_size': 1.0,
                    'normalized_brand': 'site_a_brand',
                    'normalized_category': 'vegetables'
                },
                {
                    'name': 'Fresh Bananas',
                    'normalized_name': 'fresh bananas',
                    'price': 35.0,
                    'price_per_unit': 2.92,
                    'normalized_unit': 'piece',
                    'normalized_size': 12.0,
                    'normalized_brand': 'site_a_brand',
                    'normalized_category': 'fruits'
                }
            ],
            'site_b': [
                {
                    'name': 'Premium Organic Tomatoes',
                    'normalized_name': 'premium organic tomatoes',
                    'price': 50.0,
                    'price_per_unit': 50.0,
                    'normalized_unit': 'kg',
                    'normalized_size': 1.0,
                    'normalized_brand': 'site_b_brand',
                    'normalized_category': 'vegetables'
                },
                {
                    'name': 'Yellow Bananas Fresh',
                    'normalized_name': 'yellow bananas fresh',
                    'price': 40.0,
                    'price_per_unit': 3.33,
                    'normalized_unit': 'piece',
                    'normalized_size': 12.0,
                    'normalized_brand': 'site_b_brand',
                    'normalized_category': 'fruits'
                }
            ],
            'site_c': [
                {
                    'name': 'Tomatoes Red Fresh',
                    'normalized_name': 'tomatoes red fresh',
                    'price': 42.0,
                    'price_per_unit': 42.0,
                    'normalized_unit': 'kg',
                    'normalized_size': 1.0,
                    'normalized_brand': 'site_c_brand',
                    'normalized_category': 'vegetables'
                }
            ]
        }
    
    def test_find_matches_exact_match(self, comparator):
        """Test finding matches with exact name match."""
        target_product = {
            'normalized_name': 'organic tomatoes',
            'normalized_brand': 'test_brand',
            'normalized_category': 'vegetables'
        }
        
        candidates = [
            {
                'normalized_name': 'premium organic tomatoes',
                'normalized_brand': 'other_brand',
                'normalized_category': 'vegetables',
                'price': 50.0,
                'comparison_site': 'site_b'
            },
            {
                'normalized_name': 'organic tomatoes',
                'normalized_brand': 'exact_brand',
                'normalized_category': 'vegetables',
                'price': 48.0,
                'comparison_site': 'site_c'
            }
        ]
        
        matches = comparator.find_matches(target_product, candidates)
        
        # Should find matches
        assert len(matches) > 0
        
        # Exact match should be first (highest score due to bonus)
        assert matches[0]['normalized_name'] == 'organic tomatoes'
        assert matches[0]['similarity_score'] > 90  # High score due to exact match bonus
    
    def test_find_matches_no_matches(self, comparator):
        """Test finding matches when no good matches exist."""
        target_product = {
            'normalized_name': 'completely different product',
            'normalized_brand': 'unknown',
            'normalized_category': 'unknown'
        }
        
        candidates = [
            {
                'normalized_name': 'organic tomatoes',
                'normalized_brand': 'test',
                'normalized_category': 'vegetables',
                'price': 50.0,
                'comparison_site': 'site_b'
            }
        ]
        
        matches = comparator.find_matches(target_product, candidates)
        
        # Should not find matches above threshold
        assert len(matches) == 0
    
    def test_calculate_price_difference(self, comparator):
        """Test price difference calculation."""
        source_product = {
            'name': 'Tomatoes',
            'price': 45.0,
            'price_per_unit': 45.0
        }
        
        target_product = {
            'name': 'Premium Tomatoes',
            'price': 50.0,
            'price_per_unit': 50.0,
            'comparison_site': 'site_b',
            'similarity_score': 85.0
        }
        
        result = comparator.calculate_price_difference(source_product, target_product, 'site_a')
        
        # Check structure
        assert 'source_product' in result
        assert 'target_product' in result
        assert 'source_site' in result
        assert 'target_site' in result
        assert 'price_comparison' in result
        assert 'unit_price_comparison' in result
        
        # Check price comparison values
        price_comp = result['price_comparison']
        assert price_comp['source_price'] == 45.0
        assert price_comp['target_price'] == 50.0
        assert price_comp['absolute_difference'] == -5.0  # Source is cheaper
        assert price_comp['percentage_difference'] == -10.0  # (45-50)/50*100
        assert price_comp['source_cheaper'] == True
        assert price_comp['price_advantage'] == 'site_a'
        
        # Check unit price comparison
        unit_comp = result['unit_price_comparison']
        assert unit_comp['per_unit_difference'] == -5.0
        assert unit_comp['better_unit_price'] == 'site_a'
    
    def test_calculate_price_difference_target_cheaper(self, comparator):
        """Test price difference when target is cheaper."""
        source_product = {
            'name': 'Tomatoes',
            'price': 55.0,
            'price_per_unit': 55.0
        }
        
        target_product = {
            'name': 'Premium Tomatoes',
            'price': 50.0,
            'price_per_unit': 50.0,
            'comparison_site': 'site_b',
            'similarity_score': 85.0
        }
        
        result = comparator.calculate_price_difference(source_product, target_product, 'site_a')
        
        price_comp = result['price_comparison']
        assert price_comp['absolute_difference'] == 5.0  # Source is more expensive
        assert price_comp['percentage_difference'] == 10.0  # (55-50)/50*100
        assert price_comp['source_cheaper'] == False
        assert price_comp['price_advantage'] == 'site_b'
    
    def test_compare_products_complete(self, comparator, sample_products_by_site):
        """Test complete product comparison across sites."""
        results = comparator.compare_products(sample_products_by_site)
        
        # Check structure
        assert 'matches' in results
        assert 'no_matches' in results
        assert 'statistics' in results
        assert 'price_analysis' in results
        
        # Should find some matches (cross-site)
        assert len(results['matches']) > 0
        
        # Check match structure
        match = results['matches'][0]
        assert 'source_product' in match
        assert 'target_product' in match
        assert 'source_site' in match
        assert 'target_site' in match
        assert 'price_comparison' in match
        assert 'all_matches' in match  # Top matches
    
    def test_calculate_statistics_empty(self, comparator):
        """Test statistics calculation with empty matches."""
        stats = comparator.calculate_statistics([])
        
        assert stats['total_matches'] == 0
        assert stats['source_cheaper_count'] == 0
        assert stats['target_cheaper_count'] == 0
        assert stats['average_price_difference_percentage'] == 0
    
    def test_calculate_statistics_with_matches(self, comparator):
        """Test statistics calculation with sample matches."""
        matches = [
            {
                'price_comparison': {
                    'percentage_difference': -10.0,  # Source cheaper
                    'source_cheaper': True
                }
            },
            {
                'price_comparison': {
                    'percentage_difference': 5.0,   # Target cheaper
                    'source_cheaper': False
                }
            },
            {
                'price_comparison': {
                    'percentage_difference': -2.0,  # Source cheaper
                    'source_cheaper': True
                }
            }
        ]
        
        stats = comparator.calculate_statistics(matches)
        
        assert stats['total_matches'] == 3
        assert stats['source_cheaper_count'] == 2
        assert stats['target_cheaper_count'] == 1
        assert stats['source_cheaper_percentage'] == (2/3) * 100
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
                'source_product': {'normalized_category': 'vegetables'},
                'source_site': 'site_a',
                'target_product': {'comparison_site': 'site_b'},
                'target_site': 'site_b',
                'price_comparison': {'percentage_difference': -10.0, 'source_cheaper': True},
                'similarity_score': 85.0
            },
            {
                'source_product': {'normalized_category': 'fruits'},
                'source_site': 'site_a',
                'target_product': {'comparison_site': 'site_c'},
                'target_site': 'site_c',
                'price_comparison': {'percentage_difference': 5.0, 'source_cheaper': False},
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