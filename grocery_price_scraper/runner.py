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

from scrapers import GenericScraper
from normalizer import ProductNormalizer
from comparator import PriceComparator
from reporter import ExcelReporter
from db import Database


class PriceComparisonRunner:
    """
    Main orchestrator for the price comparison pipeline.
    Coordinates scraping, normalization, comparison, and reporting.
    All configured sites are treated equally — no "primary" site distinction.
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
                               product_query: str = None,
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
            # Step 1: Scrape products from all configured sites
            logger.info("Step 1: Scraping products from configured sites...")
            products_by_site = await self._scrape_sites(categories, sites, product_query)
            
            # Step 2: Normalize all product data
            logger.info("Step 2: Normalizing product data...")
            normalized_by_site = {}
            for site, products in products_by_site.items():
                normalized_by_site[site] = self.normalizer.normalize_batch(products)
            
            # Step 3: Compare prices across sites
            logger.info("Step 3: Comparing prices across sites...")
            comparison_results = self.comparator.compare_products(normalized_by_site)
            
            # Step 4: Store data in database
            if store_data:
                logger.info("Step 4: Storing data in database...")
                await self._store_data(normalized_by_site, comparison_results)
            
            # Step 5: Generate Excel report
            if generate_report:
                logger.info("Step 5: Generating Excel report...")
                report_path = self.reporter.generate_report(comparison_results)
                comparison_results['report_path'] = report_path
            
            # Calculate pipeline statistics
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            total_products = sum(len(products) for products in normalized_by_site.values())
            products_count_by_site = {
                site: len(products) for site, products in normalized_by_site.items()
            }
            
            pipeline_stats = {
                'execution_time': duration,
                'total_products': total_products,
                'products_by_site': products_count_by_site,
                'total_matches': len(comparison_results.get('matches', [])),
                'sites_scraped': list(normalized_by_site.keys()),
                'categories_processed': categories or ['all'],
                'timestamp': end_time
            }

            if product_query:
                pipeline_stats['categories_processed'] = []
                query_products_flat = []
                for site_name, site_products in normalized_by_site.items():
                    for product in site_products:
                        query_products_flat.append({
                            'site': site_name,
                            'name': product.get('name'),
                            'price': product.get('price'),
                            'unit': product.get('unit'),
                            'size': product.get('size'),
                            'brand': product.get('brand'),
                            'url': product.get('url'),
                            'image_url': product.get('image_url'),
                            'availability': product.get('availability', True),
                            'category': product.get('category', 'general')
                        })

                pipeline_stats['product_query'] = product_query
                pipeline_stats['query_products_flat'] = query_products_flat
            
            comparison_results['pipeline_stats'] = pipeline_stats
            
            logger.info(f"Pipeline completed successfully in {duration:.2f} seconds")
            logger.info(f"Results: {pipeline_stats['total_matches']} matches found")
            
            return comparison_results
            
        except Exception as e:
            logger.error(f"Pipeline execution failed: {e}")
            raise
    
    async def _scrape_sites(self,
                            categories: List[str] = None,
                            sites: List[str] = None,
                            product_query: str = None) -> Dict[str, List[Dict[str, Any]]]:
        """
        Scrape products from all enabled sites.
        
        Args:
            categories: List of categories to scrape (optional)
            sites: List of specific sites to scrape (optional, defaults to all enabled)
            
        Returns:
            Dictionary of {site_name: [products]}
        """
        # Get enabled sites from config
        enabled_sites = {}
        sites_config = self.sites_config.get('sites', {})
        
        for site_name, site_config in sites_config.items():
            if site_config.get('enabled', False):
                if sites is None or site_name in sites:
                    enabled_sites[site_name] = site_config
        
        logger.info(f"Scraping from sites: {list(enabled_sites.keys())}")
        
        products_by_site = {}
        
        for site_name, site_config in enabled_sites.items():
            try:
                scraper = GenericScraper(site_name, site_config)
                products = await scraper.scrape_products(categories, product_query=product_query)
                products_by_site[site_name] = products
                logger.info(f"Scraped {len(products)} products from {site_name}")
            except Exception as e:
                logger.error(f"Failed to scrape {site_name}: {e}")
                products_by_site[site_name] = []
        
        total_products = sum(len(products) for products in products_by_site.values())
        logger.info(f"Scraped {total_products} total products from {len(products_by_site)} sites")
        
        return products_by_site
    
    async def _store_data(self, 
                         products_by_site: Dict[str, List[Dict[str, Any]]],
                         comparison_results: Dict[str, Any]):
        """Store scraped data and comparison results in database."""
        today = date.today()
        
        # Store products from all sites
        for site, products in products_by_site.items():
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
    parser = argparse.ArgumentParser(description="Product Price Comparison Tool")
    parser.add_argument('--product', type=str,
                       help='Single product query to scrape across all enabled sites')
    parser.add_argument('--categories', nargs='+', 
                       help='Categories to scrape (e.g., vegetables, fruits, dairy, grains)')
    parser.add_argument('--sites', nargs='+',
                       help='Sites to scrape (e.g., farm2bag, bigbasket, jiomart, amazon_fresh)')
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
            product_query=args.product,
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
        logger.info(f"Total products scraped: {stats.get('total_products', 0)}")
        
        products_by_site = stats.get('products_by_site', {})
        for site, count in products_by_site.items():
            logger.info(f"  {site}: {count} products")
        
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