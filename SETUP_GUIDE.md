# 🚀 Grocery Price Scraper - Complete Setup Guide

## Overview

This is a full-stack grocery price comparison platform with React frontend, FastAPI backend, and automated scraping capabilities.

## 📋 Prerequisites

- **Python 3.11+**
- **Node.js 16+** and **Yarn**
- **MongoDB** (running locally or remote)
- **Git**

## 🛠️ Backend Setup

### 1. Navigate to Backend Directory
```bash
cd /app/backend
```

### 2. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 3. Environment Configuration
Create `.env` file in `/app/backend/`:
```env
MONGO_URL=mongodb://localhost:27017/grocery_scraper
DB_NAME=grocery_scraper
JWT_SECRET_KEY=your-super-secret-jwt-key-change-in-production
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

### 4. Start Backend Server
```bash
# Using supervisor (recommended)
sudo supervisorctl restart backend

# Or directly with uvicorn (development)
uvicorn server:app --host 0.0.0.0 --port 8001 --reload
```

### 5. Verify Backend
```bash
curl http://localhost:8001/api/test
```

Expected response:
```json
{
  "status": "healthy",
  "message": "Product catalog API is operational"
}
```

## 🎨 Frontend Setup

### 1. Navigate to Frontend Directory
```bash
cd /app/frontend
```

### 2. Install Dependencies
```bash
yarn install
```

### 3. Environment Configuration
Create `.env` file in `/app/frontend/`:
```env
REACT_APP_BACKEND_URL=http://localhost:8001
```

### 4. Start Frontend
```bash
# Using supervisor (recommended)
sudo supervisorctl restart frontend

# Or directly with yarn (development)
yarn start
```

### 5. Verify Frontend
Open http://localhost:3000 in your browser.

## 🤖 Scraper Setup

### 1. Initialize Scraper Database
```bash
cd /app/grocery_price_scraper
python runner.py --init-db
```

### 2. Run Initial Scraping
```bash
python runner.py --categories vegetables,fruits --sites farm2bag --generate-report
```

### 3. Verify Scraper Data
```bash
python -c "
from db import Database
db = Database()
stats = db.get_statistics()
print(f'Total products: {stats[\"total_products\"]}')
"
```

## 🔑 Authentication Setup

### 1. Create API Key (For Product Access)
```bash
curl -X POST http://localhost:8001/api/scraper/auth/keys \
  -H "Content-Type: application/json" \
  -d '{"name": "Frontend App", "expires_days": 365}'
```

Save the returned `api_key` for frontend configuration.

### 2. Create User Account (For Dashboard Access)
```bash
curl -X POST http://localhost:8001/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin", 
    "email": "admin@example.com",
    "password": "secure_password",
    "full_name": "Admin User"
  }'
```

## 🗄️ Database Setup

### MongoDB Configuration

1. **Install MongoDB** (if not already installed)
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install mongodb

# macOS with Homebrew
brew install mongodb-community
```

2. **Start MongoDB Service**
```bash
# Linux
sudo systemctl start mongod
sudo systemctl enable mongod

# macOS
brew services start mongodb-community
```

3. **Verify MongoDB Connection**
```bash
mongo --eval 'db.runCommand({ connectionStatus: 1 })'
```

### SQLite (Scraper Database)

The scraper uses SQLite for historical data storage. Database is automatically created on first run:
```bash
ls -la /app/grocery_price_scraper/data/grocery_prices.db
```

## 🏃‍♂️ Quick Start (All Services)

### 1. Start All Services
```bash
cd /app
sudo supervisorctl restart all
```

### 2. Check Status
```bash
sudo supervisorctl status
```

Expected output:
```
backend                          RUNNING   pid 1234, uptime 0:00:30
frontend                         RUNNING   pid 1235, uptime 0:00:30
```

### 3. Initialize System
```bash
# Run initial scraping to populate database
cd /app/grocery_price_scraper
python runner.py --categories vegetables,fruits,dairy --generate-report

# Create API key for frontend
curl -X POST http://localhost:8001/api/scraper/auth/keys \
  -H "Content-Type: application/json" \
  -d '{"name": "Dashboard", "expires_days": 365}'
```

### 4. Access Applications

- **Frontend Dashboard**: http://localhost:3000
- **Backend API**: http://localhost:8001
- **API Documentation**: http://localhost:8001/docs (Swagger UI)

## 🔧 Development Setup

### Backend Development
```bash
cd /app/backend
pip install -e .
uvicorn server:app --reload --host 0.0.0.0 --port 8001
```

### Frontend Development
```bash
cd /app/frontend
yarn start
```

### Scraper Development
```bash
cd /app/grocery_price_scraper
pip install -e .
python runner.py --help
```

## 🧪 Testing

### Backend API Testing
```bash
cd /app/backend
python -m pytest tests/ -v
```

### Manual API Testing
```bash
# Test health endpoint
curl http://localhost:8001/api/test

# Test product catalog (requires API key)
curl -H "X-API-Key: your-api-key" http://localhost:8001/api/products

# Test authentication
curl -X POST http://localhost:8001/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "test", "email": "test@example.com", "password": "test123"}'
```

### Frontend Testing
```bash
cd /app/frontend
yarn test
```

## 📅 Scheduling Setup

### 1. Create Default Schedule
```bash
curl -X POST http://localhost:8001/api/scraper/schedules \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "name": "Daily Morning Scrape",
    "interval": "daily",
    "hour": 6,
    "minute": 0,
    "categories": ["vegetables", "fruits", "dairy"],
    "sites": ["farm2bag", "bigbasket", "jiomart"],
    "enabled": true
  }'
```

### 2. Verify Schedule
```bash
curl -H "X-API-Key: your-api-key" http://localhost:8001/api/scraper/schedules
```

## 🚨 Troubleshooting

### Common Issues

#### Backend Won't Start
```bash
# Check Python dependencies
pip check

# Check MongoDB connection
mongo --eval 'db.runCommand({ connectionStatus: 1 })'

# Check logs
sudo supervisorctl tail backend stderr
```

#### Frontend Won't Start
```bash
# Check Node.js version
node --version  # Should be 16+

# Clear cache and reinstall
rm -rf node_modules package-lock.json
yarn install

# Check environment variables
echo $REACT_APP_BACKEND_URL
```

#### Database Connection Issues
```bash
# Check MongoDB status
sudo systemctl status mongod

# Check connection string in .env
cat /app/backend/.env | grep MONGO_URL

# Test direct connection
python -c "from pymongo import MongoClient; print(MongoClient('mongodb://localhost:27017/').server_info())"
```

#### API Authentication Errors
```bash
# Verify API key creation
curl -X POST http://localhost:8001/api/scraper/auth/keys \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Key", "expires_days": 30}'

# Test API key usage
curl -H "X-API-Key: your-actual-api-key" http://localhost:8001/api/products
```

### Log Locations
- **Backend**: `/var/log/supervisor/backend.*.log`
- **Frontend**: `/var/log/supervisor/frontend.*.log`
- **Scraper**: `/app/grocery_price_scraper/logs/`

### Performance Optimization

#### Backend
```python
# Add to backend/.env for production
WORKERS=4
WORKER_CLASS=uvicorn.workers.UvicornWorker
```

#### Frontend
```bash
# Build for production
yarn build
serve -s build -l 3000
```

#### Database
```javascript
// MongoDB indexes for better performance
db.products.createIndex({ "normalized_name": 1, "site": 1 })
db.products.createIndex({ "scraped_at": -1 })
```

## 🔒 Security Considerations

### Production Deployment

1. **Change Default Secrets**
```env
JWT_SECRET_KEY=use-a-strong-random-secret-key
```

2. **Restrict CORS Origins**
```env
CORS_ORIGINS=https://yourdomain.com
```

3. **Use HTTPS**
```bash
# Add SSL certificate configuration
# Use reverse proxy (nginx/apache)
```

4. **Environment Variables**
```bash
# Never commit .env files to version control
echo "*.env" >> .gitignore
```

## 🚀 Deployment

### Docker Deployment (Recommended)
```dockerfile
# Dockerfile example included in repository
docker-compose up -d
```

### Manual Deployment
1. Set up production MongoDB
2. Configure environment variables
3. Use process manager (PM2, supervisor)
4. Set up reverse proxy (nginx)
5. Configure SSL certificates

---

## 📞 Support

For issues and questions:
1. Check logs first: `sudo supervisorctl tail backend stderr`
2. Verify services: `sudo supervisorctl status`
3. Test API endpoints manually with curl
4. Check database connectivity

## 🎯 Next Steps

After setup completion:
1. **Customize scraper sites** in `/app/grocery_price_scraper/config/sites.yml`
2. **Configure scraping categories** in `compare_rules.yml`
3. **Set up automated scheduling** via API
4. **Customize frontend theme** and branding
5. **Add real competitor scrapers** for production use