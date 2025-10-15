## Deployment

### A) Local (Windows)
- `python -m venv .venv && .\.venv\Scripts\activate`
- `pip install -r requirements.txt`
- Configure `.streamlit\secrets.toml` (see `CONFIGURATION.md`)
- `streamlit run app.py`

### B) Streamlit Cloud
- Push repo
- In app settings:
  - Main file: `app.py`
  - Python: 3.10
  - Requirements: `requirements.txt`
  - Secrets: paste contents of `secrets.toml` securely
- Restart app

### C) Docker
- Build: `docker build -t ags-ai:latest .`
- Run:
  - Windows:
    `docker run --rm -p 8501:8501 -v ${PWD}\.streamlit:/app/.streamlit ags-ai:latest`
- Provide `.streamlit/secrets.toml` on the mounted volume

### Health/Smoke
- Open `http://localhost:8501`
- Upload sample JSON from `json/` and navigate Step 1