#!/usr/bin/env python3

from utils.analysis_engine import AnalysisEngine
import json

# Load test data
with open('json/farm_3_soil_test.json', 'r') as f:
    soil_data = json.load(f)

with open('json/farm_3_leaf_test.json', 'r') as f:
    leaf_data = json.load(f)

# Convert data to analysis format
engine = AnalysisEngine()
soil_params = engine._convert_structured_to_analysis_format(soil_data, 'soil')
leaf_params = engine._convert_structured_to_analysis_format(leaf_data, 'leaf')

# Create analysis results structure with processed data
analysis_results = {
    'raw_data': {
        'soil_data': soil_params,
        'leaf_data': leaf_params
    }
}

# Import and test the key findings function
from modules.results import generate_consolidated_key_findings

# Mock step_results
step_results = []

# Generate findings
findings = generate_consolidated_key_findings(analysis_results, step_results)

# Debug: check what issues were found
print("Debugging issues found:")
from modules.results import generate_consolidated_key_findings
# I need to access the internal variables, so let me modify the approach

# Print all findings
print(f"Generated {len(findings)} findings:")
for i, finding in enumerate(findings):
    print(f"\n{i+1}. {finding.get('title', 'No title')}:")
    desc = finding.get('description', 'No description')
    print(desc)
