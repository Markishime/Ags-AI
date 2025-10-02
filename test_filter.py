#!/usr/bin/env python3
# Test the exact filter logic from display_formatted_soil_issue
issue = {
    'parameter': 'pH',
    'optimal_range': '4.0-5.5',
    'current_value': 0.0,
    'out_of_range_samples': [
        {'sample_no': 'pH', 'value': 0.0, 'min_val': 4.0, 'max_val': 5.5},
        {'sample_no': 'N (%)', 'value': 0.0, 'min_val': 4.0, 'max_val': 5.5},
        {'sample_no': 'Org. C (%)', 'value': 0.0, 'min_val': 4.0, 'max_val': 5.5},
        {'sample_no': 'Total P (mg', 'value': 0.0, 'min_val': 4.0, 'max_val': 5.5}
    ]
}

parameter = issue.get('parameter', '')
optimal_range = issue.get('optimal_range', '')
current_value = issue.get('current_value', 0)

print('Testing filter logic...')

# Check 1: non-pH parameter has pH optimal range
if parameter != 'pH' and optimal_range == '4.0-5.5':
    print('Check 1 triggered: Non-pH parameter has pH optimal range')
    exit(0)  # Would return here

# Check 2: all values are 0.0
if current_value == 0.0:
    out_of_range_samples = issue.get('out_of_range_samples', [])
    if out_of_range_samples and all(sample.get('value', 0) == 0.0 for sample in out_of_range_samples):
        print('Check 2 triggered: All sample values are 0.0')
        exit(0)  # Would return here

# Check 3: pH parameter with samples containing other parameter names
if parameter == 'pH':
    out_of_range_samples = issue.get('out_of_range_samples', [])
    if out_of_range_samples:
        sample_names = [sample.get('sample_no', '').lower() for sample in out_of_range_samples]
        print('Sample names (lowercase):', sample_names)
        other_params = ['n (%)', 'org. c (%)', 'total p', 'avail p', 'exch. k', 'exch. ca', 'exch. mg', 'cec']
        print('Checking for other params:', other_params)

        for name in sample_names:
            for other in other_params:
                if other in name:
                    print(f'Found match: "{other}" in "{name}"')
                    exit(0)  # Would return here

print('No filters triggered - issue would be displayed')
