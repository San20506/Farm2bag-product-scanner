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
    
    def compare_products(self, farm2bag_products: List[Dict[str, Any]], 
                        competitor_products: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """
        Compare Farm2bag products with competitor products.
        
        Args:
            farm2bag_products: List of Farm2bag products (normalized)
            competitor_products: Dict of {site_name: [products]} from competitors
            
        Returns:
            Dictionary containing comparison results
        """
        results = {
            'matches': [],
            'no_matches': [],
            'statistics': {},
            'price_analysis': {}
        }
        
        all_competitor_products = []
        for site, products in competitor_products.items():
            for product in products:
                product['comparison_site'] = site
                all_competitor_products.append(product)
        
        logger.info(f"Comparing {len(farm2bag_products)} Farm2bag products with {len(all_competitor_products)} competitor products")
        
        for farm2bag_product in farm2bag_products:
            matches = self.find_matches(farm2bag_product, all_competitor_products)
            
            if matches:
                best_match = matches[0]  # Highest similarity score
                comparison_result = self.calculate_price_difference(farm2bag_product, best_match)
                comparison_result['all_matches'] = matches[:3]  # Top 3 matches
                results['matches'].append(comparison_result)
            else:
                results['no_matches'].append({
                    'product': farm2bag_product,
                    'reason': 'No similar products found'
                })
        
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
    
    def calculate_price_difference(self, farm2bag_product: Dict[str, Any], 
                                 competitor_product: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate price differences between Farm2bag and competitor product.
        
        Args:
            farm2bag_product: Farm2bag product data
            competitor_product: Competitor product data
            
        Returns:
            Dictionary with comparison results
        """
        farm2bag_price = farm2bag_product.get('price', 0.0)
        competitor_price = competitor_product.get('price', 0.0)
        
        farm2bag_price_per_unit = farm2bag_product.get('price_per_unit', 0.0)
        competitor_price_per_unit = competitor_product.get('price_per_unit', 0.0)
        
        # Calculate differences
        absolute_diff = farm2bag_price - competitor_price
        percentage_diff = (absolute_diff / competitor_price * 100) if competitor_price > 0 else 0
        
        per_unit_diff = farm2bag_price_per_unit - competitor_price_per_unit
        per_unit_percentage = (per_unit_diff / competitor_price_per_unit * 100) if competitor_price_per_unit > 0 else 0
        
        return {
            'farm2bag_product': farm2bag_product,
            'competitor_product': competitor_product,
            'price_comparison': {
                'farm2bag_price': farm2bag_price,
                'competitor_price': competitor_price,
                'absolute_difference': absolute_diff,
                'percentage_difference': percentage_diff,
                'farm2bag_cheaper': absolute_diff < 0,
                'price_advantage': 'Farm2bag' if absolute_diff < 0 else 'Competitor'
            },
            'unit_price_comparison': {
                'farm2bag_price_per_unit': farm2bag_price_per_unit,
                'competitor_price_per_unit': competitor_price_per_unit,
                'per_unit_difference': per_unit_diff,
                'per_unit_percentage': per_unit_percentage,
                'better_unit_price': 'Farm2bag' if per_unit_diff < 0 else 'Competitor'
            },
            'similarity_score': competitor_product.get('similarity_score', 0)
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
            return {
                'total_matches': 0,
                'farm2bag_cheaper_count': 0,
                'competitor_cheaper_count': 0,
                'average_price_difference_percentage': 0,
                'max_savings_percentage': 0,
                'min_savings_percentage': 0
            }
        
        price_differences = [match['price_comparison']['percentage_difference'] for match in matches]
        farm2bag_cheaper = [match for match in matches if match['price_comparison']['farm2bag_cheaper']]
        
        return {
            'total_matches': len(matches),
            'farm2bag_cheaper_count': len(farm2bag_cheaper),
            'competitor_cheaper_count': len(matches) - len(farm2bag_cheaper),
            'farm2bag_cheaper_percentage': (len(farm2bag_cheaper) / len(matches)) * 100,
            'average_price_difference_percentage': sum(price_differences) / len(price_differences),
            'max_savings_percentage': min(price_differences) if price_differences else 0,  # Most negative = biggest savings
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
                'category': match['farm2bag_product'].get('normalized_category', 'unknown'),
                'site': match['competitor_product'].get('comparison_site', 'unknown'),
                'percentage_diff': match['price_comparison']['percentage_difference'],
                'farm2bag_cheaper': match['price_comparison']['farm2bag_cheaper'],
                'similarity_score': match['similarity_score']
            })
        
        df = pd.DataFrame(data)
        
        # Analysis by category
        category_analysis = df.groupby('category').agg({
            'percentage_diff': ['mean', 'count'],
            'farm2bag_cheaper': 'sum'
        }).round(2)
        
        # Analysis by site
        site_analysis = df.groupby('site').agg({
            'percentage_diff': ['mean', 'count'],
            'farm2bag_cheaper': 'sum'
        }).round(2)
        
        return {
            'by_category': category_analysis.to_dict(),
            'by_site': site_analysis.to_dict(),
            'overall_competitiveness': {
                'avg_price_difference': df['percentage_diff'].mean(),
                'competitive_categories': df.groupby('category')['farm2bag_cheaper'].sum().to_dict(),
                'most_competitive_site': df.groupby('site')['percentage_diff'].mean().idxmin() if len(df) > 0 else None
            }
        }