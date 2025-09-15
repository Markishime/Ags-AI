import streamlit as st
import sys
import os
from datetime import datetime
from PIL import Image

# Add utils to path
utils_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'utils')
if utils_path not in sys.path:
    sys.path.append(utils_path)

# Import utilities with error handling and robust fallbacks
try:
    from utils.ocr_utils import extract_data_from_image
except Exception:
    try:
        from ocr_utils import extract_data_from_image
    except Exception as e:
        st.error(f"Import error (ocr_utils): {e}")
        st.stop()

try:
    from utils.config_manager import get_ui_config
except Exception:
    try:
        from config_manager import get_ui_config
    except Exception as e:
        st.error(f"Import error (config_manager): {e}")
        st.stop()

def show_upload_page():
    """Main upload page - focused only on file upload and preview"""
    # Check authentication at page level
    if not st.session_state.get('authenticated', False):
        st.markdown('<h1 style="color: #2E8B57; text-align: center;">📤 Upload SP LAB Reports</h1>', unsafe_allow_html=True)
        st.warning("🔒 Please log in to access upload features.")
        
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
    
    st.markdown('<h1 style="color: #2E8B57; text-align: center;">📤 Upload SP LAB Reports</h1>', unsafe_allow_html=True)
    st.markdown("### Upload your soil and leaf analysis reports for comprehensive AI-powered analysis")
    
    # Main upload section
    upload_section()
    

def upload_section():
    """Handle file upload and preview only"""
    
    # Get UI configuration
    ui_config = get_ui_config()
    
    # Check authentication before allowing upload
    if not st.session_state.get('authenticated', False):
        st.warning("🔒 Please log in to upload files.")
        if st.button("🔑 Login to Continue", type="primary", use_container_width=True):
            st.session_state.current_page = 'login'
            st.rerun()
        return
    
    st.markdown("### 📁 Upload SP LAB Test Reports")
    st.info("💡 **Tip:** Upload both soil and leaf analysis reports for comprehensive analysis. Please upload both files.")
    
    # Add information about dynamic OCR processing
    st.info("🔄 **Dynamic OCR Processing:** The OCR Data Preview automatically processes new images when uploaded. Use the 'Refresh OCR' button to re-process if needed.")
    
    # Create separate containers for soil and leaf analysis
    col1, col2 = st.columns(2)
    
    # Initialize session state for uploaded files
    if 'soil_file' not in st.session_state:
        st.session_state.soil_file = None
    if 'leaf_file' not in st.session_state:
        st.session_state.leaf_file = None
    if 'land_yield_data' not in st.session_state:
        st.session_state.land_yield_data = {
            'land_size': 0,
            'land_unit': 'hectares',
            'current_yield': 0,
            'yield_unit': 'tonnes/hectare',
            'palm_density': 148  # Default palms per hectare
        }
    
    # Load saved land & yield data from Firestore if user is authenticated
    if st.session_state.get('authenticated', False) and st.session_state.get('user_id'):
        try:
            from utils.firebase_config import get_firestore_client
            db = get_firestore_client()
            if db:
                user_ref = db.collection('users').document(st.session_state['user_id'])
                user_doc = user_ref.get()
                if user_doc.exists:
                    user_data = user_doc.to_dict()
                    if 'land_yield_data' in user_data:
                        saved_data = user_data['land_yield_data']
                        # Only load if we don't have current data or if saved data is more recent
                        if (st.session_state.land_yield_data['land_size'] == 0 and 
                            st.session_state.land_yield_data['current_yield'] == 0):
                            st.session_state.land_yield_data.update({
                                'land_size': saved_data.get('land_size', 0),
                                'land_unit': saved_data.get('land_unit', 'hectares'),
                                'current_yield': saved_data.get('current_yield', 0),
                                'yield_unit': saved_data.get('yield_unit', 'tonnes/hectare')
                            })
        except Exception as e:
            # Silently fail - user can still enter data manually
            pass
    
    with col1:
        with st.container():
            st.markdown("#### 🌱 Soil Analysis")
            st.markdown("Upload **soil test reports** for nutrient analysis")
            st.info("📋 **Expected:** Soil analysis reports with pH, organic carbon, available P, exchangeable cations, etc.")
            
            soil_file = st.file_uploader(
                "Choose soil analysis file",
                type=['png', 'jpg', 'jpeg', 'pdf', 'csv', 'xlsx', 'xls'],
                help="Upload SP LAB soil analysis reports (image, PDF, or Excel/CSV)",
                key="soil_uploader"
            )
            
            if soil_file is not None:
                st.session_state.soil_file = soil_file
                # Display uploaded image
                st.markdown("##### 📄 Uploaded Soil Report")
                file_ext = os.path.splitext(soil_file.name)[1].lower()
                is_image = file_ext in ['.png', '.jpg', '.jpeg']
                if is_image:
                    soil_image = Image.open(soil_file)
                    st.image(soil_image, caption="Soil Analysis Report", use_container_width=True)
                    st.info(f"**File:** {soil_file.name}\n**Size:** {soil_file.size} bytes\n**Format:** {soil_image.format}")
                else:
                    st.info(f"**File:** {soil_file.name}\n**Size:** {soil_file.size} bytes\n**Type:** {file_ext}")
                
                # Enhanced OCR preview - Dynamic processing
                with st.expander("🔍 OCR Data Preview", expanded=True):
                    # Add refresh button for manual re-processing
                    col_refresh, col_timestamp = st.columns([1, 3])
                    with col_refresh:
                        refresh_ocr = st.button("🔄 Refresh OCR", key="refresh_soil_ocr", help="Re-process the image with OCR")
                    with col_timestamp:
                        st.caption(f"Last processed: {datetime.now().strftime('%H:%M:%S')}")
                    
                    try:
                        # Force re-processing by using file hash as cache key
                        file_hash = hash(soil_file.getvalue())
                        cache_key = f"soil_ocr_{file_hash}"
                        
                        # Check if we need to re-process (always re-process for dynamic behavior)
                        with st.spinner("🔄 Processing soil image with OCR..."):
                            # Save image to temporary file and pass path to OCR function
                            import tempfile
                            import time
                            if is_image:
                                with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext or '.png') as tmp_file:
                                    soil_image.save(tmp_file.name)
                                    ocr_preview = extract_data_from_image(tmp_file.name)
                                    tmp_file_path = tmp_file.name
                            else:
                                with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext or '.pdf') as tmp_file:
                                    tmp_file.write(soil_file.getvalue())
                                    ocr_preview = extract_data_from_image(tmp_file.name)
                                    tmp_file_path = tmp_file.name
                            # Clean up temporary file after OCR is done with delay
                            try:
                                time.sleep(0.1)  # Small delay to ensure file is released
                                os.unlink(tmp_file_path)
                            except (PermissionError, FileNotFoundError):
                                # File might still be in use or already deleted, ignore error
                                pass
                        
                        if ocr_preview.get('success'):
                            # Check if detected content type matches the upload container
                            tables = ocr_preview.get('tables', [])
                            if tables:
                                detected_type = tables[0].get('type', 'unknown')
                                
                                if detected_type.lower() != 'soil':
                                    st.error(f"❌ **Content Type Mismatch!**")
                                    st.warning(f"🔍 **Detected:** {detected_type.title()} analysis report")
                                    st.warning(f"📁 **Expected:** Soil analysis report")
                                    st.info("💡 **Please upload a soil analysis report image in this container.**")
                                    st.info("🍃 **For leaf analysis, please use the Leaf Analysis container on the right.**")
                                else:
                                    samples = tables[0].get('samples', [])
                                    if samples:
                                        sample_count = len(samples)
                                        st.success(f"✅ **{sample_count} soil samples detected**")
                                        
                                        # Show first sample preview with better formatting
                                        if sample_count > 0:
                                            first_sample = samples[0]
                                            st.markdown("**📊 First Sample Preview:**")
                                            
                                            # Display in a nice format
                                            col_a, col_b = st.columns(2)
                                            with col_a:
                                                st.write(f"**Lab No:** {first_sample.get('Lab No.', 'N/A')}")
                                                st.write(f"**Sample No:** {first_sample.get('Sample No.', 'N/A')}")
                                                st.write(f"**pH:** {first_sample.get('pH', 'N/A')}")
                                                st.write(f"**Nitrogen %:** {first_sample.get('Nitrogen %', 'N/A')}")
                                                st.write(f"**Organic Carbon %:** {first_sample.get('Organic Carbon %', 'N/A')}")
                                            
                                            with col_b:
                                                st.write(f"**Total P (mg/kg):** {first_sample.get('Total P mg/kg', 'N/A')}")
                                                st.write(f"**Available P (mg/kg):** {first_sample.get('Available P mg/kg', 'N/A')}")
                                                st.write(f"**Exchangeable K (meq%):** {first_sample.get('Exch. K meq%', 'N/A')}")
                                                st.write(f"**Exchangeable Ca (meq%):** {first_sample.get('Exch. Ca meq%', 'N/A')}")
                                                st.write(f"**Exchangeable Mg (meq%):** {first_sample.get('Exch. Mg meq%', 'N/A')}")
                                                st.write(f"**CEC (meq%):** {first_sample.get('C.E.C meq%', 'N/A')}")
                                            
                                            st.success("✅ Soil data extraction successful!")
                                            
                                            # Show additional samples if available
                                            if sample_count > 1:
                                                with st.expander(f"📋 View All {sample_count} Samples", expanded=False):
                                                    for i, sample in enumerate(samples):
                                                        st.markdown(f"**Sample {i+1}:**")
                                                        st.json(sample)
                                    else:
                                        st.warning("⚠️ No samples detected in soil report")
                            else:
                                st.warning("⚠️ No tables detected in soil report")
                        else:
                            st.error(f"❌ OCR extraction failed: {ocr_preview.get('error', 'Unknown error')}")
                    except Exception as e:
                        st.error(f"❌ OCR Preview Error: {str(e)}")
                        st.exception(e)
    
    with col2:
        with st.container():
            st.markdown("#### 🍃 Leaf Analysis")
            st.markdown("Upload **leaf test reports** for nutrient deficiency analysis")
            st.info("📋 **Expected:** Leaf analysis reports with N%, P%, K%, Mg%, Ca%, B, Cu, Zn content, etc.")
            
            leaf_file = st.file_uploader(
                "Choose leaf analysis file",
                type=['png', 'jpg', 'jpeg', 'pdf', 'csv', 'xlsx', 'xls'],
                help="Upload SP LAB leaf analysis reports (image, PDF, or Excel/CSV)",
                key="leaf_uploader"
            )
            
            if leaf_file is not None:
                st.session_state.leaf_file = leaf_file
                # Display uploaded image
                st.markdown("##### 📄 Uploaded Leaf Report")
                leaf_ext = os.path.splitext(leaf_file.name)[1].lower()
                leaf_is_image = leaf_ext in ['.png', '.jpg', '.jpeg']
                if leaf_is_image:
                    leaf_image = Image.open(leaf_file)
                    st.image(leaf_image, caption="Leaf Analysis Report", use_container_width=True)
                    st.info(f"**File:** {leaf_file.name}\n**Size:** {leaf_file.size} bytes\n**Format:** {leaf_image.format}")
                else:
                    st.info(f"**File:** {leaf_file.name}\n**Size:** {leaf_file.size} bytes\n**Type:** {leaf_ext}")
                
                # Enhanced OCR preview - Dynamic processing
                with st.expander("🔍 OCR Data Preview", expanded=True):
                    # Add refresh button for manual re-processing
                    col_refresh, col_timestamp = st.columns([1, 3])
                    with col_refresh:
                        refresh_ocr = st.button("🔄 Refresh OCR", key="refresh_leaf_ocr", help="Re-process the image with OCR")
                    with col_timestamp:
                        st.caption(f"Last processed: {datetime.now().strftime('%H:%M:%S')}")
                    
                    try:
                        # Force re-processing by using file hash as cache key
                        file_hash = hash(leaf_file.getvalue())
                        cache_key = f"leaf_ocr_{file_hash}"
                        
                        # Check if we need to re-process (always re-process for dynamic behavior)
                        with st.spinner("🔄 Processing leaf image with OCR..."):
                            # Save image to temporary file and pass path to OCR function
                            import tempfile
                            import time
                            if leaf_is_image:
                                with tempfile.NamedTemporaryFile(delete=False, suffix=leaf_ext or '.png') as tmp_file:
                                    leaf_image.save(tmp_file.name)
                                    ocr_preview = extract_data_from_image(tmp_file.name)
                                    tmp_file_path = tmp_file.name
                            else:
                                with tempfile.NamedTemporaryFile(delete=False, suffix=leaf_ext or '.pdf') as tmp_file:
                                    tmp_file.write(leaf_file.getvalue())
                                    ocr_preview = extract_data_from_image(tmp_file.name)
                                    tmp_file_path = tmp_file.name
                            # Clean up temporary file after OCR is done with delay
                            try:
                                time.sleep(0.1)  # Small delay to ensure file is released
                                os.unlink(tmp_file_path)
                            except (PermissionError, FileNotFoundError):
                                # File might still be in use or already deleted, ignore error
                                pass
                        
                        if ocr_preview.get('success'):
                            # Check if detected content type matches the upload container
                            tables = ocr_preview.get('tables', [])
                            if tables:
                                detected_type = tables[0].get('type', 'unknown')
                                
                                if detected_type.lower() != 'leaf':
                                    st.error(f"❌ **Content Type Mismatch!**")
                                    st.warning(f"🔍 **Detected:** {detected_type.title()} analysis report")
                                    st.warning(f"📁 **Expected:** Leaf analysis report")
                                    st.info("💡 **Please upload a leaf analysis report image in this container.**")
                                    st.info("🌱 **For soil analysis, please use the Soil Analysis container on the left.**")
                                else:
                                    samples = tables[0].get('samples', [])
                                    if samples:
                                        sample_count = len(samples)
                                        st.success(f"✅ **{sample_count} leaf samples detected**")
                                        
                                        # Show first sample preview with better formatting
                                        if sample_count > 0:
                                            first_sample = samples[0]
                                            st.markdown("**📊 First Sample Preview:**")
                                            
                                            # Display in a nice format
                                            col_a, col_b = st.columns(2)
                                            with col_a:
                                                st.write(f"**Lab No:** {first_sample.get('Lab No.', 'N/A')}")
                                                st.write(f"**Sample No:** {first_sample.get('Sample No.', 'N/A')}")
                                                # Get % Dry Matter values
                                                percent_dm = first_sample.get('% Dry Matter', {})
                                                st.write(f"**N %:** {percent_dm.get('N', 'N/A')}")
                                                st.write(f"**P %:** {percent_dm.get('P', 'N/A')}")
                                                st.write(f"**K %:** {percent_dm.get('K', 'N/A')}")
                                            
                                            with col_b:
                                                st.write(f"**Mg %:** {percent_dm.get('Mg', 'N/A')}")
                                                st.write(f"**Ca %:** {percent_dm.get('Ca', 'N/A')}")
                                                # Get mg/kg Dry Matter values
                                                mgkg_dm = first_sample.get('mg/kg Dry Matter', {})
                                                st.write(f"**B (mg/kg):** {mgkg_dm.get('B', 'N/A')}")
                                                st.write(f"**Cu (mg/kg):** {mgkg_dm.get('Cu', 'N/A')}")
                                                st.write(f"**Zn (mg/kg):** {mgkg_dm.get('Zn', 'N/A')}")
                                            
                                            st.success("✅ Leaf data extraction successful!")
                                            
                                            # Show additional samples if available
                                            if sample_count > 1:
                                                with st.expander(f"📋 View All {sample_count} Samples", expanded=False):
                                                    for i, sample in enumerate(samples):
                                                        st.markdown(f"**Sample {i+1}:**")
                                                        st.json(sample)
                                    else:
                                        st.warning("⚠️ No samples detected in leaf report")
                            else:
                                st.warning("⚠️ No tables detected in leaf report")
                        else:
                            st.error(f"❌ OCR extraction failed: {ocr_preview.get('error', 'Unknown error')}")
                    except Exception as e:
                        st.error(f"❌ OCR Preview Error: {str(e)}")
                        st.exception(e)
    
    # Land/Yield Size Data Section
    st.markdown("---")
    st.markdown("### 🌾 Land & Yield Information (Required)")
    st.markdown("*This information is essential for generating accurate economic forecasts and 5-year yield projections*")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("#### 📏 Land Size")
        land_size = st.number_input(
            "Land Size",
            min_value=0,
            max_value=10000,
            value=st.session_state.land_yield_data['land_size'],
            step=1,
            help="Enter the total land area for analysis",
            key="land_size_input"
        )
        land_unit = st.selectbox(
            "Unit",
            options=['hectares', 'acres', 'square_meters'],
            index=['hectares', 'acres', 'square_meters'].index(st.session_state.land_yield_data['land_unit']),
            key="land_unit_input"
        )
        st.session_state.land_yield_data['land_size'] = land_size
        st.session_state.land_yield_data['land_unit'] = land_unit
    
    with col2:
        st.markdown("#### 🌾 Current Yield")
        current_yield = st.number_input(
            "Current Yield",
            min_value=0,
            max_value=1000,
            value=st.session_state.land_yield_data['current_yield'],
            step=1,
            help="Enter the current yield per unit area",
            key="current_yield_input"
        )
        yield_unit = st.selectbox(
            "Yield Unit",
            options=['tonnes/hectare', 'kg/hectare', 'tonnes/acre', 'kg/acre'],
            index=['tonnes/hectare', 'kg/hectare', 'tonnes/acre', 'kg/acre'].index(st.session_state.land_yield_data['yield_unit']),
            key="yield_unit_input"
        )
        st.session_state.land_yield_data['current_yield'] = current_yield
        st.session_state.land_yield_data['yield_unit'] = yield_unit
    
    with col3:
        st.markdown("#### 🌴 Palm Density")
        palm_density = st.number_input(
            "Palms per Hectare",
            min_value=100,
            max_value=200,
            value=st.session_state.land_yield_data['palm_density'],
            step=1,
            help="Enter the number of oil palm trees per hectare (typical range: 136-148 palms/ha)",
            key="palm_density_input"
        )
        st.session_state.land_yield_data['palm_density'] = palm_density
    
    # Display summary of entered data
    if land_size > 0 or current_yield > 0:
        st.info(f"📊 **Summary:** {land_size} {land_unit} | {current_yield} {yield_unit} | {palm_density} palms/ha")
    
    # Save button for land & yield data
    col_save1, col_save2, col_save3 = st.columns([1, 2, 1])
    with col_save2:
        if st.button("💾 Save Land & Yield Data", type="secondary", use_container_width=True, key="save_land_yield"):
            if land_size > 0 and current_yield > 0:
                try:
                    # Save to Firestore
                    from utils.firebase_config import get_firestore_client, initialize_firebase
                    
                    db = get_firestore_client()
                    # Try to initialize Firebase and reacquire if needed
                    if not db:
                        initialize_firebase()
                        db = get_firestore_client()
                    if not st.session_state.get('authenticated', False):
                        st.error("🔒 You must be logged in to save data.")
                    elif db:
                        user_id = st.session_state.get('user_id')
                        if user_id:
                            # Save land & yield data to user's profile
                            user_ref = db.collection('users').document(user_id)
                            user_ref.update({
                                'land_yield_data': {
                                    'land_size': land_size,
                                    'land_unit': land_unit,
                                    'current_yield': current_yield,
                                    'yield_unit': yield_unit,
                                    'last_updated': datetime.now()
                                }
                            })
                            st.success("✅ Land & Yield data saved successfully!")
                        else:
                            st.error("❌ User ID not found. Please log in again.")
                    else:
                        st.error("❌ Database connection not available. Please try again later.")
                except Exception as e:
                    st.error(f"❌ Failed to save data: {str(e)}")
            else:
                st.warning("⚠️ Please enter both land size and current yield before saving.")
    
    # Analysis button
    st.markdown("---")
    
    # Check all requirements for analysis
    soil_uploaded = st.session_state.soil_file is not None
    leaf_uploaded = st.session_state.leaf_file is not None
    land_yield_provided = land_size > 0 and current_yield > 0
    user_authenticated = st.session_state.get('authenticated', False)
    
    if soil_uploaded and leaf_uploaded and land_yield_provided:
        # All requirements met
        if not user_authenticated:
            st.error("🔒 Authentication required to analyze reports. Please log in.")
            if st.button("🔑 Login to Analyze", type="primary", use_container_width=True):
                st.session_state.current_page = 'login'
                st.rerun()
        elif st.button("🚀 Start Analysis", type="primary", use_container_width=True, key="start_analysis"):
            # Store analysis data in session state
            st.session_state.analysis_data = {
                'soil_file': st.session_state.soil_file,
                'leaf_file': st.session_state.leaf_file,
                'land_yield_data': st.session_state.land_yield_data,
                'timestamp': datetime.now()
            }
                    
            # Redirect to results page
            st.session_state.current_page = 'results'
            st.rerun()
    else:
        # Check what's missing and provide specific guidance
        missing_items = []
        if not soil_uploaded:
            missing_items.append("🌱 Soil Report")
        if not leaf_uploaded:
            missing_items.append("🍃 Leaf Report")
        if not land_yield_provided:
            missing_items.append("🌾 Land & Yield Information")
        
        if missing_items:
            st.warning(f"⚠️ **All items are required for comprehensive oil palm analysis.** Please provide: {', '.join(missing_items)}")
            
            # Provide specific guidance for land & yield
            if not land_yield_provided:
                st.info("💡 **Land & Yield Information is essential for:**\n"
                       "• Economic impact calculations\n"
                       "• ROI and payback period analysis\n"
                       "• 5-year yield projections\n"
                       "• Investment recommendations")
        else:
            st.info("📁 Please upload both soil and leaf reports and provide land & yield information to start comprehensive oil palm analysis.")

def main():
    """Wrapper function for backward compatibility"""
    # Initialize session state if not already done
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 'upload'
    
    show_upload_page()

if __name__ == "__main__":
    main()
