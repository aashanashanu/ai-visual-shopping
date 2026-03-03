export interface Product {
  product_id: string;
  title: string;
  description: string;
  price: number;
  category: string;
  color: string;
  style: string;
  material?: string;
  brand?: string;
  image_url: string;
  score?: number;
}

export interface SearchRequest {
  image: string;
  query: string;
  preferences?: string;
  max_price?: number;
  min_price?: number;
  color?: string;
  category?: string;
  size?: number;
}

export interface SearchResponse {
  products: Product[];
  explanation: string;
  query: string;
  preferences: string;
  total_results: number;
}

export interface ExplanationRequest {
  query: string;
  products: Product[];
  preferences?: string;
}

export interface ExplanationResponse {
  explanation: string;
  query: string;
  preferences: string;
  product_count: number;
}
