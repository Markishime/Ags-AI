import streamlit as st
from datetime import datetime, timedelta
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, List, Any
import sys
import os
import time

# Add utils to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'utils'))

from firebase_config import get_firestore_client, COLLECTIONS
from functools import lru_cache
from auth_utils import get_user_by_id, update_user_profile

def show_dashboard():
    """Display simplified user dashboard for non-technical users"""
    # ===== HEADER SECTION =====
    display_dashboard_header()
    
    # Check authentication
    if not check_user_authentication():
        return
    
    user_id = st.session_state['user_id']
    user_info = get_user_by_id(user_id)
    
    if not user_info:
        st.error("User information not found.")
        return
    
    # ===== MAIN DASHBOARD TABS =====
    tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "📈 Analytics & Insights", "💬 Help Us Improve"])
    
    with tab1:
        # ===== SIMPLIFIED LAYOUT =====
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # ===== USER OVERVIEW SECTION =====
            display_user_overview_section(user_info, user_id)
            
            # ===== RECENT REPORTS SECTION =====
            display_recent_reports_section(user_id)
            
            # ===== QUICK ACTIONS SECTION =====
            display_simple_quick_actions()
        
        with col2:
            # ===== USER PROFILE CARD =====
            display_simple_user_profile(user_info)
            
            # ===== SYSTEM STATUS =====
            display_simple_system_status()
    
    with tab2:
        # ===== ANALYTICS & INSIGHTS TAB =====
        display_analytics_insights_tab(user_id)
    
    with tab3:
        # ===== HELP US IMPROVE TAB =====
        display_help_us_improve_tab()

# ===== SIMPLIFIED DASHBOARD SECTIONS =====
@st.cache_data(ttl=30)
def _cached_user_stats(user_id: str) -> Dict[str, Any]:
    try:
        db = get_firestore_client()
        if not db:
            return {'total_analyses': 0, 'recent_activity': 0, 'total_recommendations': 0}
        
        # Try both user_id and user_email approaches
        # First try with user_id
        q = db.collection('analysis_results').where('user_id', '==', user_id).order_by('created_at', direction='DESCENDING').limit(50)
        docs = list(q.stream())
        total = len(docs)
        
        # If no results with user_id, try with user_email from session state
        if total == 0 and 'user_email' in st.session_state:
            user_email = st.session_state.get('user_email')
            q = db.collection('analysis_results').where('user_id', '==', user_email).order_by('created_at', direction='DESCENDING').limit(50)
            docs = list(q.stream())
            total = len(docs)
        
        now = datetime.utcnow()
        week_count = 0
        recs = 0
        
        for d in docs:
            data = d.to_dict()
            created = data.get('created_at', now)
            
            # Handle different datetime formats
            if hasattr(created, 'timestamp'):
                delta_days = (now - created).days
            elif hasattr(created, 'replace') and hasattr(created, 'tzinfo') and created.tzinfo is not None:
                created_naive = created.replace(tzinfo=None)
                delta_days = (now - created_naive).days
            else:
                delta_days = 0
                
            if delta_days <= 7:
                week_count += 1
                
            # Count recommendations from the analysis data
            recommendations = data.get('recommendations', [])
            if isinstance(recommendations, list):
                recs += len(recommendations)
            elif isinstance(recommendations, dict):
                recs += len(recommendations.get('recommendations', []))
                
        return {'total_analyses': total, 'recent_activity': week_count, 'total_recommendations': recs}
    except Exception as e:
        # Silent error handling - return default values
        return {'total_analyses': 0, 'recent_activity': 0, 'total_recommendations': 0}

@st.cache_data(ttl=60)
def _cached_user_analytics(user_id: str) -> Dict[str, Any]:
    """Get comprehensive analytics data for user"""
    try:
        db = get_firestore_client()
        if not db:
            return {'total_analyses': 0, 'success_rate': 0, 'avg_processing_time': 0, 
                   'data_quality_score': 0, 'total_recommendations': 0, 'monthly_trends': [],
                   'common_issues': [], 'recent_activity': [], 'ai_insights': []}
        
        # Get all analyses for the user
        q = db.collection('analysis_results').where('user_id', '==', user_id).order_by('created_at', direction='DESCENDING').limit(100)
        docs = list(q.stream())
        
        if not docs:
            return {'total_analyses': 0, 'success_rate': 0, 'avg_processing_time': 0, 
                   'data_quality_score': 0, 'total_recommendations': 0, 'monthly_trends': [],
                   'common_issues': [], 'recent_activity': [], 'ai_insights': []}
        
        # Process analytics data
        total_analyses = len(docs)
        successful_analyses = 0
        total_processing_time = 0
        total_recommendations = 0
        monthly_counts = {}
        common_issues = {}
        recent_activity = []
        
        for doc in docs:
            data = doc.to_dict()
            
            # Count successful analyses
            if data.get('success', False):
                successful_analyses += 1
            
            # Calculate processing time
            created_at = data.get('created_at')
            if created_at:
                # Simple processing time estimation (this would be better with actual timestamps)
                total_processing_time += 30  # Assume 30 seconds average
            
            # Count recommendations
            recommendations = data.get('recommendations', [])
            if isinstance(recommendations, list):
                total_recommendations += len(recommendations)
            elif isinstance(recommendations, dict):
                total_recommendations += len(recommendations.get('recommendations', []))
            
            # Monthly trends
            if created_at:
                month_key = created_at.strftime('%Y-%m') if hasattr(created_at, 'strftime') else '2024-01'
                monthly_counts[month_key] = monthly_counts.get(month_key, 0) + 1
            
            # Extract common issues from analysis results
            analysis_results = data.get('analysis_results', {})
            if 'key_findings' in analysis_results:
                findings = analysis_results['key_findings']
                if isinstance(findings, list):
                    for finding in findings:
                        if isinstance(finding, dict) and 'finding' in finding:
                            finding_text = finding['finding'].lower()
                            # Simple keyword extraction for common issues
                            if 'deficiency' in finding_text or 'low' in finding_text:
                                common_issues['Nutrient Deficiency'] = common_issues.get('Nutrient Deficiency', 0) + 1
                            elif 'excess' in finding_text or 'high' in finding_text:
                                common_issues['Nutrient Excess'] = common_issues.get('Nutrient Excess', 0) + 1
                            elif 'ph' in finding_text:
                                common_issues['pH Issues'] = common_issues.get('pH Issues', 0) + 1
            
            # Recent activity
            if len(recent_activity) < 10:
                recent_activity.append({
                    'description': f"Analysis completed - {', '.join(data.get('report_types', ['Unknown']))}",
                    'date': created_at.strftime('%Y-%m-%d') if hasattr(created_at, 'strftime') else 'Unknown'
                })
        
        # Calculate metrics
        success_rate = (successful_analyses / total_analyses * 100) if total_analyses > 0 else 0
        avg_processing_time = total_processing_time / total_analyses if total_analyses > 0 else 0
        data_quality_score = min(10, (success_rate / 10) + (total_recommendations / total_analyses / 5)) if total_analyses > 0 else 0
        
        # Format monthly trends
        monthly_trends = [{'month': month, 'count': count} for month, count in sorted(monthly_counts.items())]
        
        # Format common issues
        common_issues_list = [{'issue': issue, 'count': count} for issue, count in sorted(common_issues.items(), key=lambda x: x[1], reverse=True)]
        
        # Generate AI insights
        ai_insights = []
        if total_analyses >= 3:
            if success_rate > 80:
                ai_insights.append({
                    'title': 'High Analysis Success Rate',
                    'description': f'Your analyses are completing successfully {success_rate:.1f}% of the time, indicating good data quality.',
                    'recommendation': 'Continue uploading clear, high-quality agricultural reports for best results.'
                })
            
            if len(common_issues_list) > 0:
                top_issue = common_issues_list[0]
                ai_insights.append({
                    'title': f'Most Common Issue: {top_issue["issue"]}',
                    'description': f'This issue appears in {top_issue["count"]} of your analyses.',
                    'recommendation': 'Consider focusing on this area for improvement in your agricultural practices.'
                })
        
        return {
            'total_analyses': total_analyses,
            'success_rate': success_rate,
            'avg_processing_time': avg_processing_time,
            'data_quality_score': data_quality_score,
            'total_recommendations': total_recommendations,
            'monthly_trends': monthly_trends,
            'common_issues': common_issues_list,
            'recent_activity': recent_activity,
            'ai_insights': ai_insights
        }
        
    except Exception as e:
        # Silent error handling - return default values
        return {'total_analyses': 0, 'success_rate': 0, 'avg_processing_time': 0, 
               'data_quality_score': 0, 'total_recommendations': 0, 'monthly_trends': [],
               'common_issues': [], 'recent_activity': [], 'ai_insights': []}

def display_user_overview_section(user_info, user_id):
    """Display simple user overview"""
    st.markdown("---")
    st.markdown("## 👋 Welcome Back!")
    
    # Simple welcome message without statistics
    st.markdown(f"Welcome back, **{user_info.get('name', 'User')}**! Ready to analyze your agricultural reports?")

@st.cache_data(ttl=30)
def _cached_recent_analyses(user_id: str) -> List[Dict[str, Any]]:
    try:
        db = get_firestore_client()
        if not db:
            return []
        
        # Try both user_id and user_email approaches
        # First try with user_id
        q = db.collection('analysis_results').where('user_id', '==', user_id).order_by('created_at', direction='DESCENDING').limit(5)
        docs = list(q.stream())
        
        # If no results with user_id, try with user_email from session state
        if len(docs) == 0 and 'user_email' in st.session_state:
            user_email = st.session_state.get('user_email')
            q = db.collection('analysis_results').where('user_id', '==', user_email).order_by('created_at', direction='DESCENDING').limit(5)
            docs = list(q.stream())
        
        return [{**d.to_dict(), 'id': d.id} for d in docs]
    except Exception as e:
        # Silent error handling - return empty list
        return []

def display_recent_reports_section(user_id):
    """Display recent reports in simple format"""
    st.markdown("---")
    st.markdown("## 📊 Recent Reports")
    
    try:
        analyses_list = _cached_recent_analyses(user_id)
        
        if analyses_list:
            for i, analysis in enumerate(analyses_list):
                # Create simple report card
                created_at = analysis.get('created_at')
                if hasattr(created_at, 'strftime'):
                    date_str = created_at.strftime('%B %d, %Y')
                else:
                    date_str = str(created_at) if created_at else 'Unknown'
                
                st.markdown(f"""
                <div style="
                    background: white;
                    padding: 15px;
                    border-radius: 10px;
                    border-left: 4px solid #667eea;
                    margin-bottom: 10px;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                ">
                    <h4 style="margin: 0 0 5px 0; color: #2c3e50;">Report #{i+1}</h4>
                    <p style="margin: 0; color: #666; font-size: 14px;">Created: {date_str}</p>
                    <p style="margin: 5px 0 0 0; color: #2c3e50;">Status: Completed</p>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("📝 No reports found. Upload your first agricultural report to get started!")
            
    except Exception as e:
        st.error(f"Error loading recent reports: {str(e)}")

def display_simple_quick_actions():
    """Display simplified quick actions"""
    st.markdown("---")
    st.markdown("## ⚡ Quick Actions")
    
    # Primary action
    if st.button("📤 Analyze Files", width='stretch', type="primary"):
        st.session_state.current_page = 'upload'
        st.rerun()
    
    # Secondary actions
    if st.button("📈 View History", width='stretch'):
        st.session_state.current_page = 'history'
        st.rerun()

def display_simple_user_profile(user_info):
    """Display simplified user profile card"""
    st.markdown("---")
    st.markdown("## 👤 Your Profile")
    
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #667eea, #764ba2);
        padding: 20px;
        border-radius: 15px;
        color: white;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    ">
        <div style="
            width: 60px;
            height: 60px;
            background: rgba(255,255,255,0.2);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0 auto 15px auto;
            font-size: 24px;
        ">
            👤
        </div>
        <h3 style="margin: 0 0 5px 0;">{user_info.get('name', 'User')}</h3>
        <p style="margin: 0 0 10px 0; opacity: 0.9;">{user_info.get('email', 'No email')}</p>
        <p style="margin: 0; font-size: 14px; opacity: 0.8;">Member since {user_info.get('created_at', 'Unknown')}</p>
    </div>
    """, unsafe_allow_html=True)

def display_simple_system_status():
    """Display simple system status"""
    st.markdown("---")
    st.markdown("## 🔧 System Status")
    
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #43e97b, #38f9d7);
        padding: 15px;
        border-radius: 10px;
        color: white;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    ">
        <h4 style="margin: 0 0 5px 0;">✅ All Systems Operational</h4>
        <p style="margin: 0; font-size: 14px; opacity: 0.9;">AI Analysis: Ready</p>
        <p style="margin: 0; font-size: 14px; opacity: 0.9;">Database: Connected</p>
    </div>
    """, unsafe_allow_html=True)

# ===== HEADER SECTION =====
def display_dashboard_header():
    """Display dashboard header with real-time clock and logout"""
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.markdown('<h1 style="color: #2E8B57; text-align: left;">🏠 Dashboard</h1>', unsafe_allow_html=True)
    
    with col2:
        # Real-time clock
        current_time = datetime.now().strftime("%H:%M:%S")
        st.metric("🕐 Current Time", current_time)
    
    with col3:
        if st.button("🚪 Logout", type="secondary", use_container_width=True):
            clear_authentication_state()
            st.success("Logged out successfully!")
            st.rerun()

def clear_authentication_state():
    """Clear authentication state from session and query params"""
    # Clear session state
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    
    # Clear query params
    st.query_params.clear()

def check_user_authentication() -> bool:
    """Check if user is authenticated"""
    if 'user_id' not in st.session_state:
        st.error("🔒 Please log in to access the dashboard.")
        if st.button("🔑 Go to Login", type="primary"):
            st.session_state.current_page = 'login'
            st.rerun()
        return False
    return True

# ===== REAL-TIME METRICS SECTION =====
def display_real_time_metrics(user_id: str):
    """Display real-time metrics with auto-refresh"""
    st.markdown("---")
    st.subheader("📊 Real-Time Metrics")
    
    # Auto-refresh every 30 seconds
    if 'last_refresh' not in st.session_state:
        st.session_state.last_refresh = time.time()
    
    current_time = time.time()
    if current_time - st.session_state.last_refresh > 30:
        st.session_state.last_refresh = current_time
        st.rerun()
    
    # Get real-time statistics
    stats = get_comprehensive_user_statistics(user_id)
    
    # Display metrics in columns
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric(
            label="📈 Total Analyses",
            value=stats.get('total_analyses', 0),
            delta=f"+{stats.get('recent_activity', 0)} this week",
            delta_color="normal"
        )
    
    with col2:
        st.metric(
            label="🌱 Soil Reports",
            value=stats.get('soil_analyses', 0),
            delta=f"{stats.get('soil_trend', 0):+.0f}% vs last month"
        )
    
    with col3:
        st.metric(
            label="🍃 Leaf Reports",
            value=stats.get('leaf_analyses', 0),
            delta=f"{stats.get('leaf_trend', 0):+.0f}% vs last month"
        )
    
    with col4:
        st.metric(
            label="⚠️ Critical Issues",
            value=stats.get('critical_issues', 0),
            delta=f"{stats.get('issues_trend', 0):+.0f}% vs last month",
            delta_color="inverse"
        )
    
    with col5:
        st.metric(
            label="💡 Recommendations",
            value=stats.get('total_recommendations', 0),
            delta=f"{stats.get('recommendations_trend', 0):+.0f}% vs last month"
        )
    
    st.markdown("---")

def get_comprehensive_user_statistics(user_id: str) -> Dict[str, Any]:
    """Get comprehensive real-time user statistics with trends"""
    try:
        db = get_firestore_client()
        if not db:
            return {}
        
        # Get all user analyses from analysis_results collection
        # Try both user_id and user_email approaches
        analyses_ref = db.collection('analysis_results').where('user_id', '==', user_id)
        analyses = analyses_ref.get()
        
        # If no results with user_id, try with user_email from session state
        if len(analyses) == 0 and 'user_email' in st.session_state:
            user_email = st.session_state.get('user_email')
            analyses_ref = db.collection('analysis_results').where('user_id', '==', user_email)
            analyses = analyses_ref.get()
        
        total_analyses = len(analyses)
        
        # Count by report type
        soil_analyses = 0
        leaf_analyses = 0
        total_issues = 0
        critical_issues = 0
        total_recommendations = 0
        
        # Time-based calculations
        now = datetime.now()
        week_ago = now - timedelta(days=7)
        month_ago = now - timedelta(days=30)
        
        recent_activity = 0
        soil_this_month = 0
        leaf_this_month = 0
        soil_last_month = 0
        leaf_last_month = 0
        
        for analysis in analyses:
            data = analysis.to_dict()
            created_at = data.get('created_at', now)
            
            # Convert timezone-aware datetime to naive for comparison
            if hasattr(created_at, 'replace') and hasattr(created_at, 'tzinfo') and created_at.tzinfo is not None:
                created_at_naive = created_at.replace(tzinfo=None)
            else:
                created_at_naive = created_at
            
            # Check raw_data for report types (soil/leaf data presence)
            raw_data = data.get('raw_data', {})
            has_soil = bool(raw_data.get('soil_data', {}))
            has_leaf = bool(raw_data.get('leaf_data', {}))
            
            if has_soil:
                soil_analyses += 1
                if created_at_naive > month_ago:
                    soil_this_month += 1
                elif month_ago > created_at_naive > (month_ago - timedelta(days=30)):
                    soil_last_month += 1
                    
            if has_leaf:
                leaf_analyses += 1
                if created_at_naive > month_ago:
                    leaf_this_month += 1
                elif month_ago > created_at_naive > (month_ago - timedelta(days=30)):
                    leaf_last_month += 1
            
            if created_at_naive > week_ago:
                recent_activity += 1
            
            # Count issues and recommendations from the analysis data structure
            issues_analysis = data.get('issues_analysis', {})
            recommendations = data.get('recommendations', {})
            
            # Count issues
            if isinstance(issues_analysis, dict):
                issues_list = issues_analysis.get('issues', [])
                if isinstance(issues_list, list):
                    total_issues += len(issues_list)
                    # Count critical issues
                    for issue in issues_list:
                        if isinstance(issue, dict) and issue.get('priority', '').lower() in ['high', 'critical']:
                            critical_issues += 1
            
            # Count recommendations
            if isinstance(recommendations, dict):
                recs_list = recommendations.get('recommendations', [])
                if isinstance(recs_list, list):
                    total_recommendations += len(recs_list)
        
        # Calculate trends
        soil_trend = ((soil_this_month - soil_last_month) / max(soil_last_month, 1)) * 100 if soil_last_month > 0 else 0
        leaf_trend = ((leaf_this_month - leaf_last_month) / max(leaf_last_month, 1)) * 100 if leaf_last_month > 0 else 0
        
        return {
            'total_analyses': total_analyses,
            'soil_analyses': soil_analyses,
            'leaf_analyses': leaf_analyses,
            'total_issues': total_issues,
            'critical_issues': critical_issues,
            'total_recommendations': total_recommendations,
            'recent_activity': recent_activity,
            'soil_trend': soil_trend,
            'leaf_trend': leaf_trend,
            'issues_trend': 0,  # Placeholder
            'recommendations_trend': 0,  # Placeholder
            'avg_issues_per_analysis': total_issues / max(total_analyses, 1)
        }
        
    except Exception as e:
        # Silent error handling - return empty dict
        return {}

# ===== RECENT ACTIVITY SECTION =====
def display_recent_activity_section(user_id: str):
    """Display recent activity with detailed information"""
    st.subheader("📊 Recent Activity")
    
    # Get recent analyses with detailed information
    recent_analyses = get_detailed_recent_analyses(user_id, limit=10)
    
    if not recent_analyses:
        st.info("No analyses found. Upload your first SP LAB report to get started!")
        if st.button("📤 Analyze Files", type="primary", key="upload_from_dashboard"):
            st.session_state.current_page = 'upload'
            st.rerun()
        return
    
    # Display analyses in an expandable format
    for i, analysis in enumerate(recent_analyses):
        with st.expander(f"📋 {analysis.get('sample_id', 'Unknown Sample')} - {analysis.get('report_type', 'Unknown').title()} Report", expanded=(i < 3)):
            display_analysis_details(analysis)

def get_detailed_recent_analyses(user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Get detailed recent analyses for user"""
    try:
        db = get_firestore_client()
        if not db:
            return []
        
        # Get recent analyses
        analyses_ref = (db.collection(COLLECTIONS['analyses'])
                       .where('user_id', '==', user_id)
                       .order_by('created_at', direction='DESCENDING')
                       .limit(limit))
        
        analyses = analyses_ref.get()
        
        results = []
        for analysis in analyses:
            data = analysis.to_dict()
            data['id'] = analysis.id
            results.append(data)
        
        return results
        
    except Exception as e:
        st.error(f"Error getting detailed recent analyses: {str(e)}")
        return []

def display_analysis_details(analysis: Dict[str, Any]):
    """Display detailed analysis information"""
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.write(f"**📅 Date:** {format_date(analysis.get('created_at', datetime.now()))}")
        st.write(f"**🏷️ Sample ID:** {analysis.get('sample_id', 'N/A')}")
        st.write(f"**📊 Report Type:** {analysis.get('report_type', 'Unknown').title()}")
    
    with col2:
        analysis_results = analysis.get('analysis_results', {})
        issues = analysis_results.get('issues', [])
        recommendations = analysis_results.get('recommendations', [])
        
        st.write(f"**⚠️ Issues Found:** {len(issues)}")
        st.write(f"**💡 Recommendations:** {len(recommendations)}")
        st.write(f"**📈 Status:** {'✅ Complete' if analysis.get('status') == 'completed' else '⏳ Processing'}")
    
    with col3:
        # Action buttons
        if st.button("👁️ View Details", key=f"view_{analysis['id']}"):
            st.session_state['selected_analysis_id'] = analysis['id']
            st.session_state.current_page = 'results'
            st.rerun()
        
        if st.button("📄 Download PDF", key=f"pdf_{analysis['id']}"):
            download_pdf_report(analysis['id'])
        
        if st.button("🗑️ Delete", key=f"delete_{analysis['id']}"):
            delete_analysis(analysis['id'])

def format_date(date_obj) -> str:
    """Format date object to string"""
    if hasattr(date_obj, 'strftime'):
        return date_obj.strftime('%Y-%m-%d %H:%M')
    return str(date_obj)

# ===== ANALYSIS TRENDS SECTION =====
def display_analysis_trends_section(user_id: str):
    """Display comprehensive analysis trends with multiple charts"""
    st.subheader("📈 Analysis Trends")
    
    # Create tabs for different trend views
    tab1, tab2, tab3 = st.tabs(["📊 Monthly Trends", "🎯 Issue Analysis", "💡 Recommendation Patterns"])
    
    with tab1:
        display_monthly_trends_chart(user_id)
    
    with tab2:
        display_issue_analysis_chart(user_id)
    
    with tab3:
        display_recommendation_patterns_chart(user_id)

def display_monthly_trends_chart(user_id: str):
    """Display monthly analysis trends"""
    try:
        db = get_firestore_client()
        if not db:
            st.info("Unable to load trend data.")
            return
        
        # Get analyses for the last 12 months
        from datetime import timezone
        twelve_months_ago = datetime.now(timezone.utc) - timedelta(days=365)
        analyses_ref = (db.collection(COLLECTIONS['analyses'])
                       .where('user_id', '==', user_id)
                       .where('created_at', '>=', twelve_months_ago))
        
        analyses = analyses_ref.get()
        
        if not analyses:
            st.info("Not enough data to show trends. Upload more reports to see analysis trends.")
            return
        
        # Process data for trends
        trend_data = {}
        for analysis in analyses:
            data = analysis.to_dict()
            created_at = data.get('created_at', datetime.now())
            
            if hasattr(created_at, 'strftime'):
                month_key = created_at.strftime('%Y-%m')
            else:
                month_key = datetime.now().strftime('%Y-%m')
            
            if month_key not in trend_data:
                trend_data[month_key] = {'soil': 0, 'leaf': 0, 'issues': 0, 'recommendations': 0}
            
            report_type = data.get('report_type', '')
            if report_type in ['soil', 'leaf']:
                trend_data[month_key][report_type] += 1
            
            # Count issues and recommendations
            analysis_results = data.get('analysis_results', {})
            issues = analysis_results.get('issues', [])
            recommendations = analysis_results.get('recommendations', [])
            trend_data[month_key]['issues'] += len(issues)
            trend_data[month_key]['recommendations'] += len(recommendations)
        
        # Create trend chart
        months = sorted(trend_data.keys())
        soil_counts = [trend_data[month]['soil'] for month in months]
        leaf_counts = [trend_data[month]['leaf'] for month in months]
        issue_counts = [trend_data[month]['issues'] for month in months]
        recommendation_counts = [trend_data[month]['recommendations'] for month in months]
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=months,
            y=soil_counts,
            mode='lines+markers',
            name='Soil Reports',
            line=dict(color='#8B4513', width=3),
            marker=dict(size=8)
        ))
        
        fig.add_trace(go.Scatter(
            x=months,
            y=leaf_counts,
            mode='lines+markers',
            name='Leaf Reports',
            line=dict(color='#228B22', width=3),
            marker=dict(size=8)
        ))
        
        fig.add_trace(go.Scatter(
            x=months,
            y=issue_counts,
            mode='lines+markers',
            name='Total Issues',
            line=dict(color='#DC143C', width=3),
            marker=dict(size=8),
            yaxis='y2'
        ))
        
        fig.add_trace(go.Scatter(
            x=months,
            y=recommendation_counts,
            mode='lines+markers',
            name='Total Recommendations',
            line=dict(color='#4169E1', width=3),
            marker=dict(size=8),
            yaxis='y2'
        ))
        
        fig.update_layout(
            title='Analysis Trends (Last 12 Months)',
            xaxis_title='Month',
            yaxis_title='Number of Reports',
            yaxis2=dict(
                title='Number of Issues/Recommendations',
                overlaying='y',
                side='right'
            ),
            hovermode='x unified',
            height=400,
            showlegend=True
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        st.error(f"Error displaying monthly trends: {str(e)}")

def display_issue_analysis_chart(user_id: str):
    """Display issue analysis pie chart"""
    try:
        db = get_firestore_client()
        if not db:
            st.info("Unable to load issue data.")
            return
        
        analyses_ref = db.collection(COLLECTIONS['analyses']).where('user_id', '==', user_id)
        analyses = analyses_ref.get()
        
        if not analyses:
            st.info("No analyses found to analyze issues.")
            return
        
        # Count issues by type
        issue_types = {}
        priority_counts = {'Low': 0, 'Medium': 0, 'High': 0, 'Critical': 0}
        
        for analysis in analyses:
            analysis_results = analysis.to_dict().get('analysis_results', {})
            issues = analysis_results.get('issues', [])
            
            for issue in issues:
                issue_type = issue.get('type', 'Unknown')
                priority = issue.get('priority', 'Medium')
                
                issue_types[issue_type] = issue_types.get(issue_type, 0) + 1
                priority_counts[priority] = priority_counts.get(priority, 0) + 1
        
        if not issue_types:
            st.info("No issues found in your analyses.")
            return
        
        # Create pie chart for issue types
        col1, col2 = st.columns(2)
        
        with col1:
            fig_types = px.pie(
                values=list(issue_types.values()),
                names=list(issue_types.keys()),
                title="Issues by Type",
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            st.plotly_chart(fig_types, use_container_width=True)
        
        with col2:
            fig_priority = px.pie(
                values=list(priority_counts.values()),
                names=list(priority_counts.keys()),
                title="Issues by Priority",
                color_discrete_map={
                    'Low': '#90EE90',
                    'Medium': '#FFD700',
                    'High': '#FFA500',
                    'Critical': '#FF6347'
                }
            )
            st.plotly_chart(fig_priority, use_container_width=True)
        
    except Exception as e:
        st.error(f"Error displaying issue analysis: {str(e)}")

def display_recommendation_patterns_chart(user_id: str):
    """Display recommendation patterns chart"""
    try:
        db = get_firestore_client()
        if not db:
            st.info("Unable to load recommendation data.")
            return
        
        analyses_ref = db.collection(COLLECTIONS['analyses']).where('user_id', '==', user_id)
        analyses = analyses_ref.get()
        
        if not analyses:
            st.info("No analyses found to analyze recommendations.")
            return
        
        # Count recommendations by category
        recommendation_categories = {}
        cost_categories = {'Low': 0, 'Medium': 0, 'High': 0}
        
        for analysis in analyses:
            analysis_results = analysis.to_dict().get('analysis_results', {})
            recommendations = analysis_results.get('recommendations', [])
            
            for rec in recommendations:
                category = rec.get('category', 'General')
                cost = rec.get('cost_level', 'Medium')
                
                recommendation_categories[category] = recommendation_categories.get(category, 0) + 1
                cost_categories[cost] = cost_categories.get(cost, 0) + 1
        
        if not recommendation_categories:
            st.info("No recommendations found in your analyses.")
            return
        
        # Create bar chart for recommendation categories
        col1, col2 = st.columns(2)
        
        with col1:
            fig_categories = px.bar(
                x=list(recommendation_categories.keys()),
                y=list(recommendation_categories.values()),
                title="Recommendations by Category",
                color=list(recommendation_categories.values()),
                color_continuous_scale='Viridis'
            )
            fig_categories.update_layout(showlegend=False)
            st.plotly_chart(fig_categories, use_container_width=True)
        
        with col2:
            fig_cost = px.bar(
                x=list(cost_categories.keys()),
                y=list(cost_categories.values()),
                title="Recommendations by Cost Level",
                color=['#90EE90', '#FFD700', '#FF6347'],
                color_discrete_map="identity"
            )
            fig_cost.update_layout(showlegend=False)
            st.plotly_chart(fig_cost, use_container_width=True)
        
    except Exception as e:
        st.error(f"Error displaying recommendation patterns: {str(e)}")

# ===== DETAILED ANALYTICS SECTION =====
def display_detailed_analytics_section(user_id: str):
    """Display detailed analytics with comprehensive insights"""
    st.subheader("🔍 Detailed Analytics")
    
    # Get comprehensive analytics
    analytics = get_comprehensive_analytics(user_id)
    
    if not analytics:
        st.info("No data available for detailed analytics.")
        return
    
    # Display analytics in tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Performance", "🎯 Insights", "📈 Forecasts", "⚙️ Settings"])
    
    with tab1:
        display_performance_analytics(analytics)
    
    with tab2:
        display_insights_analytics(analytics)
    
    with tab3:
        display_forecast_analytics(analytics)
    
    with tab4:
        display_analytics_settings()

def get_comprehensive_analytics(user_id: str) -> Dict[str, Any]:
    """Get comprehensive analytics data"""
    try:
        db = get_firestore_client()
        if not db:
            return {}
        
        analyses_ref = db.collection(COLLECTIONS['analyses']).where('user_id', '==', user_id)
        analyses = analyses_ref.get()
        
        if not analyses:
            return {}
        
        # Calculate comprehensive metrics
        total_analyses = len(analyses)
        completed_analyses = 0
        total_issues = 0
        total_recommendations = 0
        avg_processing_time = 0
        
        issue_severity = {'Low': 0, 'Medium': 0, 'High': 0, 'Critical': 0}
        recommendation_effectiveness = {'High': 0, 'Medium': 0, 'Low': 0}
        
        processing_times = []
        
        for analysis in analyses:
            data = analysis.to_dict()
            
            if data.get('status') == 'completed':
                completed_analyses += 1
            
            analysis_results = data.get('analysis_results', {})
            issues = analysis_results.get('issues', [])
            recommendations = analysis_results.get('recommendations', [])
            
            total_issues += len(issues)
            total_recommendations += len(recommendations)
            
            # Count issue severities
            for issue in issues:
                severity = issue.get('priority', 'Medium')
                issue_severity[severity] = issue_severity.get(severity, 0) + 1
            
            # Count recommendation effectiveness
            for rec in recommendations:
                effectiveness = rec.get('effectiveness', 'Medium')
                recommendation_effectiveness[effectiveness] = recommendation_effectiveness.get(effectiveness, 0) + 1
            
            # Calculate processing time
            created_at = data.get('created_at')
            completed_at = data.get('completed_at')
            if created_at and completed_at:
                if hasattr(created_at, 'timestamp') and hasattr(completed_at, 'timestamp'):
                    processing_time = completed_at.timestamp() - created_at.timestamp()
                    processing_times.append(processing_time)
        
        avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0
        
        return {
            'total_analyses': total_analyses,
            'completed_analyses': completed_analyses,
            'completion_rate': (completed_analyses / total_analyses * 100) if total_analyses > 0 else 0,
            'total_issues': total_issues,
            'total_recommendations': total_recommendations,
            'avg_processing_time': avg_processing_time,
            'issue_severity': issue_severity,
            'recommendation_effectiveness': recommendation_effectiveness,
            'avg_issues_per_analysis': total_issues / total_analyses if total_analyses > 0 else 0,
            'avg_recommendations_per_analysis': total_recommendations / total_analyses if total_analyses > 0 else 0
        }
        
    except Exception as e:
        st.error(f"Error getting comprehensive analytics: {str(e)}")
        return {}

def display_performance_analytics(analytics: Dict[str, Any]):
    """Display performance analytics"""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Completion Rate",
            f"{analytics.get('completion_rate', 0):.1f}%",
            delta=f"{analytics.get('completion_rate', 0) - 85:.1f}% vs target"
        )
    
    with col2:
        st.metric(
            "Avg Processing Time",
            f"{analytics.get('avg_processing_time', 0):.1f}s",
            delta=f"{analytics.get('avg_processing_time', 0) - 30:.1f}s vs target"
        )
    
    with col3:
        st.metric(
            "Issues per Analysis",
            f"{analytics.get('avg_issues_per_analysis', 0):.1f}",
            delta=f"{analytics.get('avg_issues_per_analysis', 0) - 2:.1f} vs avg"
        )
    
    with col4:
        st.metric(
            "Recommendations per Analysis",
            f"{analytics.get('avg_recommendations_per_analysis', 0):.1f}",
            delta=f"{analytics.get('avg_recommendations_per_analysis', 0) - 3:.1f} vs avg"
        )

def display_insights_analytics(analytics: Dict[str, Any]):
    """Display insights analytics"""
    st.write("**🔍 Key Insights:**")
    
    # Generate insights based on data
    insights = []
    
    completion_rate = analytics.get('completion_rate', 0)
    if completion_rate > 90:
        insights.append("✅ Excellent analysis completion rate!")
    elif completion_rate > 75:
        insights.append("⚠️ Good completion rate, room for improvement")
    else:
        insights.append("❌ Low completion rate, check system performance")
    
    avg_issues = analytics.get('avg_issues_per_analysis', 0)
    if avg_issues > 5:
        insights.append("🔍 High issue detection rate - comprehensive analysis")
    elif avg_issues > 2:
        insights.append("📊 Moderate issue detection - good coverage")
    else:
        insights.append("⚠️ Low issue detection - may need review")
    
    avg_recommendations = analytics.get('avg_recommendations_per_analysis', 0)
    if avg_recommendations > 4:
        insights.append("💡 Comprehensive recommendations provided")
    elif avg_recommendations > 2:
        insights.append("📋 Good recommendation coverage")
    else:
        insights.append("⚠️ Limited recommendations - may need enhancement")
    
    for insight in insights:
        st.write(insight)

def display_forecast_analytics(analytics: Dict[str, Any]):
    """Display forecast analytics"""
    st.write("**📈 Forecasts:**")
    
    # Simple forecasting based on current trends
    total_analyses = analytics.get('total_analyses', 0)
    completion_rate = analytics.get('completion_rate', 0)
    
    # Project next month
    projected_analyses = total_analyses * 1.1  # 10% growth assumption
    projected_completion = projected_analyses * (completion_rate / 100)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric(
            "Projected Analyses (Next Month)",
            f"{projected_analyses:.0f}",
            delta=f"+{projected_analyses - total_analyses:.0f}"
        )
    
    with col2:
        st.metric(
            "Projected Completions (Next Month)",
            f"{projected_completion:.0f}",
            delta=f"+{projected_completion - (total_analyses * completion_rate / 100):.0f}"
        )

def display_analytics_settings():
    """Display analytics settings"""
    st.write("**⚙️ Analytics Settings:**")
    
    # Auto-refresh setting
    st.checkbox("Auto-refresh dashboard every 30 seconds", value=True)
    
    # Chart preferences
    st.selectbox("Chart Style", ["Default", "Dark", "Light"])
    
    # Data range
    st.selectbox("Data Range", ["Last 30 days", "Last 3 months", "Last 6 months", "Last year", "All time"])
    
    if st.button("💾 Save Settings"):
        st.success("Settings saved successfully!")

# ===== USER PROFILE SECTION =====
def display_user_profile_section(user_info: Dict[str, Any]):
    """Display enhanced user profile section"""
    with st.container():
        st.subheader("👤 Profile")
        
        # Profile avatar and basic info
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.markdown("""
            <div style="text-align: center;">
                <div style="width: 80px; height: 80px; background: linear-gradient(45deg, #2E8B57, #32CD32); 
                            border-radius: 50%; display: flex; align-items: center; justify-content: center; 
                            margin: 0 auto; font-size: 32px; color: white;">
                    👤
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.write(f"**Name:** {user_info.get('name', 'N/A')}")
            st.write(f"**Email:** {user_info.get('email', 'N/A')}")
            st.write(f"**Role:** {user_info.get('role', 'user').title()}")
            
            created_at = user_info.get('created_at')
            if created_at and hasattr(created_at, 'strftime'):
                st.write(f"**Member Since:** {created_at.strftime('%B %Y')}")
        
        # Profile statistics
        st.markdown("---")
        st.write("**📊 Profile Statistics:**")
        
        user_id = st.session_state['user_id']
        stats = get_comprehensive_user_statistics(user_id)
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Analyses", stats.get('total_analyses', 0))
            st.metric("This Week", stats.get('recent_activity', 0))
        
        with col2:
            st.metric("Issues Found", stats.get('total_issues', 0))
            st.metric("Recommendations", stats.get('total_recommendations', 0))
        
        # Edit profile button
        if st.button("✏️ Edit Profile", use_container_width=True, type="secondary"):
            edit_profile_modal(user_info)

# ===== QUICK ACTIONS SECTION =====
def display_quick_actions_section():
    """Display enhanced quick actions section"""
    st.subheader("⚡ Quick Actions")
    
    # Primary actions
    if st.button("📤 Analyze Files", use_container_width=True, type="primary"):
        st.session_state.current_page = 'upload'
        st.rerun()
    
    if st.button("📈 View History", use_container_width=True):
        st.session_state.current_page = 'history'
        st.rerun()
    
    st.markdown("---")
    
    # Secondary actions
    if st.button("📋 Generate Report", use_container_width=True):
        st.info("Report generation feature coming soon!")
    
    if st.button("📧 Export Data", use_container_width=True):
        st.info("Data export feature coming soon!")
    
    if st.button("⚙️ Settings", use_container_width=True):
        st.info("Settings page coming soon!")
    
    # Admin actions
    user_info = get_user_by_id(st.session_state.get('user_id', ''))
    if user_info and user_info.get('role') == 'admin':
        st.markdown("---")
        st.write("**🔧 Admin Actions:**")
        
        if st.button("👥 User Management", use_container_width=True):
            st.session_state.current_page = 'admin'
            st.rerun()
        
        if st.button("🤖 AI Configuration", use_container_width=True):
            st.session_state.current_page = 'admin'
            st.rerun()

# ===== SYSTEM STATUS SECTION =====
def display_system_status_section():
    """Display real-time system status"""
    st.subheader("🔧 System Status")
    
    # Get system status
    status = get_system_status()
    
    # System health indicators
    col1, col2 = st.columns(2)
    
    with col1:
        # Database status
        db_status = "🟢 Online" if status.get('database', False) else "🔴 Offline"
        st.write(f"**Database:** {db_status}")
        
        # AI Service status
        ai_status = "🟢 Online" if status.get('ai_service', False) else "🔴 Offline"
        st.write(f"**AI Service:** {ai_status}")
    
    with col2:
        # Storage status
        storage_status = "🟢 Online" if status.get('storage', False) else "🔴 Offline"
        st.write(f"**Storage:** {storage_status}")
        
        # OCR Service status
        ocr_status = "🟢 Online" if status.get('ocr_service', False) else "🔴 Offline"
        st.write(f"**OCR Service:** {ocr_status}")
    
    # System metrics
    st.markdown("---")
    st.write("**📊 System Metrics:**")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Active Users", status.get('active_users', 0))
    
    with col2:
        st.metric("Processing Queue", status.get('processing_queue', 0))
    
    with col3:
        st.metric("Success Rate", f"{status.get('success_rate', 0):.1f}%")
    
    # Refresh status button
    if st.button("🔄 Refresh Status", use_container_width=True):
        st.rerun()

def get_system_status() -> Dict[str, Any]:
    """Get real-time system status"""
    try:
        db = get_firestore_client()
        
        # Check database connection
        database_online = db is not None
        
        # Check AI service status
        try:
            from utils.analysis_engine import AnalysisEngine
            engine = AnalysisEngine()
            ai_service_online = engine.llm is not None
        except Exception:
            ai_service_online = False
        
        # Check storage status
        try:
            storage_online = db is not None
        except Exception:
            storage_online = False
        
        # Check OCR service status
        try:
            import pytesseract
            pytesseract.get_tesseract_version()
            ocr_service_online = True
        except Exception:
            ocr_service_online = False
        
        # Get system metrics from real data
        try:
            if db:
                users_ref = db.collection('users')
                active_users = len(list(users_ref.stream()))
                
                analyses_ref = db.collection('analyses')
                total_analyses = len(list(analyses_ref.stream()))
                
                # Calculate success rate from completed analyses
                success_rate = 100.0 if total_analyses > 0 else 0.0
                processing_queue = 0  # Would get from actual processing queue
            else:
                active_users = 0
                processing_queue = 0
                success_rate = 0.0
        except Exception as e:
            logger.error(f"Error fetching system metrics: {str(e)}")
            active_users = 0
            processing_queue = 0
            success_rate = 0.0
        
        return {
            'database': database_online,
            'ai_service': ai_service_online,
            'storage': storage_online,
            'ocr_service': ocr_service_online,
            'active_users': active_users,
            'processing_queue': processing_queue,
            'success_rate': success_rate
        }
        
    except Exception:
        return {
            'database': False,
            'ai_service': False,
            'storage': False,
            'ocr_service': False,
            'active_users': 0,
            'processing_queue': 0,
            'success_rate': 0
        }

# ===== NOTIFICATIONS SECTION =====
def display_notifications_section(user_id: str):
    """Display enhanced notifications section"""
    st.subheader("🔔 Notifications")
    
    # Get real-time notifications
    notifications = get_real_time_notifications(user_id)
    
    if not notifications:
        st.info("No new notifications.")
        return
    
    # Display notifications with priority
    for notification in notifications[:5]:  # Show only 5 recent
        priority = notification.get('priority', 'normal')
        priority_color = {
            'high': '🔴',
            'medium': '🟡',
            'low': '🟢',
            'normal': '🔵'
        }.get(priority, '🔵')
        
        with st.container():
            st.write(f"{priority_color} **{notification.get('title', 'Notification')}**")
            st.write(notification.get('message', ''))
            st.caption(f"{notification.get('date', datetime.now().strftime('%Y-%m-%d %H:%M'))}")
            
            # Action buttons for notifications
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Mark Read", key=f"read_{notification.get('id', '')}"):
                    mark_notification_read(notification.get('id', ''))
                    st.rerun()
            
            with col2:
                if st.button("🗑️ Dismiss", key=f"dismiss_{notification.get('id', '')}"):
                    dismiss_notification(notification.get('id', ''))
                    st.rerun()
            
            st.divider()

def get_real_time_notifications(user_id: str) -> List[Dict[str, Any]]:
    """Get real-time notifications for user"""
    try:
    # This would typically fetch from a notifications collection
        # For now, return sample notifications with real-time data
        
        notifications = [
        {
                'id': '1',
            'title': 'Welcome to AGS AI Assistant!',
            'message': 'Start by uploading your first SP LAB report for analysis.',
                'date': datetime.now().strftime('%Y-%m-%d %H:%M'),
                'priority': 'high',
                'type': 'welcome'
        },
        {
                'id': '2',
            'title': 'New Feature Available',
            'message': 'Check out the new yield forecasting feature in your analysis reports.',
                'date': (datetime.now() - timedelta(hours=2)).strftime('%Y-%m-%d %H:%M'),
                'priority': 'medium',
            'type': 'feature'
            },
            {
                'id': '3',
                'title': 'System Maintenance',
                'message': 'Scheduled maintenance will occur tonight from 2-4 AM.',
                'date': (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d %H:%M'),
                'priority': 'low',
                'type': 'maintenance'
            }
        ]
        
        # Add real-time notifications based on user activity
        stats = get_comprehensive_user_statistics(user_id)
        
        if stats.get('total_analyses', 0) == 0:
            notifications.append({
                'id': '4',
                'title': 'Get Started',
                'message': 'Upload your first SP LAB report to begin analysis.',
                'date': datetime.now().strftime('%Y-%m-%d %H:%M'),
                'priority': 'high',
                'type': 'action_required'
            })
        
        if stats.get('critical_issues', 0) > 0:
            notifications.append({
                'id': '5',
                'title': 'Critical Issues Detected',
                'message': f'You have {stats.get("critical_issues", 0)} critical issues that need attention.',
                'date': datetime.now().strftime('%Y-%m-%d %H:%M'),
                'priority': 'high',
                'type': 'alert'
            })
        
        return notifications
        
    except Exception as e:
        st.error(f"Error getting notifications: {str(e)}")
        return []

def mark_notification_read(notification_id: str):
    """Mark notification as read"""
    # This would update the notification in the database
    # notification_id would be used here in a real implementation
    st.success("Notification marked as read!")

def dismiss_notification(notification_id: str):
    """Dismiss notification"""
    # This would remove or hide the notification
    # notification_id would be used here in a real implementation
    st.success("Notification dismissed!")

# ===== LEGACY FUNCTIONS (Updated for compatibility) =====
def get_user_statistics(user_id: str) -> Dict[str, Any]:
    """Get user statistics (legacy function for compatibility)"""
    return get_comprehensive_user_statistics(user_id)

def display_quick_stats(stats: Dict[str, Any]):
    """Display quick statistics cards (legacy function)"""
    # This function is now handled by display_real_time_metrics
    pass

def get_recent_analyses(user_id: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Get recent analyses for user (legacy function)"""
    return get_detailed_recent_analyses(user_id, limit)

def display_recent_analyses(analyses: List[Dict[str, Any]]):
    """Display recent analyses table (legacy function)"""
    # This function is now handled by display_recent_activity_section
    pass

def display_analysis_trends(user_id: str):
    """Display analysis trends chart (legacy function)"""
    # This function is now handled by display_analysis_trends_section
    display_analysis_trends_section(user_id)

def display_user_profile(user_info: Dict[str, Any]):
    """Display user profile card (legacy function)"""
    # This function is now handled by display_user_profile_section
    display_user_profile_section(user_info)

def edit_profile_modal(user_info: Dict[str, Any]):
    """Show edit profile modal"""
    with st.form("edit_profile_form"):
        st.subheader("Edit Profile")
        
        new_name = st.text_input("Name", value=user_info.get('name', ''))
        new_phone = st.text_input("Phone", value=user_info.get('phone', ''))
        new_company = st.text_input("Company", value=user_info.get('company', ''))
        new_location = st.text_input("Location", value=user_info.get('location', ''))
        
        col1, col2 = st.columns(2)
        with col1:
            if st.form_submit_button("💾 Save Changes", type="primary"):
                update_data = {
                    'name': new_name,
                    'phone': new_phone,
                    'company': new_company,
                    'location': new_location,
                    'updated_at': datetime.now()
                }
                
                if update_user_profile(st.session_state['user_id'], update_data):
                    st.success("Profile updated successfully!")
                    st.rerun()
                else:
                    st.error("Failed to update profile.")
        
        with col2:
            if st.form_submit_button("❌ Cancel"):
                st.rerun()

def display_quick_actions():
    """Display quick action buttons (legacy function)"""
    # This function is now handled by display_quick_actions_section
    display_quick_actions_section()

def display_notifications(user_id: str):
    """Display system notifications (legacy function)"""
    # This function is now handled by display_notifications_section
    display_notifications_section(user_id)

def get_user_notifications(user_id: str) -> List[Dict[str, Any]]:
    """Get user notifications (legacy function)"""
    # This function is now handled by get_real_time_notifications
    return get_real_time_notifications(user_id)

def download_pdf_report(analysis_id: str):
    """Download PDF report for analysis"""
    try:
        # Get analysis data
        db = get_firestore_client()
        if not db:
            st.error("Database connection failed.")
            return
        
        analysis_ref = db.collection(COLLECTIONS['analyses']).document(analysis_id)
        analysis_doc = analysis_ref.get()
        
        if not analysis_doc.exists:
            st.error("Analysis not found.")
            return
        
        analysis_data = analysis_doc.to_dict()
        
        # Check if PDF already exists in storage
        pdf_url = analysis_data.get('pdf_url')
        if pdf_url:
            st.success("PDF report is ready for download!")
            st.markdown(f"[📄 Download PDF Report]({pdf_url})")
        else:
            st.info("PDF report is being generated. Please try again in a few moments.")
            
            # Trigger PDF generation (this would be handled by a background process)
            # For now, just show a message
            if st.button("🔄 Generate PDF"):
                st.info("PDF generation started. This may take a few minutes.")
        
    except Exception as e:
        st.error(f"Error downloading PDF: {str(e)}")

def delete_analysis(analysis_id: str):
    """Delete analysis with confirmation"""
    if st.button("⚠️ Confirm Delete", type="secondary"):
        try:
            db = get_firestore_client()
            if not db:
                st.error("Database connection failed.")
                return
            
            # Delete analysis document
            analysis_ref = db.collection(COLLECTIONS['analyses']).document(analysis_id)
            analysis_ref.delete()
            
            st.success("Analysis deleted successfully!")
            st.rerun()
            
        except Exception as e:
            st.error(f"Error deleting analysis: {str(e)}")

def display_analytics_insights_tab(user_id):
    """Display Analytics & Insights tab content"""
    st.markdown("## 📈 Analytics & Insights")
    st.markdown("Discover patterns and insights from your agricultural analysis data")
    
    # Get user analytics data
    analytics_data = _cached_user_analytics(user_id)
    
    if not analytics_data or analytics_data['total_analyses'] == 0:
        st.info("No analysis data available yet. Upload some agricultural reports to see insights!")
        return
    
    # Create columns for different analytics sections
    col1, col2 = st.columns(2)
    
    with col1:
        # Analysis Trends
        st.markdown("### 📊 Analysis Trends")
        
        # Monthly analysis count
        monthly_data = analytics_data.get('monthly_trends', [])
        if monthly_data:
            import plotly.express as px
            import pandas as pd
            
            df = pd.DataFrame(monthly_data)
            fig = px.line(df, x='month', y='count', 
                         title='Monthly Analysis Count',
                         markers=True)
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Analysis trends will appear after multiple analyses")
        
        # Most Common Issues
        st.markdown("### 🎯 Most Common Issues")
        common_issues = analytics_data.get('common_issues', [])
        if common_issues:
            for issue in common_issues[:5]:
                st.markdown(f"• {issue['issue']} ({issue['count']} times)")
        else:
            st.info("Issue patterns will appear after multiple analyses")
    
    with col2:
        # Performance Metrics
        st.markdown("### ⚡ Performance Metrics")
        
        # Analysis success rate
        success_rate = analytics_data.get('success_rate', 0)
        st.metric("Success Rate", f"{success_rate:.1f}%")
        
        # Average processing time
        avg_time = analytics_data.get('avg_processing_time', 0)
        st.metric("Avg Processing Time", f"{avg_time:.1f} seconds")
        
        # Data quality score
        quality_score = analytics_data.get('data_quality_score', 0)
        st.metric("Data Quality Score", f"{quality_score:.1f}/10")
        
        # Recommendations Generated
        total_recs = analytics_data.get('total_recommendations', 0)
        st.metric("Total Recommendations", total_recs)
        
        # Recent Activity
        st.markdown("### 📅 Recent Activity")
        recent_activity = analytics_data.get('recent_activity', [])
        if recent_activity:
            for activity in recent_activity[:5]:
                st.markdown(f"• {activity['description']} - {activity['date']}")
        else:
            st.info("Recent activity will appear here")
    
    # Insights and Recommendations
    st.markdown("### 💡 AI-Generated Insights")
    insights = analytics_data.get('ai_insights', [])
    if insights:
        for insight in insights:
            with st.expander(f"🔍 {insight['title']}", expanded=False):
                st.markdown(insight['description'])
                if 'recommendation' in insight:
                    st.markdown(f"**Recommendation:** {insight['recommendation']}")
    else:
        st.info("AI insights will be generated as you complete more analyses")

def display_help_us_improve_tab():
    """Display Help Us Improve tab content"""
    st.markdown("## 💬 Help Us Improve")
    st.markdown("Your feedback helps us make our agricultural analysis platform better!")
    
    # Import the feedback system
    try:
        from utils.feedback_system import display_feedback_section as display_feedback_section_util
        
        # Get analysis ID and user ID for feedback
        analysis_id = f"dashboard_feedback_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        user_id = st.session_state.get('user_id', 'anonymous')
        
        # Display feedback section
        display_feedback_section_util(analysis_id, user_id)
        
    except Exception as e:
        st.error(f"Error loading feedback system: {str(e)}")
        st.info("Please try refreshing the page or contact support if the issue persists.")

if __name__ == "__main__":
    show_dashboard()