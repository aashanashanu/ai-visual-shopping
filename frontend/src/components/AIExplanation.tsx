import React from 'react';
import { LightBulbIcon, SparklesIcon, InformationCircleIcon } from '@heroicons/react/24/outline';

interface AIExplanationProps {
  explanation: string;
  isLoading: boolean;
  query?: string;
  preferences?: string;
}

const AIExplanation: React.FC<AIExplanationProps> = ({ 
  explanation, 
  isLoading, 
  query, 
  preferences 
}) => {
  
  // Parse markdown-like formatting to HTML
  const parseMarkdown = (text: string): string => {
    if (!text) return '';
    
    return text
      // Headers
      .replace(/### (.*$)/gim, '<h3 class="text-lg font-bold text-gray-800 mt-4 mb-2">$1</h3>')
      .replace(/## (.*$)/gim, '<h2 class="text-xl font-bold text-gray-900 mt-5 mb-3">$1</h2>')
      .replace(/# (.*$)/gim, '<h1 class="text-2xl font-bold text-gray-900 mt-6 mb-4">$1</h1>')
      // Bold
      .replace(/\*\*(.*?)\*\*/g, '<strong class="font-semibold text-gray-900">$1</strong>')
      // Italic
      .replace(/\*(.*?)\*/g, '<em class="italic">$1</em>')
      // Bullet points
      .replace(/^\- (.*$)/gim, '<li class="ml-4 mb-1 flex items-start"><span class="mr-2 mt-1.5 w-1.5 h-1.5 bg-primary-500 rounded-full flex-shrink-0"></span><span>$1</span></li>')
      // Numbered lists
      .replace(/^\d+\. (.*$)/gim, '<li class="ml-4 mb-1 flex items-start"><span class="mr-2 font-semibold text-primary-600 flex-shrink-0">•</span><span>$1</span></li>')
      // Line breaks
      .replace(/\n/g, '<br />');
  };

  if (isLoading) {
    return (
      <div className="bg-gradient-to-br from-primary-50 to-purple-50 rounded-2xl p-6 border border-primary-100">
        <div className="flex items-center mb-4">
          <div className="w-10 h-10 bg-primary-600 rounded-xl flex items-center justify-center mr-4 shadow-lg shadow-primary-200">
            <SparklesIcon className="w-6 h-6 text-white animate-pulse" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-gray-900">AI Shopping Assistant</h3>
            <p className="text-sm text-gray-500">Analyzing your preferences...</p>
          </div>
        </div>
        <div className="flex items-center justify-center py-8">
          <div className="flex space-x-2">
            <div className="w-3 h-3 bg-primary-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
            <div className="w-3 h-3 bg-primary-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
            <div className="w-3 h-3 bg-primary-600 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
          </div>
        </div>
      </div>
    );
  }

  if (!explanation) {
    return (
      <div className="bg-gray-50 rounded-2xl p-8 border-2 border-dashed border-gray-200">
        <div className="text-center">
          <div className="w-16 h-16 bg-white rounded-2xl shadow-sm flex items-center justify-center mx-auto mb-4">
            <LightBulbIcon className="w-8 h-8 text-gray-400" />
          </div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">
            Get Personalized Recommendations
          </h3>
          <p className="text-gray-500 max-w-sm mx-auto">
            Upload an image and describe what you're looking for. Our AI will explain why each product is a great match for you.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-2xl shadow-lg border border-gray-100 overflow-hidden">
      {/* Header */}
      <div className="bg-gradient-to-r from-primary-600 to-purple-600 px-6 py-4">
        <div className="flex items-center">
          <div className="w-10 h-10 bg-white/20 backdrop-blur-sm rounded-xl flex items-center justify-center mr-4">
            <SparklesIcon className="w-6 h-6 text-white" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-white">Why These Products?</h3>
            <p className="text-sm text-white/80">AI-powered personalized recommendations</p>
          </div>
        </div>
      </div>

      {/* User Context */}
      {(query || preferences) && (
        <div className="bg-gray-50 px-6 py-4 border-b border-gray-100">
          <div className="flex items-start gap-2 mb-2">
            <InformationCircleIcon className="w-4 h-4 text-gray-400 mt-0.5" />
            <span className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Your Request</span>
          </div>
          {query && (
            <div className="mb-2">
              <span className="text-xs text-gray-500">Query: </span>
              <span className="text-sm text-gray-800 font-medium">{query}</span>
            </div>
          )}
          {preferences && (
            <div>
              <span className="text-xs text-gray-500">Preferences: </span>
              <span className="text-sm text-gray-800 font-medium">{preferences}</span>
            </div>
          )}
        </div>
      )}

      {/* Explanation Content */}
      <div className="p-6">
        <div 
          className="prose prose-sm max-w-none text-gray-700 leading-relaxed"
          dangerouslySetInnerHTML={{ __html: parseMarkdown(explanation) }}
        />
      </div>

      {/* Footer */}
      <div className="bg-gray-50 px-6 py-3 border-t border-gray-100">
        <div className="flex items-center justify-between">
          <span className="text-xs text-gray-500">Powered by Amazon Nova</span>
          <div className="flex items-center gap-1">
            <SparklesIcon className="w-3 h-3 text-primary-500" />
            <span className="text-xs font-medium text-primary-600">AI Generated</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AIExplanation;
