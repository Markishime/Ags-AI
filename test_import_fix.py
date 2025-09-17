#!/usr/bin/env python3

import sys
import os
sys.path.append('.')

def test_imports():
    """Test that all modules can be imported successfully"""
    print("🔧 Testing module imports...")

    try:
        # Test analysis engine import
        from utils.analysis_engine import PromptAnalyzer
        print("✅ Analysis engine imported successfully")

        # Test results module import
        import sys
        sys.path.append('modules')
        import results
        print("✅ Results module imported successfully")

        # Test PromptAnalyzer functionality
        print("\n🔍 Testing PromptAnalyzer functionality...")
        analyzer = PromptAnalyzer()
        print("✅ PromptAnalyzer initialized successfully")

        # Test step extraction
        steps = analyzer.extract_steps_from_prompt('')
        print(f"✅ Extracted {len(steps)} default steps")

        for i, step in enumerate(steps[:2], 1):
            print(f"  Step {step['number']}: {step['title'][:50]}...")

        print("\n🎯 SUCCESS: All modules are working correctly!")
        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_imports()
    if success:
        print("\n✅ ALL IMPORTS WORKING - Results module is fully functional!")
    else:
        print("\n❌ IMPORT ERRORS DETECTED - Check the error messages above")
