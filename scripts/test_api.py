#!/usr/bin/env python3

import json
import base64
import requests
import sys
from typing import Dict, Any

class APITester:
    def __init__(self, api_base_url: str):
        self.api_base_url = api_base_url.rstrip('/')
        self.session = requests.Session()

    def create_test_image(self) -> str:
        """
        Create a simple test image (1x1 red pixel) and return as base64
        """
        # Simple 1x1 red PNG in base64
        red_pixel_base64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
        return f"data:image/png;base64,{red_pixel_base64}"

    def test_search_endpoint(self) -> Dict[str, Any]:
        """
        Test the search endpoint
        """
        print("Testing /search endpoint...")
        
        test_payload = {
            "image": self.create_test_image(),
            "query": "Show me similar products",
            "preferences": "Show me similar in blue under $100",
            "max_price": 100,
            "size": 5
        }
        
        try:
            response = self.session.post(
                f"{self.api_base_url}/search",
                json=test_payload,
                headers={"Content-Type": "application/json"}
            )
            
            print(f"Status Code: {response.status_code}")
            print(f"Response Headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"Products found: {len(result.get('products', []))}")
                print(f"Explanation: {result.get('explanation', 'No explanation')[:100]}...")
                return {"success": True, "data": result}
            else:
                print(f"Error Response: {response.text}")
                return {"success": False, "error": response.text}
                
        except Exception as e:
            print(f"Exception occurred: {str(e)}")
            return {"success": False, "error": str(e)}

    def test_explain_endpoint(self) -> Dict[str, Any]:
        """
        Test the explain endpoint
        """
        print("\nTesting /explain endpoint...")
        
        test_products = [
            {
                "product_id": "test_001",
                "title": "Test Product 1",
                "description": "A beautiful test product",
                "price": 49.99,
                "category": "test",
                "color": "blue",
                "style": "casual",
                "image_url": "https://example.com/image1.jpg"
            },
            {
                "product_id": "test_002", 
                "title": "Test Product 2",
                "description": "Another amazing test product",
                "price": 79.99,
                "category": "test",
                "color": "red",
                "style": "formal",
                "image_url": "https://example.com/image2.jpg"
            }
        ]
        
        test_payload = {
            "query": "Show me similar products",
            "products": test_products,
            "preferences": "I prefer blue items under $100"
        }
        
        try:
            response = self.session.post(
                f"{self.api_base_url}/explain",
                json=test_payload,
                headers={"Content-Type": "application/json"}
            )
            
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"Explanation generated: {result.get('explanation', 'No explanation')[:100]}...")
                return {"success": True, "data": result}
            else:
                print(f"Error Response: {response.text}")
                return {"success": False, "error": response.text}
                
        except Exception as e:
            print(f"Exception occurred: {str(e)}")
            return {"success": False, "error": str(e)}

    def test_cors(self) -> Dict[str, Any]:
        """
        Test CORS headers
        """
        print("\nTesting CORS headers...")
        
        try:
            # Test OPTIONS request
            response = self.session.options(
                f"{self.api_base_url}/search",
                headers={
                    "Origin": "http://localhost:3000",
                    "Access-Control-Request-Method": "POST",
                    "Access-Control-Request-Headers": "Content-Type"
                }
            )
            
            cors_headers = {
                "Access-Control-Allow-Origin": response.headers.get("Access-Control-Allow-Origin"),
                "Access-Control-Allow-Methods": response.headers.get("Access-Control-Allow-Methods"),
                "Access-Control-Allow-Headers": response.headers.get("Access-Control-Allow-Headers")
            }
            
            print(f"CORS Headers: {cors_headers}")
            
            return {"success": True, "cors_headers": cors_headers}
            
        except Exception as e:
            print(f"Exception occurred: {str(e)}")
            return {"success": False, "error": str(e)}

    def run_all_tests(self) -> Dict[str, Any]:
        """
        Run all API tests
        """
        print("Starting API tests...")
        print(f"API Base URL: {self.api_base_url}")
        print("=" * 50)
        
        results = {
            "search_test": self.test_search_endpoint(),
            "explain_test": self.test_explain_endpoint(),
            "cors_test": self.test_cors()
        }
        
        print("\n" + "=" * 50)
        print("TEST SUMMARY:")
        
        for test_name, result in results.items():
            status = "✅ PASS" if result["success"] else "❌ FAIL"
            print(f"{test_name}: {status}")
            
            if not result["success"]:
                print(f"  Error: {result.get('error', 'Unknown error')}")
        
        return results

def main():
    if len(sys.argv) != 2:
        print("Usage: python test_api.py <api_base_url>")
        print("Example: python test_api.py https://your-api.execute-api.us-east-1.amazonaws.com/dev")
        sys.exit(1)
    
    api_base_url = sys.argv[1]
    tester = APITester(api_base_url)
    results = tester.run_all_tests()
    
    # Exit with error code if any test failed
    failed_tests = [name for name, result in results.items() if not result["success"]]
    if failed_tests:
        print(f"\n❌ {len(failed_tests)} test(s) failed: {', '.join(failed_tests)}")
        sys.exit(1)
    else:
        print("\n✅ All tests passed!")
        sys.exit(0)

if __name__ == "__main__":
    main()
