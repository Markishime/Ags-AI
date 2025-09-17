#!/usr/bin/env python3

import sys
import os
sys.path.append('.')

import json
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_sp_lab_processing():
    """Test SP lab file parameter processing"""

    # Load SP lab test data
    with open('json/sp_lab_test_report.json', 'r') as f:
        sp_lab_data = json.load(f)

    print("=== TESTING SP LAB FILE PROCESSING ===")

    # Test parameter mapping for SP lab data
    soil_samples = []
    if 'SP_Lab_Test_Report' in sp_lab_data:
        print("Processing SP_Lab_Test_Report format...")
        for sample_id, params in sp_lab_data['SP_Lab_Test_Report'].items():
            if params:
                sample = {'sample_no': sample_id.replace('S', '').replace('/', ''), 'lab_no': sample_id}
                # Use the corrected mapping
                sample.update({
                    'pH': params.get('pH'),
                    'Nitrogen_%': params.get('Nitrogen (%)'),
                    'Organic_Carbon_%': params.get('Organic Carbon (%)'),
                    'Total_P_mg_kg': params.get('Total P (mg/kg)'),
                    'Available_P_mg_kg': params.get('Available P (mg/kg)'),
                    'Exchangeable_K_meq%': params.get('Exch. K (meq%)'),
                    'Exchangeable_Ca_meq%': params.get('Exch. Ca (meq%)'),
                    'Exchangeable_Mg_meq%': params.get('Exch. Mg (meq%)'),
                    'CEC_meq%': params.get('C.E.C (meq%)')
                })
                soil_samples.append(sample)
                print(f"Sample {sample_id}: pH={sample.get('pH')}, Nitrogen_%={sample.get('Nitrogen_%')}, Organic_Carbon_%={sample.get('Organic_Carbon_%')}")

    print(f"\nProcessed {len(soil_samples)} soil samples from SP lab file")

    # Test averages calculation
    soil_standards = {
        'pH': {'optimal': '5.0-6.0'},
        'Nitrogen_%': {'optimal': '0.15-0.25'},
        'Organic_Carbon_%': {'optimal': '2.0-3.5'},
        'Total_P_mg_kg': {'optimal': '25-45'},
        'Available_P_mg_kg': {'optimal': '10-20'},
        'Exchangeable_K_meq%': {'optimal': '0.20-0.40'},
        'Exchangeable_Ca_meq%': {'optimal': '2.5-4.5'},
        'Exchangeable_Mg_meq%': {'optimal': '0.6-1.2'},
        'CEC_meq%': {'optimal': '12-25'}
    }

    print("\n=== SP LAB AVERAGES CALCULATION ===")

    soil_averages = {}
    for param in soil_standards.keys():
        values = []
        for sample in soil_samples:
            val = sample.get(param)
            if val is not None and val != 'N/A' and str(val).lower() not in ['n.d.', 'nd']:
                try:
                    values.append(float(val))
                    print(f"  {param}: sample {sample.get('sample_no')} = {val}")
                except (ValueError, TypeError):
                    print(f"  {param}: sample {sample.get('sample_no')} = {val} (could not convert to float)")
                    pass

        if values:
            avg = sum(values) / len(values)
            soil_averages[param] = avg
            print(f"  {param}: {len(values)} values, average = {avg:.3f}")
        else:
            soil_averages[param] = 'N/A'
            print(f"  {param}: No valid values found")

    print("\n=== FINAL RESULTS ===")
    print("SP Lab soil averages:")
    for param, avg in soil_averages.items():
        if avg != 'N/A':
            print(f"  {param}: {avg:.3f}")
        else:
            print(f"  {param}: N/A")

    # Check if all parameters have values (should not be N/A)
    na_params = [param for param, avg in soil_averages.items() if avg == 'N/A']
    if na_params:
        print(f"\n⚠️  WARNING: {len(na_params)} parameters still showing N/A: {na_params}")
        return False
    else:
        print("\n✅ SUCCESS: All parameters have valid averages!")
        return True

if __name__ == "__main__":
    success = test_sp_lab_processing()
    if success:
        print("\n🎯 SP LAB PARAMETER PROCESSING: FIXED!")
    else:
        print("\n❌ SP LAB PARAMETER PROCESSING: ISSUES REMAIN")
