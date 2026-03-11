// Production-ready API service for Farm2bag Product Scanner
// Connects to the FastAPI backend at http://localhost:8001/api

import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
const API_BASE = `${BACKEND_URL}/api`;

const apiClient = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 180000, // 3 minute timeout for long-running scrape tasks
});

export const apiService = {
  /**
   * Scrape a single product across multiple stores.
   * Calls POST /api/scrape-product with product_query.
   * This endpoint polls the task until completion on the backend and returns the results.
   */
  scrapeProduct: async (query, sites = null) => {
    console.log(`[API] Scraping product: ${query}`, sites ? `on sites: ${sites.join(', ')}` : '');
    try {
      const response = await apiClient.post('/scrape-product', {
        product_query: query,
        sites: sites
      });
      
      return response.data;
    } catch (error) {
      console.error('[API] Scrape failed:', error.response?.data || error.message);
      throw error;
    }
  },

  /**
   * Health check / Hello world
   */
  checkHealth: async () => {
    try {
      const response = await apiClient.get('/');
      return response.data;
    } catch (error) {
      console.error('[API] Health check failed:', error.message);
      throw error;
    }
  }
};
