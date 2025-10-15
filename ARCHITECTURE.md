## Architecture

- `app.py`: Streamlit entrypoint and page routing
- `modules/`:
  - `results.py`: renders step results, incl. Nutrient Gap table (Step 1)
  - `dashboard.py`, `upload.py`, `history.py`, `admin.py`, `config_management.py`
- `utils/`:
  - `analysis_engine.py`: step orchestration and rules; computes tables
  - `pdf_utils.py`: PDF report generation
  - `auth_utils.py`, `firebase_config.py`: auth support with Firebase SDK
  - `ocr_utils.py`, `parsing_utils.py`: I/O and formatting
  - `parameter_standardizer.py`, `reference_search.py`: data normalization/search
- `json/`, `leaf/`, `soil/`: sample inputs and generated outputs
- Key rule: Nutrient Gap Analysis sorts by severity and magnitude; results and PDF use identical logic.

