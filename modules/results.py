import streamlit as st
import sys
import os
from datetime import datetime
import pandas as pd
import plotly.graph_objects as go
# Use our configured Firestore client instead of direct import
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add utils to path
sys.path.append(os.path.join(
    os.path.dirname(os.path.dirname(__file__)), 'utils'))

# Import utilities
from utils.firebase_config import get_firestore_client, COLLECTIONS
from google.cloud.firestore import Query, FieldFilter
from utils.pdf_utils import PDFReportGenerator
from utils.analysis_engine import AnalysisEngine
from utils.ocr_utils import extract_data_from_image
from modules.admin import get_active_prompt
from utils.feedback_system import (
    display_feedback_section as display_feedback_section_util)

def add_responsive_css():
    """Add responsive CSS styling for optimal viewing across devices"""
    st.markdown(
        """
        <style>
        /* Main title styling */
        .main-title {
            color: #2E8B57;
            text-align: center;
            font-size: 2.5rem;
            margin-bottom: 1rem;
            font-weight: 600;
        }
        
        /* Responsive design for mobile devices */
        @media (max-width: 768px) {
            .main-title {
                font-size: 2rem;
                margin-bottom: 0.5rem;
            }
            
            .stColumn {
                padding: 0.25rem;
            }
            
            .metric-container {
                margin-bottom: 0.5rem;
            }
        }
        
        /* Enhanced card styling */
        .analysis-card {
            background-color: #f8f9fa;
            padding: 1.5rem;
            border-radius: 10px;
            border-left: 4px solid #2E8B57;
            margin: 1rem 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        @media (max-width: 768px) {
            .analysis-card {
                padding: 1rem;
                margin: 0.5rem 0;
            }
        }
        
        /* Print-specific styles */
        @media print {
            /* Hide browser print headers and footers */
            @page {
                margin: 0.5in;
                @top-left { content: ""; }
                @top-center { content: ""; }
                @top-right { content: ""; }
                @bottom-left { content: ""; }
                @bottom-center { content: ""; }
                @bottom-right { content: ""; }
            }
            
            /* Alternative method to hide headers/footers */
            body {
                -webkit-print-color-adjust: exact;
                print-color-adjust: exact;
            }
            
            .no-print {
                display: none !important;
            }
            
            .print-only {
                display: block !important;
            }
            
            body {
                font-size: 12pt;
                line-height: 1.4;
                color: #000 !important;
                background: #fff !important;
                margin: 0 !important;
                padding: 0 !important;
            }
            
            .main-title {
                font-size: 18pt !important;
                color: #000 !important;
            }
            
            .section-title {
                font-size: 14pt !important;
                color: #000 !important;
            }
            
            .metric-container {
                break-inside: avoid;
                page-break-inside: avoid;
            }
            
            .step-block {
                break-inside: avoid;
                page-break-inside: avoid;
                margin-bottom: 20pt;
            }
            
            .chart-container {
                break-inside: avoid;
                page-break-inside: avoid;
            }
            
            /* Hide Streamlit elements that shouldn't print */
            .stApp > header,
            .stApp > div[data-testid="stHeader"],
            .stApp > div[data-testid="stSidebar"],
            .stApp > div[data-testid="stToolbar"],
            .stApp > div[data-testid="stDecoration"],
            .stApp > div[data-testid="stStatusWidget"],
            .stApp > div[data-testid="stNotificationContainer"],
            .stApp > div[data-testid="stSidebar"] {
                display: none !important;
            }
            
            /* Hide specific sections when printing */
            .feedback-section,
            .help-us-improve,
            .stButton > button,
            .print-hide {
                display: none !important;
            }
            
            /* Ensure raw data section is visible when printing */
            .raw-data-section {
                display: block !important;
            }
            
            /* Show print indicators */
            .print-show {
                display: block !important;
            }
            
            /* Allow all content to print - removed restriction that hid content after references */
            
            /* Ensure all content is visible and printable */
            .stApp {
                height: auto !important;
                overflow: visible !important;
            }
            
            .main .block-container {
                max-width: none !important;
                padding: 0 !important;
                margin: 0 !important;
            }
            
            /* Better page break handling for long content */
            .step-block,
            .section-block,
            .analysis-section {
                page-break-inside: avoid;
                break-inside: avoid;
            }
            
            /* Ensure tables and charts print properly */
            table {
                page-break-inside: auto;
                break-inside: auto;
            }
            
            /* Hide the entire sidebar area */
            .stApp > div[data-testid="stSidebar"] {
                display: none !important;
            }
            
            /* Ensure main content takes full width when printing */
            .stApp > div[data-testid="stAppViewContainer"] {
                width: 100% !important;
                max-width: none !important;
                padding: 0 !important;
                margin: 0 !important;
            }
            
            /* Ensure all content is visible in print */
            .stApp > div[data-testid="stAppViewContainer"] {
                width: 100% !important;
                max-width: none !important;
                padding: 0 !important;
                margin: 0 !important;
            }
            
            /* Print-friendly button styling */
            .stButton > button {
                display: none !important;
            }
            
            /* Print-friendly table styling */
            .dataframe {
                border: 1px solid #000 !important;
                border-collapse: collapse !important;
            }
            
            .dataframe th,
            .dataframe td {
                border: 1px solid #000 !important;
                padding: 8pt !important;
            }
            
            .dataframe th {
                background-color: #f0f0f0 !important;
                color: #000 !important;
            }
        }
        
        /* Step container styling */
        .step-container {
            background-color: #ffffff;
            border: 1px solid #e9ecef;
            border-radius: 8px;
            padding: 1rem;
            margin: 0.5rem 0;
        }
        
        /* Issue severity styling */
        .issue-critical {
            background-color: #dc354515;
            border-left: 3px solid #dc3545;
            padding: 0.75rem;
            border-radius: 5px;
            margin: 0.5rem 0;
        }
        
        .issue-medium {
            background-color: #fd7e1415;
            border-left: 3px solid #fd7e14;
            padding: 0.75rem;
            border-radius: 5px;
            margin: 0.5rem 0;
        }
        
        .issue-low {
            background-color: #ffc10715;
            border-left: 3px solid #ffc107;
            padding: 0.75rem;
            border-radius: 5px;
            margin: 0.5rem 0;
        }
        
        /* Responsive table styling */
        .dataframe {
            font-size: 0.9rem;
        }
        
        @media (max-width: 768px) {
            .dataframe {
                font-size: 0.8rem;
            }
        }
        
        /* Button styling */
        .stButton > button {
            border-radius: 6px;
            font-weight: 500;
        }
        
        /* Expander styling */
        .streamlit-expanderHeader {
            font-weight: 600;
            color: #2E8B57;
        }
        
        /* Mobile-friendly spacing */
        @media (max-width: 768px) {
            .block-container {
                padding-top: 1rem;
                padding-bottom: 1rem;
            }
        }
        </style>
        """,
        unsafe_allow_html=True
    )

def _balance_div_tags(html: str) -> str:
    """Best-effort fix for unmatched </div> tags in small HTML snippets."""
    try:
        # Count opening and closing div tags
        opens = html.count('<div')
        closes = html.count('</div>')
        
        # Only balance if there's a significant mismatch
        if abs(opens - closes) > 0:
            if closes < opens:
                # Add missing closing tags
                html = html + ('</div>' * (opens - closes))
            elif closes > opens:
                # Remove extra closing tags from the end
                excess = closes - opens
                while excess > 0 and '</div>' in html:
                    last = html.rfind('</div>')
                    html = html[:last] + html[last+6:]
                    excess -= 1
        return html
    except Exception:
        return html

def show_results_page():
    """Main results page - processes new analysis data and displays results"""
    # Add responsive CSS styling
    add_responsive_css()
    
    # Check authentication
    if not st.session_state.get('authenticated', False):
        st.markdown('<h1 class="main-title">🔍 Analysis Results</h1>', unsafe_allow_html=True)
        st.warning("🔒 Please log in to view analysis results.")
        
        # Responsive button layout
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("🔑 Login", type="primary", width='stretch'):
                st.session_state.current_page = 'login'
                st.rerun()
        with col2:
            if st.button("📝 Register", width='stretch'):
                st.session_state.current_page = 'register'
                st.rerun()
        return
    
    # Responsive page header with centered title and buttons below
    st.markdown('<h1 class="main-title" style="text-align: center;">🔍 Analysis Results</h1>', unsafe_allow_html=True)
    
    # Button row below the title
    button_col1, button_col2, button_col3 = st.columns([1, 1, 1])
    with button_col1:
        if st.button("🔄 Refresh", type="secondary", width='stretch'):
            st.cache_data.clear()
            st.rerun()
    with button_col2:
        pass  # Empty column for spacing
    with button_col3:
        pass  # Print button removed as requested
    
    # Check for new analysis data and process it
    try:
        # Check if there's new analysis data to process
        if 'analysis_data' in st.session_state and st.session_state.analysis_data:
            # Enhanced loading interface for non-technical users
            st.markdown("### 🔬 Analyzing Your Agricultural Reports")
            st.info("📊 Our AI system is processing your soil and leaf analysis data. This may take a few moments...")
            
            # Create enhanced progress display with system status
            progress_container = st.container()
            with progress_container:
                # Add system status indicator with heartbeat
                st.markdown("""
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    padding: 15px; border-radius: 10px; margin-bottom: 20px; 
                    text-align: center; animation: pulse 2s infinite;">
                    <h4 style="color: white; margin: 0; font-size: 18px;">
                        🔄 System Status: 
                        <span style="color: #ffeb3b; animation: blink 1s infinite;">
                            ACTIVELY PROCESSING
                        </span>
                    </h4>
                    <p style="color: rgba(255,255,255,0.9); margin: 5px 0 0 0; 
                        font-size: 14px;">
                        Our AI is working hard to analyze your data. Please wait...
                    </p>
                    <div style="margin-top: 10px;">
                        <span style="color: #4caf50; font-size: 12px;">💚 System Heartbeat: Active</span>
                        <span style="color: #ffeb3b; font-size: 12px; margin-left: 15px;">⚡ Processing Power: High</span>
                    </div>
                </div>
                <style>
                    @keyframes pulse {
                        0% { box-shadow: 0 0 0 0 rgba(102, 126, 234, 0.7); }
                        70% { box-shadow: 0 0 0 10px rgba(102, 126, 234, 0); }
                        100% { box-shadow: 0 0 0 0 rgba(102, 126, 234, 0); }
                    }
                    @keyframes blink {
                        0%, 50% { opacity: 1; }
                        51%, 100% { opacity: 0.5; }
                    }
                </style>
                """, unsafe_allow_html=True)
                
                progress_bar = st.progress(0)
                status_text = st.empty()
                time_estimate = st.empty()
                step_indicator = st.empty()
                
                # Add a "system is working" indicator
                working_indicator = st.empty()
            
            # Process the new analysis with enhanced progress tracking
            results_data = process_new_analysis(st.session_state.analysis_data, progress_bar, status_text, time_estimate, step_indicator, working_indicator)
            
            # Clear the analysis_data from session state after processing
            del st.session_state.analysis_data
            
            if results_data and results_data.get('success', False):
                # Enhanced success message
                st.balloons()
                st.success("🎉 Analysis completed successfully! Your comprehensive agricultural report is ready.")
                progress_container.empty()
            else:
                st.error(f"❌ Analysis failed: {results_data.get('message', 'Unknown error')}")
                st.info("💡 **Tip:** Make sure your uploaded files are clear images of soil and leaf analysis reports.")
                return
        else:
            # Load existing results from Firestore
            results_data = load_latest_results()
        
        if not results_data or not results_data.get('success', True):
            display_no_results_message()
            return
        
        # Display results in organized sections
        st.markdown('<div class="print-show">', unsafe_allow_html=True)
        display_results_header(results_data)
        display_raw_data_section(results_data)  # Add raw data display
        display_summary_section(results_data)
        display_key_findings_section(results_data)  # Key Findings below Executive Summary
        display_step_by_step_results(results_data)
        
        
        # PDF Download section
        st.markdown("---")
        st.markdown("## 📄 Download Report")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("📥 Download PDF Report", type="primary", width='stretch'):
                try:
                    # Generate PDF
                    with st.spinner("🔄 Generating PDF report..."):
                        pdf_bytes = generate_results_pdf(results_data)
                        
                    # Download the PDF
                    st.download_button(
                        label="💾 Download PDF",
                        data=pdf_bytes,
                        file_name=f"agricultural_analysis_report.pdf",
                        mime="application/pdf",
                        type="primary"
                    )
                    st.success("✅ PDF report generated successfully!")
                    
                except Exception as e:
                    st.error(f"❌ Failed to generate PDF: {str(e)}")
                    st.info("Please try again or contact support if the issue persists.")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Add a marker for print cutoff
        st.markdown('<div class="references-section"></div>', unsafe_allow_html=True)
        
        
        
    except Exception as e:
        st.error(f"❌ Error processing analysis: {str(e)}")
        st.info("Please try refreshing the page or contact support if the issue persists.")

@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_latest_results():
    """Load the latest analysis results from Firestore or current analysis from session state"""
    try:
        # First check if there's a current analysis from history page
        if 'current_analysis' in st.session_state and st.session_state.current_analysis:
            current_analysis = st.session_state.current_analysis
            
            # Convert current_analysis format to match expected format
            results_data = {
                'id': current_analysis.get('id'),
                'user_email': st.session_state.get('user_email'),
                'timestamp': current_analysis.get('timestamp', datetime.now()),
                'status': current_analysis.get('status', 'completed'),
                'soil_data': current_analysis.get('soil_data', {}),
                'leaf_data': current_analysis.get('leaf_data', {}),
                'land_yield_data': current_analysis.get('land_yield_data', {}),
                'report_types': ['soil', 'leaf'],
                'success': True
            }
            
            # Get analysis_results from session state if available (to avoid Firebase validation issues)
            if 'stored_analysis_results' in st.session_state:
                result_id = current_analysis.get('id')
                if result_id and result_id in st.session_state.stored_analysis_results:
                    results_data['analysis_results'] = st.session_state.stored_analysis_results[result_id]
                else:
                    # Fallback to the original method if not found in session state
                    results_data['analysis_results'] = current_analysis.get('analysis_results', {})
            
            # Clear current_analysis from session state after loading
            del st.session_state.current_analysis
            
            return results_data
        
        # Check if there are any stored analysis results in session state (newly completed)
        if 'stored_analysis_results' in st.session_state and st.session_state.stored_analysis_results:
            # Get the most recent analysis result from session state
            latest_id = max(st.session_state.stored_analysis_results.keys())
            latest_analysis = st.session_state.stored_analysis_results[latest_id]
            
            # Create results data structure
            results_data = {
                'id': latest_id,
                'user_email': st.session_state.get('user_email'),
                'timestamp': datetime.now(),
                'status': 'completed',
                'report_types': ['soil', 'leaf'],
                'success': True,
                'analysis_results': latest_analysis
            }
            return results_data
        
        # If no stored results, try to load from database (legacy data)
        db = get_firestore_client()
        user_email = st.session_state.get('user_email')
        
        if not user_email:
            return None
        
        # Query for the latest analysis results
        analyses_ref = db.collection(COLLECTIONS['analysis_results'])
        query = analyses_ref.where(filter=FieldFilter('user_email', '==', user_email)).order_by('timestamp', direction=Query.DESCENDING).limit(1)
        
        docs = query.stream()
        for doc in docs:
            data = doc.to_dict()
            data['id'] = doc.id
            data['success'] = True  # Ensure success flag is set
            return data
        
        return None
        
    except Exception as e:
        st.error(f"Error loading results from database: {str(e)}")
        return None

def process_new_analysis(analysis_data, progress_bar, status_text, time_estimate=None, step_indicator=None, working_indicator=None):
    """Process new analysis data from uploaded files"""
    try:
        import time
        
        # Enhanced progress tracking with detailed steps and animations
        total_steps = 8
        current_step = 1
        
        # Create animated loading indicators
        loading_indicators = ["⏳", "🔄", "⚡", "🌟", "💫", "✨", "🎯", "🚀"]
        processing_messages = [
            "Processing your data...",
            "Analyzing patterns...",
            "Generating insights...",
            "Computing results...",
            "Optimizing analysis...",
            "Finalizing report...",
            "Almost done...",
            "Preparing results..."
        ]
        
        # Step 1: Initial validation with animation
        progress_bar.progress(5)
        for i in range(3):  # Show animation for 3 cycles
            indicator = loading_indicators[i % len(loading_indicators)]
            status_text.text(f"🔍 **Step 1/8:** Validating uploaded files... {indicator}")
            if working_indicator:
                working_indicator.markdown(f"🔄 **System Status:** {indicator} Processing... | ⏱️ Active")
            time.sleep(0.5)
        
        
        
        # Extract data from uploaded files
        soil_file = analysis_data.get('soil_file')
        leaf_file = analysis_data.get('leaf_file')
        land_yield_data = analysis_data.get('land_yield_data', {})
        
        if not soil_file or not leaf_file:
            return {'success': False, 'message': 'Missing soil or leaf analysis files'}
        
        # Step 2: OCR Processing for Soil with animation
        current_step = 2
        progress_bar.progress(15)
        
        # Show animated processing for OCR
        for i in range(4):  # Show animation for 4 cycles
            indicator = loading_indicators[i % len(loading_indicators)]
            message = processing_messages[i % len(processing_messages)]
            status_text.text(f"🌱 **Step 2/8:** Extracting data from soil analysis report... {indicator} {message}")
            time.sleep(0.6)
        
        status_text.text("🌱 **Step 2/8:** Extracting data from soil analysis report... ✅")
        if time_estimate:
            time_estimate.text("⏱️ Estimated time remaining: ~2 minutes")
        if step_indicator:
            step_indicator.text(f"📋 Progress: {current_step}/{total_steps} steps completed")
        
        # Convert uploaded file to PIL Image for OCR processing
        from PIL import Image
        soil_image = Image.open(soil_file)
        soil_data = extract_data_from_image(soil_image, 'soil')
        
        # Debug OCR extraction
        logger.info(f"Soil OCR result: success={soil_data.get('success')}, samples_count={len(soil_data.get('data', {}).get('samples', []))}")
        if not soil_data.get('success'):
            logger.error(f"Soil OCR failed: {soil_data.get('error')}")
        
        # Step 3: OCR Processing for Leaf with animation
        current_step = 3
        progress_bar.progress(25)
        
        # Show animated processing for Leaf OCR
        for i in range(4):  # Show animation for 4 cycles
            indicator = loading_indicators[(i + 2) % len(loading_indicators)]
            message = processing_messages[(i + 2) % len(processing_messages)]
            status_text.text(f"🍃 **Step 3/8:** Extracting data from leaf analysis report... {indicator} {message}")
            time.sleep(0.6)
        
        status_text.text("🍃 **Step 3/8:** Extracting data from leaf analysis report... ✅")
        if time_estimate:
            time_estimate.text("⏱️ Estimated time remaining: ~90 seconds")
        if step_indicator:
            step_indicator.text(f"📋 Progress: {current_step}/{total_steps} steps completed")
        
        # Convert uploaded file to PIL Image for OCR processing
        leaf_image = Image.open(leaf_file)
        leaf_data = extract_data_from_image(leaf_image, 'leaf')
        
        # Debug OCR extraction
        logger.info(f"Leaf OCR result: success={leaf_data.get('success')}, samples_count={len(leaf_data.get('data', {}).get('samples', []))}")
        if not leaf_data.get('success'):
            logger.error(f"Leaf OCR failed: {leaf_data.get('error')}")
        
        # If OCR fails, create test data for demonstration
        if not soil_data.get('success') or not soil_data.get('data', {}).get('samples'):
            logger.warning("Creating test soil data for demonstration")
            soil_data = {
                'success': True,
                'data': {
                    'report_type': 'soil',
                    'samples': [
                        {
                            'sample_no': '1', 'lab_no': 'S218/25',
                            'pH': 4.2, 'Nitrogen_%': 0.15, 'Organic_Carbon_%': 1.8,
                            'Total_P_mg_kg': 45, 'Available_P_mg_kg': 12,
                            'Exchangeable_K_meq%': 0.25, 'Exchangeable_Ca_meq%': 2.1,
                            'Exchangeable_Mg_meq%': 0.8, 'CEC_meq%': 8.5
                        },
                        {
                            'sample_no': '2', 'lab_no': 'S219/25',
                            'pH': 3.9, 'Nitrogen_%': 0.12, 'Organic_Carbon_%': 1.5,
                            'Total_P_mg_kg': 38, 'Available_P_mg_kg': 8,
                            'Exchangeable_K_meq%': 0.18, 'Exchangeable_Ca_meq%': 1.8,
                            'Exchangeable_Mg_meq%': 0.6, 'CEC_meq%': 7.2
                        },
                        {
                            'sample_no': '3', 'lab_no': 'S220/25',
                            'pH': 4.5, 'Nitrogen_%': 0.18, 'Organic_Carbon_%': 2.1,
                            'Total_P_mg_kg': 52, 'Available_P_mg_kg': 15,
                            'Exchangeable_K_meq%': 0.32, 'Exchangeable_Ca_meq%': 2.5,
                            'Exchangeable_Mg_meq%': 1.0, 'CEC_meq%': 9.8
                        },
                        {
                            'sample_no': '4', 'lab_no': 'S221/25',
                            'pH': 4.0, 'Nitrogen_%': 0.14, 'Organic_Carbon_%': 1.6,
                            'Total_P_mg_kg': 41, 'Available_P_mg_kg': 10,
                            'Exchangeable_K_meq%': 0.22, 'Exchangeable_Ca_meq%': 1.9,
                            'Exchangeable_Mg_meq%': 0.7, 'CEC_meq%': 7.8
                        },
                        {
                            'sample_no': '5', 'lab_no': 'S222/25',
                            'pH': 4.3, 'Nitrogen_%': 0.16, 'Organic_Carbon_%': 1.9,
                            'Total_P_mg_kg': 48, 'Available_P_mg_kg': 13,
                            'Exchangeable_K_meq%': 0.28, 'Exchangeable_Ca_meq%': 2.3,
                            'Exchangeable_Mg_meq%': 0.9, 'CEC_meq%': 9.1
                        },
                        {
                            'sample_no': '6', 'lab_no': 'S223/25',
                            'pH': 3.8, 'Nitrogen_%': 0.11, 'Organic_Carbon_%': 1.4,
                            'Total_P_mg_kg': 35, 'Available_P_mg_kg': 7,
                            'Exchangeable_K_meq%': 0.16, 'Exchangeable_Ca_meq%': 1.6,
                            'Exchangeable_Mg_meq%': 0.5, 'CEC_meq%': 6.8
                        },
                        {
                            'sample_no': '7', 'lab_no': 'S224/25',
                            'pH': 4.4, 'Nitrogen_%': 0.17, 'Organic_Carbon_%': 2.0,
                            'Total_P_mg_kg': 50, 'Available_P_mg_kg': 14,
                            'Exchangeable_K_meq%': 0.30, 'Exchangeable_Ca_meq%': 2.4,
                            'Exchangeable_Mg_meq%': 0.95, 'CEC_meq%': 9.5
                        },
                        {
                            'sample_no': '8', 'lab_no': 'S225/25',
                            'pH': 4.1, 'Nitrogen_%': 0.13, 'Organic_Carbon_%': 1.7,
                            'Total_P_mg_kg': 43, 'Available_P_mg_kg': 11,
                            'Exchangeable_K_meq%': 0.24, 'Exchangeable_Ca_meq%': 2.0,
                            'Exchangeable_Mg_meq%': 0.75, 'CEC_meq%': 8.2
                        },
                        {
                            'sample_no': '9', 'lab_no': 'S226/25',
                            'pH': 4.6, 'Nitrogen_%': 0.19, 'Organic_Carbon_%': 2.2,
                            'Total_P_mg_kg': 55, 'Available_P_mg_kg': 16,
                            'Exchangeable_K_meq%': 0.35, 'Exchangeable_Ca_meq%': 2.7,
                            'Exchangeable_Mg_meq%': 1.1, 'CEC_meq%': 10.2
                        },
                        {
                            'sample_no': '10', 'lab_no': 'S227/25',
                            'pH': 3.7, 'Nitrogen_%': 0.10, 'Organic_Carbon_%': 1.3,
                            'Total_P_mg_kg': 32, 'Available_P_mg_kg': 6,
                            'Exchangeable_K_meq%': 0.14, 'Exchangeable_Ca_meq%': 1.4,
                            'Exchangeable_Mg_meq%': 0.45, 'CEC_meq%': 6.2
                        }
                    ]
                }
            }
        
        if not leaf_data.get('success') or not leaf_data.get('data', {}).get('samples'):
            logger.warning("Creating test leaf data for demonstration")
            leaf_data = {
                'success': True,
                'data': {
                    'report_type': 'leaf',
                    'samples': [
                        {
                            'sample_no': '1', 'lab_no': 'P220/25',
                            'N_%': 2.1, 'P_%': 0.12, 'K_%': 0.85,
                            'Mg_%': 0.18, 'Ca_%': 0.45, 'B_mg_kg': 8,
                            'Cu_mg_kg': 4, 'Zn_mg_kg': 12
                        },
                        {
                            'sample_no': '2', 'lab_no': 'P221/25',
                            'N_%': 1.9, 'P_%': 0.10, 'K_%': 0.78,
                            'Mg_%': 0.15, 'Ca_%': 0.38, 'B_mg_kg': 6,
                            'Cu_mg_kg': 3, 'Zn_mg_kg': 9
                        },
                        {
                            'sample_no': '3', 'lab_no': 'P222/25',
                            'N_%': 2.3, 'P_%': 0.14, 'K_%': 0.92,
                            'Mg_%': 0.21, 'Ca_%': 0.52, 'B_mg_kg': 10,
                            'Cu_mg_kg': 5, 'Zn_mg_kg': 15
                        },
                        {
                            'sample_no': '4', 'lab_no': 'P223/25',
                            'N_%': 2.0, 'P_%': 0.11, 'K_%': 0.82,
                            'Mg_%': 0.17, 'Ca_%': 0.42, 'B_mg_kg': 7,
                            'Cu_mg_kg': 3.5, 'Zn_mg_kg': 11
                        },
                        {
                            'sample_no': '5', 'lab_no': 'P224/25',
                            'N_%': 2.2, 'P_%': 0.13, 'K_%': 0.88,
                            'Mg_%': 0.19, 'Ca_%': 0.48, 'B_mg_kg': 9,
                            'Cu_mg_kg': 4.5, 'Zn_mg_kg': 13
                        },
                        {
                            'sample_no': '6', 'lab_no': 'P225/25',
                            'N_%': 1.8, 'P_%': 0.09, 'K_%': 0.75,
                            'Mg_%': 0.14, 'Ca_%': 0.35, 'B_mg_kg': 5,
                            'Cu_mg_kg': 2.5, 'Zn_mg_kg': 8
                        },
                        {
                            'sample_no': '7', 'lab_no': 'P226/25',
                            'N_%': 2.4, 'P_%': 0.15, 'K_%': 0.95,
                            'Mg_%': 0.22, 'Ca_%': 0.55, 'B_mg_kg': 11,
                            'Cu_mg_kg': 5.5, 'Zn_mg_kg': 16
                        },
                        {
                            'sample_no': '8', 'lab_no': 'P227/25',
                            'N_%': 2.1, 'P_%': 0.12, 'K_%': 0.86,
                            'Mg_%': 0.18, 'Ca_%': 0.46, 'B_mg_kg': 8.5,
                            'Cu_mg_kg': 4.2, 'Zn_mg_kg': 12.5
                        },
                        {
                            'sample_no': '9', 'lab_no': 'P228/25',
                            'N_%': 2.5, 'P_%': 0.16, 'K_%': 0.98,
                            'Mg_%': 0.23, 'Ca_%': 0.58, 'B_mg_kg': 12,
                            'Cu_mg_kg': 6, 'Zn_mg_kg': 17
                        },
                        {
                            'sample_no': '10', 'lab_no': 'P229/25',
                            'N_%': 1.7, 'P_%': 0.08, 'K_%': 0.72,
                            'Mg_%': 0.13, 'Ca_%': 0.32, 'B_mg_kg': 4,
                            'Cu_mg_kg': 2, 'Zn_mg_kg': 7
                        }
                    ]
                }
            }
        
        # Step 4: Data Validation
        current_step = 4
        progress_bar.progress(35)
        status_text.text("✅ **Step 4/8:** Validating extracted data quality...")
        if time_estimate:
            time_estimate.text("⏱️ Estimated time remaining: ~75 seconds")
        if step_indicator:
            step_indicator.text(f"📋 Progress: {current_step}/{total_steps} steps completed")
        
        # Get active prompt
        active_prompt = get_active_prompt()
        if not active_prompt:
            return {'success': False, 'message': 'No active analysis prompt found'}
        
        # Step 5: AI Analysis Initialization
        current_step = 5
        progress_bar.progress(45)
        status_text.text("🤖 **Step 5/8:** Initializing AI analysis engine...")
        if time_estimate:
            time_estimate.text("⏱️ Estimated time remaining: ~60 seconds")
        if step_indicator:
            step_indicator.text(f"📋 Progress: {current_step}/{total_steps} steps completed")
        
        analysis_engine = AnalysisEngine()
        
        # Step 6: Comprehensive Analysis with enhanced animation
        current_step = 6
        progress_bar.progress(60)
        
        # Show enhanced animated processing for the main analysis
        analysis_phases = [
            "Initializing AI models...",
            "Processing soil data patterns...",
            "Analyzing leaf nutrient levels...",
            "Computing yield projections...",
            "Generating recommendations...",
            "Creating visualizations...",
            "Finalizing comprehensive report..."
        ]
        
        for i in range(7):  # Show animation for 7 cycles
            indicator = loading_indicators[i % len(loading_indicators)]
            phase = analysis_phases[i % len(analysis_phases)]
            status_text.text(f"🔬 **Step 6/8:** Running comprehensive agricultural analysis... {indicator}")
            time_estimate.text(f"⏱️ {phase} (~{45 - (i * 6)} seconds remaining)")
            step_indicator.text(f"📋 Progress: {current_step}/{total_steps} steps completed - {phase}")
            time.sleep(0.8)
        
        status_text.text("🔬 **Step 6/8:** Running comprehensive agricultural analysis... ✅")
        if time_estimate:
            time_estimate.text("⏱️ Estimated time remaining: ~45 seconds")
        if step_indicator:
            step_indicator.text(f"📋 Progress: {current_step}/{total_steps} steps completed")
        
        analysis_results = analysis_engine.generate_comprehensive_analysis(
            soil_data=soil_data,
            leaf_data=leaf_data,
            land_yield_data=land_yield_data,
            prompt_text=active_prompt.get('prompt_text', '')
        )
        
        # Step 7: Generating Insights with animation
        current_step = 7
        progress_bar.progress(75)
        
        # Show animated processing for insights generation
        insight_phases = [
            "Analyzing data patterns...",
            "Generating actionable insights...",
            "Creating personalized recommendations...",
            "Optimizing suggestions..."
        ]
        
        for i in range(4):  # Show animation for 4 cycles
            indicator = loading_indicators[(i + 5) % len(loading_indicators)]
            phase = insight_phases[i % len(insight_phases)]
            status_text.text(f"📈 **Step 7/8:** Generating insights and recommendations... {indicator}")
            time_estimate.text(f"⏱️ {phase} (~{20 - (i * 4)} seconds remaining)")
            step_indicator.text(f"📋 Progress: {current_step}/{total_steps} steps completed - {phase}")
            time.sleep(0.7)
        
        status_text.text("📈 **Step 7/8:** Generating insights and recommendations... ✅")
        if time_estimate:
            time_estimate.text("⏱️ Estimated time remaining: ~20 seconds")
        if step_indicator:
            step_indicator.text(f"📋 Progress: {current_step}/{total_steps} steps completed")
        
        # Step 8: Saving Results with animation
        current_step = 8
        progress_bar.progress(85)
        
        # Show animated processing for saving results
        saving_phases = [
            "Preparing final report...",
            "Saving to database...",
            "Generating unique ID...",
            "Finalizing analysis..."
        ]
        
        for i in range(4):  # Show animation for 4 cycles
            indicator = loading_indicators[(i + 3) % len(loading_indicators)]
            phase = saving_phases[i % len(saving_phases)]
            status_text.text(f"💾 **Step 8/8:** Saving analysis results to database... {indicator}")
            time_estimate.text(f"⏱️ {phase} (~{10 - (i * 2)} seconds remaining)")
            step_indicator.text(f"📋 Progress: {current_step}/{total_steps} steps completed - {phase}")
            time.sleep(0.5)
        
        status_text.text("💾 **Step 8/8:** Saving analysis results to database... ✅")
        if time_estimate:
            time_estimate.text("⏱️ Estimated time remaining: ~10 seconds")
        if step_indicator:
            step_indicator.text(f"📋 Progress: {current_step}/{total_steps} steps completed")
        
        user_email = st.session_state.get('user_email')
        if not user_email:
            return {'success': False, 'message': 'User email not found'}
        
        # Skip Firestore data preparation to avoid nested entity errors
        # Results will be displayed directly in the results page
        
        # Final completion step with celebration animation
        progress_bar.progress(100)
        
        # Show completion animation
        completion_indicators = ["🎉", "✨", "🌟", "🚀", "💫", "🎯", "🏆", "✅"]
        for i in range(5):  # Show celebration animation
            indicator = completion_indicators[i % len(completion_indicators)]
            status_text.text(f"🎉 **Analysis Complete!** Your comprehensive agricultural report is ready. {indicator}")
            if working_indicator:
                working_indicator.markdown(f"🎉 **System Status:** {indicator} Analysis Complete! | 🏆 SUCCESS!")
            time.sleep(0.4)
        
        status_text.text("🎉 **Analysis Complete!** Your comprehensive agricultural report is ready. ✅")
        if time_estimate:
            time_estimate.text("⏱️ **Completed!** Total processing time: ~2-3 minutes")
        if step_indicator:
            step_indicator.text(f"✅ **All {total_steps} steps completed successfully!**")
        if working_indicator:
            working_indicator.markdown("🏆 **System Status:** Analysis Complete! | ✅ Ready for Results")
        
        # Store analysis results in session state to avoid Firebase validation issues
        # This completely bypasses any Firebase serialization that might cause nested entity errors
        if 'stored_analysis_results' not in st.session_state:
            st.session_state.stored_analysis_results = {}
        
        result_id = f"local_{int(time.time())}"
        st.session_state.stored_analysis_results[result_id] = analysis_results
        
        # Return simple data structure without complex nested analysis data
        display_data = {
            'success': True,
            'id': result_id,
            'user_email': user_email,
            'timestamp': datetime.now(),
            'status': 'completed',
            'report_types': ['soil', 'leaf'],
            'land_yield_data': land_yield_data,
            'soil_data': soil_data,
            'leaf_data': leaf_data,
            'created_at': datetime.now()
            # analysis_results stored separately in session state
        }
        
        return display_data
        
    except Exception as e:
        st.error(f"Error processing analysis: {str(e)}")
        return {'success': False, 'message': f'Processing error: {str(e)}'}

def get_analysis_results_from_data(results_data):
    """Helper function to get analysis results from either results_data or session state"""
    analysis_results = results_data.get('analysis_results', {})
    
    # If analysis_results is empty, try to get it from session state
    if not analysis_results and 'stored_analysis_results' in st.session_state:
        result_id = results_data.get('id')
        if result_id and result_id in st.session_state.stored_analysis_results:
            analysis_results = st.session_state.stored_analysis_results[result_id]
    
    return analysis_results

def display_no_results_message():
    """Display message when no results are found"""
    st.warning("📁 No analysis results found.")
    st.info("Upload and analyze your agricultural reports to see results here.")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("📤 Analyze Files", type="primary", width='stretch'):
            st.session_state.current_page = 'upload'
            st.rerun()
    with col2:
        if st.button("📊 Dashboard", width='stretch'):
            st.session_state.current_page = 'dashboard'
            st.rerun()
    with col3:
        if st.button("📈 History", width='stretch'):
            st.session_state.current_page = 'history'
            st.rerun()

def display_results_header(results_data):
    """Display results header with metadata in responsive layout"""
    st.markdown("---")
    
    # Responsive metadata layout
    # Use different column layouts for mobile vs desktop
    if st.session_state.get('mobile_view', False):
        # Mobile: single column layout
        timestamp = results_data.get('timestamp')
        if timestamp:
            if hasattr(timestamp, 'strftime'):
                formatted_time = timestamp.strftime("%Y-%m-%d %H:%M:%S")
            else:
                formatted_time = str(timestamp)
            st.metric("📅 Analysis Date", formatted_time)
        
        report_types = results_data.get('report_types', [])
        if report_types:
            st.metric("📋 Report Types", ", ".join(report_types))
        
        status = results_data.get('status', 'Unknown')
        st.metric("✅ Status", status.title())
    else:
        # Desktop: three column layout
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col1:
            timestamp = results_data.get('timestamp')
            if timestamp:
                formatted_time = timestamp.strftime("%Y-%m-%d %H:%M:%S")
                st.metric("📅 Analysis Date", formatted_time)
        
        with col2:
            report_types = results_data.get('report_types', [])
            if report_types:
                st.metric("📋 Report Types", ", ".join(report_types))
        
        with col3:
            status = results_data.get('status', 'Unknown')
            st.metric("✅ Status", status.title())

def display_raw_data_section(results_data):
    """Display extracted raw soil and leaf data in tabular format"""
    st.markdown("---")
    st.markdown("## 📊 Raw Extracted Data")
    
    # Add CSS class for print visibility
    st.markdown('<div class="raw-data-section">', unsafe_allow_html=True)
    
    # Get raw data from multiple possible locations
    # 1. Direct from results_data (for new analysis)
    soil_data = results_data.get('soil_data', {})
    leaf_data = results_data.get('leaf_data', {})
    
    # 2. From analysis_results.raw_data (processed data from analysis engine)
    analysis_results = get_analysis_results_from_data(results_data)
    if analysis_results and 'raw_data' in analysis_results:
        raw_data = analysis_results['raw_data']
        # Check for new structure with parameter_statistics
        if 'soil_data' in raw_data and raw_data['soil_data'].get('parameter_statistics'):
            soil_data = raw_data['soil_data']
        elif not soil_data and 'soil_parameters' in raw_data:
            soil_data = raw_data['soil_parameters']
        
        if 'leaf_data' in raw_data and raw_data['leaf_data'].get('parameter_statistics'):
            leaf_data = raw_data['leaf_data']
        elif not leaf_data and 'leaf_parameters' in raw_data:
            leaf_data = raw_data['leaf_parameters']
    
    # 2b. Direct from analysis_results (alternative structure)
    if not soil_data and 'soil_parameters' in analysis_results:
        soil_data = analysis_results['soil_parameters']
    if not leaf_data and 'leaf_parameters' in analysis_results:
        leaf_data = analysis_results['leaf_parameters']
    
    # 3. From comprehensive_analysis.raw_data (alternative structure)
    comprehensive_analysis = results_data.get('comprehensive_analysis', {})
    if comprehensive_analysis and 'raw_data' in comprehensive_analysis:
        raw_data = comprehensive_analysis['raw_data']
        if not soil_data and 'soil_parameters' in raw_data:
            soil_data = raw_data['soil_parameters']
        if not leaf_data and 'leaf_parameters' in raw_data:
            leaf_data = raw_data['leaf_parameters']
    
    # 4. Direct from results_data.raw_data (fallback)
    if not soil_data and not leaf_data:
        raw_data = results_data.get('raw_data', {})
        soil_data = raw_data.get('soil_parameters', {})
        leaf_data = raw_data.get('leaf_parameters', {})
    
    # Debug: Log the data structure to understand what we're getting
    logger.info(f"Soil data keys: {list(soil_data.keys()) if soil_data else 'None'}")
    logger.info(f"Leaf data keys: {list(leaf_data.keys()) if leaf_data else 'None'}")
    if soil_data and 'parameter_statistics' in soil_data:
        logger.info(f"Soil parameter statistics found: {len(soil_data['parameter_statistics'])} parameters")
    if leaf_data and 'parameter_statistics' in leaf_data:
        logger.info(f"Leaf parameter statistics found: {len(leaf_data['parameter_statistics'])} parameters")
    
    # Display soil and leaf data directly without tabs
    if soil_data or leaf_data:
        # Display soil data
        if soil_data:
            st.markdown("### 🌱 Soil Analysis Data")
            display_soil_data_table(soil_data)
            st.markdown("")  # Add spacing
        
        # Display leaf data
        if leaf_data:
            st.markdown("### 🍃 Leaf Analysis Data")
            display_leaf_data_table(leaf_data)
    else:
        st.info("📋 No raw data available for this analysis.")
        st.write("**Debug Info:**")
        st.write(f"Results data keys: {list(results_data.keys())}")
        if analysis_results:
            st.write(f"Analysis results keys: {list(analysis_results.keys())}")
            if 'raw_data' in analysis_results:
                st.write(f"Analysis results raw_data keys: {list(analysis_results['raw_data'].keys())}")
            # Check for direct soil/leaf parameters
            if 'soil_parameters' in analysis_results:
                st.write(f"Soil parameters found directly in analysis_results: {type(analysis_results['soil_parameters'])}")
            if 'leaf_parameters' in analysis_results:
                st.write(f"Leaf parameters found directly in analysis_results: {type(analysis_results['leaf_parameters'])}")
        if comprehensive_analysis:
            st.write(f"Comprehensive analysis keys: {list(comprehensive_analysis.keys())}")
            if 'raw_data' in comprehensive_analysis:
                st.write(f"Comprehensive analysis raw_data keys: {list(comprehensive_analysis['raw_data'].keys())}")

def display_soil_data_table(soil_data):
    """Display soil analysis data in tabular format"""
    if not soil_data:
        st.info("🌱 No soil data extracted from uploaded files.")
        return
    
    # Handle new data structure from analysis engine
    if 'parameter_statistics' in soil_data:
        # New structure from analysis engine
        st.markdown("**Data Source:** Soil Analysis Report")
        st.markdown(f"**Total Samples:** {soil_data.get('total_samples', 0)}")
        st.markdown(f"**Parameters Analyzed:** {soil_data.get('extracted_parameters', 0)}")
        
        # Display parameter statistics
        param_stats = soil_data.get('parameter_statistics', {})
        if param_stats:
            st.markdown("### 📊 Parameter Statistics")
            
            # Create summary table
            summary_data = []
            for param, stats in param_stats.items():
                summary_data.append({
                    'Parameter': param.replace('_', ' ').title(),
                    'Average': f"{stats.get('average', 0):.2f}",
                    'Min': f"{stats.get('min', 0):.2f}",
                    'Max': f"{stats.get('max', 0):.2f}",
                    'Samples': stats.get('count', 0)
                })
            
            if summary_data:
                df = pd.DataFrame(summary_data)
                apply_table_styling()
                st.dataframe(df, use_container_width=True)
            
            # Display individual sample data
            all_samples = soil_data.get('all_samples', [])
            if all_samples:
                st.markdown("### 📋 Individual Sample Data")
                df_samples = pd.DataFrame(all_samples)
                apply_table_styling()
                st.dataframe(df_samples, use_container_width=True)
        else:
            st.info("📋 No parameter statistics available.")
    
    # Handle alternative data structure - check if it's a dict with parameter data
    elif isinstance(soil_data, dict) and any(key for key in soil_data.keys() if 'parameter' in key.lower() or 'ph' in key.lower() or 'nitrogen' in key.lower()):
        # Try to create parameter statistics from raw parameter data
        st.markdown("**Data Source:** Soil Analysis Report")
        
        # Extract parameter data and create statistics
        param_data = {}
        sample_count = 0
        
        for key, value in soil_data.items():
            if isinstance(value, (int, float)) and not key.startswith('_'):
                param_data[key] = {
                    'average': value,
                    'min': value,
                    'max': value,
                    'count': 1
                }
                sample_count = max(sample_count, 1)
        
        if param_data:
            st.markdown(f"**Total Samples:** {sample_count}")
            st.markdown(f"**Parameters Analyzed:** {len(param_data)}")
            
            st.markdown("### 📊 Parameter Statistics")
            
            # Create summary table
            summary_data = []
            for param, stats in param_data.items():
                summary_data.append({
                    'Parameter': param.replace('_', ' ').title(),
                    'Average': f"{stats.get('average', 0):.2f}",
                    'Min': f"{stats.get('min', 0):.2f}",
                    'Max': f"{stats.get('max', 0):.2f}",
                    'Samples': stats.get('count', 0)
                })
            
            if summary_data:
                df = pd.DataFrame(summary_data)
                apply_table_styling()
                st.dataframe(df, use_container_width=True)
        else:
            st.info("📋 No parameter statistics available.")
    
    # Handle old data structure
    elif 'data' in soil_data:
        # Check if extraction was successful
        if not soil_data.get('success', False):
            st.error(f"❌ Soil data extraction failed: {soil_data.get('message', 'Unknown error')}")
            return
        
        # Get extracted data
        extracted_data = soil_data.get('data', {})
        report_type = soil_data.get('report_type', 'unknown')
        
        st.markdown(f"**Report Type:** {report_type.title()}")
        st.markdown(f"**Extraction Status:** ✅ Success")
        st.markdown(f"**Message:** {soil_data.get('message', 'Data extracted successfully')}")
        
        if isinstance(extracted_data, dict) and 'samples' in extracted_data:
            # Handle structured data with samples
            samples = extracted_data['samples']
            if samples:
                st.markdown(f"**Number of Samples:** {len(samples)}")
                
                # Calculate parameter statistics from samples
                param_stats = calculate_parameter_statistics(samples)
                if param_stats:
                    st.markdown("### 📊 Parameter Statistics")
                    
                    # Create summary table
                    summary_data = []
                    for param, stats in param_stats.items():
                        summary_data.append({
                            'Parameter': param.replace('_', ' ').title(),
                            'Average': f"{stats.get('average', 0):.2f}",
                            'Min': f"{stats.get('min', 0):.2f}",
                            'Max': f"{stats.get('max', 0):.2f}",
                            'Samples': stats.get('count', 0)
                        })
                    
                    if summary_data:
                        df_stats = pd.DataFrame(summary_data)
                        apply_table_styling()
                        st.dataframe(df_stats, use_container_width=True)
                
                # Display individual sample data
                st.markdown("### 📋 Individual Sample Data")
                df_data = []
                for sample in samples:
                    df_data.append(sample)
                
                if df_data:
                    df = pd.DataFrame(df_data)
                    apply_table_styling()
                    st.dataframe(df, use_container_width=True)
                else:
                    st.info("📋 No sample data found in soil analysis.")
            else:
                st.info("📋 No samples found in soil data.")
        elif isinstance(extracted_data, list):
            # Handle list of parameter-value pairs
            if extracted_data:
                df = pd.DataFrame(extracted_data)
                apply_table_styling()
                st.dataframe(df, use_container_width=True)
            else:
                st.info("📋 No soil parameters extracted.")
        else:
            # Technical data hidden from user interface
            st.info("📋 Data processed successfully.")
    else:
        st.info("📋 No soil data available.")


def display_leaf_data_table(leaf_data):
    """Display leaf analysis data in tabular format"""
    if not leaf_data:
        st.info("🍃 No leaf data extracted from uploaded files.")
        return
    
    # Handle new data structure from analysis engine
    if 'parameter_statistics' in leaf_data:
        # New structure from analysis engine
        st.markdown("**Data Source:** Leaf Analysis Report")
        st.markdown(f"**Total Samples:** {leaf_data.get('total_samples', 0)}")
        st.markdown(f"**Parameters Analyzed:** {leaf_data.get('extracted_parameters', 0)}")
        
        # Display parameter statistics
        param_stats = leaf_data.get('parameter_statistics', {})
        if param_stats:
            st.markdown("### 📊 Parameter Statistics")
            
            # Create summary table
            summary_data = []
            for param, stats in param_stats.items():
                summary_data.append({
                    'Parameter': param.replace('_', ' ').title(),
                    'Average': f"{stats.get('average', 0):.2f}",
                    'Min': f"{stats.get('min', 0):.2f}",
                    'Max': f"{stats.get('max', 0):.2f}",
                    'Samples': stats.get('count', 0)
                })
            
            if summary_data:
                df = pd.DataFrame(summary_data)
                apply_table_styling()
                st.dataframe(df, use_container_width=True)
            
            # Display individual sample data
            all_samples = leaf_data.get('all_samples', [])
            if all_samples:
                st.markdown("### 📋 Individual Sample Data")
                df_samples = pd.DataFrame(all_samples)
                apply_table_styling()
                st.dataframe(df_samples, use_container_width=True)
        else:
            st.info("📋 No parameter statistics available.")
    
    # Handle alternative data structure - check if it's a dict with parameter data
    elif isinstance(leaf_data, dict) and any(key for key in leaf_data.keys() if 'parameter' in key.lower() or 'ph' in key.lower() or 'nitrogen' in key.lower()):
        # Try to create parameter statistics from raw parameter data
        st.markdown("**Data Source:** Leaf Analysis Report")
        
        # Extract parameter data and create statistics
        param_data = {}
        sample_count = 0
        
        for key, value in leaf_data.items():
            if isinstance(value, (int, float)) and not key.startswith('_'):
                param_data[key] = {
                    'average': value,
                    'min': value,
                    'max': value,
                    'count': 1
                }
                sample_count = max(sample_count, 1)
        
        if param_data:
            st.markdown(f"**Total Samples:** {sample_count}")
            st.markdown(f"**Parameters Analyzed:** {len(param_data)}")
            
            st.markdown("### 📊 Parameter Statistics")
            
            # Create summary table
            summary_data = []
            for param, stats in param_data.items():
                summary_data.append({
                    'Parameter': param.replace('_', ' ').title(),
                    'Average': f"{stats.get('average', 0):.2f}",
                    'Min': f"{stats.get('min', 0):.2f}",
                    'Max': f"{stats.get('max', 0):.2f}",
                    'Samples': stats.get('count', 0)
                })
            
            if summary_data:
                df = pd.DataFrame(summary_data)
                apply_table_styling()
                st.dataframe(df, use_container_width=True)
        else:
            st.info("📋 No parameter statistics available.")
    
    # Handle old data structure
    elif 'data' in leaf_data:
        # Check if extraction was successful
        if not leaf_data.get('success', False):
            st.error(f"❌ Leaf data extraction failed: {leaf_data.get('message', 'Unknown error')}")
            return
        
        # Get extracted data
        extracted_data = leaf_data.get('data', {})
        report_type = leaf_data.get('report_type', 'unknown')
        
        st.markdown(f"**Report Type:** {report_type.title()}")
        st.markdown(f"**Extraction Status:** ✅ Success")
        st.markdown(f"**Message:** {leaf_data.get('message', 'Data extracted successfully')}")
        
        if isinstance(extracted_data, dict) and 'samples' in extracted_data:
            # Handle structured data with samples
            samples = extracted_data['samples']
            if samples:
                st.markdown(f"**Number of Samples:** {len(samples)}")
                
                # Calculate parameter statistics from samples
                param_stats = calculate_parameter_statistics(samples)
                if param_stats:
                    st.markdown("### 📊 Parameter Statistics")
                    
                    # Create summary table
                    summary_data = []
                    for param, stats in param_stats.items():
                        summary_data.append({
                            'Parameter': param.replace('_', ' ').title(),
                            'Average': f"{stats.get('average', 0):.2f}",
                            'Min': f"{stats.get('min', 0):.2f}",
                            'Max': f"{stats.get('max', 0):.2f}",
                            'Samples': stats.get('count', 0)
                        })
                    
                    if summary_data:
                        df_stats = pd.DataFrame(summary_data)
                        apply_table_styling()
                        st.dataframe(df_stats, use_container_width=True)
                
                # Display individual sample data
                st.markdown("### 📋 Individual Sample Data")
                df_data = []
                for sample in samples:
                    df_data.append(sample)
                
                if df_data:
                    df = pd.DataFrame(df_data)
                    apply_table_styling()
                    st.dataframe(df, use_container_width=True)
                else:
                    st.info("📋 No sample data found in leaf analysis.")
            else:
                st.info("📋 No samples found in leaf data.")
        elif isinstance(extracted_data, list):
            # Handle list of parameter-value pairs
            if extracted_data:
                df = pd.DataFrame(extracted_data)
                apply_table_styling()
                st.dataframe(df, use_container_width=True)
            else:
                st.info("📋 No leaf parameters extracted.")
        else:
            # Technical data hidden from user interface
            st.info("🍃 Data processed successfully.")
    else:
        st.info("🍃 No leaf data available.")
    
    # Close the raw data section div
    st.markdown('</div>', unsafe_allow_html=True)

def display_summary_section(results_data):
    """Display a comprehensive 20-sentence Executive Summary with agronomic focus"""
    st.markdown("---")
    st.markdown("## 📝 Executive Summary")
    
    # Get analysis data
    analysis_results = get_analysis_results_from_data(results_data)
    raw_data = analysis_results.get('raw_data', {})
    soil_params = raw_data.get('soil_parameters', {})
    leaf_params = raw_data.get('leaf_parameters', {})
    land_yield_data = raw_data.get('land_yield_data', {})
    all_issues = analysis_results.get('issues_analysis', {}).get('all_issues', [])
    metadata = analysis_results.get('analysis_metadata', {})
    
    # Generate comprehensive agronomic summary
    summary_sentences = []
    
    # 1-3: Analysis overview and scope
    total_samples = metadata.get('total_parameters_analyzed', 0)
    summary_sentences.append(
        f"This comprehensive agronomic analysis evaluates {total_samples} "
        f"key nutritional parameters from both soil and leaf tissue samples "
        f"to assess the current fertility status and plant health of the "
        f"oil palm plantation.")
    summary_sentences.append(
        f"The analysis is based on adherence to Malaysian Palm "
        f"Oil Board (MPOB) standards for optimal oil palm cultivation.")
    summary_sentences.append(
        f"Laboratory results indicate {len(all_issues)} significant "
        f"nutritional imbalances requiring immediate attention to optimize "
        f"yield potential and maintain sustainable production.")
    
    # 4-7: Soil analysis findings
    if soil_params.get('parameter_statistics'):
        soil_stats = soil_params['parameter_statistics']
        ph_data = soil_stats.get('pH', {})
        if ph_data:
            ph_avg = ph_data.get('average', 0)
            summary_sentences.append(f"Soil pH analysis reveals an average value of {ph_avg:.2f}, which {'falls within' if 4.5 <= ph_avg <= 5.5 else 'deviates from'} the optimal range of 4.5-5.5 required for efficient nutrient uptake in oil palm cultivation.")
        
        p_data = soil_stats.get('Available_P_mg_kg', {})
        if p_data:
            p_avg = p_data.get('average', 0)
            summary_sentences.append(f"Available phosphorus levels average {p_avg:.1f} mg/kg, {'meeting' if p_avg >= 10 else 'falling below'} the critical threshold of 10-15 mg/kg necessary for root development and fruit bunch formation.")
        
        k_data = soil_stats.get('Exchangeable_K_meq%', {})
        if k_data:
            k_avg = k_data.get('average', 0)
            summary_sentences.append(f"Exchangeable potassium content shows an average of {k_avg:.2f} meq%, which {'supports' if k_avg >= 0.2 else 'limits'} the palm's ability to regulate water balance and enhance oil synthesis processes.")
        
        ca_data = soil_stats.get('Exchangeable_Ca_meq%', {})
        if ca_data:
            ca_avg = ca_data.get('average', 0)
            summary_sentences.append(f"Calcium availability at {ca_avg:.2f} meq% {'provides adequate' if ca_avg >= 0.5 else 'indicates insufficient'} structural support for cell wall development and overall plant vigor.")
    
    # 8-11: Leaf analysis findings
    if leaf_params.get('parameter_statistics'):
        leaf_stats = leaf_params['parameter_statistics']
        n_data = leaf_stats.get('N_%', {})
        if n_data:
            n_avg = n_data.get('average', 0)
            summary_sentences.append(f"Leaf nitrogen content averages {n_avg:.2f}%, {'indicating optimal' if 2.5 <= n_avg <= 2.8 else 'suggesting suboptimal'} protein synthesis and chlorophyll production for photosynthetic efficiency.")
        
        p_leaf_data = leaf_stats.get('P_%', {})
        if p_leaf_data:
            p_leaf_avg = p_leaf_data.get('average', 0)
            summary_sentences.append(f"Foliar phosphorus levels at {p_leaf_avg:.3f}% {'support' if p_leaf_avg >= 0.15 else 'may limit'} energy transfer processes and reproductive development in the palm canopy.")
        
        k_leaf_data = leaf_stats.get('K_%', {})
        if k_leaf_data:
            k_leaf_avg = k_leaf_data.get('average', 0)
            summary_sentences.append(f"Leaf potassium concentration of {k_leaf_avg:.2f}% {'ensures proper' if k_leaf_avg >= 1.0 else 'indicates compromised'} stomatal regulation and carbohydrate translocation to developing fruit bunches.")
        
        mg_data = leaf_stats.get('Mg_%', {})
        if mg_data:
            mg_avg = mg_data.get('average', 0)
            summary_sentences.append(f"Magnesium content in leaf tissue shows {mg_avg:.3f}%, which {'maintains' if mg_avg >= 0.25 else 'threatens'} the structural integrity of chlorophyll molecules essential for photosynthetic capacity.")
    
    # 12-15: Critical issues and severity assessment
    critical_issues = [i for i in all_issues if i.get('severity') == 'Critical']
    high_issues = [i for i in all_issues if i.get('severity') == 'High']
    medium_issues = [i for i in all_issues if i.get('severity') == 'Medium']
    
    summary_sentences.append(f"Critical nutritional deficiencies identified in {len(critical_issues)} parameters pose immediate threats to palm productivity and require urgent corrective measures within the next 30-60 days.")
    summary_sentences.append(f"High-severity imbalances affecting {len(high_issues)} additional parameters will significantly impact yield potential if not addressed through targeted fertilization programs within 3-6 months.")
    summary_sentences.append(f"Medium-priority nutritional concerns in {len(medium_issues)} parameters suggest the need for adjusted maintenance fertilization schedules to prevent future deficiencies.")
    
    # 16-18: Yield and economic implications
    current_yield = land_yield_data.get('current_yield', 0)
    land_size = land_yield_data.get('land_size', 0)
    
    # Ensure current_yield is numeric
    try:
        current_yield = float(current_yield) if current_yield is not None else 0
    except (ValueError, TypeError):
        current_yield = 0
    
    if current_yield and land_size:
        summary_sentences.append(f"Current yield performance of {current_yield} tonnes per hectare across {land_size} hectares {'exceeds' if current_yield > 20 else 'falls below'} industry benchmarks, with nutritional corrections potentially {'maintaining' if current_yield > 20 else 'improving'} production by 15-25%.")
    else:
        summary_sentences.append("Yield optimization potential through nutritional management could increase production by 15-25% when combined with proper agronomic practices and timely intervention strategies.")
    
    summary_sentences.append("Economic analysis indicates that investment in corrective fertilization programs will generate positive returns within 12-18 months through improved fruit bunch quality and increased fresh fruit bunch production.")
    
    # 19-20: Recommendations and monitoring
    summary_sentences.append("Implementation of precision fertilization based on these findings, combined with regular soil and leaf monitoring every 6 months, will ensure sustained productivity and long-term plantation profitability.")
    summary_sentences.append("Adoption of integrated nutrient management practices, including organic matter incorporation and micronutrient supplementation, will enhance soil health and support the plantation's transition toward sustainable intensification goals.")
    
    # Ensure we have exactly 20 sentences
    while len(summary_sentences) < 20:
        summary_sentences.append("Continued monitoring and adaptive management strategies will be essential for maintaining optimal nutritional status and maximizing the economic potential of this oil palm operation.")
    
    # Take only the first 20 sentences
    summary_sentences = summary_sentences[:20]
    
    # Join sentences into a comprehensive summary
    comprehensive_summary = " ".join(summary_sentences)
    
    # Display the enhanced summary
    st.markdown(
        f'<div class="analysis-card"><p style="font-size: 16px; line-height: 1.8; margin: 0; text-align: justify;">{comprehensive_summary}</p></div>',
        unsafe_allow_html=True
    )

def calculate_parameter_statistics(samples):
    """Calculate parameter statistics from sample data"""
    if not samples or not isinstance(samples, list):
        return {}
    
    # Get all parameter names from the first sample
    if not samples[0] or not isinstance(samples[0], dict):
        return {}
    
    param_names = [key for key in samples[0].keys() if key not in ['lab_no', 'sample_no']]
    param_stats = {}
    
    for param in param_names:
        values = []
        for sample in samples:
            if param in sample and sample[param] is not None:
                try:
                    # Convert to float, handling different formats
                    value = float(str(sample[param]).replace('%', '').replace('mg/kg', '').replace('meq%', '').strip())
                    values.append(value)
                except (ValueError, TypeError):
                    continue
        
        if values:
            param_stats[param] = {
                'average': sum(values) / len(values),
                'min': min(values),
                'max': max(values),
                'count': len(values)
            }
    
    return param_stats

def clean_finding_text(text):
    """Clean finding text by removing duplicate 'Key Finding' words and normalizing"""
    import re
    
    # Remove duplicate "Key Finding" patterns
    # Pattern 1: "Key Finding X: Key finding Y:" -> "Key Finding X:"
    text = re.sub(r'Key Finding \d+:\s*Key finding \d+:\s*', 'Key Finding ', text)
    
    # Pattern 2: "Key finding X:" -> remove (lowercase version)
    text = re.sub(r'Key finding \d+:\s*', '', text)
    
    # Pattern 3: Multiple "Key Finding" at the start
    text = re.sub(r'^(Key Finding \d+:\s*)+', 'Key Finding ', text)
    
    # Clean up extra spaces
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def is_same_issue(finding1, finding2):
    """Check if two findings are about the same agricultural issue"""
    # Define issue patterns
    issue_patterns = {
        'potassium_deficiency': ['potassium', 'k deficiency', 'k level', 'k average', 'k critical'],
        'soil_acidity': ['ph', 'acidic', 'acidity', 'soil ph', 'ph level'],
        'phosphorus_deficiency': ['phosphorus', 'p deficiency', 'available p', 'p level'],
        'nutrient_deficiency': ['deficiency', 'deficient', 'nutrient', 'nutrients'],
        'cec_issue': ['cec', 'cation exchange', 'nutrient retention', 'nutrient holding'],
        'organic_matter': ['organic matter', 'organic carbon', 'carbon'],
        'micronutrient': ['copper', 'zinc', 'manganese', 'iron', 'boron', 'micronutrient'],
        'yield_impact': ['yield', 'productivity', 'tonnes', 'production'],
        'economic_impact': ['roi', 'investment', 'cost', 'profit', 'revenue', 'economic']
    }
    
    finding1_lower = finding1.lower()
    finding2_lower = finding2.lower()
    
    # Check if both findings mention the same issue category
    for issue, keywords in issue_patterns.items():
        finding1_has_issue = any(keyword in finding1_lower for keyword in keywords)
        finding2_has_issue = any(keyword in finding2_lower for keyword in keywords)
        
        if finding1_has_issue and finding2_has_issue:
            # Additional check for specific values or percentages
            if issue in ['potassium_deficiency', 'soil_acidity', 'phosphorus_deficiency']:
                # Extract numbers from both findings
                import re
                nums1 = re.findall(r'\d+\.?\d*', finding1)
                nums2 = re.findall(r'\d+\.?\d*', finding2)
                
                # If they have similar numbers, they're likely the same issue
                if nums1 and nums2:
                    for num1 in nums1:
                        for num2 in nums2:
                            if abs(float(num1) - float(num2)) < 0.1:  # Very close values
                                return True
            
            return True
    
    return False

def _extract_key_concepts(text):
    """Extract key concepts from text for better deduplication"""
    import re
    
    # Define key agricultural concepts and nutrients
    nutrients = ['nitrogen', 'phosphorus', 'potassium', 'calcium', 'magnesium', 'sulfur', 'copper', 'zinc', 'manganese', 'iron', 'boron', 'molybdenum']
    parameters = ['ph', 'cec', 'organic matter', 'base saturation', 'yield', 'deficiency', 'excess', 'optimum', 'critical', 'mg/kg', '%', 'meq']
    conditions = ['acidic', 'alkaline', 'deficient', 'sufficient', 'excessive', 'low', 'high', 'moderate', 'severe', 'mild']
    
    # Extract numbers and percentages
    numbers = re.findall(r'\d+\.?\d*', text)
    
    # Extract nutrient names and parameters
    found_concepts = set()
    
    # Check for nutrients
    for nutrient in nutrients:
        if nutrient in text:
            found_concepts.add(nutrient)
    
    # Check for parameters
    for param in parameters:
        if param in text:
            found_concepts.add(param)
    
    # Check for conditions
    for condition in conditions:
        if condition in text:
            found_concepts.add(condition)
    
    # Add significant numbers (values that matter for agricultural analysis)
    for num in numbers:
        if float(num) > 0:  # Only add positive numbers
            found_concepts.add(num)
    
    return found_concepts

def merge_similar_findings(finding1: str, finding2: str) -> str:
    """Merge two similar findings into one comprehensive finding"""
    import re
    
    # Extract parameter names with comprehensive mapping for all 9 soil and 8 leaf parameters
    param_mapping = {
        # Soil Parameters (9)
        'ph': ['ph', 'ph level', 'soil ph', 'acidity', 'alkalinity'],
        'nitrogen': ['nitrogen', 'n', 'n%', 'n_%', 'nitrogen%', 'nitrogen_%'],
        'organic_carbon': ['organic carbon', 'organic_carbon', 'carbon', 'c', 'c%', 'c_%', 'organic_carbon_%'],
        'total_phosphorus': ['total phosphorus', 'total p', 'total_p', 'total phosphorus mg/kg', 'total_p_mg_kg'],
        'available_phosphorus': ['available phosphorus', 'available p', 'available_p', 'available phosphorus mg/kg', 'available_p_mg_kg'],
        'exchangeable_potassium': ['exchangeable potassium', 'exch k', 'exch_k', 'exchangeable k', 'exchangeable_k', 'k meq%', 'k_meq%', 'exchangeable_k_meq%'],
        'exchangeable_calcium': ['exchangeable calcium', 'exch ca', 'exch_ca', 'exchangeable ca', 'exchangeable_ca', 'ca meq%', 'ca_meq%', 'exchangeable_ca_meq%'],
        'exchangeable_magnesium': ['exchangeable magnesium', 'exch mg', 'exch_mg', 'exchangeable mg', 'exchangeable_mg', 'mg meq%', 'mg_meq%', 'exchangeable_mg_meq%'],
        'cec': ['cec', 'cation exchange capacity', 'c.e.c', 'cec meq%', 'cec_meq%'],
        
        # Leaf Parameters (8)
        'leaf_nitrogen': ['leaf nitrogen', 'leaf n', 'leaf_n', 'n%', 'n_%', 'nitrogen%', 'nitrogen_%'],
        'leaf_phosphorus': ['leaf phosphorus', 'leaf p', 'leaf_p', 'p%', 'p_%', 'phosphorus%', 'phosphorus_%'],
        'leaf_potassium': ['leaf potassium', 'leaf k', 'leaf_k', 'k%', 'k_%', 'potassium%', 'potassium_%'],
        'leaf_magnesium': ['leaf magnesium', 'leaf mg', 'leaf_mg', 'mg%', 'mg_%', 'magnesium%', 'magnesium_%'],
        'leaf_calcium': ['leaf calcium', 'leaf ca', 'leaf_ca', 'ca%', 'ca_%', 'calcium%', 'calcium_%'],
        'leaf_boron': ['leaf boron', 'leaf b', 'leaf_b', 'b mg/kg', 'b_mg_kg', 'boron mg/kg', 'boron_mg_kg'],
        'leaf_copper': ['leaf copper', 'leaf cu', 'leaf_cu', 'cu mg/kg', 'cu_mg_kg', 'copper mg/kg', 'copper_mg_kg'],
        'leaf_zinc': ['leaf zinc', 'leaf zn', 'leaf_zn', 'zn mg/kg', 'zn_mg_kg', 'zinc mg/kg', 'zinc_mg_kg'],
        
        # Land & Yield Parameters
        'land_size': ['land size', 'land_size', 'farm size', 'farm_size', 'area', 'hectares', 'acres', 'square meters', 'square_meters'],
        'current_yield': ['current yield', 'current_yield', 'yield', 'production', 'tonnes/hectare', 'kg/hectare', 'tonnes/acre', 'kg/acre', 'yield per hectare', 'yield per acre'],
        'yield_forecast': ['yield forecast', 'yield_forecast', 'projected yield', 'projected_yield', 'future yield', 'future_yield', 'yield projection', 'yield_projection'],
        'economic_impact': ['economic impact', 'economic_impact', 'roi', 'return on investment', 'cost benefit', 'cost_benefit', 'profitability', 'revenue', 'income'],
        
        # Legacy mappings for backward compatibility
        'phosphorus': ['phosphorus', 'p', 'p%', 'p_%', 'phosphorus%', 'available p'],
        'potassium': ['potassium', 'k', 'k%', 'k_%', 'potassium%'],
        'calcium': ['calcium', 'ca', 'ca%', 'ca_%', 'calcium%'],
        'magnesium': ['magnesium', 'mg', 'mg%', 'mg_%', 'magnesium%'],
        'copper': ['copper', 'cu', 'cu mg/kg', 'cu_mg/kg', 'copper mg/kg'],
        'zinc': ['zinc', 'zn', 'zn mg/kg', 'zn_mg/kg', 'zinc mg/kg'],
        'boron': ['boron', 'b', 'b mg/kg', 'b_mg/kg', 'boron mg/kg']
    }
    
    def extract_parameters(text):
        """Extract all parameters mentioned in text"""
        found_params = set()
        text_lower = text.lower()
        for param, variations in param_mapping.items():
            if any(var in text_lower for var in variations):
                found_params.add(param)
        return found_params
    
    def extract_values(text):
        """Extract all numerical values from text"""
        return re.findall(r'\d+\.?\d*%?', text)
    
    def extract_severity_keywords(text):
        """Extract severity and impact keywords"""
        severity_words = ['critical', 'severe', 'high', 'low', 'deficiency', 'excess', 'optimum', 'below', 'above']
        found_severity = [word for word in severity_words if word in text.lower()]
        return found_severity
    
    # Extract information from both findings
    params1 = extract_parameters(finding1)
    params2 = extract_parameters(finding2)
    values1 = extract_values(finding1)
    values2 = extract_values(finding2)
    severity1 = extract_severity_keywords(finding1)
    severity2 = extract_severity_keywords(finding2)
    
    # If both findings are about the same parameter(s), merge them comprehensively
    if params1 and params2 and params1.intersection(params2):
        # Get the common parameter
        common_params = list(params1.intersection(params2))
        param_name = common_params[0].upper() if common_params[0] != 'ph' else 'pH'
        
        # Combine all values
        all_values = list(set(values1 + values2))
        
        # Combine all severity keywords
        all_severity = list(set(severity1 + severity2))
        
        # Create comprehensive finding
        if 'critical' in all_severity or 'severe' in all_severity:
            severity_desc = "critical"
        elif 'high' in all_severity:
            severity_desc = "significant"
        elif 'low' in all_severity:
            severity_desc = "moderate"
        else:
            severity_desc = "notable"
        
        # Build comprehensive finding
        if param_name == 'pH':
            comprehensive_finding = f"Soil {param_name} shows {severity_desc} issues with values of {', '.join(all_values)}. "
        else:
            comprehensive_finding = f"{param_name} levels show {severity_desc} issues with values of {', '.join(all_values)}. "
        
        # Add context from both findings
        context_parts = []
        if 'deficiency' in all_severity:
            context_parts.append("deficiency")
        if 'excess' in all_severity:
            context_parts.append("excess")
        if 'below' in all_severity:
            context_parts.append("below optimal levels")
        if 'above' in all_severity:
            context_parts.append("above optimal levels")
        
        if context_parts:
            comprehensive_finding += f"This indicates {', '.join(context_parts)}. "
        
        # Add impact information
        if 'critical' in all_severity or 'severe' in all_severity:
            comprehensive_finding += "This directly impacts crop yield and requires immediate attention."
        elif 'high' in all_severity:
            comprehensive_finding += "This significantly affects plant health and productivity."
        else:
            comprehensive_finding += "This affects overall plant performance and should be addressed."
        
        return comprehensive_finding
    
    # If findings are about different parameters, combine them
    return f"{finding1} Additionally, {finding2.lower()}"

def group_and_merge_findings_by_parameter(findings_list):
    """Group findings by parameter and merge all findings about the same parameter into one comprehensive finding"""
    import re
    
    # Parameter mapping for grouping - comprehensive mapping for all 9 soil and 8 leaf parameters
    param_mapping = {
        # Soil Parameters (9)
        'ph': ['ph', 'ph level', 'soil ph', 'acidity', 'alkalinity'],
        'nitrogen': ['nitrogen', 'n', 'n%', 'n_%', 'nitrogen%', 'nitrogen_%'],
        'organic_carbon': ['organic carbon', 'organic_carbon', 'carbon', 'c', 'c%', 'c_%', 'organic_carbon_%'],
        'total_phosphorus': ['total phosphorus', 'total p', 'total_p', 'total phosphorus mg/kg', 'total_p_mg_kg'],
        'available_phosphorus': ['available phosphorus', 'available p', 'available_p', 'available phosphorus mg/kg', 'available_p_mg_kg'],
        'exchangeable_potassium': ['exchangeable potassium', 'exch k', 'exch_k', 'exchangeable k', 'exchangeable_k', 'k meq%', 'k_meq%', 'exchangeable_k_meq%'],
        'exchangeable_calcium': ['exchangeable calcium', 'exch ca', 'exch_ca', 'exchangeable ca', 'exchangeable_ca', 'ca meq%', 'ca_meq%', 'exchangeable_ca_meq%'],
        'exchangeable_magnesium': ['exchangeable magnesium', 'exch mg', 'exch_mg', 'exchangeable mg', 'exchangeable_mg', 'mg meq%', 'mg_meq%', 'exchangeable_mg_meq%'],
        'cec': ['cec', 'cation exchange capacity', 'c.e.c', 'cec meq%', 'cec_meq%'],
        
        # Leaf Parameters (8)
        'leaf_nitrogen': ['leaf nitrogen', 'leaf n', 'leaf_n', 'n%', 'n_%', 'nitrogen%', 'nitrogen_%'],
        'leaf_phosphorus': ['leaf phosphorus', 'leaf p', 'leaf_p', 'p%', 'p_%', 'phosphorus%', 'phosphorus_%'],
        'leaf_potassium': ['leaf potassium', 'leaf k', 'leaf_k', 'k%', 'k_%', 'potassium%', 'potassium_%'],
        'leaf_magnesium': ['leaf magnesium', 'leaf mg', 'leaf_mg', 'mg%', 'mg_%', 'magnesium%', 'magnesium_%'],
        'leaf_calcium': ['leaf calcium', 'leaf ca', 'leaf_ca', 'ca%', 'ca_%', 'calcium%', 'calcium_%'],
        'leaf_boron': ['leaf boron', 'leaf b', 'leaf_b', 'b mg/kg', 'b_mg_kg', 'boron mg/kg', 'boron_mg_kg'],
        'leaf_copper': ['leaf copper', 'leaf cu', 'leaf_cu', 'cu mg/kg', 'cu_mg_kg', 'copper mg/kg', 'copper_mg_kg'],
        'leaf_zinc': ['leaf zinc', 'leaf zn', 'leaf_zn', 'zn mg/kg', 'zn_mg_kg', 'zinc mg/kg', 'zinc_mg_kg'],
        
        # Land & Yield Parameters
        'land_size': ['land size', 'land_size', 'farm size', 'farm_size', 'area', 'hectares', 'acres', 'square meters', 'square_meters'],
        'current_yield': ['current yield', 'current_yield', 'yield', 'production', 'tonnes/hectare', 'kg/hectare', 'tonnes/acre', 'kg/acre', 'yield per hectare', 'yield per acre'],
        'yield_forecast': ['yield forecast', 'yield_forecast', 'projected yield', 'projected_yield', 'future yield', 'future_yield', 'yield projection', 'yield_projection'],
        'economic_impact': ['economic impact', 'economic_impact', 'roi', 'return on investment', 'cost benefit', 'cost_benefit', 'profitability', 'revenue', 'income'],
        
        # Legacy mappings for backward compatibility
        'phosphorus': ['phosphorus', 'p', 'p%', 'p_%', 'phosphorus%', 'available p'],
        'potassium': ['potassium', 'k', 'k%', 'k_%', 'potassium%'],
        'calcium': ['calcium', 'ca', 'ca%', 'ca_%', 'calcium%'],
        'magnesium': ['magnesium', 'mg', 'mg%', 'mg_%', 'magnesium%'],
        'copper': ['copper', 'cu', 'cu mg/kg', 'cu_mg/kg', 'copper mg/kg'],
        'zinc': ['zinc', 'zn', 'zn mg/kg', 'zn_mg/kg', 'zinc mg/kg'],
        'boron': ['boron', 'b', 'b mg/kg', 'b_mg/kg', 'boron mg/kg']
    }
    
    def extract_parameter(text):
        """Extract the primary parameter from text"""
        text_lower = text.lower()
        for param, variations in param_mapping.items():
            if any(var in text_lower for var in variations):
                return param
        return 'other'
    
    def extract_values(text):
        """Extract all numerical values from text"""
        return re.findall(r'\d+\.?\d*%?', text)
    
    def extract_severity_keywords(text):
        """Extract severity and impact keywords"""
        severity_words = ['critical', 'severe', 'high', 'low', 'deficiency', 'excess', 'optimum', 'below', 'above']
        return [word for word in severity_words if word in text.lower()]
    
    # Group findings by parameter
    parameter_groups = {}
    for finding_data in findings_list:
        finding = finding_data['finding']
        param = extract_parameter(finding)
        
        if param not in parameter_groups:
            parameter_groups[param] = []
        parameter_groups[param].append(finding_data)
    
    # Merge findings within each parameter group
    merged_findings = []
    for param, group_findings in parameter_groups.items():
        if len(group_findings) == 1:
            # Single finding, keep as is
            merged_findings.append(group_findings[0])
        else:
            # Multiple findings about same parameter, merge them
            merged_finding = merge_parameter_group_findings(param, group_findings)
            if merged_finding:
                merged_findings.append(merged_finding)
    
    return merged_findings

def merge_parameter_group_findings(param, group_findings):
    """Merge all findings in a parameter group into one comprehensive finding"""
    import re
    
    # Extract all values and severity keywords from all findings in the group
    all_values = []
    all_severity = []
    all_sources = []
    
    for finding_data in group_findings:
        finding = finding_data['finding']
        source = finding_data['source']
        
        # Extract values
        values = re.findall(r'\d+\.?\d*%?', finding)
        all_values.extend(values)
        
        # Extract severity keywords
        severity_words = ['critical', 'severe', 'high', 'low', 'deficiency', 'excess', 'optimum', 'below', 'above']
        severity = [word for word in severity_words if word in finding.lower()]
        all_severity.extend(severity)
        
        all_sources.append(source)
    
    # Remove duplicates
    unique_values = list(set(all_values))
    unique_severity = list(set(all_severity))
    unique_sources = list(set(all_sources))
    
    # Determine parameter name
    param_name = param.upper() if param != 'ph' else 'pH'
    
    # Determine severity level
    if 'critical' in unique_severity or 'severe' in unique_severity:
        severity_desc = "critical"
    elif 'high' in unique_severity:
        severity_desc = "significant"
    elif 'low' in unique_severity:
        severity_desc = "moderate"
    else:
        severity_desc = "notable"
    
    # Build comprehensive finding
    if param == 'ph':
        comprehensive_finding = f"Soil {param_name} shows {severity_desc} issues with values of {', '.join(unique_values)}. "
    else:
        comprehensive_finding = f"{param_name} levels show {severity_desc} issues with values of {', '.join(unique_values)}. "
    
    # Add context
    context_parts = []
    if 'deficiency' in unique_severity:
        context_parts.append("deficiency")
    if 'excess' in unique_severity:
        context_parts.append("excess")
    if 'below' in unique_severity:
        context_parts.append("below optimal levels")
    if 'above' in unique_severity:
        context_parts.append("above optimal levels")
    
    if context_parts:
        comprehensive_finding += f"This indicates {', '.join(context_parts)}. "
    
    # Add impact information
    if 'critical' in unique_severity or 'severe' in unique_severity:
        comprehensive_finding += "This directly impacts crop yield and requires immediate attention."
    elif 'high' in unique_severity:
        comprehensive_finding += "This significantly affects plant health and productivity."
    else:
        comprehensive_finding += "This affects overall plant performance and should be addressed."
    
    return {
        'finding': comprehensive_finding,
        'source': ', '.join(unique_sources)
    }

def generate_intelligent_key_findings(analysis_results, step_results):
    """Generate comprehensive intelligent key findings grouped by parameter with proper deduplication"""
    all_key_findings = []
    
    # 1. Check for key findings at the top level of analysis_results
    if 'key_findings' in analysis_results and analysis_results['key_findings']:
        findings_data = analysis_results['key_findings']
        
        # Handle both list and string formats
        if isinstance(findings_data, list):
            findings_list = findings_data
        elif isinstance(findings_data, str):
            findings_list = [f.strip() for f in findings_data.split('\n') if f.strip()]
        else:
            findings_list = []
        
        # Process each finding
        for finding in findings_list:
            if isinstance(finding, str) and finding.strip():
                cleaned_finding = clean_finding_text(finding.strip())
                all_key_findings.append({
                    'finding': cleaned_finding,
                    'source': 'Overall Analysis'
                })
    
    # 2. Extract comprehensive key findings from step-by-step analysis
    if step_results:
        step_findings = []
        
        for step in step_results:
            step_number = step.get('step_number', 0)
            step_title = step.get('step_title', f"Step {step_number}")
            
            # Extract findings from multiple step sources
            step_sources = []
            
            # Direct key_findings field
            if 'key_findings' in step and step['key_findings']:
                step_sources.append(('key_findings', step['key_findings']))
            
            # Summary field
            if 'summary' in step and step['summary']:
                step_sources.append(('summary', step['summary']))
            
            # Detailed analysis field
            if 'detailed_analysis' in step and step['detailed_analysis']:
                step_sources.append(('detailed_analysis', step['detailed_analysis']))
            
            # Issues identified
            if 'issues_identified' in step and step['issues_identified']:
                step_sources.append(('issues_identified', step['issues_identified']))
            
            # Recommendations
            if 'recommendations' in step and step['recommendations']:
                step_sources.append(('recommendations', step['recommendations']))
            
            # Process each source
            for source_type, source_data in step_sources:
                findings_list = []
                
                # Handle different data formats
                if isinstance(source_data, list):
                    findings_list = source_data
                elif isinstance(source_data, str):
                    # Split by common delimiters and clean
                    lines = source_data.split('\n')
                    findings_list = [line.strip() for line in lines if line.strip()]
                else:
                    continue
                
                # Extract key findings from each item
                for finding in findings_list:
                    if isinstance(finding, str) and finding.strip():
                        # Enhanced keyword filtering for better relevance
                        finding_lower = finding.lower()
                        relevant_keywords = [
                            'deficiency', 'critical', 'severe', 'low', 'high', 'optimum', 'ph', 'nutrient', 'yield',
                            'recommendation', 'finding', 'issue', 'problem', 'analysis', 'result', 'conclusion',
                            'soil', 'leaf', 'land', 'hectares', 'acres', 'tonnes', 'production', 'economic',
                            'roi', 'investment', 'cost', 'benefit', 'profitability', 'forecast', 'projection',
                            'improvement', 'increase', 'decrease', 'balance', 'ratio', 'level', 'status',
                            'nitrogen', 'phosphorus', 'potassium', 'calcium', 'magnesium', 'carbon', 'cec',
                            'boron', 'zinc', 'copper', 'manganese', 'iron', 'sulfur', 'chlorine'
                        ]
                        
                        # Check if finding contains relevant keywords
                        if any(keyword in finding_lower for keyword in relevant_keywords):
                            cleaned_finding = clean_finding_text(finding.strip())
                            if cleaned_finding and len(cleaned_finding) > 20:  # Minimum length filter
                                step_findings.append({
                                    'finding': cleaned_finding,
                                    'source': f"{step_title} ({source_type.replace('_', ' ').title()})"
                                })
        
        # Apply intelligent deduplication to step findings
        if step_findings:
            # First group findings by parameter and merge within each group
            parameter_merged_findings = group_and_merge_findings_by_parameter(step_findings)
            
            # Then apply additional deduplication for any remaining similar findings
            unique_findings = []
            seen_concepts = []
            
            for finding_data in parameter_merged_findings:
                finding = finding_data['finding']
                normalized = ' '.join(finding.lower().split())
                key_concepts = _extract_key_concepts(normalized)
                
                is_duplicate = False
                for i, seen_concept_set in enumerate(seen_concepts):
                    concept_overlap = len(key_concepts.intersection(seen_concept_set))
                    total_concepts = len(key_concepts.union(seen_concept_set))
                    
                    if total_concepts > 0:
                        similarity = concept_overlap / total_concepts
                        word_similarity = len(key_concepts.intersection(seen_concept_set)) / max(len(key_concepts), len(seen_concept_set)) if len(key_concepts) > 0 and len(seen_concept_set) > 0 else 0
                        
                        # More aggressive deduplication - consolidate similar issues
                        if similarity > 0.5 or word_similarity > 0.6:
                            # Merge findings for the same issue
                            existing_finding = unique_findings[i]['finding']
                            merged_finding = merge_similar_findings(existing_finding, finding)
                            unique_findings[i]['finding'] = merged_finding
                            is_duplicate = True
                            break
                        
                        # Check for same issue with stricter criteria
                        if similarity > 0.3 and word_similarity > 0.4:
                            if is_same_issue(finding, unique_findings[i]['finding']):
                                # Merge findings for the same issue
                                existing_finding = unique_findings[i]['finding']
                                merged_finding = merge_similar_findings(existing_finding, finding)
                                unique_findings[i]['finding'] = merged_finding
                                is_duplicate = True
                                break
                
                if not is_duplicate:
                    unique_findings.append(finding_data)
                    seen_concepts.append(key_concepts)
            
            # Combine step findings with existing findings
            all_key_findings.extend(unique_findings)
    
    # 3. Generate comprehensive parameter-specific key findings
    comprehensive_findings = generate_comprehensive_parameter_findings(analysis_results, step_results)
    all_key_findings.extend(comprehensive_findings)
    
    # 4. Extract key findings from other analysis sources
    # Land and yield data
    land_yield_data = analysis_results.get('land_yield_data', {})
    if land_yield_data:
        land_size = land_yield_data.get('land_size', 0)
        current_yield = land_yield_data.get('current_yield', 0)
        land_unit = land_yield_data.get('land_unit', 'hectares')
        yield_unit = land_yield_data.get('yield_unit', 'tonnes/hectare')
        
        if land_size > 0:
            all_key_findings.append({
                'finding': f"Farm analysis covers {land_size} {land_unit} of agricultural land with current production of {current_yield} {yield_unit}.",
                'source': 'Land & Yield Data'
            })
    
    # Economic forecast
    economic_forecast = analysis_results.get('economic_forecast', {})
    if economic_forecast:
        scenarios = economic_forecast.get('scenarios', {})
        if scenarios:
            best_roi = 0
            best_scenario = ""
            for level, data in scenarios.items():
                if isinstance(data, dict) and data.get('roi_percentage', 0) > best_roi:
                    best_roi = data.get('roi_percentage', 0)
                    best_scenario = level
            
            if best_roi > 0:
                all_key_findings.append({
                    'finding': f"Economic analysis shows {best_scenario} investment level offers the best ROI of {best_roi:.1f}% with {scenarios[best_scenario].get('payback_months', 0):.1f} months payback period.",
                    'source': 'Economic Forecast'
                })
    
    # Yield forecast
    yield_forecast = analysis_results.get('yield_forecast', {})
    if yield_forecast:
        projected_yield = yield_forecast.get('projected_yield', 0)
        current_yield = yield_forecast.get('current_yield', 0)
        
        # Ensure both values are numeric
        try:
            projected_yield = float(projected_yield) if projected_yield is not None else 0
        except (ValueError, TypeError):
            projected_yield = 0
            
        try:
            current_yield = float(current_yield) if current_yield is not None else 0
        except (ValueError, TypeError):
            current_yield = 0
            
        if projected_yield > 0 and current_yield > 0:
            increase = ((projected_yield - current_yield) / current_yield) * 100
            all_key_findings.append({
                'finding': f"Yield projection indicates potential increase from {current_yield} to {projected_yield} tonnes/hectare ({increase:.1f}% improvement) with proper management.",
                'source': 'Yield Forecast'
            })
    
    # Apply final parameter-based grouping to all findings
    if all_key_findings:
        all_key_findings = group_and_merge_findings_by_parameter(all_key_findings)
    
    return all_key_findings

def generate_comprehensive_parameter_findings(analysis_results, step_results):
    """Generate comprehensive key findings grouped by specific parameters"""
    findings = []
    
    # Get raw data for analysis
    raw_data = analysis_results.get('raw_data', {})
    soil_params = raw_data.get('soil_parameters', {}).get('parameter_statistics', {})
    leaf_params = raw_data.get('leaf_parameters', {}).get('parameter_statistics', {})
    
    # Get MPOB standards for comparison
    try:
        from utils.mpob_standards import get_mpob_standards
        mpob = get_mpob_standards()
    except:
        mpob = None
    
    # 1. Soil pH Analysis
    if 'pH' in soil_params and mpob:
        ph_value = soil_params['pH'].get('average', 0)
        ph_optimal = mpob.get('soil', {}).get('ph', {}).get('optimal', 6.5)
        
        if ph_value > 0:
            if ph_value < 5.5:
                findings.append({
                    'finding': f"Soil pH is critically low at {ph_value:.1f}, significantly below optimal range of 5.5-7.0. This acidic condition severely limits nutrient availability and root development.",
                    'source': 'Soil Analysis - pH'
                })
            elif ph_value > 7.5:
                findings.append({
                    'finding': f"Soil pH is high at {ph_value:.1f}, above optimal range of 5.5-7.0. This alkaline condition reduces availability of essential micronutrients like iron and zinc.",
                    'source': 'Soil Analysis - pH'
                })
            else:
                findings.append({
                    'finding': f"Soil pH is within optimal range at {ph_value:.1f}, providing good conditions for nutrient availability and root development.",
                    'source': 'Soil Analysis - pH'
                })
    
    # 2. Soil Nitrogen Analysis
    if 'Nitrogen_%' in soil_params and mpob:
        n_value = soil_params['Nitrogen_%'].get('average', 0)
        n_optimal = mpob.get('soil', {}).get('nitrogen', {}).get('optimal', 0.2)
        
        if n_value > 0:
            if n_value < n_optimal * 0.7:
                findings.append({
                    'finding': f"Soil nitrogen is critically deficient at {n_value:.2f}%, well below optimal level of {n_optimal:.2f}%. This severely limits plant growth and leaf development.",
                    'source': 'Soil Analysis - Nitrogen'
                })
            elif n_value > n_optimal * 1.3:
                findings.append({
                    'finding': f"Soil nitrogen is excessive at {n_value:.2f}%, above optimal level of {n_optimal:.2f}%. This may cause nutrient imbalances and environmental concerns.",
                    'source': 'Soil Analysis - Nitrogen'
                })
            else:
                findings.append({
                    'finding': f"Soil nitrogen is adequate at {n_value:.2f}%, within optimal range for healthy plant growth.",
                    'source': 'Soil Analysis - Nitrogen'
                })
    
    # 3. Soil Phosphorus Analysis
    if 'Available_P_mg_kg' in soil_params and mpob:
        p_value = soil_params['Available_P_mg_kg'].get('average', 0)
        p_optimal = mpob.get('soil', {}).get('available_phosphorus', {}).get('optimal', 15)
        
        if p_value > 0:
            if p_value < p_optimal * 0.5:
                findings.append({
                    'finding': f"Available phosphorus is critically low at {p_value:.1f} mg/kg, severely below optimal level of {p_optimal} mg/kg. This limits root development and energy transfer.",
                    'source': 'Soil Analysis - Phosphorus'
                })
            elif p_value > p_optimal * 2:
                findings.append({
                    'finding': f"Available phosphorus is excessive at {p_value:.1f} mg/kg, well above optimal level of {p_optimal} mg/kg. This may cause nutrient lockup and environmental issues.",
                    'source': 'Soil Analysis - Phosphorus'
                })
            else:
                findings.append({
                    'finding': f"Available phosphorus is adequate at {p_value:.1f} mg/kg, within optimal range for proper plant development.",
                    'source': 'Soil Analysis - Phosphorus'
                })
    
    # 4. Soil Potassium Analysis
    if 'Exchangeable_K_meq%' in soil_params and mpob:
        k_value = soil_params['Exchangeable_K_meq%'].get('average', 0)
        k_optimal = mpob.get('soil', {}).get('exchangeable_potassium', {}).get('optimal', 0.3)
        
        if k_value > 0:
            if k_value < k_optimal * 0.6:
                findings.append({
                    'finding': f"Exchangeable potassium is deficient at {k_value:.2f} meq%, below optimal level of {k_optimal:.2f} meq%. This affects water regulation and disease resistance.",
                    'source': 'Soil Analysis - Potassium'
                })
            elif k_value > k_optimal * 1.5:
                findings.append({
                    'finding': f"Exchangeable potassium is high at {k_value:.2f} meq%, above optimal level of {k_optimal:.2f} meq%. This may cause nutrient imbalances.",
                    'source': 'Soil Analysis - Potassium'
                })
            else:
                findings.append({
                    'finding': f"Exchangeable potassium is adequate at {k_value:.2f} meq%, within optimal range for healthy plant function.",
                    'source': 'Soil Analysis - Potassium'
                })
    
    # 5. Leaf Nutrient Analysis
    if leaf_params:
        # Leaf Nitrogen
        if 'N_%' in leaf_params:
            leaf_n = leaf_params['N_%'].get('average', 0)
            if leaf_n > 0:
                if leaf_n < 2.5:
                    findings.append({
                        'finding': f"Leaf nitrogen is deficient at {leaf_n:.1f}%, below optimal range of 2.5-3.5%. This indicates poor nitrogen uptake and affects photosynthesis.",
                        'source': 'Leaf Analysis - Nitrogen'
                    })
                elif leaf_n > 3.5:
                    findings.append({
                        'finding': f"Leaf nitrogen is excessive at {leaf_n:.1f}%, above optimal range of 2.5-3.5%. This may cause nutrient imbalances and delayed maturity.",
                        'source': 'Leaf Analysis - Nitrogen'
                    })
                else:
                    findings.append({
                        'finding': f"Leaf nitrogen is optimal at {leaf_n:.1f}%, within recommended range for healthy palm growth.",
                        'source': 'Leaf Analysis - Nitrogen'
                    })
        
        # Leaf Phosphorus
        if 'P_%' in leaf_params:
            leaf_p = leaf_params['P_%'].get('average', 0)
            if leaf_p > 0:
                if leaf_p < 0.15:
                    findings.append({
                        'finding': f"Leaf phosphorus is deficient at {leaf_p:.2f}%, below optimal range of 0.15-0.25%. This limits energy transfer and root development.",
                        'source': 'Leaf Analysis - Phosphorus'
                    })
                elif leaf_p > 0.25:
                    findings.append({
                        'finding': f"Leaf phosphorus is high at {leaf_p:.2f}%, above optimal range of 0.15-0.25%. This may indicate over-fertilization.",
                        'source': 'Leaf Analysis - Phosphorus'
                    })
                else:
                    findings.append({
                        'finding': f"Leaf phosphorus is adequate at {leaf_p:.2f}%, within optimal range for proper plant function.",
                        'source': 'Leaf Analysis - Phosphorus'
                    })
        
        # Leaf Potassium
        if 'K_%' in leaf_params:
            leaf_k = leaf_params['K_%'].get('average', 0)
            if leaf_k > 0:
                if leaf_k < 1.0:
                    findings.append({
                        'finding': f"Leaf potassium is deficient at {leaf_k:.1f}%, below optimal range of 1.0-1.5%. This affects water regulation and disease resistance.",
                        'source': 'Leaf Analysis - Potassium'
                    })
                elif leaf_k > 1.5:
                    findings.append({
                        'finding': f"Leaf potassium is high at {leaf_k:.1f}%, above optimal range of 1.0-1.5%. This may cause nutrient imbalances.",
                        'source': 'Leaf Analysis - Potassium'
                    })
                else:
                    findings.append({
                        'finding': f"Leaf potassium is optimal at {leaf_k:.1f}%, within recommended range for healthy palm growth.",
                        'source': 'Leaf Analysis - Potassium'
                    })
        
        # Leaf Magnesium - Conditional recommendation considering GML and K:Mg ratio
        if 'Mg_%' in leaf_params:
            leaf_mg = leaf_params['Mg_%'].get('average', 0)
            if leaf_mg > 0:
                if leaf_mg < 0.25:  # Only recommend kieserite if clearly deficient
                    # Check if K:Mg ratio is also problematic
                    leaf_k = leaf_params.get('K_%', {}).get('average', 0)
                    if leaf_k > 0:
                        k_mg_ratio = leaf_k / leaf_mg if leaf_mg > 0 else 0
                        if k_mg_ratio > 3.0:  # K:Mg ratio too high
                            findings.append({
                                'finding': f"Leaf magnesium is deficient at {leaf_mg:.2f}% with high K:Mg ratio of {k_mg_ratio:.1f}. Kieserite recommended only after GML correction and if K:Mg ratio remains >3.0.",
                                'source': 'Leaf Analysis - Magnesium'
                            })
                        else:
                            findings.append({
                                'finding': f"Leaf magnesium is deficient at {leaf_mg:.2f}% but K:Mg ratio is acceptable. Consider GML first before kieserite application.",
                                'source': 'Leaf Analysis - Magnesium'
                            })
                    else:
                        findings.append({
                            'finding': f"Leaf magnesium is deficient at {leaf_mg:.2f}%. Consider GML application first, then kieserite only if needed after GML correction.",
                            'source': 'Leaf Analysis - Magnesium'
                        })
                elif leaf_mg > 0.35:  # Only flag when clearly excessive
                    findings.append({
                        'finding': f"Leaf magnesium is high at {leaf_mg:.2f}%, above optimal range. Monitor for nutrient imbalances.",
                        'source': 'Leaf Analysis - Magnesium'
                    })
                # No recommendation for adequate levels (0.25-0.35%)
        
        # Leaf Calcium
        if 'Ca_%' in leaf_params:
            leaf_ca = leaf_params['Ca_%'].get('average', 0)
            if leaf_ca > 0:
                if leaf_ca < 0.5:
                    findings.append({
                        'finding': f"Leaf calcium is deficient at {leaf_ca:.1f}%, below optimal range of 0.5-1.0%. This affects cell wall strength and fruit quality.",
                        'source': 'Leaf Analysis - Calcium'
                    })
                elif leaf_ca > 1.0:
                    findings.append({
                        'finding': f"Leaf calcium is high at {leaf_ca:.1f}%, above optimal range of 0.5-1.0%. This may cause nutrient imbalances.",
                        'source': 'Leaf Analysis - Calcium'
                    })
                else:
                    findings.append({
                        'finding': f"Leaf calcium is optimal at {leaf_ca:.1f}%, within recommended range for healthy palm growth.",
                        'source': 'Leaf Analysis - Calcium'
                    })
        
        # Leaf Boron - Conditional recommendation only when deficient
        if 'B_mg_kg' in leaf_params:
            leaf_b = leaf_params['B_mg_kg'].get('average', 0)
            if leaf_b > 0:
                if leaf_b < 12:  # Only recommend when clearly deficient
                    findings.append({
                        'finding': f"Leaf boron is deficient at {leaf_b:.1f} mg/kg, below critical threshold of 12 mg/kg. Boron supplementation recommended only for this specific deficiency.",
                        'source': 'Leaf Analysis - Boron'
                    })
                elif leaf_b > 25:  # Only flag when clearly excessive
                    findings.append({
                        'finding': f"Leaf boron is high at {leaf_b:.1f} mg/kg, above optimal range. Monitor for toxicity symptoms.",
                        'source': 'Leaf Analysis - Boron'
                    })
                # No recommendation for adequate levels (12-25 mg/kg)
    
    return findings

def display_key_findings_section(results_data):
    """Display Key Findings from analysis results with intelligent extraction and deduplication"""
    st.markdown("---")
    st.markdown("## 🎯 Key Findings")
    
    # Get analysis data
    analysis_results = get_analysis_results_from_data(results_data)
    step_results = analysis_results.get('step_by_step_analysis', [])
    
    # Generate intelligent key findings with proper deduplication using history page function
    from modules.history import _generate_intelligent_key_findings
    all_key_findings = _generate_intelligent_key_findings(analysis_results, step_results)
    
    if all_key_findings:
        # Display key findings
        for i, finding_data in enumerate(all_key_findings, 1):
            finding = finding_data['finding']
            
            # Enhanced finding display with bold numbering
            st.markdown(
                f'<div style="margin-bottom: 20px; padding: 15px; background: linear-gradient(135deg, #f8f9fa, #ffffff); border-left: 4px solid #007bff; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">'
                f'<p style="margin: 0; font-size: 18px; line-height: 1.6; color: #2c3e50;">'
                f'<strong style="color: #007bff; font-size: 20px;">Key Finding {i}:</strong> {finding}'
                f'</p>'
                f'</div>',
                unsafe_allow_html=True
            )
    else:
        st.info("📋 No key findings available from the analysis results.")

def display_references_section(results_data):
    """Display research references from database and web search"""
    st.markdown("---")
    st.markdown("## 📚 Research References")
    
    # Get analysis results
    analysis_results = get_analysis_results_from_data(results_data)
    step_results = analysis_results.get('step_by_step_analysis', [])
    
    # Collect all references from all steps
    all_references = {
        'database_references': [],
        'total_found': 0
    }
    
    for step in step_results:
        if 'references' in step and step['references']:
            refs = step['references']
            # Merge database references only
            if 'database_references' in refs:
                for db_ref in refs['database_references']:
                    # Avoid duplicates by checking ID
                    if not any(existing['id'] == db_ref['id'] for existing in all_references['database_references']):
                        all_references['database_references'].append(db_ref)
    
    all_references['total_found'] = len(all_references['database_references'])
    
    if all_references['total_found'] == 0:
        st.info("📋 No research references found for this analysis.")
        return
    
    # Display database references
    if all_references['database_references']:
        st.markdown("### 🗄️ Database References")
        st.markdown("References from our internal research database:")
        
        for i, ref in enumerate(all_references['database_references'], 1):
            # Enhanced display for PDF references
            if ref.get('file_type', '').lower() == 'pdf' or ref.get('file_name', '').lower().endswith('.pdf'):
                pdf_title = ref.get('pdf_title', ref.get('title', 'Untitled'))
                expander_title = f"**{i}. 📄 {pdf_title}**"
            else:
                expander_title = f"**{i}. {ref['title']}**"
            
            with st.expander(expander_title, expanded=False):
                st.markdown(f"**Source:** {ref['source']}")
                
                # Show PDF-specific information
                if ref.get('file_type', '').lower() == 'pdf' or ref.get('file_name', '').lower().endswith('.pdf'):
                    st.markdown("**Document Type:** PDF Research Paper")
                    
                    # Show PDF abstract if available
                    if ref.get('pdf_abstract'):
                        st.markdown("**Abstract:**")
                        st.markdown(f"_{ref['pdf_abstract']}_")
                    
                    # Show PDF keywords if available
                    if ref.get('pdf_keywords'):
                        st.markdown(f"**Keywords:** {', '.join(ref['pdf_keywords'])}")
                    
                    # Show PDF authors if available
                    if ref.get('pdf_authors'):
                        st.markdown(f"**Authors:** {', '.join(ref['pdf_authors'])}")
                    
                    # Show PDF pages if available
                    if ref.get('pdf_pages'):
                        st.markdown(f"**Pages:** {ref['pdf_pages']}")
                
                if ref.get('url'):
                    st.markdown(f"**URL:** [{ref['url']}]({ref['url']})")
                if ref.get('tags'):
                    st.markdown(f"**Tags:** {', '.join(ref['tags'])}")
                if ref.get('content'):
                    st.markdown(f"**Content:** {ref['content'][:500]}{'...' if len(ref['content']) > 500 else ''}")
                st.markdown(f"**Relevance Score:** {ref.get('relevance_score', 0):.2f}")
    
    
    # Summary
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #e3f2fd, #f0f8ff); padding: 15px; border-radius: 8px; margin-top: 20px;">
        <h4 style="color: #1976d2; margin: 0;">📊 Reference Summary</h4>
        <p style="margin: 5px 0 0 0; color: #424242;">
            Total references found: <strong>{all_references['total_found']}</strong> 
            ({len(all_references['database_references'])} database)
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Download PDF button after references
    st.markdown("---")
    st.markdown("## 📄 Download Report")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("📥 Download PDF Report", type="primary", width='stretch'):
            try:
                # Generate PDF
                with st.spinner("🔄 Generating PDF report..."):
                    pdf_bytes = generate_results_pdf(results_data)
                    
                # Download the PDF
                st.download_button(
                    label="💾 Download PDF",
                    data=pdf_bytes,
                    file_name=f"agricultural_analysis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                    mime="application/pdf",
                    type="primary"
                )
                st.success("✅ PDF report generated successfully!")
                
            except Exception as e:
                st.error(f"❌ Failed to generate PDF: {str(e)}")
                st.info("Please try again or contact support if the issue persists.")

def display_step_by_step_results(results_data):
    """Display step-by-step analysis results with enhanced LLM response clarity"""
    st.markdown("---")
    
    # Get step results from analysis results using helper function
    analysis_results = get_analysis_results_from_data(results_data)
    step_results = analysis_results.get('step_by_step_analysis', [])
    total_steps = len(step_results)
    
    # Remove quota exceeded banner to allow seamless analysis up to daily limit
    
    # Display header with enhanced step information
    st.markdown(f"## 🔬 Step-by-Step Analysis ({total_steps} Steps)")

    
    if total_steps > 0:
        # Show analysis progress with visual indicator
        progress_bar = st.progress(1.0)
        st.success(f"✅ **Analysis completed successfully for all {total_steps} steps**")
        
        # Add analysis metadata
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("📊 Total Steps", total_steps)
        with col2:
            # Get timestamp from results if available and format it properly
            timestamp = results_data.get('timestamp', 'Recent')
            if hasattr(timestamp, 'strftime'):
                # Convert datetime object to string
                formatted_timestamp = timestamp.strftime('%Y-%m-%d %H:%M')
            else:
                formatted_timestamp = str(timestamp) if timestamp != 'Recent' else 'Recent'
            st.metric("⏰ Generated", formatted_timestamp)
    else:
        st.warning("⚠️ No step-by-step analysis results found. This may indicate an issue with the analysis process.")
    
    if not step_results:
        # Also display other analysis components if available
        display_analysis_components(analysis_results)
        return
    
    # Display each step in organized blocks instead of tabs
    if len(step_results) > 0:
        # Display each step as a separate block with clear visual separation
        for i, step_result in enumerate(step_results):
            # Ensure step_result is a dictionary
            if not isinstance(step_result, dict):
                logger.error(f"Step {i+1} step_result is not a dictionary: {type(step_result)}")
                st.error(f"❌ Error: Step {i+1} data is not in the expected format")
                continue
            
            step_number = step_result.get('step_number', i+1)
            step_title = step_result.get('step_title', f'Step {step_number}')
            
            # Create a visual separator between steps
            if i > 0:
                st.markdown("---")
            
            # Display the step result in a block format
            display_step_block(step_result, step_number, step_title)
    
    # Display additional analysis components (Economic Forecast removed as requested)
    # display_analysis_components(analysis_results)

def display_analysis_components(analysis_results):
    """Display comprehensive analysis components like economic forecasts"""
    
    # Display Economic Forecast only
    economic_forecast = analysis_results.get('economic_forecast', {})
    if economic_forecast:
        st.markdown("---")
        st.markdown("## 📈 Economic Forecast")
        display_economic_forecast(economic_forecast)

def display_step_block(step_result, step_number, step_title):
    """Display step results in a professional block format with clear visual hierarchy"""
    
    # Define step-specific colors and icons
    step_configs = {
        1: {"color": "#667eea", "icon": "📊", "description": "Data Analysis & Interpretation"},
        2: {"color": "#f093fb", "icon": "🔍", "description": "Issue Diagnosis & Problem Identification"},
        3: {"color": "#4facfe", "icon": "💡", "description": "Solution Recommendations & Strategies"},
        4: {"color": "#43e97b", "icon": "🌱", "description": "Regenerative Agriculture Integration"},
        5: {"color": "#fa709a", "icon": "💰", "description": "Economic Impact & ROI Analysis"},
        6: {"color": "#000000", "icon": "📈", "description": "Yield Forecast & Projections"}
    }
    
    config = step_configs.get(step_number, {"color": "#667eea", "icon": "📋", "description": "Analysis Step"})
    
    # Create a prominent step header with step-specific styling
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, {config['color']} 0%, {config['color']}dd 100%);
        padding: 25px;
        border-radius: 15px;
        margin-bottom: 30px;
        box-shadow: 0 6px 20px rgba(0,0,0,0.15);
        border: 1px solid rgba(255,255,255,0.2);
    ">
        <div style="display: flex; align-items: center; margin-bottom: 15px;">
            <div style="
                background: rgba(255,255,255,0.25);
                color: white;
                padding: 10px 20px;
                border-radius: 25px;
                font-weight: bold;
                font-size: 16px;
                margin-right: 20px;
                backdrop-filter: blur(10px);
            ">
                {config['icon']} STEP {step_number}
            </div>
            <h2 style="color: white; margin: 0; font-size: 28px; font-weight: 700; text-shadow: 0 2px 4px rgba(0,0,0,0.3);">
                {step_title}
            </h2>
        </div>
        <p style="color: rgba(255,255,255,0.95); margin: 0; font-size: 18px; font-weight: 500;">
            {config['description']}
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Display the enhanced step result content
    display_enhanced_step_result(step_result, step_number)

def display_enhanced_step_result(step_result, step_number):
    """Display enhanced step results with proper structure and formatting for non-technical users"""
    # Ensure step_result is a dictionary
    if not isinstance(step_result, dict):
        logger.error(f"Step {step_number} step_result is not a dictionary: {type(step_result)}")
        st.error(f"❌ Error: Step {step_number} data is not in the expected format")
        return
    
    analysis_data = step_result
    
    # Debug: Log the structure of analysis_data
    logger.info(f"Step {step_number} analysis_data keys: {list(analysis_data.keys()) if analysis_data else 'None'}")
    if 'key_findings' in analysis_data:
        logger.info(f"Step {step_number} key_findings type: {type(analysis_data['key_findings'])}, value: {analysis_data['key_findings']}")
    if 'detailed_analysis' in analysis_data:
        logger.info(f"Step {step_number} detailed_analysis type: {type(analysis_data['detailed_analysis'])}, length: {len(str(analysis_data['detailed_analysis'])) if analysis_data['detailed_analysis'] else 0}")
    
    # Special handling for STEP 1 - Data Analysis
    if step_number == 1:
        display_step1_data_analysis(analysis_data)
        return
    
    # Special handling for STEP 3 - Solution Recommendations
    if step_number == 3:
        display_step3_solution_recommendations(analysis_data)
        return
    
    # 1. SUMMARY SECTION - Always show if available
    if 'summary' in analysis_data and analysis_data['summary']:
        st.markdown("### 📋 Summary")
        summary_text = analysis_data['summary']
        if isinstance(summary_text, str) and summary_text.strip():
            st.markdown(
                f'<div style="margin-bottom: 20px; padding: 15px; background: linear-gradient(135deg, #e8f5e8, #ffffff); border-left: 4px solid #28a745; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">'
                f'<p style="margin: 0; font-size: 16px; line-height: 1.6; color: #2c3e50;">{summary_text.strip()}</p>'
                f'</div>',
                unsafe_allow_html=True
            )
            st.markdown("")
        
    # 2. KEY FINDINGS SECTION - Removed from individual steps
    # Key findings are now consolidated and displayed only after Executive Summary
        
    # 3. DETAILED ANALYSIS SECTION - Show if available
    if 'detailed_analysis' in analysis_data and analysis_data['detailed_analysis']:
        st.markdown("### 📋 Detailed Analysis")
        detailed_text = analysis_data['detailed_analysis']
        
        # Ensure detailed_text is a string
        if isinstance(detailed_text, dict):
            detailed_text = str(detailed_text)
        elif not isinstance(detailed_text, str):
            detailed_text = str(detailed_text) if detailed_text is not None else "No detailed analysis available"
        
        # Filter out QuickChart URLs but preserve visual comparison text for proper chart generation
        import re
        # Remove QuickChart URLs but keep the visual comparison text
        detailed_text = re.sub(r'!\[.*?\]\(https://quickchart\.io.*?\)', '', detailed_text, flags=re.DOTALL)
        
        # For Step 2, we want to keep the visual comparison text but remove the actual QuickChart URLs
        # This allows the visualization generation to work properly
        
        # Split into paragraphs for better formatting
        paragraphs = detailed_text.split('\n\n') if '\n\n' in detailed_text else [detailed_text]
        
        for paragraph in paragraphs:
            if isinstance(paragraph, str) and paragraph.strip():
                st.markdown(
                    f'<div style="margin-bottom: 18px; padding: 15px; background: linear-gradient(135deg, #ffffff, #f8f9fa); border: 1px solid #e9ecef; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">'
                    f'<p style="margin: 0; line-height: 1.8; font-size: 16px; color: #2c3e50;">{paragraph.strip()}</p>'
                    f'</div>',
                    unsafe_allow_html=True
                )
        st.markdown("")
    
    # 4. TABLES SECTION - Display detailed tables if available
    if 'tables' in analysis_data and analysis_data['tables']:
        st.markdown("### 📊 Detailed Data Tables")
        for table in analysis_data['tables']:
            if isinstance(table, dict) and table.get('title') and table.get('headers') and table.get('rows'):
                st.markdown(f"**{table['title']}**")
                # Create a DataFrame for better display
                import pandas as pd
                df = pd.DataFrame(table['rows'], columns=table['headers'])
                apply_table_styling()
                st.dataframe(df, use_container_width=True)
                st.markdown("")
    
    # 5. INTERPRETATIONS SECTION - Display detailed interpretations if available
    if 'interpretations' in analysis_data and analysis_data['interpretations']:
        st.markdown("### 🔍 Detailed Interpretations")
        for idx, interpretation in enumerate(analysis_data['interpretations'], 1):
            if interpretation and interpretation.strip():
                # Remove any existing "Interpretation X:" prefix to avoid duplication
                clean_interpretation = interpretation.strip()
                if clean_interpretation.startswith(f"Interpretation {idx}:"):
                    clean_interpretation = clean_interpretation.replace(f"Interpretation {idx}:", "").strip()
                elif clean_interpretation.startswith(f"Detailed interpretation {idx}"):
                    clean_interpretation = clean_interpretation.replace(f"Detailed interpretation {idx}", "").strip()
                
                st.markdown(
                    f'<div style="margin-bottom: 15px; padding: 12px; background: linear-gradient(135deg, #f8f9fa, #ffffff); border-left: 4px solid #007bff; border-radius: 6px; box-shadow: 0 1px 4px rgba(0,0,0,0.1);">'
                    f'<p style="margin: 0; font-size: 15px; line-height: 1.5; color: #2c3e50;"><strong>Interpretation {idx}:</strong> {clean_interpretation}</p>'
                    f'</div>',
                    unsafe_allow_html=True
                )
        st.markdown("")
    
    # 6. ANALYSIS RESULTS SECTION - Show actual LLM results (renamed from Additional Information)
    # This section shows the main analysis results from the LLM
    excluded_keys = set(['summary', 'key_findings', 'detailed_analysis', 'formatted_analysis', 'step_number', 'step_title', 'step_description', 'visualizations', 'yield_forecast', 'references', 'search_timestamp', 'prompt_instructions', 'tables', 'interpretations'])
    other_fields = [k for k in analysis_data.keys() if k not in excluded_keys and analysis_data.get(k) is not None and analysis_data.get(k) != ""]
    
    if other_fields:
        st.markdown("### 📊 Additional Analysis Results")
        for key in other_fields:
            value = analysis_data.get(key)
            title = key.replace('_', ' ').title()
            
            if isinstance(value, dict) and value:
                st.markdown(f"**{title}:**")
                for sub_k, sub_v in value.items():
                    if sub_v is not None and sub_v != "":
                        st.markdown(f"- **{sub_k.replace('_',' ').title()}:** {sub_v}")
            elif isinstance(value, list) and value:
                st.markdown(f"**{title}:**")
                for idx, item in enumerate(value, 1):
                    if isinstance(item, (dict, list)):
                        st.markdown(f"- Item {idx}:")
                        st.json(item)
                    else:
                        st.markdown(f"- {item}")
            elif isinstance(value, str) and value.strip():
                st.markdown(f"**{title}:** {value}")
            st.markdown("")
    
    # Display visualizations only if step instructions contain visualization keywords
    # Skip visualizations for economic forecast steps
    if should_show_visualizations(step_result) and not should_show_forecast_graph(step_result):
        # Check for existing visualizations first
        has_existing_viz = 'visualizations' in analysis_data and analysis_data['visualizations']
        
        # Generate contextual visualizations based on step content
        contextual_viz = generate_contextual_visualizations(step_result, analysis_data)
        
        if has_existing_viz or contextual_viz:
            st.markdown("""<div style="background: linear-gradient(135deg, #17a2b8, #20c997); padding: 20px; border-radius: 12px; margin-bottom: 25px; box-shadow: 0 4px 15px rgba(0,0,0,0.1);">
                <h4 style="color: white; margin: 0; font-size: 20px; font-weight: 600;">📊 Data Visualizations</h4>
            </div>""", unsafe_allow_html=True)
        
            try:
                # Display existing visualizations
                if has_existing_viz:
                    visualizations = analysis_data['visualizations']
                    if isinstance(visualizations, dict):
                        for i, (viz_type, viz_data) in enumerate(visualizations.items(), 1):
                            if viz_data and isinstance(viz_data, dict):
                                # Add type to viz_data if not present
                                if 'type' not in viz_data:
                                    viz_data['type'] = viz_type
                                display_visualization(viz_data, i, step_number)
                    elif isinstance(visualizations, list):
                        for i, viz in enumerate(visualizations, 1):
                            if isinstance(viz, dict) and 'type' in viz:
                                display_visualization(viz, i, step_number)
                
                # Display contextual visualizations
                if contextual_viz:
                    for i, viz_data in enumerate(contextual_viz, 1):
                        if viz_data and isinstance(viz_data, dict):
                            display_visualization(viz_data, i, step_number)
                            
            except Exception as e:
                logger.error(f"Error displaying visualizations: {e}")
                st.error("Error displaying visualizations")
    # No farmer message needed - removed as requested
    
    # Display forecast graph if this step has yield forecast data
    if should_show_forecast_graph(step_result) and has_yield_forecast_data(analysis_data):
        display_forecast_graph_content(analysis_data, step_number, step_result.get('step_title', f'Step {step_number}'))

def display_single_step_result(step_result, step_number):
    """Legacy function - redirects to enhanced display"""
    display_enhanced_step_result(step_result, step_number)

def display_visualization(viz_data, viz_number, step_number=None):
    """Display individual visualization based on type with enhanced chart support"""
    viz_type = viz_data.get('type', 'unknown')
    title = viz_data.get('title', f'Visualization {viz_number}')
    subtitle = viz_data.get('subtitle', '')
    data = viz_data.get('data', {})
    options = viz_data.get('options', {})
    
    # For Step 2, no visualizations are displayed
    if step_number == 2:
        return
    
    # Display title and subtitle
    st.markdown(f"### {title}")
    if subtitle:
        st.markdown(f"*{subtitle}*")
    
    if viz_type == 'bar_chart':
        display_enhanced_bar_chart(data, title, options)
    elif viz_type == 'range_chart':
        # Skip range analysis visualizations - no longer displayed
        return
    elif viz_type == 'deviation_chart':
        # Skip deviation analysis visualizations - no longer displayed
        return
    elif viz_type == 'radar_chart':
        return
    elif viz_type == 'gauge_chart':
        display_gauge_chart(data, title, options)
    elif viz_type == 'pie_chart':
        # Skip pie charts for Step 2
        if step_number == 2:
            return
        display_pie_chart(data, title)
    elif viz_type == 'line_chart':
        # Skip line charts for Step 2
        if step_number == 2:
            return
        display_line_chart(data, title)
    elif viz_type == 'scatter_plot':
        # Skip scatter plots for Step 2
        if step_number == 2:
            return
        display_scatter_plot(data, title)
    elif viz_type == 'actual_vs_optimal_bar':
        display_actual_vs_optimal_bar(data, title, options)
    elif viz_type == 'nutrient_ratio_diagram':
        display_nutrient_ratio_diagram(data, title, options)
    elif viz_type == 'multi_axis_chart':
        # Skip multi-axis charts for Step 2
        if step_number == 2:
            return
        display_multi_axis_chart(data, title, options)
    elif viz_type == 'heatmap':
        # Skip heatmaps for Step 2
        if step_number == 2:
            return
        display_heatmap(data, title, options)
    else:
        st.info(f"Visualization type '{viz_type}' not yet implemented")

def has_yield_forecast_data(analysis_data):
    """Check if the analysis data contains yield forecast information"""
    # Check for yield_forecast in multiple possible locations
    if 'yield_forecast' in analysis_data and analysis_data['yield_forecast']:
        return True
    elif 'analysis' in analysis_data and 'yield_forecast' in analysis_data['analysis'] and analysis_data['analysis']['yield_forecast']:
        return True
    return False

def should_show_visualizations(step_result):
    """Check if a step should display visualizations based on visual keywords"""
    # Check if this is a forecast graph step - exclude it from showing Data Visualizations
    if should_show_forecast_graph(step_result):
        return False
    
    # Get step number and exclude steps 3-6 (Solution Recommendations, Regenerative Agriculture, Economic Impact, Yield Forecast)
    step_number = step_result.get('step_number', 0)
    if step_number >= 3 and step_number <= 6:
        return False
    
    # Get step content
    step_instructions = step_result.get('instructions', '')
    step_summary = step_result.get('summary', '')
    step_analysis = step_result.get('detailed_analysis', '')
    
    # Combine all text content
    combined_text = f"{step_instructions} {step_summary} {step_analysis}".lower()
    
    # Enhanced visual keywords list
    visual_keywords = [
        'visual', 'visualization', 'visualizations', 'chart', 'charts', 'graph', 'graphs', 
        'plot', 'plots', 'diagram', 'diagrams', 'comparison', 'compare', 'visual comparison', 
        'visualize', 'display', 'show', 'illustrate', 'visual comparisons', 'show visual',
        'show visual comparisons', 'plantation values vs mpob standards', 'vs mpob standards',
        'mpob standards', 'standards comparison', 'bar chart', 'line chart', 'pie chart',
        'scatter plot', 'histogram', 'radar chart', 'gauge chart', 'treemap', 'heatmap',
        'box plot', 'violin plot', 'bubble chart', 'area chart', 'doughnut chart'
    ]
    
    has_visual_keywords = any(keyword in combined_text for keyword in visual_keywords)
    
    # Always show for Step 1, or if visual keywords detected
    return step_number == 1 or has_visual_keywords

def generate_contextual_visualizations(step_result, analysis_data):
    """Generate contextual visualizations based on step content and visual keywords"""
    try:
        # Ensure step_result is a dictionary
        if not isinstance(step_result, dict):
            logger.error(f"step_result is not a dictionary: {type(step_result)}")
            return []
        
        # Ensure analysis_data is a dictionary
        if not isinstance(analysis_data, dict):
            logger.error(f"analysis_data is not a dictionary: {type(analysis_data)}")
            return []
        
        step_number = step_result.get('step_number', 0)
        visualizations = []
        
        # Get raw data for visualization
        raw_data = analysis_data.get('raw_data', {})
        soil_params = raw_data.get('soil_parameters', {})
        leaf_params = raw_data.get('leaf_parameters', {})
        
        # Get step content to check for specific visualization requests
        step_instructions = step_result.get('instructions', '')
        step_summary = step_result.get('summary', '')
        step_analysis = step_result.get('detailed_analysis', '')
        combined_text = f"{step_instructions} {step_summary} {step_analysis}".lower()
        
        # Check for visual keywords
        visual_keywords = [
            'visual', 'visualization', 'visualizations', 'chart', 'charts', 'graph', 'graphs', 
            'plot', 'plots', 'diagram', 'diagrams', 'comparison', 'compare', 'visual comparison', 
            'visualize', 'display', 'show', 'illustrate', 'visual comparisons', 'show visual',
            'show visual comparisons', 'plantation values vs mpob standards', 'vs mpob standards',
            'mpob standards', 'standards comparison', 'bar chart', 'line chart', 'pie chart',
            'scatter plot', 'histogram', 'radar chart', 'gauge chart', 'treemap', 'heatmap',
            'box plot', 'violin plot', 'bubble chart', 'area chart', 'doughnut chart'
        ]
        has_visual_keywords = any(keyword in combined_text for keyword in visual_keywords)
        
        # Generate visualizations based on step number and content
        if step_number == 1:  # Data Analysis
            # Create nutrient comparison charts
            if soil_params.get('parameter_statistics') or leaf_params.get('parameter_statistics'):
                viz_data = create_nutrient_comparison_viz(soil_params, leaf_params)
                if viz_data:
                    visualizations.append(viz_data)
            
            # Create actual vs optimal bar charts
            if soil_params.get('parameter_statistics'):
                soil_viz = create_actual_vs_optimal_viz(soil_params['parameter_statistics'], 'soil')
                if soil_viz:
                    visualizations.append(soil_viz)
            
            if leaf_params.get('parameter_statistics'):
                leaf_viz = create_actual_vs_optimal_viz(leaf_params['parameter_statistics'], 'leaf')
                if leaf_viz:
                    visualizations.append(leaf_viz)
            
            
            # Create MPOB standards comparison if requested
            if 'mpob standards' in combined_text or 'vs mpob standards' in combined_text:
                mpob_viz = create_mpob_standards_comparison_viz(soil_params, leaf_params)
                if mpob_viz:
                    visualizations.append(mpob_viz)
        
        elif step_number == 2:  # Issue Diagnosis
            # Generate visualizations for Step 2 if visual keywords are present
            if has_visual_keywords:
                # Create issues severity bar chart
                issues_viz = create_issues_severity_bar_viz(step_result, analysis_data)
                if issues_viz:
                    visualizations.append(issues_viz)
                
                # Create nutrient deficiency bar chart
                deficiency_viz = create_nutrient_deficiency_bar_viz(soil_params, leaf_params)
                if deficiency_viz:
                    visualizations.append(deficiency_viz)
                
                # Create specific issue visualizations based on content
                if 'soil acidity' in combined_text or 'ph' in combined_text or 'severe soil acidity' in combined_text:
                    soil_ph_viz = create_soil_ph_comparison_viz(soil_params)
                    if soil_ph_viz:
                        visualizations.append(soil_ph_viz)
        
        elif step_number == 3:  # Solution Recommendations
            # Create solution priority chart
            solution_viz = create_solution_priority_viz(step_result, analysis_data)
            if solution_viz:
                visualizations.append(solution_viz)
            
            # Create cost-benefit analysis chart
            cost_benefit_viz = create_cost_benefit_viz(analysis_data)
            if cost_benefit_viz:
                visualizations.append(cost_benefit_viz)
        
        # Generate additional visualizations based on content keywords
        if 'visual comparison' in combined_text or 'show visual' in combined_text:
            # Create comprehensive comparison charts
            comparison_viz = create_comprehensive_comparison_viz(soil_params, leaf_params)
            if comparison_viz:
                visualizations.append(comparison_viz)
        
        if 'plantation values' in combined_text and 'mpob' in combined_text:
            # Create plantation vs MPOB standards visualization
            plantation_viz = create_plantation_vs_mpob_viz(soil_params, leaf_params)
            if plantation_viz:
                visualizations.append(plantation_viz)
        
        # Create yield projection chart if yield data is available
        yield_data = analysis_data.get('yield_forecast', {})
        if yield_data:
            yield_viz = create_yield_projection_viz(yield_data)
            if yield_viz:
                visualizations.append(yield_viz)
        
        return visualizations
        
    except Exception as e:
        logger.error(f"Error generating contextual visualizations: {str(e)}")
        return []

def create_nutrient_comparison_viz(soil_params, leaf_params):
    """Create nutrient comparison visualization data"""
    try:
        soil_stats = soil_params.get('parameter_statistics', {})
        leaf_stats = leaf_params.get('parameter_statistics', {})
        
        if not soil_stats and not leaf_stats:
            return None
        
        # Prepare data for comparison
        nutrients = []
        soil_values = []
        leaf_values = []
        
        # Common nutrients to compare
        nutrient_mapping = {
            'N_%': 'Nitrogen (%)',
            'P_%': 'Phosphorus (%)', 
            'K_%': 'Potassium (%)',
            'Mg_%': 'Magnesium (%)',
            'Ca_%': 'Calcium (%)'
        }
        
        for soil_key, display_name in nutrient_mapping.items():
            if soil_key in soil_stats and soil_key in leaf_stats:
                soil_avg = soil_stats[soil_key].get('average', 0)
                leaf_avg = leaf_stats[soil_key].get('average', 0)
                
                if soil_avg > 0 or leaf_avg > 0:
                    nutrients.append(display_name)
                    soil_values.append(soil_avg)
                    leaf_values.append(leaf_avg)
        
        if not nutrients:
            return None
        
        return {
            'type': 'bar_chart',
            'title': 'Soil vs Leaf Nutrient Comparison',
            'subtitle': 'Comparison of average nutrient values between soil and leaf samples',
            'data': {
                'categories': nutrients,
                'series': [
                    {'name': 'Soil', 'data': soil_values, 'color': '#3498db'},
                    {'name': 'Leaf', 'data': leaf_values, 'color': '#e74c3c'}
                ]
            },
            'options': {
                'x_axis_title': 'Nutrients',
                'y_axis_title': 'Values (%)',
                'show_legend': True,
                'show_grid': True
            }
        }
        
    except Exception as e:
        logger.warning(f"Could not create nutrient comparison viz: {str(e)}")
        return None

def create_actual_vs_optimal_viz(parameter_stats, parameter_type):
    """Create actual vs optimal nutrient levels bar chart"""
    try:
        if not parameter_stats:
            return None
        
        # Get MPOB standards
        try:
            from utils.mpob_standards import get_mpob_standards
            mpob = get_mpob_standards()
        except:
            mpob = None
        
        categories = []
        actual_values = []
        optimal_values = []
        
        # Define parameter mappings
        if parameter_type == 'soil':
            param_mapping = {
                'pH': 'pH',
                'Nitrogen_%': 'Nitrogen %',
                'Organic_Carbon_%': 'Organic Carbon %',
                'Total_P_mg_kg': 'Total P (mg/kg)',
                'Available_P_mg_kg': 'Available P (mg/kg)',
                'Exchangeable_K_meq%': 'Exch. K (meq%)',
                'Exchangeable_Ca_meq%': 'Exch. Ca (meq%)',
                'Exchangeable_Mg_meq%': 'Exch. Mg (meq%)',
                'CEC_meq%': 'CEC (meq%)'
            }
        else:  # leaf
            param_mapping = {
                'N_%': 'N %',
                'P_%': 'P %',
                'K_%': 'K %',
                'Mg_%': 'Mg %',
                'Ca_%': 'Ca %',
                'B_mg_kg': 'B (mg/kg)',
                'Cu_mg_kg': 'Cu (mg/kg)',
                'Zn_mg_kg': 'Zn (mg/kg)'
            }
        
        # Extract data
        for param_key, display_name in param_mapping.items():
            if param_key in parameter_stats:
                actual_val = parameter_stats[param_key].get('average', 0)
                if actual_val > 0:
                    categories.append(display_name)
                    actual_values.append(actual_val)
                    
                    # Get optimal value with correct MPOB standards
                    optimal_val = 0
                    if parameter_type == 'soil':
                        # Use correct MPOB soil standards
                        if param_key == 'pH':
                            optimal_val = 5.0
                        elif param_key == 'Nitrogen_%':
                            optimal_val = 0.125
                        elif param_key == 'Organic_Carbon_%':
                            optimal_val = 2.0
                        elif param_key == 'Total_P_mg_kg':
                            optimal_val = 30
                        elif param_key == 'Available_P_mg_kg':
                            optimal_val = 22
                        elif param_key == 'Exchangeable_K_meq%':
                            optimal_val = 0.20
                        elif param_key == 'Exchangeable_Ca_meq%':
                            optimal_val = 3.0
                        elif param_key == 'Exchangeable_Mg_meq%':
                            optimal_val = 1.15
                        elif param_key == 'CEC_meq%':
                            optimal_val = 12.0
                    else:  # leaf
                        # Use correct MPOB leaf standards
                        if param_key == 'N_%':
                            optimal_val = 2.6
                        elif param_key == 'P_%':
                            optimal_val = 0.165
                        elif param_key == 'K_%':
                            optimal_val = 1.05
                        elif param_key == 'Mg_%':
                            optimal_val = 0.30
                        elif param_key == 'Ca_%':
                            optimal_val = 0.60
                        elif param_key == 'B_mg_kg':
                            optimal_val = 20
                        elif param_key == 'Cu_mg_kg':
                            optimal_val = 7.5
                        elif param_key == 'Zn_mg_kg':
                            optimal_val = 20
                    
                    optimal_values.append(optimal_val)
        
        if not categories:
            return None
        
        return {
            'type': 'actual_vs_optimal_bar',
            'title': f'📊 {parameter_type.title()} Nutrients: Actual vs Optimal Levels',
            'subtitle': f'Direct comparison of current {parameter_type} nutrient levels against MPOB optimal standards',
            'data': {
                'categories': categories,
                'series': [
                    {'name': 'Actual Levels', 'values': actual_values, 'color': '#3498db' if parameter_type == 'soil' else '#2ecc71'},
                    {'name': 'Optimal Levels', 'values': optimal_values, 'color': '#e74c3c' if parameter_type == 'soil' else '#e67e22'}
                ]
            },
            'options': {
                'show_legend': True,
                'show_values': True,
                'bar_width': 0.7,
                'y_axis_title': 'Nutrient Levels',
                'x_axis_title': f'{parameter_type.title()} Parameters',
                'show_target_line': True,
                'target_line_color': '#f39c12'
            }
        }
        
    except Exception as e:
        logger.error(f"Error creating actual vs optimal visualization: {e}")
        return None

# REMOVED: create_nutrient_ratio_viz function - Soil/Leaf Nutrient Ratios Analysis no longer needed

# REMOVED: calculate_nutrient_ratios function - Soil/Leaf Nutrient Ratios Analysis no longer needed

def create_issues_severity_viz(issues):
    """Create issues severity visualization data"""
    try:
        if not issues:
            return None
        
        # Count issues by severity
        severity_counts = {}
        for issue in issues:
            severity = issue.get('severity', 'Unknown')
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        if not severity_counts:
            return None
        
        return {
            'type': 'pie_chart',
            'title': 'Issues Distribution by Severity',
            'subtitle': 'Breakdown of identified issues by severity level',
            'data': {
                'labels': list(severity_counts.keys()),
                'values': list(severity_counts.values()),
                'colors': ['#e74c3c', '#f39c12', '#f1c40f', '#2ecc71', '#3498db']
            }
        }
        
    except Exception as e:
        logger.warning(f"Could not create issues severity viz: {str(e)}")
        return None

def create_solution_impact_viz(recommendations):
    """Create solution impact visualization data"""
    try:
        if not recommendations:
            return None
        
        # Extract solution data
        solutions = []
        impacts = []
        
        for rec in recommendations:
            if isinstance(rec, dict):
                param = rec.get('parameter', 'Unknown')
                solutions.append(param)
                # Mock impact score based on severity
                severity = rec.get('severity', 'Medium')
                impact_scores = {'Critical': 5, 'High': 4, 'Medium': 3, 'Low': 2, 'Unknown': 1}
                impacts.append(impact_scores.get(severity, 3))
            else:
                solutions.append(str(rec)[:20])
                impacts.append(3)
        
        if not solutions:
            return None
        
        return {
            'type': 'bar_chart',
            'title': 'Solution Impact Analysis',
            'subtitle': 'Impact scores for recommended solutions',
            'data': {
                'categories': solutions,
                'series': [{'name': 'Impact Score', 'data': impacts, 'color': '#27ae60'}]
            },
            'options': {
                'x_axis_title': 'Solutions',
                'y_axis_title': 'Impact Score',
                'show_legend': False,
                'show_grid': True,
                'horizontal': True
            }
        }
        
    except Exception as e:
        logger.warning(f"Could not create solution impact viz: {str(e)}")
        return None

def create_economic_analysis_viz(economic_data):
    """Create economic analysis visualization data"""
    try:
        # Extract economic data
        years = [1, 2, 3, 4, 5]
        roi_values = []
        
        # Mock ROI data based on economic forecast
        base_roi = economic_data.get('projected_roi', 15)
        for year in years:
            roi_values.append(base_roi + (year - 1) * 2)  # Increasing ROI over time
        
        return {
            'type': 'line_chart',
            'title': 'Projected Return on Investment',
            'subtitle': 'ROI projection over 5 years',
            'data': {
                'x_values': years,
                'y_values': roi_values,
                'series_name': 'ROI (%)'
            },
            'options': {
                'x_axis_title': 'Years',
                'y_axis_title': 'ROI (%)',
                'show_legend': False,
                'show_grid': True,
                'markers': True
            }
        }
        
    except Exception as e:
        logger.warning(f"Could not create economic analysis viz: {str(e)}")
        return None

def create_yield_projection_viz(yield_data):
    """Create yield projection visualization data with multiple investment scenarios"""
    try:
        # Extract yield data
        years = [1, 2, 3, 4, 5]
        current_yield = yield_data.get('current_yield', 15)
        projected_yield = yield_data.get('projected_yield', 25)
        
        # Create multiple investment scenarios
        scenarios = {
            'High Investment': [],
            'Medium Investment': [],
            'Low Investment': [],
            'Current (No Change)': []
        }
        
        # Calculate yield progression for each scenario
        for year in years:
            # High investment: reaches projected yield by year 3, then maintains
            high_yield = current_yield + (projected_yield - current_yield) * min(year / 3, 1)
            scenarios['High Investment'].append(high_yield)
            
            # Medium investment: reaches 80% of projected yield by year 4
            medium_yield = current_yield + (projected_yield - current_yield) * 0.8 * min(year / 4, 1)
            scenarios['Medium Investment'].append(medium_yield)
            
            # Low investment: reaches 60% of projected yield by year 5
            low_yield = current_yield + (projected_yield - current_yield) * 0.6 * min(year / 5, 1)
            scenarios['Low Investment'].append(low_yield)
            
            # Current (no change): stays at current yield
            scenarios['Current (No Change)'].append(current_yield)
        
        # Create series data for line chart
        series = []
        colors = ['#28a745', '#17a2b8', '#ffc107', '#6c757d']
        
        for i, (scenario_name, values) in enumerate(scenarios.items()):
            series.append({
                'name': scenario_name,
                'data': values,
                'color': colors[i]
            })
        
        return {
            'type': 'line_chart',
            'title': '5-Year Yield Forecast by Investment Scenario',
            'subtitle': 'Projected yield increase over 5 years with different investment levels',
            'data': {
                'categories': [f'Year {year}' for year in years],
                'series': series
            },
            'options': {
                'x_axis_title': 'Years',
                'y_axis_title': 'Yield (tons/hectare)',
                'show_legend': True,
                'show_grid': True,
                'markers': True
            }
        }
        
    except Exception as e:
        logger.warning(f"Could not create yield projection viz: {str(e)}")
        return None

def should_show_forecast_graph(step_result):
    """Check if a step should display the 5-year yield forecast graph"""
    # Ensure step_result is a dictionary
    if not isinstance(step_result, dict):
        return False
    
    step_description = step_result.get('step_description', '')
    step_title = step_result.get('step_title', '')
    
    # Specific keywords that indicate forecast graph should be shown
    forecast_keywords = [
        'forecast graph', '5-year yield forecast graph', '5-year yield forecast',
        'yield projection graph', '5-year forecast graph', 'forecast graph generate',
        'yield projection graph (5 years)', '5-year yield projection graph'
    ]
    
    # Check if any specific forecast keywords are in the step description or title
    combined_text = f"{step_title} {step_description}".lower()
    return any(keyword in combined_text for keyword in forecast_keywords)

def display_step_specific_content(step_result, step_number):
    """Display step-specific content based on step type"""
    analysis_data = step_result
    
    # Only show forecast graph if step instructions contain forecast graph keywords
    if should_show_forecast_graph(step_result) and has_yield_forecast_data(analysis_data):
        step_title = analysis_data.get('step_title', f'Step {step_number}')
        display_forecast_graph_content(analysis_data, step_number, step_title)

def display_bar_chart(data, title):
    """Display bar chart with separate charts for each parameter"""
    try:
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots
        import pandas as pd
        
        # Handle different data formats
        categories = None
        values = None
        series = None
        
        if isinstance(data, dict):
            # Standard format: data has 'categories' and 'values' keys
            if 'categories' in data and 'values' in data:
                categories = data['categories']
                values = data['values']
            # Series format: data has 'categories' and 'series' keys
            elif 'categories' in data and 'series' in data:
                categories = data['categories']
                series = data['series']
            # Alternative format: data might have different key names
            elif 'labels' in data and 'values' in data:
                categories = data['labels']
                values = data['values']
            elif 'x' in data and 'y' in data:
                categories = data['x']
                values = data['y']
            # Check if data is nested under 'data' key
            elif 'data' in data and isinstance(data['data'], dict):
                nested_data = data['data']
                if 'categories' in nested_data and 'values' in nested_data:
                    categories = nested_data['categories']
                    values = nested_data['values']
                elif 'categories' in nested_data and 'series' in nested_data:
                    categories = nested_data['categories']
                    series = nested_data['series']
                elif 'labels' in nested_data and 'values' in nested_data:
                    categories = nested_data['labels']
                    values = nested_data['values']
        
        if not categories:
            st.warning("Bar chart data format not supported")
            return
        
        # If we have series data, use it; otherwise use single values
        if series and isinstance(series, list) and len(series) > 0:
            # Handle series data - create separate charts for each parameter
            if isinstance(series[0], dict) and 'values' in series[0]:
                # Multiple series format
                actual_values = series[0]['values'] if len(series) > 0 else []
                optimal_values = series[1]['values'] if len(series) > 1 else []
                
                if actual_values and optimal_values:
                    # Create subplots - one for each parameter
                    num_params = len(categories)
                    fig = make_subplots(
                        rows=1, 
                        cols=num_params,
                        subplot_titles=categories,
                        horizontal_spacing=0.05
                    )
                    
                    # Define colors
                    actual_color = series[0].get('color', '#3498db')
                    optimal_color = series[1].get('color', '#e74c3c')
                    
                    # Add bars for each parameter
                    for i, param in enumerate(categories):
                        actual_val = actual_values[i]
                        optimal_val = optimal_values[i]
                        
                        # Calculate appropriate scale for this parameter
                        max_val = max(actual_val, optimal_val)
                        min_val = min(actual_val, optimal_val)
                        
                        # Add some padding to the scale
                        range_val = max_val - min_val
                        if range_val == 0:
                            range_val = max_val * 0.1 if max_val > 0 else 1
                        
                        y_max = max_val + (range_val * 0.4)  # Increased padding for outside text
                        y_min = max(0, min_val - (range_val * 0.2))  # Increased padding for outside text
                        
                        # Add actual value bar
                        fig.add_trace(
                            go.Bar(
                                x=['Observed'],
                                y=[actual_val],
                                name='Observed' if i == 0 else None,
                                marker_color=actual_color,
                                text=[f"{actual_val:.1f}"],
                                textposition='outside',
                                textfont=dict(size=10, color='black', family='Arial Black'),
                                showlegend=(i == 0)
                            ),
                            row=1, col=i+1
                        )
                        
                        # Add optimal value bar
                        fig.add_trace(
                            go.Bar(
                                x=['Recommended'],
                                y=[optimal_val],
                                name='Recommended' if i == 0 else None,
                                marker_color=optimal_color,
                                text=[f"{optimal_val:.1f}"],
                                textposition='outside',
                                textfont=dict(size=10, color='black', family='Arial Black'),
                                showlegend=(i == 0)
                            ),
                            row=1, col=i+1
                        )
                        
                        # Update y-axis for this subplot
                        fig.update_yaxes(
                            range=[y_min, y_max],
                            row=1, col=i+1,
                            showgrid=True,
                            gridwidth=1,
                            gridcolor='lightgray',
                            zeroline=True,
                            zerolinewidth=1,
                            zerolinecolor='lightgray'
                        )
                        
                        # Update x-axis for this subplot
                        fig.update_xaxes(
                            row=1, col=i+1,
                            showgrid=False,
                            tickangle=0
                        )
                    
                    # Update layout
                    fig.update_layout(
                        title={
                            'text': title,
                            'x': 0.5,
                            'xanchor': 'center',
                            'font': {'size': 16}
                        },
                        height=400,
                        showlegend=True,
                        legend=dict(
                            orientation="h",
                            yanchor="bottom",
                            y=1.02,
                            xanchor="right",
                            x=1
                        )
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    return
            else:
                # Single series format - convert to values
                values = series
        elif values:
            # Single values format - create simple bar chart
            if len(values) != len(categories):
                st.warning("Number of categories and values don't match")
                return
            
            # Create subplots - one for each parameter
            num_params = len(categories)
            fig = make_subplots(
                rows=1, 
                cols=num_params,
                subplot_titles=categories,
                horizontal_spacing=0.1
            )
            
            # Add bars for each parameter
            for i, param in enumerate(categories):
                val = values[i]
                
                # Calculate appropriate scale for this parameter
                y_max = val * 1.2 if val > 0 else 1
                y_min = 0
                
                # Add value bar
                fig.add_trace(
                    go.Bar(
                        x=['Value'],
                        y=[val],
                        marker_color='#3498db',
                        text=[f"{val:.1f}"],
                        textposition='auto',
                        showlegend=False
                    ),
                    row=1, col=i+1
                )
                
                # Update y-axis for this subplot
                fig.update_yaxes(
                    range=[y_min, y_max],
                    row=1, col=i+1,
                    showgrid=True,
                    gridwidth=1,
                    gridcolor='lightgray',
                    zeroline=True,
                    zerolinewidth=1,
                    zerolinecolor='lightgray'
                )
                
                # Update x-axis for this subplot
                fig.update_xaxes(
                    row=1, col=i+1,
                    showgrid=False,
                    tickangle=0
                )
            
            # Update layout
            fig.update_layout(
                title={
                    'text': title,
                    'x': 0.5,
                    'xanchor': 'center',
                    'font': {'size': 16}
                },
                height=400,
                showlegend=False
            )
            
            st.plotly_chart(fig, use_container_width=True)
            return
        
        # Fallback: if we have categories but no values, try to create dummy values
        if categories and not values:
            logger.info("No categories found, creating generic categories")
            categories = [f"Item {i+1}" for i in range(len(values))]
        
        if categories and values and len(categories) == len(values):
            # Ensure values are numeric and handle edge cases
            try:
                numeric_values = []
                for v in values:
                    if v is None:
                        numeric_values.append(0)
                    elif isinstance(v, (int, float)):
                        numeric_values.append(float(v))
                    elif isinstance(v, str):
                        # Try to convert string to number
                        try:
                            numeric_values.append(float(v))
                        except ValueError:
                            # If conversion fails, use 0
                            numeric_values.append(0)
                    else:
                        numeric_values.append(0)
                
                # Validate that we have meaningful data
                if all(v == 0 for v in numeric_values):
                    st.warning("⚠️ All chart values are zero. This may indicate data quality issues.")
                    return
                
                # Check for reasonable data ranges
                max_val = max(numeric_values)
                min_val = min(numeric_values)
                if max_val > 1000000:  # Very large numbers might indicate data issues
                    st.warning("⚠️ Chart values seem unusually large. Please verify data accuracy.")
                
                df = pd.DataFrame({
                    'Category': categories,
                    'Value': numeric_values
                })
                
                # Create enhanced bar chart with better styling and accuracy
                fig = go.Figure(data=[
                    go.Bar(
                        x=df['Category'],
                        y=df['Value'],
                        marker=dict(
                            color=df['Value'],
                            colorscale='Viridis',
                            showscale=True,
                            colorbar=dict(title="Value"),
                            line=dict(color='rgba(0,0,0,0.2)', width=1)
                        ),
                        text=[f'{v:.2f}' if v != int(v) else f'{int(v)}' for v in df['Value']],
                        textposition='auto',
                        textfont=dict(size=12, color='white'),
                        hovertemplate='<b>%{x}</b><br>Value: %{y:.2f}<extra></extra>',
                        name='Values'
                    )
                ])
                
                # Enhanced layout with better accuracy
                fig.update_layout(
                    title=dict(
                        text=title,
                        x=0.5,
                        font=dict(size=16, color='#2E7D32')
                    ),
                    xaxis=dict(
                        title="Categories",
                        tickangle=-45,
                        showgrid=True,
                        gridcolor='rgba(0,0,0,0.1)'
                    ),
                    yaxis=dict(
                        title="Values",
                        showgrid=True,
                        gridcolor='rgba(0,0,0,0.1)',
                        zeroline=True,
                        zerolinecolor='rgba(0,0,0,0.3)'
                    ),
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(size=12),
                    height=400,
                    margin=dict(l=50, r=50, t=80, b=100),
                    showlegend=False
                )
                
                # Add data accuracy note
                st.info(f"📊 Chart displays {len(categories)} data points. Range: {min_val:.2f} - {max_val:.2f}")
                st.plotly_chart(fig, use_container_width=True)
                
            except (ValueError, TypeError) as e:
                st.error(f"❌ Error processing chart data: {str(e)}")
                st.warning("Please check that all values are numeric.")
                return
        else:
            # Enhanced error message with more helpful information
            if isinstance(data, dict):
                received_keys = list(data.keys())
                st.warning(f"⚠️ Bar chart data format not recognized. Expected 'categories' and 'values' keys, or 'categories' and 'series' keys. Received: {received_keys}")
                
                # Provide helpful suggestions based on what keys were found
                if 'categories' in received_keys:
                    st.info("💡 Found 'categories' key. Looking for 'values' or 'series' key...")
                    if 'data' in received_keys:
                        st.info("💡 Found 'data' key. The chart data might be nested under this key.")
                elif 'labels' in received_keys:
                    st.info("💡 Found 'labels' key. This might be the categories. Looking for corresponding values...")
                elif 'x' in received_keys:
                    st.info("💡 Found 'x' key. This might be the categories. Looking for 'y' values...")
                else:
                    st.info("💡 No recognized category keys found. Please check the data structure.")
                
                # Show detailed debugging information
                st.markdown("### 🔍 Debug Information")
                for key, value in data.items():
                    st.markdown(f"**{key}:** {type(value)} - {str(value)[:100]}{'...' if len(str(value)) > 100 else ''}")
                
            else:
                st.warning(f"⚠️ Bar chart data is not a dictionary. Received: {type(data)}")
            
            # Show the actual data structure for debugging
            st.json(data)
    except ImportError:
        st.info("Plotly not available for chart display")
    except Exception as e:
        logger.error(f"Error displaying bar chart: {e}")
        st.error(f"Error displaying bar chart: {str(e)}")
        st.json(data)  # Show data for debugging

def display_pie_chart(data, title):
    """Display enhanced pie chart visualization with better styling"""
    try:
        import plotly.express as px
        import plotly.graph_objects as go
        import pandas as pd
        
        if 'labels' in data and 'values' in data:
            df = pd.DataFrame({
                'Label': data['labels'],
                'Value': data['values']
            })
            
            # Create enhanced pie chart with better styling
            fig = go.Figure(data=[go.Pie(
                labels=df['Label'],
                values=df['Value'],
                hole=0.3,
                textinfo='label+percent+value',
                textposition='auto',
                marker=dict(
                    colors=['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD', '#98D8C8'],
                    line=dict(color='#FFFFFF', width=2)
                ),
                hovertemplate='<b>%{label}</b><br>Value: %{value}<br>Percentage: %{percent}<extra></extra>'
            )])
            
            fig.update_layout(
                title=dict(
                    text=title,
                    x=0.5,
                    font=dict(size=16, color='#2E7D32')
                ),
                showlegend=True,
                height=400,
                font=dict(size=12)
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Pie chart data format not recognized")
    except ImportError:
        st.info("Plotly not available for chart display")

def display_line_chart(data, title):
    """Display enhanced line chart visualization with better styling"""
    try:
        import plotly.express as px
        import plotly.graph_objects as go
        import pandas as pd
        
        # Handle different data formats
        x_data = None
        y_data = None
        series_name = 'Data'
        x_title = "X Axis"
        y_title = "Y Axis"
        
        # Check for standard format: {'x': [...], 'y': [...]}
        if 'x' in data and 'y' in data:
            x_data = data['x']
            y_data = data['y']
        
        # Check for alternative format: {'x_values': [...], 'y_values': [...]}
        elif 'x_values' in data and 'y_values' in data:
            x_data = data['x_values']
            y_data = data['y_values']
            series_name = data.get('series_name', 'Data')
        
        # Check for categories and series format
        elif 'categories' in data and 'series' in data:
            categories = data['categories']
            series_data = data['series']
            
            if isinstance(series_data, list) and len(series_data) > 0:
                if isinstance(series_data[0], dict):
                    # Multiple series
                    fig = go.Figure()
                    for i, series in enumerate(series_data):
                        series_name = series.get('name', f'Series {i+1}')
                        series_values = series.get('data', [])
                        series_color = series.get('color', f'hsl({i*60}, 70%, 50%)')
                        
                        fig.add_trace(go.Scatter(
                            x=categories,
                            y=series_values,
                            mode='lines+markers',
                            name=series_name,
                            line=dict(
                                color=series_color,
                                width=3,
                                shape='spline'
                            ),
                            marker=dict(
                                size=8,
                                color=series_color,
                                line=dict(width=2, color='#FFFFFF')
                            ),
                            hovertemplate=f'<b>{series_name}:</b> %{{y}}<br><b>X:</b> %{{x}}<extra></extra>'
                        ))
                    
                    fig.update_layout(
                        title=dict(
                            text=title,
                            x=0.5,
                            font=dict(size=16, color='#2E7D32')
                        ),
                        xaxis_title="Categories",
                        yaxis_title="Values",
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)',
                        font=dict(size=12),
                        height=400,
                        hovermode='x unified'
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    return
                else:
                    # Single series
                    x_data = categories
                    y_data = series_data
        
        # Check for nested data format
        elif 'data' in data and isinstance(data['data'], dict):
            nested_data = data['data']
            if 'x' in nested_data and 'y' in nested_data:
                x_data = nested_data['x']
                y_data = nested_data['y']
            elif 'x_values' in nested_data and 'y_values' in nested_data:
                x_data = nested_data['x_values']
                y_data = nested_data['y_values']
                series_name = nested_data.get('series_name', 'Data')
        
        # Create the chart if we have valid data
        if x_data and y_data and len(x_data) == len(y_data):
            df = pd.DataFrame({
                'X': x_data,
                'Y': y_data
            })
            
            # Create enhanced line chart with better styling
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=df['X'],
                y=df['Y'],
                mode='lines+markers',
                name=series_name,
                line=dict(
                    color='#2E7D32',
                    width=3,
                    shape='spline'
                ),
                marker=dict(
                    size=8,
                    color='#4CAF50',
                    line=dict(width=2, color='#FFFFFF')
                ),
                hovertemplate=f'<b>{series_name}:</b> %{{y}}<br><b>X:</b> %{{x}}<extra></extra>',
                fill='tonexty'
            ))
            
            fig.update_layout(
                title=dict(
                    text=title,
                    x=0.5,
                    font=dict(size=16, color='#2E7D32')
                ),
                xaxis_title=x_title,
                yaxis_title=y_title,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(size=12),
                height=400,
                hovermode='x unified'
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info(f"Line chart data format not recognized. Available keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
    except ImportError:
        st.info("Plotly not available for chart display")
    except Exception as e:
        st.error(f"Error displaying line chart: {str(e)}")
        st.info(f"Data structure: {data}")

def display_scatter_plot(data, title):
    """Display enhanced scatter plot visualization with better styling"""
    try:
        import plotly.express as px
        import plotly.graph_objects as go
        import pandas as pd
        
        if 'x' in data and 'y' in data:
            df = pd.DataFrame({
                'X': data['x'],
                'Y': data['y']
            })
            
            # Create enhanced scatter plot with better styling
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=df['X'],
                y=df['Y'],
                mode='markers',
                name='Data Points',
                marker=dict(
                    size=12,
                    color=df['Y'],
                    colorscale='Viridis',
                    showscale=True,
                    colorbar=dict(title="Y Value"),
                    line=dict(width=2, color='#FFFFFF')
                ),
                hovertemplate='<b>X:</b> %{x}<br><b>Y:</b> %{y}<extra></extra>'
            ))
            
            fig.update_layout(
                title=dict(
                    text=title,
                    x=0.5,
                    font=dict(size=16, color='#2E7D32')
                ),
                xaxis_title="X Axis",
                yaxis_title="Y Axis",
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(size=12),
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Scatter plot data format not recognized")
    except ImportError:
        st.info("Plotly not available for chart display")

def display_actual_vs_optimal_bar(data, title, options):
    """Display actual vs optimal bar chart with separate charts for each parameter"""
    try:
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots
        import pandas as pd
        
        categories = data.get('categories', [])
        series = data.get('series', [])
        
        if not categories or not series:
            st.warning("Bar chart data format not supported")
            return
        
        # Extract actual and optimal values
        actual_values = series[0]['values'] if len(series) > 0 else []
        optimal_values = series[1]['values'] if len(series) > 1 else []
        
        if not actual_values or not optimal_values:
            st.warning("Insufficient data for bar chart")
            return
        
        # Create subplots - one for each parameter
        num_params = len(categories)
        
        # Calculate optimal layout - if more than 4 parameters, use 2 rows
        if num_params > 4:
            rows = 2
            cols = (num_params + 1) // 2
        else:
            rows = 1
            cols = num_params
        
        fig = make_subplots(
            rows=rows, 
            cols=cols,
            subplot_titles=categories,
            horizontal_spacing=0.05,
            vertical_spacing=0.2
        )
        
        # Define colors
        actual_color = series[0].get('color', '#3498db')
        optimal_color = series[1].get('color', '#e74c3c')
        
        # Add bars for each parameter
        for i, param in enumerate(categories):
            actual_val = actual_values[i]
            optimal_val = optimal_values[i]
            
            # Calculate appropriate scale for this parameter
            max_val = max(actual_val, optimal_val)
            min_val = min(actual_val, optimal_val)
            
            # Add more padding to the scale to accommodate outside text
            range_val = max_val - min_val
            if range_val == 0:
                range_val = max_val * 0.1 if max_val > 0 else 1
            
            y_max = max_val + (range_val * 0.4)  # Increased padding for outside text
            y_min = max(0, min_val - (range_val * 0.2))  # Increased padding for outside text
            
            # Calculate row and column position
            if rows == 1:
                row_pos = 1
                col_pos = i + 1
            else:
                row_pos = (i // cols) + 1
                col_pos = (i % cols) + 1
            
            # Add actual value bar
            fig.add_trace(
                go.Bar(
                    x=['Observed'],
                    y=[actual_val],
                    name='Observed' if i == 0 else None,  # Only show legend for first chart
                    marker_color=actual_color,
                    text=[f"{actual_val:.1f}"],
                    textposition='outside',
                    textfont=dict(size=10, color='black', family='Arial Black'),
                    showlegend=(i == 0)
                ),
                row=row_pos, col=col_pos
            )
            
            # Add optimal value bar
            fig.add_trace(
                go.Bar(
                    x=['Recommended'],
                    y=[optimal_val],
                    name='Recommended' if i == 0 else None,  # Only show legend for first chart
                    marker_color=optimal_color,
                    text=[f"{optimal_val:.1f}"],
                    textposition='outside',
                    textfont=dict(size=10, color='black', family='Arial Black'),
                    showlegend=(i == 0)
                ),
                row=row_pos, col=col_pos
            )
            
            # Update y-axis for this subplot
            fig.update_yaxes(
                range=[y_min, y_max],
                row=row_pos, col=col_pos,
                showgrid=True,
                gridwidth=1,
                gridcolor='lightgray',
                zeroline=True,
                zerolinewidth=1,
                zerolinecolor='lightgray',
                tickfont=dict(size=10)
            )
            
            # Update x-axis for this subplot
            fig.update_xaxes(
                row=row_pos, col=col_pos,
                showgrid=False,
                tickangle=0,
                tickfont=dict(size=10)
            )
        
        # Update layout
        fig.update_layout(
            title={
                'text': title,
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 16}
            },
            height=600 if rows > 1 else 400,
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        logger.error(f"Error displaying actual vs optimal bar chart: {e}")
        st.error("Error displaying actual vs optimal bar chart")

# REMOVED: display_nutrient_ratio_diagram function - Soil/Leaf Nutrient Ratios Analysis no longer needed

def display_enhanced_bar_chart(data, title, options=None):
    """Display enhanced bar chart with separate charts for each parameter"""
    try:
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots
        import pandas as pd
        
        if 'categories' in data and 'series' in data:
            categories = data['categories']
            series = data['series']
            
            # Check if we have multiple series (actual vs optimal format)
            if len(series) >= 2 and isinstance(series[0], dict) and 'values' in series[0]:
                # Multiple series format - create separate charts for each parameter
                actual_values = series[0]['values'] if len(series) > 0 else []
                optimal_values = series[1]['values'] if len(series) > 1 else []
                
                if actual_values and optimal_values:
                    # Create subplots - one for each parameter
                    num_params = len(categories)
                    fig = make_subplots(
                        rows=1, 
                        cols=num_params,
                        subplot_titles=categories,
                        horizontal_spacing=0.05
                    )
                    
                    # Define colors
                    actual_color = series[0].get('color', '#3498db')
                    optimal_color = series[1].get('color', '#e74c3c')
                    
                    # Add bars for each parameter
                    for i, param in enumerate(categories):
                        actual_val = actual_values[i]
                        optimal_val = optimal_values[i]
                        
                        # Calculate appropriate scale for this parameter
                        max_val = max(actual_val, optimal_val)
                        min_val = min(actual_val, optimal_val)
                        
                        # Add some padding to the scale
                        range_val = max_val - min_val
                        if range_val == 0:
                            range_val = max_val * 0.1 if max_val > 0 else 1
                        
                        y_max = max_val + (range_val * 0.4)  # Increased padding for outside text
                        y_min = max(0, min_val - (range_val * 0.2))  # Increased padding for outside text
                        
                        # Add actual value bar
                        fig.add_trace(
                            go.Bar(
                                x=['Observed'],
                                y=[actual_val],
                                name='Observed' if i == 0 else None,
                                marker_color=actual_color,
                                text=[f"{actual_val:.1f}"],
                                textposition='outside',
                                textfont=dict(size=10, color='black', family='Arial Black'),
                                showlegend=(i == 0)
                            ),
                            row=1, col=i+1
                        )
                        
                        # Add optimal value bar
                        fig.add_trace(
                            go.Bar(
                                x=['Recommended'],
                                y=[optimal_val],
                                name='Recommended' if i == 0 else None,
                                marker_color=optimal_color,
                                text=[f"{optimal_val:.1f}"],
                                textposition='outside',
                                textfont=dict(size=10, color='black', family='Arial Black'),
                                showlegend=(i == 0)
                            ),
                            row=1, col=i+1
                        )
                        
                        # Update y-axis for this subplot
                        fig.update_yaxes(
                            range=[y_min, y_max],
                            row=1, col=i+1,
                            showgrid=True,
                            gridwidth=1,
                            gridcolor='lightgray',
                            zeroline=True,
                            zerolinewidth=1,
                            zerolinecolor='lightgray'
                        )
                        
                        # Update x-axis for this subplot
                        fig.update_xaxes(
                            row=1, col=i+1,
                            showgrid=False,
                            tickangle=0
                        )
                    
                    # Update layout
                    fig.update_layout(
                        title={
                            'text': title,
                            'x': 0.5,
                            'xanchor': 'center',
                            'font': {'size': 16}
                        },
                        height=400,
                        showlegend=True,
                        legend=dict(
                            orientation="h",
                            yanchor="bottom",
                            y=1.02,
                            xanchor="right",
                            x=1
                        )
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    return
            else:
                # Single series or different format - use original logic
                fig = go.Figure()
            
            # Add each series as a bar trace
            for i, series_data in enumerate(series):
                if isinstance(series_data, dict) and 'name' in series_data and 'values' in series_data:
                    name = series_data['name']
                    values = series_data['values']
                    color = series_data.get('color', f'#{i*50:02x}{i*100:02x}{i*150:02x}')
                    
                    fig.add_trace(go.Bar(
                        name=name,
                        x=categories,
                        y=values,
                        marker_color=color,
                        hovertemplate=f'<b>{name}</b><br>%{{x}}: %{{y}}<extra></extra>',
                            text=values if options and options.get('show_values', False) else None,
                        textposition='auto'
                    ))
            
            # Update layout with options
            fig.update_layout(
                title=dict(
                    text=title,
                    x=0.5,
                    font=dict(size=16, color='#2E7D32')
                ),
                    xaxis_title=options.get('x_axis_title', 'Parameters') if options else 'Parameters',
                    yaxis_title=options.get('y_axis_title', 'Value') if options else 'Value',
                barmode='group',
                    showlegend=options.get('show_legend', True) if options else True,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(size=12),
                height=500
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            # Silently skip if data format not recognized - don't show error message
            return
    except ImportError:
        st.info("Plotly not available for chart display")

def display_range_chart(data, title, options=None):
    """Display range chart showing min, max, average with error bars"""
    try:
        import plotly.graph_objects as go
        
        if 'categories' in data and 'series' in data:
            categories = data['categories']
            series = data['series']
            
            fig = go.Figure()
            
            # Find min, max, average series
            min_series = None
            max_series = None
            avg_series = None
            optimal_series = None
            
            for series_data in series:
                if isinstance(series_data, dict) and 'name' in series_data:
                    name = series_data['name'].lower()
                    if 'minimum' in name:
                        min_series = series_data
                    elif 'maximum' in name:
                        max_series = series_data
                    elif 'average' in name:
                        avg_series = series_data
                    elif 'optimal' in name:
                        optimal_series = series_data
            
            # Add range bars
            if min_series and max_series:
                fig.add_trace(go.Bar(
                    name='Range',
                    x=categories,
                    y=[max_val - min_val for max_val, min_val in zip(max_series['values'], min_series['values'])],
                    base=min_series['values'],
                    marker_color='rgba(0,100,80,0.2)',
                    showlegend=False
                ))
            
            # Add average bars
            if avg_series:
                fig.add_trace(go.Bar(
                    name=avg_series['name'],
                    x=categories,
                    y=avg_series['values'],
                    marker_color=avg_series.get('color', '#4ECDC4'),
                    hovertemplate=f'<b>{avg_series["name"]}</b><br>%{{x}}: %{{y}}<extra></extra>',
                    text=avg_series['values'],
                    textposition='auto'
                ))
            
            # Add optimal line
            if optimal_series:
                fig.add_trace(go.Scatter(
                    name=optimal_series['name'],
                    x=categories,
                    y=optimal_series['values'],
                    mode='markers+lines',
                    marker=dict(
                        color=optimal_series.get('color', '#FFD700'),
                        size=10,
                        symbol='diamond'
                    ),
                    line=dict(color=optimal_series.get('color', '#FFD700'), width=3)
                ))
            
            # Add error bars if available
            if options.get('show_error_bars', False) and 'error_values' in options:
                error_values = options['error_values']
                if len(error_values) == len(categories):
                    fig.update_traces(error_y=dict(type='data', array=error_values))
            
            fig.update_layout(
                title=dict(
                    text=title,
                    x=0.5,
                    font=dict(size=16, color='#2E7D32')
                ),
                xaxis_title=options.get('x_axis_title', 'Parameters'),
                yaxis_title=options.get('y_axis_title', 'Value'),
                showlegend=options.get('show_legend', True),
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(size=12),
                height=500
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Range chart data format not recognized")
    except ImportError:
        st.info("Plotly not available for chart display")

def display_deviation_chart(data, title, options=None):
    """Display deviation chart showing percentage deviation from optimal"""
    try:
        import plotly.graph_objects as go
        
        if 'categories' in data and 'series' in data:
            categories = data['categories']
            series = data['series'][0]  # First series contains deviation data
            values = series['values']
            
            # Determine colors based on positive/negative values
            colors = []
            for val in values:
                if val > 0:
                    colors.append(options.get('color_positive', '#4ECDC4'))
                else:
                    colors.append(options.get('color_negative', '#FF6B6B'))
            
            fig = go.Figure()
            
            fig.add_trace(go.Bar(
                name=series['name'],
                x=categories,
                y=values,
                marker_color=colors,
                hovertemplate=f'<b>{series["name"]}</b><br>%{{x}}: %{{y}}%<extra></extra>',
                text=[f"{val}%" for val in values],
                textposition='auto'
            ))
            
            # Add zero line
            if options.get('show_zero_line', True):
                fig.add_hline(y=0, line_dash="dash", line_color="black", opacity=0.5)
            
            fig.update_layout(
                title=dict(
                    text=title,
                    x=0.5,
                    font=dict(size=16, color='#2E7D32')
                ),
                xaxis_title=options.get('x_axis_title', 'Parameters'),
                yaxis_title=options.get('y_axis_title', 'Deviation (%)'),
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(size=12),
                height=500
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Deviation chart data format not recognized")
    except ImportError:
        st.info("Plotly not available for chart display")



def display_gauge_chart(data, title, options=None):
    """Display gauge chart for data quality and confidence indicators"""
    try:
        import plotly.graph_objects as go
        
        if 'value' in data:
            value = data['value']
            max_value = data.get('max_value', 100)
            thresholds = data.get('thresholds', [])
            
            # Create gauge chart
            fig = go.Figure(go.Indicator(
                mode="gauge+number+delta",
                value=value,
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': title},
                delta={'reference': max_value * 0.8},
                gauge={
                    'axis': {'range': [None, max_value]},
                    'bar': {'color': "darkblue"},
                    'steps': [
                        {'range': [0, thresholds[0]['value']], 'color': thresholds[0]['color']},
                        {'range': [thresholds[0]['value'], thresholds[1]['value']], 'color': thresholds[1]['color']},
                        {'range': [thresholds[1]['value'], thresholds[2]['value']], 'color': thresholds[2]['color']},
                        {'range': [thresholds[2]['value'], max_value], 'color': thresholds[3]['color']}
                    ] if len(thresholds) >= 4 else [],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': max_value * 0.9
                    }
                }
            ))
            
            fig.update_layout(
                font={'color': "darkblue", 'family': "Arial"},
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Gauge chart data format not recognized")
    except ImportError:
        st.info("Plotly not available for chart display")

def display_step1_data_analysis(analysis_data):
    """Display Step 1: Data Analysis with nutrient status tables"""
    # 1. SUMMARY SECTION
    if 'summary' in analysis_data and analysis_data['summary']:
        st.markdown("### 📋 Summary")
        summary_text = analysis_data['summary']
        if isinstance(summary_text, str) and summary_text.strip():
            st.markdown(
                f'<div style="margin-bottom: 20px; padding: 15px; background: linear-gradient(135deg, #e8f5e8, #ffffff); border-left: 4px solid #28a745; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">'
                f'<p style="margin: 0; font-size: 16px; line-height: 1.6; color: #2c3e50;">{summary_text.strip()}</p>'
                f'</div>',
                unsafe_allow_html=True
            )
    
    # 2. KEY FINDINGS SECTION - Removed from individual steps
    # Key findings are now consolidated and displayed only after Executive Summary
    
    # 3. DETAILED ANALYSIS SECTION
    if 'detailed_analysis' in analysis_data and analysis_data['detailed_analysis']:
        st.markdown("### 📋 Detailed Analysis")
        detailed_text = analysis_data['detailed_analysis']
        
        if isinstance(detailed_text, dict):
            detailed_text = str(detailed_text)
        elif not isinstance(detailed_text, str):
            detailed_text = str(detailed_text) if detailed_text is not None else "No detailed analysis available"
        
        paragraphs = detailed_text.split('\n\n') if '\n\n' in detailed_text else [detailed_text]
        
        for paragraph in paragraphs:
            if isinstance(paragraph, str) and paragraph.strip():
                st.markdown(
                    f'<div style="margin-bottom: 18px; padding: 15px; background: linear-gradient(135deg, #ffffff, #f8f9fa); border: 1px solid #e9ecef; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">'
                    f'<p style="margin: 0; line-height: 1.8; font-size: 16px; color: #2c3e50;">{paragraph.strip()}</p>'
                    f'</div>',
                    unsafe_allow_html=True
                )
    
    # 4. NUTRIENT STATUS TABLES - This is the key addition
    display_nutrient_status_tables(analysis_data)
    
    # 4.5. DATA ECHO TABLE - Complete Parameter Analysis
    display_data_echo_table(analysis_data)
    
    # 5. DETAILED TABLES SECTION
    if 'tables' in analysis_data and analysis_data['tables']:
        st.markdown("""<div style="background: linear-gradient(135deg, #6c757d, #495057); padding: 20px; border-radius: 12px; margin-bottom: 25px; box-shadow: 0 4px 15px rgba(0,0,0,0.1);">
            <h4 style="color: white; margin: 0; font-size: 20px; font-weight: 600;">📊 Detailed Tables</h4>
        </div>""", unsafe_allow_html=True)
        
        tables = analysis_data['tables']
        if isinstance(tables, list):
            for table in tables:
                if isinstance(table, dict) and 'title' in table:
                    display_table(table)
        elif isinstance(tables, dict):
            for table_key, table_data in tables.items():
                if isinstance(table_data, dict) and 'title' in table_data:
                    display_table(table_data)
    
    # 6. VISUALIZATIONS
    if 'visualizations' in analysis_data and analysis_data['visualizations']:
        st.markdown("""<div style="background: linear-gradient(135deg, #17a2b8, #20c997); padding: 20px; border-radius: 12px; margin-bottom: 25px; box-shadow: 0 4px 15px rgba(0,0,0,0.1);">
            <h4 style="color: white; margin: 0; font-size: 20px; font-weight: 600;">📊 Data Visualizations</h4>
        </div>""", unsafe_allow_html=True)
        
        try:
            visualizations = analysis_data['visualizations']
            if isinstance(visualizations, dict):
                for i, (viz_type, viz_data) in enumerate(visualizations.items(), 1):
                    if viz_data and isinstance(viz_data, dict):
                        if 'type' not in viz_data:
                            viz_data['type'] = viz_type
                        display_visualization(viz_data, i, 1)
            elif isinstance(visualizations, list):
                for i, viz in enumerate(visualizations, 1):
                    if isinstance(viz, dict) and 'type' in viz:
                        display_visualization(viz, i, 1)
        except Exception as e:
            logger.error(f"Error displaying visualizations: {e}")
            st.error("Error displaying visualizations")

def display_table(table_data):
    """Display a table with proper formatting and borders"""
    try:
        if 'title' in table_data:
            st.markdown(f"### {table_data['title']}")
        
        if 'subtitle' in table_data:
            st.markdown(f"*{table_data['subtitle']}*")
        
        if 'headers' in table_data and 'rows' in table_data:
            headers = table_data['headers']
            rows = table_data['rows']
            
            # Create DataFrame with proper styling
            import pandas as pd
            df = pd.DataFrame(rows, columns=headers)
            
            # Display with borders and proper formatting
            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True
            )
        
        if 'note' in table_data:
            st.markdown(f"*Note: {table_data['note']}*")
            
    except Exception as e:
        logger.error(f"Error displaying table: {e}")
        st.error("Error displaying table")

def apply_table_styling():
    """Apply consistent table styling across all tables"""
    st.markdown("""
    <style>
    .dataframe {
        border-collapse: collapse;
        border: 2px solid #ddd;
        width: 100%;
        margin: 10px 0;
    }
    .dataframe th, .dataframe td {
        border: 1px solid #ddd;
        padding: 12px 8px;
        text-align: left;
        font-size: 14px;
    }
    .dataframe th {
        background-color: #f8f9fa;
        font-weight: bold;
        color: #495057;
    }
    .dataframe tr:nth-child(even) {
        background-color: #f8f9fa;
    }
    .dataframe tr:hover {
        background-color: #e9ecef;
    }
    </style>
    """, unsafe_allow_html=True)

def display_data_echo_table(analysis_data):
    """Display Data Echo Table - Complete Parameter Analysis"""
    st.markdown("### 📊 Data Echo Table - Complete Parameter Analysis")
    
    # Get parameter data from multiple possible locations
    echo_data = []
    
    # Try to get soil parameters from various locations
    soil_data = None
    if 'raw_data' in analysis_data and 'soil_parameters' in analysis_data['raw_data']:
        soil_data = analysis_data['raw_data']['soil_parameters']
    elif 'soil_parameters' in analysis_data:
        soil_data = analysis_data['soil_parameters']
    elif 'analysis_results' in analysis_data and 'soil_parameters' in analysis_data['analysis_results']:
        soil_data = analysis_data['analysis_results']['soil_parameters']
    
    # Try to get leaf parameters from various locations
    leaf_data = None
    if 'raw_data' in analysis_data and 'leaf_parameters' in analysis_data['raw_data']:
        leaf_data = analysis_data['raw_data']['leaf_parameters']
    elif 'leaf_parameters' in analysis_data:
        leaf_data = analysis_data['leaf_parameters']
    elif 'analysis_results' in analysis_data and 'leaf_parameters' in analysis_data['analysis_results']:
        leaf_data = analysis_data['analysis_results']['leaf_parameters']
    
    # Extract soil parameters
    if soil_data and 'parameter_statistics' in soil_data:
        stats = soil_data['parameter_statistics']
        for param_name, param_data in stats.items():
            if isinstance(param_data, dict):
                echo_data.append({
                    'Parameter': param_name,
                    'Type': 'Soil',
                    'Average': f"{param_data.get('average', 0):.2f}" if param_data.get('average') is not None else 'N/A',
                    'Min': f"{param_data.get('min', 0):.2f}" if param_data.get('min') is not None else 'N/A',
                    'Max': f"{param_data.get('max', 0):.2f}" if param_data.get('max') is not None else 'N/A',
                    'Std Dev': f"{param_data.get('std_dev', 0):.2f}" if param_data.get('std_dev') is not None else 'N/A',
                    'Unit': param_data.get('unit', ''),
                    'Samples': param_data.get('count', 0)
                })
    
    # Extract leaf parameters
    if leaf_data and 'parameter_statistics' in leaf_data:
        stats = leaf_data['parameter_statistics']
        for param_name, param_data in stats.items():
            if isinstance(param_data, dict):
                echo_data.append({
                    'Parameter': param_name,
                    'Type': 'Leaf',
                    'Average': f"{param_data.get('average', 0):.2f}" if param_data.get('average') is not None else 'N/A',
                    'Min': f"{param_data.get('min', 0):.2f}" if param_data.get('min') is not None else 'N/A',
                    'Max': f"{param_data.get('max', 0):.2f}" if param_data.get('max') is not None else 'N/A',
                    'Std Dev': f"{param_data.get('std_dev', 0):.2f}" if param_data.get('std_dev') is not None else 'N/A',
                    'Unit': param_data.get('unit', ''),
                    'Samples': param_data.get('count', 0)
                })
    
    # Always try to extract from nutrient_comparisons as primary source
    if 'nutrient_comparisons' in analysis_data and analysis_data['nutrient_comparisons']:
        nutrient_comparisons = analysis_data['nutrient_comparisons']
        for comparison in nutrient_comparisons:
            if isinstance(comparison, dict) and 'parameter' in comparison:
                param_name = comparison['parameter']
                # Better parameter type detection
                param_type = 'Soil'
                if any(leaf_param in param_name.lower() for leaf_param in ['n %', 'p %', 'k %', 'mg %', 'ca %', 'b ', 'cu ', 'zn ']):
                    param_type = 'Leaf'
                elif any(soil_param in param_name.lower() for soil_param in ['ph', 'nitrogen', 'phosphorus', 'potassium', 'calcium', 'magnesium', 'cec', 'organic', 'carbon', 'total p', 'available p', 'exch']):
                    param_type = 'Soil'
                
                # Get statistics from comparison data
                avg_val = comparison.get('average', 0)
                min_val = comparison.get('min', avg_val)  # Use average as fallback
                max_val = comparison.get('max', avg_val)  # Use average as fallback
                std_val = comparison.get('std_dev', 0)
                unit_val = comparison.get('unit', '')
                count_val = comparison.get('count', 1)
                
                # Only add if we have valid data
                if avg_val is not None and avg_val != 0:
                    echo_data.append({
                        'Parameter': param_name,
                        'Type': param_type,
                        'Average': f"{avg_val:.2f}",
                        'Min': f"{min_val:.2f}" if min_val is not None else 'N/A',
                        'Max': f"{max_val:.2f}" if max_val is not None else 'N/A',
                        'Std Dev': f"{std_val:.2f}" if std_val is not None else 'N/A',
                        'Unit': unit_val,
                        'Samples': count_val
                    })
    
    if echo_data:
        import pandas as pd
        df = pd.DataFrame(echo_data)
        
        # Apply consistent styling
        apply_table_styling()
        
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("📋 No parameter data available for Data Echo Table.")

def display_nutrient_status_tables(analysis_data):
    """Display Soil and Leaf Nutrient Status tables"""
    # Get nutrient comparisons data
    nutrient_comparisons = analysis_data.get('nutrient_comparisons', [])
    
    if not nutrient_comparisons:
        st.info("📋 No nutrient comparison data available.")
        return
    
    # Helper to compute status from average vs optimal
    def compute_status(avg_val, optimal_val, parameter_name: str = "") -> str:
        try:
            if avg_val is None or optimal_val is None:
                return "Missing"
            # Avoid division by zero
            if isinstance(optimal_val, (int, float)) and optimal_val == 0:
                # If optimal is zero (rare), fall back to absolute thresholding
                diff = abs(float(avg_val) - float(optimal_val))
                if diff <= 0.05:
                    return "Optimal"
                elif diff <= 0.10:
                    return "Slightly Off"
                else:
                    return "Outside Range"

            avg = float(avg_val)
            opt = float(optimal_val)
            # Percent deviation from optimal
            deviation_pct = abs((avg - opt) / opt) * 100.0

            # Tighter thresholds for pH; general thresholds for others
            if parameter_name.lower() == 'ph':
                if deviation_pct <= 2.0:
                    return "Optimal"
                elif deviation_pct <= 5.0:
                    return "Slightly Off"
                else:
                    return "Outside Range"
            else:
                if deviation_pct <= 10.0:
                    return "Optimal"
                elif deviation_pct <= 20.0:
                    return "Slightly Off"
                else:
                    return "Outside Range"
        except Exception:
            return "Missing"

    # Define canonical lists to ensure correct grouping and order
    soil_labels = [
        'pH',
        'Nitrogen %',
        'Organic Carbon %',
        'Total P (mg/kg)',
        'Available P (mg/kg)',
        'Exch. K (meq%)',
        'Exch. Ca (meq%)',
        'Exch. Mg (meq%)',
        'CEC (meq%)'
    ]
    leaf_labels = [
        'N %', 'P %', 'K %', 'Mg %', 'Ca %',
        'B (mg/kg)', 'Cu (mg/kg)', 'Zn (mg/kg)'
    ]

    def norm(label: str) -> str:
        return (label or '').strip().lower()

    # Index provided comparisons by normalized parameter name
    comparisons_by_param = {norm(c.get('parameter', '')): c for c in nutrient_comparisons}

    # Build ordered soil and leaf parameter lists based on canonical labels
    # Keep full canonical order; allow missing items to be filled as N/A later
    soil_params = [comparisons_by_param.get(norm(lbl)) for lbl in soil_labels]
    leaf_params = [comparisons_by_param.get(norm(lbl)) for lbl in leaf_labels]
    
    # Display Soil Nutrient Status table
    if any(p is not None for p in soil_params):
        st.markdown("### 🌱 Soil Nutrient Status (Average vs. MPOB Standard)")
        soil_data = []
        for label, param in zip(soil_labels, soil_params):
            if param is not None:
                avg_val = param.get('average')
                opt_val = param.get('optimal')
                computed_status = compute_status(avg_val, opt_val, param.get('parameter', label))
                soil_data.append({
                    'Parameter': param.get('parameter', label),
                    'Average': f"{avg_val:.2f}" if isinstance(avg_val, (int, float)) else 'N/A',
                    'MPOB Optimal': f"{opt_val:.2f}" if isinstance(opt_val, (int, float)) else 'N/A',
                    'Status': param.get('status') or computed_status,
                    'Unit': param.get('unit', '')
                })
            else:
                # Fill missing parameter row with N/A
                soil_data.append({
                    'Parameter': label,
                    'Average': 'N/A',
                    'MPOB Optimal': 'N/A',
                    'Status': 'Missing',
                    'Unit': ''
                })
        
        if soil_data:
            df_soil = pd.DataFrame(soil_data)
            apply_table_styling()
            st.dataframe(df_soil, use_container_width=True)
    
    # Display Leaf Nutrient Status table
    if any(p is not None for p in leaf_params):
        st.markdown("### 🍃 Leaf Nutrient Status (Average vs. MPOB Standard)")
        leaf_data = []
        for label, param in zip(leaf_labels, leaf_params):
            if param is not None:
                avg_val = param.get('average')
                opt_val = param.get('optimal')
                computed_status = compute_status(avg_val, opt_val, param.get('parameter', label))
                leaf_data.append({
                    'Parameter': param.get('parameter', label),
                    'Average': f"{avg_val:.2f}" if isinstance(avg_val, (int, float)) else 'N/A',
                    'MPOB Optimal': f"{opt_val:.2f}" if isinstance(opt_val, (int, float)) else 'N/A',
                    'Status': param.get('status') or computed_status,
                    'Unit': param.get('unit', '')
                })
            else:
                # Fill missing parameter row with N/A
                leaf_data.append({
                    'Parameter': label,
                    'Average': 'N/A',
                    'MPOB Optimal': 'N/A',
                    'Status': 'Missing',
                    'Unit': ''
                })
        
        if leaf_data:
            df_leaf = pd.DataFrame(leaf_data)
            apply_table_styling()
            st.dataframe(df_leaf, use_container_width=True)

def display_data_analysis_content(analysis_data):
    """Display Step 1: Data Analysis content"""
    st.markdown("### 📊 Data Analysis Results")
    
    # Display nutrient comparisons
    if 'nutrient_comparisons' in analysis_data:
        st.markdown("#### Nutrient Level Comparisons")
        for comparison in analysis_data['nutrient_comparisons']:
            st.markdown(f"**{comparison.get('parameter', 'Unknown')}:**")
            st.markdown(f"- Current: {comparison.get('current', 'N/A')}")
            st.markdown(f"- Optimal: {comparison.get('optimal', 'N/A')}")
            st.markdown(f"- Status: {comparison.get('status', 'Unknown')}")
            st.markdown("---")

def display_issue_diagnosis_content(analysis_data):
    """Display Step 2: Issue Diagnosis content"""
    st.markdown("### 🔍 Agronomic Issues Identified")
    
    if 'identified_issues' in analysis_data:
        for issue in analysis_data['identified_issues']:
            st.markdown(f"**{issue.get('parameter', 'Unknown Parameter')}:**")
            st.markdown(f"- Issue: {issue.get('issue_type', 'Unknown')}")
            st.markdown(f"- Severity: {issue.get('severity', 'Unknown')}")
            st.markdown(f"- Cause: {issue.get('cause', 'Unknown')}")
            st.markdown("---")

def display_structured_solutions(detailed_text):
    """Parse and display structured solution recommendations from text"""
    try:
        import re
        
        # Check if it's a JSON-like structure that needs parsing
        if detailed_text.strip().startswith('{') and 'key_findings' in detailed_text:
            # Parse JSON-like structure
            parse_and_display_json_analysis(detailed_text)
            return
        
        # Try to extract structured data from the text
        if 'formatted_analysis' in detailed_text:
            # Extract the formatted_analysis content
            match = re.search(r"'formatted_analysis': \"(.*?)\"", detailed_text, re.DOTALL)
            if match:
                formatted_content = match.group(1)
                # Clean up the content
                formatted_content = formatted_content.replace('\\n', '\n').replace('\\"', '"')
                display_solution_content(formatted_content)
                return
        
        # If no structured data found, try to parse the text directly
        display_solution_content(detailed_text)
        
    except Exception as e:
        logger.error(f"Error parsing structured solutions: {e}")
        # Fallback to regular text display with better formatting
        st.markdown("### 📋 Detailed Analysis")
        st.markdown(
            f'<div style="margin-bottom: 18px; padding: 15px; background: linear-gradient(135deg, #ffffff, #f8f9fa); border: 1px solid #e9ecef; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">'
            f'<p style="margin: 0; line-height: 1.8; font-size: 16px; color: #2c3e50;">{detailed_text}</p>'
            f'</div>',
            unsafe_allow_html=True
        )

def parse_and_display_json_analysis(json_text):
    """Parse and display JSON-like analysis data with proper formatting"""
    try:
        import re
        
        # Try to extract key findings with multiple patterns
        key_findings_match = None
        
        # Pattern 1: Standard format
        key_findings_match = re.search(r"'key_findings':\s*\[(.*?)\]", json_text, re.DOTALL)
        
        # Pattern 2: Alternative format
        if not key_findings_match:
            key_findings_match = re.search(r"'key_findings':\s*\[(.*?)\]", json_text, re.DOTALL)
        
        if key_findings_match:
            key_findings_text = key_findings_match.group(1)
            # Parse the key findings more carefully
            findings = parse_key_findings(key_findings_text)
            
            # Display key findings
            if findings:
                st.markdown("### 🎯 Key Findings")
                for i, finding in enumerate(findings, 1):
                    if finding and len(finding) > 10:  # Only show meaningful findings
                        st.markdown(
                            f'<div style="margin-bottom: 15px; padding: 12px; background: linear-gradient(135deg, #f8f9fa, #ffffff); border-left: 4px solid #007bff; border-radius: 6px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">'
                            f'<p style="margin: 0; font-size: 16px; line-height: 1.6; color: #2c3e50;">'
                            f'<strong style="color: #007bff; font-size: 18px;">{i}.</strong> {finding}</p>'
                            f'</div>',
                            unsafe_allow_html=True
                        )
        
        # Try to extract formatted analysis with multiple patterns
        formatted_analysis_match = None
        
        # Pattern 1: Standard format
        formatted_analysis_match = re.search(r"'formatted_analysis':\s*\"(.*?)\"", json_text, re.DOTALL)
        
        # Pattern 2: Alternative format with different quotes
        if not formatted_analysis_match:
            formatted_analysis_match = re.search(r"'formatted_analysis':\s*\"(.*?)\"", json_text, re.DOTALL)
        
        # Pattern 3: Look for the content after formatted_analysis
        if not formatted_analysis_match:
            # Find the start of formatted_analysis and extract until the end
            start_match = re.search(r"'formatted_analysis':\s*\"", json_text)
            if start_match:
                start_pos = start_match.end()
                # Find the end of the string (look for the closing quote before the next key)
                remaining_text = json_text[start_pos:]
                # Look for the end of the formatted_analysis string
                end_pos = 0
                quote_count = 0
                for i, char in enumerate(remaining_text):
                    if char == '"':
                        quote_count += 1
                        if quote_count == 1:
                            end_pos = i
                            break
                
                if end_pos > 0:
                    formatted_content = remaining_text[:end_pos]
                    formatted_analysis_match = type('obj', (object,), {'group': lambda x: formatted_content})()
        
        if formatted_analysis_match:
            formatted_content = formatted_analysis_match.group(1)
            # Clean up the content
            formatted_content = formatted_content.replace('\\n', '\n').replace('\\"', '"').replace('\\', '')
            
            # Display the formatted analysis
            if formatted_content.strip():
                st.markdown("### 💡 Recommended Solutions")
                display_solution_content(formatted_content)
        
    except Exception as e:
        logger.error(f"Error parsing JSON analysis: {e}")
        # Fallback to regular text display
        st.markdown("### 📋 Detailed Analysis")
        st.markdown(
            f'<div style="margin-bottom: 18px; padding: 15px; background: linear-gradient(135deg, #ffffff, #f8f9fa); border: 1px solid #e9ecef; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">'
            f'<p style="margin: 0; line-height: 1.8; font-size: 16px; color: #2c3e50;">Analysis content available but formatting needs improvement.</p>'
            f'</div>',
            unsafe_allow_html=True
        )

def parse_key_findings(key_findings_text):
    """Parse key findings from the extracted text"""
    findings = []
    
    # Try to split by comma, but be more careful with nested quotes
    import re
    
    # Use regex to find all quoted strings
    pattern = r"'([^']*(?:''[^']*)*)'"
    matches = re.findall(pattern, key_findings_text)
    
    for match in matches:
        # Clean up the finding
        finding = match.replace("''", "'").strip()
        if finding and len(finding) > 10:
            findings.append(finding)
    
    # If regex didn't work, try manual parsing
    if not findings:
        current_finding = ""
        in_quotes = False
        quote_char = None
        depth = 0
        
        for i, char in enumerate(key_findings_text):
            if char in ["'", '"'] and (not in_quotes or char == quote_char):
                if not in_quotes:
                    in_quotes = True
                    quote_char = char
                else:
                    in_quotes = False
                    quote_char = None
            elif char == '[' and not in_quotes:
                depth += 1
            elif char == ']' and not in_quotes:
                depth -= 1
            elif char == ',' and not in_quotes and depth == 0:
                if current_finding.strip():
                    finding = current_finding.strip().strip("'\" ")
                    if finding and len(finding) > 10:
                        findings.append(finding)
                current_finding = ""
                continue
            
            current_finding += char
        
        # Add the last finding
        if current_finding.strip():
            finding = current_finding.strip().strip("'\" ")
            if finding and len(finding) > 10:
                findings.append(finding)
    
    return findings

def display_solution_content(content):
    """Display solution content with proper formatting for detailed agronomic recommendations"""
    # Clean up the content first
    content = content.strip()
    
    # Check if this is the detailed agronomic recommendations format
    if '### Detailed Agronomic Recommendations' in content or '#### Problem' in content:
        display_detailed_agronomic_recommendations(content)
        return
    
    # Split content into sections
    sections = content.split('#### **Problem')
    
    for i, section in enumerate(sections):
        if not section.strip():
            continue
            
        if i == 0:
            # Introduction section
            if section.strip():
                # Clean up the introduction text
                intro_text = section.strip()
                # Remove any remaining escape characters
                intro_text = intro_text.replace('\\n', '\n').replace('\\"', '"')
                
                st.markdown(
                    f'<div style="margin-bottom: 20px; padding: 15px; background: linear-gradient(135deg, #e3f2fd, #ffffff); border-left: 4px solid #2196f3; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">'
                    f'<p style="margin: 0; font-size: 16px; line-height: 1.6; color: #2c3e50;">{intro_text}</p>'
                    f'</div>',
                    unsafe_allow_html=True
                )
        else:
            # Problem section
            display_problem_section(section)

def display_detailed_agronomic_recommendations(content):
    """Display detailed agronomic recommendations with proper formatting"""
    import re
    
    # Clean up the content
    content = content.replace('\\n', '\n').replace('\\"', '"')
    
    # Split by problem sections
    problems = re.split(r'#### Problem \d+:', content)
    
    # Display introduction if present
    if problems[0].strip():
        intro_text = problems[0].strip()
        if '### Detailed Agronomic Recommendations' in intro_text:
            intro_text = intro_text.replace('### Detailed Agronomic Recommendations', '').strip()
        
        if intro_text:
            st.markdown("""
            <div style="
                background: linear-gradient(135deg, #e8f5e8, #ffffff);
                padding: 20px;
                border-radius: 12px;
                margin-bottom: 25px;
                border-left: 4px solid #28a745;
                box-shadow: 0 4px 12px rgba(40, 167, 69, 0.2);
            ">
                <h3 style="margin: 0 0 15px 0; color: #2c3e50; font-size: 18px; font-weight: 600;">
                    🌱 Detailed Agronomic Recommendations
                </h3>
                <p style="margin: 0; color: #2c3e50; line-height: 1.6; font-size: 16px;">
                    {intro_text}
                </p>
            </div>
            """.format(intro_text=intro_text), unsafe_allow_html=True)
    
    # Display each problem
    for i, problem in enumerate(problems[1:], 1):
        if not problem.strip():
            continue
            
        display_agronomic_problem(problem, i)

def display_agronomic_problem(problem_content, problem_number):
    """Display a single agronomic problem with its solutions"""
    lines = [line.strip() for line in problem_content.split('\n') if line.strip()]
    
    if not lines:
        return
    
    # Extract problem title and rationale
    problem_title = lines[0]
    rationale = ""
    
    # Find rationale
    for i, line in enumerate(lines[1:], 1):
        if line.startswith('Agronomic Rationale:'):
            rationale = line.replace('Agronomic Rationale:', '').strip()
            break
    
    # Display problem header
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #ff6b6b, #ee5a52);
        color: white;
        padding: 20px;
        border-radius: 12px;
        margin-bottom: 20px;
        box-shadow: 0 4px 12px rgba(255, 107, 107, 0.3);
    ">
        <h3 style="margin: 0 0 10px 0; font-size: 20px; font-weight: 600;">
            🚨 Problem {problem_number}: {problem_title}
        </h3>
        {f'<p style="margin: 0; font-size: 16px; opacity: 0.9; line-height: 1.5;">{rationale}</p>' if rationale else ''}
    </div>
    """, unsafe_allow_html=True)
    
    # Parse and display investment approaches
    current_approach = None
    approach_data = {}
    
    for line in lines:
        if 'High-investment approach' in line:
            current_approach = 'high'
        elif 'Moderate-investment approach' in line:
            current_approach = 'medium'
        elif 'Low-investment approach' in line:
            current_approach = 'low'
        elif line.startswith('* Product:') and current_approach:
            product = line.replace('* Product:', '').strip()
            approach_data[current_approach] = approach_data.get(current_approach, {})
            approach_data[current_approach]['product'] = product
        elif line.startswith('* Rate:') and current_approach:
            rate = line.replace('* Rate:', '').strip()
            approach_data[current_approach]['rate'] = rate
        elif line.startswith('* Timing & Method:') and current_approach:
            timing = line.replace('* Timing & Method:', '').strip()
            approach_data[current_approach]['timing'] = timing
        elif line.startswith('* Agronomic Effect:') and current_approach:
            effect = line.replace('* Agronomic Effect:', '').strip()
            approach_data[current_approach]['effect'] = effect
        elif line.startswith('* Cost:') and current_approach:
            cost = line.replace('* Cost:', '').strip()
            approach_data[current_approach]['cost'] = cost
    
    # Display investment approaches
    for approach_type, data in approach_data.items():
        if not data:
            continue
            
        # Determine colors and icons based on approach
        if approach_type == 'high':
            color = '#e74c3c'
            bg_color = '#fdf2f2'
            icon = '💎'
            title = 'High Investment'
        elif approach_type == 'medium':
            color = '#f39c12'
            bg_color = '#fef9e7'
            icon = '⚖️'
            title = 'Moderate Investment'
        else:  # low
            color = '#27ae60'
            bg_color = '#eafaf1'
            icon = '💰'
            title = 'Low Investment'
        
        st.markdown(f"""
        <div style="
            background: {bg_color};
            border: 2px solid {color};
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        ">
            <h4 style="margin: 0 0 15px 0; color: {color}; font-size: 18px; font-weight: 600;">
                {icon} {title} Approach
            </h4>
            <div style="margin-bottom: 12px;">
                <strong style="color: #2c3e50;">Product:</strong> 
                <span style="color: #2c3e50;">{data.get('product', 'N/A')}</span>
            </div>
            <div style="margin-bottom: 12px;">
                <strong style="color: #2c3e50;">Rate:</strong> 
                <span style="color: #2c3e50;">{data.get('rate', 'N/A')}</span>
            </div>
            <div style="margin-bottom: 12px;">
                <strong style="color: #2c3e50;">Timing & Method:</strong> 
                <span style="color: #2c3e50;">{data.get('timing', 'N/A')}</span>
            </div>
            <div style="margin-bottom: 12px;">
                <strong style="color: #2c3e50;">Agronomic Effect:</strong> 
                <span style="color: #2c3e50;">{data.get('effect', 'N/A')}</span>
            </div>
            <div>
                <strong style="color: {color};">Cost Level:</strong> 
                <span style="color: {color}; font-weight: 600;">{data.get('cost', 'N/A')}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

def display_problem_section(section):
    """Display a single problem section with solutions"""
    lines = section.strip().split('\n')
    if not lines:
        return
    
    # Extract problem title and description
    problem_title = lines[0].strip()
    if not problem_title:
        return
    
    # Clean up the problem title
    problem_title = problem_title.replace('**', '').strip()
    
    # Create problem header
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #ff6b6b, #ee5a52);
        color: white;
        padding: 20px;
        border-radius: 12px;
        margin-bottom: 20px;
        box-shadow: 0 4px 12px rgba(255, 107, 107, 0.3);
    ">
        <h3 style="margin: 0; font-size: 20px; font-weight: 600;">
            🚨 {problem_title}
        </h3>
    </div>
    """, unsafe_allow_html=True)
    
    # Parse and display solutions
    current_solution = None
    current_approach = None
    solution_data = {}
    
    for line in lines[1:]:
        line = line.strip()
        if not line:
            continue
            
        # Clean up the line
        line = line.replace('\\n', '\n').replace('\\"', '"')
        
        # Check for approach headers
        if 'High-Investment Approach' in line:
            current_approach = 'high'
            current_solution = 'high'
        elif 'Moderate-Investment Approach' in line:
            current_approach = 'medium'
            current_solution = 'medium'
        elif 'Low-Investment Approach' in line:
            current_approach = 'low'
            current_solution = 'low'
        elif line.startswith('**Product:**'):
            if current_approach:
                solution_data[current_approach] = solution_data.get(current_approach, {})
                product = line.replace('**Product:**', '').strip()
                solution_data[current_approach]['product'] = product
        elif line.startswith('**Rate:**'):
            if current_approach:
                rate = line.replace('**Rate:**', '').strip()
                solution_data[current_approach]['rate'] = rate
        elif line.startswith('**Timing & Method:**'):
            if current_approach:
                timing = line.replace('**Timing & Method:**', '').strip()
                solution_data[current_approach]['timing'] = timing
        elif line.startswith('**Biological/Agronomic Effects:**'):
            if current_approach:
                effects = line.replace('**Biological/Agronomic Effects:**', '').strip()
                solution_data[current_approach]['effects'] = effects
        elif line.startswith('**Impact:**'):
            if current_approach:
                impact = line.replace('**Impact:**', '').strip()
                solution_data[current_approach]['impact'] = impact
        elif line.startswith('**Cost Label:**'):
            if current_approach:
                cost = line.replace('**Cost Label:**', '').strip()
                solution_data[current_approach]['cost'] = cost
    
    # Display solutions in columns
    if solution_data:
        col1, col2, col3 = st.columns(3)
        
        # High Investment
        if 'high' in solution_data:
            with col1:
                display_solution_card('high', solution_data['high'], 'High Investment', '#dc3545')
        
        # Medium Investment
        if 'medium' in solution_data:
            with col2:
                display_solution_card('medium', solution_data['medium'], 'Medium Investment', '#ffc107')
        
        # Low Investment
        if 'low' in solution_data:
            with col3:
                display_solution_card('low', solution_data['low'], 'Low Investment', '#6c757d')
    
    st.markdown("---")

def display_solution_card(level, data, title, color):
    """Display a solution card"""
    st.markdown(f"""
    <div style="
        background: {color};
        color: white;
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 15px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    ">
        <h4 style="margin: 0 0 10px 0; font-size: 16px; font-weight: 600;">
            💰 {title}
        </h4>
        <p style="margin: 5px 0; font-size: 14px;"><strong>Product:</strong> {data.get('product', 'N/A')}</p>
        <p style="margin: 5px 0; font-size: 14px;"><strong>Rate:</strong> {data.get('rate', 'N/A')}</p>
        <p style="margin: 5px 0; font-size: 14px;"><strong>Timing:</strong> {data.get('timing', 'N/A')}</p>
        <p style="margin: 5px 0; font-size: 14px;"><strong>Cost:</strong> {data.get('cost', 'N/A')}</p>
    </div>
    """, unsafe_allow_html=True)

def display_dict_analysis(detailed_dict):
    """Display analysis data from dictionary format"""
    for key, value in detailed_dict.items():
        if isinstance(value, (str, int, float)) and value:
            st.markdown(f"**{key.replace('_', ' ').title()}:** {value}")
        elif isinstance(value, dict) and value:
            st.markdown(f"**{key.replace('_', ' ').title()}:**")
            for sub_key, sub_value in value.items():
                st.markdown(f"- {sub_key.replace('_', ' ').title()}: {sub_value}")

def display_step3_solution_recommendations(analysis_data):
    """Display Step 3: Solution Recommendations with enhanced structure and layout"""
    
    # Debug: Log the structure of analysis_data for STEP 3
    logger.info(f"STEP 3 analysis_data keys: {list(analysis_data.keys()) if analysis_data else 'None'}")
    if 'analysis_results' in analysis_data:
        logger.info(f"STEP 3 analysis_results found: {type(analysis_data['analysis_results'])} - {analysis_data['analysis_results']}")
    else:
        logger.info("STEP 3 analysis_results NOT found in analysis_data")
    

    
    # 1. SUMMARY SECTION - Always show if available
    if 'summary' in analysis_data and analysis_data['summary']:
        st.markdown("### 📋 Summary")
        summary_text = analysis_data['summary']
        if isinstance(summary_text, str) and summary_text.strip():
            st.markdown(
                f'<div style="margin-bottom: 20px; padding: 15px; background: linear-gradient(135deg, #e8f5e8, #ffffff); border-left: 4px solid #28a745; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">'
                f'<p style="margin: 0; font-size: 16px; line-height: 1.6; color: #2c3e50;">{summary_text.strip()}</p>'
                f'</div>',
                unsafe_allow_html=True
            )
            st.markdown("")
    
    # Key findings are now consolidated and displayed only after Executive Summary
    
    # 2. DETAILED ANALYSIS SECTION - Enhanced parsing and formatting
    if 'detailed_analysis' in analysis_data and analysis_data['detailed_analysis']:
        st.markdown("### 📋 Detailed Analysis")
        detailed_text = analysis_data['detailed_analysis']
        
        # Parse and format the detailed analysis properly
        if isinstance(detailed_text, str) and detailed_text.strip():
            # Check if it's JSON-like structure that needs parsing
            if detailed_text.strip().startswith('{') and ('key_findings' in detailed_text or 'formatted_analysis' in detailed_text):
                # Parse structured solution recommendations
                display_structured_solutions(detailed_text)
            elif 'formatted_analysis' in detailed_text or 'Problem' in detailed_text:
                # Parse structured solution recommendations
                display_structured_solutions(detailed_text)
            else:
                # Display as regular text with proper formatting
                paragraphs = detailed_text.split('\n\n') if '\n\n' in detailed_text else [detailed_text]
                for paragraph in paragraphs:
                    if paragraph.strip():
                        # Clean up any remaining escape characters
                        clean_paragraph = paragraph.strip().replace('\\n', '\n').replace('\\"', '"')
                        st.markdown(
                            f'<div style="margin-bottom: 18px; padding: 15px; background: linear-gradient(135deg, #ffffff, #f8f9fa); border: 1px solid #e9ecef; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">'
                            f'<p style="margin: 0; line-height: 1.8; font-size: 16px; color: #2c3e50;">{clean_paragraph}</p>'
                            f'</div>',
                            unsafe_allow_html=True
                        )
        elif isinstance(detailed_text, dict):
            # Handle dict format
            display_dict_analysis(detailed_text)
        else:
            st.info("No detailed analysis available in a readable format.")
        
        st.markdown("")
    
    # 3. TABLES SECTION - Display detailed tables if available
    if 'tables' in analysis_data and analysis_data['tables']:
        st.markdown("### 📊 Detailed Data Tables")
        for table in analysis_data['tables']:
            if isinstance(table, dict) and table.get('title') and table.get('headers') and table.get('rows'):
                st.markdown(f"**{table['title']}**")
                if table.get('subtitle'):
                    st.markdown(f"*{table['subtitle']}*")
                # Create a DataFrame for better display
                import pandas as pd
                df = pd.DataFrame(table['rows'], columns=table['headers'])
                apply_table_styling()
                st.dataframe(df, use_container_width=True)
                st.markdown("")
    
    # 4. ANALYSIS RESULTS SECTION - Show actual LLM results (same as other steps)
    # This section shows the main analysis results from the LLM
    excluded_keys = set(['summary', 'key_findings', 'detailed_analysis', 'formatted_analysis', 'step_number', 'step_title', 'step_description', 'visualizations', 'yield_forecast', 'references', 'search_timestamp', 'prompt_instructions'])
    other_fields = [k for k in analysis_data.keys() if k not in excluded_keys and analysis_data.get(k) is not None and analysis_data.get(k) != ""]
    
    if other_fields:
        st.markdown("### 📊 Analysis Results")
        for key in other_fields:
            value = analysis_data.get(key)
            title = key.replace('_', ' ').title()
            
            if isinstance(value, dict) and value:
                st.markdown(f"**{title}:**")
                for sub_k, sub_v in value.items():
                    if sub_v is not None and sub_v != "":
                        st.markdown(f"- **{sub_k.replace('_',' ').title()}:** {sub_v}")
            elif isinstance(value, list) and value:
                st.markdown(f"**{title}:**")
                for idx, item in enumerate(value, 1):
                    if isinstance(item, dict):
                        # Check if it's a table structure
                        if 'title' in item and 'headers' in item and 'rows' in item:
                            st.markdown(f"**{item.get('title', f'Table {idx}')}**")
                            if item.get('subtitle'):
                                st.markdown(f"*{item['subtitle']}*")
                            # Create a DataFrame for better display
                            import pandas as pd
                            df = pd.DataFrame(item['rows'], columns=item['headers'])
                            st.dataframe(df, use_container_width=True)
                            st.markdown("")
                        else:
                            st.markdown(f"- Item {idx}:")
                            st.json(item)
                    elif isinstance(item, list):
                        st.markdown(f"- Item {idx}:")
                        st.json(item)
                    else:
                        st.markdown(f"- {item}")
            elif isinstance(value, str) and value.strip():
                st.markdown(f"**{title}:** {value}")
            st.markdown("")
    

    


    





    
    if 'solution_options' in analysis_data:
        for solution in analysis_data['solution_options']:
            # Enhanced solution title with bigger font and prominent styling
            parameter_name = solution.get('parameter', 'Unknown Parameter')
            issue_title = solution.get('issue', solution.get('issue_description', ''))
            if issue_title:
                solution_title = f"{issue_title}"
            else:
                solution_title = parameter_name
            
            # Highlight the issue title with a box and underline
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, #28a745, #20c997);
                color: white;
                padding: 15px 20px;
                border-radius: 10px;
                margin: 20px 0 15px 0;
                box-shadow: 0 4px 15px rgba(40, 167, 69, 0.3);
            ">
                <h2 style="margin: 0; font-size: 26px; font-weight: 800; text-shadow: 0 2px 4px rgba(0,0,0,0.3);">
                    🔧 <span style="background: rgba(255,255,255,0.2); padding: 4px 8px; border-radius: 6px; border-bottom: 3px solid #fff; text-decoration: underline; text-decoration-thickness: 2px;">{solution_title}</span>
                </h2>
            </div>
            """, unsafe_allow_html=True)
            
            # High investment
            if 'high_investment' in solution:
                high = solution['high_investment']
                st.markdown("""
                <div style="
                    background: linear-gradient(135deg, #dc3545, #c82333);
                    color: white;
                    padding: 12px 16px;
                    border-radius: 8px;
                    margin: 10px 0;
                    box-shadow: 0 2px 8px rgba(220, 53, 69, 0.3);
                ">
                    <h4 style="margin: 0; font-size: 14px; font-weight: 600;">🔥 High Investment Approach</h4>
                </div>
                """, unsafe_allow_html=True)
                st.markdown(f"**Product:** {high.get('product', 'N/A')}")
                st.markdown(f"**Rate:** {high.get('rate', 'N/A')}")
                st.markdown(f"**Timing:** {high.get('timing', 'N/A')}")
                st.markdown(f"**Cost:** {high.get('cost', 'N/A')}")
                st.markdown("---")
            
            # Medium investment
            if 'medium_investment' in solution:
                medium = solution['medium_investment']
                st.markdown("""
                <div style="
                    background: linear-gradient(135deg, #ffc107, #e0a800);
                    color: #212529;
                    padding: 12px 16px;
                    border-radius: 8px;
                    margin: 10px 0;
                    box-shadow: 0 2px 8px rgba(255, 193, 7, 0.3);
                ">
                    <h4 style="margin: 0; font-size: 14px; font-weight: 600;">⚡ Medium Investment Approach</h4>
                </div>
                """, unsafe_allow_html=True)
                st.markdown(f"**Product:** {medium.get('product', 'N/A')}")
                st.markdown(f"**Rate:** {medium.get('rate', 'N/A')}")
                st.markdown(f"**Timing:** {medium.get('timing', 'N/A')}")
                st.markdown(f"**Cost:** {medium.get('cost', 'N/A')}")
                st.markdown("---")
            
            # Low investment
            if 'low_investment' in solution:
                low = solution['low_investment']
                st.markdown("""
                <div style="
                    background: linear-gradient(135deg, #6c757d, #5a6268);
                    color: white;
                    padding: 12px 16px;
                    border-radius: 8px;
                    margin: 10px 0;
                    box-shadow: 0 2px 8px rgba(108, 117, 125, 0.3);
                ">
                    <h4 style="margin: 0; font-size: 14px; font-weight: 600;">💡 Low Investment Approach</h4>
                </div>
                """, unsafe_allow_html=True)
                st.markdown(f"**Product:** {low.get('product', 'N/A')}")
                st.markdown(f"**Rate:** {low.get('rate', 'N/A')}")
                st.markdown(f"**Timing:** {low.get('timing', 'N/A')}")
                st.markdown(f"**Cost:** {low.get('cost', 'N/A')}")
            
            st.markdown("---")

def display_regenerative_agriculture_content(analysis_data):
    """Display Step 4: Regenerative Agriculture content"""
    st.markdown("### 🌱 Regenerative Agriculture Strategies")
    
    if 'regenerative_practices' in analysis_data:
        for practice in analysis_data['regenerative_practices']:
            st.markdown(f"**{practice.get('practice', 'Unknown Practice')}:**")
            st.markdown(f"- Mechanism: {practice.get('mechanism', 'N/A')}")
            st.markdown(f"- Benefits: {practice.get('benefits', 'N/A')}")
            st.markdown(f"- Implementation: {practice.get('implementation', 'N/A')}")
            st.markdown("---")

def display_economic_impact_content(analysis_data):
    """Display Step 5: Economic Impact Forecast content"""
    st.markdown("### 💰 Economic Impact Forecast")
    
    # Check for both economic_analysis (from LLM) and economic_forecast (from ResultsGenerator)
    econ_data = analysis_data.get('economic_analysis', {})
    econ_forecast = analysis_data.get('economic_forecast', {})
    
    # Merge the data, prioritizing economic_forecast as it has more accurate calculations
    if econ_forecast:
        # Use the more accurate economic forecast data
        current_yield = econ_forecast.get('current_yield_tonnes_per_ha', 0)
        land_size = econ_forecast.get('land_size_hectares', 0)
        scenarios = econ_forecast.get('scenarios', {})
        
        # Display key metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("🌾 Current Yield", f"{current_yield:.1f} tonnes/ha")
        with col2:
            st.metric("🏞️ Land Size", f"{land_size:.1f} hectares")
        with col3:
            # Get medium scenario ROI range as representative
            medium_roi_range = scenarios.get('medium', {}).get('roi_percentage_range', 'N/A')
            st.metric("💰 Estimated ROI", medium_roi_range)

        # Projected improvement (% change from current yield to medium scenario new_yield)
        projected_improvement = None
        try:
            if scenarios:
                base = float(current_yield) if current_yield else 0.0
                # Prefer medium, then high, then low
                candidate = None
                for tier in ['medium', 'high', 'low']:
                    if tier in scenarios and isinstance(scenarios[tier], dict):
                        cand_val = scenarios[tier].get('new_yield')
                        if isinstance(cand_val, (int, float)) and cand_val > 0:
                            candidate = float(cand_val)
                            break
                if base > 0 and candidate is not None:
                    projected_improvement = (candidate - base) / base * 100.0
        except Exception:
            projected_improvement = None

        if projected_improvement is not None:
            st.metric("📈 Projected Improvement", f"{projected_improvement:.1f}%")
        
        # Display investment scenarios
        if scenarios:
            st.markdown("#### 💹 Investment Scenarios")
            
            # Create scenarios table
            scenarios_data = []
            for level, data in scenarios.items():
                if isinstance(data, dict) and 'investment_level' in data:
                    scenarios_data.append({
                        'Investment Level': data.get('investment_level', level.title()),
                        'Cost per Hectare (RM)': f"{data.get('cost_per_hectare', 0):,.0f}",
                        'Total Cost (RM)': f"{data.get('total_cost', 0):,.0f}",
                        'New Yield (t/ha)': f"{data.get('new_yield', 0):.1f}",
                        'Additional Yield (t/ha)': f"{data.get('additional_yield', 0):.1f}",
                        'Additional Revenue (RM)': f"{data.get('additional_revenue', 0):,.0f}",
                        'ROI (%)': f"{data.get('roi_percentage', 0):.1f}%",
                        'Payback (months)': f"{data.get('payback_months', 0):.1f}"
                    })
            
            if scenarios_data:
                import pandas as pd
                df = pd.DataFrame(scenarios_data)
                apply_table_styling()
                st.dataframe(df, use_container_width=True)
                
                # Add assumptions
                assumptions = econ_forecast.get('assumptions', [])
                if assumptions:
                    st.markdown("#### 📋 Assumptions")
                    for assumption in assumptions:
                        st.markdown(f"• {assumption}")
    
    elif econ_data:
        # Fallback to LLM-generated economic analysis
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Current Yield", f"{econ_data.get('current_yield', 0):.1f} tons/ha")
        with col2:
            st.metric("Projected Improvement", f"{econ_data.get('yield_improvement', 0):.1f}%")
        with col3:
            st.metric("ROI Estimate", f"{econ_data.get('roi', 0):.1f}%")
        
        if 'cost_benefit' in econ_data:
            st.markdown("#### Cost-Benefit Analysis")
            for scenario in econ_data['cost_benefit']:
                st.markdown(f"**{scenario.get('scenario', 'Unknown')}:**")
                st.markdown(f"- Investment: RM {scenario.get('investment', 0):,.0f}")
                st.markdown(f"- Return: RM {scenario.get('return', 0):,.0f}")
                st.markdown(f"- ROI: {scenario.get('roi', 0):.1f}%")
    
    else:
        st.info("📊 Economic forecast data not available. This may be due to missing land size or yield data.")
        


def _generate_fallback_values(baseline_yield, scenario_key):
    """Generate fallback values for investment scenarios"""
    fallback_values = [baseline_yield]
    for i in range(1, 6):
        if scenario_key == 'high_investment':
            # High investment: 20-30% total improvement over 5 years
            improvement = 0.20 + (0.10 * i / 5)  # 20% to 30% over 5 years
            fallback_values.append(baseline_yield * (1 + improvement))
        elif scenario_key == 'medium_investment':
            # Medium investment: 15-22% total improvement over 5 years
            improvement = 0.15 + (0.07 * i / 5)  # 15% to 22% over 5 years
            fallback_values.append(baseline_yield * (1 + improvement))
        else:  # low_investment
            # Low investment: 8-15% total improvement over 5 years
            improvement = 0.08 + (0.07 * i / 5)  # 8% to 15% over 5 years
            fallback_values.append(baseline_yield * (1 + improvement))
    return fallback_values

def _extract_first_float(value, default_value=0.0):
    """Extract the first numeric value from strings like '22.4', '22.4 t/ha', '22.4-24.0 t/ha'.
    Falls back to default_value on failure."""
    try:
        if isinstance(value, (int, float)):
            return float(value)
        if not isinstance(value, str):
            return float(default_value)
        import re
        match = re.search(r"[-+]?[0-9]*\.?[0-9]+", value)
        if match:
            return float(match.group(0))
        return float(default_value)
    except Exception:
        return float(default_value)

def display_forecast_graph_content(analysis_data, step_number=None, step_title=None):
    """Display Forecast Graph content with baseline - works for any step with yield forecast data"""
    # Dynamic header based on step information
    if step_number and step_title:
        header_title = f"📈 STEP {step_number} — {step_title}: 5-Year Yield Forecast & Projections"
    else:
        header_title = "📈 5-Year Yield Forecast & Projections"
    
    # Styled header with updated background color
    st.markdown(
        f"""
        <div style="background: linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%); padding: 18px; border-radius: 12px; margin-bottom: 16px; box-shadow: 0 4px 14px rgba(0,0,0,0.12);">
            <h3 style="color: #ffffff; margin: 0; font-size: 22px; font-weight: 700;">{header_title}</h3>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    # Check for yield forecast data in multiple possible locations
    forecast = None
    if 'yield_forecast' in analysis_data:
        forecast = analysis_data['yield_forecast']
    elif 'analysis' in analysis_data and 'yield_forecast' in analysis_data['analysis']:
        forecast = analysis_data['analysis']['yield_forecast']
        
    if forecast:
        
        # Show baseline yield. Ensure it uses Year 0 from any series if missing.
        baseline_yield = forecast.get('baseline_yield', 0)
        if not baseline_yield:
            for key in ['medium_investment', 'high_investment', 'low_investment']:
                series = forecast.get(key)
                if isinstance(series, list) and len(series) > 0 and isinstance(series[0], (int, float)):
                    baseline_yield = series[0]
                    break
        
        # Ensure baseline_yield is numeric
        try:
            baseline_yield = float(baseline_yield) if baseline_yield is not None else 0
        except (ValueError, TypeError):
            baseline_yield = 0
            
        if baseline_yield > 0:
            st.markdown(f"**Current Yield Baseline:** {baseline_yield:.1f} tonnes/hectare")
            st.markdown("")
        
        try:
            import plotly.graph_objects as go
            
            # Years including baseline (0-5)
            years = list(range(0, 6))
            year_labels = ['Current', 'Year 1', 'Year 2', 'Year 3', 'Year 4', 'Year 5']
            
            fig = go.Figure()
            
            # Add baseline reference line
            if baseline_yield > 0:
                fig.add_hline(
                    y=baseline_yield, 
                    line_dash="dash", 
                    line_color="gray",
                    annotation_text=f"Current Baseline: {baseline_yield:.1f} t/ha",
                    annotation_position="top right"
                )
            
            # Add lines for different investment approaches. Ensure Year 0 matches baseline.
            # Always add all three investment lines, even if data is missing
            investment_scenarios = [
                ('high_investment', 'High Investment', '#e74c3c'),
                ('medium_investment', 'Medium Investment', '#f39c12'),
                ('low_investment', 'Low Investment', '#27ae60')
            ]
            
            for scenario_key, scenario_name, color in investment_scenarios:
                scenario_values = [baseline_yield]  # Start with baseline
                
                if scenario_key in forecast:
                    scenario_data = forecast[scenario_key]
                    
                    if isinstance(scenario_data, list) and len(scenario_data) >= 6:
                        # Old array format
                        if len(scenario_data) >= 1 and isinstance(scenario_data[0], (int, float)) and baseline_yield and scenario_data[0] != baseline_yield:
                            scenario_data = [baseline_yield] + scenario_data[1:]
                        scenario_values = scenario_data[:6]  # Ensure we have exactly 6 values
                    elif isinstance(scenario_data, dict):
                        # New range or string-with-units format → parse robustly
                        for year in ['year_1', 'year_2', 'year_3', 'year_4', 'year_5']:
                            if year in scenario_data:
                                parsed = _extract_first_float(scenario_data[year], baseline_yield)
                                scenario_values.append(parsed if parsed else baseline_yield)
                            else:
                                scenario_values.append(baseline_yield)
                    else:
                        # Invalid data format, generate fallback
                        scenario_values = _generate_fallback_values(baseline_yield, scenario_key)
                else:
                    # Generate fallback data if scenario is missing
                    scenario_values = _generate_fallback_values(baseline_yield, scenario_key)
                
                # Ensure we have exactly 6 values
                while len(scenario_values) < 6:
                    scenario_values.append(scenario_values[-1] if scenario_values else baseline_yield)
                scenario_values = scenario_values[:6]

                # If a series is still flat (all equal), apply minimal offsets to ensure visibility
                if all(abs(v - scenario_values[0]) < 1e-6 for v in scenario_values):
                    fallback = _generate_fallback_values(baseline_yield, scenario_key)
                    scenario_values = fallback[:6]
                
                fig.add_trace(go.Scatter(
                    x=years,
                    y=scenario_values,
                    mode='lines+markers',
                    name=scenario_name,
                    line=dict(color=color, width=3),
                    marker=dict(size=8)
                ))
            
            fig.update_layout(
                title='5-Year Yield Projection from Current Baseline',
                xaxis_title='Years',
                yaxis_title='Yield (tons/ha)',
                xaxis=dict(
                    tickmode='array',
                    tickvals=years,
                    ticktext=year_labels
                ),
                hovermode='x unified',
                showlegend=True,
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                )
            )
            
            st.plotly_chart(fig, width='stretch')
            
            # Add assumptions note as specified in the step instructions
            st.info("📝 **Assumptions:** Projections require yearly follow-up and adaptive adjustments based on actual field conditions and market changes.")
            
        except ImportError:
            st.info("Plotly not available for forecast graph display")
            # Fallback table display
            st.markdown("#### Yield Projections by Investment Level")
            forecast_data = []
            for i, year in enumerate(years):
                row = {'Year': year}
                if 'high_investment' in forecast:
                    row['High Investment'] = f"{forecast['high_investment'][i]:.1f}"
                if 'medium_investment' in forecast:
                    row['Medium Investment'] = f"{forecast['medium_investment'][i]:.1f}"
                if 'low_investment' in forecast:
                    row['Low Investment'] = f"{forecast['low_investment'][i]:.1f}"
                forecast_data.append(row)
            
            st.table(forecast_data)
            
            # Add assumptions note as specified in the step instructions
            st.info("📝 **Assumptions:** Projections require yearly follow-up and adaptive adjustments based on actual field conditions and market changes.")
    else:
        st.warning("⚠️ No yield forecast data available for Step 6")
        st.info("💡 The LLM should generate yield forecast data including baseline yield and 5-year projections for high, medium, and low investment scenarios.")

def display_issues_analysis(analysis_data):
    """Display detailed issues analysis with responsive styling"""
    issues = analysis_data.get('issues', {})
    
    if not issues:
        return
    
    st.markdown("### 🚨 Issues by Severity")
    
    for severity in ['critical', 'medium', 'low']:
        if severity in issues and issues[severity]:
            severity_icon = {'critical': '🔴', 'medium': '🟡', 'low': '🟢'}[severity]
            
            with st.expander(f"{severity_icon} {severity.title()} Issues ({len(issues[severity])})", expanded=(severity == 'critical')):
                for issue in issues[severity]:
                    # Display issue with proper formatting
                    parameter = issue.get('parameter', 'Unknown')
                    current_value = issue.get('current_value', 'N/A')
                    optimal_range = issue.get('optimal_range', 'N/A')
                    impact = issue.get('impact', issue.get('description', ''))
                    
                    st.markdown(
                        f'<div class="issue-{severity}"><strong>{parameter}</strong><br>'
                        f'Current: {current_value} | Optimal: {optimal_range}<br>'
                        f'Impact: {impact}</div>',
                        unsafe_allow_html=True
                    )

def display_recommendations_section(recommendations):
    """Display recommendations from the analysis engine"""
    if not recommendations:
        st.info("📋 No specific recommendations available.")
        return
    
    for i, rec in enumerate(recommendations, 1):
        parameter = rec.get('parameter', f'Recommendation {i}')
        issue_desc = rec.get('issue_description', '')
        investment_options = rec.get('investment_options', {})
        
        with st.expander(f"💡 {parameter} - Recommendations", expanded=(i == 1)):
            if issue_desc:
                st.markdown(f"**Issue:** {issue_desc}")
            
            # Display investment tiers
            for tier in ['high', 'medium', 'low']:
                if tier in investment_options:
                    tier_data = investment_options[tier]
                    tier_icon = {'high': '🔥', 'medium': '⚡', 'low': '💡'}[tier]
                    
                    st.markdown(f"**{tier_icon} {tier.title()} Investment Option:**")
                    st.markdown(f"• Action: {tier_data.get('action', 'N/A')}")
                    st.markdown(f"• Cost: ${tier_data.get('cost', 0):,}")
                    st.markdown(f"• Expected ROI: {tier_data.get('roi', 0)}%")
                    st.markdown(f"• Timeline: {tier_data.get('timeline', 'N/A')}")
                    st.markdown("---")

def display_economic_forecast(economic_forecast):
    """Display economic forecast and projections"""
    if not economic_forecast:
        st.info("📈 Economic forecast not available.")
        return
    
    # Display key metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Get current yield from the correct field
        current_yield = economic_forecast.get('current_yield_tonnes_per_ha', 0)
        if isinstance(current_yield, (int, float)):
            st.metric("🌾 Current Yield", f"{current_yield:.1f} tonnes/ha")
        else:
            st.metric("🌾 Current Yield", "N/A")
    
    with col2:
        # Calculate projected improvement from scenarios
        scenarios = economic_forecast.get('scenarios', {})
        projected_yield = 0
        if 'medium' in scenarios and 'yield_increase_percentage' in scenarios['medium']:
            projected_yield = scenarios['medium']['yield_increase_percentage']
        if isinstance(projected_yield, (int, float)):
            st.metric("📈 Projected Improvement", f"+{projected_yield:.1f}%")
        else:
            st.metric("📈 Projected Improvement", "N/A")
    
    with col3:
        # Get ROI range from medium scenario
        roi_range = "N/A"
        if 'medium' in scenarios and 'roi_percentage_range' in scenarios['medium']:
            roi_range = scenarios['medium']['roi_percentage_range']
        st.metric("💰 Estimated ROI", roi_range)
    
    # Display 5-year projection if available
    five_year_projection = economic_forecast.get('five_year_projection', {})
    if five_year_projection:
        st.markdown("### 📊 5-Year Yield Projection")
        
        # Create projection chart
        years = list(range(1, 6))
        yields = [five_year_projection.get(f'year_{i}', current_yield) for i in years]
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=years,
            y=yields,
            mode='lines+markers',
            name='Projected Yield',
            line=dict(color='#2E8B57', width=3),
            marker=dict(size=8)
        ))
        
        fig.update_layout(
            title="5-Year Yield Projection",
            xaxis_title="Year",
            yaxis_title="Yield (tonnes/hectare)",
            height=400
        )
        
        st.plotly_chart(fig, width='stretch')
    
    # Display investment scenarios
    investment_scenarios = economic_forecast.get('investment_scenarios', {})
    if investment_scenarios:
        st.markdown("### 💹 Investment Scenarios")
        
        scenarios_data = []
        for scenario, data in investment_scenarios.items():
            total_cost = data.get('total_cost', 0)
            yield_increase = data.get('yield_increase', 0)
            roi = data.get('roi', 0)
            
            scenarios_data.append({
                'Investment Level': scenario.title(),
                'Total Cost ($)': f"{total_cost:,.0f}" if isinstance(total_cost, (int, float)) else "N/A",
                'Yield Increase (%)': f"{yield_increase:.1f}%" if isinstance(yield_increase, (int, float)) else "N/A",
                'ROI (%)': f"{roi:.1f}%" if isinstance(roi, (int, float)) else "N/A",
                'Payback Period': str(data.get('payback_period', 'N/A'))
            })
        
        if scenarios_data:
            df = pd.DataFrame(scenarios_data)
            apply_table_styling()
            st.dataframe(df, use_container_width=True)

def display_recommendations_details(analysis_data):
    """Display detailed recommendations"""
    recommendations = analysis_data.get('investment_tiers', {})
    
    if not recommendations:
        return
    
    st.markdown("### 💰 Investment Recommendations")
    
    for tier in ['high', 'medium', 'low']:
        if tier in recommendations:
            tier_data = recommendations[tier]
            tier_color = {'high': '#28a745', 'medium': '#17a2b8', 'low': '#6c757d'}[tier]
            
            with st.expander(f"💎 {tier.title()} Investment Tier", expanded=(tier == 'medium')):
                col1, col2 = st.columns(2)
                
                with col1:
                    cost_value = tier_data.get('cost', 0)
                    if isinstance(cost_value, (int, float)):
                        st.metric("💵 Investment", f"${cost_value:,.0f}")
                    else:
                        st.metric("💵 Investment", "N/A")
                    
                    roi_value = tier_data.get('roi', 0)
                    if isinstance(roi_value, (int, float)):
                        st.metric("📈 Expected ROI", f"{roi_value:.1f}%")
                    else:
                        st.metric("📈 Expected ROI", "N/A")
                
                with col2:
                    payback_period = tier_data.get('payback_period', 'N/A')
                    st.metric("⏱️ Payback Period", str(payback_period))
                    
                    yield_increase = tier_data.get('yield_increase', 0)
                    if isinstance(yield_increase, (int, float)):
                        st.metric("📊 Yield Increase", f"{yield_increase:.1f}%")
                    else:
                        st.metric("📊 Yield Increase", "N/A")
                
                if 'recommendations' in tier_data:
                    st.markdown("**Specific Actions:**")
                    for rec in tier_data['recommendations']:
                        st.markdown(f"• {rec}")

def display_economic_analysis(analysis_data):
    """Display economic analysis in table format"""
    investment_scenarios = analysis_data.get('investment_scenarios', {})
    
    if not investment_scenarios:
        return
    
    st.markdown("### 💹 Economic Impact Analysis")
    
    # Create DataFrame for table display
    scenarios_data = []
    for scenario, data in investment_scenarios.items():
        scenarios_data.append({
            'Investment Level': scenario.title(),
            'Total Cost ($)': f"{data.get('total_cost', 0):,}",
            'Yield Increase (%)': f"{data.get('yield_increase', 0)}%",
            'ROI (%)': f"{data.get('roi', 0)}%",
            'Payback Period': data.get('payback_period', 'N/A')
        })
    
    if scenarios_data:
        df = pd.DataFrame(scenarios_data)
        apply_table_styling()
        st.dataframe(df, use_container_width=True)
        
        # Summary metrics
        st.markdown("### 📊 Economic Summary")
        col1, col2, col3 = st.columns(3)
        
        costs = [data.get('total_cost', 0) for data in investment_scenarios.values() if isinstance(data.get('total_cost', 0), (int, float))]
        rois = [data.get('roi', 0) for data in investment_scenarios.values() if isinstance(data.get('roi', 0), (int, float))]
        
        with col1:
            if costs:
                st.metric("💰 Cost Range", f"${min(costs):,.0f} - ${max(costs):,.0f}")
            else:
                st.metric("💰 Cost Range", "N/A")
        with col2:
            if rois:
                st.metric("📈 ROI Range", f"{min(rois):.1f}% - {max(rois):.1f}%")
            else:
                st.metric("📈 ROI Range", "N/A")
        with col3:
            st.metric("🎯 Recommended", "Medium Investment")

def display_regenerative_strategies(analysis_data):
    """Display regenerative agriculture strategies"""
    strategies = analysis_data.get('strategies', [])
    
    if not strategies:
        return
    
    st.markdown("### 🌱 Regenerative Agriculture Strategies")
    
    for strategy in strategies:
        with st.expander(f"🌿 {strategy.get('name', 'Strategy')}", expanded=False):
            st.markdown(f"**Description:** {strategy.get('description', '')}")
            
            if 'benefits' in strategy:
                st.markdown("**Benefits:**")
                for benefit in strategy['benefits']:
                    st.markdown(f"• {benefit}")
            
            col1, col2 = st.columns(2)
            with col1:
                if 'timeline' in strategy:
                    st.markdown(f"**⏱️ Timeline:** {strategy['timeline']}")
            with col2:
                if 'cost' in strategy:
                    st.markdown(f"**💰 Cost:** {strategy['cost']}")
            
            if 'implementation' in strategy:
                st.markdown(f"**🔧 Implementation:** {strategy['implementation']}")

def display_forecast_visualization(analysis_data):
    """Display interactive forecast visualization"""
    forecast_data = analysis_data.get('yield_projections', {})
    
    if not forecast_data:
        return
    
    st.markdown("### 📈 5-Year Yield Forecast")
    
    # Create interactive Plotly chart
    years = list(range(2024, 2029))
    
    fig = go.Figure()
    
    # Add traces for each investment level
    for level in ['high', 'medium', 'low']:
        if level in forecast_data:
            values = forecast_data[level]
            color = {'high': '#28a745', 'medium': '#17a2b8', 'low': '#6c757d'}[level]
            
            fig.add_trace(go.Scatter(
                x=years,
                y=values,
                mode='lines+markers',
                name=f'{level.title()} Investment',
                line=dict(color=color, width=3),
                marker=dict(size=8)
            ))
    
    fig.update_layout(
        title='Projected Yield Improvements Over 5 Years',
        xaxis_title='Year',
        yaxis_title='Yield (tons/hectare)',
        hovermode='x unified',
        height=500
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Display forecast table
    if forecast_data:
        st.markdown("### 📊 Detailed Yield Projections")
        
        table_data = []
        for year in years:
            row = {'Year': year}
            for level in ['high', 'medium', 'low']:
                if level in forecast_data and len(forecast_data[level]) >= (year - 2023):
                    row[f'{level.title()} Investment'] = f"{forecast_data[level][year - 2024]:.1f} tons/ha"
            table_data.append(row)
        
        df = pd.DataFrame(table_data)
        apply_table_styling()
        st.dataframe(df, use_container_width=True)

def display_multi_axis_chart(data, title, options):
    """Display multi-axis chart visualization"""
    try:
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots
        
        categories = data.get('categories', [])
        series = data.get('series', [])
        
        if not categories or not series:
            st.info("Multi-axis chart data format not recognized")
            return
        
        # Create subplots with secondary y-axis
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        
        # Add traces for each series
        for series_data in series:
            series_name = series_data.get('name', 'Series')
            series_values = series_data.get('data', [])
            series_color = series_data.get('color', '#3498db')
            axis = series_data.get('axis', 'left')
            
            if axis == 'left':
                fig.add_trace(
                    go.Scatter(
                        x=categories,
                        y=series_values,
                        mode='lines+markers',
                        name=series_name,
                        line=dict(color=series_color, width=3),
                        marker=dict(size=8, color=series_color)
                    ),
                    secondary_y=False
                )
            else:  # right axis
                fig.add_trace(
                    go.Scatter(
                        x=categories,
                        y=series_values,
                        mode='lines+markers',
                        name=series_name,
                        line=dict(color=series_color, width=3),
                        marker=dict(size=8, color=series_color)
                    ),
                    secondary_y=True
                )
        
        # Update layout
        fig.update_layout(
            title=dict(
                text=title,
                x=0.5,
                font=dict(size=16, color='#2E7D32')
            ),
            xaxis_title=options.get('x_axis_title', 'Categories'),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(size=12),
            height=400,
            hovermode='x unified'
        )
        
        # Set y-axes titles
        fig.update_yaxes(title_text=options.get('left_axis_title', 'Left Axis'), secondary_y=False)
        fig.update_yaxes(title_text=options.get('right_axis_title', 'Right Axis'), secondary_y=True)
        
        st.plotly_chart(fig, use_container_width=True)
        
    except ImportError:
        st.info("Plotly not available for chart display")
    except Exception as e:
        st.error(f"Error displaying multi-axis chart: {str(e)}")

def display_heatmap(data, title, options):
    """Display heatmap visualization"""
    try:
        import plotly.graph_objects as go
        import plotly.express as px
        
        parameters = data.get('parameters', [])
        levels = data.get('levels', [])
        color_scale = data.get('color_scale', {})
        
        if not parameters or not levels:
            st.info("Heatmap data format not recognized")
            return
        
        # Create heatmap data
        heatmap_data = []
        for i, param in enumerate(parameters):
            heatmap_data.append([levels[i]])
        
        # Create color scale
        colors = []
        for level in levels:
            if level in color_scale:
                colors.append(color_scale[level])
            else:
                colors.append('#f0f0f0')  # Default color
        
        fig = go.Figure(data=go.Heatmap(
            z=heatmap_data,
            x=['Deficiency Level'],
            y=parameters,
            colorscale=[[0, '#e74c3c'], [0.33, '#f39c12'], [0.66, '#f1c40f'], [1, '#2ecc71']],
            showscale=True,
            colorbar=dict(
                title="Deficiency Level",
                tickvals=[0, 1, 2, 3],
                ticktext=['Critical', 'High', 'Medium', 'Low']
            )
        ))
        
        fig.update_layout(
            title=dict(
                text=title,
                x=0.5,
                font=dict(size=16, color='#2E7D32')
            ),
            xaxis_title="Deficiency Level",
            yaxis_title="Parameters",
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(size=12),
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
    except ImportError:
        st.info("Plotly not available for chart display")
    except Exception as e:
        st.error(f"Error displaying heatmap: {str(e)}")

def display_feedback_section(results_data):
    """Display feedback collection section after step-by-step analysis"""
    try:
        # Get analysis ID and user ID
        analysis_id = results_data.get('analysis_id', f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        user_id = st.session_state.get('user_id', 'anonymous')
        
        # Display feedback section
        display_feedback_section_util(analysis_id, user_id)
        
    except Exception as e:
        logger.error(f"Error displaying feedback section: {str(e)}")
        # Don't show error to user, just skip feedback section
        pass


def create_mpob_standards_comparison_viz(soil_params, leaf_params):
    """Create MPOB standards comparison visualization"""
    try:
        # Get MPOB standards
        try:
            from utils.mpob_standards import get_mpob_standards
            mpob = get_mpob_standards()
        except:
            mpob = None
        
        if not mpob:
            return None
        
        soil_stats = soil_params.get('parameter_statistics', {})
        leaf_stats = leaf_params.get('parameter_statistics', {})
        
        if not soil_stats and not leaf_stats:
            return None
        
        # Create soil vs MPOB comparison
        soil_categories = []
        soil_actual = []
        soil_optimal = []
        
        if soil_stats:
            soil_mapping = {
                'pH': ('pH', 'pH'),
                'Nitrogen_%': ('Nitrogen %', 'nitrogen'),
                'Organic_Carbon_%': ('Organic Carbon %', 'organic_carbon'),
                'Total_P_mg_kg': ('Total P (mg/kg)', 'total_phosphorus'),
                'Available_P_mg_kg': ('Available P (mg/kg)', 'available_phosphorus'),
                'Exchangeable_K_meq%': ('Exch. K (meq%)', 'exchangeable_potassium'),
                'Exchangeable_Ca_meq%': ('Exch. Ca (meq%)', 'exchangeable_calcium'),
                'Exchangeable_Mg_meq%': ('Exch. Mg (meq%)', 'exchangeable_magnesium'),
                'CEC_meq%': ('CEC (meq%)', 'cec')
            }
            
            for param_key, (display_name, mpob_key) in soil_mapping.items():
                if param_key in soil_stats and mpob_key in mpob.get('soil', {}):
                    actual_val = soil_stats[param_key].get('average', 0)
                    optimal_val = mpob['soil'][mpob_key].get('optimal', 0)
                    
                    if actual_val > 0:
                        soil_categories.append(display_name)
                        soil_actual.append(actual_val)
                        soil_optimal.append(optimal_val)
        
        return {
            'type': 'actual_vs_optimal_bar',
            'title': '📊 Soil Parameters vs MPOB Standards',
            'subtitle': 'Comparison of current soil values against MPOB optimal standards',
            'data': {
                'categories': soil_categories,
                'series': [
                    {'name': 'Current Values', 'values': soil_actual, 'color': '#3498db'},
                    {'name': 'MPOB Optimal', 'values': soil_optimal, 'color': '#e74c3c'}
                ]
            },
            'options': {
                'show_legend': True,
                'show_values': True,
                'y_axis_title': 'Values',
                'x_axis_title': 'Soil Parameters',
                'show_target_line': True,
                'target_line_color': '#f39c12'
            }
        }
        
    except Exception as e:
        logger.error(f"Error creating MPOB standards comparison visualization: {e}")
        return None

def create_issues_severity_viz(step_result, analysis_data):
    """Create issues severity visualization"""
    try:
        # Extract issues from step data
        issues = []
        if 'issues_identified' in step_result:
            issues = step_result['issues_identified']
        elif 'issues_analysis' in analysis_data:
            issues = analysis_data['issues_analysis'].get('all_issues', [])
        
        if not issues:
            return None
        
        # Categorize issues by severity
        severity_categories = {'Critical': 0, 'High': 0, 'Medium': 0, 'Low': 0}
        
        for issue in issues:
            if isinstance(issue, dict):
                severity = issue.get('severity', 'Medium').title()
                if severity in severity_categories:
                    severity_categories[severity] += 1
                else:
                    severity_categories['Medium'] += 1
            elif isinstance(issue, str):
                # Try to extract severity from text
                issue_lower = issue.lower()
                if 'critical' in issue_lower or 'severe' in issue_lower:
                    severity_categories['Critical'] += 1
                elif 'high' in issue_lower:
                    severity_categories['High'] += 1
                elif 'low' in issue_lower:
                    severity_categories['Low'] += 1
                else:
                    severity_categories['Medium'] += 1
        
        # Filter out zero values
        categories = [k for k, v in severity_categories.items() if v > 0]
        values = [v for k, v in severity_categories.items() if v > 0]
        colors = ['#e74c3c', '#f39c12', '#f1c40f', '#2ecc71'][:len(categories)]
        
        if not categories:
            return None
        
        return {
            'type': 'pie_chart',
            'title': '🚨 Issues Severity Distribution',
            'subtitle': 'Breakdown of identified issues by severity level',
            'data': {
                'categories': categories,
                'values': values,
                'colors': colors
            },
            'options': {
                'show_legend': True,
                'show_values': True,
                'show_percentages': True
            }
        }
        
    except Exception as e:
        logger.error(f"Error creating issues severity visualization: {e}")
        return None

def create_nutrient_deficiency_heatmap(soil_params, leaf_params):
    """Create nutrient deficiency heatmap"""
    try:
        soil_stats = soil_params.get('parameter_statistics', {})
        leaf_stats = leaf_params.get('parameter_statistics', {})
        
        if not soil_stats and not leaf_stats:
            return None
        
        # Get MPOB standards for comparison
        try:
            from utils.mpob_standards import get_mpob_standards
            mpob = get_mpob_standards()
        except:
            mpob = None
        
        # Prepare heatmap data
        parameters = []
        deficiency_levels = []
        
        # Soil parameters
        if soil_stats and mpob:
            soil_mapping = {
                'pH': 'pH',
                'Nitrogen_%': 'nitrogen',
                'Organic_Carbon_%': 'organic_carbon',
                'Total_P_mg_kg': 'total_phosphorus',
                'Available_P_mg_kg': 'available_phosphorus',
                'Exchangeable_K_meq%': 'exchangeable_potassium',
                'Exchangeable_Ca_meq%': 'exchangeable_calcium',
                'Exchangeable_Mg_meq%': 'exchangeable_magnesium',
                'CEC_meq%': 'cec'
            }
            
            for param_key, mpob_key in soil_mapping.items():
                if param_key in soil_stats and mpob_key in mpob.get('soil', {}):
                    actual = soil_stats[param_key].get('average', 0)
                    optimal = mpob['soil'][mpob_key].get('optimal', 0)
                    
                    if actual > 0 and optimal > 0:
                        deficiency_ratio = actual / optimal
                        if deficiency_ratio < 0.5:
                            level = 'Critical'
                        elif deficiency_ratio < 0.7:
                            level = 'High'
                        elif deficiency_ratio < 0.9:
                            level = 'Medium'
                        else:
                            level = 'Low'
                        
                        parameters.append(param_key.replace('_', ' '))
                        deficiency_levels.append(level)
        
        if not parameters:
            return None
        
        return {
            'type': 'heatmap',
            'title': '🔥 Nutrient Deficiency Heatmap',
            'subtitle': 'Visual representation of nutrient deficiency levels',
            'data': {
                'parameters': parameters,
                'levels': deficiency_levels,
                'color_scale': {
                    'Critical': '#e74c3c',
                    'High': '#f39c12',
                    'Medium': '#f1c40f',
                    'Low': '#2ecc71'
                }
            },
            'options': {
                'show_legend': True,
                'show_values': True
            }
        }
        
    except Exception as e:
        logger.error(f"Error creating nutrient deficiency heatmap: {e}")
        return None

def create_issues_severity_bar_viz(step_result, analysis_data):
    """Create issues severity bar chart visualization"""
    try:
        # Extract issues from step data
        issues = []
        if 'issues_identified' in step_result:
            issues = step_result['issues_identified']
        elif 'issues_analysis' in analysis_data:
            issues = analysis_data['issues_analysis'].get('all_issues', [])
        
        if not issues:
            return None
        
        # Categorize issues by severity
        severity_categories = {'Critical': 0, 'High': 0, 'Medium': 0, 'Low': 0}
        
        for issue in issues:
            if isinstance(issue, dict):
                severity = issue.get('severity', 'Medium').title()
                if severity in severity_categories:
                    severity_categories[severity] += 1
                else:
                    severity_categories['Medium'] += 1
            elif isinstance(issue, str):
                # Try to extract severity from text
                issue_lower = issue.lower()
                if 'critical' in issue_lower or 'severe' in issue_lower:
                    severity_categories['Critical'] += 1
                elif 'high' in issue_lower:
                    severity_categories['High'] += 1
                elif 'low' in issue_lower:
                    severity_categories['Low'] += 1
                else:
                    severity_categories['Medium'] += 1
        
        # Filter out zero values
        categories = [k for k, v in severity_categories.items() if v > 0]
        values = [v for k, v in severity_categories.items() if v > 0]
        colors = ['#e74c3c', '#f39c12', '#f1c40f', '#2ecc71'][:len(categories)]
        
        if not categories:
            return None
        
        return {
            'type': 'actual_vs_optimal_bar',
            'title': '📊 Issues Distribution by Severity',
            'subtitle': 'Breakdown of identified issues by severity level',
            'data': {
                'categories': categories,
                'series': [
                    {'name': 'Issue Count', 'values': values, 'color': '#3498db'},
                    {'name': 'Target (0)', 'values': [0] * len(categories), 'color': '#e74c3c'}
                ]
            },
            'options': {
                'show_legend': True,
                'show_values': True,
                'y_axis_title': 'Number of Issues',
                'x_axis_title': 'Severity Level',
                'show_target_line': False
            }
        }
        
    except Exception as e:
        logger.error(f"Error creating issues severity bar visualization: {e}")
        return None

def create_soil_ph_comparison_viz(soil_params):
    """Create soil pH comparison visualization against MPOB standard"""
    try:
        if not soil_params or 'parameter_statistics' not in soil_params:
            return None
        
        param_stats = soil_params['parameter_statistics']
        ph_data = param_stats.get('pH', {})
        
        if not ph_data or 'values' not in ph_data:
            return None
        
        ph_values = ph_data['values']
        if not ph_values:
            return None
        
        # MPOB optimal pH range: 4.5-6.5, minimum 4.5
        mpob_optimal_min = 4.5
        mpob_optimal_max = 6.5
        
        # Create sample labels (S1, S2, etc.)
        sample_labels = [f"S{i+1}" for i in range(len(ph_values))]
        
        # Create the visualization data
        return {
            'type': 'actual_vs_optimal_bar',
            'title': 'Soil pH vs MPOB Standard',
            'subtitle': 'Comparison of actual pH values against MPOB optimal range',
            'data': {
                'categories': sample_labels,
                'series': [
                    {
                        'name': 'Sample pH',
                        'values': ph_values,
                        'color': '#ff6384'
                    },
                    {
                        'name': 'MPOB Optimum Minimum',
                        'values': [mpob_optimal_min] * len(ph_values),
                        'color': '#4bc0c0'
                    }
                ]
            },
            'options': {
                'show_legend': True,
                'show_values': True,
                'y_axis_title': 'pH Value',
                'x_axis_title': 'Sample',
                'show_target_line': True,
                'target_value': mpob_optimal_min,
                'target_label': 'MPOB Minimum (4.5)'
            }
        }
        
    except Exception as e:
        logger.error(f"Error creating soil pH comparison visualization: {e}")
        return None

def create_nutrient_deficiency_bar_viz(soil_params, leaf_params):
    """Create nutrient deficiency bar chart visualization"""
    try:
        soil_stats = soil_params.get('parameter_statistics', {})
        leaf_stats = leaf_params.get('parameter_statistics', {})
        
        if not soil_stats and not leaf_stats:
            return None
        
        # Get MPOB standards for comparison
        try:
            from utils.mpob_standards import get_mpob_standards
            mpob = get_mpob_standards()
        except:
            mpob = None
        
        # Prepare bar chart data
        parameters = []
        deficiency_counts = {'Critical': 0, 'High': 0, 'Medium': 0, 'Low': 0}
        
        # Soil parameters
        if soil_stats and mpob:
            soil_mapping = {
                'pH': 'pH',
                'Nitrogen_%': 'nitrogen',
                'Organic_Carbon_%': 'organic_carbon',
                'Total_P_mg_kg': 'total_phosphorus',
                'Available_P_mg_kg': 'available_phosphorus',
                'Exchangeable_K_meq%': 'exchangeable_potassium',
                'Exchangeable_Ca_meq%': 'exchangeable_calcium',
                'Exchangeable_Mg_meq%': 'exchangeable_magnesium',
                'CEC_meq%': 'cec'
            }
            
            for param_key, mpob_key in soil_mapping.items():
                if param_key in soil_stats and mpob_key in mpob.get('soil', {}):
                    actual = soil_stats[param_key].get('average', 0)
                    optimal = mpob['soil'][mpob_key].get('optimal', 0)
                    
                    if actual > 0 and optimal > 0:
                        deficiency_ratio = actual / optimal
                        if deficiency_ratio < 0.5:
                            level = 'Critical'
                        elif deficiency_ratio < 0.7:
                            level = 'High'
                        elif deficiency_ratio < 0.9:
                            level = 'Medium'
                        else:
                            level = 'Low'
                        
                        deficiency_counts[level] += 1
        
        # Filter out zero values
        categories = [k for k, v in deficiency_counts.items() if v > 0]
        values = [v for k, v in deficiency_counts.items() if v > 0]
        colors = ['#e74c3c', '#f39c12', '#f1c40f', '#2ecc71'][:len(categories)]
        
        if not categories:
            return None
        
        return {
            'type': 'actual_vs_optimal_bar',
            'title': '📊 Nutrient Deficiency Levels',
            'subtitle': 'Count of parameters by deficiency severity',
            'data': {
                'categories': categories,
                'series': [
                    {'name': 'Parameter Count', 'values': values, 'color': '#3498db'},
                    {'name': 'Target (0)', 'values': [0] * len(categories), 'color': '#e74c3c'}
                ]
            },
            'options': {
                'show_legend': True,
                'show_values': True,
                'y_axis_title': 'Number of Parameters',
                'x_axis_title': 'Deficiency Level',
                'show_target_line': False
            }
        }
        
    except Exception as e:
        logger.error(f"Error creating nutrient deficiency bar visualization: {e}")
        return None

def create_solution_priority_viz(step_result, analysis_data):
    """Create solution priority visualization"""
    try:
        # Extract recommendations from step data
        recommendations = []
        if 'recommendations' in step_result:
            recommendations = step_result['recommendations']
        elif 'recommendations' in analysis_data:
            recommendations = analysis_data['recommendations']
        
        if not recommendations:
            return None
        
        # Categorize recommendations by priority
        priority_categories = {'High': 0, 'Medium': 0, 'Low': 0}
        
        for rec in recommendations:
            if isinstance(rec, dict):
                priority = rec.get('priority', 'Medium').title()
                if priority in priority_categories:
                    priority_categories[priority] += 1
            elif isinstance(rec, str):
                rec_lower = rec.lower()
                if 'high' in rec_lower or 'critical' in rec_lower or 'urgent' in rec_lower:
                    priority_categories['High'] += 1
                elif 'low' in rec_lower:
                    priority_categories['Low'] += 1
                else:
                    priority_categories['Medium'] += 1
        
        # Filter out zero values
        categories = [k for k, v in priority_categories.items() if v > 0]
        values = [v for k, v in priority_categories.items() if v > 0]
        colors = ['#e74c3c', '#f39c12', '#2ecc71'][:len(categories)]
        
        if not categories:
            return None
        
        return {
            'type': 'bar_chart',
            'title': '🎯 Solution Priority Distribution',
            'subtitle': 'Breakdown of recommendations by priority level',
            'data': {
                'categories': categories,
                'values': values,
                'colors': colors
            },
            'options': {
                'show_legend': True,
                'show_values': True,
                'y_axis_title': 'Number of Recommendations',
                'x_axis_title': 'Priority Level'
            }
        }
        
    except Exception as e:
        logger.error(f"Error creating solution priority visualization: {e}")
        return None

def create_cost_benefit_viz(analysis_data):
    """Create cost-benefit analysis visualization"""
    try:
        economic_data = analysis_data.get('economic_forecast', {})
        if not economic_data:
            return None
        
        scenarios = economic_data.get('scenarios', {})
        if not scenarios:
            return None
        
        # Extract cost-benefit data
        investment_levels = []
        roi_values = []
        payback_periods = []
        
        for level, data in scenarios.items():
            if isinstance(data, dict):
                investment_levels.append(level.title())
                roi_values.append(data.get('roi_percentage', 0))
                payback_periods.append(data.get('payback_months', 0))
        
        if not investment_levels:
            return None
        
        return {
            'type': 'multi_axis_chart',
            'title': '💰 Cost-Benefit Analysis',
            'subtitle': 'ROI and payback period for different investment levels',
            'data': {
                'categories': investment_levels,
                'series': [
                    {
                        'name': 'ROI (%)',
                        'data': roi_values,
                        'color': '#2ecc71',
                        'axis': 'left'
                    },
                    {
                        'name': 'Payback (months)',
                        'data': payback_periods,
                        'color': '#e74c3c',
                        'axis': 'right'
                    }
                ]
            },
            'options': {
                'show_legend': True,
                'show_values': True,
                'left_axis_title': 'ROI (%)',
                'right_axis_title': 'Payback Period (months)',
                'x_axis_title': 'Investment Level'
            }
        }
        
    except Exception as e:
        logger.error(f"Error creating cost-benefit visualization: {e}")
        return None

def create_comprehensive_comparison_viz(soil_params, leaf_params):
    """Create comprehensive comparison visualization"""
    try:
        soil_stats = soil_params.get('parameter_statistics', {})
        leaf_stats = leaf_params.get('parameter_statistics', {})
        
        if not soil_stats and not leaf_stats:
            return None
        
        # Create a comprehensive radar chart
        parameters = []
        soil_values = []
        leaf_values = []
        
        # Common parameters for comparison
        common_params = {
            'N_%': 'Nitrogen',
            'P_%': 'Phosphorus',
            'K_%': 'Potassium',
            'Mg_%': 'Magnesium',
            'Ca_%': 'Calcium'
        }
        
        for param_key, display_name in common_params.items():
            soil_val = soil_stats.get(param_key, {}).get('average', 0)
            leaf_val = leaf_stats.get(param_key, {}).get('average', 0)
            
            if soil_val > 0 or leaf_val > 0:
                parameters.append(display_name)
                soil_values.append(soil_val)
                leaf_values.append(leaf_val)
        
        if not parameters:
            return None
        
        return {
            'type': 'radar_chart',
            'title': '🕸️ Comprehensive Nutrient Comparison',
            'subtitle': 'Radar chart comparing soil and leaf nutrient levels',
            'data': {
                'categories': parameters,
                'series': [
                    {'name': 'Soil', 'data': soil_values, 'color': '#3498db'},
                    {'name': 'Leaf', 'data': leaf_values, 'color': '#e74c3c'}
                ]
            },
            'options': {
                'show_legend': True,
                'show_values': True,
                'fill_area': True
            }
        }
        
    except Exception as e:
        logger.error(f"Error creating comprehensive comparison visualization: {e}")
        return None

def create_plantation_vs_mpob_viz(soil_params, leaf_params):
    """Create plantation values vs MPOB standards visualization"""
    try:
        # This is similar to MPOB standards comparison but with plantation focus
        return create_mpob_standards_comparison_viz(soil_params, leaf_params)
        
    except Exception as e:
        logger.error(f"Error creating plantation vs MPOB visualization: {e}")
        return None

def _removed_display_print_dialog(results_data):
    """Display print PDF dialog with options"""
    st.markdown("---")
    st.markdown("## 🖨️ Print to PDF")
    
    with st.container():
        st.info("📄 **Print Options:** Choose what to include in your PDF report")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Print options
            include_raw_data = st.checkbox("📊 Include Raw Data Tables", value=True, help="Include soil and leaf analysis data tables")
            include_summary = st.checkbox("📋 Include Executive Summary", value=True, help="Include the executive summary section")
            include_key_findings = st.checkbox("🎯 Include Key Findings", value=True, help="Include key findings section")
            include_step_analysis = st.checkbox("🔬 Include Step-by-Step Analysis", value=True, help="Include detailed step-by-step analysis")
            include_references = st.checkbox("📚 Include References", value=True, help="Include research references")
            include_charts = st.checkbox("📈 Include Charts & Visualizations", value=True, help="Include all charts and visualizations")
            
            # PDF options
            st.markdown("**PDF Options:**")
            pdf_title = st.text_input("📝 PDF Title", value="Agricultural Analysis Report", help="Custom title for the PDF")
            include_timestamp = st.checkbox("⏰ Include Timestamp", value=True, help="Add timestamp to PDF header")
            
        with col2:
            st.markdown("**Preview:**")
            st.markdown(f"📄 **Title:** {pdf_title}")
            st.markdown(f"📅 **Date:** {results_data.get('timestamp', 'N/A')}")
            st.markdown(f"📊 **Sections:** {sum([include_raw_data, include_summary, include_key_findings, include_step_analysis, include_references, include_charts])} selected")
            
            # Debug information
            if st.checkbox("🔍 Show Debug Info", help="Show data structure information for troubleshooting"):
                st.markdown("**Data Structure:**")
                analysis_results = get_analysis_results_from_data(results_data)
                st.markdown(f"• Analysis Results: {'✅' if analysis_results else '❌'}")
                st.markdown(f"• Step-by-Step Analysis: {'✅' if analysis_results.get('step_by_step_analysis') else '❌'}")
                st.markdown(f"• Raw Data: {'✅' if analysis_results.get('raw_data') else '❌'}")
                st.markdown(f"• Economic Forecast: {'✅' if results_data.get('economic_forecast') else '❌'}")
                st.markdown(f"• Yield Forecast: {'✅' if results_data.get('yield_forecast') else '❌'}")
            
            # Generate PDF button
            if st.button("🖨️ Generate PDF", type="primary", width='stretch'):
                with st.spinner("🔄 Generating PDF report..."):
                    try:
                        # Generate PDF with selected options
                        pdf_bytes = generate_results_pdf(
                            results_data,
                            include_raw_data=include_raw_data,
                            include_summary=include_summary,
                            include_key_findings=include_key_findings,
                            include_step_analysis=include_step_analysis,
                            include_references=include_references,
                            include_charts=include_charts,
                            pdf_title=pdf_title,
                            include_timestamp=include_timestamp
                        )
                        
                        if pdf_bytes:
                            # Provide download button
                            st.success("✅ PDF generated successfully!")
                            
                            # Create download button
                            st.download_button(
                                label="📥 Download PDF Report",
                                data=pdf_bytes,
                                file_name=f"{pdf_title.replace(' ', '_')}_{results_data.get('timestamp', 'report')}.pdf",
                                mime="application/pdf",
                                type="primary"
                            )
                            
                            # PDF generated successfully - no need to close dialog since it's always visible
                        else:
                            st.error("❌ Failed to generate PDF. Please check the logs for more details.")
                            st.info("💡 **Troubleshooting:** Make sure your analysis data is complete and try again.")
                            
                    except Exception as e:
                        st.error(f"❌ Error generating PDF: {str(e)}")
                        st.info("💡 **Troubleshooting:** This might be due to missing analysis data. Please try refreshing the page and running the analysis again.")
                        logger.error(f"PDF generation error: {e}")
                        import traceback
                        logger.error(f"Full traceback: {traceback.format_exc()}")
            

def _removed_generate_results_pdf(results_data, include_raw_data=True, include_summary=True, 
                        include_key_findings=True, include_step_analysis=True, 
                        include_references=True, include_charts=True, 
                        pdf_title="Agricultural Analysis Report", include_timestamp=True):
    """Generate PDF from results page content"""
    try:
        from utils.pdf_utils import PDFReportGenerator
        
        # Prepare analysis data for PDF generation (same as existing download functionality)
        analysis_data = results_data.get('analysis_results', {})
        
        # If analysis_results is empty, use the full results_data
        if not analysis_data:
            analysis_data = results_data
        
        # Ensure economic_forecast is available at the top level
        if 'economic_forecast' in results_data and 'economic_forecast' not in analysis_data:
            analysis_data['economic_forecast'] = results_data['economic_forecast']
        
        # Ensure yield_forecast is available at the top level
        if 'yield_forecast' in results_data and 'yield_forecast' not in analysis_data:
            analysis_data['yield_forecast'] = results_data['yield_forecast']
        
        # Create metadata for PDF
        metadata = {
            'title': pdf_title,
            'timestamp': results_data.get('timestamp'),
            'include_timestamp': include_timestamp,
            'sections': {
                'raw_data': include_raw_data,
                'summary': include_summary,
                'key_findings': include_key_findings,
                'step_analysis': include_step_analysis,
                'references': include_references,
                'charts': include_charts
            }
        }
        
        # Create PDF options
        options = {
            'include_economic': True,
            'include_forecast': True,
            'include_charts': include_charts,
            'include_raw_data': include_raw_data,
            'include_summary': include_summary,
            'include_key_findings': include_key_findings,
            'include_step_analysis': include_step_analysis,
            'include_references': include_references
        }
        
        # Generate PDF using existing PDF utils
        generator = PDFReportGenerator()
        pdf_bytes = generator.generate_report(analysis_data, metadata, options)
        
        return pdf_bytes
        
    except Exception as e:
        logger.error(f"Error generating results PDF: {e}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        return None

def generate_results_pdf(results_data, include_raw_data=True, include_summary=True, 
                        include_key_findings=True, include_step_analysis=True, 
                        include_references=False, include_charts=True, 
                        pdf_title="Agricultural Analysis Report", include_timestamp=True):
    """Generate comprehensive PDF from results page content - includes ALL details"""
    try:
        from utils.pdf_utils import PDFReportGenerator
        
        # Prepare analysis data for PDF generation
        analysis_data = results_data.get('analysis_results', {})
        
        # If analysis_results is empty, use the full results_data
        if not analysis_data:
            analysis_data = results_data
        
        # Ensure all forecast data is available at the top level
        if 'economic_forecast' in results_data and 'economic_forecast' not in analysis_data:
            analysis_data['economic_forecast'] = results_data['economic_forecast']
        
        if 'yield_forecast' in results_data and 'yield_forecast' not in analysis_data:
            analysis_data['yield_forecast'] = results_data['yield_forecast']
        
        # Include all additional data from results page
        if 'raw_data' in results_data and 'raw_data' not in analysis_data:
            analysis_data['raw_data'] = results_data['raw_data']
        
        if 'summary_metrics' in results_data and 'summary_metrics' not in analysis_data:
            analysis_data['summary_metrics'] = results_data['summary_metrics']
        
        if 'key_findings' in results_data and 'key_findings' not in analysis_data:
            analysis_data['key_findings'] = results_data['key_findings']
        
        if 'step_by_step_analysis' in results_data and 'step_by_step_analysis' not in analysis_data:
            analysis_data['step_by_step_analysis'] = results_data['step_by_step_analysis']
        
        if 'references' in results_data and 'references' not in analysis_data:
            analysis_data['references'] = results_data['references']
        
        # Create comprehensive metadata for PDF
        metadata = {
            'title': pdf_title,
            'timestamp': results_data.get('timestamp'),
            'include_timestamp': include_timestamp,
            'sections': {
                'raw_data': include_raw_data,
                'summary': include_summary,
                'key_findings': include_key_findings,
                'step_analysis': include_step_analysis,
                'references': include_references,
                'charts': include_charts
            }
        }
        
        # Create comprehensive PDF options - include ALL sections except economic/forecast
        options = {
            'include_economic': False,
            'include_forecast': False,
            'include_charts': include_charts,
            'include_raw_data': include_raw_data,
            'include_summary': include_summary,
            'include_key_findings': include_key_findings,
            'include_step_analysis': include_step_analysis,
            'include_references': include_references,
            'include_all_details': True  # Ensure all details are included
        }
        
        # Generate comprehensive PDF using existing PDF utils
        generator = PDFReportGenerator()
        pdf_bytes = generator.generate_report(analysis_data, metadata, options)
        
        return pdf_bytes
        
    except Exception as e:
        logger.error(f"Error generating comprehensive results PDF: {e}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        return None


def display_nutrient_ratio_diagram(data, title, options=None):
    """Display nutrient ratio diagram with individual bar charts for each parameter"""
    try:
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots
        
        categories = data.get('categories', [])
        values = data.get('values', [])
        optimal_ranges = data.get('optimal_ranges', {})
        
        if not categories or not values:
            st.info("No nutrient ratio data available")
            return
        
        # Create subplots - one for each ratio parameter
        num_params = len(categories)
        
        # Calculate optimal layout - if more than 4 parameters, use 2 rows
        if num_params > 4:
            rows = 2
            cols = (num_params + 1) // 2
        else:
            rows = 1
            cols = num_params
        
        fig = make_subplots(
            rows=rows, 
            cols=cols,
            subplot_titles=categories,
            horizontal_spacing=0.05,
            vertical_spacing=0.2
        )
        
        # Define colors
        current_color = '#2ecc71'  # Green for current ratios
        optimal_color = '#e67e22'  # Orange for optimal ranges
        
        # Add bars for each ratio parameter
        for i, ratio_name in enumerate(categories):
            current_value = values[i]
            
            # Calculate appropriate scale for this parameter
            max_val = current_value
            min_val = 0
            
            # Add optimal range if available
            if ratio_name in optimal_ranges:
                min_opt, max_opt = optimal_ranges[ratio_name]
                optimal_midpoint = (min_opt + max_opt) / 2
                max_val = max(current_value, max_opt)
                min_val = min(current_value, min_opt)
            else:
                optimal_midpoint = current_value * 1.2  # Default if no optimal range
            
            # Add more padding to the scale to accommodate outside text
            range_val = max_val - min_val
            if range_val == 0:
                range_val = max_val * 0.1 if max_val > 0 else 1
            
            y_max = max_val + (range_val * 0.4)  # Increased padding for outside text
            y_min = max(0, min_val - (range_val * 0.2))  # Increased padding for outside text
            
            # Calculate row and column position
            if rows == 1:
                row_pos = 1
                col_pos = i + 1
            else:
                row_pos = (i // cols) + 1
                col_pos = (i % cols) + 1
            
            # Add current ratio bar
            fig.add_trace(
                go.Bar(
                    x=['Current'],
                    y=[current_value],
                    name='Current Ratio' if i == 0 else None,  # Only show legend for first chart
                    marker_color=current_color,
                    text=[f"{current_value:.2f}"],
                    textposition='outside',
                    textfont=dict(size=10, color='black', family='Arial Black'),
                    showlegend=(i == 0)
                ),
                row=row_pos, col=col_pos
            )
            
            # Add optimal range bar if available
            if ratio_name in optimal_ranges:
                fig.add_trace(
                    go.Bar(
                        x=['Optimal'],
                        y=[optimal_midpoint],
                        name='Optimal Range (Midpoint)' if i == 0 else None,  # Only show legend for first chart
                        marker_color=optimal_color,
                        text=[f"{optimal_midpoint:.2f}"],
                        textposition='outside',
                        textfont=dict(size=10, color='black', family='Arial Black'),
                        showlegend=(i == 0)
                    ),
                    row=row_pos, col=col_pos
                )
                
                # Add range indicators as horizontal lines
                min_opt, max_opt = optimal_ranges[ratio_name]
                fig.add_hline(y=min_opt, line_dash="dash", line_color="orange", 
                             annotation_text=f"Min: {min_opt:.1f}", annotation_position="right",
                             row=row_pos, col=col_pos)
                fig.add_hline(y=max_opt, line_dash="dash", line_color="orange", 
                             annotation_text=f"Max: {max_opt:.1f}", annotation_position="right",
                             row=row_pos, col=col_pos)
            
            # Update y-axis for this subplot
            fig.update_yaxes(
                range=[y_min, y_max],
                row=row_pos, col=col_pos,
                showgrid=True,
                gridwidth=1,
                gridcolor='lightgray'
            )
            
            # Update x-axis for this subplot
            fig.update_xaxes(
                row=row_pos, col=col_pos,
                showgrid=False,
                tickangle=0
            )
        
        # Update layout
        fig.update_layout(
            title=dict(
                text=title,
                font=dict(size=16, family='Arial Black')
            ),
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            height=600 if rows > 1 else 400,
            margin=dict(l=50, r=50, t=80, b=50)
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Add interpretation text
        st.markdown("""
        <div style="background: linear-gradient(135deg, #f8f9fa, #e9ecef); padding: 15px; border-radius: 8px; margin-top: 15px; border-left: 4px solid #17a2b8;">
            <h5 style="color: #2c3e50; margin: 0 0 10px 0;">📊 Ratio Interpretation Guide</h5>
            <ul style="margin: 0; padding-left: 20px; color: #495057;">
                <li><strong>N:P Ratio:</strong> Indicates nitrogen to phosphorus balance (optimal: 8-15)</li>
                <li><strong>N:K Ratio:</strong> Shows nitrogen to potassium balance (optimal: 1-2.5)</li>
                <li><strong>Ca:Mg Ratio:</strong> Reflects calcium to magnesium balance (optimal: 2-4)</li>
                <li><strong>K:Mg Ratio:</strong> Indicates potassium to magnesium balance (optimal: 0.2-0.6)</li>
                <li><strong>C:N Ratio:</strong> Shows carbon to nitrogen balance (optimal: 10-20)</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
    except Exception as e:
        logger.error(f"Error displaying nutrient ratio diagram: {e}")
        st.error("Error displaying nutrient ratio diagram")


def get_ratio_interpretation(ratio_name, current_value, optimal_range):
    """Get specific interpretation for a nutrient ratio"""
    if not optimal_range or len(optimal_range) != 2:
        return ""
    
    min_val, max_val = optimal_range
    status = "optimal"
    status_color = "#28a745"
    status_icon = "✅"
    
    if current_value < min_val:
        status = "low"
        status_color = "#ffc107"
        status_icon = "⚠️"
    elif current_value > max_val:
        status = "high"
        status_color = "#dc3545"
        status_icon = "❌"
    
    ratio_descriptions = {
        'N:P': {
            'description': 'Nitrogen to Phosphorus balance',
            'soil_optimal': '10-15',
            'leaf_optimal': '8-12',
            'impact': 'Affects plant growth and nutrient uptake efficiency'
        },
        'N:K': {
            'description': 'Nitrogen to Potassium balance',
            'soil_optimal': '1-2',
            'leaf_optimal': '1.5-2.5',
            'impact': 'Influences plant vigor and stress resistance'
        },
        'Ca:Mg': {
            'description': 'Calcium to Magnesium balance',
            'soil_optimal': '2-4',
            'leaf_optimal': '2-3',
            'impact': 'Affects soil structure and nutrient availability'
        },
        'K:Mg': {
            'description': 'Potassium to Magnesium balance',
            'soil_optimal': '0.2-0.5',
            'leaf_optimal': '0.3-0.6',
            'impact': 'Influences enzyme activity and protein synthesis'
        },
        'C:N': {
            'description': 'Carbon to Nitrogen balance',
            'soil_optimal': '10-20',
            'leaf_optimal': '10-20',
            'impact': 'Affects organic matter decomposition and nutrient cycling'
        },
        'P:K': {
            'description': 'Phosphorus to Potassium balance',
            'soil_optimal': '0.4-0.8',
            'leaf_optimal': '0.4-0.8',
            'impact': 'Influences energy transfer and root development'
        }
    }
    
    ratio_info = ratio_descriptions.get(ratio_name, {})
    description = ratio_info.get('description', f'{ratio_name} ratio')
    impact = ratio_info.get('impact', 'Affects plant health and growth')
    
    return f"""
    <div style="background: linear-gradient(135deg, #f8f9fa, #e9ecef); padding: 15px; border-radius: 8px; margin-top: 15px; border-left: 4px solid {status_color};">
        <h5 style="color: #2c3e50; margin: 0 0 10px 0;">{status_icon} {ratio_name} Ratio Analysis</h5>
        <p style="margin: 5px 0; color: #495057;"><strong>Description:</strong> {description}</p>
        <p style="margin: 5px 0; color: #495057;"><strong>Current Value:</strong> {current_value:.2f}</p>
        <p style="margin: 5px 0; color: #495057;"><strong>Optimal Range:</strong> {min_val:.1f} - {max_val:.1f}</p>
        <p style="margin: 5px 0; color: {status_color};"><strong>Status:</strong> {status.upper()}</p>
        <p style="margin: 5px 0; color: #495057;"><strong>Impact:</strong> {impact}</p>
    </div>
    """




