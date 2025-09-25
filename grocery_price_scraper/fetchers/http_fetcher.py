"""
HTTP fetcher using requests library for simple web scraping.
"""

import requests
from typing import Dict, Any, Optional
from loguru import logger
import time
import random


class HttpFetcher:
    """
    Simple HTTP fetcher using requests library.
    Good for basic scraping tasks that don't require JavaScript execution.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize HTTP fetcher.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.session = requests.Session()
        
        # Set default headers to mimic a real browser
        self.session.headers.update({
            'User-Agent': self.config.get('user_agent', 
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive'
        })
        
        # Configure retries and timeouts
        self.max_retries = self.config.get('max_retries', 3)
        self.timeout = self.config.get('timeout', 10)
        self.retry_delay = self.config.get('retry_delay', 1)
    
    async def fetch(self, url: str, **kwargs) -> requests.Response:
        """
        Fetch a URL with retry logic.
        
        Args:
            url: URL to fetch
            **kwargs: Additional arguments for requests
            
        Returns:
            Response object
        
        Raises:
            Exception: If all retry attempts fail
        """
        for attempt in range(self.max_retries + 1):
            try:
                logger.debug(f"Fetching URL: {url} (attempt {attempt + 1})")
                
                # Add random delay to avoid being blocked
                if attempt > 0:
                    delay = self.retry_delay * (2 ** (attempt - 1)) + random.uniform(0, 1)
                    time.sleep(delay)
                
                response = self.session.get(
                    url, 
                    timeout=self.timeout,
                    **kwargs
                )
                response.raise_for_status()
                
                logger.debug(f"Successfully fetched {url}")
                return response
                
            except requests.exceptions.RequestException as e:
                logger.warning(f"Fetch attempt {attempt + 1} failed for {url}: {e}")
                
                if attempt == self.max_retries:
                    logger.error(f"All fetch attempts failed for {url}")
                    raise
        
        # This should never be reached, but for type safety
        raise Exception(f"Failed to fetch {url}")
    
    async def fetch_text(self, url: str, **kwargs) -> str:
        """
        Fetch URL and return text content.
        
        Args:
            url: URL to fetch
            **kwargs: Additional arguments for requests
            
        Returns:
            Text content of the response
        """
        response = await self.fetch(url, **kwargs)
        return response.text
    
    async def fetch_json(self, url: str, **kwargs) -> Dict[str, Any]:
        """
        Fetch URL and return JSON content.
        
        Args:
            url: URL to fetch
            **kwargs: Additional arguments for requests
            
        Returns:
            JSON content as dictionary
        """
        response = await self.fetch(url, **kwargs)
        return response.json()
    
    def set_headers(self, headers: Dict[str, str]):
        """
        Update session headers.
        
        Args:
            headers: Headers dictionary to update
        """
        self.session.headers.update(headers)
    
    def set_cookies(self, cookies: Dict[str, str]):
        """
        Update session cookies.
        
        Args:
            cookies: Cookies dictionary to update
        """
        self.session.cookies.update(cookies)
    
    def close(self):
        """Close the session."""
        self.session.close()