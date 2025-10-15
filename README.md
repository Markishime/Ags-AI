## Ags-AI

Streamlit-based analysis tool for soil/leaf reports with MPOB comparisons and PDF export.

### Features
- Step-based analysis and tables (including Nutrient Gap Analysis sorted by severity)
- PDF report generation
- Firebase client SDK auth integration [[memory:7934617]]
- OCR/import tools and parameter statistics

### Quickstart
1. Python 3.10+
2. `python -m venv .venv && .\.venv\Scripts\activate`
3. `pip install -r requirements.txt`
4. Configure secrets: see `CONFIGURATION.md`
5. Run: `streamlit run app.py`

### Deploy
- See `DEPLOYMENT.md` for Streamlit Cloud and Docker.