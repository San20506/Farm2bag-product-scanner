import React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from './ui/card';
import { Badge } from './ui/badge';
import { ExternalLink, ShoppingCart, Tag, Store, Clock } from 'lucide-react';
import { Button } from './ui/button';

const ScrapeResult = ({ result, isScraping }) => {
  if (isScraping) {
    return (
      <div className="space-y-4 animate-pulse" aria-live="polite" aria-busy="true">
        <div className="h-6 w-1/3 bg-stone-200 rounded"></div>
        <div className="h-24 bg-stone-100 rounded"></div>
        <div className="grid grid-cols-2 gap-4">
          <div className="h-10 bg-stone-200 rounded"></div>
          <div className="h-10 bg-stone-200 rounded"></div>
        </div>
      </div>
    );
  }

  if (!result) return null;

  return (
    <Card className="border-2 border-amber-100 bg-white shadow-xl hover:shadow-2xl transition-shadow duration-300">
      <CardHeader className="bg-amber-50/50 border-b border-amber-100 p-5">
        <div className="flex justify-between items-start gap-4">
          <div className="space-y-1">
            <CardTitle className="text-2xl font-bold font-rubik text-stone-900 leading-tight">
              {result.name}
            </CardTitle>
            <div className="flex items-center gap-2 text-stone-500 font-nunito text-sm">
              <Store className="w-4 h-4 text-amber-600" aria-hidden="true" />
              <span>{result.store}</span>
            </div>
          </div>
          <Badge className="bg-amber-600 hover:bg-amber-700 text-white font-rubik py-1 px-3">
            Scraped
          </Badge>
        </div>
      </CardHeader>
      
      <CardContent className="p-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-6">
          <div className="space-y-6">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-stone-100 rounded-xl">
                <Tag className="w-6 h-6 text-amber-600" aria-hidden="true" />
              </div>
              <div>
                <p className="text-xs uppercase tracking-wider font-rubik font-bold text-stone-400">Current Price</p>
                <p className="text-4xl font-bold font-rubik text-stone-900 mt-1 font-variant-numeric-tabular-nums">
                  ₹{result.price}
                </p>
              </div>
            </div>
            
            <div className="flex items-center gap-4">
              <div className="p-3 bg-stone-100 rounded-xl">
                <Clock className="w-6 h-6 text-stone-400" aria-hidden="true" />
              </div>
              <div>
                <p className="text-xs uppercase tracking-wider font-rubik font-bold text-stone-400">Last Updated</p>
                <p className="text-stone-700 font-nunito mt-1">
                  {new Date(result.timestamp).toLocaleString()}
                </p>
              </div>
            </div>
          </div>

          <div className="bg-stone-50 p-5 rounded-2xl border border-stone-100">
            <div className="flex items-center gap-2 mb-3">
              <ShoppingCart className="w-5 h-5 text-amber-600" aria-hidden="true" />
              <h4 className="font-rubik font-bold text-stone-900">Product Details</h4>
            </div>
            <p className="text-stone-600 font-nunito leading-relaxed italic">
              “{result.details || 'No detailed description available.'}”
            </p>
          </div>
        </div>

        <div className="pt-6 border-t border-stone-100 flex gap-4">
          <Button 
            variant="outline"
            className="flex-1 h-12 border-stone-200 hover:bg-stone-50 text-stone-700 font-rubik transition-colors"
            onClick={() => window.open(result.url, '_blank')}
          >
            <ExternalLink className="w-4 h-4 mr-2" aria-hidden="true" />
            View on Store
          </Button>
          <Button className="flex-1 h-12 bg-amber-600 hover:bg-amber-700 text-white font-extra-bold font-rubik transition-colors">
            Track Price
          </Button>
        </div>
      </CardContent>
    </Card>
  );
};

export default ScrapeResult;
