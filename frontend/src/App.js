import React, { useState } from 'react';
import ProductSearch from './components/ProductSearch';
import ScrapeResult from './components/ScrapeResult';
import { apiService } from './services/api';
import { ShoppingBag, ChevronRight, LayoutGrid, Info, ArrowUpRight, TrendingDown } from 'lucide-react';
import { Button } from './components/ui/button';
import "./App.css";

const App = () => {
  const [searchResults, setSearchResults] = useState([]);
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [isSearching, setIsSearching] = useState(false);
  const [isScraping, setIsScraping] = useState(false);
  const [scrapedResults, setScrapedResults] = useState([]);
  const [comparison, setComparison] = useState(null);
  const [error, setError] = useState(null);

  const handleSearch = async (query) => {
    setIsSearching(true);
    setError(null);
    setSearchResults([]);
    setScrapedResults([]);
    setComparison(null);
    setSelectedProduct(null);
    
    try {
      // For Single Product Scraper flow, 'search' IS the scrape action
      const response = await apiService.scrapeProduct(query);
      
      if (response && response.products) {
        setSearchResults(response.products);
        setScrapedResults(response.products);
        setComparison(response.comparison);
      } else if (response.error) {
        setError(response.error);
      }
    } catch (err) {
      console.error("Scrape failed", err);
      setError("Failed to fetch product data. Ensure the backend is running at http://localhost:8001.");
    } finally {
      setIsSearching(false);
    }
  };

  const selectProduct = (product) => {
    setSelectedProduct(product);
  };

  return (
    <div className="min-h-screen bg-stone-50 text-stone-900 font-nunito">
      {/* Navbar */}
      <nav className="fixed top-0 left-0 right-0 h-20 bg-white border-b border-stone-100 z-50 px-6 backdrop-blur-md bg-white/80">
        <div className="max-w-7xl mx-auto h-full flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="bg-amber-600 p-2 rounded-xl">
              <ShoppingBag className="w-8 h-8 text-white" />
            </div>
            <span className="text-2xl font-black font-rubik tracking-tight text-stone-900">
              Farm2bag <span className="text-amber-600">Scanner</span>
            </span>
          </div>
          <div className="hidden md:flex items-center gap-8">
            <a href="#" className="font-rubik font-bold text-stone-600 hover:text-amber-600 transition-colors">Dashboard</a>
            <a href="#" className="font-rubik font-bold text-stone-600 hover:text-amber-600 transition-colors">Analytics</a>
            <Button className="bg-stone-900 hover:bg-stone-800 text-white font-bold font-rubik px-6 rounded-xl">
              Live Feed
            </Button>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="pt-32 pb-20 px-6 max-w-7xl mx-auto">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12">
          
          {/* Left Column: Search & Selection */}
          <div className="lg:col-span-5 space-y-8">
            <div className="space-y-4">
              <h1 className="text-5xl font-black font-rubik leading-[1.1] text-stone-900">
                Track Prices <br />
                <span className="text-amber-600 underline underline-offset-8 decoration-stone-200">Across Stores</span>
              </h1>
              <p className="text-lg text-stone-500 font-medium max-w-md">
                Enter a product name to trigger a live multi-store scan for real-time pricing and availability.
              </p>
            </div>

            <ProductSearch onSearch={handleSearch} isLoading={isSearching} />

            {error && (
              <div className="bg-red-50 border border-red-100 text-red-700 p-4 rounded-2xl flex items-center gap-3 animate-in fade-in">
                <Info className="w-5 h-5" />
                <p className="font-medium text-sm">{error}</p>
              </div>
            )}

            {/* Results List */}
            {searchResults.length > 0 && (
              <div className="space-y-4 mt-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
                <div className="flex items-center justify-between px-2">
                  <h3 className="font-rubik font-bold text-stone-900 uppercase tracking-wider text-sm">Matching Products</h3>
                  <span className="text-xs font-bold text-stone-400">{searchResults.length} Found</span>
                </div>
                {searchResults.map((product, idx) => (
                  <button
                    key={`${product.site}-${idx}`}
                    onClick={() => selectProduct(product)}
                    className={`w-full group text-left p-5 rounded-2xl border-2 transition-all duration-300 flex items-center justify-between ${
                      selectedProduct?.url === product.url 
                        ? 'border-amber-600 bg-amber-50 shadow-md' 
                        : 'border-white bg-white hover:border-stone-100 hover:shadow-lg'
                    }`}
                  >
                    <div className="space-y-1">
                      <h4 className="font-rubik font-bold text-stone-900 leading-tight">
                        {product.name}
                      </h4>
                      <p className="text-stone-500 text-sm flex items-center gap-1.5 capitalize">
                        {product.site} • ₹{product.price}
                      </p>
                    </div>
                    <div className={`p-2 rounded-lg transition-all duration-300 ${
                      selectedProduct?.url === product.url ? 'bg-amber-600 text-white' : 'bg-stone-100 text-stone-400 group-hover:bg-stone-900 group-hover:text-white'
                    }`}>
                      <ChevronRight className="w-5 h-5" />
                    </div>
                  </button>
                ))}
              </div>
            )}

            {/* Empty State */}
            {!isSearching && searchResults.length === 0 && !error && (
              <div className="bg-white border-2 border-dashed border-stone-200 rounded-3xl p-12 text-center space-y-4 shadow-sm">
                <div className="w-16 h-16 bg-stone-50 rounded-2xl flex items-center justify-center mx-auto">
                  <LayoutGrid className="w-8 h-8 text-stone-300" />
                </div>
                <div className="space-y-1">
                  <p className="font-rubik font-bold text-stone-900">Enter a query to start</p>
                  <p className="text-stone-400 text-sm">Compare prices across Amazon Fresh, Flipkart Grocery, and BigBasket</p>
                </div>
              </div>
            )}
          </div>

          {/* Right Column: Details & Comparison Output */}
          <div className="lg:col-span-7">
            <div className="sticky top-32 space-y-6">
              {isSearching ? (
                <div className="animate-in fade-in zoom-in-95 duration-500">
                  <ScrapeResult isScraping={true} />
                </div>
              ) : selectedProduct ? (
                <div className="animate-in fade-in zoom-in-95 duration-500">
                  <ScrapeResult result={{
                    ...selectedProduct,
                    timestamp: new Date().toISOString(),
                    details: selectedProduct.description || "Live product data from current store shelf."
                  }} isScraping={false} />
                  
                  {comparison && (
                    <div className="mt-8 bg-white border border-stone-100 rounded-3xl p-8 shadow-sm">
                      <div className="flex items-center gap-3 mb-6">
                        <TrendingDown className="w-6 h-6 text-green-600" />
                        <h3 className="text-xl font-black font-rubik text-stone-900 uppercase tracking-tight">Market Analysis</h3>
                      </div>
                      
                      <div className="grid grid-cols-2 md:grid-cols-3 gap-6">
                        <div>
                          <p className="text-xs font-bold text-stone-400 uppercase tracking-widest font-rubik">Best Price Found</p>
                          <p className="text-3xl font-black text-green-600 font-rubik mt-1">₹{comparison.best_price.price}</p>
                          <p className="text-sm font-bold text-stone-500 mt-1 capitalize">{comparison.best_price.site}</p>
                        </div>
                        <div>
                          <p className="text-xs font-bold text-stone-400 uppercase tracking-widest font-rubik">Price Variation</p>
                          <p className="text-3xl font-black text-amber-600 font-rubik mt-1">₹{comparison.price_spread.absolute}</p>
                          <p className="text-sm font-bold text-stone-500 mt-1">{comparison.price_spread.percent_vs_best}% Diff</p>
                        </div>
                        <div className="col-span-2 md:col-span-1 border-t md:border-t-0 md:border-l border-stone-100 pt-6 md:pt-0 md:pl-6">
                          <p className="text-xs font-bold text-stone-400 uppercase tracking-widest font-rubik">Scanned Sources</p>
                          <p className="text-3xl font-black text-stone-900 font-rubik mt-1">{comparison.sites_with_prices}</p>
                          <p className="text-sm font-bold text-stone-500 mt-1">Active Site Indexes</p>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <div className="bg-stone-900 rounded-3xl p-12 text-white relative overflow-hidden shadow-2xl min-h-[400px] flex items-center justify-center">
                  <div className="absolute top-0 right-0 p-8 opacity-20">
                    <ShoppingBag className="w-64 h-64 -mr-20 -mt-20" />
                  </div>
                  <div className="relative z-10 max-w-sm text-center">
                    <div className="p-4 bg-white/10 rounded-2xl inline-block mb-6">
                      <ArrowUpRight className="w-10 h-10 text-amber-500" />
                    </div>
                    <h2 className="text-3xl font-black font-rubik leading-tight mb-4 tracking-tighter">Live Scraper Connected</h2>
                    <p className="text-stone-400 font-medium">
                      The analyzer engine is ready. Enter a product query to start checking prices across the local retail market.
                    </p>
                    <div className="mt-8 flex items-center gap-4 justify-center">
                      <div className="flex -space-x-3">
                        {[1,2,3].map(i => (
                          <div key={i} className="w-10 h-10 rounded-full border-4 border-stone-900 bg-stone-700"></div>
                        ))}
                      </div>
                      <p className="text-xs font-bold font-rubik uppercase tracking-widest text-amber-500">Backend Online</p>
                    </div>
                  </div>
                </div>
              )}

              {/* Security/Trust Banner */}
              <div className="bg-stone-100 rounded-2xl p-6 border border-stone-200 flex items-start gap-4">
                <div className="p-2 bg-stone-900 rounded-lg shrink-0 mt-1">
                  <Info className="w-5 h-5 text-white" />
                </div>
                <div>
                  <h4 className="font-rubik font-bold text-stone-900">Direct Comparison</h4>
                  <p className="text-stone-600 text-sm mt-1 leading-relaxed font-medium">
                    Prices are fetched directly from store catalogs. No cached data. Verification engine matches product metadata to ensure accuracy across multiple vendor SKUs.
                  </p>
                </div>
              </div>
            </div>
          </div>

        </div>
      </main>
    </div>
  );
};

export default App;

export default App;
