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

# Import utilities
from firebase_config import initialize_firebase, initialize_admin_codes
from auth_utils import (
    login_user, register_user, reset_password, 
    logout_user, is_logged_in, is_admin, admin_signup, admin_signup_with_code
)
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
    from modules.dashboard import show_dashboard
except Exception:
    from dashboard import show_dashboard

try:
    from modules.upload import show_upload_page
except Exception:
    from upload import show_upload_page

from modules.results import show_results_page

from modules.history import show_history_page

from modules.admin import show_admin_panel

# Page configuration
st.set_page_config(
    page_title="AGS AI Assistant",
    page_icon="🌴",
    layout="wide",
    initial_sidebar_state="expanded"
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

def restore_authentication_state():
    """Restore authentication state from browser storage"""
    try:
        # Check if there's stored authentication data in query params
        auth_token = st.query_params.get('auth_token')
        user_id = st.query_params.get('user_id')
        user_email = st.query_params.get('user_email')
        
        if auth_token and user_id and user_email:
            # Restore authentication state
            st.session_state.authenticated = True
            st.session_state.user_id = user_id
            st.session_state.user_email = user_email
            st.session_state.user_name = st.query_params.get('user_name', '')
            st.session_state.user_role = st.query_params.get('user_role', 'user')
            
            # Reconstruct user_info
            st.session_state.user_info = {
                'uid': user_id,
                'email': user_email,
                'name': st.query_params.get('user_name', ''),
                'role': st.query_params.get('user_role', 'user')
            }
            
            # Clear query params to avoid showing them in URL
            st.query_params.clear()
            
    except Exception as e:
        pass  # Silently handle errors during restoration

def store_authentication_state(user_info):
    """Store authentication state persistently"""
    try:
        # Store user information in session state
        st.session_state.authenticated = True
        st.session_state.user_id = user_info.get('uid')
        st.session_state.user_email = user_info.get('email')
        st.session_state.user_name = user_info.get('name')
        st.session_state.user_role = user_info.get('role', 'user')
        st.session_state.user_info = user_info
        
        # Store authentication data in query params for persistence across page refreshes
        st.query_params.update({
            'auth_token': f"auth_{user_info.get('uid', '')}_{int(time.time())}",
            'user_id': user_info.get('uid', ''),
            'user_email': user_info.get('email', ''),
            'user_name': user_info.get('name', ''),
            'user_role': user_info.get('role', 'user')
        })
        
    except Exception as e:
        pass  # Silently handle errors during storage

def clear_authentication_state():
    """Clear authentication state and query params"""
    try:
        # Clear session state
        st.session_state.authenticated = False
        st.session_state.user_id = None
        st.session_state.user_email = None
        st.session_state.user_name = None
        st.session_state.user_role = 'user'
        st.session_state.user_info = None
        
        # Clear query params
        st.query_params.clear()
    except Exception as e:
        pass

def initialize_app():
    """Initialize the application"""
    # Initialize Firebase
    if not initialize_firebase():
        st.error("Failed to initialize Firebase. Please check your configuration.")
        st.stop()
    
    # Initialize admin codes
    default_admin_code = initialize_admin_codes()
    if default_admin_code:
        print("Default admin code initialized successfully")
    
    # Initialize session state
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'user_id' not in st.session_state:
        st.session_state.user_id = None
    if 'user_email' not in st.session_state:
        st.session_state.user_email = None
    if 'user_role' not in st.session_state:
        st.session_state.user_role = 'user'
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 'home'
    
    # Check for persistent authentication using browser session storage
    if not st.session_state.authenticated:
        # Try to restore authentication from browser storage
        restore_authentication_state()

def show_header():
    """Display application header"""
    st.markdown("""
    <div class="main-header">
        <h1>🌴 AGS AI Assistant</h1>
        <p>Advanced Oil Palm Cultivation Analysis System</p>
    </div>
    """, unsafe_allow_html=True)

def show_sidebar():
    """Display sidebar navigation"""
    with st.sidebar:
        # Logo and title
        st.markdown("""
        <div class="sidebar-logo">
            <h2>🌴 AGS AI</h2>
            <p>Smart Agriculture Assistant</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Check if user is logged in
        if st.session_state.authenticated:
            # User info
            st.success(f"Welcome, {st.session_state.user_email}!")
            st.write(f"Role: {st.session_state.user_role.title()}")
            
            st.divider()
            
            # Navigation buttons for authenticated users
            if st.button("🏠 Dashboard", use_container_width=True):
                st.session_state.current_page = 'dashboard'
                st.rerun()
            
            if st.button("📤 Analyze Files", use_container_width=True):
                st.session_state.current_page = 'upload'
                st.rerun()
            
            if st.button("📋 Analysis History", use_container_width=True):
                st.session_state.current_page = 'history'
                st.rerun()
            
            # Admin panel button for admin users
            if st.session_state.user_role == 'admin':
                if st.button("⚙️ Admin Panel", use_container_width=True):
                    st.session_state.current_page = 'admin'
                    st.rerun()
            
            st.divider()
            
            if st.button("🚪 Logout", use_container_width=True, type="secondary"):
                logout_user()
                clear_authentication_state()
                st.session_state.current_page = 'home'
                st.rerun()
        
        else:
            # Limited options for non-logged users
            if st.button("🔑 Login", use_container_width=True):
                st.session_state.current_page = 'login'
                st.rerun()
            
            if st.button("📝 Register", use_container_width=True):
                st.session_state.current_page = 'register'
                st.rerun()
            
            if st.button("🔧 Admin Registration", use_container_width=True):
                st.session_state.current_page = 'admin_register'
                st.rerun()
            
            
            st.divider()
            
            # Information for non-logged users
            st.info("📋 Please log in to access upload and analysis features.")
        
       

def show_home_page():
    """Display home/landing page"""
    # Hero section
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #2E8B57 0%, #228B22 50%, #32CD32 100%); padding: 2rem; border-radius: 15px; color: white; margin-bottom: 2rem; position: relative; overflow: hidden;">
            <div style="position: absolute; top: -20px; right: -20px; font-size: 8rem; opacity: 0.1;">🌴</div>
            <div style="position: absolute; bottom: -30px; left: -30px; font-size: 6rem; opacity: 0.1;">🤖</div>
            <h1 style="color: white; margin-bottom: 1rem; font-size: 2.5rem; text-shadow: 2px 2px 4px rgba(0,0,0,0.3);">🌴 AGS AI Assistant</h1>
            <h2 style="color: #f0f8ff; margin-bottom: 1.5rem; font-size: 1.5rem; text-shadow: 1px 1px 2px rgba(0,0,0,0.3);">AI-Powered Oil Palm Agriculture Intelligence</h2>
            <p style="font-size: 1.1rem; line-height: 1.6; margin-bottom: 0; text-shadow: 1px 1px 2px rgba(0,0,0,0.3);">Harness the power of artificial intelligence to revolutionize your oil palm cultivation. 
            Get precision analysis, smart recommendations, and optimize your plantation's potential with cutting-edge agricultural technology.</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        ## 🚀 Why Choose AGS AI Assistant?
        
        <div style="background-color: #f8f9fa; padding: 1.5rem; border-radius: 10px; margin: 1rem 0; border-left: 4px solid #28a745;">
            <h4 style="color: #28a745; margin-top: 0;">🎯 Precision Agriculture at Your Fingertips</h4>
            <p>Our AI-powered system analyzes your soil and leaf test reports with unmatched accuracy, 
            providing actionable insights to optimize your oil palm cultivation.</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        ### ✨ Key Features
        
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin: 1rem 0;">
            <div style="background: linear-gradient(45deg, #e8f5e8, #c8e6c9); padding: 1rem; border-radius: 8px; border-left: 4px solid #2E8B57; position: relative;">
                <div style="position: absolute; top: 0.5rem; right: 0.5rem; font-size: 1.5rem; opacity: 0.3;">🌱</div>
                <h5 style="color: #2E8B57; margin: 0 0 0.5rem 0;">🔬 Smart OCR Extraction</h5>
                <p style="margin: 0; font-size: 0.9rem;">Extract data from any SP LAB test report with 99%+ accuracy using advanced AI</p>
            </div>
            <div style="background: linear-gradient(45deg, #f0f8ff, #e6f3ff); padding: 1rem; border-radius: 8px; border-left: 4px solid #4169E1; position: relative;">
                <div style="position: absolute; top: 0.5rem; right: 0.5rem; font-size: 1.5rem; opacity: 0.3;">🤖</div>
                <h5 style="color: #4169E1; margin: 0 0 0.5rem 0;">📊 MPOB Compliance</h5>
                <p style="margin: 0; font-size: 0.9rem;">Compare against Malaysian Palm Oil Board standards with AI precision</p>
            </div>
            <div style="background: linear-gradient(45deg, #fff8dc, #f0e68c); padding: 1rem; border-radius: 8px; border-left: 4px solid #DAA520; position: relative;">
                <div style="position: absolute; top: 0.5rem; right: 0.5rem; font-size: 1.5rem; opacity: 0.3;">🌴</div>
                <h5 style="color: #DAA520; margin: 0 0 0.5rem 0;">🤖 AI-Powered Analysis</h5>
                <p style="margin: 0; font-size: 0.9rem;">Get intelligent insights and recommendations from agricultural AI</p>
            </div>
            <div style="background: linear-gradient(45deg, #ffe4e1, #ffb6c1); padding: 1rem; border-radius: 8px; border-left: 4px solid #DC143C; position: relative;">
                <div style="position: absolute; top: 0.5rem; right: 0.5rem; font-size: 1.5rem; opacity: 0.3;">📈</div>
                <h5 style="color: #DC143C; margin: 0 0 0.5rem 0;">📈 Yield Forecasting</h5>
                <p style="margin: 0; font-size: 0.9rem;">5-year yield projections and economic analysis powered by AI</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #2E8B57 0%, #32CD32 50%, #90EE90 100%); padding: 2rem; border-radius: 15px; color: white; margin-bottom: 2rem; position: relative; overflow: hidden;">
            <div style="position: absolute; top: -10px; right: -10px; font-size: 4rem; opacity: 0.2;">🌱</div>
            <div style="position: absolute; bottom: -10px; left: -10px; font-size: 3rem; opacity: 0.2;">🤖</div>
            <h3 style="color: white; margin-bottom: 1.5rem; text-align: center; text-shadow: 1px 1px 2px rgba(0,0,0,0.3);">🚀 AI Agriculture in 3 Steps</h3>
            <div style="text-align: center;">
                <div style="background: rgba(255,255,255,0.25); padding: 1rem; border-radius: 10px; margin: 1rem 0; border: 1px solid rgba(255,255,255,0.3);">
                    <h4 style="color: white; margin: 0 0 0.5rem 0;">1️⃣ Register</h4>
                    <p style="margin: 0; font-size: 0.9rem;">Create your AI agriculture account</p>
                </div>
                <div style="background: rgba(255,255,255,0.25); padding: 1rem; border-radius: 10px; margin: 1rem 0; border: 1px solid rgba(255,255,255,0.3);">
                    <h4 style="color: white; margin: 0 0 0.5rem 0;">2️⃣ Upload</h4>
                    <p style="margin: 0; font-size: 0.9rem;">Upload your oil palm test reports</p>
                </div>
                <div style="background: rgba(255,255,255,0.25); padding: 1rem; border-radius: 10px; margin: 1rem 0; border: 1px solid rgba(255,255,255,0.3);">
                    <h4 style="color: white; margin: 0 0 0.5rem 0;">3️⃣ Analyze</h4>
                    <p style="margin: 0; font-size: 0.9rem;">Get AI-powered agricultural insights</p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div style="background: linear-gradient(135deg, #f0f8ff 0%, #e6f3ff 100%); padding: 1.5rem; border-radius: 10px; border: 2px solid #2E8B57; position: relative;">
            <div style="position: absolute; top: 0.5rem; right: 0.5rem; font-size: 2rem; opacity: 0.3;">🌴</div>
            <h4 style="color: #2E8B57; margin-top: 0; text-align: center; font-weight: bold;">🤖 AI Agriculture Benefits</h4>
            <div style="display: flex; flex-direction: column; gap: 0.8rem;">
                <div style="display: flex; align-items: center; gap: 0.5rem; background: rgba(46, 139, 87, 0.1); padding: 0.5rem; border-radius: 5px;">
                    <span style="color: #2E8B57; font-size: 1.2rem;">🌱</span>
                    <span style="color: #2E8B57; font-weight: 500;">Smart PDF Reports</span>
                </div>
                <div style="display: flex; align-items: center; gap: 0.5rem; background: rgba(46, 139, 87, 0.1); padding: 0.5rem; border-radius: 5px;">
                    <span style="color: #2E8B57; font-size: 1.2rem;">📈</span>
                    <span style="color: #2E8B57; font-weight: 500;">AI Yield Forecasting</span>
                </div>
                <div style="display: flex; align-items: center; gap: 0.5rem; background: rgba(46, 139, 87, 0.1); padding: 0.5rem; border-radius: 5px;">
                    <span style="color: #2E8B57; font-size: 1.2rem;">💰</span>
                    <span style="color: #2E8B57; font-weight: 500;">Economic Analysis</span>
                </div>
                <div style="display: flex; align-items: center; gap: 0.5rem; background: rgba(46, 139, 87, 0.1); padding: 0.5rem; border-radius: 5px;">
                    <span style="color: #2E8B57; font-size: 1.2rem;">🎯</span>
                    <span style="color: #2E8B57; font-weight: 500;">AI Recommendations</span>
                </div>
                <div style="display: flex; align-items: center; gap: 0.5rem; background: rgba(46, 139, 87, 0.1); padding: 0.5rem; border-radius: 5px;">
                    <span style="color: #2E8B57; font-size: 1.2rem;">📊</span>
                    <span style="color: #2E8B57; font-weight: 500;">MPOB Compliance</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    st.divider()
    
    
    # Call to action
    st.markdown("""
    <div style="text-align: center; padding: 3rem; background: linear-gradient(135deg, #2E8B57 0%, #32CD32 50%, #90EE90 100%); border-radius: 15px; margin: 2rem 0; color: white; position: relative; overflow: hidden;">
        <div style="position: absolute; top: -20px; right: -20px; font-size: 6rem; opacity: 0.1;">🌴</div>
        <div style="position: absolute; bottom: -30px; left: -30px; font-size: 8rem; opacity: 0.1;">🤖</div>
        <h2 style="color: white; margin-bottom: 1rem; text-shadow: 2px 2px 4px rgba(0,0,0,0.3);">🌟 Ready to Revolutionize Your Oil Palm Agriculture?</h2>
        <p style="font-size: 1.2rem; margin-bottom: 2rem; text-shadow: 1px 1px 2px rgba(0,0,0,0.3);">Join the AI agriculture revolution and maximize your oil palm yield with cutting-edge technology</p>
        <div style="display: flex; gap: 1rem; justify-content: center; flex-wrap: wrap;">
            <div style="background: rgba(255,255,255,0.25); padding: 1rem 2rem; border-radius: 25px; border: 2px solid rgba(255,255,255,0.4); backdrop-filter: blur(10px);">
                <h4 style="color: white; margin: 0 0 0.5rem 0;">🚀 Start AI Agriculture</h4>
                <p style="margin: 0; font-size: 0.9rem;">Free AI-powered analysis</p>
            </div>
            <div style="background: rgba(255,255,255,0.25); padding: 1rem 2rem; border-radius: 25px; border: 2px solid rgba(255,255,255,0.4); backdrop-filter: blur(10px);">
                <h4 style="color: white; margin: 0 0 0.5rem 0;">📊 Instant AI Analysis</h4>
                <p style="margin: 0; font-size: 0.9rem;">Get AI insights in minutes</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    col_a, col_b = st.columns(2)
    
    with col_a:
        if st.button("🔑 Login to Your Account", use_container_width=True, type="primary"):
            st.session_state.current_page = 'login'
            st.rerun()
    
    with col_b:
        if st.button("📝 Create New Account", use_container_width=True):
            st.session_state.current_page = 'register'
            st.rerun()
    
    # Features showcase
    st.markdown("""
    <div style="background: linear-gradient(135deg, #2E8B57 0%, #32CD32 50%, #90EE90 100%); padding: 2rem; border-radius: 15px; color: white; margin: 2rem 0; position: relative; overflow: hidden;">
        <div style="position: absolute; top: -20px; right: -20px; font-size: 6rem; opacity: 0.1;">🌱</div>
        <div style="position: absolute; bottom: -30px; left: -30px; font-size: 8rem; opacity: 0.1;">🤖</div>
        <h3 style="color: white; text-align: center; margin-bottom: 2rem; text-shadow: 2px 2px 4px rgba(0,0,0,0.3);">🎯 Why Choose AI Agriculture?</h3>
        <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 2rem;">
            <div style="background: rgba(255,255,255,0.2); padding: 1.5rem; border-radius: 10px; text-align: center; border: 1px solid rgba(255,255,255,0.3); backdrop-filter: blur(10px);">
                <h4 style="color: #ffd700; margin: 0 0 1rem 0; text-shadow: 1px 1px 2px rgba(0,0,0,0.3);">🔬 AI Precision Analysis</h4>
                <p style="margin: 0; font-size: 0.9rem; text-shadow: 1px 1px 2px rgba(0,0,0,0.3);">Advanced AI algorithms provide accurate analysis of your oil palm test reports with 99%+ accuracy using machine learning.</p>
            </div>
            <div style="background: rgba(255,255,255,0.2); padding: 1.5rem; border-radius: 10px; text-align: center; border: 1px solid rgba(255,255,255,0.3); backdrop-filter: blur(10px);">
                <h4 style="color: #ffd700; margin: 0 0 1rem 0; text-shadow: 1px 1px 2px rgba(0,0,0,0.3);">📈 Smart Yield Optimization</h4>
                <p style="margin: 0; font-size: 0.9rem; text-shadow: 1px 1px 2px rgba(0,0,0,0.3);">Get AI-powered 5-year yield forecasts and economic analysis to maximize your oil palm plantation's potential.</p>
            </div>
            <div style="background: rgba(255,255,255,0.2); padding: 1.5rem; border-radius: 10px; text-align: center; border: 1px solid rgba(255,255,255,0.3); backdrop-filter: blur(10px);">
                <h4 style="color: #ffd700; margin: 0 0 1rem 0; text-shadow: 1px 1px 2px rgba(0,0,0,0.3);">🎯 AI Expert Guidance</h4>
                <p style="margin: 0; font-size: 0.9rem; text-shadow: 1px 1px 2px rgba(0,0,0,0.3);">Receive personalized AI recommendations based on MPOB standards and agricultural best practices.</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Final CTA
    st.markdown("""
    <div style="text-align: center; padding: 2rem; background: linear-gradient(135deg, #f0f8ff 0%, #e6f3ff 100%); border-radius: 15px; margin: 2rem 0; border: 3px solid #2E8B57; position: relative; overflow: hidden;">
        <div style="position: absolute; top: -10px; right: -10px; font-size: 4rem; opacity: 0.1;">🌴</div>
        <div style="position: absolute; bottom: -10px; left: -10px; font-size: 3rem; opacity: 0.1;">🤖</div>
        <h3 style="color: #2E8B57; margin-bottom: 1rem; font-weight: bold;">🚀 Ready to Start AI Agriculture?</h3>
        <p style="color: #2E8B57; margin-bottom: 2rem; font-weight: 500;">Transform your oil palm cultivation today with cutting-edge AI technology</p>
        <div style="display: flex; gap: 1rem; justify-content: center; flex-wrap: wrap;">
            <div style="background: linear-gradient(45deg, #2E8B57, #32CD32); padding: 0.8rem 2rem; border-radius: 25px; color: white; font-weight: bold; box-shadow: 0 4px 8px rgba(46, 139, 87, 0.3);">
                🌱 Upload Your Oil Palm Report
            </div>
            <div style="background: linear-gradient(45deg, #4169E1, #32CD32); padding: 0.8rem 2rem; border-radius: 25px; color: white; font-weight: bold; box-shadow: 0 4px 8px rgba(65, 105, 225, 0.3);">
                🤖 Get AI Analysis
            </div>
            <div style="background: linear-gradient(45deg, #DAA520, #2E8B57); padding: 0.8rem 2rem; border-radius: 25px; color: white; font-weight: bold; box-shadow: 0 4px 8px rgba(218, 165, 32, 0.3);">
                📈 Maximize Your Yield
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    

def show_login_page():
    """Display login page"""
    st.markdown("""
    <div class="auth-container">
    """, unsafe_allow_html=True)
    
    st.subheader("🔑 Login to Your Account")
    
    with st.form("login_form"):
        email = st.text_input("📧 Email", placeholder="Enter your email")
        password = st.text_input("🔒 Password", type="password", placeholder="Enter your password")
        
        col1, col2 = st.columns(2)
        
        with col1:
            login_button = st.form_submit_button("🔑 Login", use_container_width=True, type="primary")
        
        with col2:
            if st.form_submit_button("🔙 Back to Home", use_container_width=True):
                st.session_state.current_page = 'home'
                st.rerun()
    
    if login_button:
        if email and password:
            with st.spinner("Logging in..."):
                result = login_user(email, password)
                if result.get('success', False):
                    # Store user information persistently
                    user_info = result.get('user_info', {})
                    store_authentication_state(user_info)
                    
                    st.success("Login successful!")
                    
                    # Redirect based on user role
                    if user_info.get('role') == 'admin':
                        st.session_state.current_page = 'admin'
                    else:
                        st.session_state.current_page = 'dashboard'
                    
                    st.rerun()
                else:
                    st.error(result.get('message', 'Invalid email or password. Please try again.'))
        else:
            st.error("Please enter both email and password.")
    
    st.divider()
    
    # Additional options
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📝 Create Account", use_container_width=True):
            st.session_state.current_page = 'register'
            st.rerun()
    
    with col2:
        if st.button("🔄 Forgot Password", use_container_width=True):
            st.session_state.current_page = 'forgot_password'
            st.rerun()
    
    st.markdown("</div>", unsafe_allow_html=True)

def show_register_page():
    """Display registration page"""
    st.markdown("""
    <div class="auth-container">
    """, unsafe_allow_html=True)
    
    st.subheader("📝 Create Your Account")
    
    with st.form("register_form"):
        name = st.text_input("👤 Full Name", placeholder="Enter your full name")
        email = st.text_input("📧 Email", placeholder="Enter your email")
        password = st.text_input("🔒 Password", type="password", placeholder="Create a password")
        confirm_password = st.text_input("🔒 Confirm Password", type="password", placeholder="Confirm your password")
        
        # Additional fields
        company = st.text_input("🏢 Company/Organization (Optional)", placeholder="Your company name")
        
        # Terms and conditions
        agree_terms = st.checkbox("I agree to the Terms of Service and Privacy Policy")
        
        col1, col2 = st.columns(2)
        
        with col1:
            register_button = st.form_submit_button("📝 Create Account", use_container_width=True, type="primary")
        
        with col2:
            if st.form_submit_button("🔙 Back to Home", use_container_width=True):
                st.session_state.current_page = 'home'
                st.rerun()
    
    if register_button:
        if not agree_terms:
            st.error("Please agree to the Terms of Service and Privacy Policy.")
        elif not all([name, email, password, confirm_password]):
            st.error("Please fill in all required fields.")
        elif password != confirm_password:
            st.error("Passwords do not match.")
        elif len(password) < 6:
            st.error("Password must be at least 6 characters long.")
        else:
            with st.spinner("Creating account..."):
                if register_user(email, password, name, company, ""):
                    st.success("Account created successfully! Please log in.")
                    st.session_state.current_page = 'login'
                    st.rerun()
                else:
                    st.error("Failed to create account. Email may already be in use.")
    
    st.divider()
    
    # Link to login
    if st.button("🔑 Already have an account? Login", use_container_width=True):
        st.session_state.current_page = 'login'
        st.rerun()
    
    st.markdown("</div>", unsafe_allow_html=True)

def show_admin_register_page():
    """Display admin registration page"""
    st.markdown("""
    <div class="auth-container">
    """, unsafe_allow_html=True)
    
    st.subheader("🔧 Create Admin Account")
    st.info("Register as an administrator to access advanced system features.")
    
    with st.form("admin_register_form"):
        name = st.text_input("👤 Full Name *", placeholder="Enter your full name")
        email = st.text_input("📧 Email *", placeholder="Enter your email")
        password = st.text_input("🔒 Password *", type="password", placeholder="Create a password (min 8 characters)")
        confirm_password = st.text_input("🔒 Confirm Password *", type="password", placeholder="Confirm your password")
        
        # Required admin code field
        admin_code = st.text_input("🔑 Admin Code *", type="password", placeholder="Enter admin access code")
        
        # Optional organization field
        organization = st.text_input("🏢 Organization (Optional)", placeholder="Your organization name")
        
        # Terms and conditions
        agree_terms = st.checkbox("I agree to the Terms of Service and Privacy Policy *")
        
        col1, col2 = st.columns(2)
        
        with col1:
            register_button = st.form_submit_button("🔧 Create Admin Account", use_container_width=True, type="primary")
        
        with col2:
            if st.form_submit_button("🔙 Back to Home", use_container_width=True):
                st.session_state.current_page = 'home'
                st.rerun()
    
    if register_button:
        # Form validation
        if not agree_terms:
            st.error("Please agree to the Terms of Service and Privacy Policy.")
        elif not all([name.strip(), email.strip(), password, confirm_password, admin_code.strip()]):
            st.error("Please fill in all required fields (marked with *).")
        elif password != confirm_password:
            st.error("Passwords do not match.")
        elif len(password) < 8:
            st.error("Password must be at least 8 characters long.")
        elif not '@' in email or not '.' in email:
            st.error("Please enter a valid email address.")
        else:
            with st.spinner("Creating admin account..."):
                result = admin_signup_with_code(email, password, name, organization, admin_code)
                
                if result.get('success', False):
                    st.success("Admin account created successfully! You can now log in.")
                    st.session_state.current_page = 'login'
                    st.rerun()
                else:
                    st.error(result.get('message', 'Failed to create admin account.'))
    
    st.divider()
    
    # Links to other pages
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔑 Already have an account? Login", use_container_width=True):
            st.session_state.current_page = 'login'
            st.rerun()
    
    with col2:
        if st.button("📝 Register as User", use_container_width=True):
            st.session_state.current_page = 'register'
            st.rerun()
    
    st.markdown("</div>", unsafe_allow_html=True)

def show_forgot_password_page():
    """Display forgot password page"""
    st.markdown("""
    <div class="auth-container">
    """, unsafe_allow_html=True)
    
    st.subheader("🔄 Reset Your Password")
    
    st.info("Enter your email address and we'll send you instructions to reset your password.")
    
    with st.form("forgot_password_form"):
        email = st.text_input("📧 Email", placeholder="Enter your email")
        
        col1, col2 = st.columns(2)
        
        with col1:
            reset_button = st.form_submit_button("🔄 Send Reset Link", use_container_width=True, type="primary")
        
        with col2:
            if st.form_submit_button("🔙 Back to Login", use_container_width=True):
                st.session_state.current_page = 'login'
                st.rerun()
    
    if reset_button:
        if email:
            with st.spinner("Sending reset link..."):
                if reset_password(email):
                    st.success("Password reset link sent to your email!")
                else:
                    st.error("Failed to send reset link. Please check your email address.")
        else:
            st.error("Please enter your email address.")
    
    st.markdown("</div>", unsafe_allow_html=True)

def show_settings_page():
    """Display user settings page"""
    st.title("⚙️ Account Settings")
    
    # User profile settings
    st.subheader("👤 Profile Information")
    
    # This would load current user data from Firebase
    with st.form("profile_form"):
        name = st.text_input("Full Name", value="John Doe")
        email = st.text_input("Email", value=st.session_state.user_email, disabled=True)
        company = st.text_input("Company/Organization", value="")
        phone = st.text_input("Phone Number", value="")
        location = st.text_input("Location", value="")
        
        if st.form_submit_button("💾 Save Changes", type="primary"):
            st.success("Profile updated successfully!")
    
    st.divider()
    
    # Notification preferences
    st.subheader("🔔 Notification Preferences")
    
    email_notifications = st.checkbox("Email notifications for analysis completion", value=True)
    weekly_summary = st.checkbox("Weekly analysis summary", value=False)
    system_updates = st.checkbox("System updates and announcements", value=True)
    
    if st.button("💾 Save Notification Preferences", type="primary"):
        st.success("Notification preferences saved!")
    
    st.divider()
    
    # Security settings
    st.subheader("🔒 Security")
    
    if st.button("🔄 Change Password", use_container_width=True):
        st.info("Password change functionality would be implemented here.")
    
    if st.button("🗑️ Delete Account", use_container_width=True, type="secondary"):
        st.warning("Account deletion functionality would be implemented here.")

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
    elif current_page == 'login':
        show_login_page()
    elif current_page == 'register':
        show_register_page()
    elif current_page == 'admin_register':
        show_admin_register_page()
    elif current_page == 'forgot_password':
        show_forgot_password_page()
    elif current_page == 'upload':
        # Require authentication for upload/analyze functionality
        if st.session_state.authenticated:
            show_upload_page()
        else:
            st.warning("🔒 Please log in to upload and analyze files.")
            st.session_state.current_page = 'login'
            show_login_page()
    elif current_page == 'results':
        # Require authentication for results functionality
        if st.session_state.authenticated:
            show_results_page()
        else:
            st.warning("🔒 Please log in to view analysis results.")
            st.session_state.current_page = 'login'
            show_login_page()
    elif current_page == 'history':
        # Require authentication for history functionality
        if st.session_state.authenticated:
            show_history_page()
        else:
            st.warning("🔒 Please log in to view analysis history.")
            st.session_state.current_page = 'login'
            show_login_page()
    elif current_page == 'dashboard' and st.session_state.authenticated:
        show_dashboard()
    elif current_page == 'admin' and st.session_state.authenticated and is_admin(st.session_state.user_id):
        show_admin_panel()
    elif current_page == 'settings' and st.session_state.authenticated:
        show_settings_page()
    else:
        # Default to home if page not found or not authenticated for restricted pages
        if current_page in ['dashboard', 'admin', 'settings'] and not st.session_state.authenticated:
            st.warning("🔒 Please log in to access this page.")
            st.session_state.current_page = 'login'
            show_login_page()
        else:
            st.session_state.current_page = 'home'
            show_home_page()
    
    # Footer
    st.markdown("""
    <div class="footer">
        <p>© 2025 AGS AI Assistant | Advanced Oil Palm Cultivation Analysis System</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()