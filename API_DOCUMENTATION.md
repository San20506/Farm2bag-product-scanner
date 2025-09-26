# 🛒 Grocery Price Scraper API Documentation

## Overview

Complete REST API for grocery price scraping, comparison, and management with dual authentication system (API keys + JWT tokens).

**Base URL**: `http://localhost:8001` (local development)

## 🔐 Authentication

The API supports two authentication methods:

### 1. API Keys (For Product Catalog & Scraping Operations)
- **Header**: `X-API-Key: your-api-key` or `Authorization: Bearer your-api-key`
- **Use Case**: Product catalog access, scraping operations, scheduling
- **Creation**: `POST /api/scraper/auth/keys`

### 2. JWT Tokens (For User Management)
- **Header**: `Authorization: Bearer jwt-token`
- **Use Case**: User authentication, profile management
- **Expiration**: 24 hours
- **Refresh**: `POST /api/auth/refresh`

---

## 📦 Product Catalog API

### Get Products Catalog
```http
GET /api/products
```

**Parameters:**
- `category` (optional): Filter by category (vegetables, fruits, dairy, grains, bakery)
- `site` (optional): Filter by site (farm2bag, bigbasket, jiomart, etc.)
- `search` (optional): Search in product names
- `page` (default: 1): Page number for pagination
- `page_size` (default: 20, max: 100): Items per page
- `sort_by` (default: name): Sort field (name, price, scraped_at, price_per_unit)
- `sort_order` (default: asc): Sort order (asc, desc)
- `latest_only` (default: true): Show only latest scraped products

**Response:**
```json
{
  "products": [
    {
      "id": 1,
      "name": "Organic Tomatoes",
      "normalized_name": "organic tomatoes",
      "price": 45.50,
      "unit": "kg",
      "size": "1",
      "price_per_unit": 45.50,
      "category": "vegetables",
      "brand": "Fresh Farm",
      "url": "https://example.com/product/1",
      "image_url": "https://example.com/images/tomatoes.jpg",
      "availability": true,
      "site": "farm2bag",
      "scraped_at": "2024-07-15T10:30:00",
      "competitor_prices": []
    }
  ],
  "total": 18,
  "page": 1,
  "page_size": 20,
  "total_pages": 1,
  "categories": ["vegetables", "fruits", "bakery"],
  "sites": ["farm2bag", "bigbasket", "jiomart"]
}
```

### Get Product Details
```http
GET /api/products/{product_id}
```

**Response:** Product with competitor prices and price history
```json
{
  "id": 1,
  "name": "Organic Tomatoes",
  // ... product fields
  "competitor_prices": [
    {
      "site": "bigbasket",
      "price": 48.00,
      "price_difference": 2.50,
      "percentage_difference": 5.49,
      "is_cheaper": false,
      "scraped_at": "2024-07-15T10:30:00"
    }
  ],
  "price_history": [
    {
      "date": "2024-07-15",
      "price": 45.50,
      "price_per_unit": 45.50,
      "site": "farm2bag"
    }
  ]
}
```

### Search Products
```http
GET /api/products/search?q=tomato&limit=10
```

**Parameters:**
- `q` (required, min: 2 chars): Search query
- `limit` (default: 20, max: 50): Maximum results

### Get Current Prices
```http
GET /api/prices/{product_id}
```

**Response:** Array of competitor prices for the product

### Get Price History
```http
GET /api/prices/history/{product_id}?days=30
```

**Parameters:**
- `days` (default: 30, max: 365): Number of days of history

### Get Categories
```http
GET /api/categories
```

**Response:**
```json
[
  {
    "name": "vegetables",
    "display_name": "Vegetables",
    "product_count": 8,
    "sites_available": ["farm2bag", "bigbasket", "jiomart"]
  }
]
```

---

## 🔑 JWT Authentication API

### Register User
```http
POST /api/auth/register
```

**Request:**
```json
{
  "username": "john_doe",
  "email": "john@example.com",
  "password": "secure_password",
  "full_name": "John Doe"
}
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 86400,
  "user": {
    "id": "uuid-here",
    "username": "john_doe",
    "email": "john@example.com",
    "full_name": "John Doe",
    "is_active": true,
    "created_at": "2024-07-15T10:30:00"
  }
}
```

### Login User
```http
POST /api/auth/login
```

**Request:**
```json
{
  "username": "john_doe",
  "password": "secure_password"
}
```

### Get Current User
```http
GET /api/auth/me
```
*Requires JWT token*

### Refresh Token
```http
POST /api/auth/refresh
```
*Requires valid JWT token*

### Logout
```http
POST /api/auth/logout
```
*Requires JWT token*

### Authentication Status
```http
GET /api/auth/status
```
*Public endpoint - returns auth system status*

---

## 🤖 Scraper Management API

### Create API Key
```http
POST /api/scraper/auth/keys
```

**Request:**
```json
{
  "name": "My Frontend App",
  "expires_days": 365
}
```

### Start Scraping
```http
POST /api/scraper/scrape
```
*Requires API key*

**Request:**
```json
{
  "categories": ["vegetables", "fruits"],
  "sites": ["bigbasket", "jiomart"],
  "generate_report": true,
  "store_data": true
}
```

### Get Scraping Tasks
```http
GET /api/scraper/tasks?limit=10
```
*Requires API key*

### Get Scraper Status
```http
GET /api/scraper/status
```
*Requires API key*

### Get Database Statistics
```http
GET /api/scraper/stats
```
*Requires API key*

---

## 📅 Scheduling API

### Create Schedule
```http
POST /api/scraper/schedules
```
*Requires API key*

**Request:**
```json
{
  "name": "Daily Morning Scrape",
  "interval": "daily",
  "hour": 6,
  "minute": 0,
  "categories": ["vegetables", "fruits"],
  "sites": ["bigbasket", "jiomart"],
  "enabled": true
}
```

### List Schedules
```http
GET /api/scraper/schedules
```
*Requires API key*

### Get Schedule Details
```http
GET /api/scraper/schedules/{schedule_id}
```
*Requires API key*

### Update Schedule
```http
PUT /api/scraper/schedules/{schedule_id}
```
*Requires API key*

### Delete Schedule
```http
DELETE /api/scraper/schedules/{schedule_id}
```
*Requires API key*

---

## 🔧 Utility Endpoints

### Health Check
```http
GET /api/test
```
*Public endpoint - no authentication required*

**Response:**
```json
{
  "status": "healthy",
  "services": {
    "product_service": true,
    "database_categories": 3,
    "timestamp": "2024-07-15T10:30:00",
    "api_version": "1.0.0"
  },
  "message": "Product catalog API is operational"
}
```

### API Statistics
```http
GET /api/stats
```
*Requires API key*

---

## 🚨 Error Responses

### Authentication Errors
```json
{
  "detail": "API key required. Provide via Authorization header (Bearer token) or X-API-Key header."
}
```

### Validation Errors
```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

### Server Errors
```json
{
  "detail": "Product service not available"
}
```

---

## 📊 Rate Limits

- **API Keys**: No specific rate limits (subject to server capacity)
- **JWT Endpoints**: Standard rate limiting applied
- **Public Endpoints**: Basic rate limiting for abuse prevention

## 🔄 Data Freshness

- **Products**: Updated based on scraping schedule (default: daily at 6 AM)
- **Prices**: Real-time comparison when accessing product details
- **Categories**: Updated when new products are scraped
- **History**: Stored daily snapshots for trending analysis

## 📝 Response Codes

- `200 OK` - Success
- `201 Created` - Resource created successfully
- `400 Bad Request` - Invalid request parameters
- `401 Unauthorized` - Missing or invalid authentication
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Resource not found
- `422 Unprocessable Entity` - Validation error
- `500 Internal Server Error` - Server error
- `503 Service Unavailable` - Service temporarily unavailable