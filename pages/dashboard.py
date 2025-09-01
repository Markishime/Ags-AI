import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, List, Any, Optional
import sys
import os

# Add utils to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'utils'))

from firebase_config import get_firestore_client, get_storage_bucket, COLLECTIONS
from auth_utils import get_user_by_id, update_user_profile

def show_dashboard():
    """Display user dashboard"""
    # Header with logout button
    col1, col2 = st.columns([3, 1])
    with col1:
        st.title("🏠 Dashboard")
    with col2:
        if st.button("🚪 Logout", type="secondary", use_container_width=True):
            # Clear session state
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.success("Logged out successfully!")
            st.rerun()
    
    # Check if user is logged in
    if 'user_id' not in st.session_state:
        st.error("Please log in to access the dashboard.")
        return
    
    user_id = st.session_state['user_id']
    
    # Get user information
    user_info = get_user_by_id(user_id)
    if not user_info:
        st.error("User information not found.")
        return
    
    # Dashboard layout
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader(f"Welcome back, {user_info.get('name', 'User')}! 👋")
        
        # Quick stats
        stats = get_user_statistics(user_id)
        display_quick_stats(stats)
        
        # Recent analyses
        st.subheader("📊 Recent Analyses")
        recent_analyses = get_recent_analyses(user_id, limit=5)
        display_recent_analyses(recent_analyses)
        
        # Analysis trends
        st.subheader("📈 Analysis Trends")
        display_analysis_trends(user_id)
    
    with col2:
        # User profile card
        display_user_profile(user_info)
        
        # Quick actions
        display_quick_actions()
        
        # System notifications
        display_notifications(user_id)

def get_user_statistics(user_id: str) -> Dict[str, Any]:
    """Get user statistics"""
    try:
        db = get_firestore_client()
        if not db:
            return {}
        
        # Get all user analyses
        analyses_ref = db.collection(COLLECTIONS['analyses']).where('user_id', '==', user_id)
        analyses = analyses_ref.get()
        
        total_analyses = len(analyses)
        
        # Count by report type
        soil_analyses = 0
        leaf_analyses = 0
        total_issues = 0
        total_recommendations = 0
        
        for analysis in analyses:
            data = analysis.to_dict()
            report_type = data.get('report_type', '')
            
            if report_type == 'soil':
                soil_analyses += 1
            elif report_type == 'leaf':
                leaf_analyses += 1
            
            # Count issues and recommendations
            analysis_results = data.get('analysis_results', {})
            issues = analysis_results.get('issues', [])
            recommendations = analysis_results.get('recommendations', [])
            
            total_issues += len(issues)
            total_recommendations += len(recommendations)
        
        # Get recent activity (last 30 days)
        thirty_days_ago = datetime.now() - timedelta(days=30)
        recent_analyses = []
        for a in analyses:
            created_at = a.to_dict().get('created_at', datetime.min)
            # Convert timezone-aware datetime to naive for comparison
            if hasattr(created_at, 'replace') and hasattr(created_at, 'tzinfo') and created_at.tzinfo is not None:
                created_at_naive = created_at.replace(tzinfo=None)
            else:
                created_at_naive = created_at
            
            if created_at_naive > thirty_days_ago:
                recent_analyses.append(a)
        
        return {
            'total_analyses': total_analyses,
            'soil_analyses': soil_analyses,
            'leaf_analyses': leaf_analyses,
            'total_issues': total_issues,
            'total_recommendations': total_recommendations,
            'recent_activity': len(recent_analyses),
            'avg_issues_per_analysis': total_issues / max(total_analyses, 1)
        }
        
    except Exception as e:
        st.error(f"Error getting statistics: {str(e)}")
        return {}

def display_quick_stats(stats: Dict[str, Any]):
    """Display quick statistics cards"""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Total Analyses",
            value=stats.get('total_analyses', 0),
            delta=f"+{stats.get('recent_activity', 0)} this month"
        )
    
    with col2:
        st.metric(
            label="Soil Reports",
            value=stats.get('soil_analyses', 0)
        )
    
    with col3:
        st.metric(
            label="Leaf Reports",
            value=stats.get('leaf_analyses', 0)
        )
    
    with col4:
        st.metric(
            label="Avg Issues/Report",
            value=f"{stats.get('avg_issues_per_analysis', 0):.1f}"
        )
    
    st.divider()

def get_recent_analyses(user_id: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Get recent analyses for user"""
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
        st.error(f"Error getting recent analyses: {str(e)}")
        return []

def display_recent_analyses(analyses: List[Dict[str, Any]]):
    """Display recent analyses table"""
    if not analyses:
        st.info("No analyses found. Upload your first SP LAB report to get started!")
        if st.button("📤 Upload Report", type="primary"):
            st.session_state.current_page = 'upload'
            st.rerun()
        return
    
    # Create DataFrame for display
    display_data = []
    for analysis in analyses:
        created_at = analysis.get('created_at', datetime.now())
        if hasattr(created_at, 'strftime'):
            date_str = created_at.strftime('%Y-%m-%d %H:%M')
        else:
            date_str = str(created_at)
        
        analysis_results = analysis.get('analysis_results', {})
        issues_count = len(analysis_results.get('issues', []))
        recommendations_count = len(analysis_results.get('recommendations', []))
        
        display_data.append({
            'Date': date_str,
            'Report Type': analysis.get('report_type', 'Unknown').title(),
            'Sample ID': analysis.get('sample_id', 'N/A'),
            'Issues': issues_count,
            'Recommendations': recommendations_count,
            'Status': '✅ Complete' if analysis.get('status') == 'completed' else '⏳ Processing'
        })
    
    df = pd.DataFrame(display_data)
    
    # Display table with selection
    selected_indices = st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row"
    )
    
    # Action buttons
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📊 View Details", disabled=len(selected_indices.get('selection', {}).get('rows', [])) == 0):
            if selected_indices['selection']['rows']:
                selected_idx = selected_indices['selection']['rows'][0]
                selected_analysis = analyses[selected_idx]
                st.session_state['selected_analysis_id'] = selected_analysis['id']
                st.switch_page("pages/analysis_details.py")
    
    with col2:
        if st.button("📄 Download PDF", disabled=len(selected_indices.get('selection', {}).get('rows', [])) == 0):
            if selected_indices['selection']['rows']:
                selected_idx = selected_indices['selection']['rows'][0]
                selected_analysis = analyses[selected_idx]
                download_pdf_report(selected_analysis['id'])
    
    with col3:
        if st.button("🗑️ Delete", disabled=len(selected_indices.get('selection', {}).get('rows', [])) == 0):
            if selected_indices['selection']['rows']:
                selected_idx = selected_indices['selection']['rows'][0]
                selected_analysis = analyses[selected_idx]
                delete_analysis(selected_analysis['id'])

def display_analysis_trends(user_id: str):
    """Display analysis trends chart"""
    try:
        # Get analyses for the last 6 months
        db = get_firestore_client()
        if not db:
            st.info("Unable to load trend data.")
            return
        
        from datetime import timezone
        # Use timezone-aware datetime for Firestore query
        six_months_ago = datetime.now(timezone.utc) - timedelta(days=180)
        analyses_ref = (db.collection(COLLECTIONS['analyses'])
                       .where('user_id', '==', user_id)
                       .where('created_at', '>=', six_months_ago))
        
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
                trend_data[month_key] = {'soil': 0, 'leaf': 0, 'issues': 0}
            
            report_type = data.get('report_type', '')
            if report_type in ['soil', 'leaf']:
                trend_data[month_key][report_type] += 1
            
            # Count issues
            analysis_results = data.get('analysis_results', {})
            issues = analysis_results.get('issues', [])
            trend_data[month_key]['issues'] += len(issues)
        
        # Create trend chart
        months = sorted(trend_data.keys())
        soil_counts = [trend_data[month]['soil'] for month in months]
        leaf_counts = [trend_data[month]['leaf'] for month in months]
        issue_counts = [trend_data[month]['issues'] for month in months]
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=months,
            y=soil_counts,
            mode='lines+markers',
            name='Soil Reports',
            line=dict(color='brown')
        ))
        
        fig.add_trace(go.Scatter(
            x=months,
            y=leaf_counts,
            mode='lines+markers',
            name='Leaf Reports',
            line=dict(color='green')
        ))
        
        fig.add_trace(go.Scatter(
            x=months,
            y=issue_counts,
            mode='lines+markers',
            name='Total Issues',
            line=dict(color='red'),
            yaxis='y2'
        ))
        
        fig.update_layout(
            title='Analysis Trends (Last 6 Months)',
            xaxis_title='Month',
            yaxis_title='Number of Reports',
            yaxis2=dict(
                title='Number of Issues',
                overlaying='y',
                side='right'
            ),
            hovermode='x unified'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        st.error(f"Error displaying trends: {str(e)}")

def display_user_profile(user_info: Dict[str, Any]):
    """Display user profile card"""
    with st.container():
        st.subheader("👤 Profile")
        
        # Profile information
        st.write(f"**Name:** {user_info.get('name', 'N/A')}")
        st.write(f"**Email:** {user_info.get('email', 'N/A')}")
        st.write(f"**Role:** {user_info.get('role', 'user').title()}")
        
        created_at = user_info.get('created_at')
        if created_at and hasattr(created_at, 'strftime'):
            st.write(f"**Member Since:** {created_at.strftime('%B %Y')}")
        
        # Edit profile button
        if st.button("✏️ Edit Profile", use_container_width=True):
            edit_profile_modal(user_info)

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
    """Display quick action buttons"""
    st.subheader("⚡ Quick Actions")
    
    if st.button("📤 Upload New Report", use_container_width=True, type="primary"):
        st.session_state.current_page = 'upload'
        st.rerun()
    
    if st.button("📊 View All Analyses", use_container_width=True):
        st.switch_page("pages/history.py")
    
    if st.button("📈 Analytics", use_container_width=True):
        st.switch_page("pages/analytics.py")
    
    if st.button("⚙️ Settings", use_container_width=True):
        st.switch_page("pages/settings.py")
    
    # Admin actions
    user_info = get_user_by_id(st.session_state.get('user_id', ''))
    if user_info and user_info.get('role') == 'admin':
        st.divider()
        st.write("**Admin Actions:**")
        
        if st.button("🔧 Admin Panel", use_container_width=True):
            st.switch_page("pages/admin.py")

def display_notifications(user_id: str):
    """Display system notifications"""
    st.subheader("🔔 Notifications")
    
    # Get recent notifications (placeholder)
    notifications = get_user_notifications(user_id)
    
    if not notifications:
        st.info("No new notifications.")
        return
    
    for notification in notifications[:3]:  # Show only 3 recent
        with st.container():
            st.write(f"**{notification.get('title', 'Notification')}**")
            st.write(notification.get('message', ''))
            st.caption(notification.get('date', datetime.now().strftime('%Y-%m-%d')))
            st.divider()

def get_user_notifications(user_id: str) -> List[Dict[str, Any]]:
    """Get user notifications (placeholder)"""
    # This would typically fetch from a notifications collection
    # For now, return sample notifications
    return [
        {
            'title': 'Welcome to AGS AI Assistant!',
            'message': 'Start by uploading your first SP LAB report for analysis.',
            'date': datetime.now().strftime('%Y-%m-%d'),
            'type': 'info'
        },
        {
            'title': 'New Feature Available',
            'message': 'Check out the new yield forecasting feature in your analysis reports.',
            'date': (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d'),
            'type': 'feature'
        }
    ]

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

if __name__ == "__main__":
    show_dashboard()