#!/usr/bin/env python3

import json
import boto3
import os
import logging
from urllib.request import urlopen
import io
import time

from bedrock_client import BedrockClient
from s3_vector_store import S3VectorStore

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataSeeder:
    def __init__(self):
        # Validate required environment variables
        self.region = os.environ.get('REGION', 'us-east-1')
        self.product_images_bucket = os.environ.get('PRODUCT_IMAGES_BUCKET')

        if not self.product_images_bucket:
            raise ValueError("PRODUCT_IMAGES_BUCKET environment variable is required")

        # Configuration limits
        self.max_products = 50  # Limit total products to process
        self.max_image_size = 2 * 1024 * 1024  # 2MB per image
        self.max_description_length = 1000  # Max description length

        try:
            self.s3_client = boto3.client('s3', region_name=self.region)
            self.bedrock_client = BedrockClient(region=self.region)
            self.vector_store = S3VectorStore(
                bucket_name=self.product_images_bucket,
                region=self.region
            )
        except Exception as e:
            logger.error(f"Failed to initialize AWS clients: {str(e)}")
            raise

        # Try multiple locations for catalog file (Lambda vs local)
        possible_catalog_paths = [
            '/var/task/sample_catalog.json',  # Lambda root
            os.path.join(os.path.dirname(__file__), 'sample_catalog.json'),  # Same dir as script
            os.path.join(os.path.dirname(__file__), '..', '..', 'sample_catalog.json'),  # Project root
        ]
        
        self.catalog_file = None
        for path in possible_catalog_paths:
            if os.path.exists(path):
                self.catalog_file = path
                logger.info(f"Found catalog file at: {path}")
                break
        
        if not self.catalog_file:
            raise FileNotFoundError(f"Catalog file not found. Searched: {possible_catalog_paths}")

        # Validate S3 bucket exists and is accessible
        self._validate_s3_bucket()

    def _validate_s3_bucket(self):
        """Validate that the S3 bucket exists and is accessible"""
        try:
            self.s3_client.head_bucket(Bucket=self.product_images_bucket)
            logger.info(f"S3 bucket validated: {self.product_images_bucket}")
        except self.s3_client.exceptions.NoSuchBucket:
            raise ValueError(f"S3 bucket does not exist: {self.product_images_bucket}")
        except self.s3_client.exceptions.ClientError as e:
            if e.response['Error']['Code'] == '403':
                raise PermissionError(f"No access to S3 bucket: {self.product_images_bucket}")
            else:
                raise ValueError(f"S3 bucket access error: {str(e)}")
        except Exception as e:
            raise ValueError(f"Failed to validate S3 bucket: {str(e)}")

    def upload_product_images(self, products: list) -> list:
        """
        Upload product images from local products folder to S3 and return updated products with S3 URLs
        """
        logger.info("Uploading product images to S3...")
        
        updated_products = []
        
        for product in products:
            try:
                product_id = product.get('product_id') or product.get('id')
                image_url = product.get('image_url', '')
                
                # Validate product structure
                if not isinstance(product, dict):
                    logger.warning(f"Skipping invalid product (not a dict): {product}")
                    continue
                    
                if not product_id:
                    logger.warning(f"Skipping product without ID: {product}")
                    continue
                
                # Sanitize product_id to prevent path traversal
                product_id = str(product_id).replace('/', '_').replace('\\', '_')
                if not product_id or len(product_id) > 100:
                    logger.warning(f"Skipping product with invalid ID: {product_id}")
                    continue
                
                logger.info(f"Processing product: {product_id}")
                
                # Check if image_url is a local path (starts with 'products/')
                if image_url.startswith('products/'):
                    # Validate and sanitize the image path
                    if '..' in image_url or not image_url.startswith('products/'):
                        logger.warning(f"Skipping product with suspicious image path: {image_url}")
                        # Keep original product but skip image processing
                        updated_products.append(product)
                        continue
                    
                    # Construct safe local path
                    image_filename = os.path.basename(image_url)
                    if not image_filename or image_filename.startswith('.'):
                        logger.warning(f"Skipping product with invalid image filename: {image_filename}")
                        updated_products.append(product)
                        continue
                    
                    # In Lambda environment, files are extracted to /var/task/
                    # Check multiple possible locations for the image
                    possible_paths = [
                        f'/var/task/{image_url}',                              # Lambda root (highest priority)
                        os.path.join(os.path.dirname(__file__), image_url),   # Same dir as script
                        os.path.join(os.path.dirname(__file__), '..', '..', image_url),  # Project root
                        os.path.join(os.getcwd(), image_url),                  # Current working directory
                    ]
                    
                    local_image_path = None
                    for path in possible_paths:
                        if os.path.exists(path):
                            local_image_path = path
                            break
                    
                    if not local_image_path:
                        logger.warning(f"⚠️ Local image file not found in any location: {image_filename}")
                        updated_products.append(product)
                        continue
                    
                    try:
                        with open(local_image_path, 'rb') as image_file:
                            image_bytes = image_file.read()
                        
                        # Validate image size
                        if len(image_bytes) > self.max_image_size:
                            logger.warning(f"Image too large ({len(image_bytes)} bytes), skipping: {local_image_path}")
                            updated_products.append(product)
                            continue
                            
                        if len(image_bytes) < 100:
                            logger.warning(f"Image too small ({len(image_bytes)} bytes), skipping: {local_image_path}")
                            updated_products.append(product)
                            continue
                        
                        # Generate S3 key
                        s3_key = f"images/{product_id}.png"
                        
                        # Upload to S3
                        self.s3_client.put_object(
                            Bucket=self.product_images_bucket,
                            Key=s3_key,
                            Body=image_bytes,
                            ContentType='image/png'
                        )
                        
                        # Update product with public S3 URL
                        product['image_url'] = f"https://{self.product_images_bucket}.s3.{self.region}.amazonaws.com/{s3_key}"
                        product['s3_key'] = s3_key
                        
                        logger.info(f"✅ Uploaded image for {product_id} to {s3_key}")
                        
                    except FileNotFoundError:
                        logger.warning(f"⚠️ Local image file not found: {local_image_path}")
                        # Keep original URL if file not found
                        pass
                    except Exception as e:
                        logger.error(f"❌ Error uploading image for {product_id}: {str(e)}")
                        # Keep original URL if upload fails
                        pass
                else:
                    # Keep existing S3 URL or other format
                    logger.info(f"Keeping existing image URL for {product_id}: {image_url}")
                
                updated_products.append(product)
                
            except Exception as e:
                logger.error(f"Error processing product {product.get('product_id') or product.get('id')}: {str(e)}")
                # Keep original product if processing fails
                updated_products.append(product)
        
        logger.info(f"✅ Processed {len(updated_products)} products")
        return updated_products

    def generate_embeddings_for_products(self, products: list) -> list:
        """
        Generate multimodal embeddings for all product images
        """
        logger.info("Generating embeddings for product images...")
        
        products_with_embeddings = []
        
        for product in products:
            try:
                image_url = product.get('image_url', '')
                product_id = product.get('product_id') or product.get('id')
                
                # Download image from S3 - handle both s3:// and https:// formats
                if image_url.startswith('s3://'):
                    # Parse S3 URL: s3://bucket/key
                    s3_parts = image_url.replace('s3://', '').split('/')
                    bucket = s3_parts[0]
                    key = '/'.join(s3_parts[1:])
                    
                    try:
                        response = self.s3_client.get_object(Bucket=bucket, Key=key)
                        image_bytes = response['Body'].read()
                    except Exception as e:
                        logger.warning(f"Could not download image from S3 for {product_id}: {str(e)}")
                        continue
                        
                elif image_url.startswith('https://') and 's3' in image_url:
                    # Parse HTTPS URL: https://bucket.s3.region.amazonaws.com/key
                    # Extract bucket and key from URL
                    url_parts = image_url.replace('https://', '').split('/')
                    # First part is bucket.s3.region.amazonaws.com
                    domain_parts = url_parts[0].split('.')
                    bucket = domain_parts[0]
                    key = '/'.join(url_parts[1:])
                    
                    try:
                        response = self.s3_client.get_object(Bucket=bucket, Key=key)
                        image_bytes = response['Body'].read()
                    except Exception as e:
                        logger.warning(f"Could not download image from S3 for {product_id}: {str(e)}")
                        continue
                else:
                    # Skip products without S3 URLs
                    logger.warning(f"Skipping product without S3 URL: {product_id}")
                    continue
                
                # Generate embedding
                embedding = self.bedrock_client.generate_multimodal_embedding(image_bytes)
                
                # Add embedding to product
                product_with_embedding = product.copy()
                product_with_embedding['embedding'] = embedding
                products_with_embeddings.append(product_with_embedding)
                logger.info(f"Generated embedding for product: {product.get('product_id') or product.get('id')}")
                
            except Exception as e:
                logger.error(f"Error generating embedding for {product.get('product_id') or product.get('id')}: {str(e)}")
                # Skip this product if embedding fails
                continue
        
        return products_with_embeddings

    def seed_vector_store(self, products_with_embeddings: list) -> bool:
        """
        Seed S3 vector store with product data and embeddings
        """
        logger.info("Seeding S3 vector store...")
        
        try:
            # Prepare embeddings dict
            embeddings_dict = {}
            products_dict = {}
            
            for product in products_with_embeddings:
                # Handle both 'id' and 'product_id' field names
                product_id = product.get('product_id') or product.get('id')
                if not product_id:
                    logger.error(f"Product missing 'id' or 'product_id' field: {product}")
                    continue
                    
                embeddings_dict[product_id] = product['embedding']
                
                # Remove embedding from product data for storage
                product_copy = product.copy()
                product_copy.pop('embedding', None)
                products_dict[product_id] = product_copy
            
            # Save to S3 vector store
            self.vector_store.save_embeddings(embeddings_dict)
            self.vector_store.save_products(products_dict)
            
            logger.info(f"Successfully stored {len(products_with_embeddings)} products in S3 vector store")
            
            # Print stats
            stats = self.vector_store.get_stats()
            logger.info(f"Vector store stats: {stats}")
            
            return True
                
        except Exception as e:
            logger.error(f"Error seeding S3 vector store: {str(e)}")
            return False

    def load_catalog(self) -> list:
        """
        Load product catalog from JSON file
        """
        try:
            with open(self.catalog_file, 'r') as f:
                data = json.load(f)
                
            # Validate data structure
            if not isinstance(data, (list, dict)):
                logger.error(f"Invalid catalog format: expected list or dict, got {type(data)}")
                return []
                
            # Handle both direct array and nested object formats
            if isinstance(data, list):
                products = data
            elif isinstance(data, dict) and 'products' in data:
                products = data['products']
                if not isinstance(products, list):
                    logger.error("Invalid catalog format: 'products' field must be a list")
                    return []
            else:
                logger.error(f"Invalid catalog format: expected list or dict with 'products' key")
                return []
            
            # Validate and clean products
            validated_products = []
            for i, product in enumerate(products):
                if not isinstance(product, dict):
                    logger.warning(f"Skipping invalid product at index {i}: not a dictionary")
                    continue
                    
                # Validate required fields
                product_id = product.get('product_id') or product.get('id')
                if not product_id:
                    logger.warning(f"Skipping product at index {i}: missing 'product_id' or 'id' field")
                    continue
                    
                # Validate product structure
                validated_product = {
                    'product_id': str(product_id),
                    'name': str(product.get('name', product.get('title', f'Product {product_id}'))),
                    'description': str(product.get('description', '')),
                    'price': product.get('price', 0),
                    'image_url': str(product.get('image_url', '')),
                    'color': str(product.get('color', '')),
                    'style': str(product.get('style', '')),
                    'category': str(product.get('category', '')),
                    'material': str(product.get('material', '')),
                    'brand': str(product.get('brand', '')),
                    'size': str(product.get('size', ''))
                }
                
                # Validate price is numeric
                if isinstance(validated_product['price'], str):
                    try:
                        validated_product['price'] = float(validated_product['price'])
                    except (ValueError, TypeError):
                        logger.warning(f"Invalid price for product {product_id}, setting to 0")
                        validated_product['price'] = 0.0
                
                validated_products.append(validated_product)
            
            logger.info(f"Validated {len(validated_products)} products from catalog")
            return validated_products
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in catalog file: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Error loading catalog: {str(e)}")
            return []

    def run_seeding_process(self) -> bool:
        """
        Run the complete data seeding process
        """
        logger.info("Starting data seeding process...")
        
        # Load catalog
        products = self.load_catalog()
        if not products:
            logger.error("No products found in catalog")
            return False
        
        logger.info(f"Loaded {len(products)} products from catalog")
        
        # Upload images to S3
        products_with_s3_urls = self.upload_product_images(products)
        
        # Generate embeddings
        products_with_embeddings = self.generate_embeddings_for_products(products_with_s3_urls)
        
        if not products_with_embeddings:
            logger.error("No embeddings generated")
            return False
        
        # Seed S3 vector store
        success = self.seed_vector_store(products_with_embeddings)
        
        if success:
            logger.info("Data seeding completed successfully!")
            return True
        else:
            logger.error("Data seeding failed!")
            return False

def lambda_handler(event, context):
    """
    Lambda handler for seeding data
    """
    start_time = time.time()
    logger.info("Data seeding Lambda started")
    
    try:
        seeder = DataSeeder()
        success = seeder.run_seeding_process()
        
        execution_time = time.time() - start_time
        
        if success:
            logger.info(".2f")
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'success': True,
                    'message': 'Data seeding completed successfully',
                    'execution_time_seconds': round(execution_time, 2),
                    'timestamp': time.time()
                })
            }
        else:
            logger.error("Data seeding failed")
            return {
                'statusCode': 500,
                'body': json.dumps({
                    'success': False,
                    'message': 'Data seeding failed - check logs for details',
                    'execution_time_seconds': round(execution_time, 2),
                    'timestamp': time.time(),
                    'error_type': 'seeding_failure'
                })
            }
            
    except ValueError as e:
        # Configuration/validation errors
        logger.error(f"Configuration error: {str(e)}")
        return {
            'statusCode': 400,
            'body': json.dumps({
                'success': False,
                'message': f'Configuration error: {str(e)}',
                'error_type': 'configuration_error',
                'timestamp': time.time()
            })
        }
        
    except FileNotFoundError as e:
        # File access errors
        logger.error(f"File access error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'success': False,
                'message': f'File access error: {str(e)}',
                'error_type': 'file_access_error',
                'timestamp': time.time()
            })
        }
        
    except Exception as e:
        # Generic error handling
        logger.error(f"Unexpected error in data seeding: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'success': False,
                'message': 'An unexpected error occurred during data seeding',
                'error_type': 'unexpected_error',
                'timestamp': time.time(),
                'error_details': str(e) if len(str(e)) < 500 else str(e)[:500] + '...'
            })
        }

if __name__ == "__main__":
    # For local testing
    seeder = DataSeeder()
    seeder.run_seeding_process()
