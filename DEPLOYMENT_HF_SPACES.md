# Deployment Guide: Hugging Face Spaces (Recommended)

## Why Hugging Face Spaces?

✅ **Completely free** - No credit card required  
✅ **No branding** - No avatars, logos, or profile links  
✅ **Built for ML/AI** - Perfect for your AI assistant  
✅ **Custom domain** - Can use your own domain  
✅ **Auto-deploy** - Deploys automatically from GitHub  
✅ **Fast & reliable** - Powered by Hugging Face infrastructure  

## Quick Setup (5 minutes)

### Step 1: Create Hugging Face Account
1. Go to [huggingface.co](https://huggingface.co)
2. Sign up for a free account
3. Verify your email

### Step 2: Create a New Space
1. Go to [huggingface.co/spaces](https://huggingface.co/spaces)
2. Click **"Create new Space"**
3. Fill in:
   - **Space name**: `ags-ai-assistant` (or your preferred name)
   - **SDK**: Select **Streamlit**
   - **Visibility**: Public or Private
   - **Hardware**: CPU Basic (free tier)
4. Click **"Create Space"**

### Step 3: Connect Your GitHub Repository
1. In your Space settings, go to **"Repository"** tab
2. Click **"Add file"** → **"Upload files"**
3. Or better: Connect your GitHub repo:
   - Go to Space settings → **"Repository"**
   - Click **"Add file"** → **"Add a README"**
   - Then go to **"Settings"** → **"Repository"**
   - Enable **"GitHub integration"**
   - Connect your GitHub account
   - Select your `Ags-AI` repository
   - Set branch to `main`

### Step 4: Create Required Files

Create these files in your Space (or in your GitHub repo):

#### `app.py` (already exists - just ensure it's in root)
Your main app file should be in the root directory.

#### `requirements.txt` (already exists)
Your requirements.txt should be in the root directory.

#### `README.md` (optional but recommended)
Add a brief description of your app.

#### `.streamlit/config.toml` (already exists)
Your Streamlit config file.

### Step 5: Configure Secrets
1. In your Space, go to **"Settings"** → **"Secrets"**
2. Add all your secrets from `.streamlit/secrets.toml`:
   - Firebase credentials
   - Google AI API key
   - Document AI credentials
   - etc.

**Important**: For nested secrets like Firebase, use this format:
- Key: `FIREBASE_PROJECT_ID`
- Value: `cropdriveai`

Or use the JSON format:
- Key: `FIREBASE_SERVICE_ACCOUNT_KEY`
- Value: `{"type": "service_account", "project_id": "cropdriveai", ...}`

### Step 6: Deploy
1. If using GitHub integration, push to your repo and it auto-deploys
2. If uploading manually, upload all files and it will deploy automatically
3. Wait 2-3 minutes for the first deployment
4. Your app will be live at: `https://YOUR-USERNAME-ags-ai-assistant.hf.space`

## Accessing Secrets in Hugging Face Spaces

Update your `utils/firebase_config.py` to read from environment variables:

```python
# Hugging Face Spaces uses environment variables
import os

# In get_firebase_credentials():
if os.getenv('FIREBASE_SERVICE_ACCOUNT_KEY'):
    import json
    return json.loads(os.getenv('FIREBASE_SERVICE_ACCOUNT_KEY'))
```

## Custom Domain (Optional)

1. Go to Space **"Settings"** → **"Domain"**
2. Add your custom domain
3. Update DNS records as instructed

## Advantages Over Streamlit Cloud

- ✅ No user avatars or profile links
- ✅ No Streamlit branding
- ✅ Clean, professional appearance
- ✅ Better for AI/ML applications
- ✅ More control over deployment
- ✅ Free custom domains available

---

# Alternative Free Platforms

## 2. Render (render.com)

**Free Tier**: 750 hours/month (enough for 24/7)

**Setup**:
1. Sign up at [render.com](https://render.com)
2. Connect GitHub account
3. New → Web Service
4. Select your repository
5. Configure:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `streamlit run app.py --server.port=$PORT --server.address=0.0.0.0`
   - **Environment**: Python 3
6. Add environment variables from secrets
7. Deploy

**Pros**: Clean deployment, no branding issues  
**Cons**: Spins down after 15 min inactivity (free tier)

## 3. Railway (railway.app)

**Free Tier**: $5 credit/month (usually enough for small apps)

**Setup**:
1. Sign up at [railway.app](https://railway.app)
2. New Project → Deploy from GitHub
3. Select your repository
4. Railway auto-detects Streamlit
5. Add environment variables
6. Deploy

**Pros**: Very easy setup, no branding  
**Cons**: Limited free credits

## 4. Fly.io (fly.io)

**Free Tier**: 3 shared VMs, 3GB storage

**Setup**:
1. Install Fly CLI: `curl -L https://fly.io/install.sh | sh`
2. Sign up: `fly auth signup`
3. Create app: `fly launch`
4. Deploy: `fly deploy`

**Pros**: Full control, Docker-based  
**Cons**: More technical setup

## 5. Modal (modal.com)

**Free Tier**: Generous free tier

**Setup**:
1. Sign up at [modal.com](https://modal.com)
2. Create a Modal app
3. Deploy with their Python SDK

**Pros**: Great for AI/ML workloads  
**Cons**: Requires code changes for Modal SDK

---

## Recommendation

**Use Hugging Face Spaces** - It's the best fit for your AI assistant:
- Zero branding issues
- Built specifically for ML/AI apps
- Completely free
- Easy GitHub integration
- Professional appearance

Your app will be accessible at: `https://YOUR-USERNAME-ags-ai-assistant.hf.space`

No avatars, no logos, just your AI assistant! 🚀

