"""
Pydantic models for the grocery price scraper API.
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum


class ScrapingStatus(str, Enum):
    """Status of scraping operations."""
    PENDING = "pending"
    RUNNING = "running" 
    COMPLETED = "completed"
    FAILED = "failed"


class ScheduleInterval(str, Enum):
    """Available scheduling intervals."""
    HOURLY = "hourly"
    DAILY = "daily" 
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class ScrapeRequest(BaseModel):
    """Request model for scraping operations."""
    categories: Optional[List[str]] = Field(None, description="Categories to scrape (vegetables, fruits, dairy, grains)")
    sites: Optional[List[str]] = Field(None, description="Sites to scrape (bigbasket, jiomart, amazon_fresh, flipkart_grocery)")
    generate_report: bool = Field(True, description="Whether to generate Excel report")
    store_data: bool = Field(True, description="Whether to store data in database")


class ScrapeResponse(BaseModel):
    """Response model for scraping operations."""
    task_id: str = Field(..., description="Unique task identifier")
    status: ScrapingStatus = Field(..., description="Current status of the task")
    message: str = Field(..., description="Status message")
    started_at: datetime = Field(..., description="When the task started")
    estimated_duration: Optional[int] = Field(None, description="Estimated duration in seconds")


class ScrapeResult(BaseModel):
    """Detailed scraping result model."""
    task_id: str
    status: ScrapingStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    execution_time: Optional[float] = None
    farm2bag_products: int = 0
    competitor_products: int = 0
    total_matches: int = 0
    sites_scraped: List[str] = []
    categories_processed: List[str] = []
    report_path: Optional[str] = None
    error_message: Optional[str] = None
    pipeline_stats: Optional[Dict[str, Any]] = None


class ScheduleRequest(BaseModel):
    """Request model for scheduling operations."""
    name: str = Field(..., description="Schedule name/identifier")
    interval: ScheduleInterval = Field(..., description="Schedule interval")
    hour: Optional[int] = Field(6, description="Hour to run (for daily/weekly)", ge=0, le=23)
    minute: Optional[int] = Field(0, description="Minute to run", ge=0, le=59)
    day_of_week: Optional[int] = Field(1, description="Day of week (1=Monday, 7=Sunday) for weekly", ge=1, le=7)
    categories: Optional[List[str]] = None
    sites: Optional[List[str]] = None
    enabled: bool = Field(True, description="Whether the schedule is active")


class ScheduleResponse(BaseModel):
    """Response model for schedule operations."""
    id: str
    name: str
    interval: ScheduleInterval
    next_run: Optional[datetime]
    last_run: Optional[datetime] 
    enabled: bool
    created_at: datetime
    config: Dict[str, Any]


class DatabaseStats(BaseModel):
    """Database statistics model."""
    total_products: int
    products_by_site: Dict[str, int]
    latest_snapshot: Optional[str]
    date_range: Dict[str, Any]
    total_comparisons: int


class ApiKeyCreate(BaseModel):
    """Model for creating API keys."""
    name: str = Field(..., description="Name/description for the API key")
    expires_days: Optional[int] = Field(365, description="Days until expiration (null = never)", ge=1)


class ApiKeyResponse(BaseModel):
    """Response model for API key creation."""
    key_id: str
    name: str
    api_key: str
    expires_at: Optional[datetime]
    created_at: datetime


class ApiKeyInfo(BaseModel):
    """API key information (without the actual key)."""
    key_id: str
    name: str
    expires_at: Optional[datetime]
    created_at: datetime
    last_used: Optional[datetime]
    is_active: bool