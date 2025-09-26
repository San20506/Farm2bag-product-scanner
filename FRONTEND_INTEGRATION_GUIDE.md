# 🎨 Frontend Integration Guide - React Dashboard

## Overview

Complete guide for integrating the React frontend with the grocery price scraper backend API.

## 🏗️ Frontend Architecture

### Component Structure
```
src/
├── components/
│   ├── layout/
│   │   ├── Navbar.js           # Main navigation with user menu
│   │   ├── Sidebar.js          # Admin panel sidebar
│   │   └── Layout.js           # Main layout wrapper
│   ├── auth/
│   │   ├── LoginForm.js        # JWT authentication form
│   │   ├── RegisterForm.js     # User registration form
│   │   └── ProtectedRoute.js   # Route protection component
│   ├── products/
│   │   ├── ProductCatalog.js   # Main product listing with filters
│   │   ├── ProductCard.js      # Individual product display card
│   │   ├── ProductDetails.js   # Detailed product view modal
│   │   ├── SearchBar.js        # Product search component
│   │   └── CategoryFilter.js   # Category filtering component
│   ├── charts/
│   │   ├── PriceChart.js       # Price history line chart
│   │   ├── ComparisonChart.js  # Competitor price comparison
│   │   └── TrendChart.js       # Price trend analysis
│   ├── admin/
│   │   ├── ScrapingPanel.js    # Start/monitor scraping operations
│   │   ├── ScheduleManager.js  # Manage scraping schedules
│   │   ├── ApiKeyManager.js    # API key management
│   │   └── StatusDashboard.js  # System status overview
│   └── ui/
│       ├── Button.js           # Reusable button component
│       ├── Modal.js            # Modal dialog component
│       ├── Table.js            # Data table component
│       └── Spinner.js          # Loading spinner
├── contexts/
│   ├── AuthContext.js          # JWT authentication state
│   └── ApiContext.js           # API integration and calls
├── hooks/
│   ├── useApi.js               # Custom hook for API calls
│   ├── useAuth.js              # Authentication utilities
│   └── useProducts.js          # Product data management
├── lib/
│   ├── api.js                  # API client configuration
│   ├── utils.js                # Utility functions
│   └── constants.js            # Application constants
└── pages/
    ├── Dashboard.js            # Main dashboard page
    ├── Products.js             # Product catalog page
    ├── Analytics.js            # Price analytics page
    ├── Admin.js                # Admin panel page
    └── Profile.js              # User profile page
```

## 🔌 API Integration

### Context Providers Setup

#### AuthContext Implementation
```javascript
// src/contexts/AuthContext.js
import React, { createContext, useContext, useState, useEffect } from 'react';
import axios from 'axios';

const AuthContext = createContext();

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [loading, setLoading] = useState(true);

  // JWT token management and user authentication
  const login = async (username, password) => {
    // Implementation provided in contexts/AuthContext.js
  };

  const logout = () => {
    // Clear token and user state
  };

  return (
    <AuthContext.Provider value={{ user, token, login, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
};
```

#### ApiContext Implementation
```javascript
// src/contexts/ApiContext.js
import React, { createContext, useContext } from 'react';
import axios from 'axios';

const ApiContext = createContext();

export const useApi = () => useContext(ApiContext);

export const ApiProvider = ({ children }) => {
  const [apiKey, setApiKey] = useState(localStorage.getItem('apiKey'));

  // Product API methods
  const getProducts = async (params = {}) => {
    // GET /api/products with filtering/pagination
  };

  const searchProducts = async (query) => {
    // GET /api/products/search
  };

  const getProductDetails = async (productId) => {
    // GET /api/products/{id}
  };

  return (
    <ApiContext.Provider value={{ 
      getProducts, 
      searchProducts, 
      getProductDetails,
      // ... other API methods
    }}>
      {children}
    </ApiContext.Provider>
  );
};
```

### App.js Integration
```javascript
// src/App.js
import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import { ApiProvider } from './contexts/ApiContext';
import Layout from './components/layout/Layout';
import Dashboard from './pages/Dashboard';
import Products from './pages/Products';
import Admin from './pages/Admin';
import LoginForm from './components/auth/LoginForm';

function App() {
  return (
    <AuthProvider>
      <ApiProvider>
        <Router>
          <Layout>
            <Routes>
              <Route path="/login" element={<LoginForm />} />
              <Route path="/" element={<Dashboard />} />
              <Route path="/products" element={<Products />} />
              <Route path="/admin" element={<Admin />} />
            </Routes>
          </Layout>
        </Router>
      </ApiProvider>
    </AuthProvider>
  );
}

export default App;
```

## 🛠️ Component Implementation Examples

### Product Catalog Component
```javascript
// src/components/products/ProductCatalog.js
import React, { useState, useEffect } from 'react';
import { useApi } from '../../contexts/ApiContext';
import ProductCard from './ProductCard';
import SearchBar from './SearchBar';
import CategoryFilter from './CategoryFilter';

const ProductCatalog = () => {
  const { getProducts, getCategories } = useApi();
  const [products, setProducts] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({
    category: '',
    search: '',
    page: 1,
    page_size: 20
  });

  useEffect(() => {
    loadProducts();
    loadCategories();
  }, [filters]);

  const loadProducts = async () => {
    setLoading(true);
    const result = await getProducts(filters);
    if (result.success) {
      setProducts(result.data.products);
    }
    setLoading(false);
  };

  const loadCategories = async () => {
    const result = await getCategories();
    if (result.success) {
      setCategories(result.data);
    }
  };

  const handleSearch = (searchTerm) => {
    setFilters({ ...filters, search: searchTerm, page: 1 });
  };

  const handleCategoryFilter = (category) => {
    setFilters({ ...filters, category, page: 1 });
  };

  return (
    <div className="product-catalog">
      <div className="filters">
        <SearchBar onSearch={handleSearch} />
        <CategoryFilter 
          categories={categories} 
          onFilter={handleCategoryFilter}
          selectedCategory={filters.category}
        />
      </div>

      {loading ? (
        <div className="loading">Loading products...</div>
      ) : (
        <div className="products-grid">
          {products.map(product => (
            <ProductCard key={product.id} product={product} />
          ))}
        </div>
      )}
    </div>
  );
};

export default ProductCatalog;
```

### Product Card Component
```javascript
// src/components/products/ProductCard.js
import React, { useState } from 'react';
import { useApi } from '../../contexts/ApiContext';
import ProductDetails from './ProductDetails';

const ProductCard = ({ product }) => {
  const { getCurrentPrices } = useApi();
  const [showDetails, setShowDetails] = useState(false);
  const [competitorPrices, setCompetitorPrices] = useState([]);

  const handleViewDetails = async () => {
    const result = await getCurrentPrices(product.id);
    if (result.success) {
      setCompetitorPrices(result.data);
    }
    setShowDetails(true);
  };

  return (
    <>
      <div className="product-card">
        <img 
          src={product.image_url || '/placeholder-product.jpg'} 
          alt={product.name}
          className="product-image"
        />
        <div className="product-info">
          <h3 className="product-name">{product.name}</h3>
          <p className="product-brand">{product.brand}</p>
          <div className="price-info">
            <span className="price">₹{product.price}</span>
            <span className="unit">per {product.unit}</span>
          </div>
          <div className="product-meta">
            <span className="category">{product.category}</span>
            <span className="site">{product.site}</span>
          </div>
          <button 
            onClick={handleViewDetails}
            className="view-details-btn"
          >
            Compare Prices
          </button>
        </div>
      </div>

      {showDetails && (
        <ProductDetails
          product={product}
          competitorPrices={competitorPrices}
          onClose={() => setShowDetails(false)}
        />
      )}
    </>
  );
};

export default ProductCard;
```

### Price Chart Component
```javascript
// src/components/charts/PriceChart.js
import React, { useEffect, useState } from 'react';
import { Line } from 'react-chartjs-2';
import { useApi } from '../../contexts/ApiContext';

const PriceChart = ({ productId }) => {
  const { getPriceHistory } = useApi();
  const [chartData, setChartData] = useState(null);

  useEffect(() => {
    loadPriceHistory();
  }, [productId]);

  const loadPriceHistory = async () => {
    const result = await getPriceHistory(productId);
    if (result.success) {
      const history = result.data;
      
      const chartData = {
        labels: history.map(item => item.date),
        datasets: [
          {
            label: 'Price History',
            data: history.map(item => item.price),
            borderColor: 'rgb(75, 192, 192)',
            backgroundColor: 'rgba(75, 192, 192, 0.2)',
            tension: 0.1
          }
        ]
      };
      
      setChartData(chartData);
    }
  };

  const options = {
    responsive: true,
    plugins: {
      legend: {
        position: 'top',
      },
      title: {
        display: true,
        text: 'Price History (30 days)'
      }
    },
    scales: {
      y: {
        beginAtZero: false,
        title: {
          display: true,
          text: 'Price (₹)'
        }
      }
    }
  };

  return (
    <div className="price-chart">
      {chartData ? (
        <Line data={chartData} options={options} />
      ) : (
        <div>Loading chart...</div>
      )}
    </div>
  );
};

export default PriceChart;
```

### Admin Panel Component
```javascript
// src/components/admin/ScrapingPanel.js
import React, { useState, useEffect } from 'react';
import { useApi } from '../../contexts/ApiContext';

const ScrapingPanel = () => {
  const { 
    startScraping, 
    getScrapingStatus, 
    getScrapingTasks 
  } = useApi();
  
  const [status, setStatus] = useState(null);
  const [tasks, setTasks] = useState([]);
  const [isStarting, setIsStarting] = useState(false);

  useEffect(() => {
    loadStatus();
    loadTasks();
    
    // Poll for updates every 5 seconds
    const interval = setInterval(() => {
      loadStatus();
      loadTasks();
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  const loadStatus = async () => {
    const result = await getScrapingStatus();
    if (result.success) {
      setStatus(result.data);
    }
  };

  const loadTasks = async () => {
    const result = await getScrapingTasks();
    if (result.success) {
      setTasks(result.data);
    }
  };

  const handleStartScraping = async () => {
    setIsStarting(true);
    const result = await startScraping({
      categories: ['vegetables', 'fruits'],
      sites: ['bigbasket', 'jiomart'],
      generate_report: true,
      store_data: true
    });
    
    if (result.success) {
      alert('Scraping started successfully!');
      loadTasks();
    } else {
      alert(`Failed to start scraping: ${result.error}`);
    }
    setIsStarting(false);
  };

  return (
    <div className="scraping-panel">
      <h2>Scraper Control Panel</h2>
      
      <div className="status-section">
        <h3>System Status</h3>
        {status && (
          <div className="status-info">
            <p>Service Available: {status.service_available ? '✅' : '❌'}</p>
            <p>Active Tasks: {status.active_tasks}</p>
            <p>Database Products: {status.database_stats?.total_products || 0}</p>
          </div>
        )}
      </div>

      <div className="controls-section">
        <h3>Start Scraping</h3>
        <button 
          onClick={handleStartScraping}
          disabled={isStarting}
          className="start-scraping-btn"
        >
          {isStarting ? 'Starting...' : 'Start Scraping'}
        </button>
      </div>

      <div className="tasks-section">
        <h3>Recent Tasks</h3>
        <div className="tasks-list">
          {tasks.map(task => (
            <div key={task.task_id} className="task-item">
              <span className="task-status">{task.status}</span>
              <span className="task-time">
                {new Date(task.started_at).toLocaleString()}
              </span>
              <span className="task-products">
                {task.farm2bag_products + task.competitor_products} products
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default ScrapingPanel;
```

## 🎨 Styling with Tailwind CSS

### Product Card Styling
```css
/* Tailwind classes for ProductCard */
.product-card {
  @apply bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow p-4;
}

.product-image {
  @apply w-full h-48 object-cover rounded-md mb-4;
}

.product-name {
  @apply text-lg font-semibold text-gray-900 mb-1;
}

.product-brand {
  @apply text-sm text-gray-600 mb-2;
}

.price-info {
  @apply flex items-center justify-between mb-3;
}

.price {
  @apply text-xl font-bold text-green-600;
}

.unit {
  @apply text-sm text-gray-500;
}

.view-details-btn {
  @apply w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 transition-colors;
}
```

### Dashboard Layout
```css
.dashboard-layout {
  @apply flex h-screen bg-gray-100;
}

.sidebar {
  @apply w-64 bg-white shadow-lg;
}

.main-content {
  @apply flex-1 overflow-auto p-6;
}

.navbar {
  @apply bg-white shadow-sm border-b px-6 py-4 flex items-center justify-between;
}
```

## 🔐 Authentication Integration

### Protected Route Component
```javascript
// src/components/auth/ProtectedRoute.js
import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';

const ProtectedRoute = ({ children }) => {
  const { user, loading } = useAuth();

  if (loading) {
    return <div>Loading...</div>;
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  return children;
};

export default ProtectedRoute;
```

### Login Form
```javascript
// src/components/auth/LoginForm.js
import React, { useState } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { Navigate } from 'react-router-dom';

const LoginForm = () => {
  const { login, user } = useAuth();
  const [credentials, setCredentials] = useState({
    username: '',
    password: ''
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  if (user) {
    return <Navigate to="/" replace />;
  }

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    const result = await login(credentials.username, credentials.password);
    
    if (!result.success) {
      setError(result.error);
    }
    
    setLoading(false);
  };

  return (
    <div className="login-form">
      <h2>Login to Dashboard</h2>
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label>Username or Email</label>
          <input
            type="text"
            value={credentials.username}
            onChange={(e) => setCredentials({
              ...credentials,
              username: e.target.value
            })}
            required
          />
        </div>
        
        <div className="form-group">
          <label>Password</label>
          <input
            type="password"
            value={credentials.password}
            onChange={(e) => setCredentials({
              ...credentials,
              password: e.target.value
            })}
            required
          />
        </div>

        {error && <div className="error-message">{error}</div>}
        
        <button type="submit" disabled={loading}>
          {loading ? 'Logging in...' : 'Login'}
        </button>
      </form>
    </div>
  );
};

export default LoginForm;
```

## 📱 Responsive Design

### Mobile-First Approach
```css
/* Mobile-first responsive design */
.products-grid {
  @apply grid gap-4;
  @apply grid-cols-1;           /* Mobile: 1 column */
  @apply md:grid-cols-2;        /* Tablet: 2 columns */
  @apply lg:grid-cols-3;        /* Desktop: 3 columns */
  @apply xl:grid-cols-4;        /* Large: 4 columns */
}

.dashboard-layout {
  @apply flex flex-col md:flex-row;  /* Stack on mobile, side-by-side on tablet+ */
}

.sidebar {
  @apply w-full md:w-64;        /* Full width on mobile, fixed on desktop */
  @apply h-auto md:h-screen;    /* Auto height on mobile, full height on desktop */
}
```

## 🔄 State Management

### Custom Hooks for Data
```javascript
// src/hooks/useProducts.js
import { useState, useEffect } from 'react';
import { useApi } from '../contexts/ApiContext';

export const useProducts = (initialFilters = {}) => {
  const { getProducts } = useApi();
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [filters, setFilters] = useState(initialFilters);
  const [pagination, setPagination] = useState({});

  useEffect(() => {
    loadProducts();
  }, [filters]);

  const loadProducts = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const result = await getProducts(filters);
      if (result.success) {
        setProducts(result.data.products);
        setPagination({
          page: result.data.page,
          total: result.data.total,
          total_pages: result.data.total_pages
        });
      } else {
        setError(result.error);
      }
    } catch (err) {
      setError('Failed to load products');
    } finally {
      setLoading(false);
    }
  };

  const updateFilters = (newFilters) => {
    setFilters({ ...filters, ...newFilters });
  };

  return {
    products,
    loading,
    error,
    filters,
    pagination,
    updateFilters,
    reload: loadProducts
  };
};
```

## 🚀 Performance Optimization

### Code Splitting
```javascript
// src/App.js with lazy loading
import React, { Suspense } from 'react';
const Dashboard = React.lazy(() => import('./pages/Dashboard'));
const Products = React.lazy(() => import('./pages/Products'));
const Admin = React.lazy(() => import('./pages/Admin'));

function App() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/products" element={<Products />} />
        <Route path="/admin" element={<Admin />} />
      </Routes>
    </Suspense>
  );
}
```

### Memoization
```javascript
// Optimize re-renders with React.memo
const ProductCard = React.memo(({ product }) => {
  // Component implementation
});

// Memoize expensive calculations
const ExpensiveChart = ({ data }) => {
  const chartData = useMemo(() => {
    return processChartData(data);
  }, [data]);

  return <Chart data={chartData} />;
};
```

## 🧪 Testing Integration

### Component Testing
```javascript
// src/components/products/__tests__/ProductCard.test.js
import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { ApiProvider } from '../../../contexts/ApiContext';
import ProductCard from '../ProductCard';

const mockProduct = {
  id: 1,
  name: 'Test Product',
  price: 100,
  unit: 'kg',
  brand: 'Test Brand',
  category: 'vegetables',
  site: 'farm2bag'
};

const MockApiProvider = ({ children }) => (
  <ApiProvider value={{ getCurrentPrices: jest.fn() }}>
    {children}
  </ApiProvider>
);

test('renders product card with correct information', () => {
  render(
    <MockApiProvider>
      <ProductCard product={mockProduct} />
    </MockApiProvider>
  );

  expect(screen.getByText('Test Product')).toBeInTheDocument();
  expect(screen.getByText('₹100')).toBeInTheDocument();
  expect(screen.getByText('Test Brand')).toBeInTheDocument();
});
```

## 🔧 Environment Setup

### Package.json Dependencies
```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.8.0",
    "axios": "^1.3.0",
    "chart.js": "^4.2.0",
    "react-chartjs-2": "^5.2.0",
    "@headlessui/react": "^1.7.0",
    "@heroicons/react": "^2.0.0"
  },
  "devDependencies": {
    "@testing-library/react": "^14.0.0",
    "@testing-library/jest-dom": "^5.16.0",
    "@testing-library/user-event": "^14.4.0",
    "tailwindcss": "^3.2.0",
    "autoprefixer": "^10.4.0",
    "postcss": "^8.4.0"
  }
}
```

### Tailwind Configuration
```javascript
// tailwind.config.js
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#eff6ff',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
        }
      }
    },
  },
  plugins: [],
}
```

This integration guide provides everything needed to build a complete React frontend that seamlessly integrates with the grocery price scraper backend API.