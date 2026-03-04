"""
Comprehensive endpoint tester for PoliPulse API
Tests all endpoints and reports which ones work vs fail
"""
import requests
import json
from datetime import datetime

BASE_URL = "http://127.0.0.1:8000"
TIMEOUT = 10  # seconds

def test_endpoint(method, path, description, params=None, json_data=None):
    """Test a single endpoint and return result"""
    url = f"{BASE_URL}{path}"
    try:
        if method == "GET":
            response = requests.get(url, params=params, timeout=TIMEOUT)
        elif method == "POST":
            response = requests.post(url, json=json_data, timeout=TIMEOUT)
        
        status = response.status_code
        
        if status == 200 or status == 201:
            try:
                data = response.json()
                data_preview = str(data)[:200] if data else "Empty response"
                return "✅ PASS", status, data_preview
            except:
                return "✅ PASS", status, "Non-JSON response"
        else:
            error = response.text[:200]
            return "❌ FAIL", status, error
            
    except requests.exceptions.Timeout:
        return "⏱️ TIMEOUT", None, f"Request timed out after {TIMEOUT}s"
    except requests.exceptions.ConnectionError:
        return "🔌 NO CONNECTION", None, "Cannot connect to server"
    except Exception as e:
        return "💥 ERROR", None, str(e)[:200]


def run_all_tests():
    """Run all endpoint tests"""
    print("=" * 80)
    print("POLIPULSE API ENDPOINT TESTING")
    print(f"Testing: {BASE_URL}")
    print(f"Time: {datetime.now()}")
    print("=" * 80)
    print()
    
    tests = [
        # Elections endpoints
        ("GET", "/elections/states", "Get all states"),
        ("GET", "/elections/years", "Get all election years"),
        ("GET", "/elections/stats", "Get election statistics"),
        
        # Polls endpoints
        ("GET", "/polls", "Get all polls"),
        ("GET", "/polls/active", "Get active polls"),
        
        # Parties endpoints
        ("GET", "/parties", "Get all parties"),
        
        # Social Media endpoints
        ("GET", "/social/posts", "Get social media posts", {"limit": 10}),
        
        # Predictions endpoints
        ("GET", "/predictions", "Get all predictions"),
        ("GET", "/predictions/pm-race", "Get PM race predictions"),
        ("GET", "/predictions/seats", "Get seats predictions"),
        
        # News endpoints
        ("GET", "/news", "Get all news articles"),
        ("GET", "/news?category=india_politics", "Get India politics news", {"category": "india_politics"}),
        
        # Health check
        ("GET", "/docs", "API Documentation (Swagger UI)"),
    ]
    
    results = {"pass": 0, "fail": 0, "timeout": 0, "error": 0, "no_connection": 0}
    
    for method, path, description, *args in tests:
        params = args[0] if args else None
        json_data = args[1] if len(args) > 1 else None
        
        print(f"Testing: {method} {path}")
        print(f"  Description: {description}")
        
        result, status, message = test_endpoint(method, path, description, params, json_data)
        
        print(f"  Result: {result}")
        if status:
            print(f"  Status: {status}")
        print(f"  Response: {message}")
        print()
        
        # Track results
        if "PASS" in result:
            results["pass"] += 1
        elif "FAIL" in result:
            results["fail"] += 1
        elif "TIMEOUT" in result:
            results["timeout"] += 1
        elif "NO CONNECTION" in result:
            results["no_connection"] += 1
        else:
            results["error"] += 1
    
    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    total = len(tests)
    print(f"Total Tests: {total}")
    print(f"✅ Passed: {results['pass']}")
    print(f"❌ Failed: {results['fail']}")
    print(f"⏱️ Timeouts: {results['timeout']}")
    print(f"🔌 No Connection: {results['no_connection']}")
    print(f"💥 Errors: {results['error']}")
    print()
    
    if results['no_connection'] > 0:
        print("⚠️  WARNING: Cannot connect to server. Is uvicorn running on port 8000?")
    elif results['timeout'] > 0:
        print("⚠️  WARNING: Some requests timed out. Database queries may be too slow.")
    elif results['fail'] > 0:
        print("⚠️  Some endpoints are failing. Check the errors above.")
    elif results['pass'] == total:
        print("🎉 All endpoints working perfectly!")
    
    print("=" * 80)


if __name__ == "__main__":
    try:
        run_all_tests()
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        print(f"\n\nFatal error: {e}")
