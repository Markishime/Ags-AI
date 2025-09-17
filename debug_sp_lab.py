#!/usr/bin/env python3
import sys
sys.path.append('.')
import modules.upload as upload_module
import re

# Test SP Lab parsing with sample text
test_text = '''SP LAB
S218/25 S219/25 S220/25 S221/25 S222/25
pH
5.0 4.3 4.0 4.1 4.0
Nitrogen
0.10 0.09 0.09 0.07 0.08
Organic Carbon
0.89 0.80 0.72 0.33 0.58'''

print('Testing SP Lab parsing...')
print(f"Test text: {repr(test_text)}")

# Test the text preprocessing
raw_text = test_text.strip()
lines = [line.strip() for line in raw_text.split('\n') if line.strip()]
all_text = ' '.join(lines)
all_text = re.sub(r'[^\w\s\.\-\(\)\[\]\/]', ' ', all_text)
all_text = re.sub(r'\s+', ' ', all_text)

print(f"Processed text: {repr(all_text)}")
print(f"SP LAB check: {'SP LAB' in all_text.upper()}")
print(f"Regex check: {re.search(r'S\d{3}/\d{2}', all_text)}")

# Test the regex pattern
sp_lab_pattern = r'S(\d{1,3})/(\d{2})\s*[:\-]?\s*([^S\n]*(?=S\d|\n|$))'
sp_matches = re.findall(sp_lab_pattern, all_text, re.IGNORECASE | re.DOTALL)
print(f"SP Lab pattern matches: {len(sp_matches)}")
for i, match in enumerate(sp_matches):
    print(f"  Match {i}: {match}")

try:
    result = upload_module.format_raw_text_as_structured_json(test_text, 'soil')
    print('SP Lab parsing result:')
    print(f'Keys: {list(result.keys())}')
    if result:
        for key, value in result.items():
            print(f'{key}: {value}')
except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()
