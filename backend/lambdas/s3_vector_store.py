import json
import math
from typing import List, Dict, Tuple
import boto3
import os
from datetime import datetime

class S3VectorStore:
    """
    S3-backed vector storage for product embeddings
    Ultra-low cost alternative to OpenSearch for cost-optimized deployments
    """
    
    def __init__(self, bucket_name: str, region: str = "us-east-1"):
        self.s3 = boto3.client('s3', region_name=region)
        self.bucket_name = bucket_name
        self.embeddings_cache = None
        self.products_cache = None
        
    def load_embeddings(self) -> Dict[str, List[float]]:
        """Load all embeddings from S3"""
        if not self.embeddings_cache:
            try:
                response = self.s3.get_object(
                    Bucket=self.bucket_name, 
                    Key='embeddings/product_embeddings.json'
                )
                self.embeddings_cache = json.loads(response['Body'].read())
                print(f"Loaded {len(self.embeddings_cache)} embeddings from S3")
            except self.s3.exceptions.NoSuchKey:
                print("No embeddings found in S3, starting fresh")
                self.embeddings_cache = {}
        return self.embeddings_cache
    
    def load_products(self) -> Dict[str, Dict]:
        """Load product catalog from S3"""
        if not self.products_cache:
            try:
                response = self.s3.get_object(
                    Bucket=self.bucket_name,
                    Key='catalog/products.json'
                )
                self.products_cache = json.loads(response['Body'].read())
                print(f"Loaded {len(self.products_cache)} products from S3")
            except self.s3.exceptions.NoSuchKey:
                print("No products found in S3")
                self.products_cache = {}
        return self.products_cache
    
    def save_embeddings(self, embeddings: Dict[str, List[float]]):
        """Save embeddings to S3"""
        self.embeddings_cache = embeddings
        
        # Save to S3
        self.s3.put_object(
            Bucket=self.bucket_name,
            Key='embeddings/product_embeddings.json',
            Body=json.dumps(embeddings, indent=2),
            ContentType='application/json'
        )
        
        # Save backup with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.s3.put_object(
            Bucket=self.bucket_name,
            Key=f'embeddings/backup/product_embeddings_{timestamp}.json',
            Body=json.dumps(embeddings, indent=2),
            ContentType='application/json'
        )
        
        print(f"Saved {len(embeddings)} embeddings to S3")
    
    def save_products(self, products: Dict[str, Dict]):
        """Save product catalog to S3"""
        self.products_cache = products
        
        # Convert to list format for easier consumption
        products_list = list(products.values())
        
        self.s3.put_object(
            Bucket=self.bucket_name,
            Key='catalog/products.json',
            Body=json.dumps(products_list, indent=2),
            ContentType='application/json'
        )
        
        print(f"Saved {len(products)} products to S3")
    
    def _vector_norm(self, vector: List[float]) -> float:
        """Calculate vector norm using pure Python"""
        return math.sqrt(sum(x * x for x in vector))
    
    def _dot_product(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate dot product using pure Python"""
        return sum(a * b for a, b in zip(vec1, vec2))

    def add_embedding(self, product_id: str, embedding: List[float], product_data: Dict) -> bool:
        """Add or update a single embedding"""
        embeddings = self.load_embeddings()
        embeddings[product_id] = embedding
        self.save_embeddings(embeddings)
        return True
    
    def search_similar(self, query_embedding: List[float], top_k: int = 10) -> List[Tuple[str, float]]:
        """
        Perform k-NN search using cosine similarity
        Returns: List of (product_id, similarity_score) tuples
        """
        embeddings = self.load_embeddings()
        
        if not embeddings:
            print("No embeddings available for search")
            return []
        
        if not query_embedding or len(query_embedding) == 0:
            print("Invalid query embedding")
            return []
        
        similarities = []
        query_norm = self._vector_norm(query_embedding)
        
        if query_norm == 0:
            print("Query embedding has zero norm")
            return []
        
        for product_id, embedding in embeddings.items():
            if not embedding or len(embedding) == 0:
                continue  # Skip invalid embeddings
                
            embedding_norm = self._vector_norm(embedding)
            if embedding_norm > 0:
                similarity = self._dot_product(query_embedding, embedding) / (query_norm * embedding_norm)
                # Clamp similarity to [-1, 1] range in case of floating point errors
                similarity = max(-1.0, min(1.0, similarity))
                similarities.append((product_id, float(similarity)))
        
        # Sort by similarity (descending) and return top_k
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]
    
    def get_product_details(self, product_ids: List[str]) -> Dict[str, Dict]:
        """Get product details for given product IDs"""
        products = self.load_products()
        products_dict = {}
        
        # Convert list back to dict if needed
        if isinstance(products, list):
            products_dict = {product['product_id']: product for product in products}
        else:
            products_dict = products
        
        return {pid: products_dict.get(pid) for pid in product_ids if pid in products_dict}
    
    def get_stats(self) -> Dict[str, int]:
        """Get storage statistics"""
        embeddings = self.load_embeddings()
        products = self.load_products()
        
        return {
            'total_embeddings': len(embeddings),
            'total_products': len(products) if isinstance(products, list) else len(products),
            'embedding_dimension': len(next(iter(embeddings.values()), [])),
            'last_updated': datetime.now().isoformat()
        }
    
    def delete_all_data(self):
        """Delete all stored data (for cleanup)"""
        try:
            self.s3.delete_object(Bucket=self.bucket_name, Key='embeddings/product_embeddings.json')
            self.s3.delete_object(Bucket=self.bucket_name, Key='catalog/products.json')
            self.embeddings_cache = None
            self.products_cache = None
            print("Deleted all data from S3")
        except Exception as e:
            print(f"Error deleting data: {e}")

# Initialize global vector store
VECTOR_STORE = None

def get_vector_store(bucket_name: str, region: str = "us-east-1") -> S3VectorStore:
    """Get vector store instance - creates fresh instance to avoid cache race conditions"""
    return S3VectorStore(bucket_name, region)
