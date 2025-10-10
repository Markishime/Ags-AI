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

print('SOIL PARAMETERS AVAILABLE:')
if 'parameter_statistics' in soil_params:
    for param in sorted(soil_params['parameter_statistics'].keys()):
        stats = soil_params['parameter_statistics'][param]
        if isinstance(stats, dict) and 'average' in stats:
            print(f'  {param}: {stats["average"]:.3f}')

print()
print('LEAF PARAMETERS AVAILABLE:')
if 'parameter_statistics' in leaf_params:
    for param in sorted(leaf_params['parameter_statistics'].keys()):
        stats = leaf_params['parameter_statistics'][param]
        if isinstance(stats, dict) and 'average' in stats:
            print(f'  {param}: {stats["average"]:.3f}')
