#!/usr/bin/env python3
import sys
sys.path.append('.')

# Test the SP Lab leaf parsing function directly
def test_leaf_sp_lab():
    # Import here to avoid Firebase initialization issues
    from modules.upload import format_raw_text_as_structured_json

    test_text = '''SP LAB
Sarawak Plantation Services Sdn. Bhd.
TEST REPORT
Serial No.: SPLAB/TR/411/2025
Your Ref.: Analysis Request Form dated 7 May 2025
Date of Issue: 22 May 2025
Page 2 of 2
Analysis Results:
% Dry Matter
mg/kg Dry Matter
Lab No.
Sample No.
N
P
K
Mg
Ca
B
Cu
Zn
P220/25
1
2.13
0.140 0.59
0.26
0.87
16
2
9
P221/25
2
2.04
0.125
0.51
0.17
0.90
25
<1
9
P222/25
3
2.01
0.122
0.54
0.33
0.71
17
1
12'''

    print("Testing SP Lab leaf parsing...")
    print(f"Input text: {repr(test_text[:100])}...")

    try:
        result = format_raw_text_as_structured_json(test_text, 'leaf')
        print("✅ Function executed successfully")
        print(f"Result type: {type(result)}")
        print(f"Result keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")

        if isinstance(result, dict):
            for key, value in result.items():
                print(f"Key: {key}")
                if isinstance(value, dict):
                    print(f"  Value keys: {list(value.keys())[:5]}...")  # Show first 5 keys
                    if value:
                        first_key = list(value.keys())[0]
                        print(f"  First sample: {first_key}")
                        if isinstance(value[first_key], dict):
                            print(f"    Parameters: {list(value[first_key].keys())}")
                            print(f"    Values: {value[first_key]}")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_leaf_sp_lab()
