## Configuration

### Streamlit secrets
Create `.streamlit/secrets.toml`:
```
# Example only – do not commit real secrets
[firebase]
api_key = "..."
auth_domain = "..."
project_id = "..."
storage_bucket = "..."
messaging_sender_id = "..."
app_id = "..."

[app]
environment = "prod"
```

### Auth
- Uses Firebase client SDK for authentication
- Server-side utilities in `utils/auth_utils.py` and `utils/firebase_config.py` support verification.

### App settings
- Review `utils/firebase_config.py`, `utils/config_manager.py`, and `utils/ai_config_utils.py` for tunables.

