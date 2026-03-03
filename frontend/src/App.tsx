import React, { useState } from 'react';
import ImageUpload from './components/ImageUpload';
import ProductCard from './components/ProductCard';
import { searchProducts } from './services/api';
import { Product, SearchRequest, SearchResponse } from './types';
import { 
  MagnifyingGlassIcon, 
  SparklesIcon, 
  PhotoIcon,
  FunnelIcon,
  ChevronDownIcon,
  ChevronUpIcon
} from '@heroicons/react/24/outline';

const App: React.FC = () => {
  const [selectedImage, setSelectedImage] = useState<string>('');
  const [query, setQuery] = useState<string>('');
  const [preferences, setPreferences] = useState<string>('');
  const [maxPrice, setMaxPrice] = useState<string>('');
  const [minPrice, setMinPrice] = useState<string>('');
  const [color, setColor] = useState<string>('');
  const [category, setCategory] = useState<string>('');
  const [products, setProducts] = useState<Product[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [showAdvancedFilters, setShowAdvancedFilters] = useState<boolean>(false);
  const [searchResponse, setSearchResponse] = useState<SearchResponse | null>(null);

  const categories = ['tops', 'bottoms', 'dresses', 'shoes', 'accessories'];
  const colors = ['black', 'white', 'red', 'blue', 'green', 'yellow', 'pink', 'purple', 'orange', 'gray', 'brown', 'navy'];

  const handleImageSelect = (imageDataUrl: string) => {
    setSelectedImage(imageDataUrl);
    setProducts([]);
    setSearchResponse(null);
  };

  const handleClearImage = () => {
    setSelectedImage('');
    setProducts([]);
    setSearchResponse(null);
  };

  const handleSearch = async () => {
    if (!selectedImage) {
      alert('Please upload an image first');
      return;
    }

    setIsLoading(true);
    setProducts([]);
    setSearchResponse(null);

    try {
      const searchRequest: SearchRequest = {
        image: selectedImage,
        query: query,
        preferences: preferences,
        max_price: maxPrice ? parseFloat(maxPrice) : undefined,
        min_price: minPrice ? parseFloat(minPrice) : undefined,
        color: color || undefined,
        category: category || undefined,
        size: 5
      };

      const response = await searchProducts(searchRequest);
      setProducts(response.products);
      setSearchResponse(response);
    } catch (error) {
      console.error('Search failed:', error);
      alert('Search failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-white to-primary-50/30">
      {/* Header */}
      <header className="bg-white/80 backdrop-blur-md shadow-sm border-b sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <div className="w-10 h-10 bg-gradient-to-br from-primary-500 to-purple-600 rounded-xl flex items-center justify-center mr-3 shadow-lg shadow-primary-200">
                <SparklesIcon className="h-6 w-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold bg-gradient-to-r from-gray-900 to-gray-600 bg-clip-text text-transparent">AI Visual Shopping</h1>
                <p className="text-sm text-gray-500">Powered by Amazon Nova • Smart Recommendations</p>
              </div>
            </div>
            {products.length > 0 && (
              <div className="hidden sm:flex items-center gap-4">
                <span className="text-sm text-gray-600"><strong className="text-primary-600">{products.length}</strong> products found</span>
              </div>
            )}
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Upload (left) */}
          <div className="lg:col-span-5">
            <div className="bg-white rounded-2xl shadow-sm border border-gray-200 overflow-hidden">
              <div className="bg-gradient-to-r from-primary-50 to-purple-50 px-6 py-4 border-b border-primary-100">
                <div className="flex items-center">
                  <PhotoIcon className="h-5 w-5 text-primary-600 mr-2" />
                  <h2 className="text-lg font-bold text-gray-900">Upload Image</h2>
                </div>
              </div>
              <div className="p-6">
                <ImageUpload onImageSelect={handleImageSelect} selectedImage={selectedImage} onClearImage={handleClearImage} />
              </div>
            </div>
          </div>

          {/* Preferences (right) */}
          <div className="lg:col-span-7">
            <div className="bg-white rounded-2xl shadow-sm border border-gray-200 overflow-hidden">
              <div className="bg-gradient-to-r from-gray-50 to-gray-100 px-6 py-4 border-b border-gray-200">
                <div className="flex items-center">
                  <FunnelIcon className="h-5 w-5 text-gray-600 mr-2" />
                  <h2 className="text-lg font-bold text-gray-900">Search Preferences</h2>
                </div>
              </div>

              <div className="p-6 space-y-4">
                <div>
                  <label htmlFor="query" className="block text-sm font-semibold text-gray-700 mb-2">What are you looking for?</label>
                  <input type="text" id="query" value={query} onChange={(e) => setQuery(e.target.value)} placeholder="e.g., Summer dress for beach vacation" className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 focus:bg-white transition-all" />
                </div>

                <div>
                  <label htmlFor="preferences" className="block text-sm font-semibold text-gray-700 mb-2">Additional Preferences</label>
                  <textarea id="preferences" value={preferences} onChange={(e) => setPreferences(e.target.value)} placeholder="e.g., Prefer cotton material, casual style, under $100" rows={3} className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 focus:bg-white transition-all resize-none" />
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <button onClick={() => setShowAdvancedFilters(!showAdvancedFilters)} className="text-sm font-medium text-gray-600 hover:text-gray-900 transition-colors flex items-center gap-2">{showAdvancedFilters ? <ChevronUpIcon className="w-4 h-4" /> : <ChevronDownIcon className="w-4 h-4" />} Advanced Filters</button>
                  </div>
                  <div>
                    <button onClick={handleSearch} disabled={isLoading || !selectedImage} className="ml-2 inline-flex items-center gap-2 bg-gradient-to-r from-primary-600 to-primary-700 text-white py-2.5 px-4 rounded-xl font-semibold hover:from-primary-700 hover:to-primary-800 disabled:from-gray-400 disabled:to-gray-500 disabled:cursor-not-allowed transition-all">
                      {isLoading ? (<><div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" /><span className="text-sm">Analyzing...</span></>) : (<><MagnifyingGlassIcon className="h-4 w-4" /><span className="text-sm">Search</span></>)}
                    </button>
                  </div>
                </div>

                {showAdvancedFilters && (
                  <div className="space-y-4 pt-2 border-t border-gray-100">
                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <label className="block text-xs font-semibold text-gray-600 mb-1">Category</label>
                        <select value={category} onChange={(e) => setCategory(e.target.value)} className="w-full px-3 py-2 bg-gray-50 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500">
                          <option value="">All Categories</option>
                          {categories.map(cat => (<option key={cat} value={cat}>{cat.charAt(0).toUpperCase() + cat.slice(1)}</option>))}
                        </select>
                      </div>
                      <div>
                        <label className="block text-xs font-semibold text-gray-600 mb-1">Color</label>
                        <select value={color} onChange={(e) => setColor(e.target.value)} className="w-full px-3 py-2 bg-gray-50 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500">
                          <option value="">Any Color</option>
                          {colors.map(c => (<option key={c} value={c}>{c.charAt(0).toUpperCase() + c.slice(1)}</option>))}
                        </select>
                      </div>
                    </div>

                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <label className="block text-xs font-semibold text-gray-600 mb-1">Min Price ($)</label>
                        <input type="number" value={minPrice} onChange={(e) => setMinPrice(e.target.value)} placeholder="0" min="0" className="w-full px-3 py-2 bg-gray-50 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500" />
                      </div>
                      <div>
                        <label className="block text-xs font-semibold text-gray-600 mb-1">Max Price ($)</label>
                        <input type="number" value={maxPrice} onChange={(e) => setMaxPrice(e.target.value)} placeholder="1000" min="0" className="w-full px-3 py-2 bg-gray-50 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500" />
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Recommended (below both) */}
          <div className="lg:col-span-12">
            <div className="bg-white rounded-2xl shadow-sm border border-gray-200 min-h-[400px]">
              <div className="bg-gradient-to-r from-gray-50 to-gray-100 px-6 py-4 border-b border-gray-200 rounded-t-2xl">
                <div className="flex items-center justify-between">
                  <div className="flex items-center">
                    <SparklesIcon className="h-5 w-5 text-primary-600 mr-2" />
                    <h2 className="text-lg font-bold text-gray-900">Recommended Products</h2>
                    {products.length > 0 && (<span className="ml-3 px-3 py-1 bg-primary-100 text-primary-700 text-sm font-semibold rounded-full">{products.length} found</span>)}
                  </div>
                  {searchResponse?.total_results !== undefined && (<span className="text-sm text-gray-500">Showing top {products.length} of {searchResponse.total_results} matches</span>)}
                </div>
              </div>

              <div className="p-6">
                {products.length === 0 && !isLoading ? (
                  <div className="flex flex-col items-center justify-center py-12">
                    <div className="w-24 h-24 bg-gradient-to-br from-gray-100 to-gray-200 rounded-3xl flex items-center justify-center mb-6 shadow-inner">
                      <PhotoIcon className="w-12 h-12 text-gray-400" />
                    </div>
                    <h3 className="text-xl font-semibold text-gray-900 mb-2">Ready to Find Your Perfect Match</h3>
                    <p className="text-gray-500 text-center max-w-md mb-6">Upload an image of a product you like, describe what you're looking for, and let our AI find similar items for you.</p>
                  </div>
                ) : (
                  <div className="grid grid-cols-1 gap-6">
                    {products.map((product, index) => (<ProductCard key={product.product_id} product={product} index={index} />))}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};

export default App;

