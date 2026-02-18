#!/usr/bin/env python3

import json
import boto3
import os
import logging
from urllib.request import urlopen
from io import BytesIO

from bedrock_client import BedrockClient
from opensearch_client import OpenSearchClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataSeeder:
    def __init__(self):
        self.s3_client = boto3.client('s3')
        self.bedrock_client = BedrockClient()
        self.opensearch_client = OpenSearchClient(
            endpoint=os.environ.get('OPENSEARCH_ENDPOINT'),
            index_name=os.environ.get('OPENSEARCH_INDEX', 'products')
        )
        self.product_images_bucket = os.environ.get('PRODUCT_IMAGES_BUCKET')
        self.catalog_file = 'sample_catalog.json'

    def generate_placeholder_image(self, product_title: str) -> bytes:
        """
        Generate a placeholder image using an online service
        """
        # Using placeholder.com to generate images
        # In production, you would use actual product images
        try:
            # Create a simple placeholder image URL
            encoded_title = product_title.replace(' ', '%20')
            image_url = f"https://via.placeholder.com/400x400/3b82f6/ffffff?text={encoded_title}"
            
            with urlopen(image_url) as response:
                return response.read()
        except Exception as e:
            logger.error(f"Error generating placeholder image for {product_title}: {str(e)}")
            # Return a simple 1x1 pixel image as fallback
            return b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc`\x00\x00\x00\x02\x00\x01\xe2!\xbc\x33\x00\x00\x00\x00IEND\xaeB`\x82'

    def upload_product_images(self, products: list) -> list:
        """
        Upload product images to S3 and return updated products with S3 URLs
        """
        logger.info("Uploading product images to S3...")
        
        updated_products = []
        
        for product in products:
            try:
                # Generate placeholder image
                image_bytes = self.generate_placeholder_image(product['title'])
                
                # Upload to S3
                s3_key = f"images/{product['product_id']}.jpg"
                self.s3_client.put_object(
                    Bucket=self.product_images_bucket,
                    Key=s3_key,
                    Body=image_bytes,
                    ContentType='image/jpeg',
                    ACL='public-read'
                )
                
                # Update product with S3 URL
                product['image_url'] = f"s3://{self.product_images_bucket}/{s3_key}"
                updated_products.append(product)
                
                logger.info(f"Uploaded image for product: {product['product_id']}")
                
            except Exception as e:
                logger.error(f"Error uploading image for {product['product_id']}: {str(e)}")
                # Keep original image URL if upload fails
                updated_products.append(product)
        
        return updated_products

    def generate_embeddings_for_products(self, products: list) -> list:
        """
        Generate multimodal embeddings for all product images
        """
        logger.info("Generating embeddings for product images...")
        
        products_with_embeddings = []
        
        for product in products:
            try:
                # Download image from S3
                if product['image_url'].startswith('s3://'):
                    # Parse S3 URL
                    s3_parts = product['image_url'].replace('s3://', '').split('/')
                    bucket = s3_parts[0]
                    key = '/'.join(s3_parts[1:])
                    
                    response = self.s3_client.get_object(Bucket=bucket, Key=key)
                    image_bytes = response['Body'].read()
                else:
                    # Generate placeholder image
                    image_bytes = self.generate_placeholder_image(product['title'])
                
                # Generate embedding
                embedding = self.bedrock_client.generate_multimodal_embedding(image_bytes)
                
                products_with_embeddings.append((product, embedding))
                logger.info(f"Generated embedding for product: {product['product_id']}")
                
            except Exception as e:
                logger.error(f"Error generating embedding for {product['product_id']}: {str(e)}")
                # Skip this product if embedding fails
                continue
        
        return products_with_embeddings

    def seed_opensearch_index(self, products_with_embeddings: list) -> bool:
        """
        Seed OpenSearch with product data and embeddings
        """
        logger.info("Seeding OpenSearch index...")
        
        try:
            # Create index
            if not self.opensearch_client.create_index():
                logger.error("Failed to create OpenSearch index")
                return False
            
            # Bulk index products
            success = self.opensearch_client.index_bulk_products(products_with_embeddings)
            
            if success:
                logger.info(f"Successfully indexed {len(products_with_embeddings)} products")
                return True
            else:
                logger.error("Failed to bulk index products")
                return False
                
        except Exception as e:
            logger.error(f"Error seeding OpenSearch: {str(e)}")
            return False

    def load_catalog(self) -> list:
        """
        Load product catalog from JSON file
        """
        try:
            with open(self.catalog_file, 'r') as f:
                data = json.load(f)
                return data['products']
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
        
        # Seed OpenSearch
        success = self.seed_opensearch_index(products_with_embeddings)
        
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
    seeder = DataSeeder()
    success = seeder.run_seeding_process()
    
    return {
        'statusCode': 200 if success else 500,
        'body': json.dumps({
            'message': 'Data seeding completed successfully' if success else 'Data seeding failed'
        })
    }

if __name__ == "__main__":
    # For local testing
    seeder = DataSeeder()
    seeder.run_seeding_process()
