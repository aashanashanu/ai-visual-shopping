import React, { useState } from 'react';
import { Product } from '../types';
import { SparklesIcon, TagIcon, ChevronDownIcon, ChevronUpIcon } from '@heroicons/react/24/outline';

interface ProductCardProps {
  product: Product;
  index: number;
}

const ProductCard: React.FC<ProductCardProps> = ({ product, index }) => {
  const [showExplanation, setShowExplanation] = useState(true);

  const formatPrice = (price: number) =>
    new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(price);

  const getMatchBadge = () => {
    if (!product.score) return null;
    const score = Math.min(product.score * 20, 100);
    if (score >= 90) return { cls: 'bg-emerald-100 text-emerald-700 border-emerald-200', label: 'Best Match', icon: '🏆' };
    if (score >= 70) return { cls: 'bg-blue-100 text-blue-700 border-blue-200', label: 'Great Match', icon: '⭐' };
    if (score >= 50) return { cls: 'bg-amber-100 text-amber-700 border-amber-200', label: 'Good Match', icon: '👍' };
    return { cls: 'bg-gray-100 text-gray-600 border-gray-200', label: 'Similar', icon: '🔗' };
  };

  /** Lightweight markdown → styled HTML */
  const parseMarkdown = (text: string): string => {
    if (!text) return '';
    return text
      .replace(/### (.*$)/gim, '<h4 class="text-sm font-bold text-gray-800 mt-3 mb-1">$1</h4>')
      .replace(/## (.*$)/gim, '<h3 class="text-sm font-bold text-gray-900 mt-3 mb-1.5">$1</h3>')
      .replace(/# (.*$)/gim, '<h2 class="text-base font-bold text-gray-900 mt-4 mb-2">$1</h2>')
      .replace(/\*\*(.*?)\*\*/g, '<strong class="font-semibold text-gray-800">$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/^[-•] (.*$)/gim, '<li class="flex items-start gap-1.5 mb-0.5"><span class="mt-1.5 w-1 h-1 bg-primary-500 rounded-full flex-shrink-0"></span><span>$1</span></li>')
      .replace(/^\d+\. (.*$)/gim, '<li class="flex items-start gap-1.5 mb-0.5"><span class="mt-0.5 text-primary-600 font-semibold text-xs flex-shrink-0">●</span><span>$1</span></li>')
      .replace(/\n/g, '<br/>');
  };

  const matchBadge = getMatchBadge();
  const matchScore = product.score ? Math.round(Math.min(product.score * 20, 100)) : null;

  return (
    <div className="bg-white rounded-2xl border border-gray-100 shadow-sm hover:shadow-lg hover:border-primary-200 transition-all duration-300 overflow-hidden group">
      {/* ── Horizontal layout: image | details ── */}
      <div className="flex flex-col sm:flex-row">
        {/* Image */}
        <div className="relative sm:w-52 md:w-60 flex-shrink-0 bg-gray-50">
          <div className="aspect-square sm:h-full overflow-hidden">
            <img
              src={product.image_url}
              alt={product.title}
              className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
              onError={(e) => {
                (e.target as HTMLImageElement).src =
                  `https://via.placeholder.com/400x400?text=${encodeURIComponent(product.title)}`;
              }}
            />
          </div>

          {/* Rank */}
          <span className="absolute top-3 left-3 inline-flex items-center justify-center w-8 h-8 bg-white/95 backdrop-blur rounded-full text-sm font-bold text-gray-800 shadow border border-white/60">
            {index + 1}
          </span>

          {/* Badge */}
          {matchBadge && (
            <span className={`absolute top-3 right-3 sm:bottom-3 sm:top-auto sm:left-3 sm:right-auto inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[11px] font-semibold border backdrop-blur-sm ${matchBadge.cls}`}>
              {matchBadge.icon} {matchBadge.label}
            </span>
          )}
        </div>

        {/* Details */}
        <div className="flex-1 p-5 flex flex-col">
          {/* Title + Price */}
          <div className="flex items-start justify-between gap-3 mb-1.5">
            <h3 className="text-lg font-bold text-gray-900 leading-snug line-clamp-2">{product.title}</h3>
            <span className="text-xl font-extrabold text-primary-600 whitespace-nowrap">{formatPrice(product.price)}</span>
          </div>

          {/* Score bar */}
          {matchScore !== null && (
            <div className="flex items-center gap-3 mb-3">
              <div className="flex-1 h-1.5 bg-gray-100 rounded-full overflow-hidden">
                <div
                  className="h-full rounded-full bg-gradient-to-r from-primary-400 to-primary-600 transition-all duration-700"
                  style={{ width: `${matchScore}%` }}
                />
              </div>
              <span className="text-xs font-bold text-primary-600 tabular-nums w-8 text-right">{matchScore}%</span>
            </div>
          )}

          {/* Description */}
          <p className="text-sm text-gray-500 leading-relaxed mb-3 line-clamp-2">{product.description}</p>

          {/* Tags */}
          <div className="flex flex-wrap gap-1.5 mt-auto">
            {product.category && (
              <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-primary-50 text-primary-700 text-xs font-medium rounded-md">
                <TagIcon className="w-3 h-3" />
                {product.category}
              </span>
            )}
            {product.color && (
              <span className="inline-flex items-center gap-1.5 px-2 py-0.5 bg-gray-50 text-gray-600 text-xs font-medium rounded-md border border-gray-100">
                <span
                  className="w-2.5 h-2.5 rounded-full border border-gray-200"
                  style={{ backgroundColor: product.color.toLowerCase() === 'white' ? '#f3f4f6' : product.color.toLowerCase() }}
                />
                {product.color}
              </span>
            )}
            {product.style && (
              <span className="px-2 py-0.5 bg-gray-50 text-gray-600 text-xs font-medium rounded-md border border-gray-100">{product.style}</span>
            )}
            {product.material && (
              <span className="px-2 py-0.5 bg-gray-50 text-gray-600 text-xs font-medium rounded-md border border-gray-100">{product.material}</span>
            )}
            {product.brand && (
              <span className="px-2 py-0.5 bg-violet-50 text-violet-700 text-xs font-medium rounded-md border border-violet-100">{product.brand}</span>
            )}
          </div>
        </div>
      </div>

      {/* ── AI Explanation (collapsible, rendered as HTML) ── */}
      {product.explanation && (
        <div className="border-t border-gray-100">
          <button
            onClick={() => setShowExplanation(!showExplanation)}
            className="w-full flex items-center justify-between px-5 py-2.5 bg-gradient-to-r from-primary-50/60 to-purple-50/60 hover:from-primary-50 hover:to-purple-50 transition-colors"
          >
            <span className="flex items-center gap-2">
              <SparklesIcon className="w-4 h-4 text-primary-600" />
              <span className="text-xs font-semibold text-gray-700 uppercase tracking-wide">Why this product?</span>
            </span>
            {showExplanation ? <ChevronUpIcon className="w-4 h-4 text-gray-400" /> : <ChevronDownIcon className="w-4 h-4 text-gray-400" />}
          </button>

          {showExplanation && (
            <div className="px-5 pb-4 pt-2">
              <div
                className="text-sm text-gray-600 leading-relaxed
                  [&_strong]:text-gray-800 [&_h2]:text-base [&_h3]:text-sm [&_h4]:text-sm
                  [&_li]:text-gray-600 [&_br+br]:hidden"
                dangerouslySetInnerHTML={{ __html: parseMarkdown(product.explanation) }}
              />
              <div className="mt-3 pt-2 border-t border-gray-50 flex items-center gap-1">
                <SparklesIcon className="w-3 h-3 text-primary-400" />
                <span className="text-[10px] text-gray-400 font-medium uppercase tracking-wider">Powered by Amazon Nova</span>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default ProductCard;
