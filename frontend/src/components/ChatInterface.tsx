import React from 'react';

interface ChatInterfaceProps {
  explanation: string;
  isLoading: boolean;
}

const ChatInterface: React.FC<ChatInterfaceProps> = ({ explanation, isLoading }) => {
  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <div className="flex items-center mb-4">
        <div className="w-8 h-8 bg-primary-600 rounded-full flex items-center justify-center mr-3">
          <svg
            className="w-5 h-5 text-white"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-4l-4 4z"
            />
          </svg>
        </div>
        <h3 className="text-lg font-semibold text-gray-900">AI Shopping Assistant</h3>
      </div>
      
      {isLoading ? (
        <div className="flex items-center justify-center py-8">
          <div className="loading-spinner"></div>
          <span className="ml-3 text-gray-600">Analyzing your image...</span>
        </div>
      ) : explanation ? (
        <div className="prose prose-sm max-w-none">
          <div className="bg-gray-50 rounded-lg p-4">
            <p className="text-gray-800 leading-relaxed">{explanation}</p>
          </div>
        </div>
      ) : (
        <div className="text-gray-500 text-center py-8">
          <svg
            className="w-12 h-12 mx-auto mb-3 text-gray-300"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
            />
          </svg>
          <p>Upload an image and add your preferences to get personalized recommendations</p>
        </div>
      )}
    </div>
  );
};

export default ChatInterface;
