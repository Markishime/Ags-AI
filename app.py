import streamlit as st
import sys
import os
import time
from datetime import datetime



# Ensure project root and utils are on sys.path
repo_root = os.path.dirname(__file__)
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)
utils_dir = os.path.join(repo_root, 'utils')
if utils_dir not in sys.path:
    sys.path.append(utils_dir)

# Import utilities with robust error handling
try:
    from utils.firebase_config import initialize_firebase, initialize_admin_codes
except ImportError:
    try:
        from firebase_config import initialize_firebase, initialize_admin_codes
    except ImportError as e:
        st.error(f"Failed to import firebase_config: {e}")
        initialize_firebase = None
        initialize_admin_codes = None

try:
    from utils.translations import translate, t, get_language, set_language, toggle_language
except ImportError:
    try:
        from translations import translate, t, get_language, set_language, toggle_language
    except ImportError as e:
        st.error(f"Failed to import translations: {e}")
        # Provide fallback functions
        def translate(text, lang=None): return text
        def t(key): return key
        def get_language(): return "en"
        def set_language(lang): pass
        def toggle_language(): return "en"

# Import CropDrive integration
try:
    from utils.cropdrive_integration import (
        initialize_integration,
        send_analysis_complete,
        is_feature_available,
        send_feature_restricted,
        get_user_plan,
        get_user_id
    )
    CROPDRIVE_INTEGRATION_AVAILABLE = True
except ImportError:
    try:
        from cropdrive_integration import (
            initialize_integration,
            send_analysis_complete,
            is_feature_available,
            send_feature_restricted,
            get_user_plan,
            get_user_id
        )
        CROPDRIVE_INTEGRATION_AVAILABLE = True
    except ImportError:
        CROPDRIVE_INTEGRATION_AVAILABLE = False
        # Fallback functions
        def initialize_integration():
            return 'en', 'none', []
        def send_analysis_complete(*args, **kwargs):
            pass
        def is_feature_available(*args, **kwargs):
            return True
        def send_feature_restricted(*args, **kwargs):
            pass
        def get_user_plan():
            return 'none'
        def get_user_id():
            return ''

import json
from datetime import datetime

# Ensure Gemini API key is available to LLM clients
try:
    if hasattr(st, 'secrets') and 'google_ai' in st.secrets:
        api_key = st.secrets.google_ai.get('api_key') or st.secrets.google_ai.get('google_api_key') or st.secrets.google_ai.get('gemini_api_key')
        if api_key and not os.getenv('GOOGLE_API_KEY'):
            os.environ['GOOGLE_API_KEY'] = api_key
except Exception:
    pass

# Add modules to path
modules_dir = os.path.join(repo_root, 'modules')
if modules_dir not in sys.path:
    sys.path.append(modules_dir)

# Import pages with robust fallbacks
try:
    from modules.upload import show_upload_page
except Exception:
    from upload import show_upload_page

try:
    from modules.results import show_results_page as results_page_func
except Exception as e:
    print(f"Warning: Could not import results module: {e}")
    import traceback
    traceback.print_exc()
    results_page_func = None

try:
    from modules.admin import show_admin_panel as admin_panel_func
except Exception as e:
    print(f"Warning: Could not import admin module: {e}")
    import traceback
    traceback.print_exc()
    admin_panel_func = None

# Page configuration
st.set_page_config(
    page_title="AGS AI Assistant",
    page_icon="🌴",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Hide Streamlit branding and user profile elements
st.markdown(
    """
    <style>
    /* Hide Streamlit UI elements */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}

    /* Hide Streamlit Cloud user avatar/profile button */
    button[title*="Manage app"] {display: none !important;}
    button[title*="Profile"] {display: none !important;}
    div[data-testid="stHeader"] button {display: none !important;}
    div[data-testid="stHeader"] a {display: none !important;}
    
    /* Hide Streamlit logo */
    div[data-testid="stHeader"] img {display: none !important;}
    a[href*="streamlit.io"] img {display: none !important;}
    
    /* Hide user profile menu and avatar */
    [data-testid="stHeader"] [data-testid="stDecoration"] {display: none !important;}
    [data-testid="stHeader"] > div:first-child {display: none !important;}
    
    /* Hide Streamlit Cloud profile link */
    a[href*="streamlit.io/author"] {display: none !important;}
    a[href*="share.streamlit.io"] {display: none !important;}
    
    /* Community Cloud "Hosted with Streamlit" badge */
    a[class*="viewerBadge_link__"] {display: none !important;}
    div[class*="viewerBadge_container__"] {display: none !important;}
    
    /* Fallback: any Streamlit-hosting anchor in bottom container */
    [data-testid="stBottomBlockContainer"] a[href*="streamlit.io"] {display: none !important;}
    
    /* Hide header completely */
    header[data-testid="stHeader"] {display: none !important;}
    
    /* Additional Streamlit Cloud specific hiding */
    div[data-testid="stHeader"] {display: none !important;}
    section[data-testid="stHeader"] {display: none !important;}
    
    /* Ensure header space is removed */
    .stApp > header {display: none !important;}
    </style>
    """,
    unsafe_allow_html=True,
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #2E8B57 0%, #228B22 100%);
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        text-align: center;
        color: white;
    }
    
    .auth-container {
        max-width: 400px;
        margin: 0 auto;
        padding: 2rem;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        background-color: #f8f9fa;
    }
    
    .sidebar-logo {
        text-align: center;
        padding: 1rem;
        margin-bottom: 2rem;
    }
    
    .nav-button {
        width: 100%;
        margin-bottom: 0.5rem;
        border-radius: 5px;
        border: none;
        padding: 0.5rem 1rem;
        background-color: #2E8B57;
        color: white;
        cursor: pointer;
    }
    
    .nav-button:hover {
        background-color: #228B22;
    }
    
    .footer {
        text-align: center;
        padding: 2rem;
        margin-top: 3rem;
        border-top: 1px solid #e0e0e0;
        color: #666;
    }
</style>
""", unsafe_allow_html=True)

# Authentication functions removed - no longer needed

def initialize_app():
    """Initialize the application"""
    # Initialize CropDrive integration first (if available)
    # This handles language and user config from parent website
    if CROPDRIVE_INTEGRATION_AVAILABLE:
        try:
            current_lang, user_plan, features = initialize_integration()
            # Language is set by integration, but ensure it's in session state
            if 'language' not in st.session_state:
                st.session_state.language = current_lang
            else:
                # Update language if changed via URL params
                st.session_state.language = current_lang
        except Exception as e:
            print(f"Warning: CropDrive integration failed: {e}")
            # Fallback to default
            if 'language' not in st.session_state:
                st.session_state.language = 'en'
    else:
        # Fallback: Initialize language from URL params manually
        try:
            query_params = st.query_params
            current_lang = query_params.get('lang', 'en')
            if current_lang not in ['en', 'ms']:
                current_lang = 'en'
            if 'language' not in st.session_state:
                st.session_state.language = current_lang
        except Exception:
            if 'language' not in st.session_state:
                st.session_state.language = 'en'
    
    # Initialize Firebase
    if not initialize_firebase():
        st.error(t('status_error', default='Error') + ": Failed to initialize Firebase. Please check your configuration.")
        st.stop()
    
    # Initialize admin codes
    default_admin_code = initialize_admin_codes()
    
    # Initialize session state
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 'home'

def show_header():
    """Display application header"""
    # Add Streamlit Cloud deploy button
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f"""
        <div class="main-header">
            <h1>🌴 {t('app_title')}</h1>
            <p>{t('app_subtitle')}</p>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        # Get GitHub repository URL from secrets or use default
        github_repo = 'Markishime/Ags-AI'  # Default repository
        try:
            if hasattr(st, 'secrets') and 'github' in st.secrets:
                github_repo = st.secrets.github.get('repository', github_repo)
            import os
            github_repo = os.getenv('GITHUB_REPOSITORY', github_repo)
        except Exception:
            pass
        
        # Official Streamlit Cloud deploy button
        st.markdown(f"""
        <div style="text-align: right; padding-top: 1rem;">
            <a href="https://share.streamlit.io/deploy?repository={github_repo}" target="_blank" style="text-decoration: none;">
                <img src="https://static.streamlit.io/badges/streamlit_badge_black_white.svg" 
                     alt="Deploy on Streamlit Cloud" 
                     style="height: 28px; opacity: 0.9; transition: opacity 0.3s;"
                     onmouseover="this.style.opacity='1'" 
                     onmouseout="this.style.opacity='0.9'">
            </a>
        </div>
        """, unsafe_allow_html=True)

def show_sidebar():
    """Display sidebar navigation"""
    with st.sidebar:
        # Logo and title
        st.markdown(f"""
        <div class="sidebar-logo">
            <h2>🌴 AGS AI</h2>
            <p>{t('app_subtitle')}</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.divider()
        
        # Navigation buttons
        if st.button(t('nav_home'), use_container_width=True):
            st.session_state.current_page = 'home'
            st.rerun()
        
        if st.button(t('nav_analyze'), use_container_width=True):
            st.session_state.current_page = 'upload'
            st.rerun()
        
        # Admin panel button
        if st.button(t('nav_admin'), use_container_width=True):
            st.session_state.current_page = 'admin'
            st.rerun()
        
        # Help Us Improve button
        if st.button(t('nav_help_improve'), use_container_width=True):
            st.session_state.current_page = 'help_improve'
            st.rerun()
       

def show_home_page():
    """Display home/landing page"""
    
    # Simple explanation of what the tool does
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"""
        <div style="background-color: #f8f9fa; padding: 2rem; border-radius: 10px; margin: 1rem 0; border-left: 4px solid #2E8B57;">
            <h3 style="color: #2E8B57; margin-top: 0;">{t('home_what_title')}</h3>
            <ul style="color: #333; line-height: 1.8;">
                <li>{t('home_what_1')}</li>
                <li>{t('home_what_2')}</li>
                <li>{t('home_what_3')}</li>
                <li>{t('home_what_4')}</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div style="background-color: #f8f9fa; padding: 2rem; border-radius: 10px; margin: 1rem 0; border-left: 4px solid #2E8B57;">
            <h3 style="color: #2E8B57; margin-top: 0;">{t('home_how_title')}</h3>
            <ol style="color: #333; line-height: 1.8;">
                <li>{t('home_how_1')}</li>
                <li>{t('home_how_2')}</li>
                <li>{t('home_how_3')}</li>
                <li>{t('home_how_4')}</li>
            </ol>
        </div>
        """, unsafe_allow_html=True)
    
    # Simple call to action
    st.markdown(f"""
    <div style="text-align: center; padding: 2rem; background: #f0f8ff; border-radius: 10px; margin: 2rem 0; border: 2px solid #2E8B57;">
        <h3 style="color: #2E8B57; margin-bottom: 1rem;">{t('home_ready')}</h3>
        <p style="color: #333; margin-bottom: 2rem;">{t('home_ready_desc')}</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Simple button to start
    if st.button(t('home_start'), use_container_width=True, type="primary"):
        st.session_state.current_page = 'upload'
        st.rerun()
    

# Authentication pages removed - no longer needed

# Settings page removed - authentication no longer required

def show_upload_page():
    """Display upload page"""
    try:
        from modules.upload import show_upload_page as upload_page
        upload_page()
    except ImportError:
        st.error(t('status_error') + ": " + t('upload_error', default='Upload module not available'))
        st.info(t('status_info') + ": " + t('upload_error', default='Please contact support if this issue persists.'))

def show_results_page():
    """Display results page"""
    if results_page_func is not None:
        results_page_func()
    else:
        st.error(t('status_error') + ": " + t('results_no_results', default='Results module not available'))
        st.info(t('status_info') + ": " + t('results_no_results', default='Please contact support if this issue persists.'))

def show_help_improve_page():
    """Display Help Us Improve page"""
    try:
        from modules.dashboard import display_help_us_improve_tab
        display_help_us_improve_tab()
    except ImportError:
        st.error(t('status_error') + ": Help Us Improve module not available")
        st.info(t('status_info') + ": Please contact support if this issue persists.")

def show_admin_panel():
    """Display admin panel"""
    if admin_panel_func is not None:
        admin_panel_func()
    else:
        st.error(t('status_error') + ": " + t('admin_restricted', default='Admin module not available'))
        st.info(t('status_info') + ": " + t('admin_restricted', default='Please contact support if this issue persists.'))

def main():
    """Main application function"""
    # Initialize the application
    initialize_app()
    
    # Show header
    show_header()
    
    # Show sidebar
    show_sidebar()
    
    # Route to appropriate page based on current_page
    current_page = st.session_state.current_page
    
    if current_page == 'home':
        show_home_page()
    elif current_page == 'upload':
        show_upload_page()
    elif current_page == 'results':
        if results_page_func is not None:
            results_page_func()
        else:
            st.error(t('status_error') + ": " + t('results_no_results'))
            st.info(t('status_info') + ": " + t('results_no_results', default='Please contact support if this issue persists.'))
    elif current_page == 'admin':
        if admin_panel_func is not None:
            admin_panel_func()
        else:
            st.error(t('status_error') + ": " + t('admin_restricted'))
            st.info(t('status_info') + ": " + t('admin_restricted', default='Please contact support if this issue persists.'))
    elif current_page == 'help_improve':
        show_help_improve_page()
    else:
        # Default to home if page not found
        st.session_state.current_page = 'home'
        show_home_page()
    
    # Footer
    st.markdown(f"""
    <div class="footer">
        <p>{t('footer_copyright')}</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()