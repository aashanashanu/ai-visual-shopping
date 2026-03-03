import json
import os
import logging
from typing import Dict, List, Any

from bedrock_client import BedrockClient

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """
    Lambda handler for generating AI explanations
    """
    try:
        # Parse request body
        body = json.loads(event.get('body', '{}'))
        
        # Extract and validate parameters
        user_query = body.get('query', '')
        products = body.get('products', [])
        user_preferences = body.get('preferences', '')
        
        # Validate products list
        if not products or not isinstance(products, list):
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Products must be provided as a non-empty list'
                })
            }
        
        # Limit products to reasonable number
        if len(products) > 20:
            products = products[:20]
            logger.warning(f"Limited products to first 20 items from {len(body.get('products', []))}")
        
        # Initialize Bedrock client with environment validation
        region = os.environ.get('REGION', 'us-east-1')
        bedrock_client = BedrockClient(region=region)
        
        # Generate AI explanation
        logger.info("Generating AI explanation for products")
        explanation = bedrock_client.generate_explanation(
            user_query=user_query,
            products=products,
            user_preferences=user_preferences
        )
        
        response = {
            'explanation': explanation,
            'query': user_query,
            'preferences': user_preferences,
            'product_count': len(products)
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
        logger.error(f"Error generating explanation: {str(e)}")
        # Don't expose internal error details to client
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'An internal error occurred while generating explanation. Please try again later.'
            })
        }
