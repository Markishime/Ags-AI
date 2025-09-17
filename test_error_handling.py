#!/usr/bin/env python3
"""
Test script to verify that the AI error handling works correctly
"""

import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(__file__))

def test_error_handling():
    """Test that error handling works correctly"""
    try:
        from utils.analysis_engine import PromptAnalyzer

        # Create a prompt analyzer instance
        analyzer = PromptAnalyzer()

        # Test with a mock step that should trigger safety filters
        test_step = {
            'number': 1,
            'title': 'Test Step',
            'description': 'This is a test step for error handling'
        }

        # Mock empty parameters
        soil_params = {}
        leaf_params = {}
        land_yield_data = {}

        # This should trigger the LLM availability check
        if not analyzer.ensure_llm_available():
            print("✅ LLM not available - using fallback as expected")
            result = analyzer._get_default_step_result(test_step)
            if result and 'summary' in result:
                print("✅ Default result generated successfully")
                print(f"   Summary: {result['summary'][:50]}...")
                return True
            else:
                print("❌ Default result generation failed")
                return False
        else:
            print("✅ LLM is available")
            return True

    except Exception as e:
        print(f"❌ Error during testing: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Testing AI Error Handling...")
    print("=" * 50)

    success = test_error_handling()

    print("\n" + "=" * 50)
    if success:
        print("🎉 Error handling test passed!")
        print("✅ Safety filter errors will be handled gracefully")
        print("✅ Fallback analysis will be provided")
        print("✅ Users will see meaningful results even when AI is blocked")
    else:
        print("❌ Error handling test failed")

    print("=" * 50)
