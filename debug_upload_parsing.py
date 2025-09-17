#!/usr/bin/env python3
"""
Debug script to understand what raw_text is being passed to the parsing function
"""

import sys
import os
import json

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

from utils.parsing_utils import _parse_raw_text_to_structured_json

def debug_raw_text_parsing():
    """Debug what raw_text looks like and how it's being parsed"""

    print("🔍 DEBUGGING RAW TEXT PARSING IN UPLOAD MODULE")
    print("=" * 60)

    # Test with the expected OCR text format
    expected_raw_text = """Farm 3 Soil Test Data
Sample ID pH N (%) Org. C (%) Total P (mg/kg) Avail P (mg/kg) Exch. K (meq%) Exch. Ca (meq%) Exch. Mg (meq%) CEC (meq%)
S001 4.74 0.08 0.55 30 2 0.06 0.35 0.17 2.0
S002 5.01 0.08 0.54 34 2 0.08 0.21 0.16 3.33
S003 4.66 0.08 0.59 37 1 0.06 0.17 0.14 1.81"""

    print("\n📄 EXPECTED RAW TEXT FORMAT:")
    print("-" * 40)
    print(repr(expected_raw_text))
    print("-" * 40)

    result = _parse_raw_text_to_structured_json(expected_raw_text)
    print("\n✅ PARSING RESULT:")
    print(json.dumps(result, indent=2))

    # Now let's see what happens if we get malformed input
    malformed_text = "Farm 3 Soil Test Data\nSample ID pH N (%) Org. C (%) Total P (mg/kg) Avail P (mg/kg) Exch. K (meq%) Exch. Ca (meq%) Exch. Mg (meq%) CEC (meq%)\nS001 4.74 0.08 0.55 30 2 0.06 0.35 0.17 2.0"

    print("\n📄 MALFORMED TEXT FORMAT:")
    print("-" * 40)
    print(repr(malformed_text))
    print("-" * 40)

    result2 = _parse_raw_text_to_structured_json(malformed_text)
    print("\n❌ MALFORMED PARSING RESULT:")
    print(json.dumps(result2, indent=2))

    print("\n🔧 COMPARISON:")
    print("-" * 40)
    print("Expected samples:", len(result.get('samples', [])))
    print("Malformed samples:", len(result2.get('samples', [])))

if __name__ == "__main__":
    debug_raw_text_parsing()
