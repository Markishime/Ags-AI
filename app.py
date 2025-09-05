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
        ## 🌴 Welcome to AGS AI Assistant
        
        **Advanced Oil Palm Cultivation Analysis System**
        
        Transform your oil palm cultivation with AI-powered analysis of SP LAB test reports. 
        Our system provides:
        
        ✅ **Accurate OCR Extraction** - Extract data from soil and leaf analysis reports  
        ✅ **MPOB Standards Compliance** - Compare against Malaysian Palm Oil Board standards  
        ✅ **AI-Powered Analysis** - Get intelligent insights and recommendations  
        ✅ **Comprehensive Reports** - Generate detailed PDF reports with forecasts  
        ✅ **Yield Optimization** - 5-year yield forecasting and economic analysis  
        ✅ **Expert Recommendations** - Fertilizer and management guidance  
        
        ### 🚀 Get Started
        
        1. **Register** for a free account
        2. **Upload** your SP LAB test report images
        3. **Analyze** with AI-powered insights
        4. **Download** comprehensive PDF reports
        5. **Optimize** your oil palm cultivation
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        ### 📊 System Features
        
        **🔬 Analysis Types:**
        - Soil Analysis Reports
        - Leaf Analysis Reports
        - Nutrient Deficiency Detection
        - pH Balance Assessment
        
        **📈 Insights Provided:**
        - Parameter Comparison
        - Issue Identification
        - Economic Impact Analysis
        - Yield Forecasting
        - Priority Actions
        
        **🎯 Benefits:**
        - Increased Yield
        - Reduced Costs
        - Better Decision Making
        - MPOB Compliance
        - Expert Guidance
        """, unsafe_allow_html=True)
    
    st.divider()
    
    # Survey Download Section
    st.markdown("---")
    st.markdown("## 📋 Oil Palm Farmer Survey")
    
    st.markdown("""
    <div style="background-color: #f0f8f0; padding: 1.5rem; border-radius: 10px; margin: 1rem 0;">
        <h4>📝 Complete This Survey Before Accessing Our System</h4>
        <p><strong>Purpose:</strong> This survey helps us understand your farming challenges and improve our AI-powered analysis system.</p>
        <p><strong>Instructions:</strong></p>
        <ol>
            <li>Download the survey form below</li>
            <li>Fill it out completely with your farming information</li>
            <li>Send the completed survey to: <strong>a.loladze@agriglobalsolutions.com</strong></li>
            <li>Once submitted, you can proceed to register and use our system</li>
        </ol>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Call to action
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("""
        <div style="text-align: center; padding: 2rem; background-color: #f0f8f0; border-radius: 10px; margin: 2rem 0;">
            <h3>🌟 Ready to Optimize Your Oil Palm Cultivation?</h3>
            <p>Join thousands of farmers using AGS AI Assistant</p>
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
    st.markdown("### 🎯 Why Choose AGS AI Assistant?")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        **🤖 AI-Powered Analysis**
        
        Advanced machine learning algorithms analyze your lab reports and provide 
        intelligent insights based on MPOB standards and best practices.
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        **📊 Comprehensive Reports**
        
        Get detailed PDF reports with visual charts, economic analysis, 
        yield forecasts, and actionable recommendations.
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        **🎯 Expert Guidance**
        
        Receive specific fertilizer recommendations, application rates, 
        and management practices tailored to your plantation needs.
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