import streamlit as st
import sys
import os
from datetime import datetime
import pandas as pd
# Use our configured Firestore client instead of direct import

# Add utils to path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'utils'))

# Import utilities
from utils.firebase_config import get_firestore_client, COLLECTIONS
from google.cloud.firestore import Query

def show_history_page():
    """Main history page - displays past analysis results"""
    # Check authentication
    if not st.session_state.get('authenticated', False):
        st.markdown('<h1 style="color: #2E8B57; text-align: center;">📋 Analysis History</h1>', unsafe_allow_html=True)
        st.warning("🔒 Please log in to view analysis history.")
        
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
    
    st.markdown('<h1 style="color: #2E8B57; text-align: center;">📋 Analysis History</h1>', unsafe_allow_html=True)
    
    # Display statistics dashboard
    display_history_statistics()
    
    # Display analysis history
    display_analysis_history()
    
    # Navigation buttons
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📤 Analyze Files", type="primary", use_container_width=True):
            st.session_state.current_page = 'upload'
            st.rerun()
    
    with col2:
        if st.button("🔍 View Current Results", use_container_width=True):
            st.session_state.current_page = 'results'
            st.rerun()
    
    with col3:
        if st.button("🏠 Home", use_container_width=True):
            st.session_state.current_page = 'home'
            st.rerun()

def display_history_statistics():
    """Display statistics dashboard for analysis history"""
    try:
        user_id = st.session_state.get('user_id')
        if not user_id:
            return
        
        db = get_firestore_client()
        if not db:
            return
        
        # Get all user analyses for statistics from analysis_results collection
        analyses_ref = db.collection('analysis_results')
        user_analyses = analyses_ref.where('user_id', '==', user_id).get()
        

        
        if not user_analyses:
            return
        
        # Calculate statistics
        total_analyses = len(user_analyses)
        completed_analyses = total_analyses  # analysis_results are always completed
        failed_analyses = 0  # No failed analyses in analysis_results collection
        
        # Calculate average health scores and other metrics
        health_scores = []
        total_issues = 0
        total_parameters = 0
        
        for doc in user_analyses:
            analysis_data = doc.to_dict()
            
            # Get metrics from analysis_metadata
            analysis_metadata = analysis_data.get('analysis_metadata', {})
            if analysis_metadata:
                # Try to extract health score from metadata or calculate from step analysis
                step_analysis = analysis_data.get('step_by_step_analysis', [])
                if step_analysis:
                    # Calculate a simple health score based on number of issues found
                    total_steps = len(step_analysis)
                    issues_found = 0
                    for step in step_analysis:
                        if 'issues_identified' in step:
                            issues_found += len(step['issues_identified'])
                    
                    # Simple health score calculation (100 - (issues * 10))
                    health_score = max(0, 100 - (issues_found * 10))
                    health_scores.append(health_score)
                    total_issues += issues_found
                    total_parameters += total_steps
        
        avg_health_score = sum(health_scores) / len(health_scores) if health_scores else 0
        avg_issues_per_analysis = total_issues / completed_analyses if completed_analyses > 0 else 0
        avg_parameters_per_analysis = total_parameters / completed_analyses if completed_analyses > 0 else 0
        
        # Get date range with proper datetime handling
        timestamps = []
        for doc in user_analyses:
            created_at = doc.to_dict().get('created_at', datetime.now())
            # Convert timezone-aware datetime to naive for comparison
            if hasattr(created_at, 'replace') and hasattr(created_at, 'tzinfo') and created_at.tzinfo is not None:
                created_at_naive = created_at.replace(tzinfo=None)
            else:
                created_at_naive = created_at
            timestamps.append(created_at_naive)
        
        if timestamps:
            earliest = min(timestamps)
            latest = max(timestamps)
            days_span = (latest - earliest).days + 1
        else:
            days_span = 0
        
        # Display statistics in columns
        st.markdown("### 📊 Analysis Statistics")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="📈 Total Analyses",
                value=total_analyses,
                delta=f"{completed_analyses} completed"
            )
        
        with col2:
            st.metric(
                label="🎯 Success Rate",
                value=f"{(completed_analyses/total_analyses*100):.1f}%" if total_analyses > 0 else "0%",
                delta=f"{failed_analyses} failed" if failed_analyses > 0 else None
            )
        
        with col3:
            st.metric(
                label="💚 Avg Health Score",
                value=f"{avg_health_score:.1f}%" if avg_health_score > 0 else "N/A",
                delta=f"{len(health_scores)} analyses"
            )
        
        with col4:
            st.metric(
                label="📅 Analysis Period",
                value=f"{days_span} days",
                delta=f"Since {earliest.strftime('%Y-%m-%d')}" if timestamps else None
            )
        
        # Additional metrics row
        col5, col6, col7, col8 = st.columns(4)
        
        with col5:
            st.metric(
                label="🔍 Avg Issues Found",
                value=f"{avg_issues_per_analysis:.1f}",
                delta="per analysis"
            )
        
        with col6:
            st.metric(
                label="📊 Avg Parameters",
                value=f"{avg_parameters_per_analysis:.1f}",
                delta="per analysis"
            )
        
        with col7:
            # Calculate analysis frequency
            if days_span > 0:
                frequency = total_analyses / days_span
                st.metric(
                    label="📈 Analysis Frequency",
                    value=f"{frequency:.2f}",
                    delta="per day"
                )
            else:
                st.metric(
                    label="📈 Analysis Frequency",
                    value="N/A",
                    delta="per day"
                )
        
        with col8:
            # Calculate recent activity (last 7 days)
            now = datetime.now()
            recent_analyses = 0
            for doc in user_analyses:
                created_at = doc.to_dict().get('created_at', now)
                # Convert timezone-aware datetime to naive for comparison
                if hasattr(created_at, 'replace') and hasattr(created_at, 'tzinfo') and created_at.tzinfo is not None:
                    created_at_naive = created_at.replace(tzinfo=None)
                else:
                    created_at_naive = created_at
                if (now - created_at_naive).days <= 7:
                    recent_analyses += 1
            
            st.metric(
                label="🕒 Recent Activity",
                value=recent_analyses,
                delta="last 7 days"
            )
        
        st.markdown("---")
        
    except Exception as e:
        st.error(f"Error loading statistics: {str(e)}")

def display_analysis_history():
    """Display user's analysis history with enhanced features"""
    st.markdown("### 📊 Your Analysis History")
    
    # Check if user info is available
    user_id = st.session_state.get('user_id')
    if not user_id:
        st.error("User information not available. Please log in again.")
        return
    
    try:
        db = get_firestore_client()
        if not db:
            st.error("Database connection failed")
            return
        
        # Add search and filter options
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            search_term = st.text_input("🔍 Search analyses", placeholder="Search by date, status, or content...")
        with col2:
            status_filter = st.selectbox("Filter by Status", ["All", "completed"])
        with col3:
            limit = st.selectbox("Show", [10, 20, 50], index=1)
        
        # Get user's analyses from analysis_results collection using correct field
        analyses_ref = db.collection('analysis_results')
        query = analyses_ref.where('user_id', '==', user_id).order_by('created_at', direction=Query.DESCENDING).limit(limit)
        
        user_analyses = query.get()
        
        if not user_analyses:
            st.info("📋 No analysis history found. Upload your first report to get started!")
            return
        
        # Filter analyses based on search and status
        filtered_analyses = []
        for doc in user_analyses:
            analysis_data = doc.to_dict()
            
            # Apply status filter (analysis_results are always completed)
            if status_filter != "All" and status_filter != "completed":
                continue
            
            # Apply search filter
            if search_term:
                search_lower = search_term.lower()
                created_at = analysis_data.get('created_at', datetime.now())
                
                # Handle timezone-aware datetime for string formatting
                if hasattr(created_at, 'replace') and hasattr(created_at, 'tzinfo') and created_at.tzinfo is not None:
                    created_at_naive = created_at.replace(tzinfo=None)
                else:
                    created_at_naive = created_at
                    
                timestamp_str = created_at_naive.strftime('%Y-%m-%d %H:%M').lower()
                status_str = 'completed'  # analysis_results are always completed
                
                # Search in timestamp, status, and analysis content
                if (search_lower not in timestamp_str and 
                    search_lower not in status_str and
                    not _search_in_analysis_content(analysis_data, search_lower)):
                    continue
            
            filtered_analyses.append((doc, analysis_data))
        
        if not filtered_analyses:
            st.info("🔍 No analyses match your search criteria.")
            return
        
        # Display filtered analyses
        st.markdown(f"**Found {len(filtered_analyses)} analysis record(s)**")
        
        for doc, analysis_data in filtered_analyses:
            created_at = analysis_data.get('created_at', datetime.now())
            status = 'completed'  # analysis_results are always completed
            
            # Handle timezone-aware datetime for display
            if hasattr(created_at, 'replace') and hasattr(created_at, 'tzinfo') and created_at.tzinfo is not None:
                timestamp = created_at.replace(tzinfo=None)
            else:
                timestamp = created_at
            
            # Create status badge
            status_color = '🟢'  # Always completed for analysis_results
            
            with st.expander(f"{status_color} **{timestamp.strftime('%Y-%m-%d %H:%M')}** - {status.title()}", expanded=False):
                # Main info columns
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.markdown("**📊 Analysis Info**")
                    st.write(f"**Status:** {status.title()}")
                    st.write(f"**Report Type:** Step-by-Step Analysis")
                    st.write(f"**Created:** {timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
                
                with col2:
                    st.markdown("**📋 Data Summary**")
                    # Get sample counts from raw_data structure
                    raw_data = analysis_data.get('raw_data', {})
                    soil_data = raw_data.get('soil_data', {})
                    leaf_data = raw_data.get('leaf_data', {})
                    
                    soil_samples = 0
                    leaf_samples = 0
                    

                    
                    if soil_data and soil_data.get('success'):
                        # Try different possible data structures
                        soil_samples_data = soil_data.get('data', {})
                        if isinstance(soil_samples_data, dict):
                            soil_samples = len(soil_samples_data.get('samples', []))
                        elif isinstance(soil_samples_data, list):
                            soil_samples = len(soil_samples_data)
                        else:
                            # If no samples array, count the number of parameters
                            soil_samples = len([k for k in soil_data.keys() if k not in ['success', 'data', 'metadata']])
                    
                    if leaf_data and leaf_data.get('success'):
                        # Try different possible data structures
                        leaf_samples_data = leaf_data.get('data', {})
                        if isinstance(leaf_samples_data, dict):
                            leaf_samples = len(leaf_samples_data.get('samples', []))
                        elif isinstance(leaf_samples_data, list):
                            leaf_samples = len(leaf_samples_data)
                        else:
                            # If no samples array, count the number of parameters
                            leaf_samples = len([k for k in leaf_data.keys() if k not in ['success', 'data', 'metadata']])
                    
                    st.write(f"**Soil Samples:** {soil_samples}")
                    st.write(f"**Leaf Samples:** {leaf_samples}")
                    
                    # Land/Yield data from raw_data
                    land_yield = raw_data.get('land_yield_data', {})
                    if land_yield:
                        st.write(f"**Land Size:** {land_yield.get('land_size', 'N/A')} {land_yield.get('land_unit', 'hectares')}")
                        st.write(f"**Current Yield:** {land_yield.get('current_yield', 'N/A')} {land_yield.get('yield_unit', 'tonnes/ha')}")
                    else:
                        st.write("**Land/Yield Data:** Not available")
                
                with col3:
                    st.markdown("**📈 Analysis Results**")
                    # Get step-by-step analysis count
                    step_analysis = analysis_data.get('step_by_step_analysis', [])
                    st.write(f"**Analysis Steps:** {len(step_analysis)}")
                    
                    # Get key metrics from analysis_metadata
                    analysis_metadata = analysis_data.get('analysis_metadata', {})
                    if analysis_metadata:
                        st.write(f"**Analysis Type:** {analysis_metadata.get('analysis_type', 'Unknown')}")
                        
                        # Count data sources more accurately
                        data_sources_count = 0
                        raw_data = analysis_data.get('raw_data', {})
                        if raw_data.get('soil_data', {}).get('success'):
                            data_sources_count += 1
                        if raw_data.get('leaf_data', {}).get('success'):
                            data_sources_count += 1
                        if raw_data.get('land_yield_data', {}):
                            data_sources_count += 1
                        
                        st.write(f"**Data Sources:** {data_sources_count}")
                    
                    # Economic forecast info
                    economic_forecast = analysis_data.get('economic_forecast', {})
                    if economic_forecast:
                        scenarios = economic_forecast.get('scenarios', {})
                        if scenarios:
                            st.write(f"**ROI Estimate:** {scenarios.get('medium', {}).get('roi_percentage', 0):.1f}%")
                
                with col4:
                    st.markdown("**⚡ Actions**")
                    if st.button("📊 View Full Report", key=f"view_{doc.id}"):
                        # Store analysis data for results page - convert to expected format
                        st.session_state.current_analysis = {
                            'id': doc.id,
                            'analysis_results': analysis_data,  # Full analysis_results data
                            'soil_data': soil_data,
                            'leaf_data': leaf_data,
                            'land_yield_data': land_yield,
                            'timestamp': timestamp,
                            'status': status
                        }
                        st.session_state.current_page = 'results'
                        st.rerun()
                    
                    if st.button("📥 Download PDF", key=f"pdf_{doc.id}"):
                        # Generate and download PDF
                        _download_analysis_pdf(analysis_data, doc.id)
                    
                    if st.button("🗑️ Delete", key=f"delete_{doc.id}"):
                        if st.session_state.get(f"confirm_delete_{doc.id}", False):
                            _delete_analysis(doc.id)
                            st.rerun()
                        else:
                            st.session_state[f"confirm_delete_{doc.id}"] = True
                            st.warning("Click again to confirm deletion")
                
                # Show detailed summary if available
                if step_analysis and status.lower() == 'completed':
                    st.markdown("---")
                    st.markdown("**📋 Analysis Summary**")
                    
                    # Show key findings from step-by-step analysis with intelligent deduplication
                    if step_analysis:
                        key_findings = _generate_intelligent_key_findings(analysis_data, step_analysis)
                        
                        if key_findings:
                            st.markdown("**Key Findings:**")
                            for i, finding_data in enumerate(key_findings[:5], 1):  # Show top 5
                                finding = finding_data['finding'] if isinstance(finding_data, dict) else finding_data
                                st.write(f"{i}. {finding}")
                    
                    # Show economic forecast summary
                    if economic_forecast:
                        scenarios = economic_forecast.get('scenarios', {})
                        if scenarios:
                            st.markdown("**Economic Forecast:**")
                            for level, data in scenarios.items():
                                if isinstance(data, dict):
                                    st.write(f"• **{level.title()} Investment:** ROI {data.get('roi_percentage', 0):.1f}%, Payback {data.get('payback_months', 0):.1f} months")
        
    except Exception as e:
        st.error(f"Error loading history: {str(e)}")
        st.exception(e)

def _clean_finding_text(text):
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

def _group_findings_by_parameter(step_findings):
    """Group findings by parameter to avoid duplicates and create comprehensive findings"""
    parameter_groups = {
        'soil_ph': {
            'keywords': ['ph', 'acidity', 'alkaline', 'acidic', 'soil ph', 'ph level', 'ph value', 'ph is'],
            'findings': [],
            'parameter_name': 'Soil pH'
        },
        'soil_nitrogen': {
            'keywords': ['nitrogen', 'n%', 'n %', 'nitrogen %', 'soil nitrogen', 'nitrogen level'],
            'findings': [],
            'parameter_name': 'Soil Nitrogen'
        },
        'soil_phosphorus': {
            'keywords': ['phosphorus', 'p%', 'p %', 'phosphorus %', 'available p', 'soil phosphorus', 'phosphorus level', 'phosphorus is', 'mg/kg'],
            'findings': [],
            'parameter_name': 'Soil Phosphorus'
        },
        'soil_potassium': {
            'keywords': ['potassium', 'k%', 'k %', 'potassium %', 'exchangeable k', 'soil potassium', 'potassium level'],
            'findings': [],
            'parameter_name': 'Soil Potassium'
        },
        'leaf_nitrogen': {
            'keywords': ['leaf nitrogen', 'leaf n', 'leaf n%', 'leaf n %', 'foliar nitrogen'],
            'findings': [],
            'parameter_name': 'Leaf Nitrogen'
        },
        'leaf_phosphorus': {
            'keywords': ['leaf phosphorus', 'leaf p', 'leaf p%', 'leaf p %', 'foliar phosphorus'],
            'findings': [],
            'parameter_name': 'Leaf Phosphorus'
        },
        'leaf_potassium': {
            'keywords': ['leaf potassium', 'leaf k', 'leaf k%', 'leaf k %', 'foliar potassium'],
            'findings': [],
            'parameter_name': 'Leaf Potassium'
        },
        'leaf_magnesium': {
            'keywords': ['leaf magnesium', 'leaf mg', 'leaf mg%', 'leaf mg %', 'foliar magnesium'],
            'findings': [],
            'parameter_name': 'Leaf Magnesium'
        },
        'leaf_calcium': {
            'keywords': ['leaf calcium', 'leaf ca', 'leaf ca%', 'leaf ca %', 'foliar calcium'],
            'findings': [],
            'parameter_name': 'Leaf Calcium'
        },
        'leaf_boron': {
            'keywords': ['leaf boron', 'leaf b', 'leaf b mg/kg', 'foliar boron'],
            'findings': [],
            'parameter_name': 'Leaf Boron'
        },
        'general': {
            'keywords': [],
            'findings': [],
            'parameter_name': 'General Analysis'
        }
    }
    
    # Group findings by parameter
    for finding_data in step_findings:
        finding = finding_data['finding'].lower()
        assigned = False
        
        for param_key, param_info in parameter_groups.items():
            if param_key == 'general':
                continue
                
            for keyword in param_info['keywords']:
                if keyword in finding:
                    param_info['findings'].append(finding_data)
                    assigned = True
                    break
            
            if assigned:
                break
        
        # If no specific parameter found, add to general
        if not assigned:
            parameter_groups['general']['findings'].append(finding_data)
    
    # Create consolidated findings for each parameter group
    consolidated_findings = []
    
    for param_key, param_info in parameter_groups.items():
        if not param_info['findings']:
            continue
            
        if param_key == 'general':
            # For general findings, keep them separate
            for finding_data in param_info['findings']:
                consolidated_findings.append(finding_data)
        else:
            # For parameter-specific findings, consolidate them
            if len(param_info['findings']) == 1:
                # Single finding - keep as is
                consolidated_findings.append(param_info['findings'][0])
            else:
                # Multiple findings - consolidate into one comprehensive finding
                main_finding = param_info['findings'][0]['finding']
                additional_details = []
                
                for finding_data in param_info['findings'][1:]:
                    finding_text = finding_data['finding']
                    # Extract additional details that aren't already covered
                    if finding_text.lower() != main_finding.lower():
                        additional_details.append(finding_text)
                
                # Create consolidated finding by intelligently merging all findings for this parameter
                all_findings_text = [f['finding'] for f in param_info['findings']]
                
                # Use the most comprehensive finding as base, then add unique details from others
                consolidated_finding = main_finding
                
                # Add unique details from other findings that aren't already covered
                for finding_text in additional_details:
                    # Check if this finding adds new information
                    if not any(phrase in consolidated_finding.lower() for phrase in finding_text.lower().split()[:3]):
                        # Add only the most important new information
                        key_phrases = finding_text.split('.')
                        if key_phrases:
                            consolidated_finding += f" {key_phrases[0].strip()}."
                
                consolidated_findings.append({
                    'finding': consolidated_finding
                })
    
    return consolidated_findings

def _generate_intelligent_key_findings(analysis_data, step_results):
    """Generate intelligent key findings with proper deduplication from all analysis sources - History page version"""
    all_key_findings = []
    
    # 1. Check for key findings at the top level of analysis_data
    if 'key_findings' in analysis_data and analysis_data['key_findings']:
        findings_data = analysis_data['key_findings']
        
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
                cleaned_finding = _clean_finding_text(finding.strip())
                all_key_findings.append({
                    'finding': cleaned_finding
                })
    
    # 2. Extract key findings from step-by-step analysis with intelligent processing
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
                            'improvement', 'increase', 'decrease', 'balance', 'ratio', 'level', 'status'
                        ]
                        
                        # Check if finding contains relevant keywords
                        if any(keyword in finding_lower for keyword in relevant_keywords):
                            cleaned_finding = _clean_finding_text(finding.strip())
                            if cleaned_finding and len(cleaned_finding) > 20:  # Minimum length filter
                                step_findings.append({
                                    'finding': cleaned_finding
                                })
        
        # Apply intelligent deduplication to step findings with parameter-based grouping
        if step_findings:
            unique_findings = _group_findings_by_parameter(step_findings)
            all_key_findings.extend(unique_findings)
    
    # 3. Generate comprehensive parameter-specific key findings
    comprehensive_findings = _generate_comprehensive_parameter_findings(analysis_data, step_results)
    all_key_findings.extend(comprehensive_findings)
    
    # 4. Extract key findings from other analysis sources
    # Land and yield data
    land_yield_data = analysis_data.get('land_yield_data', {})
    if land_yield_data:
        land_size = land_yield_data.get('land_size', 0)
        current_yield = land_yield_data.get('current_yield', 0)
        land_unit = land_yield_data.get('land_unit', 'hectares')
        yield_unit = land_yield_data.get('yield_unit', 'tonnes/hectare')
        
        if land_size > 0:
            all_key_findings.append({
                'finding': f"Farm analysis covers {land_size} {land_unit} of agricultural land with current production of {current_yield} {yield_unit}."
            })
    
    # Economic forecast
    economic_forecast = analysis_data.get('economic_forecast', {})
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
                    'finding': f"Economic analysis shows {best_scenario} investment level offers the best ROI of {best_roi:.1f}% with {scenarios[best_scenario].get('payback_months', 0):.1f} months payback period."
                })
    
    # Yield forecast
    yield_forecast = analysis_data.get('yield_forecast', {})
    if yield_forecast:
        projected_yield = yield_forecast.get('projected_yield', 0)
        current_yield = yield_forecast.get('current_yield', 0)
        if projected_yield > 0 and current_yield > 0:
            increase = ((projected_yield - current_yield) / current_yield) * 100
            all_key_findings.append({
                'finding': f"Yield projection indicates potential increase from {current_yield} to {projected_yield} tonnes/hectare ({increase:.1f}% improvement) with proper management."
            })
    
    return all_key_findings

def _generate_comprehensive_parameter_findings(analysis_data, step_results):
    """Generate comprehensive key findings grouped by specific parameters - History page version"""
    findings = []
    
    # Get raw data for analysis
    raw_data = analysis_data.get('raw_data', {})
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
                    'finding': f"Soil pH is critically low at {ph_value:.1f}, significantly below optimal range of 5.5-7.0. This acidic condition severely limits nutrient availability and root development."
                })
            elif ph_value > 7.5:
                findings.append({
                    'finding': f"Soil pH is high at {ph_value:.1f}, above optimal range of 5.5-7.0. This alkaline condition reduces availability of essential micronutrients like iron and zinc."
                })
            else:
                findings.append({
                    'finding': f"Soil pH is within optimal range at {ph_value:.1f}, providing good conditions for nutrient availability and root development."
                })
    
    # 2. Soil Nitrogen Analysis
    if 'Nitrogen_%' in soil_params and mpob:
        n_value = soil_params['Nitrogen_%'].get('average', 0)
        n_optimal = mpob.get('soil', {}).get('nitrogen', {}).get('optimal', 0.2)
        
        if n_value > 0:
            if n_value < n_optimal * 0.7:
                findings.append({
                    'finding': f"Soil nitrogen is critically deficient at {n_value:.2f}%, well below optimal level of {n_optimal:.2f}%. This severely limits plant growth and leaf development."
                })
            elif n_value > n_optimal * 1.3:
                findings.append({
                    'finding': f"Soil nitrogen is excessive at {n_value:.2f}%, above optimal level of {n_optimal:.2f}%. This may cause nutrient imbalances and environmental concerns."
                })
            else:
                findings.append({
                    'finding': f"Soil nitrogen is adequate at {n_value:.2f}%, within optimal range for healthy plant growth."
                })
    
    # 3. Soil Phosphorus Analysis
    if 'Available_P_mg_kg' in soil_params and mpob:
        p_value = soil_params['Available_P_mg_kg'].get('average', 0)
        p_optimal = mpob.get('soil', {}).get('available_phosphorus', {}).get('optimal', 15)
        
        if p_value > 0:
            if p_value < p_optimal * 0.5:
                findings.append({
                    'finding': f"Available phosphorus is critically low at {p_value:.1f} mg/kg, severely below optimal level of {p_optimal} mg/kg. This limits root development and energy transfer."
                })
            elif p_value > p_optimal * 2:
                findings.append({
                    'finding': f"Available phosphorus is excessive at {p_value:.1f} mg/kg, well above optimal level of {p_optimal} mg/kg. This may cause nutrient lockup and environmental issues."
                })
            else:
                findings.append({
                    'finding': f"Available phosphorus is adequate at {p_value:.1f} mg/kg, within optimal range for proper plant development."
                })
    
    # 4. Soil Potassium Analysis
    if 'Exchangeable_K_meq%' in soil_params and mpob:
        k_value = soil_params['Exchangeable_K_meq%'].get('average', 0)
        k_optimal = mpob.get('soil', {}).get('exchangeable_potassium', {}).get('optimal', 0.3)
        
        if k_value > 0:
            if k_value < k_optimal * 0.6:
                findings.append({
                    'finding': f"Exchangeable potassium is deficient at {k_value:.2f} meq%, below optimal level of {k_optimal:.2f} meq%. This affects water regulation and disease resistance."
                })
            elif k_value > k_optimal * 1.5:
                findings.append({
                    'finding': f"Exchangeable potassium is high at {k_value:.2f} meq%, above optimal level of {k_optimal:.2f} meq%. This may cause nutrient imbalances."
                })
            else:
                findings.append({
                    'finding': f"Exchangeable potassium is adequate at {k_value:.2f} meq%, within optimal range for healthy plant function."
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
                    })
                elif leaf_n > 3.5:
                    findings.append({
                        'finding': f"Leaf nitrogen is excessive at {leaf_n:.1f}%, above optimal range of 2.5-3.5%. This may cause nutrient imbalances and delayed maturity.",
                    })
                else:
                    findings.append({
                        'finding': f"Leaf nitrogen is optimal at {leaf_n:.1f}%, within recommended range for healthy palm growth.",
                    })
        
        # Leaf Phosphorus
        if 'P_%' in leaf_params:
            leaf_p = leaf_params['P_%'].get('average', 0)
            if leaf_p > 0:
                if leaf_p < 0.15:
                    findings.append({
                        'finding': f"Leaf phosphorus is deficient at {leaf_p:.2f}%, below optimal range of 0.15-0.25%. This limits energy transfer and root development.",
                    })
                elif leaf_p > 0.25:
                    findings.append({
                        'finding': f"Leaf phosphorus is high at {leaf_p:.2f}%, above optimal range of 0.15-0.25%. This may indicate over-fertilization.",
                    })
                else:
                    findings.append({
                        'finding': f"Leaf phosphorus is adequate at {leaf_p:.2f}%, within optimal range for proper plant function.",
                    })
        
        # Leaf Potassium
        if 'K_%' in leaf_params:
            leaf_k = leaf_params['K_%'].get('average', 0)
            if leaf_k > 0:
                if leaf_k < 1.0:
                    findings.append({
                        'finding': f"Leaf potassium is deficient at {leaf_k:.1f}%, below optimal range of 1.0-1.5%. This affects water regulation and disease resistance.",
                    })
                elif leaf_k > 1.5:
                    findings.append({
                        'finding': f"Leaf potassium is high at {leaf_k:.1f}%, above optimal range of 1.0-1.5%. This may cause nutrient imbalances.",
                    })
                else:
                    findings.append({
                        'finding': f"Leaf potassium is optimal at {leaf_k:.1f}%, within recommended range for healthy palm growth.",
                    })
        
        # Leaf Magnesium
        if 'Mg_%' in leaf_params:
            leaf_mg = leaf_params['Mg_%'].get('average', 0)
            if leaf_mg > 0:
                if leaf_mg < 0.2:
                    findings.append({
                        'finding': f"Leaf magnesium is deficient at {leaf_mg:.2f}%, below optimal range of 0.2-0.3%. This affects chlorophyll production and photosynthesis.",
                    })
                elif leaf_mg > 0.3:
                    findings.append({
                        'finding': f"Leaf magnesium is high at {leaf_mg:.2f}%, above optimal range of 0.2-0.3%. This may indicate over-fertilization.",
                    })
                else:
                    findings.append({
                        'finding': f"Leaf magnesium is adequate at {leaf_mg:.2f}%, within optimal range for healthy palm growth.",
                    })
        
        # Leaf Calcium
        if 'Ca_%' in leaf_params:
            leaf_ca = leaf_params['Ca_%'].get('average', 0)
            if leaf_ca > 0:
                if leaf_ca < 0.5:
                    findings.append({
                        'finding': f"Leaf calcium is deficient at {leaf_ca:.1f}%, below optimal range of 0.5-1.0%. This affects cell wall strength and fruit quality.",
                    })
                elif leaf_ca > 1.0:
                    findings.append({
                        'finding': f"Leaf calcium is high at {leaf_ca:.1f}%, above optimal range of 0.5-1.0%. This may cause nutrient imbalances.",
                    })
                else:
                    findings.append({
                        'finding': f"Leaf calcium is optimal at {leaf_ca:.1f}%, within recommended range for healthy palm growth.",
                    })
        
        # Leaf Boron
        if 'B_mg_kg' in leaf_params:
            leaf_b = leaf_params['B_mg_kg'].get('average', 0)
            if leaf_b > 0:
                if leaf_b < 10:
                    findings.append({
                        'finding': f"Leaf boron is deficient at {leaf_b:.1f} mg/kg, below optimal range of 10-20 mg/kg. This affects fruit development and pollen viability.",
                    })
                elif leaf_b > 20:
                    findings.append({
                        'finding': f"Leaf boron is high at {leaf_b:.1f} mg/kg, above optimal range of 10-20 mg/kg. This may cause toxicity symptoms.",
                    })
                else:
                    findings.append({
                        'finding': f"Leaf boron is adequate at {leaf_b:.1f} mg/kg, within optimal range for healthy palm growth.",
                    })
    
    return findings

def _search_in_analysis_content(analysis_data: dict, search_term: str) -> bool:
    """Search for term in analysis content"""
    try:
        # Search in step-by-step analysis
        step_analysis = analysis_data.get('step_by_step_analysis', [])
        for step in step_analysis:
            if 'summary' in step and search_term in step['summary'].lower():
                return True
            if 'key_findings' in step:
                for finding in step['key_findings']:
                    if search_term in finding.lower():
                        return True
            if 'formatted_analysis' in step and search_term in step['formatted_analysis'].lower():
                return True
        
        # Search in economic forecast
        economic_forecast = analysis_data.get('economic_forecast', {})
        if economic_forecast:
            scenarios = economic_forecast.get('scenarios', {})
            for level, data in scenarios.items():
                if isinstance(data, dict) and search_term in level.lower():
                    return True
        
        # Search in raw data (land/yield data)
        raw_data = analysis_data.get('raw_data', {})
        land_yield = raw_data.get('land_yield_data', {})
        if land_yield:
            for key, value in land_yield.items():
                if isinstance(value, str) and search_term in value.lower():
                    return True
        
        # Search in analysis metadata
        analysis_metadata = analysis_data.get('analysis_metadata', {})
        if analysis_metadata:
            for key, value in analysis_metadata.items():
                if isinstance(value, str) and search_term in value.lower():
                    return True
                elif isinstance(value, list):
                    for item in value:
                        if isinstance(item, str) and search_term in item.lower():
                            return True
        
        return False
    except Exception:
        return False

def _download_analysis_pdf(analysis_data: dict, analysis_id: str):
    """Download analysis as PDF"""
    try:
        from utils.pdf_utils import PDFReportGenerator
        
        # Generate PDF
        pdf_generator = PDFReportGenerator()
        
        if not analysis_data:
            st.error("No analysis data available for PDF generation")
            return
        
        # Prepare metadata
        metadata = {
            'report_type': 'historical',
            'lab_number': f'HIST-{analysis_id[:8]}',
            'sample_date': analysis_data.get('created_at', datetime.now()).strftime('%Y-%m-%d'),
            'farm_name': 'Historical Analysis'
        }
        
        # Generate PDF
        options = {
            'include_charts': True,
            'include_economic': True,
            'include_forecast': True
        }
        
        pdf_buffer = pdf_generator.generate_report(analysis_data, metadata, options)
        
        # Create download button
        timestamp = analysis_data.get('created_at', datetime.now()).strftime("%Y%m%d_%H%M%S")
        filename = f"historical_analysis_{timestamp}.pdf"
        
        st.download_button(
            label="💾 Download PDF Report",
            data=pdf_buffer,
            file_name=filename,
            mime="application/pdf"
        )
        
    except Exception as e:
        st.error(f"Error generating PDF: {str(e)}")

def _delete_analysis(analysis_id: str):
    """Delete analysis from database"""
    try:
        db = get_firestore_client()
        if not db:
            st.error("Database connection failed")
            return
        
        # Delete the analysis document from analysis_results collection
        db.collection('analysis_results').document(analysis_id).delete()
        
        # Clear confirmation state
        if f"confirm_delete_{analysis_id}" in st.session_state:
            del st.session_state[f"confirm_delete_{analysis_id}"]
        
        st.success("Analysis deleted successfully!")
        
    except Exception as e:
        st.error(f"Error deleting analysis: {str(e)}")

def main():
    """Wrapper function for backward compatibility"""
    show_history_page()

if __name__ == "__main__":
    main()
