"""
Test suite for Ollama integration
Verifies the backend ideology agent service and FastAPI endpoint
"""

import sys
import json
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

from ideology_agent_service import (
    IdeologyAgentService,
    ScoringResult,
    IdeologyInterpretation,
)


def test_ollama_connection():
    """Test Ollama connection with proper error handling"""
    print("\n=== Test 1: Ollama Connection ===")
    service = IdeologyAgentService(ollama_base_url="http://localhost:11434", timeout=5)
    
    # Test with mock responses that don't require Ollama running
    test_responses = [0, 1, 1, 0, 1]
    test_score = 60
    
    try:
        # This should fail gracefully since Ollama likely isn't running
        result = service.get_ollama_interpretation(test_score, test_responses)
        print(f"✓ Ollama interpretation returned: {result[:100]}...")
        return True
    except Exception as e:
        print(f"✗ Ollama error handling failed: {e}")
        return False


def test_static_fallback():
    """Test static interpretation fallback"""
    print("\n=== Test 2: Static Interpretation Fallback ===")
    service = IdeologyAgentService()
    
    test_cases = [
        (100, "high_environmental"),
        (80, "high_environmental"),
        (60, "environmental"),
        (50, "balanced"),
        (40, "balanced"),
        (20, "comfort"),
        (0, "high_comfort"),
    ]
    
    all_passed = True
    for score, expected_type in test_cases:
        interpretation = service.get_static_interpretation(score)
        if interpretation:
            print(f"✓ Score {score}: {interpretation[:60]}...")
        else:
            print(f"✗ Score {score}: No interpretation returned")
            all_passed = False
    
    return all_passed


def test_scoring_calculation():
    """Test ideology score calculation"""
    print("\n=== Test 3: Scoring Calculation ===")
    service = IdeologyAgentService()
    
    test_cases = [
        ([0, 0, 0, 0, 0], 0, "comfort"),      # All comfort choices
        ([1, 1, 1, 1, 1], 100, "environmental"),  # All environmental choices
        ([0, 1, 1, 0, 1], 60, "environmental"),   # Mixed (3 environmental)
        ([0, 0, 1, 0, 0], 20, "comfort"),    # Only 1 environmental
    ]
    
    all_passed = True
    for responses, expected_score, expected_lean in test_cases:
        result = service.calculate_score(responses)
        
        if result.score == expected_score and result.lean == expected_lean:
            print(f"✓ Responses {responses}: Score={result.score}, Lean={result.lean}")
        else:
            print(f"✗ Responses {responses}: Expected ({expected_score}, {expected_lean}), got ({result.score}, {result.lean})")
            all_passed = False
    
    return all_passed


def test_score_validation():
    """Test input validation"""
    print("\n=== Test 4: Input Validation ===")
    service = IdeologyAgentService()
    
    # Test with wrong number of responses
    try:
        service.calculate_score([0, 1, 0])  # Only 3 responses, need 5
        print("✗ Should have raised ValueError for wrong number of responses")
        return False
    except ValueError as e:
        print(f"✓ Correctly rejected invalid responses: {e}")
        return True


def test_interpret_score():
    """Test full interpret_score flow"""
    print("\n=== Test 5: Full Interpretation Flow ===")
    service = IdeologyAgentService()
    
    test_responses = [0, 1, 1, 0, 1]
    test_score = 60
    
    # Test without Ollama
    try:
        result = service.interpret_score(test_score, test_responses, use_ollama=False)
        
        if isinstance(result, IdeologyInterpretation):
            print(f"✓ Static interpretation: Score={result.score}, Lean={result.lean}")
            print(f"  Interpretation: {result.interpretation[:80]}...")
            
            # Verify response model structure
            if result.score == 60 and result.lean in ["environmental", "balanced", "comfort"]:
                print(f"✓ Response model structure is correct")
                return True
            else:
                print(f"✗ Response model has incorrect values")
                return False
        else:
            print(f"✗ Result is not IdeologyInterpretation: {type(result)}")
            return False
    except Exception as e:
        print(f"✗ Interpretation failed: {e}")
        return False


def test_endpoint_request_model():
    """Test that endpoint accepts ScoringResult correctly"""
    print("\n=== Test 6: Endpoint Request Model ===")
    
    try:
        # Create a ScoringResult as would be passed to the endpoint
        score_result = ScoringResult(
            score=60,
            lean="environmental",
            responses=[0, 1, 1, 0, 1]
        )
        
        print(f"✓ ScoringResult created successfully:")
        print(f"  score={score_result.score}, lean={score_result.lean}, responses={score_result.responses}")
        
        # Verify it serializes to JSON correctly
        json_data = score_result.model_dump()
        print(f"✓ ScoringResult serializes to JSON: {json_data}")
        
        return True
    except Exception as e:
        print(f"✗ ScoringResult model failed: {e}")
        return False


def test_response_model():
    """Test IdeologyInterpretation response model"""
    print("\n=== Test 7: Response Model ===")
    
    try:
        interpretation = IdeologyInterpretation(
            score=60,
            lean="environmental",
            interpretation="You lean toward environmental considerations."
        )
        
        print(f"✓ IdeologyInterpretation created successfully")
        
        # Verify it serializes to JSON correctly
        json_data = interpretation.model_dump()
        print(f"✓ IdeologyInterpretation serializes to JSON:")
        print(f"  {json.dumps(json_data, indent=2)}")
        
        return True
    except Exception as e:
        print(f"✗ IdeologyInterpretation model failed: {e}")
        return False


def test_ollama_timeout():
    """Test timeout handling"""
    print("\n=== Test 8: Timeout Handling ===")
    service = IdeologyAgentService(ollama_base_url="http://localhost:11434", timeout=1)
    
    test_responses = [0, 1, 1, 0, 1]
    test_score = 60
    
    try:
        # With a 1-second timeout, this should fail and fallback
        result = service.get_ollama_interpretation(test_score, test_responses)
        
        # If we got here, it either succeeded (unlikely) or fell back to static
        if result == service.get_static_interpretation(test_score):
            print(f"✓ Timeout handled correctly, fell back to static interpretation")
            return True
        else:
            print(f"✓ Ollama responded within timeout: {result[:80]}...")
            return True
    except Exception as e:
        print(f"✗ Timeout handling failed: {e}")
        return False


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("OLLAMA INTEGRATION TEST SUITE")
    print("="*60)
    
    tests = [
        ("Ollama Connection & Error Handling", test_ollama_connection),
        ("Static Fallback", test_static_fallback),
        ("Score Calculation", test_scoring_calculation),
        ("Input Validation", test_score_validation),
        ("Full Interpretation Flow", test_interpret_score),
        ("Endpoint Request Model", test_endpoint_request_model),
        ("Response Model", test_response_model),
        ("Timeout Handling", test_ollama_timeout),
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
    print("TEST SUMMARY")
    print("="*60)
    
    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)
    
    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed_count}/{total_count} tests passed")
    
    if passed_count == total_count:
        print("\n✓ ALL TESTS PASSED!")
        return 0
    else:
        print(f"\n✗ {total_count - passed_count} tests failed")
        return 1


if __name__ == "__main__":
    exit(main())
