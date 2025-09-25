"""
Integration tests for the complete pipeline.
"""

import pytest
import asyncio
import tempfile
import os
from datetime import date

from runner import PriceComparisonRunner
from db import Database


class TestPipelineIntegration:
    """Integration tests for the complete price comparison pipeline."""
    
    @pytest.fixture
    def temp_config_dir(self):
        """Create temporary configuration directory for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create config files in temp directory
            sites_config = """
sites:
  test_site:
    name: "Test Site"
    base_url: "https://test.com"
    enabled: true
    rate_limit: 0.1
    use_playwright: false
    
global:
  max_concurrent_requests: 1
  request_timeout: 5
"""
            
            rules_config = """
unit_mappings:
  kg: kg
  piece: piece
  
brand_aliases:
  test: [test, test_brand]
  
category_mappings:
  vegetables: vegetables
  fruits: fruits
  
name_cleaners:
  - pattern: '\\b(fresh|organic)\\b'
    replacement: ''
    
size_patterns:
  - pattern: '(\\d+(?:\\.\\d+)?)\\s*kg'
    unit_type: weight
    conversion: 1.0
    
comparison:
  matching_threshold: 70
  weight_name: 0.8
  weight_brand: 0.1
  weight_category: 0.1
"""
            
            # Write config files
            os.makedirs(os.path.join(temp_dir, 'config'), exist_ok=True)
            
            with open(os.path.join(temp_dir, 'config', 'sites.yml'), 'w') as f:
                f.write(sites_config)
                
            with open(os.path.join(temp_dir, 'config', 'compare_rules.yml'), 'w') as f:
                f.write(rules_config)
            
            yield os.path.join(temp_dir, 'config')
    
    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_file:
            db_path = temp_file.name
        
        # Create database
        db = Database(db_path)
        
        yield db
        
        # Cleanup
        db.close()
        if os.path.exists(db_path):
            os.unlink(db_path)
    
    @pytest.mark.asyncio
    async def test_runner_initialization(self, temp_config_dir):
        """Test that runner initializes correctly with config."""
        runner = PriceComparisonRunner(config_dir=temp_config_dir)
        
        assert runner.sites_config is not None
        assert runner.rules_config is not None
        assert runner.normalizer is not None
        assert runner.comparator is not None
        assert runner.reporter is not None
        assert runner.database is not None
    
    @pytest.mark.asyncio
    async def test_farm2bag_scraping(self, temp_config_dir):
        """Test Farm2bag scraping (mock data)."""
        runner = PriceComparisonRunner(config_dir=temp_config_dir)
        
        products = await runner._scrape_farm2bag(['vegetables', 'fruits'])
        
        assert len(products) > 0
        
        # Check product structure
        for product in products:
            assert 'name' in product
            assert 'price' in product
            assert 'site' in product
            assert product['site'] == 'farm2bag'
    
    @pytest.mark.asyncio
    async def test_competitor_scraping(self, temp_config_dir):
        """Test competitor scraping (mock data)."""
        runner = PriceComparisonRunner(config_dir=temp_config_dir)
        
        competitor_products = await runner._scrape_competitors(
            categories=['vegetables'],
            sites=['test_site']
        )
        
        # Should return mock data since actual scraping is not implemented
        assert isinstance(competitor_products, dict)
    
    @pytest.mark.asyncio
    async def test_full_pipeline_execution(self, temp_config_dir):
        """Test complete pipeline execution."""
        runner = PriceComparisonRunner(config_dir=temp_config_dir)
        
        # Run pipeline with limited scope for testing
        results = await runner.run_full_pipeline(
            categories=['vegetables'],
            sites=None,  # Use default enabled sites
            generate_report=False,  # Skip report generation for speed
            store_data=False  # Skip database storage for this test
        )
        
        # Check results structure
        assert 'matches' in results
        assert 'no_matches' in results
        assert 'statistics' in results
        assert 'pipeline_stats' in results
        
        # Check pipeline stats
        stats = results['pipeline_stats']
        assert 'execution_time' in stats
        assert 'farm2bag_products' in stats
        assert 'competitor_products' in stats
        assert 'timestamp' in stats
        
        # Should have some data
        assert stats['farm2bag_products'] > 0
    
    @pytest.mark.asyncio
    async def test_database_integration(self, temp_db):
        """Test database integration with pipeline."""
        # Store sample products
        products = [
            {
                'site': 'farm2bag',
                'name': 'Test Tomatoes',
                'normalized_name': 'test tomatoes',
                'price': 45.0,
                'unit': 'kg',
                'size': '1',
                'normalized_unit': 'kg',
                'normalized_size': 1.0,
                'price_per_unit': 45.0,
                'category': 'vegetables',
                'normalized_category': 'vegetables',
                'brand': 'farm2bag',
                'normalized_brand': 'farm2bag',
                'url': 'https://test.com/tomatoes',
                'image_url': '',
                'availability': True
            }
        ]
        
        # Store products
        count = temp_db.store_products(products)
        assert count == 1
        
        # Retrieve products
        today = date.today()
        retrieved = temp_db.get_products_by_date(today)
        assert len(retrieved) == 1
        assert retrieved[0]['name'] == 'Test Tomatoes'
        
        # Check statistics
        stats = temp_db.get_statistics()
        assert stats['total_products'] == 1
        assert 'farm2bag' in stats['products_by_site']
    
    @pytest.mark.asyncio
    async def test_report_generation(self, temp_config_dir):
        """Test Excel report generation."""
        runner = PriceComparisonRunner(config_dir=temp_config_dir)
        
        # Create sample comparison results
        comparison_results = {
            'matches': [
                {
                    'farm2bag_product': {
                        'name': 'Test Product',
                        'normalized_category': 'vegetables'
                    },
                    'competitor_product': {
                        'name': 'Competitor Product',
                        'comparison_site': 'test_site'
                    },
                    'price_comparison': {
                        'farm2bag_price': 45.0,
                        'competitor_price': 50.0,
                        'absolute_difference': -5.0,
                        'percentage_difference': -10.0,
                        'farm2bag_cheaper': True,
                        'price_advantage': 'Farm2bag'
                    },
                    'unit_price_comparison': {
                        'farm2bag_price_per_unit': 45.0,
                        'competitor_price_per_unit': 50.0,
                        'per_unit_difference': -5.0,
                        'per_unit_percentage': -10.0,
                        'better_unit_price': 'Farm2bag'
                    },
                    'similarity_score': 85.0
                }
            ],
            'no_matches': [],
            'statistics': {
                'total_matches': 1,
                'farm2bag_cheaper_count': 1,
                'competitor_cheaper_count': 0,
                'farm2bag_cheaper_percentage': 100.0,
                'average_price_difference_percentage': -10.0
            },
            'price_analysis': {
                'by_category': {},
                'by_site': {},
                'overall_competitiveness': {}
            }
        }
        
        # Generate report
        report_path = runner.reporter.generate_report(comparison_results, 'test_report.xlsx')
        
        assert os.path.exists(report_path)
        assert report_path.endswith('test_report.xlsx')
        
        # Cleanup
        if os.path.exists(report_path):
            os.unlink(report_path)
    
    @pytest.mark.asyncio
    async def test_pipeline_error_handling(self, temp_config_dir):
        """Test pipeline error handling."""
        runner = PriceComparisonRunner(config_dir=temp_config_dir)
        
        # Test with invalid categories (should not crash)
        try:
            results = await runner.run_full_pipeline(
                categories=['invalid_category'],
                generate_report=False,
                store_data=False
            )
            # Should complete without error, just with no matches
            assert 'pipeline_stats' in results
        except Exception as e:
            pytest.fail(f"Pipeline should handle invalid categories gracefully: {e}")
    
    @pytest.mark.asyncio
    async def test_configuration_loading(self, temp_config_dir):
        """Test configuration file loading."""
        runner = PriceComparisonRunner(config_dir=temp_config_dir)
        
        # Check sites config loaded
        assert 'sites' in runner.sites_config
        assert 'test_site' in runner.sites_config['sites']
        
        # Check rules config loaded
        assert 'unit_mappings' in runner.rules_config
        assert 'comparison' in runner.rules_config
        
        # Test with missing config directory
        missing_runner = PriceComparisonRunner(config_dir='/nonexistent/path')
        assert missing_runner.sites_config == {}
        assert missing_runner.rules_config == {}


if __name__ == "__main__":
    pytest.main([__file__])