#!/usr/bin/env python3
"""
Debug script to understand OCR text format and fix parsing
"""

import sys
import os
import json

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

from utils.parsing_utils import _parse_raw_text_to_structured_json

# Test OCR text that produces the malformed structure
test_ocr_text = """Farm 3 Soil Test Data
Sample ID pH N (%) Org. C (%) Total P (mg/kg) Avail P (mg/kg) Exch. K (meq%) Exch. Ca (meq%) Exch. Mg (meq%) CEC (meq%)
S001 4.74 0.08 0.55 30 2 0.06 0.35 0.17 2.0
S002 5.01 0.08 0.54 34 2 0.08 0.21 0.16 3.33
S003 4.66 0.08 0.59 37 1 0.06 0.17 0.14 1.81
S004 4.59 0.07 0.47 34 2 0.06 0.2 0.15 2.85
S005 4.87 0.09 0.58 26 1 0.07 0.21 0.14 1.41
S006 5.1 0.07 0.6 30 1 0.05 0.27 0.16 4.46
S007 4.72 0.08 0.59 40 2 0.08 0.22 0.15 2.28
S008 4.58 0.09 0.62 39 1 0.07 0.18 0.12 2.46
S009 4.58 0.08 0.51 38 2 0.07 0.31 0.12 3.9
S010 4.94 0.08 0.45 21 1 0.08 0.17 0.13 3.72
S011 4.72 0.08 0.47 29 1 0.08 0.21 0.12 2.69
S012 5.26 0.07 0.58 27 2 0.06 0.25 0.1 3.0"""

def debug_parsing():
    print("🔍 DEBUGGING OCR TEXT PARSING")
    print("=" * 60)

    print("\n📄 RAW OCR TEXT:")
    print("-" * 40)
    print(test_ocr_text)
    print("-" * 40)

    print("\n🔧 CURRENT PARSING RESULT:")
    print("-" * 40)
    result = _parse_raw_text_to_structured_json(test_ocr_text)
    print(json.dumps(result, indent=2))
    print("-" * 40)

    print("\n📊 ANALYSIS:")
    print("-" * 40)

    # Check the structure
    if 'samples' in result:
        print(f"✅ Found {len(result['samples'])} samples")
        if result['samples']:
            print(f"📋 First sample structure: {json.dumps(result['samples'][0], indent=2)}")
            print(f"📋 Last sample structure: {json.dumps(result['samples'][-1], indent=2)}")
        else:
            print("❌ No samples found")
    else:
        print("❌ No 'samples' key found")

    # Expected structure
    expected_structure = {
        "type": "soil",
        "samples": [
            {
                "Sample ID": "S001",
                "pH": 4.74,
                "N (%)": 0.08,
                "Org. C (%)": 0.55,
                "Total P (mg/kg)": 30,
                "Avail P (mg/kg)": 2,
                "Exch. K (meq%)": 0.06,
                "Exch. Ca (meq%)": 0.35,
                "Exch. Mg (meq%)": 0.17,
                "CEC (meq%)": 2.0
            }
        ]
    }

    print("
🎯 EXPECTED STRUCTURE:"    print("-" * 40)
    print(json.dumps(expected_structure, indent=2))

    print("\n🔧 ISSUES IDENTIFIED:")
    print("-" * 40)
    if 'samples' in result and result['samples']:
        sample_keys = list(result['samples'][0].keys())
        expected_keys = list(expected_structure['samples'][0].keys())
        print(f"Current sample keys: {sample_keys}")
        print(f"Expected sample keys: {expected_keys}")
        print(f"Match: {sample_keys == expected_keys}")

if __name__ == "__main__":
    debug_parsing()
