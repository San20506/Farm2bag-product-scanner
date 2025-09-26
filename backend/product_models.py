"""
Pydantic models for product catalog and price comparison API endpoints.
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum


class ProductCategory(str, Enum):
    """Available product categories."""
    VEGETABLES = "vegetables"
    FRUITS = "fruits"
    DAIRY = "dairy"
    GRAINS = "grains"
    BAKERY = "bakery"
    GENERAL = "general"


class ProductSite(str, Enum):
    """Available scraping sites."""
    FARM2BAG = "farm2bag"
    BIGBASKET = "bigbasket"
    JIOMART = "jiomart"
    AMAZON_FRESH = "amazon_fresh"
    FLIPKART_GROCERY = "flipkart_grocery"


class ProductBase(BaseModel):
    """Base product model."""
    name: str
    normalized_name: Optional[str] = None
    price: float
    unit: str
    size: str
    normalized_unit: Optional[str] = None
    normalized_size: Optional[float] = None
    price_per_unit: Optional[float] = None
    category: str
    normalized_category: Optional[str] = None
    brand: str
    normalized_brand: Optional[str] = None
    url: Optional[str] = None
    image_url: Optional[str] = None
    availability: bool = True
    site: str


class Product(ProductBase):
    """Product model with database fields."""
    id: int
    scraped_at: datetime
    created_at: datetime


class ProductResponse(ProductBase):
    """Product response model for API."""
    id: int
    scraped_at: datetime
    competitor_prices: Optional[List['CompetitorPrice']] = None


class CompetitorPrice(BaseModel):
    """Competitor price information."""
    site: str
    price: float
    price_per_unit: Optional[float] = None
    price_difference: Optional[float] = None
    percentage_difference: Optional[float] = None
    is_cheaper: Optional[bool] = None
    url: Optional[str] = None
    scraped_at: datetime


class PriceHistory(BaseModel):
    """Price history for a product."""
    date: str
    price: float
    price_per_unit: Optional[float] = None
    site: str


class ProductSearchResponse(BaseModel):
    """Response for product search."""
    products: List[ProductResponse]
    total_count: int
    page: int
    page_size: int
    categories: List[str]
    sites: List[str]


class CategoryInfo(BaseModel):
    """Category information."""
    name: str
    display_name: str
    product_count: int
    sites_available: List[str]


class ProductDetailResponse(ProductBase):
    """Detailed product response with price comparisons and history."""
    id: int
    scraped_at: datetime
    competitor_prices: List[CompetitorPrice]
    price_history: List[PriceHistory]
    similar_products: Optional[List[ProductResponse]] = None


class ProductListQuery(BaseModel):
    """Query parameters for product listing."""
    category: Optional[str] = None
    site: Optional[str] = None
    search: Optional[str] = None
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)
    sort_by: str = Field("name", pattern="^(name|price|scraped_at|price_per_unit)$")
    sort_order: str = Field("asc", pattern="^(asc|desc)$")


# Update forward references
ProductResponse.model_rebuild()
ProductDetailResponse.model_rebuild()