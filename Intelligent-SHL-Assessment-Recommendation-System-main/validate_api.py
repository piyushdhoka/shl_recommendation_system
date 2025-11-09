"""
API Validation Script

This script validates that the API endpoints match the specification requirements.
"""

import requests
import json
import sys


def test_health_endpoint(base_url: str = "http://127.0.0.1:8000"):
    """Test the /health endpoint."""
    print("=" * 60)
    print("Testing /health endpoint...")
    print("=" * 60)
    
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health check passed")
            print(f"   Status Code: {response.status_code}")
            print(f"   Response: {data}")
            return True
        else:
            print(f"❌ Health check failed")
            print(f"   Status Code: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"❌ Connection Error: Could not connect to {base_url}")
        print("   Make sure the API server is running:")
        print("   uvicorn main:app --reload")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_recommend_endpoint(base_url: str = "http://127.0.0.1:8000"):
    """Test the /recommend endpoint."""
    print("\n" + "=" * 60)
    print("Testing /recommend endpoint...")
    print("=" * 60)
    
    test_queries = [
        "I am hiring for Java developers who can also collaborate effectively with my business teams.",
        "Looking to hire mid-level professionals who are proficient in Python, SQL and Java Script."
    ]
    
    all_passed = True
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n--- Test Query {i} ---")
        print(f"Query: {query[:60]}...")
        
        try:
            response = requests.post(
                f"{base_url}/recommend",
                json={"query": query},
                timeout=60
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Validate response structure
                checks = {
                    "Has 'query' field": "query" in data,
                    "Has 'recommendations' field": "recommendations" in data,
                    "Recommendations is a list": isinstance(data.get("recommendations"), list),
                    "5-10 recommendations": 5 <= len(data.get("recommendations", [])) <= 10,
                }
                
                # Validate each recommendation
                recommendations = data.get("recommendations", [])
                if recommendations:
                    first_rec = recommendations[0]
                    checks["Has 'assessment_name'"] = "assessment_name" in first_rec
                    checks["Has 'url' field"] = "url" in first_rec
                    checks["URL is not empty"] = bool(first_rec.get("url", "").strip())
                    checks["Name is not empty"] = bool(first_rec.get("assessment_name", "").strip())
                
                # Print results
                all_checks_passed = True
                for check_name, check_result in checks.items():
                    status = "✅" if check_result else "❌"
                    print(f"   {status} {check_name}: {check_result}")
                    if not check_result:
                        all_checks_passed = False
                
                print(f"\n   Total Recommendations: {len(recommendations)}")
                if recommendations:
                    print(f"   Sample Recommendation:")
                    print(f"     Name: {recommendations[0].get('assessment_name', 'N/A')}")
                    print(f"     URL: {recommendations[0].get('url', 'N/A')[:60]}...")
                
                if not all_checks_passed:
                    all_passed = False
                    
            elif response.status_code == 400:
                print(f"❌ Bad Request (400)")
                print(f"   Response: {response.json()}")
                all_passed = False
            else:
                print(f"❌ Error: Status Code {response.status_code}")
                print(f"   Response: {response.text[:200]}")
                all_passed = False
                
        except requests.exceptions.ConnectionError:
            print(f"❌ Connection Error: Could not connect to {base_url}")
            all_passed = False
        except Exception as e:
            print(f"❌ Error: {e}")
            all_passed = False
    
    return all_passed


def main():
    """Run all API validation tests."""
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000"
    
    print("\n" + "=" * 60)
    print("API VALIDATION TEST SUITE")
    print("=" * 60)
    print(f"Testing API at: {base_url}\n")
    
    health_ok = test_health_endpoint(base_url)
    recommend_ok = test_recommend_endpoint(base_url)
    
    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)
    print(f"Health Endpoint: {'✅ PASS' if health_ok else '❌ FAIL'}")
    print(f"Recommend Endpoint: {'✅ PASS' if recommend_ok else '❌ FAIL'}")
    
    if health_ok and recommend_ok:
        print("\n🎉 All API validation tests passed!")
        return 0
    else:
        print("\n⚠️  Some tests failed. Please review the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

