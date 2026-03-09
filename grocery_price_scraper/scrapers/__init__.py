"""
Scrapers package - Contains site scrapers for product websites.

All scrapers should inherit from ScraperBase and implement the required methods.
"""

from .base_scraper import ScraperBase
from .generic_scraper import GenericScraper

__all__ = ['ScraperBase', 'GenericScraper']