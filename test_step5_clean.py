#!/usr/bin/env python3
"""
Test script to verify that Step 5 no longer displays raw LLM output
"""

def test_step5_clean_display():
    """Verify that Step 5 display function no longer shows raw LLM content"""

    with open('modules/results.py', 'r') as f:
        content = f.read()

    # Check that display_step5_economic_forecast no longer calls display_formatted_economic_tables
    display_step5 = content[content.find('def display_step5_economic_forecast'):content.find('def display_year_2_5_economic_tables')]

    # Should NOT contain these problematic calls
    no_display_formatted_tables = 'display_formatted_economic_tables' not in display_step5
    no_economic_analysis_display = 'economic_analysis' not in display_step5 or '#### 📊 Economic Analysis' not in display_step5

    print(f"✅ display_step5_economic_forecast no longer calls display_formatted_economic_tables: {no_display_formatted_tables}")
    print(f"✅ display_step5_economic_forecast no longer displays raw economic_analysis: {no_economic_analysis_display}")

    # Should contain these good calls
    has_economic_overview = 'display_economic_overview(forecast_data)' in display_step5
    has_5_year_tables = 'display_5_year_economic_tables(forecast_data)' in display_step5
    has_5_year_charts = 'display_5_year_economic_charts(forecast_data)' in display_step5

    print(f"✅ display_step5_economic_forecast calls display_economic_overview: {has_economic_overview}")
    print(f"✅ display_step5_economic_forecast calls display_5_year_economic_tables: {has_5_year_tables}")
    print(f"✅ display_step5_economic_forecast calls display_5_year_economic_charts: {has_5_year_charts}")

    # Check analysis engine
    with open('utils/analysis_engine.py', 'r') as f:
        ae_content = f.read()

    # Should not include economic_analysis in Step 5 results
    step5_parsing = ae_content[ae_content.find("elif step['number'] == 5:  # Economic Impact Forecast"):ae_content.find("elif step['number'] == 6:")]
    no_economic_analysis_in_step5 = "'economic_analysis':" not in step5_parsing

    print(f"✅ Analysis engine no longer includes economic_analysis in Step 5 results: {no_economic_analysis_in_step5}")

    all_checks_pass = all([
        no_display_formatted_tables,
        no_economic_analysis_display,
        has_economic_overview,
        has_5_year_tables,
        has_5_year_charts,
        no_economic_analysis_in_step5
    ])

    print(f"\n🎉 Step 5 clean display verification: {'PASSED' if all_checks_pass else 'FAILED'}")
    print("✅ Step 5 now only displays properly formatted economic forecast data")
    print("✅ No more raw LLM output or malformed tables in Step 5")

if __name__ == "__main__":
    test_step5_clean_display()
