"""
Quick test script to verify all API endpoints are working
"""
import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def test_endpoint(url, method="GET", data=None, expected_status=200):
    """Test a single endpoint"""
    try:
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            response = requests.post(url, json=data)
        
        status_ok = "✅" if response.status_code == expected_status else "❌"
        print(f"{status_ok} {method} {url}")
        print(f"   Status: {response.status_code}")
        
        if response.status_code == expected_status:
            if response.content:
                result = response.json()
                if isinstance(result, list):
                    print(f"   Response: List with {len(result)} items")
                elif isinstance(result, dict):
                    print(f"   Response keys: {list(result.keys())[:5]}")
            return True
        else:
            print(f"   Error: {response.text[:200]}")
            return False
    except Exception as e:
        print(f"❌ {method} {url}")
        print(f"   Exception: {e}")
        return False

def main():
    print("=" * 60)
    print("PoliPulse API Endpoint Tests")
    print("=" * 60)
    
    tests_passed = 0
    tests_total = 0
    
    # Test Core Endpoints
    print("\n🔹 Core Endpoints:")
    tests_total += 1
    if test_endpoint(f"{BASE_URL}/"): tests_passed += 1
    
    tests_total += 1
    if test_endpoint(f"{BASE_URL}/health"): tests_passed += 1
    
    # Test Elections (Phase 1)
    print("\n🔹 Elections Endpoints:")
    tests_total += 1
    if test_endpoint(f"{BASE_URL}/elections/states"): tests_passed += 1
    
    tests_total += 1
    if test_endpoint(f"{BASE_URL}/elections/years"): tests_passed += 1
    
    # Test Polls
    print("\n🔹 Polls Endpoints:")
    tests_total += 1
    if test_endpoint(f"{BASE_URL}/polls"): tests_passed += 1
    
    # Test Parties
    print("\n🔹 Parties Endpoints:")
    tests_total += 1
    if test_endpoint(f"{BASE_URL}/parties"): tests_passed += 1
    
    # Test Social Media
    print("\n🔹 Social Media Endpoints:")
    tests_total += 1
    if test_endpoint(f"{BASE_URL}/social/posts?days=7&limit=10"): tests_passed += 1
    
    # Test Predictions
    print("\n🔹 Predictions Endpoints:")
    tests_total += 1
    if test_endpoint(f"{BASE_URL}/predictions/pm-race"): tests_passed += 1
    
    tests_total += 1
    if test_endpoint(f"{BASE_URL}/predictions/seats-projection"): tests_passed += 1
    
    # Test News
    print("\n🔹 News Endpoints:")
    tests_total += 1
    if test_endpoint(f"{BASE_URL}/news/latest/india"): tests_passed += 1
    
    tests_total += 1
    if test_endpoint(f"{BASE_URL}/news/latest/geopolitics"): tests_passed += 1
    
    # Summary
    print("\n" + "=" * 60)
    print(f"Tests Passed: {tests_passed}/{tests_total}")
    print(f"Success Rate: {(tests_passed/tests_total*100):.1f}%")
    print("=" * 60)
    
    if tests_passed == tests_total:
        print("\n✅ ALL TESTS PASSED! API is fully functional.")
    else:
        print(f"\n⚠️ {tests_total - tests_passed} test(s) failed.")

if __name__ == "__main__":
    main()
