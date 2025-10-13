import re

# Test XML parsing
test_xml = '''
<tables>
<table title="Economic Forecast Assumptions">
<headers>
<header>Parameter</header>
<header>Value/Range</header>
</headers>
<rows>
<row>
<cell>FFB Price</cell>
<cell>RM 650 - RM 750 per tonne</cell>
</row>
<row>
<cell>Ground Magnesium Limestone (GML)</cell>
<cell>RM 250 - RM 350 per tonne</cell>
</row>
</rows>
</table>
</tables>
<tables>
<table title="5-Year Economic Forecast: High-Investment Scenario">
<headers>
<header>Year</header>
<header>Yield improvement t/ha</header>
<header>Revenue RM/ha</header>
<header>Input cost RM/ha</header>
<header>Net profit RM/ha</header>
<header>Cumulative net profit RM/ha</header>
<header>ROI %</header>
</headers>
<rows>
<row>
<cell>1</cell>
<cell>2.5 - 3.5</cell>
<cell>1,625 - 2,625</cell>
<cell>3,185 - 3,955</cell>
<cell>-2,330 - -560</cell>
<cell>-2,330 - -560</cell>
<cell>-73.2% to -14.2%</cell>
</row>
</rows>
</table>
</tables>
'''

# Test the regex patterns
xml_tables_pattern = r'<tables>\s*<table[^>]*title="([^"]*)"[^>]*>([\s\S]*?)</table>\s*</tables>'
xml_matches = re.findall(xml_tables_pattern, test_xml, re.DOTALL | re.IGNORECASE)
print('XML matches found:', len(xml_matches))

for i, (title, content) in enumerate(xml_matches):
    print(f'\nTable {i+1}: {title}')

    # Test header extraction
    headers_section = re.search(r'<headers>(.*?)</headers>', content, re.DOTALL | re.IGNORECASE)
    headers = []
    if headers_section:
        header_matches = re.findall(r'<header>(.*?)</header>', headers_section.group(1), re.DOTALL | re.IGNORECASE)
        headers = [re.sub(r'<[^>]+>', '', h).strip() for h in header_matches]
    print('Headers:', headers)

    # Test row extraction
    rows_section = re.search(r'<rows>(.*?)</rows>', content, re.DOTALL | re.IGNORECASE)
    rows = []
    if rows_section:
        row_matches = re.findall(r'<row>(.*?)</row>', rows_section.group(1), re.DOTALL | re.IGNORECASE)
        print('Rows found:', len(row_matches))
        for row_match in row_matches:
            cell_matches = re.findall(r'<cell>(.*?)</cell>', row_match, re.DOTALL | re.IGNORECASE)
            clean_cells = [re.sub(r'<[^>]+>', '', cell).strip() for cell in cell_matches]
            rows.append(clean_cells)
            print('Cells:', clean_cells)

    print('Parsed data would create DataFrame with:')
    print('Columns:', headers)
    print('Data:', rows)
