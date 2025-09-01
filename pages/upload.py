import streamlit as st
import sys
import os
from datetime import datetime
from PIL import Image
import io
import base64
import pandas as pd
from google.cloud import firestore
import plotly.graph_objects as go
import plotly.express as px

# Add utils to path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'utils'))

# Import utilities
from utils.ocr_utils import extract_data_from_image
from utils.analysis_engine import analyze_lab_data
from utils.pdf_utils import PDFReportGenerator
from utils.firebase_config import get_firestore_client, get_storage_bucket, COLLECTIONS

def show_upload_page():
    """Main upload and analysis page"""
    # Check authentication at page level
    if not st.session_state.get('authenticated', False):
        st.markdown('<h1 style="color: #2E8B57; text-align: center;">📤 Upload & Analyze SP LAB Reports</h1>', unsafe_allow_html=True)
        st.warning("🔒 Please log in to access upload and analysis features.")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔑 Login", type="primary", use_container_width=True):
                st.session_state.current_page = 'login'
                st.rerun()
        with col2:
            if st.button("📝 Register", use_container_width=True):
                st.session_state.current_page = 'register'
                st.rerun()
        return
    
    st.markdown('<h1 style="color: #2E8B57; text-align: center;">📤 Upload & Analyze SP LAB Reports</h1>', unsafe_allow_html=True)
    
    # Create tabs - conditionally include history for authenticated users
    if st.session_state.get('authenticated', False):
        tab1, tab2, tab3 = st.tabs(["📊 Upload Report", "🔍 Analysis Results", "📋 Report History"])
    else:
        tab1, tab2 = st.tabs(["📊 Upload Report", "🔍 Analysis Results"])
    
    with tab1:
        upload_section()
    
    with tab2:
        if 'current_analysis' in st.session_state:
            display_analysis_results()
        else:
            st.info("Upload and analyze a report to see results here.")
    
    # Only show history tab for authenticated users
    if st.session_state.get('authenticated', False):
        with tab3:
            display_report_history()

def main():
    """Wrapper function for backward compatibility"""
    # Initialize session state if not already done
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 'upload'
    
    show_upload_page()

def upload_section():
    """Handle file upload and processing"""
    
    # Check authentication before allowing upload
    if not st.session_state.get('authenticated', False):
        st.warning("🔒 Please log in to upload and analyze files.")
        if st.button("🔑 Login to Continue", type="primary", use_container_width=True):
            st.session_state.current_page = 'login'
            st.rerun()
        return
    
    st.markdown("### 📁 Upload SP LAB Test Report")
    
    # Create separate containers for soil and leaf analysis
    col1, col2 = st.columns(2)
    
    # Initialize session state for uploaded files
    if 'soil_file' not in st.session_state:
        st.session_state.soil_file = None
    if 'leaf_file' not in st.session_state:
        st.session_state.leaf_file = None
    
    with col1:
        with st.container():
            st.markdown("#### 🌱 Soil Analysis")
            st.markdown("Upload soil test reports for nutrient analysis and recommendations")
            
            soil_file = st.file_uploader(
                "Choose soil analysis image",
                type=['png', 'jpg', 'jpeg'],
                help="Upload clear images of SP LAB soil analysis reports",
                key="soil_uploader"
            )
            
            if soil_file is not None:
                st.session_state.soil_file = soil_file
                # Display uploaded image
                st.markdown("##### 🖼️ Uploaded Soil Report")
                soil_image = Image.open(soil_file)
                st.image(soil_image, caption="Soil Analysis Report", use_container_width=True)
                
                # Image info
                st.info(f"**File:** {soil_file.name}\n**Size:** {soil_file.size} bytes\n**Format:** {soil_image.format}")
                
                # Preview OCR capability
                with st.expander("🔍 Preview OCR Extraction"):
                    try:
                        # Quick OCR preview
                        ocr_preview = extract_data_from_image(soil_image, 'soil')
                        if ocr_preview.get('success'):
                            if ocr_preview.get('data', {}).get('samples'):
                                sample_count = len(ocr_preview['data']['samples'])
                                st.success(f"✅ OCR Preview: {sample_count} samples detected")
                                
                                # Show first sample preview
                                if sample_count > 0:
                                    first_sample = ocr_preview['data']['samples'][0]
                                    st.write("**First Sample Preview:**")
                                    st.json(first_sample)
                            else:
                                st.warning("⚠️ OCR Preview: No samples detected")
                        else:
                            st.error(f"❌ OCR Preview Failed: {ocr_preview.get('error', 'Unknown error')}")
                    except Exception as e:
                        st.error(f"❌ OCR Preview Error: {str(e)}")
    
    with col2:
        with st.container():
            st.markdown("#### 🍃 Leaf Analysis")
            st.markdown("Upload leaf test reports for nutrient deficiency analysis")
            
            leaf_file = st.file_uploader(
                "Choose leaf analysis image",
                type=['png', 'jpg', 'jpeg'],
                help="Upload clear images of SP LAB leaf analysis reports",
                key="leaf_uploader"
            )
            
            if leaf_file is not None:
                st.session_state.leaf_file = leaf_file
                # Display uploaded image
                st.markdown("##### 🖼️ Uploaded Leaf Report")
                leaf_image = Image.open(leaf_file)
                st.image(leaf_image, caption="Leaf Analysis Report", use_container_width=True)
                
                # Image info
                st.info(f"**File:** {leaf_file.name}\n**Size:** {leaf_file.size} bytes\n**Format:** {leaf_image.format}")
                
                # Preview OCR capability
                with st.expander("🔍 Preview OCR Extraction"):
                    try:
                        # Quick OCR preview
                        ocr_preview = extract_data_from_image(leaf_image, 'leaf')
                        if ocr_preview.get('success'):
                            if ocr_preview.get('data', {}).get('samples'):
                                sample_count = len(ocr_preview['data']['samples'])
                                st.success(f"✅ OCR Preview: {sample_count} samples detected")
                                
                                # Show first sample preview
                                if sample_count > 0:
                                    first_sample = ocr_preview['data']['samples'][0]
                                    st.write("**First Sample Preview:**")
                                    st.json(first_sample)
                            else:
                                st.warning("⚠️ OCR Preview: No samples detected")
                        else:
                            st.error(f"❌ OCR Preview Failed: {ocr_preview.get('error', 'Unknown error')}")
                    except Exception as e:
                        st.error(f"❌ OCR Preview Error: {str(e)}")
    
    # Land/Yield Size Data Section
    st.markdown("---")
    st.markdown("### 🌾 Land & Yield Information")
    st.markdown("*This information is crucial for accurate economic forecasting and yield predictions*")
    
    # Initialize session state for land/yield data
    if 'land_size' not in st.session_state:
        st.session_state.land_size = 0
    if 'land_unit' not in st.session_state:
        st.session_state.land_unit = 'hectares'
    if 'current_yield' not in st.session_state:
        st.session_state.current_yield = 0
    if 'yield_unit' not in st.session_state:
        st.session_state.yield_unit = 'tonnes/hectare'
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📏 Land Size")
        land_size = st.number_input(
            "Land Size",
            min_value=0,
            max_value=10000,
            value=st.session_state.land_size,
            step=1,
            help="Enter the total land area for analysis",
            key="land_size_input"
        )
        land_unit = st.selectbox(
            "Unit",
            options=['hectares', 'acres', 'square_meters'],
            index=['hectares', 'acres', 'square_meters'].index(st.session_state.land_unit),
            key="land_unit_input"
        )
        st.session_state.land_size = land_size
        st.session_state.land_unit = land_unit
    
    with col2:
        st.markdown("#### 🌾 Current Yield")
        current_yield = st.number_input(
            "Current Yield",
            min_value=0,
            max_value=1000,
            value=st.session_state.current_yield,
            step=1,
            help="Enter the current yield per unit area",
            key="current_yield_input"
        )
        yield_unit = st.selectbox(
            "Yield Unit",
            options=['tonnes/hectare', 'kg/hectare', 'tonnes/acre', 'kg/acre'],
            index=['tonnes/hectare', 'kg/hectare', 'tonnes/acre', 'kg/acre'].index(st.session_state.yield_unit),
            key="yield_unit_input"
        )
        st.session_state.current_yield = current_yield
        st.session_state.yield_unit = yield_unit
    
    # Display summary of entered data
    if land_size > 0 or current_yield > 0:
        st.info(f"📊 **Summary:** {land_size} {land_unit} | {current_yield} {yield_unit}")
    
    # Single analysis button for both files
    st.markdown("---")
    if st.session_state.soil_file is not None or st.session_state.leaf_file is not None:
        # Double-check authentication before processing
        if not st.session_state.get('authenticated', False):
            st.error("🔒 Authentication required to analyze reports. Please log in.")
            if st.button("🔑 Login to Analyze", type="primary", use_container_width=True):
                st.session_state.current_page = 'login'
                st.rerun()
        elif st.button("🚀 Analyze Both Reports", type="primary", use_container_width=True, key="process_both"):
            # Prepare land/yield data
            land_yield_data = {
                'land_size': st.session_state.land_size,
                'land_unit': st.session_state.land_unit,
                'current_yield': st.session_state.current_yield,
                'yield_unit': st.session_state.yield_unit
            }
            process_both_reports(st.session_state.soil_file, st.session_state.leaf_file, land_yield_data)
    
        

def process_both_reports(soil_file, leaf_file, land_yield_data=None):
    """Process both soil and leaf reports together with land/yield data"""
    
    with st.spinner("Processing both reports... This may take a few moments."):
        try:
            results = {}
            
            # Process soil file if available
            if soil_file is not None:
                st.write("🌱 **Processing Soil Report...**")
                with st.spinner("Extracting soil data using OCR..."):
                    soil_image = Image.open(soil_file)
                    soil_result = process_single_report(soil_file, soil_image, "Soil Analysis")
                    if soil_result:
                        results['soil'] = soil_result
                        
                        # Show detailed extraction results
                        ocr_result = soil_result.get('ocr_result', {})
                        if ocr_result.get('success'):
                            if ocr_result.get('data', {}).get('samples'):
                                sample_count = len(ocr_result['data']['samples'])
                                st.success(f"✅ Soil analysis completed - {sample_count} samples extracted")
                                
                                # Show sample overview
                                with st.expander("📊 Soil Samples Overview"):
                                    samples = ocr_result['data']['samples']
                                    for i, sample in enumerate(samples[:5]):  # Show first 5
                                        st.write(f"**Sample {i+1}:** {len(sample)} parameters")
                                    if len(samples) > 5:
                                        st.write(f"... and {len(samples) - 5} more samples")
                            else:
                                st.success("✅ Soil analysis completed")
                        else:
                            st.error(f"❌ Soil OCR failed: {ocr_result.get('error', 'Unknown error')}")
                    else:
                        st.error("❌ Soil analysis failed")
            
            # Process leaf file if available
            if leaf_file is not None:
                st.write("🍃 **Processing Leaf Report...**")
                with st.spinner("Extracting leaf data using OCR..."):
                    leaf_image = Image.open(leaf_file)
                    leaf_result = process_single_report(leaf_file, leaf_image, "Leaf Analysis")
                    if leaf_result:
                        results['leaf'] = leaf_result
                        
                        # Show detailed extraction results
                        ocr_result = leaf_result.get('ocr_result', {})
                        if ocr_result.get('success'):
                            if ocr_result.get('data', {}).get('samples'):
                                sample_count = len(ocr_result['data']['samples'])
                                st.success(f"✅ Leaf analysis completed - {sample_count} samples extracted")
                                
                                # Show sample overview
                                with st.expander("📊 Leaf Samples Overview"):
                                    samples = ocr_result['data']['samples']
                                    for i, sample in enumerate(samples[:5]):  # Show first 5
                                        st.write(f"**Sample {i+1}:** {len(sample)} parameters")
                                    if len(samples) > 5:
                                        st.write(f"... and {len(samples) - 5} more samples")
                            else:
                                st.success("✅ Leaf analysis completed")
                        else:
                            st.error(f"❌ Leaf OCR failed: {ocr_result.get('error', 'Unknown error')}")
                    else:
                        st.error("❌ Leaf analysis failed")
            
            if results:
                # Add land/yield data to results
                if land_yield_data:
                    results['land_yield_data'] = land_yield_data
                    st.write(f"🌾 **Land/Yield Data:** {land_yield_data['land_size']} {land_yield_data['land_unit']} | {land_yield_data['current_yield']} {land_yield_data['yield_unit']}")
                
                # Generate combined analysis using active prompt from database
                st.write("🧠 **Generating Combined Analysis...**")
                combined_analysis = generate_combined_analysis(results)
                
                # Save combined results
                st.write("💾 **Saving Combined Results...**")
                analysis_id = save_combined_analysis_to_db(results, combined_analysis)
                
                if analysis_id:
                    st.success("✅ Combined analysis saved successfully")
                    
                    # Store in session state for display
                    st.session_state.current_analysis = {
                        'id': analysis_id,
                        'type': 'combined',
                        'soil_data': results.get('soil'),
                        'leaf_data': results.get('leaf'),
                        'land_yield_data': land_yield_data,
                        'combined_analysis': combined_analysis,
                        'timestamp': datetime.now()
                    }
                    
                    st.balloons()
                    st.success("🎉 Combined analysis completed! Check the 'Analysis Results' tab.")
                else:
                    st.error("Failed to save combined results to database")
            else:
                st.error("No valid data could be extracted from the uploaded files")
                
        except Exception as e:
            st.error(f"Processing error: {str(e)}")

def process_single_report(uploaded_file, image, report_type):
    """Process a single report and return the results"""
    try:
        # Convert PIL image to bytes
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='PNG')
        img_byte_arr = img_byte_arr.getvalue()
        
        # Perform OCR using the imported function with specific report type
        pil_image = Image.open(io.BytesIO(img_byte_arr))
        ocr_result = extract_data_from_image(pil_image, report_type.lower())
        
        if not ocr_result.get('success', False):
            st.error(f"OCR processing failed for {report_type}: {ocr_result.get('error', 'Unknown error')}")
            return None
        
        # Log OCR extraction results
        st.info(f"✅ {report_type} OCR completed successfully")
        if ocr_result.get('data', {}).get('samples'):
            sample_count = len(ocr_result['data']['samples'])
            st.info(f"📊 Extracted {sample_count} samples from {report_type} report")
        elif ocr_result.get('parameters'):
            param_count = len(ocr_result['parameters'])
            st.info(f"📊 Extracted {param_count} parameters from {report_type} report")
        
        # Use the imported analyze_lab_data function
        analysis_options = {
            'include_economic': True,
            'include_forecast': True,
            'detailed_recommendations': True
        }
        
        analysis_result = analyze_lab_data(
            ocr_result,
            analysis_options
        )
        
        return {
            'filename': uploaded_file.name,
            'report_type': report_type,
            'ocr_result': ocr_result,
            'analysis_result': analysis_result,
            'image_data': img_byte_arr
        }
        
    except Exception as e:
        st.error(f"Error processing {report_type}: {str(e)}")
        return None

def generate_combined_analysis(results):
    """Generate comprehensive combined analysis using active prompt from database"""
    try:
        from utils.firebase_config import get_firestore_client
        from utils.analysis_engine import analyze_lab_data
        
        db = get_firestore_client()
        
        # Fetch active prompt
        prompts_ref = db.collection('prompts')
        active_prompt_query = prompts_ref.where('is_active', '==', True).limit(1)
        active_prompt_docs = list(active_prompt_query.stream())
        
        if not active_prompt_docs:
            return {'error': 'No active prompt found in database'}
        
        active_prompt = active_prompt_docs[0].to_dict()
        prompt_text = active_prompt.get('prompt_text', '')
        
        # Prepare data for comprehensive analysis
        soil_data = results.get('soil', {}).get('ocr_result', {})
        leaf_data = results.get('leaf', {}).get('ocr_result', {})
        land_yield_data = results.get('land_yield_data', {})
        
        # Execute comprehensive analysis for both soil and leaf data
        analysis_options = {
            'include_economic': True,
            'include_forecast': True,
            'detailed_recommendations': True,
            'include_charts': True,
            'land_yield_data': land_yield_data  # Include land/yield data for economic forecasting
        }
        
        soil_analysis = None
        leaf_analysis = None
        
        # Analyze soil data if available
        if soil_data.get('data', {}).get('samples'):
            soil_extracted = {
                'report_type': 'soil',
                'samples': soil_data.get('data', {}).get('samples', [])
            }
            soil_analysis = analyze_lab_data(soil_extracted, analysis_options)
            st.success(f"✅ Soil analysis completed with {len(soil_data['data']['samples'])} samples")
        elif soil_data.get('parameters'):
            # Fallback for old format
            soil_extracted = {
                'report_type': 'soil',
                'parameters': soil_data.get('parameters', [])
            }
            soil_analysis = analyze_lab_data(soil_extracted, analysis_options)
            st.success(f"✅ Soil analysis completed with {len(soil_data['parameters'])} parameters")
        
        # Analyze leaf data if available
        if leaf_data.get('data', {}).get('samples'):
            leaf_extracted = {
                'report_type': 'leaf', 
                'samples': leaf_data.get('data', {}).get('samples', [])
            }
            leaf_analysis = analyze_lab_data(leaf_extracted, analysis_options)
            st.success(f"✅ Leaf analysis completed with {len(leaf_data['data']['samples'])} samples")
        elif leaf_data.get('parameters'):
            # Fallback for old format
            leaf_extracted = {
                'report_type': 'leaf', 
                'parameters': leaf_data.get('parameters', [])
            }
            leaf_analysis = analyze_lab_data(leaf_extracted, analysis_options)
            st.success(f"✅ Leaf analysis completed with {len(leaf_data['parameters'])} parameters")
        
        # Query reference documents for supporting information
        reference_docs = query_reference_documents(soil_analysis, leaf_analysis)
        
        # Generate comprehensive combined analysis
        combined_analysis = {
            'prompt_used': active_prompt,
            'soil_analysis': soil_analysis,
            'leaf_analysis': leaf_analysis,
            'land_yield_data': land_yield_data,
            'reference_documents': reference_docs,
            'comprehensive_results': generate_comprehensive_results(soil_analysis, leaf_analysis, prompt_text, land_yield_data),
            'key_findings': extract_key_findings(soil_analysis, leaf_analysis),
            'economic_forecast': combine_economic_forecasts(soil_analysis, leaf_analysis, land_yield_data),
            'yield_forecast': generate_combined_yield_forecast(soil_analysis, leaf_analysis, land_yield_data),
            'recommendations': generate_comprehensive_recommendations(soil_analysis, leaf_analysis, prompt_text),
            'summary': generate_executive_summary(soil_analysis, leaf_analysis),
            'analysis_timestamp': datetime.now().isoformat()
        }
        
        return combined_analysis
        
    except Exception as e:
        st.error(f"Error generating combined analysis: {str(e)}")
        return {'error': str(e)}

def query_reference_documents(soil_analysis, leaf_analysis):
    """Query Firestore reference_documents collection using relevant keywords from detected issues"""
    try:
        from utils.firebase_config import get_firestore_client, COLLECTIONS
        
        db = get_firestore_client()
        if not db:
            return []
        
        reference_docs = []
        keywords = set()
        issue_categories = set()
        
        # Enhanced keyword extraction from soil analysis
        if soil_analysis and soil_analysis.get('issues'):
            for issue in soil_analysis['issues']:
                param = issue.get('parameter', '').lower()
                severity = issue.get('severity', 'medium').lower()
                
                # Add parameter name
                keywords.add(param)
                
                # Add category-specific keywords
                if 'ph' in param or 'acidity' in param:
                    keywords.update(['ph', 'acidity', 'lime', 'alkaline', 'soil_ph', 'liming'])
                    issue_categories.add('soil_ph')
                elif 'nitrogen' in param or 'n' == param:
                    keywords.update(['nitrogen', 'fertilizer', 'urea', 'nutrient', 'n_deficiency'])
                    issue_categories.add('nitrogen')
                elif 'phosphorus' in param or 'phosphorous' in param or 'p' == param:
                    keywords.update(['phosphorus', 'phosphate', 'dap', 'fertilizer', 'p_deficiency'])
                    issue_categories.add('phosphorus')
                elif 'potassium' in param or 'k' == param:
                    keywords.update(['potassium', 'kcl', 'potash', 'fertilizer', 'k_deficiency'])
                    issue_categories.add('potassium')
                elif 'organic' in param or 'carbon' in param:
                    keywords.update(['organic_matter', 'compost', 'soil_health', 'carbon'])
                    issue_categories.add('organic_matter')
                elif 'calcium' in param or 'ca' == param:
                    keywords.update(['calcium', 'lime', 'gypsum', 'ca_deficiency'])
                    issue_categories.add('calcium')
                elif 'magnesium' in param or 'mg' == param:
                    keywords.update(['magnesium', 'dolomite', 'mg_deficiency'])
                    issue_categories.add('magnesium')
                elif 'cec' in param:
                    keywords.update(['cec', 'cation_exchange', 'soil_fertility'])
                    issue_categories.add('soil_fertility')
                
                # Add severity-based keywords
                if severity == 'high' or severity == 'critical':
                    keywords.add('urgent_treatment')
        
        # Enhanced keyword extraction from leaf analysis
        if leaf_analysis and leaf_analysis.get('issues'):
            for issue in leaf_analysis['issues']:
                param = issue.get('parameter', '').lower()
                severity = issue.get('severity', 'medium').lower()
                
                # Add parameter name
                keywords.add(param)
                
                # Add foliar-specific keywords
                keywords.update(['foliar', 'spray', 'deficiency', 'leaf_analysis'])
                
                # Add nutrient-specific keywords for leaf analysis
                if 'n' == param or 'nitrogen' in param:
                    keywords.update(['foliar_nitrogen', 'leaf_yellowing', 'n_spray'])
                    issue_categories.add('foliar_nitrogen')
                elif 'p' == param or 'phosphorus' in param:
                    keywords.update(['foliar_phosphorus', 'p_spray', 'leaf_purple'])
                    issue_categories.add('foliar_phosphorus')
                elif 'k' == param or 'potassium' in param:
                    keywords.update(['foliar_potassium', 'k_spray', 'leaf_burn'])
                    issue_categories.add('foliar_potassium')
                elif 'mg' == param or 'magnesium' in param:
                    keywords.update(['foliar_magnesium', 'mg_spray', 'chlorosis'])
                    issue_categories.add('foliar_magnesium')
                elif 'ca' == param or 'calcium' in param:
                    keywords.update(['foliar_calcium', 'ca_spray', 'leaf_tip_burn'])
                    issue_categories.add('foliar_calcium')
                elif 'b' == param or 'boron' in param:
                    keywords.update(['boron', 'micronutrient', 'b_deficiency'])
                    issue_categories.add('micronutrients')
                elif 'zn' == param or 'zinc' in param:
                    keywords.update(['zinc', 'micronutrient', 'zn_deficiency'])
                    issue_categories.add('micronutrients')
                elif 'cu' == param or 'copper' in param:
                    keywords.update(['copper', 'micronutrient', 'cu_deficiency'])
                    issue_categories.add('micronutrients')
        
        # Add general palm oil keywords
        keywords.update(['palm_oil', 'oil_palm', 'elaeis_guineensis', 'plantation'])
        
        # Query reference documents using multiple strategies
        if keywords or issue_categories:
            ref_collection = db.collection(COLLECTIONS['reference_documents'])
            doc_scores = {}  # Track document relevance scores
            
            # Strategy 1: Query by keywords array
            for keyword in list(keywords)[:15]:  # Limit to prevent too many queries
                try:
                    docs = ref_collection.where('keywords', 'array_contains', keyword).limit(5).get()
                    
                    for doc in docs:
                        doc_data = doc.to_dict()
                        doc_id = doc.id
                        doc_data['id'] = doc_id
                        
                        # Calculate relevance score
                        score = doc_scores.get(doc_id, 0)
                        score += 1  # Base score for keyword match
                        
                        # Bonus for exact parameter matches
                        if keyword in doc_data.get('title', '').lower():
                            score += 2
                        if keyword in doc_data.get('description', '').lower():
                            score += 1
                        
                        doc_scores[doc_id] = score
                        
                        # Add to results if not already present
                        if not any(d.get('id') == doc_id for d in reference_docs):
                            reference_docs.append(doc_data)
                            
                except Exception as e:
                    print(f"Error querying keyword '{keyword}': {str(e)}")
                    continue
            
            # Strategy 2: Query by category if available
            for category in issue_categories:
                try:
                    docs = ref_collection.where('category', '==', category).limit(3).get()
                    
                    for doc in docs:
                        doc_data = doc.to_dict()
                        doc_id = doc.id
                        doc_data['id'] = doc_id
                        
                        # Higher score for category matches
                        score = doc_scores.get(doc_id, 0)
                        score += 3  # Higher score for category match
                        doc_scores[doc_id] = score
                        
                        # Add to results if not already present
                        if not any(d.get('id') == doc_id for d in reference_docs):
                            reference_docs.append(doc_data)
                            
                except Exception as e:
                    print(f"Error querying category '{category}': {str(e)}")
                    continue
            
            # Sort documents by relevance score
            if doc_scores:
                reference_docs.sort(key=lambda x: doc_scores.get(x.get('id', ''), 0), reverse=True)
        
        # Return top 10 most relevant documents with enhanced metadata
        final_docs = []
        for doc in reference_docs[:10]:
            # Add relevance score to document
            doc['relevance_score'] = doc_scores.get(doc.get('id', ''), 0)
            
            # Ensure required fields exist
            if 'title' not in doc:
                doc['title'] = 'Untitled Document'
            if 'description' not in doc:
                doc['description'] = 'No description available'
            if 'keywords' not in doc:
                doc['keywords'] = []
            
            final_docs.append(doc)
        
        return final_docs
        
    except Exception as e:
        print(f"Error querying reference documents: {str(e)}")
        return []

def generate_comprehensive_results(soil_analysis, leaf_analysis, prompt_text, land_yield_data=None):
    """Generate comprehensive analysis results with detailed metrics, key findings, and economic forecasts"""
    try:
        results = {
            'analysis_metadata': {
                'timestamp': datetime.now().isoformat(),
                'analysis_type': 'comprehensive',
                'prompt_used': prompt_text[:100] + '...' if prompt_text and len(prompt_text) > 100 else prompt_text,
                'data_sources': []
            },
            'summary_metrics': {
                'total_parameters_analyzed': 0,
                'total_issues_identified': 0,
                'critical_issues_count': 0,
                'high_priority_issues_count': 0,
                'medium_priority_issues_count': 0,
                'low_priority_issues_count': 0,
                'soil_health_score': 0,
                'leaf_health_score': 0,
                'overall_health_score': 0,
                'nutrient_balance_score': 0,
                'risk_assessment_score': 0,
                'improvement_potential': 0
            },
            'detailed_analysis': {
                'soil_parameters': {},
                'leaf_parameters': {},
                'nutrient_status': {},
                'deficiency_analysis': {},
                'excess_analysis': {},
                'parameter_correlations': []
            },
            'health_indicators': {
                'critical_issues': [],
                'high_priority_issues': [],
                'medium_priority_issues': [],
                'low_priority_issues': [],
                'positive_indicators': [],
                'improvement_areas': [],
                'risk_factors': []
            },
            'economic_analysis': {
                'total_treatment_cost': 0,
                'cost_breakdown': [],
                'expected_yield_increase': 0,
                'annual_revenue_increase': 0,
                'roi_percentage': 0,
                'payback_months': 0,
                'cost_benefit_ratio': 0
            },
            'yield_forecast': {
                'current_yield_estimate': land_yield_data.get('current_yield', 18.5) if land_yield_data else 18.5,
                'yield_unit': land_yield_data.get('yield_unit', 'tonnes/hectare') if land_yield_data else 'tonnes/hectare',
                'land_size': land_yield_data.get('land_size', 1) if land_yield_data else 1,
                'land_unit': land_yield_data.get('land_unit', 'hectares') if land_yield_data else 'hectares',
                'crop_type': land_yield_data.get('crop_type', 'Unknown') if land_yield_data else 'Unknown',
                'crop_age': land_yield_data.get('crop_age', 'Unknown') if land_yield_data else 'Unknown',
                'projected_yield_improvement': 0,
                'five_year_projection': [],
                'improvement_timeline': {},
                'yield_factors': []
            },
            'data_quality': {
                'soil_data_completeness': 0,
                'leaf_data_completeness': 0,
                'overall_confidence': 0,
                'data_reliability': 'high'
            }
        }
        
        # Track data sources
        if soil_analysis:
            results['analysis_metadata']['data_sources'].append('soil_analysis')
        if leaf_analysis:
            results['analysis_metadata']['data_sources'].append('leaf_analysis')
        
        # Process soil analysis with enhanced metrics
        if soil_analysis:
            soil_params = soil_analysis.get('analysis_results', [])
            soil_issues = soil_analysis.get('issues', [])
            
            results['summary_metrics']['total_parameters_analyzed'] += len(soil_params)
            results['summary_metrics']['total_issues_identified'] += len(soil_issues)
            
            # Categorize soil issues by severity
            soil_critical = []
            soil_high = []
            soil_medium = []
            soil_low = []
            
            for issue in soil_issues:
                severity = issue.get('severity', 'medium').lower()
                issue_detail = {
                    'parameter': issue.get('parameter', 'Unknown'),
                    'issue': issue.get('issue', ''),
                    'description': issue.get('description', ''),
                    'severity': severity,
                    'source': 'soil',
                    'recommendation': issue.get('recommendation', {})
                }
                
                if severity in ['critical', 'high']:
                    results['summary_metrics']['critical_issues_count'] += 1
                    results['summary_metrics']['high_priority_issues_count'] += 1
                    soil_critical.append(issue_detail)
                    results['health_indicators']['critical_issues'].append(issue_detail)
                elif severity == 'medium':
                    results['summary_metrics']['medium_priority_issues_count'] += 1
                    soil_medium.append(issue_detail)
                    results['health_indicators']['medium_priority_issues'].append(issue_detail)
                else:
                    results['summary_metrics']['low_priority_issues_count'] += 1
                    soil_low.append(issue_detail)
                    results['health_indicators']['low_priority_issues'].append(issue_detail)
            
            # Calculate soil health score with weighted parameters
            total_soil_params = len(soil_params) if soil_params else 9
            critical_penalty = len(soil_critical) * 20
            medium_penalty = len(soil_medium) * 10
            low_penalty = len(soil_low) * 5
            
            soil_health_score = max(0, 100 - (critical_penalty + medium_penalty + low_penalty))
            results['summary_metrics']['soil_health_score'] = soil_health_score
            
            # Store detailed soil analysis
            results['detailed_analysis']['soil_parameters'] = {
                'total_tested': total_soil_params,
                'with_issues': len(soil_issues),
                'optimal': total_soil_params - len(soil_issues),
                'critical_issues': soil_critical,
                'medium_issues': soil_medium,
                'low_issues': soil_low,
                'parameters_breakdown': soil_params
            }
            
            # Data quality for soil
            expected_soil_params = ['pH', 'Nitrogen', 'Phosphorus', 'Potassium', 'Organic Carbon', 'CEC', 'Calcium', 'Magnesium']
            actual_soil_params = [p.get('parameter', '') for p in soil_params] if soil_params else []
            soil_completeness = (len(actual_soil_params) / len(expected_soil_params)) * 100
            results['data_quality']['soil_data_completeness'] = min(100, soil_completeness)
        
        # Process leaf analysis with enhanced metrics
        if leaf_analysis:
            leaf_params = leaf_analysis.get('analysis_results', [])
            leaf_issues = leaf_analysis.get('issues', [])
            
            results['summary_metrics']['total_parameters_analyzed'] += len(leaf_params)
            results['summary_metrics']['total_issues_identified'] += len(leaf_issues)
            
            # Categorize leaf issues by severity
            leaf_critical = []
            leaf_high = []
            leaf_medium = []
            leaf_low = []
            
            for issue in leaf_issues:
                severity = issue.get('severity', 'medium').lower()
                issue_detail = {
                    'parameter': issue.get('parameter', 'Unknown'),
                    'issue': issue.get('issue', ''),
                    'description': issue.get('description', ''),
                    'severity': severity,
                    'source': 'leaf',
                    'recommendation': issue.get('recommendation', {})
                }
                
                if severity in ['critical', 'high']:
                    results['summary_metrics']['critical_issues_count'] += 1
                    results['summary_metrics']['high_priority_issues_count'] += 1
                    leaf_critical.append(issue_detail)
                    results['health_indicators']['critical_issues'].append(issue_detail)
                elif severity == 'medium':
                    results['summary_metrics']['medium_priority_issues_count'] += 1
                    leaf_medium.append(issue_detail)
                    results['health_indicators']['medium_priority_issues'].append(issue_detail)
                else:
                    results['summary_metrics']['low_priority_issues_count'] += 1
                    leaf_low.append(issue_detail)
                    results['health_indicators']['low_priority_issues'].append(issue_detail)
            
            # Calculate leaf health score
            total_leaf_params = len(leaf_params) if leaf_params else 8
            critical_penalty = len(leaf_critical) * 20
            medium_penalty = len(leaf_medium) * 10
            low_penalty = len(leaf_low) * 5
            
            leaf_health_score = max(0, 100 - (critical_penalty + medium_penalty + low_penalty))
            results['summary_metrics']['leaf_health_score'] = leaf_health_score
            
            # Store detailed leaf analysis
            results['detailed_analysis']['leaf_parameters'] = {
                'total_tested': total_leaf_params,
                'with_issues': len(leaf_issues),
                'optimal': total_leaf_params - len(leaf_issues),
                'critical_issues': leaf_critical,
                'medium_issues': leaf_medium,
                'low_issues': leaf_low,
                'parameters_breakdown': leaf_params
            }
            
            # Data quality for leaf
            expected_leaf_params = ['N', 'P', 'K', 'Mg', 'Ca', 'B', 'Cu', 'Zn']
            actual_leaf_params = [p.get('parameter', '') for p in leaf_params] if leaf_params else []
            leaf_completeness = (len(actual_leaf_params) / len(expected_leaf_params)) * 100
            results['data_quality']['leaf_data_completeness'] = min(100, leaf_completeness)
        
        # Calculate overall health score
        soil_score = results['summary_metrics']['soil_health_score']
        leaf_score = results['summary_metrics']['leaf_health_score']
        
        if soil_score > 0 and leaf_score > 0:
            results['summary_metrics']['overall_health_score'] = (soil_score + leaf_score) / 2
        elif soil_score > 0:
            results['summary_metrics']['overall_health_score'] = soil_score
        elif leaf_score > 0:
            results['summary_metrics']['overall_health_score'] = leaf_score
        
        # Calculate nutrient balance score
        nutrient_issues = []
        all_issues = results['health_indicators']['critical_issues'] + results['health_indicators']['medium_priority_issues']
        
        for issue in all_issues:
            param = issue.get('parameter', '').lower()
            if any(nutrient in param for nutrient in ['nitrogen', 'phosphorus', 'potassium', 'calcium', 'magnesium', 'n', 'p', 'k', 'ca', 'mg']):
                nutrient_issues.append(issue)
        
        nutrient_penalty = len(nutrient_issues) * 12
        results['summary_metrics']['nutrient_balance_score'] = max(0, 100 - nutrient_penalty)
        
        # Calculate risk assessment score
        risk_penalty = (results['summary_metrics']['critical_issues_count'] * 25 + 
                       results['summary_metrics']['high_priority_issues_count'] * 15 +
                       results['summary_metrics']['medium_priority_issues_count'] * 8)
        results['summary_metrics']['risk_assessment_score'] = max(0, 100 - risk_penalty)
        
        # Calculate improvement potential
        max_possible_improvement = min(results['summary_metrics']['total_issues_identified'] * 2, 25)
        results['summary_metrics']['improvement_potential'] = max_possible_improvement
        
        # Economic analysis
        total_cost = 0
        cost_breakdown = []
        
        for issue in all_issues:
            recommendation = issue.get('recommendation', {})
            if recommendation and 'cost_estimate' in recommendation:
                cost_str = str(recommendation['cost_estimate'])
                import re
                cost_match = re.search(r'RM\s*(\d+)', cost_str)
                if cost_match:
                    cost = float(cost_match.group(1))
                    total_cost += cost
                    cost_breakdown.append({
                        'item': issue['parameter'],
                        'cost': cost,
                        'description': recommendation.get('action', ''),
                        'priority': issue['severity']
                    })
        
        # Calculate economic projections
        expected_yield_increase = min(results['summary_metrics']['improvement_potential'], 20)
        current_yield = 18.5  # tons/hectare
        yield_value_per_ton = 2500  # RM per ton
        
        annual_revenue_increase = current_yield * (expected_yield_increase / 100) * yield_value_per_ton
        roi_percentage = (annual_revenue_increase / total_cost * 100) if total_cost > 0 else 0
        payback_months = (total_cost / (annual_revenue_increase / 12)) if annual_revenue_increase > 0 else 0
        cost_benefit_ratio = annual_revenue_increase / total_cost if total_cost > 0 else 0
        
        results['economic_analysis'] = {
            'total_treatment_cost': total_cost,
            'cost_breakdown': cost_breakdown,
            'expected_yield_increase': expected_yield_increase,
            'annual_revenue_increase': annual_revenue_increase,
            'roi_percentage': roi_percentage,
            'payback_months': payback_months,
            'cost_benefit_ratio': cost_benefit_ratio
        }
        
        # Yield forecast
        base_yield = 18.5
        improvement = expected_yield_increase / 100
        
        five_year_projection = []
        for year in range(2024, 2030):
            if year == 2024:
                projected_yield = base_yield  # Implementation year
            elif year == 2025:
                projected_yield = base_yield + (base_yield * improvement * 0.3)  # 30% of improvement
            elif year == 2026:
                projected_yield = base_yield + (base_yield * improvement * 0.6)  # 60% of improvement
            elif year == 2027:
                projected_yield = base_yield + (base_yield * improvement * 0.8)  # 80% of improvement
            else:
                projected_yield = base_yield + (base_yield * improvement)  # Full improvement
            
            five_year_projection.append({
                'year': year,
                'projected_yield': round(projected_yield, 2),
                'revenue_estimate': round(projected_yield * yield_value_per_ton, 2)
            })
        
        results['yield_forecast'] = {
            'current_yield_estimate': base_yield,
            'projected_yield_improvement': expected_yield_increase,
            'five_year_projection': five_year_projection,
            'improvement_timeline': {
                'immediate': 'Implementation phase (0-6 months)',
                'short_term': 'Initial improvements (6-18 months)',
                'medium_term': 'Significant gains (18-36 months)',
                'long_term': 'Full potential realized (36+ months)'
            },
            'yield_factors': [
                'Nutrient optimization',
                'Soil health improvement',
                'Balanced fertilization',
                'Proper pH management'
            ]
        }
        
        # Overall data quality and confidence
        soil_quality = results['data_quality']['soil_data_completeness']
        leaf_quality = results['data_quality']['leaf_data_completeness']
        
        if soil_quality > 0 and leaf_quality > 0:
            overall_confidence = (soil_quality + leaf_quality) / 2
        elif soil_quality > 0:
            overall_confidence = soil_quality
        elif leaf_quality > 0:
            overall_confidence = leaf_quality
        else:
            overall_confidence = 0
        
        results['data_quality']['overall_confidence'] = overall_confidence
        
        if overall_confidence >= 90:
            results['data_quality']['data_reliability'] = 'very_high'
        elif overall_confidence >= 75:
            results['data_quality']['data_reliability'] = 'high'
        elif overall_confidence >= 60:
            results['data_quality']['data_reliability'] = 'medium'
        else:
            results['data_quality']['data_reliability'] = 'low'
        
        # Identify positive indicators
        if results['summary_metrics']['overall_health_score'] > 80:
            results['health_indicators']['positive_indicators'].append('Excellent overall plantation health')
        elif results['summary_metrics']['overall_health_score'] > 70:
            results['health_indicators']['positive_indicators'].append('Good overall plantation health')
        
        if results['summary_metrics']['nutrient_balance_score'] > 85:
            results['health_indicators']['positive_indicators'].append('Well-balanced nutrient profile')
        
        if results['summary_metrics']['critical_issues_count'] == 0:
            results['health_indicators']['positive_indicators'].append('No critical issues detected')
        
        if results['economic_analysis']['roi_percentage'] > 200:
            results['health_indicators']['positive_indicators'].append('High return on investment potential')
        
        # Identify improvement areas and risk factors
        if results['summary_metrics']['soil_health_score'] < 60:
            results['health_indicators']['improvement_areas'].append('Soil health requires immediate attention')
            results['health_indicators']['risk_factors'].append('Poor soil health may limit yield potential')
        
        if results['summary_metrics']['leaf_health_score'] < 60:
            results['health_indicators']['improvement_areas'].append('Leaf nutrient status needs improvement')
            results['health_indicators']['risk_factors'].append('Nutrient deficiencies may affect tree health')
        
        if results['summary_metrics']['nutrient_balance_score'] < 70:
            results['health_indicators']['improvement_areas'].append('Nutrient management program optimization needed')
        
        if results['summary_metrics']['critical_issues_count'] > 3:
            results['health_indicators']['risk_factors'].append('Multiple critical issues require urgent intervention')
        
        if results['economic_analysis']['payback_months'] > 24:
            results['health_indicators']['risk_factors'].append('Long payback period for recommended treatments')
        
        return results
        
    except Exception as e:
        return {'error': f"Error generating comprehensive results: {str(e)}"}

def extract_key_findings(soil_analysis, leaf_analysis):
    """Extract key findings from both analyses"""
    try:
        findings = []
        
        if soil_analysis:
            soil_summary = soil_analysis.get('summary', '')
            if soil_summary:
                findings.append(f"Soil Analysis: {soil_summary}")
            
            # Add critical soil issues
            for issue in soil_analysis.get('issues', [])[:3]:  # Top 3 issues
                if issue.get('severity') == 'high':
                    findings.append(f"Critical Soil Issue: {issue.get('parameter', 'Unknown')} - {issue.get('description', '')}")
        
        if leaf_analysis:
            leaf_summary = leaf_analysis.get('summary', '')
            if leaf_summary:
                findings.append(f"Leaf Analysis: {leaf_summary}")
            
            # Add critical leaf issues
            for issue in leaf_analysis.get('issues', [])[:3]:  # Top 3 issues
                if issue.get('severity') == 'high':
                    findings.append(f"Critical Leaf Issue: {issue.get('parameter', 'Unknown')} - {issue.get('description', '')}")
        
        return findings[:10]  # Return max 10 key findings
        
    except Exception as e:
        return [f"Error extracting key findings: {str(e)}"]

def combine_economic_forecasts(soil_analysis, leaf_analysis, land_yield_data=None):
    """Combine economic forecasts from both analyses with land/yield data"""
    try:
        combined_forecast = {
            'total_cost': 0,
            'expected_yield_increase': 0,
            'annual_revenue_increase': 0,
            'roi_percentage': 0,
            'payback_months': 0,
            'cost_breakdown': []
        }
        
        # Combine soil economic data
        if soil_analysis and soil_analysis.get('economic_analysis'):
            soil_econ = soil_analysis['economic_analysis']
            combined_forecast['total_cost'] += soil_econ.get('total_cost', 0)
            combined_forecast['expected_yield_increase'] += soil_econ.get('expected_yield_increase', 0)
            combined_forecast['annual_revenue_increase'] += soil_econ.get('annual_revenue_increase', 0)
            
            for item in soil_econ.get('cost_breakdown', []):
                item['category'] = 'Soil Treatment'
                combined_forecast['cost_breakdown'].append(item)
        
        # Combine leaf economic data
        if leaf_analysis and leaf_analysis.get('economic_analysis'):
            leaf_econ = leaf_analysis['economic_analysis']
            combined_forecast['total_cost'] += leaf_econ.get('total_cost', 0)
            combined_forecast['expected_yield_increase'] += leaf_econ.get('expected_yield_increase', 0)
            combined_forecast['annual_revenue_increase'] += leaf_econ.get('annual_revenue_increase', 0)
            
            for item in leaf_econ.get('cost_breakdown', []):
                item['category'] = 'Foliar Treatment'
                combined_forecast['cost_breakdown'].append(item)
        
        # Adjust calculations based on actual land size if available
        if land_yield_data:
            land_size = land_yield_data.get('land_size', 1)
            land_unit = land_yield_data.get('land_unit', 'hectares')
            
            # Convert to hectares if needed
            if land_unit == 'acres':
                land_size_hectares = land_size * 0.4047
            else:
                land_size_hectares = land_size
            
            # Scale costs and revenue by actual land size
            combined_forecast['total_cost'] *= land_size_hectares
            combined_forecast['annual_revenue_increase'] *= land_size_hectares
            
            # Add land size info to forecast
            combined_forecast['land_size'] = land_size
            combined_forecast['land_unit'] = land_unit
            combined_forecast['land_size_hectares'] = land_size_hectares
        
        # Calculate combined ROI and payback
        if combined_forecast['total_cost'] > 0:
            combined_forecast['roi_percentage'] = (combined_forecast['annual_revenue_increase'] / combined_forecast['total_cost']) * 100
            combined_forecast['payback_months'] = (combined_forecast['total_cost'] / (combined_forecast['annual_revenue_increase'] / 12)) if combined_forecast['annual_revenue_increase'] > 0 else 0
        
        return combined_forecast
        
    except Exception as e:
        return {'error': f"Error combining economic forecasts: {str(e)}"}

def generate_combined_yield_forecast(soil_analysis, leaf_analysis, land_yield_data=None):
    """Generate combined 5-year yield forecast with land/yield data"""
    try:
        # Base yield parameters - use actual data if available
        if land_yield_data and land_yield_data.get('current_yield', 0) > 0:
            base_yield = land_yield_data['current_yield']
            # Convert to tonnes/hectare if needed
            if land_yield_data.get('yield_unit') == 'kg/hectare':
                base_yield = base_yield / 1000
            elif land_yield_data.get('yield_unit') in ['tonnes/acre', 'kg/acre']:
                # Convert acre to hectare (1 acre = 0.4047 hectare)
                if 'kg' in land_yield_data.get('yield_unit', ''):
                    base_yield = (base_yield / 1000) / 0.4047
                else:
                    base_yield = base_yield / 0.4047
        else:
            base_yield = 18.5  # Default tons/hectare
        
        years = list(range(2024, 2030))
        
        # Calculate total improvement potential
        soil_improvement = 0
        leaf_improvement = 0
        
        if soil_analysis and soil_analysis.get('yield_forecast'):
            soil_improvement = soil_analysis['yield_forecast'].get('improvement_potential', 0)
        
        if leaf_analysis and leaf_analysis.get('yield_forecast'):
            leaf_improvement = leaf_analysis['yield_forecast'].get('improvement_potential', 0)
        
        # Combined improvement (with synergy factor)
        total_improvement = (soil_improvement + leaf_improvement) * 1.1  # 10% synergy bonus
        total_improvement = min(total_improvement, 25)  # Cap at 25% improvement
        
        # Generate scenarios
        current_scenario = [base_yield - (i * 0.1) for i in range(6)]  # Declining without treatment
        improved_scenario = [
            base_yield,  # Year 1: Implementation
            base_yield + total_improvement * 0.2,  # Year 2: 20% of improvement
            base_yield + total_improvement * 0.5,  # Year 3: 50% of improvement
            base_yield + total_improvement * 0.7,  # Year 4: 70% of improvement
            base_yield + total_improvement * 0.9,  # Year 5: 90% of improvement
            base_yield + total_improvement  # Year 6: Full improvement
        ]
        
        return {
            'years': years,
            'current_scenario': current_scenario,
            'improved_scenario': improved_scenario,
            'improvement_potential': total_improvement,
            'total_additional_revenue': sum(improved_scenario) - sum(current_scenario),
            'synergy_factor': 1.1
        }
        
    except Exception as e:
        return {'error': f"Error generating yield forecast: {str(e)}"}

def generate_comprehensive_recommendations(soil_analysis, leaf_analysis, prompt_text):
    """Generate comprehensive recommendations from both analyses"""
    try:
        recommendations = []
        
        # Priority recommendations from soil analysis
        if soil_analysis and soil_analysis.get('issues'):
            for issue in soil_analysis['issues']:
                if issue.get('severity') == 'high':
                    rec = issue.get('recommendation', {})
                    if rec:
                        recommendations.append({
                            'category': 'Soil Management',
                            'priority': 'High',
                            'action': rec.get('action', 'Address soil issue'),
                            'description': rec.get('description', ''),
                            'dosage': rec.get('dosage', ''),
                            'cost_estimate': rec.get('cost_estimate', ''),
                            'timeline': '1-3 months'
                        })
        
        # Priority recommendations from leaf analysis
        if leaf_analysis and leaf_analysis.get('issues'):
            for issue in leaf_analysis['issues']:
                if issue.get('severity') == 'high':
                    rec = issue.get('recommendation', {})
                    if rec:
                        recommendations.append({
                            'category': 'Foliar Management',
                            'priority': 'High',
                            'action': rec.get('action', 'Address foliar issue'),
                            'description': rec.get('description', ''),
                            'dosage': rec.get('dosage', ''),
                            'cost_estimate': rec.get('cost_estimate', ''),
                            'timeline': '2-4 weeks'
                        })
        
        # Add medium priority recommendations
        for analysis, category in [(soil_analysis, 'Soil'), (leaf_analysis, 'Foliar')]:
            if analysis and analysis.get('issues'):
                for issue in analysis['issues']:
                    if issue.get('severity') == 'medium' and len(recommendations) < 10:
                        rec = issue.get('recommendation', {})
                        if rec:
                            recommendations.append({
                                'category': f'{category} Management',
                                'priority': 'Medium',
                                'action': rec.get('action', f'Address {category.lower()} issue'),
                                'description': rec.get('description', ''),
                                'dosage': rec.get('dosage', ''),
                                'cost_estimate': rec.get('cost_estimate', ''),
                                'timeline': '1-6 months'
                            })
        
        return recommendations[:10]  # Return max 10 recommendations
        
    except Exception as e:
        return [{'error': f"Error generating recommendations: {str(e)}"}]

def generate_executive_summary(soil_analysis, leaf_analysis):
    """Generate executive summary of the combined analysis"""
    try:
        summary_parts = []
        
        # Count total parameters and issues
        total_params = 0
        total_issues = 0
        critical_issues = 0
        
        if soil_analysis:
            soil_params = len(soil_analysis.get('analysis_results', []))
            soil_issues = len(soil_analysis.get('issues', []))
            total_params += soil_params
            total_issues += soil_issues
            critical_issues += len([i for i in soil_analysis.get('issues', []) if i.get('severity') == 'high'])
        
        if leaf_analysis:
            leaf_params = len(leaf_analysis.get('analysis_results', []))
            leaf_issues = len(leaf_analysis.get('issues', []))
            total_params += leaf_params
            total_issues += leaf_issues
            critical_issues += len([i for i in leaf_analysis.get('issues', []) if i.get('severity') == 'high'])
        
        # Generate summary
        summary_parts.append(f"Comprehensive analysis of {total_params} parameters from soil and leaf samples completed.")
        
        if total_issues > 0:
            summary_parts.append(f"Analysis identified {total_issues} issues requiring attention, with {critical_issues} classified as critical.")
        else:
            summary_parts.append("Analysis shows optimal nutrient levels across all parameters.")
        
        # Add specific insights
        if soil_analysis and soil_analysis.get('summary'):
            summary_parts.append(f"Soil condition: {soil_analysis['summary']}")
        
        if leaf_analysis and leaf_analysis.get('summary'):
            summary_parts.append(f"Plant nutrition status: {leaf_analysis['summary']}")
        
        # Add economic outlook
        if critical_issues > 0:
            summary_parts.append("Immediate intervention recommended to prevent yield losses and optimize economic returns.")
        elif total_issues > 0:
            summary_parts.append("Moderate interventions recommended to enhance productivity and profitability.")
        else:
            summary_parts.append("Current management practices are effective. Continue monitoring for optimal results.")
        
        return " ".join(summary_parts)
        
    except Exception as e:
        return f"Error generating executive summary: {str(e)}"

def save_combined_analysis_to_db(results, combined_analysis):
    """Save combined analysis results to database"""
    try:
        from utils.firebase_config import get_firestore_client, get_storage_bucket
        import uuid
        
        db = get_firestore_client()
        bucket = get_storage_bucket()
        
        # Generate unique analysis ID
        analysis_id = str(uuid.uuid4())
        
        # Prepare data for storage
        analysis_data = {
            'id': analysis_id,
            'user_id': st.session_state.get('user_id', 'unknown'),
            'type': 'combined_analysis',
            'soil_data': results.get('soil', {}),
            'leaf_data': results.get('leaf', {}),
            'combined_analysis': combined_analysis,
            'timestamp': datetime.now(),
            'status': 'completed'
        }
        
        # Save to Firestore
        db.collection('analyses').document(analysis_id).set(analysis_data)
        
        # Update user analysis count
        if st.session_state.get('user_id'):
            user_ref = db.collection('users').document(st.session_state.user_id)
            user_ref.update({
                'analysis_count': firestore.Increment(1),
                'last_analysis': datetime.now()
            })
        
        return analysis_id
        
    except Exception as e:
        st.error(f"Error saving to database: {str(e)}")
        return None

def save_analysis_to_db(filename, image_data, ocr_result, extracted_data, analysis_result):
    """Save analysis results to Firestore and image to Storage"""
    try:
        db = get_firestore_client()
        bucket = get_storage_bucket()
        
        if not db:
            return None
        
        # Upload image to Firebase Storage
        image_path = f"analyses/{st.session_state.user_info['uid']}/{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
        
        if bucket:
            blob = bucket.blob(image_path)
            blob.upload_from_string(image_data, content_type='image/png')
            image_url = blob.public_url
        else:
            image_url = None
        
        # Create analysis document
        analysis_doc = {
            'user_id': st.session_state.user_info['uid'],
            'filename': filename,
            'image_path': image_path,
            'image_url': image_url,
            'report_type': extracted_data.get('report_type', 'unknown'),
            'ocr_text': ocr_result.get('text', ''),
            'extracted_data': extracted_data.get('data', {}),
            'analysis_results': analysis_result.get('analysis', {}),
            'created_at': datetime.now(),
            'status': 'completed'
        }
        
        # Add to Firestore
        doc_ref = db.collection(COLLECTIONS['analyses']).add(analysis_doc)
        
        # Update user analysis count
        user_ref = db.collection(COLLECTIONS['users']).document(st.session_state.user_info['uid'])
        user_ref.update({
            'analyses_count': firestore.Increment(1),
            'last_analysis': datetime.now()
        })
        
        return doc_ref[1].id
        
    except Exception as e:
        st.error(f"Database save error: {str(e)}")
        return None

def display_analysis_results():
    """Display comprehensive analysis results with enhanced visualizations"""
    
    if 'current_analysis' not in st.session_state:
        st.info("No analysis results to display.")
        return
    
    analysis = st.session_state.current_analysis
    
    st.markdown("### 📊 Comprehensive Analysis Results")
    
    # Check if this is a comprehensive combined analysis
    combined_analysis = analysis.get('combined_analysis', {})
    
    if combined_analysis and isinstance(combined_analysis, dict) and 'comprehensive_results' in combined_analysis:
        # New comprehensive analysis structure
        display_enhanced_combined_analysis(analysis, combined_analysis)
    else:
        # Legacy analysis structure
        display_legacy_analysis(analysis)

def display_enhanced_combined_analysis(analysis, combined_analysis):
    """Display enhanced combined analysis with comprehensive results and visualizations"""
    
    # Create tabs for different sections
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Raw Data", "📋 Summary", "🔍 Analysis Steps", "📈 Visualizations", "📄 Reports"])
    
    with tab1:
        display_raw_data_section(analysis)
    
    with tab2:
        display_summary_section(analysis, combined_analysis)
    
    with tab3:
        display_analysis_steps_section(analysis, combined_analysis)
    
    with tab4:
        display_visualizations_section(analysis, combined_analysis)
    
    with tab5:
        display_reports_section(analysis, combined_analysis)

def display_raw_data_section(analysis):
    """Display raw extracted data from both soil and leaf files"""
    st.markdown("### 📊 Raw Extracted Data")
    
    # Soil Data Section
    soil_data = analysis.get('soil_data')
    if soil_data:
        st.markdown("#### 🌱 Soil Analysis Data")
        
        # Display OCR extraction info
        ocr_result = soil_data.get('ocr_result', {})
        if ocr_result.get('success'):
            st.success(f"✅ Successfully extracted {ocr_result.get('total_parameters', 0)} soil parameters")
            
            # Display parameters in a structured format
            parameters = ocr_result.get('parameters', [])
            if parameters:
                # Group by sample number for better display
                soil_df = pd.DataFrame(parameters)
                
                if 'Sample_No' in soil_df.columns:
                    # Display as pivot table
                    pivot_df = soil_df.pivot_table(
                        index='Sample_No', 
                        columns='Parameter', 
                        values='Value', 
                        aggfunc='first'
                    )
                    st.markdown("**Soil Parameters by Sample:**")
                    st.dataframe(pivot_df, use_container_width=True)
                else:
                    # Display as regular table
                    st.markdown("**Soil Parameters:**")
                    st.dataframe(soil_df[['Parameter', 'Value', 'Unit']], use_container_width=True)
                
                # Show raw text preview
                with st.expander("🔍 View Raw OCR Text (Soil)"):
                    raw_text = ocr_result.get('raw_text', 'No raw text available')
                    st.text_area("Raw OCR Output", raw_text[:1000] + "..." if len(raw_text) > 1000 else raw_text, height=200)
        else:
            st.error(f"❌ Soil OCR failed: {ocr_result.get('error', 'Unknown error')}")
    
    # Leaf Data Section
    leaf_data = analysis.get('leaf_data')
    if leaf_data:
        st.markdown("#### 🍃 Leaf Analysis Data")
        
        # Display OCR extraction info
        ocr_result = leaf_data.get('ocr_result', {})
        if ocr_result.get('success'):
            st.success(f"✅ Successfully extracted {ocr_result.get('total_parameters', 0)} leaf parameters")
            
            # Display parameters in a structured format
            parameters = ocr_result.get('parameters', [])
            if parameters:
                # Group by sample number for better display
                leaf_df = pd.DataFrame(parameters)
                
                if 'Sample_No' in leaf_df.columns:
                    # Display as pivot table
                    pivot_df = leaf_df.pivot_table(
                        index='Sample_No', 
                        columns='Parameter', 
                        values='Value', 
                        aggfunc='first'
                    )
                    st.markdown("**Leaf Parameters by Sample:**")
                    st.dataframe(pivot_df, use_container_width=True)
                else:
                    # Display as regular table
                    st.markdown("**Leaf Parameters:**")
                    st.dataframe(leaf_df[['Parameter', 'Value', 'Unit']], use_container_width=True)
                
                # Show raw text preview
                with st.expander("🔍 View Raw OCR Text (Leaf)"):
                    raw_text = ocr_result.get('raw_text', 'No raw text available')
                    st.text_area("Raw OCR Output", raw_text[:1000] + "..." if len(raw_text) > 1000 else raw_text, height=200)
        else:
            st.error(f"❌ Leaf OCR failed: {ocr_result.get('error', 'Unknown error')}")
    
    # Data Quality Summary
    st.markdown("#### 📈 Data Extraction Summary")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        soil_params = len(soil_data.get('ocr_result', {}).get('parameters', [])) if soil_data else 0
        st.metric("Soil Parameters", soil_params, help="Total soil parameters extracted")
    
    with col2:
        leaf_params = len(leaf_data.get('ocr_result', {}).get('parameters', [])) if leaf_data else 0
        st.metric("Leaf Parameters", leaf_params, help="Total leaf parameters extracted")
    
    with col3:
        total_params = soil_params + leaf_params
        expected_total = 90 + 80  # 10 samples × 9 soil params + 10 samples × 8 leaf params
        extraction_rate = (total_params / expected_total * 100) if expected_total > 0 else 0
        st.metric("Extraction Rate", f"{extraction_rate:.1f}%", help="Percentage of expected parameters extracted")

def display_summary_section(analysis, combined_analysis):
    """Display executive summary and key findings"""
    # Executive Summary
    st.markdown("#### 📋 Executive Summary")
    summary = combined_analysis.get('summary', 'No summary available')
    st.info(summary)
    
    # Get comprehensive results structure
    comprehensive_results = combined_analysis.get('comprehensive_results', {})
    summary_metrics = comprehensive_results.get('summary_metrics', {})
    health_indicators = comprehensive_results.get('health_indicators', {})
    detailed_analysis = comprehensive_results.get('detailed_analysis', {})
    economic_analysis = comprehensive_results.get('economic_analysis', {})
    data_quality = comprehensive_results.get('data_quality', {})
    
    # Key Metrics Dashboard
    st.markdown("#### 📊 Key Metrics")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        total_params = summary_metrics.get('total_parameters_analyzed', 0)
        st.metric("Parameters Analyzed", total_params)
    with col2:
        total_issues = summary_metrics.get('total_issues_identified', 0)
        st.metric("Issues Identified", total_issues)
    with col3:
        critical_count = summary_metrics.get('critical_issues_count', 0)
        st.metric("Critical Issues", critical_count, delta=f"-{critical_count}" if critical_count > 0 else None)
    with col4:
        health_score = health_indicators.get('overall_health_score', 0)
        st.metric("Health Score", f"{health_score:.1f}%", delta=f"{health_score-75:.1f}%" if health_score != 0 else None)

def display_analysis_steps_section(analysis, combined_analysis):
    """Display step-by-step analysis process and prompt results"""
    st.markdown("### 🔍 Analysis Steps & Process")
    
    # Show the prompt used
    st.markdown("#### 📝 Analysis Prompt Used")
    prompt_info = combined_analysis.get('prompt_info', {})
    if prompt_info:
        st.info(f"**Prompt:** {prompt_info.get('name', 'Default Prompt')}")
        st.text_area("Prompt Content", prompt_info.get('content', 'No prompt content available'), height=150)
    
    # Show analysis steps
    st.markdown("#### 🔄 Processing Steps")
    
    steps = [
        {"step": 1, "title": "Image Upload & Preprocessing", "status": "✅ Complete", "details": "Images uploaded and preprocessed for OCR"},
        {"step": 2, "title": "OCR Text Extraction", "status": "✅ Complete", "details": "Text extracted from both soil and leaf reports"},
        {"step": 3, "title": "Data Parsing & Validation", "status": "✅ Complete", "details": "Parameters identified and validated"},
        {"step": 4, "title": "Analysis Engine Processing", "status": "✅ Complete", "details": "AI analysis performed using active prompt"},
        {"step": 5, "title": "Results Generation", "status": "✅ Complete", "details": "Comprehensive results and recommendations generated"}
    ]
    
    for step in steps:
        with st.expander(f"Step {step['step']}: {step['title']} - {step['status']}"):
            st.write(step['details'])
            
            # Add specific details for each step
            if step['step'] == 2:  # OCR step
                soil_data = analysis.get('soil_data', {})
                leaf_data = analysis.get('leaf_data', {})
                
                col1, col2 = st.columns(2)
                with col1:
                    if soil_data.get('ocr_result', {}).get('success'):
                        st.success("Soil OCR: Success")
                        st.write(f"Parameters extracted: {len(soil_data.get('ocr_result', {}).get('parameters', []))}")
                    else:
                        st.error("Soil OCR: Failed")
                
                with col2:
                    if leaf_data.get('ocr_result', {}).get('success'):
                        st.success("Leaf OCR: Success")
                        st.write(f"Parameters extracted: {len(leaf_data.get('ocr_result', {}).get('parameters', []))}")
                    else:
                        st.error("Leaf OCR: Failed")
            
            elif step['step'] == 4:  # Analysis step
                # Show analysis results summary
                comprehensive_results = combined_analysis.get('comprehensive_results', {})
                if comprehensive_results:
                    st.write("**Analysis Results:**")
                    st.write(f"- Health Score: {comprehensive_results.get('health_indicators', {}).get('overall_health_score', 0):.1f}%")
                    st.write(f"- Issues Identified: {comprehensive_results.get('summary_metrics', {}).get('total_issues_identified', 0)}")
                    st.write(f"- Recommendations Generated: {len(comprehensive_results.get('detailed_analysis', {}).get('recommendations', []))}")

def display_visualizations_section(analysis, combined_analysis):
    """Display charts and visualizations"""
    st.markdown("### 📈 Data Visualizations")
    
    # Get comprehensive results structure
    comprehensive_results = combined_analysis.get('comprehensive_results', {})
    health_indicators = comprehensive_results.get('health_indicators', {})
    
    # Health Indicators Section
    if health_indicators:
        st.markdown("#### 🏥 Health Indicators")
        
        # Health scores visualization
        health_scores = {
            'Overall Health': health_indicators.get('overall_health_score', 0),
            'Soil Health': health_indicators.get('soil_health_score', 0),
            'Leaf Health': health_indicators.get('leaf_health_score', 0),
            'Nutrient Balance': health_indicators.get('nutrient_balance_score', 0),
            'Risk Assessment': health_indicators.get('risk_assessment_score', 0)
        }
        
        # Filter out zero scores
        health_scores = {k: v for k, v in health_scores.items() if v > 0}
        
        if health_scores:
            fig_health = px.bar(
                x=list(health_scores.keys()),
                y=list(health_scores.values()),
                title='Health Scores Overview',
                labels={'x': 'Health Category', 'y': 'Score (%)'},
                color=list(health_scores.values()),
                color_continuous_scale='RdYlGn',
                range_color=[0, 100]
            )
            fig_health.update_layout(height=400)
            st.plotly_chart(fig_health, use_container_width=True)
        
        # Health status indicators
        col1, col2, col3 = st.columns(3)
        
        with col1:
            positive_indicators = health_indicators.get('positive_indicators', [])
            if positive_indicators:
                st.markdown("##### ✅ Positive Indicators")
                for indicator in positive_indicators[:3]:
                    st.success(f"• {indicator}")
        
        with col2:
            improvement_areas = health_indicators.get('improvement_areas', [])
            if improvement_areas:
                st.markdown("##### 🔧 Improvement Areas")
                for area in improvement_areas[:3]:
                    st.warning(f"• {area}")
        
        with col3:
            risk_factors = health_indicators.get('risk_factors', [])
            if risk_factors:
                st.markdown("##### ⚠️ Risk Factors")
                for risk in risk_factors[:3]:
                    st.error(f"• {risk}")
    
    # Detailed Analysis Section
    if detailed_analysis:
        st.markdown("#### 🔬 Detailed Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            soil_summary = detailed_analysis.get('soil_summary', {})
            if soil_summary:
                st.markdown("##### 🌱 Soil Analysis Summary")
                st.metric("Parameters Tested", soil_summary.get('parameters_tested', 0))
                st.metric("Issues Found", soil_summary.get('issues_found', 0))
                st.metric("Optimal Parameters", soil_summary.get('optimal_parameters', 0))
        
        with col2:
            leaf_summary = detailed_analysis.get('leaf_summary', {})
            if leaf_summary:
                st.markdown("##### 🍃 Leaf Analysis Summary")
                st.metric("Parameters Tested", leaf_summary.get('parameters_tested', 0))
                st.metric("Issues Found", leaf_summary.get('issues_found', 0))
                st.metric("Optimal Parameters", leaf_summary.get('optimal_parameters', 0))
    
    # Issues Breakdown Visualization
    issues_by_priority = summary_metrics.get('issues_by_priority', {})
    if issues_by_priority and sum(issues_by_priority.values()) > 0:
        st.markdown("#### ⚠️ Issues Analysis")
        
        # Create issues breakdown chart
        fig_issues = px.pie(
            values=list(issues_by_priority.values()),
            names=list(issues_by_priority.keys()),
            title='Issues Distribution by Priority',
            color_discrete_map={'Critical': '#FF4B4B', 'High': '#FF8C00', 'Medium': '#FFA500', 'Low': '#FFD700'}
        )
        st.plotly_chart(fig_issues, use_container_width=True)
    
    # Economic Analysis Section
    if economic_analysis:
        st.markdown("#### 💰 Economic Analysis")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            total_cost = economic_analysis.get('total_treatment_cost', 0)
            st.metric("Total Investment", f"RM {total_cost:,.0f}")
        with col2:
            yield_increase = economic_analysis.get('expected_yield_increase', 0)
            st.metric("Yield Increase", f"{yield_increase:.1f}%")
        with col3:
            roi = economic_analysis.get('roi_percentage', 0)
            st.metric("ROI", f"{roi:.1f}%")
        with col4:
            payback = economic_analysis.get('payback_period_months', 0)
            st.metric("Payback Period", f"{payback:.1f} months")
        
        # Cost breakdown
            cost_breakdown = economic_analysis.get('cost_breakdown', {})
            if cost_breakdown:
                st.markdown("##### 💸 Cost Breakdown")
                
                fig_cost = px.pie(
                    values=list(cost_breakdown.values()),
                    names=list(cost_breakdown.keys()),
                    title='Treatment Cost Breakdown'
                )
                st.plotly_chart(fig_cost, use_container_width=True)
    
    # Parameter Distribution Charts
    st.markdown("#### 📊 Parameter Distribution")
    
    # Soil parameters chart
    soil_data = analysis.get('soil_data', {})
    if soil_data and soil_data.get('ocr_result', {}).get('success'):
        soil_params = soil_data.get('ocr_result', {}).get('parameters', [])
        if soil_params:
            soil_df = pd.DataFrame(soil_params)
            if 'Parameter' in soil_df.columns and 'Value' in soil_df.columns:
                # Create bar chart for soil parameters
                fig_soil = px.bar(
                    soil_df.groupby('Parameter')['Value'].mean().reset_index(),
                    x='Parameter',
                    y='Value',
                    title='Average Soil Parameter Values',
                    color='Value',
                    color_continuous_scale='Viridis'
                )
                fig_soil.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(fig_soil, use_container_width=True)
    
    # Leaf parameters chart
    leaf_data = analysis.get('leaf_data', {})
    if leaf_data and leaf_data.get('ocr_result', {}).get('success'):
        leaf_params = leaf_data.get('ocr_result', {}).get('parameters', [])
        if leaf_params:
            leaf_df = pd.DataFrame(leaf_params)
            if 'Parameter' in leaf_df.columns and 'Value' in leaf_df.columns:
                # Create bar chart for leaf parameters
                fig_leaf = px.bar(
                    leaf_df.groupby('Parameter')['Value'].mean().reset_index(),
                    x='Parameter',
                    y='Value',
                    title='Average Leaf Parameter Values',
                    color='Value',
                    color_continuous_scale='Plasma'
                )
                fig_leaf.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(fig_leaf, use_container_width=True)

def display_reports_section(analysis, combined_analysis):
    """Display PDF report download and export options"""
    st.markdown("### 📄 Reports & Export")
    
    # PDF Report Generation
    st.markdown("#### 📋 Generate PDF Report")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.info("Generate a comprehensive PDF report containing all analysis results, raw data, and recommendations.")
        
        # Report customization options
        include_raw_data = st.checkbox("Include Raw Data Tables", value=True)
        include_visualizations = st.checkbox("Include Charts & Visualizations", value=True)
        include_recommendations = st.checkbox("Include Recommendations", value=True)
        include_metadata = st.checkbox("Include Analysis Metadata", value=True)
    
    with col2:
        if st.button("📄 Generate PDF Report", type="primary", use_container_width=True):
            try:
                # Generate PDF report
                pdf_content = generate_pdf_report(
                    analysis, 
                    combined_analysis,
                    include_raw_data=include_raw_data,
                    include_visualizations=include_visualizations,
                    include_recommendations=include_recommendations,
                    include_metadata=include_metadata
                )
                
                if pdf_content:
                    # Create download button
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"lab_analysis_report_{timestamp}.pdf"
                    
                    st.download_button(
                        label="⬇️ Download PDF Report",
                        data=pdf_content,
                        file_name=filename,
                        mime="application/pdf",
                        use_container_width=True
                    )
                    st.success("✅ PDF report generated successfully!")
                else:
                    st.error("❌ Failed to generate PDF report")
            except Exception as e:
                st.error(f"❌ Error generating PDF: {str(e)}")
    
    # Data Export Options
    st.markdown("#### 📊 Export Raw Data")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Export soil data as CSV
        soil_data = analysis.get('soil_data', {})
        if soil_data and soil_data.get('ocr_result', {}).get('success'):
            soil_params = soil_data.get('ocr_result', {}).get('parameters', [])
            if soil_params:
                soil_df = pd.DataFrame(soil_params)
                csv_soil = soil_df.to_csv(index=False)
                st.download_button(
                    label="📥 Download Soil Data (CSV)",
                    data=csv_soil,
                    file_name=f"soil_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
    
    with col2:
        # Export leaf data as CSV
        leaf_data = analysis.get('leaf_data', {})
        if leaf_data and leaf_data.get('ocr_result', {}).get('success'):
            leaf_params = leaf_data.get('ocr_result', {}).get('parameters', [])
            if leaf_params:
                leaf_df = pd.DataFrame(leaf_params)
                csv_leaf = leaf_df.to_csv(index=False)
                st.download_button(
                    label="📥 Download Leaf Data (CSV)",
                    data=csv_leaf,
                    file_name=f"leaf_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
    
    with col3:
        # Export combined analysis as JSON
        if combined_analysis:
            import json
            json_data = json.dumps(combined_analysis, indent=2, default=str)
            st.download_button(
                label="📥 Download Analysis (JSON)",
                data=json_data,
                file_name=f"analysis_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                use_container_width=True
            )
    
    # Report History
    st.markdown("#### 📚 Report History")
    st.info("Previous reports and analyses will be displayed here. This feature connects to the existing report history system.")
    
    # Link to existing report history
    if st.button("📋 View Full Report History", use_container_width=True):
        st.session_state.active_tab = "Report History"
        st.rerun()
    
    # Data Quality Assessment
    if data_quality:
        st.markdown("#### 📊 Data Quality Assessment")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            soil_completeness = data_quality.get('soil_data_completeness', 0)
            st.metric("Soil Data Completeness", f"{soil_completeness:.1f}%")
        with col2:
            leaf_completeness = data_quality.get('leaf_data_completeness', 0)
            st.metric("Leaf Data Completeness", f"{leaf_completeness:.1f}%")
        with col3:
            confidence = data_quality.get('overall_confidence', 0)
            st.metric("Analysis Confidence", f"{confidence:.1f}%")
        
        reliability = data_quality.get('reliability_rating', 'Unknown')
        if reliability != 'Unknown':
            if reliability == 'High':
                st.success(f"🎯 **Data Reliability:** {reliability} - Analysis results are highly reliable")
            elif reliability == 'Medium':
                st.warning(f"⚠️ **Data Reliability:** {reliability} - Analysis results are moderately reliable")
            else:
                st.error(f"🚨 **Data Reliability:** {reliability} - Analysis results may have limitations")
    
    # 5-Year Yield Forecast Visualization
    yield_forecast = comprehensive_results.get('yield_forecast', {})
    if yield_forecast:
        st.markdown("#### 📈 5-Year Yield Forecast")
        
        # Display forecast overview
        forecast_overview = yield_forecast.get('forecast_overview', {})
        if forecast_overview:
            col1, col2, col3 = st.columns(3)
            with col1:
                baseline = forecast_overview.get('baseline_yield', 0)
                st.metric("Baseline Yield", f"{baseline:.1f} tonnes/ha")
            with col2:
                projected = forecast_overview.get('projected_yield_year_5', 0)
                st.metric("Year 5 Projection", f"{projected:.1f} tonnes/ha")
            with col3:
                improvement = forecast_overview.get('total_improvement', 0)
                st.metric("Total Improvement", f"{improvement:.1f}%")
        
        # Create yield forecast chart
        projections = yield_forecast.get('yearly_projections', [])
        if projections and len(projections) >= 5:
            years = [proj.get('year', 2024 + i) for i, proj in enumerate(projections[:5])]
            yields = [proj.get('yield', 0) for proj in projections[:5]]
            baseline_yield = forecast_overview.get('baseline_yield', yields[0] if yields else 20)
            
            fig_yield = go.Figure()
            
            # Add baseline
            fig_yield.add_trace(go.Scatter(
                x=years,
                y=[baseline_yield] * len(years),
                mode='lines',
                name='Baseline Yield',
                line=dict(color='red', dash='dash')
            ))
            
            # Add projected yield
            fig_yield.add_trace(go.Scatter(
                x=years,
                y=yields,
                mode='lines+markers',
                name='Projected Yield',
                line=dict(color='green', width=3),
                marker=dict(size=8)
            ))
            
            # Fill area between lines
            fig_yield.add_trace(go.Scatter(
                x=years + years[::-1],
                y=yields + [baseline_yield] * len(years),
                fill='toself',
                fillcolor='rgba(0,255,0,0.1)',
                line=dict(color='rgba(255,255,255,0)'),
                name='Improvement Potential',
                showlegend=False
            ))
            
            fig_yield.update_layout(
                title='5-Year Yield Forecast (Tonnes/Hectare)',
                xaxis_title='Year',
                yaxis_title='Yield (Tonnes/Hectare)',
                hovermode='x unified',
                height=400
            )
            
            st.plotly_chart(fig_yield, use_container_width=True)
        
        # Improvement timeline
        improvement_timeline = yield_forecast.get('improvement_timeline', {})
        if improvement_timeline:
            st.markdown("##### 📅 Improvement Timeline")
            col1, col2, col3 = st.columns(3)
            with col1:
                short_term = improvement_timeline.get('short_term_months', 0)
                st.metric("Short-term Results", f"{short_term} months")
            with col2:
                medium_term = improvement_timeline.get('medium_term_months', 0)
                st.metric("Medium-term Results", f"{medium_term} months")
            with col3:
                long_term = improvement_timeline.get('long_term_months', 0)
                st.metric("Long-term Results", f"{long_term} months")
        
        # Yield factors
        yield_factors = yield_forecast.get('yield_factors', {})
        if yield_factors:
            st.markdown("##### 🌱 Key Yield Factors")
            col1, col2, col3 = st.columns(3)
            with col1:
                soil_factor = yield_factors.get('soil_improvement_factor', 0)
                st.metric("Soil Improvement", f"{soil_factor:.1f}%")
            with col2:
                leaf_factor = yield_factors.get('leaf_improvement_factor', 0)
                st.metric("Leaf Health", f"{leaf_factor:.1f}%")
            with col3:
                synergy = yield_factors.get('synergy_factor', 1.0)
                st.metric("Synergy Factor", f"{synergy:.1f}x")
    
    # Key Findings from comprehensive results
    key_findings = combined_analysis.get('key_findings', [])
    if key_findings:
        st.markdown("#### 🔍 Key Findings")
        for i, finding in enumerate(key_findings[:5], 1):
            st.markdown(f"**{i}.** {finding}")
    
    # Comprehensive Recommendations from comprehensive results
    recommendations = combined_analysis.get('recommendations', [])
    if recommendations:
        st.markdown("#### 💡 Comprehensive Recommendations")
        
        # Group recommendations by priority
        critical_recs = [r for r in recommendations if r.get('priority') == 'Critical']
        high_priority = [r for r in recommendations if r.get('priority') == 'High']
        medium_priority = [r for r in recommendations if r.get('priority') == 'Medium']
        
        if critical_recs:
            st.markdown("##### 🚨 Critical Priority Actions")
            for rec in critical_recs:
                with st.container():
                    st.markdown(f"**{rec.get('action', 'Unknown Action')}** ({rec.get('category', 'General')})")
                    st.markdown(f"📝 {rec.get('description', 'No description available')}")
                    if rec.get('dosage'):
                        st.markdown(f"📏 **Dosage:** {rec['dosage']}")
                    if rec.get('cost_estimate'):
                        st.markdown(f"💰 **Cost:** {rec['cost_estimate']}")
                    if rec.get('timeline'):
                        st.markdown(f"⏱️ **Timeline:** {rec['timeline']}")
                    st.markdown("---")
        
        if high_priority:
            st.markdown("##### 🔴 High Priority Actions")
            for rec in high_priority:
                with st.container():
                    st.markdown(f"**{rec.get('action', 'Unknown Action')}** ({rec.get('category', 'General')})")
                    st.markdown(f"📝 {rec.get('description', 'No description available')}")
                    if rec.get('dosage'):
                        st.markdown(f"📏 **Dosage:** {rec['dosage']}")
                    if rec.get('cost_estimate'):
                        st.markdown(f"💰 **Cost:** {rec['cost_estimate']}")
                    if rec.get('timeline'):
                        st.markdown(f"⏱️ **Timeline:** {rec['timeline']}")
                    st.markdown("---")
        
        if medium_priority:
            with st.expander("🟡 Medium Priority Actions"):
                for rec in medium_priority:
                    st.markdown(f"**{rec.get('action', 'Unknown Action')}** ({rec.get('category', 'General')})")
                    st.markdown(f"📝 {rec.get('description', 'No description available')}")
                    if rec.get('dosage'):
                        st.markdown(f"📏 **Dosage:** {rec['dosage']}")
                    if rec.get('cost_estimate'):
                        st.markdown(f"💰 **Cost:** {rec['cost_estimate']}")
                    if rec.get('timeline'):
                        st.markdown(f"⏱️ **Timeline:** {rec['timeline']}")
                    st.markdown("---")
    
    # Reference Documents
    reference_docs = combined_analysis.get('reference_documents', [])
    if reference_docs:
        with st.expander("📚 Supporting Reference Documents"):
            for doc in reference_docs[:5]:
                st.markdown(f"**{doc.get('title', 'Untitled Document')}**")
                if doc.get('description'):
                    st.markdown(f"📄 {doc['description']}")
                if doc.get('keywords'):
                    keywords = ', '.join(doc['keywords'][:5])
                    st.markdown(f"🏷️ **Keywords:** {keywords}")
                st.markdown("---")
    
    # Download options
    st.markdown("#### 📥 Download Options")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📄 Generate Comprehensive PDF Report", use_container_width=True, key=f"pdf_{analysis.get('id', 'unknown')}"):
            generate_comprehensive_pdf_report(analysis, combined_analysis)
    
    with col2:
        if st.button("📊 Export Analysis Data (CSV)", use_container_width=True, key=f"csv_{analysis.get('id', 'unknown')}"):
            export_comprehensive_data_csv(analysis, combined_analysis)

def display_legacy_analysis(analysis):
    """Display legacy analysis structure for backward compatibility"""
    # Handle different analysis structures
    if analysis.get('type') == 'combined':
        # Combined analysis structure
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Report Type", "Combined Analysis")
        with col2:
            soil_params = len(analysis.get('soil_data', {}).get('ocr_result', {}).get('extracted_data', {}))
            leaf_params = len(analysis.get('leaf_data', {}).get('ocr_result', {}).get('extracted_data', {}))
            st.metric("Parameters Found", soil_params + leaf_params)
        with col3:
            st.metric("Analysis Date", analysis['timestamp'].strftime('%Y-%m-%d %H:%M'))
        
        # Display soil and leaf data separately
        if analysis.get('soil_data', {}).get('ocr_result', {}).get('extracted_data'):
            st.markdown("#### 🌱 Soil Analysis Data")
            soil_df = pd.DataFrame.from_dict(analysis['soil_data']['ocr_result']['extracted_data'], orient='index')
            st.dataframe(soil_df, use_container_width=True)
        
        if analysis.get('leaf_data', {}).get('ocr_result', {}).get('extracted_data'):
            st.markdown("#### 🍃 Leaf Analysis Data")
            leaf_df = pd.DataFrame.from_dict(analysis['leaf_data']['ocr_result']['extracted_data'], orient='index')
            st.dataframe(leaf_df, use_container_width=True)
    else:
        # Single analysis structure (from history)
        col1, col2, col3 = st.columns(3)
        with col1:
            report_type = analysis.get('extracted_data', {}).get('report_type', 'Unknown')
            st.metric("Report Type", report_type.title())
        with col2:
            data_count = len(analysis.get('extracted_data', {}).get('data', {}))
            st.metric("Parameters Found", data_count)
        with col3:
            st.metric("Analysis Date", analysis['timestamp'].strftime('%Y-%m-%d %H:%M'))
        
        # Extracted data
        if analysis.get('extracted_data', {}).get('data'):
            st.markdown("#### 📋 Extracted Data")
            df = pd.DataFrame.from_dict(analysis['extracted_data']['data'], orient='index')
            st.dataframe(df, use_container_width=True)
    
    # Analysis results
    if analysis.get('type') == 'combined':
        # Combined analysis results
        if analysis.get('combined_analysis'):
            st.markdown("#### 🧠 Combined Analysis Results")
            combined_data = analysis['combined_analysis']
            
            # Display combined recommendations
            if combined_data.get('recommendations'):
                st.markdown("##### 💡 Recommendations")
                if isinstance(combined_data['recommendations'], list):
                    for rec in combined_data['recommendations']:
                        st.write(f"• {rec}")
                else:
                    st.write(combined_data['recommendations'])
            
            # Display economic impact if available
            if combined_data.get('economic_impact'):
                st.markdown("##### 💰 Economic Impact")
                st.json(combined_data['economic_impact'])
    else:
        # Single analysis results
        if analysis.get('analysis_result', {}).get('analysis'):
            st.markdown("#### 🧠 Analysis Results")
            
            analysis_data = analysis['analysis_result']['analysis']
            
            # Issues found
            if 'issues' in analysis_data:
                st.markdown("##### ⚠️ Issues Identified")
                for issue in analysis_data['issues']:
                    st.warning(f"**{issue['parameter']}:** {issue['description']}")
            
            # Recommendations
            if 'recommendations' in analysis_data:
                st.markdown("##### 💡 Recommendations")
                for rec in analysis_data['recommendations']:
                    st.info(f"**{rec['category']}:** {rec['recommendation']}")
            
            # Forecast
            if 'forecast' in analysis_data:
                st.markdown("##### 📈 Yield Forecast")
                st.json(analysis_data['forecast'])
    
    # Download options
    st.markdown("#### 📥 Download Options")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📄 Generate PDF Report", use_container_width=True, key=f"legacy_pdf_{analysis.get('id', 'unknown')}"):
            generate_pdf_report(analysis)
    
    with col2:
        if st.button("📊 Export Data (CSV)", use_container_width=True, key=f"legacy_csv_{analysis.get('id', 'unknown')}"):
            export_data_csv(analysis)

def display_report_history():
    """Display user's analysis history"""
    
    st.markdown("### 📋 Your Analysis History")
    
    # Check if user is authenticated
    if not st.session_state.get('authenticated', False):
        st.warning("🔒 Please log in to view your analysis history.")
        return
    
    # Check if user info is available
    if 'user_info' not in st.session_state or not st.session_state.user_info:
        st.error("User information not available. Please log in again.")
        return
    
    try:
        db = get_firestore_client()
        if not db:
            st.error("Database connection failed")
            return
        
        # Get user's analyses from analysis_results collection
        analyses_ref = db.collection(COLLECTIONS['analysis_results'])
        user_analyses = analyses_ref.where('user_id', '==', st.session_state.user_info['uid']).order_by('created_at', direction=firestore.Query.DESCENDING).limit(20).get()
        
        if not user_analyses:
            st.info("No analysis history found. Upload your first report to get started!")
            return
        
        # Display analyses
        for doc in user_analyses:
            analysis_data = doc.to_dict()
            
            with st.expander(f"📊 {analysis_data['filename']} - {analysis_data['created_at'].strftime('%Y-%m-%d %H:%M')}"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.write(f"**Type:** {analysis_data.get('report_type', 'Unknown').title()}")
                    st.write(f"**Status:** {analysis_data.get('status', 'Unknown').title()}")
                
                with col2:
                    st.write(f"**Parameters:** {len(analysis_data.get('extracted_data', {}))}")
                    st.write(f"**Date:** {analysis_data['created_at'].strftime('%Y-%m-%d')}")
                
                with col3:
                    if st.button(f"View Details", key=f"view_{doc.id}"):
                        st.session_state.current_analysis = {
                            'id': doc.id,
                            'filename': analysis_data['filename'],
                            'extracted_data': {'data': analysis_data.get('extracted_data', {}), 'report_type': analysis_data.get('report_type', 'unknown')},
                            'analysis_result': {'analysis': analysis_data.get('analysis_results', {})},
                            'timestamp': analysis_data['created_at']
                        }
                        st.rerun()
                
                # Show extracted data preview
                if analysis_data.get('extracted_data'):
                    st.write("**Data Preview:**")
                    preview_data = dict(list(analysis_data['extracted_data'].items())[:3])
                    st.json(preview_data)
        
    except Exception as e:
        st.error(f"Error loading history: {str(e)}")

def generate_comprehensive_pdf_report(analysis, combined_analysis):
    """Generate comprehensive PDF report (placeholder)"""
    st.info("Comprehensive PDF report generation will be implemented in the next phase.")

def export_comprehensive_data_csv(analysis, combined_analysis):
    """Export comprehensive data as CSV (placeholder)"""
    st.info("Comprehensive CSV export will be implemented in the next phase.")

def generate_pdf_report(analysis, combined_analysis=None, include_raw_data=True, include_visualizations=True, include_recommendations=True, include_metadata=True):
    """Generate a comprehensive PDF report with customizable sections"""
    try:
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
        import io
        
        # Create PDF buffer
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
        
        # Get styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=24, spaceAfter=30, alignment=TA_CENTER, textColor=colors.HexColor('#2E7D32'))
        heading_style = ParagraphStyle('CustomHeading', parent=styles['Heading2'], fontSize=16, spaceAfter=12, textColor=colors.HexColor('#4CAF50'))
        subheading_style = ParagraphStyle('CustomSubHeading', parent=styles['Heading3'], fontSize=14, spaceAfter=8, textColor=colors.HexColor('#388E3C'))
        body_style = ParagraphStyle('CustomBody', parent=styles['Normal'], fontSize=11, spaceAfter=6)
        
        # Build story
        story = []
        
        # Title Page
        story.append(Paragraph("SP LAB Test Report Analysis", title_style))
        story.append(Spacer(1, 20))
        story.append(Paragraph(f"Generated on: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}", styles['Normal']))
        story.append(PageBreak())
        
        # Executive Summary
        if combined_analysis and include_recommendations:
            story.append(Paragraph("Executive Summary", heading_style))
            summary = combined_analysis.get('summary', 'No summary available')
            story.append(Paragraph(summary, body_style))
            story.append(Spacer(1, 20))
        
        # Comprehensive Analysis Results
        if combined_analysis and combined_analysis.get('comprehensive_results'):
            story.append(Paragraph("Comprehensive Analysis Results", heading_style))
            
            comprehensive_results = combined_analysis.get('comprehensive_results', {})
            
            # Key Findings
            if comprehensive_results.get('key_findings'):
                story.append(Paragraph("Key Findings", subheading_style))
                key_findings = comprehensive_results['key_findings']
                if isinstance(key_findings, list):
                    for finding in key_findings:
                        story.append(Paragraph(f"• {finding}", body_style))
                else:
                    story.append(Paragraph(str(key_findings), body_style))
                story.append(Spacer(1, 12))
            
            # Economic Analysis
            if comprehensive_results.get('economic_analysis'):
                story.append(Paragraph("Economic Analysis", subheading_style))
                economic = comprehensive_results['economic_analysis']
                if isinstance(economic, dict):
                    for key, value in economic.items():
                        if key != 'cost_breakdown':  # Handle separately
                            story.append(Paragraph(f"<b>{key.replace('_', ' ').title()}:</b> {value}", body_style))
                story.append(Spacer(1, 12))
            
            # Yield Forecast
            if comprehensive_results.get('yield_forecast'):
                story.append(Paragraph("Yield Forecast", subheading_style))
                yield_forecast = comprehensive_results['yield_forecast']
                if isinstance(yield_forecast, dict):
                    for key, value in yield_forecast.items():
                        story.append(Paragraph(f"<b>{key.replace('_', ' ').title()}:</b> {value}", body_style))
                story.append(Spacer(1, 12))
            
            # Recommendations
            if comprehensive_results.get('recommendations'):
                story.append(Paragraph("Recommendations", subheading_style))
                recommendations = comprehensive_results['recommendations']
                if isinstance(recommendations, list):
                    for rec in recommendations:
                        if isinstance(rec, dict):
                            action = rec.get('action', '')
                            description = rec.get('description', '')
                            priority = rec.get('priority', 'medium')
                            story.append(Paragraph(f"<b>{action}</b> ({priority}): {description}", body_style))
                        else:
                            story.append(Paragraph(f"• {rec}", body_style))
                else:
                    story.append(Paragraph(str(recommendations), body_style))
                story.append(Spacer(1, 12))
        
        # Raw Data Section
        if include_raw_data:
            story.append(Paragraph("Raw Extracted Data", heading_style))
            
            # Soil Data
            soil_data = analysis.get('soil_data', {})
            if soil_data and soil_data.get('ocr_result', {}).get('success'):
                story.append(Paragraph("Soil Analysis Data", subheading_style))
                soil_params = soil_data.get('ocr_result', {}).get('parameters', [])
                
                if soil_params:
                    # Create table data
                    table_data = [['Sample No.', 'Parameter', 'Value', 'Unit']]
                    for param in soil_params[:20]:  # Limit to first 20 for PDF
                        table_data.append([
                            param.get('Sample_No', 'N/A'),
                            param.get('Parameter', 'N/A'),
                            str(param.get('Value', 'N/A')),
                            param.get('Unit', 'N/A')
                        ])
                    
                    # Create table
                    table = Table(table_data)
                    table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, 0), 10),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black)
                    ]))
                    story.append(table)
                    story.append(Spacer(1, 20))
            
            # Leaf Data
            leaf_data = analysis.get('leaf_data', {})
            if leaf_data and leaf_data.get('ocr_result', {}).get('success'):
                story.append(Paragraph("Leaf Analysis Data", subheading_style))
                leaf_params = leaf_data.get('ocr_result', {}).get('parameters', [])
                
                if leaf_params:
                    # Create table data
                    table_data = [['Sample No.', 'Parameter', 'Value', 'Unit']]
                    for param in leaf_params[:20]:  # Limit to first 20 for PDF
                        table_data.append([
                            param.get('Sample_No', 'N/A'),
                            param.get('Parameter', 'N/A'),
                            str(param.get('Value', 'N/A')),
                            param.get('Unit', 'N/A')
                        ])
                    
                    # Create table
                    table = Table(table_data)
                    table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, 0), 10),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black)
                    ]))
                    story.append(table)
                    story.append(Spacer(1, 20))
        
        # Analysis Results
        if combined_analysis and include_recommendations:
            story.append(PageBreak())
            story.append(Paragraph("Analysis Results", heading_style))
            
            comprehensive_results = combined_analysis.get('comprehensive_results', {})
            
            # Key Metrics
            summary_metrics = comprehensive_results.get('summary_metrics', {})
            if summary_metrics:
                story.append(Paragraph("Key Metrics", subheading_style))
                metrics_data = [
                    ['Metric', 'Value'],
                    ['Parameters Analyzed', str(summary_metrics.get('total_parameters_analyzed', 0))],
                    ['Issues Identified', str(summary_metrics.get('total_issues_identified', 0))],
                    ['Critical Issues', str(summary_metrics.get('critical_issues_count', 0))]
                ]
                
                health_indicators = comprehensive_results.get('health_indicators', {})
                if health_indicators:
                    metrics_data.append(['Health Score', f"{health_indicators.get('overall_health_score', 0):.1f}%"])
                
                metrics_table = Table(metrics_data)
                metrics_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.lightblue),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                story.append(metrics_table)
                story.append(Spacer(1, 20))
            
            # Recommendations
            detailed_analysis = comprehensive_results.get('detailed_analysis', {})
            recommendations = detailed_analysis.get('recommendations', [])
            if recommendations:
                story.append(Paragraph("Recommendations", subheading_style))
                for i, rec in enumerate(recommendations[:10], 1):  # Limit to 10 recommendations
                    story.append(Paragraph(f"{i}. {rec}", styles['Normal']))
                    story.append(Spacer(1, 6))
        
        # Metadata
        if include_metadata:
            story.append(PageBreak())
            story.append(Paragraph("Analysis Metadata", heading_style))
            
            metadata_data = [
                ['Field', 'Value'],
                ['Analysis Date', datetime.now().strftime('%Y-%m-%d %H:%M:%S')],
                ['Report Type', 'Combined Soil & Leaf Analysis'],
                ['OCR Engine', 'Tesseract with Enhanced Processing'],
                ['Analysis Engine', 'AI-Powered Agricultural Analysis']
            ]
            
            # Add file information if available
            if analysis.get('soil_data', {}).get('ocr_result', {}).get('success'):
                soil_params_count = len(analysis.get('soil_data', {}).get('ocr_result', {}).get('parameters', []))
                metadata_data.append(['Soil Parameters Extracted', str(soil_params_count)])
            
            if analysis.get('leaf_data', {}).get('ocr_result', {}).get('success'):
                leaf_params_count = len(analysis.get('leaf_data', {}).get('ocr_result', {}).get('parameters', []))
                metadata_data.append(['Leaf Parameters Extracted', str(leaf_params_count)])
            
            metadata_table = Table(metadata_data)
            metadata_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(metadata_table)
        
        # Build PDF
        doc.build(story)
        
        # Get PDF content
        pdf_content = buffer.getvalue()
        buffer.close()
        
        return pdf_content
        
    except ImportError:
        # Fallback if reportlab is not available
        st.error("PDF generation requires reportlab library. Please install it: pip install reportlab")
        return None
    except Exception as e:
        st.error(f"Error generating PDF: {str(e)}")
        return None

def export_data_csv(analysis):
    """Export data as CSV (placeholder)"""
    st.info("CSV export will be implemented in the next phase.")

if __name__ == "__main__":
    main()