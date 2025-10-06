from utils.analysis_engine import ResultsGenerator

rg = ResultsGenerator()
land_yield_data = {
    'land_size': 31.0,
    'current_yield': 28.0,
    'land_unit': 'hectares',
    'yield_unit': 'tonnes/hectare'
}

forecast = rg.generate_economic_forecast(land_yield_data, [])

print('=== ECONOMIC FORECAST STRUCTURE TEST ===')
print('Available keys:', list(forecast.keys()))
if 'scenarios' in forecast:
    print('Scenarios available:', list(forecast['scenarios'].keys()))
    for scenario in ['high', 'medium', 'low']:
        if scenario in forecast['scenarios']:
            data = forecast['scenarios'][scenario]
            yearly_available = 'yearly_data' in data
            print(f'{scenario}: yearly_data available = {yearly_available}')
            if yearly_available:
                years_count = len(data['yearly_data'])
                print(f'{scenario}: years available = {years_count}')
                if years_count > 0:
                    print(f'{scenario}: sample year 1 data keys = {list(data["yearly_data"][0].keys())}')
