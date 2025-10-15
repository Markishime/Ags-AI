## Architecture (plain language)

Think of the app as three parts:

1) The App (what you see)
- `app.py` starts the Streamlit web app and shows pages
- `modules/` contains the pages and sections (upload, dashboard, results)

2) The Engine (how results are calculated)
- `utils/analysis_engine.py` turns your data into averages, gaps, and tables
- `modules/results.py` draws the tables, including the Nutrient Gap Analysis
- `utils/pdf_utils.py` makes the PDF report with the same tables

3) Helpers (supporting tools)
- `utils/auth_utils.py`, `utils/firebase_config.py` handle login if enabled
- `utils/ocr_utils.py`, `utils/parsing_utils.py` help read files
- `utils/parameter_standardizer.py` keeps parameter names consistent

Data samples live in `json/`, and generated example outputs are in `leaf/` and `soil/`.

Important: The Nutrient Gap table is sorted with Critical issues at the top, then Low, then Balanced, using the size of the gap.

