# Streamlit Cloud Deployment Checklist

## Pre-Deployment Checklist

### ✅ Code Preparation
- [x] All dependencies listed in `requirements.txt`
- [x] System dependencies listed in `packages.txt`
- [x] No hardcoded paths or local file references
- [x] Environment variables properly configured
- [x] `.gitignore` excludes sensitive files

### ✅ Repository Setup
- [ ] Code pushed to GitHub repository
- [ ] Repository is public (for free Streamlit Cloud)
- [ ] Main file is `app.py`
- [ ] All necessary files are committed

### ✅ Streamlit Cloud Configuration
- [ ] Secrets configured in Streamlit Cloud dashboard
- [ ] Firebase credentials added to secrets
- [ ] Google AI API key added to secrets
- [ ] Admin codes configured

## Required Secrets Configuration

Add these to your Streamlit Cloud secrets (copy from your .env file):

```toml
[firebase]
api_key = "your_firebase_api_key"
auth_domain = "agriai-cbd8b.firebaseapp.com"
project_id = "agriai-cbd8b"
storage_bucket = "agriai-cbd8b.firebasestorage.app"
messaging_sender_id = "your_messaging_sender_id"
app_id = "your_firebase_app_id"

# Firebase Service Account (for admin operations)
firebase_type = "service_account"
firebase_private_key_id = "21fa9105b46a99409d1eaf4cba203d2223584a50"
firebase_private_key = "-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQCl+cTm6znoEGxN\nSA8mRvVZMQDDjQ/4qqoscMcyCy3JRWYJIGdfrwkVVeAoTRjbvqTniulVGQ7uB01f\nw6j2WKoF9fQ2WaE02GbArDHRW4oE9knFAaz7akOcwgde8CnbQ8p/urKZWyYKQb92\nSWaN0svwPnKsqruYHrUHm/ohyAK3Px12d7FrrrIrl5QOxFFSdFElXuPyJPAUdIDA\nMGr1BlfzuwvOS422oo2jkFV09yOxBgXT0Bqsn8X4Fybpdd6jhtviJfRP0F/7P+Hx\nSjz1m7z2OPk/TuYW1q6kfB3IQkG9vtpv/faqyg3MYo7NBW4asf8mFRr3x/m+ZjX9\nUYwYelbVAgMBAAECggEAJfKdWk6dxrk6idDX5eCDaAkUK6Gs7SXYEqEWahK0PTho\nw91sxSu33/Dqd0xpSpSkD2xrPNGl4DY7MpIBp5FODl7VnzeO7A4uMA8utLdBLzFA\nXJKtgi4hl02lccdnSoKNYfbFrtpwMBgoNltB31s61YrxnRjMG1OqADthTSf1tv+Q\nKzNuQR8vIhhW1DMI5Kb63P8M5eKEINTb4+PZclfFDAkUPpCQlu93R79kKuoHxafl\ndW20aWEavfoR61yKTV/Pmmh+psF5QFnQRJ99egRQioXM5YHNZeu6hqu3Ex+yVvCC\ngs+vR8VTM4cNn2dsdLU+lYzdfCIDNONy/OGaHUH+YQKBgQDqZtnsbYnPnMsc/VV6\ng+7MX4Lao3Sn3o+vnxh+wl5GvjLRluF3PcXvYqpOHKxBOlapSwn9PN9iegSm0RcN\nkyAYGGJnK0ukfaO1VMnZkr+qRT6+ndKxCdDCbrbI9dZxbpSijbR7/o0ag7bbryr0\nnH+FTeCwpSyX2VAeFU/oE5upJwKBgQC1RNwSAILqdp2RgZ1cEv/9zXsZNuqcEwYW\nALR3Oz8bqxuzDAFE85lEDwiKp3XkhOfBuPeytK4j0NFOY0v+rqPGe9rnxhIx9dXX\nn6Y2ZJsbUmyAsNDDELG4gRxvOIqcHwFTkrPHoeiRizHmH9FASl3iODsyimFxFcRc\ng3gFoJ0lowKBgHBgtwH+0h9TEJ3pZt3B+u7Iq7eevgLtVP3hzKCZFxHbhgmtyJKe\nbxMBvpyMapkrGvk3HKboVECmNyyy+dZsPurOZf8IZs+J3L7G068YCAPeBuLkT2rJ\nReixo7hdBF6FoYT9YxY/R+76TuSr6nAzx39lgt+tkN+MNDj4BsNBA1PpAoGAFRFg\nxpLapGeO3reC0429xQDZ2s9gKy2m2m3Qi78OEagsev3dM+dgG+Hnaz4VXK75xLE7\n0MBhMPZ3LTYrQfmIPWxtv9xshvP8m6gJiG7e/CjzRW3HhbRuA3S2GlMnAQg1fkIh\ntQUjY68a6JUwG9nI2Z8ReklNE/ikrt/01iqZuSMCgYEA0XHD3h4seUV/lnmJ3x4L\n1RDw7gOLxyxP+7Vn4nzEHyDcrAij0H3EshrFlECW/KyEAUukvMWVqCV5FxuZ6/Vz\nFoG9HZwJtWopjpXrmOLbUBiKxwDQ2Lo1PwEbGvsOl5/2MwnkbNKs1D/AfNBChJ/8\nN5oY8xmm0A88wxvz95dF/Ec=\n-----END PRIVATE KEY-----\n"
firebase_client_email = "firebase-adminsdk-fbsvc@agriai-cbd8b.iam.gserviceaccount.com"
firebase_client_id = "100151148066111611456"
firebase_auth_uri = "https://accounts.google.com/o/oauth2/auth"
firebase_token_uri = "https://oauth2.googleapis.com/token"
firebase_auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
firebase_client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-fbsvc%40agriai-cbd8b.iam.gserviceaccount.com"
firebase_universe_domain = "googleapis.com"

# Firebase Storage Bucket
firebase_storage_bucket = "agriai-cbd8b.firebasestorage.app"

[google_ai]
api_key = "AIzaSyD8voLGNp5yE0co4VhP3M0TgkaW8lWPZVs"

# Alternative Google AI keys (for compatibility)
google_api_key = "AIzaSyD8voLGNp5yE0co4VhP3M0TgkaW8lWPZVs"
gemini_api_key = "AIzaSyD8voLGNp5yE0co4VhP3M0TgkaW8lWPZVs"

[admin]
admin_codes = ["DEFAULT_ADMIN_2025", "your_admin_code_2"]

[ocr]
tesseract_path = "/usr/bin/tesseract"

# Tavily Search API (for reference search)
tavily_api_key = "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"

# Application Settings
[app]
streamlit_server_port = 8501
streamlit_server_address = "localhost"
environment = "development"
log_level = "INFO"
max_upload_size_mb = 10
session_timeout_minutes = 60
```

## Deployment Steps

1. **GitHub Setup**:
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/YOUR_USERNAME/ags-ai-assistant.git
   git push -u origin main
   ```

2. **Streamlit Cloud**:
   - Go to [share.streamlit.io](https://share.streamlit.io)
   - Click "New app"
   - Select your repository
   - Set main file: `app.py`
   - Configure secrets
   - Deploy!

## Post-Deployment

- [ ] Test all major features
- [ ] Verify Firebase authentication works
- [ ] Test document upload and analysis
- [ ] Check OCR functionality
- [ ] Verify admin panel access

## Troubleshooting

### Common Issues:
1. **Tesseract not found**: Ensure `packages.txt` includes `tesseract-ocr`
2. **Firebase errors**: Check secrets configuration
3. **Import errors**: Verify all dependencies in `requirements.txt`
4. **File not found**: Ensure no hardcoded local paths

### Performance Optimization:
- Consider adding caching for expensive operations
- Optimize image processing for cloud environment
- Monitor memory usage for large document processing
