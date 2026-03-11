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
import asyncio
import re

# Import scraper components
from scraper_routes import scraper_router, init_scraper_services
from scheduler_service import SchedulerService

# Import new product and auth components
from product_routes import product_router, init_product_service
from auth_routes import auth_router, init_jwt_auth_service


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
app.include_router(product_router)
app.include_router(auth_router)

# Initialize scraper services
scheduler_service_instance = None

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    global scheduler_service_instance
    
    try:
        # Initialize scraper services with database
        init_scraper_services(db)
        
        # Initialize product service
        init_product_service()
        
        # Initialize JWT auth service
        init_jwt_auth_service(db)
        
        # Start scheduler service
        from scraper_routes import scheduler_service
        if scheduler_service:
            await scheduler_service.start()
            scheduler_service_instance = scheduler_service
            logger.info("Scheduler service started successfully")
        
        logger.info("All services initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")


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


# ── URL-based Product Scraping (simple drop-links flow) ──────────────
from url_scraper import scrape_multiple_urls
from scraper_models import ScrapeRequest, ScrapingStatus

class ScrapeUrlsRequest(BaseModel):
    urls: List[str] = Field(..., description="List of product page URLs to scrape")


class ScrapeProductRequest(BaseModel):
    product_query: str = Field(..., min_length=2, description="Single product name or search query")
    sites: List[str] | None = Field(default=None, description="Optional specific site keys to scrape")


def _price_to_float(value) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip()
    if not text:
        return None
    cleaned = re.sub(r"[^0-9.,]", "", text)
    if not cleaned:
        return None
    # Keep dot as decimal separator and remove thousands commas.
    cleaned = cleaned.replace(",", "")
    try:
        return float(cleaned)
    except ValueError:
        return None

@app.post("/api/scrape-urls")
async def scrape_urls(request: ScrapeUrlsRequest):
    """
    Drop product URLs → auto-scrape product details → compare.
    No config needed. Just paste links.
    """
    if not request.urls:
        return {"products": [], "message": "No URLs provided"}
    if len(request.urls) > 10:
        return {"error": "Maximum 10 URLs per request", "products": []}

    results = await scrape_multiple_urls(request.urls)
    return {
        "products": results,
        "total": len(results),
        "successful": sum(1 for r in results if r.get("success")),
        "message": f"Scraped {len(results)} URLs"
    }


@app.post("/api/scrape-product")
async def scrape_single_product(request: ScrapeProductRequest):
    """
    Input one product query and scrape it across configured enabled sites.
    This endpoint wraps the async task API and waits for completion.
    """
    from scraper_routes import scraper_service

    if not scraper_service or not scraper_service.is_available():
        return {"error": "Scraper service not available", "products": []}

    query = request.product_query.strip()
    if not query:
        return {"error": "product_query is required", "products": []}

    scrape_request = ScrapeRequest(
        product_query=query,
        sites=request.sites,
        generate_report=False,
        store_data=False
    )

    start_response = await scraper_service.start_scraping(scrape_request)
    task_id = start_response.task_id

    timeout_seconds = 120
    poll_interval_seconds = 1
    elapsed = 0

    while elapsed < timeout_seconds:
        task_result = await scraper_service.get_task_status(task_id)
        if task_result and task_result.status == ScrapingStatus.COMPLETED:
            pipeline_stats = task_result.pipeline_stats or {}
            query_products = pipeline_stats.get("query_products_flat", [])
            sites_attempted = pipeline_stats.get("sites_scraped", [])

            products = [
                {
                    "site": p.get("site"),
                    "name": p.get("name"),
                    "price": p.get("price"),
                    "url": p.get("url"),
                    "image": p.get("image_url"),
                    "description": p.get("brand"),
                    "success": True
                }
                for p in query_products
            ]

            comparable = []
            for item in products:
                price_value = _price_to_float(item.get("price"))
                if price_value is None:
                    continue
                comparable.append({**item, "price": round(price_value, 2)})

            comparison = None
            if comparable:
                comparable.sort(key=lambda x: x["price"])
                cheapest = comparable[0]
                highest = comparable[-1]
                spread_abs = round(highest["price"] - cheapest["price"], 2)
                spread_pct = round((spread_abs / cheapest["price"]) * 100, 2) if cheapest["price"] > 0 else None

                price_table = []
                for row in comparable:
                    delta = round(row["price"] - cheapest["price"], 2)
                    delta_pct = round((delta / cheapest["price"]) * 100, 2) if cheapest["price"] > 0 else None
                    price_table.append({
                        "site": row.get("site"),
                        "price": row["price"],
                        "difference_from_best": delta,
                        "difference_percent_from_best": delta_pct,
                        "url": row.get("url"),
                    })

                comparison = {
                    "sites_with_prices": len(comparable),
                    "best_price": {
                        "site": cheapest.get("site"),
                        "price": cheapest["price"],
                        "url": cheapest.get("url"),
                    },
                    "highest_price": {
                        "site": highest.get("site"),
                        "price": highest["price"],
                        "url": highest.get("url"),
                    },
                    "price_spread": {
                        "absolute": spread_abs,
                        "percent_vs_best": spread_pct,
                    },
                    "price_table": price_table,
                }

            return {
                "task_id": task_id,
                "status": "completed",
                "product_query": query,
                "requested_sites": request.sites,
                "sites_attempted": sites_attempted,
                "sites_returned": [p.get("site") for p in products],
                "products": products,
                "total": len(products),
                "successful": len(products),
                "comparison": comparison
            }

        if task_result and task_result.status == ScrapingStatus.FAILED:
            return {
                "task_id": task_id,
                "status": "failed",
                "error": task_result.error_message or "Scraping failed",
                "products": []
            }

        await asyncio.sleep(poll_interval_seconds)
        elapsed += poll_interval_seconds

    return {
        "task_id": task_id,
        "status": "running",
        "message": "Scraping is still running. Check task status API for updates.",
        "products": []
    }

