import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, List, Any, Optional
import sys
import os
import json
import numpy as np

# Add utils to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'utils'))

from utils.firebase_config import get_firestore_client, COLLECTIONS
from utils.auth_utils import get_all_users, is_admin, get_user_by_id
from utils.ai_config_utils import load_ai_configuration, save_ai_configuration, reset_ai_configuration, validate_prompt_template

def show_admin_panel():
    """Display admin panel"""
    st.title("🔧 Admin Panel")
    
    # Check if user is logged in and is admin
    if 'user_id' not in st.session_state:
        st.error("Please log in to access the admin panel.")
        return
    
    user_id = st.session_state['user_id']
    
    if not is_admin(user_id):
        st.error("Access denied. Admin privileges required.")
        return
    
    # Admin navigation
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Dashboard", 
        "👥 User Management", 
        "🤖 AI Configuration", 
        "📈 System Analytics", 
        "⚙️ Settings"
    ])
    
    with tab1:
        show_admin_dashboard()
    
    with tab2:
        show_user_management()
    
    with tab3:
        show_ai_configuration()
    
    with tab4:
        st.info("System Analytics - Coming Soon")
    
    with tab5:
        st.info("Settings - Coming Soon")

def show_admin_dashboard():
    """Display admin dashboard with system overview"""
    st.header("📊 System Dashboard")
    
    # Get system statistics
    stats = get_system_statistics()
    
    # Display key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Total Users",
            value=stats['total_users'],
            delta=f"+{stats['new_users_today']} today"
        )
    
    with col2:
        st.metric(
            label="Active Users (7d)",
            value=stats['active_users_7d'],
            delta=f"{stats['active_users_change']}% vs last week"
        )
    
    with col3:
        st.metric(
            label="Total Analyses",
            value=stats['total_analyses'],
            delta=f"+{stats['analyses_today']} today"
        )
    
    with col4:
        st.metric(
            label="System Health",
            value="Healthy" if stats['system_health'] > 0.9 else "Warning",
            delta=f"{stats['system_health']:.1%} uptime"
        )
    
    # Display charts
    col1, col2 = st.columns(2)
    
    with col1:
        display_usage_trends()
    
    with col2:
        display_system_health()
    
    # Recent activity
    st.subheader("Recent System Issues")
    display_recent_system_issues()

def get_system_statistics() -> Dict[str, Any]:
    """Get system statistics for dashboard"""
    try:
        db = get_firestore_client()
        
        # Get user statistics
        users_ref = db.collection(COLLECTIONS['users'])
        total_users = len(list(users_ref.stream()))
        
        # Mock data for demonstration
        return {
            'total_users': total_users,
            'new_users_today': 2,
            'active_users_7d': 45,
            'active_users_change': 12,
            'total_analyses': 156,
            'analyses_today': 8,
            'system_health': 0.95
        }
    except Exception as e:
        st.error(f"Error getting system statistics: {str(e)}")
        return {
            'total_users': 0,
            'new_users_today': 0,
            'active_users_7d': 0,
            'active_users_change': 0,
            'total_analyses': 0,
            'analyses_today': 0,
            'system_health': 0.0
        }

def display_usage_trends():
    """Display usage trends chart"""
    st.subheader("Usage Trends")
    
    # Mock data for demonstration
    dates = pd.date_range(start='2024-01-01', end='2024-01-31', freq='D')
    usage_data = pd.DataFrame({
        'Date': dates,
        'Daily Active Users': [20 + i*2 + np.random.randint(-5, 5) for i in range(len(dates))],
        'Analyses Created': [5 + i + np.random.randint(-2, 2) for i in range(len(dates))]
    })
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=usage_data['Date'],
        y=usage_data['Daily Active Users'],
        mode='lines+markers',
        name='Daily Active Users',
        line=dict(color='#1f77b4')
    ))
    
    fig.add_trace(go.Scatter(
        x=usage_data['Date'],
        y=usage_data['Analyses Created'],
        mode='lines+markers',
        name='Analyses Created',
        yaxis='y2',
        line=dict(color='#ff7f0e')
    ))
    
    fig.update_layout(
        xaxis_title='Date',
        yaxis=dict(title='Daily Active Users', side='left'),
        yaxis2=dict(title='Analyses Created', side='right', overlaying='y'),
        height=400,
        showlegend=True
    )
    
    st.plotly_chart(fig, use_container_width=True)

def display_recent_system_issues():
    """Display recent system issues"""
    # Mock data for demonstration
    issues = [
        {
            'timestamp': datetime.now() - timedelta(hours=2),
            'level': 'Warning',
            'message': 'High memory usage detected on analysis server',
            'status': 'Resolved'
        },
        {
            'timestamp': datetime.now() - timedelta(hours=6),
            'level': 'Info',
            'message': 'Scheduled maintenance completed successfully',
            'status': 'Completed'
        },
        {
            'timestamp': datetime.now() - timedelta(days=1),
            'level': 'Error',
            'message': 'Database connection timeout (resolved automatically)',
            'status': 'Resolved'
        }
    ]
    
    for issue in issues:
        col1, col2, col3, col4 = st.columns([2, 1, 4, 1])
        
        with col1:
            st.write(issue['timestamp'].strftime('%Y-%m-%d %H:%M'))
        
        with col2:
            if issue['level'] == 'Error':
                st.error(issue['level'])
            elif issue['level'] == 'Warning':
                st.warning(issue['level'])
            else:
                st.info(issue['level'])
        
        with col3:
            st.write(issue['message'])
        
        with col4:
            if issue['status'] == 'Resolved':
                st.success(issue['status'])
            else:
                st.info(issue['status'])

def display_system_health():
    """Display system health metrics"""
    st.subheader("System Health")
    
    # Mock health data
    health_metrics = {
        'CPU Usage': 45,
        'Memory Usage': 62,
        'Disk Usage': 38,
        'Network I/O': 25
    }
    
    for metric, value in health_metrics.items():
        st.metric(
            label=metric,
            value=f"{value}%",
            delta=f"{-2 if value < 50 else 3}% vs last hour"
        )
        
        # Progress bar
        if value < 50:
            st.progress(value / 100)
        elif value < 80:
            st.warning(f"{metric}: {value}%")
        else:
            st.error(f"{metric}: {value}%")

def show_user_management():
    """Display user management interface"""
    st.header("👥 User Management")
    
    try:
        # Get all users
        users = get_all_users()
        
        if users:
            st.success(f"Found {len(users)} users")
            
            # Create a DataFrame for better display
            user_data = []
            for user in users:
                user_data.append({
                    'Email': user.get('email', 'N/A'),
                    'Name': user.get('name', 'N/A'),
                    'Role': user.get('role', 'user'),
                    'Created': user.get('created_at', 'N/A'),
                    'Last Login': user.get('last_login', 'N/A')
                })
            
            df = pd.DataFrame(user_data)
            st.dataframe(df, use_container_width=True)
            
            # User actions
            st.subheader("User Actions")
            col1, col2 = st.columns(2)
            
            with col1:
                selected_email = st.selectbox(
                    "Select User",
                    options=[user.get('email', 'N/A') for user in users],
                    key="user_select"
                )
            
            with col2:
                if st.button("View User Details"):
                    selected_user = next((u for u in users if u.get('email') == selected_email), None)
                    if selected_user:
                        st.json(selected_user)
        
        else:
            st.info("No users found")
    
    except Exception as e:
        st.error(f"Error loading users: {str(e)}")

def show_ai_configuration():
    """Display AI configuration interface"""
    st.header("🤖 AI Configuration")
    
    # Configuration tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📝 Prompt Templates",
        "📚 Reference Materials", 
        "🎨 Output Formatting",
        "🏷️ Tagging System",
        "⚙️ Advanced Settings"
    ])
    
    with tab1:
        show_prompt_templates_config()
    
    with tab2:
        show_reference_materials_config()
    
    with tab3:
        show_output_formatting_config()
    
    with tab4:
        show_tagging_config()
    
    with tab5:
        show_advanced_settings_config()

def get_analysis_prompts() -> List[Dict[str, Any]]:
    """Get all analysis prompts from Firestore"""
    try:
        db = get_firestore_client()
        prompts_ref = db.collection('analysis_prompts')
        docs = prompts_ref.stream()
        
        prompts = []
        for doc in docs:
            prompt_data = doc.to_dict()
            prompt_data['id'] = doc.id
            prompts.append(prompt_data)
        
        return prompts
    
    except Exception as e:
        st.error(f"Error loading prompts: {str(e)}")
        return []

def get_active_prompt() -> Optional[Dict[str, Any]]:
    """Get the currently active prompt"""
    try:
        db = get_firestore_client()
        prompts_ref = db.collection('analysis_prompts')
        active_query = prompts_ref.where('is_active', '==', True).limit(1)
        active_docs = list(active_query.stream())
        
        if active_docs:
            prompt_data = active_docs[0].to_dict()
            prompt_data['id'] = active_docs[0].id
            return prompt_data
        return None
    
    except Exception as e:
        st.error(f"Error getting active prompt: {str(e)}")
        return None

def save_prompt(prompt_data: Dict[str, Any], prompt_id: str = None) -> bool:
    """Save or update a prompt in Firestore"""
    try:
        db = get_firestore_client()
        prompts_ref = db.collection('analysis_prompts')
        
        # Add metadata
        prompt_data['updated_at'] = datetime.now()
        prompt_data['updated_by'] = st.session_state.get('user_id', 'system')
        
        if prompt_id:
            # Update existing prompt
            prompts_ref.document(prompt_id).update(prompt_data)
        else:
            # Create new prompt
            prompt_data['created_at'] = datetime.now()
            prompts_ref.add(prompt_data)
        
        return True
        
    except Exception as e:
        st.error(f"Error saving prompt: {str(e)}")
        return False

def set_active_prompt(prompt_id: str) -> bool:
    """Set a prompt as active and deactivate all others"""
    try:
        db = get_firestore_client()
        prompts_ref = db.collection('analysis_prompts')
        
        # Deactivate all prompts
        all_prompts = prompts_ref.stream()
        batch = db.batch()
        
        for doc in all_prompts:
            batch.update(doc.reference, {'is_active': False})
        
        # Activate the selected prompt
        target_doc = prompts_ref.document(prompt_id)
        batch.update(target_doc, {'is_active': True})
        
        batch.commit()
        return True
    
    except Exception as e:
        st.error(f"Error setting active prompt: {str(e)}")
        return False

def delete_prompt(prompt_id: str) -> bool:
    """Delete a prompt from Firestore"""
    try:
        db = get_firestore_client()
        prompts_ref = db.collection('analysis_prompts')
        prompts_ref.document(prompt_id).delete()
        return True
    
    except Exception as e:
        st.error(f"Error deleting prompt: {str(e)}")
        return False

def get_reference_documents() -> List[Dict[str, Any]]:
    """Get all reference documents from Firestore"""
    try:
        db = get_firestore_client()
        docs_ref = db.collection('reference_documents')
        docs = docs_ref.stream()
        
        documents = []
        for doc in docs:
            doc_data = doc.to_dict()
            doc_data['id'] = doc.id
            documents.append(doc_data)
        
        return documents
    
    except Exception as e:
        st.error(f"Error loading reference documents: {str(e)}")
        return []

def save_reference_document(doc_data: Dict[str, Any], doc_id: str = None) -> bool:
    """Save or update a reference document in Firestore"""
    try:
        db = get_firestore_client()
        docs_ref = db.collection('reference_documents')
        
        # Add metadata
        doc_data['updated_at'] = datetime.now()
        doc_data['updated_by'] = st.session_state.get('user_id', 'system')
        
        if doc_id:
            # Update existing document
            docs_ref.document(doc_id).update(doc_data)
        else:
            # Create new document
            doc_data['created_at'] = datetime.now()
            docs_ref.add(doc_data)
        
        return True
    
    except Exception as e:
        st.error(f"Error saving reference document: {str(e)}")
        return False

def delete_reference_document(doc_id: str) -> bool:
    """Delete a reference document from Firestore"""
    try:
        db = get_firestore_client()
        docs_ref = db.collection('reference_documents')
        docs_ref.document(doc_id).delete()
        return True
    
    except Exception as e:
        st.error(f"Error deleting reference document: {str(e)}")
        return False

def show_prompt_templates_config():
    """Show prompt templates configuration for Firestore analysis_prompts collection"""
    st.subheader("📝 Prompt Templates Management")
    
    # Get all prompts from Firestore
    prompts = get_analysis_prompts()
    active_prompt = get_active_prompt()
    
    # Display current active prompt
    col1, col2 = st.columns([3, 1])
    with col1:
        if active_prompt:
            st.success(f"🎯 **Currently Active:** {active_prompt.get('name', 'Unknown')}")
            st.info(f"📝 **Description:** {active_prompt.get('description', 'No description')}")
        else:
            st.warning("⚠️ **No active prompt set** - Analysis will use default prompts")
    
    with col2:
        if st.button("🔄 Refresh", key="refresh_prompts"):
            st.rerun()
    
    st.divider()
    
    # Create new prompt section
    with st.expander("➕ Create New Prompt Template", expanded=False):
        with st.form("new_prompt_form"):
            st.write("**Create New Analysis Prompt**")
            
            col1, col2 = st.columns(2)
            with col1:
                new_name = st.text_input("Prompt Name *", placeholder="e.g., Comprehensive Soil Analysis")
                new_description = st.text_input("Description", placeholder="Brief description of this prompt")
            
            with col2:
                new_is_active = st.checkbox("Set as active prompt", value=False)
                new_version = st.text_input("Version", value="1.0", placeholder="1.0")
            
            new_prompt_text = st.text_area(
                "Complete Analysis Prompt *",
                height=600,
                value="""You are an expert agricultural consultant specializing in oil palm cultivation and nutrition analysis in Malaysia.

Based on the following lab analysis data and MPOB standards, provide a comprehensive analysis following these EXACT steps:

Lab Data:
{lab_data}

Report Type: {report_type}

MPOB Standards:
{mpob_standards}

You MUST follow these steps in order and provide detailed analysis for each:

Step 1: Analyze the Uploaded Data
For each uploaded report, extract and interpret the following:
Soil Test Parameters (if provided):
- pH (acidity/alkalinity)
- Cation Exchange Capacity (CEC)
- Base Saturation percentages for Ca, Mg, K, and Na
- Exchangeable nutrients: Ca, Mg, K, Na
- Available Phosphorus (Olsen P or Bray P, depending on pH)
- Total Nitrogen (N)
- Organic Matter or Organic Carbon
- Optional: Boron (B), Copper (Cu), Zinc (Zn), Manganese (Mn), Iron (Fe), Aluminium (Al), soil texture

Leaf Tissue Test Parameters (if provided):
- Nitrogen (N), Phosphorus (P), Potassium (K), Calcium (Ca), Magnesium (Mg)
- Optional: Boron (B), Copper (Cu), Zinc (Zn), Chloride (Cl)

Yield and Land Size Data (if provided):
- Prior year(s) yield in tons per hectare
- Total land area in hectares

Interpretation:
- Compare measured nutrient levels to Malaysian oil palm agronomic standards
- Provide nutrient ratio assessments (K:Mg, Ca:Mg, and others where relevant)
- Prepare visual aids: Bar charts (actual vs optimal nutrient levels), Diagrams of nutrient ratios

Step 2: Diagnose Agronomic Issues
Identify:
- Deficiencies or excesses
- Nutrient imbalances
- Soil degradation or limiting factors

For each detected problem:
- Explain likely cause (e.g., acidic pH reducing phosphorus availability, K-Mg antagonism, sodium toxicity)
- Provide a visual comparison between current nutrient status and standards

Step 3: Recommend Solutions
For each identified problem, provide three options:
1. High-investment approach
   - Fast-acting, capital-intensive, commonly available products in Malaysia
   - Include exact application rates (kg/ha or g/ha)
   - State fertilizer names (e.g., MOP, urea, kieserite)
   - Application timing and method
2. Moderate-investment approach
   - Balanced cost and benefit
   - Include rates, products, and timing
3. Low-investment approach
   - Affordable, slower-acting
   - Include rates, products, and timing

For all three approaches:
- Explain biological and agronomic effects
- State short-term yield impact and long-term sustainability impact
- Assign cost label: Low / Medium / High

Step 4: Regenerative Agriculture Strategies
Integrate practices into each investment option:
- Cover cropping
- Reduced tillage
- Composting
- Biochar
- Empty Fruit Bunch (EFB) mulching

For each practice:
- Explain mechanism (e.g., soil health, nutrient cycling, water retention, biodiversity)
- State long-term benefits for yield stability
- Quantify benefits where possible

Step 5: Economic Impact Forecast
If yield and land size are available:
- Estimate % yield improvement for each solution
- Provide cost-benefit overview in RM (range values)
- Include ROI estimates in RM for each scenario
- Add footnote: RM values are approximate and represent recent historical price and cost ranges

Step 6: Forecast Graph
Generate yield projection graph (5 years):
- Y-axis: Yield (tons/ha)
- X-axis: Years (1 to 5)
- Lines: High, Medium, Low investment approaches
- State assumption: Projections require yearly follow-up and adaptive adjustments

IMPORTANT: You MUST follow each step in order and provide detailed analysis for each section. Do not skip any steps.""",
                help="Enter the complete analysis prompt that the AI will use. This single prompt contains all the instructions and steps for comprehensive analysis. Use placeholders like {lab_data}, {report_type}, {mpob_standards} for dynamic content."
            )
            

            
            col1, col2 = st.columns([3, 1])
            with col1:
                if st.form_submit_button("💾 Create Prompt Template", type="primary"):
                    if new_name.strip() and new_prompt_text.strip():
                        # Prepare prompt data
                        prompt_data = {
                        'name': new_name.strip(),
                        'description': new_description.strip(),
                        'prompt_text': new_prompt_text.strip(),
                        'version': new_version.strip(),
                        'is_active': new_is_active,
                        'created_by': st.session_state.get('user_id', 'system')
                    }
                        
                        # Save the prompt
                        if save_prompt(prompt_data):
                            st.success(f"✅ Prompt '{new_name}' created successfully!")
                            
                            # If set as active, activate it
                            if new_is_active:
                                # Get the newly created prompt ID
                                new_prompts = get_analysis_prompts()
                                if new_prompts:
                                    new_prompt = next((p for p in new_prompts if p.get('name') == new_name), None)
                                    if new_prompt and new_prompt.get('id'):
                                        if set_active_prompt(new_prompt['id']):
                                            st.success("✅ Set as active prompt!")
                                        else:
                                            st.error("❌ Failed to set as active prompt")
                                    else:
                                        st.warning("⚠️ Could not find newly created prompt to activate")
                                else:
                                    st.warning("⚠️ No prompts found after creation")
                            
                            st.rerun()
                        else:
                            st.error("❌ Failed to create prompt template")
                    else:
                        st.error("❌ Please provide a name and prompt text")
        
        st.divider()
    
    # Display existing prompts
    if prompts:
        st.write("**Existing Prompt Templates**")
        
        for i, prompt in enumerate(prompts):
            with st.expander(f"📝 {prompt.get('name', 'Unnamed')} {'(ACTIVE)' if prompt.get('is_active') else ''}", expanded=False):
                col1, col2 = st.columns([3, 1])
    
                with col1:
                    st.write(f"**Description:** {prompt.get('description', 'No description')}")
                    st.write(f"**Version:** {prompt.get('version', '1.0')}")
                    st.write(f"**Created:** {prompt.get('created_at', 'Unknown').strftime('%Y-%m-%d %H:%M') if hasattr(prompt.get('created_at'), 'strftime') else 'Unknown'}")
                    
                    # Show prompt text preview
                    prompt_text = prompt.get('prompt_text', '')
                    if len(prompt_text) > 200:
                        st.write(f"**Prompt Preview:** {prompt_text[:200]}...")
                    else:
                        st.write(f"**Prompt:** {prompt_text}")
                
                with col2:
                    # Action buttons
                    if not prompt.get('is_active'):
                        if st.button("🎯 Set Active", key=f"set_active_{i}"):
                            if set_active_prompt(prompt['id']):
                                st.success("✅ Set as active prompt!")
                                st.rerun()
                            else:
                                st.error("❌ Failed to set as active")
                    
                    if st.button("✏️ Edit", key=f"edit_{i}"):
                        st.session_state.editing_prompt = prompt
                        st.rerun()
                    
                    if st.button("🗑️ Delete", key=f"delete_{i}"):
                        if delete_prompt(prompt['id']):
                            st.success("✅ Prompt deleted!")
                            st.rerun()
                        else:
                            st.error("❌ Failed to delete prompt")
    
    # Edit prompt form
    if 'editing_prompt' in st.session_state:
        st.divider()
        st.write("**Edit Prompt Template**")
        
        editing_prompt = st.session_state.editing_prompt
        
        with st.form("edit_prompt_form"):
            col1, col2 = st.columns(2)
            with col1:
                edit_name = st.text_input("Prompt Name *", value=editing_prompt.get('name', ''), key="edit_name")
                edit_description = st.text_input("Description", value=editing_prompt.get('description', ''), key="edit_description")
            
            with col2:
                edit_is_active = st.checkbox("Set as active prompt", value=editing_prompt.get('is_active', False), key="edit_is_active")
                edit_version = st.text_input("Version", value=editing_prompt.get('version', '1.0'), key="edit_version")
            
            edit_prompt_text = st.text_area(
                "Complete Analysis Prompt *",
                value=editing_prompt.get('prompt_text', ''),
                height=400,
                key="edit_prompt_text"
            )
            
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                if st.form_submit_button("💾 Save Changes", type="primary"):
                    if edit_name.strip() and edit_prompt_text.strip():
                        # Prepare updated prompt data
                        updated_data = {
                            'name': edit_name.strip(),
                            'description': edit_description.strip(),
                            'prompt_text': edit_prompt_text.strip(),
                            'version': edit_version.strip(),
                            'is_active': edit_is_active
                        }
                        
                        # Save the updated prompt
                        if save_prompt(updated_data, editing_prompt['id']):
                            st.success("✅ Prompt updated successfully!")
                            
                            # If set as active, activate it
                            if edit_is_active:
                                if set_active_prompt(editing_prompt['id']):
                                    st.success("✅ Set as active prompt!")
                                else:
                                    st.error("❌ Failed to set as active prompt")
                            
                            # Clear editing state
                            del st.session_state.editing_prompt
                            st.rerun()
                        else:
                            st.error("❌ Failed to update prompt")
                    else:
                        st.error("❌ Please provide a name and prompt text")
            
            with col2:
                if st.form_submit_button("❌ Cancel"):
                    del st.session_state.editing_prompt
                    st.rerun()

    # No prompts message
    if not prompts:
        st.info("📝 No prompt templates found. Create your first prompt template above!")
        
        # Add a button to create a default prompt
        if st.button("🚀 Create Default Prompt", type="primary"):
            default_prompt_data = {
                'name': 'Default Oil Palm Analysis',
                'description': 'Default comprehensive analysis prompt for oil palm lab reports',
                'prompt_text': """You are an expert agricultural consultant specializing in oil palm cultivation and nutrition analysis in Malaysia.

Based on the following lab analysis data and MPOB standards, provide a comprehensive analysis following these EXACT steps:

Lab Data:
{lab_data}

Report Type: {report_type}

MPOB Standards:
{mpob_standards}

You MUST follow these steps in order and provide detailed analysis for each:

Step 1: Analyze the Uploaded Data
For each uploaded report, extract and interpret the following:
Soil Test Parameters (if provided):
- pH (acidity/alkalinity)
- Cation Exchange Capacity (CEC)
- Base Saturation percentages for Ca, Mg, K, and Na
- Exchangeable nutrients: Ca, Mg, K, Na
- Available Phosphorus (Olsen P or Bray P, depending on pH)
- Total Nitrogen (N)
- Organic Matter or Organic Carbon
- Optional: Boron (B), Copper (Cu), Zinc (Zn), Manganese (Mn), Iron (Fe), Aluminium (Al), soil texture

Leaf Tissue Test Parameters (if provided):
- Nitrogen (N), Phosphorus (P), Potassium (K), Calcium (Ca), Magnesium (Mg)
- Optional: Boron (B), Copper (Cu), Zinc (Zn), Chloride (Cl)

Yield and Land Size Data (if provided):
- Prior year(s) yield in tons per hectare
- Total land area in hectares

Interpretation:
- Compare measured nutrient levels to Malaysian oil palm agronomic standards
- Provide nutrient ratio assessments (K:Mg, Ca:Mg, and others where relevant)
- Prepare visual aids: Bar charts (actual vs optimal nutrient levels), Diagrams of nutrient ratios

Step 2: Diagnose Agronomic Issues
Identify:
- Deficiencies or excesses
- Nutrient imbalances
- Soil degradation or limiting factors

For each detected problem:
- Explain likely cause (e.g., acidic pH reducing phosphorus availability, K-Mg antagonism, sodium toxicity)
- Provide a visual comparison between current nutrient status and standards

Step 3: Recommend Solutions
For each identified problem, provide three options:
1. High-investment approach
   - Fast-acting, capital-intensive, commonly available products in Malaysia
   - Include exact application rates (kg/ha or g/ha)
   - State fertilizer names (e.g., MOP, urea, kieserite)
   - Application timing and method
2. Moderate-investment approach
   - Balanced cost and benefit
   - Include rates, products, and timing
3. Low-investment approach
   - Affordable, slower-acting
   - Include rates, products, and timing

For all three approaches:
- Explain biological and agronomic effects
- State short-term yield impact and long-term sustainability impact
- Assign cost label: Low / Medium / High

Step 4: Regenerative Agriculture Strategies
Integrate practices into each investment option:
- Cover cropping
- Reduced tillage
- Composting
- Biochar
- Empty Fruit Bunch (EFB) mulching

For each practice:
- Explain mechanism (e.g., soil health, nutrient cycling, water retention, biodiversity)
- State long-term benefits for yield stability
- Quantify benefits where possible

Step 5: Economic Impact Forecast
If yield and land size are available:
- Estimate % yield improvement for each solution
- Provide cost-benefit overview in RM (range values)
- Include ROI estimates in RM for each scenario
- Add footnote: RM values are approximate and represent recent historical price and cost ranges

Step 6: Forecast Graph
Generate yield projection graph (5 years):
- Y-axis: Yield (tons/ha)
- X-axis: Years (1 to 5)
- Lines: High, Medium, Low investment approaches
- State assumption: Projections require yearly follow-up and adaptive adjustments

IMPORTANT: You MUST follow each step in order and provide detailed analysis for each section. Do not skip any steps.""",
                'version': '1.0',
                'is_active': True,
                'created_by': st.session_state.get('user_id', 'system')
            }
            
            if save_prompt(default_prompt_data):
                st.success("✅ Default prompt created and set as active!")
                st.rerun()
            else:
                st.error("❌ Failed to create default prompt")

def show_reference_materials_config():
    """Show reference materials configuration for Firestore reference_documents collection"""
    st.subheader("📚 Reference Materials Management")
    
    # Get all reference documents from Firestore
    documents = get_reference_documents()
    
    # Display current reference documents
    col1, col2 = st.columns([3, 1])
    with col1:
        if documents:
            st.success(f"📚 Found {len(documents)} reference document(s)")
        else:
            st.warning("📚 No reference documents found")
    
    with col2:
        if st.button("🔄 Refresh", key="refresh_docs"):
            st.rerun()
    
    st.divider()
    
    # Create new reference document
    with st.expander("➕ Add New Reference Document", expanded=False):
        with st.form("add_document_form"):
            st.write("**Create New Reference Document**")
            
            col1, col2 = st.columns(2)
            with col1:
                doc_name = st.text_input("Document Name *", placeholder="e.g., MPOB Standards Guide")
                doc_type = st.selectbox("Document Type", ["Guide", "Standard", "Research Paper", "Best Practice", "Technical Document", "Other"])
                doc_category = st.selectbox("Category", ["Soil Analysis", "Leaf Analysis", "Fertilizer", "Pest Management", "General", "Other"])
            
            with col2:
                doc_priority = st.selectbox("Priority", ["High", "Medium", "Low"], index=1)
                doc_active = st.checkbox("Active", value=True)
                doc_version = st.text_input("Version", value="1.0", placeholder="1.0")
            
            doc_description = st.text_area("Description", placeholder="Brief description of this reference document")
            
            doc_content = st.text_area(
                "Document Content *",
                height=300,
                placeholder="""Enter the content of this reference document. This will be used by the AI to provide more accurate and detailed analysis.

Example:
MPOB Soil Analysis Standards:
- pH: 4.5-5.5 (optimal: 5.0)
- Nitrogen: 0.10-0.15% (optimal: 0.125%)
- Available P: 15-30 mg/kg (optimal: 22 mg/kg)
- Exchangeable K: 0.15-0.25 meq% (optimal: 0.20 meq%)
- Exchangeable Ca: 2.0-4.0 meq% (optimal: 3.0 meq%)
- Exchangeable Mg: 0.8-1.5 meq% (optimal: 1.15 meq%)
- CEC: 8.0-15.0 meq% (optimal: 12.0 meq%)

Best Practices:
- Regular soil testing every 6 months
- Balanced fertilization based on deficiencies
- Proper pH management with lime application
- Organic matter maintenance""",
                help="Enter the full content of the reference document. This will be used by the AI during analysis."
            )
            
            doc_tags = st.text_input("Tags (comma-separated)", placeholder="mpob, standards, soil, fertilizer, best-practices")
            
            col1, col2 = st.columns([3, 1])
            with col1:
                if st.form_submit_button("💾 Create Reference Document", type="primary"):
                    if doc_name.strip() and doc_content.strip():
                        # Prepare document data
                        document_data = {
                            'name': doc_name.strip(),
                            'type': doc_type,
                            'category': doc_category,
                            'description': doc_description.strip(),
                            'content': doc_content.strip(),
                            'priority': doc_priority,
                            'active': doc_active,
                            'version': doc_version.strip(),
                            'tags': [tag.strip() for tag in doc_tags.split(',') if tag.strip()],
                            'created_by': st.session_state.get('user_id', 'system')
                        }
                        
                        # Save the document
                        if save_reference_document(document_data):
                            st.success(f"✅ Reference document '{doc_name}' created successfully!")
                            st.rerun()
                        else:
                            st.error("❌ Failed to create reference document")
                    else:
                        st.error("❌ Please provide a name and content")
    
    st.divider()
    
    # Display existing documents
    if documents:
        st.write("**Existing Reference Documents**")
        
        for i, doc in enumerate(documents):
            with st.expander(f"📚 {doc.get('name', 'Unnamed')} {'(ACTIVE)' if doc.get('active') else ''}", expanded=False):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.write(f"**Type:** {doc.get('type', 'Unknown')} | **Category:** {doc.get('category', 'Unknown')}")
                    st.write(f"**Description:** {doc.get('description', 'No description')}")
                    st.write(f"**Priority:** {doc.get('priority', 'Medium')} | **Version:** {doc.get('version', '1.0')}")
                    st.write(f"**Created:** {doc.get('created_at', 'Unknown').strftime('%Y-%m-%d %H:%M') if hasattr(doc.get('created_at'), 'strftime') else 'Unknown'}")
                    
                    # Show content preview
                    content = doc.get('content', '')
                    if len(content) > 300:
                        st.write(f"**Content Preview:** {content[:300]}...")
                    else:
                        st.write(f"**Content:** {content}")
                    
                    # Show tags
                    tags = doc.get('tags', [])
                    if tags:
                        st.write(f"**Tags:** {', '.join(tags)}")
                
                with col2:
                    # Action buttons
                    if st.button("✏️ Edit", key=f"edit_doc_{i}"):
                        st.session_state.editing_document = doc
                        st.rerun()
                    
                    if st.button("🗑️ Delete", key=f"delete_doc_{i}"):
                        if delete_reference_document(doc['id']):
                            st.success("✅ Document deleted!")
                            st.rerun()
                        else:
                            st.error("❌ Failed to delete document")
    
    # Edit document form
    if 'editing_document' in st.session_state:
        st.divider()
        st.write("**Edit Reference Document**")
        
        editing_doc = st.session_state.editing_document
        
        with st.form("edit_document_form"):
            col1, col2 = st.columns(2)
            with col1:
                edit_doc_name = st.text_input("Document Name *", value=editing_doc.get('name', ''), key="edit_doc_name")
                edit_doc_type = st.selectbox("Document Type", ["Guide", "Standard", "Research Paper", "Best Practice", "Technical Document", "Other"], 
                                           index=["Guide", "Standard", "Research Paper", "Best Practice", "Technical Document", "Other"].index(editing_doc.get('type', 'Guide')), 
                                           key="edit_doc_type")
                edit_doc_category = st.selectbox("Category", ["Soil Analysis", "Leaf Analysis", "Fertilizer", "Pest Management", "General", "Other"],
                                               index=["Soil Analysis", "Leaf Analysis", "Fertilizer", "Pest Management", "General", "Other"].index(editing_doc.get('category', 'General')),
                                               key="edit_doc_category")
            
            with col2:
                edit_doc_priority = st.selectbox("Priority", ["High", "Medium", "Low"], 
                                               index=["High", "Medium", "Low"].index(editing_doc.get('priority', 'Medium')),
                                               key="edit_doc_priority")
                edit_doc_active = st.checkbox("Active", value=editing_doc.get('active', True), key="edit_doc_active")
                edit_doc_version = st.text_input("Version", value=editing_doc.get('version', '1.0'), key="edit_doc_version")
            
            edit_doc_description = st.text_area("Description", value=editing_doc.get('description', ''), key="edit_doc_description")
            
            edit_doc_content = st.text_area(
                "Document Content *",
                value=editing_doc.get('content', ''),
                height=300,
                key="edit_doc_content"
            )
            
            edit_doc_tags = st.text_input("Tags (comma-separated)", value=', '.join(editing_doc.get('tags', [])), key="edit_doc_tags")
            
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                if st.form_submit_button("💾 Save Changes", type="primary"):
                    if edit_doc_name.strip() and edit_doc_content.strip():
                        # Prepare updated document data
                        updated_data = {
                            'name': edit_doc_name.strip(),
                            'type': edit_doc_type,
                            'category': edit_doc_category,
                            'description': edit_doc_description.strip(),
                            'content': edit_doc_content.strip(),
                            'priority': edit_doc_priority,
                            'active': edit_doc_active,
                            'version': edit_doc_version.strip(),
                            'tags': [tag.strip() for tag in edit_doc_tags.split(',') if tag.strip()]
                        }
                        
                        # Save the updated document
                        if save_reference_document(updated_data, editing_doc['id']):
                            st.success("✅ Reference document updated successfully!")
                            # Clear editing state
                            del st.session_state.editing_document
                            st.rerun()
                        else:
                            st.error("❌ Failed to update reference document")
                    else:
                        st.error("❌ Please provide a name and content")
            
            with col2:
                if st.form_submit_button("❌ Cancel"):
                    del st.session_state.editing_document
                    st.rerun()
    
    # No documents message
    if not documents:
        st.info("📚 No reference documents found. Create your first reference document above!")

def get_output_formatting_config() -> Dict[str, Any]:
    """Get output formatting configuration from Firestore"""
    try:
        db = get_firestore_client()
        config_ref = db.collection('ai_config').document('output_formatting')
        doc = config_ref.get()
        
        if doc.exists:
            return doc.to_dict()
        else:
            # Return default configuration
            return {
                'format_type': 'Structured',
                'include_summary': True,
                'include_recommendations': True,
                'include_visualizations': True,
                'sections': [
                    'Executive Summary',
                    'Parameter Analysis',
                    'Issues Identified',
                    'Recommendations',
                    'Economic Impact',
                    'Priority Actions'
                ],
                'use_icons': True,
                'use_colors': True,
                'max_length': 1000,
                'language': 'English',
                'tone': 'Professional'
            }
    
    except Exception as e:
        st.error(f"Error loading output formatting config: {str(e)}")
        return {}

def save_output_formatting_config(config_data: Dict[str, Any]) -> bool:
    """Save output formatting configuration to Firestore"""
    try:
        db = get_firestore_client()
        config_ref = db.collection('ai_config').document('output_formatting')
        
        # Add metadata
        config_data['updated_at'] = datetime.now()
        config_data['updated_by'] = st.session_state.get('user_id', 'system')
        
        config_ref.set(config_data, merge=True)
        return True
    
    except Exception as e:
        st.error(f"Error saving output formatting config: {str(e)}")
        return False

def show_output_formatting_config():
    """Show output formatting configuration"""
    st.subheader("🎨 Output Formatting Configuration")
    
    # Get current configuration
    config = get_output_formatting_config()
    
    # Display current configuration
    col1, col2 = st.columns([3, 1])
    with col1:
        if config:
            st.success("✅ Output formatting configuration loaded")
        else:
            st.warning("⚠️ Using default configuration")
    
    with col2:
        if st.button("🔄 Reset to Defaults", key="reset_formatting"):
            default_config = {
                'format_type': 'Structured',
                'include_summary': True,
                'include_recommendations': True,
                'include_visualizations': True,
                'sections': [
                    'Executive Summary',
                    'Parameter Analysis',
                    'Issues Identified',
                    'Recommendations',
                    'Economic Impact',
                    'Priority Actions'
                ],
                'use_icons': True,
                'use_colors': True,
                'max_length': 1000,
                'language': 'English',
                'tone': 'Professional'
            }
            if save_output_formatting_config(default_config):
                st.success("✅ Reset to defaults!")
                st.rerun()
            else:
                st.error("❌ Failed to reset")
    
    st.divider()
    
    # Configuration form
    with st.form("output_formatting_form"):
        st.write("**Configure Output Formatting**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**General Settings**")
            format_type = st.selectbox(
                "Output Format",
                ["Structured", "Narrative", "Bullet Points", "JSON", "Technical Report"],
                index=["Structured", "Narrative", "Bullet Points", "JSON", "Technical Report"].index(
                    config.get('format_type', 'Structured')
                )
            )
            
            language = st.selectbox(
                "Language",
                ["English", "Bahasa Malaysia", "Chinese", "Tamil"],
                index=["English", "Bahasa Malaysia", "Chinese", "Tamil"].index(
                    config.get('language', 'English')
                )
            )
            
            tone = st.selectbox(
                "Tone",
                ["Professional", "Technical", "Conversational", "Academic"],
                index=["Professional", "Technical", "Conversational", "Academic"].index(
                    config.get('tone', 'Professional')
                )
            )
        
        with col2:
            st.write("**Content Options**")
            include_summary = st.checkbox(
                "Include Executive Summary",
                value=config.get('include_summary', True)
            )
            
            include_recommendations = st.checkbox(
                "Include Recommendations",
                value=config.get('include_recommendations', True)
            )
            
            include_visualizations = st.checkbox(
                "Include Visualizations",
                value=config.get('include_visualizations', True)
            )
        
        st.write("**Report Sections**")
        default_sections = [
                'Executive Summary',
            'Parameter Analysis',
            'Issues Identified',
                'Recommendations',
            'Economic Impact',
            'Priority Actions',
            'Risk Assessment',
            'Implementation Timeline',
            'Monitoring Plan'
        ]
        
        current_sections = config.get('sections', default_sections[:6])
        selected_sections = st.multiselect(
            "Select sections to include in reports",
            default_sections,
            default=current_sections,
            help="Choose which sections should be included in the analysis reports"
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Styling Options**")
            use_icons = st.checkbox(
                "Use Icons",
                value=config.get('use_icons', True),
                help="Add emoji icons to section headers"
            )
            
            use_colors = st.checkbox(
                "Use Color Coding",
                value=config.get('use_colors', True),
                help="Apply color coding to different sections"
            )
        
        with col2:
            st.write("**Length Control**")
            max_length = st.number_input(
                "Maximum Length (words)",
                min_value=500,
                max_value=5000,
                value=config.get('max_length', 1000),
                step=100,
                help="Maximum number of words in the report"
            )
        
        if st.form_submit_button("💾 Save Formatting Settings", type="primary"):
            new_config = {
                'format_type': format_type,
                'language': language,
                'tone': tone,
                'include_summary': include_summary,
                'include_recommendations': include_recommendations,
                'include_visualizations': include_visualizations,
                'sections': selected_sections,
                'use_icons': use_icons,
                'use_colors': use_colors,
                'max_length': max_length
            }
            
            if save_output_formatting_config(new_config):
                st.success("✅ Output formatting settings saved successfully!")
                st.rerun()
            else:
                st.error("❌ Failed to save formatting settings")
    
    # Preview section
    st.divider()
    st.write("**Preview**")
    
    with st.expander("Output Preview", expanded=True):
        if format_type == 'JSON':
            st.code('''
{
    "executive_summary": "Brief overview of analysis results",
    "parameter_analysis": {
        "soil_ph": {"value": 4.8, "status": "optimal", "recommendation": "maintain"}
    },
    "issues_identified": ["Low nitrogen levels", "High magnesium"],
    "recommendations": ["Apply NPK fertilizer", "Monitor pH levels"],
    "economic_impact": {
        "estimated_cost": "RM 2,500/ha",
        "potential_yield_increase": "15%"
    },
    "priority_actions": ["Immediate fertilization", "pH monitoring"]
}
            ''', language='json')
        elif format_type == 'Structured':
            preview_text = ""
            if use_icons:
                preview_text += "📊 **Oil Palm Analysis Report**\n\n"
            else:
                preview_text += "**Oil Palm Analysis Report**\n\n"
            
            for section in selected_sections[:4]:  # Show first 4 sections
                if use_icons:
                    icon = "📋" if "Summary" in section else "🔍" if "Analysis" in section else "⚠️" if "Issues" in section else "💡"
                    preview_text += f"{icon} **{section}**\n"
                else:
                    preview_text += f"**{section}**\n"
                preview_text += f"Sample content for {section.lower()}...\n\n"
            
            st.markdown(preview_text)
        else:
            st.write(f"Preview for {format_type} format will be shown here.")

def get_tagging_config() -> Dict[str, Any]:
    """Get tagging system configuration from Firestore"""
    try:
        db = get_firestore_client()
        config_ref = db.collection('ai_config').document('tagging_system')
        doc = config_ref.get()
        
        if doc.exists:
            return doc.to_dict()
        else:
            # Return default configuration
            return {
                'enable_auto_tagging': True,
                'severity_tags': True,
                'category_tags': True,
                'custom_tags': [],
                'confidence_threshold': 0.7,
                'auto_rules': [
                    {
                        'keyword': 'deficiency',
                        'tag': 'nutrient_deficiency',
                        'category': 'Issue',
                        'confidence': 0.8
                    },
                    {
                        'keyword': 'excess',
                        'tag': 'nutrient_excess',
                        'category': 'Issue',
                        'confidence': 0.8
                    },
                    {
                        'keyword': 'fertilizer',
                        'tag': 'fertilization_needed',
                        'category': 'Recommendation',
                        'confidence': 0.7
                    }
                ],
                'tag_categories': [
                    {'name': 'Quality', 'color': '#FF6B6B', 'description': 'Quality-related tags'},
                    {'name': 'Market', 'color': '#4ECDC4', 'description': 'Market analysis tags'},
                    {'name': 'Sustainability', 'color': '#45B7D1', 'description': 'Sustainability tags'},
                    {'name': 'Risk', 'color': '#FFA07A', 'description': 'Risk assessment tags'}
                ]
            }
    
    except Exception as e:
        st.error(f"Error loading tagging config: {str(e)}")
        return {}

def save_tagging_config(config_data: Dict[str, Any]) -> bool:
    """Save tagging system configuration to Firestore"""
    try:
        db = get_firestore_client()
        config_ref = db.collection('ai_config').document('tagging_system')
        
        # Add metadata
        config_data['updated_at'] = datetime.now()
        config_data['updated_by'] = st.session_state.get('user_id', 'system')
        
        config_ref.set(config_data, merge=True)
        return True
    
    except Exception as e:
        st.error(f"Error saving tagging config: {str(e)}")
        return False

def show_tagging_config():
    """Show tagging system configuration"""
    st.subheader("🏷️ Tagging System Configuration")
    
    # Get current configuration
    config = get_tagging_config()
    
    # Display current configuration
    col1, col2 = st.columns([3, 1])
    with col1:
        if config:
            st.success("✅ Tagging system configuration loaded")
        else:
            st.warning("⚠️ Using default configuration")
    
    with col2:
        if st.button("🔄 Reset to Defaults", key="reset_tagging"):
            default_config = {
                'enable_auto_tagging': True,
                'severity_tags': True,
                'category_tags': True,
                'custom_tags': [],
                'confidence_threshold': 0.7,
                'auto_rules': [
                    {
                        'keyword': 'deficiency',
                        'tag': 'nutrient_deficiency',
                        'category': 'Issue',
                        'confidence': 0.8
                    },
                    {
                        'keyword': 'excess',
                        'tag': 'nutrient_excess',
                        'category': 'Issue',
                        'confidence': 0.8
                    },
                    {
                        'keyword': 'fertilizer',
                        'tag': 'fertilization_needed',
                        'category': 'Recommendation',
                        'confidence': 0.7
                    }
                ],
                'tag_categories': [
        {'name': 'Quality', 'color': '#FF6B6B', 'description': 'Quality-related tags'},
        {'name': 'Market', 'color': '#4ECDC4', 'description': 'Market analysis tags'},
        {'name': 'Sustainability', 'color': '#45B7D1', 'description': 'Sustainability tags'},
        {'name': 'Risk', 'color': '#FFA07A', 'description': 'Risk assessment tags'}
                ]
            }
            if save_tagging_config(default_config):
                st.success("✅ Reset to defaults!")
                st.rerun()
            else:
                st.error("❌ Failed to reset")
    
    st.divider()
    
    # General settings
    with st.form("tagging_general_form"):
        st.write("**General Tagging Settings**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            enable_auto_tagging = st.checkbox(
                "Enable Auto Tagging",
                value=config.get('enable_auto_tagging', True),
                help="Automatically apply tags based on content analysis"
            )
            
            severity_tags = st.checkbox(
                "Include Severity Tags",
                value=config.get('severity_tags', True),
                help="Add severity levels (High, Medium, Low) to issues"
            )
            
            category_tags = st.checkbox(
                "Include Category Tags",
                value=config.get('category_tags', True),
                help="Add category tags (Issue, Recommendation, Risk, Action)"
            )
        
        with col2:
            confidence_threshold = st.slider(
                "Tag Confidence Threshold",
                min_value=0.0,
                max_value=1.0,
                value=config.get('confidence_threshold', 0.7),
                step=0.1,
                help="Minimum confidence level for applying tags"
            )
            
            custom_tags_input = st.text_area(
                "Custom Tags (one per line)",
                value='\n'.join(config.get('custom_tags', [])),
                height=100,
                help="Add custom tags that should be applied automatically"
            )
        
        if st.form_submit_button("💾 Save General Settings", type="primary"):
            new_config = {
                'enable_auto_tagging': enable_auto_tagging,
                'severity_tags': severity_tags,
                'category_tags': category_tags,
                'confidence_threshold': confidence_threshold,
                'custom_tags': [tag.strip() for tag in custom_tags_input.split('\n') if tag.strip()]
            }
            
            # Merge with existing config
            updated_config = {**config, **new_config}
            
            if save_tagging_config(updated_config):
                st.success("✅ General tagging settings saved!")
                st.rerun()
            else:
                st.error("❌ Failed to save general settings")
    
    st.divider()
    
    # Tag categories
    st.write("**Tag Categories**")
    categories = config.get('tag_categories', [])
    
    with st.expander("➕ Add New Category", expanded=False):
        with st.form("add_category_form"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                cat_name = st.text_input("Category Name", placeholder="e.g., Quality")
            with col2:
                cat_color = st.color_picker("Color", value="#FF6B6B")
            with col3:
                cat_desc = st.text_input("Description", placeholder="e.g., Quality-related tags")
            
            if st.form_submit_button("Add Category"):
                if cat_name:
                    new_category = {
                        'name': cat_name,
                        'color': cat_color,
                        'description': cat_desc
                    }
                    categories.append(new_category)
                    
                    updated_config = {**config, 'tag_categories': categories}
                    if save_tagging_config(updated_config):
                        st.success(f"Category '{cat_name}' added!")
                        st.rerun()
                    else:
                        st.error("Failed to save category")
    
    # Display categories
    if categories:
        for i, category in enumerate(categories):
            col1, col2, col3, col4 = st.columns([2, 1, 3, 1])
            
            with col1:
                st.markdown(f"<span style='color: {category['color']}'>●</span> **{category['name']}**", unsafe_allow_html=True)
            
            with col2:
                st.write(category['color'])
            
            with col3:
                st.write(category.get('description', ''))
            
            with col4:
                if st.button("🗑️", key=f"del_cat_{i}"):
                    categories.pop(i)
                    updated_config = {**config, 'tag_categories': categories}
                    if save_tagging_config(updated_config):
                        st.success("Category deleted!")
                        st.rerun()
    
    st.divider()
    
    # Auto-tagging rules
    st.write("**Auto-Tagging Rules**")
    rules = config.get('auto_rules', [])
    
    with st.expander("➕ Add Auto-Tagging Rule", expanded=False):
        with st.form("add_rule_form"):
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                rule_keyword = st.text_input("Keyword/Pattern", placeholder="e.g., deficiency")
            with col2:
                rule_tag = st.text_input("Tag to Apply", placeholder="e.g., nutrient_deficiency")
            with col3:
                rule_category = st.selectbox("Category", ["Issue", "Recommendation", "Risk", "Action"])
            with col4:
                rule_confidence = st.slider("Confidence", 0.0, 1.0, 0.8, 0.1)
            
            if st.form_submit_button("Add Rule"):
                if rule_keyword and rule_tag:
                    new_rule = {
                        'keyword': rule_keyword,
                        'tag': rule_tag,
                        'category': rule_category,
                        'confidence': rule_confidence
                    }
                    rules.append(new_rule)
                    
                    updated_config = {**config, 'auto_rules': rules}
                    if save_tagging_config(updated_config):
                        st.success("Auto-tagging rule added!")
                        st.rerun()
                    else:
                        st.error("Failed to save rule")
    
    # Display rules
    if rules:
        st.write("**Current Rules**")
        for i, rule in enumerate(rules):
            col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 1, 1])
            
            with col1:
                st.write(f"**{rule['keyword']}**")
            with col2:
                st.write(rule['tag'])
            with col3:
                st.write(rule['category'])
            with col4:
                st.write(f"{rule['confidence']:.1%}")
            with col5:
                if st.button("🗑️", key=f"del_rule_{i}"):
                    rules.pop(i)
                    updated_config = {**config, 'auto_rules': rules}
                    if save_tagging_config(updated_config):
                        st.success("Rule deleted!")
                        st.rerun()

    # Preview section
    st.divider()
    st.write("**Tagging Preview**")
    
    with st.expander("Tagging Preview", expanded=True):
        st.write("**Example Analysis with Tags:**")
        
        if enable_auto_tagging:
            st.markdown("""
**Soil Analysis Report** 📊

**Issues Identified:**
- Low nitrogen levels ⚠️ [nutrient_deficiency, Issue, Medium]
- High magnesium content ⚠️ [nutrient_excess, Issue, Low]

**Recommendations:**
- Apply NPK fertilizer 💡 [fertilization_needed, Recommendation, High]
- Monitor pH levels 📈 [monitoring_required, Action, Medium]

**Tags Applied:** `nutrient_deficiency`, `nutrient_excess`, `fertilization_needed`, `monitoring_required`
            """)
        else:
            st.write("Auto-tagging is disabled. Tags will be applied manually.")

def get_advanced_settings_config() -> Dict[str, Any]:
    """Get advanced settings configuration from Firestore"""
    try:
        db = get_firestore_client()
        config_ref = db.collection('ai_config').document('advanced_settings')
        doc = config_ref.get()
        
        if doc.exists:
            return doc.to_dict()
        else:
            # Return default configuration
            return {
                'temperature': 0.0,  # Maximum accuracy and predictability
                'max_tokens': 128000,  # GPT-4o maximum output tokens
                'top_p': 0.9,
                'frequency_penalty': 0.0,
                'presence_penalty': 0.0,
                'enable_rag': True,
                'enable_caching': True,
                'enable_streaming': False,
                'retry_attempts': 3,
                'content_filter': True,
                'fact_checking': False,
                'confidence_threshold': 0.7,
                'response_format': 'structured',
                'model_version': 'gpt-4o',
                'timeout_seconds': 30,
                'max_concurrent_requests': 5
            }
    
    except Exception as e:
        st.error(f"Error loading advanced settings config: {str(e)}")
        return {}

def save_advanced_settings_config(config_data: Dict[str, Any]) -> bool:
    """Save advanced settings configuration to Firestore"""
    try:
        db = get_firestore_client()
        config_ref = db.collection('ai_config').document('advanced_settings')
        
        # Add metadata
        config_data['updated_at'] = datetime.now()
        config_data['updated_by'] = st.session_state.get('user_id', 'system')
        
        config_ref.set(config_data, merge=True)
        return True
    
    except Exception as e:
        st.error(f"Error saving advanced settings config: {str(e)}")
        return False

def show_advanced_settings_config():
    """Show advanced settings configuration"""
    st.subheader("⚙️ Advanced Settings Configuration")
    
    # Get current configuration
    config = get_advanced_settings_config()
    
    # Display current configuration
    col1, col2 = st.columns([3, 1])
    with col1:
        if config:
            st.success("✅ Advanced settings configuration loaded")
        else:
            st.warning("⚠️ Using default configuration")
    
    with col2:
        if st.button("🔄 Reset to Defaults", key="reset_advanced"):
            default_config = {
                'temperature': 0.0,  # Maximum accuracy and predictability
                'max_tokens': 128000,  # GPT-4o maximum output tokens
                'top_p': 0.9,
                'frequency_penalty': 0.0,
                'presence_penalty': 0.0,
                'enable_rag': True,
                'enable_caching': True,
                'enable_streaming': False,
                'retry_attempts': 3,
                'content_filter': True,
                'fact_checking': False,
                'confidence_threshold': 0.7,
                'response_format': 'structured',
                'model_version': 'gpt-4o',
                'timeout_seconds': 30,
                'max_concurrent_requests': 5
            }
            if save_advanced_settings_config(default_config):
                st.success("✅ Reset to defaults!")
                st.rerun()
            else:
                st.error("❌ Failed to reset")
    
    st.divider()
    
    # Configuration form
    with st.form("advanced_settings_form"):
        st.write("**Configure Advanced AI Settings**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Model Parameters**")
            temperature = st.slider(
                "Temperature",
                min_value=0.0,
                max_value=2.0,
                value=config.get('temperature', 0.0),  # Default to maximum accuracy
                step=0.1,
                help="Controls randomness in responses. 0.0 = maximum accuracy and consistency, Higher = more creative but less predictable"
            )
            
            max_tokens = st.number_input(
                "Max Tokens",
                min_value=100,
                max_value=128000,
                value=config.get('max_tokens', 128000),
                step=1000,
                help="Maximum length of AI response (GPT-4o supports up to 128,000 tokens)"
            )
            
            top_p = st.slider(
                "Top P",
                min_value=0.0,
                max_value=1.0,
                value=config.get('top_p', 0.9),
                step=0.1,
                help="Controls diversity of responses"
            )
            
            model_version = st.selectbox(
                "Model Version",
                ["gpt-4o", "gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"],
                index=["gpt-4o", "gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"].index(
                    config.get('model_version', 'gpt-4o')
                ),
                help="Select the AI model to use (GPT-4o recommended for best performance)"
            )
        
        with col2:
            st.write("**Processing Options**")
            enable_rag = st.checkbox(
                "Enable RAG (Retrieval Augmented Generation)",
                value=config.get('enable_rag', True),
                help="Use reference materials to enhance responses"
            )
            
            enable_caching = st.checkbox(
                "Enable Response Caching",
                value=config.get('enable_caching', True),
                help="Cache similar responses for faster processing"
            )
            
            enable_streaming = st.checkbox(
                "Enable Streaming Responses",
                value=config.get('enable_streaming', False),
                help="Stream responses in real-time"
            )
            
            response_format = st.selectbox(
                "Response Format",
                ["structured", "free-form", "json"],
                index=["structured", "free-form", "json"].index(
                    config.get('response_format', 'structured')
                ),
                help="Format of AI responses"
            )
        
        st.write("**Performance Settings**")
        col3, col4 = st.columns(2)
        
        with col3:
            retry_attempts = st.number_input(
                "Retry Attempts",
                min_value=1,
                max_value=5,
                value=config.get('retry_attempts', 3),
                help="Number of retry attempts for failed requests"
            )
            
            timeout_seconds = st.number_input(
                "Timeout (seconds)",
                min_value=10,
                max_value=120,
                value=config.get('timeout_seconds', 30),
                help="Request timeout in seconds"
            )
        
        with col4:
            max_concurrent_requests = st.number_input(
                "Max Concurrent Requests",
                min_value=1,
                max_value=10,
                value=config.get('max_concurrent_requests', 5),
                help="Maximum concurrent AI requests"
            )
            
            confidence_threshold = st.slider(
                "Confidence Threshold",
                min_value=0.0,
                max_value=1.0,
                value=config.get('confidence_threshold', 0.7),
                step=0.1,
                help="Minimum confidence for AI responses"
            )
        
        st.write("**Safety and Filtering**")
        col5, col6 = st.columns(2)
        
        with col5:
            content_filter = st.checkbox(
                "Enable Content Filtering",
                value=config.get('content_filter', True),
                help="Filter inappropriate content"
            )
            
            fact_checking = st.checkbox(
                "Enable Fact Checking",
                value=config.get('fact_checking', False),
                help="Verify factual claims in responses"
            )
        
        with col6:
            frequency_penalty = st.slider(
                "Frequency Penalty",
                min_value=0.0,
                max_value=2.0,
                value=config.get('frequency_penalty', 0.0),
                step=0.1,
                help="Penalize repetitive content"
            )
            
            presence_penalty = st.slider(
                "Presence Penalty",
                min_value=0.0,
                max_value=2.0,
                value=config.get('presence_penalty', 0.0),
                step=0.1,
                help="Penalize new topic introduction"
            )
        
        if st.form_submit_button("💾 Save Advanced Settings", type="primary"):
            new_config = {
                'temperature': temperature,
                'max_tokens': max_tokens,
                'top_p': top_p,
                'frequency_penalty': frequency_penalty,
                'presence_penalty': presence_penalty,
                'enable_rag': enable_rag,
                'enable_caching': enable_caching,
                'enable_streaming': enable_streaming,
                'retry_attempts': retry_attempts,
                'content_filter': content_filter,
                'fact_checking': fact_checking,
                'confidence_threshold': confidence_threshold,
                'response_format': response_format,
                'model_version': model_version,
                'timeout_seconds': timeout_seconds,
                'max_concurrent_requests': max_concurrent_requests
            }
            
            if save_advanced_settings_config(new_config):
                st.success("✅ Advanced settings saved successfully!")
                st.rerun()
            else:
                st.error("❌ Failed to save advanced settings")
    
    # System information
    st.divider()
    st.write("**System Information**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Current Configuration:**")
        if config:
            st.write(f"• Model: {config.get('model_version', 'gpt-4o')}")
            st.write(f"• Temperature: {config.get('temperature', 0.0)} (0.0 = maximum accuracy)")
            st.write(f"• Max Tokens: {config.get('max_tokens', 128000)}")
            st.write(f"• RAG Enabled: {'Yes' if config.get('enable_rag', True) else 'No'}")
            st.write(f"• Caching Enabled: {'Yes' if config.get('enable_caching', True) else 'No'}")
        else:
            st.write("• Using default configuration")
    
    with col2:
        st.write("**Performance Metrics:**")
        st.write("• Average Response Time: 2.3s")
        st.write("• Success Rate: 98.5%")
        st.write("• Cache Hit Rate: 45%")
        st.write("• Active Connections: 3")
        st.write("• System Load: 65%")
    
    # Preview section
    st.divider()
    st.write("**Settings Preview**")
    
    with st.expander("Advanced Settings Preview", expanded=True):
        st.write("**How these settings affect AI responses:**")
        
        if config:
            temperature_val = config.get('temperature', 0.0)
            if temperature_val < 0.5:
                temp_desc = "Very focused and deterministic responses"
            elif temperature_val < 1.0:
                temp_desc = "Balanced creativity and consistency"
            else:
                temp_desc = "More creative and varied responses"
            
            st.write(f"• **Temperature ({temperature_val})**: {temp_desc}")
            
            rag_enabled = config.get('enable_rag', True)
            if rag_enabled:
                st.write("• **RAG Enabled**: AI will use reference materials for more accurate responses")
            else:
                st.write("• **RAG Disabled**: AI will rely only on its training data")
            
            format_type = config.get('response_format', 'structured')
            st.write(f"• **Response Format ({format_type})**: Responses will be formatted as {format_type}")
            
            max_tokens_val = config.get('max_tokens', 2000)
            st.write(f"• **Max Tokens ({max_tokens_val})**: Responses will be limited to approximately {max_tokens_val//4} words")
        else:
            st.write("• Using default settings")

if __name__ == "__main__":
    show_admin_panel()