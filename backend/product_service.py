"""
Product service for managing product catalog and price comparison data.
"""

import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, date, timedelta
import sqlite3
from loguru import logger

# Add grocery_price_scraper to path
SCRAPER_DIR = Path(__file__).parent.parent / "grocery_price_scraper"
sys.path.insert(0, str(SCRAPER_DIR))

from db import Database
from product_models import (
    Product, ProductResponse, CompetitorPrice, PriceHistory, 
    CategoryInfo, ProductDetailResponse, ProductSearchResponse,
    ProductListQuery
)


class ProductService:
    """
    Service for managing product catalog and price comparison functionality.
    """
    
    def __init__(self):
        """Initialize product service with scraper database."""
        try:
            self.db = Database()
            logger.info("Product service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize product service: {e}")
            self.db = None
    
    def is_available(self) -> bool:
        """Check if the product service is available."""
        return self.db is not None
    
    async def get_products(
        self, 
        query: ProductListQuery,
        latest_only: bool = True
    ) -> ProductSearchResponse:
        """
        Get products with filtering, searching, and pagination.
        
        Args:
            query: Query parameters for filtering and pagination
            latest_only: If True, only return products from latest scraping session
            
        Returns:
            ProductSearchResponse with filtered products
        """
        if not self.is_available():
            return ProductSearchResponse(
                products=[], 
                total_count=0, 
                page=query.page,
                page_size=query.page_size,
                categories=[],
                sites=[]
            )
        
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Build base query
                base_query = """
                    SELECT DISTINCT p.* FROM products p
                """
                
                conditions = []
                params = []
                
                # Filter by latest scraping date if requested
                if latest_only:
                    conditions.append("DATE(p.scraped_at) = (SELECT MAX(DATE(scraped_at)) FROM products)")
                
                # Apply filters
                if query.category:
                    conditions.append("p.normalized_category = ?")
                    params.append(query.category.lower())
                
                if query.site:
                    conditions.append("p.site = ?")
                    params.append(query.site)
                
                if query.search:
                    conditions.append("(p.name LIKE ? OR p.normalized_name LIKE ?)")
                    search_term = f"%{query.search.lower()}%"
                    params.extend([search_term, search_term])
                
                # Combine conditions
                if conditions:
                    base_query += " WHERE " + " AND ".join(conditions)
                
                # Get total count
                count_query = f"SELECT COUNT(*) FROM ({base_query})"
                cursor.execute(count_query, params)
                total_count = cursor.fetchone()[0]
                
                # Add sorting
                sort_column = query.sort_by
                if sort_column == "scraped_at":
                    sort_column = "p.scraped_at"
                elif sort_column == "price":
                    sort_column = "p.price"
                elif sort_column == "price_per_unit":
                    sort_column = "p.price_per_unit"
                else:
                    sort_column = "p.name"
                
                order_by = f" ORDER BY {sort_column} {'ASC' if query.sort_order == 'asc' else 'DESC'}"
                
                # Add pagination
                offset = (query.page - 1) * query.page_size
                pagination = f" LIMIT {query.page_size} OFFSET {offset}"
                
                # Execute final query
                final_query = base_query + order_by + pagination
                cursor.execute(final_query, params)
                rows = cursor.fetchall()
                
                # Convert to product responses
                products = []
                for row in rows:
                    product_dict = dict(row)
                    product = ProductResponse(**product_dict)
                    products.append(product)
                
                # Get available categories and sites for metadata
                cursor.execute("""
                    SELECT DISTINCT normalized_category 
                    FROM products 
                    WHERE normalized_category IS NOT NULL
                    ORDER BY normalized_category
                """)
                categories = [row[0] for row in cursor.fetchall()]
                
                cursor.execute("""
                    SELECT DISTINCT site 
                    FROM products 
                    ORDER BY site
                """)
                sites = [row[0] for row in cursor.fetchall()]
                
                # Calculate total pages
                total_pages = (total_count + query.page_size - 1) // query.page_size
                
                return ProductSearchResponse(
                    products=products,
                    total=total_count,  # Changed from total_count to total
                    page=query.page,
                    page_size=query.page_size,
                    total_pages=total_pages,  # Added total_pages
                    categories=categories,
                    sites=sites
                )
                
        except Exception as e:
            logger.error(f"Failed to get products: {e}")
            return ProductSearchResponse(
                products=[], 
                total_count=0, 
                page=query.page,
                page_size=query.page_size,
                categories=[],
                sites=[]
            )
    
    async def get_product_by_id(self, product_id: int) -> Optional[ProductDetailResponse]:
        """
        Get detailed product information including competitor prices and history.
        
        Args:
            product_id: Product ID
            
        Returns:
            ProductDetailResponse or None if not found
        """
        if not self.is_available():
            return None
        
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Get main product
                cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
                product_row = cursor.fetchone()
                
                if not product_row:
                    return None
                
                product_dict = dict(product_row)
                
                # Get competitor prices for same/similar product
                competitor_prices = await self._get_competitor_prices(
                    product_dict['normalized_name'], 
                    product_dict['site'],
                    conn
                )
                
                # Get price history
                price_history = await self._get_price_history(
                    product_dict['normalized_name'],
                    product_dict['site'], 
                    conn
                )
                
                return ProductDetailResponse(
                    **product_dict,
                    competitor_prices=competitor_prices,
                    price_history=price_history
                )
                
        except Exception as e:
            logger.error(f"Failed to get product {product_id}: {e}")
            return None
    
    async def _get_competitor_prices(
        self, 
        normalized_name: str, 
        current_site: str,
        conn: sqlite3.Connection
    ) -> List[CompetitorPrice]:
        """Get competitor prices for a product."""
        cursor = conn.cursor()
        
        # Find similar products from other sites
        cursor.execute("""
            SELECT * FROM products 
            WHERE normalized_name = ? 
            AND site != ? 
            AND DATE(scraped_at) = (SELECT MAX(DATE(scraped_at)) FROM products)
            ORDER BY price ASC
        """, (normalized_name, current_site))
        
        rows = cursor.fetchall()
        competitor_prices = []
        
        # Get base price for comparison (latest from current site)
        cursor.execute("""
            SELECT price, price_per_unit FROM products 
            WHERE normalized_name = ? AND site = ?
            ORDER BY scraped_at DESC LIMIT 1
        """, (normalized_name, current_site))
        
        base_product = cursor.fetchone()
        base_price = base_product[0] if base_product else None
        
        for row in rows:
            row_dict = dict(row)
            
            # Calculate price differences
            price_diff = None
            percentage_diff = None
            is_cheaper = None
            
            if base_price and row_dict['price']:
                price_diff = row_dict['price'] - base_price
                percentage_diff = (price_diff / base_price) * 100
                is_cheaper = row_dict['price'] < base_price
            
            competitor_price = CompetitorPrice(
                site=row_dict['site'],
                price=row_dict['price'],
                price_per_unit=row_dict.get('price_per_unit'),
                price_difference=price_diff,
                percentage_difference=percentage_diff,
                is_cheaper=is_cheaper,
                url=row_dict.get('url'),
                scraped_at=datetime.fromisoformat(row_dict['scraped_at'])
            )
            competitor_prices.append(competitor_price)
        
        return competitor_prices
    
    async def _get_price_history(
        self, 
        normalized_name: str, 
        site: str,
        conn: sqlite3.Connection,
        days: int = 30
    ) -> List[PriceHistory]:
        """Get price history for a product."""
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT DATE(scraped_at) as date, price, price_per_unit, site
            FROM products 
            WHERE normalized_name = ? AND site = ?
            AND scraped_at >= DATE('now', '-{} days')
            GROUP BY DATE(scraped_at), site
            ORDER BY DATE(scraped_at) DESC
        """.format(days), (normalized_name, site))
        
        rows = cursor.fetchall()
        history = []
        
        for row in rows:
            price_history = PriceHistory(
                date=row[0],
                price=row[1],
                price_per_unit=row[2],
                site=row[3]
            )
            history.append(price_history)
        
        return history
    
    async def search_products(self, search_query: str, limit: int = 20) -> List[ProductResponse]:
        """
        Search products by name.
        
        Args:
            search_query: Search term
            limit: Maximum results to return
            
        Returns:
            List of matching products
        """
        query = ProductListQuery(
            search=search_query,
            page_size=limit,
            page=1
        )
        
        result = await self.get_products(query)
        return result.products
    
    async def get_current_prices(self, product_id: int) -> List[CompetitorPrice]:
        """
        Get current competitor prices for a specific product.
        
        Args:
            product_id: Product ID
            
        Returns:
            List of current competitor prices
        """
        if not self.is_available():
            return []
        
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Get the product to find its normalized name
                cursor.execute("SELECT normalized_name, site FROM products WHERE id = ?", (product_id,))
                product = cursor.fetchone()
                
                if not product:
                    return []
                
                return await self._get_competitor_prices(
                    product['normalized_name'],
                    product['site'],
                    conn
                )
                
        except Exception as e:
            logger.error(f"Failed to get current prices for product {product_id}: {e}")
            return []
    
    async def get_categories(self) -> List[CategoryInfo]:
        """
        Get all available categories with metadata.
        
        Returns:
            List of category information
        """
        if not self.is_available():
            return []
        
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT 
                        normalized_category,
                        COUNT(*) as product_count,
                        GROUP_CONCAT(DISTINCT site) as sites
                    FROM products 
                    WHERE normalized_category IS NOT NULL
                    GROUP BY normalized_category
                    ORDER BY normalized_category
                """)
                
                rows = cursor.fetchall()
                categories = []
                
                for row in rows:
                    category_info = CategoryInfo(
                        name=row[0],
                        display_name=row[0].replace('_', ' ').title(),
                        product_count=row[1],
                        sites_available=row[2].split(',') if row[2] else []
                    )
                    categories.append(category_info)
                
                return categories
                
        except Exception as e:
            logger.error(f"Failed to get categories: {e}")
            return []