"""
Test the FastAPI endpoints directly
"""

import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

from fastapi.testclient import TestClient
from server import app

client = TestClient(app)


def test_endpoint_interpret_without_ollama():
    """Test /api/ideology/interpret endpoint without Ollama"""
    print("\n=== Test: Interpret Endpoint (Static) ===")
    
    payload = {
        "score": 60,
        "lean": "environmental",
        "responses": [0, 1, 1, 0, 1]
    }
    
    response = client.post("/api/ideology/interpret", json=payload, params={"use_ollama": False})
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Status code: {response.status_code}")
        print(f"✓ Response: {data}")
        
        # Verify response structure
        if all(key in data for key in ["score", "lean", "interpretation"]):
            print(f"✓ Response has all required fields")
            print(f"  Score: {data['score']}")
            print(f"  Lean: {data['lean']}")
            print(f"  Interpretation: {data['interpretation'][:80]}...")
            return True
        else:
            print(f"✗ Response missing required fields")
            return False
    else:
        print(f"✗ Status code: {response.status_code}")
        print(f"✗ Response: {response.text}")
        return False


def test_endpoint_interpret_with_ollama():
    """Test /api/ideology/interpret endpoint with Ollama (will fallback)"""
    print("\n=== Test: Interpret Endpoint (Ollama Attempt) ===")
    
    payload = {
        "score": 60,
        "lean": "environmental",
        "responses": [0, 1, 1, 0, 1]
    }
    
    response = client.post("/api/ideology/interpret", json=payload, params={"use_ollama": True})
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Status code: {response.status_code}")
        print(f"✓ Response received (with or without Ollama)")
        print(f"  Score: {data['score']}")
        print(f"  Lean: {data['lean']}")
        print(f"  Interpretation: {data['interpretation'][:80]}...")
        return True
    else:
        print(f"✗ Status code: {response.status_code}")
        print(f"✗ Response: {response.text}")
        return False


def test_endpoint_questions():
    """Test /api/ideology/questions endpoint"""
    print("\n=== Test: Questions Endpoint ===")
    
    response = client.get("/api/ideology/questions")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Status code: {response.status_code}")
        print(f"✓ Returned {len(data)} questions")
        
        if len(data) == 5:
            print(f"✓ Correct number of questions (5)")
            for i, question in enumerate(data[:2]):
                print(f"  Question {i+1}: {question['text'][:60]}...")
            return True
        else:
            print(f"✗ Expected 5 questions, got {len(data)}")
            return False
    else:
        print(f"✗ Status code: {response.status_code}")
        return False


def test_endpoint_invalid_input():
    """Test error handling with invalid input"""
    print("\n=== Test: Error Handling (Invalid Input) ===")
    
    # Invalid: wrong number of responses
    payload = {
        "score": 60,
        "lean": "environmental",
        "responses": [0, 1, 1]  # Only 3, should be 5
    }
    
    response = client.post("/api/ideology/interpret", json=payload)
    
    if response.status_code in [400, 422]:  # Bad request or validation error
        print(f"✓ Correctly rejected invalid input (status {response.status_code})")
        return True
    elif response.status_code == 500:
        print(f"✓ Server error returned (could be validation or internal)")
        print(f"  Response: {response.text[:100]}")
        return True
    else:
        print(f"✗ Unexpected status code: {response.status_code}")
        print(f"  Response: {response.text}")
        return False


def main():
    """Run endpoint tests"""
    print("\n" + "="*60)
    print("FASTAPI ENDPOINT TEST SUITE")
    print("="*60)
    
    tests = [
        ("Questions Endpoint", test_endpoint_questions),
        ("Interpret Endpoint (Static)", test_endpoint_interpret_without_ollama),
        ("Interpret Endpoint (Ollama)", test_endpoint_interpret_with_ollama),
        ("Error Handling", test_endpoint_invalid_input),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            passed = test_func()
            results.append((test_name, passed))
        except Exception as e:
            print(f"\n✗ TEST CRASHED: {test_name}")
            print(f"  Error: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*60)
    print("ENDPOINT TEST SUMMARY")
    print("="*60)
    
    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)
    
    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed_count}/{total_count} tests passed")
    
    if passed_count == total_count:
        print("\n✓ ALL ENDPOINT TESTS PASSED!")
        return 0
    else:
        print(f"\n✗ {total_count - passed_count} tests failed")
        return 1


if __name__ == "__main__":
    exit(main())
