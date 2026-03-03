import json
import boto3
import base64
import os
import logging
from urllib.parse import unquote_plus
from typing import Dict, List, Any

from bedrock_client import BedrockClient
from s3_vector_store import S3VectorStore

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """
    Main Lambda handler for image search functionality
    """
    try:
        # Parse request body
        body = json.loads(event.get('body', '{}'))
        
        # Extract parameters with validation
        user_query = body.get('query', '')
        preferences = body.get('preferences', '')
        max_price = body.get('max_price')
        min_price = body.get('min_price')
        color = body.get('color')
        category = body.get('category')
        
        # Validate and sanitize size parameter
        try:
            size = int(body.get('size', 5))
            if size < 1:
                size = 1
            elif size > 5:  # Enforce max of 5 results from search API
                size = 5
        except (ValueError, TypeError):
            size = 5  # Default fallback
        
        # Extract and validate image data
        image_data = body.get('image')
        
        if not image_data:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Image data is required'
                })
            }
        
        # Validate image data length (base64 encoded, ~4/3 of original size)
        if len(image_data) > 10 * 1024 * 1024:  # 10MB limit
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Image data too large. Maximum size is 10MB.'
                })
            }
        
        # Initialize clients with environment validation
        region = os.environ.get('REGION', 'us-east-1')
        product_bucket = os.environ.get('PRODUCT_IMAGES_BUCKET')
        user_bucket = os.environ.get('USER_UPLOADS_BUCKET')
        
        if not product_bucket:
            logger.error("PRODUCT_IMAGES_BUCKET environment variable not set")
            return {
                'statusCode': 500,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Service configuration error. Please try again later.'
                })
            }
        
        bedrock_client = BedrockClient(region=region)
        vector_store = S3VectorStore(
            bucket_name=product_bucket,
            region=region
        )
        
        # Decode base64 image with validation
        if image_data.startswith('data:image/'):
            # Remove data URL prefix
            image_data = image_data.split(',')[1]
        
        try:
            image_bytes = base64.b64decode(image_data, validate=True)
        except Exception as e:
            logger.warning(f"Invalid base64 image data: {str(e)}")
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Invalid image data format. Please provide valid base64 encoded image.'
                })
            }
        
        # Generate embedding for the uploaded image
        logger.info("Generating embedding for uploaded image")
        query_embedding = bedrock_client.generate_multimodal_embedding(image_bytes)
        
        # Search for similar products
        logger.info("Searching for similar products")
        similar_product_ids = vector_store.search_similar(
            query_embedding=query_embedding,
            top_k=size * 2  # Get more results for filtering
        )
        
        # Get product details
        product_ids = [pid for pid, _ in similar_product_ids]
        all_products = vector_store.get_product_details(product_ids)
        
        # Convert to list and apply filters
        similar_products = []
        for product_id, similarity_score in similar_product_ids:
            if product_id in all_products:
                product = all_products[product_id]
                product['similarity_score'] = similarity_score
                
                # Apply filters with safe type checking
                product_price = product.get('price', 0)
                if isinstance(product_price, str):
                    try:
                        product_price = float(product_price)
                    except (ValueError, TypeError):
                        product_price = 0
                
                if min_price is not None and product_price < min_price:
                    continue
                if max_price is not None and product_price > max_price:
                    continue
                
                product_color = product.get('color', '').lower() if product.get('color') else ''
                if color and color.lower() != product_color:
                    continue
                
                product_category = product.get('category', '').lower() if product.get('category') else ''
                if category and category.lower() != product_category:
                    continue
                
                similar_products.append(product)
        
        logger.info(f"Found {len(similar_products)} similar products after filtering")
        
        # Apply AI-based filtering if preferences are provided (but not when explicit filters exist)
        if preferences and similar_products and not (color or category or min_price is not None or max_price is not None):
            logger.info("Applying AI-based filtering")
            filtered_products = bedrock_client.filter_products_by_preferences(
                products=similar_products,
                preferences=preferences,
                query=user_query
            )
            # Use filtered products if any match, otherwise use original results
            similar_products = filtered_products if filtered_products else similar_products
        elif preferences and similar_products:
            # If explicit filters were applied, log that we're skipping AI filtering
            logger.info("Skipping AI filtering - explicit filters already applied")
        
        # Limit to requested size
        similar_products = similar_products[:size]
        
        # Generate AI explanation
        explanation = ""
        if similar_products:
            logger.info("Generating AI explanation")
            try:
                explanation = bedrock_client.generate_explanation(
                    user_query=user_query,
                    products=similar_products,
                    user_preferences=preferences
                )
            except Exception as e:
                logger.warning(f"Failed to generate AI explanation: {str(e)}")
                explanation = "Found similar products based on your image search."
        
        response = {
            'products': similar_products,
            'explanation': explanation,
            'query': user_query,
            'preferences': preferences,
            'total_results': len(similar_products)
        }
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
                'Access-Control-Allow-Methods': 'POST,OPTIONS'
            },
            'body': json.dumps(response)
        }
        
    except Exception as e:
        logger.error(f"Error in image search: {str(e)}")
        # Don't expose internal error details to client
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,X-Amz-User-Agent,X-Requested-With',
                'Access-Control-Allow-Methods': 'POST,OPTIONS'
            },
            'body': json.dumps({
                'error': 'An internal error occurred. Please try again later.'
            })
        }

def _extract_price_from_preferences(preferences: str) -> tuple:
    """
    Extract price range from user preferences text
    Returns (min_price, max_price) tuple
    """
    import re
    
    min_price = None
    max_price = None
    
    # Look for price patterns like "under $100", "below $50", "over $200", "between $50 and $100"
    under_pattern = r'(?:under|below|less than)\s*\$?(\d+(?:\.\d{2})?)'
    over_pattern = r'(?:over|above|more than)\s*\$?(\d+(?:\.\d{2})?)'
    between_pattern = r'between\s*\$?(\d+(?:\.\d{2})?)\s*and\s*\$?(\d+(?:\.\d{2})?)'
    
    if re.search(between_pattern, preferences, re.IGNORECASE):
        match = re.search(between_pattern, preferences, re.IGNORECASE)
        min_price = float(match.group(1))
        max_price = float(match.group(2))
    elif re.search(under_pattern, preferences, re.IGNORECASE):
        match = re.search(under_pattern, preferences, re.IGNORECASE)
        max_price = float(match.group(1))
    elif re.search(over_pattern, preferences, re.IGNORECASE):
        match = re.search(over_pattern, preferences, re.IGNORECASE)
        min_price = float(match.group(1))
    
    return min_price, max_price

def _extract_color_from_preferences(preferences: str) -> str:
    """
    Extract color from user preferences text
    """
    colors = [
        'red', 'blue', 'green', 'yellow', 'black', 'white', 'gray', 'grey',
        'brown', 'pink', 'purple', 'orange', 'navy', 'beige', 'teal',
        'silver', 'gold', 'multicolor', 'multi-color'
    ]
    
    preferences_lower = preferences.lower()
    for color in colors:
        if color in preferences_lower:
            return color
    
    return None
