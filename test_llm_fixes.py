#!/usr/bin/env python3

import sys
import os
sys.path.append('.')

from utils.analysis_engine import PromptAnalyzer
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_llm_fixes():
    """Test the LLM fixes for step-by-step analysis and safety filters"""

    # Test step
    step = {
        'number': 1,
        'title': 'Data Overview and Summary Statistics',
        'description': 'Step 1: Provide a comprehensive overview of all soil and leaf analysis data. Calculate and present summary statistics (mean, range, standard deviation) for each parameter across ALL samples. Create detailed tables showing all sample data with their actual values. Identify any data quality issues or anomalies.'
    }

    # Test data
    soil_params = {
        'all_samples': [
            {'sample_no': 'S001', 'pH': 5.5, 'Nitrogen_%': 0.08, 'Organic_Carbon_%': 0.55},
            {'sample_no': 'S002', 'pH': 6.0, 'Nitrogen_%': 0.09, 'Organic_Carbon_%': 0.54}
        ],
        'parameter_statistics': {
            'pH': {'average': 5.75, 'min': 5.5, 'max': 6.0, 'count': 2},
            'Nitrogen_%': {'average': 0.085, 'min': 0.08, 'max': 0.09, 'count': 2}
        }
    }

    leaf_params = {
        'all_samples': [
            {'sample_no': 'L001', 'N_%': 2.1, 'P_%': 0.12, 'K_%': 0.45},
            {'sample_no': 'L002', 'N_%': 2.3, 'P_%': 0.13, 'K_%': 0.47}
        ],
        'parameter_statistics': {
            'N_%': {'average': 2.2, 'min': 2.1, 'max': 2.3, 'count': 2},
            'P_%': {'average': 0.125, 'min': 0.12, 'max': 0.13, 'count': 2}
        }
    }

    land_yield_data = {'current_yield': 20.5, 'area_hectares': 100}

    try:
        print("🔧 Testing PromptAnalyzer initialization...")
        analyzer = PromptAnalyzer()
        print("✅ PromptAnalyzer initialized successfully")

        print("\n🔍 Testing step analysis generation...")
        result = analyzer.generate_step_analysis(
            step, soil_params, leaf_params, land_yield_data
        )

        if result and 'summary' in result:
            print("✅ Step analysis generated successfully!")
            print(f"Summary: {result.get('summary', '')[:150]}...")

            # Check if it's a safety filter fallback
            if "safety" in result.get('summary', '').lower() or "blocked" in result.get('summary', '').lower():
                print("⚠️  WARNING: Got safety filter fallback response")
                return False
            else:
                print("🎉 SUCCESS: Got actual detailed analysis!")

                # Check for required fields
                required_fields = ['summary', 'detailed_analysis', 'key_findings', 'specific_recommendations']
                missing_fields = [field for field in required_fields if field not in result]
                if missing_fields:
                    print(f"⚠️  Missing fields: {missing_fields}")
                else:
                    print("✅ All required fields present")

                # Check for tables if step requires them
                if 'table' in step['description'].lower() and 'tables' in result:
                    if result['tables']:
                        print(f"✅ Tables generated: {len(result['tables'])} table(s)")
                    else:
                        print("⚠️  Step requires tables but none were generated")

                return True

        else:
            print("❌ Step analysis failed or returned unexpected format")
            print(f"Result: {result}")
            return False

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_step_extraction():
    """Test the step extraction functionality"""
    print("\n🔧 Testing step extraction...")

    analyzer = PromptAnalyzer()

    # Test with empty prompt (should use default steps)
    steps = analyzer.extract_steps_from_prompt("")
    print(f"✅ Default steps extracted: {len(steps)} steps")
    for step in steps[:2]:  # Show first 2 steps
        print(f"  Step {step['number']}: {step['title'][:50]}...")

    # Test with custom prompt
    custom_prompt = """
    Step 1: Data Overview - Analyze all samples
    Step 2: Soil Analysis - Compare against standards
    Step 3: Recommendations - Provide fertilizer suggestions
    """

    custom_steps = analyzer.extract_steps_from_prompt(custom_prompt)
    print(f"✅ Custom steps extracted: {len(custom_steps)} steps")
    for step in custom_steps:
        print(f"  Step {step['number']}: {step['title']}")

    return True

if __name__ == "__main__":
    print("=== TESTING LLM FIXES ===")

    # Test step extraction
    step_test = test_step_extraction()

    # Test LLM analysis
    analysis_test = test_llm_fixes()

    if step_test and analysis_test:
        print("\n🎯 ALL TESTS PASSED - LLM fixes working correctly!")
    else:
        print("\n❌ SOME TESTS FAILED - Review the issues above")
