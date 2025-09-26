"""
Scheduler service for automated grocery price scraping.
"""

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import uuid
import asyncio
from loguru import logger

from scraper_models import (
    ScheduleRequest, ScheduleResponse, ScheduleInterval, 
    ScrapeRequest
)


class SchedulerService:
    """
    Service for managing automated scraping schedules.
    """
    
    def __init__(self, db_collection, scraper_service):
        """
        Initialize the scheduler service.
        
        Args:
            db_collection: MongoDB collection for storing schedules
            scraper_service: ScraperService instance for running scrapes
        """
        self.db = db_collection
        self.scraper_service = scraper_service
        self.scheduler = AsyncIOScheduler()
        self.active_schedules: Dict[str, Dict[str, Any]] = {}
        
        # Set up default schedule (daily at 6 AM)
        self.default_schedule = {
            "name": "default_daily_scrape",
            "interval": ScheduleInterval.DAILY,
            "hour": 6,
            "minute": 0,
            "categories": None,
            "sites": None,
            "enabled": True
        }
    
    async def start(self):
        """Start the scheduler and load existing schedules."""
        try:
            # Start the scheduler
            self.scheduler.start()
            logger.info("Scheduler service started")
            
            # Load existing schedules from database
            await self._load_schedules()
            
            # Create default schedule if none exist
            schedules = await self.list_schedules()
            if not schedules:
                await self._create_default_schedule()
                
        except Exception as e:
            logger.error(f"Failed to start scheduler service: {e}")
            raise
    
    async def stop(self):
        """Stop the scheduler."""
        try:
            self.scheduler.shutdown()
            logger.info("Scheduler service stopped")
        except Exception as e:
            logger.error(f"Failed to stop scheduler service: {e}")
    
    async def create_schedule(self, request: ScheduleRequest) -> ScheduleResponse:
        """
        Create a new automated schedule.
        
        Args:
            request: Schedule configuration
            
        Returns:
            ScheduleResponse with schedule details
        """
        # Generate unique schedule ID
        schedule_id = str(uuid.uuid4())
        
        # Create schedule document
        schedule_doc = {
            "id": schedule_id,
            "name": request.name,
            "interval": request.interval,
            "hour": request.hour,
            "minute": request.minute,
            "day_of_week": request.day_of_week,
            "categories": request.categories,
            "sites": request.sites,
            "enabled": request.enabled,
            "created_at": datetime.utcnow(),
            "last_run": None,
            "next_run": None
        }
        
        # Add to scheduler if enabled
        if request.enabled:
            next_run = self._add_job_to_scheduler(schedule_id, request)
            schedule_doc["next_run"] = next_run
        
        # Store in database
        await self.db.insert_one(schedule_doc)
        
        # Keep in memory
        self.active_schedules[schedule_id] = schedule_doc
        
        logger.info(f"Created schedule '{request.name}' with ID {schedule_id}")
        
        return ScheduleResponse(
            id=schedule_id,
            name=request.name,
            interval=request.interval,
            next_run=schedule_doc.get("next_run"),
            last_run=schedule_doc.get("last_run"),
            enabled=request.enabled,
            created_at=schedule_doc["created_at"],
            config={
                "hour": request.hour,
                "minute": request.minute,
                "day_of_week": request.day_of_week,
                "categories": request.categories,
                "sites": request.sites
            }
        )
    
    def _add_job_to_scheduler(self, schedule_id: str, request: ScheduleRequest) -> datetime:
        """
        Add a job to the APScheduler.
        
        Args:
            schedule_id: Unique schedule identifier
            request: Schedule configuration
            
        Returns:
            Next run datetime
        """
        # Create the trigger based on interval
        if request.interval == ScheduleInterval.HOURLY:
            trigger = IntervalTrigger(hours=1, start_date=datetime.utcnow())
        elif request.interval == ScheduleInterval.DAILY:
            trigger = CronTrigger(
                hour=request.hour,
                minute=request.minute
            )
        elif request.interval == ScheduleInterval.WEEKLY:
            trigger = CronTrigger(
                day_of_week=request.day_of_week - 1,  # APScheduler uses 0-6, we use 1-7
                hour=request.hour,
                minute=request.minute
            )
        elif request.interval == ScheduleInterval.MONTHLY:
            trigger = CronTrigger(
                day=1,  # First day of month
                hour=request.hour,
                minute=request.minute
            )
        else:
            raise ValueError(f"Unsupported interval: {request.interval}")
        
        # Add job to scheduler
        job = self.scheduler.add_job(
            func=self._execute_scheduled_scrape,
            trigger=trigger,
            args=[schedule_id],
            id=schedule_id,
            replace_existing=True
        )
        
        return job.next_run_time
    
    async def _execute_scheduled_scrape(self, schedule_id: str):
        """
        Execute a scheduled scraping operation.
        
        Args:
            schedule_id: Schedule identifier
        """
        try:
            logger.info(f"Executing scheduled scrape for schedule {schedule_id}")
            
            # Get schedule configuration
            schedule = self.active_schedules.get(schedule_id)
            if not schedule:
                # Try to load from database
                schedule_doc = await self.db.find_one({"id": schedule_id})
                if not schedule_doc:
                    logger.error(f"Schedule {schedule_id} not found")
                    return
                schedule = schedule_doc
            
            # Create scrape request
            scrape_request = ScrapeRequest(
                categories=schedule.get("categories"),
                sites=schedule.get("sites"),
                generate_report=True,
                store_data=True
            )
            
            # Start scraping
            response = await self.scraper_service.start_scraping(scrape_request)
            
            # Update last run time
            now = datetime.utcnow()
            await self.db.update_one(
                {"id": schedule_id},
                {"$set": {"last_run": now}}
            )
            
            if schedule_id in self.active_schedules:
                self.active_schedules[schedule_id]["last_run"] = now
            
            logger.info(f"Scheduled scrape started successfully: task_id={response.task_id}")
            
        except Exception as e:
            logger.error(f"Failed to execute scheduled scrape for {schedule_id}: {e}")
    
    async def list_schedules(self) -> List[ScheduleResponse]:
        """
        List all schedules.
        
        Returns:
            List of ScheduleResponse objects
        """
        cursor = self.db.find().sort("created_at", -1)
        schedules = []
        
        async for doc in cursor:
            # Get next run time from scheduler if job exists
            next_run = None
            if self.scheduler.get_job(doc["id"]):
                next_run = self.scheduler.get_job(doc["id"]).next_run_time
            
            schedules.append(ScheduleResponse(
                id=doc["id"],
                name=doc["name"],
                interval=doc["interval"],
                next_run=next_run,
                last_run=doc.get("last_run"),
                enabled=doc["enabled"],
                created_at=doc["created_at"],
                config={
                    "hour": doc.get("hour"),
                    "minute": doc.get("minute"),
                    "day_of_week": doc.get("day_of_week"),
                    "categories": doc.get("categories"),
                    "sites": doc.get("sites")
                }
            ))
        
        return schedules
    
    async def get_schedule(self, schedule_id: str) -> Optional[ScheduleResponse]:
        """
        Get a specific schedule by ID.
        
        Args:
            schedule_id: Schedule identifier
            
        Returns:
            ScheduleResponse if found, None otherwise
        """
        doc = await self.db.find_one({"id": schedule_id})
        if not doc:
            return None
        
        # Get next run time from scheduler
        next_run = None
        if self.scheduler.get_job(schedule_id):
            next_run = self.scheduler.get_job(schedule_id).next_run_time
        
        return ScheduleResponse(
            id=doc["id"],
            name=doc["name"],
            interval=doc["interval"],
            next_run=next_run,
            last_run=doc.get("last_run"),
            enabled=doc["enabled"],
            created_at=doc["created_at"],
            config={
                "hour": doc.get("hour"),
                "minute": doc.get("minute"),
                "day_of_week": doc.get("day_of_week"),
                "categories": doc.get("categories"),
                "sites": doc.get("sites")
            }
        )
    
    async def update_schedule(self, schedule_id: str, request: ScheduleRequest) -> Optional[ScheduleResponse]:
        """
        Update an existing schedule.
        
        Args:
            schedule_id: Schedule identifier
            request: Updated schedule configuration
            
        Returns:
            Updated ScheduleResponse if successful, None if not found
        """
        # Check if schedule exists
        existing = await self.db.find_one({"id": schedule_id})
        if not existing:
            return None
        
        # Remove existing job from scheduler
        if self.scheduler.get_job(schedule_id):
            self.scheduler.remove_job(schedule_id)
        
        # Update document
        update_doc = {
            "name": request.name,
            "interval": request.interval,
            "hour": request.hour,
            "minute": request.minute,
            "day_of_week": request.day_of_week,
            "categories": request.categories,
            "sites": request.sites,
            "enabled": request.enabled,
            "next_run": None
        }
        
        # Add to scheduler if enabled
        if request.enabled:
            next_run = self._add_job_to_scheduler(schedule_id, request)
            update_doc["next_run"] = next_run
        
        # Update in database
        await self.db.update_one(
            {"id": schedule_id},
            {"$set": update_doc}
        )
        
        # Update in memory
        if schedule_id in self.active_schedules:
            self.active_schedules[schedule_id].update(update_doc)
        
        logger.info(f"Updated schedule {schedule_id}")
        
        return await self.get_schedule(schedule_id)
    
    async def delete_schedule(self, schedule_id: str) -> bool:
        """
        Delete a schedule.
        
        Args:
            schedule_id: Schedule identifier
            
        Returns:
            True if deleted successfully, False if not found
        """
        # Remove from scheduler
        if self.scheduler.get_job(schedule_id):
            self.scheduler.remove_job(schedule_id)
        
        # Remove from database
        result = await self.db.delete_one({"id": schedule_id})
        
        # Remove from memory
        if schedule_id in self.active_schedules:
            del self.active_schedules[schedule_id]
        
        logger.info(f"Deleted schedule {schedule_id}")
        
        return result.deleted_count > 0
    
    async def _load_schedules(self):
        """Load existing schedules from database and add to scheduler."""
        cursor = self.db.find({"enabled": True})
        
        async for doc in cursor:
            try:
                # Convert to ScheduleRequest for processing
                request = ScheduleRequest(
                    name=doc["name"],
                    interval=doc["interval"],
                    hour=doc.get("hour", 6),
                    minute=doc.get("minute", 0),
                    day_of_week=doc.get("day_of_week", 1),
                    categories=doc.get("categories"),
                    sites=doc.get("sites"),
                    enabled=doc["enabled"]
                )
                
                # Add to scheduler
                next_run = self._add_job_to_scheduler(doc["id"], request)
                
                # Update next_run in database
                await self.db.update_one(
                    {"id": doc["id"]},
                    {"$set": {"next_run": next_run}}
                )
                
                # Keep in memory
                doc["next_run"] = next_run
                self.active_schedules[doc["id"]] = doc
                
                logger.info(f"Loaded schedule '{doc['name']}' (ID: {doc['id']})")
                
            except Exception as e:
                logger.error(f"Failed to load schedule {doc['id']}: {e}")
    
    async def _create_default_schedule(self):
        """Create the default daily schedule."""
        try:
            request = ScheduleRequest(**self.default_schedule)
            await self.create_schedule(request)
            logger.info("Created default daily scraping schedule (6 AM)")
        except Exception as e:
            logger.error(f"Failed to create default schedule: {e}")