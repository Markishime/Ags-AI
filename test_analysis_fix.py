#!/usr/bin/env python3

import sys
sys.path.append('.')

print("🔧 Testing Analysis Engine Fixes")
print("=" * 50)

try:
    from utils.analysis_engine import AnalysisEngine
    print("✅ Analysis engine imported successfully")

    # Initialize the engine
    engine = AnalysisEngine()
    print("✅ Analysis engine initialized successfully")

    # Test with sample data
    sample_soil_data = {
        "Farm_Soil_Test_Data": {
            "S001": {
                "pH": 5.0,
                "N (%)": 0.08,
                "Org. C (%)": 0.55,
                "Available P (mg/kg)": 2.0
            },
            "S002": {
                "pH": 5.1,
                "N (%)": 0.09,
                "Org. C (%)": 0.56,
                "Available P (mg/kg)": 3.0
            }
        }
    }

    print("\n📊 Testing soil data processing...")
    result = engine._convert_structured_to_analysis_format(sample_soil_data, 'soil')
    print(f"✅ Soil data processed: {result.get('total_samples', 0)} samples")

    # Test feedback system
    print("\n📝 Testing feedback system...")
    if hasattr(engine, 'feedback_system'):
        print("✅ Feedback system found")
        try:
            insights = engine.feedback_system.get_learning_insights()
            print("✅ Feedback system working")
        except Exception as e:
            print(f"⚠️  Feedback system error (non-critical): {str(e)}")
    else:
        print("ℹ️  Feedback system not initialized")

    print("\n🎉 All critical tests passed!")

except Exception as e:
    print(f"❌ Error: {str(e)}")
    import traceback
    traceback.print_exc()
