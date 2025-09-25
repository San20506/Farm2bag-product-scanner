"""
Product normalizer for standardizing product names, units, and sizes.
"""

import re
from typing import Dict, Any, List, Tuple
from loguru import logger


class ProductNormalizer:
    """
    Normalizes product data for consistent comparison across different sites.
    """
    
    def __init__(self, rules: Dict[str, Any]):
        """
        Initialize normalizer with rules.
        
        Args:
            rules: Normalization rules from compare_rules.yml
        """
        self.rules = rules
        self.unit_mappings = rules.get('unit_mappings', {})
        self.brand_aliases = rules.get('brand_aliases', {})
        self.category_mappings = rules.get('category_mappings', {})
        self.name_cleaners = rules.get('name_cleaners', [])
        self.size_patterns = rules.get('size_patterns', [])
    
    def normalize_product(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize a single product.
        
        Args:
            product: Product dictionary
            
        Returns:
            Normalized product dictionary
        """
        normalized = product.copy()
        
        # Normalize name
        normalized['normalized_name'] = self.normalize_name(product.get('name', ''))
        
        # Normalize unit and size
        normalized_unit, normalized_size = self.normalize_unit_and_size(
            product.get('unit', ''), 
            product.get('size', '')
        )
        normalized['normalized_unit'] = normalized_unit
        normalized['normalized_size'] = normalized_size
        
        # Normalize brand
        normalized['normalized_brand'] = self.normalize_brand(product.get('brand', ''))
        
        # Normalize category
        normalized['normalized_category'] = self.normalize_category(product.get('category', ''))
        
        # Calculate price per standard unit
        normalized['price_per_unit'] = self.calculate_price_per_unit(
            product.get('price', 0.0),
            normalized_unit,
            normalized_size
        )
        
        return normalized
    
    def normalize_name(self, name: str) -> str:
        """
        Normalize product name by removing common variations.
        
        Args:
            name: Original product name
            
        Returns:
            Normalized name
        """
        if not name:
            return ''
        
        normalized = name.lower().strip()
        
        # Apply name cleaners (remove common words/patterns)
        for cleaner in self.name_cleaners:
            pattern = cleaner.get('pattern', '')
            replacement = cleaner.get('replacement', '')
            normalized = re.sub(pattern, replacement, normalized, flags=re.IGNORECASE)
        
        # Remove extra whitespace
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        return normalized
    
    def normalize_brand(self, brand: str) -> str:
        """
        Normalize brand name using aliases.
        
        Args:
            brand: Original brand name
            
        Returns:
            Normalized brand name
        """
        if not brand:
            return ''
        
        brand_lower = brand.lower().strip()
        
        # Check for brand aliases
        for canonical, aliases in self.brand_aliases.items():
            if brand_lower in [alias.lower() for alias in aliases]:
                return canonical
        
        return brand_lower
    
    def normalize_category(self, category: str) -> str:
        """
        Normalize category using mappings.
        
        Args:
            category: Original category
            
        Returns:
            Normalized category
        """
        if not category:
            return 'general'
        
        category_lower = category.lower().strip()
        
        # Check for category mappings
        return self.category_mappings.get(category_lower, category_lower)
    
    def normalize_unit_and_size(self, unit: str, size: str) -> Tuple[str, float]:
        """
        Normalize unit and size to standard formats.
        
        Args:
            unit: Original unit (kg, liter, piece, etc.)
            size: Original size (1, 500g, 1L, etc.)
            
        Returns:
            Tuple of (normalized_unit, normalized_size_in_standard_units)
        """
        if not unit:
            unit = 'piece'
        
        if not size:
            size = '1'
        
        # Normalize unit
        unit_lower = unit.lower().strip()
        normalized_unit = self.unit_mappings.get(unit_lower, unit_lower)
        
        # Extract numeric size and convert to standard unit
        size_value = self.extract_size_value(size, unit_lower)
        
        return normalized_unit, size_value
    
    def extract_size_value(self, size: str, unit: str) -> float:
        """
        Extract numeric size value and convert to standard unit.
        
        Args:
            size: Size string (e.g., '500g', '1.5L', '2')
            unit: Unit string
            
        Returns:
            Size value in standard unit
        """
        if not size:
            return 1.0
        
        # Try to extract number from size string
        size_str = str(size).lower().replace(',', '')
        
        # Check each size pattern
        for pattern_config in self.size_patterns:
            pattern = pattern_config.get('pattern', '')
            unit_type = pattern_config.get('unit_type', '')
            conversion = pattern_config.get('conversion', 1.0)
            
            match = re.search(pattern, size_str)
            if match:
                try:
                    value = float(match.group(1))
                    
                    # Apply unit conversion if needed
                    if unit_type and unit_type in unit.lower():
                        value *= conversion
                    
                    return value
                except (ValueError, IndexError):
                    continue
        
        # Fallback: try to extract any number
        match = re.search(r'(\d+\.?\d*)', size_str)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                pass
        
        return 1.0
    
    def calculate_price_per_unit(self, price: float, unit: str, size: float) -> float:
        """
        Calculate price per standard unit for comparison.
        
        Args:
            price: Product price
            unit: Normalized unit
            size: Normalized size
            
        Returns:
            Price per standard unit
        """
        # Ensure price is numeric
        if isinstance(price, str):
            price = self._parse_price(price)
        
        if not price or not size or size == 0:
            return 0.0
        
        return float(price) / float(size)
    
    def normalize_batch(self, products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Normalize a batch of products.
        
        Args:
            products: List of product dictionaries
            
        Returns:
            List of normalized products
        """
        normalized_products = []
        
        for product in products:
            try:
                normalized = self.normalize_product(product)
                normalized_products.append(normalized)
            except Exception as e:
                logger.error(f"Failed to normalize product {product.get('name', 'Unknown')}: {e}")
                # Add original product with minimal normalization
                product['normalized_name'] = product.get('name', '').lower()
                product['normalized_unit'] = product.get('unit', 'piece')
                product['normalized_size'] = 1.0
                product['normalized_brand'] = product.get('brand', '').lower()
                product['normalized_category'] = product.get('category', 'general')
                product['price_per_unit'] = product.get('price', 0.0)
                normalized_products.append(product)
        
        logger.info(f"Normalized {len(normalized_products)} products")
        return normalized_products