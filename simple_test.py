#!/usr/bin/env python3
import sys
sys.path.append('.')

# Test the SP Lab parsing function directly
def test_sp_lab():
    # Import here to avoid Firebase initialization issues
    from modules.upload import format_raw_text_as_structured_json

    test_text = '''SP LAB
S218/25 S219/25 S220/25 S221/25 S222/25
pH
5.0 4.3 4.0 4.1 4.0
Nitrogen
0.10 0.09 0.09 0.07 0.08
Organic Carbon
0.89 0.80 0.72 0.33 0.58'''

    print("Testing SP Lab parsing...")
    print(f"Input text: {repr(test_text[:100])}...")

    try:
        result = format_raw_text_as_structured_json(test_text, 'soil')
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
                else:
                    print(f"  Value: {value}")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_sp_lab()
