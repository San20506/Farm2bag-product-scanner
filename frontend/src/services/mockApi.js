// Mock API service for Farm2bag Product Scanner
// Used while the backend is disconnected

const delay = (ms) => new Promise(resolve => setTimeout(resolve, ms));

const mockProducts = [
  {
    id: 1,
    name: "Organic Basmati Rice",
    price: 450,
    store: "Store A",
    category: "Grains",
    url: "https://example.com/p1",
    timestamp: new Date().toISOString()
  },
  {
    id: 2,
    name: "Sunflower Oil 1L",
    price: 180,
    store: "Store B",
    category: "Oils",
    url: "https://example.com/p2",
    timestamp: new Date().toISOString()
  },
  {
    id: 3,
    name: "Toor Dal 1kg",
    price: 160,
    store: "Store A",
    category: "Pulses",
    url: "https://example.com/p3",
    timestamp: new Date().toISOString()
  }
];

export const mockApiService = {
  searchProducts: async (query) => {
    console.log(`[Mock API] Searching for: ${query}`);
    await delay(800);
    if (!query) return [];
    return mockProducts.filter(p => 
      p.name.toLowerCase().includes(query.toLowerCase()) ||
      p.store.toLowerCase().includes(query.toLowerCase())
    );
  },

  scrapeProduct: async (url) => {
    console.log(`[Mock API] Scraping URL: ${url}`);
    await delay(2000); // Simulate network latency
    
    // Simulate a successful scrape
    return {
      success: true,
      data: {
        id: Math.floor(Math.random() * 1000),
        name: "Scraped Product Name",
        price: (Math.random() * 200 + 50).toFixed(2),
        store: "Scraped Store",
        url: url,
        timestamp: new Date().toISOString(),
        details: "Detailed product description found on the page."
      }
    };
  }
};
