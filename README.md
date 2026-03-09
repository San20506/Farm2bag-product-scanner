# 🛒 Farm2Bag Product Scanner Platform

A high-performance, full-stack grocery price comparison and market analysis engine. This platform automates price discovery across multiple e-commerce sites, matching products with fuzzy logic and providing real-time competitive analytics.

[![Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen)](#)
[![Stack](https://img.shields.io/badge/Stack-FastAPI%20%7C%20React%20%7C%20Playwright-blue)](#)
[![Internal](https://img.shields.io/badge/Internal-Farm2Bag%20Analytics-orange)](#)

---

## ⚡ Core Capabilities

- **Multi-Site Scraping engine**: Parallelized discovery across Farm2Bag, BigBasket, JioMart, and others.
- **Intelligent Product Matching**: Normalizes units and names using fuzzy matching to compare "Apples to Apples".
- **Real-time Analytics**: Live price difference calculations and "Cheaper than" indicators.
- **Historical Tracking**: Time-series analysis of price fluctuations for market trend forecasting.
- **Dual Auth Security**: JWT for users and Scoped API Keys for programmatic integration.

## 🏗️ Technical Architecture

The system is built as a distributed modular architecture for scalability:

- **Scraper Engine (`/grocery_price_scraper`)**: Python-based scrapers using Playwright and BeautifulSoup4 for robust extraction.
- **Backend API (`/backend`)**: High-concurrency FastAPI server handling data persistence and analytics.
- **Frontend Dashboard (`/website`)**: Responsive React application for visualizing competitive data.
- **Databases**: 
  - **MongoDB**: Primary store for product metadata and system logs.
  - **SQLite**: Dedicated store for high-volume price history snapshots.

## 🚀 Quick Start

### 1. Prerequisites
- Python 3.10+
- Node.js 18+
- MongoDB instance

### 2. Installation

```bash
# Clone the repository
git clone https://github.com/San20506/Farm2bag-product-scanner.git
cd Farm2bag-product-scanner

# Setup Backend
cd backend
pip install -r requirements.txt
cp .env.example .env # Configure your MONGO_URL

# Setup Frontend
cd ../website
npm install
npm start
```

### 3. Running Scrapers

```bash
python run.py --categories vegetables --sites farm2bag,bigbasket
```

## 🛠️ Configuration

Configuration is managed via YAML files in `grocery_price_scraper/config/`:
- `sites.yml`: Target selectors and base URLs.
- `compare_rules.yml`: Fuzzy matching thresholds and unit normalization.

## 🔒 Security
The platform implements multiple layers of security:
- **JWT Authentication** for the management dashboard.
- **API Keys** with specific expiration for external integrations.
- **Rate Limiting** on all scraper-triggering endpoints.

---

Built for **Farm2Bag** | *Market Monitoring Division*
