import streamlit as st
import sys
import os
from datetime import datetime
import pandas as pd
from google.cloud import firestore

# Add utils to path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'utils'))

# Import utilities
from utils.firebase_config import get_firestore_client, COLLECTIONS

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
        query = analyses_ref.where('user_id', '==', user_id).order_by('created_at', direction=firestore.Query.DESCENDING).limit(limit)
        
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
                    
                    # Show key findings from step-by-step analysis
                    if step_analysis:
                        key_findings = []
                        for step in step_analysis:
                            if 'key_findings' in step and step['key_findings']:
                                key_findings.extend(step['key_findings'][:2])  # Limit to 2 per step
                        
                        if key_findings:
                            st.markdown("**Key Findings:**")
                            for i, finding in enumerate(key_findings[:5], 1):  # Show top 5
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
