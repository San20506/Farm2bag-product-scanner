"""
FastAPI routes for the grocery price scraper API.
"""

from fastapi import APIRouter, HTTPException, Depends, Header, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Optional, Dict, Any
from datetime import datetime
import os

from scraper_models import (
    ScrapeRequest, ScrapeResponse, ScrapeResult, 
    ScheduleRequest, ScheduleResponse,
    DatabaseStats, ApiKeyCreate, ApiKeyResponse, ApiKeyInfo
)
from scraper_service import ScraperService
from scheduler_service import SchedulerService
from auth_service import AuthService


# Security scheme
security = HTTPBearer(auto_error=False)

# Router for scraper endpoints
scraper_router = APIRouter(prefix="/api/scraper", tags=["Grocery Price Scraper"])

# Global services - will be initialized in main server
scraper_service: Optional[ScraperService] = None
scheduler_service: Optional[SchedulerService] = None
auth_service: Optional[AuthService] = None


def init_scraper_services(db):
    """Initialize scraper services with database collections."""
    global scraper_service, scheduler_service, auth_service
    
    scraper_service = ScraperService(db.scraper_tasks)
    scheduler_service = SchedulerService(db.scraper_schedules, scraper_service)
    auth_service = AuthService(db.api_keys)


async def get_current_key_id(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    x_api_key: Optional[str] = Header(None)
) -> str:
    """
    Validate API key from Authorization header or X-API-Key header.
    
    Returns:
        Key ID if valid
        
    Raises:
        HTTPException if invalid or missing
    """
    if not auth_service:
        raise HTTPException(status_code=500, detail="Authentication service not available")
    
    # Get API key from headers
    api_key = None
    if credentials and credentials.credentials:
        api_key = credentials.credentials
    elif x_api_key:
        api_key = x_api_key
    
    if not api_key:
        raise HTTPException(
            status_code=401, 
            detail="API key required. Provide via Authorization header (Bearer token) or X-API-Key header."
        )
    
    # Validate API key
    key_id = await auth_service.validate_api_key(api_key)
    if not key_id:
        raise HTTPException(status_code=403, detail="Invalid or expired API key")
    
    return key_id


# Authentication endpoints (no API key required)
@scraper_router.post("/auth/keys", response_model=ApiKeyResponse)
async def create_api_key(request: ApiKeyCreate):
    """Create a new API key for accessing scraper endpoints."""
    if not auth_service:
        raise HTTPException(status_code=500, detail="Authentication service not available")
    
    try:
        return await auth_service.create_api_key(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create API key: {str(e)}")


@scraper_router.get("/auth/keys", response_model=List[ApiKeyInfo])
async def list_api_keys(key_id: str = Depends(get_current_key_id)):
    """List all API keys (admin function)."""
    if not auth_service:
        raise HTTPException(status_code=500, detail="Authentication service not available")
    
    return await auth_service.list_api_keys()


@scraper_router.delete("/auth/keys/{target_key_id}")
async def revoke_api_key(target_key_id: str, key_id: str = Depends(get_current_key_id)):
    """Revoke an API key."""
    if not auth_service:
        raise HTTPException(status_code=500, detail="Authentication service not available")
    
    success = await auth_service.revoke_api_key(target_key_id)
    if not success:
        raise HTTPException(status_code=404, detail="API key not found")
    
    return {"message": f"API key {target_key_id} revoked successfully"}


# Core scraper endpoints
@scraper_router.post("/scrape", response_model=ScrapeResponse)
async def start_scraping(request: ScrapeRequest, key_id: str = Depends(get_current_key_id)):
    """
    Start a new scraping operation.
    
    This endpoint triggers an asynchronous scraping pipeline that:
    1. Scrapes Farm2bag products
    2. Scrapes competitor products from configured sites
    3. Normalizes and compares product data
    4. Generates reports and stores results
    """
    if not scraper_service:
        raise HTTPException(status_code=500, detail="Scraper service not available")
    
    if not scraper_service.is_available():
        raise HTTPException(status_code=503, detail="Scraper engine not available")
    
    try:
        return await scraper_service.start_scraping(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start scraping: {str(e)}")


@scraper_router.get("/tasks/{task_id}", response_model=ScrapeResult)
async def get_task_status(task_id: str, key_id: str = Depends(get_current_key_id)):
    """Get the status and results of a scraping task."""
    if not scraper_service:
        raise HTTPException(status_code=500, detail="Scraper service not available")
    
    result = await scraper_service.get_task_status(task_id)
    if not result:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return result


@scraper_router.get("/tasks", response_model=List[ScrapeResult])
async def get_recent_tasks(
    limit: int = Query(10, ge=1, le=100),
    key_id: str = Depends(get_current_key_id)
):
    """Get recent scraping tasks and their results."""
    if not scraper_service:
        raise HTTPException(status_code=500, detail="Scraper service not available")
    
    return await scraper_service.get_recent_results(limit)


@scraper_router.get("/status", response_model=Dict[str, Any])
async def get_scraper_status(key_id: str = Depends(get_current_key_id)):
    """
    Get current scraper system status and statistics.
    """
    if not scraper_service:
        raise HTTPException(status_code=500, detail="Scraper service not available")
    
    try:
        stats = await scraper_service.get_database_stats()
        
        return {
            "service_available": scraper_service.is_available(),
            "active_tasks": len(scraper_service.active_tasks),
            "database_stats": stats.dict(),
            "system_info": {
                "timestamp": datetime.utcnow(),
                "version": "1.0.0"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")


@scraper_router.get("/stats", response_model=DatabaseStats)
async def get_database_stats(key_id: str = Depends(get_current_key_id)):
    """Get detailed database statistics."""
    if not scraper_service:
        raise HTTPException(status_code=500, detail="Scraper service not available")
    
    return await scraper_service.get_database_stats()


# Scheduling endpoints
@scraper_router.post("/schedules", response_model=ScheduleResponse)
async def create_schedule(request: ScheduleRequest, key_id: str = Depends(get_current_key_id)):
    """Create a new automated scraping schedule."""
    if not scheduler_service:
        raise HTTPException(status_code=500, detail="Scheduler service not available")
    
    try:
        return await scheduler_service.create_schedule(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create schedule: {str(e)}")


@scraper_router.get("/schedules", response_model=List[ScheduleResponse])
async def list_schedules(key_id: str = Depends(get_current_key_id)):
    """List all automated scraping schedules."""
    if not scheduler_service:
        raise HTTPException(status_code=500, detail="Scheduler service not available")
    
    return await scheduler_service.list_schedules()


@scraper_router.get("/schedules/{schedule_id}", response_model=ScheduleResponse)
async def get_schedule(schedule_id: str, key_id: str = Depends(get_current_key_id)):
    """Get details of a specific schedule."""
    if not scheduler_service:
        raise HTTPException(status_code=500, detail="Scheduler service not available")
    
    schedule = await scheduler_service.get_schedule(schedule_id)
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    return schedule


@scraper_router.put("/schedules/{schedule_id}", response_model=ScheduleResponse)
async def update_schedule(
    schedule_id: str, 
    request: ScheduleRequest,
    key_id: str = Depends(get_current_key_id)
):
    """Update an existing schedule."""
    if not scheduler_service:
        raise HTTPException(status_code=500, detail="Scheduler service not available")
    
    schedule = await scheduler_service.update_schedule(schedule_id, request)
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    return schedule


@scraper_router.delete("/schedules/{schedule_id}")
async def delete_schedule(schedule_id: str, key_id: str = Depends(get_current_key_id)):
    """Delete a schedule."""
    if not scheduler_service:
        raise HTTPException(status_code=500, detail="Scheduler service not available")
    
    success = await scheduler_service.delete_schedule(schedule_id)
    if not success:
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    return {"message": f"Schedule {schedule_id} deleted successfully"}


# Maintenance endpoints
@scraper_router.post("/maintenance/cleanup")
async def cleanup_old_data(
    days_to_keep: int = Query(90, ge=1, le=365),
    key_id: str = Depends(get_current_key_id)
):
    """Clean up old scraping data and results."""
    if not scraper_service:
        raise HTTPException(status_code=500, detail="Scraper service not available")
    
    try:
        result = await scraper_service.cleanup_old_data(days_to_keep)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cleanup failed: {str(e)}")


# Information endpoints (no auth required for basic info)
@scraper_router.get("/info")
async def get_api_info():
    """Get basic API information and available endpoints."""
    return {
        "name": "Grocery Price Scraper API",
        "version": "1.0.0", 
        "description": "REST API for automated grocery price scraping and comparison",
        "endpoints": {
            "scraping": [
                "POST /api/scraper/scrape - Start scraping operation",
                "GET /api/scraper/tasks/{task_id} - Get task status",
                "GET /api/scraper/tasks - List recent tasks"
            ],
            "scheduling": [
                "POST /api/scraper/schedules - Create schedule", 
                "GET /api/scraper/schedules - List schedules",
                "PUT /api/scraper/schedules/{id} - Update schedule",
                "DELETE /api/scraper/schedules/{id} - Delete schedule"
            ],
            "auth": [
                "POST /api/scraper/auth/keys - Create API key",
                "GET /api/scraper/auth/keys - List API keys",
                "DELETE /api/scraper/auth/keys/{id} - Revoke API key"
            ],
            "monitoring": [
                "GET /api/scraper/status - System status",
                "GET /api/scraper/stats - Database statistics"
            ]
        },
        "authentication": "API key required (Bearer token or X-API-Key header)",
        "supported_sites": ["BigBasket", "JioMart", "Amazon Fresh", "Flipkart Grocery"],
        "supported_categories": ["vegetables", "fruits", "dairy", "grains", "bakery"]
    }