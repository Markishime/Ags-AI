### Ags‑AI User Guide
A complete, non‑technical guide for running, understanding, and sharing Ags‑AI.

## 1) What Ags‑AI Is
Ags‑AI reads your soil and leaf test results and compares them with MPOB standards, highlighting gaps and generating a PDF report.

## 2) What You Can Do
- Upload soil/leaf data
- See Nutrient Gap Analysis (Critical → Low → Balanced)
- Export a matching PDF

## 3) Requirements
- Windows 10/11, Python 3.10+, browser

## 4) Quickstart
1. `python -m venv .venv`
2. `.\.venv\\Scripts\\activate`
3. `pip install -r requirements.txt`
4. Copy `.streamlit/secrets.example.toml` to `.streamlit/secrets.toml`
5. `streamlit run app.py` → open `http://localhost:8501`

## 5) Uploading Data
Use the Upload page; examples are in `json/`.

## 6) Reading Results
Severity by absolute percent gap:
- Balanced ≤ 5%
- Low 5–15%
- Critical > 15%

## 7) Exporting PDF
Use the export option; PDF matches the on‑screen tables.

## 8) Configuration
Edit `.streamlit/secrets.toml`. Minimal local:
```
[app]
environment = "production"
log_level = "INFO"
```

## 9) Deployment Options
- Local Windows
- Streamlit Cloud
- Docker

## 10) Troubleshooting
- Update pip if install fails: `pip install -U pip`
- Try sample files in `json/` to validate

## 11) Where Things Live
- Start: `app.py`
- Results tables: `modules/results.py`
- PDF: `utils/pdf_utils.py`
- Engine: `utils/analysis_engine.py`
- Config: `.streamlit/secrets.toml`
