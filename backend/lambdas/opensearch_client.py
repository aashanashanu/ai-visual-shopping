import json
import boto3
from opensearchpy import OpenSearch, RequestsHttpConnection
from opensearchpy.exceptions import NotFoundError, RequestError
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

class OpenSearchClient:
    def __init__(self, endpoint: str, index_name: str = 'products'):
        self.endpoint = endpoint
        self.index_name = index_name
        self.client = OpenSearch(
            hosts=[{'host': endpoint.replace('https://', ''), 'port': 443}],
            http_auth=self._get_aws_auth(),
            use_ssl=True,
            verify_certs=True,
            connection_class=RequestsHttpConnection,
            timeout=30
        )

    def _get_aws_auth(self):
        """Get AWS authentication for OpenSearch"""
        import requests_aws4auth
        credentials = boto3.Session().get_credentials()
        return requests_aws4auth.AWS4Auth(
            credentials.access_key,
            credentials.secret_key,
            boto3.Session().region_name,
            'es',
            session_token=credentials.token
        )

    def create_index(self) -> bool:
        """
        Create OpenSearch index with k-NN configuration
        """
        index_body = {
            "settings": {
                "index": {
                    "knn": True,
                    "knn.algo_param.ef_search": 512
                }
            },
            "mappings": {
                "properties": {
                    "product_id": {
                        "type": "keyword"
                    },
                    "title": {
                        "type": "text",
                        "analyzer": "standard"
                    },
                    "description": {
                        "type": "text",
                        "analyzer": "standard"
                    },
                    "price": {
                        "type": "float"
                    },
                    "category": {
                        "type": "keyword"
                    },
                    "color": {
                        "type": "keyword"
                    },
                    "style": {
                        "type": "keyword"
                    },
                    "image_url": {
                        "type": "keyword"
                    },
                    "image_embedding": {
                        "type": "knn_vector",
                        "dimension": 1024,
                        "method": {
                            "name": "hnsw",
                            "space_type": "cosinesimil",
                            "engine": "nmslib",
                            "parameters": {
                                "ef_construction": 512,
                                "m": 16
                            }
                        }
                    }
                }
            }
        }
        
        try:
            # Delete index if it exists
            if self.client.indices.exists(index=self.index_name):
                self.client.indices.delete(index=self.index_name)
                logger.info(f"Deleted existing index: {self.index_name}")
            
            # Create new index
            response = self.client.indices.create(
                index=self.index_name,
                body=index_body
            )
            logger.info(f"Created index: {self.index_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating index: {str(e)}")
            return False

    def index_product(self, product: dict, embedding: list) -> bool:
        """
        Index a single product with its embedding
        """
        try:
            document = {
                "product_id": product["product_id"],
                "title": product["title"],
                "description": product["description"],
                "price": product["price"],
                "category": product["category"],
                "color": product["color"],
                "style": product["style"],
                "image_url": product["image_url"],
                "image_embedding": embedding
            }
            
            response = self.client.index(
                index=self.index_name,
                id=product["product_id"],
                body=document,
                refresh=True
            )
            logger.info(f"Indexed product: {product['product_id']}")
            return True
            
        except Exception as e:
            logger.error(f"Error indexing product {product['product_id']}: {str(e)}")
            return False

    def search_similar_products(self, query_embedding: list, size: int = 5, 
                               min_price: float = None, max_price: float = None,
                               color: str = None, category: str = None) -> list:
        """
        Search for similar products using k-NN vector search
        """
        try:
            # Build the k-NN query
            knn_query = {
                "size": size,
                "query": {
                    "knn": {
                        "image_embedding": {
                            "vector": query_embedding,
                            "k": size
                        }
                    }
                }
            }
            
            # Add filters if provided
            if min_price is not None or max_price is not None or color or category:
                filter_conditions = []
                
                if min_price is not None:
                    filter_conditions.append({
                        "range": {
                            "price": {
                                "gte": min_price
                            }
                        }
                    })
                
                if max_price is not None:
                    filter_conditions.append({
                        "range": {
                            "price": {
                                "lte": max_price
                            }
                        }
                    })
                
                if color:
                    filter_conditions.append({
                        "term": {
                            "color": color.lower()
                        }
                    })
                
                if category:
                    filter_conditions.append({
                        "term": {
                            "category": category.lower()
                        }
                    })
                
                if filter_conditions:
                    knn_query["query"]["knn"]["image_embedding"]["filter"] = {
                        "bool": {
                            "must": filter_conditions
                        }
                    }
            
            # Execute search
            response = self.client.search(
                index=self.index_name,
                body=knn_query
            )
            
            # Extract and format results
            products = []
            for hit in response['hits']['hits']:
                product = hit['_source']
                product['score'] = hit['_score']
                # Remove embedding from response to reduce payload size
                if 'image_embedding' in product:
                    del product['image_embedding']
                products.append(product)
            
            logger.info(f"Found {len(products)} similar products")
            return products
            
        except Exception as e:
            logger.error(f"Error searching similar products: {str(e)}")
            return []

    def get_product_by_id(self, product_id: str) -> dict:
        """
        Get a specific product by ID
        """
        try:
            response = self.client.get(
                index=self.index_name,
                id=product_id
            )
            product = response['_source']
            if 'image_embedding' in product:
                del product['image_embedding']
            return product
            
        except NotFoundError:
            logger.warning(f"Product not found: {product_id}")
            return None
        except Exception as e:
            logger.error(f"Error getting product {product_id}: {str(e)}")
            return None

    def index_bulk_products(self, products_with_embeddings: list) -> bool:
        """
        Bulk index multiple products
        """
        try:
            bulk_body = []
            for product, embedding in products_with_embeddings:
                # Index operation
                bulk_body.append({
                    "index": {
                        "_index": self.index_name,
                        "_id": product["product_id"]
                    }
                })
                
                # Document
                document = {
                    "product_id": product["product_id"],
                    "title": product["title"],
                    "description": product["description"],
                    "price": product["price"],
                    "category": product["category"],
                    "color": product["color"],
                    "style": product["style"],
                    "image_url": product["image_url"],
                    "image_embedding": embedding
                }
                bulk_body.append(document)
            
            # Execute bulk operation
            response = self.client.bulk(
                index=self.index_name,
                body=bulk_body,
                refresh=True
            )
            
            # Check for errors
            if response['errors']:
                logger.error("Bulk indexing had errors")
                return False
            else:
                logger.info(f"Successfully bulk indexed {len(products_with_embeddings)} products")
                return True
                
        except Exception as e:
            logger.error(f"Error in bulk indexing: {str(e)}")
            return False
