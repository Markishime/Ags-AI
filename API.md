## Programmatic Interfaces (for advanced users)

You usually don’t need these, but if you want to integrate Ags‑AI into another system, start here.

### Analysis Engine
`utils/analysis_engine.py`
- `AnalysisEngine` orchestrates steps and constructs the data structures used by the UI and PDF.
- Inputs: structured soil/leaf statistics (or raw OCR structures), optional yield data.
- Outputs: JSON-like dictionaries with tables, summaries, and recommendations.

### Results Rendering
`modules/results.py`
- `display_nutrient_gap_analysis_table(analysis_data)` builds the Step 1 Nutrient Gap Analysis.
- Severity is based on absolute percent gap (Critical > 15%, Low 5–15%, Balanced ≤ 5%).

### PDF Generation
`utils/pdf_utils.py`
- `_create_nutrient_gap_analysis_table_pdf(story, analysis_data, main_analysis_results)` renders the same table in the PDF.

