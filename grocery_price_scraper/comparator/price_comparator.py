"""
Price comparator for matching products across sites and calculating differences.
"""

from typing import List, Dict, Any, Tuple, Optional
from rapidfuzz import fuzz, process
from loguru import logger
import pandas as pd


class PriceComparator:
    """
    Compares products across different sites using fuzzy matching
    and calculates price differences.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize comparator with configuration.
        
        Args:
            config: Configuration from compare_rules.yml
        """
        self.config = config
        self.matching_threshold = config.get('matching_threshold', 80)
        self.weight_name = config.get('weight_name', 0.7)
        self.weight_brand = config.get('weight_brand', 0.2)
        self.weight_category = config.get('weight_category', 0.1)
        self.exact_match_bonus = config.get('exact_match_bonus', 10)
    
    def compare_products(self, products_by_site: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """
        Compare products across all sites using cross-site pairing.
        
        Args:
            products_by_site: Dict of {site_name: [products]} for all sites
            
        Returns:
            Dictionary containing comparison results
        """
        results = {
            'matches': [],
            'no_matches': [],
            'statistics': {},
            'price_analysis': {}
        }
        
        site_names = list(products_by_site.keys())
        
        if len(site_names) < 2:
            logger.warning("Need at least 2 sites to compare prices")
            results['statistics'] = self._empty_statistics()
            return results
        
        # Cross-site comparisons: compare each site against every other site
        total_source = 0
        for i, source_site in enumerate(site_names):
            source_products = products_by_site[source_site]
            
            # Build candidate pool from all other sites
            candidate_products = []
            for j, other_site in enumerate(site_names):
                if i == j:
                    continue
                for product in products_by_site[other_site]:
                    product_copy = product.copy()
                    product_copy['comparison_site'] = other_site
                    candidate_products.append(product_copy)
            
            total_source += len(source_products)
            
            for source_product in source_products:
                matches = self.find_matches(source_product, candidate_products)
                
                if matches:
                    best_match = matches[0]  # Highest similarity score
                    comparison_result = self.calculate_price_difference(
                        source_product, best_match, source_site
                    )
                    comparison_result['all_matches'] = matches[:3]  # Top 3 matches
                    results['matches'].append(comparison_result)
                else:
                    results['no_matches'].append({
                        'product': source_product,
                        'site': source_site,
                        'reason': 'No similar products found on other sites'
                    })
        
        logger.info(f"Compared {total_source} products across {len(site_names)} sites")
        
        # Calculate statistics
        results['statistics'] = self.calculate_statistics(results['matches'])
        results['price_analysis'] = self.analyze_pricing(results['matches'])
        
        logger.info(f"Found matches for {len(results['matches'])} products, {len(results['no_matches'])} without matches")
        
        return results
    
    def find_matches(self, target_product: Dict[str, Any], 
                    candidate_products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Find matching products using fuzzy matching.
        
        Args:
            target_product: Product to find matches for
            candidate_products: List of candidate products
            
        Returns:
            List of matching products with similarity scores
        """
        matches = []
        
        target_name = target_product.get('normalized_name', '')
        target_brand = target_product.get('normalized_brand', '')
        target_category = target_product.get('normalized_category', '')
        
        for candidate in candidate_products:
            candidate_name = candidate.get('normalized_name', '')
            candidate_brand = candidate.get('normalized_brand', '')
            candidate_category = candidate.get('normalized_category', '')
            
            # Calculate similarity scores
            name_similarity = fuzz.ratio(target_name, candidate_name)
            brand_similarity = fuzz.ratio(target_brand, candidate_brand) if target_brand and candidate_brand else 0
            category_match = 100 if target_category == candidate_category else 0
            
            # Calculate weighted score
            overall_score = (
                name_similarity * self.weight_name +
                brand_similarity * self.weight_brand +
                category_match * self.weight_category
            )
            
            # Bonus for exact matches
            if target_name == candidate_name:
                overall_score += self.exact_match_bonus
            
            if overall_score >= self.matching_threshold:
                match_info = candidate.copy()
                match_info['similarity_score'] = overall_score
                match_info['name_similarity'] = name_similarity
                match_info['brand_similarity'] = brand_similarity
                match_info['category_match'] = category_match
                matches.append(match_info)
        
        # Sort by similarity score (descending)
        matches.sort(key=lambda x: x['similarity_score'], reverse=True)
        
        return matches
    
    def calculate_price_difference(self, source_product: Dict[str, Any], 
                                 target_product: Dict[str, Any],
                                 source_site: str = "unknown") -> Dict[str, Any]:
        """
        Calculate price differences between two products from different sites.
        
        Args:
            source_product: Source product data
            target_product: Target product data (from another site)
            source_site: Name of the source site
            
        Returns:
            Dictionary with comparison results
        """
        source_price = source_product.get('price', 0.0)
        target_price = target_product.get('price', 0.0)
        
        source_price_per_unit = source_product.get('price_per_unit', 0.0)
        target_price_per_unit = target_product.get('price_per_unit', 0.0)
        
        target_site = target_product.get('comparison_site', 'unknown')
        
        # Calculate differences
        absolute_diff = source_price - target_price
        percentage_diff = (absolute_diff / target_price * 100) if target_price > 0 else 0
        
        per_unit_diff = source_price_per_unit - target_price_per_unit
        per_unit_percentage = (per_unit_diff / target_price_per_unit * 100) if target_price_per_unit > 0 else 0
        
        return {
            'source_product': source_product,
            'source_site': source_site,
            'target_product': target_product,
            'target_site': target_site,
            'price_comparison': {
                'source_price': source_price,
                'target_price': target_price,
                'absolute_difference': absolute_diff,
                'percentage_difference': percentage_diff,
                'source_cheaper': absolute_diff < 0,
                'price_advantage': source_site if absolute_diff < 0 else target_site
            },
            'unit_price_comparison': {
                'source_price_per_unit': source_price_per_unit,
                'target_price_per_unit': target_price_per_unit,
                'per_unit_difference': per_unit_diff,
                'per_unit_percentage': per_unit_percentage,
                'better_unit_price': source_site if per_unit_diff < 0 else target_site
            },
            'similarity_score': target_product.get('similarity_score', 0)
        }
    
    def _empty_statistics(self) -> Dict[str, Any]:
        """Return empty statistics dict."""
        return {
            'total_matches': 0,
            'source_cheaper_count': 0,
            'target_cheaper_count': 0,
            'average_price_difference_percentage': 0,
            'max_savings_percentage': 0,
            'min_savings_percentage': 0
        }
    
    def calculate_statistics(self, matches: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate overall statistics from matches.
        
        Args:
            matches: List of product matches
            
        Returns:
            Statistics dictionary
        """
        if not matches:
            return self._empty_statistics()
        
        price_differences = [match['price_comparison']['percentage_difference'] for match in matches]
        source_cheaper = [match for match in matches if match['price_comparison']['source_cheaper']]
        
        return {
            'total_matches': len(matches),
            'source_cheaper_count': len(source_cheaper),
            'target_cheaper_count': len(matches) - len(source_cheaper),
            'source_cheaper_percentage': (len(source_cheaper) / len(matches)) * 100,
            'average_price_difference_percentage': sum(price_differences) / len(price_differences),
            'max_savings_percentage': min(price_differences) if price_differences else 0,
            'min_savings_percentage': max(price_differences) if price_differences else 0,
            'median_price_difference': sorted(price_differences)[len(price_differences) // 2]
        }
    
    def analyze_pricing(self, matches: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze pricing patterns by category and site.
        
        Args:
            matches: List of product matches
            
        Returns:
            Pricing analysis dictionary
        """
        if not matches:
            return {}
        
        # Convert to DataFrame for easier analysis
        data = []
        for match in matches:
            data.append({
                'source_site': match.get('source_site', 'unknown'),
                'target_site': match.get('target_site', 'unknown'),
                'category': match['source_product'].get('normalized_category', 'unknown'),
                'percentage_diff': match['price_comparison']['percentage_difference'],
                'source_cheaper': match['price_comparison']['source_cheaper'],
                'similarity_score': match['similarity_score']
            })
        
        df = pd.DataFrame(data)
        
        # Analysis by category
        category_analysis = df.groupby('category').agg({
            'percentage_diff': ['mean', 'count'],
            'source_cheaper': 'sum'
        }).round(2)
        
        # Analysis by target site
        site_analysis = df.groupby('target_site').agg({
            'percentage_diff': ['mean', 'count'],
            'source_cheaper': 'sum'
        }).round(2)
        
        return {
            'by_category': category_analysis.to_dict(),
            'by_site': site_analysis.to_dict(),
            'overall_competitiveness': {
                'avg_price_difference': df['percentage_diff'].mean(),
                'competitive_categories': df.groupby('category')['source_cheaper'].sum().to_dict(),
                'cheapest_site': df.groupby('target_site')['percentage_diff'].mean().idxmin() if len(df) > 0 else None
            }
        }