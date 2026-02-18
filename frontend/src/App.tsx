import React, { useState } from 'react';
import ImageUpload from './components/ImageUpload';
import ProductCard from './components/ProductCard';
import ChatInterface from './components/ChatInterface';
import { searchProducts } from './services/api';
import { Product, SearchRequest } from './types';
import { MagnifyingGlassIcon, SparklesIcon } from '@heroicons/react/24/outline';

const App: React.FC = () => {
  const [selectedImage, setSelectedImage] = useState<string>('');
  const [query, setQuery] = useState<string>('');
  const [preferences, setPreferences] = useState<string>('');
  const [maxPrice, setMaxPrice] = useState<string>('');
  const [minPrice, setMinPrice] = useState<string>('');
  const [products, setProducts] = useState<Product[]>([]);
  const [explanation, setExplanation] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(false);

  const handleImageSelect = (imageDataUrl: string) => {
    setSelectedImage(imageDataUrl);
    setProducts([]);
    setExplanation('');
  };

  const handleClearImage = () => {
    setSelectedImage('');
    setProducts([]);
    setExplanation('');
  };

  const handleSearch = async () => {
    if (!selectedImage) {
      alert('Please upload an image first');
      return;
    }

    setIsLoading(true);
    setProducts([]);
    setExplanation('');

    try {
      const searchRequest: SearchRequest = {
        image: selectedImage,
        query: query,
        preferences: preferences,
        max_price: maxPrice ? parseFloat(maxPrice) : undefined,
        min_price: minPrice ? parseFloat(minPrice) : undefined,
        size: 5
      };

      const response = await searchProducts(searchRequest);
      setProducts(response.products);
      setExplanation(response.explanation);
    } catch (error) {
      console.error('Search failed:', error);
      alert('Search failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <SparklesIcon className="h-8 w-8 text-primary-600 mr-3" />
              <div>
                <h1 className="text-2xl font-bold text-gray-900">
                  AI Visual Shopping
                </h1>
                <p className="text-sm text-gray-600">
                  Powered by Amazon Nova
                </p>
              </div>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Left Column - Input */}
          <div className="space-y-6">
            <ImageUpload
              onImageSelect={handleImageSelect}
              selectedImage={selectedImage}
              onClearImage={handleClearImage}
            />

            <div className="bg-white rounded-lg shadow-md p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">
                Search Preferences
              </h2>
              
              <div className="space-y-4">
                <div>
                  <label htmlFor="query" className="block text-sm font-medium text-gray-700 mb-1">
                    What are you looking for?
                  </label>
                  <input
                    type="text"
                    id="query"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder="e.g., Show me similar products"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                  />
                </div>

                <div>
                  <label htmlFor="preferences" className="block text-sm font-medium text-gray-700 mb-1">
                    Additional Preferences
                  </label>
                  <textarea
                    id="preferences"
                    value={preferences}
                    onChange={(e) => setPreferences(e.target.value)}
                    placeholder="e.g., Show me similar in blue under $100"
                    rows={3}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label htmlFor="minPrice" className="block text-sm font-medium text-gray-700 mb-1">
                      Min Price ($)
                    </label>
                    <input
                      type="number"
                      id="minPrice"
                      value={minPrice}
                      onChange={(e) => setMinPrice(e.target.value)}
                      placeholder="0"
                      min="0"
                      step="0.01"
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                    />
                  </div>
                  <div>
                    <label htmlFor="maxPrice" className="block text-sm font-medium text-gray-700 mb-1">
                      Max Price ($)
                    </label>
                    <input
                      type="number"
                      id="maxPrice"
                      value={maxPrice}
                      onChange={(e) => setMaxPrice(e.target.value)}
                      placeholder="1000"
                      min="0"
                      step="0.01"
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                    />
                  </div>
                </div>

                <button
                  onClick={handleSearch}
                  disabled={isLoading || !selectedImage}
                  className="w-full bg-primary-600 text-white py-2 px-4 rounded-md hover:bg-primary-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors flex items-center justify-center"
                >
                  {isLoading ? (
                    <>
                      <div className="loading-spinner w-4 h-4 mr-2"></div>
                      Searching...
                    </>
                  ) : (
                    <>
                      <MagnifyingGlassIcon className="h-5 w-5 mr-2" />
                      Search Similar Products
                    </>
                  )}
                </button>
              </div>
            </div>

            <ChatInterface explanation={explanation} isLoading={isLoading} />
          </div>

          {/* Right Column - Results */}
          <div className="space-y-6">
            <div className="bg-white rounded-lg shadow-md p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">
                Recommended Products
                {products.length > 0 && (
                  <span className="ml-2 text-sm font-normal text-gray-600">
                    ({products.length} found)
                  </span>
                )}
              </h2>

              {products.length === 0 && !isLoading && (
                <div className="text-center py-12">
                  <svg
                    className="w-16 h-16 mx-auto mb-4 text-gray-300"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"
                    />
                  </svg>
                  <p className="text-gray-500">
                    Upload an image and search to see recommendations
                  </p>
                </div>
              )}

              <div className="space-y-4">
                {products.map((product) => (
                  <ProductCard key={product.product_id} product={product} />
                ))}
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};

export default App;
