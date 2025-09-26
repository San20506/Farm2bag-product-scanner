import React, { createContext, useContext, useState, useEffect } from 'react';
import axios from 'axios';

const ApiContext = createContext();

export const useApi = () => {
  const context = useContext(ApiContext);
  if (!context) {
    throw new Error('useApi must be used within an ApiProvider');
  }
  return context;
};

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

export const ApiProvider = ({ children }) => {
  const [apiKey, setApiKey] = useState(localStorage.getItem('apiKey'));
  const [apiKeyName, setApiKeyName] = useState(localStorage.getItem('apiKeyName'));

  // Create API instance with interceptors
  const apiClient = axios.create({
    baseURL: BACKEND_URL
  });

  // Request interceptor to add API key
  apiClient.interceptors.request.use((config) => {
    if (apiKey) {
      config.headers['X-API-Key'] = apiKey;
    }
    return config;
  });

  // Response interceptor for error handling
  apiClient.interceptors.response.use(
    (response) => response,
    (error) => {
      if (error.response?.status === 403 || error.response?.status === 401) {
        console.error('API authentication failed:', error.response?.data);
      }
      return Promise.reject(error);
    }
  );

  const createApiKey = async (name) => {
    try {
      const response = await axios.post(`${BACKEND_URL}/api/scraper/auth/keys`, {
        name,
        expires_days: 365
      });

      const { api_key, name: keyName } = response.data;
      
      setApiKey(api_key);
      setApiKeyName(keyName);
      localStorage.setItem('apiKey', api_key);
      localStorage.setItem('apiKeyName', keyName);
      
      return { success: true, apiKey: api_key };
    } catch (error) {
      console.error('API key creation failed:', error);
      return { 
        success: false, 
        error: error.response?.data?.detail || 'API key creation failed' 
      };
    }
  };

  const clearApiKey = () => {
    setApiKey(null);
    setApiKeyName(null);
    localStorage.removeItem('apiKey');
    localStorage.removeItem('apiKeyName');
  };

  // Product API methods
  const getProducts = async (params = {}) => {
    try {
      const response = await apiClient.get('/api/products', { params });
      return { success: true, data: response.data };
    } catch (error) {
      return { success: false, error: error.response?.data?.detail || 'Failed to fetch products' };
    }
  };

  const getProductDetails = async (productId) => {
    try {
      const response = await apiClient.get(`/api/products/${productId}`);
      return { success: true, data: response.data };
    } catch (error) {
      return { success: false, error: error.response?.data?.detail || 'Failed to fetch product details' };
    }
  };

  const searchProducts = async (query) => {
    try {
      const response = await apiClient.get('/api/products/search', { 
        params: { q: query } 
      });
      return { success: true, data: response.data };
    } catch (error) {
      return { success: false, error: error.response?.data?.detail || 'Search failed' };
    }
  };

  const getCategories = async () => {
    try {
      const response = await apiClient.get('/api/categories');
      return { success: true, data: response.data };
    } catch (error) {
      return { success: false, error: error.response?.data?.detail || 'Failed to fetch categories' };
    }
  };

  const getCurrentPrices = async (productId) => {
    try {
      const response = await apiClient.get(`/api/prices/${productId}`);
      return { success: true, data: response.data };
    } catch (error) {
      return { success: false, error: error.response?.data?.detail || 'Failed to fetch prices' };
    }
  };

  const getPriceHistory = async (productId) => {
    try {
      const response = await apiClient.get(`/api/prices/history/${productId}`);
      return { success: true, data: response.data };
    } catch (error) {
      return { success: false, error: error.response?.data?.detail || 'Failed to fetch price history' };
    }
  };

  // Scraper API methods
  const startScraping = async (params) => {
    try {
      const response = await apiClient.post('/api/scraper/scrape', params);
      return { success: true, data: response.data };
    } catch (error) {
      return { success: false, error: error.response?.data?.detail || 'Failed to start scraping' };
    }
  };

  const getScrapingTasks = async () => {
    try {
      const response = await apiClient.get('/api/scraper/tasks');
      return { success: true, data: response.data };
    } catch (error) {
      return { success: false, error: error.response?.data?.detail || 'Failed to fetch tasks' };
    }
  };

  const getScrapingStatus = async () => {
    try {
      const response = await apiClient.get('/api/scraper/status');
      return { success: true, data: response.data };
    } catch (error) {
      return { success: false, error: error.response?.data?.detail || 'Failed to fetch status' };
    }
  };

  const getSchedules = async () => {
    try {
      const response = await apiClient.get('/api/scraper/schedules');
      return { success: true, data: response.data };
    } catch (error) {
      return { success: false, error: error.response?.data?.detail || 'Failed to fetch schedules' };
    }
  };

  const createSchedule = async (scheduleData) => {
    try {
      const response = await apiClient.post('/api/scraper/schedules', scheduleData);
      return { success: true, data: response.data };
    } catch (error) {
      return { success: false, error: error.response?.data?.detail || 'Failed to create schedule' };
    }
  };

  const value = {
    apiKey,
    apiKeyName,
    createApiKey,
    clearApiKey,
    // Product methods
    getProducts,
    getProductDetails,
    searchProducts,
    getCategories,
    getCurrentPrices,
    getPriceHistory,
    // Scraper methods
    startScraping,
    getScrapingTasks,
    getScrapingStatus,
    getSchedules,
    createSchedule,
    hasApiKey: !!apiKey
  };

  return (
    <ApiContext.Provider value={value}>
      {children}
    </ApiContext.Provider>
  );
};