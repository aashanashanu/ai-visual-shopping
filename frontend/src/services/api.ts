import axios from 'axios';
import { SearchRequest, SearchResponse, ExplanationRequest, ExplanationResponse } from '../types';

const API_BASE_URL = process.env.REACT_APP_API_URL;

if (!API_BASE_URL) {
  throw new Error('REACT_APP_API_URL environment variable is required. Please configure the API URL in your .env file.');
}

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 60000, // 60 seconds to match Lambda timeout
});

export const searchProducts = async (request: SearchRequest): Promise<SearchResponse> => {
  try {
    const response = await api.post('/search', request);
    return response.data;
  } catch (error) {
    console.error('Error searching products:', error);
    throw error;
  }
};

export const generateExplanation = async (request: ExplanationRequest): Promise<ExplanationResponse> => {
  try {
    const response = await api.post('/explain', request);
    return response.data;
  } catch (error) {
    console.error('Error generating explanation:', error);
    throw error;
  }
};

export const uploadImageToS3 = async (file: File): Promise<string> => {
  // This would implement direct S3 upload if needed
  // For now, we'll convert to base64 in the component
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      const result = reader.result as string;
      resolve(result);
    };
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
};
