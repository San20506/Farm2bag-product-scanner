"""
Fetchers package - HTTP and browser-based fetching utilities.
"""

from .http_fetcher import HttpFetcher
from .playwright_fetcher import PlaywrightFetcher

__all__ = ['HttpFetcher', 'PlaywrightFetcher']