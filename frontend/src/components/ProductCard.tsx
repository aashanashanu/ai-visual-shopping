import React from 'react';
import { Product } from '../types';
import { SparklesIcon, ShoppingBagIcon, TagIcon, CheckCircleIcon } from '@heroicons/react/24/outline';

interface ProductCardProps {
  product: Product;
  index: number;
  matchReason?: string;
}

const ProductCard: React.FC<ProductCardProps> = ({ product, index, matchReason }) => {
  const formatPrice = (price: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(price);
  };

  const getMatchBadge = () => {
    if (!product.score) return null;
    const score = Math.min(product.score * 20, 100);
    if (score >= 90) return { color: 'bg-green-100 text-green-800', label: 'Best Match' };
    if (score >= 70) return { color: 'bg-blue-100 text-blue-800', label: 'Great Match' };
    if (score >= 50) return { color: 'bg-yellow-100 text-yellow-800', label: 'Good Match' };
    return { color: 'bg-gray-100 text-gray-800', label: 'Similar' };
  };

  const matchBadge = getMatchBadge();

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden hover:shadow-xl hover:border-primary-300 transition-all duration-300 group">
      {/* Product Image */}
      <div className="relative aspect-square w-full bg-gray-100 overflow-hidden">
        <img
          src={product.image_url}
          alt={product.title}
          className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
          onError={(e) => {
            const target = e.target as HTMLImageElement;
            target.src = `https://via.placeholder.com/400x400?text=${encodeURIComponent(product.title)}`;
          }}
        />
        
        {/* Match Badge */}
        {matchBadge && (
          <div className="absolute top-3 left-3">
            <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold ${matchBadge.color}`}>
              <SparklesIcon className="w-3 h-3 mr-1" />
              {matchBadge.label}
            </span>
          </div>
        )}

        {/* Product Number */}
        <div className="absolute top-3 right-3">
          <span className="inline-flex items-center justify-center w-8 h-8 bg-white/90 backdrop-blur-sm rounded-full text-sm font-bold text-gray-700 shadow-sm">
            {index + 1}
          </span>
        </div>

        {/* Hover Overlay */}
        <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300">
          <div className="absolute bottom-4 left-4 right-4">
            <button className="w-full bg-white text-gray-900 py-2 px-4 rounded-lg font-medium hover:bg-gray-100 transition-colors flex items-center justify-center">
              <ShoppingBagIcon className="w-4 h-4 mr-2" />
              View Details
            </button>
          </div>
        </div>
      </div>

      {/* Product Details */}
      <div className="p-5">
        {/* Title & Price */}
        <div className="flex justify-between items-start gap-3 mb-2">
          <h3 className="text-lg font-bold text-gray-900 leading-tight line-clamp-2 flex-1">
            {product.title}
          </h3>
          <span className="text-xl font-bold text-primary-600 whitespace-nowrap">
            {formatPrice(product.price)}
          </span>
        </div>

        {/* Match Score Bar */}
        {product.score && (
          <div className="mb-3">
            <div className="flex items-center justify-between text-xs text-gray-500 mb-1">
              <span>Match Score</span>
              <span className="font-semibold text-primary-600">{Math.round(Math.min(product.score * 20, 100))}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-gradient-to-r from-primary-500 to-primary-600 h-2 rounded-full transition-all duration-500"
                style={{ width: `${Math.min(product.score * 20, 100)}%` }}
              />
            </div>
          </div>
        )}

        {/* Description */}
        <p className="text-sm text-gray-600 mb-4 line-clamp-2 leading-relaxed">
          {product.description}
        </p>

        {/* Match Reason */}
        {matchReason && (
          <div className="mb-4 p-3 bg-green-50 border border-green-100 rounded-lg">
            <div className="flex items-start gap-2">
              <CheckCircleIcon className="w-4 h-4 text-green-600 mt-0.5 flex-shrink-0" />
              <p className="text-sm text-green-800 leading-relaxed">{matchReason}</p>
            </div>
          </div>
        )}

        {/* Product Attributes */}
        <div className="flex flex-wrap gap-2">
          {product.category && (
            <span className="inline-flex items-center px-2.5 py-1 bg-primary-50 text-primary-700 text-xs font-medium rounded-md border border-primary-100">
              <TagIcon className="w-3 h-3 mr-1" />
              {product.category}
            </span>
          )}
          {product.color && (
            <span className="inline-flex items-center px-2.5 py-1 bg-gray-100 text-gray-700 text-xs font-medium rounded-md border border-gray-200">
              <span 
                className="w-2 h-2 rounded-full mr-1.5 border border-gray-300" 
                style={{ backgroundColor: product.color.toLowerCase() === 'white' ? '#f3f4f6' : product.color.toLowerCase() }}
              />
              {product.color}
            </span>
          )}
          {product.style && (
            <span className="inline-flex items-center px-2.5 py-1 bg-gray-100 text-gray-700 text-xs font-medium rounded-md border border-gray-200">
              {product.style}
            </span>
          )}
          {product.material && (
            <span className="inline-flex items-center px-2.5 py-1 bg-gray-100 text-gray-700 text-xs font-medium rounded-md border border-gray-200">
              {product.material}
            </span>
          )}
          {product.brand && (
            <span className="inline-flex items-center px-2.5 py-1 bg-purple-50 text-purple-700 text-xs font-medium rounded-md border border-purple-100">
              {product.brand}
            </span>
          )}
        </div>
      </div>
    </div>
  );
};

export default ProductCard;
