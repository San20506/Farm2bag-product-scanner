"""
SQLite database wrapper for storing daily snapshots and historical data.
"""

import sqlite3
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, date
from loguru import logger
import os


class Database:
    """
    SQLite database wrapper for the grocery price scraper.
    Stores daily snapshots of product prices for historical analysis.
    """
    
    def __init__(self, db_path: str = "data/grocery_prices.db"):
        """
        Initialize database connection.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # Initialize database
        self._create_tables()
        logger.info(f"Database initialized: {db_path}")
    
    def _create_tables(self):
        """Create database tables if they don't exist."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Products table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    site TEXT NOT NULL,
                    name TEXT NOT NULL,
                    normalized_name TEXT,
                    price REAL NOT NULL,
                    unit TEXT,
                    size TEXT,
                    normalized_unit TEXT,
                    normalized_size REAL,
                    price_per_unit REAL,
                    category TEXT,
                    normalized_category TEXT,
                    brand TEXT,
                    normalized_brand TEXT,
                    url TEXT,
                    image_url TEXT,
                    availability BOOLEAN,
                    scraped_at TIMESTAMP NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Daily snapshots table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS daily_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    snapshot_date DATE NOT NULL UNIQUE,
                    total_products INTEGER,
                    sites_scraped TEXT,  -- JSON array of site names
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Price comparisons table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS price_comparisons (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    comparison_date DATE NOT NULL,
                    farm2bag_product_id INTEGER,
                    competitor_product_id INTEGER,
                    price_difference REAL,
                    percentage_difference REAL,
                    similarity_score REAL,
                    farm2bag_cheaper BOOLEAN,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (farm2bag_product_id) REFERENCES products (id),
                    FOREIGN KEY (competitor_product_id) REFERENCES products (id)
                )
            """)
            
            # Create indexes for better query performance
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_products_site_date 
                ON products (site, scraped_at)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_products_normalized_name 
                ON products (normalized_name)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_comparisons_date 
                ON price_comparisons (comparison_date)
            """)
            
            conn.commit()
            logger.debug("Database tables created/verified")
    
    def store_products(self, products: List[Dict[str, Any]], snapshot_date: date = None) -> int:
        """
        Store a batch of products in the database.
        
        Args:
            products: List of product dictionaries
            snapshot_date: Date for this snapshot (defaults to today)
            
        Returns:
            Number of products stored
        """
        if not products:
            return 0
        
        if snapshot_date is None:
            snapshot_date = date.today()
        
        stored_count = 0
        sites_scraped = set()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            for product in products:
                try:
                    cursor.execute("""
                        INSERT INTO products (
                            site, name, normalized_name, price, unit, size,
                            normalized_unit, normalized_size, price_per_unit,
                            category, normalized_category, brand, normalized_brand,
                            url, image_url, availability, scraped_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        product.get('site', ''),
                        product.get('name', ''),
                        product.get('normalized_name', ''),
                        product.get('price', 0.0),
                        product.get('unit', ''),
                        product.get('size', ''),
                        product.get('normalized_unit', ''),
                        product.get('normalized_size', 0.0),
                        product.get('price_per_unit', 0.0),
                        product.get('category', ''),
                        product.get('normalized_category', ''),
                        product.get('brand', ''),
                        product.get('normalized_brand', ''),
                        product.get('url', ''),
                        product.get('image_url', ''),
                        product.get('availability', True),
                        product.get('scraped_at', datetime.now())
                    ))
                    
                    stored_count += 1
                    sites_scraped.add(product.get('site', 'unknown'))
                    
                except Exception as e:
                    logger.error(f"Failed to store product {product.get('name', 'Unknown')}: {e}")
            
            # Create/update daily snapshot record
            cursor.execute("""
                INSERT OR REPLACE INTO daily_snapshots 
                (snapshot_date, total_products, sites_scraped)
                VALUES (?, ?, ?)
            """, (
                snapshot_date,
                stored_count,
                json.dumps(list(sites_scraped))
            ))
            
            conn.commit()
        
        logger.info(f"Stored {stored_count} products for {snapshot_date}")
        return stored_count
    
    def store_comparisons(self, comparison_results: Dict[str, Any], comparison_date: date = None) -> int:
        """
        Store price comparison results.
        
        Args:
            comparison_results: Results from PriceComparator
            comparison_date: Date for this comparison (defaults to today)
            
        Returns:
            Number of comparisons stored
        """
        if comparison_date is None:
            comparison_date = date.today()
        
        matches = comparison_results.get('matches', [])
        if not matches:
            return 0
        
        stored_count = 0
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            for match in matches:
                try:
                    # Get product IDs (this is a simplified approach)
                    # In a real implementation, you'd want to properly match products by unique identifiers
                    
                    farm2bag_name = match['farm2bag_product'].get('name', '')
                    competitor_name = match['competitor_product'].get('name', '')
                    
                    cursor.execute("""
                        INSERT INTO price_comparisons (
                            comparison_date, farm2bag_product_id, competitor_product_id,
                            price_difference, percentage_difference, similarity_score,
                            farm2bag_cheaper
                        ) VALUES (?, 
                            (SELECT id FROM products WHERE name = ? AND site = 'farm2bag' ORDER BY created_at DESC LIMIT 1),
                            (SELECT id FROM products WHERE name = ? ORDER BY created_at DESC LIMIT 1),
                            ?, ?, ?, ?
                        )
                    """, (
                        comparison_date,
                        farm2bag_name,
                        competitor_name,
                        match['price_comparison']['absolute_difference'],
                        match['price_comparison']['percentage_difference'],
                        match['similarity_score'],
                        match['price_comparison']['farm2bag_cheaper']
                    ))
                    
                    stored_count += 1
                    
                except Exception as e:
                    logger.error(f"Failed to store comparison for {farm2bag_name}: {e}")
            
            conn.commit()
        
        logger.info(f"Stored {stored_count} price comparisons for {comparison_date}")
        return stored_count
    
    def get_products_by_date(self, target_date: date, site: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get products for a specific date.
        
        Args:
            target_date: Date to query
            site: Optional site filter
            
        Returns:
            List of product dictionaries
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row  # Enable column access by name
            cursor = conn.cursor()
            
            query = """
                SELECT * FROM products 
                WHERE DATE(scraped_at) = ?
            """
            params = [target_date]
            
            if site:
                query += " AND site = ?"
                params.append(site)
            
            query += " ORDER BY name"
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            return [dict(row) for row in rows]
    
    def get_price_history(self, product_name: str, site: str, days: int = 30) -> List[Dict[str, Any]]:
        """
        Get price history for a specific product.
        
        Args:
            product_name: Product name to query
            site: Site name
            days: Number of days to look back
            
        Returns:
            List of price history records
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT DATE(scraped_at) as date, price, price_per_unit
                FROM products 
                WHERE normalized_name = ? AND site = ?
                AND scraped_at >= DATE('now', '-{} days')
                ORDER BY scraped_at DESC
            """.format(days), (product_name.lower(), site))
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def get_daily_snapshots(self, days: int = 30) -> List[Dict[str, Any]]:
        """
        Get daily snapshot statistics.
        
        Args:
            days: Number of days to look back
            
        Returns:
            List of daily snapshot records
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM daily_snapshots
                WHERE snapshot_date >= DATE('now', '-{} days')
                ORDER BY snapshot_date DESC
            """.format(days))
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get overall database statistics.
        
        Returns:
            Dictionary with database statistics
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Total products
            cursor.execute("SELECT COUNT(*) FROM products")
            total_products = cursor.fetchone()[0]
            
            # Products by site
            cursor.execute("""
                SELECT site, COUNT(*) as count 
                FROM products 
                GROUP BY site 
                ORDER BY count DESC
            """)
            products_by_site = dict(cursor.fetchall())
            
            # Latest snapshot
            cursor.execute("""
                SELECT snapshot_date, total_products 
                FROM daily_snapshots 
                ORDER BY snapshot_date DESC 
                LIMIT 1
            """)
            latest_snapshot = cursor.fetchone()
            
            # Date range
            cursor.execute("""
                SELECT MIN(DATE(scraped_at)) as first_date, 
                       MAX(DATE(scraped_at)) as last_date 
                FROM products
            """)
            date_range = cursor.fetchone()
            
            return {
                'total_products': total_products,
                'products_by_site': products_by_site,
                'latest_snapshot': {
                    'date': latest_snapshot[0] if latest_snapshot else None,
                    'products': latest_snapshot[1] if latest_snapshot else 0
                },
                'date_range': {
                    'first_date': date_range[0] if date_range else None,
                    'last_date': date_range[1] if date_range else None
                }
            }
    
    def cleanup_old_data(self, days_to_keep: int = 90):
        """
        Clean up old data beyond the specified retention period.
        
        Args:
            days_to_keep: Number of days of data to retain
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Delete old products
            cursor.execute("""
                DELETE FROM products 
                WHERE scraped_at < DATE('now', '-{} days')
            """.format(days_to_keep))
            products_deleted = cursor.rowcount
            
            # Delete old snapshots
            cursor.execute("""
                DELETE FROM daily_snapshots 
                WHERE snapshot_date < DATE('now', '-{} days')
            """.format(days_to_keep))
            snapshots_deleted = cursor.rowcount
            
            # Delete old comparisons
            cursor.execute("""
                DELETE FROM price_comparisons 
                WHERE comparison_date < DATE('now', '-{} days')
            """.format(days_to_keep))
            comparisons_deleted = cursor.rowcount
            
            conn.commit()
            
            logger.info(f"Cleaned up old data: {products_deleted} products, {snapshots_deleted} snapshots, {comparisons_deleted} comparisons")
    
    def close(self):
        """Close database connection (SQLite auto-closes, but good practice)."""
        pass