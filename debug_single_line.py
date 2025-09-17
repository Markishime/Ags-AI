#!/usr/bin/env python3
"""
Debug script for single-line OCR parsing
"""

import sys
import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

from utils.parsing_utils import _parse_raw_text_to_structured_json

def test_single_line_parsing():
    """Test single-line OCR parsing"""

    print("🧪 TESTING SINGLE-LINE OCR PARSING")
    print("=" * 60)

    # Test with single-line OCR output
    single_line_text = 'Farm 3 Soil Test Data Sample ID pH N (%) Org. C (%) Total P (mg/kg) Avail P (mg/kg) Exch. K (meq%) Exch. Ca (meq%) Exch. Mg (meq%) CEC (meq%) S001 4.74 0.08 0.55 30 2 0.06 0.35 0.17 2.0 S002 5.01 0.08 0.54 34 2 0.08 0.21 0.16 3.33'

    print(f"Input text length: {len(single_line_text)}")
    print(f"Input text: {single_line_text[:150]}...")
    print()

    try:
        result = _parse_raw_text_to_structured_json(single_line_text)
        print("✅ Parsing completed")
        print(f"Result type: {type(result)}")
        print(f"Result keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")

        if isinstance(result, dict):
            if 'Farm_3_Soil_Test_Data' in result:
                soil_data = result['Farm_3_Soil_Test_Data']
                print(f"✅ Found soil data with {len(soil_data)} samples")
                print(f"Sample IDs: {list(soil_data.keys())}")
            elif 'type' in result:
                print(f"❌ Parsing failed: {result}")
            else:
                print(f"❌ Unexpected result structure: {result}")
        else:
            print(f"❌ Result is not a dict: {result}")

    except Exception as e:
        print(f"❌ Exception during parsing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_single_line_parsing()
