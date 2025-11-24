"""
Translation system for AGS AI Assistant
Supports English and Bahasa Malaysia (Malaysian)
"""

import streamlit as st
from typing import Dict, Any

# Translation dictionaries
TRANSLATIONS = {
    'en': {
        # Common
        'app_title': 'AGS AI Assistant',
        'app_subtitle': 'Advanced Oil Palm Cultivation Analysis System',
        'language': 'Language',
        'english': 'English',
        'malay': 'Malaysian',
        'toggle_language': 'Toggle Language',
        
        # Navigation
        'nav_home': 'Home',
        'nav_analyze': 'Analyze Files',
        'nav_admin': 'Admin Panel',
        'nav_help_improve': '💬 Help Us Improve',
        'nav_upload': 'Upload',
        
        # Home Page
        'home_title': 'Welcome to AGS AI Assistant',
        'home_what_title': 'What this tool does:',
        'home_what_1': 'Reads your soil and leaf test reports',
        'home_what_2': 'Analyzes the data using AI',
        'home_what_3': 'Gives you farming recommendations',
        'home_what_4': 'Shows yield predictions for your plantation',
        'home_how_title': 'How to use it:',
        'home_how_1': 'Upload your test reports',
        'home_how_2': 'Enter your farm details',
        'home_how_3': 'Get your analysis results',
        'home_how_4': 'Review recommendations and insights',
        'home_ready': 'Ready to get started?',
        'home_ready_desc': 'Upload your oil palm test reports and get helpful farming advice.',
        'home_start': 'Start Analysis',
        
        # Dashboard
        'dashboard_title': 'Dashboard',
        'dashboard_welcome': 'Welcome Back, {}!',
        'dashboard_welcome_msg': 'Ready to revolutionize your oil palm cultivation with AI-powered insights?',
        'dashboard_tab_1': '📊 Dashboard',
        'dashboard_tab_2': '💬 Help Us Improve',
        'dashboard_reports': 'Previous Reports',
        'dashboard_no_reports': 'No Reports Found',
        'dashboard_no_reports_msg': 'Upload your first oil palm agricultural report to get started with AI analysis!',
        'dashboard_no_reports_desc': 'Our AI will analyze your soil and leaf data to provide intelligent insights.',
        'dashboard_actions': 'AI Agriculture Actions',
        'dashboard_action_analyze': 'Analyze Agricultural Reports',
        'dashboard_action_analyze_desc': 'Upload your oil palm soil and leaf test reports for AI analysis',
        'dashboard_action_results': 'View Latest Results',
        'dashboard_action_results_desc': 'Open your most recent AI analysis summary',
        'dashboard_start_analysis': '📤 Start AI Analysis',
        'dashboard_view_results': '📊 View Results',
        'dashboard_profile': 'AI Agriculture Profile',
        'dashboard_status': 'AI Agriculture System Status',
        'dashboard_status_operational': 'AI Agriculture Systems Operational',
        'dashboard_status_analysis': 'AI Analysis: Ready',
        'dashboard_status_database': 'Database: Connected',
        'dashboard_status_ocr': 'OCR: Active',
        'dashboard_status_online': 'Analysis: Online',
        'dashboard_member_since': 'AI Agriculture Member since {}',
        'dashboard_logout': '🚪 Logout',
        'dashboard_help_title': '💬 Help Us Improve AI Agriculture',
        'dashboard_help_desc': 'Your feedback helps us make our AI-powered agricultural analysis platform better for oil palm cultivation!',
        
        # Upload
        'upload_title': 'Upload and Analyze',
        'upload_desc': 'Upload your oil palm test reports',
        'upload_select_files': 'Select files',
        'upload_file_types': 'Supported: PDF, JPG, PNG',
        'upload_analyzing': 'Analyzing...',
        'upload_success': 'Analysis complete!',
        'upload_error': 'Error during analysis',
        
        # Results
        'results_title': 'Analysis Results',
        'results_no_results': 'No results available',
        
        
        # Admin
        'admin_title': 'Admin Panel',
        'admin_restricted': 'Admin access only',
        
        # Common actions
        'btn_view': 'View',
        'btn_download': 'Download',
        'btn_delete': 'Delete',
        'btn_edit': 'Edit',
        'btn_save': 'Save',
        'btn_cancel': 'Cancel',
        'btn_submit': 'Submit',
        'btn_back': 'Back',
        
        # Status messages
        'status_success': 'Success',
        'status_error': 'Error',
        'status_warning': 'Warning',
        'status_info': 'Info',
        'status_loading': 'Loading...',
        
        # Time
        'time_created': 'Created: {}',
        'time_updated': 'Updated: {}',
        
        # Reports
        'report_type': 'Type: {} Analysis',
        'report_status': 'Status: AI Analysis Complete',
        
        # System
        'system_ready': 'All Systems Operational',
        'system_status': 'System Status',
        
        # Footer
        'footer_copyright': '© 2025 AGS AI Assistant | Advanced Oil Palm Cultivation Analysis System',
    },
    'ms': {
        # Common
        'app_title': 'Pembantu AI AGS',
        'app_subtitle': 'Sistem Analisis Penanaman Kelapa Sawit Lanjutan',
        'language': 'Bahasa',
        'english': 'Bahasa Inggeris',
        'malay': 'Bahasa Malaysia',
        'toggle_language': 'Tukar Bahasa',
        
        # Navigation
        'nav_home': 'Laman Utama',
        'nav_analyze': 'Analisa Fail',
        'nav_admin': 'Panel Admin',
        'nav_help_improve': '💬 Bantu Kami Meningkatkan',
        'nav_upload': 'Muat Naik',
        
        # Home Page
        'home_title': 'Selamat Datang ke Pembantu AI AGS',
        'home_what_title': 'Apa yang alat ini lakukan:',
        'home_what_1': 'Membaca laporan ujian tanah dan daun anda',
        'home_what_2': 'Menganalisis data menggunakan AI',
        'home_what_3': 'Memberi cadangan pertanian kepada anda',
        'home_what_4': 'Menunjukkan ramalan hasil untuk ladang anda',
        'home_how_title': 'Cara menggunakannya:',
        'home_how_1': 'Muat naik laporan ujian anda',
        'home_how_2': 'Masukkan butiran ladang anda',
        'home_how_3': 'Dapatkan hasil analisis anda',
        'home_how_4': 'Semak cadangan dan pandangan',
        'home_ready': 'Bersedia untuk bermula?',
        'home_ready_desc': 'Muat naik laporan ujian kelapa sawit anda dan dapatkan nasihat pertanian yang berguna.',
        'home_start': 'Mula Analisis',
        
        # Dashboard
        'dashboard_title': 'Papan Pemuka',
        'dashboard_welcome': 'Selamat Datang Semula, {}!',
        'dashboard_welcome_msg': 'Bersedia untuk merevolusikan penanaman kelapa sawit anda dengan pandangan yang dikuasakan oleh AI?',
        'dashboard_tab_1': '📊 Papan Pemuka',
        'dashboard_tab_2': '💬 Bantu Kami Meningkatkan',
        'dashboard_reports': 'Laporan Terdahulu',
        'dashboard_no_reports': 'Tiada Laporan Dijumpai',
        'dashboard_no_reports_msg': 'Muat naik laporan pertanian kelapa sawit pertama anda untuk bermula dengan analisis AI!',
        'dashboard_no_reports_desc': 'AI kami akan menganalisis data tanah dan daun anda untuk memberikan pandangan yang bijak.',
        'dashboard_actions': 'Tindakan Pertanian AI',
        'dashboard_action_analyze': 'Analisa Laporan Pertanian',
        'dashboard_action_analyze_desc': 'Muat naik laporan ujian tanah dan daun kelapa sawit anda untuk analisis AI',
        'dashboard_action_results': 'Lihat Hasil Terkini',
        'dashboard_action_results_desc': 'Buka ringkasan analisis AI terkini anda',
        'dashboard_start_analysis': '📤 Mula Analisis AI',
        'dashboard_view_results': '📊 Lihat Hasil',
        'dashboard_profile': 'Profil Pertanian AI',
        'dashboard_status': 'Status Sistem Pertanian AI',
        'dashboard_status_operational': 'Sistem Pertanian AI Beroperasi',
        'dashboard_status_analysis': 'Analisis AI: Sedia',
        'dashboard_status_database': 'Pangkalan Data: Bersambung',
        'dashboard_status_ocr': 'OCR: Aktif',
        'dashboard_status_online': 'Analisis: Dalam Talian',
        'dashboard_member_since': 'Ahli Pertanian AI sejak {}',
        'dashboard_logout': '🚪 Log Keluar',
        'dashboard_help_title': '💬 Bantu Kami Meningkatkan Pertanian AI',
        'dashboard_help_desc': 'Maklum balas anda membantu kami menjadikan platform analisis pertanian yang dikuasakan oleh AI lebih baik untuk penanaman kelapa sawit!',
        
        # Upload
        'upload_title': 'Muat Naik dan Analisa',
        'upload_desc': 'Muat naik laporan ujian kelapa sawit anda',
        'upload_select_files': 'Pilih fail',
        'upload_file_types': 'Disokong: PDF, JPG, PNG',
        'upload_analyzing': 'Menganalisis...',
        'upload_success': 'Analisis selesai!',
        'upload_error': 'Ralat semasa analisis',
        
        # Results
        'results_title': 'Hasil Analisis',
        'results_no_results': 'Tiada hasil tersedia',
        
        
        # Admin
        'admin_title': 'Panel Admin',
        'admin_restricted': 'Akses admin sahaja',
        
        # Common actions
        'btn_view': 'Lihat',
        'btn_download': 'Muat Turun',
        'btn_delete': 'Padam',
        'btn_edit': 'Edit',
        'btn_save': 'Simpan',
        'btn_cancel': 'Batal',
        'btn_submit': 'Hantar',
        'btn_back': 'Kembali',
        
        # Status messages
        'status_success': 'Berjaya',
        'status_error': 'Ralat',
        'status_warning': 'Amaran',
        'status_info': 'Maklumat',
        'status_loading': 'Memuatkan...',
        
        # Time
        'time_created': 'Dicipta: {}',
        'time_updated': 'Dikemaskini: {}',
        
        # Reports
        'report_type': 'Jenis: Analisis {}',
        'report_status': 'Status: Analisis AI Selesai',
        
        # System
        'system_ready': 'Semua Sistem Beroperasi',
        'system_status': 'Status Sistem',
        
        # Footer
        'footer_copyright': '© 2025 Pembantu AI AGS | Sistem Analisis Penanaman Kelapa Sawit Lanjutan',
    }
}

def get_language() -> str:
    """Get current language from session state, default to 'en' (English)"""
    if 'language' not in st.session_state:
        st.session_state.language = 'en'  # Default to English for clarity
    return st.session_state.language

def set_language(lang: str):
    """Set current language"""
    if lang in ['en', 'ms']:
        st.session_state.language = lang

def toggle_language():
    """Toggle between English and Malaysian"""
    current = get_language()
    set_language('en' if current == 'ms' else 'ms')

def translate(key: str, default: str = None, **kwargs) -> str:
    """
    Translate a key to the current language
    
    Args:
        key: Translation key
        default: Default value if key not found
        **kwargs: Format parameters for string formatting
        
    Returns:
        Translated string
    """
    lang = get_language()
    translations = TRANSLATIONS.get(lang, TRANSLATIONS['en'])
    
    text = translations.get(key, default or key)
    
    # Format string if kwargs provided
    if kwargs:
        try:
            text = text.format(**kwargs)
        except (KeyError, ValueError):
            pass  # Return as-is if formatting fails
    
    return text

def t(key: str, default: str = None, **kwargs) -> str:
    """Short alias for translate"""
    return translate(key, default, **kwargs)

