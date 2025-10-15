## Deployment (for everyone)

This guide shows three ways to run the app. Choose the one that fits you.

### A) Local on Windows (simplest)
1) Install Python 3.10+
2) Open PowerShell in the project folder
3) Create a private environment and install the app
   - `python -m venv .venv`
   - `.\\.venv\\Scripts\\activate`
   - `pip install -r requirements.txt`
4) Configure secrets
   - Copy `.streamlit/secrets.example.toml` to `.streamlit/secrets.toml`
   - Fill in values (you can leave optional sections blank)
5) Run the app
   - `streamlit run app.py`
6) Use the browser link shown (usually `http://localhost:8501`)

Troubleshooting
- If the window doesn’t open, copy the URL from the terminal into your browser
- If install fails, run `pip install -U pip` and try again

### B) Streamlit Cloud (no local setup)
1) Push the repository to your Git provider (GitHub/GitLab)
2) Create a Streamlit Cloud app
3) Settings:
   - Main file: `app.py`
   - Python version: 3.10
   - Requirements file: `requirements.txt`
   - Secrets: paste your `.streamlit/secrets.toml` contents into the Secrets UI
4) Save and deploy
5) Open the public URL Streamlit provides

### C) Docker (advanced, portable)
1) Build the image:
   - `docker build -t ags-ai:latest .`
2) Run the container:
   - `docker run --rm -p 8501:8501 -v ${PWD}\\.streamlit:/app/.streamlit ags-ai:latest`
3) Open `http://localhost:8501`

Notes
- The `-v` mount lets you provide your own `secrets.toml` from the host machine

### Health check
- Open the app and upload a sample from `json/`
- Go to Step 1 to see the Nutrient Gap Analysis table