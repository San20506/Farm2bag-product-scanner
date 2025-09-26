"""
FastAPI routes for product catalog and price comparison endpoints.
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional
from datetime import datetime

from product_models import (
    ProductResponse, ProductDetailResponse, ProductSearchResponse,
    CategoryInfo, CompetitorPrice, ProductListQuery
)
from product_service import ProductService
from auth_service import AuthService
from scraper_routes import get_current_key_id  # Reuse existing auth


# Router for product endpoints  
product_router = APIRouter(prefix="/api", tags=["Product Catalog"])

# Global service - will be initialized in main server
product_service: Optional[ProductService] = None


def init_product_service():
    """Initialize product service."""
    global product_service
    product_service = ProductService()


# Product catalog endpoints
@product_router.get("/products", response_model=ProductSearchResponse)
async def get_products(
    category: Optional[str] = Query(None, description="Filter by category"),
    site: Optional[str] = Query(None, description="Filter by site"),
    search: Optional[str] = Query(None, description="Search in product names"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    sort_by: str = Query("name", pattern="^(name|price|scraped_at|price_per_unit)$", description="Sort field"),
    sort_order: str = Query("asc", pattern="^(asc|desc)$", description="Sort order"),
    latest_only: bool = Query(True, description="Show only latest scraped products"),
    key_id: str = Depends(get_current_key_id)
):
    """
    Get product catalog with filtering, searching, and pagination.
    
    This endpoint provides the main product browsing functionality for the frontend.
    Returns products with competitor pricing information when available.
    """
    if not product_service or not product_service.is_available():
        raise HTTPException(status_code=503, detail="Product service not available")
    
    try:
        query = ProductListQuery(
            category=category,
            site=site,
            search=search,
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        result = await product_service.get_products(query, latest_only=latest_only)
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get products: {str(e)}")


@product_router.get("/products/search", response_model=List[ProductResponse])  
async def search_products(
    q: str = Query(..., min_length=2, description="Search query"),
    limit: int = Query(20, ge=1, le=50, description="Maximum results"),
    key_id: str = Depends(get_current_key_id)
):
    """
    Search products by name or description.
    
    Provides fast search functionality for the frontend search bar.
    Returns basic product information for search results.
    """
    if not product_service or not product_service.is_available():
        raise HTTPException(status_code=503, detail="Product service not available")
    
    try:
        products = await product_service.search_products(q, limit)
        return products
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@product_router.get("/products/{product_id}", response_model=ProductDetailResponse)
async def get_product_details(
    product_id: int,
    key_id: str = Depends(get_current_key_id)
):
    """
    Get detailed information for a specific product.
    
    Includes competitor prices, price history, and similar products.
    This is used for product detail pages and comparison views.
    """
    if not product_service or not product_service.is_available():
        raise HTTPException(status_code=503, detail="Product service not available")
    
    try:
        product = await product_service.get_product_by_id(product_id)
        
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        return product
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get product details: {str(e)}")


@product_router.get("/prices/{product_id}", response_model=List[CompetitorPrice])
async def get_current_prices(
    product_id: int,
    key_id: str = Depends(get_current_key_id)
):
    """
    Get current competitor prices for a specific product.
    
    Returns real-time price comparison data for the specified product
    across all available competitor sites.
    """
    if not product_service or not product_service.is_available():
        raise HTTPException(status_code=503, detail="Product service not available")
    
    try:
        prices = await product_service.get_current_prices(product_id)
        return prices
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get current prices: {str(e)}")


@product_router.get("/prices/history/{product_id}")
async def get_price_history(
    product_id: int,
    days: int = Query(30, ge=1, le=365, description="Number of days of history"),
    key_id: str = Depends(get_current_key_id)
):
    """
    Get price history timeseries for a specific product.
    
    Returns historical pricing data for charts and trend analysis.
    Used by the frontend for price history graphs.
    """
    if not product_service or not product_service.is_available():
        raise HTTPException(status_code=503, detail="Product service not available")
    
    try:
        # Get product details to access its normalized name and site
        product = await product_service.get_product_by_id(product_id)
        
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        # Return the price history from the product details
        # (This could be optimized to call the service directly with days parameter)
        return product.price_history
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get price history: {str(e)}")


@product_router.get("/categories", response_model=List[CategoryInfo])
async def get_categories(key_id: str = Depends(get_current_key_id)):
    """
    Get all available product categories.
    
    Returns category metadata including product counts and available sites.
    Used for category navigation and filtering in the frontend.
    """
    if not product_service or not product_service.is_available():
        raise HTTPException(status_code=503, detail="Product service not available")
    
    try:
        categories = await product_service.get_categories()
        return categories
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get categories: {str(e)}")


# Health check and test endpoints
@product_router.get("/test")
async def api_health_check():
    """
    Health check endpoint for frontend/backend integration testing.
    
    Returns system status and available services for debugging and monitoring.
    This endpoint does not require authentication.
    """
    try:
        services_status = {
            "product_service": product_service.is_available() if product_service else False,
            "timestamp": datetime.utcnow(),
            "api_version": "1.0.0"
        }
        
        # Test database connectivity if available
        if product_service and product_service.is_available():
            try:
                # Try to get category count as a simple connectivity test
                categories = await product_service.get_categories()
                services_status["database_categories"] = len(categories)
            except Exception as e:
                services_status["database_error"] = str(e)
        
        return {
            "status": "healthy" if services_status["product_service"] else "degraded",
            "services": services_status,
            "message": "Product catalog API is operational"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "services": {"product_service": False},
            "message": f"Health check failed: {str(e)}",
            "timestamp": datetime.utcnow()
        }


@product_router.get("/stats")
async def get_api_stats(key_id: str = Depends(get_current_key_id)):
    """
    Get API and database statistics.
    
    Provides overview statistics for admin dashboard.
    """
    if not product_service or not product_service.is_available():
        raise HTTPException(status_code=503, detail="Product service not available")
    
    try:
        # Get basic stats from the scraper database
        stats = product_service.db.get_statistics() if product_service.db else {}
        
        # Add API-specific stats
        api_stats = {
            "database_stats": stats,
            "api_info": {
                "version": "1.0.0",
                "endpoints_available": [
                    "/api/products - Product catalog",
                    "/api/products/{id} - Product details", 
                    "/api/products/search - Product search",
                    "/api/prices/{id} - Current prices",
                    "/api/prices/history/{id} - Price history",
                    "/api/categories - Available categories"
                ],
                "authentication": "API key required",
                "last_updated": datetime.utcnow()
            }
        }
        
        return api_stats
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")