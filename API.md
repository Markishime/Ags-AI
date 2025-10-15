## Programmatic Interfaces

- `utils/analysis_engine.py`
  - `AnalysisEngine`: orchestrates steps, parses prompt, generates tables and metrics
  - Input: structured soil/leaf stats dicts, raw OCR structures, yield data
  - Output: per-step JSON blocks consumed by UI and PDF

- `modules/results.py`
  - `display_nutrient_gap_analysis_table(analysis_data)`: builds Step 1 table with consistent severity/sorting

- `utils/pdf_utils.py`
  - `_create_nutrient_gap_analysis_table_pdf(story, analysis_data, main_analysis_results)`: PDF companion of the same table

