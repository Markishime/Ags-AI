#!/usr/bin/env python3
"""
Test script for the enhanced parsing function
"""

import sys
import os
import json
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

from utils.parsing_utils import _parse_raw_text_to_structured_json

def test_parsing_scenarios():
    """Test various text formats that might come from OCR"""

    print("🧪 TESTING ENHANCED PARSING FUNCTION")
    print("=" * 60)

    # Test 1: Standard format (should work)
    print("\n📋 Test 1: Standard Format")
    print("-" * 30)
    standard_text = """Farm 3 Soil Test Data
Sample ID pH N (%) Org. C (%) Total P (mg/kg) Avail P (mg/kg) Exch. K (meq%) Exch. Ca (meq%) Exch. Mg (meq%) CEC (meq%)
S001 4.74 0.08 0.55 30 2 0.06 0.35 0.17 2.0
S002 5.01 0.08 0.54 34 2 0.08 0.21 0.16 3.33"""

    result1 = _parse_raw_text_to_structured_json(standard_text)
    if 'Farm_3_Soil_Test_Data' in result1:
        print(f"Result: soil with {len(result1['Farm_3_Soil_Test_Data'])} samples")
    elif 'Farm_3_Leaf_Test_Data' in result1:
        print(f"Result: leaf with {len(result1['Farm_3_Leaf_Test_Data'])} samples")
    else:
        print(f"Result: unknown with {len(result1.get('samples', []))} samples")

    # Test 2: Just data rows (no title)
    print("\n📋 Test 2: No Title")
    print("-" * 30)
    no_title_text = """Sample ID pH N (%) Org. C (%) Total P (mg/kg) Avail P (mg/kg) Exch. K (meq%) Exch. Ca (meq%) Exch. Mg (meq%) CEC (meq%)
S001 4.74 0.08 0.55 30 2 0.06 0.35 0.17 2.0
S002 5.01 0.08 0.54 34 2 0.08 0.21 0.16 3.33"""

    result2 = _parse_raw_text_to_structured_json(no_title_text)
    if 'Farm_3_Soil_Test_Data' in result2:
        print(f"Result: soil with {len(result2['Farm_3_Soil_Test_Data'])} samples")
    elif 'Farm_3_Leaf_Test_Data' in result2:
        print(f"Result: leaf with {len(result2['Farm_3_Leaf_Test_Data'])} samples")
    else:
        print(f"Result: unknown with {len(result2.get('samples', []))} samples")

    # Test 3: Just data (no headers)
    print("\n📋 Test 3: No Headers")
    print("-" * 30)
    no_headers_text = """S001 4.74 0.08 0.55 30 2 0.06 0.35 0.17 2.0
S002 5.01 0.08 0.54 34 2 0.08 0.21 0.16 3.33"""

    result3 = _parse_raw_text_to_structured_json(no_headers_text)
    if 'Farm_3_Soil_Test_Data' in result3:
        print(f"Result: soil with {len(result3['Farm_3_Soil_Test_Data'])} samples")
    elif 'Farm_3_Leaf_Test_Data' in result3:
        print(f"Result: leaf with {len(result3['Farm_3_Leaf_Test_Data'])} samples")
    else:
        print(f"Result: unknown with {len(result3.get('samples', []))} samples")

    # Test 4: Leaf data
    print("\n📋 Test 4: Leaf Data")
    print("-" * 30)
    leaf_text = """Farm 3 Leaf Test Data
Sample ID N (%) P (%) K (%) Mg (%) Ca (%) B (mg/kg) Cu (mg/kg) Zn (mg/kg) Fe (mg/kg) Mn (mg/kg)
L001 2.1 0.15 1.8 0.25 1.2 25 8 35 120 45
L002 2.3 0.18 2.1 0.28 1.4 28 9 38 135 52"""

    result4 = _parse_raw_text_to_structured_json(leaf_text)
    if 'Farm_3_Soil_Test_Data' in result4:
        print(f"Result: soil with {len(result4['Farm_3_Soil_Test_Data'])} samples")
    elif 'Farm_3_Leaf_Test_Data' in result4:
        print(f"Result: leaf with {len(result4['Farm_3_Leaf_Test_Data'])} samples")
    else:
        print(f"Result: unknown with {len(result4.get('samples', []))} samples")

    # Test 5: Malformed data
    print("\n📋 Test 5: Malformed Data")
    print("-" * 30)
    malformed_text = """Some random text
that doesn't contain
any analysis data"""

    result5 = _parse_raw_text_to_structured_json(malformed_text)
    if 'Farm_3_Soil_Test_Data' in result5:
        print(f"Result: soil with {len(result5['Farm_3_Soil_Test_Data'])} samples")
    elif 'Farm_3_Leaf_Test_Data' in result5:
        print(f"Result: leaf with {len(result5['Farm_3_Leaf_Test_Data'])} samples")
    else:
        print(f"Result: unknown with {len(result5.get('samples', []))} samples")

    print("\n✅ All tests completed!")

if __name__ == "__main__":
    test_parsing_scenarios()
