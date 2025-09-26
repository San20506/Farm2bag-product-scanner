# 🏗️ Architecture Guide - Grocery Price Scraper

## System Overview

A full-stack grocery price comparison platform with automated scraping, real-time price analysis, and web-based dashboard.

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React Frontend │    │  FastAPI Backend │    │ Python Scrapers │
│                 │    │                 │    │                 │
│  - Dashboard    │◄──►│  - REST API     │◄──►│  - Modular      │
│  - Auth UI      │    │  - JWT Auth     │    │  - Async        │
│  - Charts       │    │  - API Keys     │    │  - Scheduled    │
│  - Admin Panel  │    │  - Validation   │    │  - Configurable │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │              ┌─────────────────┐              │
         │              │   Databases     │              │
         └──────────────►│                 │◄─────────────┘
                        │ - MongoDB (API) │
                        │ - SQLite (Data) │
                        └─────────────────┘
```

## 📂 Project Structure

```
/app/
├── backend/                    # FastAPI Backend
│   ├── server.py              # Main FastAPI application
│   ├── product_routes.py      # Product catalog endpoints
│   ├── scraper_routes.py      # Scraper management endpoints
│   ├── auth_routes.py         # JWT authentication endpoints
│   ├── product_service.py     # Product business logic
│   ├── scraper_service.py     # Scraper integration service
│   ├── jwt_auth.py           # JWT authentication service
│   ├── auth_service.py       # API key authentication
│   ├── product_models.py     # Product data models
│   ├── scraper_models.py     # Scraper data models
│   └── requirements.txt      # Python dependencies
│
├── frontend/                   # React Frontend
│   ├── src/
│   │   ├── components/       # React components
│   │   ├── contexts/         # React context providers
│   │   │   ├── AuthContext.js    # JWT authentication
│   │   │   └── ApiContext.js     # API integration
│   │   ├── hooks/           # Custom React hooks
│   │   ├── lib/             # Utility libraries
│   │   └── App.js           # Main application
│   ├── public/              # Static assets
│   └── package.json         # Node.js dependencies
│
├── grocery_price_scraper/      # Python Scraper Module
│   ├── scrapers/            # Site-specific scrapers
│   │   ├── base_scraper.py  # Abstract base scraper
│   │   └── farm2bag_scraper.py  # Farm2bag implementation
│   ├── fetchers/            # HTTP/Playwright fetchers
│   ├── normalizer/          # Data normalization
│   ├── comparator/          # Price comparison logic
│   ├── reporter/            # Excel report generation
│   ├── config/              # Configuration files
│   │   ├── sites.yml       # Site scraping configs
│   │   └── compare_rules.yml   # Normalization rules
│   ├── db.py               # SQLite database wrapper
│   └── runner.py           # Main pipeline orchestrator
│
├── tests/                      # Test suites
├── API_DOCUMENTATION.md        # API reference
├── SETUP_GUIDE.md             # Installation instructions
└── README.md                  # Project overview
```

## 🔧 Core Components

### 1. Backend Services

#### FastAPI Application (`server.py`)
- **Purpose**: Main application entry point and service coordination
- **Key Features**:
  - CORS configuration for frontend integration
  - Service initialization and lifecycle management
  - Router registration and URL routing
  - Database connection management

#### Product Service (`product_service.py`)
- **Purpose**: Product catalog and price comparison business logic
- **Key Features**:
  - Product querying with filtering/pagination
  - Competitor price analysis
  - Price history tracking
  - Category management

#### Scraper Service (`scraper_service.py`)
- **Purpose**: Integration between API and scraping pipeline
- **Key Features**:
  - Async task management
  - Scraping pipeline orchestration
  - Result storage and retrieval
  - Status tracking

#### Authentication Services
- **JWT Auth (`jwt_auth.py`)**: User authentication for dashboard
- **API Key Auth (`auth_service.py`)**: Programmatic API access
- **Routes (`auth_routes.py`)**: Authentication endpoints

### 2. Frontend Architecture

#### Context Providers
- **AuthContext**: JWT token management, user state
- **ApiContext**: API integration, request handling

#### Component Structure
```
components/
├── layout/
│   ├── Navbar.js           # Navigation with auth
│   └── Sidebar.js          # Admin panel sidebar
├── auth/
│   ├── LoginForm.js        # JWT login
│   └── RegisterForm.js     # User registration
├── products/
│   ├── ProductCatalog.js   # Main product listing
│   ├── ProductCard.js      # Individual product display
│   ├── ProductDetails.js   # Detailed product view
│   └── SearchBar.js        # Product search
├── charts/
│   ├── PriceChart.js       # Price history visualization
│   └── ComparisonChart.js  # Competitor comparison
└── admin/
    ├── ScrapingPanel.js    # Scraper management
    └── ScheduleManager.js  # Schedule configuration
```

### 3. Scraper Architecture

#### Modular Design
```python
class ScraperBase(ABC):
    """Abstract base for all scrapers"""
    
    @abstractmethod
    async def scrape_products(self, categories: List[str]) -> List[Dict]:
        """Site-specific product scraping"""
        pass
    
    @abstractmethod 
    async def scrape_product_details(self, product_url: str) -> Dict:
        """Detailed product information"""
        pass
```

#### Pipeline Flow
```
1. Configuration Loading (sites.yml, compare_rules.yml)
2. Site-Specific Scraping (Farm2bag, BigBasket, etc.)
3. Data Normalization (names, prices, units)
4. Price Comparison (fuzzy matching, similarity scoring)
5. Report Generation (Excel, statistics)
6. Database Storage (SQLite for history, MongoDB for API)
```

## 🔄 Data Flow

### 1. Product Catalog Flow
```
Frontend Request → API Authentication → Product Service → SQLite Query → 
Response Formatting → JSON API Response → Frontend Display
```

### 2. Scraping Flow
```
Schedule Trigger → Scraper Service → Pipeline Orchestrator → 
Site Scrapers → Data Normalizer → Price Comparator → 
Database Storage → Report Generation → Status Update
```

### 3. Authentication Flow
```
User Login → JWT Token Generation → Token Storage (localStorage) → 
API Request Headers → Token Validation → Protected Resource Access
```

## 🗄️ Database Design

### MongoDB Collections

#### Users Collection
```javascript
{
  "_id": ObjectId,
  "id": "uuid-string",
  "username": "string",
  "email": "string", 
  "password_hash": "bcrypt-hash",
  "full_name": "string",
  "is_active": boolean,
  "created_at": ISODate,
  "last_login": ISODate
}
```

#### API Keys Collection
```javascript
{
  "_id": ObjectId,
  "key_id": "uuid-string",
  "name": "string",
  "api_key_hash": "hashed-key",
  "expires_at": ISODate,
  "created_at": ISODate,
  "last_used": ISODate,
  "is_active": boolean
}
```

#### Scraper Tasks Collection
```javascript
{
  "_id": ObjectId,
  "task_id": "uuid-string",
  "status": "pending|running|completed|failed",
  "started_at": ISODate,
  "completed_at": ISODate,
  "execution_time": Number,
  "farm2bag_products": Number,
  "competitor_products": Number,
  "sites_scraped": ["string"],
  "categories_processed": ["string"],
  "error_message": "string"
}
```

### SQLite Schema

#### Products Table
```sql
CREATE TABLE products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    site TEXT NOT NULL,
    name TEXT NOT NULL,
    normalized_name TEXT,
    price REAL NOT NULL,
    unit TEXT,
    size TEXT,
    normalized_unit TEXT,
    normalized_size REAL,
    price_per_unit REAL,
    category TEXT,
    normalized_category TEXT,
    brand TEXT,
    normalized_brand TEXT,
    url TEXT,
    image_url TEXT,
    availability BOOLEAN,
    scraped_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Price Comparisons Table
```sql
CREATE TABLE price_comparisons (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    comparison_date DATE NOT NULL,
    farm2bag_product_id INTEGER,
    competitor_product_id INTEGER,
    price_difference REAL,
    percentage_difference REAL,
    similarity_score REAL,
    farm2bag_cheaper BOOLEAN,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 🔐 Security Architecture

### Authentication Layers

#### 1. JWT Authentication (Frontend Users)
- **Purpose**: Dashboard access, user sessions
- **Implementation**: 
  - bcrypt password hashing
  - HS256 JWT signing
  - 24-hour token expiration
  - Refresh token support

#### 2. API Key Authentication (Programmatic Access)
- **Purpose**: Product catalog, scraping operations
- **Implementation**:
  - UUID-based key generation
  - SHA-256 key hashing
  - Configurable expiration
  - Usage tracking

### Security Measures

#### Backend Protection
```python
# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request rate limiting (future enhancement)
# Authentication middleware
# Input validation with Pydantic
```

#### Frontend Protection
```javascript
// Token management
const token = localStorage.getItem('token');
axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;

// Automatic token refresh
// Route protection
// XSS prevention
```

## 📊 API Design

### RESTful Principles
- **Resource-based URLs**: `/api/products/{id}`
- **HTTP methods**: GET, POST, PUT, DELETE
- **Status codes**: 200, 201, 400, 401, 403, 404, 500
- **JSON responses**: Consistent format with error handling

### Authentication Strategy
```
Public Endpoints:
- GET /api/test
- GET /api/auth/status
- POST /api/auth/register
- POST /api/auth/login

API Key Protected:
- GET /api/products
- GET /api/categories  
- POST /api/scraper/scrape
- GET /api/scraper/status

JWT Protected:
- GET /api/auth/me
- POST /api/auth/refresh
```

### Response Format
```json
{
  "success": boolean,
  "data": object|array,
  "message": "string",
  "timestamp": "ISO-8601",
  "pagination": {
    "page": number,
    "page_size": number,
    "total": number,
    "total_pages": number
  }
}
```

## ⚡ Performance Considerations

### Backend Optimization
- **Async Operations**: FastAPI + async/await for I/O operations
- **Database Indexing**: Strategic indexes on frequently queried fields
- **Connection Pooling**: MongoDB connection management
- **Caching Strategy**: In-memory caching for frequently accessed data

### Frontend Optimization
- **Code Splitting**: React lazy loading for components
- **State Management**: Context providers for global state
- **API Optimization**: Request debouncing, caching
- **Bundle Optimization**: Webpack optimization for production builds

### Scraper Optimization
- **Rate Limiting**: Configurable delays between requests
- **Async Scraping**: Concurrent site processing
- **Error Resilience**: Retry mechanisms and graceful degradation
- **Data Deduplication**: Efficient storage and comparison algorithms

## 🚀 Deployment Architecture

### Development Setup
```
Local Machine:
├── Frontend: localhost:3000
├── Backend: localhost:8001
├── MongoDB: localhost:27017
└── SQLite: local file system
```

### Production Deployment
```
Cloud Infrastructure:
├── Frontend: CDN/Static hosting
├── Backend: Container orchestration
├── Database: Managed MongoDB service
├── Load Balancer: API gateway
└── Monitoring: Logging and metrics
```

### Container Architecture
```dockerfile
# Multi-stage Docker build
FROM node:16 AS frontend-build
# Frontend build stage

FROM python:3.11 AS backend
# Backend runtime

FROM nginx:alpine AS production
# Production serving
```

## 🔄 Integration Patterns

### Frontend-Backend Integration
- **API Client**: Axios with interceptors
- **Error Handling**: Centralized error management
- **Loading States**: UI feedback for async operations
- **Real-time Updates**: Polling for status updates

### Scraper-API Integration
- **Async Task Management**: Background job processing
- **Status Tracking**: Real-time scraping progress
- **Result Storage**: Efficient data persistence
- **Error Reporting**: Comprehensive error tracking

## 📈 Scalability Design

### Horizontal Scaling
- **Stateless Services**: API servers without local state
- **Database Clustering**: MongoDB replica sets
- **Load Distribution**: Multiple scraper workers
- **Caching Layers**: Redis for session and data caching

### Vertical Scaling
- **Resource Allocation**: CPU/memory optimization
- **Database Optimization**: Query performance tuning
- **Connection Pooling**: Efficient resource utilization
- **Background Processing**: Separate worker processes

---

This architecture provides a solid foundation for a scalable, maintainable grocery price comparison platform with clear separation of concerns and robust integration patterns.