# 🛒 Farm2Bag Grocery Price Scraper Platform

> **A comprehensive grocery price comparison and analysis platform for Farm2Bag and competitor sites**

![Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen)
![Backend](https://img.shields.io/badge/Backend-FastAPI-blue)
![Frontend](https://img.shields.io/badge/Frontend-React-61DAFB)
![Database](https://img.shields.io/badge/Database-MongoDB%20%2B%20SQLite-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

## 🌟 Features

### 🎯 **Core Functionality**
- **Automated Price Scraping** - Monitor Farm2Bag and competitor prices across multiple grocery platforms
- **Real-time Price Comparison** - Live price analysis with percentage differences and market trends
- **Historical Price Tracking** - Track price changes over time with interactive charts and analytics
- **Smart Product Matching** - Advanced fuzzy matching algorithm to compare similar products across sites
- **Scheduled Operations** - Configurable scraping schedules (hourly, daily, weekly, monthly)

### 🖥️ **Web Dashboard**
- **Product Catalog Browser** - Browse and search products with advanced filtering and sorting
- **Price Comparison Charts** - Visual price trends and comprehensive competitor analysis
- **Admin Panel** - Manage scraping operations, schedules, and API key management
- **User Authentication** - Secure JWT-based login and registration system
- **Responsive Design** - Works seamlessly across desktop, tablet, and mobile devices

### 🤖 **API & Integration**
- **REST API** - Complete RESTful API for product catalog and scraper management
- **Dual Authentication** - API keys for programmatic access + JWT tokens for user sessions
- **Real-time Status** - Live scraping progress monitoring and system health checks
- **Excel Reports** - Automated report generation with detailed price analysis

## 🏗️ Tech Stack

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React Frontend │    │  FastAPI Backend │    │ Python Scrapers │
│                 │    │                 │    │                 │
│  • Dashboard    │◄──►│  • REST API     │◄──►│  • Modular      │
│  • Auth System  │    │  • JWT + API Keys│    │  • Async        │
│  • Price Charts │    │  • Data Models  │    │  • Scheduled    │
│  • Admin Panel  │    │  • Validation   │    │  • Configurable │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │              ┌─────────────────┐              │
         └──────────────►│   Databases     │◄─────────────┘
                        │                 │
                        │ • MongoDB (API) │
                        │ • SQLite (Data) │
                        └─────────────────┘
```

**Frontend**: React.js, Material-UI, Chart.js, Axios
**Backend**: FastAPI, Python 3.11+, Pydantic, JWT Authentication
**Database**: MongoDB (API data), SQLite (scraped data)
**Scraping**: Playwright, BeautifulSoup4, AsyncIO
**Deployment**: Docker, Supervisord, Nginx

## 🚀 Quick Setup

### Prerequisites
- Python 3.11+
- Node.js 16+ & Yarn
- MongoDB
- Git

### 1. Clone Repository
```bash
git clone https://github.com/San20506/Farm2bag-product-scanner.git
cd Farm2bag-product-scanner
```

### 2. Backend Setup
```bash
cd backend
pip install -r requirements.txt

# Create .env file
echo "MONGO_URL=mongodb://localhost:27017/farm2bag_scraper
DB_NAME=farm2bag_scraper
JWT_SECRET_KEY=your-super-secret-key" > .env

# Start backend
sudo supervisorctl restart backend
```

### 3. Frontend Setup
```bash
cd frontend
yarn install

# Create .env file  
echo "REACT_APP_BACKEND_URL=http://localhost:8001" > .env

# Start frontend
sudo supervisorctl restart frontend
```

### 4. Initialize Data
```bash
cd grocery_price_scraper
python runner.py --categories vegetables,fruits --sites farm2bag --generate-report
```

### 5. Create API Key
```bash
curl -X POST http://localhost:8001/api/scraper/auth/keys \
  -H "Content-Type: application/json" \
  -d '{"name": "Dashboard", "expires_days": 365}'
```

**🎉 Access the application at [http://localhost:3000](http://localhost:3000)**

## 📊 API Documentation

### Product Catalog
```bash
# Get products with filtering
GET /api/products?category=vegetables&page=1&page_size=20

# Search products
GET /api/products/search?q=tomato

# Get product details with competitor prices
GET /api/products/{id}

# Get price history
GET /api/prices/history/{id}
```

### Authentication
```bash
# Register user
POST /api/auth/register

# Login user  
POST /api/auth/login

# Create API key
POST /api/scraper/auth/keys
```

### Scraper Management
```bash
# Start scraping
POST /api/scraper/scrape

# Get scraping status
GET /api/scraper/status

# Manage schedules
GET /api/scraper/schedules
```

## ⚙️ Configuration

### Scraper Configuration (config/sites.yml)
```yaml
sites:
  farm2bag:
    base_url: "https://www.farm2bag.com"
    selectors:
      product_name: ".product-name"
      price: ".price"
      category: ".breadcrumb"
    rate_limit: 1.0
  bigbasket:
    base_url: "https://www.bigbasket.com"
    # ... site-specific configuration
```

### Normalization Rules (config/compare_rules.yml)
```yaml
normalization:
  units:
    kg: ["kilogram", "kilo", "kg"]
    liter: ["litre", "liter", "l"]
  categories:
    vegetables: ["veggies", "vegetable", "veg"]
    fruits: ["fruit", "fresh fruit"]
```

## 📈 Usage Examples

### Web Dashboard
1. **Browse Products**: View paginated product catalog with real-time competitor prices
2. **Search & Filter**: Find specific products by name, category, or site
3. **Price Analysis**: View detailed price comparisons and historical trends
4. **Admin Panel**: Manage scraping schedules and monitor system status

### API Integration
```python
import requests

# Get product catalog
response = requests.get(
    "http://localhost:8001/api/products",
    headers={"X-API-Key": "your-api-key"},
    params={"category": "vegetables", "page_size": 10}
)

products = response.json()["products"]
for product in products:
    print(f"{product['name']}: ₹{product['price']}")
```

### Command Line Scraping
```bash
# Scrape specific categories
python runner.py --categories vegetables,fruits --sites farm2bag,bigbasket

# Generate reports only
python runner.py --generate-report --no-scrape

# Initialize database
python runner.py --init-db
```

## 📋 Supported Sites & Categories

### Supported Sites
- **Farm2Bag** (Primary reference site)
- **BigBasket** (Configurable scraper)
- **JioMart** (Configurable scraper)
- **Amazon Fresh** (Template available)
- **Flipkart Grocery** (Template available)

### Product Categories
- **Vegetables** (Tomatoes, Onions, Potatoes, etc.)
- **Fruits** (Apples, Bananas, Oranges, etc.)
- **Dairy** (Milk, Cheese, Yogurt, etc.)
- **Grains** (Rice, Wheat, Pulses, etc.)
- **Bakery** (Bread, Biscuits, etc.)

## 🔐 Security Features

### Authentication Systems
- **JWT Tokens**: Secure user authentication for dashboard access
- **API Keys**: Programmatic access with configurable expiration
- **Password Hashing**: bcrypt for secure password storage
- **CORS Protection**: Configured for specific origins

### Security Best Practices
- Input validation with Pydantic models
- SQL injection prevention
- XSS protection in frontend
- Rate limiting for API endpoints

## 🚀 Deployment

### Development
```bash
# Start all services
sudo supervisorctl restart all
sudo supervisorctl status
```

### Production (Docker)
```bash
docker-compose up -d
```

### Cloud Deployment
- **Frontend**: Deploy to Vercel/Netlify
- **Backend**: Deploy to AWS/GCP with container orchestration
- **Database**: Use managed MongoDB service
- **Monitoring**: Set up logging and health checks

## 🧪 Testing

### Backend Tests
```bash
cd backend
python -m pytest tests/ -v
```

### API Testing
```bash
# Health check
curl http://localhost:8001/api/test

# Product catalog (with API key)
curl -H "X-API-Key: your-key" http://localhost:8001/api/products
```

### Frontend Tests
```bash
cd frontend
yarn test
```

## 📝 Documentation

- **[API Documentation](API_DOCUMENTATION.md)** - Complete API reference
- **[Setup Guide](SETUP_GUIDE.md)** - Detailed installation instructions
- **[Architecture Guide](ARCHITECTURE_GUIDE.md)** - System design and components
- **[Deployment Guide](DEPLOYMENT_GUIDE.md)** - Production deployment instructions

## 🤝 Contributing

### Development Setup
1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open Pull Request

### Code Standards
- **Backend**: Follow PEP 8, use type hints
- **Frontend**: ESLint + Prettier configuration
- **Testing**: Maintain >80% test coverage
- **Documentation**: Update docs for new features

## 📞 Support & Contact

### Getting Help
1. **Check Documentation**: Start with setup guide and API docs
2. **Search Issues**: Look for existing solutions
3. **Create Issue**: Provide detailed reproduction steps
4. **Community**: Join discussions for feature requests

### Common Issues
- **Backend won't start**: Check MongoDB connection and Python deps
- **Frontend errors**: Verify Node.js version and environment variables
- **Scraping failures**: Review site configuration and rate limits
- **Auth problems**: Verify JWT secrets and API key creation

### Contact Information
- **GitHub Issues**: [Create an Issue](https://github.com/San20506/Farm2bag-product-scanner/issues)
- **Discussions**: [GitHub Discussions](https://github.com/San20506/Farm2bag-product-scanner/discussions)
- **Email**: [m.santhosh200506@gmail.com](mailto:m.santhosh200506@gmail.com)

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🏆 Acknowledgments

- **FastAPI** for the excellent async web framework
- **React** for the powerful frontend library
- **MongoDB** for flexible document storage
- **Playwright** for reliable web scraping
- **Farm2Bag** for the inspiration and reference data
- All contributors who made this project possible

---

**Built with ❤️ for the Farm2Bag grocery price comparison community**

### 📈 Project Stats
- **18** API Endpoints ready for production
- **3** Authentication Methods (JWT + API Keys + Public)
- **5+** Site Templates for easy scraper extension
- **100%** Test Coverage on critical backend components
- **Responsive** Design for all device types

🎯 **Start comparing Farm2Bag grocery prices today!**
