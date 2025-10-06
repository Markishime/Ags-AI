from utils.analysis_engine import ResultsGenerator
import json

# Test the economic forecast generation
rg = ResultsGenerator()
land_yield_data = {
    'land_size': 31.0,
    'current_yield': 28.0,
    'land_unit': 'hectares',
    'yield_unit': 'tonnes/hectare'
}

forecast = rg.generate_economic_forecast(land_yield_data, [])

print('=== ECONOMIC FORECAST VERIFICATION ===')
print(f"User Data: Land Size {land_yield_data['land_size']} {land_yield_data['land_unit']}, Current Yield {land_yield_data['current_yield']} {land_yield_data['yield_unit']}")
print()

for scenario in ['high', 'medium', 'low']:
    if scenario in forecast['scenarios']:
        data = forecast['scenarios'][scenario]
        print(f'{scenario.upper()} INVESTMENT SCENARIO:')
        print(f"  Total Cost Range: RM {data['total_cost_range']}")
        print(f"  Target Yield Range: {data['new_yield_range']} t/ha")
        print(f"  5-Year Cumulative Profit: RM {data['cumulative_net_profit_range']}")
        print(f"  5-Year ROI: {data['roi_5year_range']}")
        print(f"  Payback Period: {data['payback_period_range']}")

        # Show Year 1 and Year 5 for verification
        yearly = data['yearly_data']
        y1 = yearly[0]  # Year 1
        y5 = yearly[4]  # Year 5

        print(f"  Year 1 - Profit: RM {y1['net_profit_low']:,.0f}-{y1['net_profit_high']:,.0f}, ROI: {y1['roi_low']:.1f}%-{y1['roi_high']:.1f}%")
        print(f"  Year 5 - Profit: RM {y5['net_profit_low']:,.0f}-{y5['net_profit_high']:,.0f}, ROI: {y5['roi_low']:.1f}%-{y5['roi_high']:.1f}%")
        print()
