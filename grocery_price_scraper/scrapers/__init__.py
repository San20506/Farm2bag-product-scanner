"""
Scrapers package - Contains site-specific scrapers for grocery websites.

All scrapers should inherit from ScraperBase and implement the required methods.
"""

from .base_scraper import ScraperBase
from .farm2bag_scraper import Farm2bagScraper

__all__ = ['ScraperBase', 'Farm2bagScraper']