"""
Scraper service that integrates the grocery price scraper with FastAPI backend.
"""

import asyncio
import sys
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from loguru import logger
import uuid
import json

# Add the grocery_price_scraper to Python path
SCRAPER_DIR = Path(__file__).parent.parent / "grocery_price_scraper"
sys.path.insert(0, str(SCRAPER_DIR))

try:
    from runner import PriceComparisonRunner
except ImportError as e:
    logger.error(f"Failed to import scraper components: {e}")
    PriceComparisonRunner = None

from scraper_models import (
    ScrapeRequest, ScrapeResponse, ScrapeResult, ScrapingStatus, 
    DatabaseStats
)


class ScraperService:
    """
    Service class that manages grocery price scraping operations.
    """
    
    def __init__(self, db_collection):
        """
        Initialize the scraper service.
        
        Args:
            db_collection: MongoDB collection for storing task results
        """
        self.db = db_collection
        self.active_tasks: Dict[str, Dict[str, Any]] = {}
        self.config_dir = str(SCRAPER_DIR / "config")
        
        # Initialize the runner if available
        if PriceComparisonRunner:
            try:
                self.runner = PriceComparisonRunner(config_dir=self.config_dir)
                logger.info("Scraper service initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize scraper runner: {e}")
                self.runner = None
        else:
            self.runner = None
            logger.warning("Scraper runner not available - check scraper installation")
    
    def is_available(self) -> bool:
        """Check if the scraper service is available."""
        return self.runner is not None
    
    async def start_scraping(self, request: ScrapeRequest) -> ScrapeResponse:
        """
        Start a scraping operation asynchronously.
        
        Args:
            request: Scraping request parameters
            
        Returns:
            ScrapeResponse with task ID and status
        """
        if not self.is_available():
            raise RuntimeError("Scraper service is not available")
        
        # Generate unique task ID
        task_id = str(uuid.uuid4())
        start_time = datetime.utcnow()
        
        # Store task info
        task_info = {
            "task_id": task_id,
            "status": ScrapingStatus.PENDING,
            "request": request.dict(),
            "started_at": start_time,
            "estimated_duration": 60  # Default estimate: 60 seconds
        }
        
        self.active_tasks[task_id] = task_info
        
        # Start the scraping process asynchronously
        asyncio.create_task(self._run_scraping_pipeline(task_id, request))
        
        return ScrapeResponse(
            task_id=task_id,
            status=ScrapingStatus.PENDING,
            message="Scraping task queued successfully",
            started_at=start_time,
            estimated_duration=60
        )
    
    async def _run_scraping_pipeline(self, task_id: str, request: ScrapeRequest):
        """
        Internal method to run the scraping pipeline.
        
        Args:
            task_id: Unique task identifier
            request: Scraping request parameters
        """
        try:
            # Update status to running
            self.active_tasks[task_id]["status"] = ScrapingStatus.RUNNING
            start_time = datetime.utcnow()
            
            logger.info(f"Starting scraping pipeline for task {task_id}")
            
            # Run the pipeline
            results = await self.runner.run_full_pipeline(
                categories=request.categories,
                sites=request.sites,
                generate_report=request.generate_report,
                store_data=request.store_data
            )
            
            # Process results
            end_time = datetime.utcnow()
            execution_time = (end_time - start_time).total_seconds()
            
            pipeline_stats = results.get('pipeline_stats', {})
            
            result = ScrapeResult(
                task_id=task_id,
                status=ScrapingStatus.COMPLETED,
                started_at=start_time,
                completed_at=end_time,
                execution_time=execution_time,
                farm2bag_products=pipeline_stats.get('farm2bag_products', 0),
                competitor_products=pipeline_stats.get('competitor_products', 0),
                total_matches=pipeline_stats.get('total_matches', 0),
                sites_scraped=pipeline_stats.get('sites_scraped', []),
                categories_processed=pipeline_stats.get('categories_processed', []),
                report_path=results.get('report_path'),
                pipeline_stats=pipeline_stats
            )
            
            # Store result in database
            await self.db.insert_one(result.dict())
            
            # Update active task
            self.active_tasks[task_id].update({
                "status": ScrapingStatus.COMPLETED,
                "completed_at": end_time,
                "result": result.dict()
            })
            
            logger.info(f"Scraping pipeline completed successfully for task {task_id}")
            
        except Exception as e:
            # Handle errors
            end_time = datetime.utcnow()
            error_message = str(e)
            
            logger.error(f"Scraping pipeline failed for task {task_id}: {error_message}")
            
            result = ScrapeResult(
                task_id=task_id,
                status=ScrapingStatus.FAILED,
                started_at=self.active_tasks[task_id]["started_at"],
                completed_at=end_time,
                error_message=error_message
            )
            
            # Store error result in database
            await self.db.insert_one(result.dict())
            
            # Update active task
            self.active_tasks[task_id].update({
                "status": ScrapingStatus.FAILED,
                "completed_at": end_time,
                "error_message": error_message
            })
    
    async def get_task_status(self, task_id: str) -> Optional[ScrapeResult]:
        """
        Get the status of a scraping task.
        
        Args:
            task_id: Task identifier
            
        Returns:
            ScrapeResult if found, None otherwise
        """
        # Check active tasks first
        if task_id in self.active_tasks:
            task_info = self.active_tasks[task_id]
            
            if task_info["status"] in [ScrapingStatus.PENDING, ScrapingStatus.RUNNING]:
                return ScrapeResult(
                    task_id=task_id,
                    status=task_info["status"],
                    started_at=task_info["started_at"]
                )
            elif "result" in task_info:
                return ScrapeResult(**task_info["result"])
        
        # Check database for completed tasks
        task_doc = await self.db.find_one({"task_id": task_id})
        if task_doc:
            return ScrapeResult(**task_doc)
        
        return None
    
    async def get_recent_results(self, limit: int = 10) -> List[ScrapeResult]:
        """
        Get recent scraping results.
        
        Args:
            limit: Maximum number of results to return
            
        Returns:
            List of recent ScrapeResult objects
        """
        cursor = self.db.find().sort("started_at", -1).limit(limit)
        results = []
        
        async for doc in cursor:
            results.append(ScrapeResult(**doc))
            
        return results
    
    async def get_database_stats(self) -> DatabaseStats:
        """
        Get database statistics from the scraper database.
        
        Returns:
            DatabaseStats object
        """
        if not self.is_available():
            return DatabaseStats(
                total_products=0,
                products_by_site={},
                latest_snapshot=None,
                date_range={},
                total_comparisons=0
            )
        
        try:
            # Get stats from the scraper's database
            stats = self.runner.get_database_stats()
            
            return DatabaseStats(
                total_products=stats.get('total_products', 0),
                products_by_site=stats.get('products_by_site', {}),
                latest_snapshot=stats.get('latest_snapshot'),
                date_range=stats.get('date_range', {}),
                total_comparisons=stats.get('total_comparisons', 0)
            )
            
        except Exception as e:
            logger.error(f"Failed to get database stats: {e}")
            return DatabaseStats(
                total_products=0,
                products_by_site={},
                latest_snapshot=None,
                date_range={},
                total_comparisons=0
            )
    
    async def cleanup_old_data(self, days_to_keep: int = 90) -> Dict[str, Any]:
        """
        Clean up old data from the scraper database.
        
        Args:
            days_to_keep: Number of days to keep data
            
        Returns:
            Cleanup results
        """
        if not self.is_available():
            raise RuntimeError("Scraper service is not available")
        
        try:
            await self.runner.cleanup_old_data(days_to_keep)
            
            # Also cleanup old API task results
            cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
            result = await self.db.delete_many({"started_at": {"$lt": cutoff_date}})
            
            return {
                "success": True,
                "days_kept": days_to_keep,
                "api_tasks_deleted": result.deleted_count,
                "message": f"Cleaned up data older than {days_to_keep} days"
            }
            
        except Exception as e:
            logger.error(f"Failed to cleanup old data: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to cleanup old data"
            }