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
from utils.parsing_utils import _parse_raw_text_to_structured_json
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
            
            # Create enhanced progress display
            progress_container = st.container()
            with progress_container:
                progress_bar = st.progress(0)
                status_text = st.empty()
                time_estimate = st.empty()
                step_indicator = st.empty()
            
            # Process the new analysis with enhanced progress tracking
            results_data = process_new_analysis(st.session_state.analysis_data, progress_bar, status_text, time_estimate, step_indicator)
            
            # Clear the analysis_data from session state after processing
            del st.session_state.analysis_data
            
            # Always clear the progress container after analysis (success or failure)
            progress_container.empty()
            
            if results_data and results_data.get('success', False):
                # Enhanced success message
                st.balloons()
                st.success("🎉 Analysis completed successfully! Your comprehensive agricultural report is ready.")
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

        # Add raw data and average data tables before Executive Summary
        display_raw_data_tables(results_data)
        display_average_data_tables(results_data)

        # Executive Summary
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

def process_new_analysis(analysis_data, progress_bar=None, status_text=None, time_estimate=None, step_indicator=None):
    """Process new analysis data from uploaded files with enhanced progress tracking"""
    try:
        import time
        
        # Validate analysis_data is not None
        if analysis_data is None:
            logger.error("analysis_data is None")
            return {'success': False, 'message': 'No analysis data provided'}
        
        # Enhanced progress tracking with detailed steps
        total_steps = 8
        current_step = 1
        
        # Step 1: Initial validation
        if progress_bar:
            progress_bar.progress(5)
        if status_text:
            status_text.text("🔍 **Step 1/8:** Validating uploaded files...")
        if time_estimate:
            time_estimate.text("⏱️ Estimated time remaining: ~2-3 minutes")
        if step_indicator:
            step_indicator.text(f"📋 Progress: {current_step}/{total_steps} steps completed")
        
        # Extract data from uploaded files
        soil_file = analysis_data.get('soil_file')
        leaf_file = analysis_data.get('leaf_file')
        land_yield_data = analysis_data.get('land_yield_data', {})
        
        if not soil_file or not leaf_file:
            return {'success': False, 'message': 'Missing soil or leaf analysis files'}
        
        # Step 2: OCR Processing for Soil
        current_step = 2
        if progress_bar:
            progress_bar.progress(15)
        if status_text:
            status_text.text("🌱 **Step 2/8:** Extracting data from soil analysis report...")
        if time_estimate:
            time_estimate.text("⏱️ Estimated time remaining: ~2 minutes")
        if step_indicator:
            step_indicator.text(f"📋 Progress: {current_step}/{total_steps} steps completed")
        
        # Check if structured data is available from upload page (preferred)
        structured_soil_data = st.session_state.get('structured_soil_data', {})
        structured_leaf_data = st.session_state.get('structured_leaf_data', {})

        logger.info(f"Structured soil data available: {bool(structured_soil_data)}")
        logger.info(f"Structured leaf data available: {bool(structured_leaf_data)}")

        if structured_soil_data:
            logger.info(f"Soil data keys: {list(structured_soil_data.keys())}")
        if structured_leaf_data:
            logger.info(f"Leaf data keys: {list(structured_leaf_data.keys())}")

        # Handle structured data processing - can be partial
        soil_samples = []
        leaf_samples = []
        raw_soil_text = ""
        raw_leaf_text = ""

        # Process structured soil data if available
        if structured_soil_data:
            logger.info("Processing structured soil data")
            temp_soil_data = {'success': True, 'data': {'samples': []}}

            if 'Farm_Soil_Test_Data' in structured_soil_data:
                logger.info(f"Converting Farm_Soil_Test_Data with {len(structured_soil_data['Farm_Soil_Test_Data'])} samples")
                for sample_id, params in structured_soil_data['Farm_Soil_Test_Data'].items():
                    sample = {'sample_no': sample_id.replace('S', ''), 'lab_no': ''}
                    sample.update(params)
                    temp_soil_data['data']['samples'].append(sample)
            elif 'SP_Lab_Test_Report' in structured_soil_data:
                logger.info(f"Converting SP_Lab_Test_Report soil with {len(structured_soil_data['SP_Lab_Test_Report'])} samples")
                for sample_id, params in structured_soil_data['SP_Lab_Test_Report'].items():
                    sample = {'sample_no': sample_id.replace('S', '').replace('/', ''), 'lab_no': sample_id}
                    sample.update(params)
                    temp_soil_data['data']['samples'].append(sample)

            soil_samples = temp_soil_data['data']['samples']
            logger.info(f"Successfully converted {len(soil_samples)} soil samples from structured data")

        # Step 3: Processing Leaf Data
        current_step = 3
        if progress_bar:
            progress_bar.progress(25)
        if status_text:
            status_text.text("🍃 **Step 3/8:** Extracting data from leaf analysis report...")
        if time_estimate:
            time_estimate.text("⏱️ Estimated time remaining: ~1.5 minutes")
        if step_indicator:
            step_indicator.text(f"📋 Progress: {current_step}/{total_steps} steps completed")
        
        # Process structured leaf data if available
        if structured_leaf_data:
            logger.info("Processing structured leaf data")
            temp_leaf_data = {'success': True, 'data': {'samples': []}}

            if 'Farm_Leaf_Test_Data' in structured_leaf_data:
                logger.info(f"Converting Farm_Leaf_Test_Data with {len(structured_leaf_data['Farm_Leaf_Test_Data'])} samples")
                for sample_id, params in structured_leaf_data['Farm_Leaf_Test_Data'].items():
                    sample = {'sample_no': sample_id.replace('L', ''), 'lab_no': ''}
                    sample.update(params)
                    temp_leaf_data['data']['samples'].append(sample)
            elif 'SP_Lab_Test_Report' in structured_leaf_data:
                logger.info(f"Converting SP_Lab_Test_Report leaf with {len(structured_leaf_data['SP_Lab_Test_Report'])} samples")
                for sample_id, params in structured_leaf_data['SP_Lab_Test_Report'].items():
                    sample = {'sample_no': sample_id.replace('P', '').replace('/', ''), 'lab_no': sample_id}
                    sample.update(params)
                    temp_leaf_data['data']['samples'].append(sample)

            leaf_samples = temp_leaf_data['data']['samples']
            logger.info(f"Successfully converted {len(leaf_samples)} leaf samples from structured data")

        # Determine if we need OCR processing for missing data
        need_soil_ocr = len(soil_samples) == 0
        need_leaf_ocr = len(leaf_samples) == 0

        logger.info(f"Soil samples from structured data: {len(soil_samples)}, need OCR: {need_soil_ocr}")
        logger.info(f"Leaf samples from structured data: {len(leaf_samples)}, need OCR: {need_leaf_ocr}")

        if need_soil_ocr or need_leaf_ocr:
            # Step 4: OCR Processing
            current_step = 4
            if progress_bar:
                progress_bar.progress(40)
            if status_text:
                status_text.text("🔍 **Step 4/8:** Processing images with OCR technology...")
            if time_estimate:
                time_estimate.text("⏱️ Estimated time remaining: ~1 minute")
            if step_indicator:
                step_indicator.text(f"📋 Progress: {current_step}/{total_steps} steps completed")
            
            logger.info("Processing missing data through OCR")
        
        # Convert uploaded file to PIL Image for OCR processing
        from PIL import Image
        import tempfile
        import os
        
        # Parallel OCR processing for both soil and leaf (optimized)
        import concurrent.futures
        import threading
        
        def process_soil_ocr():
            if need_soil_ocr:
                file_ext = os.path.splitext(soil_file.name)[1].lower()
                if file_ext in ['.png', '.jpg', '.jpeg']:
                    with tempfile.NamedTemporaryFile(suffix=file_ext, delete=False) as tmp_file:
                        soil_image = Image.open(soil_file)
                        soil_image.save(tmp_file.name)
                        result = extract_data_from_image(tmp_file.name)
                        try:
                            os.unlink(tmp_file.name)
                        except (PermissionError, FileNotFoundError):
                            pass
                        return result
                else:
                    # For non-image files (PDF, Excel, etc.), save the file and let extract_data_from_image handle it
                    with tempfile.NamedTemporaryFile(suffix=file_ext or '.pdf', delete=False) as tmp_file:
                        tmp_file.write(soil_file.getvalue())
                        tmp_file.flush()  # Ensure data is written
                        result = extract_data_from_image(tmp_file.name)
                        try:
                            os.unlink(tmp_file.name)
                        except (PermissionError, FileNotFoundError):
                            pass
                        return result
            return None
        
        def process_leaf_ocr():
            if need_leaf_ocr:
                file_ext = os.path.splitext(leaf_file.name)[1].lower()
                if file_ext in ['.png', '.jpg', '.jpeg']:
                    with tempfile.NamedTemporaryFile(suffix=file_ext, delete=False) as tmp_file:
                        leaf_image = Image.open(leaf_file)
                        leaf_image.save(tmp_file.name)
                        result = extract_data_from_image(tmp_file.name)
                        try:
                            os.unlink(tmp_file.name)
                        except (PermissionError, FileNotFoundError):
                            pass
                        return result
                else:
                    # For non-image files (PDF, Excel, etc.), save the file and let extract_data_from_image handle it
                    with tempfile.NamedTemporaryFile(suffix=file_ext or '.pdf', delete=False) as tmp_file:
                        tmp_file.write(leaf_file.getvalue())
                        tmp_file.flush()  # Ensure data is written
                        result = extract_data_from_image(tmp_file.name)
                        try:
                            os.unlink(tmp_file.name)
                        except (PermissionError, FileNotFoundError):
                            pass
                        return result
            return None
        
        # Process both OCR operations in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            soil_future = executor.submit(process_soil_ocr)
            leaf_future = executor.submit(process_leaf_ocr)
            
            # Wait for both to complete
            soil_ocr_result = soil_future.result()
            leaf_ocr_result = leaf_future.result()

            # Process OCR results and merge with existing structured data
            if need_soil_ocr:
                if soil_ocr_result and isinstance(soil_ocr_result, dict):
                    logger.info("Processing soil OCR results")
                    # Extract samples from OCR result
                    if soil_ocr_result.get('tables') and len(soil_ocr_result['tables']) > 0:
                        ocr_soil_samples = soil_ocr_result['tables'][0].get('samples', [])
                        if ocr_soil_samples:
                            soil_samples.extend(ocr_soil_samples)
                            logger.info(f"Added {len(ocr_soil_samples)} soil samples from OCR")

                    # Extract raw text
                    if soil_ocr_result.get('raw_data', {}).get('text'):
                        raw_soil_text = soil_ocr_result['raw_data']['text']
                    elif soil_ocr_result.get('text'):
                        raw_soil_text = soil_ocr_result['text']
                else:
                    logger.warning("Soil OCR processing returned None or invalid result")

            if need_leaf_ocr:
                if leaf_ocr_result and isinstance(leaf_ocr_result, dict):
                    logger.info("Processing leaf OCR results")
                    # Extract samples from OCR result
                    if leaf_ocr_result.get('tables') and len(leaf_ocr_result['tables']) > 0:
                        ocr_leaf_samples = leaf_ocr_result['tables'][0].get('samples', [])
                        if ocr_leaf_samples:
                            leaf_samples.extend(ocr_leaf_samples)
                            logger.info(f"Added {len(ocr_leaf_samples)} leaf samples from OCR")

                    # Extract raw text
                    if leaf_ocr_result.get('raw_data', {}).get('text'):
                        raw_leaf_text = leaf_ocr_result['raw_data']['text']
                    elif leaf_ocr_result.get('text'):
                        raw_leaf_text = leaf_ocr_result['text']
                else:
                    logger.warning("Leaf OCR processing returned None or invalid result")

        # Log final sample counts
        logger.info(f"Final soil samples count: {len(soil_samples)}")
        logger.info(f"Final leaf samples count: {len(leaf_samples)}")

        # Create data structures for analysis
        soil_data = {'success': True, 'data': {'samples': soil_samples}}
        leaf_data = {'success': True, 'data': {'samples': leaf_samples}}

        # Extract raw text for analysis
        if not raw_soil_text and st.session_state.get('raw_soil_text'):
            raw_soil_text = st.session_state.raw_soil_text
        if not raw_leaf_text and st.session_state.get('raw_leaf_text'):
            raw_leaf_text = st.session_state.raw_leaf_text

        logger.info(f"Final data - Soil samples: {len(soil_samples)}, Leaf samples: {len(leaf_samples)}")

        # Validate that we have some data to work with
        if len(soil_samples) == 0 and len(leaf_samples) == 0:
            logger.error("No samples found from either structured data or OCR processing")
            st.error("❌ **Analysis Failed**: Unable to extract data from uploaded reports.")
            st.info("💡 **Tips for better results:**")
            st.info("• Ensure images are clear and well-lit")
            st.info("• Use high-resolution images (at least 300 DPI)")
            st.info("• Make sure text is readable and not distorted")
            st.info("• Try uploading PDF files instead of images")
            st.info("• Check that the reports contain readable tabular data")
            return {'success': False, 'message': 'No data could be extracted from uploaded files'}

        # Step 5: Data Validation
        current_step = 5
        if progress_bar:
            progress_bar.progress(55)
        if status_text:
            status_text.text("✅ **Step 5/8:** Validating extracted data...")
        if time_estimate:
            time_estimate.text("⏱️ Estimated time remaining: ~45 seconds")
        if step_indicator:
            step_indicator.text(f"📋 Progress: {current_step}/{total_steps} steps completed")
        
        # Get active prompt
        active_prompt = get_active_prompt()
        if not active_prompt:
            return {'success': False, 'message': 'No active analysis prompt found'}
        
        # Step 6: AI Analysis
        current_step = 6
        if progress_bar:
            progress_bar.progress(70)
        if status_text:
            status_text.text("🤖 **Step 6/8:** Running AI analysis on your data...")
        if time_estimate:
            time_estimate.text("⏱️ Estimated time remaining: ~30 seconds")
        if step_indicator:
            step_indicator.text(f"📋 Progress: {current_step}/{total_steps} steps completed")
        
        analysis_engine = AnalysisEngine()
        
        # Analysis processing
        
        # Transform OCR data structure to match analysis engine expectations
        # Convert parameter names from spaces to underscores for analysis engine compatibility
        transformed_soil_samples = []
        for sample in soil_samples:
            # Dynamic transformation - extract all available parameters
            transformed_sample = {
                'sample_no': sample.get('Sample No.', sample.get('Sample ID', sample.get('sample_id', 0))),
                'lab_no': sample.get('Lab No.', sample.get('lab_no', ''))
            }

            # Extract all numeric parameters dynamically
            for key, value in sample.items():
                if key not in ['Sample No.', 'Sample ID', 'sample_id', 'Lab No.', 'lab_no'] and value is not None:
                    # Try to convert to float, keep original if it fails
                    if isinstance(value, str):
                        try:
                            transformed_sample[key] = float(value) if value.strip() else 0.0
                        except (ValueError, TypeError):
                            transformed_sample[key] = value
                    elif isinstance(value, (int, float)):
                        transformed_sample[key] = float(value)
                    else:
                        transformed_sample[key] = value

            # Ensure we have the standard soil parameters mapped correctly
            soil_param_mappings = {
                'pH': ['pH', 'ph', 'PH'],
                'Nitrogen_%': ['Nitrogen %', 'N (%)', 'nitrogen', 'N'],
                'Organic_Carbon_%': ['Organic Carbon %', 'Org. C (%)', 'organic_carbon', 'Organic Matter'],
                'Total_P_mg_kg': ['Total P mg/kg', 'Total P (mg/kg)', 'total_p', 'P'],
                'Available_P_mg_kg': ['Available P mg/kg', 'Avail P (mg/kg)', 'available_p'],
                'Exchangeable_K_meq%': ['Exch. K meq%', 'Exchangeable K (meq%)', 'exchangeable_k', 'K'],
                'Exchangeable_Ca_meq%': ['Exch. Ca meq%', 'Exchangeable Ca (meq%)', 'exchangeable_ca', 'Ca'],
                'Exchangeable_Mg_meq%': ['Exch. Mg meq%', 'Exchangeable Mg (meq%)', 'exchangeable_mg', 'Mg'],
                'CEC_meq%': ['C.E.C meq%', 'CEC (meq%)', 'cec', 'CEC']
            }

            # Apply mappings for standard parameters
            for standard_param, possible_names in soil_param_mappings.items():
                if standard_param not in transformed_sample or transformed_sample[standard_param] == 0.0:
                    for param_name in possible_names:
                        if param_name in sample and sample[param_name] is not None:
                            try:
                                transformed_sample[standard_param] = float(sample[param_name]) if isinstance(sample[param_name], str) else sample[param_name]
                                break
                            except (ValueError, TypeError):
                                continue

            # Ensure all standard parameters exist with default values if not found
            for standard_param in soil_param_mappings.keys():
                if standard_param not in transformed_sample:
                    transformed_sample[standard_param] = 0.0

            transformed_soil_samples.append(transformed_sample)
        
        transformed_leaf_samples = []
        for sample in leaf_samples:
            # Dynamic transformation - extract all available parameters
            transformed_sample = {
                'sample_no': sample.get('Sample No.', sample.get('Sample ID', sample.get('sample_id', 0))),
                'lab_no': sample.get('Lab No.', sample.get('lab_no', ''))
            }

            # Handle structured data format (% Dry Matter and mg/kg Dry Matter)
            percent_dm = sample.get('% Dry Matter', sample.get('percent_dm', {}))
            mgkg_dm = sample.get('mg/kg Dry Matter', sample.get('mgkg_dm', {}))

            # Extract all parameters dynamically from different sources
            for key, value in sample.items():
                if key not in ['Sample No.', 'Sample ID', 'sample_id', 'Lab No.', 'lab_no', '% Dry Matter', 'mg/kg Dry Matter', 'percent_dm', 'mgkg_dm'] and value is not None:
                    # Try to convert to float, keep original if it fails
                    if isinstance(value, str):
                        try:
                            transformed_sample[key] = float(value) if value.strip() else 0.0
                        except (ValueError, TypeError):
                            transformed_sample[key] = value
                    elif isinstance(value, (int, float)):
                        transformed_sample[key] = float(value)
                    else:
                        transformed_sample[key] = value

            # Extract from structured format (% Dry Matter)
            for nutrient in ['N', 'P', 'K', 'Mg', 'Ca']:
                if nutrient in percent_dm and percent_dm[nutrient] is not None:
                    param_key = f'{nutrient}_%'
                    try:
                        transformed_sample[param_key] = float(percent_dm[nutrient]) if isinstance(percent_dm[nutrient], str) else percent_dm[nutrient]
                    except (ValueError, TypeError):
                        transformed_sample[param_key] = percent_dm[nutrient]

            # Extract from structured format (mg/kg Dry Matter)
            for nutrient in ['B', 'Cu', 'Zn', 'Fe', 'Mn']:
                if nutrient in mgkg_dm and mgkg_dm[nutrient] is not None:
                    param_key = f'{nutrient}_mg_kg'
                    try:
                        transformed_sample[param_key] = float(mgkg_dm[nutrient]) if isinstance(mgkg_dm[nutrient], str) else mgkg_dm[nutrient]
                    except (ValueError, TypeError):
                        transformed_sample[param_key] = mgkg_dm[nutrient]

            # Ensure we have the standard leaf parameters mapped correctly
            leaf_param_mappings = {
                'N_%': ['N (%)', 'nitrogen', 'N', 'N_%'],
                'P_%': ['P (%)', 'phosphorus', 'P', 'P_%'],
                'K_%': ['K (%)', 'potassium', 'K', 'K_%'],
                'Mg_%': ['Mg (%)', 'magnesium', 'Mg', 'Mg_%'],
                'Ca_%': ['Ca (%)', 'calcium', 'Ca', 'Ca_%'],
                'B_mg_kg': ['B (mg/kg)', 'boron', 'B', 'B_mg_kg'],
                'Cu_mg_kg': ['Cu (mg/kg)', 'copper', 'Cu', 'Cu_mg_kg'],
                'Zn_mg_kg': ['Zn (mg/kg)', 'zinc', 'Zn', 'Zn_mg_kg'],
                'Fe_mg_kg': ['Fe (mg/kg)', 'iron', 'Fe', 'Fe_mg_kg'],
                'Mn_mg_kg': ['Mn (mg/kg)', 'manganese', 'Mn', 'Mn_mg_kg']
            }

            # Apply mappings for standard parameters
            for standard_param, possible_names in leaf_param_mappings.items():
                if standard_param not in transformed_sample or transformed_sample[standard_param] == 0.0:
                    for param_name in possible_names:
                        if param_name in sample and sample[param_name] is not None:
                            try:
                                transformed_sample[standard_param] = float(sample[param_name]) if isinstance(sample[param_name], str) else sample[param_name]
                                break
                            except (ValueError, TypeError):
                                continue

            # Ensure all standard parameters exist with default values if not found
            for standard_param in leaf_param_mappings.keys():
                if standard_param not in transformed_sample:
                    transformed_sample[standard_param] = 0.0

            transformed_leaf_samples.append(transformed_sample)
        
        transformed_soil_data = {
            'success': soil_data.get('success', True),
            'data': {
                'samples': transformed_soil_samples,
                'total_samples': len(transformed_soil_samples)
            }
        }
        
        transformed_leaf_data = {
            'success': leaf_data.get('success', True),
            'data': {
                'samples': transformed_leaf_samples,
                'total_samples': len(transformed_leaf_samples)
            }
        }
        
        # Debug: Log the data being passed to analysis
        logger.info(f"🔍 Starting analysis with:")
        logger.info(f"  - Soil samples: {len(transformed_soil_data['data']['samples'])}")
        logger.info(f"  - Leaf samples: {len(transformed_leaf_data['data']['samples'])}")
        logger.info(f"  - First soil sample: {transformed_soil_data['data']['samples'][0] if transformed_soil_data['data']['samples'] else 'None'}")
        logger.info(f"  - First leaf sample: {transformed_leaf_data['data']['samples'][0] if transformed_leaf_data['data']['samples'] else 'None'}")
        
        try:
            analysis_results = analysis_engine.generate_comprehensive_analysis(
                soil_data=transformed_soil_data,
                leaf_data=transformed_leaf_data,
                land_yield_data=land_yield_data,
                prompt_text=active_prompt.get('prompt_text', ''),
                progress_callback=None
            )

            logger.info(f"✅ Analysis completed successfully")
            logger.info(f"🔍 Analysis results keys: {list(analysis_results.keys()) if analysis_results else 'None'}")
        except Exception as e:
            logger.error(f"❌ Analysis failed: {str(e)}")
            import traceback
            logger.error(f"❌ Analysis traceback: {traceback.format_exc()}")
            st.error(f"❌ **Analysis Failed**: {str(e)}")
            return
        
        # Step 7: Generating Insights
        current_step = 7
        if progress_bar:
            progress_bar.progress(85)
        if status_text:
            status_text.text("💡 **Step 7/8:** Generating insights and recommendations...")
        if time_estimate:
            time_estimate.text("⏱️ Estimated time remaining: ~15 seconds")
        if step_indicator:
            step_indicator.text(f"📋 Progress: {current_step}/{total_steps} steps completed")

        # Step 8: Saving Results
        current_step = 8
        if progress_bar:
            progress_bar.progress(95)
        if status_text:
            status_text.text("💾 **Step 8/8:** Saving your analysis results...")
        if time_estimate:
            time_estimate.text("⏱️ Almost done!")
        if step_indicator:
            step_indicator.text(f"📋 Progress: {current_step}/{total_steps} steps completed")
        
        user_email = st.session_state.get('user_email')
        if not user_email:
            return {'success': False, 'message': 'User email not found'}
        
        # Skip Firestore data preparation to avoid nested entity errors
        # Results will be displayed directly in the results page
        
        # Analysis completed
        
        # Add original OCR data to analysis results for raw data display
        analysis_results['raw_ocr_data'] = {
            'soil_data': {
                'success': soil_data.get('success', True),
                'samples': soil_samples,
                'total_samples': len(soil_samples),
                'tables': soil_data.get('tables', []),
                'raw_data': {'text': raw_soil_text} if raw_soil_text else {},
                'text': raw_soil_text
            },
            'leaf_data': {
                'success': leaf_data.get('success', True),
                'samples': leaf_samples,
                'total_samples': len(leaf_samples),
                'tables': leaf_data.get('tables', []),
                'raw_data': {'text': raw_leaf_text} if raw_leaf_text else {},
                'text': raw_leaf_text
            }
        }
        
        # Store analysis results in session state to avoid Firebase validation issues
        # This completely bypasses any Firebase serialization that might cause nested entity errors
        if 'stored_analysis_results' not in st.session_state:
            st.session_state.stored_analysis_results = {}
        
        result_id = f"local_{int(time.time())}"
        st.session_state.stored_analysis_results[result_id] = analysis_results
        
        # Final progress completion
        if progress_bar:
            progress_bar.progress(100)
        if status_text:
            status_text.text("✅ **Analysis Complete!** Your comprehensive report is ready.")
        if time_estimate:
            time_estimate.text("🎉 Done!")
        if step_indicator:
            step_indicator.text(f"📋 All {total_steps} steps completed successfully!")
        
        # Return data structure with analysis results included
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
            'created_at': datetime.now(),
            'analysis_results': analysis_results  # Include analysis results for raw data display
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

def parse_raw_text_comprehensive(raw_text: str, data_type: str) -> list:
    """
    Comprehensive raw text parsing with multiple fallback strategies.
    This function tries various approaches to extract structured data from raw OCR text.
    """
    import re
    import logging
    logger = logging.getLogger(__name__)

    logger.info(f"Starting comprehensive parsing for {data_type} data")
    logger.info(f"Raw text length: {len(raw_text)}")

    if not raw_text or len(raw_text.strip()) < 10:
        logger.warning("Raw text too short for parsing")
        return []

    samples = []

    try:
        # Strategy 1: Try the existing parsing function first
        parsed_data = _parse_raw_text_to_structured_json(raw_text)
        if parsed_data.get('samples') and len(parsed_data['samples']) > 0:
            logger.info(f"Strategy 1 successful: {len(parsed_data['samples'])} samples")
            return parsed_data['samples']

        # Strategy 2: Manual table parsing for common formats
        samples = parse_table_format(raw_text, data_type)
        if samples:
            logger.info(f"Strategy 2 successful: {len(samples)} samples")
            return samples

        # Strategy 3: Line-by-line parsing for simple formats
        samples = parse_line_by_line(raw_text, data_type)
        if samples:
            logger.info(f"Strategy 3 successful: {len(samples)} samples")
            return samples

        # Strategy 4: Keyword-based extraction
        samples = parse_keyword_based(raw_text, data_type)
        if samples:
            logger.info(f"Strategy 4 successful: {len(samples)} samples")
            return samples

    except Exception as e:
        logger.error(f"Error in comprehensive parsing: {str(e)}")

    logger.warning(f"No samples found with any parsing strategy for {data_type}")
    return samples


def parse_table_format(raw_text: str, data_type: str) -> list:
    """Parse table-like formatted text"""
    import re

    lines = [line.strip() for line in raw_text.split('\n') if line.strip()]
    if len(lines) < 2:
        return []

    # Look for header line and data lines
    header_line = None
    data_lines = []

    # Find the most likely header line (contains common parameter names)
    for i, line in enumerate(lines):
        line_lower = line.lower()
        if data_type == 'soil' and any(keyword in line_lower for keyword in ['ph', 'cec', 'nitrogen', 'phosphorus', 'potassium']):
            header_line = line
            data_lines = lines[i+1:]
            break
        elif data_type == 'leaf' and any(keyword in line_lower for keyword in ['nitrogen', 'phosphorus', 'potassium', 'magnesium', 'calcium']):
            header_line = line
            data_lines = lines[i+1:]
            break

    if not header_line:
        return []

    # Parse header to identify columns
    header_parts = re.split(r'\s+', header_line)
    logger.info(f"Detected header parts: {header_parts}")

    samples = []
    for line in data_lines[:20]:  # Limit to first 20 lines to avoid processing noise
        line = line.strip()
        if not line or len(line) < 10:  # Skip short lines
            continue

        # Split line into parts
        parts = re.split(r'\s+', line)
        if len(parts) >= len(header_parts) - 1:  # At least as many parts as headers minus sample ID
            sample = {}
            # Try to map parts to headers
            for i, part in enumerate(parts):
                if i < len(header_parts):
                    header = header_parts[i].strip()
                    # Clean up the value
                    value = part.strip()
                    if value and value != '-':
                        try:
                            # Try to convert to number if possible
                            if '.' in value or value.isdigit():
                                sample[header] = float(value)
                            else:
                                sample[header] = value
                        except ValueError:
                            sample[header] = value
            if sample:
                samples.append(sample)

    return samples


def parse_line_by_line(raw_text: str, data_type: str) -> list:
    """Parse text line by line looking for parameter-value pairs"""
    import re

    lines = [line.strip() for line in raw_text.split('\n') if line.strip()]
    samples = []

    current_sample = {}
    sample_id = None

    for line in lines:
        line_lower = line.lower()

        # Look for sample ID patterns
        sample_match = re.search(r'(S\d{3,4}|L\d{3,4}|Sample\s+\d+)', line, re.IGNORECASE)
        if sample_match:
            # Save previous sample if it exists
            if current_sample and sample_id:
                current_sample['sample_id'] = sample_id
                samples.append(current_sample)

            # Start new sample
            sample_id = sample_match.group(1)
            current_sample = {}

        # Look for parameter-value pairs
        # Common patterns: "Parameter: value", "Parameter = value", "Parameter value"
        param_patterns = [
            r'([A-Za-z][A-Za-z\s]+?):\s*([0-9.-]+)',  # "Parameter: value"
            r'([A-Za-z][A-Za-z\s]+?)=\s*([0-9.-]+)',  # "Parameter = value"
            r'([A-Za-z][A-Za-z\s]+?)\s+([0-9.-]+)',  # "Parameter value"
        ]

        for pattern in param_patterns:
            matches = re.findall(pattern, line, re.IGNORECASE)
            for match in matches:
                param, value = match
                param = param.strip().lower()

                # Map common parameter names
                param_mapping = {
                    'ph': 'pH',
                    'nitrogen': 'nitrogen',
                    'phosphorus': 'phosphorus',
                    'potassium': 'potassium',
                    'magnesium': 'magnesium',
                    'calcium': 'calcium',
                    'cec': 'cec',
                    'organic carbon': 'organic_carbon',
                    'total p': 'total_p',
                    'available p': 'available_p',
                    'exchangeable k': 'exchangeable_k',
                    'exchangeable ca': 'exchangeable_ca',
                    'exchangeable mg': 'exchangeable_mg'
                }

                mapped_param = param_mapping.get(param, param)
                try:
                    current_sample[mapped_param] = float(value)
                except ValueError:
                    current_sample[mapped_param] = value

    # Don't forget the last sample
    if current_sample and sample_id:
        current_sample['sample_id'] = sample_id
        samples.append(current_sample)

    return samples


def parse_keyword_based(raw_text: str, data_type: str) -> list:
    """Extract data using keyword patterns"""
    import re

    text_lower = raw_text.lower()
    samples = []

    # Define patterns for different data types
    if data_type == 'soil':
        patterns = {
            'pH': r'ph[:\s=]*([0-9.]+)',
            'nitrogen': r'nitrogen[:\s=]*([0-9.]+)',
            'organic_carbon': r'(?:organic carbon|org\.?\s*c)[:\s=]*([0-9.]+)',
            'total_p': r'(?:total p|total phosphorus)[:\s=]*([0-9.]+)',
            'available_p': r'(?:available p|avail p)[:\s=]*([0-9.]+)',
            'exchangeable_k': r'(?:exchangeable k|exch\.?\s*k)[:\s=]*([0-9.]+)',
            'exchangeable_ca': r'(?:exchangeable ca|exch\.?\s*ca)[:\s=]*([0-9.]+)',
            'exchangeable_mg': r'(?:exchangeable mg|exch\.?\s*mg)[:\s=]*([0-9.]+)',
            'cec': r'cec[:\s=]*([0-9.]+)'
        }
    else:  # leaf
        patterns = {
            'nitrogen': r'nitrogen[:\s=]*([0-9.]+)',
            'phosphorus': r'phosphorus[:\s=]*([0-9.]+)',
            'potassium': r'potassium[:\s=]*([0-9.]+)',
            'magnesium': r'magnesium[:\s=]*([0-9.]+)',
            'calcium': r'calcium[:\s=]*([0-9.]+)',
            'boron': r'boron[:\s=]*([0-9.]+)',
            'copper': r'copper[:\s=]*([0-9.]+)',
            'zinc': r'zinc[:\s=]*([0-9.]+)',
            'iron': r'iron[:\s=]*([0-9.]+)',
            'manganese': r'manganese[:\s=]*([0-9.]+)'
        }

    # Extract values using patterns
    extracted_data = {}
    for param, pattern in patterns.items():
        match = re.search(pattern, text_lower, re.IGNORECASE)
        if match:
            try:
                extracted_data[param] = float(match.group(1))
            except (ValueError, IndexError):
                pass

    if extracted_data:
        # Look for sample ID
        sample_match = re.search(r'(S\d{3,4}|L\d{3,4}|Sample\s+\d+)', raw_text, re.IGNORECASE)
        sample_id = sample_match.group(1) if sample_match else "Sample_1"

        sample = {'sample_id': sample_id}
        sample.update(extracted_data)
        samples.append(sample)

    return samples


def create_basic_samples_from_raw_text(raw_text: str, data_type: str) -> list:
    """
    Create basic sample structures from raw text when other parsing methods fail.
    This ensures analysis can proceed even with minimal data extraction.
    """
    import re
    import logging
    logger = logging.getLogger(__name__)

    logger.info(f"Creating basic samples from raw text for {data_type}")

    if not raw_text or len(raw_text.strip()) < 20:
        return []

    # Look for any numeric values in the text
    numbers = re.findall(r'(\d+\.?\d*)', raw_text)

    if not numbers:
        logger.warning("No numeric values found in raw text")
        return []

    # Create a basic sample with found numbers
    sample = {'sample_id': f'{data_type.title()}_Sample_1'}

    # For soil data, assign numbers to common parameters
    if data_type == 'soil':
        soil_params = ['pH', 'nitrogen', 'organic_carbon', 'total_p', 'available_p',
                      'exchangeable_k', 'exchangeable_ca', 'exchangeable_mg', 'cec']

        for i, param in enumerate(soil_params):
            if i < len(numbers):
                try:
                    sample[param] = float(numbers[i])
                except ValueError:
                    sample[param] = 0.0

    # For leaf data, assign numbers to common parameters
    elif data_type == 'leaf':
        leaf_params = ['nitrogen', 'phosphorus', 'potassium', 'magnesium', 'calcium',
                      'boron', 'copper', 'zinc', 'iron', 'manganese']

        for i, param in enumerate(leaf_params):
            if i < len(numbers):
                try:
                    sample[param] = float(numbers[i])
                except ValueError:
                    sample[param] = 0.0

    if len(sample) > 1:  # More than just sample_id
        logger.info(f"Created basic sample with {len(sample)-1} parameters")
        return [sample]
    else:
        logger.warning("Could not create meaningful sample from raw text")
        return []


# Raw Extracted Data section removed as requested

def process_html_tables(text):
    """Process HTML tables in text and convert them to proper Streamlit tables"""
    import re
    import pandas as pd
    
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        # Fallback if BeautifulSoup is not available
        logger.warning("BeautifulSoup not available, using regex fallback for table parsing")
        return process_html_tables_regex(text)
    
    # Find all HTML table blocks
    table_pattern = r'<tables>(.*?)</tables>'
    table_blocks = re.findall(table_pattern, text, re.DOTALL)
    
    processed_text = text
    
    for table_block in table_blocks:
        try:
            # Parse the HTML table
            soup = BeautifulSoup(table_block, 'html.parser')
            table = soup.find('table')
            
            if table:
                # Extract table title
                title = table.get('title', 'Table')
                
                # Extract headers
                thead = table.find('thead')
                headers = []
                if thead:
                    header_row = thead.find('tr')
                    if header_row:
                        headers = [th.get_text(strip=True) for th in header_row.find_all(['th', 'td'])]
                
                # Extract rows
                tbody = table.find('tbody')
                rows = []
                if tbody:
                    for tr in tbody.find_all('tr'):
                        row = [td.get_text(strip=True) for td in tr.find_all(['td', 'th'])]
                        if row:  # Only add non-empty rows
                            rows.append(row)
                
                # Create a styled HTML table
                if headers and rows:
                    # Create table HTML with proper styling
                    table_html = f"""
                    <div style="margin: 20px 0; overflow-x: auto;">
                        <h4 style="color: #2c3e50; margin-bottom: 15px; font-weight: 600;">{title}</h4>
                        <table style="width: 100%; border-collapse: collapse; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                            <thead>
                                <tr style="background: linear-gradient(135deg, #667eea, #764ba2); color: white;">
                    """
                    
                    # Add headers
                    for header in headers:
                        table_html += f'<th style="padding: 12px 15px; text-align: left; font-weight: 600; border-right: 1px solid rgba(255,255,255,0.2);">{header}</th>'
                    
                    table_html += """
                                </tr>
                            </thead>
                            <tbody>
                    """
                    
                    # Add rows
                    for i, row in enumerate(rows):
                        row_style = "background: #f8f9fa;" if i % 2 == 0 else "background: white;"
                        table_html += f'<tr style="{row_style}">'
                        for cell in row:
                            # Handle colspan if present
                            if cell == '' and len(row) < len(headers):
                                continue
                            table_html += f'<td style="padding: 10px 15px; border-right: 1px solid #e9ecef; border-bottom: 1px solid #e9ecef;">{cell}</td>'
                        table_html += '</tr>'
                    
                    table_html += """
                            </tbody>
                        </table>
                    </div>
                    """
                    
                    # Replace the original table block with the styled HTML
                    original_block = f'<tables>{table_block}</tables>'
                    processed_text = processed_text.replace(original_block, table_html)
                    
        except Exception as e:
            # If parsing fails, keep the original text
            logger.warning(f"Failed to parse HTML table: {str(e)}")
            continue
    
    return processed_text

def process_html_tables_regex(text):
    """Fallback function to process HTML tables using regex when BeautifulSoup is not available"""
    import re
    
    # Find all HTML table blocks
    table_pattern = r'<tables>(.*?)</tables>'
    table_blocks = re.findall(table_pattern, text, re.DOTALL)
    
    processed_text = text
    
    for table_block in table_blocks:
        try:
            # Extract table title
            title_match = re.search(r'<table[^>]*title="([^"]*)"', table_block)
            title = title_match.group(1) if title_match else "Table"
            
            # Extract headers
            header_pattern = r'<thead>.*?<tr>(.*?)</tr>.*?</thead>'
            header_match = re.search(header_pattern, table_block, re.DOTALL)
            headers = []
            if header_match:
                header_cells = re.findall(r'<t[hd][^>]*>(.*?)</t[hd]>', header_match.group(1))
                headers = [cell.strip() for cell in header_cells]
            
            # Extract rows
            row_pattern = r'<tbody>(.*?)</tbody>'
            tbody_match = re.search(row_pattern, table_block, re.DOTALL)
            rows = []
            if tbody_match:
                row_matches = re.findall(r'<tr>(.*?)</tr>', tbody_match.group(1), re.DOTALL)
                for row_match in row_matches:
                    cells = re.findall(r'<t[hd][^>]*>(.*?)</t[hd]>', row_match)
                    if cells:
                        rows.append([cell.strip() for cell in cells])
            
            # Create a styled HTML table
            if headers and rows:
                table_html = f"""
                <div style="margin: 20px 0; overflow-x: auto;">
                    <h4 style="color: #2c3e50; margin-bottom: 15px; font-weight: 600;">{title}</h4>
                    <table style="width: 100%; border-collapse: collapse; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                        <thead>
                            <tr style="background: linear-gradient(135deg, #667eea, #764ba2); color: white;">
                """
                
                # Add headers
                for header in headers:
                    table_html += f'<th style="padding: 12px 15px; text-align: left; font-weight: 600; border-right: 1px solid rgba(255,255,255,0.2);">{header}</th>'
                
                table_html += """
                            </tr>
                        </thead>
                        <tbody>
                """
                
                # Add rows
                for i, row in enumerate(rows):
                    row_style = "background: #f8f9fa;" if i % 2 == 0 else "background: white;"
                    table_html += f'<tr style="{row_style}">'
                    for cell in row:
                        table_html += f'<td style="padding: 10px 15px; border-right: 1px solid #e9ecef; border-bottom: 1px solid #e9ecef;">{cell}</td>'
                    table_html += '</tr>'
                
                table_html += """
                        </tbody>
                    </table>
                </div>
                """
                
                # Replace the original table block with the styled HTML
                original_block = f'<tables>{table_block}</tables>'
                processed_text = processed_text.replace(original_block, table_html)
                
        except Exception as e:
            # If parsing fails, keep the original text
            logger.warning(f"Failed to parse HTML table with regex: {str(e)}")
            continue
    
    return processed_text

def display_raw_soil_data(soil_data):
    """Display raw soil OCR data in tabular format"""
    if not soil_data or 'samples' not in soil_data:
        st.warning("📋 No soil data available.")
        return
    
    samples = soil_data['samples']
    if not samples:
        st.warning("📋 No soil samples found.")
        return
    
    # Create a DataFrame from the samples
    import pandas as pd
    
    # Convert samples to DataFrame
    df_data = []
    for sample in samples:
        row = {'Lab No.': sample.get('Lab No.', 'N/A')}
        # Add all parameters
        for key, value in sample.items():
            if key != 'Lab No.':
                row[key] = value
        df_data.append(row)
    
    if df_data:
        df = pd.DataFrame(df_data)
        st.dataframe(df, use_container_width=True)
        
        # Show summary
        st.info(f"📊 **Total Samples:** {len(samples)}")
    else:
        st.warning("📋 No soil data available.")

def display_raw_leaf_data(leaf_data):
    """Display raw leaf OCR data in tabular format"""
    if not leaf_data or 'samples' not in leaf_data:
        st.warning("📋 No leaf data available.")
        return
    
    samples = leaf_data['samples']
    if not samples:
        st.warning("📋 No leaf samples found.")
        return
    
    # Create a DataFrame from the samples
    import pandas as pd
    
    # Convert samples to DataFrame
    df_data = []
    for sample in samples:
        row = {'Lab No.': sample.get('Lab No.', 'N/A')}
        # Add all parameters
        for key, value in sample.items():
            if key != 'Lab No.':
                row[key] = value
        df_data.append(row)
    
    if df_data:
        df = pd.DataFrame(df_data)
        st.dataframe(df, use_container_width=True)
        
        # Show summary
        st.info(f"📊 **Total Samples:** {len(samples)}")
    else:
        st.warning("📋 No leaf data available.")

def calculate_parameter_averages(data_samples, data_type):
    """Calculate averages for each parameter across all samples"""
    if not data_samples or not isinstance(data_samples, list):
        return {}

    # Collect all parameter values
    parameter_values = {}
    total_samples = len(data_samples)

    for sample in data_samples:
        if isinstance(sample, dict):
            for param, value in sample.items():
                # Skip non-numeric parameters and sample identifiers
                if param.lower() in ['sample_id', 'lab_no', 'sample_no', 'id'] or not isinstance(value, (int, float)):
                    continue

                if param not in parameter_values:
                    parameter_values[param] = []
                parameter_values[param].append(value)

    # Calculate averages
    averages = {}
    for param, values in parameter_values.items():
        if values:
            try:
                averages[param] = sum(values) / len(values)
            except (TypeError, ZeroDivisionError):
                continue

    return averages

def display_soil_data_table_with_averages(soil_samples, soil_averages):
    """Display soil data table with parameter averages and MPOB standards"""
    if not soil_samples:
        return

    st.markdown("#### 🌱 Soil Analysis Data")
    st.markdown(f"**Total Samples:** {len(soil_samples)}")

    # Create DataFrame for soil samples
    soil_df = pd.DataFrame(soil_samples)

    # Keep only numeric columns for the table
    numeric_cols = []
    for col in soil_df.columns:
        if col not in ['sample_no', 'lab_no'] and soil_df[col].dtype in ['int64', 'float64']:
            numeric_cols.append(col)

    if numeric_cols:
        # Create table with samples and averages
        table_data = []
        for i, sample in enumerate(soil_samples):
            row = {'Sample': f"S{i+1:03d}"}
            for col in numeric_cols:
                value = sample.get(col, 0)
                row[col] = f"{value:.3f}" if isinstance(value, (int, float)) else str(value)
            table_data.append(row)

        # Add averages row
        if soil_averages:
            avg_row = {'Sample': '**Average**'}
            for col in numeric_cols:
                if col in soil_averages:
                    avg_row[col] = f"**{soil_averages[col]:.3f}**"
                else:
                    avg_row[col] = "**N/A**"
            table_data.append(avg_row)

        # Display the table
        df_table = pd.DataFrame(table_data)
        st.dataframe(df_table, use_container_width=True)

        # Display parameter averages with MPOB standards
        if soil_averages:
            st.markdown("**📊 Parameter Averages & MPOB Standards:**")

            # Soil parameter mappings with accurate MPOB standards for Malaysian oil palm
            soil_standards = {
                'pH': {'optimal': '4.5-6.0', 'low': '<4.5', 'high': '>6.0'},
                'Nitrogen %': {'optimal': '0.15-0.25', 'low': '<0.15', 'high': '>0.25'},
                'Organic Carbon %': {'optimal': '1.5-2.5', 'low': '<1.5', 'high': '>2.5'},
                'Total P mg/kg': {'optimal': '15-25', 'low': '<15', 'high': '>25'},
                'Available P mg/kg': {'optimal': '10-20', 'low': '<10', 'high': '>20'},
                'Exch. K meq%': {'optimal': '0.20-0.40', 'low': '<0.20', 'high': '>0.40'},
                'Exch. Ca meq%': {'optimal': '2.0-4.0', 'low': '<2.0', 'high': '>4.0'},
                'Exch. Mg meq%': {'optimal': '0.6-1.2', 'low': '<0.6', 'high': '>1.2'},
                'C.E.C meq%': {'optimal': '15-25', 'low': '<15', 'high': '>25'}
            }

            cols = st.columns(2)
            with cols[0]:
                st.markdown("**Basic Parameters:**")
                for param in ['pH', 'Organic Carbon %', 'C.E.C meq%']:
                    if param in soil_averages:
                        avg_val = soil_averages[param]
                        status = "✅ Optimal"
                        if param in soil_standards:
                            try:
                                optimal_min = float(soil_standards[param]['optimal'].split('-')[0])
                                optimal_max = float(soil_standards[param]['optimal'].split('-')[1])
                                if avg_val < optimal_min:
                                    status = "⚠️ Low"
                                elif avg_val > optimal_max:
                                    status = "⚠️ High"
                            except:
                                # Fallback to low/high thresholds
                                try:
                                    low_threshold = float(soil_standards[param]['low'].replace('<', ''))
                                    high_threshold = float(soil_standards[param]['high'].replace('>', ''))
                                    if avg_val < low_threshold:
                                        status = "⚠️ Low"
                                    elif avg_val > high_threshold:
                                        status = "⚠️ High"
                                except:
                                    pass
                        st.markdown(f"• **{param}:** {avg_val:.3f} {status}")

            with cols[1]:
                st.markdown("**Nutrient Parameters:**")
                for param in ['Nitrogen %', 'Total P mg/kg', 'Available P mg/kg', 'Exch. K meq%', 'Exch. Ca meq%', 'Exch. Mg meq%']:
                    if param in soil_averages:
                        avg_val = soil_averages[param]
                        status = "✅ Optimal"
                        if param in soil_standards:
                            try:
                                optimal_min = float(soil_standards[param]['optimal'].split('-')[0])
                                optimal_max = float(soil_standards[param]['optimal'].split('-')[1])
                                if avg_val < optimal_min:
                                    status = "⚠️ Low"
                                elif avg_val > optimal_max:
                                    status = "⚠️ High"
                            except:
                                pass
                        st.markdown(f"• **{param}:** {avg_val:.3f} {status}")

def display_leaf_data_table_with_averages(leaf_samples, leaf_averages):
    """Display leaf data table with parameter averages and MPOB standards"""
    if not leaf_samples:
        return

    st.markdown("#### 🍃 Leaf Analysis Data")
    st.markdown(f"**Total Samples:** {len(leaf_samples)}")

    # Create DataFrame for leaf samples
    leaf_df = pd.DataFrame(leaf_samples)

    # Keep only numeric columns for the table
    numeric_cols = []
    for col in leaf_df.columns:
        if col not in ['sample_no', 'lab_no'] and leaf_df[col].dtype in ['int64', 'float64']:
            numeric_cols.append(col)

    if numeric_cols:
        # Create table with samples and averages
        table_data = []
        for i, sample in enumerate(leaf_samples):
            row = {'Sample': f"L{i+1:03d}"}
            for col in numeric_cols:
                value = sample.get(col, 0)
                row[col] = f"{value:.3f}" if isinstance(value, (int, float)) else str(value)
            table_data.append(row)

        # Add averages row
        if leaf_averages:
            avg_row = {'Sample': '**Average**'}
            for col in numeric_cols:
                if col in leaf_averages:
                    avg_row[col] = f"**{leaf_averages[col]:.3f}**"
                else:
                    avg_row[col] = "**N/A**"
            table_data.append(avg_row)

        # Display the table
        df_table = pd.DataFrame(table_data)
        st.dataframe(df_table, use_container_width=True)

        # Display parameter averages with MPOB standards
        if leaf_averages:
            st.markdown("**📊 Parameter Averages & MPOB Standards:**")

            # Leaf parameter mappings with accurate MPOB standards for Malaysian oil palm (mature fronds)
            leaf_standards = {
                'N': {'optimal': '2.4-2.8', 'low': '<2.2', 'high': '>3.0'},
                'P': {'optimal': '0.14-0.20', 'low': '<0.12', 'high': '>0.25'},
                'K': {'optimal': '0.9-1.3', 'low': '<0.8', 'high': '>1.5'},
                'Mg': {'optimal': '0.25-0.45', 'low': '<0.20', 'high': '>0.50'},
                'Ca': {'optimal': '0.5-0.9', 'low': '<0.4', 'high': '>1.0'},
                'B': {'optimal': '18-28', 'low': '<15', 'high': '>35'},
                'Cu': {'optimal': '8-18', 'low': '<6', 'high': '>25'},
                'Zn': {'optimal': '18-35', 'low': '<15', 'high': '>45'}
            }

            cols = st.columns(2)
            with cols[0]:
                st.markdown("**Macronutrients:**")
                for param in ['N', 'P', 'K', 'Mg', 'Ca']:
                    if param in leaf_averages:
                        avg_val = leaf_averages[param]
                        status = "✅ Optimal"
                        if param in leaf_standards:
                            try:
                                optimal_min = float(leaf_standards[param]['optimal'].split('-')[0])
                                optimal_max = float(leaf_standards[param]['optimal'].split('-')[1])
                                if avg_val < optimal_min:
                                    status = "⚠️ Low"
                                elif avg_val > optimal_max:
                                    status = "⚠️ High"
                            except:
                                pass
                        st.markdown(f"• **{param} (%):** {avg_val:.3f} {status}")

            with cols[1]:
                st.markdown("**Micronutrients:**")
                for param in ['B', 'Cu', 'Zn']:
                    if param in leaf_averages:
                        avg_val = leaf_averages[param]
                        status = "✅ Optimal"
                        if param in leaf_standards:
                            try:
                                optimal_min = float(leaf_standards[param]['optimal'].split('-')[0])
                                optimal_max = float(leaf_standards[param]['optimal'].split('-')[1])
                                if avg_val < optimal_min:
                                    status = "⚠️ Low"
                                elif avg_val > optimal_max:
                                    status = "⚠️ High"
                            except:
                                pass
                        st.markdown(f"• **{param} (mg/kg):** {avg_val:.3f} {status}")


def format_raw_text_as_table(raw_text, data_type):
    """Format raw OCR text into a clean HTML table structure"""
    if not raw_text:
        return None

    try:
        # Clean and normalize the text
        lines = [line.strip() for line in raw_text.split('\n') if line.strip()]

        if not lines:
            return None

        # Detect data type and set appropriate headers
        if data_type.lower() == 'soil':
            title = "🌱 Farm Soil Test Data"
            headers = ["Sample ID", "pH", "N (%)", "Org. C (%)", "Total P (mg/kg)",
                      "Avail P (mg/kg)", "Exch. K (meq%)", "Exch. Ca (meq%)",
                      "Exch. Mg (meq%)", "CEC (meq%)"]
        else:  # leaf data
            title = "🍃 Farm Leaf Test Data"
            headers = ["Sample ID", "N (%)", "P (%)", "K (%)", "Mg (%)", "Ca (%)",
                      "B (mg/kg)", "Cu (mg/kg)", "Zn (mg/kg)", "Fe (mg/kg)", "Mn (mg/kg)"]

        # Parse data rows - look for lines that might contain sample data
        data_rows = []
        for line in lines:
            # Skip lines that are likely headers or metadata
            if any(keyword.lower() in line.lower() for keyword in [
                'sample', 'parameter', 'analysis', 'report', 'date', 'lab',
                'test', 'method', 'unit', 'range', 'standard', 'mpob'
            ]):
                continue

            # Try to split by common delimiters
            parts = []
            if '\t' in line:
                parts = line.split('\t')
            elif ',' in line:
                parts = line.split(',')
            elif '|' in line:
                parts = line.split('|')
            elif len(line.split()) >= 2:
                # Try to extract numeric values
                words = line.split()
                parts = []
                current_part = ""
                for word in words:
                    if word.replace('.', '').replace('-', '').isdigit() or '.' in word:
                        if current_part:
                            parts.append(current_part.strip())
                        parts.append(word.strip())
                        current_part = ""
                    else:
                        if current_part:
                            current_part += " "
                        current_part += word

                if current_part:
                    parts.append(current_part.strip())

            # Clean and validate parts
            parts = [p.strip() for p in parts if p.strip()]

            # Only add rows that have reasonable data (at least 2 parts, first might be sample ID)
            if len(parts) >= 2 and len(parts) <= len(headers):
                # Pad with empty strings if needed
                while len(parts) < len(headers):
                    parts.append("")
                data_rows.append(parts[:len(headers)])  # Don't exceed header count

        # Limit to first 20 rows to avoid overwhelming display
        data_rows = data_rows[:20]

        if not data_rows:
            return None

        # Create HTML table
        table_html = f"""
        <div style="margin: 20px 0; overflow-x: auto;">
            <h4 style="color: #2c3e50; margin-bottom: 15px; font-weight: 600;">{title}</h4>
            <table style="width: 100%; border-collapse: collapse; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                <thead>
                    <tr style="background: linear-gradient(135deg, #667eea, #764ba2); color: white;">
        """

        # Add headers
        for header in headers:
            table_html += f'<th style="padding: 12px 8px; text-align: center; font-weight: 600; border-right: 1px solid rgba(255,255,255,0.2); font-size: 12px;">{header}</th>'

        table_html += """
                    </tr>
                </thead>
                <tbody>
        """

        # Add data rows
        for i, row in enumerate(data_rows):
            row_style = "background: #f8f9fa;" if i % 2 == 0 else "background: white;"
            table_html += f'<tr style="{row_style}">'
            for cell in row:
                table_html += f'<td style="padding: 8px 6px; border-right: 1px solid #e9ecef; border-bottom: 1px solid #e9ecef; text-align: center; font-size: 11px;">{cell}</td>'
            table_html += '</tr>'

        table_html += """
                </tbody>
            </table>
        </div>
        """

        return table_html

    except Exception as e:
        st.warning(f"Could not format {data_type} data as table: {str(e)}")
        return None


def display_raw_ocr_text(results_data):
    """Display the raw OCR text that was extracted from uploaded files with parameter averages"""
    st.markdown("---")
    st.markdown("## 📄 Raw OCR Text Extracted")

    analysis_results = get_analysis_results_from_data(results_data)
    raw_ocr_data = analysis_results.get('raw_ocr_data', {})

    soil_raw_text = ""
    leaf_raw_text = ""
    soil_samples = []
    leaf_samples = []

    # Try to get raw text and samples from different sources
    if raw_ocr_data:
        if 'soil_data' in raw_ocr_data:
            soil_data = raw_ocr_data['soil_data']
            if soil_data.get('raw_data', {}).get('text'):
                soil_raw_text = soil_data['raw_data']['text']
            if soil_data.get('samples'):
                soil_samples = soil_data['samples']
        if 'leaf_data' in raw_ocr_data:
            leaf_data = raw_ocr_data['leaf_data']
            if leaf_data.get('raw_data', {}).get('text'):
                leaf_raw_text = leaf_data['raw_data']['text']
            if leaf_data.get('samples'):
                leaf_samples = leaf_data['samples']

    # Fallback to direct results data
    if not soil_raw_text and results_data.get('soil_data', {}).get('raw_data', {}).get('text'):
        soil_raw_text = results_data['soil_data']['raw_data']['text']
    if not leaf_raw_text and results_data.get('leaf_data', {}).get('raw_data', {}).get('text'):
        leaf_raw_text = results_data['leaf_data']['raw_data']['text']

    # Additional fallback to raw_data.text (direct text field)
    if not soil_raw_text and results_data.get('soil_data', {}).get('text'):
        soil_raw_text = results_data['soil_data']['text']
    if not leaf_raw_text and results_data.get('leaf_data', {}).get('text'):
        leaf_raw_text = results_data['leaf_data']['text']

    # Get samples from results_data if not found in raw_ocr_data
    if not soil_samples and results_data.get('soil_data', {}).get('samples'):
        soil_samples = results_data['soil_data']['samples']
    if not leaf_samples and results_data.get('leaf_data', {}).get('samples'):
        leaf_samples = results_data['leaf_data']['samples']

    # Display Raw Data Tables and Parameter Averages from Structured Data
    if soil_samples or leaf_samples:
        st.markdown("### 📊 Raw Data Analysis")

        # Create and display soil data table with averages
        if soil_samples:
            soil_averages = calculate_parameter_averages(soil_samples, 'soil')
            display_soil_data_table_with_averages(soil_samples, soil_averages)

        # Create and display leaf data table with averages
        if leaf_samples:
            leaf_averages = calculate_parameter_averages(leaf_samples, 'leaf')
            display_leaf_data_table_with_averages(leaf_samples, leaf_averages)

    # Display formatted tables first
    if soil_raw_text:
        soil_table = format_raw_text_as_table(soil_raw_text, 'soil')
        if soil_table:
            st.markdown("### 📊 Soil Data Table")
            st.markdown(soil_table, unsafe_allow_html=True)

    if leaf_raw_text:
        leaf_table = format_raw_text_as_table(leaf_raw_text, 'leaf')
        if leaf_table:
            st.markdown("### 📊 Leaf Data Table")
            st.markdown(leaf_table, unsafe_allow_html=True)

    # Display the original raw OCR text
    if soil_raw_text:
        with st.expander("🌱 Raw Soil OCR Text", expanded=False):
            st.text_area("Extracted Text", soil_raw_text, height=300, disabled=True)
            st.info("💡 This is the exact raw text extracted from your soil analysis report by OCR.")
            st.markdown("**Text Statistics:**")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Length", f"{len(soil_raw_text)} chars")
            with col2:
                st.metric("Lines", len(soil_raw_text.split('\n')))
            with col3:
                st.metric("Words", len(soil_raw_text.split()))

    if leaf_raw_text:
        with st.expander("🍃 Raw Leaf OCR Text", expanded=False):
            st.text_area("Extracted Text", leaf_raw_text, height=300, disabled=True)
            st.info("💡 This is the exact raw text extracted from your leaf analysis report by OCR.")
            st.markdown("**Text Statistics:**")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Length", f"{len(leaf_raw_text)} chars")
            with col2:
                st.metric("Lines", len(leaf_raw_text.split('\n')))
            with col3:
                st.metric("Words", len(leaf_raw_text.split()))

    # If no raw text found, show debug information
    if not soil_raw_text and not leaf_raw_text:
        st.warning("⚠️ No raw OCR text found in the analysis results.")
        st.info("This might indicate that the OCR processing failed or the data structure is different.")
        with st.expander("🔍 Debug: Available Data Structures", expanded=False):
            st.write("**Results data keys:**", list(results_data.keys()))
            if analysis_results:
                st.write("**Analysis results keys:**", list(analysis_results.keys()))
                if 'raw_ocr_data' in analysis_results:
                    st.write("**Raw OCR data keys:**", list(analysis_results['raw_ocr_data'].keys()))
        st.info("📋 No raw OCR text available. The analysis may have used structured table data instead.")

# Soil data table function removed as requested


# Table functions removed as requested

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
    
    if len(critical_issues) > 0:
        critical_params = [issue['parameter'] for issue in critical_issues]
        if len(critical_params) == 1:
            summary_sentences.append(f"Critical nutritional deficiency identified in {critical_params[0]} poses immediate threats to palm productivity and requires urgent corrective measures within the next 30-60 days.")
        else:
            params_list = ", ".join(critical_params[:-1]) + f" and {critical_params[-1]}"
            summary_sentences.append(f"Critical nutritional deficiencies identified in {len(critical_issues)} parameters ({params_list}) pose immediate threats to palm productivity and require urgent corrective measures within the next 30-60 days.")
    else:
        summary_sentences.append("No critical nutritional deficiencies were identified, indicating generally adequate nutrient availability for palm productivity.")
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

    if total_steps == 0:
        st.warning("⚠️ No step-by-step analysis results found. This may indicate an issue with the analysis process.")
    
    if not step_results:
        # Also display other analysis components if available
        display_analysis_components(analysis_results)
        return
    
    # Display each step in organized blocks instead of tabs
    if len(step_results) > 0:
        # Display each step as a separate block with clear visual separation
        for i, current_step_result in enumerate(step_results):
            # Ensure current_step_result is a dictionary
            if not isinstance(current_step_result, dict):
                logger.error(f"Step {i+1} current_step_result is not a dictionary: {type(current_step_result)}")
                st.error(f"❌ Error: Step {i+1} data is not in the expected format")
                continue
            
            step_number = current_step_result.get('step_number', i+1)
            step_title = current_step_result.get('step_title', f'Step {step_number}')
            
            # Create a visual separator between steps
            if i > 0:
                st.markdown("---")
            
            # Display the step result in a block format
            display_step_block(current_step_result, step_number, step_title)
    
    # After all steps are displayed, ensure Step 6 forecast graph is shown
    ensure_forecast_graph_displayed(step_results, results_data)
    
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

def ensure_forecast_graph_displayed(step_results, results_data):
    """Ensure Step 6 forecast graph is always displayed"""
    try:
        # Check if Step 6 exists and should show forecast graph
        if len(step_results) >= 6:
            step_6_result = step_results[5]  # 0-indexed, so 5 is step 6
            step_6_number = step_6_result.get('step_number', 6)

            # Check if forecast graph should be shown and hasn't been displayed yet
            if step_6_number == 6 and should_show_forecast_graph(step_6_result) and has_yield_forecast_data(results_data):
                st.markdown("---")
                st.markdown("## 📈 Step 6: Yield Forecast & Projections")
                st.info("📊 **5-Year Yield Forecast**: This comprehensive forecast shows your expected yield performance over the next 5 years under different investment scenarios.")
                display_forecast_graph_content(results_data)
    except Exception as e:
        logger.warning(f"Could not ensure forecast graph display: {e}")
        # Fallback: always show forecast graph for Step 6 if data is available
        try:
            if has_yield_forecast_data(results_data):
                st.markdown("---")
                st.markdown("## 📈 Yield Forecast & Projections")
                display_forecast_graph_content(results_data)
        except Exception as e2:
            logger.warning(f"Fallback forecast graph display failed: {e2}")

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
        st.markdown("### 📋 Executive Summary")

        # Create an enhanced container for the summary
        st.markdown(
            """
            <div style="background: linear-gradient(135deg, #e8f5e8 0%, #f0f8f0 100%); border: 2px solid #28a745; border-radius: 12px; padding: 20px; margin: 15px 0; box-shadow: 0 4px 12px rgba(40, 167, 69, 0.15);">
                <div style="display: flex; align-items: center; margin-bottom: 15px;">
                    <div style="background: #28a745; color: white; padding: 8px 12px; border-radius: 20px; font-weight: bold; font-size: 14px; margin-right: 15px;">
                        📋 SUMMARY
                    </div>
                    <div style="flex: 1; height: 2px; background: linear-gradient(90deg, #28a745, transparent);"></div>
                </div>
            """,
            unsafe_allow_html=True
        )

        summary_text = analysis_data['summary']
        if isinstance(summary_text, str) and summary_text.strip():
            # Clean up the summary text
            import re
            clean_summary = summary_text.strip()

            # Remove excessive formatting that might confuse users
            clean_summary = re.sub(r'\*\*\s*\*\*', '', clean_summary)  # Remove empty bold
            clean_summary = re.sub(r'_\s*_', '', clean_summary)  # Remove empty italic

            # Split into sentences for better readability
            sentences = re.split(r'(?<=[.!?])\s+', clean_summary)
            if len(sentences) > 3:
                # Group sentences into paragraphs for better readability
                paragraphs = []
                current_paragraph = ""
                for i, sentence in enumerate(sentences):
                    current_paragraph += sentence + " "
                    if (i + 1) % 2 == 0 or i == len(sentences) - 1:
                        paragraphs.append(current_paragraph.strip())
                        current_paragraph = ""

                clean_summary = "\n\n".join(paragraphs)
            else:
                clean_summary = " ".join(sentences)

            st.markdown(
                f'<div style="background: rgba(255,255,255,0.9); padding: 15px; border-radius: 8px; border-left: 4px solid #28a745; box-shadow: 0 2px 6px rgba(0,0,0,0.1);">'
                f'<p style="margin: 0; font-size: 16px; line-height: 1.7; color: #155724; font-weight: 500;">{clean_summary}</p>'
                f'</div>',
                unsafe_allow_html=True
            )

        # Close the enhanced container
        st.markdown("</div>", unsafe_allow_html=True)
    
        
    # 3. DETAILED ANALYSIS SECTION - Show if available
    if 'detailed_analysis' in analysis_data and analysis_data['detailed_analysis']:
        st.markdown("### 📋 Detailed Analysis")

        # Create an enhanced container for the detailed analysis
        st.markdown(
            """
            <div style="background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%); border: 1px solid #dee2e6; border-radius: 10px; padding: 20px; margin: 15px 0; box-shadow: 0 4px 8px rgba(0,0,0,0.05);">
            """,
            unsafe_allow_html=True
        )

        detailed_text = analysis_data['detailed_analysis']
        
        # Ensure detailed_text is a string
        if isinstance(detailed_text, dict):
            detailed_text = str(detailed_text)
        elif not isinstance(detailed_text, str):
            detailed_text = str(detailed_text) if detailed_text is not None else "No detailed analysis available"
        
        # Clean and process the text
        import re
        # Remove QuickChart URLs but keep the visual comparison text
        detailed_text = re.sub(r'!\[.*?\]\(https://quickchart\.io.*?\)', '', detailed_text, flags=re.DOTALL)
        
        # Process HTML tables and other content
        processed_text = process_html_tables(detailed_text)
        
        # Split into paragraphs for better formatting
        paragraphs = processed_text.split('\n\n') if '\n\n' in processed_text else [processed_text]
        
        for i, paragraph in enumerate(paragraphs):
            if isinstance(paragraph, str) and paragraph.strip():
                # Skip empty paragraphs
                if paragraph.strip() == '':
                    continue
                    
                # Check if this paragraph contains a table (already processed)
                if '<table' in paragraph and '</table>' in paragraph:
                    # This is an HTML table, render it directly
                    st.markdown(paragraph, unsafe_allow_html=True)
                else:
                    # Clean up the paragraph text
                    clean_paragraph = paragraph.strip()

                    # Remove excessive markdown formatting that might confuse users
                    clean_paragraph = re.sub(r'\*\*\s*\*\*', '', clean_paragraph)  # Remove empty bold
                    clean_paragraph = re.sub(r'_\s*_', '', clean_paragraph)  # Remove empty italic

                    # Add numbering for key points if they start with bullet points
                    if clean_paragraph.startswith('- ') or clean_paragraph.startswith('• '):
                        # Convert bullet points to numbered list for better readability
                        lines = clean_paragraph.split('\n')
                        numbered_lines = []
                        for j, line in enumerate(lines, 1):
                            line = line.strip()
                            if line.startswith('- ') or line.startswith('• '):
                                line = line[2:]  # Remove bullet
                                numbered_lines.append(f"{j}. {line}")
                            else:
                                numbered_lines.append(line)
                        clean_paragraph = '\n'.join(numbered_lines)

                    # Regular text paragraph with enhanced formatting
                    st.markdown(
                        f'<div style="margin-bottom: 15px; padding: 12px; background: rgba(255,255,255,0.8); border-left: 3px solid #007bff; border-radius: 6px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">'
                        f'<p style="margin: 0; line-height: 1.7; font-size: 15px; color: #2c3e50; font-weight: 400;">{clean_paragraph}</p>'
                        f'</div>',
                        unsafe_allow_html=True
                    )

        # Close the enhanced container
        st.markdown("</div>", unsafe_allow_html=True)
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
        st.markdown("### 🔍 Expert Interpretations")

        # Create an enhanced container for interpretations
        st.markdown(
            """
            <div style="background: linear-gradient(135deg, #e7f3ff 0%, #f0f8ff 100%); border: 2px solid #007bff; border-radius: 12px; padding: 20px; margin: 15px 0; box-shadow: 0 4px 12px rgba(0, 123, 255, 0.15);">
                <div style="display: flex; align-items: center; margin-bottom: 15px;">
                    <div style="background: #007bff; color: white; padding: 8px 12px; border-radius: 20px; font-weight: bold; font-size: 14px; margin-right: 15px;">
                        🔍 ANALYSIS
                    </div>
                    <div style="flex: 1; height: 2px; background: linear-gradient(90deg, #007bff, transparent);"></div>
                </div>
            """,
            unsafe_allow_html=True
        )

        for idx, interpretation in enumerate(analysis_data['interpretations'], 1):
            if interpretation and interpretation.strip():
                # Remove any existing "Interpretation X:" prefix to avoid duplication
                clean_interpretation = interpretation.strip()
                if clean_interpretation.startswith(f"Interpretation {idx}:"):
                    clean_interpretation = clean_interpretation.replace(f"Interpretation {idx}:", "").strip()
                elif clean_interpretation.startswith(f"Detailed interpretation {idx}"):
                    clean_interpretation = clean_interpretation.replace(f"Detailed interpretation {idx}", "").strip()
                
                # Clean up the interpretation text
                import re
                clean_interpretation = re.sub(r'\*\*\s*\*\*', '', clean_interpretation)  # Remove empty bold
                clean_interpretation = re.sub(r'_\s*_', '', clean_interpretation)  # Remove empty italic
                
                st.markdown(
                    f'<div style="margin-bottom: 12px; padding: 15px; background: rgba(255,255,255,0.9); border-radius: 8px; border-left: 4px solid #007bff; box-shadow: 0 2px 6px rgba(0,0,0,0.1);">'
                    f'<div style="display: flex; align-items: flex-start; margin-bottom: 8px;">'
                    f'<div style="background: #007bff; color: white; padding: 4px 8px; border-radius: 12px; font-weight: bold; font-size: 12px; margin-right: 10px; flex-shrink: 0;">{idx}</div>'
                    f'<div style="flex: 1;">'
                    f'<p style="margin: 0; font-size: 15px; line-height: 1.6; color: #2c3e50; font-weight: 500;">{clean_interpretation}</p>'
                    f'</div>'
                    f'</div>'
                    f'</div>',
                    unsafe_allow_html=True
                )

        # Close the enhanced container
        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("")
    
    # 6. ANALYSIS RESULTS SECTION - Show actual LLM results (renamed from Additional Information)
    # This section shows the main analysis results from the LLM
    excluded_keys = set(['summary', 'key_findings', 'detailed_analysis', 'formatted_analysis', 'step_number', 'step_title', 'step_description', 'visualizations', 'yield_forecast', 'references', 'search_timestamp', 'prompt_instructions', 'tables', 'interpretations', 'data_quality'])
    other_fields = [k for k in analysis_data.keys() if k not in excluded_keys and analysis_data.get(k) is not None and analysis_data.get(k) != ""]
    
    if other_fields:
        st.markdown("### 📊 Additional Analysis Results")

        # Create an enhanced container for additional results
        st.markdown(
            """
            <div style="background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%); border: 1px solid #dee2e6; border-radius: 10px; padding: 20px; margin: 15px 0; box-shadow: 0 4px 8px rgba(0,0,0,0.05);">
            """,
            unsafe_allow_html=True
        )

        for key in other_fields:
            value = analysis_data.get(key)
            title = key.replace('_', ' ').title()
            
            if isinstance(value, dict) and value:
                st.markdown(f"**{title}:**")
                for sub_k, sub_v in value.items():
                    if sub_v is not None and sub_v != "":
                        st.markdown(f"- **{sub_k.replace('_',' ').title()}:** {sub_v}")
            elif isinstance(value, list) and value:
                # Special handling for recommendations
                if key.lower() in ['recommendations', 'recommendation']:
                    st.markdown("### 💡 Solution Recommendations")
                    for idx, item in enumerate(value, 1):
                        if isinstance(item, dict):
                            # Enhanced recommendation display
                            action = item.get('action', '')
                            timeline = item.get('timeline', '')
                            cost_estimate = item.get('cost_estimate', '')
                            expected_impact = item.get('expected_impact', '')
                            success_indicators = item.get('success_indicators', '')

                            st.markdown(f"**Recommendation {idx}:** {action}")
                            if timeline:
                                st.markdown(f"⏰ **Timeline:** {timeline}")
                            if cost_estimate:
                                st.markdown(f"💰 **Cost Estimate:** {cost_estimate}")
                            if expected_impact:
                                st.markdown(f"📈 **Expected Impact:** {expected_impact}")
                            if success_indicators:
                                st.markdown(f"✅ **Success Indicators:** {success_indicators}")
                            st.markdown("---")
                        else:
                            st.markdown(f"**Recommendation {idx}:** {item}")
                else:
                    st.markdown(f"**{title}:**")
                    for idx, item in enumerate(value, 1):
                        if isinstance(item, (dict, list)):
                            if key.lower() not in ['recommendations', 'recommendation']:
                                st.markdown(f"- **{title} {idx}:**")
                            # Convert dict/list to clean structured text
                            if isinstance(item, dict):
                                for k, v in item.items():
                                    if v is not None and v != "":
                                        st.markdown(f"  • **{k.replace('_', ' ').title()}:** {v}")
                            elif isinstance(item, list):
                                for i, sub_item in enumerate(item, 1):
                                    st.markdown(f"  • Item {i}: {sub_item}")
                        else:
                            if key.lower() not in ['recommendations', 'recommendation']:
                                st.markdown(f"- {item}")
                            else:
                                st.markdown(f"**Recommendation {idx}:** {item}")
            elif isinstance(value, str) and value.strip():
                st.markdown(f"**{title}:** {value}")
            st.markdown("")
    
        # Close the enhanced container
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Display visualizations for all steps - ensure all content is shown
    try:
        display_all_step_content(step_result, step_number)
    except Exception as e:
        logger.error(f"Error calling display_all_step_content for step {step_number}: {e}")
        st.info(f"📊 Step {step_number} content will be displayed by the enhanced analysis system.")

# Removed duplicate function - using the enhanced version below

def create_issues_visualization(detailed_text):
    """Create a visualization of identified issues"""
    try:
        import re

        # Extract issues from text
        issues = []
        issue_patterns = [
            r'Issue Title:\s*([^\n]+)',
            r'([A-Z][^.!?]*issue[^.!?]*)',
            r'([A-Z][^.!?]*problem[^.!?]*)'
        ]

        for pattern in issue_patterns:
            matches = re.findall(pattern, detailed_text, re.IGNORECASE)
            issues.extend(matches)

        if issues:
            # Create a simple bar chart of issues
            import plotly.graph_objects as go

            fig = go.Figure()

            # Create dummy data for visualization
            issue_counts = {}
            for issue in issues[:5]:  # Limit to 5 issues
                issue_name = issue[:30] + "..." if len(issue) > 30 else issue
                issue_counts[issue_name] = 1

            fig.add_trace(go.Bar(
                x=list(issue_counts.keys()),
                y=list(issue_counts.values()),
                marker_color='#dc3545',
                name='Identified Issues'
            ))

            fig.update_layout(
                title="🔍 Key Issues Identified",
                xaxis_title="Issue Type",
                yaxis_title="Count",
                height=400,
                showlegend=False
            )

            return {
                'type': 'plotly_chart',
                'data': fig,
                'title': 'Key Issues Analysis',
                'subtitle': 'Summary of major issues identified in the analysis'
            }

        return None

    except Exception as e:
        logger.warning(f"Could not create issues visualization: {e}")
        return None

def create_recommendations_visualization(detailed_text):
    """Create a visualization of recommendations"""
    try:
        import re

        # Extract recommendations from text
        recommendations = []
        rec_patterns = [
            r'Recommendation Title:\s*([^\n]+)',
            r'([A-Z][^.!?]*recommend[^.!?]*)',
            r'([A-Z][^.!?]*solution[^.!?]*)'
        ]

        for pattern in rec_patterns:
            matches = re.findall(pattern, detailed_text, re.IGNORECASE)
            recommendations.extend(matches)

        if recommendations:
            # Create a simple bar chart of recommendations
            import plotly.graph_objects as go

            fig = go.Figure()

            # Create dummy data for visualization
            rec_counts = {}
            for rec in recommendations[:5]:  # Limit to 5 recommendations
                rec_name = rec[:30] + "..." if len(rec) > 30 else rec
                rec_counts[rec_name] = 1

            fig.add_trace(go.Bar(
                x=list(rec_counts.keys()),
                y=list(rec_counts.values()),
                marker_color='#28a745',
                name='Recommendations'
            ))

            fig.update_layout(
                title="💡 Key Recommendations",
                xaxis_title="Recommendation Type",
                yaxis_title="Count",
                height=400,
                showlegend=False
            )

            return {
                'type': 'plotly_chart',
                'data': fig,
                'title': 'Recommendations Summary',
                'subtitle': 'Key recommendations for improving agricultural performance'
            }

        return None

    except Exception as e:
        logger.warning(f"Could not create recommendations visualization: {e}")
        return None

def display_single_step_result(step_result, step_number):
    """Legacy function - redirects to enhanced display"""
    display_enhanced_step_result(step_result, step_number)

def display_data_table(table_data, title):
    """Display a data table with proper formatting"""
    try:
        if not table_data or 'headers' not in table_data or 'rows' not in table_data:
            st.warning(f"No valid table data found for {title}")
            return
        
        headers = table_data['headers']
        rows = table_data['rows']
        
        if not headers or not rows:
            st.warning(f"Empty table data for {title}")
            return
        
        # Create a DataFrame for better display
        import pandas as pd
        
        # Convert rows to DataFrame
        df = pd.DataFrame(rows, columns=headers)
        
        # Display the table
        st.markdown(f"### {title}")
        st.dataframe(df, use_container_width=True)
        
    except Exception as e:
        logger.error(f"Error displaying table {title}: {e}")
        st.error(f"Error displaying table {title}")

def display_all_step_content(step_result, step_number):
    """Ensure all step content (visualizations, tables, graphs) is displayed with proper structure"""
    try:
        # Ensure parameters are correct types
        if not isinstance(step_result, dict):
            logger.error(f"step_result is not a dictionary: {type(step_result)}, value: {step_result}")
            return

        if not isinstance(step_number, int):
            try:
                step_number = int(step_number)
            except (ValueError, TypeError):
                logger.error(f"step_number is not a valid integer: {type(step_number)}, value: {step_number}")
                step_number = 0

        analysis_data = step_result

        # 1. Display VISUALIZATIONS section if available
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
                                display_visualization(viz_data, i, step_number)
                    elif isinstance(visualizations, list):
                        for i, viz in enumerate(visualizations, 1):
                            if isinstance(viz, dict) and 'type' in viz:
                                display_visualization(viz, i, step_number)
                except Exception as e:
                    logger.error(f"Error displaying visualizations for step {step_number}: {e}")
                    st.error(f"Error displaying visualizations for Step {step_number}")

        # 2. Generate and display contextual visualizations if no existing ones
        if step_number == 1:  # Step 1 gets special MPOB comparison bar graphs
            if 'visualizations' not in analysis_data or not analysis_data['visualizations']:
                # Generate MPOB comparison bar graphs for Step 1
                pass  # This is handled by the main Step 1 display function

        # 3. Display FORECAST GRAPH for Step 6
        if step_number == 6 and should_show_forecast_graph(step_result):
            # This is handled by the ensure_forecast_graph_displayed function
            pass

        # 4. Generate additional contextual visualizations based on step content
        logger.info(f"Calling generate_contextual_visualizations with step_result type: {type(step_result)}, analysis_data type: {type(analysis_data)}")
        try:
            # Ensure parameters are in correct format before calling
            if isinstance(step_result, dict) and isinstance(analysis_data, dict) and isinstance(step_number, int):
                # Use the correct parameter order: step_result, analysis_data
                step_result_with_number = step_result.copy()
                step_result_with_number['step_number'] = step_number
                contextual_visualizations = generate_contextual_visualizations(step_result_with_number, analysis_data)
            else:
                logger.warning(f"Invalid parameter types for generate_contextual_visualizations: step_result={type(step_result)}, analysis_data={type(analysis_data)}, step_number={type(step_number)}")
                contextual_visualizations = None
        except Exception as e:
            logger.error(f"Error calling generate_contextual_visualizations: {e}")
            contextual_visualizations = None

        try:
            if contextual_visualizations and isinstance(analysis_data, dict):
                if 'visualizations' not in analysis_data or not analysis_data['visualizations']:
                    st.markdown("""<div style="background: linear-gradient(135deg, #17a2b8, #20c997); padding: 20px; border-radius: 12px; margin-bottom: 25px; box-shadow: 0 4px 15px rgba(0,0,0,0.1);">
                        <h4 style="color: white; margin: 0; font-size: 20px; font-weight: 600;">📊 Data Visualizations</h4>
                    </div>""", unsafe_allow_html=True)

                for i, viz_data in enumerate(contextual_visualizations, 1):
                    if viz_data and isinstance(viz_data, dict):
                        try:
                            display_visualization(viz_data, i, step_number)
                        except Exception as e:
                            logger.error(f"Error displaying visualization {i} for step {step_number}: {e}")
                            logger.warning(f"Could not display all step content for step {step_number}: {e}")
                            st.info(f"📊 Step {step_number} visualizations and content will be displayed by the enhanced analysis system.")
        except Exception as e:
            logger.error(f"Error processing contextual visualizations: {e}")

        # Close the try block for display_all_step_content function
    except Exception as e:
        logger.error(f"Error in display_all_step_content: {e}")
        st.warning(f"Some content for step {step_number} could not be displayed.")

    # End of display_enhanced_step_result function


# Temporarily commented out to resolve import issues - function moved below

def create_plotly_figure(viz_data):
    """Convert visualization data structure to Plotly figure"""
    try:
        import plotly.graph_objects as go
        import plotly.express as px
        
        viz_type = viz_data.get('type', '')
        data = viz_data.get('data', {})
        options = viz_data.get('options', {})
        
        if viz_type == 'bar_chart':
            fig = go.Figure()
            
            categories = data.get('categories', [])
            series = data.get('series', [])
            
            for serie in series:
                fig.add_trace(go.Bar(
                    name=serie.get('name', ''),
                    x=categories,
                    y=serie.get('data', []),
                    marker_color=serie.get('color', '#3498db')
                ))
            
            fig.update_layout(
                title=viz_data.get('title', ''),
                xaxis_title=options.get('x_axis_title', ''),
                yaxis_title=options.get('y_axis_title', ''),
                showlegend=options.get('show_legend', True),
                template='plotly_white',
                height=400
            )
            
            if options.get('show_grid', True):
                fig.update_xaxes(showgrid=True)
                fig.update_yaxes(showgrid=True)
            
            return fig
            
        elif viz_type == 'line_chart':
            fig = go.Figure()
            
            categories = data.get('categories', [])
            series = data.get('series', [])
            
            for serie in series:
                fig.add_trace(go.Scatter(
                    name=serie.get('name', ''),
                    x=categories,
                    y=serie.get('data', []),
                    mode='lines+markers',
                    line=dict(color=serie.get('color', '#3498db'))
                ))
            
            fig.update_layout(
                title=viz_data.get('title', ''),
                xaxis_title=options.get('x_axis_title', ''),
                yaxis_title=options.get('y_axis_title', ''),
                showlegend=options.get('show_legend', True),
                template='plotly_white',
                height=400
            )
            
            return fig
            
        elif viz_type == 'pie_chart':
            labels = data.get('labels', [])
            values = data.get('values', [])
            colors = data.get('colors', [])
            
            fig = go.Figure(data=[go.Pie(
                labels=labels,
                values=values,
                marker_colors=colors if colors else None
            )])
            
            fig.update_layout(
                title=viz_data.get('title', ''),
                template='plotly_white',
                height=400
            )
            
            return fig
            
        return None
        
    except Exception as e:
        logger.error(f"Error creating Plotly figure: {e}")
        return None

def display_visualization(viz_data, viz_number, step_number=None):
    """Display visualization data using Streamlit and Plotly"""
    if not viz_data or not isinstance(viz_data, dict):
        return
    
    try:
        # Display visualization title
        title = viz_data.get('title', f'Visualization {viz_number}')
        st.markdown(f"#### {title}")
        
        # Display subtitle if available
        subtitle = viz_data.get('subtitle', '')
        if subtitle:
            st.markdown(f"*{subtitle}*")
        
        # Handle different visualization types
        viz_type = viz_data.get('type', 'plotly')
        
        if viz_type == 'plotly' and 'figure' in viz_data:
            # Display Plotly figure directly
            st.plotly_chart(viz_data['figure'], use_container_width=True)
        
        elif viz_type in ['bar_chart', 'line_chart', 'pie_chart']:
            # Convert data structure to Plotly figure
            fig = create_plotly_figure(viz_data)
            if fig:
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning(f"Could not create {viz_type} visualization")
        
        elif viz_type == 'dataframe' and 'data' in viz_data:
            # Display DataFrame
            st.dataframe(viz_data['data'], use_container_width=True)
        
        elif viz_type == 'metric' and 'metrics' in viz_data:
            # Display metrics
            metrics = viz_data['metrics']
            if isinstance(metrics, list) and len(metrics) > 0:
                cols = st.columns(len(metrics))
                for i, metric in enumerate(metrics):
                    with cols[i]:
                        st.metric(
                            label=metric.get('label', ''),
                            value=metric.get('value', ''),
                            delta=metric.get('delta', None)
                        )
        
        elif viz_type == 'html' and 'content' in viz_data:
            # Display HTML content
            st.markdown(viz_data['content'], unsafe_allow_html=True)
        
        else:
            # Fallback: try to display as JSON if no specific type matches
            st.json(viz_data)
            
    except Exception as e:
        logger.error(f"Error displaying visualization {viz_number}: {e}")
        st.error(f"Error displaying visualization: {str(e)}")

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
    
    # Always show for Step 1, or if visual keywords detected (including Step 2)
    return step_number == 1 or has_visual_keywords

def generate_contextual_visualizations(step_result, analysis_data):
    """Generate contextual visualizations based on step content and visual keywords"""
    try:
        logger.info(f"generate_contextual_visualizations (2nd version) called with step_result type: {type(step_result)}, analysis_data type: {type(analysis_data)}")

        # Handle parameter swapping - if step_result is an integer and analysis_data is a dict, swap them
        if isinstance(step_result, int) and isinstance(analysis_data, dict):
            logger.warning("Parameters appear to be swapped in 2nd version, correcting...")
            temp = step_result
            step_result = analysis_data
            analysis_data = temp

        # Ensure step_result is a dictionary
        if not isinstance(step_result, dict):
            logger.error(f"step_result is not a dictionary after correction: {type(step_result)}, value: {step_result}")
            return []
        
        # Ensure analysis_data is a dictionary
        if not isinstance(analysis_data, dict):
            logger.error(f"analysis_data is not a dictionary after correction: {type(analysis_data)}, value: {analysis_data}")
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
        
        # Common nutrients to compare - mapping soil to leaf parameter names
        nutrient_mapping = {
            'Nitrogen %': {'soil': 'Nitrogen %', 'leaf': 'N', 'display': 'Nitrogen (%)'},
            'Phosphorus': {'soil': 'Total P mg/kg', 'leaf': 'P', 'display': 'Phosphorus'},
            'Potassium': {'soil': 'K cmol/kg', 'leaf': 'K', 'display': 'Potassium'},
            'Magnesium': {'soil': 'Mg cmol/kg', 'leaf': 'Mg', 'display': 'Magnesium'},
            'Calcium': {'soil': 'Ca cmol/kg', 'leaf': 'Ca', 'display': 'Calcium'}
        }
        
        for nutrient_info in nutrient_mapping.values():
            soil_key = nutrient_info['soil']
            leaf_key = nutrient_info['leaf']
            display_name = nutrient_info['display']
            
            if soil_key in soil_stats and leaf_key in leaf_stats:
                soil_avg = soil_stats[soil_key].get('average', 0)
                leaf_avg = leaf_stats[leaf_key].get('average', 0)
                
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
    
    step_number = step_result.get('step_number', 0)

    # Step 6 (Yield Forecast & Projections) MUST always show the forecast graph
    if step_number == 6:
        return True
    
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
                
                for key, value in data.items():
                    st.markdown(f"**{key}:** {type(value)} - {str(value)[:100]}{'...' if len(str(value)) > 100 else ''}")
                
            else:
                st.warning(f"⚠️ Bar chart data is not a dictionary. Received: {type(data)}")
            
            # Show the actual data structure in clean format
            if isinstance(data, dict):
                st.markdown("**Chart Data:**")
                for k, v in data.items():
                    st.markdown(f"• **{k}:** {v}")
            else:
                st.markdown(f"**Chart Data:** {str(data)}")
    except ImportError:
        st.info("Plotly not available for chart display")
    except Exception as e:
        logger.error(f"Error displaying bar chart: {e}")
        st.error(f"Error displaying bar chart: {str(e)}")
        # Show data in clean format instead of JSON
        if isinstance(data, dict):
            st.markdown("**Debug Data:**")
            for k, v in data.items():
                st.markdown(f"• **{k}:** {v}")
        else:
            st.markdown(f"**Debug Data:** {str(data)}")

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
        
        # Check for Chart.js style format: {'labels': [...], 'datasets': [...]}
        elif 'labels' in data and 'datasets' in data:
            labels = data['labels']
            datasets = data['datasets']

            if isinstance(datasets, list) and len(datasets) > 0:
                fig = go.Figure()

                for i, dataset in enumerate(datasets):
                    if isinstance(dataset, dict) and 'data' in dataset:
                        dataset_name = dataset.get('label', f'Dataset {i+1}')
                        dataset_data = dataset['data']
                        dataset_color = dataset.get('borderColor', f'hsl({i*60}, 70%, 50%)')

                        # Extract color from borderColor if it's a string
                        if isinstance(dataset_color, str) and dataset_color.startswith('#'):
                            color = dataset_color
                        else:
                            color = f'hsl({i*60}, 70%, 50%)'

                        fig.add_trace(go.Scatter(
                            x=labels,
                            y=dataset_data,
                            mode='lines+markers',
                            name=dataset_name,
                            line=dict(
                                color=color,
                                width=3,
                                shape='spline'
                            ),
                            marker=dict(
                                size=8,
                                color=color,
                                line=dict(width=2, color='#FFFFFF')
                            ),
                            hovertemplate=f'<b>{dataset_name}:</b> %{{y}}<br><b>X:</b> %{{x}}<extra></extra>'
                        ))

                fig.update_layout(
                    title=dict(
                        text=title,
                        x=0.5,
                        font=dict(size=16, color='#2E7D32')
                    ),
                    xaxis_title="Time Period",
                    yaxis_title="Yield (tonnes/ha)",
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(size=12),
                    height=400,
                    hovermode='x unified',
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
    
    # 3. DETAILED ANALYSIS SECTION - Enhanced Professional Display
    if 'detailed_analysis' in analysis_data and analysis_data['detailed_analysis']:
        st.markdown("### 📋 Detailed Analysis")

        # Professional header styling
        st.markdown("""
        <div style="background: linear-gradient(135deg, #667eea, #764ba2); padding: 15px; border-radius: 10px; margin-bottom: 20px;">
            <h4 style="color: white; margin: 0; font-size: 18px; font-weight: 600;">
                🔍 Comprehensive Parameter Analysis & Recommendations
            </h4>
            <p style="color: #f0f0f0; margin: 5px 0 0 0; font-size: 14px;">
                Detailed evaluation of your soil and leaf parameters with expert recommendations
            </p>
        </div>
        """, unsafe_allow_html=True)

        detailed_text = analysis_data['detailed_analysis']
        
        if isinstance(detailed_text, dict):
            detailed_text = str(detailed_text)
        elif not isinstance(detailed_text, str):
            detailed_text = str(detailed_text) if detailed_text is not None else "No detailed analysis available"
        
        # Split into logical sections for better readability
        if '\n\n' in detailed_text:
            paragraphs = detailed_text.split('\n\n')
        elif '\n' in detailed_text:
            paragraphs = detailed_text.split('\n')
        else:
            paragraphs = [detailed_text]

        for i, paragraph in enumerate(paragraphs):
            if isinstance(paragraph, str) and paragraph.strip():
                # Determine section type for styling
                if any(keyword in paragraph.lower() for keyword in ['recommendation', 'action', 'solution']):
                    bg_color = "#d4edda"  # Light green for recommendations
                    border_color = "#28a745"
                    icon = "💡"
                elif any(keyword in paragraph.lower() for keyword in ['issue', 'problem', 'deficient', 'low']):
                    bg_color = "#f8d7da"  # Light red for issues
                    border_color = "#dc3545"
                    icon = "⚠️"
                elif any(keyword in paragraph.lower() for keyword in ['optimal', 'good', 'excellent', 'within range']):
                    bg_color = "#d1ecf1"  # Light blue for positive results
                    border_color = "#17a2b8"
                    icon = "✅"
                else:
                    bg_color = "#f8f9fa"  # Light gray for general info
                    border_color = "#6c757d"
                    icon = "📊"

                st.markdown(
                    f'<div style="margin-bottom: 15px; padding: 18px; background: {bg_color}; border-left: 4px solid {border_color}; border-radius: 8px; box-shadow: 0 2px 6px rgba(0,0,0,0.08);">'
                    f'<div style="display: flex; align-items: flex-start;">'
                    f'<span style="font-size: 20px; margin-right: 10px;">{icon}</span>'
                    f'<div style="flex: 1;">'
                    f'<p style="margin: 0; line-height: 1.7; font-size: 16px; color: #2c3e50; font-weight: 400;">{paragraph.strip()}</p>'
                    f'</div>'
                    f'</div>'
                    f'</div>',
                    unsafe_allow_html=True
                )
    
    # 4. NUTRIENT STATUS TABLES - This is the key addition
    display_nutrient_status_tables(analysis_data)
    
    # 4.5. DATA ECHO TABLE - Complete Parameter Analysis
    display_data_echo_table(analysis_data)
    
    # 5. DETAILED TABLES SECTION
    st.markdown("""<div style="background: linear-gradient(135deg, #6c757d, #495057); padding: 20px; border-radius: 12px; margin-bottom: 25px; box-shadow: 0 4px 15px rgba(0,0,0,0.1);">
        <h4 style="color: white; margin: 0; font-size: 20px; font-weight: 600;">📊 Detailed Tables</h4>
    </div>""", unsafe_allow_html=True)

    tables_displayed = False

    # Display tables from LLM response
    if 'tables' in analysis_data and analysis_data['tables']:
        tables = analysis_data['tables']
        if isinstance(tables, list):
            for table in tables:
                if isinstance(table, dict) and 'title' in table:
                    display_table(table)
                    tables_displayed = True
        elif isinstance(tables, dict):
            for table_key, table_data in tables.items():
                if isinstance(table_data, dict) and 'title' in table_data:
                    display_table(table_data)
                    tables_displayed = True

    # If no tables from LLM, generate comprehensive tables from data
    if not tables_displayed:
        generate_comprehensive_tables(analysis_data)
    
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

    # 6.5. SOIL & LEAF NUTRIENT STATUS BAR GRAPHS
    display_nutrient_status_bar_graphs(analysis_data)

def generate_comprehensive_tables(analysis_data):
    """Generate comprehensive detailed tables from data when LLM doesn't provide them"""
    try:
        # Get soil and leaf data
        soil_data = None
        leaf_data = None

        # Try multiple locations for data
        if 'analysis_results' in analysis_data and 'raw_ocr_data' in analysis_data['analysis_results']:
            raw_ocr = analysis_data['analysis_results']['raw_ocr_data']
            if 'soil_data' in raw_ocr:
                soil_data = raw_ocr['soil_data']
            if 'leaf_data' in raw_ocr:
                leaf_data = raw_ocr['leaf_data']

        if not soil_data and 'raw_data' in analysis_data and 'soil_parameters' in analysis_data['raw_data']:
            soil_data = analysis_data['raw_data']['soil_parameters']
        if not leaf_data and 'raw_data' in analysis_data and 'leaf_parameters' in analysis_data['raw_data']:
            leaf_data = analysis_data['raw_data']['leaf_parameters']

        # Generate soil parameters detailed table
        if soil_data and 'samples' in soil_data and soil_data['samples']:
            create_detailed_parameter_table(soil_data['samples'], 'Soil Parameters Detailed Analysis', 'Soil', '🌱')

        # Generate leaf parameters detailed table
        if leaf_data and 'samples' in leaf_data and leaf_data['samples']:
            create_detailed_parameter_table(leaf_data['samples'], 'Leaf Parameters Detailed Analysis', 'Leaf', '🍃')

        # Generate MPOB compliance table
        generate_mpob_compliance_table(analysis_data)

        # Generate recommendations priority table
        generate_recommendations_priority_table(analysis_data)

    except Exception as e:
        logger.warning(f"Could not generate comprehensive tables: {e}")
        st.info("📊 Detailed analysis tables will be generated by the AI in subsequent steps.")

def create_detailed_parameter_table(samples, title, param_type, icon):
    """Create a detailed parameter analysis table"""
    try:
        import pandas as pd

        if not samples:
            return

        # Get all parameter names from samples
        all_params = set()
        for sample in samples:
            all_params.update(sample.keys())

        # Filter to relevant parameters
        if param_type == 'Soil':
            relevant_params = ['pH', 'N (%)', 'Org. C (%)', 'Total P (mg/kg)', 'Avail P (mg/kg)',
                             'Exch. K (meq%)', 'Exch. Ca (meq%)', 'Exch. Mg (meq%)', 'CEC (meq%)']
        else:  # Leaf
            relevant_params = ['N (%)', 'P (%)', 'K (%)', 'Mg (%)', 'Ca (%)',
                             'B (mg/kg)', 'Cu (mg/kg)', 'Zn (mg/kg)']

        # Calculate statistics for each parameter
        table_data = []
        for param in relevant_params:
            if param in all_params:
                values = []
                for sample in samples:
                    if param in sample:
                        val = sample[param]
                        if val is not None and val != 'N/A' and val != '':
                            try:
                                float_val = float(val)
                                if param_type == 'Soil':
                                    if abs(float_val) < 10000:
                                        values.append(float_val)
                                else:
                                    if abs(float_val) < 100:
                                        values.append(float_val)
                            except (ValueError, TypeError):
                                pass

                if values:
                    avg_val = sum(values) / len(values)
                    min_val = min(values)
                    max_val = max(values)
                    std_dev = (sum((x - avg_val) ** 2 for x in values) / len(values)) ** 0.5

                    # Get MPOB standard
                    standards = soil_standards if param_type == 'Soil' else leaf_standards
                    optimal = standards.get(param, {}).get('optimal', 'N/A')
                    range_info = standards.get(param, {}).get('range', '')

                    table_data.append({
                        'Parameter': param,
                        'Average': f"{avg_val:.3f}",
                        'Minimum': f"{min_val:.3f}",
                        'Maximum': f"{max_val:.3f}",
                        'Std Dev': f"{std_dev:.3f}",
                        'Sample Count': len(values),
                        'MPOB Optimal': str(optimal)
                    })

        if table_data:
            # Display table
            st.markdown(f"### {icon} {title}")

            df = pd.DataFrame(table_data)
            st.dataframe(df, use_container_width=True, hide_index=True)

            # Display summary statistics
            st.markdown("#### 📈 Summary Statistics")
            total_samples = len(samples)
            total_params = len(table_data)
            st.info(f"📊 Analyzed {total_params} parameters across {total_samples} samples")

    except Exception as e:
        logger.warning(f"Could not create detailed {param_type} parameter table: {e}")

def generate_mpob_compliance_table(analysis_data):
    """Generate MPOB compliance summary table"""
    try:
        import pandas as pd

        compliance_data = []

        # Get nutrient comparisons if available
        nutrient_comparisons = []
        if 'nutrient_comparisons' in analysis_data:
            nutrient_comparisons = analysis_data['nutrient_comparisons']

        if nutrient_comparisons:
            for comparison in nutrient_comparisons:
                if isinstance(comparison, dict):
                    compliance_data.append({
                        'Parameter': comparison.get('parameter', 'Unknown'),
                        'Type': comparison.get('type', 'Unknown'),
                        'Current Average': f"{comparison.get('average', 0):.3f}",
                        'MPOB Optimal': f"{comparison.get('optimal', 0)}",
                        'Status': comparison.get('status', 'Unknown'),
                        'Deviation': 'Within Range' if comparison.get('status') == 'Within Range' else 'Needs Attention'
                    })

        if compliance_data:
            st.markdown("### 🎯 MPOB Standards Compliance Summary")

            df = pd.DataFrame(compliance_data)
            st.dataframe(df, use_container_width=True, hide_index=True)

    except Exception as e:
        logger.warning(f"Could not generate MPOB compliance table: {e}")

def generate_recommendations_priority_table(analysis_data):
    """Generate recommendations priority table based on data analysis"""
    try:
        import pandas as pd

        recommendations = []

        # Analyze soil data for recommendations
        soil_data = None
        if 'analysis_results' in analysis_data and 'raw_ocr_data' in analysis_data['analysis_results']:
            soil_data = analysis_data['analysis_results']['raw_ocr_data'].get('soil_data')

        if soil_data and 'samples' in soil_data:
            samples = soil_data['samples']
            if samples:
                # Calculate averages and check against standards
                soil_params = ['pH', 'N (%)', 'Org. C (%)', 'Total P (mg/kg)', 'Avail P (mg/kg)']

                for param in soil_params:
                    values = []
                    for sample in samples:
                        if param in sample:
                            val = sample[param]
                            if val is not None and val != 'N/A':
                                try:
                                    float_val = float(val)
                                    if abs(float_val) < 10000:
                                        values.append(float_val)
                                except:
                                    pass

                    if values:
                        avg_val = sum(values) / len(values)
                        optimal = soil_standards.get(param, {}).get('optimal', 0)

                        if param == 'pH' and abs(avg_val - optimal) > 0.5:
                            recommendations.append({
                                'Issue': f'Soil pH imbalance ({avg_val:.2f})',
                                'Priority': 'High',
                                'Recommendation': 'Adjust soil pH with lime or sulfur',
                                'Expected Impact': 'Improved nutrient availability'
                            })
                        elif param == 'N (%)' and avg_val < 0.15:
                            recommendations.append({
                                'Issue': f'Low soil nitrogen ({avg_val:.3f}%)',
                                'Priority': 'High',
                                'Recommendation': 'Apply nitrogen fertilizer',
                                'Expected Impact': 'Enhanced plant growth'
                            })

        if recommendations:
            st.markdown("### 🚀 Priority Recommendations")

            df = pd.DataFrame(recommendations)
            st.dataframe(df, use_container_width=True, hide_index=True)

    except Exception as e:
        logger.warning(f"Could not generate recommendations priority table: {e}")

def display_nutrient_status_bar_graphs(analysis_data):
    """Display Soil and Leaf Nutrient Status bar graphs comparing averages vs MPOB standards"""
    try:
        # Get soil and leaf data from various possible locations
        soil_data = None
        leaf_data = None

        # Try to get data from analysis results
        if 'analysis_results' in analysis_data:
            results = analysis_data['analysis_results']
            if 'raw_ocr_data' in results:
                raw_ocr = results['raw_ocr_data']
                if 'soil_data' in raw_ocr:
                    soil_data = raw_ocr['soil_data']
                if 'leaf_data' in raw_ocr:
                    leaf_data = raw_ocr['leaf_data']

        # Try alternative locations
        if not soil_data and 'raw_data' in analysis_data and 'soil_parameters' in analysis_data['raw_data']:
            soil_data = analysis_data['raw_data']['soil_parameters']
        if not leaf_data and 'raw_data' in analysis_data and 'leaf_parameters' in analysis_data['raw_data']:
            leaf_data = analysis_data['raw_data']['leaf_parameters']

        if soil_data or leaf_data:
            st.markdown("### 🌱 Soil & Leaf Nutrient Status (Average vs. MPOB Standard)")

            # Create soil nutrient status bar graph
            if soil_data and 'samples' in soil_data and soil_data['samples']:
                create_nutrient_status_bar_graph(soil_data['samples'], 'Soil', '🌱', [
                    'pH', 'N (%)', 'Org. C (%)', 'Total P (mg/kg)', 'Avail P (mg/kg)',
                    'Exch. K (meq%)', 'Exch. Ca (meq%)', 'Exch. Mg (meq%)', 'CEC (meq%)'
                ])

            # Create leaf nutrient status bar graph
            if leaf_data and 'samples' in leaf_data and leaf_data['samples']:
                create_nutrient_status_bar_graph(leaf_data['samples'], 'Leaf', '🍃', [
                    'N (%)', 'P (%)', 'K (%)', 'Mg (%)', 'Ca (%)',
                    'B (mg/kg)', 'Cu (mg/kg)', 'Zn (mg/kg)'
                ])

    except Exception as e:
        logger.warning(f"Could not display nutrient status bar graphs: {e}")
        st.info("📊 Nutrient status comparison graphs not available.")

def create_nutrient_status_bar_graph(samples, nutrient_type, icon, parameters):
    """Create a bar graph comparing nutrient averages vs MPOB standards"""
    try:
        import plotly.graph_objects as go

        # Calculate averages for each parameter
        averages = {}
        for param in parameters:
            values = []
            for sample in samples:
                if param in sample:
                    val = sample[param]
                    if val is not None and val != 'N/A' and val != '':
                        try:
                            float_val = float(val)
                            # Filter out obviously incorrect values
                            if nutrient_type == 'Soil':
                                if abs(float_val) < 10000:
                                    values.append(float_val)
                            else:  # Leaf
                                if abs(float_val) < 100:
                                    values.append(float_val)
                        except (ValueError, TypeError):
                            pass

            if values:
                averages[param] = sum(values) / len(values)

        if not averages:
            return

        # Get MPOB standards
        standards = soil_standards if nutrient_type == 'Soil' else leaf_standards

        # Prepare data for plotting
        params_list = []
        avg_values = []
        optimal_values = []
        status_colors = []

        for param in parameters:
            if param in averages and param in standards:
                avg_val = averages[param]
                optimal_val = standards[param].get('optimal', 0)

                params_list.append(param)
                avg_values.append(avg_val)
                optimal_values.append(optimal_val)

                # Determine status color based on range
                low_val = standards[param].get('low', '<0').replace('<', '')
                high_val = standards[param].get('high', '>999').replace('>', '')

                try:
                    min_val = float(low_val)
                    max_val = float(high_val)
                    if avg_val >= min_val and avg_val <= max_val:
                        status_colors.append('#28a745')  # Green
                    elif avg_val < min_val:
                        status_colors.append('#ffc107')  # Yellow
                    else:
                        status_colors.append('#dc3545')  # Red
                except (ValueError, TypeError):
                    status_colors.append('#6c757d')  # Gray

        if not params_list:
            return

        # Create the bar graph
        fig = go.Figure()

        # Add average values bars
        fig.add_trace(go.Bar(
            name=f'{nutrient_type} Average',
            x=params_list,
            y=avg_values,
            marker_color=status_colors,
            hovertemplate='<b>%{x}</b><br>Average: %{y:.2f}<extra></extra>'
        ))

        # Add MPOB optimal reference line
        fig.add_trace(go.Scatter(
            name='MPOB Optimal',
            x=params_list,
            y=optimal_values,
            mode='lines+markers',
            line=dict(color='#dc3545', width=3, dash='dash'),
            marker=dict(size=8, color='#dc3545'),
            hovertemplate='<b>%{x}</b><br>MPOB Optimal: %{y:.2f}<extra></extra>'
        ))

        # Update layout
        fig.update_layout(
            title={
                'text': f'{icon} {nutrient_type} Nutrient Status (Average vs. MPOB Standard)',
                'y': 0.95,
                'x': 0.5,
                'xanchor': 'center',
                'yanchor': 'top',
                'font': {'size': 16, 'color': '#2c3e50'}
            },
            xaxis_title="Parameters",
            yaxis_title="Values",
            height=500,
            plot_bgcolor='rgba(248,249,250,0.8)',
            paper_bgcolor='white',
            font={'color': '#2c3e50'},
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            barmode='overlay'
        )

        # Display the graph
        st.plotly_chart(fig, use_container_width=True)

        # Display summary table
        st.markdown(f"#### {icon} {nutrient_type} Nutrient Summary")

        summary_data = []
        for i, param in enumerate(params_list):
            status_text = "Within Range" if status_colors[i] == '#28a745' else "Low" if status_colors[i] == '#ffc107' else "High"
            summary_data.append({
                'Parameter': param,
                'Average': f"{avg_values[i]:.2f}",
                'MPOB Optimal': f"{optimal_values[i]}",
                'Status': status_text,
                'Unit': standards[param].get('range', '').split('-')[0] if 'range' in standards[param] else ''
            })

        import pandas as pd
        summary_df = pd.DataFrame(summary_data)
        st.dataframe(summary_df, use_container_width=True, hide_index=True)

    except Exception as e:
        logger.warning(f"Could not create {nutrient_type} nutrient status bar graph: {e}")
        st.info(f"📊 {nutrient_type} nutrient status graph not available.")

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
    elif 'analysis_results' in analysis_data and 'raw_data' in analysis_data['analysis_results'] and 'soil_parameters' in analysis_data['analysis_results']['raw_data']:
        soil_data = analysis_data['analysis_results']['raw_data']['soil_parameters']
    elif 'analysis_results' in analysis_data and 'soil_data' in analysis_data['analysis_results']:
        soil_data = analysis_data['analysis_results']['soil_data']
    # Try additional locations
    elif 'analysis_results' in analysis_data and 'raw_ocr_data' in analysis_data['analysis_results'] and 'soil_data' in analysis_data['analysis_results']['raw_ocr_data']:
        soil_data = analysis_data['analysis_results']['raw_ocr_data']['soil_data']
    elif 'raw_ocr_data' in analysis_data and 'soil_data' in analysis_data['raw_ocr_data']:
        soil_data = analysis_data['raw_ocr_data']['soil_data']
    
    # Try to get leaf parameters from various locations
    leaf_data = None
    if 'raw_data' in analysis_data and 'leaf_parameters' in analysis_data['raw_data']:
        leaf_data = analysis_data['raw_data']['leaf_parameters']
    elif 'leaf_parameters' in analysis_data:
        leaf_data = analysis_data['leaf_parameters']
    elif 'analysis_results' in analysis_data and 'raw_data' in analysis_data['analysis_results'] and 'leaf_parameters' in analysis_data['analysis_results']['raw_data']:
        leaf_data = analysis_data['analysis_results']['raw_data']['leaf_parameters']
    elif 'analysis_results' in analysis_data and 'leaf_data' in analysis_data['analysis_results']:
        leaf_data = analysis_data['analysis_results']['leaf_data']
    # Try additional locations
    elif 'analysis_results' in analysis_data and 'raw_ocr_data' in analysis_data['analysis_results'] and 'leaf_data' in analysis_data['analysis_results']['raw_ocr_data']:
        leaf_data = analysis_data['analysis_results']['raw_ocr_data']['leaf_data']
    elif 'raw_ocr_data' in analysis_data and 'leaf_data' in analysis_data['raw_ocr_data']:
        leaf_data = analysis_data['raw_ocr_data']['leaf_data']

    # Debug logging (commented out for production)
    if soil_data:
        print(f"Soil data keys: {list(soil_data.keys())}")
        if 'parameter_statistics' in soil_data:
            print(f"Soil parameter statistics: {list(soil_data['parameter_statistics'].keys())}")
    if leaf_data:
        print(f"Leaf data keys: {list(leaf_data.keys())}")
        if 'parameter_statistics' in leaf_data:
            print(f"Leaf parameter statistics: {list(leaf_data['parameter_statistics'].keys())}")
    
    # Define parameter type mappings for correct classification
    soil_parameter_names = {
        'ph', 'nitrogen', 'nitrogen %', 'n (%)', 'organic carbon', 'organic carbon %', 'org. c (%)',
        'total p', 'total p (mg/kg)', 'available p', 'available p (mg/kg)', 'avail p (mg/kg)',
        'exchangeable k', 'exch. k (meq%)', 'exch. k meq%', 'exchangeable ca', 'exch. ca (meq%)', 'exch. ca meq%',
        'exchangeable mg', 'exch. mg (meq%)', 'exch. mg meq%', 'cec', 'cec (meq%)', 'c.e.c (meq%)', 'c.e.c meq%'
    }
    
    leaf_parameter_names = {
        'n (%)', 'p (%)', 'k (%)', 'mg (%)', 'ca (%)', 'b (mg/kg)', 'cu (mg/kg)', 'zn (mg/kg)',
        'n', 'p', 'k', 'mg', 'ca', 'b', 'cu', 'zn'
    }
    
    def determine_parameter_type(param_name):
        """Determine if a parameter is soil or leaf based on its name"""
        param_lower = param_name.lower().strip()
        if param_lower in soil_parameter_names:
            return 'Soil'
        elif param_lower in leaf_parameter_names:
            return 'Leaf'
        else:
            # Default classification based on common patterns
            if any(keyword in param_lower for keyword in ['ph', 'carbon', 'cec', 'exchangeable', 'exch.']):
                return 'Soil'
            elif any(keyword in param_lower for keyword in ['b (mg/kg)', 'cu (mg/kg)', 'zn (mg/kg)']):
                return 'Leaf'
            else:
                return 'Unknown'
    
    # Extract soil parameters
    if soil_data:
        # Try parameter_statistics first
        if 'parameter_statistics' in soil_data:
            stats = soil_data['parameter_statistics']
            for param_name, param_data in stats.items():
                if isinstance(param_data, dict):
                    # Ensure correct type classification
                    param_type = determine_parameter_type(param_name)
                    if param_type == 'Soil' or param_type == 'Unknown':  # Default unknown to soil if from soil_data
                        echo_data.append({
                            'Parameter': param_name,
                            'Type': 'Soil',
                            'Average': f"{param_data.get('average', 0):.2f}" if param_data.get('average') is not None else 'Missing',
                            'Min': f"{param_data.get('min', 0):.2f}" if param_data.get('min') is not None else 'Missing',
                            'Max': f"{param_data.get('max', 0):.2f}" if param_data.get('max') is not None else 'Missing',
                            'Std Dev': f"{param_data.get('std_dev', 0):.2f}" if param_data.get('std_dev') is not None else 'Missing',
                            'Unit': param_data.get('unit', ''),
                            'Samples': param_data.get('count', 0)
                        })
        # Fallback: calculate from samples if parameter_statistics not available
        elif 'samples' in soil_data or 'all_samples' in soil_data:
            samples = soil_data.get('samples', soil_data.get('all_samples', []))
            if samples:
                # Calculate basic statistics for key parameters
                soil_params = ['pH', 'N (%)', 'Org. C (%)', 'Total P (mg/kg)', 'Avail P (mg/kg)', 'Exch. K (meq%)', 'Exch. Ca (meq%)', 'Exch. Mg (meq%)', 'CEC (meq%)']
                for param in soil_params:
                    values = []
                    for sample in samples:
                        # Try different parameter name variations
                        val = sample.get(param)
                        if val is None:
                            if param == 'N (%)':
                                val = sample.get('Nitrogen (%)') or sample.get('N_%')
                            elif param == 'Org. C (%)':
                                val = sample.get('Organic Carbon (%)') or sample.get('Organic_Carbon_%')
                            elif param == 'Total P (mg/kg)':
                                val = sample.get('Total_P_mg_kg')
                            elif param == 'Avail P (mg/kg)':
                                val = sample.get('Available P (mg/kg)') or sample.get('Available_P_mg_kg')
                            elif param == 'Exch. K (meq%)':
                                val = sample.get('Exchangeable K (meq%)') or sample.get('Exchangeable_K_meq%')
                            elif param == 'Exch. Ca (meq%)':
                                val = sample.get('Exchangeable Ca (meq%)') or sample.get('Exchangeable_Ca_meq%')
                            elif param == 'Exch. Mg (meq%)':
                                val = sample.get('Exchangeable Mg (meq%)') or sample.get('Exchangeable_Mg_meq%')
                            elif param == 'CEC (meq%)':
                                val = sample.get('C.E.C (meq%)') or sample.get('CEC_meq%')

                        if val is not None and val != 'N/A' and val != '':
                            try:
                                float_val = float(val)
                                if abs(float_val) < 10000:  # Reasonable upper limit
                                    values.append(float_val)
                            except (ValueError, TypeError):
                                pass

                    if values:
                        avg_val = sum(values) / len(values)
                        min_val = min(values)
                        max_val = max(values)
                        echo_data.append({
                            'Parameter': param,
                            'Type': 'Soil',
                            'Average': f"{avg_val:.2f}",
                            'Min': f"{min_val:.2f}",
                            'Max': f"{max_val:.2f}",
                            'Std Dev': 'N/A',
                            'Unit': '',
                            'Samples': len(values)
                })
    
    # Extract leaf parameters
    if leaf_data:
        # Try parameter_statistics first
        if 'parameter_statistics' in leaf_data:
            stats = leaf_data['parameter_statistics']
            for param_name, param_data in stats.items():
                if isinstance(param_data, dict):
                    # Ensure correct type classification
                    param_type = determine_parameter_type(param_name)
                    if param_type == 'Leaf' or (param_type == 'Unknown' and 'leaf' in str(leaf_data).lower()):  # Default unknown to leaf if from leaf_data
                        echo_data.append({
                            'Parameter': param_name,
                            'Type': 'Leaf',
                            'Average': f"{param_data.get('average', 0):.2f}" if param_data.get('average') is not None else 'Missing',
                            'Min': f"{param_data.get('min', 0):.2f}" if param_data.get('min') is not None else 'Missing',
                            'Max': f"{param_data.get('max', 0):.2f}" if param_data.get('max') is not None else 'Missing',
                            'Std Dev': f"{param_data.get('std_dev', 0):.2f}" if param_data.get('std_dev') is not None else 'Missing',
                            'Unit': param_data.get('unit', ''),
                            'Samples': param_data.get('count', 0)
                        })
        # Fallback: calculate from samples if parameter_statistics not available
        elif 'samples' in leaf_data or 'all_samples' in leaf_data:
            samples = leaf_data.get('samples', leaf_data.get('all_samples', []))
            if samples:
                # Calculate basic statistics for key parameters
                leaf_params = ['N (%)', 'P (%)', 'K (%)', 'Mg (%)', 'Ca (%)', 'B (mg/kg)', 'Cu (mg/kg)', 'Zn (mg/kg)']
                for param in leaf_params:
                    values = []
                    for sample in samples:
                        # Try different parameter name variations
                        val = sample.get(param)
                        if val is None:
                            if param == 'N (%)':
                                val = sample.get('N_%')
                            elif param == 'P (%)':
                                val = sample.get('P_%')
                            elif param == 'K (%)':
                                val = sample.get('K_%')
                            elif param == 'Mg (%)':
                                val = sample.get('Mg_%')
                            elif param == 'Ca (%)':
                                val = sample.get('Ca_%')
                            elif param == 'B (mg/kg)':
                                val = sample.get('B_mg_kg')
                            elif param == 'Cu (mg/kg)':
                                val = sample.get('Cu_mg_kg')
                            elif param == 'Zn (mg/kg)':
                                val = sample.get('Zn_mg_kg')

                        if val is not None and val != 'N/A' and val != '':
                            try:
                                float_val = float(val)
                                if abs(float_val) < 100:  # Reasonable upper limit for leaf nutrients
                                    values.append(float_val)
                            except (ValueError, TypeError):
                                pass

                    if values:
                        avg_val = sum(values) / len(values)
                        min_val = min(values)
                        max_val = max(values)
                        echo_data.append({
                            'Parameter': param,
                            'Type': 'Leaf',
                            'Average': f"{avg_val:.2f}",
                            'Min': f"{min_val:.2f}",
                            'Max': f"{max_val:.2f}",
                            'Std Dev': 'N/A',
                            'Unit': '',
                            'Samples': len(values)
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
                        'Min': f"{min_val:.2f}" if min_val is not None else 'Missing',
                        'Max': f"{max_val:.2f}" if max_val is not None else 'Missing',
                        'Std Dev': f"{std_val:.2f}" if std_val is not None else 'Missing',
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

def generate_nutrient_comparisons_from_raw_data(analysis_data):
    """Generate nutrient comparisons from raw data when not available in standard format"""
    try:
        comparisons = []

        # Get soil data from various locations
        soil_data = None
        if 'raw_data' in analysis_data and 'soil_parameters' in analysis_data['raw_data']:
            soil_data = analysis_data['raw_data']['soil_parameters']
        elif 'analysis_results' in analysis_data and 'raw_ocr_data' in analysis_data['analysis_results'] and 'soil_data' in analysis_data['analysis_results']['raw_ocr_data']:
            soil_data = analysis_data['analysis_results']['raw_ocr_data']['soil_data']

        # Get leaf data from various locations
        leaf_data = None
        if 'raw_data' in analysis_data and 'leaf_parameters' in analysis_data['raw_data']:
            leaf_data = analysis_data['raw_data']['leaf_parameters']
        elif 'analysis_results' in analysis_data and 'raw_ocr_data' in analysis_data['analysis_results'] and 'leaf_data' in analysis_data['analysis_results']['raw_ocr_data']:
            leaf_data = analysis_data['analysis_results']['raw_ocr_data']['leaf_data']

        # MPOB standards for comparison
        soil_standards = {
            'pH': {'optimal': 5.0, 'unit': ''},
            'N (%)': {'optimal': 0.20, 'unit': '%'},
            'Org. C (%)': {'optimal': 2.0, 'unit': '%'},
            'Total P (mg/kg)': {'optimal': 20, 'unit': 'mg/kg'},
            'Avail P (mg/kg)': {'optimal': 15, 'unit': 'mg/kg'},
            'Exch. K (meq%)': {'optimal': 0.30, 'unit': 'meq%'},
            'Exch. Ca (meq%)': {'optimal': 3.0, 'unit': 'meq%'},
            'Exch. Mg (meq%)': {'optimal': 0.9, 'unit': 'meq%'},
            'CEC (meq%)': {'optimal': 20, 'unit': 'meq%'}
        }

        leaf_standards = {
            'N (%)': {'optimal': 2.6, 'unit': '%'},
            'P (%)': {'optimal': 0.17, 'unit': '%'},
            'K (%)': {'optimal': 1.1, 'unit': '%'},
            'Mg (%)': {'optimal': 0.35, 'unit': '%'},
            'Ca (%)': {'optimal': 0.7, 'unit': '%'},
            'B (mg/kg)': {'optimal': 23, 'unit': 'mg/kg'},
            'Cu (mg/kg)': {'optimal': 13, 'unit': 'mg/kg'},
            'Zn (mg/kg)': {'optimal': 26, 'unit': 'mg/kg'}
        }

        # Generate soil comparisons
        if soil_data and 'samples' in soil_data:
            samples = soil_data['samples']
            if samples:
                for param, std_info in soil_standards.items():
                    values = []
                    for sample in samples:
                        val = sample.get(param)
                        if val is not None:
                            try:
                                float_val = float(val)
                                if abs(float_val) < 10000:  # Filter out obviously wrong values
                                    values.append(float_val)
                            except (ValueError, TypeError):
                                pass

                    if values:
                        avg_val = sum(values) / len(values)
                        comparisons.append({
                            'parameter': param,
                            'type': 'Soil',
                            'average': avg_val,
                            'min': min(values),
                            'max': max(values),
                            'count': len(values),
                            'unit': std_info['unit'],
                            'optimal': std_info['optimal'],
                            'status': 'Within Range' if abs(avg_val - std_info['optimal']) / std_info['optimal'] <= 0.2 else 'Outside Range'
                        })

        # Generate leaf comparisons
        if leaf_data and 'samples' in leaf_data:
            samples = leaf_data['samples']
            if samples:
                # Map parameter names to their locations in the nested structure
                param_mapping = {
                    'N (%)': ('% Dry Matter', 'N'),
                    'P (%)': ('% Dry Matter', 'P'),
                    'K (%)': ('% Dry Matter', 'K'),
                    'Mg (%)': ('% Dry Matter', 'Mg'),
                    'Ca (%)': ('% Dry Matter', 'Ca'),
                    'B (mg/kg)': ('mg/kg Dry Matter', 'B'),
                    'Cu (mg/kg)': ('mg/kg Dry Matter', 'Cu'),
                    'Zn (mg/kg)': ('mg/kg Dry Matter', 'Zn')
                }
                
                for param, std_info in leaf_standards.items():
                    values = []
                    if param in param_mapping:
                        section, key = param_mapping[param]
                        for sample in samples:
                            section_data = sample.get(section, {})
                            val = section_data.get(key)
                            if val is not None:
                                try:
                                    # Handle string values like "<1"
                                    if isinstance(val, str):
                                        if val.startswith('<'):
                                            val = val[1:]  # Remove '<' and use the number
                                        elif val.startswith('>'):
                                            val = val[1:]  # Remove '>' and use the number
                                    
                                    float_val = float(val)
                                    if abs(float_val) < 100:  # Filter out obviously wrong values
                                        values.append(float_val)
                                except (ValueError, TypeError):
                                    pass

                    if values:
                        avg_val = sum(values) / len(values)
                        comparisons.append({
                            'parameter': param,
                            'type': 'Leaf',
                            'average': avg_val,
                            'min': min(values),
                            'max': max(values),
                            'count': len(values),
                            'unit': std_info['unit'],
                            'optimal': std_info['optimal'],
                            'status': 'Within Range' if abs(avg_val - std_info['optimal']) / std_info['optimal'] <= 0.2 else 'Outside Range'
                        })

        return comparisons if comparisons else None

    except Exception as e:
        logger.warning(f"Could not generate nutrient comparisons from raw data: {e}")
        return None

def generate_nutrient_comparisons_from_structured_data():
    """Generate nutrient comparisons from structured data in session state"""
    try:
        import streamlit as st

        structured_soil_data = st.session_state.get('structured_soil_data', {})
        structured_leaf_data = st.session_state.get('structured_leaf_data', {})

        comparisons = []

        # MPOB standards
        soil_standards = {
            'pH': {'optimal': 5.0, 'unit': ''},
            'N (%)': {'optimal': 0.20, 'unit': '%'},
            'Org. C (%)': {'optimal': 2.0, 'unit': '%'},
            'Total P (mg/kg)': {'optimal': 20, 'unit': 'mg/kg'},
            'Avail P (mg/kg)': {'optimal': 15, 'unit': 'mg/kg'},
            'Exch. K (meq%)': {'optimal': 0.30, 'unit': 'meq%'},
            'Exch. Ca (meq%)': {'optimal': 3.0, 'unit': 'meq%'},
            'Exch. Mg (meq%)': {'optimal': 0.9, 'unit': 'meq%'},
            'CEC (meq%)': {'optimal': 20, 'unit': 'meq%'}
        }

        leaf_standards = {
            'N (%)': {'optimal': 2.6, 'unit': '%'},
            'P (%)': {'optimal': 0.17, 'unit': '%'},
            'K (%)': {'optimal': 1.1, 'unit': '%'},
            'Mg (%)': {'optimal': 0.35, 'unit': '%'},
            'Ca (%)': {'optimal': 0.7, 'unit': '%'},
            'B (mg/kg)': {'optimal': 23, 'unit': 'mg/kg'},
            'Cu (mg/kg)': {'optimal': 13, 'unit': 'mg/kg'},
            'Zn (mg/kg)': {'optimal': 26, 'unit': 'mg/kg'}
        }

        # Process soil data
        if structured_soil_data:
            for container_key in ['Farm_Soil_Test_Data', 'SP_Lab_Test_Report']:
                if container_key in structured_soil_data:
                    samples_data = structured_soil_data[container_key]
                    if samples_data:
                        for param, std_info in soil_standards.items():
                            values = []
                            for sample_id, params in samples_data.items():
                                if param in params:
                                    val = params[param]
                                    try:
                                        float_val = float(val)
                                        if abs(float_val) < 10000:
                                            values.append(float_val)
                                    except (ValueError, TypeError):
                                        pass

                            if values:
                                avg_val = sum(values) / len(values)
                                comparisons.append({
                                    'parameter': param,
                                    'type': 'Soil',
                                    'average': avg_val,
                                    'min': min(values),
                                    'max': max(values),
                                    'count': len(values),
                                    'unit': std_info['unit'],
                                    'optimal': std_info['optimal'],
                                    'status': 'Within Range' if abs(avg_val - std_info['optimal']) / std_info['optimal'] <= 0.2 else 'Outside Range'
                                })
                    break

        # Process leaf data
        if structured_leaf_data:
            for container_key in ['Farm_Leaf_Test_Data', 'SP_Lab_Test_Report']:
                if container_key in structured_leaf_data:
                    samples_data = structured_leaf_data[container_key]
                    if samples_data:
                        for param, std_info in leaf_standards.items():
                            values = []
                            for sample_id, params in samples_data.items():
                                if param in params:
                                    val = params[param]
                                    try:
                                        float_val = float(val)
                                        if abs(float_val) < 100:
                                            values.append(float_val)
                                    except (ValueError, TypeError):
                                        pass

                            if values:
                                avg_val = sum(values) / len(values)
                                comparisons.append({
                                    'parameter': param,
                                    'type': 'Leaf',
                                    'average': avg_val,
                                    'min': min(values),
                                    'max': max(values),
                                    'count': len(values),
                                    'unit': std_info['unit'],
                                    'optimal': std_info['optimal'],
                                    'status': 'Within Range' if abs(avg_val - std_info['optimal']) / std_info['optimal'] <= 0.2 else 'Outside Range'
                                })
                    break

        return comparisons if comparisons else None

    except Exception as e:
        logger.warning(f"Could not generate nutrient comparisons from structured data: {e}")
        return None

def display_nutrient_status_tables(analysis_data):
    """Display Soil and Leaf Nutrient Status tables"""
    # Get nutrient comparisons data from multiple possible locations
    nutrient_comparisons = analysis_data.get('nutrient_comparisons', [])
    
    # Try to get from analysis_results if not found directly
    if not nutrient_comparisons and 'analysis_results' in analysis_data:
        nutrient_comparisons = analysis_data['analysis_results'].get('nutrient_comparisons', [])

    # Try to get from step_by_step_analysis
    if not nutrient_comparisons and 'analysis_results' in analysis_data and 'step_by_step_analysis' in analysis_data['analysis_results']:
        step_results = analysis_data['analysis_results']['step_by_step_analysis']
        if isinstance(step_results, list) and len(step_results) > 0:
            first_step = step_results[0]
            if isinstance(first_step, dict):
                nutrient_comparisons = first_step.get('nutrient_comparisons', [])

    # Try additional locations
    if not nutrient_comparisons and 'step_by_step_analysis' in analysis_data:
        step_results = analysis_data['step_by_step_analysis']
        if isinstance(step_results, list) and len(step_results) > 0:
            first_step = step_results[0]
            if isinstance(first_step, dict):
                nutrient_comparisons = first_step.get('nutrient_comparisons', [])

    # Generate nutrient comparisons from raw data if still not found
    if not nutrient_comparisons:
        nutrient_comparisons = generate_nutrient_comparisons_from_raw_data(analysis_data)

    if not nutrient_comparisons:
        # Try to generate from structured data
        nutrient_comparisons = generate_nutrient_comparisons_from_structured_data()
    
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
        'N (%)', 'P (%)', 'K (%)', 'Mg (%)', 'Ca (%)',
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
                    'Average': f"{avg_val:.2f}" if isinstance(avg_val, (int, float)) else 'Missing',
                    'MPOB Optimal': f"{opt_val:.2f}" if isinstance(opt_val, (int, float)) else 'Missing',
                    'Status': param.get('status') or computed_status,
                    'Unit': param.get('unit', '')
                })
            else:
                # Fill missing parameter row with N/A
                soil_data.append({
                    'Parameter': label,
                    'Average': 'Missing',
                    'MPOB Optimal': 'Missing',
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
                    'Average': f"{avg_val:.2f}" if isinstance(avg_val, (int, float)) else 'Missing',
                    'MPOB Optimal': f"{opt_val:.2f}" if isinstance(opt_val, (int, float)) else 'Missing',
                    'Status': param.get('status') or computed_status,
                    'Unit': param.get('unit', '')
                })
            else:
                # Fill missing parameter row with N/A
                leaf_data.append({
                    'Parameter': label,
                    'Average': 'Missing',
                    'MPOB Optimal': 'Missing',
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
    
    # Safety check: If no data available, show a message
    if not analysis_data or not any(analysis_data.get(key) for key in ['summary', 'detailed_analysis', 'analysis_results']):
        st.warning("⚠️ No Step 3 analysis data available. Please ensure the analysis has been completed.")
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
                            # Convert to clean structured text
                            if isinstance(item, dict):
                                for k, v in item.items():
                                    if v is not None and v != "":
                                        st.markdown(f"  • **{k.replace('_', ' ').title()}:** {v}")
                            else:
                                st.markdown(f"  • {item}")
                    elif isinstance(item, list):
                        st.markdown(f"- Item {idx}:")
                        # Convert list to clean structured text
                        for i, sub_item in enumerate(item, 1):
                            if isinstance(sub_item, dict):
                                st.markdown(f"  • Item {i}:")
                                for k, v in sub_item.items():
                                    if v is not None and v != "":
                                        st.markdown(f"    - **{k.replace('_', ' ').title()}:** {v}")
                            else:
                                st.markdown(f"  • Item {i}: {sub_item}")
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
        
        # Show baseline yield. Prefer explicit baseline; fall back to user's economic data
        raw_baseline = forecast.get('baseline_yield')
        baseline_yield = _extract_first_float(raw_baseline, 0.0)

        # If still zero/empty, try to infer from user's economic forecast
        if not baseline_yield:
            econ_paths = [
                ('economic_forecast', 'current_yield_tonnes_per_ha'),
                ('economic_forecast', 'current_yield'),
            ]
            # nested under analysis
            if 'analysis' in analysis_data and isinstance(analysis_data['analysis'], dict):
                analysis_econ = analysis_data['analysis'].get('economic_forecast', {})
                if analysis_econ:
                    baseline_yield = _extract_first_float(
                        analysis_econ.get('current_yield_tonnes_per_ha') or analysis_econ.get('current_yield'),
                        0.0,
                    )
            if not baseline_yield and 'economic_forecast' in analysis_data:
                econ = analysis_data.get('economic_forecast', {})
                baseline_yield = _extract_first_float(
                    econ.get('current_yield_tonnes_per_ha') or econ.get('current_yield'),
                    0.0,
                )

        # As a final fallback, attempt to use the first point of any numeric series
        if not baseline_yield:
            for key in ['medium_investment', 'high_investment', 'low_investment']:
                series = forecast.get(key)
                if isinstance(series, list) and len(series) > 0:
                    baseline_yield = _extract_first_float(series[0], 0.0)
                    if baseline_yield:
                        break
            
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
        st.warning("⚠️ No yield forecast data available - generating default forecast graph")
        st.info("💡 The LLM should generate yield forecast data including baseline yield and 5-year projections for high, medium, and low investment scenarios.")

        # Generate default forecast graph when no data is available
        generate_default_forecast_graph(analysis_data)

def generate_default_forecast_graph(analysis_data):
    """Generate a default forecast graph when LLM doesn't provide yield forecast data"""
    try:
        # Try to get current yield from economic forecast
        current_yield = 0
        if 'economic_forecast' in analysis_data:
            econ = analysis_data['economic_forecast']
            current_yield = econ.get('current_yield_tonnes_per_ha', econ.get('current_yield', 15))

        # If no economic data, use a reasonable default
        if current_yield <= 0:
            current_yield = 15  # Default yield for Malaysian oil palm

        # Generate 5-year forecast with realistic growth rates
        years = list(range(2024, 2029))
        baseline_yield = [current_yield] * len(years)

        # High investment: 8-12% annual growth
        high_yield = []
        for i in range(len(years)):
            if i == 0:
                high_yield.append(current_yield)
            else:
                growth_rate = 0.08 + (i * 0.01)  # Increasing growth rate
                high_yield.append(high_yield[i-1] * (1 + growth_rate))

        # Medium investment: 4-8% annual growth
        medium_yield = []
        for i in range(len(years)):
            if i == 0:
                medium_yield.append(current_yield)
            else:
                growth_rate = 0.04 + (i * 0.005)
                medium_yield.append(medium_yield[i-1] * (1 + growth_rate))

        # Low investment: 1-3% annual growth (minimal improvement)
        low_yield = []
        for i in range(len(years)):
            if i == 0:
                low_yield.append(current_yield)
            else:
                growth_rate = 0.01 + (i * 0.001)
                low_yield.append(low_yield[i-1] * (1 + growth_rate))

        # Create the graph
        try:
            import plotly.graph_objects as go

            fig = go.Figure()

            # Add traces
            fig.add_trace(go.Scatter(
                x=years,
                y=baseline_yield,
                mode='lines+markers',
                name='Current Yield (Baseline)',
                line=dict(color='#6c757d', width=3, dash='dash'),
                marker=dict(size=8, color='#6c757d'),
                hovertemplate='<b>Year %{x}</b><br>Yield: %{y:.1f} tons/ha<extra></extra>'
            ))

            fig.add_trace(go.Scatter(
                x=years,
                y=high_yield,
                mode='lines+markers',
                name='High Investment Scenario',
                line=dict(color='#28a745', width=3),
                marker=dict(size=8, color='#28a745'),
                hovertemplate='<b>Year %{x}</b><br>Yield: %{y:.1f} tons/ha<br>High Investment<extra></extra>'
            ))

            fig.add_trace(go.Scatter(
                x=years,
                y=medium_yield,
                mode='lines+markers',
                name='Medium Investment Scenario',
                line=dict(color='#ffc107', width=3),
                marker=dict(size=8, color='#ffc107'),
                hovertemplate='<b>Year %{x}</b><br>Yield: %{y:.1f} tons/ha<br>Medium Investment<extra></extra>'
            ))

            fig.add_trace(go.Scatter(
                x=years,
                y=low_yield,
                mode='lines+markers',
                name='Low Investment Scenario',
                line=dict(color='#dc3545', width=3),
                marker=dict(size=8, color='#dc3545'),
                hovertemplate='<b>Year %{x}</b><br>Yield: %{y:.1f} tons/ha<br>Low Investment<extra></extra>'
            ))

            # Update layout
            fig.update_layout(
                title={
                    'text': '5-Year Oil Palm Yield Forecast',
                    'y': 0.95,
                    'x': 0.5,
                    'xanchor': 'center',
                    'yanchor': 'top',
                    'font': {'size': 18, 'color': '#2c3e50'}
                },
                xaxis_title="Year",
                yaxis_title="Yield (tons/ha)",
                height=500,
                plot_bgcolor='rgba(248,249,250,0.8)',
                paper_bgcolor='white',
                font={'color': '#2c3e50'},
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                ),
                hovermode='x unified'
            )

            # Display the graph
            st.plotly_chart(fig, use_container_width=True)

            # Display forecast table
            st.markdown("### 📊 Yield Forecast Data")
            forecast_data = []
            for i, year in enumerate(years):
                forecast_data.append({
                    'Year': year,
                    'Baseline': f"{baseline_yield[i]:.1f}",
                    'Low Investment': f"{low_yield[i]:.1f}",
                    'Medium Investment': f"{medium_yield[i]:.1f}",
                    'High Investment': f"{high_yield[i]:.1f}"
                })

            st.dataframe(forecast_data, use_container_width=True, hide_index=True)

            # Add investment scenario details
            st.markdown("### 💰 Investment Scenario Details")

            col1, col2, col3 = st.columns(3)

            with col1:
                st.markdown("""
                **🟢 High Investment Scenario**
                - Intensive fertilization program
                - Regular soil and leaf analysis
                - Advanced irrigation systems
                - Pest and disease management
                - Expected growth: 8-12% annually
                """)

            with col2:
                st.markdown("""
                **🟡 Medium Investment Scenario**
                - Moderate fertilization program
                - Annual soil and leaf analysis
                - Basic irrigation improvements
                - Standard pest management
                - Expected growth: 4-8% annually
                """)

            with col3:
                st.markdown("""
                **🔴 Low Investment Scenario**
                - Basic fertilization maintenance
                - Minimal monitoring
                - Rain-fed irrigation
                - Reactive pest management
                - Expected growth: 1-3% annually
                """)

        except ImportError:
            st.warning("Plotly not available for forecast graph display")
            # Fallback table display
            st.markdown("#### Yield Forecast Table")
            forecast_data = []
            for i, year in enumerate(years):
                forecast_data.append({
                    'Year': year,
                    'Baseline': f"{baseline_yield[i]:.1f}",
                    'Low Investment': f"{low_yield[i]:.1f}",
                    'Medium Investment': f"{medium_yield[i]:.1f}",
                    'High Investment': f"{high_yield[i]:.1f}"
                })

            st.table(forecast_data)

        # Add assumptions note
        st.info("📝 **Default Forecast Assumptions:** This forecast is generated using standard oil palm growth rates. Actual results may vary based on field conditions, management practices, and external factors. Regular monitoring and adaptive management are recommended.")

    except Exception as e:
        st.error(f"Error generating default forecast graph: {e}")
        st.info("Unable to generate forecast graph. Please ensure the LLM provides yield forecast data in the analysis.")

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
            
            # Additional information
            if st.checkbox("🔍 Show Additional Info", help="Show additional information about the analysis"):
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


def display_structured_ocr_data():
    """Display structured OCR data from upload page in JSON and table format"""
    st.markdown("### 📝 Structured OCR Data (Upload Page)")
    st.markdown("*This data will be used by the AI for analysis. Each sample ID contains its parameter values:*")

    # Get structured data from session state
    structured_soil_data = st.session_state.get('structured_soil_data', {})
    structured_leaf_data = st.session_state.get('structured_leaf_data', {})

    if structured_soil_data or structured_leaf_data:
        # Display JSON format in expandable section
        with st.expander("🔍 Structured JSON Data", expanded=False):
            st.markdown("**Raw structured data extracted from uploaded files:**")
            if structured_soil_data:
                st.markdown("#### 🌱 Soil Data (JSON)")
                st.json(structured_soil_data)
            if structured_leaf_data:
                st.markdown("#### 🍃 Leaf Data (JSON)")
                st.json(structured_leaf_data)

        # Display data in table format
        st.markdown("### 🗂️ Laboratory Raw Data Tables")

        # Display soil data table
        if structured_soil_data:
            display_structured_data_table(structured_soil_data, "Soil", "🌱")

        # Display leaf data table
        if structured_leaf_data:
            display_structured_data_table(structured_leaf_data, "Leaf", "🍃")

        # Parameter averages summary removed as requested
    else:
        st.info("ℹ️ **Note**: No structured OCR data available from upload page. Data will be processed through OCR analysis.")


def display_structured_data_table(data, data_type, icon):
    """Display structured data in table format"""
    if 'Farm_Soil_Test_Data' in data:
        container_key = 'Farm_Soil_Test_Data'
        sample_prefix = 'S'
        title = f"{icon} {data_type} Data - Farm Test Results"
    elif 'Farm_Leaf_Test_Data' in data:
        container_key = 'Farm_Leaf_Test_Data'
        sample_prefix = 'L'
        title = f"{icon} {data_type} Data - Farm Test Results"
    elif 'SP_Lab_Test_Report' in data:
        container_key = 'SP_Lab_Test_Report'
        sample_prefix = data_type[0]  # 'S' for Soil, 'L' for Leaf
        title = f"{icon} {data_type} Data - SP Lab Test Report"
    else:
        st.warning(f"No {data_type.lower()} data found in structured format")
        return

    st.markdown(f"#### {title}")

    samples_data = data[container_key]

    if samples_data:
        # Create table data
        table_data = []

        # Get all parameter names from all samples
        all_params = set()
        for sample_id, params in samples_data.items():
            all_params.update(params.keys())

        # Sort parameters for consistent display
        sorted_params = sorted(all_params)

        # Create header row
        header = ["Sample ID"] + sorted_params
        table_data.append(header)

        # Add data rows
        for sample_id, params in samples_data.items():
            row = [f"{sample_prefix}{sample_id}"]
            for param in sorted_params:
                value = params.get(param, "N/A")
                if isinstance(value, (int, float)) and not isinstance(value, bool):
                    row.append(f"{value:.3f}")
                else:
                    row.append(str(value))
            table_data.append(row)

        # Display the table
        if len(table_data) > 1:  # More than just header
            df = pd.DataFrame(table_data[1:], columns=table_data[0])
            st.dataframe(df, use_container_width=True, hide_index=True)

            # Show sample count (removed debug info as requested)
            # sample_count = len(samples_data)
            # st.info(f"📊 **{data_type} Data**: {sample_count} samples loaded from structured OCR data")

            # Calculate and display averages for LLM use (removed as requested)
            # st.markdown(f"**📈 {data_type} Parameter Averages (for LLM Analysis):**")
            # averages_text = calculate_structured_data_averages(samples_data, sorted_params, data_type)
            # st.code(averages_text, language="text")
        else:
            st.warning(f"No {data_type.lower()} samples found in structured data")
    else:
        st.warning(f"No {data_type.lower()} data available in structured format")


def calculate_structured_data_averages(samples_data, params, data_type):
    """Calculate averages for structured data parameters"""
    averages = {}

    for param in params:
        values = []
        for sample_id, sample_params in samples_data.items():
            if param in sample_params:
                value = sample_params[param]
                if isinstance(value, (int, float)) and not isinstance(value, bool):
                    # Filter out obviously incorrect values
                    if data_type == "Soil":
                        if abs(value) < 10000:  # Reasonable upper limit for soil
                            values.append(value)
                    else:  # Leaf
                        if abs(value) < 100:  # Reasonable upper limit for leaf
                            values.append(value)

        if values:
            avg = sum(values) / len(values)
            averages[param] = avg

    # Format for LLM use
    result_lines = [f"{data_type} Parameter Averages:"]
    for param, avg in averages.items():
        result_lines.append(f"  {param}: {avg:.3f}")

    return "\n".join(result_lines)


def calculate_structured_data_averages_summary(data, data_type):
    """Calculate and format averages summary for LLM use"""
    if data_type == "Soil":
        container_key = 'Farm_Soil_Test_Data' if 'Farm_Soil_Test_Data' in data else 'SP_Lab_Test_Report'
    else:  # Leaf
        container_key = 'Farm_Leaf_Test_Data' if 'Farm_Leaf_Test_Data' in data else 'SP_Lab_Test_Report'

    if container_key not in data:
        return None

    samples_data = data[container_key]
    if not samples_data:
        return None

    # Calculate averages for each parameter
    averages = {}

    # Get all parameters from first sample to ensure consistent order
    first_sample = next(iter(samples_data.values()))
    params = list(first_sample.keys())

    for param in params:
        values = []
        for sample_id, sample_params in samples_data.items():
            if param in sample_params:
                value = sample_params[param]
                if isinstance(value, (int, float)) and not isinstance(value, bool):
                    # Filter out obviously incorrect values
                    if data_type == "Soil":
                        if abs(value) < 10000:  # Reasonable upper limit for soil
                            values.append(value)
                    else:  # Leaf
                        if abs(value) < 100:  # Reasonable upper limit for leaf
                            values.append(value)

        if values:
            avg = sum(values) / len(values)
            averages[param] = avg

    # Format for LLM use
    result_lines = [f"{data_type} Parameter Averages Across All Samples:"]
    result_lines.append(f"Total Samples: {len(samples_data)}")
    result_lines.append("")

    for param, avg in averages.items():
        result_lines.append(f"  {param}: {avg:.3f}")

    return "\n".join(result_lines)


def display_raw_data_tables(results_data):
    """Display raw soil and leaf data tables with clean formatting"""
    st.markdown("---")
    st.markdown("## 📊 Raw Laboratory Data")

    # Display Structured OCR Data from Upload Page
    display_structured_ocr_data()

    # Get analysis data
    analysis_results = get_analysis_results_from_data(results_data)

    # Try to get raw data from multiple possible locations
    raw_data = analysis_results.get('raw_data', {})
    raw_ocr_data = analysis_results.get('raw_ocr_data', {})

    # Extract soil and leaf parameters from different possible structures
    soil_params = {}
    leaf_params = {}

    # Check if raw_data has the expected structure (from analysis engine)
    if raw_data.get('soil_parameters') or raw_data.get('leaf_parameters'):
        soil_params = raw_data.get('soil_parameters', {})
        leaf_params = raw_data.get('leaf_parameters', {})

        # Ensure samples are available in the right format
        if 'all_samples' in soil_params and not soil_params.get('samples'):
            soil_params['samples'] = soil_params['all_samples']
        if 'all_samples' in leaf_params and not leaf_params.get('samples'):
            leaf_params['samples'] = leaf_params['all_samples']

    # Check if raw_ocr_data has the data (from analysis engine or upload processing)
    elif raw_ocr_data.get('soil_data') or raw_ocr_data.get('leaf_data'):
        soil_params = raw_ocr_data.get('soil_data', {})
        leaf_params = raw_ocr_data.get('leaf_data', {})

        # Ensure samples are available in the right format
        if 'all_samples' in soil_params and not soil_params.get('samples'):
            soil_params['samples'] = soil_params['all_samples']
        if 'all_samples' in leaf_params and not leaf_params.get('samples'):
            leaf_params['samples'] = leaf_params['all_samples']

    # Also check if there's data directly in results_data
    if not soil_params and results_data.get('soil_data'):
        soil_params = results_data['soil_data']
        logger.info(f"Using soil data from results_data: {len(soil_params.get('samples', []))} samples")
    if not leaf_params and results_data.get('leaf_data'):
        leaf_params = results_data['leaf_data']
        logger.info(f"Using leaf data from results_data: {len(leaf_params.get('samples', []))} samples")

        # Soil and Leaf analysis data tables removed as requested


def display_average_data_tables(results_data):
    """Display average parameter values for soil and leaf data with MPOB standards comparison"""
    st.markdown("---")
    st.markdown("## 📈 Parameter Averages & Standards Compliance")

    # Get analysis data
    analysis_results = get_analysis_results_from_data(results_data)

    # Try to get raw data from multiple possible locations
    raw_data = analysis_results.get('raw_data', {})
    raw_ocr_data = analysis_results.get('raw_ocr_data', {})

    # Extract soil and leaf parameters from different possible structures
    soil_params = {}
    leaf_params = {}

    # Check if raw_data has the expected structure (from analysis engine)
    if raw_data.get('soil_parameters') or raw_data.get('leaf_parameters'):
        soil_params = raw_data.get('soil_parameters', {})
        leaf_params = raw_data.get('leaf_parameters', {})

        # Ensure samples are available in the right format
        if 'all_samples' in soil_params and not soil_params.get('samples'):
            soil_params['samples'] = soil_params['all_samples']
        if 'all_samples' in leaf_params and not leaf_params.get('samples'):
            leaf_params['samples'] = leaf_params['all_samples']

    # Check if raw_ocr_data has the data (from analysis engine or upload processing)
    elif raw_ocr_data.get('soil_data') or raw_ocr_data.get('leaf_data'):
        soil_params = raw_ocr_data.get('soil_data', {})
        leaf_params = raw_ocr_data.get('leaf_data', {})

        # Ensure samples are available in the right format
        if 'all_samples' in soil_params and not soil_params.get('samples'):
            soil_params['samples'] = soil_params['all_samples']
        if 'all_samples' in leaf_params and not leaf_params.get('samples'):
            leaf_params['samples'] = leaf_params['all_samples']

    # Also check if there's data directly in results_data
    if not soil_params and results_data.get('soil_data'):
        soil_params = results_data['soil_data']
    if not leaf_params and results_data.get('leaf_data'):
        leaf_params = results_data['leaf_data']

    # MPOB Standards - Accurate values for Malaysian Oil Palm cultivation (matching actual data format)
    soil_standards = {
        'pH': {'optimal': 5.0, 'low': '<4.5', 'high': '>6.0', 'range': '4.5-6.0'},
        'N (%)': {'optimal': 0.20, 'low': '<0.15', 'high': '>0.25', 'range': '0.15-0.25'},
        'Org. C (%)': {'optimal': 2.0, 'low': '<1.5', 'high': '>2.5', 'range': '1.5-2.5'},
        'Total P (mg/kg)': {'optimal': 20, 'low': '<15', 'high': '>25', 'range': '15-25'},
        'Avail P (mg/kg)': {'optimal': 15, 'low': '<10', 'high': '>20', 'range': '10-20'},
        'Exch. K (meq%)': {'optimal': 0.30, 'low': '<0.20', 'high': '>0.40', 'range': '0.20-0.40'},
        'Exch. Ca (meq%)': {'optimal': 3.0, 'low': '<2.0', 'high': '>4.0', 'range': '2.0-4.0'},
        'Exch. Mg (meq%)': {'optimal': 0.9, 'low': '<0.6', 'high': '>1.2', 'range': '0.6-1.2'},
        'Exch. K meq%': {'optimal': 0.30, 'low': '<0.20', 'high': '>0.40', 'range': '0.20-0.40'},
        'Exch. Ca meq%': {'optimal': 3.0, 'low': '<2.0', 'high': '>4.0', 'range': '2.0-4.0'},
        'Exch. Mg meq%': {'optimal': 0.9, 'low': '<0.6', 'high': '>1.2', 'range': '0.6-1.2'},
        'CEC (meq%)': {'optimal': 20, 'low': '<15', 'high': '>25', 'range': '15-25'}
    }

    leaf_standards = {
        'N (%)': {'optimal': 2.6, 'low': '<2.4', 'high': '>2.8', 'range': '2.4-2.8'},
        'P (%)': {'optimal': 0.17, 'low': '<0.14', 'high': '>0.20', 'range': '0.14-0.20'},
        'K (%)': {'optimal': 1.1, 'low': '<0.9', 'high': '>1.3', 'range': '0.9-1.3'},
        'Mg (%)': {'optimal': 0.35, 'low': '<0.25', 'high': '>0.45', 'range': '0.25-0.45'},
        'Ca (%)': {'optimal': 0.7, 'low': '<0.5', 'high': '>0.9', 'range': '0.5-0.9'},
        'B (mg/kg)': {'optimal': 23, 'low': '<18', 'high': '>28', 'range': '18-28'},
        'Cu (mg/kg)': {'optimal': 13, 'low': '<8', 'high': '>18', 'range': '8-18'},
        'Zn (mg/kg)': {'optimal': 26, 'low': '<18', 'high': '>35', 'range': '18-35'}
    }

    # Display soil averages
    if soil_params and soil_params.get('samples'):
        st.markdown("### 🌱 Soil Parameters - Average Values & Standards")
        soil_samples = soil_params.get('samples', [])

        if soil_samples:
            # Calculate averages
            soil_averages = {}
            for param in soil_standards.keys():
                values = []
                for sample in soil_samples:
                    # Try multiple parameter name variations
                    val = None

                    # Direct match first
                    if param in sample:
                        val = sample[param]
                    # Try alternative names
                    elif param == 'N (%)' and 'Nitrogen (%)' in sample:
                        val = sample['Nitrogen (%)']
                    elif param == 'N (%)' and 'Nitrogen_%' in sample:
                        val = sample['Nitrogen_%']
                    elif param == 'Org. C (%)' and 'Organic Carbon (%)' in sample:
                        val = sample['Organic Carbon (%)']
                    elif param == 'Org. C (%)' and 'Organic_Carbon_%' in sample:
                        val = sample['Organic_Carbon_%']
                    elif param == 'Total P (mg/kg)' and 'Total_P_mg_kg' in sample:
                        val = sample['Total_P_mg_kg']
                    elif param == 'Avail P (mg/kg)' and 'Available P (mg/kg)' in sample:
                        val = sample['Available P (mg/kg)']
                    elif param == 'Avail P (mg/kg)' and 'Available_P_mg_kg' in sample:
                        val = sample['Available_P_mg_kg']
                    elif param == 'Exch. K (meq%)' and 'Exchangeable K (meq%)' in sample:
                        val = sample['Exchangeable K (meq%)']
                    elif param == 'Exch. K (meq%)' and 'Exchangeable_K_meq%' in sample:
                        val = sample['Exchangeable_K_meq%']
                    elif param == 'Exch. K (meq%)' and 'Exch. K meq%' in sample:
                        val = sample['Exch. K meq%']
                    elif param == 'Exch. K (meq%)' and 'Exch. K (meq%)' in sample:
                        val = sample['Exch. K (meq%)']
                    elif param == 'Exch. Ca (meq%)' and 'Exchangeable Ca (meq%)' in sample:
                        val = sample['Exchangeable Ca (meq%)']
                    elif param == 'Exch. Ca (meq%)' and 'Exchangeable_Ca_meq%' in sample:
                        val = sample['Exchangeable_Ca_meq%']
                    elif param == 'Exch. Ca (meq%)' and 'Exch. Ca meq%' in sample:
                        val = sample['Exch. Ca meq%']
                    elif param == 'Exch. Ca (meq%)' and 'Exch. Ca (meq%)' in sample:
                        val = sample['Exch. Ca (meq%)']
                    elif param == 'Exch. Mg (meq%)' and 'Exchangeable Mg (meq%)' in sample:
                        val = sample['Exchangeable Mg (meq%)']
                    elif param == 'Exch. Mg (meq%)' and 'Exchangeable_Mg_meq%' in sample:
                        val = sample['Exchangeable_Mg_meq%']
                    elif param == 'Exch. Mg (meq%)' and 'Exch. Mg meq%' in sample:
                        val = sample['Exch. Mg meq%']
                    elif param == 'Exch. Mg (meq%)' and 'Exch. Mg (meq%)' in sample:
                        val = sample['Exch. Mg (meq%)']
                    elif param == 'CEC (meq%)' and 'C.E.C (meq%)' in sample:
                        val = sample['C.E.C (meq%)']
                    elif param == 'CEC (meq%)' and 'CEC_meq%' in sample:
                        val = sample['CEC_meq%']

                    # Try to convert to float and add to values list
                    if val is not None and val != 'N/A' and val != '':
                        try:
                            float_val = float(val)
                            # Skip obviously wrong values (like the 2025.000 values we saw)
                            if abs(float_val) < 10000:  # Reasonable upper limit
                                values.append(float_val)
                        except (ValueError, TypeError):
                            pass

                if values:
                    soil_averages[param] = sum(values) / len(values)
                else:
                    soil_averages[param] = 'N/A'

            # Create averages table with standards
            soil_avg_data = []
            for param, avg_val in soil_averages.items():
                standards = soil_standards.get(param, {})
                status = "❓ Unknown"

                if avg_val != 'N/A':
                    try:
                        avg_float = float(avg_val)
                        if 'optimal' in standards:
                            optimal_val = standards['optimal']
                            # Handle both numeric optimal value and string range
                            if isinstance(optimal_val, (int, float)):
                                # Use the numeric optimal value for comparison
                                if 'low' in standards and 'high' in standards:
                                    low_str = standards['low'].replace('<', '')
                                    high_str = standards['high'].replace('>', '')
                                    try:
                                        min_val = float(low_str)
                                        max_val = float(high_str)
                                        if avg_float >= min_val and avg_float <= max_val:
                                            status = "✅ Optimal"
                                        elif avg_float < min_val:
                                            status = "⚠️ Low"
                                        else:
                                            status = "⚠️ High"
                                    except (ValueError, TypeError):
                                        status = "❓ Unknown"
                                else:
                                    status = "❓ Unknown"
                            elif isinstance(optimal_val, str) and '-' in optimal_val:
                                # Handle legacy range format
                                min_val, max_val = map(float, optimal_val.split('-'))
                                if avg_float >= min_val and avg_float <= max_val:
                                    status = "✅ Optimal"
                                elif avg_float < min_val:
                                    status = "⚠️ Low"
                                else:
                                    status = "⚠️ High"
                    except (ValueError, TypeError):
                        pass

                # Display min-max range instead of optimal value only
                min_val = standards.get('min', 'N/A')
                max_val = standards.get('max', 'N/A')
                if min_val != 'N/A' and max_val != 'N/A':
                    optimal_display = f"{min_val}-{max_val}"
                else:
                    # Fallback to range if available, otherwise optimal
                    range_val = standards.get('range', standards.get('optimal', 'N/A'))
                    optimal_display = str(range_val) if range_val != 'N/A' else 'N/A'

                soil_avg_data.append({
                    'Parameter': param.replace('_', ' ').replace('%', '(%)').replace('mg_kg', '(mg/kg)').replace('meq', '(meq)'),
                    'Average Value': f"{avg_val:.3f}" if avg_val != 'N/A' else 'N/A',
                    'MPOB Optimal Range': optimal_display,
                    'Status': status
                })

            # Display table
            import pandas as pd
            soil_avg_df = pd.DataFrame(soil_avg_data)
            st.dataframe(soil_avg_df, use_container_width=True, hide_index=True)

    # Display leaf averages
    if leaf_params and leaf_params.get('samples'):
        st.markdown("### 🍃 Leaf Parameters - Average Values & Standards")
        leaf_samples = leaf_params.get('samples', [])

        if leaf_samples:
            # Calculate averages
            leaf_averages = {}
            for param in leaf_standards.keys():
                values = []
                for sample in leaf_samples:
                    # Try multiple parameter name variations
                    val = None

                    # Direct match first
                    if param in sample:
                        val = sample[param]
                    # Try alternative names with comprehensive matching
                    elif param == 'N (%)':
                        # Try multiple possible names for Nitrogen
                        for name in ['N_%', 'Nitrogen (%)', 'Nitrogen_%', 'N', 'Nitrogen']:
                            if name in sample:
                                val = sample[name]
                                break
                    elif param == 'P (%)':
                        # Try multiple possible names for Phosphorus
                        for name in ['P_%', 'Phosphorus (%)', 'Phosphorus_%', 'P', 'Phosphorus']:
                            if name in sample:
                                val = sample[name]
                                break
                    elif param == 'K (%)':
                        # Try multiple possible names for Potassium
                        for name in ['K_%', 'Potassium (%)', 'Potassium_%', 'K', 'Potassium']:
                            if name in sample:
                                val = sample[name]
                                break
                    elif param == 'Mg (%)':
                        # Try multiple possible names for Magnesium
                        for name in ['Mg_%', 'Magnesium (%)', 'Magnesium_%', 'Mg', 'Magnesium']:
                            if name in sample:
                                val = sample[name]
                                break
                    elif param == 'Ca (%)':
                        # Try multiple possible names for Calcium
                        for name in ['Ca_%', 'Calcium (%)', 'Calcium_%', 'Ca', 'Calcium']:
                            if name in sample:
                                val = sample[name]
                                break
                    elif param == 'B (mg/kg)':
                        # Try multiple possible names for Boron
                        for name in ['B_mg_kg', 'B (mg/kg)', 'Boron (mg/kg)', 'Boron_mg_kg', 'B', 'Boron']:
                            if name in sample:
                                val = sample[name]
                                break
                    elif param == 'Cu (mg/kg)':
                        # Try multiple possible names for Copper
                        for name in ['Cu_mg_kg', 'Cu (mg/kg)', 'Copper (mg/kg)', 'Copper_mg_kg', 'Cu', 'Copper']:
                            if name in sample:
                                val = sample[name]
                                break
                    elif param == 'Zn (mg/kg)':
                        # Try multiple possible names for Zinc
                        for name in ['Zn_mg_kg', 'Zn (mg/kg)', 'Zinc (mg/kg)', 'Zinc_mg_kg', 'Zn', 'Zinc']:
                            if name in sample:
                                val = sample[name]
                                break

                    # Try to convert to float and add to values list
                    if val is not None and val != 'N/A' and val != '':
                        try:
                            float_val = float(val)
                            # Skip obviously wrong values (like the 2025.000 values we saw)
                            if abs(float_val) < 100:  # Reasonable upper limit for leaf nutrients
                                values.append(float_val)
                        except (ValueError, TypeError):
                            pass

                if values:
                    leaf_averages[param] = sum(values) / len(values)
                else:
                    leaf_averages[param] = 'N/A'

            # Create averages table with standards
            leaf_avg_data = []
            for param, avg_val in leaf_averages.items():
                standards = leaf_standards.get(param, {})
                status = "❓ Unknown"

                if avg_val != 'N/A':
                    try:
                        avg_float = float(avg_val)
                        if 'optimal' in standards:
                            optimal_val = standards['optimal']
                            # Handle both numeric optimal value and string range
                            if isinstance(optimal_val, (int, float)):
                                # Use the numeric optimal value for comparison
                                if 'low' in standards and 'high' in standards:
                                    low_str = standards['low'].replace('<', '')
                                    high_str = standards['high'].replace('>', '')
                                    try:
                                        min_val = float(low_str)
                                        max_val = float(high_str)
                                        if avg_float >= min_val and avg_float <= max_val:
                                            status = "✅ Optimal"
                                        elif avg_float < min_val:
                                            status = "⚠️ Low"
                                        else:
                                            status = "⚠️ High"
                                    except (ValueError, TypeError):
                                        status = "❓ Unknown"
                                else:
                                    status = "❓ Unknown"
                            elif isinstance(optimal_val, str) and '-' in optimal_val:
                                # Handle legacy range format
                                min_val, max_val = map(float, optimal_val.split('-'))
                                if avg_float >= min_val and avg_float <= max_val:
                                    status = "✅ Optimal"
                                elif avg_float < min_val:
                                    status = "⚠️ Low"
                                else:
                                    status = "⚠️ High"
                    except (ValueError, TypeError):
                        pass

                # Display min-max range instead of optimal value only
                min_val = standards.get('min', 'N/A')
                max_val = standards.get('max', 'N/A')
                if min_val != 'N/A' and max_val != 'N/A':
                    optimal_display = f"{min_val}-{max_val}"
                else:
                    # Fallback to range if available, otherwise optimal
                    range_val = standards.get('range', standards.get('optimal', 'N/A'))
                    optimal_display = str(range_val) if range_val != 'N/A' else 'N/A'

                leaf_avg_data.append({
                    'Parameter': param.replace('_', ' ').replace('%', '(%)').replace('mg_kg', '(mg/kg)'),
                    'Average Value': f"{avg_val:.3f}" if avg_val != 'N/A' else 'N/A',
                    'MPOB Optimal Range': optimal_display,
                    'Status': status
                })

            # Display table
            import pandas as pd
            leaf_avg_df = pd.DataFrame(leaf_avg_data)
            st.dataframe(leaf_avg_df, use_container_width=True, hide_index=True)


