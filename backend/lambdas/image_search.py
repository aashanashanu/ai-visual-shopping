import json
import boto3
import base64
import os
import logging
from urllib.parse import unquote_plus
from typing import Dict, List, Any

from bedrock_client import BedrockClient
from opensearch_client import OpenSearchClient

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """
    Main Lambda handler for image search functionality
    """
    try:
        # Parse request body
        body = json.loads(event.get('body', '{}'))
        
        # Extract parameters
        image_data = body.get('image')
        user_query = body.get('query', '')
        preferences = body.get('preferences', '')
        max_price = body.get('max_price')
        min_price = body.get('min_price')
        color = body.get('color')
        category = body.get('category')
        size = int(body.get('size', 5))
        
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
        
        # Initialize clients
        bedrock_client = BedrockClient(region=os.environ.get('REGION', 'us-east-1'))
        opensearch_client = OpenSearchClient(
            endpoint=os.environ.get('OPENSEARCH_ENDPOINT'),
            index_name=os.environ.get('OPENSEARCH_INDEX', 'products')
        )
        
        # Decode base64 image
        if image_data.startswith('data:image/'):
            # Remove data URL prefix
            image_data = image_data.split(',')[1]
        
        image_bytes = base64.b64decode(image_data)
        
        # Generate embedding for the uploaded image
        logger.info("Generating embedding for uploaded image")
        query_embedding = bedrock_client.generate_multimodal_embedding(image_bytes)
        
        # Search for similar products
        logger.info("Searching for similar products")
        similar_products = opensearch_client.search_similar_products(
            query_embedding=query_embedding,
            size=size * 2,  # Get more results for filtering
            min_price=min_price,
            max_price=max_price,
            color=color,
            category=category
        )
        
        # Apply AI-based filtering if preferences are provided
        if preferences and similar_products:
            logger.info("Applying AI-based filtering")
            filtered_products = bedrock_client.filter_products_by_preferences(
                products=similar_products,
                preferences=preferences
            )
            # Use filtered products if any match, otherwise use original results
            similar_products = filtered_products if filtered_products else similar_products
        
        # Limit to requested size
        similar_products = similar_products[:size]
        
        # Generate AI explanation
        explanation = ""
        if similar_products:
            logger.info("Generating AI explanation")
            explanation = bedrock_client.generate_explanation(
                user_query=user_query,
                products=similar_products,
                user_preferences=preferences
            )
        
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
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Internal server error',
                'message': str(e)
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
