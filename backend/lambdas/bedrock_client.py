import json
import boto3
import base64
from typing import Dict, List, Any

class BedrockClient:
    def __init__(self, region: str = 'us-east-1'):
        self.client = boto3.client('bedrock-runtime', region_name=region)
        self.region = region

    def generate_multimodal_embedding(self, image_bytes: bytes) -> List[float]:
        """
        Generate embedding using Amazon Nova Multimodal Embedding model
        """
        # Convert image to base64
        image_base64 = base64.b64encode(image_bytes).decode('utf-8')
        
        request_body = {
            "inputImage": image_base64,
            "embeddingConfig": {
                "outputEmbeddingLength": 1024
            }
        }
        
        try:
            response = self.client.invoke_model(
                modelId="amazon.nova-multimodal-embedding-v1:0",
                body=json.dumps(request_body),
                contentType="application/json",
                accept="application/json"
            )
            
            response_body = json.loads(response['body'].read())
            return response_body['embedding']
            
        except Exception as e:
            print(f"Error generating embedding: {str(e)}")
            raise e

    def generate_explanation(
        self, 
        user_query: str, 
        products: List[Dict[str, Any]], 
        user_preferences: str = ""
    ) -> str:
        """
        Generate explanation using Nova 2 Lite model
        """
        # Format product information for the prompt
        products_text = "\n".join([
            f"Product {i+1}: {product['title']} - ${product['price']} - {product['description']}"
            for i, product in enumerate(products[:5])
        ])
        
        system_prompt = """You are a helpful AI shopping assistant. Based on the user's uploaded image and preferences, 
        explain why the recommended products are good matches. Be conversational, personalized, and persuasive. 
        Focus on style, color, price range, and how each product meets the user's needs."""
        
        user_prompt = f"""
        User Query: {user_query}
        Additional Preferences: {user_preferences}
        
        Recommended Products:
        {products_text}
        
        Please provide a conversational explanation of why these products match the user's uploaded image and preferences.
        Format your response as a helpful shopping assistant would, highlighting the key matching features.
        """
        
        request_body = {
            "messages": [
                {
                    "role": "system",
                    "content": [{"text": system_prompt}]
                },
                {
                    "role": "user", 
                    "content": [{"text": user_prompt}]
                }
            ],
            "inferenceConfig": {
                "maxTokens": 500,
                "temperature": 0.7,
                "topP": 0.9
            }
        }
        
        try:
            response = self.client.invoke_model(
                modelId="amazon.nova-lite-v1:0",
                body=json.dumps(request_body),
                contentType="application/json",
                accept="application/json"
            )
            
            response_body = json.loads(response['body'].read())
            return response_body['output']['message']['content'][0]['text']
            
        except Exception as e:
            print(f"Error generating explanation: {str(e)}")
            raise e

    def filter_products_by_preferences(
        self, 
        products: List[Dict[str, Any]], 
        preferences: str
    ) -> List[Dict[str, Any]]:
        """
        Use Nova 2 Lite to filter products based on user preferences
        """
        products_text = "\n".join([
            f"ID: {product['product_id']}, Title: {product['title']}, Price: ${product['price']}, Color: {product['color']}, Style: {product['style']}"
            for product in products
        ])
        
        system_prompt = """You are a product filtering assistant. Based on the user's preferences, 
        return only the product IDs that match the criteria. Focus on color, price range, and style preferences.
        Return the response as a JSON list of product IDs."""
        
        user_prompt = f"""
        User Preferences: {preferences}
        
        Available Products:
        {products_text}
        
        Return only the product IDs that match the user's preferences as a JSON list.
        Example: ["product_1", "product_3", "product_5"]
        """
        
        request_body = {
            "messages": [
                {
                    "role": "system",
                    "content": [{"text": system_prompt}]
                },
                {
                    "role": "user",
                    "content": [{"text": user_prompt}]
                }
            ],
            "inferenceConfig": {
                "maxTokens": 200,
                "temperature": 0.1,
                "topP": 0.9
            }
        }
        
        try:
            response = self.client.invoke_model(
                modelId="amazon.nova-lite-v1:0",
                body=json.dumps(request_body),
                contentType="application/json",
                accept="application/json"
            )
            
            response_body = json.loads(response['body'].read())
            result_text = response_body['output']['message']['content'][0]['text']
            
            # Parse the JSON list of product IDs
            matching_ids = json.loads(result_text)
            
            # Filter products based on matching IDs
            filtered_products = [
                product for product in products 
                if product['product_id'] in matching_ids
            ]
            
            return filtered_products
            
        except Exception as e:
            print(f"Error filtering products: {str(e)}")
            # Return original products if filtering fails
            return products
