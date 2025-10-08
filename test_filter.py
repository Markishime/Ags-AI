from modules.results import _strip_step5_raw_economic_blocks

test_text = '''Some text before
Scenarios: {"high": {"investment_level": "High", "cost_per_hectare_range": "RM 2195-2501", "total_cost_range": "RM 68,045-77,531", "current_yield": 28, "new_yield_range": "35.0-37.8 t/ha", "additional_yield_range": "7.0-9.8 t/ha", "yearly_data": {"item_0": "{\"year\": 1, \"yield_low\": 32.9, \"yield_high\": 35.84, \"additional_yield_low\": 4.899999999999999, \"additional_yield_high\": 7.840000000000003, \"additional_revenue_low\": 98734.99999999997, \"additional_revenue_high\": 182280.0000000001, \"cost_low\": 68045, \"cost_high\": 77531, \"net_profit_low\": 30689.99999999997, \"net_profit_high\": 104749.00000000009, \"cumulative_profit_low\": 30689.99999999997, \"cumulative_profit_high\": 104749.00000000009, \"roi_low\": 42.16354344122654, \"roi_high\": 143.90971039182295}", "item_1": "{\"year\": 2, \"yield_low\": 33.95, \"yield_high\": 37.31, \"additional_yield_low\": 5.950000000000003, \"additional_yield_high\": 9.310000000000002, \"additional_revenue_low\": 119892.50000000006, \"additional_revenue_high\": 216457.50000000006, \"cost_low\": 12400.0, \"cost_high\": 12400.0, \"net_profit_low\": 107492.50000000006, \"net_profit_high\": 204057.50000000006, \"cumulative_profit_low\": 138182.50000000003, \"cumulative_profit_high\": 308806.5000000001, \"roi_low\": 147.67887563884165, \"roi_high\": 280.34497444633735}"}}

Some text after'''

result = _strip_step5_raw_economic_blocks(test_text)
print('Original length:', len(test_text))
print('Cleaned length:', len(result))
print('Contains raw data:', 'Scenarios:' in result or 'Assumptions:' in result)
print('Cleaned text:')
print(result)
