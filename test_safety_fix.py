#!/usr/bin/env python3

import sys
import os
sys.path.append('.')

from utils.analysis_engine import PromptAnalyzer
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_safety_fix():
    """Test if the safety filter fixes work with simplified prompts"""

    # Test step
    step = {
        'number': 1,
        'title': 'Data Overview',
        'description': 'Step 1: Provide an overview of all soil and leaf analysis data. Calculate summary statistics for each parameter. Create tables showing sample data. Identify any data patterns.'
    }

    # Test data - simplified
    soil_params = {
        'all_samples': [
            {'sample_no': 'S001', 'pH': 5.5, 'nitrogen': 0.08},
            {'sample_no': 'S002', 'pH': 6.0, 'nitrogen': 0.09}
        ],
        'parameter_statistics': {
            'pH': {'average': 5.75, 'min': 5.5, 'max': 6.0, 'count': 2},
            'nitrogen': {'average': 0.085, 'min': 0.08, 'max': 0.09, 'count': 2}
        }
    }

    leaf_params = {
        'all_samples': [
            {'sample_no': 'L001', 'nitrogen': 2.1, 'phosphorus': 0.12},
            {'sample_no': 'L002', 'nitrogen': 2.3, 'phosphorus': 0.13}
        ],
        'parameter_statistics': {
            'nitrogen': {'average': 2.2, 'min': 2.1, 'max': 2.3, 'count': 2},
            'phosphorus': {'average': 0.125, 'min': 0.12, 'max': 0.13, 'count': 2}
        }
    }

    land_yield_data = {'current_yield': 20.5}

    try:
        print("🔧 Testing PromptAnalyzer with simplified prompts...")
        analyzer = PromptAnalyzer()
        print("✅ PromptAnalyzer initialized successfully")

        print("\n🔍 Testing step analysis generation with simplified prompt...")
        result = analyzer.generate_step_analysis(
            step, soil_params, leaf_params, land_yield_data
        )

        if result and 'summary' in result:
            print("✅ Step analysis generated successfully!")
            print(f"Summary: {result.get('summary', '')[:100]}...")

            # Check if it's a safety filter fallback
            summary = result.get('summary', '').lower()
            if "safety" in summary or "blocked" in summary or "restriction" in summary:
                print("⚠️  WARNING: Still getting safety filter response")
                return False
            else:
                print("🎉 SUCCESS: Got normal analysis response (no safety filters)!")

                # Check for required fields
                required_fields = ['summary', 'detailed_analysis', 'key_findings', 'specific_recommendations']
                missing_fields = [field for field in required_fields if field not in result]
                if missing_fields:
                    print(f"⚠️  Missing fields: {missing_fields}")
                else:
                    print("✅ All required fields present")

                return True

        else:
            print("❌ Step analysis failed or returned unexpected format")
            print(f"Result keys: {list(result.keys()) if result else 'None'}")
            return False

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_safety_fix()
    if success:
        print("\n🎯 SAFETY FILTER FIX VERIFICATION: PASSED!")
        print("The simplified prompts successfully avoid safety filter triggers.")
    else:
        print("\n❌ SAFETY FILTER FIX VERIFICATION: FAILED")
        print("Safety filters are still being triggered. Further simplification may be needed.")
