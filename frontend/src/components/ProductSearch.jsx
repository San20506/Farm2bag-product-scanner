import React, { useState } from 'react';
import { Search, Loader2 } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent } from './ui/card';
import { Input } from './ui/input';
import { Button } from './ui/button';

const ProductSearch = ({ onSearch, isLoading }) => {
  const [query, setQuery] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (query.trim()) {
      onSearch(query);
    }
  };

  return (
    <Card className="shadow-lg border-2 border-stone-100 mb-8 overflow-hidden">
      <CardHeader className="bg-stone-50 border-b border-stone-100">
        <CardTitle className="text-xl font-bold font-rubik text-stone-900 flex items-center gap-2">
          <Search className="w-5 h-5 text-amber-600" aria-hidden="true" />
          Product Discovery
        </CardTitle>
      </CardHeader>
      <CardContent className="pt-6">
        <form onSubmit={handleSubmit} className="flex gap-3">
          <div className="relative flex-1">
            <label htmlFor="product-search" className="sr-only">Search products</label>
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-stone-400 pointer-events-none" aria-hidden="true" />
            <Input
              id="product-search"
              type="text"
              name="query"
              placeholder="Search by product name or store…"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className="pl-10 h-12 border-stone-200 focus-visible:ring-2 focus-visible:ring-amber-500 font-nunito"
            />
          </div>
          <Button 
            type="submit" 
            disabled={isLoading || !query.trim()}
            className="h-12 px-8 bg-amber-600 hover:bg-amber-700 text-white font-rubik font-medium transition-colors duration-200"
          >
            {isLoading ? (
              <Loader2 className="w-4 h-4 animate-spin mr-2" aria-hidden="true" />
            ) : null}
            Search
          </Button>
        </form>
      </CardContent>
    </Card>
  );
};

export default ProductSearch;
