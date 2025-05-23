#!/usr/bin/env python3
"""
Test script for checking the health endpoint and rate limiting functionality
"""
import time
import requests
import sys
from concurrent.futures import ThreadPoolExecutor

BASE_URL = "http://localhost:5001"  # Default port
HEALTH_ENDPOINT = f"{BASE_URL}/api/v1/tickets/health"
AVAILABLE_ENDPOINT = f"{BASE_URL}/api/v1/tickets/available"

def test_health_check():
    """Test the health check endpoint"""
    print("Testing health check endpoint...")
    try:
        response = requests.get(HEALTH_ENDPOINT)
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "healthy" and data.get("database") == "connected":
                print("✅ Health check endpoint working correctly")
                return True
            else:
                print("❌ Health check endpoint returned unexpected data:", data)
                return False
        else:
            print(f"❌ Health check endpoint returned status code: {response.status_code}")
            return False
    except requests.RequestException as e:
        print(f"❌ Error connecting to health check endpoint: {str(e)}")
        return False

def test_rate_limiting():
    """Test the rate limiting functionality"""
    print("\nTesting rate limiting...")
    
    # Function to make a request and return the status code
    def make_request():
        try:
            response = requests.get(AVAILABLE_ENDPOINT)
            return response.status_code
        except requests.RequestException:
            return 0
    
    # Make requests in parallel to trigger rate limiting
    status_codes = []
    with ThreadPoolExecutor(max_workers=20) as executor:
        for _ in range(110):  # Make enough requests to trigger the rate limit
            status_codes.append(executor.submit(make_request))
            time.sleep(0.1)  # Small delay to not overwhelm the system
    
    # Get the results
    status_codes = [future.result() for future in status_codes]
    
    # Check if any requests were rate limited (429 Too Many Requests)
    if 429 in status_codes:
        print(f"✅ Rate limiting is working: {status_codes.count(429)} requests were rate-limited")
        return True
    else:
        print("❌ Rate limiting test failed: No requests were rate-limited")
        return False

def test_production_features():
    """Test production-ready features"""
    health_result = test_health_check()
    rate_limit_result = test_rate_limiting()
    
    if health_result and rate_limit_result:
        print("\n✅ All production features are working correctly")
        return 0
    else:
        print("\n❌ Some production features are not working correctly")
        return 1

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        BASE_URL = f"http://localhost:{sys.argv[1]}"
        HEALTH_ENDPOINT = f"{BASE_URL}/api/v1/tickets/health"
        AVAILABLE_ENDPOINT = f"{BASE_URL}/api/v1/tickets/available"
    
    print(f"Testing production features on {BASE_URL}")
    sys.exit(test_production_features())
