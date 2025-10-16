## Ags-AI

An easy-to-use app that reads your soil and leaf test results, compares them to Malaysian MPOB standards, and presents clear tables and a downloadable PDF report. No data science skills needed.

### What you can do with Ags‑AI
- See which nutrients are below the recommended minimum and how severe the gap is
- Understand priorities using the Nutrient Gap Analysis (Critical at the top)
- Export a professional PDF report for sharing with your team
- Upload common lab formats or farm-style spreadsheets

### What you need
- Windows 10/11
- Python 3.10 or newer
- Your soil and/or leaf test data files (see examples in the `json/` folder)

### Quickstart (5 steps)
1) Install Python if you haven’t already.
2) Open PowerShell in the project folder.
3) Create and activate an isolated environment:
   - `python -m venv .venv`
   - `.\\.venv\\Scripts\\activate`
4) Install the app:
   - `pip install -r requirements.txt`
5) Start the app:
   - `streamlit run app.py`

Your browser will open at `http://localhost:8501`. Use the Upload page to add your files and go to Step 1 to see the analysis.

### Configuration
- The app reads settings from `.streamlit/secrets.toml`.
- Copy the provided template: `.streamlit/secrets.example.toml` to `.streamlit/secrets.toml` and fill in values.
- Full details are in `CONFIGURATION.md`.

### Need help deploying?
- Step‑by‑step guides for Local, Streamlit Cloud, and Docker are in `DEPLOYMENT.md`.

> **Runs successfully on my machine as of Oct 16, 2025** ([https://github.com/Markishime/Ags-AI](https://github.com/Markishime/Ags-AI) @ 88be584 v1.0). To start on a clean Windows machine: follow the Quickstart steps above (Python venv + `pip install -r requirements.txt` + `streamlit run app.py`).
