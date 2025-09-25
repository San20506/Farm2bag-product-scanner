"""
Main runner script that orchestrates the entire price comparison pipeline.
"""

import asyncio
import yaml
import argparse
from datetime import datetime, date
from typing import Dict, Any, List
from loguru import logger
import sys
import os

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(__file__))

from scrapers import Farm2bagScraper
from normalizer import ProductNormalizer
from comparator import PriceComparator
from reporter import ExcelReporter
from db import Database


class PriceComparisonRunner:
    """
    Main orchestrator for the price comparison pipeline.
    Coordinates scraping, normalization, comparison, and reporting.
    """
    
    def __init__(self, config_dir: str = "config"):
        """
        Initialize the runner with configuration.
        
        Args:
            config_dir: Directory containing configuration files
        """
        self.config_dir = config_dir
        self.sites_config = self._load_config("sites.yml")
        self.rules_config = self._load_config("compare_rules.yml")
        
        # Initialize components
        self.normalizer = ProductNormalizer(self.rules_config)
        self.comparator = PriceComparator(self.rules_config.get('comparison', {}))
        self.reporter = ExcelReporter()
        self.database = Database()
        
        logger.info("Price comparison runner initialized")
    
    def _load_config(self, filename: str) -> Dict[str, Any]:
        """Load YAML configuration file."""
        config_path = os.path.join(self.config_dir, filename)
        try:
            with open(config_path, 'r') as file:
                return yaml.safe_load(file)
        except FileNotFoundError:
            logger.error(f"Configuration file not found: {config_path}")
            return {}
        except yaml.YAMLError as e:
            logger.error(f"Error parsing YAML config {filename}: {e}")
            return {}
    
    async def run_full_pipeline(self, 
                               categories: List[str] = None,
                               sites: List[str] = None,
                               generate_report: bool = True,
                               store_data: bool = True) -> Dict[str, Any]:
        """
        Run the complete price comparison pipeline.
        
        Args:
            categories: List of categories to scrape (optional)
            sites: List of sites to scrape (optional, defaults to enabled sites)
            generate_report: Whether to generate Excel report
            store_data: Whether to store data in database
            
        Returns:
            Dictionary with pipeline results
        """
        logger.info("Starting full price comparison pipeline")
        start_time = datetime.now()
        
        try:
            # Step 1: Scrape Farm2bag data
            logger.info("Step 1: Scraping Farm2bag products...")
            farm2bag_products = await self._scrape_farm2bag(categories)
            
            # Step 2: Scrape competitor data
            logger.info("Step 2: Scraping competitor products...")
            competitor_products = await self._scrape_competitors(categories, sites)
            
            # Step 3: Normalize all product data
            logger.info("Step 3: Normalizing product data...")
            normalized_farm2bag = self.normalizer.normalize_batch(farm2bag_products)
            
            normalized_competitors = {}
            for site, products in competitor_products.items():
                normalized_competitors[site] = self.normalizer.normalize_batch(products)
            
            # Step 4: Compare prices
            logger.info("Step 4: Comparing prices...")
            comparison_results = self.comparator.compare_products(
                normalized_farm2bag, normalized_competitors
            )
            
            # Step 5: Store data in database
            if store_data:
                logger.info("Step 5: Storing data in database...")
                await self._store_data(normalized_farm2bag, normalized_competitors, comparison_results)
            
            # Step 6: Generate Excel report
            if generate_report:
                logger.info("Step 6: Generating Excel report...")
                report_path = self.reporter.generate_report(comparison_results)
                comparison_results['report_path'] = report_path
            
            # Calculate pipeline statistics
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            pipeline_stats = {
                'execution_time': duration,
                'farm2bag_products': len(normalized_farm2bag),
                'competitor_products': sum(len(products) for products in normalized_competitors.values()),
                'total_matches': len(comparison_results.get('matches', [])),
                'sites_scraped': list(normalized_competitors.keys()),
                'categories_processed': categories or ['all'],
                'timestamp': end_time
            }
            
            comparison_results['pipeline_stats'] = pipeline_stats
            
            logger.info(f"Pipeline completed successfully in {duration:.2f} seconds")
            logger.info(f"Results: {pipeline_stats['total_matches']} matches found")
            
            return comparison_results
            
        except Exception as e:
            logger.error(f"Pipeline execution failed: {e}")
            raise
    
    async def _scrape_farm2bag(self, categories: List[str] = None) -> List[Dict[str, Any]]:
        """Scrape Farm2bag products (currently returns mock data)."""
        farm2bag_config = {
            'base_url': 'https://farm2bag.com',
            'rate_limit': 0.5
        }
        
        scraper = Farm2bagScraper(farm2bag_config)
        products = await scraper.scrape_products(categories)
        
        logger.info(f"Scraped {len(products)} Farm2bag products")
        return products
    
    async def _scrape_competitors(self, 
                                 categories: List[str] = None,
                                 sites: List[str] = None) -> Dict[str, List[Dict[str, Any]]]:
        """
        Scrape competitor products.
        Currently returns mock data for demonstration.
        """
        # Get enabled sites from config
        enabled_sites = {}
        sites_config = self.sites_config.get('sites', {})
        
        for site_name, site_config in sites_config.items():
            if site_config.get('enabled', False):
                if sites is None or site_name in sites:
                    enabled_sites[site_name] = site_config
        
        logger.info(f"Scraping from sites: {list(enabled_sites.keys())}")
        
        # For now, return mock competitor data
        # TODO: Implement actual scrapers for BigBasket, JioMart, etc.
        competitor_products = {}
        
        for site_name in enabled_sites.keys():
            # Mock competitor products for demonstration
            mock_products = [
                {
                    'name': 'Organic Tomatoes Premium',
                    'price': '50.00',
                    'unit': 'kg',
                    'size': '1',
                    'category': 'vegetables',
                    'brand': f'{site_name.title()} Fresh',
                    'url': f'https://{site_name}.com/tomatoes',
                    'image_url': f'https://{site_name}.com/images/tomatoes.jpg',
                    'availability': True,
                    'site': site_name
                },
                {
                    'name': 'Fresh Bananas',
                    'price': '40.00',
                    'unit': 'dozen',
                    'size': '1',
                    'category': 'fruits',
                    'brand': f'{site_name.title()}',
                    'url': f'https://{site_name}.com/bananas',
                    'image_url': f'https://{site_name}.com/images/bananas.jpg',
                    'availability': True,
                    'site': site_name
                },
                {
                    'name': 'Whole Wheat Bread',
                    'price': '28.00',
                    'unit': 'piece',
                    'size': '400g',
                    'category': 'bakery',
                    'brand': f'{site_name.title()} Bakery',
                    'url': f'https://{site_name}.com/bread',
                    'image_url': f'https://{site_name}.com/images/bread.jpg',
                    'availability': True,
                    'site': site_name
                }
            ]
            
            # Add site to each product
            for product in mock_products:
                product['scraped_at'] = datetime.now()
            
            competitor_products[site_name] = mock_products
        
        total_products = sum(len(products) for products in competitor_products.values())
        logger.info(f"Scraped {total_products} competitor products from {len(competitor_products)} sites")
        
        return competitor_products
    
    async def _store_data(self, 
                         farm2bag_products: List[Dict[str, Any]],
                         competitor_products: Dict[str, List[Dict[str, Any]]],
                         comparison_results: Dict[str, Any]):
        """Store scraped data and comparison results in database."""
        today = date.today()
        
        # Store Farm2bag products
        self.database.store_products(farm2bag_products, today)
        
        # Store competitor products
        for site, products in competitor_products.items():
            self.database.store_products(products, today)
        
        # Store comparison results
        self.database.store_comparisons(comparison_results, today)
        
        logger.info("All data stored in database successfully")
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        return self.database.get_statistics()
    
    async def cleanup_old_data(self, days_to_keep: int = 90):
        """Clean up old data from database."""
        self.database.cleanup_old_data(days_to_keep)
        logger.info(f"Cleaned up data older than {days_to_keep} days")


async def main():
    """Main entry point for command-line usage."""
    parser = argparse.ArgumentParser(description="Grocery Price Comparison Tool")
    parser.add_argument('--categories', nargs='+', 
                       help='Categories to scrape (vegetables, fruits, dairy, grains)')
    parser.add_argument('--sites', nargs='+',
                       help='Sites to scrape (bigbasket, jiomart, amazon_fresh, flipkart_grocery)')
    parser.add_argument('--no-report', action='store_true',
                       help='Skip Excel report generation')
    parser.add_argument('--no-store', action='store_true', 
                       help='Skip database storage')
    parser.add_argument('--stats', action='store_true',
                       help='Show database statistics and exit')
    parser.add_argument('--cleanup', type=int, metavar='DAYS',
                       help='Clean up data older than DAYS and exit')
    parser.add_argument('--config-dir', default='config',
                       help='Configuration directory path')
    
    args = parser.parse_args()
    
    # Setup logging
    logger.remove()  # Remove default handler
    logger.add(sys.stdout, level="INFO", 
               format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | {message}")
    
    # Initialize runner
    runner = PriceComparisonRunner(config_dir=args.config_dir)
    
    try:
        if args.stats:
            # Show database statistics
            stats = runner.get_database_stats()
            logger.info("Database Statistics:")
            logger.info(f"Total products: {stats['total_products']}")
            logger.info(f"Products by site: {stats['products_by_site']}")
            logger.info(f"Latest snapshot: {stats['latest_snapshot']}")
            logger.info(f"Date range: {stats['date_range']}")
            return
        
        if args.cleanup:
            # Clean up old data
            await runner.cleanup_old_data(args.cleanup)
            return
        
        # Run the pipeline
        results = await runner.run_full_pipeline(
            categories=args.categories,
            sites=args.sites,
            generate_report=not args.no_report,
            store_data=not args.no_store
        )
        
        # Print summary
        stats = results.get('pipeline_stats', {})
        logger.info("\n" + "="*50)
        logger.info("PIPELINE EXECUTION SUMMARY")
        logger.info("="*50)
        logger.info(f"Execution time: {stats.get('execution_time', 0):.2f} seconds")
        logger.info(f"Farm2bag products: {stats.get('farm2bag_products', 0)}")
        logger.info(f"Competitor products: {stats.get('competitor_products', 0)}")
        logger.info(f"Total matches found: {stats.get('total_matches', 0)}")
        logger.info(f"Sites scraped: {', '.join(stats.get('sites_scraped', []))}")
        
        if 'report_path' in results:
            logger.info(f"Report saved: {results['report_path']}")
        
        logger.info("="*50)
        
    except KeyboardInterrupt:
        logger.info("Pipeline interrupted by user")
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())