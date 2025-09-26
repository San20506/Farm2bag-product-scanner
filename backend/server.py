from fastapi import FastAPI, APIRouter
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List
import uuid
from datetime import datetime

# Import scraper components
from scraper_routes import scraper_router, init_scraper_services
from scheduler_service import SchedulerService


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")


# Define Models
class StatusCheck(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class StatusCheckCreate(BaseModel):
    client_name: str

# Add your routes to the router instead of directly to app
@api_router.get("/")
async def root():
    return {"message": "Hello World"}

@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_dict = input.dict()
    status_obj = StatusCheck(**status_dict)
    _ = await db.status_checks.insert_one(status_obj.dict())
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    status_checks = await db.status_checks.find().to_list(1000)
    return [StatusCheck(**status_check) for status_check in status_checks]

# Include the routers in the main app
app.include_router(api_router)
app.include_router(scraper_router)

# Initialize scraper services
scheduler_service_instance = None

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    global scheduler_service_instance
    
    try:
        # Initialize scraper services with database
        init_scraper_services(db)
        
        # Start scheduler service
        from scraper_routes import scheduler_service
        if scheduler_service:
            await scheduler_service.start()
            scheduler_service_instance = scheduler_service
            logger.info("Scheduler service started successfully")
        
        logger.info("All scraper services initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize scraper services: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    global scheduler_service_instance
    
    try:
        # Stop scheduler service
        if scheduler_service_instance:
            await scheduler_service_instance.stop()
            logger.info("Scheduler service stopped")
        
        # Close database connection
        client.close()
        logger.info("Database connection closed")
        
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    """This is replaced by the new shutdown_event handler."""
    pass
