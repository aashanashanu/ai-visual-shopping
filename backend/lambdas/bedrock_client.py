import json
import boto3
import base64
import os
from typing import Dict, List, Any
import time
import random

class BedrockClient:
    def __init__(self, region: str = 'us-east-1'):
        self.client = boto3.client('bedrock-runtime', region_name=region)
        self.region = region
        self.max_retries = 3
        self.base_delay = 1.0  # Base delay in seconds

    def _invoke_with_retry(self, model_id: str, body: str) -> Dict[str, Any]:
        """Invoke Bedrock model with retry logic and exponential backoff"""
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                response = self.client.invoke_model(
                    modelId=model_id,
                    body=body,
                    contentType="application/json",
                    accept="application/json"
                )
                return response
                
            except self.client.exceptions.ThrottlingException as e:
                last_exception = e
                if attempt < self.max_retries - 1:
                    # Exponential backoff with jitter for throttling
                    delay = self.base_delay * (2 ** attempt) + random.uniform(0, 1)
                    print(f"Throttling detected, retrying in {delay:.2f} seconds (attempt {attempt + 1}/{self.max_retries})")
                    time.sleep(delay)
                    continue
                else:
                    raise
                    
            except self.client.exceptions.ServiceUnavailableException as e:
                last_exception = e
                if attempt < self.max_retries - 1:
                    # Shorter delay for service unavailable
                    delay = self.base_delay * (2 ** attempt)
                    print(f"Service unavailable, retrying in {delay:.2f} seconds (attempt {attempt + 1}/{self.max_retries})")
                    time.sleep(delay)
                    continue
                else:
                    raise
                    
            except Exception as e:
                # For other exceptions, don't retry
                raise e
        
        # This should not be reached, but just in case
        raise last_exception or Exception("Max retries exceeded")

    def generate_multimodal_embedding(self, image_bytes: bytes) -> List[float]:
        """
        Generate embedding using Amazon Nova Multimodal Embedding model
        """
        # Validate image size (reasonable limit for Lambda)
        if len(image_bytes) > 5 * 1024 * 1024:  # 5MB limit
            raise ValueError("Image too large. Maximum size is 5MB.")
        
        if len(image_bytes) < 100:  # Minimum size check
            raise ValueError("Image data too small. Please provide a valid image.")
        
        # Convert image to base64
        image_base64 = base64.b64encode(image_bytes).decode('utf-8')
        
        # Detect image format from bytes
        import imghdr
        image_format = imghdr.what(None, h=image_bytes)
        if image_format is None:
            # Fallback to jpeg if detection fails
            image_format = 'jpeg'
        
        # Validate supported formats
        supported_formats = ['jpeg', 'jpg', 'png', 'webp']
        if image_format.lower() not in supported_formats:
            raise ValueError(f"Unsupported image format: {image_format}. Supported formats: {', '.join(supported_formats)}")
        
        request_body = {
            "schemaVersion": "nova-multimodal-embed-v1",
            "taskType": "SINGLE_EMBEDDING",
            "singleEmbeddingParams": {
                "embeddingPurpose": "IMAGE_RETRIEVAL",
                "embeddingDimension": 1024,
                "image": {
                    "format": image_format,
                    "source": {
                        "bytes": image_base64
                    }
                }
            }
        }
        
        try:
            response = self._invoke_with_retry(
                model_id="amazon.nova-2-multimodal-embeddings-v1:0",
                body=json.dumps(request_body)
            )
            
            response_body = json.loads(response['body'].read())
            # Handle the new response format
            if 'embeddings' in response_body:
                # New format with embeddings array
                embeddings = response_body['embeddings']
                if embeddings and len(embeddings) > 0:
                    return embeddings[0]['embedding']
            else:
                # Fallback to old format
                return response_body['outputEmbedding']
            
            raise ValueError("No embedding returned from model")
            
        except Exception as e:
            print(f"Error generating embedding: {str(e)}")
            print(f"Error type: {type(e).__name__}")
            if hasattr(e, 'response'):
                print(f"Error response: {e.response}")
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
        # Validate inputs
        if not products or not isinstance(products, list):
            raise ValueError("Products must be provided as a non-empty list")
        
        if len(products) > 20:
            products = products[:20]  # Limit to prevent token limits
        
        # Validate product structure
        for i, product in enumerate(products):
            if not isinstance(product, dict):
                raise ValueError(f"Product at index {i} must be a dictionary")
            if 'name' not in product and 'title' not in product:
                raise ValueError(f"Product at index {i} must have 'name' or 'title' field")
        
        # Format product information for the prompt
        products_text = "\n".join([
            f"Product {i+1}: {product.get('name', product.get('title', 'Unknown Product'))} - ${product.get('price', 0)} - {product.get('description', 'No description')}"
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
        
        # Allow configurable max tokens via environment variable
        try:
            max_tokens = int(os.environ.get("EXPLANATION_MAX_TOKENS", "500"))
        except ValueError:
            max_tokens = 500

        # Cap max tokens to a reasonable upper bound to avoid very large bills
        MAX_ALLOWED_TOKENS = 4096
        if max_tokens > MAX_ALLOWED_TOKENS:
            max_tokens = MAX_ALLOWED_TOKENS

        request_body = {
            "messages": [
                {
                    "role": "user",
                    "content": [{"text": f"{system_prompt}\n\n{user_prompt}"}]
                }
            ],
            "inferenceConfig": {
                "maxTokens": max_tokens,
                "temperature": 0.7,
                "topP": 0.9
            }
        }
        
        try:
            response = self.client.invoke_model(
                modelId="us.amazon.nova-2-lite-v1:0",
                body=json.dumps(request_body),
                contentType="application/json",
                accept="application/json"
            )
            
            response_body = json.loads(response['body'].read())

            # Safely extract all text parts returned by the model and concatenate them
            try:
                content_parts = response_body['output']['message']['content']
                texts = []
                for part in content_parts:
                    if isinstance(part, dict) and 'text' in part:
                        texts.append(part['text'])
                    elif isinstance(part, str):
                        texts.append(part)
                full_text = "\n".join(texts).strip()
                return full_text
            except Exception:
                # Fallback: try the original path or return an empty string
                try:
                    return response_body.get('output', {}).get('message', {}).get('content', [])[0].get('text', '')
                except Exception:
                    return ''
            
        except Exception as e:
            print(f"Error generating explanation: {str(e)}")
            raise e

    def filter_products_by_preferences(
        self, 
        products: List[Dict[str, Any]], 
        preferences: str,
        query: str = ""
    ) -> List[Dict[str, Any]]:
        """
        Use Nova 2 Lite to filter products based on user query and preferences
        """
        # Validate inputs
        if not products or not isinstance(products, list):
            return products  # Return original if invalid
        
        if not preferences and not query:
            return products  # Return original if no query or preferences
        
        if len(products) > 20:
            products = products[:20]  # Limit to prevent token limits
        
        # Validate product structure
        valid_products = []
        for product in products:
            if isinstance(product, dict) and 'product_id' in product:
                valid_products.append(product)
        
        if not valid_products:
            return products  # Return original if no valid products
        
        # Build comprehensive product text with all relevant attributes
        products_text = "\n".join([
            f"ID: {product['product_id']}, "
            f"Title: {product.get('title', product.get('name', 'Unknown'))}, "
            f"Category: {product.get('category', 'N/A')}, "
            f"Price: ${product.get('price', 0)}, "
            f"Color: {product.get('color', 'N/A')}, "
            f"Style: {product.get('style', 'N/A')}, "
            f"Material: {product.get('material', 'N/A')}, "
            f"Brand: {product.get('brand', 'N/A')}, "
            f"Description: {product.get('description', 'N/A')[:100]}"
            for product in valid_products
        ])
        
        system_prompt = """You are a product filtering assistant. Based on the user's search query and preferences, 
        return only the product IDs that best match what they're looking for. Consider color, style, category, price, material, and brand.
        Return the response as a JSON list of product IDs."""
        
        # Build user prompt with both query and preferences
        user_prompt = f"""
User Search Query: {query if query else "Find similar products"}
User Preferences: {preferences if preferences else "None specified"}

Available Products:
{products_text}

Based on the user's search query and preferences, return only the product IDs that best match as a JSON list.
Example: ["product_1", "product_3", "product_5"]
"""
        
        request_body = {
            "messages": [
                {
                    "role": "user",
                    "content": [{"text": f"{system_prompt}\n\n{user_prompt}"}]
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
                modelId="us.amazon.nova-2-lite-v1:0",
                body=json.dumps(request_body),
                contentType="application/json",
                accept="application/json"
            )
            
            response_body = json.loads(response['body'].read())
            result_text = response_body['output']['message']['content'][0]['text']
            
            # Parse the JSON list of product IDs
            try:
                matching_ids = json.loads(result_text)
                if not isinstance(matching_ids, list):
                    raise ValueError("Response is not a list")
            except (json.JSONDecodeError, ValueError):
                print(f"Failed to parse AI response as JSON list: {result_text}")
                return products  # Return original products on parse failure
            
            # Filter products based on matching IDs
            filtered_products = [
                product for product in products 
                if product.get('product_id') in matching_ids
            ]
            
            return filtered_products
            
        except Exception as e:
            print(f"Error filtering products: {str(e)}")
            # Return original products if filtering fails
            return products
