## Configuration (no prior experience needed)

The app reads a single file for settings: `.streamlit/secrets.toml`. A complete blank template is already in the project as `.streamlit/secrets.example.toml`.

### 1) Create your secrets file
1) Copy the example: `.streamlit/secrets.example.toml` ➜ `.streamlit/secrets.toml`
2) Open the new file and fill in values you have. You can leave optional items empty.

### 2) Minimum you need to run locally
This is enough for most users:
```
[app]
environment = "production"
log_level = "INFO"
```

### 3) Optional: Firebase (for login)
If you use authentication, fill these:
```
[firebase]
api_key = ""            # optional client-side key
auth_domain = ""
project_id = ""
storage_bucket = ""     # required for file storage
messaging_sender_id = ""
app_id = ""
```

Advanced (Admin SDK) – only if you manage your own Firebase service account:
```
firebase_type = "service_account"
firebase_private_key_id = ""
firebase_private_key = """-----BEGIN PRIVATE KEY-----

-----END PRIVATE KEY-----"""
firebase_client_email = ""
firebase_client_id = ""
firebase_auth_uri = "https://accounts.google.com/o/oauth2/auth"
firebase_token_uri = "https://oauth2.googleapis.com/token"
firebase_auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
firebase_client_x509_cert_url = ""
firebase_universe_domain = "googleapis.com"
```

### 4) Optional: Google AI and Document AI
Only if you plan to use those features.
```
[google_ai]
api_key = ""

[google_documentai]
type = "service_account"
project_id = ""
private_key_id = ""
private_key = """-----BEGIN PRIVATE KEY-----

-----END PRIVATE KEY-----"""
client_email = ""
client_id = ""
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = ""
universe_domain = "googleapis.com"
processor_id = ""
location = "us"
```

### 5) Admin and email (optional)
```
[admin]
admin_codes = ["DEFAULT_ADMIN_2025"]

[smtp]
host = "smtp.gmail.com"
port = 587
username = ""
password = ""
from_email = ""
ssl = false
```

That’s it—save the file and start the app.

