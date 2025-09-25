# Grocery Price Scraper

A Python project that scrapes grocery product prices from competitor websites, normalizes them, compares them with Farm2bag's prices, and generates Excel reports.

## Features

- **Multi-site Scraping**: Supports BigBasket, JioMart, Amazon Fresh, Flipkart Grocery
- **Data Normalization**: Normalizes product names, units, and sizes
- **Fuzzy Matching**: Compares products across different sites using fuzzy matching
- **Excel Reports**: Generates detailed and summary Excel reports
- **SQLite Storage**: Stores daily snapshots for historical analysis
- **Modular Design**: Easy to add new scrapers and extend functionality

## Project Structure

```
grocery_price_scraper/
├── scrapers/           # Site-specific scrapers
├── fetchers/          # HTTP and Playwright fetchers  
├── normalizer/        # Product normalization logic
├── comparator/        # Price comparison and matching
├── reporter/          # Excel report generation
├── config/            # Configuration files
├── data/              # Data storage and reports
├── tests/             # Unit tests
├── tooling/           # Setup and utility scripts
├── db.py              # SQLite database wrapper
├── runner.py          # Main orchestrator
└── requirements.txt   # Python dependencies
```

## Quick Start

1. **Setup Environment**:
   ```bash
   cd /app/grocery_price_scraper
   bash tooling/local_setup.sh
   ```

2. **Run Price Comparison**:
   ```bash
   python runner.py
   ```

3. **View Reports**:
   Reports are generated in `data/reports/YYYY-MM-DD_report.xlsx`

## Dependencies

- Python 3.11+
- Only free libraries: requests, playwright, beautifulsoup4, pandas, openpyxl, sqlite3, pyyaml, rapidfuzz, pytest

## Configuration

- `config/sites.yml`: Competitor site selectors and settings
- `config/compare_rules.yml`: Normalization and matching rules

## Testing

```bash
pytest tests/
```